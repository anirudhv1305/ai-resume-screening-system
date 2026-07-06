"""
Tests for Phase 6 persistence: ScreeningResult upsert, schema migration,
and GET /api/screening/rankings/{job_id} read-back.

All tests use an in-memory SQLite database so they are fully isolated from
the production DB file and from each other.
"""
from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from backend.database import Base, _upgrade_screening_results_table
from models.entities import Candidate, JobDescription, ScreeningResult
from models.schemas import RankedCandidate
from services.screening_service import ScreeningService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    return engine


def _make_session(engine):
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return Session()


def _seed_candidate(db, *, name="Alice", skills=None, experience_years=3.0):
    candidate = Candidate(
        filename=f"{name.lower()}.pdf",
        name=name,
        email=f"{name.lower()}@example.com",
        resume_text=f"Resume of {name}",
        cleaned_text=f"resume {name.lower()} python fastapi",
        skills=skills or ["python", "fastapi"],
        education=["Bachelor's"],
        experience_years=experience_years,
        experience_highlights=[],
    )
    db.add(candidate)
    db.flush()
    return candidate


def _seed_job(db, *, title="Backend Engineer", description="Python FastAPI developer"):
    job = JobDescription(
        title=title,
        description_text=description,
        cleaned_text=description.lower(),
        required_skills=["python", "fastapi"],
        minimum_years_experience=2.0,
    )
    db.add(job)
    db.flush()
    return job


def _make_scores(**overrides):
    base = {
        "skill_score": 80.0,
        "keyword_score": 70.0,
        "qualifications_score": 90.0,
        "experience_score": 100.0,
        "semantic_score": 75.0,
        "match_score": 83.0,
        "matched_skills": ["python", "fastapi"],
        "missing_skills": ["docker"],
        "matched_keywords": ["python", "api"],
        "missing_keywords": ["kubernetes"],
        "matched_qualifications": ["bachelor's"],
        "missing_qualifications": [],
        "recommendation": "Strong Match",
        "recommendation_reason": "Good fit",
        "ai_suggestions": ["Add Docker experience"],
        "improvements": ["Get AWS cert"],
        "explanation": ["Matched skills: python, fastapi"],
    }
    base.update(overrides)
    return base


def _make_screening_service(scores: dict) -> ScreeningService:
    """Return a ScreeningService whose matching_service always returns `scores`."""
    matching = MagicMock()
    matching.score_candidate.return_value = scores
    matching.score_candidate_profile.return_value = scores
    matching.encode_texts.return_value = [[0.1] * 384, [0.1] * 384]
    matching.compute_cosine_similarity.return_value = scores["semantic_score"]

    nlp = MagicMock()
    nlp.clean_text.side_effect = lambda t: t.lower()
    nlp.parse_job_description.return_value = {
        "cleaned_text": "python fastapi developer",
        "required_skills": ["python", "fastapi"],
        "minimum_years_experience": 2.0,
    }

    job_svc = MagicMock()
    return ScreeningService(
        matching_service=matching,
        nlp_service=nlp,
        job_service=job_svc,
    )


# ---------------------------------------------------------------------------
# 1. Entity model — all Phase 6 columns present
# ---------------------------------------------------------------------------

