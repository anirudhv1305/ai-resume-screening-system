from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from models.entities import Candidate
from services.ai_suggestions_service import AISuggestionsService
from services.matching_service import MatchingService
from utils.ai_providers.base import AIProviderResponse


class MockAIProvider:
    """Mock AI provider for testing."""
    
    def __init__(self, response_text: str = "Test AI response", fail: bool = False):
        self.response_text = response_text
        self.fail = fail
    
    def generate(self, prompt: str, **kwargs):
        if self.fail:
            return AIProviderResponse(
                content="",
                provider="mock",
                model="test",
                success=False,
                error="Mock error",
            )
        return AIProviderResponse(
            content=self.response_text,
            provider="mock",
            model="test",
            success=True,
        )


class AISuggestionsTests(unittest.TestCase):
    
    def setUp(self):
        self.service = AISuggestionsService()
    
    @patch("services.ai_suggestions_service.get_ai_provider_factory")
    def test_generate_suggestions_with_ai(self, mock_factory_func):
        # Setup mock factory with available provider
        mock_factory = MagicMock()
        mock_factory.get_available_providers.return_value = ["mock"]
        mock_factory.generate_with_fallback.return_value = AIProviderResponse(
            content="1. Add Docker projects\n2. Get AWS certification\n3. Quantify achievements",
            provider="mock",
            model="test",
            success=True,
        )
        mock_factory_func.return_value = mock_factory
        
        service = AISuggestionsService()
        suggestions = service.generate_suggestions(
            candidate_name="John Doe",
            matched_skills=["python", "fastapi"],
            missing_skills=["docker", "kubernetes"],
            match_score=65.0,
        )
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
        self.assertTrue(any("docker" in s.lower() or "aws" in s.lower() or "achiev" in s.lower() for s in suggestions))
    
    def test_generate_suggestions_fallback(self):
        # No AI providers available
        service = AISuggestionsService()
        service.factory = MagicMock()
        service.factory.get_available_providers.return_value = []
        
        suggestions = service.generate_suggestions(
            candidate_name="John Doe",
            matched_skills=["python"],
            missing_skills=["docker", "kubernetes"],
            match_score=50.0,
        )
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
        # Should contain deterministic suggestions
        self.assertTrue(any("docker" in s.lower() or "kubernetes" in s.lower() for s in suggestions))
    
    @patch("services.ai_suggestions_service.get_ai_provider_factory")
    def test_generate_improvements_with_ai(self, mock_factory_func):
        mock_factory = MagicMock()
        mock_factory.get_available_providers.return_value = ["mock"]
        mock_factory.generate_with_fallback.return_value = AIProviderResponse(
            content="1. Focus on Docker first\n2. Get certified\n3. Build portfolio",
            provider="mock",
            model="test",
            success=True,
        )
        mock_factory_func.return_value = mock_factory
        
        service = AISuggestionsService()
        improvements = service.generate_improvements(
            missing_skills=["docker", "kubernetes"],
            missing_qualifications=["aws certified"],
            experience_gap=2.0,
        )
        
        self.assertIsInstance(improvements, list)
        self.assertGreater(len(improvements), 0)
    
    def test_generate_improvements_fallback(self):
        service = AISuggestionsService()
        service.factory = MagicMock()
        service.factory.get_available_providers.return_value = []
        
        improvements = service.generate_improvements(
            missing_skills=["docker"],
            missing_qualifications=[],
            experience_gap=0,
        )
        
        self.assertIsInstance(improvements, list)
        self.assertGreater(len(improvements), 0)
        self.assertTrue(any("docker" in imp.lower() for imp in improvements))
    
    @patch("services.ai_suggestions_service.get_ai_provider_factory")
    def test_generate_recommendation_reason_with_ai(self, mock_factory_func):
        mock_factory = MagicMock()
        mock_factory.get_available_providers.return_value = ["mock"]
        mock_factory.generate_with_fallback.return_value = AIProviderResponse(
            content="Strong candidate with excellent skill alignment and relevant experience.",
            provider="mock",
            model="test",
            success=True,
        )
        mock_factory_func.return_value = mock_factory
        
        service = AISuggestionsService()
        reason = service.generate_recommendation_reason(
            match_score=85.0,
            skill_score=90.0,
            keyword_score=80.0,
            experience_score=85.0,
            qualifications_score=100.0,
            matched_skills=["python", "docker", "kubernetes"],
            missing_skills=[],
            recommendation="Strong Match",
        )
        
        self.assertIsInstance(reason, str)
        self.assertGreater(len(reason), 10)
    
    def test_generate_recommendation_reason_fallback(self):
        service = AISuggestionsService()
        service.factory = MagicMock()
        service.factory.get_available_providers.return_value = []
        
        reason = service.generate_recommendation_reason(
            match_score=85.0,
            skill_score=90.0,
            keyword_score=80.0,
            experience_score=85.0,
            qualifications_score=100.0,
            matched_skills=["python", "docker"],
            missing_skills=["kubernetes"],
            recommendation="Strong Match",
        )
        
        self.assertIsInstance(reason, str)
        self.assertGreater(len(reason), 10)
        self.assertIn("skill", reason.lower())


