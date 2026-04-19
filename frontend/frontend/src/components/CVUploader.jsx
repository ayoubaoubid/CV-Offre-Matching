import { useState } from "react";
import API from "../services/api";

export default function CVUploader() {
  const [file, setFile] = useState(null);

  const uploadCV = async () => {
    const formData = new FormData();
    formData.append("cv", file);

    try {
      await API.post("/upload-cv/", formData);
      alert("CV uploaded!");
    } catch {
      alert("Upload failed");
    }
  };

  return (
    <div>
      <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      <button onClick={uploadCV}>Upload CV</button>
    </div>
  );
}