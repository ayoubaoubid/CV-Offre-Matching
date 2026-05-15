from data_engine.preprocessing.final_dataset_builder import main as build_final_dataset
from data_engine.preprocessing.text_cleaner import main as build_cleaned_offres
from data_engine.preprocessing.tfidf_vectorizer import train_tfidf
from data_engine.preprocessing.dbscan_clustering import main as run_dbscan_clustering


def main():
    print("Etape 1/4 - Construction de cleaned_offres.csv")
    build_cleaned_offres()

    print("\nEtape 2/4 - Construction de final_dataset.csv")
    build_final_dataset()

    print("\nEtape 3/4 - Entrainement du vectorizer TF-IDF")
    train_tfidf()

    print("\nEtape 4/4 - Clustering DBSCAN")
    run_dbscan_clustering()

    print("\nPipeline termine avec succes.")


if __name__ == "__main__":
    main()
