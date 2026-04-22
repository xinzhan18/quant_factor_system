#!/usr/bin/env python3
"""Extract representative figures for a paper under vault/papers/{slug}/images/."""

from __future__ import annotations

import argparse
from pathlib import Path

from research.papers import extract_paper_images, infer_arxiv_id, slugify_paper_name
from research.storage.paths import StoragePaths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract representative paper images for /factor-paper."
    )
    parser.add_argument(
        "--pdf",
        required=True,
        help="Source PDF path, typically under storage/vault/raw/papers/.",
    )
    parser.add_argument(
        "--paper-slug",
        help="Optional paper slug. Defaults to slugified PDF stem.",
    )
    parser.add_argument(
        "--arxiv-id",
        help="Optional explicit arXiv ID. If omitted, infer from filename when possible.",
    )
    parser.add_argument(
        "--out-dir",
        help="Optional output directory. Defaults to storage/vault/papers/{slug}/images/",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    pdf_path = Path(args.pdf)
    paper_slug = args.paper_slug or slugify_paper_name(pdf_path.stem)
    paths = StoragePaths()
    output_dir = (
        Path(args.out_dir)
        if args.out_dir
        else paths.paper_assets_dir(paper_slug) / "images"
    )
    arxiv_id = args.arxiv_id or infer_arxiv_id(pdf_path.stem)
    records = extract_paper_images(pdf_path, output_dir, arxiv_id=arxiv_id)
    print(f"Wrote {len(records)} image(s) to {output_dir}")
    for record in records:
        rel = record.path.relative_to(output_dir.parent.parent.parent.parent)
        print(f"- {rel.as_posix()} [{record.source}]")


if __name__ == "__main__":
    main()
