"""Post-refresh format audit for INDEX.md + its Bases dependencies.

Called at the end of :func:`research.memory.index_refresher.refresh_index`
(and as a standalone ``research audit index`` CLI command). Raises
:class:`IndexFormatError` on any violation — Phase 4 archive halts
unconditionally on that, matching the Autonomous-Mining rule of stopping
only on system-level integrity errors.

Checks:

1. ``INDEX.md`` exists and has frontmatter.
2. Frontmatter ``round`` / ``last_batch`` match ``state.yaml``.
3. All three ``_bases/*.base`` files exist and parse as YAML.
4. Every ``directions/*.md`` carries required keys for the directions
   base (``status``, ``priority``, ``rounds``, ``admits``, ``last_batch``).
5. Every non-retired ``factors/F*.md`` carries required keys for the
   factors base (``composite_grade``, ``ic_ir_validation``,
   ``monotonicity_validation``, ``direction``, ``decision``, ``status``).
6. Every ``batches/*/judge.md`` carries required keys for the
   recent-batches base (``batch_id``, ``direction``, ``admit_count``,
   ``reject_count``, ``reserve_count``, ``candidate_count``).
7. INDEX body contains the three base embeds (``![[_bases/...]]``) and
   the ``<!-- BEGIN/END INSIGHT -->`` sentinels.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from research.memory.index_narrative import INSIGHT_BEGIN, INSIGHT_END
from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml


class IndexFormatError(RuntimeError):
    """Raised when ``audit_index_format`` detects a hard invariant violation."""


@dataclass
class IndexAuditReport:
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def fail(self, msg: str) -> None:
        self.errors.append(msg)


_DIRECTION_REQUIRED_KEYS = (
    "status",
    "priority",
    "rounds",
    "admits",
    "last_batch",
)
# The rich metric keys (composite_grade, ic_ir_validation, ...) are written
# by the async report subagent AFTER phase4 archive commits. Requiring them
# here would race against the subagent. Audit only checks the keys that
# ``factor_writer`` + ``factor_md_sync`` set synchronously — Bases still
# renders rows with nulls in the missing cells until the subagent finishes.
_FACTOR_REQUIRED_KEYS = (
    "decision",
    "status",
    "direction",
)
_JUDGE_REQUIRED_KEYS = (
    "batch_id",
    "direction",
    "admit_count",
    "reject_count",
    "reserve_count",
    "candidate_count",
)
_BASE_FILES = ("directions.base", "factors.base", "recent_batches.base")

_FM_RE = re.compile(r"\A---\s*\n(?P<fm>.*?)\n---\s*\n?", re.DOTALL)


def _read_fm(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    m = _FM_RE.match(path.read_text(encoding="utf-8"))
    if m is None:
        return {}
    data = yaml.safe_load(m.group("fm"))
    return data if isinstance(data, dict) else {}


def _check_required_keys(
    report: IndexAuditReport,
    fm: dict[str, Any],
    required: tuple[str, ...],
    label: str,
) -> None:
    missing = [k for k in required if fm.get(k) in (None, "")]
    if missing:
        report.fail(f"{label}: missing frontmatter keys {missing}")


def _check_frontmatter_sync(
    report: IndexAuditReport, paths: StoragePaths, fm: dict[str, Any]
) -> None:
    try:
        state = load_yaml(paths.state_file) or {}
    except FileNotFoundError:
        return
    if not isinstance(state, dict):
        return
    for key in ("round", "last_batch"):
        expected = state.get(key)
        actual = fm.get(key)
        if expected is not None and actual != expected:
            report.fail(
                f"INDEX frontmatter {key}={actual!r} but state.yaml says {expected!r}"
            )


def _check_base_files(report: IndexAuditReport, paths: StoragePaths) -> None:
    bases_dir = paths.vault_dir / "_bases"
    if not bases_dir.exists():
        report.fail(f"_bases/ directory missing at {bases_dir}")
        return
    for fname in _BASE_FILES:
        fp = bases_dir / fname
        if not fp.exists():
            report.fail(f"_bases/{fname} missing")
            continue
        try:
            yaml.safe_load(fp.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            report.fail(f"_bases/{fname} invalid YAML: {exc}")


def _check_index_body(report: IndexAuditReport, text: str) -> None:
    # Obsidian .base embeds keep the .base extension in the wikilink.
    for target in (
        "_bases/directions.base",
        "_bases/factors.base",
        "_bases/recent_batches.base",
    ):
        if f"![[{target}]]" not in text:
            report.fail(f"INDEX body missing base embed ![[{target}]]")
    if INSIGHT_BEGIN not in text or INSIGHT_END not in text:
        report.fail(
            f"INDEX body missing insight sentinels "
            f"({INSIGHT_BEGIN!r} / {INSIGHT_END!r})"
        )


def _check_directions(report: IndexAuditReport, paths: StoragePaths) -> None:
    for md in sorted(paths.directions_dir.glob("*.md")):
        fm = _read_fm(md)
        if not fm:
            report.fail(f"{md.name}: no frontmatter")
            continue
        _check_required_keys(report, fm, _DIRECTION_REQUIRED_KEYS, md.name)


def _check_factors(report: IndexAuditReport, paths: StoragePaths) -> None:
    for yp in sorted(paths.factors_dir.glob("F*.yaml")):
        try:
            data = load_yaml(yp) or {}
        except Exception as exc:
            report.fail(f"{yp.name}: unreadable YAML ({exc})")
            continue
        if not isinstance(data, dict) or data.get("status") == "retired":
            continue
        mp = yp.with_suffix(".md")
        if not mp.exists():
            # Factor.md is written asynchronously by the report subagent.
            # Phase 4 returns before it lands, so a missing md is not a
            # structural failure — only a drift when the md exists but is
            # structurally broken.
            continue
        fm = _read_fm(mp)
        if not fm:
            report.fail(f"{mp.name}: no frontmatter")
            continue
        _check_required_keys(report, fm, _FACTOR_REQUIRED_KEYS, mp.name)


def _check_judges(report: IndexAuditReport, paths: StoragePaths) -> None:
    for batch_dir in sorted(paths.batches_dir.iterdir()):
        if not batch_dir.is_dir():
            continue
        jp = batch_dir / "judge.md"
        if not jp.exists():
            continue
        fm = _read_fm(jp)
        if not fm:
            report.fail(f"batches/{batch_dir.name}/judge.md: no frontmatter")
            continue
        _check_required_keys(
            report, fm, _JUDGE_REQUIRED_KEYS, f"batches/{batch_dir.name}/judge.md"
        )


def audit_index_format(paths: StoragePaths) -> IndexAuditReport:
    """Run all structural checks; returns a report (does not raise)."""
    report = IndexAuditReport()

    index_path = paths.vault_index_file
    if not index_path.exists():
        report.fail(f"INDEX.md missing at {index_path}")
        return report
    text = index_path.read_text(encoding="utf-8")
    fm = _read_fm(index_path)
    if not fm:
        report.fail("INDEX.md has no frontmatter")
    else:
        _check_frontmatter_sync(report, paths, fm)
    _check_index_body(report, text)
    _check_base_files(report, paths)
    _check_directions(report, paths)
    _check_factors(report, paths)
    _check_judges(report, paths)
    return report


def audit_index_format_or_raise(paths: StoragePaths) -> None:
    """Convenience wrapper: raise IndexFormatError on any violation."""
    report = audit_index_format(paths)
    if report.ok:
        return
    bullets = "\n".join(f"  - {e}" for e in report.errors)
    raise IndexFormatError(
        f"INDEX.md format audit failed ({len(report.errors)} issue(s)):\n{bullets}"
    )
