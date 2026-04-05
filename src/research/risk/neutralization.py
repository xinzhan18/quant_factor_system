"""Cap neutralization: per-date OLS on log(market_cap).

Pure function. No I/O, no Qlib.
Extracted from the old stats/risk_model.py._neutralize_cross_section().
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


def neutralize_cap(
    factor_wide: pd.DataFrame,
    market_cap_wide: pd.DataFrame,
    min_obs: int = 30,
) -> pd.DataFrame:
    """Cross-sectionally regress out log(market_cap) per date.

    Parameters
    ----------
    factor_wide : (date x symbol) DataFrame of factor values.
    market_cap_wide : (date x symbol) DataFrame of market capitalisation.
    min_obs : minimum valid observations per date.

    Returns
    -------
    Residual DataFrame, same shape as *factor_wide*.

    Note: This is cap-only neutralization. Industry neutralization
    requires a DataProvider extension that does not yet exist.
    """
    result = factor_wide.copy()
    result[:] = np.nan

    for date in factor_wide.index:
        y = factor_wide.loc[date].values.astype(float)

        if date not in market_cap_wide.index:
            continue
        cap = market_cap_wide.loc[date].values.astype(float)

        valid = np.isfinite(y) & np.isfinite(cap) & (cap > 0)
        if valid.sum() < min_obs:
            continue

        log_cap = np.log(cap[valid])
        y_v = y[valid]

        X = np.column_stack([np.ones(valid.sum()), log_cap])
        try:
            beta, _, _, _ = np.linalg.lstsq(X, y_v, rcond=None)
            resid = y_v - X @ beta
        except np.linalg.LinAlgError:
            continue

        full_resid = np.full(len(y), np.nan)
        full_resid[valid] = resid
        result.loc[date] = full_resid

    return result
