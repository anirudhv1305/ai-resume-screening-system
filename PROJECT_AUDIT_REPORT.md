# AI Resume Screening Project Audit Report

## Discovery Summary

- Frontend: React 18 with Vite 7 and Axios.
- Backend: FastAPI, Uvicorn, SQLAlchemy, Pydantic Settings.
- Database: SQLite by default, PostgreSQL through `DATABASE_URL`.
- AI/ML: spaCy for extraction, Sentence Transformers `all-MiniLM-L6-v2` for semantic matching, PyMuPDF for PDF text extraction.
- API: REST endpoints under `/api` for health, resume uploads, job uploads, screening, ranking, download, and deletion.
- Authentication: none implemented.
- Deployment: Render backend in `render.yaml`; Vercel frontend in `frontend/vercel.json`.
- Environment variables: `DATABASE_URL`, `CORS_ORIGINS`, `RESUME_DIR`, `JOB_DIR`, `SPACY_MODEL`, `SENTENCE_TRANSFORMER_MODEL`, `VITE_API_URL`; `DEBUG` is consumed by settings.

## Dependency Graph

```text
frontend/src/App.jsx
  -> frontend/src/api/client.js
  -> /api/jobs, /api/resumes, /api/screening, /api/resume/{id}/download

backend.main
  -> backend.config
  -> backend.database
  -> routes/*
     -> backend.dependencies
     -> services/*
        -> services.resume_service -> utils.file_validation -> PyMuPDF -> services.nlp_service
        -> services.job_service -> utils.file_validation -> services.nlp_service
        -> services.screening_service -> services.matching_service
        -> services.matching_service -> SentenceTransformer
     -> models.schemas
     -> models.entities
        -> backend.database.Base
```

## Issues Found And Fixes Applied

| Severity | Area | Issue | Fix |
| --- | --- | --- | --- |
| Critical | Runtime | `uvicorn backend.main:app` failed from the repo root because backend modules used top-level imports. | Converted backend-owned imports to package-safe `backend.*` imports. |
| High | Runtime/config | Ambient `DEBUG=release` caused Pydantic boolean parsing failure at startup. | Added robust debug parsing that safely defaults unknown values to `False`. |
| High | Upload security | Job upload filename handling did not normalize path-like filenames. | Sanitized job upload filenames with `Path(...).name`. |
| Medium | File consistency | Failed parse or DB writes could leave uploaded files behind. | Added rollback and saved-file cleanup for job and resume upload flows. |
| Medium | Performance | Ranking retrieval could trigger N+1 candidate queries. | Added `selectinload` for screening result candidate relationships. |
| Medium | Database | Screening foreign keys had no ORM indexes. | Added indexes on `candidate_id` and `job_id`. |
| Medium | API validation | Empty `candidate_ids` lists were treated like no filter. | Rejected empty candidate filters with a clear validation error. |
| Low | QA | No project tests existed. | Added focused standard-library backend tests. |
| Low | UI/UX | Dashboard was functional but dense and dark-only. | Modernized recruiter dashboard layout, stats, responsive behavior, and states. |

## Testing Performed

- `venv\Scripts\python.exe -m compileall -q backend routes services models utils tests`
- `venv\Scripts\python.exe -m unittest discover -s tests`
- `npm.cmd run build`
- Local Uvicorn health check at `http://127.0.0.1:8765/api/health`

## Remaining Risks

- No authentication or authorization is implemented; exposed deployments should be protected before handling private resumes.
- No automated browser-based end-to-end tests are configured.
- No frontend linting setup exists in `package.json`.
- Existing databases created before the ORM index change may need a migration or manual index creation.
- The first SentenceTransformer model load can be slow and requires model availability.

## Recommendations

- Add authentication and role-based authorization before production use.
- Add database migrations with Alembic.
- Add frontend linting and E2E tests with a browser automation tool.
- Add CI that runs Python tests, compile checks, and frontend builds.
- Consider asynchronous/background processing for large resume batches.
