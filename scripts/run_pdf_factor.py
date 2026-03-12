#!/usr/bin/env python
"""Run PDF-to-factor automation pipeline."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable, List

from data.ricequant_source import RiceQuantSource
from data.storage.timescale_storage import TimescaleDB
from factors.automation import (
    CodeGenerator,
    FactorExtractor,
    FactorRegister,
    PDFParser,
)

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def discover_pdf_files(pdf: str | None, batch: str | None) -> List[Path]:
    files: List[Path] = []
    if pdf:
        files.append(Path(pdf))
    if batch:
        batch_path = Path(batch)
        if batch_path.is_dir():
            files.extend(sorted(batch_path.glob("*.pdf")))
        else:
            files.extend(sorted(Path(".").glob(batch)))
    unique = []
    seen = set()
    for file in files:
        resolved = file.resolve()
        if resolved not in seen:
            unique.append(file)
            seen.add(resolved)
    return unique


def process_pdfs(
    pdf_files: Iterable[Path],
    parse_only: bool,
    generate_only: bool,
    output_dir: Path,
) -> None:
    db = TimescaleDB()
    _source = RiceQuantSource()

    parser = PDFParser()
    extractor = FactorExtractor()
    generator = CodeGenerator()
    register = FactorRegister(db=db)

    output_dir.mkdir(parents=True, exist_ok=True)

    for pdf_file in pdf_files:
        logger.info("Processing PDF: %s", pdf_file)
        parsed = parser.parse(str(pdf_file))
        factors = extractor.extract(parsed)

        if not factors:
            logger.warning("No factors extracted from %s", pdf_file)
            continue

        for factor in factors:
            logger.info("Extracted factor: %s (%s)", factor.name, factor.display_name)
            if parse_only:
                continue

            target_file = output_dir / f"{factor.name}.py"
            generator.generate(factor, output_path=str(target_file))

            if generate_only:
                continue

            status = register.register(factor)
            logger.info("Register result: %s", status)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Automate factor extraction from PDF documents.")
    parser.add_argument("--pdf", type=str, help="Single PDF file path.")
    parser.add_argument("--batch", type=str, help="Batch directory or glob pattern for PDFs.")
    parser.add_argument("--parse-only", action="store_true", help="Only parse and extract factor info.")
    parser.add_argument("--generate-only", action="store_true", help="Only parse/extract/generate code.")
    parser.add_argument(
        "--output-dir",
        default="factors/generated",
        help="Directory to save generated factor python files.",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logs.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    setup_logging(args.verbose)

    pdf_files = discover_pdf_files(args.pdf, args.batch)
    if not pdf_files:
        raise SystemExit("No PDF files provided. Use --pdf or --batch.")

    process_pdfs(
        pdf_files=pdf_files,
        parse_only=args.parse_only,
        generate_only=args.generate_only,
        output_dir=Path(args.output_dir),
    )


if __name__ == "__main__":
    main()

