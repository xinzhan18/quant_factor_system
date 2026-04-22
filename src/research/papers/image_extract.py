"""Optional paper-image extraction helpers for /factor-paper."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import io
import re
import shutil
import tarfile
import tempfile
from typing import Any
from urllib.request import urlopen

from research.papers.pdf_extract import slugify_paper_name

try:
    import fitz  # type: ignore
except ImportError:  # pragma: no cover - optional runtime dependency
    fitz = None

try:
    import requests
except ImportError:  # pragma: no cover - optional runtime dependency
    requests = None


_CAPTION_RE = re.compile(
    r"(?im)^\s*(figure|fig\.?|table|tab\.?|exhibit)\s+([A-Za-z0-9.\-]+)\s*[:.\-]?\s*(.+)?$"
)


@dataclass(frozen=True)
class ImageExtractRecord:
    path: Path
    source: str
    page: int | None = None
    caption_kind: str | None = None
    caption_number: str | None = None
    caption_text: str | None = None


def infer_arxiv_id(value: str) -> str | None:
    """Extract an arXiv identifier from a free-form string."""
    m = re.search(r"(?:arxiv:)?(\d{4}\.\d{4,5})(?:v\d+)?", value, flags=re.IGNORECASE)
    return m.group(1) if m else None


def detect_page_captions(text: str) -> list[dict[str, str]]:
    """Return detected Figure/Table/Exhibit captions from a page."""
    captions: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for kind, number, desc in _CAPTION_RE.findall(text or ""):
        normalized_kind = kind.lower().rstrip(".")
        normalized_number = number.strip().rstrip(".:;-")
        normalized_desc = (desc or "").strip()
        key = (normalized_kind, normalized_number, normalized_desc)
        if key in seen:
            continue
        seen.add(key)
        captions.append(
            {
                "kind": normalized_kind,
                "number": normalized_number,
                "description": normalized_desc,
            }
        )
    return captions


def caption_to_filename_stub(
    kind: str,
    number: str,
    description: str,
    *,
    fallback_index: int = 1,
) -> str:
    """Build a stable filename stem from a caption."""
    prefix = {"fig": "figure", "figure": "figure", "tab": "table", "table": "table"}.get(
        kind, kind
    )
    number_bits = slugify_paper_name(number).replace("_", "") or str(fallback_index)
    desc_bits = slugify_paper_name(description)
    if desc_bits and desc_bits != "paper":
        words = desc_bits.split("_")[:6]
        return f"{prefix}{number_bits}_{'_'.join(words)}"
    return f"{prefix}{number_bits}"


def _fetch_url_bytes(url: str) -> bytes:
    if requests is not None:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        return resp.content
    with urlopen(url, timeout=60) as resp:  # nosec B310 - trusted arXiv URL only
        return resp.read()


def _extract_tar_safely(blob: bytes, target_dir: Path) -> None:
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
        safe_members = []
        for member in tar.getmembers():
            if member.name.startswith("/") or ".." in member.name:
                continue
            safe_members.append(member)
        tar.extractall(path=target_dir, members=safe_members)


def _copy_source_figures(source_root: Path, output_dir: Path) -> list[ImageExtractRecord]:
    records: list[ImageExtractRecord] = []
    seen_names: set[str] = set()
    figure_dirs = ("pics", "pic", "figures", "figure", "fig", "figs", "images", "img")
    for dirname in figure_dirs:
        candidate = source_root / dirname
        if not candidate.exists():
            continue
        for path in sorted(candidate.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".pdf"}:
                continue
            out_name = path.name
            if out_name in seen_names:
                out_name = f"{path.stem}_{len(seen_names)+1}{path.suffix.lower()}"
            seen_names.add(out_name)
            out_path = output_dir / out_name
            shutil.copy2(path, out_path)
            records.append(ImageExtractRecord(path=out_path, source="arxiv-source"))
    return records


def _render_small_source_pdfs(source_root: Path, output_dir: Path) -> list[ImageExtractRecord]:
    if fitz is None:
        return []
    records: list[ImageExtractRecord] = []
    for pdf_path in sorted(source_root.rglob("*.pdf")):
        try:
            doc = fitz.open(pdf_path)
        except Exception:
            continue
        if len(doc) > 5:
            doc.close()
            continue
        for idx, page in enumerate(doc, start=1):
            pix = page.get_pixmap(dpi=200)
            out_path = output_dir / f"{pdf_path.stem}_page{idx}.png"
            pix.save(out_path.as_posix())
            records.append(ImageExtractRecord(path=out_path, source="pdf-figure", page=idx))
        doc.close()
    return records


def try_extract_arxiv_source_images(
    arxiv_id: str,
    output_dir: Path,
) -> list[ImageExtractRecord]:
    """Best-effort image extraction from arXiv source package."""
    with tempfile.TemporaryDirectory(prefix="paper_source_") as tmp:
        temp_root = Path(tmp)
        blob = _fetch_url_bytes(f"https://arxiv.org/e-print/{arxiv_id}")
        _extract_tar_safely(blob, temp_root)
        records = _copy_source_figures(temp_root, output_dir)
        if records:
            return records
        return _render_small_source_pdfs(temp_root, output_dir)


def render_captioned_pages(pdf_path: Path, output_dir: Path) -> list[ImageExtractRecord]:
    """Render only pages that contain Figure/Table captions."""
    if fitz is None:
        raise ImportError(
            "PyMuPDF is required for paper image extraction. Install with: pip install PyMuPDF"
        )
    records: list[ImageExtractRecord] = []
    doc = fitz.open(pdf_path)
    try:
        for page_number, page in enumerate(doc, start=1):
            captions = detect_page_captions(page.get_text())
            if not captions:
                continue
            caption = captions[0]
            stub = caption_to_filename_stub(
                caption["kind"],
                caption["number"],
                caption["description"],
                fallback_index=page_number,
            )
            out_path = output_dir / f"{stub}.png"
            page.get_pixmap(dpi=200).save(out_path.as_posix())
            records.append(
                ImageExtractRecord(
                    path=out_path,
                    source="page-render",
                    page=page_number,
                    caption_kind=caption["kind"],
                    caption_number=caption["number"],
                    caption_text=caption["description"],
                )
            )
    finally:
        doc.close()
    return records


def extract_embedded_images(pdf_path: Path, output_dir: Path) -> list[ImageExtractRecord]:
    """Fallback: extract embedded bitmap assets from a PDF."""
    if fitz is None:
        raise ImportError(
            "PyMuPDF is required for paper image extraction. Install with: pip install PyMuPDF"
        )
    records: list[ImageExtractRecord] = []
    doc = fitz.open(pdf_path)
    try:
        for page_number, page in enumerate(doc, start=1):
            for img_index, img in enumerate(page.get_images(full=True), start=1):
                xref = img[0]
                try:
                    base_image: dict[str, Any] = doc.extract_image(xref)
                except Exception:
                    continue
                ext = base_image.get("ext", "png")
                out_path = output_dir / f"page{page_number:03d}_img{img_index:02d}.{ext}"
                out_path.write_bytes(base_image["image"])
                records.append(
                    ImageExtractRecord(
                        path=out_path,
                        source="pdf-extraction",
                        page=page_number,
                    )
                )
    finally:
        doc.close()
    return records


def extract_paper_images(
    pdf_path: Path,
    output_dir: Path,
    *,
    arxiv_id: str | None = None,
) -> list[ImageExtractRecord]:
    """Extract representative paper images using a tiered strategy."""
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    records: list[ImageExtractRecord] = []
    resolved_arxiv_id = arxiv_id or infer_arxiv_id(pdf_path.stem)
    if resolved_arxiv_id:
        try:
            records = try_extract_arxiv_source_images(resolved_arxiv_id, output_dir)
        except Exception:
            records = []
    if records:
        return records

    records = render_captioned_pages(pdf_path, output_dir)
    if records:
        return records

    return extract_embedded_images(pdf_path, output_dir)
