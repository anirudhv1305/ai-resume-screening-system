from __future__ import annotations

import logging
import re
from collections import Counter
from datetime import datetime
from functools import lru_cache

from backend.config import get_settings


logger = logging.getLogger(__name__)

EMAIL_PATTERN = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}"
)
YEAR_RANGE_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:\+|plus)?\s*(?:-|to)?\s*(\d+(?:\.\d+)?)?\s+years?",
    re.IGNORECASE,
)
EXPERIENCE_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:\+|plus)?\s+years?\s+(?:of\s+)?experience",
    re.IGNORECASE,
)
EDUCATION_PATTERN = re.compile(
    r"\b(b\.?tech|m\.?tech|bachelor(?:'s)?|master(?:'s)?|mba|ph\.?d|b\.?sc|m\.?sc|"
    r"associate|diploma|computer science|information technology|engineering)\b",
    re.IGNORECASE,
)

# Certification and degree patterns
DEGREE_PATTERN = re.compile(
    r"\b(bachelor(?:'s)?|master(?:'s)?|phd|m\.?b\.?a|associate|diploma|"
    r"b\.?(?:tech|sc|a|eng)|m\.?(?:tech|sc|a|eng))\b",
    re.IGNORECASE,
)

CERTIFICATION_PATTERN = re.compile(
    r"\b(aws certified|azure certified|gcp certified|certified kubernetes|"
    r"ciscomp|oscp|cism|cissp|pmp|itil|scrum master|oracle certified|"
    r"microsoft certified|comptia|ccna|ccnp|ccie|aws solution architect|"
    r"aws developer|azure administrator|gcp associate cloud engineer)\b",
    re.IGNORECASE,
)


