"""Cap neutralization: vectorized row-wise OLS on log(market_cap).

Pure function. No I/O, no Qlib.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def neutralize_cap(
    factor_wide: pd.DataFrame,
    market_cap_wide: pd.DataFrame,
    min_obs: int = 30,
) -> pd.DataFrame:
    """Cross-sectionally regress out log(market_cap) per date.

    Univariate regression: y = a + b * log(cap) + residual.
    Computed analytically (slope = cov/var) with row-wise vectorized ops.

    Parameters
    ----------
    factor_wide : (date x symbol) DataFrame of factor values.
    market_cap_wide : (date x symbol) DataFrame of market capitalisation.
    min_obs : minimum valid observations per date.

    Returns
    -------
    Residual DataFrame, same shape as *factor_wide*.
    """
    log_cap = np.log(market_cap_wide.where(market_cap_wide > 0))

    # Align dates and symbols
    common_dates = factor_wide.index.intersection(log_cap.index)
    common_syms = factor_wide.columns.intersection(log_cap.columns)
    if len(common_dates) == 0 or len(common_syms) == 0:
        return pd.DataFrame(np.nan, index=factor_wide.index, columns=factor_wide.columns)

    y = factor_wide.loc[common_dates, common_syms]
    x = log_cap.loc[common_dates, common_syms]

    # Valid mask: both y and x finite
    valid = y.notna() & x.notna()
    n_valid = valid.sum(axis=1)
    enough = n_valid >= min_obs

    # Mask invalid cells
    y_masked = y.where(valid)
    x_masked = x.where(valid)

    # Row-wise means
    y_mean = y_masked.mean(axis=1)
    x_mean = x_masked.mean(axis=1)

    # Centered values
    y_c = y_masked.sub(y_mean, axis=0)
    x_c = x_masked.sub(x_mean, axis=0)

    # Slope = cov(y, x) / var(x) per row
    cov_xy = (y_c * x_c).mean(axis=1)
    var_x = (x_c ** 2).mean(axis=1)
    slope = cov_xy / var_x.where(var_x > 1e-12)

    # Intercept = y_mean - slope * x_mean
    intercept = y_mean - slope * x_mean

    # Residual = y - predicted
    predicted = x_masked.mul(slope, axis=0).add(intercept, axis=0)
    residual = y_masked - predicted

    # Mask dates with insufficient observations
    residual = residual.where(enough, axis=0, other=np.nan)

    # Reindex back to original shape
    result = pd.DataFrame(np.nan, index=factor_wide.index, columns=factor_wide.columns)
    result.loc[common_dates, common_syms] = residual
    return result
