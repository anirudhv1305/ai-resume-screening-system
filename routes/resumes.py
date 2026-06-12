from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.dependencies import get_db
from models.schemas import CandidateRead, CandidateUploadResponse, ResumeDeleteResponse
from services.resume_service import get_resume_service


router = APIRouter(tags=["Resumes"])


@router.post("/resumes/upload", response_model=CandidateUploadResponse)
async def upload_resumes(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
) -> CandidateUploadResponse:
    service = get_resume_service()
    candidates = await service.upload_resumes(db, files)
    return CandidateUploadResponse(uploaded_count=len(candidates), candidates=candidates)


@router.get("/resumes", response_model=list[CandidateRead])
def list_candidates(db: Session = Depends(get_db)) -> list[CandidateRead]:
    service = get_resume_service()
    return service.list_resumes(db)


@router.delete("/resume/{resume_id}", response_model=ResumeDeleteResponse)
def delete_resume(
    resume_id: int,
    db: Session = Depends(get_db),
) -> ResumeDeleteResponse:
    service = get_resume_service()
    return service.delete_resume(db, resume_id)


@router.get("/resume/{resume_id}/download")
def download_resume(
    resume_id: int,
    db: Session = Depends(get_db),
) -> FileResponse:
    service = get_resume_service()
    resume_path, filename = service.get_resume_file(db, resume_id)
    return FileResponse(path=resume_path, filename=filename, media_type="application/pdf")
