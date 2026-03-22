"""Multi-stage factor mining evaluation pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from .config import MiningConfig
from .expression import ExpressionValidator

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """Result of a batch evaluation."""
    admitted: List[Dict[str, Any]] = field(default_factory=list)
    rejected: List[Dict[str, Any]] = field(default_factory=list)
    replacements: List[Dict[str, Any]] = field(default_factory=list)


class FactorMiningEvaluator:
    """Multi-stage factor mining evaluation pipeline using Qlib."""

    def __init__(self, config: MiningConfig):
        self.config = config
        self._factor_cache: Dict[str, pd.DataFrame] = {}
        self._ensure_qlib_initialized()

    def _ensure_qlib_initialized(self) -> None:
        """Initialize Qlib idempotently."""
        try:
            import qlib
            if not getattr(qlib, "_is_initialized", False):
                qlib.init(provider_uri=self.config.qlib_data_dir)
        except Exception as e:
            logger.warning("Qlib init failed: %s", e)

    def _compute_ic_from_frames(self, factor_values: pd.DataFrame, returns: pd.DataFrame) -> Dict[str, Any]:
        """Compute daily cross-sectional Spearman IC.
        Both DataFrames must have (datetime, instrument) MultiIndex.
        """
        factor_col = factor_values.columns[0]
        returns_col = returns.columns[0]
        merged = factor_values.join(returns, how="inner").dropna()
        if merged.empty:
            return {"ic_mean": np.nan, "ic_std": np.nan, "ic_ir": np.nan, "ic_win_rate": np.nan, "n_days": 0}
        daily_ics = []
        for dt, group in merged.groupby(level="datetime"):
            if len(group) < 3:
                continue
            if group[factor_col].nunique() < 2 or group[returns_col].nunique() < 2:
                continue
            ic, _ = spearmanr(group[factor_col], group[returns_col])
            if not np.isnan(ic):
                daily_ics.append(float(ic))
        if not daily_ics:
            return {"ic_mean": np.nan, "ic_std": np.nan, "ic_ir": np.nan, "ic_win_rate": np.nan, "n_days": 0}
        ic_arr = np.array(daily_ics)
        ic_mean = float(ic_arr.mean())
        ic_std = float(ic_arr.std()) if len(ic_arr) > 1 else np.nan
        ic_ir = float(ic_mean / ic_std) if ic_std and ic_std != 0 else np.nan
        ic_win_rate = float((ic_arr > 0).sum() / len(ic_arr))
        return {"ic_mean": ic_mean, "ic_std": ic_std, "ic_ir": ic_ir, "ic_win_rate": ic_win_rate, "n_days": len(ic_arr)}

    def _compute_factor_qlib(self, expression: str, instruments: list, start_time: str, end_time: str) -> pd.DataFrame:
        """Use Qlib expression engine to compute factor values."""
        from qlib.data import D
        return D.features(instruments=instruments, fields=[expression], start_time=start_time, end_time=end_time)

    def _get_returns_qlib(self, instruments: list, start_time: str, end_time: str) -> pd.DataFrame:
        """Load pre-computed forward returns from Qlib."""
        from qlib.data import D
        return D.features(instruments=instruments, fields=["$returns_1d"], start_time=start_time, end_time=end_time)

    def _pairwise_correlation(self, a: pd.DataFrame, b: pd.DataFrame) -> float:
        """Compute time-averaged cross-sectional Spearman correlation."""
        a_col, b_col = a.columns[0], b.columns[0]
        merged = a.join(b, how="inner", lsuffix="_a", rsuffix="_b").dropna()
        if merged.empty:
            return 0.0
        corrs = []
        col_a, col_b = merged.columns[0], merged.columns[1]
        for dt, group in merged.groupby(level="datetime"):
            if len(group) < 3:
                continue
            rho, _ = spearmanr(group[col_a], group[col_b])
            if not np.isnan(rho):
                corrs.append(rho)
        return float(np.mean(corrs)) if corrs else 0.0

    def _get_fast_screening_universe(self) -> list:
        """Select top-N stocks by average daily turnover from configured universe."""
        if self.config.custom_universe:
            universe = self.config.custom_universe
        else:
            from qlib.data import D
            universe = list(D.instruments(self.config.universe))
        if len(universe) > self.config.fast_screening_universe_size:
            return universe[:self.config.fast_screening_universe_size]
        return universe

    def _get_full_universe(self) -> list:
        if self.config.custom_universe:
            return self.config.custom_universe
        from qlib.data import D
        return list(D.instruments(self.config.universe))

    def _fast_ic_screening(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Stage 1: Calculate IC on fast-screening subset universe."""
        subset = self._get_fast_screening_universe()
        results = []
        for c in candidates:
            try:
                values = self._compute_factor_qlib(c["expression"], subset, self.config.train_start, self.config.train_end)
                returns = self._get_returns_qlib(subset, self.config.train_start, self.config.train_end)
                ic_stats = self._compute_ic_from_frames(values, returns)
                c["stage1"] = ic_stats
                if abs(ic_stats.get("ic_mean", 0)) >= self.config.ic_threshold:
                    results.append(c)
                else:
                    logger.info("Stage 1 reject %s: IC=%.4f", c["name"], ic_stats.get("ic_mean", 0))
            except Exception as e:
                c["stage1"] = {"error": str(e)}
                logger.warning("Stage 1 error for %s: %s", c.get("name"), e)
        return results

    def _batch_dedup(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Stage 1.5: Remove intra-batch duplicates. Keep higher-IC factor."""
        if len(candidates) <= 1:
            return list(candidates)
        subset = self._get_fast_screening_universe()
        values_map: Dict[str, pd.DataFrame] = {}
        for c in candidates:
            try:
                vals = self._compute_factor_qlib(c["expression"], subset, self.config.train_start, self.config.train_end)
                values_map[c["expression"]] = vals
            except Exception:
                values_map[c["expression"]] = pd.DataFrame()
        sorted_candidates = sorted(candidates, key=lambda c: abs(c.get("stage1", {}).get("ic_mean", 0)), reverse=True)
        kept = []
        for c in sorted_candidates:
            c_vals = values_map.get(c["expression"])
            if c_vals is None or c_vals.empty:
                kept.append(c)
                continue
            is_dup = False
            for k in kept:
                k_vals = values_map.get(k["expression"])
                if k_vals is None or k_vals.empty:
                    continue
                corr = self._pairwise_correlation(c_vals, k_vals)
                if abs(corr) >= self.config.correlation_threshold:
                    is_dup = True
                    logger.info("Dedup: %s removed (corr=%.3f with %s)", c["name"], corr, k["name"])
                    break
            if not is_dup:
                kept.append(c)
        return kept

    def _load_library(self):
        from .library import FactorLibrary
        return FactorLibrary(self.config)

    def _correlation_check(self, candidates: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Stage 2: Full universe computation + correlation check with library."""
        library = self._load_library()
        lib_factors = library.list_factors()
        full_universe = self._get_full_universe()
        passed, rejected = [], []
        lib_values: Dict[str, pd.DataFrame] = {}
        for lf in lib_factors:
            try:
                vals = self._compute_factor_qlib(lf["expression"], full_universe, self.config.train_start, self.config.train_end)
                lib_values[lf["id"]] = vals
            except Exception as e:
                logger.warning("Failed to compute library factor %s: %s", lf["id"], e)
        for c in candidates:
            try:
                factor_vals = self._compute_factor_qlib(c["expression"], full_universe, self.config.train_start, self.config.train_end)
                self._factor_cache[c["expression"]] = factor_vals
                returns = self._get_returns_qlib(full_universe, self.config.train_start, self.config.train_end)
                full_ic = self._compute_ic_from_frames(factor_vals, returns)
                c["full_ic"] = full_ic
                max_corr, max_corr_factor = 0.0, None
                all_corrs: Dict[str, float] = {}
                for lid, lvals in lib_values.items():
                    corr = abs(self._pairwise_correlation(factor_vals, lvals))
                    all_corrs[lid] = corr
                    if corr > max_corr:
                        max_corr, max_corr_factor = corr, lid
                c["_lib_correlations"] = all_corrs
                if max_corr < self.config.correlation_threshold:
                    c["stage2"] = {"max_corr": max_corr, "max_corr_factor": max_corr_factor, "passed": True}
                    passed.append(c)
                else:
                    c["stage2"] = {"max_corr": max_corr, "max_corr_factor": max_corr_factor, "passed": False}
                    rejected.append(c)
            except Exception as e:
                c["stage2"] = {"error": str(e), "passed": False}
                rejected.append(c)
        return passed, rejected

    def _replacement_check(self, rejected: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Stage 2.5: Check if rejected factors can replace weaker library members."""
        replacements = []
        for c in rejected:
            full_ic = abs(c.get("full_ic", {}).get("ic_mean", 0))
            if full_ic < self.config.replacement_ic_min:
                continue
            g_star = c.get("stage2", {}).get("max_corr_factor")
            if g_star is None:
                continue
            g_ic = abs(self._get_library_factor_ic(g_star) or 0)
            conflicts = self._count_library_conflicts(c)
            if full_ic >= self.config.replacement_ic_ratio * abs(g_ic) and conflicts == 1:
                replacements.append({"new_factor": c, "replaces": g_star})
        return replacements

    def _get_library_factor_ic(self, factor_id: str) -> Optional[float]:
        library = self._load_library()
        return library.get_factor_ic(factor_id)

    def _count_library_conflicts(self, candidate: Dict[str, Any]) -> int:
        corrs = candidate.get("_lib_correlations", {})
        return sum(1 for v in corrs.values() if v >= self.config.correlation_threshold)

    def _full_validation(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Stage 3: Full validation with IS/OOS metrics. Reuses cached factor values."""
        full_universe = self._get_full_universe()
        validated = []
        for c in candidates:
            try:
                cached_vals = self._factor_cache.get(c["expression"])
                returns_is = self._get_returns_qlib(full_universe, self.config.train_start, self.config.train_end)
                if cached_vals is not None:
                    ic_is = self._compute_ic_from_frames(cached_vals, returns_is)
                else:
                    vals_is = self._compute_factor_qlib(c["expression"], full_universe, self.config.train_start, self.config.train_end)
                    ic_is = self._compute_ic_from_frames(vals_is, returns_is)
                    cached_vals = vals_is
                test_end = self.config.test_end or str(pd.Timestamp.now().date())
                vals_oos = self._compute_factor_qlib(c["expression"], full_universe, self.config.test_start, test_end)
                returns_oos = self._get_returns_qlib(full_universe, self.config.test_start, test_end)
                ic_oos = self._compute_ic_from_frames(vals_oos, returns_oos)
                quantile_ret = self._compute_quantile_returns(cached_vals, returns_is)

                # Compute long-short return and monotonicity
                ls_return = np.nan
                monotonicity = np.nan
                if quantile_ret:
                    q_keys = sorted(quantile_ret.keys())
                    q_vals = [quantile_ret[k] for k in q_keys if not np.isnan(quantile_ret.get(k, np.nan))]
                    if len(q_vals) >= 2:
                        ls_return = float(q_vals[-1] - q_vals[0])
                        from scipy.stats import spearmanr as _sp
                        mono, _ = _sp(range(len(q_vals)), q_vals)
                        monotonicity = float(mono) if not np.isnan(mono) else np.nan

                c["stage3"] = {
                    "ic_mean_is": ic_is.get("ic_mean"),
                    "ic_ir_is": ic_is.get("ic_ir"),
                    "ic_mean_oos": ic_oos.get("ic_mean"),
                    "ic_ir_oos": ic_oos.get("ic_ir"),
                    "ic_win_rate": ic_is.get("ic_win_rate"),
                    "quantile_returns": quantile_ret,
                    "ls_return": ls_return,
                    "monotonicity": monotonicity,
                }
                validated.append(c)
            except Exception as e:
                c["stage3"] = {"error": str(e)}
                validated.append(c)
        return validated

    def _compute_quantile_returns(self, factor_values: pd.DataFrame, returns: pd.DataFrame, n_quantiles: int = 5) -> Dict[str, float]:
        factor_col = factor_values.columns[0]
        returns_col = returns.columns[0]
        merged = factor_values.join(returns, how="inner").dropna()
        if merged.empty:
            return {f"q{i+1}": np.nan for i in range(n_quantiles)}
        result = {}
        for dt, group in merged.groupby(level="datetime"):
            if len(group) < n_quantiles:
                continue
            group = group.copy()
            group["quantile"] = pd.qcut(group[factor_col], n_quantiles, labels=False, duplicates="drop")
            for q in range(n_quantiles):
                q_ret = group.loc[group["quantile"] == q, returns_col].mean()
                result.setdefault(f"q{q+1}", []).append(q_ret)
        return {k: float(np.nanmean(v)) if v else np.nan for k, v in result.items()}

    def evaluate_batch(self, candidates: List[Dict[str, Any]]) -> BatchResult:
        """Run multi-stage pipeline on a batch of candidate factors."""
        self._factor_cache.clear()
        validator = ExpressionValidator(self.config)
        valid, invalid = [], []
        for c in candidates:
            result = validator.validate(c["expression"])
            if result.valid:
                valid.append(c)
            else:
                c["validation_error"] = result.errors
                invalid.append(c)
        if not valid:
            return BatchResult(admitted=[], rejected=invalid, replacements=[])
        stage1_passed = self._fast_ic_screening(valid)
        stage1_deduped = self._batch_dedup(stage1_passed)
        stage2_passed, stage2_rejected = self._correlation_check(stage1_deduped)
        replacements = self._replacement_check(stage2_rejected)
        validated = self._full_validation(stage2_passed)
        all_rejected = invalid + [c for c in valid if c not in stage1_passed]
        all_rejected += [c for c in stage1_passed if c not in stage1_deduped]
        all_rejected += stage2_rejected
        return BatchResult(admitted=validated, rejected=all_rejected, replacements=replacements)
