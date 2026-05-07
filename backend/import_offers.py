"""
=============================================================
  SCRIPT : import_offres.py
  Importer les offres depuis :
      data_engine/preprocessing/cleaned_offeres.csv

  Colonnes du CSV :
      titre, entreprise, secteur, localisation,
      competences, experience, contrat, text_clean

  UTILISATION :
      python import_offres.py
  OU avec chemin personnalisé :
      python import_offres.py --file autrechemin/offres.csv
=============================================================
"""

import os
import sys
import django
import argparse
import pandas as pd
import unicodedata

# -------------------------------------------------------------
#  Initialiser Django
# -------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# -------------------------------------------------------------
#  Imports modèles APRÈS django.setup()
# -------------------------------------------------------------
from apps.jobs.models import Cluster, JobOffer, JobSkill
from apps.users.models import User, Skill

# -------------------------------------------------------------
#  Couleurs terminal
# -------------------------------------------------------------
GREEN  = '\033[92m'
YELLOW = '\033[93m'
RED    = '\033[91m'
RESET  = '\033[0m'
BOLD   = '\033[1m'

def ok(msg):    print(f"  {GREEN}✔{RESET}  {msg}")
def skip(msg):  print(f"  {YELLOW}⏭{RESET}  {msg}")
def err(msg):   print(f"  {RED}✘{RESET}  {msg}")
def title(msg): print(f"\n{BOLD}{'─'*55}\n  {msg}\n{'─'*55}{RESET}")


# -------------------------------------------------------------
#  Utilitaires
# -------------------------------------------------------------

def clean(value):
    """Retourne une chaîne propre ou '' si NaN."""
    if pd.isna(value):
        return ''
    return str(value).strip()


def normalize(value):
    if pd.isna(value) or value is None:
        return ''
    text = str(value).strip()
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    return ' '.join(text.lower().split())


def map_contrat(raw):
    """
    Normalise le type de contrat vers les choix Django.
    Accepte : cdi, cdd, stage, freelance (insensible à la casse)
    """
    mapping = {
        'cdi':       'CDI',
        'cdd':       'CDD',
        'stage':     'Stage',
        'freelance': 'Freelance',
        'interim':   'CDD',
        'intérim':   'CDD',
    }
    return mapping.get(raw.lower().strip(), 'CDI')


def parse_experience(raw):
    """
    Extrait un entier depuis des valeurs comme :
    '3', '3 ans', '2-4 ans', '+5 ans', 'débutant'
    """
    if not raw:
        return 0
    raw = str(raw).lower().strip()

    # cas : débutant / junior
    if any(w in raw for w in ['débutant', 'junior', 'sans', '0']):
        return 0

    # extraire le premier chiffre trouvé
    import re
    nums = re.findall(r'\d+', raw)
    if nums:
        return int(nums[0])
    return 0


def build_description(row):
    """Construit une description lisible si le CSV ne fournit pas de description brute."""
    description = clean(row.get('description', ''))
    if description:
        return description

    parts = [f"Poste: {clean(row.get('titre', ''))}."]

    entreprise = clean(row.get('entreprise', ''))
    if entreprise:
        parts.append(f"Entreprise: {entreprise}.")

    secteur = clean(row.get('secteur', ''))
    if secteur:
        parts.append(f"Secteur: {secteur}.")

    localisation = clean(row.get('localisation', ''))
    if localisation:
        parts.append(f"Localisation: {localisation}.")

    contrat = clean(row.get('contrat', ''))
    if contrat:
        parts.append(f"Type de contrat: {contrat}.")

    competences = clean(row.get('competences', ''))
    if competences:
        parts.append(f"Competences recherchees: {competences}.")

    experience = clean(row.get('experience', ''))
    if experience:
        parts.append(f"Experience/profil: {experience}.")

    return ' '.join(parts).strip()


def get_or_create_cluster(raw_cluster):
    """Cree ou recupere un cluster si le CSV en fournit un."""
    if raw_cluster in ('', None) or pd.isna(raw_cluster):
        return None

    cluster_number = int(raw_cluster)
    cluster = Cluster.objects.filter(k_value=cluster_number).first()
    if cluster:
        return cluster

    return Cluster.objects.create(
        label=f'Cluster {cluster_number}',
        k_value=cluster_number,
        domain='',
    )


def get_or_create_skill(name):
    """Récupère ou crée un skill depuis son nom."""
    name = name.strip()
    if not name:
        return None
    skill, created = Skill.objects.get_or_create(
        name__iexact=name,
        defaults={'name': name, 'type': 'hard'}
    )
    return skill


def get_admin():
    """Récupère le premier admin disponible."""
    admin = User.objects.filter(role='admin').first()
    if not admin:
        print(f"\n{RED}ERREUR : Aucun admin trouvé dans la base.{RESET}")
        print("Lance d'abord : python seed.py\n")
        sys.exit(1)
    return admin


# -------------------------------------------------------------
#  Fonction principale d'import
# -------------------------------------------------------------

