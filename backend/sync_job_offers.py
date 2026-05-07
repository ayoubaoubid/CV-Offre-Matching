import os
import sys
import unicodedata
from collections import defaultdict

import django
import pandas as pd
from django.db import transaction


sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.jobs.models import Cluster, JobOffer  # noqa: E402
from apps.users.models import User  # noqa: E402


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
CLUSTERED_CSV = os.path.join(
    PROJECT_DIR, "data_engine", "clustering", "clustered_offres.csv"
)
REKRUTE_CSV = os.path.join(
    PROJECT_DIR, "data_engine", "scraping", "rekrute_jobs_.csv"
)
MAROCANNONCES_CSV = os.path.join(
    PROJECT_DIR, "data_engine", "scraping", "marocannonces_offres_emploi.csv"
)


def normalize(value):
    if pd.isna(value) or value is None:
        return ""
    text = str(value).strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return " ".join(text.lower().split())


def clean_text(value):
    if pd.isna(value) or value is None:
        return ""
    return " ".join(str(value).strip().split())


def build_fallback_description(row):
    parts = [f"Poste: {clean_text(row.get('titre', ''))}."]

    entreprise = clean_text(row.get("entreprise", ""))
    if entreprise:
        parts.append(f"Entreprise: {entreprise}.")

    secteur = clean_text(row.get("secteur", ""))
    if secteur:
        parts.append(f"Secteur: {secteur}.")

    localisation = clean_text(row.get("localisation", ""))
    if localisation:
        parts.append(f"Localisation: {localisation}.")

    contrat = clean_text(row.get("contrat", ""))
    if contrat:
        parts.append(f"Type de contrat: {contrat}.")

    competences = clean_text(row.get("competences", ""))
    if competences:
        parts.append(f"Compétences recherchées: {competences}.")

    experience = clean_text(row.get("experience", ""))
    if experience:
        parts.append(f"Expérience/profil: {experience}.")

    return " ".join(parts).strip()


def load_cluster_rows():
    df = pd.read_csv(CLUSTERED_CSV).fillna("")
    indexed = defaultdict(list)

    for _, row in df.iterrows():
        record = {
            "titre": normalize(row.get("titre")),
            "entreprise": normalize(row.get("entreprise")),
            "secteur": normalize(row.get("secteur")),
            "localisation": normalize(row.get("localisation")),
            "contrat": normalize(row.get("contrat")),
            "cluster_number": int(row.get("cluster")),
            "raw": row.to_dict(),
        }
        indexed[(record["titre"], record["entreprise"])].append(record)

    return indexed


def pick_cluster_row(job, indexed_rows):
    candidates = indexed_rows.get((normalize(job.title), normalize(job.entreprise)), [])
    if not candidates:
        return None, "introuvable"

    if len(candidates) == 1:
        return candidates[0], "titre+entreprise"

    filters = [
        ("localisation", lambda row: row["localisation"] == normalize(job.localisation)),
        ("secteur", lambda row: row["secteur"] == normalize(job.secteur)),
        ("contrat", lambda row: row["contrat"] == normalize(job.type_contrat)),
    ]

    for reason, predicate in filters:
        narrowed = [row for row in candidates if predicate(row)]
        if narrowed:
            candidates = narrowed
        if len(candidates) == 1:
            return candidates[0], f"titre+entreprise+{reason}"

    return None, "ambigu"


def load_rekrute_descriptions():
    df = pd.read_csv(REKRUTE_CSV).fillna("")
    descriptions = {}
    for _, row in df.iterrows():
        key = (normalize(row.get("titre")), normalize(row.get("entreprise")))
        if key == ("", ""):
            continue
        description = clean_text(row.get("description", ""))
        if description:
            descriptions[key] = description
    return descriptions


def load_marocannonces_descriptions():
    df = pd.read_csv(MAROCANNONCES_CSV).fillna("")
    descriptions = {}
    for _, row in df.iterrows():
        key = (normalize(row.get("title")), normalize(row.get("city")))
        if key == ("", ""):
            continue
        description = clean_text(row.get("description", ""))
        if description:
            descriptions[key] = description
    return descriptions


def ensure_clusters(cluster_numbers):
    cluster_map = {}

    for cluster_number in sorted(cluster_numbers):
        cluster = Cluster.objects.filter(k_value=cluster_number).first()
        if cluster is None:
            cluster = Cluster.objects.create(
                label=f"Cluster {cluster_number}",
                k_value=cluster_number,
                domain="",
            )
        elif cluster.label != f"Cluster {cluster_number}":
            cluster.label = f"Cluster {cluster_number}"
            cluster.save(update_fields=["label"])

        cluster_map[cluster_number] = cluster

    return cluster_map


@transaction.atomic
def sync_job_offers_and_users():
    indexed_rows = load_cluster_rows()
    rekrute_descriptions = load_rekrute_descriptions()
    marocannonces_descriptions = load_marocannonces_descriptions()

    matched_rows = []
    unmatched_jobs = []

    for job in JobOffer.objects.select_related("cluster").all():
        row, reason = pick_cluster_row(job, indexed_rows)
        if row is None:
            unmatched_jobs.append((job.id_jobOffer, job.title, job.entreprise, reason))
            continue
        matched_rows.append((job, row, reason))

    if unmatched_jobs:
        raise RuntimeError(f"Offres non appariées: {unmatched_jobs[:10]}")

    cluster_map = ensure_clusters({row["cluster_number"] for _, row, _ in matched_rows})

    cluster_updates = 0
    description_updates = 0
    rekrute_count = 0
    marocannonces_count = 0
    fallback_count = 0
    matching_stats = defaultdict(int)

    for job, row, reason in matched_rows:
        matching_stats[reason] += 1

        cluster = cluster_map[row["cluster_number"]]
        changed_fields = []

        if job.cluster_id != cluster.id:
            job.cluster = cluster
            changed_fields.append("cluster")
            cluster_updates += 1

        description = rekrute_descriptions.get(
            (normalize(job.title), normalize(job.entreprise))
        )
        if description:
            rekrute_count += 1
        else:
            description = marocannonces_descriptions.get(
                (normalize(job.title), normalize(job.localisation))
            )
            if description:
                marocannonces_count += 1
            else:
                description = build_fallback_description(row["raw"])
                fallback_count += 1

        if job.description != description:
            job.description = description
            changed_fields.append("description")
            description_updates += 1

        if changed_fields:
            job.save(update_fields=changed_fields)

    password_updates = 0
    for user in User.objects.all():
        simple_password = "admin123" if user.role == User.Role.ADMIN else "candidate123"
        user.set_password(simple_password)
        user.save(update_fields=["password"])
        password_updates += 1

    print("Synchronisation terminee")
    print(f"Offres mises a jour (cluster): {cluster_updates}")
    print(f"Offres mises a jour (description): {description_updates}")
    print(f"Descriptions depuis ReKrute: {rekrute_count}")
    print(f"Descriptions depuis MarocAnnonces: {marocannonces_count}")
    print(f"Descriptions reconstruites: {fallback_count}")
    print(f"Clusters disponibles: {Cluster.objects.count()}")
    print(f"Utilisateurs avec mot de passe simplifie: {password_updates}")
    print("Detail du matching clusters:")
    for reason, count in sorted(matching_stats.items()):
        print(f"  - {reason}: {count}")
    print("Mots de passe definis:")
    print("  - admins: admin123")
    print("  - candidats: candidate123")


if __name__ == "__main__":
    sync_job_offers_and_users()
