"""PDF extraction fallback strategy orchestrator."""

from pathlib import Path

from utils.pdf_extraction.base import PDFExtractor
from utils.pdf_extraction.pdfplumber_extractor import PDFPlumberExtractor
from utils.pdf_extraction.pymupdf_extractor import PyMuPDFExtractor
from utils.pdf_extraction.pypdf2_extractor import PyPDF2Extractor


class PDFExtractionStrategy:
    """
    Orchestrates PDF text extraction with fallback strategy.
    
    Attempts extraction in order:
    1. PyMuPDF (fitz) - Best for modern PDFs
    2. PyPDF2 - Good fallback for structured PDFs
    3. pdfplumber - Last resort for layout-aware extraction
    
    Selects the result with the best quality score based on:
    - Text length
    - Word count
    - Printable character ratio
    """

    def __init__(self):
        """Initialize extractors in priority order."""
        self.extractors = [
            ("PyMuPDF", PyMuPDFExtractor()),
            ("PyPDF2", PyPDF2Extractor()),
            ("pdfplumber", PDFPlumberExtractor()),
        ]
        self.results = []  # Store results for debugging

    def extract(self, file_path: str) -> str:
        """
        Extract text from PDF using fallback strategy.
        
        Tries each extractor in sequence. Returns the extraction result
        with the highest quality score. If all fail, raises RuntimeError.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            Best-quality extracted text.
            
        Raises:
            RuntimeError: If all extraction methods fail.
        """
        file_path = str(file_path)
        self.results = []
        best_result = None
        best_score = -1

        for extractor_name, extractor in self.extractors:
            try:
                text = extractor.extract(file_path)
                quality = PDFExtractor._calculate_quality_score(text)
                
                result = {
                    "extractor": extractor_name,
                    "success": True,
                    "text": text,
                    "quality": quality,
                }
                self.results.append(result)
                
                # Select if better quality score
                if quality["score"] > best_score:
                    best_score = quality["score"]
                    best_result = text
                    
            except Exception as exc:
                self.results.append(
                    {
                        "extractor": extractor_name,
                        "success": False,
                        "error": str(exc),
                    }
                )
                continue

        if best_result is None:
            # All extractors failed - build detailed error message
            error_details = "; ".join(
                [
                    f"{r['extractor']}: {r.get('error', 'Unknown error')}"
                    for r in self.results
                    if not r["success"]
                ]
            )
            raise RuntimeError(
                f"All PDF extraction methods failed for {Path(file_path).name}: {error_details}"
            )

        return best_result

    def get_extraction_report(self) -> dict:
        """
        Get detailed report of extraction attempts.
        
        Returns:
            Dictionary with extraction results and quality metrics for each attempt.
        """
        return {
            "attempts": len(self.results),
            "results": self.results,
        }
