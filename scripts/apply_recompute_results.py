#!/usr/bin/env python3
"""Apply a recompute audit run back into ``storage/vault/factors/F*.yaml``.

The audit script (``recompute_factor_metrics.py``) writes per-factor YAML
under ``storage/cache/recompute_audit/<run>/`` but never overwrites the
truth source. This script promotes those audit results into the factor
library, replacing ``validation_metrics`` with a primary-universe view
plus a full multi-universe grid and a robustness summary.

Schema after apply::

    primary_universe: csi1000
    validation_metrics:                  # csi1000 alias — drives composite grade
      ic_mean, ic_ir, ic_win_rate, monotonicity, long_short_mean,
      long_short_sharpe, long_short_tstat, coverage
    validation_metrics_by_universe:      # full grid
      all_tradable: { coverage, ic_mean, ic_ir, ic_win_rate, monotonicity,
                      long_short_mean, long_short_sharpe, long_short_tstat }
      csi300:      { ... }
      csi1000:     { ... }
    universe_robustness:
      icir_min, icir_max, icir_ratio
      ic_sign_consistent_across_universes: bool
      csi300_passes_admission_floor: bool   # mono>=0.6 AND |ICIR|>=0.15
    recompute_provenance:
      run_name, applied_at, audit_relpath
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml, save_yaml

logger = logging.getLogger(__name__)

PRIMARY_UNIVERSE_DEFAULT = "all_tradable"
AUDIT_DIR_DEFAULT = "tradable_mask_v1_st"
ICIR_FLOOR = 0.15
MONO_FLOOR = 0.6


def _flatten_universe_block(block: dict[str, Any]) -> dict[str, Any]:
    """Audit yaml → per-universe basic snapshot.

    Keep only the 5 fields needed for cross-universe comparison: coverage,
    ic_mean, ic_ir, monotonicity, long_short_sharpe. Richer fields (ICIR
    train, ls_tstat, max_dd, win_rate) live on the primary-universe
    ``validation_metrics`` block, not on every universe.
    """
    if not isinstance(block, dict) or block.get("error"):
        return {"error": block.get("error", "missing") if isinstance(block, dict) else "missing"}
    ic_val = block.get("ic_validation") or {}
    q_val = block.get("quintile_validation") or {}
    ls_stats = q_val.get("ls_stats") or {}
    return {
        "coverage": _round(block.get("coverage"), 4),
        "ic_mean": _round(ic_val.get("ic_mean"), 6),
        "ic_ir": _round(ic_val.get("ic_ir"), 4),
        "monotonicity": _round(q_val.get("monotonicity"), 4),
        "long_short_sharpe": _round(ls_stats.get("sharpe"), 4),
    }


def _round(value: Any, digits: int) -> Any:
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return value
    if f != f:  # NaN
        return None
    return round(f, digits)


def _compute_robustness(
    grid: dict[str, dict[str, Any]],
    *,
    primary: str,
) -> dict[str, Any]:
    icirs = []
    ic_means = []
    monos = []
    for name, blk in grid.items():
        if "error" in blk:
            continue
        if blk.get("ic_ir") is not None:
            icirs.append(blk["ic_ir"])
        if blk.get("ic_mean") is not None:
            ic_means.append(blk["ic_mean"])
        if blk.get("monotonicity") is not None:
            monos.append(blk["monotonicity"])

    icir_min, icir_max = (min(icirs), max(icirs)) if icirs else (None, None)
    ic_sign_consistent = bool(
        ic_means and (all(x > 0 for x in ic_means) or all(x < 0 for x in ic_means))
    )
    icir_ratio = None
    if icir_min is not None and icir_max not in (None, 0):
        icir_ratio = round(abs(icir_min) / abs(icir_max), 4) if abs(icir_max) > 0 else None

    csi300_block = grid.get("csi300") or {}
    csi300_passes = (
        "error" not in csi300_block
        and abs(csi300_block.get("ic_ir") or 0.0) >= ICIR_FLOOR
        and abs(csi300_block.get("monotonicity") or 0.0) >= MONO_FLOOR
    )

    return {
        "icir_min": _round(icir_min, 4),
        "icir_max": _round(icir_max, 4),
        "icir_robustness_ratio": icir_ratio,
        "ic_mean_min": _round(min(ic_means), 6) if ic_means else None,
        "ic_mean_max": _round(max(ic_means), 6) if ic_means else None,
        "mono_min": _round(min(monos), 4) if monos else None,
        "mono_max": _round(max(monos), 4) if monos else None,
        "ic_sign_consistent_across_universes": ic_sign_consistent,
        "csi300_passes_admission_floor": csi300_passes,
        "primary_universe": primary,
    }


def _hard_gate_status(
    primary_metrics: dict[str, Any],
    primary_audit_block: dict[str, Any],
) -> dict[str, Any]:
    """Apply a stripped CP01 to the primary-universe metrics.

    Reads ``ic_train`` from the raw audit block (not in the trimmed
    per-universe summary) so we can still compute the train→val decay
    flag without bloating the public schema.
    """
    mono_val = primary_metrics.get("monotonicity")
    ic_oos = primary_metrics.get("ic_mean")
    ic_train = (primary_audit_block.get("ic_train") or {}).get("ic_mean")

    flags: list[str] = []
    if mono_val is not None and abs(mono_val) < MONO_FLOOR:
        flags.append("mono_weak")
    if ic_oos is not None and abs(ic_oos) < 0.008:
        flags.append("ic_oos_below_floor")
    if (
        ic_train is not None
        and ic_oos is not None
        and ic_train != 0
        and (ic_oos / ic_train if ic_train != 0 else 0) < 0.20
    ):
        flags.append("oos_decay_severe")
    if mono_val is not None and ic_oos is not None and (mono_val * ic_oos) < 0:
        flags.append("mono_ic_sign_mismatch")

    return {
        "primary_universe_flags": flags,
        "needs_reverdict": bool(flags),
    }


def apply_audit(
    factor_yaml: Path,
    audit_yaml: Path,
    *,
    primary_universe: str,
    run_name: str,
    audit_relpath: str,
) -> dict[str, Any]:
    record = load_yaml(factor_yaml) or {}
    audit = load_yaml(audit_yaml) or {}

    grid_in = audit.get("new_metrics_by_universe") or {}
    grid_out: dict[str, dict[str, Any]] = {}
    for name, block in grid_in.items():
        grid_out[name] = _flatten_universe_block(block)

    if primary_universe not in grid_out:
        raise ValueError(
            f"{factor_yaml.name}: primary_universe={primary_universe} missing "
            f"in audit grid ({sorted(grid_out)})"
        )
    primary_metrics = grid_out[primary_universe]
    if "error" in primary_metrics:
        logger.warning(
            "%s: primary universe %s has error=%s — leaving validation_metrics unset",
            factor_yaml.name, primary_universe, primary_metrics.get("error"),
        )

    primary_audit_block = grid_in.get(primary_universe) or {}
    primary_ic_val = primary_audit_block.get("ic_validation") or {}
    primary_q_val = primary_audit_block.get("quintile_validation") or {}
    primary_ls = primary_q_val.get("ls_stats") or {}
    record["primary_universe"] = primary_universe
    record["validation_metrics"] = {
        "coverage": _round(primary_audit_block.get("coverage"), 4),
        "ic_mean": _round(primary_ic_val.get("ic_mean"), 6),
        "ic_ir": _round(primary_ic_val.get("ic_ir"), 4),
        "ic_win_rate": _round(primary_ic_val.get("ic_win_rate"), 4),
        "monotonicity": _round(primary_q_val.get("monotonicity"), 4),
        "long_short_mean": _round(primary_q_val.get("ls_mean"), 6),
        "long_short_sharpe": _round(primary_ls.get("sharpe"), 4),
        "long_short_tstat": _round(primary_ls.get("tstat"), 4),
        "long_short_max_dd": _round(primary_ls.get("max_dd"), 4),
    }
    record["validation_metrics_by_universe"] = grid_out
    record["universe_robustness"] = _compute_robustness(
        grid_out, primary=primary_universe
    )
    record["reverdict_status"] = _hard_gate_status(primary_metrics, primary_audit_block)
    record["recompute_provenance"] = {
        "run_name": run_name,
        "applied_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "audit_relpath": audit_relpath,
    }
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-name", default=AUDIT_DIR_DEFAULT)
    parser.add_argument("--primary-universe", default=PRIMARY_UNIVERSE_DEFAULT)
    parser.add_argument("--factors", nargs="*", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    paths = StoragePaths()
    audit_dir = paths.cache_dir / "recompute_audit" / args.run_name
    if not audit_dir.exists():
        raise FileNotFoundError(f"audit dir missing: {audit_dir}")

    targets = (
        [paths.factor_yaml_file(fid) for fid in args.factors]
        if args.factors
        else sorted(paths.factors_dir.glob("F*.yaml"))
    )

    summary: list[dict[str, Any]] = []
    for factor_yaml in targets:
        fid = factor_yaml.stem
        audit_yaml = audit_dir / f"{fid}.yaml"
        if not audit_yaml.exists():
            logger.warning("audit missing for %s — skipped", fid)
            continue
        try:
            audit_relpath = str(audit_yaml.relative_to(paths.root))
        except ValueError:
            audit_relpath = str(audit_yaml)
        try:
            updated = apply_audit(
                factor_yaml,
                audit_yaml,
                primary_universe=args.primary_universe,
                run_name=args.run_name,
                audit_relpath=audit_relpath,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("apply failed for %s: %s", fid, exc)
            summary.append({"factor_id": fid, "error": f"{type(exc).__name__}: {exc}"})
            continue
        rev = updated.get("reverdict_status") or {}
        summary.append(
            {
                "factor_id": fid,
                "name": updated.get("name"),
                "primary_ic_ir": updated["validation_metrics"].get("ic_ir"),
                "primary_mono": updated["validation_metrics"].get("monotonicity"),
                "csi300_passes": (updated["universe_robustness"] or {}).get(
                    "csi300_passes_admission_floor"
                ),
                "needs_reverdict": rev.get("needs_reverdict"),
                "flags": ",".join(rev.get("primary_universe_flags") or []),
            }
        )
        if not args.dry_run:
            save_yaml(factor_yaml, updated)
            logger.info("updated %s", factor_yaml.name)
        else:
            logger.info("[dry-run] would update %s", factor_yaml.name)

    summary_path = audit_dir / "apply_summary.csv"
    import csv

    if summary:
        keys = list(summary[0].keys())
        with summary_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(summary)
        logger.info("wrote %s", summary_path)


if __name__ == "__main__":
    main()