class ScreeningResultSchemaTests(unittest.TestCase):
    def test_all_phase6_columns_exist_on_orm_model(self):
        expected = {
            "keyword_score",
            "qualifications_score",
            "matched_keywords",
            "missing_keywords",
            "matched_qualifications",
            "missing_qualifications",
            "recommendation",
            "recommendation_reason",
            "ai_suggestions",
            "improvements",
        }
        mapper_columns = {c.key for c in ScreeningResult.__mapper__.columns}
        missing = expected - mapper_columns
        self.assertEqual(missing, set(), f"ORM model missing columns: {missing}")

    def test_screening_result_roundtrip_all_fields(self):
        engine = _make_engine()
        db = _make_session(engine)
        candidate = _seed_candidate(db)
        job = _seed_job(db)

        result = ScreeningResult(
            candidate_id=candidate.id,
            job_id=job.id,
            skill_score=80.0,
            keyword_score=70.0,
            qualifications_score=90.0,
            experience_score=100.0,
            semantic_score=75.0,
            match_score=83.0,
            matched_skills=["python"],
            missing_skills=["docker"],
            matched_keywords=["python"],
            missing_keywords=["kubernetes"],
            matched_qualifications=["bachelor's"],
            missing_qualifications=[],
            recommendation="Strong Match",
            recommendation_reason="Good fit",
            ai_suggestions=["Add Docker"],
            improvements=["Get cert"],
            explanation=["Matched: python"],
        )
        db.add(result)
        db.commit()
        db.expire_all()

        loaded = db.get(ScreeningResult, result.id)
        self.assertEqual(loaded.keyword_score, 70.0)
        self.assertEqual(loaded.qualifications_score, 90.0)
        self.assertEqual(loaded.matched_keywords, ["python"])
        self.assertEqual(loaded.missing_keywords, ["kubernetes"])
        self.assertEqual(loaded.matched_qualifications, ["bachelor's"])
        self.assertEqual(loaded.missing_qualifications, [])
        self.assertEqual(loaded.recommendation, "Strong Match")
        self.assertEqual(loaded.recommendation_reason, "Good fit")
        self.assertEqual(loaded.ai_suggestions, ["Add Docker"])
        self.assertEqual(loaded.improvements, ["Get cert"])
        db.close()


# ---------------------------------------------------------------------------
# 2. Schema migration — _upgrade_screening_results_table
# ---------------------------------------------------------------------------

class SchemaMigrationTests(unittest.TestCase):
    def _engine_without_new_cols(self):
        """Create a DB that looks like the pre-Phase-6 schema."""
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE screening_results (
                    id INTEGER PRIMARY KEY,
                    candidate_id INTEGER NOT NULL,
                    job_id INTEGER NOT NULL,
                    skill_score FLOAT NOT NULL DEFAULT 0.0,
                    experience_score FLOAT NOT NULL DEFAULT 0.0,
                    semantic_score FLOAT NOT NULL DEFAULT 0.0,
                    match_score FLOAT NOT NULL DEFAULT 0.0,
                    matched_skills JSON NOT NULL,
                    missing_skills JSON NOT NULL,
                    explanation JSON NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
        return engine

    def test_migration_adds_all_missing_columns(self):
        engine = self._engine_without_new_cols()
        # Patch the module-level engine used by _upgrade_screening_results_table
        with patch("backend.database.engine", engine):
            _upgrade_screening_results_table()

        inspector = inspect(engine)
        cols = {c["name"] for c in inspector.get_columns("screening_results")}
        for col in (
            "keyword_score", "qualifications_score",
            "matched_keywords", "missing_keywords",
            "matched_qualifications", "missing_qualifications",
            "recommendation", "recommendation_reason",
            "ai_suggestions", "improvements",
        ):
            self.assertIn(col, cols, f"Migration did not add column: {col}")

    def test_migration_is_idempotent(self):
        """Running migration twice must not raise."""
        engine = self._engine_without_new_cols()
        with patch("backend.database.engine", engine):
            _upgrade_screening_results_table()
            _upgrade_screening_results_table()  # second run — must be a no-op

        inspector = inspect(engine)
        cols = {c["name"] for c in inspector.get_columns("screening_results")}
        self.assertIn("keyword_score", cols)

    def test_migration_skips_when_table_absent(self):
        """If screening_results table doesn't exist yet, migration must not crash."""
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )
        with patch("backend.database.engine", engine):
            _upgrade_screening_results_table()  # should be a silent no-op


# ---------------------------------------------------------------------------
# 3. process_candidates — upsert via job_id path
# ---------------------------------------------------------------------------

