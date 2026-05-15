import { useState } from "react";
import { applyToJob } from "../services/applicationService";
import { saveJob } from "../services/savedService";

export default function JobCard({ job }) {
  const [saved, setSaved] = useState(false);
  const [applyMessage, setApplyMessage] = useState("");
  const [applying, setApplying] = useState(false);

  const handleSave = async () => {
    try {
      await saveJob(job.id);
      setSaved(true);
    } catch (err) {
      console.error(err);
    }
  };

  const handleApply = async () => {
    setApplying(true);
    setApplyMessage("");
    try {
      const response = await applyToJob(job.id);
      setApplyMessage(response.data?.message || "Candidature envoyee.");
    } catch (error) {
      setApplyMessage(error.response?.data?.message || "Candidature impossible.");
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="surface-card job-card h-100">
      <div className="job-card__header">
        <h5 className="mb-2">{job.title}</h5>
        <div className="d-flex align-items-center gap-2">
          {job.contractType ? <span className="job-badge">{job.contractType}</span> : null}
          {job.score !== undefined && job.score !== null ? (
            <span className="badge bg-success">Score: {job.score}%</span>
          ) : null}
        </div>
      </div>

      <p className="mb-1 fw-semibold">{job.company || "Entreprise non renseignee"}</p>
      <p className="mb-1 text-muted">{job.location || "Localisation non renseignee"}</p>

      {job.sector ? <p className="mb-2">Secteur: {job.sector}</p> : null}

      <p className="small text-muted flex-grow-1 job-card__text">
        {job.description
          ? `${job.description.slice(0, 180)}${job.description.length > 180 ? "..." : ""}`
          : "Description non disponible"}
      </p>

      <div className="d-flex gap-2 flex-wrap mt-2">
        <button
          className={`btn ${saved ? "btn-danger" : "btn-outline-primary"}`}
          onClick={handleSave}
        >
          {saved ? "Saved" : "Save"}
        </button>
        <button className="btn btn-primary" onClick={handleApply} disabled={applying}>
          {applying ? "Envoi..." : "Postuler"}
        </button>
      </div>
      {applyMessage ? <p className="small text-success mb-0 mt-2">{applyMessage}</p> : null}
    </div>
  );
}
