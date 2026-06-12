from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.dependencies import get_db
from models.entities import JobDescription
from models.schemas import JobRead, JobUploadResponse
from services.job_service import get_job_service


router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("/upload", response_model=JobUploadResponse)
async def upload_job_description(
    title: Annotated[str, Form(...)],
    description: Annotated[str | None, Form()] = None,
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
) -> JobUploadResponse:
    service = get_job_service()
    job = await service.create_job(db, title=title, description=description, file=file)
    return JobUploadResponse(job=job)


@router.get("", response_model=list[JobRead])
def list_jobs(db: Session = Depends(get_db)) -> list[JobDescription]:
    return list(
        db.scalars(select(JobDescription).order_by(JobDescription.created_at.desc())).all()
    )
