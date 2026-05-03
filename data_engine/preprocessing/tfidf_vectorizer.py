import pandas as pd
import spacy
import re
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("cleaned_offres.csv").fillna("")

# =========================
# SPACY
# =========================
nlp = spacy.load("fr_core_news_sm")

# =========================
# BAD WORDS FILTER
# =========================
BAD_WORDS = {"acros", "casanca", "action", "activité"}

# =========================
# CLEAN RAW TEXT
# =========================
def clean_raw_text(text):
    text = str(text).lower()
    text = re.sub(r'\d+', ' ', text)
    text = re.sub(r'[^a-zA-ZÀ-ÿ\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# =========================
# TOKEN FILTER
# =========================
def is_valid_token(token):
    lemma = token.lemma_.lower()

    return (
        token.is_alpha
        and not token.is_stop
        and len(lemma) > 3
        and len(lemma) <= 20
        and lemma.isalpha()
        and lemma not in BAD_WORDS
    )

# =========================
# PREPROCESS
# =========================
def preprocess(text):
    if not text or text.strip() == "":
        return ""

    doc = nlp(text.lower())

    tokens = [
        token.lemma_.lower()
        for token in doc
        if is_valid_token(token)
    ]

    return " ".join(tokens)

# =========================
# TEXT BUILD
# =========================
df["text_clean"] = (
    df["titre"].astype(str) + " " +
    df["competences"].astype(str) + " " +
    df["secteur"].astype(str)
)

df["text_clean"] = df["text_clean"].apply(clean_raw_text)
df["text_clean"] = df["text_clean"].apply(preprocess)

# =========================
# SAVE DATASET
# =========================
df.to_csv("final_dataset.csv", index=False)

# =========================
# TF-IDF
# =========================
vectorizer = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1,2),
    min_df=4,
    max_df=0.9,
    token_pattern=r'(?u)\b[a-zA-ZÀ-ÿ]{4,}\b'
)

X = vectorizer.fit_transform(df["text_clean"])

# =========================
# FILTER FEATURES
# =========================
features = np.array(vectorizer.get_feature_names_out())

mask = [
    len(f.split()) <= 2 and len(f) > 3
    for f in features
]

X = X[:, mask]
features = features[mask]

# =========================
# SAVE
# =========================
joblib.dump(vectorizer, "tfidf_vectorizer.pkl")
joblib.dump(X, "tfidf_matrix.pkl")

# =========================
# DEBUG
# =========================
print("Shape TF-IDF:", X.shape)
print("Top Features:", features[:20])