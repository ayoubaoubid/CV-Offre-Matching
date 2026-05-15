import api from "./api";

export const saveJob = (jobId) => {
  return api.post(`/jobs/save/${jobId}/`);
};

export const getSavedJobs = () => {
  return api.get("/jobs/saved/");
};

export const removeSavedJob = (jobId) => {
  return api.delete(`/jobs/save/${jobId}/`);
};