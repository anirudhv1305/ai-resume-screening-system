"""PyMuPDF (fitz) PDF extraction implementation."""

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

fitz = LazyModule("fitz")


class PyMuPDFExtractor(PDFExtractor):
    """Extract text from PDF using PyMuPDF (fitz) library."""

    def extract(self, file_path: str) -> str:
        """
        Extract text from PDF using PyMuPDF.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            Extracted text.
            
        Raises:
            Exception: If extraction fails.
        """
        try:
            with fitz.open(file_path) as document:
                pages = [page.get_text("text") for page in document]
            return "\n".join(pages)
        except Exception as exc:
            raise RuntimeError(
                f"PyMuPDF extraction failed for {file_path}: {exc}"
            ) from exc
