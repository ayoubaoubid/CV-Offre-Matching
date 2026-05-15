import API from "./api";


function normalizeJob(job) {
  return {
    id: job.id,
    title: job.title ?? "",
    company: job.company ?? "",
    sector: job.sector ?? "",
    location: job.location ?? "",
    contractType: job.contract_type ?? "",
    description: job.description ?? "",
    experienceRequired: job.experience_required ?? 0,
    salary: job.salary ?? "",
    status: job.status ?? "",
    expiresAt: job.expires_at ?? "",
    createdAt: job.created_at ?? "",
    requiredSkills: job.required_skills ?? job.skills ?? [],
    applicationsCount: job.applications_count ?? 0,
  };
}


export async function getRecruiterDashboard() {
  return API.get("/jobs/recruiter/dashboard/");
}


export async function getRecruiterJobs(params = {}) {
  const response = await API.get("/jobs/recruiter/jobs/", { params });
  return {
    ...response,
    data: Array.isArray(response.data) ? response.data.map(normalizeJob) : [],
  };
}


export async function getRecruiterJob(jobId) {
  const response = await API.get(`/jobs/recruiter/jobs/${jobId}/`);
  return {
    ...response,
    data: normalizeJob(response.data),
  };
}


export async function createRecruiterJob(data) {
  return API.post("/jobs/recruiter/jobs/", data);
}


export async function updateRecruiterJob(jobId, data) {
  return API.put(`/jobs/recruiter/jobs/${jobId}/`, data);
}


export async function deleteRecruiterJob(jobId) {
  return API.delete(`/jobs/recruiter/jobs/${jobId}/`);
}


export async function updateRecruiterJobStatus(jobId, status) {
  return API.patch(`/jobs/recruiter/jobs/${jobId}/status/`, { status });
}


export async function getJobCandidates(jobId) {
  return API.get(`/jobs/recruiter/jobs/${jobId}/candidates/`);
}


export async function inviteCandidateToApply(jobId, candidateId) {
  return API.post(`/jobs/recruiter/jobs/${jobId}/candidates/${candidateId}/invite/`);
}


export async function getRecruiterApplications(params = {}) {
  return API.get("/matching/recruiter/applications/", { params });
}


export async function updateApplicationStatus(applicationId, data) {
  return API.patch(`/matching/recruiter/applications/${applicationId}/status/`, data);
}


export async function getCompanyProfile() {
  return API.get("/users/company-profile/");
}


export async function updateCompanyProfile(data) {
  return API.put("/users/company-profile/", data);
}
