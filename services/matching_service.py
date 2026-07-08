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

        import torch

        if not hasattr(self, "_embedding_cache"):
            self._embedding_cache = {}

        embeddings = []
        texts_to_compute = []
        compute_indices = []

        for idx, text in enumerate(texts):
            if text in self._embedding_cache:
                embeddings.append(self._embedding_cache[text])
            else:
                embeddings.append(None)
                texts_to_compute.append(text)
                compute_indices.append(idx)

        if texts_to_compute:
            with torch.inference_mode():
                computed = self.model.encode(
                    texts_to_compute,
                    convert_to_tensor=True,
                    normalize_embeddings=True,
                )
            for sub_idx, idx in enumerate(compute_indices):
                emb = computed[sub_idx]
                self._embedding_cache[texts_to_compute[sub_idx]] = emb
                embeddings[idx] = emb

            # Bounded cache size to avoid memory leaks
            while len(self._embedding_cache) > 200:
                self._embedding_cache.pop(next(iter(self._embedding_cache)))

        return torch.stack(embeddings)

    @staticmethod
    def compute_cosine_similarity(resume_embedding, job_embedding) -> float:
        from sentence_transformers import util
        similarity = util.cos_sim(resume_embedding, job_embedding).item()
        return round(max(min(similarity, 1.0), 0.0) * 100, 2)

    def semantic_similarity(self, resume_text: str, job_text: str) -> float:
        if not resume_text or not job_text:
            return 0.0

        # Truncate to ~2000 chars — model max is 512 tokens, extra text is wasted work
        embeddings = self.encode_texts([resume_text[:2000], job_text[:2000]])
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
        candidate_keywords: list[str] | None = None,
        job_keywords: list[str] | None = None,
        candidate_qualifications: dict | None = None,
        job_qualifications: dict | None = None,
        generate_ai_insights: bool = False,
        job_title: str | None = None,
    ) -> dict[str, float | list[str] | str]:
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

        # Calculate keyword score (default 100 if not provided)
        keyword_score = 100.0
        matched_keywords: list[str] = []
        missing_keywords: list[str] = []
        
        if candidate_keywords is not None and job_keywords is not None:
            candidate_kw_set = {kw.lower() for kw in candidate_keywords}
            job_kw_set = {kw.lower() for kw in job_keywords}
            matched_keywords = sorted(candidate_kw_set.intersection(job_kw_set))
            missing_keywords = sorted(job_kw_set.difference(candidate_kw_set))
            
            if job_kw_set:
                keyword_score = round(
                    (len(matched_keywords) / len(job_kw_set)) * 100,
                    2,
                )

        # Calculate qualifications score (default 100 if not provided)
        qualifications_score = 100.0
        matched_qualifications: list[str] = []
        missing_qualifications: list[str] = []
        
        if candidate_qualifications is not None and job_qualifications is not None:
            from services.nlp_service import NLPService
            comparison = NLPService.compare_qualifications(
                candidate_qualifications, job_qualifications
            )
            matched_degrees = comparison.get("matched_degrees", [])
            missing_degrees = comparison.get("missing_degrees", [])
            matched_certs = comparison.get("matched_certifications", [])
            missing_certs = comparison.get("missing_certifications", [])
            
            matched_qualifications = sorted(matched_degrees + matched_certs)
            missing_qualifications = sorted(missing_degrees + missing_certs)
            
            total_required = len(missing_degrees) + len(matched_degrees) + len(missing_certs) + len(matched_certs)
            if total_required > 0:
                qualifications_score = round(
                    ((len(matched_degrees) + len(matched_certs)) / total_required) * 100,
                    2,
                )

        # Calculate final score with new weights
        final_score = round(
            (skill_score * self.settings.skill_weight)
            + (keyword_score * self.settings.keyword_weight)
            + (experience_score * self.settings.experience_weight)
            + (qualifications_score * self.settings.qualifications_weight)
            + (semantic_score * self.settings.education_weight),  # education_weight repurposed for semantic
            2,
        )

        # Determine recommendation
        recommendation = self._categorize_recommendation(final_score)

        explanation = self._build_explanation(
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
            skill_score=skill_score,
            keyword_score=keyword_score,
            experience_score=experience_score,
            qualifications_score=qualifications_score,
            semantic_score=semantic_score,
            candidate_years=candidate_years,
            required_years=required_years,
        )

        result = {
            "skill_score": skill_score,
            "keyword_score": keyword_score,
            "experience_score": experience_score,
            "qualifications_score": qualifications_score,
            "semantic_score": semantic_score,
            "match_score": final_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "matched_keywords": matched_keywords,
            "missing_keywords": missing_keywords,
            "matched_qualifications": matched_qualifications,
            "missing_qualifications": missing_qualifications,
            "recommendation": recommendation,
            "explanation": explanation,
        }

        # Optionally generate AI insights
        if generate_ai_insights:
            from services.ai_suggestions_service import get_ai_suggestions_service
            
            ai_service = get_ai_suggestions_service()
            
            # Generate AI suggestions
            ai_suggestions = ai_service.generate_suggestions(
                candidate_name=candidate.name,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                matched_keywords=matched_keywords,
                missing_keywords=missing_keywords,
                match_score=final_score,
                job_title=job_title,
            )
            
            # Generate AI improvements
            experience_gap = max(0, required_years - candidate_years)
            improvements = ai_service.generate_improvements(
                missing_skills=missing_skills,
                missing_qualifications=missing_qualifications,
                experience_gap=experience_gap,
            )
            
            # Generate AI recommendation reason
            recommendation_reason = ai_service.generate_recommendation_reason(
                match_score=final_score,
                skill_score=skill_score,
                keyword_score=keyword_score,
                experience_score=experience_score,
                qualifications_score=qualifications_score,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                recommendation=recommendation,
            )
            
            result["ai_suggestions"] = ai_suggestions
            result["improvements"] = improvements
            result["recommendation_reason"] = recommendation_reason

        return result

    @staticmethod
    def _categorize_recommendation(score: float) -> str:
        """Categorize candidate based on match score."""
        if score >= 80.0:
            return "Strong Match"
        elif score >= 60.0:
            return "Moderate Match"
        else:
            return "Weak Match"

    @staticmethod
    def _build_explanation(
        *,
        matched_skills: list[str],
        missing_skills: list[str],
        matched_keywords: list[str],
        missing_keywords: list[str],
        skill_score: float,
        keyword_score: float,
        experience_score: float,
        qualifications_score: float,
        semantic_score: float,
        candidate_years: float,
        required_years: float,
    ) -> list[str]:
        explanation: list[str] = []
        if matched_skills:
            explanation.append("Matched skills: " + ", ".join(matched_skills[:6]))
        else:
            explanation.append("No direct skill overlap was detected from the parsed resume.")

        if matched_keywords:
            explanation.append("Matched keywords: " + ", ".join(matched_keywords[:6]))

        if required_years > 0:
            explanation.append(
                f"Experience fit: candidate {candidate_years:.1f} years vs "
                f"required {required_years:.1f} years."
            )
        else:
            explanation.append("No minimum years of experience were explicitly requested.")

        if missing_skills:
            explanation.append("Missing or weaker skills: " + ", ".join(missing_skills[:6]))

        if missing_keywords:
            explanation.append("Missing keywords: " + ", ".join(missing_keywords[:6]))

        explanation.append(
            f"Scores - Skill: {skill_score:.1f}/100, Keyword: {keyword_score:.1f}/100, "
            f"Experience: {experience_score:.1f}/100, Qualifications: {qualifications_score:.1f}/100, "
            f"Semantic: {semantic_score:.1f}/100"
        )
        return explanation


@lru_cache
def get_matching_service() -> MatchingService:
    return MatchingService()
