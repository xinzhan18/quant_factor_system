"""Phase 2 EXECUTE orchestrator (schema v3).

Consumes a frozen manifest + pre-computed factor values + reference data
and produces ``batches/batch_{id}/result.yaml``. Zero LLM involvement.

Design invariants (result.yaml schema v3):

* **Single source of truth per metric** — IC stats live at
  ``candidates[].ic.*``, monotonicity at ``candidates[].quintile.*.monotonicity``,
  library correlation at ``candidates[].uniqueness.max_lib_corr``. No parallel
  duplicated blocks. Every metric is produced by exactly one vectorized
  module.
* **Multi-horizon, not multi-universe** — the orchestrator runs every
  entry in ``inputs.forward_returns_by_horizon`` on both train and
  validation and derives the IC-decay half-life from the per-horizon
  train means. Multi-universe is not part of this phase.
* **``multiple_testing_risk_bucket`` is populated by Phase 3 pre-pack**
  (``checkpoints/generator.py``) — Phase 2 writes ``None``.
* **Per-candidate failures are isolated** — an exception on one
  candidate sets its ``compute_error`` field and produces no metric
  fields; sibling candidates continue normally.

Downstream consumers (hard_gates / generator / factor_writer) read
``candidates[]`` fields directly — see the plan document for the field
path table.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from core.factor_stats import multiindex_to_flat
from research.compute.preprocess import PreprocessConfig, preprocess_factor
from research.compute.vectorized_barra import compute_barra_exposures
from research.compute.vectorized_distribution import compute_distribution
from research.compute.vectorized_feasibility import (
    build_proxy_portfolio,
    compute_liquidity_coverage,
    compute_rebalance_stress,
    compute_signal_autocorr_lag1,
    compute_signal_half_life,
    compute_small_cap_concentration,
    compute_tail_concentration,
)
from research.compute.vectorized_ic import (
    compute_ic_analytics,
    compute_ic_half_life,
    compute_multi_horizon_ic,
)
from research.compute.vectorized_quintile import (
    compute_long_short_stats,
    compute_quintile_returns,
)
from research.compute.vectorized_redundancy import (
    compute_incremental_ic,
    compute_pairwise_redundancy,
)
from research.compute.vectorized_stability import (
    compute_sign_consistency,
    compute_split_stability,
    compute_train_validation_decay,
)
from research.storage.paths import StoragePaths
from research.storage.yaml_io import save_yaml

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


@dataclass
class CandidateInputs:
    """Per-candidate data bundle consumed by Phase 2."""

    candidate_id: str
    expression: str
    source_type: str  # "dsl" | "python"
    factor_series: pd.Series
    tradable_mask: pd.Series


@dataclass
class Phase2Inputs:
    """All inputs needed to run Phase 2 on a single batch."""

    batch_id: str
    candidates: list[CandidateInputs]

    forward_returns_by_horizon: dict[int, pd.DataFrame]
    """``{horizon_days: flat [time, symbol, value]}`` — forward returns
    for every horizon to score. ``primary_horizon`` must be one of the
    keys; its IC drives the train/validation top-level fields and the
    Barra residual IC."""

    primary_horizon: int

    style_matrix: pd.DataFrame
    library_signals: dict[str, pd.DataFrame]
    amount_data: pd.DataFrame
    market_cap: pd.DataFrame

    train_range: tuple[str, str]
    validation_range: tuple[str, str]

    preprocess_config: PreprocessConfig = field(default_factory=PreprocessConfig)
    universe: str = "csi1000"

    # Optional — when provided, per-candidate Q1..Qn daily / IC daily /
    # long-short daily series are persisted to
    # ``paths.candidate_diagnostics_dir(batch_id, cand_id)`` and
    # ``result.yaml.candidates[].diagnostics_relpath`` references them.
    paths: StoragePaths | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _series_to_mi_df(s: pd.Series, col: str = "value") -> pd.DataFrame:
    """MultiIndex(time, symbol) Series → single-column DataFrame."""
    df = s.to_frame(name=col)
    df.index.names = ["datetime", "instrument"]
    return df


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _expression_depth(expr: str) -> int:
    """Crude nesting depth — open-paren count, matching legacy behavior."""
    return int(expr.count("(")) if expr else 0


def _strip_ic_series(by_horizon: dict[int, dict[str, Any]]) -> dict[int, dict[str, Any]]:
    """Drop ``ic_series_train`` / ``ic_series_validation`` before YAML."""
    return {
        h: {
            "train": blk["train"],
            "validation": blk["validation"],
        }
        for h, blk in by_horizon.items()
    }


# ---------------------------------------------------------------------------
# Diagnostics parquet writer
# ---------------------------------------------------------------------------


def _persist_diagnostics(
    *,
    inputs: "Phase2Inputs",
    candidate_id: str,
    clean_series: pd.Series,
    qret_train: dict[str, Any],
    qret_val: dict[str, Any],
    ic_train_series: pd.Series,
    ic_val_series: pd.Series,
) -> str | None:
    """Write per-candidate daily diagnostic series to parquet.

    Writes six files under ``paths.candidate_diagnostics_dir``:

    * ``quantile_daily_train.parquet`` — (date × Q1..Qn)
    * ``quantile_daily_validation.parquet`` — (date × Q1..Qn)
    * ``long_short_daily.parquet`` — (date × value) derived from Q5-Q1
    * ``ic_daily.parquet`` — (date × ic_train, ic_validation)
    * ``coverage_daily.parquet`` — (date × coverage fraction of universe)
    * ``factor_hist.parquet`` — 50-bin IS/OOS factor value histogram

    Returns the diagnostics dir path relative to the storage root so
    Phase 4 can resolve it without hard-coding ``cache/``.
    """
    if inputs.paths is None:
        return None
    out_dir = inputs.paths.candidate_diagnostics_dir(inputs.batch_id, candidate_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    q_train_df: pd.DataFrame = qret_train["per_quintile_daily"]
    q_val_df: pd.DataFrame = qret_val["per_quintile_daily"]
    q_train_df.to_parquet(out_dir / "quantile_daily_train.parquet")
    q_val_df.to_parquet(out_dir / "quantile_daily_validation.parquet")

    # Long-short series = Q_n - Q_1 per date (preserves NaN days)
    def _ls_from(qdf: pd.DataFrame) -> pd.DataFrame:
        if qdf.empty:
            return pd.DataFrame({"long_short": []}, index=pd.Index([], name="datetime"))
        q_last = qdf.columns[-1]
        return pd.DataFrame(
            {"long_short": (qdf[q_last] - qdf["q1"]).to_numpy()},
            index=qdf.index,
        )

    ls_train = _ls_from(q_train_df)
    ls_val = _ls_from(q_val_df)
    pd.concat(
        {"train": ls_train, "validation": ls_val},
        names=["split"],
    ).to_parquet(out_dir / "long_short_daily.parquet")

    ic_df = pd.concat(
        {
            "train": ic_train_series.rename("ic").to_frame(),
            "validation": ic_val_series.rename("ic").to_frame(),
        },
        names=["split"],
    )
    ic_df.to_parquet(out_dir / "ic_daily.parquet")

    # Coverage daily: fraction of universe with non-null factor value per date.
    # Uses the preprocessed series so coverage matches what enters downstream
    # analytics (same series as the other 4 diagnostic files).
    time_level = clean_series.index.names[0]
    factor_wide = clean_series.unstack(level=-1)
    if factor_wide.shape[1] == 0:
        coverage_values = np.zeros(factor_wide.shape[0], dtype=float)
    else:
        coverage_values = (
            factor_wide.notna().sum(axis=1).to_numpy() / factor_wide.shape[1]
        )
    coverage_df = pd.DataFrame(
        {"coverage": coverage_values},
        index=pd.Index(factor_wide.index, name="datetime"),
    )
    coverage_df.to_parquet(out_dir / "coverage_daily.parquet")

    # Factor value histogram (IS / OOS split via 50 shared bins over pooled range).
    # Bin edges span 0.5th-99.5th pooled percentile for robustness vs. outliers.
    is_start = pd.Timestamp(inputs.train_range[0])
    is_end = pd.Timestamp(inputs.train_range[1])
    oos_start = pd.Timestamp(inputs.validation_range[0])
    oos_end = pd.Timestamp(inputs.validation_range[1])

    clean_flat = clean_series.dropna().reset_index()
    clean_flat.columns = ["datetime", "instrument", "v"]
    is_mask = (clean_flat["datetime"] >= is_start) & (
        clean_flat["datetime"] <= is_end
    )
    oos_mask = (clean_flat["datetime"] >= oos_start) & (
        clean_flat["datetime"] <= oos_end
    )
    is_vals = clean_flat.loc[is_mask, "v"].to_numpy()
    oos_vals = clean_flat.loc[oos_mask, "v"].to_numpy()

    pooled = (
        np.concatenate([is_vals, oos_vals])
        if (is_vals.size + oos_vals.size) > 0
        else np.array([0.0, 1.0])
    )
    lo, hi = np.nanpercentile(pooled, [0.5, 99.5])
    if not np.isfinite(lo) or not np.isfinite(hi) or lo >= hi:
        lo, hi = 0.0, 1.0
    edges = np.linspace(lo, hi, 51)
    is_hist, _ = np.histogram(is_vals, bins=edges)
    oos_hist, _ = np.histogram(oos_vals, bins=edges)
    is_freq = is_hist / max(is_hist.sum(), 1)
    oos_freq = oos_hist / max(oos_hist.sum(), 1)
    pd.DataFrame(
        {
            "bin_edge_lo": edges[:-1],
            "bin_edge_hi": edges[1:],
            "is_freq": is_freq,
            "oos_freq": oos_freq,
        }
    ).to_parquet(out_dir / "factor_hist.parquet", index=False)

    try:
        rel = str(out_dir.relative_to(inputs.paths.root))
    except ValueError:
        rel = str(out_dir)
    return rel


# ---------------------------------------------------------------------------
# Per-candidate evaluation
# ---------------------------------------------------------------------------


def _evaluate_candidate(
    cand: CandidateInputs,
    inputs: Phase2Inputs,
) -> dict[str, Any]:
    """Run the full vectorized metric suite on one candidate (schema v3).

    On failure, returns ``{"candidate_id", "expression", "source_type",
    "expression_depth", "compute_error"}`` only — no partial metric
    fields, sibling candidates continue.
    """
    try:
        if inputs.primary_horizon not in inputs.forward_returns_by_horizon:
            raise ValueError(
                f"primary_horizon={inputs.primary_horizon} missing from "
                "forward_returns_by_horizon"
            )

        # --- 1. Preprocess (tradable mask → MAD winsorize → z-score) ---
        clean_series = preprocess_factor(
            cand.factor_series,
            inputs.preprocess_config,
            tradable_mask=cand.tradable_mask,
        )
        coverage = float(clean_series.notna().mean())

        cand_mi = _series_to_mi_df(clean_series.dropna())
        if cand_mi.empty:
            raise ValueError("preprocessed factor is empty (all NaN)")

        factor_flat = cand_mi.reset_index()
        factor_flat.columns = ["time", "symbol", "value"]

        # --- 2. Multi-horizon IC (one pass for every horizon × split) ---
        by_horizon = compute_multi_horizon_ic(
            factor_flat,
            inputs.forward_returns_by_horizon,
            train_range=inputs.train_range,
            validation_range=inputs.validation_range,
        )
        primary = by_horizon[inputs.primary_horizon]
        ic_train_series: pd.Series = primary["ic_series_train"]
        ic_val_series: pd.Series = primary["ic_series_validation"]
        train_ic_mean = primary["train"]["ic_mean"]
        val_ic_mean = primary["validation"]["ic_mean"]

        # Primary horizon sign — drives Barra survival + downstream gates
        if val_ic_mean is None or not np.isfinite(val_ic_mean) or val_ic_mean == 0:
            primary_sign = 1
        else:
            primary_sign = 1 if val_ic_mean > 0 else -1

        # Combined (train + validation) IC series for by-year / quarter / autocorr
        combined_series = pd.concat(
            [ic_train_series, ic_val_series]
        ).sort_index()
        ic_analytics = compute_ic_analytics(combined_series)

        sign_consistent = compute_sign_consistency(ic_train_series, ic_val_series)
        tv_decay = compute_train_validation_decay(train_ic_mean, val_ic_mean)
        tv_decay_out: float | None = (
            None if pd.isna(tv_decay) else round(float(tv_decay), 4)
        )

        horizon_train_means = {
            h: blk["train"]["ic_mean"] for h, blk in by_horizon.items()
        }
        half_life_days = compute_ic_half_life(horizon_train_means)

        # --- 3. Quintile (train + validation) + long-short stats ---
        fv_train_flat = factor_flat[
            (factor_flat["time"] >= pd.Timestamp(inputs.train_range[0]))
            & (factor_flat["time"] <= pd.Timestamp(inputs.train_range[1]))
        ]
        fv_val_flat = factor_flat[
            (factor_flat["time"] >= pd.Timestamp(inputs.validation_range[0]))
            & (factor_flat["time"] <= pd.Timestamp(inputs.validation_range[1]))
        ]
        primary_returns = inputs.forward_returns_by_horizon[inputs.primary_horizon]
        fr_train_flat = primary_returns[
            (primary_returns["time"] >= pd.Timestamp(inputs.train_range[0]))
            & (primary_returns["time"] <= pd.Timestamp(inputs.train_range[1]))
        ]
        fr_val_flat = primary_returns[
            (primary_returns["time"] >= pd.Timestamp(inputs.validation_range[0]))
            & (primary_returns["time"] <= pd.Timestamp(inputs.validation_range[1]))
        ]

        qret_train = compute_quintile_returns(fv_train_flat, fr_train_flat)
        qret_val = compute_quintile_returns(fv_val_flat, fr_val_flat)

        ls_stats_train = compute_long_short_stats(qret_train["long_short_daily"])
        ls_stats_val = compute_long_short_stats(qret_val["long_short_daily"])

        # Persist daily diagnostic series to parquet (so Phase 4 doesn't recompute)
        diagnostics_relpath = _persist_diagnostics(
            inputs=inputs,
            candidate_id=cand.candidate_id,
            clean_series=clean_series,
            qret_train=qret_train,
            qret_val=qret_val,
            ic_train_series=ic_train_series,
            ic_val_series=ic_val_series,
        )

        # --- 4. Stability (split + decay + sign consistency already above) ---
        split = compute_split_stability(ic_val_series)

        # --- 5. Uniqueness (library correlation + incremental IC) ---
        redundancy = compute_pairwise_redundancy(cand_mi, inputs.library_signals)

        ret_flat = inputs.forward_returns_by_horizon[inputs.primary_horizon]
        library_flat = {
            fid: multiindex_to_flat(df)
            for fid, df in inputs.library_signals.items()
        }
        incr_ic = compute_incremental_ic(factor_flat, ret_flat, library_flat)

        uniqueness = {
            "max_lib_corr": redundancy["max_lib_corr"],
            "nearest_factor_id": redundancy["nearest_factor_id"],
            "is_near_duplicate": redundancy["is_near_duplicate"],
            "exceeds_threshold": redundancy["exceeds_threshold"],
            "all_correlations": redundancy["all_correlations"],
            "incremental_ic": incr_ic,
        }

        # --- 6. Feasibility (portfolio-side + signal persistence) ---
        tradable_mi = _series_to_mi_df(
            cand.tradable_mask.astype(bool), col="tradable"
        )
        proxy = build_proxy_portfolio(cand_mi, tradable_mi)
        turnover_mean = float(proxy.turnover.mean())
        lcr = compute_liquidity_coverage(proxy.abs_weights, inputs.amount_data)
        tail = compute_tail_concentration(proxy.abs_weights)
        small_cap = compute_small_cap_concentration(
            proxy.abs_weights, inputs.market_cap
        )
        signal_half_life = compute_signal_half_life(cand_mi)
        signal_autocorr = compute_signal_autocorr_lag1(cand_mi)
        rebalance_stress = compute_rebalance_stress(turnover_mean, tail, lcr)

        # --- 7. Barra residual IC (CP04) — primary horizon only ---
        barra = compute_barra_exposures(
            factor_flat,
            inputs.style_matrix,
            primary_returns,
            raw_view_ic=val_ic_mean,
        )

        # --- 8. Distribution ---
        distribution = compute_distribution(cand_mi)

        return {
            "candidate_id": cand.candidate_id,
            "expression": cand.expression,
            "source_type": cand.source_type,
            "expression_depth": _expression_depth(cand.expression),
            "coverage": round(coverage, 4),
            "sign": int(primary_sign),
            "compute_error": None,
            "ic": {
                "train": primary["train"],
                "validation": primary["validation"],
                "sign_consistent": sign_consistent,
                "train_validation_decay": tv_decay_out,
                "by_year": ic_analytics["by_year"],
                "autocorr_lag1": ic_analytics["autocorr_lag1"],
                "cum_ic_max_drawdown": ic_analytics["cum_ic_max_drawdown"],
                "best_quarter": ic_analytics["best_quarter"],
                "worst_quarter": ic_analytics["worst_quarter"],
                "by_horizon": _strip_ic_series(by_horizon),
                "half_life_days": half_life_days,
            },
            "diagnostics_relpath": diagnostics_relpath,
            "quintile": {
                "train": {
                    **qret_train["quintile_returns"],
                    "monotonicity": qret_train["monotonicity"],
                    "ls_mean": qret_train["long_short_mean"],
                    "n_days": qret_train["long_short_n_days"],
                },
                "validation": {
                    **qret_val["quintile_returns"],
                    "monotonicity": qret_val["monotonicity"],
                    "ls_mean": qret_val["long_short_mean"],
                    "n_days": qret_val["long_short_n_days"],
                },
                "ls_stats": {
                    "train": ls_stats_train,
                    "validation": ls_stats_val,
                },
            },
            "stability": {"split_stability": split},
            "uniqueness": uniqueness,
            "feasibility": {
                "turnover_mean": turnover_mean,
                "liquidity_coverage": lcr,
                "tail_concentration": tail,
                "small_cap_concentration": small_cap,
                "signal_half_life": signal_half_life,
                "signal_autocorr_lag1": signal_autocorr,
                "rebalance_stress": rebalance_stress,
            },
            "barra": barra,
            "distribution": distribution,
            "multiple_testing_risk_bucket": None,
        }
    except Exception as exc:  # noqa: BLE001 — intentional catch-all
        logger.exception(
            "phase2: candidate %s failed: %s", cand.candidate_id, exc
        )
        return {
            "candidate_id": cand.candidate_id,
            "expression": cand.expression,
            "source_type": cand.source_type,
            "expression_depth": _expression_depth(cand.expression),
            "compute_error": f"{type(exc).__name__}: {exc}",
        }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_phase2(inputs: Phase2Inputs, output_path: str | Path) -> dict[str, Any]:
    """Run Phase 2 on all candidates in *inputs* and write ``result.yaml``."""
    results = [_evaluate_candidate(c, inputs) for c in inputs.candidates]

    n_ok = sum(1 for r in results if r.get("compute_error") is None)
    n_err = len(results) - n_ok

    horizons = sorted(int(h) for h in inputs.forward_returns_by_horizon.keys())

    result = {
        "batch_id": inputs.batch_id,
        "generated_at": _now_iso(),
        "universe": inputs.universe,
        "train_range": list(inputs.train_range),
        "validation_range": list(inputs.validation_range),
        "horizons": horizons,
        "primary_horizon": int(inputs.primary_horizon),
        "n_candidates": len(results),
        "n_ok": n_ok,
        "n_errors": n_err,
        "candidates": results,
    }

    save_yaml(output_path, result)
    logger.info(
        "phase2: wrote %s (%d candidates, %d errors)",
        output_path,
        len(results),
        n_err,
    )
    return result
