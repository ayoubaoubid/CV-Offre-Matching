"""
Resynchronise les skills des offres deja presentes en base a partir du CSV source.

Le script:
- ne cree pas de nouvelles offres,
- ne supprime pas d'offres,
- met a jour uniquement les relations JobSkill.

Usage:
    python resync_job_skills.py
    python resync_job_skills.py --file autrechemin/offres.csv
    python resync_job_skills.py --delimiter ";"
"""

import argparse
import os
import re
import sys
import unicodedata
from collections import defaultdict

import django
import pandas as pd
from pandas.errors import ParserError
from django.db import transaction


sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.jobs.models import JobOffer, JobSkill  # noqa: E402
from apps.users.models import Skill  # noqa: E402


GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"
SKILL_NAME_MAX_LENGTH = Skill._meta.get_field("name").max_length
SKILL_KEYWORDS = {
    "python": "Python",
    "django": "Django",
    "react": "React",
    "javascript": "JavaScript",
    "sql": "SQL",
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "power bi": "Power BI",
    "tableau": "Tableau",
    "excel": "Excel",
    "git": "Git",
    "docker": "Docker",
    "linux": "Linux",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "scikit learn": "Scikit-learn",
    "scikit-learn": "Scikit-learn",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "nlp": "NLP",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "matplotlib": "Matplotlib",
    "autocad": "AutoCAD",
    "sketchup": "SketchUp",
    "crm": "CRM",
    "bureautique": "Bureautique",
    "videosurveillance": "Videosurveillance",
    "modelisation 3d": "Modelisation 3D",
    "genie electrique": "Genie electrique",
    "mecanique": "Mecanique",
    "systemes mecaniques": "Systemes mecaniques",
    "systemes electriques": "Systemes electriques",
    "pneumatiques": "Pneumatiques",
    "logistique": "Logistique",
    "transport": "Transport",
    "vente": "Vente",
    "commerce": "Commerce",
    "negociation": "Negociation",
    "relation client": "Relation client",
    "securite": "Securite",
    "telesurveillance": "Telesurveillance",
    "analyse": "Analyse",
    "francais": "Francais",
    "arabe": "Arabe",
}
NOISE_PATTERNS = [
    "poste base",
    "nous offrons",
    "interesse",
    "postulez",
    "envoyant votre cv",
    "candidature",
    "disponibilite",
    "zone :",
    "objectif :",
]


def ok(message):
    print(f"  {GREEN}OK{RESET}  {message}")


def skip(message):
    print(f"  {YELLOW}SKIP{RESET}  {message}")


def err(message):
    print(f"  {RED}ERR{RESET}  {message}")


def title(message):
    print(f"\n{BOLD}{'-' * 55}\n  {message}\n{'-' * 55}{RESET}")


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


def split_skills(raw_value):
    raw_value = clean(raw_value)
    if not raw_value:
        return []

    if "|" in raw_value:
        chunks = raw_value.split("|")
    elif ";" in raw_value:
        chunks = raw_value.split(";")
    else:
        chunks = raw_value.split(",")

    return [chunk.strip() for chunk in chunks if chunk.strip()]


def normalize_for_matching(value):
    value = normalize(value)
    value = value.replace("-", " ")
    return re.sub(r"\s+", " ", value).strip()


def extract_skills_from_free_text(raw_value):
    text = clean(raw_value)
    normalized_text = normalize_for_matching(text)
    extracted = []

    for pattern, label in SKILL_KEYWORDS.items():
        regex = r"(?<!\w)" + re.escape(pattern) + r"(?!\w)"
        if re.search(regex, normalized_text):
            extracted.append(label)

    return extracted


def sanitize_skill_name(name):
    name = clean(name)
    if not name:
        return None

    # Ignore long free-text fragments incorrectly stored in the competences column.
    if len(name) > SKILL_NAME_MAX_LENGTH:
        return None

    return name


def looks_like_free_text(name):
    normalized_name = normalize_for_matching(name)
    if len(name) > SKILL_NAME_MAX_LENGTH:
        return True
    if any(pattern in normalized_name for pattern in NOISE_PATTERNS):
        return True
    if len(normalized_name.split()) > 8:
        return True
    return False


def normalize_skill_candidates(raw_names):
    normalized_names = []
    skipped_names = []

    for raw_name in raw_names:
        if not clean(raw_name):
            continue

        candidates = [raw_name]
        if looks_like_free_text(raw_name):
            extracted = extract_skills_from_free_text(raw_name)
            if extracted:
                candidates = extracted

        for candidate in candidates:
            safe_name = sanitize_skill_name(candidate)
            if safe_name is None:
                skipped_names.append(clean(candidate or raw_name))
                continue
            normalized_names.append(safe_name)

    deduped = list(dict.fromkeys(normalized_names))
    return deduped, skipped_names


def get_or_create_skill(name):
    name = sanitize_skill_name(name)
    if not name:
        return None

    skill = Skill.objects.filter(name__iexact=name).first()
    if skill is None:
        skill = Skill.objects.create(name=name, type=Skill.SkillType.HARD)
    return skill


def read_csv_with_fallbacks(csv_path, delimiter):
    delimiters = [delimiter]
    for candidate in [",", ";", "\t"]:
        if candidate not in delimiters:
            delimiters.append(candidate)

    encodings = ["utf-8", "latin-1"]
    last_error = None

    for current_delimiter in delimiters:
        for encoding in encodings:
            try:
                df = pd.read_csv(csv_path, delimiter=current_delimiter, encoding=encoding)
                return df, current_delimiter, encoding
            except (UnicodeDecodeError, ParserError) as exc:
                last_error = exc

    raise last_error


