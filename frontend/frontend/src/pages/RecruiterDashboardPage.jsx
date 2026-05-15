import { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AuthContext } from "../context/AuthContext";
import { getRecruiterDashboard } from "../services/recruiterService";


export default function RecruiterDashboardPage() {
  const { user, authReady } = useContext(AuthContext);
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
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
    const loadDashboard = async () => {
      try {
        const response = await getRecruiterDashboard();
        if (isMounted) {
          setStats(response.data);
        }
      } catch {
        if (isMounted) {
          setError("Impossible de charger le dashboard recruteur.");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadDashboard();
    return () => {
      isMounted = false;
    };
  }, [authReady, navigate, user]);

  if (!authReady || loading) {
    return <div className="page-frame py-5"><p>Chargement...</p></div>;
  }

  return (
    <div className="app-page">
      <div className="page-frame">
        <section className="dashboard-hero mb-4">
          <div>
            <span className="section-tag">Recruteur</span>
            <h2 className="mb-3">Dashboard recruteur</h2>
            <p className="text-muted mb-0">
              Suivez vos offres, candidatures et candidats compatibles.
            </p>
          </div>
          <button className="btn btn-success" onClick={() => navigate("/recruiter/jobs/new")}>
            Nouvelle offre
          </button>
        </section>

        {error ? <p className="text-danger">{error}</p> : null}

        <div className="row g-3 mb-4">
          {[
            ["Offres publiees", stats?.total_offers ?? 0],
            ["Offres actives", stats?.active_offers ?? 0],
            ["Brouillons", stats?.draft_offers ?? 0],
            ["Candidatures", stats?.total_applications ?? 0],
            ["Candidats recommandes", stats?.recommended_candidates ?? 0],
            ["Score moyen", `${stats?.average_matching_score ?? 0}%`],
          ].map(([label, value]) => (
            <div className="col-md-4 col-lg-2" key={label}>
              <div className="surface-card info-card h-100 text-center">
                <strong className="fs-4 d-block">{value}</strong>
                <span className="text-muted small">{label}</span>
              </div>
            </div>
          ))}
        </div>

        <div className="surface-card info-card">
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h5 className="mb-0">Dernieres candidatures</h5>
            <button className="btn btn-outline-primary btn-sm" onClick={() => navigate("/recruiter/applications")}>
              Tout voir
            </button>
          </div>
          {stats?.latest_applications?.length ? (
            <div className="table-responsive">
              <table className="table align-middle">
                <thead>
                  <tr>
                    <th>Candidat</th>
                    <th>Offre</th>
                    <th>Score</th>
                    <th>Statut</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.latest_applications.map((application) => (
                    <tr key={application.id}>
                      <td>{application.candidate_name}</td>
                      <td>{application.job_title}</td>
                      <td>{application.score}%</td>
                      <td>{application.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-muted mb-0">Aucune candidature recue pour le moment.</p>
          )}
        </div>
      </div>
    </div>
  );
}
