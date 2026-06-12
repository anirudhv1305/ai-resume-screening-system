from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.config import get_settings
from models.entities import JobDescription
from services.nlp_service import NLPService, get_nlp_service
from services.resume_service import ResumeService
from utils.file_validation import validate_uploaded_file


class JobService:
    def __init__(self, nlp_service: NLPService) -> None:
        self.settings = get_settings()
        self.nlp_service = nlp_service

    async def create_job(
        self,
        db: Session,
        title: str,
        description: str | None = None,
        file: UploadFile | None = None,
    ) -> JobDescription:
        if not title.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job title is required.",
            )

        source_filename: str | None = None
        storage_path: str | None = None
        uploaded_text = ""

        saved_path: Path | None = None
        try:
            if file and file.filename:
                source_filename = Path(file.filename).name
                saved_path = await self._save_file(file, self.settings.job_dir)
                storage_path = str(saved_path)
                uploaded_text = self._extract_job_text(saved_path)

            final_text = "\n".join(
                part for part in [description or "", uploaded_text] if part
            ).strip()
            if not final_text:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Provide a job description in text or file form.",
                )

            parsed_job = self.nlp_service.parse_job_description(final_text)
            job = JobDescription(
                title=title.strip(),
                source_filename=source_filename,
                storage_path=storage_path,
                description_text=final_text,
                cleaned_text=parsed_job["cleaned_text"],
                required_skills=parsed_job["required_skills"],
                minimum_years_experience=parsed_job["minimum_years_experience"],
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            return job
        except Exception:
            db.rollback()
            if saved_path and saved_path.exists():
                saved_path.unlink()
            raise

    def create_job_from_text(
        self,
        db: Session,
        *,
        title: str,
        description: str,
    ) -> JobDescription:
        if not title.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job title is required.",
            )

        cleaned_text = self.nlp_service.clean_text(description)
        if not cleaned_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job description text is required.",
            )

        parsed_job = self.nlp_service.parse_job_description(cleaned_text)
        job = JobDescription(
            title=title.strip(),
            source_filename=None,
            storage_path=None,
            description_text=cleaned_text,
            cleaned_text=parsed_job["cleaned_text"],
            required_skills=parsed_job["required_skills"],
            minimum_years_experience=parsed_job["minimum_years_experience"],
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    async def _save_file(self, file: UploadFile, directory: Path) -> Path:
        safe_filename = Path(file.filename or "job-description.txt").name
        unique_name = f"{uuid4().hex}_{safe_filename}"
        destination = directory / unique_name
        content = await file.read()
        try:
            validate_uploaded_file(
                filename=file.filename,
                content=content,
                allowed_extensions={".pdf", ".txt"},
                entity_name="Job description",
            )
            destination.write_bytes(content)
        finally:
            await file.close()
        return destination

    @staticmethod
    def _extract_job_text(path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return ResumeService.extract_text_from_pdf(path)
        if suffix == ".txt":
            return path.read_text(encoding="utf-8")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description uploads must be .pdf or .txt files.",
        )


def get_job_service() -> JobService:
    return JobService(get_nlp_service())
