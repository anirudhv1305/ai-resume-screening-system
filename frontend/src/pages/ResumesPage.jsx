import { useRef, useState } from "react";
import { getResumeDownloadUrl } from "../api/client";
import { EmptyState, Skeleton, SkillChip } from "../components/UI";

export default function ResumesPage({ candidates, loading, onUploadResumes, onDeleteResume }) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [search, setSearch] = useState("");
  const [confirmId, setConfirmId] = useState(null);
  const fileRef = useRef();

  const filtered = candidates.filter((c) => {
    const q = search.toLowerCase();
    return (
      !q ||
      (c.name || "").toLowerCase().includes(q) ||
      (c.email || "").toLowerCase().includes(q) ||
      (c.filename || "").toLowerCase().includes(q) ||
      (c.skills || []).some((s) => s.toLowerCase().includes(q))
    );
  });

  async function handleFiles(files) {
    if (!files?.length) return;
    setUploading(true);
    await onUploadResumes(files);
    setUploading(false);
  }

  function onDrop(e) {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  }

  async function confirmDelete(id) {
    await onDeleteResume(id);
    setConfirmId(null);
  }

  return (
    <div className="page-resumes">
      <div
        className={`drop-zone ${dragging ? "drop-zone-active" : ""} ${uploading ? "drop-zone-uploading" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !uploading && fileRef.current?.click()}
      >
        <input
          ref={fileRef}
          type="file"
          multiple
          accept=".pdf"
          style={{ display: "none" }}
          onChange={(e) => handleFiles(e.target.files)}
        />
        {uploading ? (
          <>
            <div className="drop-spinner" />
            <p>Uploading and parsing resumes…</p>
          </>
        ) : (
          <>
            <div className="drop-icon">📄</div>
            <p className="drop-title">Drag & drop PDF resumes here</p>
            <p className="drop-sub">or click to browse files</p>
          </>
        )}
      </div>

      <div className="page-toolbar">
        <input
          className="search-input"
          type="text"
          placeholder="Search by name, email, or skill…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <span className="result-count">{filtered.length} resume{filtered.length !== 1 ? "s" : ""}</span>
      </div>

      {loading ? (
        <div className="card-grid">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} height={180} radius={12} />)}
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState icon="📄" title="No resumes found" body={search ? "Try a different search." : "Upload PDF resumes above to get started."} />
      ) : (
        <div className="resume-grid">
          {filtered.map((c) => (
            <div key={c.id} className="resume-card">
              <div className="resume-card-header">
                <div className="resume-avatar">{(c.name || c.filename)[0].toUpperCase()}</div>
                <div className="resume-card-info">
                  <strong>{c.name || c.filename}</strong>
                  <span>{c.email || "No email detected"}</span>
                  {c.phone && <span>{c.phone}</span>}
                </div>
              </div>

              <div className="resume-meta">
                <div className="meta-pill">
                  <span>📅</span> {(c.experience_years || 0).toFixed(1)} yrs exp
                </div>
                {c.score != null && (
                  <div className="meta-pill meta-pill-score">
                    <span>⭐</span> {Number(c.score).toFixed(1)} score
                  </div>
                )}
              </div>

              {c.skills?.length > 0 && (
                <div className="resume-skills">
                  {c.skills.slice(0, 5).map((s) => (
                    <SkillChip key={s} label={s} tone="neutral" />
                  ))}
                  {c.skills.length > 5 && (
                    <span className="skill-more">+{c.skills.length - 5}</span>
                  )}
                </div>
              )}

              <div className="resume-card-actions">
                <a
                  className="btn btn-ghost btn-sm"
                  href={getResumeDownloadUrl(c.id)}
                  target="_blank"
                  rel="noreferrer"
                >
                  Download
                </a>
                {confirmId === c.id ? (
                  <div className="confirm-row">
                    <span>Delete?</span>
                    <button className="btn btn-danger btn-sm" onClick={() => confirmDelete(c.id)}>Yes</button>
                    <button className="btn btn-ghost btn-sm" onClick={() => setConfirmId(null)}>No</button>
                  </div>
                ) : (
                  <button className="btn btn-danger btn-sm" onClick={() => setConfirmId(c.id)}>
                    Delete
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
