import pandas as pd
import joblib
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("../preprocessing/cleaned_offres.csv")
X = joblib.load("../preprocessing/tfidf_matrix.pkl")

# =========================
# FIND OPTIMAL K
# =========================
scores = []

for k in range(2, 10):
    model = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = model.fit_predict(X)
    score = silhouette_score(X, labels)
    scores.append(score)

optimal_k = range(2, 10)[scores.index(max(scores))]
print("Optimal K:", optimal_k)

# =========================
# FINAL MODEL
# =========================
kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
df["cluster"] = kmeans.fit_predict(X)

df.to_csv("clustered_offres.csv", index=False)

# save model
joblib.dump(kmeans, "kmeans_model.pkl")

# =========================
# PCA REDUCTION
# =========================
pca = PCA(n_components=2)
X_2d = pca.fit_transform(X.toarray())

# =========================
# PLOT CLUSTERS
# =========================
plt.figure(figsize=(10, 6))

scatter = plt.scatter(
    X_2d[:, 0],
    X_2d[:, 1],
    c=df["cluster"],
    cmap="tab10",
    alpha=0.7
)

plt.title("Job Clusters Visualization (PCA)")
plt.xlabel("PCA 1")
plt.ylabel("PCA 2")

plt.colorbar(scatter)
plt.show()