"""AI Suggestions Service for Phase 5."""

from __future__ import annotations

import logging
from functools import lru_cache

from utils.ai_prompts import AIPromptTemplates
from utils.ai_providers import get_ai_provider_factory


logger = logging.getLogger(__name__)


class AISuggestionsService:
    """Service for generating AI-powered suggestions and recommendations."""
    
    def __init__(self):
        self.factory = get_ai_provider_factory()
        self.prompts = AIPromptTemplates()
    
    def generate_suggestions(
        self,
        *,
        candidate_name: str | None,
        matched_skills: list[str],
        missing_skills: list[str],
        matched_keywords: list[str] | None = None,
        missing_keywords: list[str] | None = None,
        match_score: float,
        job_title: str | None = None,
    ) -> list[str]:
        """
        Generate personalized improvement suggestions for a candidate.
        
        Returns list of actionable suggestions.
        Falls back to deterministic suggestions if AI unavailable.
        """
        # Try AI providers first
        if self.factory.get_available_providers():
            prompt = self.prompts.resume_improvement_suggestions(
                candidate_name=candidate_name or "Candidate",
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                matched_keywords=matched_keywords or [],
                missing_keywords=missing_keywords or [],
                match_score=match_score,
                job_title=job_title or "the target position",
            )
            
            response = self.factory.generate_with_fallback(
                prompt,
                temperature=0.7,
                max_tokens=500,
            )
            
            if response.success:
                logger.info(f"AI suggestions generated via {response.provider}")
                return self._parse_suggestions(response.content)
        
        # Fallback to deterministic suggestions
        logger.info("Using deterministic fallback for suggestions")
        return self._generate_deterministic_suggestions(
            missing_skills=missing_skills,
            missing_keywords=missing_keywords or [],
            match_score=match_score,
        )
    
    def generate_improvements(
        self,
        *,
        missing_skills: list[str],
        missing_qualifications: list[str] | None = None,
        experience_gap: float = 0.0,
    ) -> list[str]:
        """
        Generate prioritized improvement recommendations.
        
        Returns list of improvement recommendations.
        Falls back to deterministic improvements if AI unavailable.
        """
        # Try AI providers first
        if self.factory.get_available_providers():
            prompt = self.prompts.skill_gap_analysis(
                missing_skills=missing_skills,
                missing_qualifications=missing_qualifications or [],
                experience_gap=experience_gap,
            )
            
            response = self.factory.generate_with_fallback(
                prompt,
                temperature=0.7,
                max_tokens=400,
            )
            
            if response.success:
                logger.info(f"AI improvements generated via {response.provider}")
                return self._parse_suggestions(response.content)
        
        # Fallback to deterministic improvements
        logger.info("Using deterministic fallback for improvements")
        return self._generate_deterministic_improvements(
            missing_skills=missing_skills,
            missing_qualifications=missing_qualifications or [],
            experience_gap=experience_gap,
        )
    
    def generate_recommendation_reason(
        self,
        *,
        match_score: float,
        skill_score: float,
        keyword_score: float,
        experience_score: float,
        qualifications_score: float,
        matched_skills: list[str],
        missing_skills: list[str],
        recommendation: str,
    ) -> str:
        """
        Generate AI-enhanced explanation for recommendation.
        
        Returns explanation string.
        Falls back to deterministic explanation if AI unavailable.
        """
        # Try AI providers first
        if self.factory.get_available_providers():
            prompt = self.prompts.recommendation_explanation(
                match_score=match_score,
                skill_score=skill_score,
                keyword_score=keyword_score,
                experience_score=experience_score,
                qualifications_score=qualifications_score,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                recommendation=recommendation,
            )
            
            response = self.factory.generate_with_fallback(
                prompt,
                temperature=0.6,
                max_tokens=200,
            )
            
            if response.success:
                logger.info(f"AI recommendation reason generated via {response.provider}")
                return response.content.strip()
        
        # Fallback to deterministic explanation
        logger.info("Using deterministic fallback for recommendation reason")
        return self._generate_deterministic_reason(
            match_score=match_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            recommendation=recommendation,
        )
    
    @staticmethod
    def _parse_suggestions(ai_response: str) -> list[str]:
        """Parse AI response into list of suggestions."""
        suggestions = []
        lines = ai_response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove numbering (1., 2., etc.) and bullet points
            line = line.lstrip('0123456789.-•*# \t')
            
            if len(line) > 10:  # Ignore very short lines
                suggestions.append(line)
        
        return suggestions[:10]  # Limit to 10 suggestions
    
    @staticmethod
    def _generate_deterministic_suggestions(
        missing_skills: list[str],
        missing_keywords: list[str],
        match_score: float,
    ) -> list[str]:
        """Generate deterministic fallback suggestions."""
        suggestions = []
        
        if missing_skills:
            top_skills = missing_skills[:3]
            suggestions.append(
                f"Add projects or experience demonstrating: {', '.join(top_skills)}"
            )
            if len(missing_skills) > 3:
                suggestions.append(
                    f"Consider obtaining certifications in: {', '.join(missing_skills[3:6])}"
                )
        
        if missing_keywords:
            suggestions.append(
                "Incorporate relevant industry keywords throughout your resume"
            )
        
        if match_score < 60:
            suggestions.append(
                "Quantify your achievements with specific metrics and results"
            )
            suggestions.append(
                "Tailor your resume summary to highlight alignment with job requirements"
            )
        elif match_score < 80:
            suggestions.append(
                "Expand on relevant projects that demonstrate required skills"
            )
        
        if not suggestions:
            suggestions.append(
                "Continue building experience in your current skill areas"
            )
        
        return suggestions[:5]
    
    @staticmethod
    def _generate_deterministic_improvements(
        missing_skills: list[str],
        missing_qualifications: list[str],
        experience_gap: float,
    ) -> list[str]:
        """Generate deterministic fallback improvements."""
        improvements = []
        
        if missing_skills:
            improvements.append(
                f"Priority skills to develop: {', '.join(missing_skills[:4])}"
            )
        
        if missing_qualifications:
            improvements.append(
                f"Consider pursuing: {', '.join(missing_qualifications[:3])}"
            )
        
        if experience_gap > 0:
            improvements.append(
                f"Gain {experience_gap:.1f} more years of relevant experience"
            )
        
        if not improvements:
            improvements.append(
                "Continue developing expertise in your current skill areas"
            )
        
        return improvements[:5]
    
    @staticmethod
    def _generate_deterministic_reason(
        match_score: float,
        matched_skills: list[str],
        missing_skills: list[str],
        recommendation: str,
    ) -> str:
        """Generate deterministic fallback recommendation reason."""
        if match_score >= 80:
            skills_text = f"with strong alignment in {len(matched_skills)} key skills"
            gap_text = f" and {len(missing_skills)} areas for growth" if missing_skills else ""
            return f"Candidate demonstrates {skills_text}{gap_text}."
        elif match_score >= 60:
            return f"Candidate matches {len(matched_skills)} required skills but has gaps in {len(missing_skills)} areas."
        else:
            return f"Candidate shows potential but requires development in {len(missing_skills)} key skill areas."


@lru_cache
def get_ai_suggestions_service() -> AISuggestionsService:
    """Get singleton AISuggestionsService instance."""
    return AISuggestionsService()
