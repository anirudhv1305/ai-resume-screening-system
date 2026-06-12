from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from backend.dependencies import get_db
from models.schemas import CandidateUploadResponse, RankRequest, ResultsResponse
from services.resume_service import get_resume_service
from services.screening_service import get_screening_service
from utils.result_formatters import build_results_response


router = APIRouter(tags=["ATS"])


@router.post("/upload", response_model=CandidateUploadResponse)
async def upload_candidates(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
) -> CandidateUploadResponse:
    service = get_resume_service()
    candidates = await service.upload_resumes(db, files)
    return CandidateUploadResponse(uploaded_count=len(candidates), candidates=candidates)


@router.post("/rank", response_model=ResultsResponse)
def rank_candidates(
    payload: RankRequest,
    db: Session = Depends(get_db),
) -> ResultsResponse:
    service = get_screening_service()
    try:
        job, rankings = service.process_job_text(
            db,
            job_description=payload.job_description,
            title=payload.title,
            candidate_ids=payload.candidate_ids,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return build_results_response(job=job, rankings=rankings)


@router.get("/results", response_model=ResultsResponse)
def get_results(
    job_id: int | None = Query(default=None),
    skill: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ResultsResponse:
    service = get_screening_service()
    try:
        job, rankings = service.get_results_for_job(
            db,
            job_id=job_id,
            skill_filter=skill,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return build_results_response(job=job, rankings=rankings)
