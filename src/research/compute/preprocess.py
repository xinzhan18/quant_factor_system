"""Preprocessor -- vectorized cross-sectional preprocessing pipeline.

Pipeline steps (applied per-date cross-section using groupby):
    1. universe_mask  -- filter to stocks in the target universe
    2. tradability    -- drop stocks with NaN close or zero volume
    3. winsorize      -- clip outliers at mean +/- n_sigma * std
    4. zscore         -- standardize to mean=0, std=1
    5. neutralize     -- (optional) subtract industry/size group means

All operations are vectorized using pandas groupby -- no Python
for-loops over dates.

Usage:
    pp = Preprocessor(sigma=3.0)
    clean = pp.run(factor_df, market_df=market_df)
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class Preprocessor:
    """Vectorized cross-sectional factor preprocessing.

    Parameters
    ----------
    sigma : float
        Number of standard deviations for winsorization.  Default 3.0.
    neutralize_col : str or None
        Column name in *market_df* to use for group-neutralization
        (e.g. ``"industry"``).  If None, neutralization is skipped.
    """

    def __init__(
        self,
        sigma: float = 3.0,
        neutralize_col: Optional[str] = None,
    ) -> None:
        self.sigma = sigma
        self.neutralize_col = neutralize_col

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        factor_df: pd.DataFrame,
        market_df: Optional[pd.DataFrame] = None,
        tradability_check: bool = True,
    ) -> pd.DataFrame:
        """Apply the full preprocessing pipeline.

        Parameters
        ----------
        factor_df : pd.DataFrame
            Factor values with (datetime, instrument) MultiIndex and a
            single value column.
        market_df : pd.DataFrame, optional
            Market data with the same MultiIndex.  Must contain ``$close``
            and ``$volume`` columns if *tradability_check* is True, and
            *neutralize_col* if neutralization is enabled.
        tradability_check : bool
            Whether to mask out untradable stocks (NaN close / zero volume).

        Returns
        -------
        pd.DataFrame
            Preprocessed factor values, same shape/index as input (with NaN
            for filtered-out rows).
        """
        result = factor_df.copy()

        if tradability_check and market_df is not None:
            result = self._apply_tradability(result, market_df)

        result = self._winsorize(result)
        result = self._zscore(result)

        if self.neutralize_col and market_df is not None:
            result = self._neutralize(result, market_df)

        return result

    # ------------------------------------------------------------------
    # Pipeline steps
    # ------------------------------------------------------------------

    def _apply_tradability(
        self,
        factor_df: pd.DataFrame,
        market_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Set factor to NaN where close is NaN or volume is zero.

        Mutates *factor_df* in place -- caller (``run``) already made
        a copy, so no extra copy is needed here.
        """
        result = factor_df
        col = result.columns[0]

        has_close = "$close" in market_df.columns or "close" in market_df.columns
        has_volume = "$volume" in market_df.columns or "volume" in market_df.columns

        if has_close:
            close_col = "$close" if "$close" in market_df.columns else "close"
            mask_close = market_df[close_col].isna()
            result.loc[mask_close, col] = np.nan

        if has_volume:
            vol_col = "$volume" if "$volume" in market_df.columns else "volume"
            mask_vol = market_df[vol_col] == 0
            result.loc[mask_vol, col] = np.nan

        return result

    def _winsorize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cross-sectional winsorization: clip to mean +/- sigma*std per date."""
        col = df.columns[0]
        g = df[col].groupby(level="datetime")
        mean = g.transform("mean")
        std = g.transform("std")
        lower = mean - self.sigma * std
        upper = mean + self.sigma * std
        result = df.copy()
        result[col] = df[col].clip(lower=lower, upper=upper)
        return result

    def _zscore(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cross-sectional z-score: (x - mean) / std per date."""
        col = df.columns[0]
        original_nan = df[col].isna()
        g = df[col].groupby(level="datetime")
        mean = g.transform("mean")
        std = g.transform("std")
        result = df.copy()
        safe_std = std.replace(0, np.nan)
        result[col] = (df[col] - mean) / safe_std
        # Fill zero-std group NaN with 0.0, but preserve original NaN
        zero_std_fill = result[col].isna() & ~original_nan
        result.loc[zero_std_fill, col] = 0.0
        return result

    def _neutralize(
        self,
        factor_df: pd.DataFrame,
        market_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Group-neutralize: subtract group mean per date per group."""
        col = factor_df.columns[0]
        group_col = self.neutralize_col

        if group_col not in market_df.columns:
            logger.warning(
                "Neutralization column '%s' not in market_df, skipping",
                group_col,
            )
            return factor_df

        combined = factor_df.copy()
        combined["_group"] = market_df[group_col]

        def _demean_group(g: pd.DataFrame) -> pd.DataFrame:
            out = g.copy()
            out[col] = g[col] - g[col].mean()
            return out

        result = combined.groupby(
            [combined.index.get_level_values("datetime"), "_group"],
            group_keys=False,
        ).apply(_demean_group)

        return result[[col]]
