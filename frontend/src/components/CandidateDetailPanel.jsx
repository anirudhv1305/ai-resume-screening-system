import { useState } from "react";

import { getResumeDownloadUrl } from "../api/client";

function clampScore(value) {
  return Math.max(0, Math.min(Number(value) || 0, 100));
}

function getRecommendationStyle(recommendation) {
  if (!recommendation) return "moderate";
  const lower = recommendation.toLowerCase();
  if (lower.includes("strong")) return "strong";
  if (lower.includes("weak")) return "weak";
  return "moderate";
}

function CircularScore({ score }) {
  const clamped = clampScore(score);
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clamped / 100) * circumference;
  
  return (
    <div className="circular-score">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke="#e0e8e5"
          strokeWidth="8"
        />
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke="#167f68"
          strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 70 70)"
        />
      </svg>
      <div className="score-overlay">
        <strong>{clamped.toFixed(1)}</strong>
        <span>Match</span>
      </div>
    </div>
  );
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
      {items.map((skill, idx) => (
        <span key={`${skill}-${idx}`} className={`skill-token ${tone}`}>
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

  const recommendationStyle = getRecommendationStyle(candidate.recommendation);

  return (
    <aside className="detail-panel" aria-label="Candidate details">
      <div className="detail-header">
        <div>
          <p className="surface-label">Candidate Detail</p>
          <h2>{candidate.candidate_name || candidate.filename}</h2>
          <span>{candidate.email || candidate.filename}</span>
        </div>
        <CircularScore score={candidate.match_score} />
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

      {candidate.recommendation && (
        <section className="detail-section recommendation-section">
          <h3>Recommendation</h3>
          <div className={`recommendation-card recommendation-${recommendationStyle}`}>
            <strong>{candidate.recommendation}</strong>
            {candidate.recommendation_reason && (
              <p>{candidate.recommendation_reason}</p>
            )}
          </div>
        </section>
      )}

      <section className="detail-section">
        <h3>Score Breakdown</h3>
        <div className="score-grid">
          <div className="score-card">
            <span className="score-label">Skills Match</span>
            <strong className="score-value">{clampScore(candidate.skill_score).toFixed(1)}</strong>
            <div className="mini-progress">
              <span style={{ width: `${clampScore(candidate.skill_score)}%` }} />
            </div>
          </div>
          <div className="score-card">
            <span className="score-label">Keywords Match</span>
            <strong className="score-value">{clampScore(candidate.keyword_score || 0).toFixed(1)}</strong>
            <div className="mini-progress">
              <span style={{ width: `${clampScore(candidate.keyword_score || 0)}%` }} />
            </div>
          </div>
          <div className="score-card">
            <span className="score-label">Experience Match</span>
            <strong className="score-value">{clampScore(candidate.experience_score).toFixed(1)}</strong>
            <div className="mini-progress">
              <span style={{ width: `${clampScore(candidate.experience_score)}%` }} />
            </div>
          </div>
          <div className="score-card">
            <span className="score-label">Education Match</span>
            <strong className="score-value">{clampScore(candidate.education_score || 0).toFixed(1)}</strong>
            <div className="mini-progress">
              <span style={{ width: `${clampScore(candidate.education_score || 0)}%` }} />
            </div>
          </div>
          <div className="score-card">
            <span className="score-label">Qualification Match</span>
            <strong className="score-value">{clampScore(candidate.qualification_score || 0).toFixed(1)}</strong>
            <div className="mini-progress">
              <span style={{ width: `${clampScore(candidate.qualification_score || 0)}%` }} />
            </div>
          </div>
          <div className="score-card">
            <span className="score-label">Semantic Match</span>
            <strong className="score-value">{clampScore(candidate.semantic_score).toFixed(1)}</strong>
            <div className="mini-progress">
              <span style={{ width: `${clampScore(candidate.semantic_score)}%` }} />
            </div>
          </div>
        </div>
      </section>

      <section className="detail-section">
        <h3>Skills Analysis</h3>
        <div className="analysis-subsection">
          <h4>Matched Skills</h4>
          <SkillList
            items={candidate.matched_skills}
            emptyText="No direct skill overlap detected."
            tone="matched"
          />
        </div>
        <div className="analysis-subsection">
          <h4>Missing Skills</h4>
          <SkillList
            items={candidate.missing_skills}
            emptyText="No missing skills identified."
            tone="missing"
          />
        </div>
      </section>

      <section className="detail-section">
        <h3>Keywords Analysis</h3>
        <div className="analysis-subsection">
          <h4>Matched Keywords</h4>
          <SkillList
            items={candidate.matched_keywords}
            emptyText="No matching keywords found."
            tone="matched"
          />
        </div>
        <div className="analysis-subsection">
          <h4>Missing Keywords</h4>
          <SkillList
            items={candidate.missing_keywords}
            emptyText="No missing keywords identified."
            tone="missing"
          />
        </div>
      </section>

      <section className="detail-section">
        <h3>Qualifications Analysis</h3>
        <div className="analysis-subsection">
          <h4>Matched Qualifications</h4>
          <SkillList
            items={candidate.matched_qualifications}
            emptyText="No matching qualifications found."
            tone="matched"
          />
        </div>
        <div className="analysis-subsection">
          <h4>Missing Qualifications</h4>
          <SkillList
            items={candidate.missing_qualifications}
            emptyText="No missing qualifications identified."
            tone="missing"
          />
        </div>
      </section>

      {candidate.ai_suggestions?.length > 0 && (
        <section className="detail-section ai-section">
          <h3>AI Suggestions</h3>
          <div className="ai-card">
            <ul className="ai-list">
              {candidate.ai_suggestions.map((suggestion, idx) => (
                <li key={idx}>{suggestion}</li>
              ))}
            </ul>
          </div>
        </section>
      )}

      {candidate.improvements?.length > 0 && (
        <section className="detail-section ai-section">
          <h3>Improvement Recommendations</h3>
          <div className="ai-card">
            <ul className="ai-list">
              {candidate.improvements.map((improvement, idx) => (
                <li key={idx}>{improvement}</li>
              ))}
            </ul>
          </div>
        </section>
      )}

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
