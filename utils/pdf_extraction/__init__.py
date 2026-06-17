"""PDF extraction module with fallback strategy."""

from utils.pdf_extraction.fallback import PDFExtractionStrategy
from utils.pdf_extraction.pdfplumber_extractor import PDFPlumberExtractor
from utils.pdf_extraction.pymupdf_extractor import PyMuPDFExtractor
from utils.pdf_extraction.pypdf2_extractor import PyPDF2Extractor

__all__ = [
    "PDFExtractionStrategy",
    "PyMuPDFExtractor",
    "PyPDF2Extractor",
    "PDFPlumberExtractor",
]
