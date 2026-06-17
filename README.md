# AI Resume Screening System

An end-to-end AI-powered Applicant Tracking System (ATS) built with FastAPI, React, spaCy, Sentence Transformers, and SQLite/PostgreSQL support.

---

## Features

- Upload one or many PDF resumes
- Upload job descriptions as text or PDF/TXT file
- Parse resume text with multi-strategy PDF extraction (PyMuPDF, pdfplumber, PyPDF2)
- Extract skills, education, experience, and qualifications from resumes
- Rank candidates against a job description using a 5-dimension scoring model:
  - Skill match: 40%
  - Keyword match: 20%
  - Experience relevance: 20%
  - Qualifications match: 10%
  - Semantic similarity: 10%
- Keyword analysis with matched and missing keywords
- Qualification analysis with matched and missing degrees/certifications
- AI-powered suggestions and improvement recommendations (OpenAI / Claude / Gemini)
- Deterministic fallback when no AI provider is configured
- Recommendation engine: Strong Match / Moderate Match / Weak Match
- View, download, and delete uploaded resumes
- React dashboard with candidate ranking table and detail panel

---

## Technology Stack

### Frontend
- React 18
- Vite
- Axios

### Backend
- FastAPI
- SQLAlchemy (SQLite default, PostgreSQL for production)
- Pydantic v2

### NLP
- spaCy (`en_core_web_sm`)
- Sentence Transformers (`all-MiniLM-L6-v2`)

### AI Providers (optional)
- OpenAI (`gpt-4o-mini`)
- Anthropic Claude (`claude-3-5-sonnet-20241022`)
- Google Gemini (`gemini-1.5-flash`)

### PDF Extraction
- PyMuPDF (primary)
- pdfplumber (fallback)
- PyPDF2 (final fallback)

---

## Project Structure

```
.
├── backend/
│   ├── config.py          # Settings, weights, env vars
│   ├── database.py        # SQLAlchemy engine and session
│   ├── dependencies.py    # FastAPI dependency injection
│   ├── main.py            # App factory, lifespan, CORS
│   └── requirements.txt   # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── api/client.js
│   │   ├── components/
│   │   │   ├── CandidateDetailPanel.jsx
│   │   │   ├── CandidateTable.jsx
│   │   │   └── Sidebar.jsx
│   │   ├── App.jsx
│   │   └── styles.css
│   ├── package.json
│   ├── vercel.json
│   └── vite.config.js
├── models/
│   ├── entities.py        # SQLAlchemy ORM models
│   └── schemas.py         # Pydantic request/response schemas
├── routes/
│   ├── ats.py
│   ├── health.py
│   ├── jobs.py
│   ├── resumes.py
│   └── screening.py
├── services/
│   ├── ai_suggestions_service.py
│   ├── job_service.py
│   ├── matching_service.py
│   ├── nlp_service.py
│   ├── resume_service.py
│   └── screening_service.py
├── utils/
│   ├── ai_providers/      # OpenAI / Claude / Gemini wrappers
│   ├── pdf_extraction/    # Multi-strategy PDF extractors
│   ├── ai_prompts.py
│   ├── file_validation.py
│   └── result_formatters.py
├── tests/
├── render.yaml
├── runtime.txt
└── start.bat
```

---

## API Overview

### Resume Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/resumes/upload` | Upload one or more PDF resumes |
| GET | `/api/resumes` | List all uploaded resumes |
| DELETE | `/api/resume/{id}` | Delete a resume |
| GET | `/api/resume/{id}/download` | Download original resume file |

### Jobs
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/jobs/upload` | Create a job description |
| GET | `/api/jobs` | List all job descriptions |

### Screening
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/screening/match` | Match all resumes against a job description (batch) |
| GET | `/api/screening/rankings/{job_id}` | Retrieve stored rankings for a job |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check (used by Render) |

---

## Scoring Model

```
final_score = (skill_score × 0.40)
            + (keyword_score × 0.20)
            + (experience_score × 0.20)
            + (qualifications_score × 0.10)
            + (semantic_score × 0.10)
```

Each response includes: candidate name, scores per dimension, matched skills, missing skills, matched/missing keywords, matched/missing qualifications, recommendation, and optional AI suggestions.

---

## Local Setup

### Option 1: One-Click Start

```bat
start.bat
```

Starts backend at `http://127.0.0.1:8000` and frontend at `http://localhost:5173`.

### Option 2: Manual

**Backend:**
```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn backend.main:app --reload
```

**Frontend:**
```bat
cd frontend
npm install
npm run dev
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in values:

```env
# Database
DATABASE_URL=sqlite:///./resume_screening.db

# CORS
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Storage
RESUME_DIR=./resumes
JOB_DIR=./backend/storage/jobs

# NLP Models
SPACY_MODEL=en_core_web_sm
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2

# AI Providers (optional — system works without these)
OPENAI_API_KEY=<your-openai-key>
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_API_KEY=<your-anthropic-key>
CLAUDE_MODEL=claude-3-5-sonnet-20241022
GOOGLE_API_KEY=<your-google-key>
GEMINI_MODEL=gemini-1.5-flash
PREFERRED_AI_PROVIDER=openai
```

AI providers are optional. When no keys are set, the system falls back to deterministic suggestions.

To use PostgreSQL:
```env
DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/resume_screening
```

---

## Deployment

### Frontend — Vercel

1. Set the Vercel project root to `frontend/`
2. Build command: `npm run build`
3. Output directory: `dist`
4. Add environment variable:
   ```env
   VITE_API_URL=https://your-render-backend.onrender.com/api
   ```

`frontend/vercel.json` handles SPA route rewrites automatically.

### Backend — Render

`render.yaml` is included for one-click Render deployment with PostgreSQL.

Set these environment variables in Render dashboard:
```env
CORS_ORIGINS=https://your-vercel-project.vercel.app,http://localhost:5173
RESUME_DIR=/var/data/resumes
JOB_DIR=/var/data/jobs
SPACY_MODEL=en_core_web_sm
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
OPENAI_API_KEY=<optional>
ANTHROPIC_API_KEY=<optional>
GOOGLE_API_KEY=<optional>
```

`DATABASE_URL` is injected automatically from the Render PostgreSQL instance.

Startup command (already in `render.yaml`):
```
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Health check path: `/api/health`

---

## Architecture Overview

```
Browser (React + Vite)
        │
        │ HTTP / REST
        ▼
FastAPI Backend
  ├── routes/          → HTTP layer, request validation
  ├── services/        → Business logic (NLP, matching, AI)
  ├── models/          → ORM entities + Pydantic schemas
  └── utils/           → PDF extraction, AI providers, prompts
        │
        ├── spaCy NLP  → skill/entity extraction
        ├── SentenceTransformers → semantic similarity (batch encoded)
        ├── AI Providers → OpenAI / Claude / Gemini (optional)
        └── SQLite / PostgreSQL
```

On server startup, spaCy and SentenceTransformer models are pre-warmed so the first request is not slow.

---

## Screenshots

> _Add screenshots here before portfolio submission._

| Dashboard | Candidate Detail |
|-----------|-----------------|
| _(screenshot)_ | _(screenshot)_ |

---

## License

This project is provided for educational and portfolio use.
