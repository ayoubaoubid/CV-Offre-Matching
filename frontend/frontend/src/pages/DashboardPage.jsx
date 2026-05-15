import { useContext, useDeferredValue, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import JobCard from "../components/JobCard";
import { AuthContext } from "../context/AuthContext";
import { getJobs } from "../services/jobService";


const REFRESH_INTERVAL_MS = 5000;
const PAGE_SIZE = 30;


export default function DashboardPage() {
  const { user, authReady } = useContext(AuthContext);
  const [jobs, setJobs] = useState([]);
  const [search, setSearch] = useState("");
  const [locationFilter, setLocationFilter] = useState("");
  const [contractFilter, setContractFilter] = useState("");
  const [pageState, setPageState] = useState({
    filterKey: "",
    page: 1,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const deferredSearch = useDeferredValue(search);

  useEffect(() => {
    if (authReady && !user) {
      navigate("/");
    }
  }, [authReady, navigate, user]);

  useEffect(() => {
    if (!authReady || !user) {
      return undefined;
    }

    let isMounted = true;

    const loadJobs = async ({ silent = false } = {}) => {
      if (!silent && isMounted) {
        setLoading(true);
      }

      try {
        const res = await getJobs();
        if (!isMounted) {
          return;
        }
        setJobs(res.data);
        setError("");
      } catch (fetchError) {
        if (!isMounted) {
          return;
        }
        if (!fetchError.response) {
          setError("Le backend Django n'est pas demarre ou n'est pas accessible sur http://127.0.0.1:8000.");
        } else {
          setError(`Erreur API /jobs/: ${fetchError.response.status}`);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadJobs();

    const intervalId = window.setInterval(() => {
      loadJobs({ silent: true });
    }, REFRESH_INTERVAL_MS);

    const handleFocus = () => {
      loadJobs({ silent: true });
    };

    window.addEventListener("focus", handleFocus);

    return () => {
      isMounted = false;
      window.clearInterval(intervalId);
      window.removeEventListener("focus", handleFocus);
    };
  }, [authReady, user]);

  const locationOptions = useMemo(
    () => [...new Set(jobs.map((job) => job.location).filter(Boolean))].sort(),
    [jobs]
  );

  const contractOptions = useMemo(
    () => [...new Set(jobs.map((job) => job.contractType).filter(Boolean))].sort(),
    [jobs]
  );

  const filteredJobs = useMemo(() => {
    const query = deferredSearch.trim().toLowerCase();

    return jobs
      .filter((job) => {
        const matchesSearch = !query || [
          job.title,
          job.company,
          job.location,
          job.sector,
          job.description,
        ]
          .filter(Boolean)
          .some((value) => value.toLowerCase().includes(query));

        const matchesLocation = !locationFilter || job.location === locationFilter;
        const matchesContract = !contractFilter || job.contractType === contractFilter;

        return matchesSearch && matchesLocation && matchesContract;
      })
      .sort((left, right) => {
        const leftDate = new Date(left.createdAt || left.publishedAt || 0).getTime();
        const rightDate = new Date(right.createdAt || right.publishedAt || 0).getTime();
        return rightDate - leftDate;
      });
  }, [contractFilter, deferredSearch, jobs, locationFilter]);

  const filterKey = `${search}|${locationFilter}|${contractFilter}`;
  const currentPage = pageState.filterKey === filterKey ? pageState.page : 1;
  const totalPages = Math.max(1, Math.ceil(filteredJobs.length / PAGE_SIZE));
  const safePage = Math.min(currentPage, totalPages);
  const pageStart = (safePage - 1) * PAGE_SIZE;
  const visibleJobs = filteredJobs.slice(pageStart, pageStart + PAGE_SIZE);

  const goToPage = (page) => {
    setPageState({
      filterKey,
      page: Math.min(Math.max(page, 1), totalPages),
    });
  };

  if (!authReady || !user) {
    return <div className="page-frame py-5"><p>Chargement...</p></div>;
  }

  return (
    <div className="app-page">
      <div className="page-frame">
        <section className="dashboard-hero mb-4">
          <div>
            <span className="section-tag">Offres</span>
            <h2 className="mb-3">Dashboard des offres</h2>
            <p className="text-muted mb-0">
              Recherche par mot-cle, ville et contrat, avec un espace candidat mieux structure.
            </p>
          </div>
          <div className="dashboard-hero__meta">
            <strong>{filteredJobs.length}</strong>
            <span>offres filtrees</span>
          </div>
        </section>

        <div className="surface-card filter-panel mb-4">
          <div className="row w-100 justify-content-center">
            <div className="col-lg-4 col-md-6 mb-2">
              <input
                className="form-control"
                placeholder="Recherche par titre, entreprise, lieu, secteur..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>
            <div className="col-lg-3 col-md-3 mb-2">
              <select className="form-select" value={locationFilter} onChange={(event) => setLocationFilter(event.target.value)}>
                <option value="">Toutes les villes</option>
                {locationOptions.map((location) => (
                  <option key={location} value={location}>{location}</option>
                ))}
              </select>
            </div>
            <div className="col-lg-3 col-md-3 mb-2">
              <select className="form-select" value={contractFilter} onChange={(event) => setContractFilter(event.target.value)}>
                <option value="">Tous les contrats</option>
                {contractOptions.map((contract) => (
                  <option key={contract} value={contract}>{contract}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-3 d-flex gap-2 flex-wrap">
            {user?.role === "candidate" ? (
              <button className="btn btn-success" onClick={() => navigate("/upload")}>
                Completer CV
              </button>
            ) : null}
            <button className="btn btn-primary" onClick={() => navigate("/results")}>
              Voir le matching
            </button>
            {user?.role === "candidate" ? (
              <button className="btn btn-outline-dark" onClick={() => navigate("/profile")}>
                Mon profil
              </button>
            ) : null}
          </div>
        </div>

        {!loading && !error ? (
          <p className="text-muted">
            {filteredJobs.length} offre{filteredJobs.length > 1 ? "s" : ""} trouvee{filteredJobs.length > 1 ? "s" : ""}
          </p>
        ) : null}

        {loading ? <p className="text-center">Chargement des offres...</p> : null}
        {error ? <p className="text-center text-danger">{error}</p> : null}

        {!loading && !error && filteredJobs.length === 0 ? (
          <p className="text-center text-muted">Aucune offre a afficher.</p>
        ) : null}

        <div className="row mt-4">
          {visibleJobs.map((job) => (
            <div className="col-md-6 col-lg-4 mb-3" key={job.id}>
              <JobCard job={job} />
            </div>
          ))}
        </div>

        {!loading && !error && filteredJobs.length > PAGE_SIZE ? (
          <div className="d-flex justify-content-center align-items-center gap-2 flex-wrap mt-3">
            <button
              className="btn btn-outline-primary"
              disabled={safePage === 1}
              onClick={() => goToPage(safePage - 1)}
            >
              Precedent
            </button>
            <span className="text-muted">
              Page {safePage} sur {totalPages}
            </span>
            <button
              className="btn btn-outline-primary"
              disabled={safePage === totalPages}
              onClick={() => goToPage(safePage + 1)}
            >
              Suivant
            </button>
          </div>
        ) : null}
      </div>
    </div>
  );
}
