"""Phase 2 EXECUTE orchestrator.

Consumes a frozen manifest + pre-computed factor values + reference data
and produces ``batches/batch_{id}/result.yaml``. Zero LLM involvement.

The orchestrator is intentionally **thin**: all the heavy math lives in
``research.compute.vectorized_*`` modules. Phase 2's job is to:

1. split each candidate's signal into train / validation ranges
2. call every vectorized module and collect structured outputs
3. catch per-candidate failures so one bad candidate doesn't break the batch
4. serialize the whole thing to ``result.yaml`` with the frozen schema

Data ingestion (DB / Qlib / DSL expression evaluation) is **out of scope
for P1.4**. The inputs-dataclass is the contract between this orchestrator
and whatever future Phase 1 / data layer produces the factor values. That
boundary is what makes Phase 2 end-to-end-testable on synthetic data
without a live database.

The ``multiple_testing_risk_bucket`` field in ``result.yaml`` is left
``None`` at Phase 2 time; P2 ``checkpoints/generator.py`` fills it in
during Phase 3 pre-pack via ``stats/mt_budget.py`` (see §7.MT).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from research.compute.preprocess import PreprocessConfig, preprocess_factor
from research.compute.vectorized_barra import compute_barra_exposures
from research.compute.vectorized_feasibility import (
    build_proxy_portfolio,
    compute_half_life,
    compute_holding_period_proxy,
    compute_liquidity_coverage,
    compute_rebalance_stress,
    compute_small_cap_concentration,
    compute_tail_concentration,
)
from research.compute.vectorized_ic import (
    compute_effect_strength,
    compute_support_windows,
)
from research.compute.vectorized_quintile import compute_quintile_returns
from research.compute.vectorized_redundancy import compute_pairwise_redundancy
from research.compute.vectorized_stability import (
    compute_sign_consistency,
    compute_split_stability,
    compute_train_validation_decay,
)
from research.compute.report_card import compute_report_card
from research.storage.yaml_io import save_yaml

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schema + inputs
# ---------------------------------------------------------------------------

# Frozen result.yaml schema version. Bump this if the structure changes;
# P2 (Phase 3 JUDGE) cross-checks it so a schema mismatch fails loudly
# instead of silently mis-parsing.
RESULT_SCHEMA_VERSION = "1"


@dataclass
class CandidateInputs:
    """Per-candidate data bundle consumed by Phase 2.

    All Series/DataFrames use the conventional indices:

    * ``factor_series`` — MultiIndex ``(time, symbol)`` Series of raw
      factor values (pre-preprocess)
    * ``tradable_mask`` — MultiIndex ``(time, symbol)`` bool Series

    The orchestrator pivots / re-flattens as needed for each downstream
    vectorized module.
    """

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

    forward_returns_flat: pd.DataFrame
    """Flat ``[time, symbol, value]`` frame of forward returns."""

    style_matrix: pd.DataFrame
    """MultiIndex (datetime, instrument) with the 7 Barra style columns."""

    library_signals: dict[str, pd.DataFrame]
    """``{factor_id: MultiIndex DataFrame}`` — admitted factors for redundancy."""

    amount_data: pd.DataFrame
    """MultiIndex (datetime, instrument) single-column ``$amount``."""

    market_cap: pd.DataFrame
    """MultiIndex (datetime, instrument) single-column ``$market_cap``."""

    train_range: tuple[str, str]
    validation_range: tuple[str, str]
    support_windows: list[dict[str, Any]] = field(default_factory=list)

    sample_policy_version: str = "v3"
    preprocess_version: str = "p1"
    preprocess_config: PreprocessConfig = field(default_factory=PreprocessConfig)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _series_to_flat(s: pd.Series) -> pd.DataFrame:
    """MultiIndex(time, symbol) Series → flat [time, symbol, value]."""
    df = s.reset_index()
    df.columns = ["time", "symbol", "value"]
    return df


def _series_to_mi_df(s: pd.Series, col: str = "value") -> pd.DataFrame:
    """MultiIndex(time, symbol) Series → single-column DataFrame."""
    df = s.to_frame(name=col)
    df.index.names = ["datetime", "instrument"]
    return df


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Per-candidate evaluation
# ---------------------------------------------------------------------------


def _evaluate_candidate(
    cand: CandidateInputs,
    inputs: Phase2Inputs,
) -> dict[str, Any]:
    """Run the full vectorized metric suite on one candidate.

    On failure, returns a minimal dict with ``compute_error`` filled in —
    sibling candidates continue.
    """
    try:
        # --- 1. Preprocess (MAD winsorize + z-score) ---
        clean_series = preprocess_factor(
            cand.factor_series,
            inputs.preprocess_config,
            tradable_mask=cand.tradable_mask,
        )

        factor_flat = _series_to_flat(clean_series.dropna())
        if factor_flat.empty:
            raise ValueError("preprocessed factor is empty (all NaN)")

        coverage = float(clean_series.notna().mean())

        # --- 2. Effect strength (IC mean/std/ir/win_rate/mono) ---
        es = compute_effect_strength(
            factor_flat,
            inputs.forward_returns_flat,
            train_range=inputs.train_range,
            validation_range=inputs.validation_range,
        )
        ic_series_train = es.pop("ic_series_train")
        ic_series_val = es.pop("ic_series_validation")
        primary_sign = 1.0 if es["validation"]["ic_mean"] > 0 else -1.0

        # --- 3. Quintile returns + monotonicity on validation slice ---
        val_start, val_end = inputs.validation_range
        mask_fv = (factor_flat["time"] >= pd.Timestamp(val_start)) & (
            factor_flat["time"] <= pd.Timestamp(val_end)
        )
        mask_fr = (
            inputs.forward_returns_flat["time"] >= pd.Timestamp(val_start)
        ) & (inputs.forward_returns_flat["time"] <= pd.Timestamp(val_end))
        qret = compute_quintile_returns(
            factor_flat[mask_fv],
            inputs.forward_returns_flat[mask_fr],
        )

        # --- 4. Stability (split + support windows + decay + sign consistency) ---
        split = compute_split_stability(ic_series_val)
        support = (
            compute_support_windows(
                factor_flat,
                inputs.forward_returns_flat,
                primary_sign=primary_sign,
                windows=inputs.support_windows,
            )
            if inputs.support_windows
            else {"checks": [], "warning": "none"}
        )
        sign_ok = compute_sign_consistency(ic_series_train, ic_series_val)
        decay = compute_train_validation_decay(
            es["train"]["ic_mean"], es["validation"]["ic_mean"]
        )

        # --- 5. Redundancy vs library ---
        cand_mi = _series_to_mi_df(clean_series.dropna())
        redundancy = compute_pairwise_redundancy(cand_mi, inputs.library_signals)

        # --- 6. Feasibility (proxy portfolio + liq + concentration + stress) ---
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
        half_life = compute_half_life(cand_mi)
        holding = compute_holding_period_proxy(half_life)
        stress = compute_rebalance_stress(turnover_mean, tail, lcr)

        # --- 7. Barra residual IC (CP04) ---
        barra = compute_barra_exposures(
            factor_flat,
            inputs.style_matrix,
            inputs.forward_returns_flat,
            raw_view_ic=es["validation"]["ic_mean"],
        )

        # --- 8. Full 6-dimension FactorReportCard (旧 evaluator 多维分析) ---
        try:
            # factor_flat is [time, symbol, value]; split into IS/OOS DataFrames
            train_start_ts = pd.Timestamp(inputs.train_range[0])
            train_end_ts = pd.Timestamp(inputs.train_range[1])
            val_start_ts = pd.Timestamp(inputs.validation_range[0])
            val_end_ts = pd.Timestamp(inputs.validation_range[1])

            fv_is = factor_flat[
                (factor_flat["time"] >= train_start_ts)
                & (factor_flat["time"] <= train_end_ts)
            ]
            fv_oos = factor_flat[
                (factor_flat["time"] >= val_start_ts)
                & (factor_flat["time"] <= val_end_ts)
            ]
            ret_is = inputs.forward_returns_flat[
                (inputs.forward_returns_flat["time"] >= train_start_ts)
                & (inputs.forward_returns_flat["time"] <= train_end_ts)
            ]
            ret_oos = inputs.forward_returns_flat[
                (inputs.forward_returns_flat["time"] >= val_start_ts)
                & (inputs.forward_returns_flat["time"] <= val_end_ts)
            ]

            # daily_ics_by_horizon: {1: ic_series_train} — we only have h=1
            daily_ics_by_horizon = {1: ic_series_train}

            # lib_corr_profile from redundancy
            lib_corr_profile = redundancy.get("all_correlations") or {}

            rc = compute_report_card(
                daily_ics_is=ic_series_train,
                daily_ics_oos=ic_series_val,
                factor_vals_is=fv_is.set_index(["time", "symbol"])["value"].to_frame(),
                factor_vals_oos=fv_oos.set_index(["time", "symbol"])["value"].to_frame(),
                returns_is=ret_is.set_index(["time", "symbol"])["value"].to_frame(),
                returns_oos=ret_oos.set_index(["time", "symbol"])["value"].to_frame(),
                daily_ics_by_horizon=daily_ics_by_horizon,
                lib_values={},  # loaded separately if needed
                lib_corr_profile=lib_corr_profile,
                stage2_info={"max_corr": redundancy.get("max_lib_corr", 0.0),
                             "max_corr_factor": redundancy.get("nearest_factor_id")},
                expression_depth=cand.expression.count("("),
            )
            report_card = rc.to_dict()
        except Exception as rc_exc:
            logger.warning("report_card failed for %s: %s", cand.candidate_id, rc_exc)
            report_card = None

        return {
            "candidate_id": cand.candidate_id,
            "expression": cand.expression,
            "source_type": cand.source_type,
            "coverage": round(coverage, 4),
            "sign": int(primary_sign),
            "report_card": report_card,
            "effect_strength": es,
            "quintile": {
                "quintile_returns_validation": qret["quintile_returns"],
                "monotonicity_validation": qret["monotonicity"],
                "long_short_mean_validation": qret["long_short_mean"],
                "long_short_n_days": qret["long_short_n_days"],
            },
            "stability": {
                "split_stability": split,
                "support_windows": support,
                "sign_consistency_train_validation": sign_ok,
                "train_validation_decay": None
                if pd.isna(decay)
                else round(float(decay), 4),
            },
            "redundancy": redundancy,
            "feasibility": {
                "turnover_mean": turnover_mean,
                "liquidity_coverage": lcr,
                "tail_concentration": tail,
                "small_cap_concentration": small_cap,
                "half_life": half_life,
                "holding_period": holding,
                "rebalance_stress": stress,
            },
            "barra": barra,
            # §7.MT populated in Phase 3 pre-pack, not here
            "multiple_testing_risk_bucket": None,
            "compute_error": None,
        }
    except Exception as exc:  # noqa: BLE001 — intentional catch-all
        logger.exception(
            "phase2: candidate %s failed: %s", cand.candidate_id, exc
        )
        return {
            "candidate_id": cand.candidate_id,
            "expression": cand.expression,
            "source_type": cand.source_type,
            "compute_error": f"{type(exc).__name__}: {exc}",
        }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_phase2(inputs: Phase2Inputs, output_path: str | Path) -> dict[str, Any]:
    """Run Phase 2 on all candidates in *inputs* and write ``result.yaml``.

    Returns the ``result`` dict that was written (useful for in-process
    testing; production callers go through the file).
    """
    results: list[dict[str, Any]] = []
    for cand in inputs.candidates:
        results.append(_evaluate_candidate(cand, inputs))

    n_ok = sum(1 for r in results if r.get("compute_error") is None)
    n_err = len(results) - n_ok

    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "batch_id": inputs.batch_id,
        "generated_at": _now_iso(),
        "sample_policy_version": inputs.sample_policy_version,
        "preprocess_version": inputs.preprocess_version,
        "train_range": list(inputs.train_range),
        "validation_range": list(inputs.validation_range),
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
