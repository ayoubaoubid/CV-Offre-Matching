# Ancienne implementation conservee en commentaire pour ne pas perdre le travail precedent.
#
# import pandas as pd
# import numpy as np
# import os
# import joblib
# import matplotlib.pyplot as plt
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.cluster import DBSCAN
# from sklearn.decomposition import PCA
#
# # =====================================================================
# # CONFIGURATION DES CHEMINS (RELATIFS AU SCRIPT)
# # =====================================================================
# SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
#
# DATASET_PATH = os.path.join(SCRIPT_DIR, "final_dataset.csv")
# MODELS_DIR = os.path.join(PROJECT_DIR, "models")
# CLUSTERING_DIR = os.path.join(PROJECT_DIR, "clustering")
#
# os.makedirs(MODELS_DIR, exist_ok=True)
# os.makedirs(CLUSTERING_DIR, exist_ok=True)
#
# BAD_WORDS = {
#     "lancer", "maroc", "emploi", "poste", "profil", "candidat", "recrutement",
#     "recrute", "recherche", "rejoindre", "equipe", "groupe", "societe", "entreprise",
#     "offre", "annonce", "https", "www", "html", "avoir", "faire", "etre", "notre",
#     "votre", "salaire", "discuter", "discuté", "négocier", "avoir", "expérience",
#     "diplome", "diplômé", "bac", "bacc", "baccalauréat", "domaine", "domaines",
# }
#
# def main():
#     print("═══════════════════════════════════════════════════════")
#     print(" ÉTAPE 1 — CHARGEMENT DU DATASET")
#     print("═══════════════════════════════════════════════════════")
#
#     if not os.path.exists(DATASET_PATH):
#         print(f"[ERREUR] Le fichier {DATASET_PATH} n'existe pas.")
#         return
#
#     df = pd.read_csv(DATASET_PATH)
#     print(f"-> Dataset chargé avec succès : {len(df)} offres.")
#
#     if "text_clean" not in df.columns:
#         print("[ERREUR] La colonne 'text_clean' est absente du dataset.")
#         return
#
#     df = df.dropna(subset=["text_clean"]).reset_index(drop=True)
#
#     print("\n═══════════════════════════════════════════════════════")
#     print(" ÉTAPE 2 — CHARGEMENT DU VECTORIZER TF-IDF ET DE LA MATRICE EXISTANTS")
#     print("═══════════════════════════════════════════════════════")
#
#     vectorizer_path = os.path.join(MODELS_DIR, "tfidf_vectorizer.pkl")
#     matrix_path = os.path.join(MODELS_DIR, "tfidf_matrix.pkl")
#
#     if not os.path.exists(vectorizer_path):
#         print(f"[ERREUR] Le fichier vectorizer n'existe pas : {vectorizer_path}")
#         return
#     if not os.path.exists(matrix_path):
#         print(f"[ERREUR] Le fichier matrice TF-IDF n'existe pas : {matrix_path}")
#         return
#
#     vectorizer = joblib.load(vectorizer_path)
#     tfidf_matrix = joblib.load(matrix_path)
#
#     print(f"-> Vectorizer chargé depuis : {vectorizer_path}")
#     print(f"-> Matrice TF-IDF chargée depuis : {matrix_path}")
#     print(f"-> Shape de la matrice TF-IDF : {tfidf_matrix.shape}")
#
#     print("\n═══════════════════════════════════════════════════════")
#     print(" ÉTAPE 3 — CLUSTERING DBSCAN")
#     print("═══════════════════════════════════════════════════════")
#
#     eps_optimal = 0.6
#     min_samples = 2
#
#     print(f"Application de DBSCAN (eps={eps_optimal}, min_samples={min_samples}, metric='cosine')...")
#     dbscan = DBSCAN(eps=eps_optimal, min_samples=min_samples, metric='cosine')
#
#     df["cluster_dbscan"] = dbscan.fit_predict(tfidf_matrix)
#
#     print("-> Distribution des clusters :")
#     cluster_counts = df["cluster_dbscan"].value_counts().sort_index()
#     for cluster_id, count in cluster_counts.items():
#         if cluster_id == -1:
#             print(f"  Bruit (Outliers, label -1) : {count} offres")
#         else:
#             print(f"  Cluster {cluster_id} : {count} offres")
#
#     print("\n═══════════════════════════════════════════════════════")
#     print(" ÉTAPE 4 — VISUALISATION PCA ET SAUVEGARDE")
#     print("═══════════════════════════════════════════════════════")
#
#     print("Réduction de dimensionnalité via PCA (2D)...")
#     pca = PCA(n_components=2, random_state=42)
#     reduced_features = pca.fit_transform(tfidf_matrix.toarray())
#
#     plt.figure(figsize=(10, 7))
#
#     bruit = df["cluster_dbscan"] == -1
#     vrais_clusters = df["cluster_dbscan"] != -1
#
#     plt.scatter(
#         reduced_features[bruit, 0],
#         reduced_features[bruit, 1],
#         c="lightgray",
#         label="Bruit (-1)",
#         alpha=0.5,
#         s=15
#     )
#
#     scatter = plt.scatter(
#         reduced_features[vrais_clusters, 0],
#         reduced_features[vrais_clusters, 1],
#         c=df.loc[vrais_clusters, "cluster_dbscan"],
#         cmap="tab10",
#         alpha=0.8,
#         s=25
#     )
#
#     plt.colorbar(scatter, label="Cluster DBSCAN")
#     plt.title("Visualisation des clusters DBSCAN")
#     plt.xlabel("Composante PCA 1")
#     plt.ylabel("Composante PCA 2")
#     plt.legend()
#     plt.show()
#
#     # pca_plot_path = os.path.join(SCRIPT_DIR, "dbscan_clusters_visualization.png")
#     # plt.savefig(pca_plot_path)
#     # plt.close()
#     # print(f"-> Visualisation sauvegardée dans : {pca_plot_path}")
#     #
#     # clustered_path = os.path.join(CLUSTERING_DIR, "dbscan_clustered_offres.csv")
#     # df.to_csv(clustered_path, index=False, encoding="utf-8")
#     # print(f"-> Dataset avec clusters sauvegardé dans : {clustered_path}")
#     #
#     # dbscan_model_path = os.path.join(MODELS_DIR, "dbscan_model.pkl")
#     # joblib.dump(dbscan, dbscan_model_path)
#     # print(f"-> Modèle DBSCAN sauvegardé dans : {dbscan_model_path}")
#
# if __name__ == "__main__":
#     main()

from pathlib import Path

import joblib
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA


# Use a non-interactive backend so the script works from terminals and Code Runner.
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

EPS_OPTIMAL = 0.6
MIN_SAMPLES = 3


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
        eps=EPS_OPTIMAL,
        min_samples=MIN_SAMPLES,
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
        f"Applying DBSCAN with eps={EPS_OPTIMAL}, "
        f"min_samples={MIN_SAMPLES}, metric='cosine'"
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
