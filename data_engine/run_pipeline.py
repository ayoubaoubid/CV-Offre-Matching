from data_engine.preprocessing.final_dataset_builder import main as build_final_dataset
from data_engine.preprocessing.text_cleaner import main as build_cleaned_offres
from data_engine.preprocessing.tfidf_vectorizer import train_tfidf


def main():
    print("Etape 1/3 - Construction de cleaned_offres.csv")
    build_cleaned_offres()

    print("\nEtape 2/3 - Construction de final_dataset.csv")
    build_final_dataset()

    print("\nEtape 3/3 - Entrainement du vectorizer TF-IDF")
    train_tfidf()

    print("\nPipeline termine avec succes.")


if __name__ == "__main__":
    main()
