"""
=============================================================
  SCRIPT : import_offers.py
  Importer les offres depuis :
      data_engine/preprocessing/final_dataset.csv

  Colonnes du CSV :
      titre, entreprise, secteur, localisation,
      competences, experience, contrat, description

  UTILISATION :
      python import_offers.py
  OU avec chemin personnalise :
      python import_offers.py --file autrechemin/offres.csv
=============================================================
"""

import argparse
import os
import re
import sys
import unicodedata

import django
import pandas as pd


sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.jobs.models import Cluster, JobOffer, JobSkill  # noqa: E402
from apps.users.models import Skill, User  # noqa: E402


GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


def ok(msg):
    print(f"  {GREEN}OK{RESET}  {msg}")


def skip(msg):
    print(f"  {YELLOW}SKIP{RESET}  {msg}")


def err(msg):
    print(f"  {RED}ERR{RESET}  {msg}")


def title(msg):
    print(f"\n{BOLD}{'-' * 55}\n  {msg}\n{'-' * 55}{RESET}")


def clean(value):
    if pd.isna(value) or value is None:
        return ""
    return " ".join(str(value).strip().split())


def normalize(value):
    if pd.isna(value) or value is None:
        return ""
    text = str(value).strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return " ".join(text.lower().split())


def map_contrat(raw):
    mapping = {
        "cdi": "CDI",
        "cdd": "CDD",
        "stage": "Stage",
        "freelance": "Freelance",
        "interim": "CDD",
        "interim ": "CDD",
        "a discuter": "CDI",
        "autre": "CDI",
    }
    return mapping.get(clean(raw).lower(), clean(raw) or "CDI")


def parse_experience(raw):
    if not raw:
        return 0

    raw = str(raw).lower().strip()
    if any(word in raw for word in ["debutant", "junior", "sans", "0"]):
        return 0

    import re

    values = re.findall(r"\d+", raw)
    if values:
        return int(values[0])
    return 0


def build_description(row):
    description = clean(row.get("description", ""))
    if description:
        return description

    fallback = clean(row.get("text_for_matching", ""))
    if fallback:
        return fallback

    parts = [f"Poste: {clean(row.get('titre', ''))}."]

    entreprise = clean(row.get("entreprise", ""))
    if entreprise:
        parts.append(f"Entreprise: {entreprise}.")

    secteur = clean(row.get("secteur", ""))
    if secteur:
        parts.append(f"Secteur: {secteur}.")

    localisation = clean(row.get("localisation", ""))
    if localisation:
        parts.append(f"Localisation: {localisation}.")

    contrat = clean(row.get("contrat", ""))
    if contrat:
        parts.append(f"Type de contrat: {contrat}.")

    competences = clean(row.get("competences", ""))
    if competences:
        parts.append(f"Competences recherchees: {competences}.")

    experience = clean(row.get("experience", ""))
    if experience:
        parts.append(f"Experience/profil: {experience}.")

    return " ".join(parts).strip()


def get_or_create_cluster(raw_cluster):
    if raw_cluster in ("", None) or pd.isna(raw_cluster):
        return None

    cluster_number = int(raw_cluster)
    cluster = Cluster.objects.filter(k_value=cluster_number).first()
    if cluster:
        return cluster

    return Cluster.objects.create(
        label=f"Cluster {cluster_number}",
        k_value=cluster_number,
        domain="",
    )


def get_or_create_skill(name):
    name = clean(name)
    if not name:
        return None

    skill = Skill.objects.filter(name__iexact=name).first()
    if skill is None:
        skill = Skill.objects.create(name=name, type=Skill.SkillType.HARD)
    return skill


def parse_skill_names(raw_value):
    raw_value = clean(raw_value)
    if not raw_value:
        return []

    chunks = re.split(r"[|;,]+", raw_value)

    max_length = Skill._meta.get_field("name").max_length
    skill_names = []

    for chunk in chunks:
        skill_name = clean(chunk)
        if not skill_name or len(skill_name) > max_length:
            continue
        skill_names.append(skill_name)

    return list(dict.fromkeys(skill_names))