def import_offres(csv_path, delimiter=','):

    title(f"Import CSV → {csv_path}")

    # ── Lire le CSV ──────────────────────────────────────────
    try:
        df = pd.read_csv(csv_path, delimiter=delimiter, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, delimiter=delimiter, encoding='latin-1')
    except FileNotFoundError:
        print(f"\n{RED}Fichier introuvable : {csv_path}{RESET}\n")
        sys.exit(1)

    print(f"\n  Lignes trouvées : {len(df)}")
    print(f"  Colonnes        : {list(df.columns)}\n")

    # ── Vérifier les colonnes attendues ──────────────────────
    expected = ['titre','entreprise','secteur','localisation',
                'competences','experience','contrat','text_clean']
    missing = [c for c in expected if c not in df.columns]
    if missing:
        print(f"{YELLOW}⚠ Colonnes manquantes : {missing}{RESET}")
        print(f"  Colonnes présentes : {list(df.columns)}\n")

    admin = get_admin()

    # ── Compteurs ────────────────────────────────────────────
    created = 0
    skipped = 0
    errors  = 0

    # ── Parcourir chaque ligne ───────────────────────────────
    for idx, row in df.iterrows():
        try:
            # Lire les champs
            titre        = clean(row.get('titre', ''))
            entreprise   = clean(row.get('entreprise', ''))
            secteur      = clean(row.get('secteur', ''))
            localisation = clean(row.get('localisation', ''))
            competences  = clean(row.get('competences', ''))
            experience   = clean(row.get('experience', '0'))
            contrat      = clean(row.get('contrat', 'CDI'))
            description  = build_description(row)
            cluster      = get_or_create_cluster(row.get('cluster'))

            # ── Vérifier champs obligatoires ─────────────────
            if not titre:
                skip(f"Ligne {idx+2} ignorée — titre vide")
                skipped += 1
                continue

            if not entreprise:
                skip(f"Ligne {idx+2} ignorée — entreprise vide")
                skipped += 1
                continue

            # ── Eviter les doublons (titre + entreprise) ──────
            if JobOffer.objects.filter(
                title__iexact=titre,
                entreprise__iexact=entreprise
            ).exists():
                skip(f"Doublon ignoré : {titre} — {entreprise}")
                skipped += 1
                continue

            # ── Créer l'offre ─────────────────────────────────
            offre = JobOffer.objects.create(
                admin               = admin,
                cluster             = cluster,
                title               = titre,
                entreprise          = entreprise,
                secteur             = secteur,
                localisation        = localisation,
                description         = description,
                type_contrat        = map_contrat(contrat),
                experience_required = parse_experience(experience),
                status              = 'open',
                # cluster_id = NULL → sera assigné par K-means plus tard
            )

            # ── Créer les compétences liées ───────────────────
            # Format attendu : "Python, Django, SQL"
            # ou              : "Python|Django|SQL"
            # ou              : "Python;Django;SQL"
            if competences:
                # Détecter le séparateur
                if '|' in competences:
                    skill_list = competences.split('|')
                elif ';' in competences:
                    skill_list = competences.split(';')
                else:
                    skill_list = competences.split(',')

                for skill_name in skill_list:
                    skill_name = skill_name.strip()
                    if not skill_name:
                        continue
                    skill = get_or_create_skill(skill_name)
                    if skill:
                        JobSkill.objects.get_or_create(
                            job   = offre,
                            skill = skill,
                            defaults={'is_required': True}
                        )

            created += 1
            ok(f"[{created}] {titre} — {entreprise} ({localisation})")

        except Exception as e:
            errors += 1
            err(f"Ligne {idx+2} — Erreur : {e}")
            continue

    # ── Résumé ───────────────────────────────────────────────
    print(f"\n{BOLD}{'═'*55}{RESET}")
    print(f"  {GREEN}✔ Offres créées   : {created}{RESET}")
    print(f"  {YELLOW}⏭ Ignorées        : {skipped}{RESET}")
    print(f"  {RED}✘ Erreurs         : {errors}{RESET}")
    print(f"  Total traité      : {len(df)}")
    print(f"  Total en base     : {JobOffer.objects.count()} offres")
    print(f"{BOLD}{'═'*55}{RESET}\n")


# -------------------------------------------------------------
#  Point d'entrée
# -------------------------------------------------------------
if __name__ == '__main__':

    # Chemin par défaut vers ton fichier CSV
    DEFAULT_CSV = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', 'data_engine', 'preprocessing', 'cleaned_offres.csv'
    )

    parser = argparse.ArgumentParser(description='Importer les offres CSV')
    parser.add_argument(
        '--file',
        default=DEFAULT_CSV,
        help='Chemin vers le fichier CSV (défaut: data_engine/preprocessing/cleaned_offeres.csv)'
    )
    parser.add_argument(
        '--delimiter',
        default=',',
        help='Séparateur CSV (, ou ;)'
    )
    args = parser.parse_args()

    import_offres(
        csv_path  = args.file,
        delimiter = args.delimiter,
    )
