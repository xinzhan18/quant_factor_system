"""§7.MT multiple testing budget — Phase 3 pre-pack input.

Core insight (refactor_plan §7.MT): the multiple-testing counters are
**pure functions of ``storage/batches/``**. There is no persistent
``batch_usage`` table because git already has all the data — scanning a
hundred small ``manifest.yaml`` files takes milliseconds, so we never
cache.

Two public functions:

* :func:`scan_batches_for_mt` — walk ``batches/batch_*/manifest.yaml``,
  count judged-only batches, bucket by direction and sample_policy
  version. Pure function, no I/O besides glob + yaml load.
* :func:`compute_mt_budget` — consume those counts plus the current
  candidate's validation metrics, apply the §7.MT formula (constants
  from ``config.yaml.thresholds.mt_budget``), return the dict that goes
  into CP03 ``numeric_hint``.

The formula itself and its constants are extracted from the legacy
``research.stats.multiple_testing`` module into the new namespace — we
do not import from ``research.stats`` (that package is in the R9
deprecated list).

Three hard constraints (per refactor_plan §7.MT):

1. **Python algorithm**, LLM cannot override the bucket value
2. **sample_policy_version bump resets validation_exposure** — the scan
   only counts batches whose manifest declares the current version
3. **Judged-only** — scan skips batches without a ``judge.md`` (avoids
   half-finished batches polluting counts)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from research.storage.yaml_io import load_yaml


# ---------------------------------------------------------------------------
# Scan
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MtCounts:
    """Counts produced by :func:`scan_batches_for_mt`."""

    cumulative_candidates: int
    direction_candidates: int
    validation_exposure: int
    n_batches_scanned: int


def scan_batches_for_mt(
    batches_dir: str | Path,
    current_batch_id: str,
    current_direction: str,
    sample_policy_version: str,
) -> MtCounts:
    """Count judged-only historical batches from the ``batches/`` directory.

    Parameters
    ----------
    batches_dir
        Path to ``storage/batches/``.
    current_batch_id
        The batch we are about to judge — excluded from counts to avoid
        self-correction loops.
    current_direction
        ``direction`` string to match for ``direction_candidates``.
    sample_policy_version
        Only batches with this exact version contribute to
        ``validation_exposure``. Bumping the version in ``config.yaml``
        effectively resets the budget.

    Returns
    -------
    MtCounts
        Counts ready to be passed into :func:`compute_mt_budget`.
    """
    root = Path(batches_dir)
    if not root.exists():
        return MtCounts(0, 0, 0, 0)

    cumulative = 0
    per_direction = 0
    exposure = 0
    scanned = 0

    for manifest_path in sorted(root.glob("batch_*/manifest.yaml")):
        batch_dir = manifest_path.parent
        batch_id = batch_dir.name

        # Skip current batch and anything lexicographically after it
        if batch_id >= current_batch_id:
            continue
        # Judged-only: require judge.md alongside manifest
        if not (batch_dir / "judge.md").exists():
            continue

        manifest = load_yaml(manifest_path)
        if not manifest:
            continue

        candidates = manifest.get("candidates") or []
        n_cand = len(candidates)
        cumulative += n_cand
        scanned += 1

        if manifest.get("direction") == current_direction:
            per_direction += n_cand
        if manifest.get("sample_policy_version") == sample_policy_version:
            exposure += 1

    return MtCounts(
        cumulative_candidates=cumulative,
        direction_candidates=per_direction,
        validation_exposure=exposure,
        n_batches_scanned=scanned,
    )


# ---------------------------------------------------------------------------
# Formula
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MtBudgetConfig:
    """Constants for the §7.MT formula — loaded from ``config.yaml``.

    The default values below come from the initial placeholder
    calibration in ``storage/config.yaml.thresholds.mt_budget``. They
    are re-calibrated on a first PR against historical ``batches/``.
    """

    family_log_base: float = 600
    direction_log_base: float = 80
    exposure_divisor: float = 40
    weight_family: float = 0.50
    weight_direction: float = 0.30
    weight_exposure: float = 0.20
    bucket_low: float = 0.40
    bucket_high: float = 0.70
    adjusted_strength_discount: float = 0.50

    @classmethod
    def from_config_dict(cls, cfg: dict[str, Any]) -> "MtBudgetConfig":
        """Build from a ``config.yaml.thresholds.mt_budget`` sub-dict."""
        weights = cfg.get("weights", {})
        return cls(
            family_log_base=float(cfg.get("family_log_base", cls.family_log_base)),
            direction_log_base=float(
                cfg.get("direction_log_base", cls.direction_log_base)
            ),
            exposure_divisor=float(
                cfg.get("exposure_divisor", cls.exposure_divisor)
            ),
            weight_family=float(weights.get("family", cls.weight_family)),
            weight_direction=float(weights.get("direction", cls.weight_direction)),
            weight_exposure=float(weights.get("exposure", cls.weight_exposure)),
            bucket_low=float(cfg.get("bucket_low", cls.bucket_low)),
            bucket_high=float(cfg.get("bucket_high", cls.bucket_high)),
            adjusted_strength_discount=float(
                cfg.get(
                    "adjusted_strength_discount", cls.adjusted_strength_discount
                )
            ),
        )


def _raw_mt_score(counts: MtCounts, cfg: MtBudgetConfig) -> dict[str, Any]:
    """Compute the raw score plus its three term breakdown."""
    # Protect against log(1) or log(<=1) — clamp the log base to a sane floor
    family_base = max(cfg.family_log_base, 2.0)
    direction_base = max(cfg.direction_log_base, 2.0)
    divisor = max(cfg.exposure_divisor, 1.0)

    term_family = float(
        np.clip(np.log1p(counts.cumulative_candidates) / math.log(family_base), 0.0, 1.0)
    )
    term_direction = float(
        np.clip(np.log1p(counts.direction_candidates) / math.log(direction_base), 0.0, 1.0)
    )
    term_exposure = float(np.clip(counts.validation_exposure / divisor, 0.0, 1.0))

    score = (
        cfg.weight_family * term_family
        + cfg.weight_direction * term_direction
        + cfg.weight_exposure * term_exposure
    )
    return {
        "score": float(score),
        "terms": {
            "family": term_family,
            "direction": term_direction,
            "exposure": term_exposure,
        },
    }


def _bucket_from_score(score: float, cfg: MtBudgetConfig) -> str:
    if score < cfg.bucket_low:
        return "low"
    if score <= cfg.bucket_high:
        return "medium"
    return "high"


def _search_adjusted_strength(
    ic_mean: float,
    ic_ir: float,
    mono: float,
    expanding_pass: bool,
    mt_score: float,
    discount: float,
) -> dict[str, Any]:
    """Raw effect-strength composite, discounted by multiple-testing risk.

    Uses the same coefficient structure as the legacy
    ``compute_search_adjusted_strength`` to preserve tested semantics:
    40% IC mean (normalized to 0.02), 30% IC IR (to 0.20),
    20% monotonicity (to 0.40), 10% expanding-window pass flag.

    NaN inputs are treated as 0.0 (most conservative for an
    un-measurable factor).
    """
    _ic = 0.0 if ic_mean is None or np.isnan(ic_mean) else ic_mean
    _ir = 0.0 if ic_ir is None or np.isnan(ic_ir) else ic_ir
    _mono = 0.0 if mono is None or np.isnan(mono) else mono

    raw = (
        0.40 * float(np.clip(abs(_ic) / 0.02, 0, 1))
        + 0.30 * float(np.clip(abs(_ir) / 0.20, 0, 1))
        + 0.20 * float(np.clip(abs(_mono) / 0.40, 0, 1))
        + 0.10 * float(bool(expanding_pass))
    )
    adjusted = float(raw * (1 - discount * mt_score))

    if adjusted >= 0.70:
        bucket = "high"
    elif adjusted >= 0.40:
        bucket = "medium"
    else:
        bucket = "low"

    return {
        "raw": round(raw, 4),
        "adjusted": round(adjusted, 4),
        "bucket": bucket,
    }


def compute_mt_budget(
    counts: MtCounts,
    cfg: MtBudgetConfig,
    *,
    ic_mean: float | None = None,
    ic_ir: float | None = None,
    monotonicity: float | None = None,
    expanding_pass: bool = False,
) -> dict[str, Any]:
    """Produce the full §7.MT numeric_hint dict for one candidate.

    Parameters
    ----------
    counts
        Output of :func:`scan_batches_for_mt`.
    cfg
        Formula constants (from ``config.yaml.thresholds.mt_budget``).
    ic_mean, ic_ir, monotonicity, expanding_pass
        The candidate's validation effect metrics. If any are missing,
        the search-adjusted strength is computed treating them as 0.

    Returns
    -------
    dict
        The complete CP03 numeric_hint fragment:

        .. code-block:: yaml

           mt_score: 0.52
           mt_bucket: medium
           search_adjusted_strength:
             raw: 0.62
             adjusted: 0.41
             bucket: medium
           mt_breakdown:
             cumulative_candidates: 612
             direction_candidates: 47
             validation_exposure: 102
             terms:
               family: 0.8
               direction: 0.6
               exposure: 1.0
    """
    raw = _raw_mt_score(counts, cfg)
    mt_score = round(raw["score"], 4)
    bucket = _bucket_from_score(raw["score"], cfg)

    search_adjusted = _search_adjusted_strength(
        ic_mean=float(ic_mean) if ic_mean is not None else 0.0,
        ic_ir=float(ic_ir) if ic_ir is not None else 0.0,
        mono=float(monotonicity) if monotonicity is not None else 0.0,
        expanding_pass=expanding_pass,
        mt_score=raw["score"],
        discount=cfg.adjusted_strength_discount,
    )

    return {
        "mt_score": mt_score,
        "mt_bucket": bucket,
        "search_adjusted_strength": search_adjusted,
        "mt_breakdown": {
            "cumulative_candidates": counts.cumulative_candidates,
            "direction_candidates": counts.direction_candidates,
            "validation_exposure": counts.validation_exposure,
            "n_batches_scanned": counts.n_batches_scanned,
            "terms": raw["terms"],
        },
    }
