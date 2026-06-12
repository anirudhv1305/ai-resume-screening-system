import { useState } from "react";

import { getResumeDownloadUrl } from "../api/client";

function clampScore(value) {
  return Math.max(0, Math.min(Number(value) || 0, 100));
}

function ProgressBar({ label, value }) {
  const score = clampScore(value);
  return (
    <div className="progress-metric">
      <div className="metric-row">
        <span>{label}</span>
        <strong>{score.toFixed(1)}</strong>
      </div>
      <div className="progress-track" aria-hidden="true">
        <span style={{ width: `${score}%` }} />
      </div>
    </div>
  );
}

function SkillList({ items, emptyText, tone = "neutral" }) {
  if (!items?.length) {
    return <p className="muted-text">{emptyText}</p>;
  }

  return (
    <div className="skill-list">
      {items.map((skill) => (
        <span key={skill} className={`skill-token ${tone}`}>
          {skill}
        </span>
      ))}
    </div>
  );
}

export default function CandidateDetailPanel({ candidate, activeJob, busy, onDeleteResume }) {
  const [deleting, setDeleting] = useState(false);

  async function handleDelete() {
    if (!candidate) return;
    setDeleting(true);
    try {
      await onDeleteResume(candidate.candidate_id);
    } finally {
      setDeleting(false);
    }
  }

  if (!candidate) {
    return (
      <aside className="detail-panel empty-detail" aria-label="Candidate details">
        <p className="surface-label">Candidate Detail</p>
        <h2>No candidate selected</h2>
        <p className="muted-text">Screening details will appear here.</p>
      </aside>
    );
  }

  return (
    <aside className="detail-panel" aria-label="Candidate details">
      <div className="detail-header">
        <div>
          <p className="surface-label">Candidate Detail</p>
          <h2>{candidate.candidate_name || candidate.filename}</h2>
          <span>{candidate.email || candidate.filename}</span>
        </div>
        <strong className="detail-score">{candidate.match_score.toFixed(1)}</strong>
      </div>

      <div className="detail-actions">
        <a
          className="small-button ghost"
          href={getResumeDownloadUrl(candidate.candidate_id)}
          target="_blank"
          rel="noreferrer"
        >
          Download
        </a>
        <button
          className="small-button danger"
          type="button"
          disabled={busy || deleting}
          onClick={handleDelete}
        >
          {deleting ? "Deleting..." : "Delete"}
        </button>
      </div>

      <section className="detail-section">
        <h3>Score breakdown</h3>
        <ProgressBar label="Skills" value={candidate.skill_score} />
        <ProgressBar label="Semantic" value={candidate.semantic_score} />
        <ProgressBar label="Experience" value={candidate.experience_score} />
      </section>

      <section className="detail-section">
        <h3>Matched skills</h3>
        <SkillList
          items={candidate.matched_skills}
          emptyText="No direct skill overlap was detected."
          tone="matched"
        />
      </section>

      <section className="detail-section">
        <h3>Missing skills</h3>
        <SkillList
          items={candidate.missing_skills}
          emptyText="No required skills are currently marked missing."
          tone="missing"
        />
      </section>

      <section className="detail-section">
        <h3>Explanation</h3>
        <ul className="explanation-list">
          {candidate.explanation?.length ? (
            candidate.explanation.map((item) => <li key={item}>{item}</li>)
          ) : (
            <li>No explanation was returned for this ranking.</li>
          )}
        </ul>
      </section>

      <dl className="profile-meta">
        <div>
          <dt>Job</dt>
          <dd>{activeJob?.title || "Not selected"}</dd>
        </div>
        <div>
          <dt>Experience</dt>
          <dd>{candidate.experience_years.toFixed(1)} years</dd>
        </div>
        <div>
          <dt>Phone</dt>
          <dd>{candidate.phone || "Not detected"}</dd>
        </div>
      </dl>
    </aside>
  );
}
