from __future__ import annotations

import logging

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()


class Base(DeclarativeBase):
    pass


def _build_engine():
    url = settings.database_url
    kwargs: dict[str, object] = {"pool_pre_ping": True}

    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        # PostgreSQL — use a modest pool suitable for Render's free tier
        kwargs["pool_size"] = 5
        kwargs["max_overflow"] = 10
        kwargs["pool_timeout"] = 30
        kwargs["pool_recycle"] = 1800

    return create_engine(url, **kwargs)


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    from models.entities import Candidate, JobDescription, ScreeningResult  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _upgrade_screening_results_table()


def _upgrade_screening_results_table() -> None:
    """
    Idempotent runtime migration: add Phase 6 columns to screening_results
    if they are missing.  Works on both SQLite and PostgreSQL.
    """
    inspector = inspect(engine)
    if "screening_results" not in inspector.get_table_names():
        return

    existing = {col["name"] for col in inspector.get_columns("screening_results")}

    # Map column name → DDL type (compatible with both SQLite and PostgreSQL)
    required_columns: dict[str, str] = {
        "keyword_score": "FLOAT",
        "qualifications_score": "FLOAT",
        "matched_keywords": "TEXT",
        "missing_keywords": "TEXT",
        "matched_qualifications": "TEXT",
        "missing_qualifications": "TEXT",
        "recommendation": "VARCHAR(64)",
        "recommendation_reason": "TEXT",
        "ai_suggestions": "TEXT",
        "improvements": "TEXT",
    }

    missing_cols = {k: v for k, v in required_columns.items() if k not in existing}
    if not missing_cols:
        return

    with engine.begin() as connection:
        for name, ddl_type in missing_cols.items():
            logger.info("Schema migration: adding column %s to screening_results", name)
            connection.execute(
                text(f"ALTER TABLE screening_results ADD COLUMN {name} {ddl_type}")
            )
