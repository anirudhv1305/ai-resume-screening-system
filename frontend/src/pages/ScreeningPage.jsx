import { useEffect, useState } from "react";
import { CircularScore, RecommendationBadge, ScoreBadge, SkillChip, EmptyState, MiniBar } from "../components/UI";
import { getResumeDownloadUrl } from "../api/client";

const STAGES = [
  "Extracting PDF text",
  "Parsing resume content",
  "Extracting skills",
  "Keyword matching",
  "Qualification matching",
  "Semantic similarity",
  "AI analysis",
  "Final ranking",
];

export default function ScreeningPage({
  jobs, candidates, rankings, activeJobId, setActiveJobId,
  onRunScreening, screening,
}) {
  const [selectedJob, setSelectedJob] = useState(activeJobId || "");
  const [stage, setStage] = useState(0);
  const [selected, setSelected] = useState(null);
  const [hasRun, setHasRun] = useState(rankings.length > 0);

  // Sync hasRun when rankings arrive from parent (e.g. after navigation or refresh)
  useEffect(() => {
    if (rankings.length > 0) setHasRun(true);
  }, [rankings]);

  const activeRankings = rankings;

  async function handleRun() {
    if (!selectedJob) return;
    setStage(0);
    setHasRun(false);

    const interval = setInterval(() => {
      setStage((s) => {
        if (s >= STAGES.length - 1) { clearInterval(interval); return s; }
        return s + 1;
      });
    }, 400);

    const result = await onRunScreening(Number(selectedJob), candidates.map((c) => c.id));
    clearInterval(interval);
    setStage(STAGES.length - 1);
    if (result) setHasRun(true);
  }

  const selectedCandidate = selected
    ? activeRankings.find((r) => r.candidate_id === selected)
    : activeRankings[0] || null;

  return (
    <div className="page-screening">
      <div className="screening-controls section-card">
        <div className="section-card-header">
          <h2 className="section-card-title">Configure Screening</h2>
        </div>
        <div className="section-card-body screening-setup">
          <div className="form-group">
            <label className="form-label">Select Job Description</label>
            <select
              className="form-select"
              value={selectedJob}
              onChange={(e) => { setSelectedJob(e.target.value); setActiveJobId(Number(e.target.value) || null); }}
            >
              <option value="">Choose a job…</option>
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>{j.title}</option>
              ))}
            </select>
          </div>
          <div className="screening-info">
            <span className="meta-pill">{candidates.length} resumes available</span>
            {selectedJob && jobs.find((j) => j.id === Number(selectedJob)) && (
              <span className="meta-pill">
                {jobs.find((j) => j.id === Number(selectedJob))?.required_skills?.length || 0} required skills
              </span>
            )}
          </div>
          <button
            className="btn btn-primary btn-lg"
            disabled={!selectedJob || screening || candidates.length === 0}
            onClick={handleRun}
          >
            {screening ? "Screening…" : "▶ Run Screening"}
          </button>
        </div>

        {screening && (
          <div className="screening-progress">
            {STAGES.map((s, i) => (
              <div key={s} className={`stage-row ${i < stage ? "done" : i === stage ? "active" : "pending"}`}>
                <span className="stage-dot" />
                <span className="stage-label">{s}</span>
                {i < stage && <span className="stage-check">✓</span>}
                {i === stage && <span className="stage-spinner" />}
              </div>
            ))}
          </div>
        )}
      </div>

      {hasRun && activeRankings.length > 0 && (
        <div className="screening-results">
          <div className="results-list">
            <div className="section-card">
              <div className="section-card-header">
                <h2 className="section-card-title">Rankings ({activeRankings.length})</h2>
              </div>
              <div className="section-card-body p0">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Candidate</th>
                      <th>Score</th>
                      <th>Match</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeRankings.map((r, i) => (
                      <tr
                        key={r.candidate_id}
                        className={selectedCandidate?.candidate_id === r.candidate_id ? "row-selected" : ""}
                        onClick={() => setSelected(r.candidate_id)}
                        style={{ cursor: "pointer" }}
                      >
                        <td className="rank-cell">{i + 1}</td>
                        <td>
                          <div className="candidate-cell">
                            <div className="candidate-avatar">{(r.candidate_name || r.filename)[0].toUpperCase()}</div>
                            <div>
                              <div className="candidate-name">{r.candidate_name || r.filename}</div>
                              <div className="candidate-email">{r.email || "—"}</div>
                            </div>
                          </div>
                        </td>
                        <td><ScoreBadge score={r.match_score} /></td>
                        <td><RecommendationBadge recommendation={r.recommendation} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="results-detail">
            {selectedCandidate ? (
              <CandidateDetail candidate={selectedCandidate} />
            ) : (
              <EmptyState icon="👆" title="Select a candidate" body="Click a row to view details." />
            )}
          </div>
        </div>
      )}

      {!screening && !hasRun && (
        <EmptyState
          icon="🔍"
          title="No screening results yet"
          body="Select a job and click Run Screening to rank candidates."
        />
      )}
    </div>
  );
}