class ProcessCandidatesUpsertTests(unittest.TestCase):
    def setUp(self):
        self.engine = _make_engine()
        self.db = _make_session(self.engine)
        self.candidate = _seed_candidate(self.db)
        self.job = _seed_job(self.db)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_first_call_inserts_row(self):
        scores = _make_scores()
        service = _make_screening_service(scores)
        service.process_candidates(self.db, self.job.id)

        rows = self.db.query(ScreeningResult).all()
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.candidate_id, self.candidate.id)
        self.assertEqual(row.job_id, self.job.id)
        self.assertEqual(row.match_score, 83.0)
        self.assertEqual(row.recommendation, "Strong Match")
        self.assertEqual(row.matched_keywords, ["python", "api"])
        self.assertEqual(row.ai_suggestions, ["Add Docker experience"])

    def test_second_call_updates_existing_row(self):
        scores_v1 = _make_scores(match_score=60.0, recommendation="Moderate Match")
        service = _make_screening_service(scores_v1)
        service.process_candidates(self.db, self.job.id)

        scores_v2 = _make_scores(match_score=90.0, recommendation="Strong Match")
        service2 = _make_screening_service(scores_v2)
        service2.process_candidates(self.db, self.job.id)

        rows = self.db.query(ScreeningResult).all()
        self.assertEqual(len(rows), 1, "Upsert must not create a duplicate row")
        self.assertEqual(rows[0].match_score, 90.0)
        self.assertEqual(rows[0].recommendation, "Strong Match")

    def test_all_phase6_fields_persisted_by_process_candidates(self):
        scores = _make_scores()
        service = _make_screening_service(scores)
        service.process_candidates(self.db, self.job.id)

        row = self.db.query(ScreeningResult).one()
        self.assertEqual(row.keyword_score, 70.0)
        self.assertEqual(row.qualifications_score, 90.0)
        self.assertEqual(row.matched_keywords, ["python", "api"])
        self.assertEqual(row.missing_keywords, ["kubernetes"])
        self.assertEqual(row.matched_qualifications, ["bachelor's"])
        self.assertEqual(row.missing_qualifications, [])
        self.assertEqual(row.recommendation, "Strong Match")
        self.assertEqual(row.recommendation_reason, "Good fit")
        self.assertEqual(row.ai_suggestions, ["Add Docker experience"])
        self.assertEqual(row.improvements, ["Get AWS cert"])

    def test_created_at_is_set_on_insert(self):
        scores = _make_scores()
        service = _make_screening_service(scores)
        service.process_candidates(self.db, self.job.id)

        row = self.db.query(ScreeningResult).one()
        self.assertIsNotNone(row.created_at)
        self.assertIsInstance(row.created_at, datetime)

    def test_created_at_is_updated_on_rescore(self):
        scores = _make_scores()
        service = _make_screening_service(scores)
        service.process_candidates(self.db, self.job.id)
        first_ts = self.db.query(ScreeningResult).one().created_at

        import time; time.sleep(0.01)
        service2 = _make_screening_service(_make_scores(match_score=55.0))
        service2.process_candidates(self.db, self.job.id)
        second_ts = self.db.query(ScreeningResult).one().created_at

        self.assertGreaterEqual(second_ts, first_ts)


# ---------------------------------------------------------------------------
# 4. match_candidates_to_job_text — upsert via raw text path
# ---------------------------------------------------------------------------

