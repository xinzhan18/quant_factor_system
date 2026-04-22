"""Paper-ingestion helpers for external PDF-driven direction discovery."""

from .image_extract import (
    caption_to_filename_stub,
    detect_page_captions,
    extract_paper_images,
    infer_arxiv_id,
)
from .pdf_extract import (
    extract_pdf_to_markdown,
    normalize_extracted_text,
    render_extract_markdown,
    slugify_paper_name,
)

__all__ = [
    "caption_to_filename_stub",
    "detect_page_captions",
    "extract_paper_images",
    "extract_pdf_to_markdown",
    "infer_arxiv_id",
    "normalize_extracted_text",
    "render_extract_markdown",
    "slugify_paper_name",
]
