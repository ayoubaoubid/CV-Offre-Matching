import API from "./api";


function normalizeMatch(job) {
  return {
    ...job,
    contractType: job.contract_type ?? job.contractType ?? "",
    score: job.score ?? job.matching_score ?? 0,
  };
}


export async function getRecommendations() {
  const response = await API.get("/matching/recommendations/");
  return response.data.map(normalizeMatch);
}


export async function getMatchingResults() {
  return getRecommendations();
}