class MatchCandidatesUpsertTests(unittest.TestCase):
    def setUp(self):
        self.engine = _make_engine()
        self.db = _make_session(self.engine)
        self.candidate = _seed_candidate(self.db)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_match_inserts_job_and_result_rows(self):
        scores = _make_scores()
        service = _make_screening_service(scores)
        service.match_candidates_to_job_text(
            self.db,
            job_description="Python FastAPI developer needed",
            title="Backend Engineer",
        )

        self.assertEqual(self.db.query(JobDescription).count(), 1)
        self.assertEqual(self.db.query(ScreeningResult).count(), 1)

    def test_repeated_match_same_text_reuses_job_row(self):
        scores = _make_scores()
        service = _make_screening_service(scores)
        jd_text = "Python FastAPI developer needed"

        service.match_candidates_to_job_text(
            self.db, job_description=jd_text, title="Backend Engineer"
        )
        service.match_candidates_to_job_text(
            self.db, job_description=jd_text, title="Backend Engineer"
        )

        self.assertEqual(
            self.db.query(JobDescription).count(), 1,
            "_resolve_or_create_job_for_match must deduplicate identical job text",
        )
        self.assertEqual(
            self.db.query(ScreeningResult).count(), 1,
            "Upsert must not create a second ScreeningResult row",
        )

    def test_match_upserts_result_on_rescore(self):
        scores_v1 = _make_scores(match_score=55.0, recommendation="Weak Match")
        service = _make_screening_service(scores_v1)
        service.match_candidates_to_job_text(
            self.db,
            job_description="Python FastAPI developer needed",
            title="Backend Engineer",
        )

        scores_v2 = _make_scores(match_score=88.0, recommendation="Strong Match")
        service2 = _make_screening_service(scores_v2)
        service2.match_candidates_to_job_text(
            self.db,
            job_description="Python FastAPI developer needed",
            title="Backend Engineer",
        )

        rows = self.db.query(ScreeningResult).all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].match_score, 88.0)
        self.assertEqual(rows[0].recommendation, "Strong Match")

    def test_match_persists_all_phase6_fields(self):
        scores = _make_scores()
        service = _make_screening_service(scores)
        rankings = service.match_candidates_to_job_text(
            self.db,
            job_description="Python FastAPI developer needed",
            title="Backend Engineer",
        )

        row = self.db.query(ScreeningResult).one()
        self.assertEqual(row.keyword_score, 70.0)
        self.assertEqual(row.qualifications_score, 90.0)
        self.assertEqual(row.matched_keywords, ["python", "api"])
        self.assertEqual(row.missing_keywords, ["kubernetes"])
        self.assertEqual(row.matched_qualifications, ["bachelor's"])
        self.assertEqual(row.missing_qualifications, [])
        self.assertEqual(row.recommendation, "Strong Match")
        self.assertEqual(row.ai_suggestions, ["Add Docker experience"])
        self.assertEqual(row.improvements, ["Get AWS cert"])

        # Response must also carry the fields
        self.assertEqual(len(rankings), 1)
        rc = rankings[0]
        self.assertEqual(rc.keyword_score, 70.0)
        self.assertEqual(rc.recommendation, "Strong Match")
        self.assertIsNotNone(rc.screened_at)

    def test_different_job_titles_create_separate_jobs(self):
        scores = _make_scores()
        service = _make_screening_service(scores)
        service.match_candidates_to_job_text(
            self.db, job_description="Python developer", title="Role A"
        )
        service.match_candidates_to_job_text(
            self.db, job_description="Python developer", title="Role B"
        )

        self.assertEqual(self.db.query(JobDescription).count(), 2)


# ---------------------------------------------------------------------------
# 5. get_rankings — reads persisted data back correctly
# ---------------------------------------------------------------------------

