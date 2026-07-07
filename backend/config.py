from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "AI Resume Screening System"
    api_prefix: str = "/api"
    debug: bool = False
    database_url: str = f"sqlite:///{(ROOT_DIR / 'resume_screening.db').as_posix()}"

    storage_dir: Path = ROOT_DIR / "backend" / "storage"
    resume_dir: Path = ROOT_DIR / "resumes"
    job_dir: Path = ROOT_DIR / "backend" / "storage" / "jobs"

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    sentence_transformer_model: str = "all-MiniLM-L6-v2"
    spacy_model: str = "en_core_web_sm"

    # AI Provider configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    claude_model: str = "claude-3-5-sonnet-20241022"
    google_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    preferred_ai_provider: str = "openai"  # openai, claude, or gemini

    # Scoring weights for 5-dimension model (total = 100%)
    skill_weight: float = 0.40
    keyword_weight: float = 0.20
    experience_weight: float = 0.20
    education_weight: float = 0.10
    qualifications_weight: float = 0.10
    # semantic_weight retained for backward compatibility only — not used in scoring
    semantic_weight: float = 0.10

    skill_catalog: list[str] = Field(
        default_factory=lambda: [
            "python",
            "java",
            "javascript",
            "typescript",
            "react",
            "next.js",
            "node.js",
            "express",
            "fastapi",
            "django",
            "flask",
            "sql",
            "postgresql",
            "mysql",
            "mongodb",
            "redis",
            "docker",
            "kubernetes",
            "aws",
            "azure",
            "gcp",
            "terraform",
            "git",
            "ci/cd",
            "jenkins",
            "github actions",
            "linux",
            "pandas",
            "numpy",
            "scikit-learn",
            "tensorflow",
            "pytorch",
            "nlp",
            "machine learning",
            "deep learning",
            "data analysis",
            "data engineering",
            "spark",
            "hadoop",
            "airflow",
            "power bi",
            "tableau",
            "excel",
            "rest api",
            "graphql",
            "microservices",
            "oop",
            "agile",
            "scrum",
            "communication",
            "leadership",
            "problem solving",
            "project management",
            "testing",
            "pytest",
            "unit testing",
            "selenium",
            "c++",
            "c#",
            "html",
            "css",
            "tailwind",
            "bootstrap",
        ]
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off", ""}:
                return False
            return False
        return bool(value)

    def ensure_directories(self) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.resume_dir.mkdir(parents=True, exist_ok=True)
        self.job_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
