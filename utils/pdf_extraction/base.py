"""Abstract base class for PDF extraction strategies."""

from abc import ABC, abstractmethod
from pathlib import Path


class PDFExtractor(ABC):
    """Abstract base class for PDF extraction implementations."""

    @abstractmethod
    def extract(self, file_path: str) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            Extracted text as a string.
            
        Raises:
            Exception: If extraction fails.
        """
        pass

    @staticmethod
    def _calculate_quality_score(text: str) -> dict:
        """
        Calculate quality metrics for extracted text.
        
        Args:
            text: Extracted text.
            
        Returns:
            Dictionary with quality metrics:
            - text_length: Total character count
            - word_count: Total word count
            - printable_ratio: Ratio of printable characters to total characters
            - score: Overall quality score (0-100)
        """
        if not text:
            return {
                "text_length": 0,
                "word_count": 0,
                "printable_ratio": 0.0,
                "score": 0,
            }

        text_length = len(text)
        word_count = len(text.split())

        # Count printable characters (exclude control chars, excessive whitespace)
        printable_chars = sum(
            1
            for c in text
            if c.isprintable() or c in ("\n", "\t", "\r")
        )
        printable_ratio = printable_chars / text_length if text_length > 0 else 0.0

        # Quality score based on:
        # - Text length (more is better, but diminishing returns after 1000 chars)
        # - Word count (more meaningful words is better)
        # - Printability (higher ratio is better)
        length_score = min(text_length / 1000 * 50, 50)  # Max 50 points
        word_score = min(word_count / 100 * 30, 30)  # Max 30 points
        printable_score = printable_ratio * 20  # Max 20 points

        score = round(length_score + word_score + printable_score, 2)

        return {
            "text_length": text_length,
            "word_count": word_count,
            "printable_ratio": round(printable_ratio, 4),
            "score": score,
        }
