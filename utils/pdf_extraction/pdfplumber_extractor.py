"""pdfplumber PDF extraction implementation."""

from utils.pdf_extraction.base import PDFExtractor
import importlib

class LazyModule:
    def __init__(self, name):
        self._name = name
        self._mod = None

    def _load(self):
        if self._mod is None:
            self._mod = importlib.import_module(self._name)
        return self._mod

    def __getattr__(self, item):
        return getattr(self._load(), item)

    def __setattr__(self, key, value):
        if key in ("_name", "_mod"):
            super().__setattr__(key, value)
        else:
            setattr(self._load(), key, value)

    def __delattr__(self, name):
        if name in ("_name", "_mod"):
            super().__delattr__(name)
        else:
            delattr(self._load(), name)

pdfplumber = LazyModule("pdfplumber")


class PDFPlumberExtractor(PDFExtractor):
    """Extract text from PDF using pdfplumber library."""

    def extract(self, file_path: str) -> str:
        """
        Extract text from PDF using pdfplumber.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            Extracted text.
            
        Raises:
            Exception: If extraction fails.
        """
        try:
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    try:
                         text = page.extract_text()
                         if text:
                             text_parts.append(text)
                    except Exception as page_exc:
                         # Log but continue with other pages
                         print(
                             f"Warning: Failed to extract page {page_num}: {page_exc}"
                         )
                         continue
            return "\n".join(text_parts)
        except Exception as exc:
            raise RuntimeError(
                f"pdfplumber extraction failed for {file_path}: {exc}"
            ) from exc
