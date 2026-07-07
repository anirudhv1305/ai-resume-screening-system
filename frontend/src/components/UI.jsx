export function ScoreBadge({ score, size = "md" }) {
  const s = Math.max(0, Math.min(Number(score) || 0, 100));
  const cls = s >= 80 ? "strong" : s >= 60 ? "moderate" : "weak";
  return <span className={`score-badge score-badge-${cls} score-badge-${size}`}>{s.toFixed(1)}</span>;
}

export function RecommendationBadge({ recommendation }) {
  if (!recommendation) return null;
  const lower = recommendation.toLowerCase();
  const cls = lower.includes("strong") ? "strong" : lower.includes("weak") ? "weak" : "moderate";
  return <span className={`rec-badge rec-${cls}`}>{recommendation}</span>;
}

export function MiniBar({ value, color }) {
  const pct = Math.max(0, Math.min(Number(value) || 0, 100));
  return (
    <div className="mini-bar-track">
      <div className="mini-bar-fill" style={{ width: `${pct}%`, background: color || "var(--accent)" }} />
    </div>
  );
}

export function CircularScore({ score, size = 120 }) {
  const s = Math.max(0, Math.min(Number(score) || 0, 100));
  const r = (size / 2) * 0.72;
  const circ = 2 * Math.PI * r;
  const offset = circ - (s / 100) * circ;
  const cls = s >= 80 ? "strong" : s >= 60 ? "moderate" : "weak";
  const colors = { strong: "#16a34a", moderate: "#d97706", weak: "#dc2626" };
  return (
    <div className="circular-score-wrap" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#e5e7eb" strokeWidth={size * 0.07} />
        <circle
          cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={colors[cls]} strokeWidth={size * 0.07}
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round" transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <div className="circular-score-label">
        <strong style={{ color: colors[cls] }}>{s.toFixed(0)}</strong>
        <span>/ 100</span>
      </div>
    </div>
  );
}

export function SkillChip({ label, tone = "neutral" }) {
  return <span className={`skill-chip skill-chip-${tone}`}>{label}</span>;
}

export function StatCard({ label, value, sub, accent }) {
  return (
    <div className="stat-card" style={accent ? { borderTopColor: accent } : {}}>
      <div className="stat-value">{value ?? "—"}</div>
      <div className="stat-label">{label}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

export function Skeleton({ height = 20, width = "100%", radius = 6 }) {
  return (
    <div
      className="skeleton"
      style={{ height, width, borderRadius: radius }}
    />
  );
}

export function EmptyState({ icon, title, body }) {
  return (
    <div className="empty-state">
      <div className="empty-icon">{icon}</div>
      <h3>{title}</h3>
      {body && <p>{body}</p>}
    </div>
  );
}

export function SectionCard({ title, children, action }) {
  return (
    <div className="section-card">
      <div className="section-card-header">
        <h2 className="section-card-title">{title}</h2>
        {action && <div className="section-card-action">{action}</div>}
      </div>
      <div className="section-card-body">{children}</div>
    </div>
  );
}