def load_csv_rows(csv_path, delimiter):
    df, used_delimiter, used_encoding = read_csv_with_fallbacks(csv_path, delimiter)
    print(f"  CSV lu avec delimiter='{used_delimiter}' et encoding='{used_encoding}'")

    indexed = defaultdict(list)
    for _, row in df.fillna("").iterrows():
        record = {
            "titre": clean(row.get("titre", "")),
            "entreprise": clean(row.get("entreprise", "")),
            "secteur": clean(row.get("secteur", "")),
            "localisation": clean(row.get("localisation", "")),
            "contrat": clean(row.get("contrat", "")),
            "skills": split_skills(row.get("competences", "")),
        }
        key = (normalize(record["titre"]), normalize(record["entreprise"]))
        if key != ("", ""):
            indexed[key].append(record)
    return indexed


def pick_csv_row(job, indexed_rows):
    candidates = indexed_rows.get((normalize(job.title), normalize(job.entreprise)), [])
    if not candidates:
        return None, "introuvable"

    if len(candidates) == 1:
        return candidates[0], "titre+entreprise"

    filters = [
        ("localisation", lambda row: normalize(row["localisation"]) == normalize(job.localisation)),
        ("secteur", lambda row: normalize(row["secteur"]) == normalize(job.secteur)),
        ("contrat", lambda row: normalize(row["contrat"]) == normalize(job.type_contrat)),
    ]

    remaining = candidates
    for reason, predicate in filters:
        narrowed = [row for row in remaining if predicate(row)]
        if narrowed:
            remaining = narrowed
        if len(remaining) == 1:
            return remaining[0], f"titre+entreprise+{reason}"

    return None, "ambigu"


def sync_job_skills(job, skill_names):
    sanitized_names, skipped_names = normalize_skill_candidates(skill_names)
    wanted_names = {name.lower() for name in sanitized_names}
    existing = list(JobSkill.objects.filter(job=job).select_related("skill"))

    removed = 0
    for job_skill in existing:
        if job_skill.skill.name.lower() not in wanted_names:
            job_skill.delete()
            removed += 1

    added = 0
    for name in sanitized_names:
        skill = get_or_create_skill(name)
        if skill is None:
            continue
        _job_skill, created = JobSkill.objects.get_or_create(
            job=job,
            skill=skill,
            defaults={"is_required": True},
        )
        if created:
            added += 1

    return added, removed, skipped_names


@transaction.atomic
def resync_job_skills(csv_path, delimiter):
    title(f"Resynchronisation JobSkill -> {csv_path}")
    indexed_rows = load_csv_rows(csv_path, delimiter)

    updated_jobs = 0
    added_links = 0
    removed_links = 0
    unmatched_jobs = []
    ambiguous_jobs = []

    jobs = JobOffer.objects.all().order_by("id_jobOffer")
    for job in jobs:
        row, reason = pick_csv_row(job, indexed_rows)
        if row is None:
            payload = (job.id_jobOffer, job.title, job.entreprise)
            if reason == "ambigu":
                ambiguous_jobs.append(payload)
            else:
                unmatched_jobs.append(payload)
            continue

        added, removed, skipped_names = sync_job_skills(job, row["skills"])
        if added or removed:
            updated_jobs += 1
            added_links += added
            removed_links += removed
            ok(
                f"{job.id_jobOffer} | {job.title} | +{added} skill(s), -{removed} skill(s) [{reason}]"
            )
        if skipped_names:
            skip(
                f"{job.id_jobOffer} | {job.title} | {len(skipped_names)} valeur(s) competences ignoree(s) car invalides"
            )

    print(f"\n{BOLD}{'=' * 55}{RESET}")
    print(f"  Offres mises a jour     : {updated_jobs}")
    print(f"  Liens JobSkill ajoutes  : {added_links}")
    print(f"  Liens JobSkill supprimes: {removed_links}")
    print(f"  Offres sans match CSV   : {len(unmatched_jobs)}")
    print(f"  Offres ambiguës         : {len(ambiguous_jobs)}")
    print(f"{BOLD}{'=' * 55}{RESET}\n")

    if unmatched_jobs:
        skip("Exemples sans correspondance:")
        for job_id, title_text, company in unmatched_jobs[:10]:
            print(f"    - {job_id} | {title_text} | {company}")

    if ambiguous_jobs:
        skip("Exemples ambigus:")
        for job_id, title_text, company in ambiguous_jobs[:10]:
            print(f"    - {job_id} | {title_text} | {company}")


if __name__ == "__main__":
    default_csv = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "data_engine",
        "preprocessing",
        "cleaned_offres.csv",
    )

    parser = argparse.ArgumentParser(description="Resynchroniser les JobSkill depuis le CSV")
    parser.add_argument(
        "--file",
        default=default_csv,
        help="Chemin vers le CSV source des offres",
    )
    parser.add_argument(
        "--delimiter",
        default=",",
        help="Separateur CSV (, ou ;)",
    )
    args = parser.parse_args()

    try:
        resync_job_skills(args.file, args.delimiter)
    except FileNotFoundError:
        err(f"Fichier introuvable: {args.file}")
        sys.exit(1)
