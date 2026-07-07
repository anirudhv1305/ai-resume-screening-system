import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { StatCard, RecommendationBadge, ScoreBadge, EmptyState, Skeleton } from "../components/UI";

export default function DashboardPage({ jobs, candidates, rankings, activeJob, loading, onRunScreening, screening, activeJobId, setActiveJobId }) {
  const navigate = useNavigate();

  const stats = useMemo(() => {
    const scores = rankings.map((r) => Number(r.match_score) || 0);
    const strong = rankings.filter((r) => r.match_score >= 80).length;
    const moderate = rankings.filter((r) => r.match_score >= 60 && r.match_score < 80).length;
    const weak = rankings.filter((r) => r.match_score < 60).length;
    const avg = scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : null;
    const top = scores.length ? Math.max(...scores) : null;
    const low = scores.length ? Math.min(...scores) : null;
    return { strong, moderate, weak, avg, top, low };
  }, [rankings]);

  return (
    <div className="page-dashboard">
      <div className="dashboard-stats">
        {loading ? (
          Array.from({ length: 9 }).map((_, i) => <Skeleton key={i} height={96} radius={12} />)
        ) : (
          <>
            <StatCard label="Total Resumes" value={candidates.length} accent="#6366f1" />
            <StatCard label="Total Jobs" value={jobs.length} accent="#0ea5e9" />
            <StatCard label="Screenings Run" value={rankings.length} accent="#8b5cf6" />
            <StatCard label="Strong Matches" value={stats.strong} accent="#16a34a" sub="≥ 80%" />
            <StatCard label="Moderate Matches" value={stats.moderate} accent="#d97706" sub="60–79%" />
            <StatCard label="Weak Matches" value={stats.weak} accent="#dc2626" sub="< 60%" />
            <StatCard label="Average Score" value={stats.avg !== null ? `${stats.avg.toFixed(1)}%` : "—"} accent="#0d9488" />
            <StatCard label="Highest Score" value={stats.top !== null ? `${stats.top.toFixed(1)}%` : "—"} accent="#16a34a" />
            <StatCard label="Lowest Score" value={stats.low !== null ? `${stats.low.toFixed(1)}%` : "—"} accent="#dc2626" />
          </>
        )}
      </div>

      <div className="dashboard-body">
        <div className="dashboard-main">
          <div className="section-card">
            <div className="section-card-header">
              <h2 className="section-card-title">Recent Rankings</h2>
              <button className="btn btn-ghost btn-sm" onClick={() => navigate("/screening")}>
                Run Screening →
              </button>
            </div>
            <div className="section-card-body">
              {loading ? (
                <div className="skeleton-list">
                  {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} height={52} radius={8} />)}
                </div>
              ) : rankings.length === 0 ? (
                <EmptyState icon="🔍" title="No screenings yet" body="Upload resumes, create a job, then run screening." />
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Candidate</th>
                      <th>Score</th>
                      <th>Skills</th>
                      <th>Experience</th>
                      <th>Match</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rankings.slice(0, 8).map((r, i) => (
                      <tr key={r.candidate_id}>
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
                        <td className="muted-cell">{r.matched_skills?.length || 0} matched</td>
                        <td className="muted-cell">{(r.experience_years || 0).toFixed(1)} yrs</td>
                        <td><RecommendationBadge recommendation={r.recommendation} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>

        <div className="dashboard-side">
          <div className="section-card">
            <div className="section-card-header">
              <h2 className="section-card-title">Quick Actions</h2>
            </div>
            <div className="section-card-body quick-actions">
              <button className="quick-action-btn" onClick={() => navigate("/resumes")}>
                <span className="qa-icon">📄</span>
                <span>Upload Resumes</span>
              </button>
              <button className="quick-action-btn" onClick={() => navigate("/jobs")}>
                <span className="qa-icon">💼</span>
                <span>Create Job</span>
              </button>
              <button
                className="quick-action-btn qa-primary"
                onClick={() => navigate("/screening")}
              >
                <span className="qa-icon">🔍</span>
                <span>Run Screening</span>
              </button>
              <button className="quick-action-btn" onClick={() => navigate("/analytics")}>
                <span className="qa-icon">📊</span>
                <span>View Analytics</span>
              </button>
            </div>
          </div>

          <div className="section-card">
            <div className="section-card-header">
              <h2 className="section-card-title">Active Job</h2>
            </div>
            <div className="section-card-body">
              {jobs.length === 0 ? (
                <EmptyState icon="💼" title="No jobs yet" />
              ) : (
                <>
                  <select
                    className="form-select"
                    value={activeJobId || ""}
                    onChange={(e) => setActiveJobId(Number(e.target.value) || null)}
                  >
                    <option value="">Select a job</option>
                    {jobs.map((j) => (
                      <option key={j.id} value={j.id}>{j.title}</option>
                    ))}
                  </select>
                  {activeJob && (
                    <div className="active-job-meta">
                      <div className="meta-row">
                        <span>Required Skills</span>
                        <strong>{activeJob.required_skills?.length || 0}</strong>
                      </div>
                      <div className="meta-row">
                        <span>Min Experience</span>
                        <strong>{activeJob.minimum_years_experience || 0} yrs</strong>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
