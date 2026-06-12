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
    job_dir: Path = storage_dir / "jobs"

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    sentence_transformer_model: str = "all-MiniLM-L6-v2"
    spacy_model: str = "en_core_web_sm"

    skill_weight: float = 0.40
    experience_weight: float = 0.30
    semantic_weight: float = 0.30

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
