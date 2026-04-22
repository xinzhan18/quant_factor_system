"""Deterministic PDF-to-Markdown extraction for paper ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re

try:
    import pdfplumber
except ImportError:  # pragma: no cover - optional runtime dependency
    pdfplumber = None


def slugify_paper_name(value: str) -> str:
    """Normalize a filename/title into a markdown-safe slug."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "paper"


def normalize_extracted_text(text: str) -> str:
    """Collapse noisy whitespace while preserving page structure."""
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def render_extract_markdown(
    pdf_path: Path,
    pages: list[str],
    *,
    generated_at: str | None = None,
) -> str:
    """Render a page-wise markdown extraction artifact."""
    ts = generated_at or datetime.now(timezone.utc).isoformat()
    slug = slugify_paper_name(pdf_path.stem)
    lines = [
        "---",
        f"paper_slug: {slug}",
        f"source_pdf: {pdf_path.as_posix()}",
        f"page_count: {len(pages)}",
        "parser: pdfplumber",
        f"generated_at: {ts}",
        "---",
        "",
        f"# {pdf_path.stem}",
        "",
        "> Deterministic PDF text extraction. LLM should read this file, then write a structured",
        "> paper note under `vault/papers/` before generating any direction.",
        "",
    ]
    for idx, page_text in enumerate(pages, start=1):
        body = normalize_extracted_text(page_text)
        lines.extend(
            [
                f"## Page {idx:03d}",
                "",
                body or "_No extractable text on this page._",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


@dataclass(frozen=True)
class ExtractResult:
    source_pdf: Path
    output_md: Path
    page_count: int


def extract_pdf_to_markdown(pdf_path: Path, output_path: Path) -> ExtractResult:
    """Extract PDF pages and write a markdown artifact."""
    if pdfplumber is None:
        raise ImportError(
            "pdfplumber is required for paper extraction. Install with: pip install pdfplumber"
        )
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pages: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_extract_markdown(pdf_path, pages),
        encoding="utf-8",
    )
    return ExtractResult(
        source_pdf=pdf_path,
        output_md=output_path,
        page_count=len(pages),
    )
