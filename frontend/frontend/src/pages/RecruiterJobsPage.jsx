import { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AuthContext } from "../context/AuthContext";
import {
  deleteRecruiterJob,
  getRecruiterJobs,
  updateRecruiterJobStatus,
} from "../services/recruiterService";


export default function RecruiterJobsPage() {
  const { user, authReady } = useContext(AuthContext);
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const loadJobs = async ({ showLoading = true } = {}) => {
    if (showLoading) {
      setLoading(true);
    }
    try {
      const response = await getRecruiterJobs(statusFilter ? { status: statusFilter } : {});
      setJobs(response.data);
      setError("");
    } catch {
      setError("Impossible de charger vos offres.");
    } finally {
      setLoading(false);
    }
  };

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
    const loadInitialJobs = async () => {
      try {
        const response = await getRecruiterJobs(statusFilter ? { status: statusFilter } : {});
        if (isMounted) {
          setJobs(response.data);
          setError("");
        }
      } catch {
        if (isMounted) {
          setError("Impossible de charger vos offres.");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadInitialJobs();
    return () => {
      isMounted = false;
    };
  }, [authReady, navigate, statusFilter, user]);

  const changeStatus = async (jobId, status) => {
    await updateRecruiterJobStatus(jobId, status);
    loadJobs({ showLoading: false });
  };

  const removeJob = async (jobId) => {
    await deleteRecruiterJob(jobId);
    loadJobs({ showLoading: false });
  };

  if (!authReady) {
    return <div className="page-frame py-5"><p>Chargement...</p></div>;
  }

  return (
    <div className="app-page">
      <div className="page-frame">
        <section className="dashboard-hero mb-4">
          <div>
            <span className="section-tag">Offres recruteur</span>
            <h2 className="mb-3">Mes offres</h2>
            <p className="text-muted mb-0">Creez, modifiez et suivez vos offres d'emploi.</p>
          </div>
          <button className="btn btn-success" onClick={() => navigate("/recruiter/jobs/new")}>
            Ajouter une offre
          </button>
        </section>

        <div className="surface-card filter-panel mb-4">
          <select className="form-select" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            <option value="">Tous les statuts</option>
            <option value="open">Actives</option>
            <option value="draft">Brouillons</option>
            <option value="closed">Fermees</option>
          </select>
        </div>

        {error ? <p className="text-danger">{error}</p> : null}
        {loading ? <p>Chargement des offres...</p> : null}

        <div className="row g-3">
          {jobs.map((job) => (
            <div className="col-lg-6" key={job.id}>
              <div className="surface-card job-card">
                <div className="d-flex justify-content-between gap-3">
                  <div>
                    <h5>{job.title}</h5>
                    <p className="text-muted mb-1">{job.company}</p>
                    <p className="small mb-2">{job.location || "Localisation non renseignee"} - {job.contractType || "Contrat non renseigne"}</p>
                  </div>
                  <span className="job-badge">{job.status}</span>
                </div>
                <p className="small text-muted">{job.description?.slice(0, 180)}{job.description?.length > 180 ? "..." : ""}</p>
                <p className="small mb-2">Candidatures: {job.applicationsCount}</p>
                <div className="d-flex flex-wrap gap-2 mt-auto">
                  <button className="btn btn-outline-primary btn-sm" onClick={() => navigate(`/recruiter/jobs/${job.id}/edit`)}>
                    Modifier
                  </button>
                  <button className="btn btn-outline-primary btn-sm" onClick={() => navigate(`/recruiter/jobs/${job.id}/candidates`)}>
                    Candidats
                  </button>
                  <button className="btn btn-outline-dark btn-sm" onClick={() => changeStatus(job.id, job.status === "open" ? "closed" : "open")}>
                    {job.status === "open" ? "Fermer" : "Activer"}
                  </button>
                  <button className="btn btn-outline-danger btn-sm" onClick={() => removeJob(job.id)}>
                    Supprimer
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