class GetRankingsReadbackTests(unittest.TestCase):
    def setUp(self):
        self.engine = _make_engine()
        self.db = _make_session(self.engine)
        self.candidate = _seed_candidate(self.db)
        self.job = _seed_job(self.db)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def _persist_result(self, **overrides):
        scores = _make_scores(**overrides)
        service = _make_screening_service(scores)
        service.process_candidates(self.db, self.job.id)

    def test_get_rankings_returns_all_phase6_fields(self):
        self._persist_result()
        service = _make_screening_service(_make_scores())
        rankings = service.get_rankings(self.db, self.job.id)

        self.assertEqual(len(rankings), 1)
        rc = rankings[0]
        self.assertIsInstance(rc, RankedCandidate)
        self.assertEqual(rc.keyword_score, 70.0)
        self.assertEqual(rc.qualifications_score, 90.0)
        self.assertEqual(rc.matched_keywords, ["python", "api"])
        self.assertEqual(rc.missing_keywords, ["kubernetes"])
        self.assertEqual(rc.matched_qualifications, ["bachelor's"])
        self.assertEqual(rc.missing_qualifications, [])
        self.assertEqual(rc.recommendation, "Strong Match")
        self.assertEqual(rc.recommendation_reason, "Good fit")
        self.assertEqual(rc.ai_suggestions, ["Add Docker experience"])
        self.assertEqual(rc.improvements, ["Get AWS cert"])
        self.assertIsNotNone(rc.screened_at)

    def test_get_rankings_sorted_by_match_score_desc(self):
        # Add a second candidate
        candidate2 = _seed_candidate(self.db, name="Bob", skills=["python"])
        self.db.commit()

        scores_high = _make_scores(match_score=90.0)
        scores_low = _make_scores(match_score=40.0)

        matching = MagicMock()
        matching.score_candidate.side_effect = [scores_high, scores_low]
        nlp = MagicMock()
        job_svc = MagicMock()
        service = ScreeningService(matching, nlp, job_svc)
        service.process_candidates(self.db, self.job.id)

        rankings = service.get_rankings(self.db, self.job.id)
        self.assertEqual(len(rankings), 2)
        self.assertGreaterEqual(rankings[0].match_score, rankings[1].match_score)

    def test_get_rankings_empty_for_unknown_job(self):
        service = _make_screening_service(_make_scores())
        rankings = service.get_rankings(self.db, job_id=9999)
        self.assertEqual(rankings, [])

    def test_get_rankings_skill_filter(self):
        candidate2 = _seed_candidate(self.db, name="Bob", skills=["java"])
        self.db.commit()

        scores = _make_scores()
        matching = MagicMock()
        matching.score_candidate.return_value = scores
        service = ScreeningService(matching, MagicMock(), MagicMock())
        service.process_candidates(self.db, self.job.id)

        rankings_python = service.get_rankings(self.db, self.job.id, skill_filter="python")
        rankings_java = service.get_rankings(self.db, self.job.id, skill_filter="java")

        # Alice has python, Bob has java
        self.assertEqual(len(rankings_python), 1)
        self.assertEqual(rankings_python[0].candidate_name, "Alice")
        self.assertEqual(len(rankings_java), 1)
        self.assertEqual(rankings_java[0].candidate_name, "Bob")

    def test_screened_at_reflects_last_run_timestamp(self):
        self._persist_result()
        service = _make_screening_service(_make_scores())
        rankings = service.get_rankings(self.db, self.job.id)
        self.assertIsNotNone(rankings[0].screened_at)

    def test_null_phase6_fields_default_to_empty_lists(self):
        """Rows written before Phase 6 (NULL in new cols) must not crash get_rankings."""
        result = ScreeningResult(
            candidate_id=self.candidate.id,
            job_id=self.job.id,
            skill_score=50.0,
            experience_score=50.0,
            semantic_score=50.0,
            match_score=50.0,
            matched_skills=[],
            missing_skills=[],
            explanation=[],
            # Phase 6 fields intentionally omitted → NULL
        )
        self.db.add(result)
        self.db.commit()

        service = _make_screening_service(_make_scores())
        rankings = service.get_rankings(self.db, self.job.id)
        self.assertEqual(len(rankings), 1)
        rc = rankings[0]
        self.assertEqual(rc.matched_keywords, [])
        self.assertEqual(rc.missing_keywords, [])
        self.assertIsNone(rc.keyword_score)
        self.assertIsNone(rc.recommendation)


# ---------------------------------------------------------------------------
# 6. UniqueConstraint — DB-level duplicate prevention
# ---------------------------------------------------------------------------

class UniqueConstraintTests(unittest.TestCase):
    def test_unique_constraint_prevents_duplicate_rows(self):
        engine = _make_engine()
        db = _make_session(engine)
        candidate = _seed_candidate(db)
        job = _seed_job(db)
        db.commit()

        db.add(ScreeningResult(
            candidate_id=candidate.id, job_id=job.id,
            skill_score=50.0, experience_score=50.0,
            semantic_score=50.0, match_score=50.0,
            matched_skills=[], missing_skills=[], explanation=[],
        ))
        db.commit()

        from sqlalchemy.exc import IntegrityError
        with self.assertRaises(IntegrityError):
            db.add(ScreeningResult(
                candidate_id=candidate.id, job_id=job.id,
                skill_score=80.0, experience_score=80.0,
                semantic_score=80.0, match_score=80.0,
                matched_skills=[], missing_skills=[], explanation=[],
            ))
            db.commit()

        db.close()


if __name__ == "__main__":
    unittest.main()
