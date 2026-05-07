import API from "./api";

function normalizeJob(job) {
  return {
    id: job.id,
    title: job.title ?? "",
    company: job.company ?? "",
    location: job.location ?? "",
    sector: job.sector ?? "",
    contractType: job.contract_type ?? "",
    description: job.description ?? "",
    clusterNumber: job.cluster_number,
    publishedAt: job.published_at,
    createdAt: job.created_at,
    status: job.status ?? "",
  };
}

export async function getJobs() {
  const response = await API.get("/jobs/");
  return {
    ...response,
    data: Array.isArray(response.data)
      ? response.data.map(normalizeJob)
      : [],
  };
}
