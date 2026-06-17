"""Tests for PDF extraction with fallback strategy."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from utils.pdf_extraction import (
    PDFExtractionStrategy,
    PDFPlumberExtractor,
    PyMuPDFExtractor,
    PyPDF2Extractor,
)
from utils.pdf_extraction.base import PDFExtractor


class TestPDFExtractor:
    """Test PDFExtractor base class."""

    def test_quality_score_empty_text(self):
        """Test quality scoring for empty text."""
        score = PDFExtractor._calculate_quality_score("")
        assert score["text_length"] == 0
        assert score["word_count"] == 0
        assert score["printable_ratio"] == 0.0
        assert score["score"] == 0

    def test_quality_score_short_text(self):
        """Test quality scoring for short text."""
        text = "Hello World"
        score = PDFExtractor._calculate_quality_score(text)
        assert score["text_length"] == len(text)
        assert score["word_count"] == 2
        assert score["printable_ratio"] == 1.0
        assert 0 < score["score"] < 100

    def test_quality_score_long_text(self):
        """Test quality scoring for longer text."""
        text = "This is a resume with much more content. " * 50
        score = PDFExtractor._calculate_quality_score(text)
        assert score["text_length"] > 500
        assert score["word_count"] > 50
        assert score["printable_ratio"] > 0.9
        assert 80 < score["score"] <= 100

    def test_quality_score_text_with_special_chars(self):
        """Test quality scoring for text with special characters."""
        text = "Hello\x00World\nTest\tData"
        score = PDFExtractor._calculate_quality_score(text)
        assert score["text_length"] > 0
        assert score["word_count"] > 0
        # Printable ratio should account for control characters
        assert 0 <= score["printable_ratio"] <= 1.0


class TestPyMuPDFExtractor:
    """Test PyMuPDF extraction."""

    @patch("utils.pdf_extraction.pymupdf_extractor.fitz.open")
    def test_successful_extraction(self, mock_fitz_open):
        """Test successful PyMuPDF extraction."""
        mock_doc = MagicMock()
        mock_page1 = MagicMock()
        mock_page2 = MagicMock()
        mock_page1.get_text.return_value = "Page 1 content"
        mock_page2.get_text.return_value = "Page 2 content"
        # Make the document iterable
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page1, mock_page2]))
        mock_fitz_open.return_value.__enter__.return_value = mock_doc

        extractor = PyMuPDFExtractor()
        result = extractor.extract("test.pdf")
        
        assert "Page 1 content" in result
        assert "Page 2 content" in result
        assert "\n" in result

    @patch("utils.pdf_extraction.pymupdf_extractor.fitz.open")
    def test_extraction_error(self, mock_fitz_open):
        """Test PyMuPDF extraction error handling."""
        mock_fitz_open.side_effect = RuntimeError("Invalid PDF")

        extractor = PyMuPDFExtractor()
        with pytest.raises(RuntimeError, match="PyMuPDF extraction failed"):
            extractor.extract("test.pdf")


class TestPyPDF2Extractor:
    """Test PyPDF2 extraction."""

    @patch("utils.pdf_extraction.pypdf2_extractor.PdfReader")
    @patch("builtins.open", create=True)
    def test_successful_extraction(self, mock_file_open, mock_pdf_reader):
        """Test successful PyPDF2 extraction."""
        mock_page1 = MagicMock()
        mock_page2 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2.extract_text.return_value = "Page 2 content"
        
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader

        extractor = PyPDF2Extractor()
        result = extractor.extract("test.pdf")
        
        assert "Page 1 content" in result
        assert "Page 2 content" in result

    @patch("utils.pdf_extraction.pypdf2_extractor.PdfReader")
    @patch("builtins.open", create=True)
    def test_partial_extraction_with_error(self, mock_file_open, mock_pdf_reader):
        """Test PyPDF2 extraction with one page failing."""
        mock_page1 = MagicMock()
        mock_page2 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2.extract_text.side_effect = Exception("Page 2 error")
        
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader

        extractor = PyPDF2Extractor()
        result = extractor.extract("test.pdf")
        
        # Should contain successful page
        assert "Page 1 content" in result


class TestPDFPlumberExtractor:
    """Test pdfplumber extraction."""

    @patch("utils.pdf_extraction.pdfplumber_extractor.pdfplumber.open")
    def test_successful_extraction(self, mock_pdfplumber_open):
        """Test successful pdfplumber extraction."""
        mock_page1 = MagicMock()
        mock_page2 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2.extract_text.return_value = "Page 2 content"
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        extractor = PDFPlumberExtractor()
        result = extractor.extract("test.pdf")
        
        assert "Page 1 content" in result
        assert "Page 2 content" in result

    @patch("utils.pdf_extraction.pdfplumber_extractor.pdfplumber.open")
    def test_extraction_error(self, mock_pdfplumber_open):
        """Test pdfplumber extraction error handling."""
        mock_pdfplumber_open.side_effect = RuntimeError("Invalid PDF")

        extractor = PDFPlumberExtractor()
        with pytest.raises(RuntimeError, match="pdfplumber extraction failed"):
            extractor.extract("test.pdf")


class TestPDFExtractionStrategy:
    """Test PDF extraction fallback strategy."""

    @patch("utils.pdf_extraction.fallback.PyMuPDFExtractor.extract")
    def test_successful_extraction_primary(self, mock_pymupdf_extract):
        """Test fallback strategy with successful primary extractor."""
        mock_pymupdf_extract.return_value = "Extracted text"

        strategy = PDFExtractionStrategy()
        result = strategy.extract("test.pdf")
        
        assert result == "Extracted text"
        # Verify primary was called
        mock_pymupdf_extract.assert_called_once()

    @patch("utils.pdf_extraction.fallback.PyMuPDFExtractor.extract")
    @patch("utils.pdf_extraction.fallback.PyPDF2Extractor.extract")
    def test_fallback_to_pypdf2(
        self, mock_pypdf2_extract, mock_pymupdf_extract
    ):
        """Test fallback to PyPDF2 when PyMuPDF fails."""
        mock_pymupdf_extract.side_effect = RuntimeError("PyMuPDF failed")
        mock_pypdf2_extract.return_value = "PyPDF2 extracted text"

        strategy = PDFExtractionStrategy()
        result = strategy.extract("test.pdf")
        
        assert result == "PyPDF2 extracted text"
        mock_pymupdf_extract.assert_called_once()
        mock_pypdf2_extract.assert_called_once()

    @patch("utils.pdf_extraction.fallback.PyMuPDFExtractor.extract")
    @patch("utils.pdf_extraction.fallback.PyPDF2Extractor.extract")
    @patch("utils.pdf_extraction.fallback.PDFPlumberExtractor.extract")
    def test_fallback_to_pdfplumber(
        self, mock_pdfplumber_extract, mock_pypdf2_extract, mock_pymupdf_extract
    ):
        """Test fallback all the way to pdfplumber."""
        mock_pymupdf_extract.side_effect = RuntimeError("PyMuPDF failed")
        mock_pypdf2_extract.side_effect = RuntimeError("PyPDF2 failed")
        mock_pdfplumber_extract.return_value = "pdfplumber extracted text"

        strategy = PDFExtractionStrategy()
        result = strategy.extract("test.pdf")
        
        assert result == "pdfplumber extracted text"
        mock_pymupdf_extract.assert_called_once()
        mock_pypdf2_extract.assert_called_once()
        mock_pdfplumber_extract.assert_called_once()

    @patch("utils.pdf_extraction.fallback.PyMuPDFExtractor.extract")
    @patch("utils.pdf_extraction.fallback.PyPDF2Extractor.extract")
    @patch("utils.pdf_extraction.fallback.PDFPlumberExtractor.extract")
    def test_all_extractors_fail(
        self, mock_pdfplumber_extract, mock_pypdf2_extract, mock_pymupdf_extract
    ):
        """Test when all extractors fail."""
        mock_pymupdf_extract.side_effect = RuntimeError("PyMuPDF failed")
        mock_pypdf2_extract.side_effect = RuntimeError("PyPDF2 failed")
        mock_pdfplumber_extract.side_effect = RuntimeError("pdfplumber failed")

        strategy = PDFExtractionStrategy()
        with pytest.raises(RuntimeError, match="All PDF extraction methods failed"):
            strategy.extract("test.pdf")

    @patch("utils.pdf_extraction.fallback.PyMuPDFExtractor.extract")
    @patch("utils.pdf_extraction.fallback.PyPDF2Extractor.extract")
    def test_quality_based_selection(self, mock_pypdf2_extract, mock_pymupdf_extract):
        """Test that strategy selects best quality result."""
        # PyMuPDF returns short result (low quality)
        mock_pymupdf_extract.return_value = "Short"
        # PyPDF2 returns longer result (higher quality)
        mock_pypdf2_extract.return_value = "Much longer extracted text from PyPDF2"

        strategy = PDFExtractionStrategy()
        result = strategy.extract("test.pdf")
        
        # Should select PyPDF2 result due to better quality
        assert result == "Much longer extracted text from PyPDF2"

    @patch("utils.pdf_extraction.fallback.PyMuPDFExtractor.extract")
    def test_extraction_report(self, mock_pymupdf_extract):
        """Test extraction report generation."""
        mock_pymupdf_extract.return_value = "Extracted text"

        strategy = PDFExtractionStrategy()
        strategy.extract("test.pdf")
        report = strategy.get_extraction_report()
        
        assert "attempts" in report
        assert "results" in report
        assert len(report["results"]) > 0
        assert report["results"][0]["success"] is True
        assert "quality" in report["results"][0]


class TestPDFExtractionIntegration:
    """Integration tests for PDF extraction."""

    def test_empty_pdf_handling(self):
        """Test handling of empty PDF (all extractors return empty string)."""
        with patch("utils.pdf_extraction.fallback.PyMuPDFExtractor.extract") as m1, \
             patch("utils.pdf_extraction.fallback.PyPDF2Extractor.extract") as m2, \
             patch("utils.pdf_extraction.fallback.PDFPlumberExtractor.extract") as m3:
            
            m1.return_value = ""
            m2.return_value = ""
            m3.return_value = ""

            strategy = PDFExtractionStrategy()
            result = strategy.extract("empty.pdf")
            
            # Should return empty string (best quality score is 0)
            assert result == ""

    def test_corrupted_pdf_handling(self):
        """Test handling of corrupted PDF."""
        with patch("utils.pdf_extraction.fallback.PyMuPDFExtractor.extract") as m1, \
             patch("utils.pdf_extraction.fallback.PyPDF2Extractor.extract") as m2, \
             patch("utils.pdf_extraction.fallback.PDFPlumberExtractor.extract") as m3:
            
            m1.side_effect = RuntimeError("Corrupted")
            m2.return_value = "Partial recovery from PyPDF2"
            m3.side_effect = RuntimeError("Also failed")

            strategy = PDFExtractionStrategy()
            result = strategy.extract("corrupted.pdf")
            
            assert result == "Partial recovery from PyPDF2"
            report = strategy.get_extraction_report()
            
            # Verify report shows failure and success
            assert report["results"][0]["success"] is False
            assert report["results"][1]["success"] is True
            assert report["results"][2]["success"] is False
