"""Centralized AI prompt templates for Phase 5."""

from __future__ import annotations


class AIPromptTemplates:
    """Reusable prompt templates for AI provider interactions."""
    
    @staticmethod
    def resume_improvement_suggestions(
        candidate_name: str,
        matched_skills: list[str],
        missing_skills: list[str],
        matched_keywords: list[str],
        missing_keywords: list[str],
        match_score: float,
        job_title: str = "the target position",
    ) -> str:
        """Generate prompt for resume improvement suggestions."""
        return f"""You are an expert resume consultant. Analyze this candidate's profile against the job requirements.

Candidate: {candidate_name}
Job: {job_title}
Overall Match Score: {match_score}/100

Matched Skills: {', '.join(matched_skills) if matched_skills else 'None'}
Missing Skills: {', '.join(missing_skills) if missing_skills else 'None'}

Matched Keywords: {', '.join(matched_keywords[:10]) if matched_keywords else 'None'}
Missing Keywords: {', '.join(missing_keywords[:10]) if missing_keywords else 'None'}

Provide 3-5 specific, actionable suggestions to improve this resume for the target role.
Each suggestion should:
- Be specific and actionable
- Address identified gaps
- Be professional and constructive
- Focus on measurable improvements

Format as a numbered list. Be concise and direct."""

    @staticmethod
    def skill_gap_analysis(
        missing_skills: list[str],
        missing_qualifications: list[str],
        experience_gap: float,
    ) -> str:
        """Generate prompt for skill gap analysis."""
        gap_info = []
        if missing_skills:
            gap_info.append(f"Missing Skills: {', '.join(missing_skills)}")
        if missing_qualifications:
            gap_info.append(f"Missing Qualifications: {', '.join(missing_qualifications)}")
        if experience_gap > 0:
            gap_info.append(f"Experience Gap: {experience_gap} years needed")
        
        gaps_text = "\n".join(gap_info) if gap_info else "No significant gaps"
        
        return f"""Analyze these skill and qualification gaps for a job candidate:

{gaps_text}

Provide 3-5 prioritized improvement recommendations.
Focus on:
- Most impactful skills to develop first
- Realistic timeline for improvement
- Alternative qualifications if applicable
- How to demonstrate existing transferable skills

Format as a numbered list. Be practical and encouraging."""

    @staticmethod
    def recommendation_explanation(
        match_score: float,
        skill_score: float,
        keyword_score: float,
        experience_score: float,
        qualifications_score: float,
        matched_skills: list[str],
        missing_skills: list[str],
        recommendation: str,
    ) -> str:
        """Generate prompt for recommendation explanation."""
        return f"""Generate a professional, concise explanation for this candidate recommendation.

Recommendation: {recommendation}
Overall Match: {match_score}/100

Score Breakdown:
- Skills: {skill_score}/100
- Keywords: {keyword_score}/100
- Experience: {experience_score}/100
- Qualifications: {qualifications_score}/100

Matched Skills: {', '.join(matched_skills[:10]) if matched_skills else 'None'}
Missing Skills: {', '.join(missing_skills[:5]) if missing_skills else 'None'}

Write 1-2 sentences explaining why this candidate received this recommendation.
Be specific about strengths and note any significant gaps.
Professional tone. No placeholders."""

    @staticmethod
    def resume_enhancement_prompt(
        resume_text: str,
        job_requirements: str,
        missing_elements: list[str],
    ) -> str:
        """Generate prompt for resume enhancement suggestions."""
        return f"""Review this resume against the job requirements and suggest specific enhancements.

Job Requirements:
{job_requirements[:500]}...

Missing Elements:
{', '.join(missing_elements) if missing_elements else 'Various skills and qualifications'}

Resume Excerpt:
{resume_text[:1000]}...

Provide 4-6 specific recommendations to strengthen this resume:
1. What sections to expand or add
2. What skills/keywords to emphasize
3. What achievements to quantify
4. What formatting improvements to make

Be specific and actionable. Format as numbered list."""

    @staticmethod
    def qualification_gap_recommendations(
        candidate_degrees: list[str],
        candidate_certs: list[str],
        required_degrees: list[str],
        required_certs: list[str],
    ) -> str:
        """Generate prompt for qualification gap recommendations."""
        return f"""Analyze qualification gaps between candidate and job requirements.

Candidate Has:
- Degrees: {', '.join(candidate_degrees) if candidate_degrees else 'None listed'}
- Certifications: {', '.join(candidate_certs) if candidate_certs else 'None listed'}

Job Requires:
- Degrees: {', '.join(required_degrees) if required_degrees else 'None specified'}
- Certifications: {', '.join(required_certs) if required_certs else 'None specified'}

Provide 2-4 recommendations:
- Highlight equivalent qualifications if applicable
- Suggest relevant certifications to pursue
- Recommend work experience to compensate
- Suggest online courses or bootcamps

Be constructive and realistic. Format as numbered list."""
