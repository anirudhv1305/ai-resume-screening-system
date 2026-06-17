from __future__ import annotations

import unittest

from models.entities import Candidate
from services.matching_service import MatchingService
from services.nlp_service import NLPService


class KeywordExtractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.nlp = NLPService()

    def test_extract_keywords_basic(self) -> None:
        text = "Python developer with machine learning experience and data analysis skills"
        keywords = self.nlp.extract_keywords(text, top_n=5)
        
        self.assertIsInstance(keywords, list)
        self.assertGreater(len(keywords), 0)
        self.assertIn("python", keywords)
        self.assertIn("developer", keywords)

    def test_extract_keywords_filters_stop_words(self) -> None:
        text = "The candidate has experience with Python and Java programming"
        keywords = self.nlp.extract_keywords(text, top_n=10)
        
        stop_words = ["the", "has", "with", "and"]
        for word in stop_words:
            self.assertNotIn(word, keywords)
    
    def test_extract_keywords_filters_generic_terms(self) -> None:
        text = "Required skills: Python, Java. Candidate must have 5 years experience in the role."
        keywords = self.nlp.extract_keywords(text, top_n=10)
        
        # Should filter generic recruiting terms
        generic_terms = ["required", "requirements", "experience", "candidate", "role", "years"]
        for term in generic_terms:
            self.assertNotIn(term, keywords)
        
        # Should keep technical terms
        self.assertIn("python", keywords)
        self.assertIn("java", keywords)

    def test_extract_keywords_empty_text(self) -> None:
        keywords = self.nlp.extract_keywords("", top_n=10)
        self.assertEqual(keywords, [])

    def test_extract_keywords_respects_top_n(self) -> None:
        text = "Python Java JavaScript TypeScript Ruby Go Rust PHP Kotlin Swift Dart Scala"
        keywords = self.nlp.extract_keywords(text, top_n=3)
        self.assertLessEqual(len(keywords), 3)


class QualificationDetectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.nlp = NLPService()

    def test_extract_qualifications_degrees(self) -> None:
        text = "Bachelor's in Computer Science and Master's in Data Science"
        quals = self.nlp.extract_qualifications(text)
        
        self.assertIn("degrees", quals)
        self.assertIn("certifications", quals)
        self.assertGreater(len(quals["degrees"]), 0)
        self.assertTrue(any("bachelor" in d.lower() for d in quals["degrees"]))
        self.assertTrue(any("master" in d.lower() for d in quals["degrees"]))

    def test_extract_qualifications_certifications(self) -> None:
        text = "AWS Certified Solutions Architect and Azure Certified Administrator"
        quals = self.nlp.extract_qualifications(text)
        
        self.assertGreater(len(quals["certifications"]), 0)
        self.assertTrue(any("aws" in c.lower() for c in quals["certifications"]))

    def test_extract_qualifications_empty_text(self) -> None:
        quals = self.nlp.extract_qualifications("")
        self.assertEqual(quals["degrees"], [])
        self.assertEqual(quals["certifications"], [])

    def test_compare_qualifications_matching(self) -> None:
        candidate_quals = {
            "degrees": ["Bachelor's", "Master's"],
            "certifications": ["AWS Certified"]
        }
        job_quals = {
            "degrees": ["Bachelor's"],
            "certifications": ["AWS Certified", "Azure Certified"]
        }
        
        comparison = NLPService.compare_qualifications(candidate_quals, job_quals)
        
        self.assertIn("matched_degrees", comparison)
        self.assertIn("missing_degrees", comparison)
        self.assertIn("matched_certifications", comparison)
        self.assertIn("missing_certifications", comparison)
        self.assertIn("bachelor's", comparison["matched_degrees"])
        self.assertIn("aws certified", comparison["matched_certifications"])
        self.assertIn("azure certified", comparison["missing_certifications"])


class RecommendationClassificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = MatchingService()

    def test_strong_match_classification(self) -> None:
        recommendation = self.service._categorize_recommendation(85.0)
        self.assertEqual(recommendation, "Strong Match")
        
        recommendation = self.service._categorize_recommendation(80.0)
        self.assertEqual(recommendation, "Strong Match")
        
        recommendation = self.service._categorize_recommendation(100.0)
        self.assertEqual(recommendation, "Strong Match")

    def test_moderate_match_classification(self) -> None:
        recommendation = self.service._categorize_recommendation(70.0)
        self.assertEqual(recommendation, "Moderate Match")
        
        recommendation = self.service._categorize_recommendation(60.0)
        self.assertEqual(recommendation, "Moderate Match")
        
        recommendation = self.service._categorize_recommendation(79.9)
        self.assertEqual(recommendation, "Moderate Match")

    def test_weak_match_classification(self) -> None:
        recommendation = self.service._categorize_recommendation(50.0)
        self.assertEqual(recommendation, "Weak Match")
        
        recommendation = self.service._categorize_recommendation(0.0)
        self.assertEqual(recommendation, "Weak Match")
        
        recommendation = self.service._categorize_recommendation(59.9)
        self.assertEqual(recommendation, "Weak Match")


class WeightedScoringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = MatchingService()

    def test_weighted_score_all_dimensions(self) -> None:
        candidate = Candidate(
            skills=["python", "fastapi", "sql"],
            experience_years=5.0
        )
        
        scores = self.service.score_candidate_profile(
            candidate=candidate,
            required_skills=["python", "fastapi", "sql"],
            minimum_years_experience=5.0,
            semantic_score=90.0,
            candidate_keywords=["python", "api", "database"],
            job_keywords=["python", "api", "database"],
            candidate_qualifications={"degrees": ["Bachelor's"], "certifications": ["AWS Certified"]},
            job_qualifications={"degrees": ["Bachelor's"], "certifications": ["AWS Certified"]},
        )
        
        self.assertEqual(scores["skill_score"], 100.0)
        self.assertEqual(scores["keyword_score"], 100.0)
        self.assertEqual(scores["experience_score"], 100.0)
        self.assertEqual(scores["qualifications_score"], 100.0)
        self.assertEqual(scores["semantic_score"], 90.0)
        
        # Expected: 100*0.4 + 100*0.2 + 100*0.2 + 100*0.1 + 90*0.1 = 40 + 20 + 20 + 10 + 9 = 99.0
        self.assertEqual(scores["match_score"], 99.0)
        self.assertEqual(scores["recommendation"], "Strong Match")

    def test_weighted_score_partial_match(self) -> None:
        candidate = Candidate(
            skills=["python"],
            experience_years=2.0
        )
        
        scores = self.service.score_candidate_profile(
            candidate=candidate,
            required_skills=["python", "java", "sql"],
            minimum_years_experience=5.0,
            semantic_score=60.0,
            candidate_keywords=["python"],
            job_keywords=["python", "java", "database"],
            candidate_qualifications={"degrees": [], "certifications": []},
            job_qualifications={"degrees": ["Bachelor's"], "certifications": ["AWS Certified"]},
        )
        
        self.assertAlmostEqual(scores["skill_score"], 33.33, places=1)
        self.assertAlmostEqual(scores["keyword_score"], 33.33, places=1)
        self.assertEqual(scores["experience_score"], 40.0)
        self.assertEqual(scores["qualifications_score"], 0.0)
        self.assertEqual(scores["semantic_score"], 60.0)
        
        # Expected: 33.33*0.4 + 33.33*0.2 + 40*0.2 + 0*0.1 + 60*0.1 = 13.33 + 6.67 + 8 + 0 + 6 = 34.0
        self.assertAlmostEqual(scores["match_score"], 34.0, places=0)
        self.assertEqual(scores["recommendation"], "Weak Match")

    def test_weighted_score_backward_compatibility(self) -> None:
        # Test that old calls without keywords/qualifications still work
        candidate = Candidate(
            skills=["python", "fastapi"],
            experience_years=3.0
        )
        
        scores = self.service.score_candidate_profile(
            candidate=candidate,
            required_skills=["python", "fastapi"],
            minimum_years_experience=2.0,
            semantic_score=85.0,
        )
        
        self.assertEqual(scores["skill_score"], 100.0)
        self.assertEqual(scores["keyword_score"], 100.0)  # Default when not provided
        self.assertEqual(scores["experience_score"], 100.0)
        self.assertEqual(scores["qualifications_score"], 100.0)  # Default when not provided
        self.assertEqual(scores["semantic_score"], 85.0)
        
        # Expected: 100*0.4 + 100*0.2 + 100*0.2 + 100*0.1 + 85*0.1 = 40 + 20 + 20 + 10 + 8.5 = 98.5
        self.assertEqual(scores["match_score"], 98.5)

    def test_explanation_includes_all_dimensions(self) -> None:
        candidate = Candidate(
            skills=["python", "react"],
            experience_years=4.0
        )
        
        scores = self.service.score_candidate_profile(
            candidate=candidate,
            required_skills=["python", "java"],
            minimum_years_experience=3.0,
            semantic_score=70.0,
            candidate_keywords=["python", "web"],
            job_keywords=["python", "java", "backend"],
        )
        
        explanation = scores["explanation"]
        self.assertIsInstance(explanation, list)
        self.assertGreater(len(explanation), 0)
        
        # Check explanation contains relevant info
        explanation_text = " ".join(explanation).lower()
        self.assertIn("skill", explanation_text)
        self.assertIn("keyword", explanation_text)
        self.assertIn("experience", explanation_text)


if __name__ == "__main__":
    unittest.main()
