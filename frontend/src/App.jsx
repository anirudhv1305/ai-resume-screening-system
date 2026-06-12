import { startTransition, useDeferredValue, useEffect, useMemo, useState } from "react";

import {
  deleteResume,
  fetchCandidates,
  fetchJobs,
  fetchRankings,
  processResumes,
  uploadJob,
  uploadResumes,
} from "./api/client";
import CandidateDetailPanel from "./components/CandidateDetailPanel";
import CandidateTable from "./components/CandidateTable";
import Sidebar from "./components/Sidebar";

export default function App() {
  const [jobs, setJobs] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [rankings, setRankings] = useState([]);
  const [activeJobId, setActiveJobId] = useState(null);
  const [skillFilter, setSkillFilter] = useState("");
  const [appliedSkillFilter, setAppliedSkillFilter] = useState("");
  const [busy, setBusy] = useState(false);
  const [loadingRankings, setLoadingRankings] = useState(false);
  const [selectedCandidateId, setSelectedCandidateId] = useState(null);
  const [message, setMessage] = useState("System ready. Add a job description to begin.");

  // Defer large ranking list updates so filtering and uploads feel responsive.
  const deferredRankings = useDeferredValue(rankings);
  const activeJob = jobs.find((job) => job.id === activeJobId) || null;
  const scoreStats = useMemo(() => {
    if (!deferredRankings.length) {
      return { averageScore: null, topScore: null };
    }

    const scores = deferredRankings.map((candidate) => Number(candidate.match_score) || 0);
    const total = scores.reduce((sum, score) => sum + score, 0);
    return {
      averageScore: total / scores.length,
      topScore: Math.max(...scores),
    };
  }, [deferredRankings]);
  const selectedCandidate = useMemo(
    () =>
      deferredRankings.find((candidate) => candidate.candidate_id === selectedCandidateId) ||
      deferredRankings[0] ||
      null,
    [deferredRankings, selectedCandidateId]
  );

  useEffect(() => {
    async function loadInitialData() {
      setBusy(true);
      try {
        const [jobData, candidateData] = await Promise.all([
          fetchJobs(),
          fetchCandidates(),
        ]);
        setJobs(jobData);
        setCandidates(candidateData);
        if (jobData.length) {
          setActiveJobId(jobData[0].id);
        }
      } catch (error) {
        setMessage(resolveError(error, "Failed to load the dashboard."));
      } finally {
        setBusy(false);
      }
    }

    loadInitialData();
  }, []);

  useEffect(() => {
    if (!activeJobId) {
      setRankings([]);
      return;
    }

    async function loadRankings() {
      setLoadingRankings(true);
      try {
        const response = await fetchRankings(activeJobId, appliedSkillFilter);
        startTransition(() => setRankings(response.rankings));
      } catch (error) {
        setMessage(resolveError(error, "Failed to load rankings."));
      } finally {
        setLoadingRankings(false);
      }
    }

    loadRankings();
  }, [activeJobId, appliedSkillFilter]);

  useEffect(() => {
    if (!deferredRankings.length) {
      setSelectedCandidateId(null);
      return;
    }

    const selectedStillExists = deferredRankings.some(
      (candidate) => candidate.candidate_id === selectedCandidateId
    );
    if (!selectedStillExists) {
      setSelectedCandidateId(deferredRankings[0].candidate_id);
    }
  }, [deferredRankings, selectedCandidateId]);

  async function handleCreateJob(payload) {
    setBusy(true);
    try {
      const response = await uploadJob(payload);
      setJobs((currentJobs) => [response.job, ...currentJobs]);
      setActiveJobId(response.job.id);
      setMessage(`Job "${response.job.title}" saved and ready for screening.`);
      return true;
    } catch (error) {
      setMessage(resolveError(error, "Unable to upload the job description."));
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function handleResumeUpload(files) {
    setBusy(true);
    try {
      const response = await uploadResumes(files);
      setCandidates((currentCandidates) => [
        ...response.candidates,
        ...currentCandidates,
      ]);
      setMessage(`${response.uploaded_count} resume(s) uploaded and parsed successfully.`);
      return true;
    } catch (error) {
      setMessage(resolveError(error, "Unable to upload one or more resumes."));
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function handleProcess() {
    if (!activeJobId) {
      setMessage("Choose or create a job description before processing resumes.");
      return;
    }

    setBusy(true);
    setLoadingRankings(true);
    try {
      const payload = {
        job_id: activeJobId,
        candidate_ids: candidates.map((candidate) => candidate.id),
      };
      const response = await processResumes(payload);
      startTransition(() => setRankings(response.rankings));
      const refreshedCandidates = await fetchCandidates();
      setCandidates(refreshedCandidates);
      setMessage(
        `Processed ${response.processed_count} candidate(s) for ${activeJob?.title || "the active job"}.`
      );
      return true;
    } catch (error) {
      setMessage(resolveError(error, "Resume processing failed."));
      return false;
    } finally {
      setBusy(false);
      setLoadingRankings(false);
    }
  }

  async function handleDeleteResume(resumeId) {
    setBusy(true);
    try {
      const response = await deleteResume(resumeId);
      setCandidates((currentCandidates) =>
        currentCandidates.filter((candidate) => candidate.id !== resumeId)
      );
      startTransition(() =>
        setRankings((currentRankings) =>
          currentRankings.filter((candidate) => candidate.candidate_id !== resumeId)
        )
      );
      setMessage(response.message);
      return true;
    } catch (error) {
      setMessage(resolveError(error, "Unable to delete the selected resume."));
      return false;
    } finally {
      setBusy(false);
    }
  }

  function handleApplyFilter() {
    setAppliedSkillFilter(skillFilter.trim());
  }

  function handleResetFilter() {
    setSkillFilter("");
    setAppliedSkillFilter("");
  }

  return (
    <div className="ats-shell">
      <Sidebar
        jobs={jobs}
        activeJobId={activeJobId}
        onSelectJob={setActiveJobId}
        onCreateJob={handleCreateJob}
        onUploadResumes={handleResumeUpload}
        onProcess={handleProcess}
        busy={busy}
        candidateCount={candidates.length}
        rankedCount={deferredRankings.length}
        averageScore={scoreStats.averageScore}
        message={loadingRankings ? "Analyzing candidates..." : message}
      />

      <main className="candidate-workspace" aria-label="Candidate rankings">
        <CandidateTable
          rankings={deferredRankings}
          loading={loadingRankings}
          activeJob={activeJob}
          skillFilter={skillFilter}
          setSkillFilter={setSkillFilter}
          onApplyFilter={handleApplyFilter}
          onResetFilter={handleResetFilter}
          selectedCandidateId={selectedCandidate?.candidate_id || null}
          onSelectCandidate={setSelectedCandidateId}
          averageScore={scoreStats.averageScore}
          topScore={scoreStats.topScore}
          candidateCount={candidates.length}
        />
      </main>

      <CandidateDetailPanel
        key={selectedCandidate?.candidate_id || "empty-detail"}
        candidate={selectedCandidate}
        activeJob={activeJob}
        busy={busy}
        onDeleteResume={handleDeleteResume}
      />
    </div>
  );
}

function resolveError(error, fallbackMessage) {
  return error?.response?.data?.detail || fallbackMessage;
}
