"""Multi-stage factor mining evaluation pipeline."""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from core.metrics import ic_summary_from_series
from core.factor_stats import (
    daily_cross_sectional_ic as _shared_daily_ic,
    ic_summary as _shared_ic_summary,
    multiindex_to_flat,
    pairwise_cross_sectional_corr as _shared_pairwise_corr,
    quintile_returns as _shared_quintile_returns,
)
from .config import MiningConfig
from .domain.results import BatchResult, _clean_factor_dict  # noqa: F401 — re-export for backward compat
from .domain.similarity import compute_structural_similarity, check_lookahead_bias  # noqa: F401
from .domain.policies import _candidate_cache_key, _is_python_candidate  # noqa: F401
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

        if self.config.neutralize_mode in ("industry", "both"):
            industry_df = self._load_industry_from_db(instruments, start_time, end_time)
            if industry_df is not None:
                aux["industry"] = industry_df

        self._aux_cache[cache_key] = aux
        return aux

    def _load_industry_from_db(self, instruments: list, start_time: str, end_time: str) -> Optional[pd.DataFrame]:
        """Load industry classification from TimescaleDB ref_industry table.

        ref_industry is a static symbol→industry_code mapping (no date column).
        We broadcast it across all trading dates in [start_time, end_time] to produce
        a MultiIndex (datetime, instrument) DataFrame with an 'industry_code' column,
        matching the format expected by FactorPreprocessor.neutralize().
        """
        try:
            import psycopg2
            conn = psycopg2.connect(self.config.system.database.connection_string)
            with conn.cursor() as cur:
                symbols = [str(s) for s in instruments]
                placeholders = ",".join(["%s"] * len(symbols))
                cur.execute(
                    f"SELECT symbol, industry_code FROM ref_industry WHERE symbol IN ({placeholders})",
                    symbols,
                )
                rows = cur.fetchall()
            conn.close()

            if not rows:
                logger.debug("No industry data found in ref_industry for given instruments")
                return None

            ind_map = {sym: code for sym, code in rows}

            # Get trading dates from the already-loaded aux data (volume/close loaded above)
            from qlib.data import D
            dates_df = D.features(
                instruments=instruments,
                fields=["$close"],
                start_time=start_time,
                end_time=end_time,
            )
            dates = dates_df.index.get_level_values("datetime").unique()

            rows_out = []
            for dt in dates:
                for sym in instruments:
                    code = ind_map.get(str(sym))
                    if code is not None:
                        rows_out.append((dt, sym, code))

            if not rows_out:
                return None

            df = pd.DataFrame(rows_out, columns=["datetime", "instrument", "industry_code"])
            df = df.set_index(["datetime", "instrument"]).sort_index()
            logger.info("Loaded industry data from TimescaleDB: %d symbols, %d dates",
                        len(ind_map), len(dates))
            return df

        except Exception as e:
            logger.warning("Could not load industry data from TimescaleDB: %s — industry neutralization skipped", e)
            return None

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

    def _load_ohlcv_panel(self, instruments: list,
                          start_time: str, end_time: str) -> pd.DataFrame:
        """Load OHLCV data as (datetime, instrument) MultiIndex DataFrame.

        Returns columns: open, high, low, close, volume.
        Used by ``_compute_factor_python`` to feed panel data into sandbox.
        """
        from qlib.data import D
        fields = ["$open", "$high", "$low", "$close", "$volume"]
        df = D.features(instruments, fields, start_time=start_time, end_time=end_time)
        df.columns = ["open", "high", "low", "close", "volume"]
        return df

    def _compute_factor_python(self, candidate: Dict[str, Any], instruments: list,
                               start_time: str, end_time: str) -> pd.DataFrame:
        """Execute Python factor in sandbox, return DataFrame matching Qlib output format.

        The sandbox receives the OHLCV panel and returns a pd.Series with the
        same (datetime, instrument) MultiIndex.  We wrap it as a single-column
        DataFrame to match ``_compute_factor_qlib`` output.
        """
        from mining.sandbox import run_factor_in_sandbox
        df = self._load_ohlcv_panel(instruments, start_time, end_time)
        code = candidate["code"]
        params = candidate.get("params", {})
        series = run_factor_in_sandbox(code, df, params, timeout=self.config.sandbox_timeout)
        return series.to_frame(name="factor")

    def _compute_factor(self, candidate: Dict[str, Any], instruments: list,
                        start_time: str, end_time: str) -> pd.DataFrame:
        """Unified dispatcher: route to DSL (Qlib) or Python (sandbox) execution path."""
        if _is_python_candidate(candidate):
            return self._compute_factor_python(candidate, instruments, start_time, end_time)
        return self._compute_factor_qlib(candidate["expression"], instruments, start_time, end_time)

    # ──────────────────── IC Computation ────────────────────

    def _compute_daily_ics(
        self, factor_values: pd.DataFrame, returns: pd.DataFrame,
        aux_data: Optional[Dict[str, pd.DataFrame]] = None,
    ) -> pd.Series:
        """Compute daily cross-sectional Spearman IC.

        Returns a pd.Series with DatetimeIndex for easy groupby year/month/quarter.
        Delegates to core.factor_stats.daily_cross_sectional_ic after converting
        MultiIndex DataFrames to flat format.
        """
        if aux_data:
            factor_values, returns = self._preprocessor.preprocess_for_ic(
                factor=factor_values, returns=returns, **aux_data,
            )
        flat_factor = multiindex_to_flat(factor_values)
        flat_returns = multiindex_to_flat(returns)
        return _shared_daily_ic(flat_factor, flat_returns, method="spearman", min_obs=3)

    def _compute_ic_from_frames(
        self, factor_values: pd.DataFrame, returns: pd.DataFrame,
        aux_data: Optional[Dict[str, pd.DataFrame]] = None,
    ) -> Dict[str, Any]:
        """Compute IC summary stats. Delegates to shared functions."""
        daily_ics = self._compute_daily_ics(factor_values, returns, aux_data)
        if daily_ics.empty:
            return {"ic_mean": np.nan, "ic_std": np.nan, "ic_ir": np.nan,
                    "ic_win_rate": np.nan, "n_days": 0}
        summary = _shared_ic_summary(daily_ics)
        summary["n_days"] = len(daily_ics)
        return summary

    # ──────────────────── Correlation ────────────────────

    def _pairwise_correlation(self, a: pd.DataFrame, b: pd.DataFrame) -> float:
        """Average daily cross-sectional Spearman correlation.

        Delegates to core.factor_stats.pairwise_cross_sectional_corr.
        """
        flat_a = multiindex_to_flat(a)
        flat_b = multiindex_to_flat(b)
        result = _shared_pairwise_corr(flat_a, flat_b, min_obs=3)
        return result if result is not None else 0.0

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

    def _stage1_window(self):
        """Return (start, end) for Stage 1: last N years of training period."""
        from datetime import datetime, timedelta
        end = datetime.strptime(self.config.train_end, "%Y-%m-%d")
        start = end - timedelta(days=365 * self.config.stage1_lookback_years)
        return start.strftime("%Y-%m-%d"), self.config.train_end

    def _fast_ic_screening(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        universe = self._get_full_universe()
        s1_start, s1_end = self._stage1_window()
        returns = self._get_returns_qlib(universe, s1_start, s1_end)
        aux = self._load_aux_data(universe, s1_start, s1_end)
        results = []
        for c in candidates:
            try:
                values = self._compute_factor(c, universe, s1_start, s1_end)
                self._subset_factor_cache[_candidate_cache_key(c)] = values
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
            ckey = _candidate_cache_key(c)
            cached = self._subset_factor_cache.get(ckey)
            if cached is not None:
                values_map[ckey] = cached
            else:
                try:
                    universe = self._get_full_universe()
                    s1_start, s1_end = self._stage1_window()
                    vals = self._compute_factor(c, universe, s1_start, s1_end)
                    values_map[ckey] = vals
                except Exception:
                    values_map[ckey] = pd.DataFrame()
        sorted_candidates = sorted(candidates,
                                    key=lambda c: abs(c.get("stage1", {}).get("ic_mean", 0)),
                                    reverse=True)
        kept = []
        for c in sorted_candidates:
            c_vals = values_map.get(_candidate_cache_key(c))
            if c_vals is None or c_vals.empty:
                kept.append(c)
                continue
            is_dup = False
            for k in kept:
                k_vals = values_map.get(_candidate_cache_key(k))
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

    def _corr_check_window(self) -> tuple:
        """Return (start, end) for the correlation check window.

        Uses the last `corr_check_years` of the IS period.  Correlation rank is
        stable over 1–2 years; no need to load 8 years of library data.
        """
        from datetime import date, timedelta
        end = pd.Timestamp(self.config.train_end).date()
        start = date(end.year - self.config.corr_check_years, end.month, end.day)
        return str(start), str(end)

    def _corr_fetch_window(self) -> tuple:
        """Return a 3-month continuous window at the end of the IS period.

        Using a continuous range (not sampled dates) lets TimescaleDB use the
        (factor_name, time) index directly — no type cast, no chunk scatter.
        3 months × 5000 stocks × 34 factors ≈ 11 M rows, fetched in ~5 s.
        """
        end = pd.Timestamp(self.config.train_end)
        start = end - pd.DateOffset(months=3)
        return str(start.date()), str(end.date())

    def _compute_lib_corrs_sampled(
        self,
        candidate_flat: pd.DataFrame,
        lib_factor_names: List[str],
        _unused_sample_dates: List[str],   # kept for API compat, ignored
    ) -> Dict[str, float]:
        """Compute Spearman correlation between a candidate and all library factors.

        Fetches a 3-month continuous window from TimescaleDB (index-friendly range
        scan), then vectorises cross-sectional rank correlation in Python.

        Returns {factor_name: abs_mean_daily_spearman}.
        """
        import psycopg2

        win_start, win_end = self._corr_fetch_window()

        if candidate_flat.empty or not lib_factor_names:
            return {}

        cand = candidate_flat[
            (candidate_flat["time"] >= pd.Timestamp(win_start)) &
            (candidate_flat["time"] <= pd.Timestamp(win_end))
        ].copy()
        if cand.empty:
            return {}

        result: Dict[str, float] = {}
        try:
            import time as _time
            conn = psycopg2.connect(self.config.system.database.connection_string)
            placeholders_f = ",".join(["%s"] * len(lib_factor_names))
            _t0 = _time.perf_counter()
            with conn.cursor() as cur:
                cur.execute("SET max_parallel_workers_per_gather = 0")
                cur.execute(
                    f"SELECT factor_name, time, symbol, value FROM factor_values "
                    f"WHERE factor_name IN ({placeholders_f}) "
                    f"AND time >= %s AND time <= %s",
                    lib_factor_names + [win_start, win_end],
                )
                rows = cur.fetchall()
            conn.close()
            logger.info("Corr DB fetch: %.2fs, %s rows", _time.perf_counter() - _t0, f"{len(rows):,}")

            if not rows:
                return {}

            lib_df = pd.DataFrame(rows, columns=["factor_name", "time", "symbol", "value"])
            lib_df["time"] = pd.to_datetime(lib_df["time"])

            _t1 = _time.perf_counter()
            # Vectorised Spearman across all lib factors simultaneously:
            # pivot → cross-sectional rank → z-score → matrix multiply → mean
            lib_wide = lib_df.pivot_table(
                index=["time", "symbol"], columns="factor_name", values="value", aggfunc="first"
            )
            cand_s = cand.set_index(["time", "symbol"])["value"].rename("_cand_")
            combined = lib_wide.join(cand_s, how="inner").dropna(subset=["_cand_"])

            if len(combined) >= 30:
                # Cross-sectional rank per day (NaN stays NaN)
                ranked = combined.groupby(level="time").rank(method="average", na_option="keep")

                # Keep only days with ≥ 10 valid candidate observations
                valid_days = ranked["_cand_"].notna().groupby(level="time").sum()
                valid_days = valid_days[valid_days >= 10].index
                ranked = ranked.loc[ranked.index.get_level_values("time").isin(valid_days)]

                if not ranked.empty:
                    # Z-score ranks per day: (rank - mean) / std
                    grp = ranked.groupby(level="time")
                    daily_std = grp.transform("std")
                    daily_std[daily_std < 1e-9] = np.nan
                    ranked_z = (ranked - grp.transform("mean")) / daily_std

                    # Daily Spearman ≈ mean(z_cand × z_lib) per day, then mean across days
                    cand_z = ranked_z["_cand_"]
                    lib_z = ranked_z.drop(columns=["_cand_"])
                    products = lib_z.multiply(cand_z, axis=0)
                    mean_corrs = products.groupby(level="time").mean().mean()

                    result = {
                        fname: abs(float(v))
                        for fname, v in mean_corrs.items()
                        if not np.isnan(v) and fname in set(lib_factor_names)
                    }

            logger.info("Corr compute: %.2fs | total: %.2fs | %s rows, %d/%d lib factors matched",
                        _time.perf_counter() - _t1, _time.perf_counter() - _t0,
                        f"{len(rows):,}", len(result), len(lib_factor_names))
        except Exception as e:
            logger.warning("Correlation check failed: %s", e)
        return result

    def _correlation_check(self, candidates: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        library = self._load_library()
        lib_factors = library.list_factors()
        lib_factor_names = [f"factor_{lf['id']}" for lf in lib_factors]
        id_by_fname = {f"factor_{lf['id']}": lf["id"] for lf in lib_factors}

        full_universe = self._get_full_universe()
        corr_start, corr_end = self._corr_check_window()
        returns = self._get_returns_qlib(full_universe, self.config.train_start, self.config.train_end)
        aux = self._load_aux_data(full_universe, self.config.train_start, self.config.train_end)

        logger.info("Stage 2 corr: %d lib factors, window %s → %s",
                    len(lib_factor_names), corr_start, corr_end)

        passed, rejected = [], []
        for c in candidates:
            try:
                factor_vals = self._compute_factor(c, full_universe,
                                                   self.config.train_start, self.config.train_end)
                self._factor_cache[_candidate_cache_key(c)] = factor_vals
                full_ic = self._compute_ic_from_frames(factor_vals, returns, aux_data=aux)
                c["full_ic"] = full_ic

                flat = multiindex_to_flat(factor_vals)
                corrs_by_fname = self._compute_lib_corrs_sampled(
                    flat, lib_factor_names, []
                )
                all_corrs = {id_by_fname[fn]: v for fn, v in corrs_by_fname.items() if fn in id_by_fname}
                c["_lib_correlations"] = all_corrs

                max_corr = max(all_corrs.values(), default=0.0)
                max_corr_factor = max(all_corrs, key=all_corrs.get) if all_corrs else None

                if max_corr < self.config.correlation_threshold:
                    c["stage2"] = {"max_corr": max_corr, "max_corr_factor": max_corr_factor, "passed": True}
                    passed.append(c)
                else:
                    c["stage2"] = {"max_corr": max_corr, "max_corr_factor": max_corr_factor, "passed": False}
                    c["reject_reason"] = "stage2_corr"
                    c["reject_meta"] = {
                        "code": "stage2_corr",
                        "blocker": max_corr_factor,
                        "corr": max_corr,
                    }
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

        Strategy: factor value loading is sequential (Qlib D.features is not
        thread-safe); IC computation and report card building are pure pandas
        and run in parallel via ThreadPoolExecutor.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        full_universe = self._get_full_universe()
        test_end = self.config.test_end

        # Shared data (loaded once, sequential)
        aux_is = self._load_aux_data(full_universe, self.config.train_start, self.config.train_end)
        aux_oos = self._load_aux_data(full_universe, self.config.test_start, test_end)
        returns_is = self._get_returns_qlib(full_universe, self.config.train_start, self.config.train_end)
        returns_oos = self._get_returns_qlib(full_universe, self.config.test_start, test_end)

        # Multi-horizon returns: horizon=1 reuses returns_is (no extra Qlib call)
        returns_multi: Dict[int, pd.DataFrame] = {}
        for h in self.config.decay_horizons:
            if h == 1:
                returns_multi[1] = returns_is
            else:
                expr = f"Ref($close, -{h}) / $close - 1"
                try:
                    returns_multi[h] = self._compute_factor_qlib(
                        expr, full_universe, self.config.train_start, self.config.train_end,
                    )
                except Exception as e:
                    logger.warning("Failed to compute horizon %d returns: %s", h, e)

        # ── Step 1: Load all factor values sequentially (Qlib not thread-safe) ──
        factor_vals_map: Dict[str, tuple] = {}  # ckey -> (vals_is, vals_oos)
        load_errors: Dict[str, Exception] = {}
        for c in candidates:
            ckey = _candidate_cache_key(c)
            try:
                vals_is = self._factor_cache.get(ckey)
                if vals_is is None:
                    vals_is = self._compute_factor(
                        c, full_universe, self.config.train_start, self.config.train_end,
                    )
                vals_oos = self._compute_factor(c, full_universe, self.config.test_start, test_end)
                factor_vals_map[ckey] = (vals_is, vals_oos)
            except Exception as e:
                load_errors[ckey] = e
                logger.warning("Stage 3 factor load error for %s: %s", c.get("name"), e)

        # ── Step 2: IC computation + report card — parallel (pure pandas) ──────
        def _compute_stats_and_rc(c: Dict[str, Any]) -> Dict[str, Any]:
            ckey = _candidate_cache_key(c)
            vals_is, vals_oos = factor_vals_map[ckey]

            daily_ics_is = self._compute_daily_ics(vals_is, returns_is, aux_data=aux_is)
            daily_ics_oos = self._compute_daily_ics(vals_oos, returns_oos, aux_data=aux_oos)

            # Reuse daily_ics_is for horizon=1 to avoid redundant computation
            daily_ics_by_horizon: Dict[int, pd.Series] = {1: daily_ics_is}
            for h, ret_h in returns_multi.items():
                if h != 1:
                    daily_ics_by_horizon[h] = self._compute_daily_ics(
                        vals_is, ret_h, aux_data=aux_is,
                    )

            rc = compute_report_card(
                daily_ics_is=daily_ics_is,
                daily_ics_oos=daily_ics_oos,
                factor_vals_is=vals_is,
                factor_vals_oos=vals_oos,
                returns_is=returns_is,
                returns_oos=returns_oos,
                daily_ics_by_horizon=daily_ics_by_horizon,
                lib_values=self._lib_values_cache,
                lib_corr_profile=c.get("_lib_correlations", {}),
                stage2_info=c.get("stage2", {}),
                expression_depth=self._max_expression_depth(c.get("expression", "")),
            )
            return {"rc": rc, "vals_is": vals_is, "vals_oos": vals_oos}

        screened, errors = [], []
        eligible = [c for c in candidates if _candidate_cache_key(c) not in load_errors]
        max_workers = min(4, len(eligible)) if eligible else 1

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_to_c = {pool.submit(_compute_stats_and_rc, c): c for c in eligible}
            for future in as_completed(future_to_c):
                c = future_to_c[future]
                try:
                    result = future.result()
                    rc = result["rc"]
                    c["report_card"] = rc.to_dict()
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
                    c["_factor_values"] = result["vals_is"]
                    c["_factor_values_oos"] = result["vals_oos"]
                    screened.append(c)
                except Exception as e:
                    c["stage3"] = {"error": str(e)}
                    c["report_card"] = {"error": str(e)}
                    errors.append(c)
                    logger.warning("Stage 3 error for %s: %s", c.get("name"), e)

        # Add factor-load failures to errors
        for c in candidates:
            ckey = _candidate_cache_key(c)
            if ckey in load_errors:
                c["stage3"] = {"error": str(load_errors[ckey])}
                c["report_card"] = {"error": str(load_errors[ckey])}
                errors.append(c)

        return screened, errors

    # Keep old name as alias for backward compatibility
    _full_validation = _compute_report_cards

    # ──────────────────── Quantile Returns (legacy) ────────────────────

    def _compute_quantile_returns(self, factor_values: pd.DataFrame,
                                   returns: pd.DataFrame,
                                   n_quantiles: int = 5) -> Dict[str, float]:
        """Legacy quantile returns. Delegates to core.factor_stats."""
        flat_factor = multiindex_to_flat(factor_values)
        flat_returns = multiindex_to_flat(returns)
        q_rets, _ = _shared_quintile_returns(
            flat_factor, flat_returns, n_quantiles=n_quantiles, min_obs=n_quantiles,
        )
        return q_rets

    # ──────────────────── Optuna Parameter Optimization ────────────────────

    def _optimize_params(self, candidate: dict) -> dict:
        """Use Optuna to search param_space for best Rank IC. Returns candidate with optimized params."""
        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)

        param_space = candidate.get("param_space")
        if not param_space:
            return candidate

        # Use fast screening instruments and train period
        instruments = self._get_fast_screening_universe()
        start = self.config.train_start
        end = self.config.train_end

        def objective(trial):
            params = {}
            for name, bounds in param_space.items():
                if isinstance(bounds, (list, tuple)) and len(bounds) == 2:
                    if isinstance(bounds[0], int) and isinstance(bounds[1], int):
                        params[name] = trial.suggest_int(name, bounds[0], bounds[1])
                    else:
                        params[name] = trial.suggest_float(name, float(bounds[0]), float(bounds[1]))
                else:
                    params[name] = bounds  # Fixed value
            test_candidate = {**candidate, "params": params}
            try:
                factor_values = self._compute_factor(test_candidate, instruments, start, end)
                # Compute rank IC against forward returns
                returns = self._get_returns_qlib(instruments, start, end)
                merged = factor_values.join(returns, how="inner").dropna()
                if len(merged) < 50:
                    return 0.0
                ic = merged.iloc[:, 0].corr(merged.iloc[:, 1], method="spearman")
                return abs(ic) if not pd.isna(ic) else 0.0
            except Exception:
                return 0.0

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=self.config.optuna_trials,
                       timeout=self.config.optuna_timeout, show_progress_bar=False)

        if study.best_value > 0:
            result = {**candidate, "params": study.best_params}
            return result
        return candidate

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

    # ──────────────────── Hard Gates ────────────────────

    def _apply_hard_gates(
        self, screened: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Post-Stage3 hard gates. Cannot be overridden by LLM or --admit."""
        passed, gated = [], []
        for c in screened:
            rc = c.get("report_card", {})
            reasons: List[Dict[str, Any]] = []

            if rc.get("ic_sign_consistent") is False:
                reasons.append({"code": "ic_sign_flip", "value": None})

            decay = rc.get("oos_decay_ratio")
            if decay is not None and decay < self.config.hard_gate_oos_decay_min:
                reasons.append({"code": "oos_decay_too_low",
                                "value": round(decay, 3),
                                "threshold": self.config.hard_gate_oos_decay_min})

            cov = rc.get("coverage")
            if cov is not None and cov < self.config.hard_gate_coverage_min:
                reasons.append({"code": "coverage_too_low",
                                "value": round(cov, 3),
                                "threshold": self.config.hard_gate_coverage_min})

            mono_is = rc.get("monotonicity_is")
            mono_oos = rc.get("monotonicity_oos")
            if (mono_is is not None and mono_oos is not None
                    and mono_is != 0 and mono_oos != 0
                    and (mono_is * mono_oos < 0)):
                reasons.append({"code": "mono_sign_flip",
                                "value": {"is": round(mono_is, 2),
                                          "oos": round(mono_oos, 2)}})

            ic_oos_val = rc.get("ic_mean_oos")
            if ic_oos_val is not None and abs(ic_oos_val) < self.config.hard_gate_ic_oos_min:
                reasons.append({"code": "ic_oos_too_low",
                                "value": round(abs(ic_oos_val), 4),
                                "threshold": self.config.hard_gate_ic_oos_min})

            if reasons:
                c["hard_gate_reject"] = reasons
                gated.append(c)
                logger.info("Hard gate reject %s: %s",
                            c["name"], [r["code"] for r in reasons])
            else:
                passed.append(c)
        return passed, gated

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
            if _is_python_candidate(c):
                result = validator.validate_python(c.get("code", ""))
            else:
                result = validator.validate(c["expression"])
            if result.valid:
                valid.append(c)
            else:
                c["validation_error"] = result.errors
                invalid.append(c)

        if not valid:
            return BatchResult(screened=[], rejected=invalid, replacements=[])

        # Optimize params for Python factors with param_space
        optimized_valid = []
        for candidate in valid:
            if candidate.get("param_space") and _is_python_candidate(candidate):
                try:
                    candidate = self._optimize_params(candidate)
                except Exception as e:
                    logger.warning("Optuna optimization failed for %s: %s", candidate["name"], e)
            optimized_valid.append(candidate)
        valid = optimized_valid

        if skip_stage1:
            dedup_input = valid
        else:
            stage1_passed = self._fast_ic_screening(valid)
            dedup_input = stage1_passed

        # batch_dedup always runs (even when skip_stage1) to remove correlated
        # candidates within the same batch.
        stage2_input = self._batch_dedup(dedup_input)

        stage2_passed, stage2_rejected = self._correlation_check(stage2_input)
        replacements = self._replacement_check(stage2_rejected)
        screened, stage3_errors = self._compute_report_cards(stage2_passed)
        # Apply hard gates (cannot be overridden by LLM or --admit)
        screened, hard_gated = self._apply_hard_gates(screened)

        all_rejected = list(invalid)
        if not skip_stage1:
            all_rejected += [c for c in valid if c not in stage1_passed]
        # dedup rejects (always tracked)
        dedup_rejected = [c for c in dedup_input if c not in stage2_input]
        for c in dedup_rejected:
            c.setdefault("reject_reason",
                         "batch_dedup: correlated with earlier kept candidate")
        all_rejected += dedup_rejected
        all_rejected += stage2_rejected
        all_rejected += stage3_errors
        all_rejected += hard_gated

        # Build canonical metrics for library storage (f['stage3'] and f['full_ic'] unchanged)
        from .schema import normalize_metrics
        for f in screened:
            raw = {**f.get('full_ic', {}), **f.get('stage3', {})}
            f['metrics'] = normalize_metrics(raw)
        for r in replacements:
            nf = r.get('new_factor', r)
            raw = {**nf.get('full_ic', {}), **nf.get('stage3', {})}
            nf['metrics'] = normalize_metrics(raw)

        return BatchResult(screened=screened, rejected=all_rejected, replacements=replacements)
