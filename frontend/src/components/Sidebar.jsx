import { useState } from "react";

export default function Sidebar({
  jobs,
  activeJobId,
  onSelectJob,
  onCreateJob,
  onUploadResumes,
  onProcess,
  busy,
  candidateCount,
  rankedCount,
  averageScore,
  message,
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [jobFile, setJobFile] = useState(null);
  const [resumeFiles, setResumeFiles] = useState([]);

  async function handleJobSubmit(event) {
    event.preventDefault();
    const success = await onCreateJob({ title, description, file: jobFile });
    if (success) {
      setTitle("");
      setDescription("");
      setJobFile(null);
      event.target.reset();
    }
  }

  async function handleResumeSubmit(event) {
    event.preventDefault();
    if (!resumeFiles.length) return;
    const success = await onUploadResumes(resumeFiles);
    if (success) {
      setResumeFiles([]);
      event.target.reset();
    }
  }

  return (
    <aside className="sidebar" aria-label="Screening navigation">
      <div className="brand-lockup">
        <span className="brand-mark">AI</span>
        <div>
          <strong>Resume Screening ATS</strong>
          <span>Recruiter command center</span>
        </div>
      </div>

      <nav className="side-nav" aria-label="Workspace sections">
        <a href="#upload-resumes">
          <span className="nav-icon upload" />
          Upload Resumes
        </a>
        <a href="#job-description">
          <span className="nav-icon job" />
          Job Description
        </a>
        <a href="#candidate-table">
          <span className="nav-icon candidates" />
          Candidates
        </a>
      </nav>

      <section id="upload-resumes" className="sidebar-section">
        <h2>Upload Resumes</h2>
        <form className="side-form" onSubmit={handleResumeSubmit}>
          <label>
            Resume PDFs
            <input
              required
              type="file"
              multiple
              accept=".pdf"
              onChange={(event) => setResumeFiles(Array.from(event.target.files || []))}
            />
          </label>
          <p className="file-count">{resumeFiles.length} file(s) queued</p>
          <button className="primary-button" type="submit" disabled={busy}>
            Upload resumes
          </button>
        </form>
      </section>

      <section id="job-description" className="sidebar-section">
        <h2>Job Description</h2>
        <label>
          Active job
          <select
            value={activeJobId || ""}
            onChange={(event) => onSelectJob(Number(event.target.value) || null)}
          >
            <option value="">Choose a job</option>
            {jobs.map((job) => (
              <option key={job.id} value={job.id}>
                {job.title}
              </option>
            ))}
          </select>
        </label>

        <form className="side-form" onSubmit={handleJobSubmit}>
          <label>
            Job title
            <input
              required
              type="text"
              value={title}
              placeholder="Senior Python Developer"
              onChange={(event) => setTitle(event.target.value)}
            />
          </label>

          <label>
            Description
            <textarea
              rows="5"
              value={description}
              placeholder="Responsibilities, skills, and experience expectations"
              onChange={(event) => setDescription(event.target.value)}
            />
          </label>

          <label>
            Optional job file
            <input
              type="file"
              accept=".pdf,.txt"
              onChange={(event) => setJobFile(event.target.files?.[0] || null)}
            />
          </label>

          <button className="primary-button" type="submit" disabled={busy}>
            Save job
          </button>
        </form>
      </section>

      <section id="candidate-table" className="sidebar-section">
        <h2>Candidates</h2>
        <div className="pipeline-stats" aria-label="Pipeline summary">
          <span>
            <strong>{candidateCount}</strong>
            Uploaded
          </span>
          <span>
            <strong>{rankedCount}</strong>
            Ranked
          </span>
          <span>
            <strong>{averageScore === null ? "--" : averageScore.toFixed(1)}</strong>
            Avg score
          </span>
        </div>
        <button
          className="primary-button full-width"
          type="button"
          onClick={onProcess}
          disabled={busy || !activeJobId}
        >
          Run screening
        </button>
      </section>

      <div className="system-message" role="status">
        <span className={busy ? "status-light busy" : "status-light"} />
        <p>{message}</p>
      </div>
    </aside>
  );
}
