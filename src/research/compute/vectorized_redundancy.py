"""Vectorized uniqueness checks — Phase 2 CP05 inputs.

Two ways to ask "how much does this candidate overlap with the existing
library?":

1. **Pairwise rank correlation** (``compute_pairwise_redundancy``) — for
   each library factor, compute daily cross-sectional Spearman rank
   correlation, take the time-mean, and report the maximum absolute
   correlation + the nearest factor. Drives the ``uniqueness.max_lib_corr``
   field in ``result.yaml``.

2. **Incremental IC** (``compute_incremental_ic``) — regress the
   candidate onto the library per-date, take the residual, and compute
   its IC against forward returns. If residual IC ≈ raw IC, the
   candidate carries independent signal; if it collapses, the library
   already spans it. Delegates to ``core.factor_stats.incremental_ic``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from core.factor_stats import incremental_ic, incremental_ic_from_wides


def _as_series(signal: pd.DataFrame | pd.Series) -> pd.Series:
    """Extract a single-column DataFrame as a Series, or pass through."""
    if hasattr(signal, "ndim") and signal.ndim == 2:
        return signal.iloc[:, 0]
    return signal  # type: ignore[return-value]


@dataclass(frozen=True)
class LibraryRankCache:
    """Per-library pre-computed wide-format ranks.

    Each library factor keeps its own (T_l, S_l) grid (matching what
    ``unstack`` produced for that factor), so candidate-vs-library
    correlations use the same per-pair grid intersection that the legacy
    ``_rank_corr_timeseries`` did. Ranks are pre-computed once per build;
    the candidate's ``.unstack()`` and per-library ``.rank()`` happen at
    eval time but reuse the cached library ranks (no per-candidate
    library unstack).
    """
    indexes: dict[str, pd.DatetimeIndex]   # fid → wide-format row index
    columns: dict[str, pd.Index]           # fid → wide-format column index
    ranks: dict[str, np.ndarray]           # fid → (T_l, S_l) rank with NaN where invalid
    validity: dict[str, np.ndarray]        # fid → (T_l, S_l) bool


def build_library_rank_cache(
    library_signals: dict[str, pd.DataFrame | pd.Series],
) -> LibraryRankCache:
    """Pre-compute wide-format ranks for every library signal once.

    Each library signal is unstacked and rank-transformed (axis=1,
    method='average') at its own native grid — different rolling-window
    lengths produce different leading-NaN dates, and forcing them onto a
    single intersected grid would shrink each library's effective window
    relative to the legacy per-pair behavior. We keep per-library grids
    and let the candidate align against each one individually.
    """
    if not library_signals:
        return LibraryRankCache(indexes={}, columns={}, ranks={}, validity={})

    indexes: dict[str, pd.DatetimeIndex] = {}
    columns: dict[str, pd.Index] = {}
    ranks: dict[str, np.ndarray] = {}
    validity: dict[str, np.ndarray] = {}
    for fid, sig in library_signals.items():
        s = _as_series(sig)
        wide = s.unstack(level=-1)
        indexes[fid] = wide.index
        columns[fid] = wide.columns
        validity[fid] = wide.notna().to_numpy()
        ranks[fid] = wide.rank(axis=1, method="average").to_numpy()

    return LibraryRankCache(
        indexes=indexes, columns=columns, ranks=ranks, validity=validity,
    )


def compute_pairwise_redundancy_precomputed(
    candidate_signal: pd.DataFrame | pd.Series,
    cache: LibraryRankCache,
    threshold: float = 0.7,
    min_obs: int = 5,
) -> dict[str, Any]:
    """Same return shape as compute_pairwise_redundancy, using cached lib ranks.

    For bit-equivalence with legacy: each library uses its own grid (so
    inter-library NaN-pattern differences don't leak into one factor's
    correlation), and ranks are recomputed on the joint-mask intersection
    on both sides (rank-of-rank is order-preserving, so this matches
    legacy ``cand_a.where(joint).rank(...)``).
    """
    if not cache.ranks:
        return {
            "max_lib_corr": 0.0,
            "nearest_factor_id": None,
            "is_near_duplicate": False,
            "exceeds_threshold": False,
            "all_correlations": {},
        }

    cand = _as_series(candidate_signal)
    cand_wide = cand.unstack(level=-1)

    # Pre-rank cand once over its native validity mask. For rows where
    # the joint mask later equals cand_valid, this cached rank IS the
    # joint-masked rank — no re-rank needed. Same property holds for the
    # cached library ranks vs lib_valid. Skipping the per-(cand, lib)
    # rank where the equality holds is the dominant win on this step
    # (in trade-day data the bulk of rows have cand_valid == lib_valid).
    cand_full_arr = cand_wide.to_numpy()
    cand_full_valid = np.isfinite(cand_full_arr)
    cand_full_rank = (
        pd.DataFrame(cand_full_arr).rank(axis=1, method="average").to_numpy()
    )

    all_corrs: dict[str, float] = {}
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        for fid in cache.ranks:
            lib_idx = cache.indexes[fid]
            lib_cols = cache.columns[fid]
            idx = cand_wide.index.intersection(lib_idx)
            cols = cand_wide.columns.intersection(lib_cols)
            if len(idx) == 0 or len(cols) == 0:
                all_corrs[fid] = float("nan")
                continue

            cand_row_pos = cand_wide.index.get_indexer(idx)
            cand_col_pos = cand_wide.columns.get_indexer(cols)
            cand_arr = cand_full_arr[np.ix_(cand_row_pos, cand_col_pos)]
            cand_valid = cand_full_valid[np.ix_(cand_row_pos, cand_col_pos)]
            cand_rank = cand_full_rank[np.ix_(cand_row_pos, cand_col_pos)]

            row_pos = lib_idx.get_indexer(idx)
            col_pos = lib_cols.get_indexer(cols)
            lib_rank = cache.ranks[fid][np.ix_(row_pos, col_pos)]
            lib_valid = cache.validity[fid][np.ix_(row_pos, col_pos)]

            joint = cand_valid & lib_valid
            joint_n = joint.sum(axis=1)
            keep = joint_n >= min_obs
            if not keep.any():
                all_corrs[fid] = float("nan")
                continue

            # Per-row skip: when joint_n == cand_n on row d, then
            # joint[d] == cand_valid[d] (since joint ⊆ cand_valid), so
            # the cached cand_rank[d] IS the joint-masked rank.
            cand_n = cand_valid.sum(axis=1)
            lib_n = lib_valid.sum(axis=1)
            cand_skip = joint_n == cand_n
            lib_skip = joint_n == lib_n

            cr = np.where(cand_skip[:, None], cand_rank, np.nan)
            lr = np.where(lib_skip[:, None], lib_rank.astype(float), np.nan)

            need_cand_rerank = keep & ~cand_skip
            need_lib_rerank = keep & ~lib_skip
            need_either = need_cand_rerank | need_lib_rerank
            if need_either.any():
                idx_rerank = np.where(need_either)[0]
                cand_sub = np.where(joint[idx_rerank], cand_arr[idx_rerank], np.nan)
                lib_sub = np.where(joint[idx_rerank], lib_rank[idx_rerank], np.nan)
                n_sub = cand_sub.shape[0]
                stacked = np.concatenate([cand_sub, lib_sub], axis=0)
                stacked_r = (
                    pd.DataFrame(stacked).rank(axis=1, method="average").to_numpy()
                )
                cr_sub = stacked_r[:n_sub]
                lr_sub = stacked_r[n_sub:]
                # Map back only to rows that actually need each side rerun.
                cand_rerank_local = need_cand_rerank[idx_rerank]
                lib_rerank_local = need_lib_rerank[idx_rerank]
                if cand_rerank_local.any():
                    cr[idx_rerank[cand_rerank_local]] = cr_sub[cand_rerank_local]
                if lib_rerank_local.any():
                    lr[idx_rerank[lib_rerank_local]] = lr_sub[lib_rerank_local]

            mc = np.nanmean(cr, axis=1, keepdims=True)
            ml = np.nanmean(lr, axis=1, keepdims=True)
            c_dev = cr - mc
            l_dev = lr - ml
            num = np.nansum(c_dev * l_dev, axis=1)
            den_c = np.sqrt(np.nansum(c_dev * c_dev, axis=1))
            den_l = np.sqrt(np.nansum(l_dev * l_dev, axis=1))
            den = den_c * den_l
            with np.errstate(invalid="ignore", divide="ignore"):
                corr = np.where(den > 0, num / den, np.nan)
            corr = np.where(keep, corr, np.nan)
            corr_finite = corr[np.isfinite(corr)]
            all_corrs[fid] = float(corr_finite.mean()) if corr_finite.size else float("nan")

    abs_corrs = {fid: abs(c) for fid, c in all_corrs.items() if not np.isnan(c)}
    if not abs_corrs:
        return {
            "max_lib_corr": 0.0,
            "nearest_factor_id": None,
            "is_near_duplicate": False,
            "exceeds_threshold": False,
            "all_correlations": all_corrs,
        }
    nearest_id = max(abs_corrs, key=lambda k: abs_corrs[k])
    max_corr = abs_corrs[nearest_id]
    return {
        "max_lib_corr": round(max_corr, 4),
        "nearest_factor_id": nearest_id,
        "is_near_duplicate": max_corr > 0.9,
        "exceeds_threshold": max_corr > threshold,
        "all_correlations": all_corrs,
    }


def _rank_corr_timeseries(
    cand_wide: pd.DataFrame,
    lib_wide: pd.DataFrame,
    min_obs: int = 5,
) -> pd.Series:
    """Daily cross-sectional Spearman rank correlation.

    Vectorised: joint-dropna mask, per-row rank (pandas ``rank(axis=1)``
    uses argsort internally — no Python per-row loop), Pearson on ranks
    via nansum/nanmean. Returns a Series indexed by date.
    """
    # Align to shared (date × symbol) grid, inner-join on both axes
    idx = cand_wide.index.intersection(lib_wide.index)
    cols = cand_wide.columns.intersection(lib_wide.columns)
    if len(idx) == 0 or len(cols) == 0:
        return pd.Series(dtype=float)
    cand_a = cand_wide.loc[idx, cols]
    lib_a = lib_wide.loc[idx, cols]

    # Joint validity mask — ranks must use the same valid set
    joint = cand_a.notna() & lib_a.notna()
    n_valid = joint.sum(axis=1)
    keep_rows = n_valid >= min_obs
    if not keep_rows.any():
        return pd.Series(dtype=float, index=idx)

    cand_m = cand_a.where(joint)
    lib_m = lib_a.where(joint)

    # Per-row rank (method='average' matches pandas default used by old impl)
    cand_r = cand_m.rank(axis=1, method="average")
    lib_r = lib_m.rank(axis=1, method="average")

    # Pearson of ranks, per row, via nan-aware numpy
    ca = cand_r.to_numpy(dtype=float)
    la = lib_r.to_numpy(dtype=float)

    # Suppress "mean of empty slice" — empty rows resolve to NaN which is
    # masked out by keep_rows below.
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        mc = np.nanmean(ca, axis=1, keepdims=True)
        ml = np.nanmean(la, axis=1, keepdims=True)
        c_dev = ca - mc
        l_dev = la - ml
        num = np.nansum(c_dev * l_dev, axis=1)
        den_c = np.sqrt(np.nansum(c_dev * c_dev, axis=1))
        den_l = np.sqrt(np.nansum(l_dev * l_dev, axis=1))
    den = den_c * den_l
    with np.errstate(invalid="ignore", divide="ignore"):
        corr = np.where(den > 0, num / den, np.nan)
    out = pd.Series(corr, index=idx)
    out = out.where(keep_rows, np.nan)
    return out.dropna()


def compute_pairwise_redundancy(
    candidate_signal: pd.DataFrame | pd.Series,
    library_signals: dict[str, pd.DataFrame | pd.Series],
    threshold: float = 0.7,
) -> dict[str, Any]:
    """Candidate-vs-library cross-sectional rank correlation summary.

    Parameters
    ----------
    candidate_signal
        MultiIndex (datetime, instrument), single value column (or Series).
    library_signals
        ``{factor_id: DataFrame}`` for all admitted factors.
    threshold
        Absolute correlation cutoff for the ``exceeds_threshold`` flag
        (typically ``config.thresholds.max_lib_corr_high == 0.70``).

    Returns
    -------
    dict with keys ``max_lib_corr, nearest_factor_id, is_near_duplicate,
    exceeds_threshold, all_correlations``. ``is_near_duplicate`` is
    hardcoded at ``|corr| > 0.9`` (a stricter gate than
    ``exceeds_threshold``).
    """
    cand = _as_series(candidate_signal)
    cand_wide = cand.unstack(level=-1)

    all_corrs: dict[str, float] = {}
    for fid, lib_df in library_signals.items():
        lib_series = _as_series(lib_df)
        lib_wide = lib_series.unstack(level=-1)
        daily = _rank_corr_timeseries(cand_wide, lib_wide)
        all_corrs[fid] = float(daily.mean()) if not daily.empty else float("nan")

    if not all_corrs:
        return {
            "max_lib_corr": 0.0,
            "nearest_factor_id": None,
            "is_near_duplicate": False,
            "exceeds_threshold": False,
            "all_correlations": {},
        }

    abs_corrs = {
        fid: abs(c) for fid, c in all_corrs.items() if not np.isnan(c)
    }
    if not abs_corrs:
        return {
            "max_lib_corr": 0.0,
            "nearest_factor_id": None,
            "is_near_duplicate": False,
            "exceeds_threshold": False,
            "all_correlations": all_corrs,
        }

    nearest_id = max(abs_corrs, key=lambda k: abs_corrs[k])
    max_corr = abs_corrs[nearest_id]

    return {
        "max_lib_corr": round(max_corr, 4),
        "nearest_factor_id": nearest_id,
        "is_near_duplicate": max_corr > 0.9,
        "exceeds_threshold": max_corr > threshold,
        "all_correlations": all_corrs,
    }


def compute_incremental_ic(
    factor_flat: pd.DataFrame,
    returns_flat: pd.DataFrame,
    library_flat: dict[str, pd.DataFrame],
    min_obs: int = 30,
) -> float | None:
    """IC of candidate residuals after projecting out the library panel.

    Thin wrapper over ``core.factor_stats.incremental_ic`` — returns the
    first element (``ic_mean``) and normalizes NaN/None to ``None`` for
    YAML friendliness.

    Parameters
    ----------
    factor_flat
        Flat ``[time, symbol, value]`` candidate panel.
    returns_flat
        Flat ``[time, symbol, value]`` forward-returns panel.
    library_flat
        ``{factor_id: flat DataFrame}``. Callers that hold MultiIndex
        library signals should convert via
        ``core.factor_stats.multiindex_to_flat`` first.
    """
    if not library_flat:
        return None

    min_required = max(min_obs, len(library_flat) + 2)
    ic_mean, _ = incremental_ic(
        factor_flat, returns_flat, library_flat, min_obs=min_required
    )
    if ic_mean is None or not np.isfinite(ic_mean):
        return None
    return round(float(ic_mean), 6)


def compute_incremental_ic_from_wides(
    factor_flat: pd.DataFrame,
    returns_wide: pd.DataFrame,
    library_wides: dict[str, pd.DataFrame],
    min_obs: int = 30,
) -> float | None:
    """Wides-only variant — pivots only the candidate, reuses cached
    library + returns wides for the OLS solve.

    Drops the per-candidate ``multiindex_to_flat`` + per-library
    ``set_index().unstack()`` round trip that ``compute_incremental_ic``
    incurs. The Phase 2 batch runner caches the wides on
    ``Phase2Inputs`` once per batch.
    """
    if not library_wides:
        return None
    target_wide = factor_flat.set_index(["time", "symbol"])["value"].unstack(level=-1)
    min_required = max(min_obs, len(library_wides) + 2)
    ic_mean, _ = incremental_ic_from_wides(
        target_wide, returns_wide, library_wides, min_obs=min_required,
    )
    if ic_mean is None or not np.isfinite(ic_mean):
        return None
    return round(float(ic_mean), 6)
