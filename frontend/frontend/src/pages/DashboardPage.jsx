import { useEffect, useState } from "react";
import { getJobs } from "../services/jobService";
import JobCard from "../components/JobCard";
import { useNavigate } from "react-router-dom";

export default function DashboardPage() {
  const [jobs, setJobs] = useState([]);
  const [search, setSearch] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    getJobs().then((res) => setJobs(res.data));
  }, []);

  const filtered = jobs.filter((j) =>
    j.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="container mt-4">
      <h2 className="text-center">Dashboard</h2>

      <div className="text-center">
        <input className="form-control w-50 mx-auto"
          placeholder="Search job..."
          onChange={(e) => setSearch(e.target.value)} />

        <button className="btn btn-primary mt-2" onClick={() => navigate("/results")}>
          View Matching
        </button>
      </div>

      <div className="row mt-3">
        {filtered.map((job) => (
          <div className="col-md-4" key={job.id}>
            <JobCard job={job} />
          </div>
        ))}
      </div>
    </div>
  );
}