from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.dependencies import get_db
from models.schemas import (
    DirectMatchRequest,
    DirectMatchResponse,
    ProcessRequest,
    ProcessResponse,
    RankingResponse,
)
from services.screening_service import get_screening_service


router = APIRouter(prefix="/screening", tags=["Screening"])


@router.post("/process", response_model=ProcessResponse)
def process_resumes(
    payload: ProcessRequest, db: Session = Depends(get_db)
) -> ProcessResponse:
    service = get_screening_service()
    try:
        rankings = service.process_candidates(
            db, job_id=payload.job_id, candidate_ids=payload.candidate_ids
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc

    return ProcessResponse(
        job_id=payload.job_id,
        processed_count=len(rankings),
        total_candidates=len(rankings),
        rankings=rankings,
    )


@router.get("/rankings/{job_id}", response_model=RankingResponse)
def get_ranked_candidates(
    job_id: int,
    skill: str | None = Query(default=None, description="Optional skill filter"),
    db: Session = Depends(get_db),
) -> RankingResponse:
    service = get_screening_service()
    rankings = service.get_rankings(db, job_id=job_id, skill_filter=skill)
    return RankingResponse(job_id=job_id, total_candidates=len(rankings), rankings=rankings)


@router.post("/match", response_model=DirectMatchResponse)
def match_uploaded_resumes(
    payload: DirectMatchRequest,
    db: Session = Depends(get_db),
) -> DirectMatchResponse:
    service = get_screening_service()
    try:
        rankings = service.match_candidates_to_job_text(
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

    return DirectMatchResponse(
        job_title=payload.title,
        total_candidates=len(rankings),
        rankings=rankings,
    )
