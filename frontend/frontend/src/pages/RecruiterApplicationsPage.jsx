import { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AuthContext } from "../context/AuthContext";
import {
  getRecruiterApplications,
  updateApplicationStatus,
} from "../services/recruiterService";


const STATUS_OPTIONS = [
  ["pending", "En attente"],
  ["reviewed", "Vue"],
  ["interview", "Entretien"],
  ["accepted", "Acceptee"],
  ["rejected", "Refusee"],
];


export default function RecruiterApplicationsPage() {
  const { user, authReady } = useContext(AuthContext);
  const navigate = useNavigate();
  const [applications, setApplications] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const loadApplications = async ({ showLoading = true } = {}) => {
    if (showLoading) {
      setLoading(true);
    }
    try {
      const response = await getRecruiterApplications(
        statusFilter ? { status: statusFilter } : {}
      );
      setApplications(response.data);
      setError("");
    } catch {
      setError("Impossible de charger les candidatures.");
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
    const loadInitialApplications = async () => {
      try {
        const response = await getRecruiterApplications(
          statusFilter ? { status: statusFilter } : {}
        );
        if (isMounted) {
          setApplications(response.data);
          setError("");
        }
      } catch {
        if (isMounted) {
          setError("Impossible de charger les candidatures.");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadInitialApplications();
    return () => {
      isMounted = false;
    };
  }, [authReady, navigate, statusFilter, user]);

  const changeStatus = async (applicationId, nextStatus) => {
    await updateApplicationStatus(applicationId, { status: nextStatus });
    loadApplications({ showLoading: false });
  };

  if (!authReady) {
    return <div className="page-frame py-5"><p>Chargement...</p></div>;
  }

  return (
    <div className="app-page">
      <div className="page-frame">
        <section className="dashboard-hero mb-4">
          <div>
            <span className="section-tag">Candidatures</span>
            <h2 className="mb-3">Candidatures recues</h2>
            <p className="text-muted mb-0">Analysez et traitez les candidatures de vos offres.</p>
          </div>
        </section>

        <div className="surface-card filter-panel mb-4">
          <select className="form-select" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            <option value="">Tous les statuts</option>
            {STATUS_OPTIONS.map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </div>

        {error ? <p className="text-danger">{error}</p> : null}
        {loading ? <p>Chargement des candidatures...</p> : null}

        <div className="surface-card info-card">
          <div className="table-responsive">
            <table className="table align-middle">
              <thead>
                <tr>
                  <th>Candidat</th>
                  <th>Offre</th>
                  <th>Score</th>
                  <th>Statut</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {applications.map((application) => (
                  <tr key={application.id}>
                    <td>
                      <strong>{application.candidate_name}</strong>
                      <div className="small text-muted">{application.candidate_email}</div>
                    </td>
                    <td>{application.job_title}</td>
                    <td>{application.matching_score}%</td>
                    <td>{application.status}</td>
                    <td>
                      <select
                        className="form-select form-select-sm"
                        value={application.status}
                        onChange={(event) => changeStatus(application.id, event.target.value)}
                      >
                        {STATUS_OPTIONS.map(([value, label]) => (
                          <option key={value} value={value}>{label}</option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!applications.length && !loading ? (
            <p className="text-muted mb-0">Aucune candidature trouvee.</p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
