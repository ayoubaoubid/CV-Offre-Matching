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
      <h2 className="text-center">Matching Results</h2>

      <div className="row">
        {results.map((job) => (
          <div className="col-md-4" key={job.id}>
            <JobCard job={job} />
          </div>
        ))}
      </div>
    </div>
  );
}