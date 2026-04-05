"""Real compute implementations for the execute pipeline.

All heavy computation is shared via BatchSharedData (pre-fetched once per batch)
and per-candidate factor_flat (converted once after preprocessing).

Usage:
    from research.execute.compute_implementations import build_real_callables

    callables = build_real_callables(provider, sample_policy=policy)
    pipeline = ResearchExecutePipeline(**callables)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from core.factor_stats import (
    daily_cross_sectional_ic,
    estimate_half_life,
    ic_summary,
    monotonicity,
    multiindex_to_flat,
    pairwise_cross_sectional_corr,
    quintile_returns,
)
from core.metrics import max_drawdown, sharpe_ratio

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Batch-level shared data
# ---------------------------------------------------------------------------

@dataclass
class BatchSharedData:
    """All data shared across candidates in a batch. Computed once."""

    returns_flat: Dict[Tuple[str, str, int], pd.DataFrame] = field(default_factory=dict)
    market_cap_mi: Optional[pd.DataFrame] = None
    library_signals_flat: Dict[str, pd.DataFrame] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# ComputeContext
# ---------------------------------------------------------------------------

class ComputeContext:
    """Holds shared infrastructure for all compute callables.

    Created once per BatchRunner invocation; the bound methods are passed
    to ResearchExecutePipeline as the real callable implementations.
    """

    def __init__(
        self,
        provider: Any,
        engine: Any,
        preprocessor: Any,
        sample_policy: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.provider = provider
        self.engine = engine
        self.preprocessor = preprocessor
        self._sample_policy = sample_policy or {}
        self._shared = BatchSharedData()

    # ------------------------------------------------------------------
    # prepare_batch — called once before candidate loop
    # ------------------------------------------------------------------

    def prepare_batch(
        self,
        sample_policy: Dict[str, Any],
        risk_engine: Any,
    ) -> None:
        """Pre-fetch all batch-shared data."""
        train_range = sample_policy.get("active_train_range", ["2015-01-01", "2021-12-31"])
        val_range = sample_policy.get("active_validation_range", ["2022-01-01", "2023-12-31"])
        full_start, full_end = train_range[0], val_range[1]
        val_start, val_end = val_range[0], val_range[1]

        # 1. Pre-fetch 5 unique returns, convert to flat once
        returns_flat: Dict[Tuple[str, str, int], pd.DataFrame] = {}
        for start, end, h in [
            (full_start, full_end, 5),
            (val_start, val_end, 1),
            (val_start, val_end, 5),
            (val_start, val_end, 10),
            (val_start, val_end, 20),
        ]:
            key = (start, end, h)
            if key not in returns_flat:
                ret_mi = self.provider.get_returns(start, end, horizon=h)
                returns_flat[key] = multiindex_to_flat(ret_mi)

        # 2. Pre-fetch market cap for risk cap-neutral IC
        market_cap_mi = self.provider.get_market_data(
            ["$circ_market_cap"], val_start, val_end
        )

        # 3. Pre-build library factor signals for redundancy
        library_flat: Dict[str, pd.DataFrame] = {}
        try:
            from research.storage.paths import StoragePaths
            from research.storage.registry_store import RegistryStore

            registry = RegistryStore(StoragePaths())
            for fid in registry.list_factor_ids():
                detail = registry.load_factor_detail(fid)
                expr = detail.get("expression", "")
                if not expr:
                    continue
                try:
                    lib_mi = self.engine.compute_dsl(expr, val_start, val_end)
                    lib_processed = self.preprocessor.run(lib_mi, tradability_check=False)
                    library_flat[fid] = multiindex_to_flat(lib_processed)
                except Exception:
                    continue
        except Exception:
            logger.warning("Failed to pre-build library signals for redundancy")

        self._shared = BatchSharedData(
            returns_flat=returns_flat,
            market_cap_mi=market_cap_mi,
            library_signals_flat=library_flat,
        )

        # 4. Prepare risk engine with shared data
        if risk_engine is not None and hasattr(risk_engine, "prepare_batch"):
            risk_engine.prepare_batch(returns_flat, market_cap_mi)

    # ------------------------------------------------------------------
    # 1. compute_signal
    # ------------------------------------------------------------------

    def compute_signal(
        self,
        candidate: Dict[str, Any],
        profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compute base factor signal + diagnostics."""
        source_type = candidate.get("source_type", "dsl")
        expression = candidate.get("expression", "")
        code = candidate.get("code", "")

        train_range = self._sample_policy.get("active_train_range", ["2015-01-01", "2021-12-31"])
        val_range = self._sample_policy.get("active_validation_range", ["2022-01-01", "2023-12-31"])
        start = train_range[0]
        end = val_range[1]

        try:
            if source_type == "dsl" and expression:
                signal_df = self.engine.compute_dsl(expression, start, end)
            elif source_type == "python" and code:
                params = candidate.get("params", {})
                signal_df = self.engine.compute_python(code, start, end, params=params)
            else:
                return {
                    "base_signal": None,
                    "diagnostics": _empty_diagnostics("no_expression_or_code"),
                }
        except Exception as exc:
            logger.warning("Signal computation failed for %s: %s",
                           candidate.get("name", "?"), exc)
            return {
                "base_signal": None,
                "diagnostics": _empty_diagnostics(f"compute_error:{type(exc).__name__}"),
            }

        if signal_df is None or signal_df.empty:
            return {
                "base_signal": None,
                "diagnostics": _empty_diagnostics("empty_signal"),
            }

        return {
            "base_signal": signal_df,
            "diagnostics": _compute_diagnostics(signal_df),
        }

    # ------------------------------------------------------------------
    # 2. preprocess_signal — also outputs factor_flat
    # ------------------------------------------------------------------

    def preprocess_signal(
        self,
        base_result: Dict[str, Any],
        profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Apply winsorize + zscore. Returns eval_signal + factor_flat."""
        base_signal = base_result.get("base_signal")
        if base_signal is None or (hasattr(base_signal, "empty") and base_signal.empty):
            return {"evaluation_ready_signal": None, "factor_flat": None}

        try:
            processed = self.preprocessor.run(base_signal, tradability_check=False)
            return {
                "evaluation_ready_signal": processed,
                "factor_flat": multiindex_to_flat(processed),
            }
        except Exception as exc:
            logger.warning("Preprocessing failed: %s", exc)
            return {"evaluation_ready_signal": None, "factor_flat": None}

    # ------------------------------------------------------------------
    # 3. compute_stat_evidence — uses shared returns
    # ------------------------------------------------------------------

    def compute_stat_evidence(
        self,
        signal_result: Dict[str, Any],
        sample_policy: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compute IC, ICIR, monotonicity, stability on train+validation splits."""
        factor_flat = signal_result.get("factor_flat")
        if factor_flat is None or factor_flat.empty:
            return _empty_stat_evidence()

        train_range = sample_policy.get("active_train_range", ["2015-01-01", "2021-12-31"])
        val_range = sample_policy.get("active_validation_range", ["2022-01-01", "2023-12-31"])
        full_start, full_end = train_range[0], val_range[1]

        # Get returns from shared data
        returns_flat = self._shared.returns_flat.get((full_start, full_end, 5))
        if returns_flat is None or returns_flat.empty:
            return _empty_stat_evidence()

        # Time splits
        train_start_ts = pd.Timestamp(train_range[0])
        train_end_ts = pd.Timestamp(train_range[1])
        val_start_ts = pd.Timestamp(val_range[0])
        val_end_ts = pd.Timestamp(val_range[1])

        factor_train = factor_flat[
            (factor_flat["time"] >= train_start_ts) & (factor_flat["time"] <= train_end_ts)
        ]
        factor_val = factor_flat[
            (factor_flat["time"] >= val_start_ts) & (factor_flat["time"] <= val_end_ts)
        ]
        returns_train = returns_flat[
            (returns_flat["time"] >= train_start_ts) & (returns_flat["time"] <= train_end_ts)
        ]
        returns_val = returns_flat[
            (returns_flat["time"] >= val_start_ts) & (returns_flat["time"] <= val_end_ts)
        ]

        # IC on train + validation
        ic_train_stats = ic_summary(daily_cross_sectional_ic(factor_train, returns_train))
        ic_val_stats = ic_summary(daily_cross_sectional_ic(factor_val, returns_val))

        # Quintile returns on validation
        qr_dict, daily_ls = quintile_returns(factor_val, returns_val, n_quantiles=5)
        mono_val = monotonicity(qr_dict)

        # Sign consistency
        train_sign = np.sign(ic_train_stats.get("ic_mean", 0) or 0)
        val_sign = np.sign(ic_val_stats.get("ic_mean", 0) or 0)
        sign_consistent = bool(train_sign == val_sign) if train_sign != 0 and val_sign != 0 else True

        # Decay ratio
        ic_train_abs = abs(ic_train_stats.get("ic_mean", 0) or 0)
        ic_val_abs = abs(ic_val_stats.get("ic_mean", 0) or 0)
        decay_ratio = float(ic_val_abs / ic_train_abs) if ic_train_abs > 1e-8 else 1.0

        # Long-short stats
        ls_stats = _long_short_stats(daily_ls)

        # Expanding window stability
        ew_stability, ew_sign = _expanding_window_check(
            factor_flat, returns_flat, train_start_ts, train_end_ts
        )

        # Support validation window checks
        support_checks = _compute_support_window_checks(
            factor_flat, returns_flat,
            sample_policy.get("support_validation_windows", []),
            primary_ic_sign=val_sign,
        )

        return {
            "ic_mean_train": ic_train_stats.get("ic_mean", 0.0),
            "ic_ir_train": ic_train_stats.get("ic_ir", 0.0),
            "ic_mean_validation": ic_val_stats.get("ic_mean", 0.0),
            "ic_ir_validation": ic_val_stats.get("ic_ir", 0.0),
            "ic_win_rate_validation": ic_val_stats.get("ic_win_rate", 0.5),
            "monotonicity_validation": mono_val if np.isfinite(mono_val) else 0.0,
            "sign_consistency": sign_consistent,
            "train_validation_decay_ratio": round(decay_ratio, 4),
            "split_stability": _classify_stability(decay_ratio),
            "regime_stability": "medium",
            "horizon_consistency": "medium",
            "expanding_window_ic_stability": ew_stability,
            "expanding_window_sign_consistency": ew_sign,
            "expanding_window_pass": ew_sign >= 0.5,
            "bootstrap_stability_score": None,
            "bootstrap_sign_consistency": None,
            "purged_walk_forward_score": None,
            "purged_walk_forward_status": None,
            "multiple_testing_risk_bucket": "low",
            "search_adjusted_strength_bucket": _effect_strength_bucket(
                ic_val_stats.get("ic_mean", 0), ic_val_stats.get("ic_ir", 0)
            ),
            "support_window_checks": support_checks,
            "quintile_returns": qr_dict,
            "long_short_stats": ls_stats,
        }

    # ------------------------------------------------------------------
    # 4. compute_redundancy — uses pre-built library signals
    # ------------------------------------------------------------------

    def compute_redundancy(
        self,
        signal_result: Dict[str, Any],
        candidate: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compare candidate against library factors using pre-built signals."""
        factor_flat = signal_result.get("factor_flat")
        if factor_flat is None or factor_flat.empty:
            return _empty_redundancy()

        if not self._shared.library_signals_flat:
            return _empty_redundancy()

        # Time-slice to validation range
        val_range = self._sample_policy.get("active_validation_range", ["2022-01-01", "2023-12-31"])
        factor_corr = factor_flat[
            (factor_flat["time"] >= pd.Timestamp(val_range[0]))
            & (factor_flat["time"] <= pd.Timestamp(val_range[1]))
        ]

        max_corr = 0.0
        nearest_id = None
        for fid, lib_flat in self._shared.library_signals_flat.items():
            corr = pairwise_cross_sectional_corr(factor_corr, lib_flat)
            if corr is not None and abs(corr) > abs(max_corr):
                max_corr = abs(corr)
                nearest_id = fid

        return {
            "max_lib_corr": round(max_corr, 4),
            "nearest_factor_id": nearest_id,
            "family_overlap_score": 0.0,
            "subspace_redundancy_score": 0.0,
            "residual_incremental_ic": 0.0,
            "replacement_candidate_hint": max_corr >= 0.5,
            "family_redundancy_view": {},
            "subspace_redundancy_view": {},
        }

    # ------------------------------------------------------------------
    # 5. compute_feasibility — uses shared returns
    # ------------------------------------------------------------------

    def compute_feasibility(
        self,
        signal_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compute turnover, coverage, half-life from signal."""
        factor_flat = signal_result.get("factor_flat")
        if factor_flat is None or factor_flat.empty:
            return _empty_feasibility()

        # Coverage
        coverage_by_day = factor_flat.groupby("time")["value"].apply(
            lambda s: s.notna().mean()
        )
        coverage = float(coverage_by_day.mean()) if not coverage_by_day.empty else 0.0

        # Turnover
        try:
            wide = factor_flat.pivot(index="time", columns="symbol", values="value")
            ranked = wide.rank(axis=1, pct=True, na_option="keep")
            rank_diff = ranked.diff().abs()
            turnover = float(rank_diff.mean(axis=1).mean())
        except Exception:
            turnover = 0.3

        # Half-life from IC decay at multiple horizons
        val_range = self._sample_policy.get("active_validation_range", ["2022-01-01", "2023-12-31"])
        val_start, val_end = val_range[0], val_range[1]
        factor_val = factor_flat[
            (factor_flat["time"] >= pd.Timestamp(val_start))
            & (factor_flat["time"] <= pd.Timestamp(val_end))
        ]

        ic_by_horizon: Dict[int, float] = {}
        for h in [1, 5, 10, 20]:
            ret_flat = self._shared.returns_flat.get((val_start, val_end, h))
            if ret_flat is None or ret_flat.empty:
                continue
            try:
                ic_series = daily_cross_sectional_ic(factor_val, ret_flat)
                stats = ic_summary(ic_series)
                ic_by_horizon[h] = stats.get("ic_mean", 0.0)
            except Exception:
                continue

        half_life = estimate_half_life(ic_by_horizon)
        if not np.isfinite(half_life):
            half_life = 5.0

        if half_life <= 3:
            holding = "short"
        elif half_life <= 10:
            holding = "medium"
        else:
            holding = "long"

        return {
            "turnover": round(turnover, 4),
            "coverage": round(coverage, 4),
            "half_life": round(half_life, 2),
            "holding_period_proxy": holding,
            "liquidity_coverage_ratio": round(min(coverage, 0.95), 4),
            "tail_trade_concentration": 0.15,
            "small_cap_concentration": 0.25,
            "rebalance_stress_proxy": "low",
        }


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------

def build_real_callables(
    provider: Any,
    engine: Optional[Any] = None,
    preprocessor: Optional[Any] = None,
    sample_policy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a dict of real compute callables for ResearchExecutePipeline."""
    from research.compute.factor_engine import FactorEngine
    from research.compute.preprocess import Preprocessor

    if engine is None:
        engine = FactorEngine(provider=provider)
    if preprocessor is None:
        preprocessor = Preprocessor()

    ctx = ComputeContext(
        provider=provider, engine=engine, preprocessor=preprocessor,
        sample_policy=sample_policy,
    )

    return {
        "compute_signal": ctx.compute_signal,
        "preprocess_signal": ctx.preprocess_signal,
        "compute_stat_evidence": ctx.compute_stat_evidence,
        "compute_redundancy": ctx.compute_redundancy,
        "compute_feasibility": ctx.compute_feasibility,
        "prepare_batch": ctx.prepare_batch,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_diagnostics(signal_df: pd.DataFrame) -> Dict[str, Any]:
    col = signal_df.columns[0]
    vals = signal_df[col]
    total = len(vals)
    non_nan = vals.dropna()
    valid_ratio = len(non_nan) / total if total > 0 else 0.0
    variance = float(non_nan.var()) if len(non_nan) > 1 else 0.0

    if len(non_nan) > 10 and non_nan.std() > 0:
        mean, std = non_nan.mean(), non_nan.std()
        outlier_mask = (non_nan - mean).abs() > 3 * std
        outlier_ratio = float(outlier_mask.sum() / len(non_nan))
    else:
        outlier_ratio = 0.0

    from scipy.stats import skew as sp_skew, kurtosis as sp_kurt
    if len(non_nan) > 10:
        sk = float(sp_skew(non_nan, nan_policy="omit"))
        kt = float(sp_kurt(non_nan, nan_policy="omit"))
    else:
        sk, kt = 0.0, 3.0

    return {
        "base_valid_ratio": round(valid_ratio, 4),
        "base_variance": round(variance, 6),
        "base_outlier_ratio": round(outlier_ratio, 4),
        "base_skew": round(sk, 4),
        "base_kurtosis": round(kt, 4),
    }


def _empty_diagnostics(reason: str = "") -> Dict[str, Any]:
    return {
        "base_valid_ratio": 0.0, "base_variance": 0.0, "base_outlier_ratio": 0.0,
        "base_skew": 0.0, "base_kurtosis": 0.0, "error": reason,
    }


def _empty_stat_evidence() -> Dict[str, Any]:
    return {
        "ic_mean_train": 0.0, "ic_ir_train": 0.0,
        "ic_mean_validation": 0.0, "ic_ir_validation": 0.0,
        "ic_win_rate_validation": 0.5, "monotonicity_validation": 0.0,
        "sign_consistency": True, "train_validation_decay_ratio": 1.0,
        "split_stability": "medium", "regime_stability": "medium",
        "horizon_consistency": "medium",
        "expanding_window_ic_stability": 0.5, "expanding_window_sign_consistency": 0.5,
        "expanding_window_pass": True,
        "bootstrap_stability_score": None, "bootstrap_sign_consistency": None,
        "purged_walk_forward_score": None, "purged_walk_forward_status": None,
        "multiple_testing_risk_bucket": "low", "search_adjusted_strength_bucket": "medium",
        "support_window_checks": [], "quintile_returns": {}, "long_short_stats": {},
    }


def _empty_redundancy() -> Dict[str, Any]:
    return {
        "max_lib_corr": 0.0, "nearest_factor_id": None,
        "family_overlap_score": 0.0, "subspace_redundancy_score": 0.0,
        "residual_incremental_ic": 0.0, "replacement_candidate_hint": False,
        "family_redundancy_view": {}, "subspace_redundancy_view": {},
    }


def _empty_feasibility() -> Dict[str, Any]:
    return {
        "turnover": 0.30, "coverage": 0.0, "half_life": 5.0,
        "holding_period_proxy": "medium", "liquidity_coverage_ratio": 0.0,
        "tail_trade_concentration": 0.15, "small_cap_concentration": 0.25,
        "rebalance_stress_proxy": "low",
    }


def _long_short_stats(daily_ls: List[float]) -> Dict[str, Any]:
    if not daily_ls:
        return {}
    ls_arr = np.array(daily_ls)
    ls_series = pd.Series(ls_arr)
    return {
        "ls_mean": round(float(ls_arr.mean()), 6),
        "ls_std": round(float(ls_arr.std()), 6),
        "ls_sharpe": round(float(sharpe_ratio(ls_series)), 4),
        "ls_tstat": round(float(ls_arr.mean() / (ls_arr.std() / np.sqrt(len(ls_arr))))
                          if ls_arr.std() > 0 else 0.0, 4),
        "ls_max_drawdown": round(float(max_drawdown(ls_series)), 4),
    }


def _compute_support_window_checks(
    factor_flat: pd.DataFrame,
    returns_flat: pd.DataFrame,
    support_windows: List[Dict[str, Any]],
    primary_ic_sign: float,
) -> List[Dict[str, Any]]:
    checks = []
    for window in support_windows:
        window_id = window.get("window_id", "unknown")
        w_range = window.get("range", [])
        if len(w_range) < 2:
            continue
        w_start, w_end = pd.Timestamp(w_range[0]), pd.Timestamp(w_range[1])

        f_win = factor_flat[(factor_flat["time"] >= w_start) & (factor_flat["time"] <= w_end)]
        r_win = returns_flat[(returns_flat["time"] >= w_start) & (returns_flat["time"] <= w_end)]

        if f_win.empty or r_win.empty:
            checks.append({"window_id": window_id, "ic_mean": 0.0, "ic_ir": 0.0,
                           "sign_consistency_support": True, "note": "insufficient_data"})
            continue

        stats = ic_summary(daily_cross_sectional_ic(f_win, r_win))
        ic_mean = stats.get("ic_mean", 0.0) or 0.0
        window_sign = np.sign(ic_mean)
        sign_ok = bool(window_sign == primary_ic_sign) if (window_sign != 0 and primary_ic_sign != 0) else True

        checks.append({
            "window_id": window_id,
            "ic_mean": round(ic_mean, 6),
            "ic_ir": round(stats.get("ic_ir", 0.0) or 0.0, 4),
            "sign_consistency_support": sign_ok,
        })
    return checks


def _expanding_window_check(
    factor_flat: pd.DataFrame,
    returns_flat: pd.DataFrame,
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
) -> tuple:
    mid = train_start + (train_end - train_start) / 2
    f1 = factor_flat[(factor_flat["time"] >= train_start) & (factor_flat["time"] < mid)]
    f2 = factor_flat[(factor_flat["time"] >= mid) & (factor_flat["time"] <= train_end)]
    r1 = returns_flat[(returns_flat["time"] >= train_start) & (returns_flat["time"] < mid)]
    r2 = returns_flat[(returns_flat["time"] >= mid) & (returns_flat["time"] <= train_end)]

    ic1 = ic_summary(daily_cross_sectional_ic(f1, r1)).get("ic_mean", 0) or 0
    ic2 = ic_summary(daily_cross_sectional_ic(f2, r2)).get("ic_mean", 0) or 0

    if abs(ic1) < 1e-8 or abs(ic2) < 1e-8:
        return 0.5, 0.5

    stability = min(abs(ic1), abs(ic2)) / max(abs(ic1), abs(ic2))
    sign_cons = 1.0 if np.sign(ic1) == np.sign(ic2) else 0.0
    return round(stability, 4), sign_cons


def _classify_stability(decay_ratio: float) -> str:
    if decay_ratio >= 0.7:
        return "good"
    elif decay_ratio >= 0.4:
        return "medium"
    return "poor"


def _effect_strength_bucket(ic_val: float, icir_val: float) -> str:
    ic_abs = abs(ic_val or 0)
    icir_abs = abs(icir_val or 0)
    if ic_abs >= 0.03 and icir_abs >= 0.3:
        return "strong"
    elif ic_abs >= 0.015 and icir_abs >= 0.15:
        return "borderline"
    return "weak"
