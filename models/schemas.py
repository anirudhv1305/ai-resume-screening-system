from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CandidateRead(BaseModel):
    id: int
    filename: str
    storage_path: str | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experience_years: float = 0.0
    score: float | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class JobRead(BaseModel):
    id: int
    title: str
    source_filename: str | None = None
    description_text: str = ""
    required_skills: list[str] = Field(default_factory=list)
    minimum_years_experience: float = 0.0
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class CandidateUploadResponse(BaseModel):
    uploaded_count: int
    candidates: list[CandidateRead]


class ResumeDeleteResponse(BaseModel):
    id: int
    filename: str
    deleted: bool
    file_removed: bool
    message: str


class JobUploadResponse(BaseModel):
    job: JobRead


class ProcessRequest(BaseModel):
    job_id: int
    candidate_ids: list[int] | None = None


class DirectMatchRequest(BaseModel):
    job_description: str
    title: str | None = None
    candidate_ids: list[int] | None = None
    generate_ai_insights: bool = False  # Phase 5: Optional AI insights


class RankRequest(BaseModel):
    job_description: str = Field(min_length=1)
    title: str | None = None
    candidate_ids: list[int] | None = None


class RankedCandidate(BaseModel):
    candidate_id: int
    filename: str
    candidate_name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experience_years: float = 0.0
    match_score: float
    skill_score: float
    experience_score: float
    semantic_score: float
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    explanation: list[str] = Field(default_factory=list)
    screened_at: datetime | None = None
    # Phase 6: keyword + qualification fields
    keyword_score: float | None = None
    qualifications_score: float | None = None
    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    matched_qualifications: list[str] = Field(default_factory=list)
    missing_qualifications: list[str] = Field(default_factory=list)
    # Phase 5: AI-enhanced fields (optional, backward compatible)
    ai_suggestions: list[str] | None = None
    improvements: list[str] | None = None
    recommendation: str | None = None
    recommendation_reason: str | None = None


class RankingResponse(BaseModel):
    job_id: int
    total_candidates: int
    rankings: list[RankedCandidate]


class ProcessResponse(RankingResponse):
    processed_count: int


class DirectMatchResponse(BaseModel):
    job_title: str | None = None
    total_candidates: int
    rankings: list[RankedCandidate]


class CandidateResult(BaseModel):
    name: str
    score: float
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    explanation: str


class ResultsResponse(BaseModel):
    job_id: int
    job_title: str | None = None
    results: list[CandidateResult]