class MatchingServiceAIIntegrationTests(unittest.TestCase):
    
    def setUp(self):
        self.service = MatchingService()
    
    @patch("services.ai_suggestions_service.get_ai_suggestions_service")
    def test_score_with_ai_insights_enabled(self, mock_ai_service_func):
        # Setup mock AI service
        mock_ai_service = MagicMock()
        mock_ai_service.generate_suggestions.return_value = ["Suggestion 1", "Suggestion 2"]
        mock_ai_service.generate_improvements.return_value = ["Improvement 1"]
        mock_ai_service.generate_recommendation_reason.return_value = "Good candidate"
        mock_ai_service_func.return_value = mock_ai_service
        
        candidate = Candidate(
            name="John Doe",
            skills=["python", "fastapi"],
            experience_years=3.0,
        )
        
        scores = self.service.score_candidate_profile(
            candidate=candidate,
            required_skills=["python", "fastapi", "docker"],
            minimum_years_experience=2.0,
            semantic_score=80.0,
            generate_ai_insights=True,
            job_title="Backend Engineer",
        )
        
        # Verify AI fields are present
        self.assertIn("ai_suggestions", scores)
        self.assertIn("improvements", scores)
        self.assertIn("recommendation_reason", scores)
        
        # Verify AI fields are populated
        self.assertEqual(scores["ai_suggestions"], ["Suggestion 1", "Suggestion 2"])
        self.assertEqual(scores["improvements"], ["Improvement 1"])
        self.assertEqual(scores["recommendation_reason"], "Good candidate")
        
        # Verify AI service was called
        mock_ai_service.generate_suggestions.assert_called_once()
        mock_ai_service.generate_improvements.assert_called_once()
        mock_ai_service.generate_recommendation_reason.assert_called_once()
    
    def test_score_without_ai_insights(self):
        candidate = Candidate(
            name="John Doe",
            skills=["python", "fastapi"],
            experience_years=3.0,
        )
        
        scores = self.service.score_candidate_profile(
            candidate=candidate,
            required_skills=["python", "fastapi"],
            minimum_years_experience=2.0,
            semantic_score=80.0,
            generate_ai_insights=False,
        )
        
        # Verify AI fields are NOT present
        self.assertNotIn("ai_suggestions", scores)
        self.assertNotIn("improvements", scores)
        self.assertNotIn("recommendation_reason", scores)
        
        # Verify standard fields are present
        self.assertIn("match_score", scores)
        self.assertIn("recommendation", scores)
        self.assertIn("matched_skills", scores)


class ProviderFallbackChainTests(unittest.TestCase):
    
    @patch("services.ai_suggestions_service.get_ai_provider_factory")
    def test_openai_success(self, mock_factory_func):
        mock_factory = MagicMock()
        mock_factory.get_available_providers.return_value = ["openai"]
        mock_factory.generate_with_fallback.return_value = AIProviderResponse(
            content="OpenAI suggestion",
            provider="openai",
            model="gpt-4o-mini",
            success=True,
        )
        mock_factory_func.return_value = mock_factory
        
        service = AISuggestionsService()
        suggestions = service.generate_suggestions(
            candidate_name="Test",
            matched_skills=["python"],
            missing_skills=["docker"],
            match_score=70.0,
        )
        
        self.assertGreater(len(suggestions), 0)
    
    @patch("services.ai_suggestions_service.get_ai_provider_factory")
    def test_claude_fallback(self, mock_factory_func):
        mock_factory = MagicMock()
        mock_factory.get_available_providers.return_value = ["claude"]
        mock_factory.generate_with_fallback.return_value = AIProviderResponse(
            content="Claude suggestion",
            provider="claude",
            model="claude-3-5-sonnet",
            success=True,
        )
        mock_factory_func.return_value = mock_factory
        
        service = AISuggestionsService()
        suggestions = service.generate_suggestions(
            candidate_name="Test",
            matched_skills=["python"],
            missing_skills=["docker"],
            match_score=70.0,
        )
        
        self.assertGreater(len(suggestions), 0)
    
    @patch("services.ai_suggestions_service.get_ai_provider_factory")
    def test_all_providers_fail_uses_fallback(self, mock_factory_func):
        mock_factory = MagicMock()
        mock_factory.get_available_providers.return_value = ["openai"]
        mock_factory.generate_with_fallback.return_value = AIProviderResponse(
            content="",
            provider="none",
            model="",
            success=False,
            error="All providers failed",
        )
        mock_factory_func.return_value = mock_factory
        
        service = AISuggestionsService()
        suggestions = service.generate_suggestions(
            candidate_name="Test",
            matched_skills=["python"],
            missing_skills=["docker"],
            match_score=70.0,
        )
        
        # Should still get deterministic suggestions
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)


class NoProviderScenarioTests(unittest.TestCase):
    
    def test_no_api_keys_configured(self):
        service = AISuggestionsService()
        service.factory = MagicMock()
        service.factory.get_available_providers.return_value = []
        
        # Should work with deterministic fallback
        suggestions = service.generate_suggestions(
            candidate_name="Test",
            matched_skills=["python"],
            missing_skills=["docker", "kubernetes"],
            match_score=60.0,
        )
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
    
    def test_missing_api_key_graceful_degradation(self):
        service = AISuggestionsService()
        service.factory = MagicMock()
        service.factory.get_available_providers.return_value = []
        
        # All three functions should work
        suggestions = service.generate_suggestions(
            candidate_name="Test",
            matched_skills=[],
            missing_skills=["docker"],
            match_score=50.0,
        )
        
        improvements = service.generate_improvements(
            missing_skills=["docker"],
            missing_qualifications=[],
            experience_gap=0,
        )
        
        reason = service.generate_recommendation_reason(
            match_score=50.0,
            skill_score=40.0,
            keyword_score=50.0,
            experience_score=60.0,
            qualifications_score=70.0,
            matched_skills=[],
            missing_skills=["docker"],
            recommendation="Weak Match",
        )
        
        self.assertIsInstance(suggestions, list)
        self.assertIsInstance(improvements, list)
        self.assertIsInstance(reason, str)
        self.assertGreater(len(suggestions), 0)
        self.assertGreater(len(improvements), 0)
        self.assertGreater(len(reason), 0)


if __name__ == "__main__":
    unittest.main()
