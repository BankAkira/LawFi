"""OCR module using Google Cloud Vision API for Thai text extraction from PDFs."""

import io
from pathlib import Path

from google.cloud import vision


class OCRService:
    """Extract text from PDF files using Google Cloud Vision API."""

    def __init__(self):
        self.client = vision.ImageAnnotatorClient()

    def extract_text_from_pdf(self, pdf_path: str | Path) -> str:
        """Extract text from a PDF file. Handles both text-based and scanned PDFs."""
        pdf_path = Path(pdf_path)
        with open(pdf_path, "rb") as f:
            content = f.read()

        return self.extract_text_from_bytes(content)

    def extract_text_from_bytes(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bytes using Vision API document text detection."""
        # Vision API accepts PDFs directly for document text detection
        input_config = vision.InputConfig(
            content=pdf_bytes,
            mime_type="application/pdf",
        )
        # Process up to 100 pages per request
        feature = vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)
        request = vision.AnnotateFileRequest(
            input_config=input_config,
            features=[feature],
            pages=[],  # empty = all pages
        )

        response = self.client.batch_annotate_files(requests=[request])

        # Combine text from all pages
        all_text = []
        for file_response in response.responses:
            for page_response in file_response.responses:
                if page_response.full_text_annotation:
                    all_text.append(page_response.full_text_annotation.text)

        return "\n".join(all_text)

    def is_scanned_pdf(self, pdf_path: str | Path) -> bool:
        """Check if a PDF is scanned (image-based) by attempting text extraction.

        Returns True if the PDF likely needs OCR.
        """
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(str(pdf_path))
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()

            # If very little text found, likely scanned
            return len(text.strip()) < 100
        except Exception:
            # If PyMuPDF not available, assume needs OCR
            return True
