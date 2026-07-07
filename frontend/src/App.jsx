import { useCallback, useEffect, useRef, useState } from "react";
import { Route, Routes } from "react-router-dom";

import {
  deleteResume,
  fetchCandidates,
  fetchJobs,
  matchResumes,
  uploadJob,
  uploadResumes,
} from "./api/client";
import Layout from "./components/Layout";
import ToastContainer from "./components/Toast";
import DashboardPage from "./pages/DashboardPage";
import ResumesPage from "./pages/ResumesPage";
import JobsPage from "./pages/JobsPage";
import ScreeningPage from "./pages/ScreeningPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import SettingsPage from "./pages/SettingsPage";

export default function App() {
  const [jobs, setJobs] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [rankings, setRankings] = useState([]);
  const [activeJobId, setActiveJobId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [screening, setScreening] = useState(false);
  const [toasts, setToasts] = useState([]);
  const toastId = useRef(0);

  const toast = useCallback((message, type = "info") => {
    const id = ++toastId.current;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  }, []);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  useEffect(() => {
    async function init() {
      setLoading(true);
      try {
        const [jobData, candidateData] = await Promise.all([fetchJobs(), fetchCandidates()]);
        setJobs(jobData);
        setCandidates(candidateData);
        if (jobData.length) setActiveJobId(jobData[0].id);
      } catch {
        toast("Failed to load dashboard data.", "error");
      } finally {
        setLoading(false);
      }
    }
    init();
  }, [toast]);

  const activeJob = jobs.find((j) => j.id === activeJobId) || null;

  async function handleCreateJob(payload) {
    try {
      const res = await uploadJob(payload);
      setJobs((prev) => [res.job, ...prev]);
      setActiveJobId(res.job.id);
      toast(`Job "${res.job.title}" created successfully.`, "success");
      return res.job;
    } catch (err) {
      toast(resolveError(err, "Failed to create job."), "error");
      return null;
    }
  }

  async function handleUploadResumes(files) {
    try {
      const res = await uploadResumes(files);
      setCandidates((prev) => [...res.candidates, ...prev]);
      toast(`${res.uploaded_count} resume(s) uploaded successfully.`, "success");
      return true;
    } catch (err) {
      toast(resolveError(err, "Failed to upload resumes."), "error");
      return false;
    }
  }

  async function handleRunScreening(jobId, candidateIds) {
    const job = jobs.find((j) => j.id === jobId);
    if (!job?.description_text) {
      toast("Job has no description text. Re-save the job first.", "error");
      return null;
    }
    setScreening(true);
    try {
      const res = await matchResumes({
        job_description: job.description_text,
        title: job.title,
        candidate_ids: candidateIds,
      });
      setRankings(res.rankings);
      setActiveJobId(jobId);
      toast(`Screened ${res.total_candidates} candidate(s) successfully.`, "success");
      return res.rankings;
    } catch (err) {
      toast(resolveError(err, "Screening failed."), "error");
      return null;
    } finally {
      setScreening(false);
    }
  }

  async function handleDeleteResume(resumeId) {
    try {
      const res = await deleteResume(resumeId);
      setCandidates((prev) => prev.filter((c) => c.id !== resumeId));
      setRankings((prev) => prev.filter((r) => r.candidate_id !== resumeId));
      toast(res.message || "Resume deleted.", "success");
      return true;
    } catch (err) {
      toast(resolveError(err, "Failed to delete resume."), "error");
      return false;
    }
  }

  const sharedProps = {
    jobs,
    candidates,
    rankings,
    activeJob,
    activeJobId,
    setActiveJobId,
    loading,
    screening,
    onCreateJob: handleCreateJob,
    onUploadResumes: handleUploadResumes,
    onRunScreening: handleRunScreening,
    onDeleteResume: handleDeleteResume,
    toast,
  };

  return (
    <>
      <Layout loading={loading}>
        <Routes>
          <Route path="/" element={<DashboardPage {...sharedProps} />} />
          <Route path="/resumes" element={<ResumesPage {...sharedProps} />} />
          <Route path="/jobs" element={<JobsPage {...sharedProps} />} />
          <Route path="/screening" element={<ScreeningPage {...sharedProps} />} />
          <Route path="/analytics" element={<AnalyticsPage {...sharedProps} />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </Layout>
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </>
  );
}

function resolveError(err, fallback) {
  return err?.response?.data?.detail || fallback;
}
