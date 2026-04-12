"""``research audit`` subcommand group.

Currently implements only the ``mt-budget`` subcommand (§7.MT); other
audit commands (reports, links, state, failures, duplicates) land in
follow-up commits.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from research.checkpoints.mt_budget import (
    MtBudgetConfig,
    compute_mt_budget,
    scan_batches_for_mt,
)
from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml


def _load_mt_config(paths: StoragePaths) -> MtBudgetConfig:
    cfg = load_yaml(paths.config_file) or {}
    mt_dict = (cfg.get("thresholds") or {}).get("mt_budget", {})
    return MtBudgetConfig.from_config_dict(mt_dict)


def format_mt_budget_report(
    paths: StoragePaths,
    sample_policy_version: str,
    direction: str | None = None,
) -> str:
    """Render a human-readable ``mt-budget`` summary.

    With no direction: scan once with ``current_direction="<global>"``
    so ``direction_candidates`` falls back to 0 (we only care about
    cumulative and validation_exposure).

    With a direction: report both the direction-specific counter and
    the predicted next-batch bucket.
    """
    cfg = _load_mt_config(paths)
    lines: list[str] = []

    if direction is None:
        counts = scan_batches_for_mt(
            paths.batches_dir,
            current_batch_id="zzz_not_a_real_batch",
            current_direction="<global>",
            sample_policy_version=sample_policy_version,
        )
        hint = compute_mt_budget(counts, cfg)
        lines.append(f"# Multiple-Testing Budget ({sample_policy_version})")
        lines.append("")
        lines.append(f"- Cumulative candidates: {counts.cumulative_candidates}")
        lines.append(f"- Validation exposure (this policy): {counts.validation_exposure}")
        lines.append(f"- Batches scanned: {counts.n_batches_scanned}")
        lines.append("")
        lines.append(
            f"Predicted next-batch mt_bucket (no direction context): "
            f"**{hint['mt_bucket']}** (score={hint['mt_score']:.3f})"
        )
        return "\n".join(lines)

    counts = scan_batches_for_mt(
        paths.batches_dir,
        current_batch_id="zzz_not_a_real_batch",
        current_direction=direction,
        sample_policy_version=sample_policy_version,
    )
    hint = compute_mt_budget(counts, cfg)
    lines.append(
        f"# Multiple-Testing Budget — direction={direction} ({sample_policy_version})"
    )
    lines.append("")
    lines.append(f"- Cumulative candidates (all directions): {counts.cumulative_candidates}")
    lines.append(f"- Direction candidates: {counts.direction_candidates}")
    lines.append(f"- Validation exposure (this policy): {counts.validation_exposure}")
    lines.append(f"- Batches scanned: {counts.n_batches_scanned}")
    lines.append("")
    lines.append(
        f"Predicted next-batch mt_bucket for direction={direction}: "
        f"**{hint['mt_bucket']}** (score={hint['mt_score']:.3f})"
    )
    return "\n".join(lines)


def register_audit_subcommand(subparsers: argparse._SubParsersAction) -> None:
    """Attach ``research audit mt-budget`` to the top-level argparse router."""
    audit_p = subparsers.add_parser(
        "audit",
        help="Audit commands (mt-budget, reports, links, ...)",
    )
    audit_sub = audit_p.add_subparsers(dest="audit_cmd", required=True)

    mt = audit_sub.add_parser(
        "mt-budget",
        help="Print current §7.MT multiple-testing budget status",
    )
    mt.add_argument(
        "--direction",
        type=str,
        default=None,
        help="Scope the report to one direction",
    )
    mt.set_defaults(func=_run_mt_budget)


def _run_mt_budget(args: argparse.Namespace) -> None:
    storage_root = Path(getattr(args, "storage_root", "storage"))
    paths = StoragePaths(storage_root)
    cfg = load_yaml(paths.config_file) or {}
    sample_policy_version = (
        (cfg.get("sample_policy") or {}).get("sample_policy_version", "v3")
    )
    print(
        format_mt_budget_report(
            paths, sample_policy_version, direction=args.direction
        )
    )
