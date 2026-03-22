"""PDF parser based on pdfplumber."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

try:
    import pdfplumber
except ImportError:  # pragma: no cover - depends on optional package
    pdfplumber = None


class PDFParser:
    """Parse PDF files into plain text for downstream factor extraction."""

    def __init__(self) -> None:
        self._logger = logger

    def parse(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parse a PDF and return extracted text content.

        Returns:
            dict with keys: pdf_path, page_count, pages, text
        """
        if pdfplumber is None:
            raise ImportError(
                "pdfplumber is required for PDFParser. Install with: pip install pdfplumber"
            )

        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        pages: List[str] = []
        self._logger.info("Parsing PDF: %s", path)

        with pdfplumber.open(path) as pdf:
            for page_idx, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                pages.append(page_text)
                self._logger.debug("Parsed page %d with %d chars", page_idx, len(page_text))

        text = "\n\n".join(pages)
        result = {
            "pdf_path": str(path),
            "page_count": len(pages),
            "pages": pages,
            "text": text,
        }
        self._logger.info("PDF parsed successfully: %s (%d pages)", path.name, len(pages))
        return result

