from __future__ import annotations

import asyncio
import importlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

from backend.config import get_settings
from models.entities import Candidate
from services.job_service import JobService
from services.matching_service import MatchingService
from services.resume_service import ResumeService
from services.screening_service import ScreeningService


class FakeUploadFile:
    def __init__(self, filename: str, content: bytes) -> None:
        self.filename = filename
        self._content = content
        self.closed = False

    async def read(self) -> bytes:
        return self._content

    async def close(self) -> None:
        self.closed = True


class BackendStartupTests(unittest.TestCase):
    def test_backend_main_imports_with_noisy_debug_env(self) -> None:
        with patch.dict(os.environ, {"DEBUG": "release"}):
            get_settings.cache_clear()
            module = importlib.import_module("backend.main")
            importlib.reload(module)

        get_settings.cache_clear()
        self.assertEqual(module.app.title, "AI Resume Screening System")


class MatchingServiceTests(unittest.TestCase):
    def test_score_candidate_profile_uses_expected_weights(self) -> None:
        service = MatchingService()
        candidate = Candidate(skills=["python", "fastapi"], experience_years=2.0)

        scores = service.score_candidate_profile(
            candidate=candidate,
            required_skills=["python", "sql"],
            minimum_years_experience=4.0,
            semantic_score=80.0,
        )

        self.assertEqual(scores["skill_score"], 50.0)
        self.assertEqual(scores["experience_score"], 50.0)
        self.assertEqual(scores["semantic_score"], 80.0)
        # New weights: skill=40%, keyword=20%(default 100), exp=20%, qual=10%(default 100), semantic=10%
        # 50*0.4 + 100*0.2 + 50*0.2 + 100*0.1 + 80*0.1 = 20 + 20 + 10 + 10 + 8 = 68.0
        self.assertEqual(scores["match_score"], 68.0)
        self.assertEqual(scores["matched_skills"], ["python"])
        self.assertEqual(scores["missing_skills"], ["sql"])
        self.assertEqual(scores["recommendation"], "Moderate Match")


class ScreeningServiceTests(unittest.TestCase):
    def test_empty_candidate_filter_is_rejected(self) -> None:
        service = ScreeningService(
            matching_service=object(),
            nlp_service=object(),
            job_service=object(),
        )

        with self.assertRaisesRegex(ValueError, "At least one candidate id"):
            service.match_candidates_to_job_text(
                object(),
                job_description="Need Python experience",
                candidate_ids=[],
            )


class UploadSafetyTests(unittest.TestCase):
    def test_job_upload_filename_is_sanitized(self) -> None:
        service = JobService(nlp_service=object())

        directory = Path("backend/storage/jobs/test-upload-temp")
        directory.mkdir(parents=True, exist_ok=True)
        saved_path = None
        try:
            upload = FakeUploadFile("..\\nested/evil.txt", b"Python developer")
            saved_path = asyncio.run(service._save_file(upload, directory))

            self.assertEqual(saved_path.parent, Path(directory))
            self.assertTrue(saved_path.name.endswith("_evil.txt"))
            self.assertTrue(upload.closed)
            self.assertEqual(saved_path.read_bytes(), b"Python developer")
        finally:
            if saved_path and saved_path.exists():
                saved_path.unlink()
            if directory.exists():
                directory.rmdir()

    def test_resume_path_must_stay_inside_allowed_roots(self) -> None:
        service = ResumeService(nlp_service=object())

        with self.assertRaises(HTTPException):
            service._resolve_resume_path(str(Path(tempfile.gettempdir()) / "escape.pdf"))


if __name__ == "__main__":
    unittest.main()
