from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy import inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config import get_settings


settings = get_settings()


class Base(DeclarativeBase):
    pass


engine_kwargs: dict[str, object] = {"pool_pre_ping": True}
if settings.database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    from models.entities import Candidate, JobDescription, ScreeningResult  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _upgrade_screening_results_table()


def _upgrade_screening_results_table() -> None:
    inspector = inspect(engine)
    if "screening_results" not in inspector.get_table_names():
        return

    existing = {col["name"] for col in inspector.get_columns("screening_results")}
    required_columns = {
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

    with engine.begin() as connection:
        for name, ddl_type in required_columns.items():
            if name in existing:
                continue
            connection.execute(
                text(f"ALTER TABLE screening_results ADD COLUMN {name} {ddl_type}")
            )
