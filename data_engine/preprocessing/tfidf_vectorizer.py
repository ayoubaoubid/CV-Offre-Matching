from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR.parent / "models"
FINAL_DATASET_PATH = BASE_DIR / "final_dataset.csv"
VECTORIZER_PATH = MODELS_DIR / "tfidf_vectorizer.pkl"
MATRIX_PATH = MODELS_DIR / "tfidf_matrix.pkl"


def build_vectorizer():
    return TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.9,
        token_pattern=r"(?u)\b[a-zA-ZÀ-ÿ]{3,}\b",
    )


def train_tfidf():
    df = pd.read_csv(FINAL_DATASET_PATH).fillna("")
    vectorizer = build_vectorizer()
    matrix = vectorizer.fit_transform(df["text_clean"])

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    joblib.dump(matrix, MATRIX_PATH)

    print(f"Vectorizer sauvegarde: {VECTORIZER_PATH}")
    print(f"Matrice TF-IDF sauvegardee: {MATRIX_PATH}")
    print(f"Shape TF-IDF: {matrix.shape}")


if __name__ == "__main__":
    train_tfidf()
