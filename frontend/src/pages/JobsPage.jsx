import { useState } from "react";
import { EmptyState, SkillChip } from "../components/UI";

export default function JobsPage({ jobs, onCreateJob, loading }) {
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    title: "", description: "", file: null,
  });

  function set(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    const result = await onCreateJob(form);
    setSubmitting(false);
    if (result) {
      setForm({ title: "", description: "", file: null });
      setShowForm(false);
    }
  }

  return (
    <div className="page-jobs">
      <div className="page-toolbar">
        <span className="result-count">{jobs.length} job{jobs.length !== 1 ? "s" : ""}</span>
        <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Cancel" : "+ New Job"}
        </button>
      </div>

      {showForm && (
        <div className="section-card form-card">
          <div className="section-card-header">
            <h2 className="section-card-title">Create Job Description</h2>
          </div>
          <form className="section-card-body job-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Job Title *</label>
              <input
                className="form-input"
                required
                type="text"
                placeholder="e.g. Senior Python Developer"
                value={form.title}
                onChange={(e) => set("title", e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Job Description *</label>
              <textarea
                className="form-textarea"
                rows={8}
                required={!form.file}
                placeholder="Paste the full job description including responsibilities, required skills, qualifications, and experience requirements…"
                value={form.description}
                onChange={(e) => set("description", e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Upload JD File (optional — PDF or TXT)</label>
              <input
                className="form-input"
                type="file"
                accept=".pdf,.txt"
                onChange={(e) => set("file", e.target.files?.[0] || null)}
              />
              {form.file && <span className="file-hint">📎 {form.file.name}</span>}
            </div>

            <div className="form-actions">
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? "Saving…" : "Save Job"}
              </button>
              <button type="button" className="btn btn-ghost" onClick={() => setShowForm(false)}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="jobs-list">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="job-card skeleton-card" style={{ height: 120 }} />
          ))}
        </div>
      ) : jobs.length === 0 ? (
        <EmptyState icon="💼" title="No jobs yet" body="Create your first job description to start screening candidates." />
      ) : (
        <div className="jobs-list">
          {jobs.map((j) => (
            <div key={j.id} className="job-card">
              <div className="job-card-header">
                <div>
                  <h3 className="job-title">{j.title}</h3>
                  <span className="job-date">
                    {j.created_at ? new Date(j.created_at).toLocaleDateString() : ""}
                  </span>
                </div>
                <div className="job-card-meta">
                  <span className="meta-pill">
                    {j.minimum_years_experience || 0} yrs exp required
                  </span>
                  <span className="meta-pill">
                    {j.required_skills?.length || 0} skills
                  </span>
                </div>
              </div>
              {j.required_skills?.length > 0 && (
                <div className="job-skills">
                  {j.required_skills.slice(0, 8).map((s) => (
                    <SkillChip key={s} label={s} tone="neutral" />
                  ))}
                  {j.required_skills.length > 8 && (
                    <span className="skill-more">+{j.required_skills.length - 8}</span>
                  )}
                </div>
              )}
              {j.description_text && (
                <p className="job-desc-preview">
                  {j.description_text.slice(0, 200)}{j.description_text.length > 200 ? "…" : ""}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
