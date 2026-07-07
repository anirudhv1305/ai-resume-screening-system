export default function SettingsPage() {
  return (
    <div className="page-settings">
      <div className="section-card">
        <div className="section-card-header">
          <h2 className="section-card-title">AI Provider</h2>
        </div>
        <div className="section-card-body settings-body">
          <p className="settings-note">
            AI provider keys are configured via environment variables on the backend.
            Set <code>OPENAI_API_KEY</code>, <code>ANTHROPIC_API_KEY</code>, or <code>GOOGLE_API_KEY</code> in your <code>.env</code> file.
            The system automatically falls back to deterministic suggestions when no key is configured.
          </p>
          <div className="settings-table">
            <div className="settings-row">
              <span>OpenAI (GPT-4o-mini)</span>
              <span className="settings-env"><code>OPENAI_API_KEY</code></span>
            </div>
            <div className="settings-row">
              <span>Anthropic Claude</span>
              <span className="settings-env"><code>ANTHROPIC_API_KEY</code></span>
            </div>
            <div className="settings-row">
              <span>Google Gemini</span>
              <span className="settings-env"><code>GOOGLE_API_KEY</code></span>
            </div>
          </div>
        </div>
      </div>

      <div className="section-card">
        <div className="section-card-header">
          <h2 className="section-card-title">Scoring Weights</h2>
        </div>
        <div className="section-card-body settings-body">
          <p className="settings-note">Weights are configured in <code>backend/config.py</code>.</p>
          <div className="settings-table">
            {[
              ["Skill Match", "40%", "skill_weight"],
              ["Keyword Match", "20%", "keyword_weight"],
              ["Experience", "20%", "experience_weight"],
              ["Qualifications", "10%", "qualifications_weight"],
              ["Semantic Similarity", "10%", "education_weight"],
            ].map(([label, val, key]) => (
              <div key={key} className="settings-row">
                <span>{label}</span>
                <span className="settings-weight">{val}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="section-card">
        <div className="section-card-header">
          <h2 className="section-card-title">Database</h2>
        </div>
        <div className="section-card-body settings-body">
          <p className="settings-note">
            Set <code>DATABASE_URL</code> in your <code>.env</code> file.
            SQLite is used locally. PostgreSQL is used on Render.
          </p>
          <div className="settings-table">
            <div className="settings-row">
              <span>Local</span>
              <span className="settings-env"><code>sqlite:///./resume_screening.db</code></span>
            </div>
            <div className="settings-row">
              <span>Production</span>
              <span className="settings-env"><code>postgresql+psycopg2://…</code></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