def get_admin():
    admin = User.objects.filter(role="admin").first()
    if not admin:
        print(f"\n{RED}ERREUR : Aucun admin trouve dans la base.{RESET}")
        print("Lance d'abord : python seed.py\n")
        sys.exit(1)
    return admin


def validate_columns(df):
    required = [
        "titre",
        "entreprise",
        "secteur",
        "localisation",
        "competences",
        "experience",
        "contrat",
    ]
    optional = ["description", "source", "text_clean", "text_for_matching", "cluster"]

    missing_required = [column for column in required if column not in df.columns]
    if missing_required:
        print(f"{RED}Colonnes obligatoires manquantes : {missing_required}{RESET}")
        print(f"  Colonnes presentes : {list(df.columns)}\n")
        sys.exit(1)

    missing_optional = [column for column in optional if column not in df.columns]
    if missing_optional:
        print(f"{YELLOW}Colonnes optionnelles absentes : {missing_optional}{RESET}")


def import_offres(csv_path, delimiter=","):
    title(f"Import CSV -> {csv_path}")

    try:
        df = pd.read_csv(csv_path, delimiter=delimiter, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, delimiter=delimiter, encoding="latin-1")
    except FileNotFoundError:
        print(f"\n{RED}Fichier introuvable : {csv_path}{RESET}\n")
        sys.exit(1)

    print(f"\n  Lignes trouvees : {len(df)}")
    print(f"  Colonnes        : {list(df.columns)}\n")
    validate_columns(df)

    admin = get_admin()
    created = 0
    skipped = 0
    errors = 0

    for idx, row in df.iterrows():
        try:
            titre = clean(row.get("titre", ""))
            entreprise = clean(row.get("entreprise", ""))
            secteur = clean(row.get("secteur", ""))
            localisation = clean(row.get("localisation", ""))
            competences = clean(row.get("competences", ""))
            experience = clean(row.get("experience", "0"))
            contrat = clean(row.get("contrat", "CDI"))
            description = build_description(row)
            cluster = get_or_create_cluster(row.get("cluster"))

            if not titre:
                skip(f"Ligne {idx + 2} ignoree - titre vide")
                skipped += 1
                continue

            if not entreprise:
                skip(f"Ligne {idx + 2} ignoree - entreprise vide")
                skipped += 1
                continue

            if JobOffer.objects.filter(title__iexact=titre, entreprise__iexact=entreprise).exists():
                skip(f"Doublon ignore : {titre} - {entreprise}")
                skipped += 1
                continue

            offre = JobOffer.objects.create(
                admin=admin,
                cluster=cluster,
                title=titre,
                entreprise=entreprise,
                secteur=secteur,
                localisation=localisation,
                description=description,
                type_contrat=map_contrat(contrat),
                experience_required=parse_experience(experience),
                status=JobOffer.Status.OPEN,
            )

            for skill_name in parse_skill_names(competences):
                skill = get_or_create_skill(skill_name)
                if skill is None:
                    continue
                JobSkill.objects.get_or_create(
                    job=offre,
                    skill=skill,
                    defaults={"is_required": True},
                )

            created += 1
            ok(f"[{created}] {titre} - {entreprise} ({localisation})")
        except Exception as exc:
            errors += 1
            err(f"Ligne {idx + 2} - Erreur : {exc}")

    print(f"\n{BOLD}{'=' * 55}{RESET}")
    print(f"  Offres creees   : {created}")
    print(f"  Ignorees        : {skipped}")
    print(f"  Erreurs         : {errors}")
    print(f"  Total traite    : {len(df)}")
    print(f"  Total en base   : {JobOffer.objects.count()} offres")
    print(f"{BOLD}{'=' * 55}{RESET}\n")


if __name__ == "__main__":
    default_csv = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "data_engine",
        "preprocessing",
        "final_dataset.csv",
    )

    parser = argparse.ArgumentParser(description="Importer les offres CSV")
    parser.add_argument(
        "--file",
        default=default_csv,
        help="Chemin vers le fichier CSV (defaut: data_engine/preprocessing/final_dataset.csv)",
    )
    parser.add_argument(
        "--delimiter",
        default=",",
        help="Separateur CSV (, ou ;)",
    )
    args = parser.parse_args()

    import_offres(csv_path=args.file, delimiter=args.delimiter)
