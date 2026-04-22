#!/usr/bin/env python3
"""Extract a source PDF into a page-wise markdown artifact for /factor-paper."""

from __future__ import annotations

import argparse
from pathlib import Path

from research.papers import extract_pdf_to_markdown, slugify_paper_name
from research.storage.paths import StoragePaths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract a paper PDF into markdown for LLM processing."
    )
    parser.add_argument(
        "--pdf",
        required=True,
        help="Path to the source PDF, typically under storage/vault/raw/papers/.",
    )
    parser.add_argument(
        "--out",
        help="Optional output path. Defaults to storage/vault/raw/paper_extracts/{slug}.md",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    pdf_path = Path(args.pdf)
    paths = StoragePaths()
    output_path = (
        Path(args.out)
        if args.out
        else paths.paper_extract_file(slugify_paper_name(pdf_path.stem))
    )
    result = extract_pdf_to_markdown(pdf_path, output_path)
    print(f"Wrote {result.output_md} ({result.page_count} pages)")


if __name__ == "__main__":
    main()
