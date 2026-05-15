import { useContext, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { AuthContext } from "../context/AuthContext";
import { getJobCandidates, getRecruiterJob } from "../services/recruiterService";


export default function RecruiterCandidatesPage() {
  const { user, authReady } = useContext(AuthContext);
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!authReady) {
      return;
    }
    if (!user) {
      navigate("/");
      return;
    }
    if (user.role !== "admin") {
      navigate("/dashboard");
      return;
    }

    let isMounted = true;
    const loadCandidates = async () => {
      try {
        const [jobResponse, candidatesResponse] = await Promise.all([
          getRecruiterJob(jobId),
          getJobCandidates(jobId),
        ]);
        if (isMounted) {
          setJob(jobResponse.data);
          setCandidates(candidatesResponse.data);
        }
      } catch {
        if (isMounted) {
          setError("Impossible de charger les candidats compatibles.");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadCandidates();
    return () => {
      isMounted = false;
    };
  }, [authReady, jobId, navigate, user]);

  if (!authReady || loading) {
    return <div className="page-frame py-5"><p>Chargement...</p></div>;
  }

  return (
    <div className="app-page">
      <div className="page-frame">
        <section className="dashboard-hero mb-4">
          <div>
            <span className="section-tag">Matching recruteur</span>
            <h2 className="mb-3">{job?.title}</h2>
            <p className="text-muted mb-0">Candidats compatibles avec cette offre.</p>
          </div>
          <button className="btn btn-outline-primary" onClick={() => navigate("/recruiter/jobs")}>
            Retour aux offres
          </button>
        </section>

        {error ? <p className="text-danger">{error}</p> : null}

        <div className="row g-3">
          {candidates.map((candidate, index) => (
            <div className="col-lg-6" key={candidate.id}>
              <div className="surface-card info-card h-100">
                <div className="d-flex justify-content-between align-items-start gap-3">
                  <div>
                    <h5>{index + 1}. {candidate.name}</h5>
                    <p className="text-muted mb-1">{candidate.email}</p>
                    <p className="small mb-2">{candidate.title || "Titre non renseigne"} - {candidate.location || "Ville non renseignee"}</p>
                  </div>
                  <span className="badge bg-success">{candidate.score}%</span>
                </div>
                <p className="mb-2"><strong>Experience:</strong> {candidate.experience_years} an(s)</p>
                <p className="mb-2"><strong>Raison:</strong> {candidate.reason}</p>
                <div className="skill-cloud mb-3">
                  {candidate.skills.slice(0, 8).map((skill) => (
                    <span className="skill-pill" key={skill}>{skill}</span>
                  ))}
                </div>
                <div className="d-flex gap-2 flex-wrap">
                  <a className="btn btn-outline-primary btn-sm" href={`mailto:${candidate.email}`}>
                    Contacter
                  </a>
                  <button className="btn btn-outline-dark btn-sm" type="button">
                    Inviter a postuler
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {!candidates.length ? <p className="text-muted">Aucun candidat compatible trouve.</p> : null}
      </div>
    </div>
  );
}
