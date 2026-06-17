import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api",
});

export async function fetchJobs() {
  const { data } = await apiClient.get("/jobs");
  return data;
}

export async function fetchCandidates() {
  const { data } = await apiClient.get("/resumes");
  return data;
}

export async function deleteResume(resumeId) {
  const { data } = await apiClient.delete(`/resume/${resumeId}`);
  return data;
}

export function getResumeDownloadUrl(resumeId) {
  return `${apiClient.defaults.baseURL}/resume/${resumeId}/download`;
}

export async function uploadJob({ title, description, file }) {
  const formData = new FormData();
  formData.append("title", title);
  if (description) {
    formData.append("description", description);
  }
  if (file) {
    formData.append("file", file);
  }

  const { data } = await apiClient.post("/jobs/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function uploadResumes(files) {
  const formData = new FormData();
  Array.from(files).forEach((file) => formData.append("files", file));

  const { data } = await apiClient.post("/resumes/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function matchResumes({ job_description, title, candidate_ids }) {
  const { data } = await apiClient.post("/screening/match", {
    job_description,
    title,
    candidate_ids,
  });
  return data;
}

export async function fetchRankings(jobId, skill) {
  const params = {};
  if (skill) {
    params.skill = skill;
  }
  const { data } = await apiClient.get(`/screening/rankings/${jobId}`, { params });
  return data;
}
