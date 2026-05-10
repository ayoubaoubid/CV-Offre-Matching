import { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import JobCard from "../components/JobCard";
import { AuthContext } from "../context/AuthContext";
import { getRecommendations } from "../services/matchingService";


export default function ResultsPage() {
  const { user, authReady } = useContext(AuthContext);
  const navigate = useNavigate();
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (authReady && !user) {
      navigate("/");
    }
  }, [authReady, navigate, user]);

  useEffect(() => {
    if (!authReady || !user) {
      return;
    }

    let isMounted = true;

    const fetchData = async () => {
      setIsLoading(true);
      setErrorMessage("");

      try {
        const data = await getRecommendations();
        if (isMounted) {
          setResults(data);
        }
      } catch (error) {
        if (isMounted) {
          setErrorMessage(
            error.response?.data?.message || "Impossible de charger les recommandations."
          );
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchData();

    return () => {
      isMounted = false;
    };
  }, [authReady, user]);

  if (!authReady || !user) {
    return <div className="page-frame py-5"><p>Chargement...</p></div>;
  }

  return (
    <div className="app-page">
      <div className="page-frame">
        <section className="dashboard-hero mb-4">
          <div>
            <span className="section-tag">Matching</span>
            <h2 className="mb-2">Resultats de matching</h2>
            <p className="text-muted mb-0">
              Les offres les plus proches du profil candidat apparaissent ici.
            </p>
          </div>
        </section>

        {errorMessage ? (
          <div className="alert alert-warning mt-3" role="alert">
            {errorMessage}
          </div>
        ) : null}

        {isLoading ? <p className="text-muted mt-3">Chargement des recommandations...</p> : null}

        {!isLoading && !errorMessage && results.length === 0 ? (
          <p className="text-muted mt-3">Aucune recommandation disponible pour le moment.</p>
        ) : null}

        <div className="row mt-3">
          {!isLoading && results.map((job) => (
            <div className="col-md-6 col-lg-4 mb-3" key={job.id}>
              <JobCard job={job} />
            </div>
          ))}
        </div>

        <div className="surface-card info-card mt-4">
          <h4>Visualisation</h4>
          <p className="mb-0 text-muted">
            Cette zone peut accueillir ensuite le radar des skills, le nuage de mots,
            la distribution des scores et la visualisation des clusters.
          </p>
        </div>
      </div>
    </div>
  );
}
