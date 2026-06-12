from __future__ import annotations

import logging
import re
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


@lru_cache
def get_nlp_service() -> NLPService:
    return NLPService()
