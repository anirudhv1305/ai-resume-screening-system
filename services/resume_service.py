from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import fitz
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.config import get_settings
from models.entities import Candidate
from models.schemas import CandidateRead, ResumeDeleteResponse
from services.nlp_service import NLPService, get_nlp_service
from utils.file_validation import validate_uploaded_file


class ResumeService:
    def __init__(self, nlp_service: NLPService) -> None:
        self.settings = get_settings()
        self.nlp_service = nlp_service

    async def upload_resumes(
        self, db: Session, files: list[UploadFile]
    ) -> list[Candidate]:
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one resume PDF must be uploaded.",
            )

        candidates: list[Candidate] = []
        saved_paths: list[Path] = []
        try:
            for file in files:
                self._validate_pdf(file)
                saved_path = await self._save_file(file, self.settings.resume_dir)
                saved_paths.append(saved_path)
                resume_text = self.extract_text_from_pdf(saved_path)
                if not resume_text.strip():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"No readable text found in {file.filename}.",
                    )

                parsed_resume = self.nlp_service.parse_resume(resume_text)
                original_filename = Path(file.filename or saved_path.name).name
                candidate = Candidate(
                    filename=original_filename,
                    storage_path=str(saved_path),
                    name=parsed_resume["name"],
                    email=parsed_resume["email"],
                    phone=parsed_resume["phone"],
                    resume_text=resume_text,
                    cleaned_text=parsed_resume["cleaned_text"],
                    skills=parsed_resume["skills"],
                    education=parsed_resume["education"],
                    experience_years=parsed_resume["experience_years"],
                    experience_highlights=parsed_resume["experience_highlights"],
                )
                db.add(candidate)
                candidates.append(candidate)

            db.commit()
        except Exception:
            db.rollback()
            for saved_path in saved_paths:
                if saved_path.exists():
                    saved_path.unlink()
            raise

        for candidate in candidates:
            db.refresh(candidate)
        return candidates

    def list_resumes(self, db: Session) -> list[CandidateRead]:
        candidates = list(
            db.scalars(
                select(Candidate)
                .options(selectinload(Candidate.screening_results))
                .order_by(Candidate.created_at.desc())
            ).all()
        )
        return [self._build_resume_summary(candidate) for candidate in candidates]

    def delete_resume(self, db: Session, resume_id: int) -> ResumeDeleteResponse:
        candidate = db.get(Candidate, resume_id)
        if candidate is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with id {resume_id} was not found.",
            )

        file_removed = False
        file_missing = False
        if candidate.storage_path:
            resume_path = self._resolve_resume_path(candidate.storage_path)
            if resume_path.exists():
                resume_path.unlink()
                file_removed = True
            else:
                file_missing = True

        response = ResumeDeleteResponse(
            id=candidate.id,
            filename=candidate.filename,
            deleted=True,
            file_removed=file_removed,
            message=(
                "Resume record deleted, but the file was already missing on disk."
                if file_missing
                else "Resume deleted successfully."
            ),
        )

        db.delete(candidate)
        db.commit()
        return response

    def get_resume_file(self, db: Session, resume_id: int) -> tuple[Path, str]:
        candidate = db.get(Candidate, resume_id)
        if candidate is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with id {resume_id} was not found.",
            )
        if not candidate.storage_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume file path is missing for this record.",
            )

        resume_path = self._resolve_resume_path(candidate.storage_path)
        if not resume_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume file could not be found on disk.",
            )
        return resume_path, candidate.filename

    @staticmethod
    def _validate_pdf(file: UploadFile) -> None:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resume uploads must be PDF files.",
            )

    async def _save_file(self, file: UploadFile, directory: Path) -> Path:
        safe_filename = Path(file.filename or "resume.pdf").name
        unique_name = f"{uuid4().hex}_{safe_filename}"
        destination = directory / unique_name
        content = await file.read()
        try:
            validate_uploaded_file(
                filename=file.filename,
                content=content,
                allowed_extensions={".pdf"},
                entity_name="Resume",
            )
            destination.write_bytes(content)
        finally:
            await file.close()
        return destination

    def _resolve_resume_path(self, storage_path: str) -> Path:
        candidate_path = Path(storage_path).resolve()
        allowed_roots = [
            self.settings.resume_dir.resolve(),
            (self.settings.storage_dir / "resumes").resolve(),
        ]

        for allowed_root in allowed_roots:
            try:
                candidate_path.relative_to(allowed_root)
                return candidate_path
            except ValueError:
                continue

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stored resume path is invalid.",
        )

    @staticmethod
    def _latest_score(candidate: Candidate) -> float | None:
        if not candidate.screening_results:
            return None

        latest_result = max(
            candidate.screening_results,
            key=lambda result: (
                result.created_at.isoformat() if result.created_at else "",
                result.id,
            ),
        )
        return float(latest_result.match_score)

    def _build_resume_summary(self, candidate: Candidate) -> CandidateRead:
        return CandidateRead(
            id=candidate.id,
            filename=candidate.filename,
            storage_path=candidate.storage_path,
            name=candidate.name,
            email=candidate.email,
            phone=candidate.phone,
            skills=candidate.skills or [],
            education=candidate.education or [],
            experience_years=float(candidate.experience_years or 0.0),
            score=self._latest_score(candidate),
            created_at=candidate.created_at,
        )

    @staticmethod
    def extract_text_from_pdf(path: Path) -> str:
        try:
            with fitz.open(path) as document:
                pages = [page.get_text("text") for page in document]
        except Exception as exc:  # pragma: no cover
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse PDF {path.name}: {exc}",
            ) from exc
        return "\n".join(pages)


def get_resume_service() -> ResumeService:
    return ResumeService(get_nlp_service())
