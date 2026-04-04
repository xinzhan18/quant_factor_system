"""Layer 3: Local subspace redundancy via daily cross-sectional ridge regression.

Pure functions, no I/O.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from research.redundancy.pairwise import _as_series


def _ridge_regression_crosssection(
    y: np.ndarray,
    X: np.ndarray,
    alpha: float = 1.0,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Solve ridge regression for one cross-section.

    Parameters
    ----------
    y : array of shape (n_stocks,)
    X : array of shape (n_stocks, k_basis)
    alpha : ridge penalty

    Returns
    -------
    beta : array (k_basis,)
    residual : array (n_stocks,)
    r_squared : float
    """
    k = X.shape[1]
    XtX = X.T @ X + alpha * np.eye(k)
    Xty = X.T @ y
    beta = np.linalg.solve(XtX, Xty)
    y_hat = X @ beta
    residual = y - y_hat
    ss_res = np.sum(residual ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return beta, residual, r_squared


def _determine_confidence(
    basis_count: int,
    family_size: int,
    validation_days: int,
) -> str:
    """Determine confidence level per the spec rules."""
    if family_size < 2:
        return "insufficient_family_size"
    if basis_count < 2:
        return "insufficient_basis"
    if basis_count == 2 and validation_days >= 120:
        return "low"
    if basis_count == 3:
        if family_size <= 5 or validation_days < 250:
            return "medium"
        if family_size >= 6 and validation_days >= 250:
            return "high"
    # Fallback: basis_count == 2 but validation_days < 120
    return "insufficient_basis"


def compute_subspace_redundancy(
    candidate_signal: pd.DataFrame,
    basis_signals: dict[str, pd.DataFrame],
    forward_returns: pd.DataFrame,
    family_size: int = 0,
    alpha: float = 1.0,
) -> dict:
    """Compute local subspace redundancy via daily cross-sectional ridge
    regression.

    For each date's cross-section:
        candidate_t = basis_t @ beta_t + residual_t
    Then:
        subspace_redundancy_score = median(R^2 across dates)
        residual_incremental_ic  = mean(corr(residual_t, fwd_return_t))

    Parameters
    ----------
    candidate_signal : DataFrame
        MultiIndex (datetime, instrument), single value column.
    basis_signals : dict[str, DataFrame]
        ``{factor_id: DataFrame}`` for the selected basis factors (up to K=3).
    forward_returns : DataFrame
        MultiIndex (datetime, instrument), single value column of forward returns.
    family_size : int
        Total number of factors in the candidate's family (for confidence calc).
    alpha : float
        Ridge regularization parameter.

    Returns
    -------
    dict with keys:
        subspace_redundancy_score, residual_incremental_ic,
        basis_factor_ids, basis_factor_count, validation_days,
        subspace_confidence
    """
    basis_ids = list(basis_signals.keys())
    basis_count = len(basis_ids)

    cand = _as_series(candidate_signal)
    fwd = _as_series(forward_returns)

    parts = {"cand": cand, "fwd": fwd}
    for fid in basis_ids:
        parts[fid] = _as_series(basis_signals[fid])

    combined = pd.DataFrame(parts)
    combined = combined.dropna()

    if combined.empty:
        return _empty_result(basis_ids, family_size)

    dates = combined.index.get_level_values(0).unique()
    validation_days = len(dates)

    confidence = _determine_confidence(basis_count, family_size, validation_days)

    r2_list: list[float] = []
    residual_ic_list: list[float] = []

    for dt in dates:
        try:
            cross = combined.loc[dt]
        except KeyError:
            continue
        if isinstance(cross, pd.Series):
            # Only one instrument on this date -- skip.
            continue
        if len(cross) < max(5, basis_count + 2):
            continue

        y = cross["cand"].values.astype(float)
        X = cross[basis_ids].values.astype(float)
        fwd_ret = cross["fwd"].values.astype(float)

        _beta, residual, r2 = _ridge_regression_crosssection(y, X, alpha=alpha)
        r2_list.append(r2)

        # Spearman rank correlation of residual with forward return.
        if len(residual) >= 5:
            r_rank = pd.Series(residual).rank()
            f_rank = pd.Series(fwd_ret).rank()
            ic = r_rank.corr(f_rank)
            if not np.isnan(ic):
                residual_ic_list.append(ic)

    if not r2_list:
        return _empty_result(basis_ids, family_size)

    return {
        "subspace_redundancy_score": round(float(np.median(r2_list)), 4),
        "residual_incremental_ic": round(float(np.mean(residual_ic_list)), 4) if residual_ic_list else 0.0,
        "basis_factor_ids": basis_ids,
        "basis_factor_count": basis_count,
        "validation_days": validation_days,
        "subspace_confidence": confidence,
    }


def _empty_result(basis_ids: list[str], family_size: int) -> dict:
    """Return a result dict when no valid cross-sections exist."""
    confidence = _determine_confidence(len(basis_ids), family_size, 0)
    return {
        "subspace_redundancy_score": None,
        "residual_incremental_ic": None,
        "basis_factor_ids": basis_ids,
        "basis_factor_count": len(basis_ids),
        "validation_days": 0,
        "subspace_confidence": confidence,
    }
