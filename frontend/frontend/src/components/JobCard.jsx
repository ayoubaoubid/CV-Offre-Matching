import { useState } from "react";

export default function JobCard({ job }) {
  const [saved, setSaved] = useState(false);

  return (
    <div className="card p-3 m-2 shadow">
      <h5>{job.title}</h5>
      <p>{job.company}</p>
      <p>{job.location}</p>

      <span className="badge bg-primary">Score: {job.score}%</span>

      <button
        className={`btn mt-2 ${saved ? "btn-danger" : "btn-outline-primary"}`}
        onClick={() => setSaved(!saved)}
      >
        {saved ? "Saved ❤️" : "Save 🤍"}
      </button>
    </div>
  );
}