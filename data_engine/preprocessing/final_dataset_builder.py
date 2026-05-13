from pathlib import Path

import pandas as pd
from spacy.lang.fr.stop_words import STOP_WORDS

from data_engine.preprocessing.skill_extractor import get_nlp
from data_engine.utils.text_utils import clean_raw_text_for_nlp, join_unique_parts


BASE_DIR = Path(__file__).resolve().parent
CLEANED_PATH = BASE_DIR / "cleaned_offres.csv"
FINAL_PATH = BASE_DIR / "final_dataset.csv"
BAD_WORDS = {"acros", "casanca", "action", "activite"}


def is_valid_token(token):
    lemma = token.lemma_.lower()
    return (
        token.is_alpha
        and lemma not in STOP_WORDS
        and len(lemma) > 2
        and len(lemma) <= 25
        and lemma.isalpha()
        and lemma not in BAD_WORDS
    )


def preprocess_text(text):
    cleaned_text = clean_raw_text_for_nlp(text)
    if not cleaned_text:
        return ""

    doc = get_nlp()(cleaned_text)
    tokens = [token.lemma_.lower() for token in doc if is_valid_token(token)]
    return " ".join(tokens)


def build_text_for_matching(row):
    return join_unique_parts(
        [
            row.get("titre", ""),
            row.get("competences", ""),
            row.get("secteur", ""),
            row.get("description", ""),
        ]
    )


def build_final_dataset():
    df = pd.read_csv(CLEANED_PATH).fillna("")
    df["text_for_matching"] = df.apply(build_text_for_matching, axis=1)
    df["text_clean"] = df["text_for_matching"].apply(preprocess_text)
    df = df[df["titre"].astype(str).str.strip() != ""].copy()
    return df


def main():
    dataset = build_final_dataset()
    dataset.to_csv(FINAL_PATH, index=False, encoding="utf-8")
    print(f"final_dataset.csv genere: {FINAL_PATH}")
    print(f"Lignes: {len(dataset)}")


if __name__ == "__main__":
    main()
