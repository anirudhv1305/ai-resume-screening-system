import { useMemo } from "react";
import { EmptyState } from "../components/UI";

function Bar({ label, value, max, color }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="chart-bar-row">
      <span className="chart-bar-label">{label}</span>
      <div className="chart-bar-track">
        <div className="chart-bar-fill" style={{ width: `${pct}%`, background: color || "var(--accent)" }} />
      </div>
      <span className="chart-bar-val">{value}</span>
    </div>
  );
}

export default function AnalyticsPage({ rankings, candidates }) {
  const data = useMemo(() => {
    if (!rankings.length) return null;

    const scores = rankings.map((r) => Number(r.match_score) || 0);
    const buckets = { "0–20": 0, "21–40": 0, "41–60": 0, "61–80": 0, "81–100": 0 };
    scores.forEach((s) => {
      if (s <= 20) buckets["0–20"]++;
      else if (s <= 40) buckets["21–40"]++;
      else if (s <= 60) buckets["41–60"]++;
      else if (s <= 80) buckets["61–80"]++;
      else buckets["81–100"]++;
    });

    const skillFreq = {};
    rankings.forEach((r) => {
      (r.matched_skills || []).forEach((s) => { skillFreq[s] = (skillFreq[s] || 0) + 1; });
    });
    const topSkills = Object.entries(skillFreq).sort((a, b) => b[1] - a[1]).slice(0, 10);

    const missingFreq = {};
    rankings.forEach((r) => {
      (r.missing_skills || []).forEach((s) => { missingFreq[s] = (missingFreq[s] || 0) + 1; });
    });
    const topMissing = Object.entries(missingFreq).sort((a, b) => b[1] - a[1]).slice(0, 10);

    const recCounts = { "Strong Match": 0, "Moderate Match": 0, "Weak Match": 0 };
    rankings.forEach((r) => {
      if (r.recommendation && recCounts[r.recommendation] !== undefined) {
        recCounts[r.recommendation]++;
      }
    });

    const expBuckets = { "0–2 yrs": 0, "3–5 yrs": 0, "6–10 yrs": 0, "10+ yrs": 0 };
    rankings.forEach((r) => {
      const y = Number(r.experience_years) || 0;
      if (y <= 2) expBuckets["0–2 yrs"]++;
      else if (y <= 5) expBuckets["3–5 yrs"]++;
      else if (y <= 10) expBuckets["6–10 yrs"]++;
      else expBuckets["10+ yrs"]++;
    });

    return { buckets, topSkills, topMissing, recCounts, expBuckets };
  }, [rankings]);

  if (!rankings.length) {
    return <EmptyState icon="📊" title="No data yet" body="Run a screening to see analytics." />;
  }

  const maxSkill = data.topSkills[0]?.[1] || 1;
  const maxMissing = data.topMissing[0]?.[1] || 1;
  const maxBucket = Math.max(...Object.values(data.buckets), 1);
  const maxExp = Math.max(...Object.values(data.expBuckets), 1);
  const maxRec = Math.max(...Object.values(data.recCounts), 1);

  return (
    <div className="page-analytics">
      <div className="analytics-grid">
        <div className="section-card">
          <div className="section-card-header"><h2 className="section-card-title">Score Distribution</h2></div>
          <div className="section-card-body">
            {Object.entries(data.buckets).map(([label, val]) => (
              <Bar key={label} label={label} value={val} max={maxBucket} color="#6366f1" />
            ))}
          </div>
        </div>

        <div className="section-card">
          <div className="section-card-header"><h2 className="section-card-title">Recommendation Breakdown</h2></div>
          <div className="section-card-body">
            <Bar label="Strong Match" value={data.recCounts["Strong Match"]} max={maxRec} color="#16a34a" />
            <Bar label="Moderate Match" value={data.recCounts["Moderate Match"]} max={maxRec} color="#d97706" />
            <Bar label="Weak Match" value={data.recCounts["Weak Match"]} max={maxRec} color="#dc2626" />
          </div>
        </div>

        <div className="section-card">
          <div className="section-card-header"><h2 className="section-card-title">Experience Distribution</h2></div>
          <div className="section-card-body">
            {Object.entries(data.expBuckets).map(([label, val]) => (
              <Bar key={label} label={label} value={val} max={maxExp} color="#0ea5e9" />
            ))}
          </div>
        </div>

        <div className="section-card">
          <div className="section-card-header"><h2 className="section-card-title">Top Matched Skills</h2></div>
          <div className="section-card-body">
            {data.topSkills.length === 0 ? (
              <p className="muted">No skill data.</p>
            ) : data.topSkills.map(([skill, count]) => (
              <Bar key={skill} label={skill} value={count} max={maxSkill} color="#0d9488" />
            ))}
          </div>
        </div>

        <div className="section-card">
          <div className="section-card-header"><h2 className="section-card-title">Top Missing Skills</h2></div>
          <div className="section-card-body">
            {data.topMissing.length === 0 ? (
              <p className="muted">No missing skill data.</p>
            ) : data.topMissing.map(([skill, count]) => (
              <Bar key={skill} label={skill} value={count} max={maxMissing} color="#dc2626" />
            ))}
          </div>
        </div>

        <div className="section-card">
          <div className="section-card-header"><h2 className="section-card-title">Pipeline Summary</h2></div>
          <div className="section-card-body analytics-summary">
            <div className="summary-stat">
              <strong>{candidates.length}</strong><span>Total Resumes</span>
            </div>
            <div className="summary-stat">
              <strong>{rankings.length}</strong><span>Screened</span>
            </div>
            <div className="summary-stat">
              <strong>{data.recCounts["Strong Match"]}</strong><span>Strong Matches</span>
            </div>
            <div className="summary-stat">
              <strong>
                {rankings.length
                  ? (rankings.reduce((a, r) => a + (Number(r.match_score) || 0), 0) / rankings.length).toFixed(1)
                  : "—"}%
              </strong>
              <span>Avg Score</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
