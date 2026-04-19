import { useState } from "react";
import API from "../services/api";

export default function CVUploader() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);

  const uploadCV = async () => {
    if (!file) return alert("Please select a file");

    const formData = new FormData();
    formData.append("cv", file);

    setLoading(true);

    try {
      await API.post("/upload-cv/", formData);

      // 🔥 simulation feature extraction (IMPORTANT DATA MINING STEP)
      console.log("TF-IDF + NLP extraction triggered...");

      alert("CV uploaded & analyzed!");
    } catch (err) {
      alert("Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mt-4 text-center">

      <h2>📄 Upload CV</h2>

      <input
        type="file"
        className="form-control w-50 mx-auto mt-3"
        onChange={(e) => setFile(e.target.files[0])}
      />

      <button
        className="btn btn-success mt-3"
        onClick={uploadCV}
        disabled={loading}
      >
        {loading ? "Uploading..." : "Upload CV"}
      </button>

      <hr />

      {/* 🔥 FORMULE DATA MINING (EXPLICATION VISUELLE) */}
      <div className="alert alert-info mt-3">
        <b>Matching Formula:</b><br />
        Score = 0.5 × Cosine Similarity + 0.25 × Jaccard + 0.15 × Experience Match + 0.10 × Geo Match
      </div>

    </div>
  );
}