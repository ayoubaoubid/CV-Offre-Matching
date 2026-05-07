import { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import JobCard from "../components/JobCard";
import { AuthContext } from "../context/AuthContext";
import { getMatchingResults } from "../services/matchingService";


export default function ResultsPage() {
  const { user, authReady } = useContext(AuthContext);
  const navigate = useNavigate();
  const [results, setResults] = useState([]);

  useEffect(() => {
    if (authReady && !user) {
      navigate("/");
    }
  }, [authReady, navigate, user]);

  useEffect(() => {
    if (!authReady || !user) {
      return;
    }

    getMatchingResults().then((response) => setResults(response.data));
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

        <div className="row mt-3">
          {results.map((job) => (
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
