"""Phase 4 back-fill — surgical Python edits, no LLM involvement.

Called after F{id} allocation to inject the newly-minted id into all
Phase 3 artifacts that referred to the candidate by its C{id} only.
All functions are idempotent: re-running with the same mapping is a
no-op if the fills are already in place.
"""
from __future__ import annotations

import re
from pathlib import Path


_FM_RE = re.compile(r"\A(---\s*\n)(?P<fm>.*?)(\n---\s*\n)", re.DOTALL)


def backfill_candidate_md(path: Path, factor_id: str) -> None:
    text = path.read_text(encoding="utf-8")
    m = _FM_RE.match(text)
    if m is None:
        return
    fm = m.group("fm")
    # Already filled — no change
    if re.search(rf"(?m)^factor_id:\s*{re.escape(factor_id)}\s*$", fm):
        return
    new_fm = re.sub(r"(?m)^factor_id:\s*\S.*$", f"factor_id: {factor_id}", fm)
    if new_fm == fm:
        return
    new_text = text[: m.start("fm")] + new_fm + text[m.end("fm") :]
    path.write_text(new_text, encoding="utf-8")


def backfill_judge_md(path: Path, cand_to_fid: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8")
    for cid, fid in cand_to_fid.items():
        # Inline "admit" → "admit → F{id}" in the verdict cell, once
        verdict_pat = rf"(\|\s*{re.escape(cid)}\s*\|\s*admit)(\s*\|)"
        if f"admit → {fid}" not in text:
            text = re.sub(verdict_pat, rf"\1 → {fid}\2", text, count=1)
        # Append [[factors/F{id}]] to the detail cell's existing candidate link
        detail_pat = rf"(\[\[batches/[^\]]*candidates/{re.escape(cid)}[^\]]*\]\])"
        if f"[[factors/{fid}]]" not in text:
            text = re.sub(detail_pat, rf"\1 · [[factors/{fid}]]", text, count=1)
    path.write_text(text, encoding="utf-8")


def backfill_direction_md(path: Path, cand_to_fid: dict[str, str], batch_id: str) -> None:
    text = path.read_text(encoding="utf-8")
    for cid, fid in cand_to_fid.items():
        if f"admit → [[factors/{fid}]]" in text:
            continue
        pat = (
            rf"(- \[\[batches/{re.escape(batch_id)}/candidates/{re.escape(cid)}[^\]]*\]\]"
            rf"[^\n]*→\s*)\*\*admit\*\*"
        )
        text = re.sub(pat, rf"\1**admit → [[factors/{fid}]]**", text, count=1)
    path.write_text(text, encoding="utf-8")
