"""PyPDF2 PDF extraction implementation."""

from utils.pdf_extraction.base import PDFExtractor

class LazyPdfReader:
    def __new__(cls, *args, **kwargs):
        from PyPDF2 import PdfReader
        return PdfReader(*args, **kwargs)

PdfReader = LazyPdfReader


class PyPDF2Extractor(PDFExtractor):
    """Extract text from PDF using PyPDF2 library."""

    def extract(self, file_path: str) -> str:
        """
        Extract text from PDF using PyPDF2.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            Extracted text.
            
        Raises:
            Exception: If extraction fails.
        """
        try:
            text_parts = []
            with open(file_path, "rb") as file:
                reader = PdfReader(file)
                for page_num, page in enumerate(reader.pages):
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
                f"PyPDF2 extraction failed for {file_path}: {exc}"
            ) from exc
