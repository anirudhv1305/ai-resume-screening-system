"""pdfplumber PDF extraction implementation."""

import pdfplumber

from utils.pdf_extraction.base import PDFExtractor


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
