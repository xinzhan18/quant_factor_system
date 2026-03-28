"""Multi-stage factor mining evaluation pipeline."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from core.metrics import ic_summary_from_series
from .config import MiningConfig
from .expression import ExpressionValidator
from .metrics import FactorReportCard, compute_report_card
from .operators import register_custom_operators
from .preprocessing import FactorPreprocessor

logger = logging.getLogger(__name__)

# Optional Qlib import — patched in tests via `mining.evaluator.D`
try:
    from qlib.data import D
except ImportError:
    D = None  # type: ignore[assignment]


def _clean_factor_dict(c: Dict[str, Any]) -> Dict[str, Any]:
    """Extract only serializable fields from a factor dict (whitelist approach)."""
    ALLOWED_KEYS = {
        "name", "expression", "category", "rationale", "batch",
        "stage1", "stage2", "stage3", "full_ic", "report_card",
        "validation_error", "reject_reason",
    }
    return {k: v for k, v in c.items() if k in ALLOWED_KEYS}


@dataclass
class BatchResult:
    """Result of a batch evaluation.

    ``screened`` contains factors that passed Stage 1-2 hard filters and have
    a full 6-dimension FactorReportCard.  They are *not* automatically admitted
    — the LLM in the Ralph Loop skill reviews them and decides.

    ``admitted`` is an alias kept for backward compatibility (same list).
    """
    screened: List[Dict[str, Any]] = field(default_factory=list)
    rejected: List[Dict[str, Any]] = field(default_factory=list)
    replacements: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def admitted(self) -> List[Dict[str, Any]]:
        """Backward-compatible alias for screened."""
        return self.screened

    def to_dict(self) -> Dict[str, Any]:
        """Return a clean, serializable dict for YAML/JSON export."""
        clean_replacements = []
        for r in self.replacements:
            if isinstance(r, dict) and "new_factor" in r:
                clean_replacements.append({
                    "new_factor": _clean_factor_dict(r["new_factor"]),
                    "replaces": r.get("replaces"),
                })
            else:
                clean_replacements.append(_clean_factor_dict(r))
        return {
            "screened": [_clean_factor_dict(c) for c in self.screened],
            "rejected": [_clean_factor_dict(c) for c in self.rejected],
            "replacements": clean_replacements,
        }


class FactorMiningEvaluator:
    """Multi-stage factor mining evaluation pipeline using Qlib."""

    def __init__(self, config: MiningConfig):
        self.config = config
        self._factor_cache: Dict[str, pd.DataFrame] = {}
        self._subset_factor_cache: Dict[str, pd.DataFrame] = {}
        self._lib_values_cache: Dict[str, pd.DataFrame] = {}
        self._preprocessor = FactorPreprocessor(config)
        self._aux_cache: Dict[str, Dict[str, pd.DataFrame]] = {}
        self._ensure_qlib_initialized()
        try:
            register_custom_operators()
            from qlib.config import C
            C.kernels = 1
        except Exception as e:
            logger.warning("Failed to register custom operators: %s", e)

    def _ensure_qlib_initialized(self) -> None:
        try:
            import qlib
            if not getattr(qlib, "_is_initialized", False):
                qlib.init(provider_uri=self.config.qlib_data_dir)
        except ImportError:
            logger.error(
                "Qlib is not installed. Install with: pip install qlib. "
                "The evaluator will fail when computing factors."
            )
        except Exception as e:
            logger.error("Qlib init failed: %s", e)

    # ──────────────────── Data Loading ────────────────────

    def _load_aux_data(self, instruments: list, start_time: str, end_time: str) -> Dict[str, pd.DataFrame]:
        inst_hash = hashlib.md5(",".join(sorted(instruments)).encode()).hexdigest()[:12]
        cache_key = f"{inst_hash}_{start_time}_{end_time}"
        if cache_key in self._aux_cache:
            return self._aux_cache[cache_key]
        aux: Dict[str, pd.DataFrame] = {}
        try:
            core_df = D.features(instruments=instruments, fields=["$volume", "$close"],
                                 start_time=start_time, end_time=end_time)
            for col in core_df.columns:
                aux[col.replace("$", "")] = core_df[[col]]
        except Exception as e:
            logger.warning("Failed to load core aux data: %s", e)
        try:
            limit_df = D.features(instruments=instruments, fields=["$limit_up", "$limit_down"],
                                  start_time=start_time, end_time=end_time)
            for col in limit_df.columns:
                aux[col.replace("$", "")] = limit_df[[col]]
        except Exception:
            logger.debug("limit_up/limit_down not available")
        if self.config.neutralize_mode != "none":
            try:
                mcap_df = D.features(instruments=instruments, fields=["$market_cap"],
                                     start_time=start_time, end_time=end_time)
                aux["market_cap"] = mcap_df[["$market_cap"]]
            except Exception:
                logger.debug("market_cap not available for neutralization")
        self._aux_cache[cache_key] = aux
        return aux

    def _compute_factor_qlib(self, expression: str, instruments: list,
                              start_time: str, end_time: str) -> pd.DataFrame:
        from qlib.data import D
        return D.features(instruments=instruments, fields=[expression],
                          start_time=start_time, end_time=end_time)

    def _get_returns_qlib(self, instruments: list, start_time: str,
                           end_time: str) -> pd.DataFrame:
        from qlib.data import D
        return D.features(instruments=instruments, fields=["$returns_1d"],
                          start_time=start_time, end_time=end_time)

    # ──────────────────── IC Computation ────────────────────

    def _compute_daily_ics(
        self, factor_values: pd.DataFrame, returns: pd.DataFrame,
        aux_data: Optional[Dict[str, pd.DataFrame]] = None,
    ) -> pd.Series:
        """Compute daily cross-sectional Spearman IC.

        Returns a pd.Series with DatetimeIndex for easy groupby year/month/quarter.
        """
        if aux_data:
            factor_values, returns = self._preprocessor.preprocess_for_ic(
                factor=factor_values, returns=returns, **aux_data,
            )
        factor_col = factor_values.columns[0]
        returns_col = returns.columns[0]
        merged = factor_values.join(returns, how="inner").dropna()
        if merged.empty:
            return pd.Series(dtype=float)
        records = []
        for dt, group in merged.groupby(level="datetime"):
            if len(group) < 3:
                continue
            if group[factor_col].nunique() < 2 or group[returns_col].nunique() < 2:
                continue
            ic, _ = spearmanr(group[factor_col], group[returns_col])
            if not np.isnan(ic):
                records.append((dt, float(ic)))
        if not records:
            return pd.Series(dtype=float)
        dates, ics = zip(*records)
        return pd.Series(ics, index=pd.DatetimeIndex(dates), dtype=float)

    def _compute_ic_from_frames(
        self, factor_values: pd.DataFrame, returns: pd.DataFrame,
        aux_data: Optional[Dict[str, pd.DataFrame]] = None,
    ) -> Dict[str, Any]:
        """Compute IC summary stats. Backward-compatible wrapper around _compute_daily_ics."""
        daily_ics = self._compute_daily_ics(factor_values, returns, aux_data)
        if daily_ics.empty:
            return {"ic_mean": np.nan, "ic_std": np.nan, "ic_ir": np.nan,
                    "ic_win_rate": np.nan, "n_days": 0}
        summary = ic_summary_from_series(daily_ics)
        summary["n_days"] = len(daily_ics)
        return summary

    # ──────────────────── Correlation ────────────────────

    def _pairwise_correlation(self, a: pd.DataFrame, b: pd.DataFrame) -> float:
        a_col, b_col = a.columns[0], b.columns[0]
        merged = a.join(b, how="inner", lsuffix="_a", rsuffix="_b").dropna()
        if merged.empty:
            return 0.0
        if a_col == b_col:
            col_a, col_b = f"{a_col}_a", f"{b_col}_b"
        else:
            col_a, col_b = a_col, b_col
        corrs = []
        for _, group in merged.groupby(level="datetime"):
            if len(group) < 3:
                continue
            rho, _ = spearmanr(group[col_a], group[col_b])
            if not np.isnan(rho):
                corrs.append(rho)
        return float(np.mean(corrs)) if corrs else 0.0

    # ──────────────────── Universe ────────────────────

    def _resolve_universe(self):
        if self.config.custom_universe:
            return self.config.custom_universe
        from qlib.data import D
        return D.instruments(self.config.universe)

    def _get_fast_screening_universe(self) -> list:
        universe = self._resolve_universe()
        try:
            from qlib.data import D
            vol_data = D.features(instruments=universe, fields=["$volume"],
                                  start_time=self.config.train_start,
                                  end_time=self.config.train_end)
            avg_vol = vol_data.groupby(level="instrument").mean().squeeze()
            return avg_vol.nlargest(self.config.fast_screening_universe_size).index.tolist()
        except Exception as e:
            logger.warning("Failed to sort universe by liquidity: %s", e)
            return self._get_full_universe()[:self.config.fast_screening_universe_size]

    def _get_full_universe(self) -> list:
        universe = self._resolve_universe()
        if isinstance(universe, list):
            return universe
        from qlib.data import D
        vol_data = D.features(instruments=universe, fields=["$volume"],
                              start_time=self.config.train_start,
                              end_time=self.config.train_end)
        return vol_data.index.get_level_values("instrument").unique().tolist()

    # ──────────────────── Stage 1: Fast IC Screening ────────────────────

    def _fast_ic_screening(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        subset = self._get_fast_screening_universe()
        returns = self._get_returns_qlib(subset, self.config.train_start, self.config.train_end)
        aux = self._load_aux_data(subset, self.config.train_start, self.config.train_end)
        results = []
        for c in candidates:
            try:
                values = self._compute_factor_qlib(c["expression"], subset,
                                                    self.config.train_start, self.config.train_end)
                self._subset_factor_cache[c["expression"]] = values
                ic_stats = self._compute_ic_from_frames(values, returns, aux_data=aux)
                c["stage1"] = ic_stats
                if abs(ic_stats.get("ic_mean", 0)) >= self.config.ic_threshold:
                    results.append(c)
                else:
                    logger.info("Stage 1 reject %s: IC=%.4f", c["name"], ic_stats.get("ic_mean", 0))
            except Exception as e:
                c["stage1"] = {"error": str(e)}
                logger.warning("Stage 1 error for %s: %s", c.get("name"), e)
        return results

    # ──────────────────── Stage 1.5: Batch Dedup ────────────────────

    def _batch_dedup(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(candidates) <= 1:
            return list(candidates)
        values_map: Dict[str, pd.DataFrame] = {}
        for c in candidates:
            cached = self._subset_factor_cache.get(c["expression"])
            if cached is not None:
                values_map[c["expression"]] = cached
            else:
                try:
                    subset = self._get_fast_screening_universe()
                    vals = self._compute_factor_qlib(c["expression"], subset,
                                                      self.config.train_start, self.config.train_end)
                    values_map[c["expression"]] = vals
                except Exception:
                    values_map[c["expression"]] = pd.DataFrame()
        sorted_candidates = sorted(candidates,
                                    key=lambda c: abs(c.get("stage1", {}).get("ic_mean", 0)),
                                    reverse=True)
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

    # ──────────────────── Stage 2: Correlation Check ────────────────────

    def _load_library(self):
        from .library import FactorLibrary
        return FactorLibrary(self.config)

    def _load_lib_values_from_db(self, lib_factors: List[Dict[str, Any]],
                                full_universe: list) -> Dict[str, pd.DataFrame]:
        """Try to load library factor values from DB. Returns {factor_id: DataFrame}."""
        result = {}
        try:
            import psycopg2
            conn = psycopg2.connect(self.config.system.database.connection_string)
            with conn.cursor() as cur:
                for lf in lib_factors:
                    factor_name = f"factor_{lf['id']}"
                    cur.execute(
                        "SELECT time, symbol, value FROM factor_values WHERE factor_name = %s",
                        (factor_name,),
                    )
                    rows = cur.fetchall()
                    if not rows:
                        continue
                    df = pd.DataFrame(rows, columns=["datetime", "instrument", factor_name])
                    df["datetime"] = pd.to_datetime(df["datetime"])
                    df = df.set_index(["datetime", "instrument"]).sort_index()
                    result[lf["id"]] = df
            conn.close()
        except Exception as e:
            logger.debug("Could not load library factors from DB: %s", e)
        return result

    def _correlation_check(self, candidates: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        library = self._load_library()
        lib_factors = library.list_factors()
        full_universe = self._get_full_universe()
        passed, rejected = [], []

        # Try loading library factor values from DB first (fast path)
        lib_values = self._load_lib_values_from_db(lib_factors, full_universe)
        db_loaded = len(lib_values)

        # Fallback: compute missing library factors via Qlib
        for lf in lib_factors:
            if lf["id"] in lib_values:
                continue
            try:
                vals = self._compute_factor_qlib(lf["expression"], full_universe,
                                                  self.config.train_start, self.config.train_end)
                lib_values[lf["id"]] = vals
            except Exception as e:
                logger.warning("Failed to compute library factor %s: %s", lf["id"], e)

        if db_loaded:
            logger.info("Library factors: %d from DB, %d computed via Qlib",
                       db_loaded, len(lib_values) - db_loaded)
        # Cache for Stage 3 (incremental IC computation)
        self._lib_values_cache = lib_values
        returns = self._get_returns_qlib(full_universe, self.config.train_start, self.config.train_end)
        aux = self._load_aux_data(full_universe, self.config.train_start, self.config.train_end)
        for c in candidates:
            try:
                factor_vals = self._compute_factor_qlib(c["expression"], full_universe,
                                                         self.config.train_start, self.config.train_end)
                self._factor_cache[c["expression"]] = factor_vals
                full_ic = self._compute_ic_from_frames(factor_vals, returns, aux_data=aux)
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

    # ──────────────────── Stage 2.5: Replacement Check ────────────────────

    def _replacement_check(self, rejected: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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

    # ──────────────────── Stage 3: Report Card Computation ────────────────────

    @staticmethod
    def _max_expression_depth(expression: str) -> int:
        max_d = current = 0
        for ch in expression:
            if ch == "(":
                current += 1
                max_d = max(max_d, current)
            elif ch == ")":
                current -= 1
        return max_d

    def _compute_report_cards(self, candidates: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Stage 3: Compute 6-dimension FactorReportCard for each candidate.

        Returns (screened, errors).  All screened factors have a ``report_card``
        dict attached.  No admission decision is made here — the LLM in the
        Ralph Loop skill reviews the report cards and decides.
        """
        full_universe = self._get_full_universe()
        test_end = self.config.test_end or str(pd.Timestamp.now().date())

        # Shared data (loaded once)
        aux_is = self._load_aux_data(full_universe, self.config.train_start, self.config.train_end)
        aux_oos = self._load_aux_data(full_universe, self.config.test_start, test_end)
        returns_is = self._get_returns_qlib(full_universe, self.config.train_start, self.config.train_end)
        returns_oos = self._get_returns_qlib(full_universe, self.config.test_start, test_end)

        # Multi-horizon returns for IC decay
        returns_multi: Dict[int, pd.DataFrame] = {}
        for h in self.config.decay_horizons:
            if h == 1:
                returns_multi[h] = returns_is
            else:
                try:
                    expr = f"Ref($close, -{h}) / $close - 1"
                    returns_multi[h] = self._compute_factor_qlib(
                        expr, full_universe, self.config.train_start, self.config.train_end,
                    )
                except Exception as e:
                    logger.warning("Failed to compute %d-day forward returns: %s", h, e)

        screened, errors = [], []
        for c in candidates:
            try:
                # IS factor values (from Stage 2 cache or fresh)
                factor_vals_is = self._factor_cache.get(c["expression"])
                if factor_vals_is is None:
                    factor_vals_is = self._compute_factor_qlib(
                        c["expression"], full_universe,
                        self.config.train_start, self.config.train_end,
                    )

                # OOS factor values
                factor_vals_oos = self._compute_factor_qlib(
                    c["expression"], full_universe, self.config.test_start, test_end,
                )

                # Daily IC series
                daily_ics_is = self._compute_daily_ics(factor_vals_is, returns_is, aux_data=aux_is)
                daily_ics_oos = self._compute_daily_ics(factor_vals_oos, returns_oos, aux_data=aux_oos)

                # Multi-horizon daily ICs for decay
                daily_ics_by_horizon: Dict[int, pd.Series] = {}
                for h, ret_h in returns_multi.items():
                    daily_ics_by_horizon[h] = self._compute_daily_ics(
                        factor_vals_is, ret_h, aux_data=aux_is,
                    )

                # Build report card
                rc = compute_report_card(
                    daily_ics_is=daily_ics_is,
                    daily_ics_oos=daily_ics_oos,
                    factor_vals_is=factor_vals_is,
                    factor_vals_oos=factor_vals_oos,
                    returns_is=returns_is,
                    returns_oos=returns_oos,
                    daily_ics_by_horizon=daily_ics_by_horizon,
                    lib_values=self._lib_values_cache,
                    lib_corr_profile=c.get("_lib_correlations", {}),
                    stage2_info=c.get("stage2", {}),
                    expression_depth=self._max_expression_depth(c["expression"]),
                )

                c["report_card"] = rc.to_dict()

                # Backward-compatible stage3 dict
                c["stage3"] = {
                    "ic_mean_is": rc.ic_mean,
                    "ic_ir_is": rc.ic_ir,
                    "ic_mean_oos": rc.ic_mean_oos,
                    "ic_ir_oos": rc.ic_ir_oos,
                    "ic_win_rate": rc.ic_win_rate,
                    "quantile_returns": rc.quantile_returns_is,
                    "ls_return": rc.ls_return,
                    "monotonicity": rc.monotonicity_is,
                }

                # Transient values for publisher (not saved to YAML)
                c["_factor_values"] = factor_vals_is
                c["_factor_values_oos"] = factor_vals_oos

                screened.append(c)
            except Exception as e:
                c["stage3"] = {"error": str(e)}
                c["report_card"] = {"error": str(e)}
                errors.append(c)
                logger.warning("Stage 3 error for %s: %s", c.get("name"), e)

        return screened, errors

    # Keep old name as alias for backward compatibility
    _full_validation = _compute_report_cards

    # ──────────────────── Quantile Returns (legacy) ────────────────────

    def _compute_quantile_returns(self, factor_values: pd.DataFrame,
                                   returns: pd.DataFrame,
                                   n_quantiles: int = 5) -> Dict[str, float]:
        """Legacy quantile returns (used by external callers if any)."""
        factor_col = factor_values.columns[0]
        returns_col = returns.columns[0]
        merged = factor_values.join(returns, how="inner").dropna()
        if merged.empty:
            return {f"q{i + 1}": np.nan for i in range(n_quantiles)}
        result = {}
        for _, group in merged.groupby(level="datetime"):
            if len(group) < n_quantiles:
                continue
            group = group.copy()
            group["quantile"] = pd.qcut(group[factor_col], n_quantiles,
                                         labels=False, duplicates="drop")
            for q in range(n_quantiles):
                q_ret = group.loc[group["quantile"] == q, returns_col].mean()
                result.setdefault(f"q{q + 1}", []).append(q_ret)
        return {k: float(np.nanmean(v)) if v else np.nan for k, v in result.items()}

    # ──────────────────── Probe: Lightweight Single-Expression IC ────────────────────

    def probe_single(self, expression: str, start: str = "2024-01-01",
                     end: str = "2024-12-31") -> dict:
        """Lightweight probe: compute IC for a single expression over full universe.

        Uses all stocks (no subset), specified date range, returns IC stats only.
        No correlation check, no report card.

        Args:
            expression: Qlib alpha expression string
            start: Start date for IC computation
            end: End date for IC computation

        Returns:
            Dict with ic_mean, ic_std, ic_ir, ic_win_rate, n_days.
            On error, returns {"error": str}.
        """
        try:
            # Validate expression first
            validator = ExpressionValidator(self.config)
            result = validator.validate(expression)
            if not result.valid:
                return {"error": f"Invalid expression: {result.errors}"}

            # Use full universe
            universe = self.config.custom_universe
            if not universe:
                universe = self._get_full_universe()

            returns = self._get_returns_qlib(universe, start, end)
            aux = self._load_aux_data(universe, start, end)
            values = self._compute_factor_qlib(expression, universe, start, end)
            ic_stats = self._compute_ic_from_frames(values, returns, aux_data=aux)
            return ic_stats
        except Exception as e:
            return {"error": str(e)}

    # ──────────────────── Main Entry Point ────────────────────

    def evaluate_batch(self, candidates: List[Dict[str, Any]],
                       skip_stage1: bool = False) -> BatchResult:
        """Run multi-stage pipeline on a batch of candidate factors.

        Args:
            candidates: List of candidate factor dicts.
            skip_stage1: If True, skip Stage 1 (fast IC screening) and Stage 1.5
                (batch dedup). Use when candidates have already been validated by
                the Probe phase. Goes directly to Stage 2 (correlation check).
        """
        self._factor_cache.clear()
        self._subset_factor_cache = {}
        self._lib_values_cache = {}

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
            return BatchResult(screened=[], rejected=invalid, replacements=[])

        if skip_stage1:
            stage2_input = valid
        else:
            stage1_passed = self._fast_ic_screening(valid)
            stage2_input = self._batch_dedup(stage1_passed)

        stage2_passed, stage2_rejected = self._correlation_check(stage2_input)
        replacements = self._replacement_check(stage2_rejected)
        screened, stage3_errors = self._compute_report_cards(stage2_passed)

        all_rejected = list(invalid)
        if not skip_stage1:
            all_rejected += [c for c in valid if c not in stage1_passed]
            all_rejected += [c for c in stage1_passed if c not in stage2_input]
        all_rejected += stage2_rejected
        all_rejected += stage3_errors

        return BatchResult(screened=screened, rejected=all_rejected, replacements=replacements)
