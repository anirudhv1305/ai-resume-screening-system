from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from models.entities import Candidate, JobDescription, ScreeningResult
from models.schemas import RankedCandidate
from services.job_service import JobService, get_job_service
from services.matching_service import MatchingService, get_matching_service
from services.nlp_service import NLPService, get_nlp_service


class ScreeningService:
    def __init__(
        self,
        matching_service: MatchingService,
        nlp_service: NLPService,
        job_service: JobService,
    ) -> None:
        self.matching_service = matching_service
        self.nlp_service = nlp_service
        self.job_service = job_service

    def process_candidates(
        self, db: Session, job_id: int, candidate_ids: list[int] | None = None
    ) -> list[RankedCandidate]:
        job = db.scalar(select(JobDescription).where(JobDescription.id == job_id))
        if job is None:
            raise ValueError("Job description not found.")
        if candidate_ids is not None and not candidate_ids:
            raise ValueError("At least one candidate id is required when filtering.")

        candidate_query = select(Candidate)
        if candidate_ids:
            candidate_query = candidate_query.where(Candidate.id.in_(candidate_ids))

        candidates = list(db.scalars(candidate_query).all())
        if not candidates:
            raise ValueError("No resumes available for screening.")

        for candidate in candidates:
            scores = self.matching_service.score_candidate(candidate, job)
            # Reuse the same result row when a candidate is rescored for the same job.
            result = db.scalar(
                select(ScreeningResult).where(
                    ScreeningResult.candidate_id == candidate.id,
                    ScreeningResult.job_id == job.id,
                )
            )
            if result is None:
                result = ScreeningResult(candidate_id=candidate.id, job_id=job.id)
                db.add(result)

            result.skill_score = float(scores["skill_score"])
            result.experience_score = float(scores["experience_score"])
            result.semantic_score = float(scores["semantic_score"])
            result.match_score = float(scores["match_score"])
            result.matched_skills = list(scores["matched_skills"])
            result.missing_skills = list(scores["missing_skills"])
            result.explanation = list(scores["explanation"])

        db.commit()
        return self.get_rankings(db, job_id)

    def get_rankings(
        self, db: Session, job_id: int, skill_filter: str | None = None
    ) -> list[RankedCandidate]:
        results = list(
            db.scalars(
                select(ScreeningResult)
                .options(selectinload(ScreeningResult.candidate))
                .where(ScreeningResult.job_id == job_id)
            ).all()
        )

        rankings: list[RankedCandidate] = []
        normalized_filter = skill_filter.lower().strip() if skill_filter else None

        for result in results:
            candidate = result.candidate
            if candidate is None:
                continue
            candidate_skills = [skill.lower() for skill in (candidate.skills or [])]
            if normalized_filter and normalized_filter not in candidate_skills:
                continue

            rankings.append(
                RankedCandidate(
                    candidate_id=candidate.id,
                    filename=candidate.filename,
                    candidate_name=candidate.name,
                    email=candidate.email,
                    phone=candidate.phone,
                    skills=candidate.skills or [],
                    education=candidate.education or [],
                    experience_years=float(candidate.experience_years or 0.0),
                    match_score=float(result.match_score or 0.0),
                    skill_score=float(result.skill_score or 0.0),
                    experience_score=float(result.experience_score or 0.0),
                    semantic_score=float(result.semantic_score or 0.0),
                    matched_skills=result.matched_skills or [],
                    missing_skills=result.missing_skills or [],
                    explanation=result.explanation or [],
                    screened_at=result.created_at,
                )
            )

        rankings.sort(key=lambda item: item.match_score, reverse=True)
        return rankings

    def match_candidates_to_job_text(
        self,
        db: Session,
        *,
        job_description: str,
        title: str | None = None,
        candidate_ids: list[int] | None = None,
    ) -> list[RankedCandidate]:
        if candidate_ids is not None and not candidate_ids:
            raise ValueError("At least one candidate id is required when filtering.")
        cleaned_job_text = self.nlp_service.clean_text(job_description)
        if not cleaned_job_text:
            raise ValueError("Job description text is required.")

        candidate_query = select(Candidate)
        if candidate_ids:
            candidate_query = candidate_query.where(Candidate.id.in_(candidate_ids))

        candidates = list(db.scalars(candidate_query).all())
        if not candidates:
            raise ValueError("No uploaded resumes are available for matching.")

        parsed_job = self.nlp_service.parse_job_description(cleaned_job_text)

        # Encode all resume texts plus the job description in one batch to avoid
        # recomputing the same job embedding for every candidate.
        texts_to_encode = [candidate.cleaned_text for candidate in candidates]
        texts_to_encode.append(parsed_job["cleaned_text"])
        embeddings = self.matching_service.encode_texts(texts_to_encode)
        job_embedding = embeddings[-1]

        rankings: list[RankedCandidate] = []
        for index, candidate in enumerate(candidates):
            semantic_score = self.matching_service.compute_cosine_similarity(
                embeddings[index],
                job_embedding,
            )
            scores = self.matching_service.score_candidate_profile(
                candidate=candidate,
                required_skills=list(parsed_job["required_skills"]),
                minimum_years_experience=float(
                    parsed_job["minimum_years_experience"]
                ),
                semantic_score=semantic_score,
            )

            rankings.append(
                RankedCandidate(
                    candidate_id=candidate.id,
                    filename=candidate.filename,
                    candidate_name=candidate.name,
                    email=candidate.email,
                    phone=candidate.phone,
                    skills=candidate.skills or [],
                    education=candidate.education or [],
                    experience_years=float(candidate.experience_years or 0.0),
                    match_score=float(scores["match_score"]),
                    skill_score=float(scores["skill_score"]),
                    experience_score=float(scores["experience_score"]),
                    semantic_score=float(scores["semantic_score"]),
                    matched_skills=list(scores["matched_skills"]),
                    missing_skills=list(scores["missing_skills"]),
                    explanation=list(scores["explanation"]),
                    screened_at=None,
                )
            )

        rankings.sort(key=lambda item: item.match_score, reverse=True)
        return rankings

    def process_job_text(
        self,
        db: Session,
        *,
        job_description: str,
        title: str | None = None,
        candidate_ids: list[int] | None = None,
    ) -> tuple[JobDescription, list[RankedCandidate]]:
        job = self.job_service.create_job_from_text(
            db,
            title=(title or "Ad Hoc Resume Ranking").strip(),
            description=job_description,
        )
        rankings = self.process_candidates(db, job.id, candidate_ids)
        return job, rankings

    def get_results_for_job(
        self,
        db: Session,
        *,
        job_id: int | None = None,
        skill_filter: str | None = None,
    ) -> tuple[JobDescription, list[RankedCandidate]]:
        if job_id is None:
            job = db.scalar(
                select(JobDescription).order_by(
                    JobDescription.created_at.desc(),
                    JobDescription.id.desc(),
                )
            )
        else:
            job = db.scalar(select(JobDescription).where(JobDescription.id == job_id))

        if job is None:
            raise ValueError("No ranking results are available yet.")

        rankings = self.get_rankings(db, job.id, skill_filter=skill_filter)
        return job, rankings


def get_screening_service() -> ScreeningService:
    return ScreeningService(
        get_matching_service(),
        get_nlp_service(),
        get_job_service(),
    )
