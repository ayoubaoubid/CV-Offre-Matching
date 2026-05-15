import API from "./api";


export async function applyToJob(jobId) {
  return API.post(`/matching/applications/${jobId}/`);
}
