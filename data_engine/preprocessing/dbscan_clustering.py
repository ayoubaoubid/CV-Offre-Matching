from pathlib import Path

import joblib
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA

matplotlib.use("Agg")


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

DATASET_PATH = SCRIPT_DIR / "final_dataset.csv"
MODELS_DIR = PROJECT_DIR / "models"
CLUSTERING_DIR = PROJECT_DIR / "clustering"

SOURCE_VECTORIZER_PATH = MODELS_DIR / "tfidf_vectorizer.pkl"
SOURCE_MATRIX_PATH = MODELS_DIR / "tfidf_matrix.pkl"
DBSCAN_VECTORIZER_PATH = MODELS_DIR / "tfidf_vectorizer_dbscan_now.pkl"
DBSCAN_MODEL_PATH = MODELS_DIR / "dbscan_model_now.pkl"
CLUSTERED_DATASET_PATH = CLUSTERING_DIR / "dbscan_clustered_offres_new.csv"
PLOT_PATH = CLUSTERING_DIR / "dbscan_clusters_visualization.png"

eps_optimal = 0.6
min_samples = 3


def ensure_directories():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    CLUSTERING_DIR.mkdir(parents=True, exist_ok=True)


def load_dataset():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset introuvable: {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)
    if "text_clean" not in df.columns:
        raise ValueError("La colonne 'text_clean' est absente du dataset.")

    df = df.dropna(subset=["text_clean"]).reset_index(drop=True)
    return df


def load_vectorizer_and_matrix():
    if not SOURCE_VECTORIZER_PATH.exists():
        raise FileNotFoundError(f"Vectorizer introuvable: {SOURCE_VECTORIZER_PATH}")
    if not SOURCE_MATRIX_PATH.exists():
        raise FileNotFoundError(f"Matrice TF-IDF introuvable: {SOURCE_MATRIX_PATH}")

    vectorizer = joblib.load(SOURCE_VECTORIZER_PATH)
    tfidf_matrix = joblib.load(SOURCE_MATRIX_PATH)
    return vectorizer, tfidf_matrix


def run_dbscan(tfidf_matrix):
    model = DBSCAN(
        eps=eps_optimal,
        min_samples=min_samples,
        metric="cosine",
    )
    labels = model.fit_predict(tfidf_matrix)
    return model, labels


def build_plot(tfidf_matrix, labels):
    reduced_features = PCA(n_components=2, random_state=42).fit_transform(
        tfidf_matrix.toarray()
    )

    plt.figure(figsize=(10, 7))
    noise_mask = labels == -1
    cluster_mask = labels != -1

    plt.scatter(
        reduced_features[noise_mask, 0],
        reduced_features[noise_mask, 1],
        c="lightgray",
        label="Noise (-1)",
        alpha=0.5,
        s=15,
    )

    scatter = plt.scatter(
        reduced_features[cluster_mask, 0],
        reduced_features[cluster_mask, 1],
        c=labels[cluster_mask],
        cmap="tab10",
        alpha=0.8,
        s=25,
    )

    plt.colorbar(scatter, label="DBSCAN Cluster")
    plt.title("DBSCAN clusters")
    plt.xlabel("PCA component 1")
    plt.ylabel("PCA component 2")
    plt.legend()
    plt.tight_layout()
    plt.savefig(PLOT_PATH)
    plt.close()


def print_cluster_distribution(labels):
    counts = pd.Series(labels).value_counts().sort_index()
    print("Cluster distribution:")
    for cluster_id, count in counts.items():
        if cluster_id == -1:
            print(f"  Noise (-1): {count} offers")
        else:
            print(f"  Cluster {cluster_id}: {count} offers")


def main():
    ensure_directories()

    print("=" * 60)
    print("STEP 1 - LOAD DATASET")
    print("=" * 60)
    df = load_dataset()
    print(f"Dataset loaded: {len(df)} offers")

    print("\n" + "=" * 60)
    print("STEP 2 - LOAD TF-IDF VECTORIZER AND MATRIX")
    print("=" * 60)
    vectorizer, tfidf_matrix = load_vectorizer_and_matrix()
    print(f"Vectorizer loaded from: {SOURCE_VECTORIZER_PATH}")
    print(f"TF-IDF matrix loaded from: {SOURCE_MATRIX_PATH}")
    print(f"TF-IDF matrix shape: {tfidf_matrix.shape}")

    if len(df) != tfidf_matrix.shape[0]:
        raise ValueError(
            "Le nombre de lignes du dataset ne correspond pas a la matrice TF-IDF. "
            f"dataset={len(df)}, matrix={tfidf_matrix.shape[0]}"
        )

    print("\n" + "=" * 60)
    print("STEP 3 - RUN DBSCAN")
    print("=" * 60)
    print(
        f"Applying DBSCAN with eps={eps_optimal}, "
        f"min_samples={min_samples}, metric='cosine'"
    )
    dbscan_model, labels = run_dbscan(tfidf_matrix)
    df["cluster_dbscan"] = labels
    print_cluster_distribution(labels)

    print("\n" + "=" * 60)
    print("STEP 4 - SAVE OUTPUTS")
    print("=" * 60)

    df.to_csv(CLUSTERED_DATASET_PATH, index=False, encoding="utf-8")
    print(f"Clustered dataset saved to: {CLUSTERED_DATASET_PATH}")

    joblib.dump(vectorizer, DBSCAN_VECTORIZER_PATH)
    print(f"DBSCAN vectorizer saved to: {DBSCAN_VECTORIZER_PATH}")
          
    joblib.dump(dbscan_model, DBSCAN_MODEL_PATH)
    print(f"DBSCAN model saved to: {DBSCAN_MODEL_PATH}")

    build_plot(tfidf_matrix, labels)
    print(f"Cluster plot saved to: {PLOT_PATH}")

    print("\nDBSCAN pipeline completed successfully.")


if __name__ == "__main__":
    main()