function CandidateDetail({ candidate: c }) {
  const scores = [
    { label: "Skills", value: c.skill_score, color: "#6366f1" },
    { label: "Keywords", value: c.keyword_score ?? 0, color: "#0ea5e9" },
    { label: "Experience", value: c.experience_score, color: "#8b5cf6" },
    { label: "Qualifications", value: c.qualifications_score ?? 0, color: "#d97706" },
    { label: "Semantic", value: c.semantic_score, color: "#0d9488" },
  ];

  return (
    <div className="section-card candidate-detail-card">
      <div className="detail-hero">
        <div className="detail-hero-left">
          <div className="detail-avatar">{(c.candidate_name || c.filename)[0].toUpperCase()}</div>
          <div>
            <h2 className="detail-name">{c.candidate_name || c.filename}</h2>
            <p className="detail-email">{c.email || "No email"}</p>
            {c.phone && <p className="detail-phone">{c.phone}</p>}
          </div>
        </div>
        <CircularScore score={c.match_score} size={110} />
      </div>

      <div className="detail-actions-row">
        <RecommendationBadge recommendation={c.recommendation} />
        <a className="btn btn-ghost btn-sm" href={getResumeDownloadUrl(c.candidate_id)} target="_blank" rel="noreferrer">
          ↓ Download
        </a>
      </div>

      {c.recommendation_reason && (
        <div className="detail-reason">{c.recommendation_reason}</div>
      )}

      <div className="detail-scores">
        {scores.map(({ label, value, color }) => (
          <div key={label} className="score-row">
            <span className="score-row-label">{label}</span>
            <MiniBar value={value} color={color} />
            <span className="score-row-val">{(Number(value) || 0).toFixed(1)}</span>
          </div>
        ))}
      </div>

      <div className="detail-chips-section">
        <ChipGroup title="✓ Matched Skills" items={c.matched_skills} tone="matched" />
        <ChipGroup title="✗ Missing Skills" items={c.missing_skills} tone="missing" />
        <ChipGroup title="✓ Matched Keywords" items={c.matched_keywords} tone="matched" />
        <ChipGroup title="✗ Missing Keywords" items={c.missing_keywords} tone="missing" />
        <ChipGroup title="✓ Qualifications" items={c.matched_qualifications} tone="matched" />
        <ChipGroup title="✗ Missing Quals" items={c.missing_qualifications} tone="missing" />
      </div>

      {c.ai_suggestions?.length > 0 && (
        <div className="ai-block">
          <h4>AI Suggestions</h4>
          <ul>{c.ai_suggestions.map((s, i) => <li key={i}>{s}</li>)}</ul>
        </div>
      )}

      {c.improvements?.length > 0 && (
        <div className="ai-block">
          <h4>Improvement Recommendations</h4>
          <ul>{c.improvements.map((s, i) => <li key={i}>{s}</li>)}</ul>
        </div>
      )}
    </div>
  );
}

function ChipGroup({ title, items, tone }) {
  if (!items?.length) return null;
  return (
    <div className="chip-group">
      <span className="chip-group-title">{title}</span>
      <div className="chip-row">
        {items.map((item) => <SkillChip key={item} label={item} tone={tone} />)}
      </div>
    </div>
  );
}
