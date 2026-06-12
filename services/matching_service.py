from __future__ import annotations

import logging
from functools import lru_cache

from backend.config import get_settings
from models.entities import Candidate, JobDescription


logger = logging.getLogger(__name__)


class MatchingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._model = None

    @property
    def model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info("Loading SentenceTransformer model: %s", self.settings.sentence_transformer_model)
                self._model = SentenceTransformer(
                    self.settings.sentence_transformer_model,
                    device="cpu",
                )
            except Exception as exc:
                logger.error("Failed to load SentenceTransformer: %s", exc)
                raise RuntimeError(
                    "Sentence Transformer model could not be loaded. "
                    "Install dependencies and ensure the model is downloadable."
                ) from exc
        return self._model

    def encode_texts(self, texts: list[str]):
        if not texts:
            raise ValueError("At least one text input is required for embedding.")

        return self.model.encode(
            texts,
            convert_to_tensor=True,
            normalize_embeddings=True,
        )

    @staticmethod
    def compute_cosine_similarity(resume_embedding, job_embedding) -> float:
        from sentence_transformers import util
        similarity = util.cos_sim(resume_embedding, job_embedding).item()
        return round(max(min(similarity, 1.0), 0.0) * 100, 2)

    def semantic_similarity(self, resume_text: str, job_text: str) -> float:
        if not resume_text or not job_text:
            return 0.0

        embeddings = self.encode_texts([resume_text, job_text])
        return self.compute_cosine_similarity(embeddings[0], embeddings[1])

    def score_candidate(
        self, candidate: Candidate, job: JobDescription
    ) -> dict[str, float | list[str]]:
        semantic_score = self.semantic_similarity(candidate.cleaned_text, job.cleaned_text)
        return self.score_candidate_profile(
            candidate=candidate,
            required_skills=job.required_skills or [],
            minimum_years_experience=float(job.minimum_years_experience or 0.0),
            semantic_score=semantic_score,
        )

    def score_candidate_profile(
        self,
        *,
        candidate: Candidate,
        required_skills: list[str],
        minimum_years_experience: float,
        semantic_score: float,
    ) -> dict[str, float | list[str]]:
        candidate_skills = {skill.lower() for skill in (candidate.skills or [])}
        required_skill_set = {skill.lower() for skill in required_skills}

        matched_skills = sorted(candidate_skills.intersection(required_skill_set))
        missing_skills = sorted(required_skill_set.difference(candidate_skills))

        skill_score = 100.0
        if required_skill_set:
            skill_score = round(
                (len(matched_skills) / len(required_skill_set)) * 100,
                2,
            )

        required_years = float(minimum_years_experience or 0.0)
        candidate_years = float(candidate.experience_years or 0.0)
        experience_score = 100.0
        if required_years > 0:
            experience_score = round(min(candidate_years / required_years, 1.0) * 100, 2)

        final_score = round(
            (skill_score * self.settings.skill_weight)
            + (experience_score * self.settings.experience_weight)
            + (semantic_score * self.settings.semantic_weight),
            2,
        )

        explanation = self._build_explanation(
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            skill_score=skill_score,
            experience_score=experience_score,
            semantic_score=semantic_score,
            candidate_years=candidate_years,
            required_years=required_years,
        )

        return {
            "skill_score": skill_score,
            "experience_score": experience_score,
            "semantic_score": semantic_score,
            "match_score": final_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "explanation": explanation,
        }

    @staticmethod
    def _build_explanation(
        *,
        matched_skills: list[str],
        missing_skills: list[str],
        skill_score: float,
        experience_score: float,
        semantic_score: float,
        candidate_years: float,
        required_years: float,
    ) -> list[str]:
        explanation: list[str] = []
        if matched_skills:
            explanation.append("Matched skills: " + ", ".join(matched_skills[:6]))
        else:
            explanation.append("No direct skill overlap was detected from the parsed resume.")

        if required_years > 0:
            explanation.append(
                f"Experience fit: candidate {candidate_years:.1f} years vs "
                f"required {required_years:.1f} years."
            )
        else:
            explanation.append("No minimum years of experience were explicitly requested.")

        if missing_skills:
            explanation.append("Missing or weaker skills: " + ", ".join(missing_skills[:6]))

        explanation.append(
            f"Semantic alignment score: {semantic_score:.1f}/100 and skill score "
            f"{skill_score:.1f}/100."
        )
        if experience_score < 60:
            explanation.append("Experience score is lower than the target profile.")
        return explanation


@lru_cache
def get_matching_service() -> MatchingService:
    return MatchingService()