class NLPService:
    def __init__(self) -> None:
        settings = get_settings()
        self.skill_catalog = settings.skill_catalog
        self._spacy_model_name = settings.spacy_model
        self._nlp = None
        self._skill_matcher = None

    @property
    def nlp(self):
        if self._nlp is None:
            self._nlp = self._load_model(self._spacy_model_name)
            self._skill_matcher = None  # reset matcher when model loads
        return self._nlp

    @property
    def skill_matcher(self):
        if self._skill_matcher is None:
            import spacy  # noqa: F401 — deferred to avoid import-time load
            from spacy.matcher import PhraseMatcher
            self._skill_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
            self._skill_matcher.add(
                "SKILLS", [self.nlp.make_doc(skill) for skill in self.skill_catalog]
            )
        return self._skill_matcher

    @staticmethod
    def _load_model(model_name: str):
        import spacy
        from spacy.language import Language  # noqa: F401
        try:
            logger.info("Loading spaCy model: %s", model_name)
            nlp = spacy.load(model_name)
        except OSError:
            logger.warning("spaCy model '%s' not found, falling back to blank 'en'.", model_name)
            nlp = spacy.blank("en")
            if "sentencizer" not in nlp.pipe_names:
                nlp.add_pipe("sentencizer")
        return nlp

    @staticmethod
    def clean_text(text: str) -> str:
        text = text.replace("\x00", " ")
        text = re.sub(r"[\r\t]+", " ", text)
        text = re.sub(r"[ ]{2,}", " ", text)
        text = re.sub(r"\n{2,}", "\n", text)
        return text.strip()

    def parse_resume(self, raw_text: str) -> dict[str, object]:
        from spacy.tokens import Doc  # noqa: F401
        cleaned = self.clean_text(raw_text)
        doc = self.nlp(cleaned)
        return {
            "cleaned_text": cleaned,
            "name": self.extract_name(cleaned, doc),
            "email": self.extract_email(cleaned),
            "phone": self.extract_phone(cleaned),
            "skills": self.extract_skills(doc),
            "education": self.extract_education(cleaned, doc),
            "experience_years": self.extract_experience_years(cleaned),
            "experience_highlights": self.extract_experience_highlights(doc),
        }

    def parse_job_description(self, raw_text: str) -> dict[str, object]:
        cleaned = self.clean_text(raw_text)
        doc = self.nlp(cleaned)
        return {
            "cleaned_text": cleaned,
            "required_skills": self.extract_skills(doc),
            "minimum_years_experience": self.extract_required_experience(cleaned),
        }

    def extract_name(self, text: str, doc) -> str | None:
        for entity in doc.ents:
            if entity.label_ == "PERSON" and len(entity.text.split()) <= 4:
                return entity.text.strip()

        first_line = text.splitlines()[0].strip() if text.splitlines() else ""
        if 1 <= len(first_line.split()) <= 4 and first_line.replace(" ", "").isalpha():
            return first_line.title()
        return None

    @staticmethod
    def extract_email(text: str) -> str | None:
        match = EMAIL_PATTERN.search(text)
        return match.group(0) if match else None

    @staticmethod
    def extract_phone(text: str) -> str | None:
        match = PHONE_PATTERN.search(text)
        return match.group(0) if match else None

    def extract_skills(self, doc) -> list[str]:
        matches = self.skill_matcher(doc)
        skills = {doc[start:end].text.lower().strip() for _, start, end in matches}
        return sorted(skills)

    def extract_education(self, text: str, doc) -> list[str]:
        results: list[str] = []
        seen: set[str] = set()

        for sentence in doc.sents:
            cleaned = sentence.text.strip()
            normalized = cleaned.lower()
            if EDUCATION_PATTERN.search(normalized) and normalized not in seen:
                results.append(cleaned)
                seen.add(normalized)
            if len(results) >= 5:
                break

        if not results:
            for line in text.splitlines():
                cleaned = line.strip()
                normalized = cleaned.lower()
                if EDUCATION_PATTERN.search(normalized) and normalized not in seen:
                    results.append(cleaned)
                    seen.add(normalized)
                if len(results) >= 5:
                    break

        return results

    def extract_experience_highlights(self, doc) -> list[str]:
        keywords = (
            "experience",
            "worked",
            "managed",
            "built",
            "developed",
            "engineer",
            "analyst",
            "lead",
            "designed",
        )

        highlights: list[str] = []
        for sentence in doc.sents:
            text = sentence.text.strip()
            lowered = text.lower()
            if any(keyword in lowered for keyword in keywords):
                highlights.append(text)
            if len(highlights) >= 5:
                break
        return highlights

    @staticmethod
    def extract_experience_years(text: str) -> float:
        experience_matches = [
            float(match.group(1)) for match in EXPERIENCE_PATTERN.finditer(text)
        ]
        if experience_matches:
            return max(experience_matches)

        current_year = datetime.now().year
        detected_years = [
            int(year)
            for year in re.findall(r"\b(?:19|20)\d{2}\b", text)
            if 1970 <= int(year) <= current_year
        ]
        if len(detected_years) >= 2:
            return float(max(min(current_year - min(detected_years), 40), 0))
        return 0.0

    @staticmethod
    def extract_required_experience(text: str) -> float:
        range_match = YEAR_RANGE_PATTERN.search(text)
        if range_match:
            return float(range_match.group(1))

        years = [float(match.group(1)) for match in EXPERIENCE_PATTERN.finditer(text)]
        if years:
            return min(years)
        return 0.0

    def extract_keywords(self, text: str, top_n: int = 10) -> list[str]:
        """
        Extract keywords from text using TF-IDF-like heuristics.
        
        Returns top N keywords based on frequency and word length.
        Filters out common stop words, short words, and generic recruiting terms.
        
        Args:
            text: Input text to extract keywords from
            top_n: Number of keywords to return (default 10)
            
        Returns:
            List of keywords sorted by relevance
        """
        if not text:
            return []
        
        # Common stop words to filter
        stop_words = {
            "the", "a", "an", "and", "or", "but", "is", "are", "was", "were",
            "be", "been", "being", "have", "has", "had", "do", "does", "did",
            "will", "would", "could", "should", "may", "might", "must", "can",
            "of", "in", "on", "at", "to", "for", "from", "by", "with", "as",
            "that", "this", "these", "those", "i", "you", "he", "she", "it",
            "we", "they", "what", "which", "who", "when", "where", "why", "how",
        }
        
        # Generic recruiting terms to filter
        generic_terms = {
            "required", "requirements", "experience", "candidate", "candidates",
            "position", "positions", "role", "roles", "job", "jobs",
            "responsibilities", "responsibility", "duties", "description",
            "skills", "skill", "ability", "abilities", "qualifications",
            "looking", "seeking", "hiring", "team", "work", "working",
            "years", "year", "company", "opportunity", "opportunities",
            "knowledge", "understanding", "degree", "bachelor", "master",
        }
        
        # Clean and tokenize
        text_lower = text.lower()
        # Split on whitespace and punctuation, preserve technical terms with +, #, ., -, /
        words = re.findall(r"\b[a-z]+(?:[+#.\-/][a-z]+)?\b", text_lower)
        
        # Filter: remove stop words, generic terms, keep words 3+ chars
        filtered_words = [
            w for w in words 
            if w not in stop_words 
            and w not in generic_terms
            and len(w) >= 3 
            and not w.isdigit()
        ]
        
        if not filtered_words:
            return []
        
        # Calculate frequency
        word_freq = Counter(filtered_words)
        
        # Get top N keywords
        top_keywords = [word for word, _ in word_freq.most_common(top_n)]
        return top_keywords

    def extract_qualifications(self, text: str) -> dict[str, list[str]]:
        """
        Extract degrees and certifications from text.
        
        Returns:
            Dictionary with 'degrees' and 'certifications' lists
        """
        if not text:
            return {"degrees": [], "certifications": []}
        
        degrees = []
        certifications = []
        seen_degrees = set()
        seen_certs = set()
        
        # Extract degrees
        for match in DEGREE_PATTERN.finditer(text):
            degree = match.group(0).strip().lower()
            normalized = degree.replace(".", "")
            if normalized not in seen_degrees:
                degrees.append(match.group(0).strip())
                seen_degrees.add(normalized)
            if len(degrees) >= 5:
                break
        
        # Extract certifications
        for match in CERTIFICATION_PATTERN.finditer(text):
            cert = match.group(0).strip().lower()
            if cert not in seen_certs:
                certifications.append(match.group(0).strip())
                seen_certs.add(cert)
            if len(certifications) >= 5:
                break
        
        return {
            "degrees": degrees,
            "certifications": certifications,
        }

    @staticmethod
    def compare_qualifications(
        candidate_quals: dict[str, list[str]],
        job_quals: dict[str, list[str]],
    ) -> dict[str, list[str]]:
        """
        Compare candidate qualifications with job requirements.
        
        Args:
            candidate_quals: Dict with 'degrees' and 'certifications' lists
            job_quals: Dict with required 'degrees' and 'certifications'
            
        Returns:
            Dict with 'matched' and 'missing' qualifications
        """
        candidate_degrees = {d.lower() for d in (candidate_quals.get("degrees") or [])}
        candidate_certs = {c.lower() for c in (candidate_quals.get("certifications") or [])}
        
        required_degrees = {d.lower() for d in (job_quals.get("degrees") or [])}
        required_certs = {c.lower() for c in (job_quals.get("certifications") or [])}
        
        matched_degrees = sorted(candidate_degrees.intersection(required_degrees))
        missing_degrees = sorted(required_degrees.difference(candidate_degrees))
        
        matched_certs = sorted(candidate_certs.intersection(required_certs))
        missing_certs = sorted(required_certs.difference(candidate_certs))
        
        return {
            "matched_degrees": matched_degrees,
            "missing_degrees": missing_degrees,
            "matched_certifications": matched_certs,
            "missing_certifications": missing_certs,
        }


@lru_cache
def get_nlp_service() -> NLPService:
    return NLPService()
