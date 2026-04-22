"""Phase 4 back-fill — surgical Python edits, no LLM involvement.

Called after F{id} allocation to inject the newly-minted id into all
Phase 3 artifacts that referred to the candidate by its C{id} only.
All functions are idempotent: re-running with the same mapping is a
no-op if the fills are already in place.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml


_FM_RE = re.compile(r"\A(---\s*\n)(?P<fm>.*?)(\n---\s*\n)", re.DOTALL)
_BUCKET_PAT = re.compile(r"bucket\s*`(\w+)`")


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


def ensure_judge_bases_fields(path: Path) -> None:
    """Add flat ``admit_count`` / ``reject_count`` / ``reserve_count`` /
    ``candidate_count`` / ``mt_bucket`` to the judge frontmatter so the
    ``recent_batches.base`` file can query them without nested-object access.

    Idempotent: each key is appended only if absent. Values are derived
    from the existing ``candidates`` frontmatter list (authoritative) and
    the body's ``bucket `X``` prose token. No existing keys are touched.
    """
    text = path.read_text(encoding="utf-8")
    m = _FM_RE.match(text)
    if m is None:
        return
    fm_text = m.group("fm")
    body = text[m.end():]

    fm = yaml.safe_load(fm_text) or {}
    if not isinstance(fm, dict):
        return

    candidates = fm.get("candidates") or []
    counts = {"admit": 0, "reject": 0, "reserve": 0}
    for c in candidates:
        v = c.get("verdict") if isinstance(c, dict) else None
        if v in counts:
            counts[v] += 1

    flat: dict[str, object] = {
        "admit_count": counts["admit"],
        "reject_count": counts["reject"],
        "reserve_count": counts["reserve"],
        "candidate_count": len(candidates),
    }
    bucket_m = _BUCKET_PAT.search(body)
    if bucket_m:
        flat["mt_bucket"] = bucket_m.group(1)

    to_append: list[str] = []
    for key, value in flat.items():
        if re.search(rf"(?m)^{re.escape(key)}:\s*", fm_text):
            continue
        to_append.append(f"{key}: {value}")
    if not to_append:
        return

    new_fm = fm_text.rstrip("\n") + "\n" + "\n".join(to_append)
    new_text = m.group(1) + new_fm + m.group(3) + body
    path.write_text(new_text, encoding="utf-8")


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
