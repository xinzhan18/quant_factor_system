from __future__ import annotations

from pathlib import Path

from research.papers.pdf_extract import (
    normalize_extracted_text,
    render_extract_markdown,
    slugify_paper_name,
)


def test_slugify_paper_name() -> None:
    assert slugify_paper_name("Factor Miner 2026.pdf") == "factor_miner_2026_pdf"
    assert slugify_paper_name("  ") == "paper"


def test_normalize_extracted_text() -> None:
    raw = "Alpha   beta\r\n\r\n\r\nGamma\t delta\n\n\nEpsilon"
    assert normalize_extracted_text(raw) == "Alpha beta\n\nGamma delta\n\nEpsilon"


def test_render_extract_markdown() -> None:
    md = render_extract_markdown(
        Path("storage/vault/raw/papers/factor_miner.pdf"),
        [" First page  \n\n", ""],
        generated_at="2026-04-22T12:00:00+00:00",
    )
    assert "paper_slug: factor_miner" in md
    assert "source_pdf: storage/vault/raw/papers/factor_miner.pdf" in md
    assert "## Page 001" in md
    assert "First page" in md
    assert "## Page 002" in md
    assert "_No extractable text on this page._" in md
