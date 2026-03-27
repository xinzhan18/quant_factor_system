"""Baseline alpha factor evaluation.

Evaluates ~75 well-known alpha factors across 3 batches (A, B, C) to build
a comprehensive IC baseline map. Factors that pass all pipeline stages are
automatically admitted to the library.

Usage:
    python -m scripts.baseline_eval [--batch A|B|C|all] [--ic-only]
"""

from __future__ import annotations

import argparse
import logging
import multiprocessing
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml

# Must use fork for Qlib compatibility
multiprocessing.set_start_method("fork", force=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from mining.config import MiningConfig
from mining.evaluator import FactorMiningEvaluator, BatchResult
from mining.operators import register_custom_operators

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("baseline_eval")

CANDIDATES_DIR = PROJECT_ROOT / "mining" / "candidates"
MEMORY_DIR = PROJECT_ROOT / "mining" / "memory"

BATCH_FILES = {
    "A": CANDIDATES_DIR / "baseline_A.yaml",
    "B": CANDIDATES_DIR / "baseline_B.yaml",
    "C": CANDIDATES_DIR / "baseline_C.yaml",
}


def load_candidates(batch_file: Path) -> List[Dict[str, Any]]:
    """Load candidates from a YAML batch file."""
    with open(batch_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    candidates = data.get("candidates", [])
    batch_id = data.get("batch_id", batch_file.stem)
    for c in candidates:
        c["batch"] = batch_id
    return candidates


def run_ic_only(evaluator: FactorMiningEvaluator, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run only Stage 1 (fast IC screening) and return all results with IC values.

    Unlike evaluate_batch, this does NOT filter — it returns IC for every candidate
    so we can build a comprehensive IC map.
    """
    subset = evaluator._get_fast_screening_universe()
    returns = evaluator._get_returns_qlib(subset, evaluator.config.train_start, evaluator.config.train_end)
    aux = evaluator._load_aux_data(subset, evaluator.config.train_start, evaluator.config.train_end)
    results = []
    for c in candidates:
        try:
            values = evaluator._compute_factor_qlib(
                c["expression"], subset, evaluator.config.train_start, evaluator.config.train_end
            )
            ic_stats = evaluator._compute_ic_from_frames(values, returns, aux_data=aux)
            c["ic_stats"] = ic_stats
            logger.info(
                "  %-30s IC=%.4f  IR=%.3f  WR=%.2f  days=%d",
                c["name"],
                ic_stats.get("ic_mean", float("nan")),
                ic_stats.get("ic_ir", float("nan")),
                ic_stats.get("ic_win_rate", float("nan")),
                ic_stats.get("n_days", 0),
            )
        except Exception as e:
            c["ic_stats"] = {"error": str(e), "ic_mean": None}
            logger.warning("  %-30s ERROR: %s", c["name"], e)
        results.append(c)
    return results


def run_full_batch(evaluator: FactorMiningEvaluator, candidates: List[Dict[str, Any]]) -> BatchResult:
    """Run the full multi-stage pipeline on a batch."""
    return evaluator.evaluate_batch(candidates)


def save_ic_results(results: List[Dict[str, Any]], batch_key: str) -> Path:
    """Save IC-only results to YAML."""
    out_path = CANDIDATES_DIR / f"baseline_{batch_key}_result.yaml"
    output = {
        "batch_id": f"baseline_{batch_key}",
        "timestamp": datetime.now().isoformat(),
        "mode": "ic_screening",
        "summary": {
            "total": len(results),
            "computed": sum(1 for r in results if r.get("ic_stats", {}).get("ic_mean") is not None),
            "errors": sum(1 for r in results if "error" in r.get("ic_stats", {})),
        },
        "results": [],
    }
    for r in sorted(results, key=lambda x: abs(x.get("ic_stats", {}).get("ic_mean", 0) or 0), reverse=True):
        ic = r.get("ic_stats", {})
        entry = {
            "name": r["name"],
            "expression": r["expression"],
            "category": r.get("category", "other"),
            "ic_mean": ic.get("ic_mean"),
            "ic_std": ic.get("ic_std"),
            "ic_ir": ic.get("ic_ir"),
            "ic_win_rate": ic.get("ic_win_rate"),
            "n_days": ic.get("n_days", 0),
        }
        if "error" in ic:
            entry["error"] = ic["error"]
        output["results"].append(entry)
    with open(out_path, "w", encoding="utf-8") as f:
        yaml.dump(output, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return out_path


def save_full_results(result: BatchResult, batch_key: str) -> Path:
    """Save full pipeline results to YAML."""
    out_path = CANDIDATES_DIR / f"baseline_{batch_key}_result.yaml"

    def _clean(c: Dict[str, Any]) -> Dict[str, Any]:
        """Remove transient DataFrame values for YAML serialization."""
        return {k: v for k, v in c.items() if not k.startswith("_")}

    output = {
        "batch_id": f"baseline_{batch_key}",
        "timestamp": datetime.now().isoformat(),
        "mode": "full_pipeline",
        "summary": {
            "admitted": len(result.admitted),
            "rejected": len(result.rejected),
            "replacements": len(result.replacements),
        },
        "admitted": [_clean(c) for c in result.admitted],
        "rejected": [_clean(c) for c in result.rejected],
        "replacements": [
            {"new_factor": _clean(r["new_factor"]), "replaces": r["replaces"]}
            for r in result.replacements
        ],
    }
    with open(out_path, "w", encoding="utf-8") as f:
        yaml.dump(output, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return out_path


def build_baseline_yaml(all_results: Dict[str, List[Dict[str, Any]]]) -> Path:
    """Build comprehensive baseline.yaml from all IC results."""
    baseline_path = MEMORY_DIR / "baseline.yaml"
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    ic_map = []
    category_ics: Dict[str, List[float]] = {}
    custom_op_status: Dict[str, str] = {}

    # Known custom operators
    custom_ops = {
        "TsDecay", "TsMomentum", "TsAutoCorr", "RealizedVol", "TsEntropy",
        "AmihudIlliq", "HHI", "SignedPower", "Tanh", "Exp", "Sigmoid",
        "Softmax", "Scale", "Zscore", "Winsorize",
    }

    for batch_key, results in all_results.items():
        for r in results:
            ic_val = r.get("ic_stats", {}).get("ic_mean")
            error = r.get("ic_stats", {}).get("error")
            entry = {
                "name": r["name"],
                "expression": r["expression"],
                "category": r.get("category", "other"),
                "batch": f"baseline_{batch_key}",
                "ic_mean": round(ic_val, 6) if ic_val is not None else None,
            }
            if error:
                entry["error"] = error
            ic_map.append(entry)

            # Category aggregation
            cat = r.get("category", "other")
            if ic_val is not None:
                category_ics.setdefault(cat, []).append(abs(ic_val))

            # Track custom operator usage
            for op in custom_ops:
                if op + "(" in r["expression"]:
                    if error:
                        custom_op_status[op] = f"FAILED: {error}"
                    elif ic_val is not None:
                        custom_op_status[op] = f"OK (IC={ic_val:.4f})"
                    else:
                        custom_op_status[op] = "UNKNOWN"

    # Sort by |IC|
    ic_map.sort(key=lambda x: abs(x.get("ic_mean") or 0), reverse=True)

    # Category performance
    cat_perf = {}
    for cat, vals in sorted(category_ics.items()):
        import numpy as np
        cat_perf[cat] = {
            "count": len(vals),
            "avg_abs_ic": round(float(np.mean(vals)), 6),
            "max_abs_ic": round(float(np.max(vals)), 6),
        }

    baseline = {
        "generated_at": datetime.now().isoformat(),
        "total_factors": len(ic_map),
        "computed_successfully": sum(1 for e in ic_map if e.get("ic_mean") is not None),
        "above_threshold": sum(1 for e in ic_map if (e.get("ic_mean") or 0) and abs(e["ic_mean"]) >= 0.03),
        "ic_map": ic_map,
        "category_performance": cat_perf,
        "custom_operator_status": custom_op_status,
    }

    with open(baseline_path, "w", encoding="utf-8") as f:
        yaml.dump(baseline, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    return baseline_path


def print_summary(all_results: Dict[str, List[Dict[str, Any]]]) -> None:
    """Print a summary table of all results."""
    print("\n" + "=" * 80)
    print("BASELINE EVALUATION SUMMARY")
    print("=" * 80)

    all_entries = []
    for batch_key, results in all_results.items():
        for r in results:
            ic_val = r.get("ic_stats", {}).get("ic_mean")
            all_entries.append((r["name"], r.get("category", ""), ic_val, batch_key))

    # Sort by |IC|
    all_entries.sort(key=lambda x: abs(x[2] or 0), reverse=True)

    print(f"\n{'Name':<35} {'Category':<15} {'IC Mean':>10} {'Batch':>5}")
    print("-" * 70)
    for name, cat, ic, batch in all_entries:
        ic_str = f"{ic:.4f}" if ic is not None else "ERROR"
        marker = " ***" if ic is not None and abs(ic) >= 0.03 else ""
        print(f"{name:<35} {cat:<15} {ic_str:>10} {batch:>5}{marker}")

    # Stats
    valid = [e for e in all_entries if e[2] is not None]
    above = [e for e in valid if abs(e[2]) >= 0.03]
    print(f"\nTotal: {len(all_entries)} | Computed: {len(valid)} | |IC|>=0.03: {len(above)}")
    print("*** = passes IC threshold")


def main():
    parser = argparse.ArgumentParser(description="Baseline alpha factor evaluation")
    parser.add_argument("--batch", choices=["A", "B", "C", "all"], default="all",
                        help="Which batch to evaluate (default: all)")
    parser.add_argument("--ic-only", action="store_true",
                        help="Run IC screening only (no correlation check / admission)")
    args = parser.parse_args()

    batches = list(BATCH_FILES.keys()) if args.batch == "all" else [args.batch]

    logger.info("Initializing evaluator...")
    config = MiningConfig()
    evaluator = FactorMiningEvaluator(config)

    # Force single-threaded Qlib to ensure custom operators are available
    # (multiprocessing workers don't inherit operator registry)
    from qlib.config import C
    C.kernels = 1

    # Verify custom operators registered
    from qlib.data.ops import Operators
    registered = register_custom_operators()
    logger.info("Registered %d custom operators: %s", len(registered), list(registered.keys()))

    all_ic_results: Dict[str, List[Dict[str, Any]]] = {}

    for batch_key in batches:
        batch_file = BATCH_FILES[batch_key]
        candidates = load_candidates(batch_file)
        logger.info("=" * 60)
        logger.info("Batch %s: %d candidates from %s", batch_key, len(candidates), batch_file.name)
        logger.info("=" * 60)

        t0 = time.time()

        if args.ic_only:
            results = run_ic_only(evaluator, candidates)
            all_ic_results[batch_key] = results
            out_path = save_ic_results(results, batch_key)
        else:
            # First run IC-only to get comprehensive IC map
            ic_results = run_ic_only(evaluator, candidates)
            all_ic_results[batch_key] = ic_results
            save_ic_results(ic_results, batch_key)

            # Then run full pipeline for admission
            logger.info("Running full pipeline for batch %s...", batch_key)
            batch_result = run_full_batch(evaluator, candidates)
            out_path = save_full_results(batch_result, batch_key)

            logger.info(
                "Batch %s: %d admitted, %d rejected, %d replacements",
                batch_key, len(batch_result.admitted), len(batch_result.rejected), len(batch_result.replacements),
            )

            # Auto-admit passing factors
            if batch_result.admitted:
                from mining.library import FactorLibrary
                library = FactorLibrary(config)
                for factor in batch_result.admitted:
                    factor["metrics"] = factor.get("stage3", {})
                    fid = library.admit(factor)
                    logger.info("Admitted: %s → factor_%s (IC=%.4f)",
                                factor["name"], fid,
                                factor.get("stage3", {}).get("ic_mean_is", 0) or 0)

        elapsed = time.time() - t0
        logger.info("Batch %s completed in %.1f seconds. Results: %s", batch_key, elapsed, out_path)

    # Build baseline context
    if all_ic_results:
        baseline_path = build_baseline_yaml(all_ic_results)
        logger.info("Baseline IC map saved to: %s", baseline_path)

    # Print summary
    print_summary(all_ic_results)


if __name__ == "__main__":
    main()
