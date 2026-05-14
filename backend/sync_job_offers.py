import os
import sys
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher

import django
import pandas as pd
from django.db import transaction


sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.jobs.models import Cluster, JobOffer  # noqa: E402
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
CLUSTERED_CSV = os.path.join(
    PROJECT_DIR, "data_engine", "clustering", "dbscan_clustered_offres_new.csv"
)
REKRUTE_CSV = os.path.join(
    PROJECT_DIR, "data_engine", "scraping", "rekrute_jobs_.csv"
)
MAROCANNONCES_CSV = os.path.join(
    PROJECT_DIR, "data_engine", "scraping","BeautifulSoup", "marocannonces_offres_emploi.csv"
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


def normalize_title(value):
    text = normalize(value)
    for old, new in {
        "/": " ",
        "-": " ",
        "(": " ",
        ")": " ",
        ",": " ",
        ".": " ",
    }.items():
        text = text.replace(old, new)
    return " ".join(text.split())


def title_similarity(left, right):
    if not left or not right:
        return 0
    return SequenceMatcher(None, normalize_title(left), normalize_title(right)).ratio()


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
    cluster_column = "cluster_dbscan" if "cluster_dbscan" in df.columns else "cluster"
    indexed = defaultdict(list)

    for _, row in df.iterrows():
        record = {
            "titre": normalize(row.get("titre")),
            "entreprise": normalize(row.get("entreprise")),
            "secteur": normalize(row.get("secteur")),
            "localisation": normalize(row.get("localisation")),
            "contrat": normalize(row.get("contrat")),
            "cluster_number": int(row.get(cluster_column)),
            "raw": row.to_dict(),
        }
        indexed[(record["titre"], record["entreprise"])].append(record)

    return indexed


def load_all_cluster_numbers():
    df = pd.read_csv(CLUSTERED_CSV).fillna("")
    cluster_column = "cluster_dbscan" if "cluster_dbscan" in df.columns else "cluster"
    return {int(value) for value in df[cluster_column].tolist()}


def iter_all_cluster_rows(indexed_rows):
    for rows in indexed_rows.values():
        for row in rows:
            yield row


def dedupe_candidates(candidates):
    unique = {}
    for row in candidates:
        key = (
            row["titre"],
            row["entreprise"],
            row["secteur"],
            row["localisation"],
            row["contrat"],
            row["cluster_number"],
        )
        unique.setdefault(key, row)
    return list(unique.values())


def pick_cluster_row(job, indexed_rows):
    candidates = dedupe_candidates(
        indexed_rows.get((normalize(job.title), normalize(job.entreprise)), [])
    )
    if len(candidates) == 1:
        return candidates[0], "titre+entreprise"

    normalized_title = normalize(job.title)
    normalized_company = normalize(job.entreprise)
    normalized_location = normalize(job.localisation)
    normalized_contract = normalize(job.type_contrat)

    if candidates:
        filters = [
            ("localisation", lambda row: row["localisation"] == normalized_location),
            ("secteur", lambda row: row["secteur"] == normalize(job.secteur)),
            ("contrat", lambda row: row["contrat"] == normalized_contract),
        ]

        for reason, predicate in filters:
            narrowed = [row for row in candidates if predicate(row)]
            if narrowed:
                candidates = dedupe_candidates(narrowed)
            if len(candidates) == 1:
                return candidates[0], f"titre+entreprise+{reason}"

        cluster_numbers = {row["cluster_number"] for row in candidates}
        if len(cluster_numbers) == 1:
            return candidates[0], "titre+entreprise+cluster-identique"

    # Fallback 1: titre + localisation si cela identifie un cluster unique.
    title_location_candidates = [
        row for row in iter_all_cluster_rows(indexed_rows)
        if row["titre"] == normalized_title
        and row["localisation"] == normalized_location
    ]
    title_location_candidates = dedupe_candidates(title_location_candidates)
    title_location_clusters = {row["cluster_number"] for row in title_location_candidates}
    if len(title_location_clusters) == 1 and title_location_candidates:
        return title_location_candidates[0], "titre+localisation"

    # Fallback 2: fuzzy matching sur le titre avec meme entreprise.
    same_company_candidates = dedupe_candidates([
        row for row in iter_all_cluster_rows(indexed_rows)
        if row["entreprise"] == normalized_company
    ])
    best_candidate = None
    best_score = 0
    second_best_score = 0
    for row in same_company_candidates:
        current_score = title_similarity(job.title, row["titre"])
        if row["localisation"] == normalized_location and normalized_location:
            current_score += 0.08
        if row["contrat"] == normalized_contract and normalized_contract:
            current_score += 0.04
        if current_score > best_score:
            second_best_score = best_score
            best_score = current_score
            best_candidate = row
        elif current_score > second_best_score:
            second_best_score = current_score

    if (
        best_candidate is not None
        and best_score >= 0.88
        and (best_score - second_best_score) >= 0.03
    ):
        return best_candidate, "fuzzy-titre+entreprise"

    return None, "introuvable" if not candidates else "ambigu"


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
        stored_k_value = cluster_number
        expected_label = "Cluster -1 (Noise)" if cluster_number == -1 else f"Cluster {cluster_number}"
        cluster = Cluster.objects.filter(k_value=stored_k_value).first()
        if cluster is None:
            cluster = Cluster.objects.create(
                label=expected_label,
                k_value=stored_k_value,
                domain="",
            )
        elif cluster.label != expected_label:
            cluster.label = expected_label
            cluster.save(update_fields=["label"])

        cluster_map[cluster_number] = cluster

    return cluster_map


@transaction.atomic
def sync_job_offers():
    indexed_rows = load_cluster_rows()
    all_cluster_numbers = load_all_cluster_numbers()

    matched_rows = []
    unmatched_jobs = []

    for job in JobOffer.objects.select_related("cluster").all():
        row, reason = pick_cluster_row(job, indexed_rows)
        if row is None:
            unmatched_jobs.append((job.id_jobOffer, job.title, job.entreprise, reason))
            continue
        matched_rows.append((job, row, reason))

    cluster_map = ensure_clusters(all_cluster_numbers)

    cluster_updates = 0
    matching_stats = defaultdict(int)
    unmatched_count = len(unmatched_jobs)

    for job, row, reason in matched_rows:
        matching_stats[reason] += 1

        cluster_number = row["cluster_number"]
        cluster = cluster_map[cluster_number]
        changed_fields = []

        if job.cluster_id != cluster.id:
            job.cluster = cluster
            changed_fields.append("cluster")
            cluster_updates += 1

        if changed_fields:
            job.save(update_fields=changed_fields)

    print("Synchronisation terminee")
    print(f"Offres mises a jour (cluster): {cluster_updates}")
    print(f"Clusters disponibles: {Cluster.objects.count()}")
    print(f"Offres non appariees ignorees: {unmatched_count}")
    print("Detail du matching clusters:")
    for reason, count in sorted(matching_stats.items()):
        print(f"  - {reason}: {count}")
    if unmatched_jobs:
        print("Exemples d'offres non appariees:")
        for job_id, title, entreprise, reason in unmatched_jobs[:10]:
            print(f"  - {job_id} | {title} | {entreprise} | {reason}")
if __name__ == "__main__":
    sync_job_offers()
