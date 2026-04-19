import { useEffect, useState } from "react";
import { getMatchingResults } from "../services/matchingService";
import JobCard from "../components/JobCard";

export default function ResultsPage() {
  const [results, setResults] = useState([]);

  useEffect(() => {
    getMatchingResults().then((res) => setResults(res.data));
  }, []);

  return (
    <div className="container mt-4">

      <h2 className="text-center">🎯 Matching Results</h2>

      <div className="row mt-3">
        {results.map((job) => (
          <div className="col-md-4" key={job.id}>
            <JobCard job={job} />
          </div>
        ))}
      </div>

      {/* 📊 VISUALISATION SECTION */}
      <div className="mt-5 text-center">

        <h4>📊 Visualisation</h4>

        <div className="alert alert-secondary">
          🔹 Radar Chart (Skills vs Job) <br />
          🔹 WordCloud (Top Skills) <br />
          🔹 Score Distribution Graph <br />
          🔹 Clustering (K-Means Groups)
        </div>

      </div>

    </div>
  );
}