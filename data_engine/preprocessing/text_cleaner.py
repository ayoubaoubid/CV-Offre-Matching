from pathlib import Path

import pandas as pd

from data_engine.preprocessing.skill_extractor import extract_skills_from_text, serialize_skills
from data_engine.utils.text_utils import clean_rekrute_description, clean_text, looks_like_free_text


BASE_DIR = Path(__file__).resolve().parent
SCRAPING_DIR = BASE_DIR.parent / "scraping"
MAROCANNONCES_PATH = SCRAPING_DIR / "BeautifulSoup" / "marocannonces_offres_emploi.csv"
REKRUTE_PATH = SCRAPING_DIR / "rekrute_jobs_.csv"
OUTPUT_PATH = BASE_DIR / "cleaned_offres.csv"

OUTPUT_COLUMNS = [
    "titre",
    "entreprise",
    "secteur",
    "localisation",
    "competences",
    "experience",
    "contrat",
    "description",
    "source",
]


def normalize_skills_field(skills_text, fallback_text=""):
    skills_text = clean_text(skills_text)
    fallback_text = clean_text(fallback_text)

    if skills_text and not looks_like_free_text(skills_text):
        return skills_text, ""

    source_text = skills_text or fallback_text
    extracted = serialize_skills(extract_skills_from_text(source_text))
    description = source_text if source_text and looks_like_free_text(source_text) else ""
    return extracted, description


def build_marocannonces_frame():
    df = pd.read_csv(MAROCANNONCES_PATH).fillna("")
    df = df.rename(
        columns={
            "Titre du poste": "titre",
            "Entreprise": "entreprise",
            "Secteur d'activite": "secteur",
            "Localisation geographique": "localisation",
            "Competences requises": "competences",
            "Niveau d'experience requis": "experience",
            "Type de contrat": "contrat",
        }
    )

    for column in ["titre", "entreprise", "secteur", "localisation", "experience", "contrat"]:
        df[column] = df[column].apply(clean_text)

    normalized = df.apply(
        lambda row: normalize_skills_field(row.get("competences", ""), row.get("experience", "")),
        axis=1,
        result_type="expand",
    )
    df["competences"] = normalized[0]
    df["description"] = normalized[1]
    df["source"] = "marocannonces"
    return df[OUTPUT_COLUMNS]


def build_rekrute_frame():
    df = pd.read_csv(REKRUTE_PATH).fillna("")
    for column in ["titre", "entreprise", "secteur", "localisation", "experience", "contrat"]:
        df[column] = df[column].apply(clean_text)

    df["description"] = df["description"].apply(clean_rekrute_description)
    df["competences"] = df["description"].apply(
        lambda value: serialize_skills(extract_skills_from_text(value))
    )
    df["source"] = "rekrute"
    return df[OUTPUT_COLUMNS]


def build_cleaned_dataset():
    marocannonces_df = build_marocannonces_frame()
    rekrute_df = build_rekrute_frame()

    dataset = pd.concat([marocannonces_df, rekrute_df], ignore_index=True).fillna("")
    dataset = dataset.drop_duplicates(
        subset=["titre", "entreprise", "localisation", "source"],
        keep="first",
    )
    return dataset


def main():
    dataset = build_cleaned_dataset()
    dataset.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"cleaned_offres.csv genere: {OUTPUT_PATH}")
    print(f"Lignes: {len(dataset)}")
    print(f"Sources: {dataset['source'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
