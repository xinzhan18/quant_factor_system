"""Factor preprocessing pipeline for the mining evaluator."""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

from .config import MiningConfig

logger = logging.getLogger(__name__)


class FactorPreprocessor:
    """Preprocessing pipeline applied uniformly to all factors before IC calculation."""

    def __init__(self, config: MiningConfig):
        self.config = config

    def build_tradable_mask(
        self,
        volume: Optional[pd.DataFrame] = None,
        close: Optional[pd.DataFrame] = None,
        limit_up: Optional[pd.DataFrame] = None,
        limit_down: Optional[pd.DataFrame] = None,
    ) -> pd.Series:
        """Build boolean mask: True = tradable.

        Parameters
        ----------
        volume : DataFrame with (datetime, instrument) MultiIndex, column $volume
        close : DataFrame with (datetime, instrument) MultiIndex, column $close
        limit_up : DataFrame with (datetime, instrument) MultiIndex, column $limit_up
        limit_down : DataFrame with (datetime, instrument) MultiIndex, column $limit_down

        Returns
        -------
        pd.Series of booleans indexed like the input data; True means tradable.
        """
        # Get reference index from first available input
        ref = volume if volume is not None else close
        if ref is None:
            ref = limit_up if limit_up is not None else limit_down
        if ref is None:
            raise ValueError("At least one data input required")

        mask = pd.Series(True, index=ref.index)

        if self.config.filter_suspend:
            if volume is not None:
                mask &= volume[volume.columns[0]] > 0
            else:
                logger.warning(
                    "filter_suspend enabled but volume data not provided — skipping"
                )

        if self.config.filter_limit:
            if close is None:
                logger.warning(
                    "filter_limit enabled but close data not provided — skipping limit filter"
                )
            else:
                if limit_up is not None:
                    mask &= close[close.columns[0]] < limit_up[limit_up.columns[0]]
                else:
                    logger.warning(
                        "filter_limit enabled but limit_up data not provided — skipping limit-up filter"
                    )

                if limit_down is not None:
                    mask &= close[close.columns[0]] > limit_down[limit_down.columns[0]]
                else:
                    logger.warning(
                        "filter_limit enabled but limit_down data not provided — skipping limit-down filter"
                    )

        return mask

    def clean_factor_values(self, factor: pd.DataFrame) -> pd.DataFrame:
        """Clean raw factor values: inf->NaN, winsorize, standardize.

        All operations are applied cross-sectionally (per date).

        Parameters
        ----------
        factor : DataFrame with (datetime, instrument) MultiIndex, single factor column.

        Returns
        -------
        Cleaned DataFrame with the same shape and index.
        """
        result = factor.copy()
        col = result.columns[0]

        # Step 1: Replace inf with NaN
        result[col] = result[col].replace([np.inf, -np.inf], np.nan)

        def _process_group(group: pd.Series) -> pd.Series:
            vals = group.copy()
            valid = vals.dropna()
            if len(valid) < 3:
                return vals

            # --- Winsorize ---
            if self.config.winsorize_method == "mad":
                median = valid.median()
                mad = (valid - median).abs().median()
                mad_e = mad * 1.4826
                if mad_e > 0:
                    vals = vals.clip(
                        lower=median - self.config.winsorize_n * mad_e,
                        upper=median + self.config.winsorize_n * mad_e,
                    )
            else:  # sigma
                mean = valid.mean()
                std = valid.std()
                if std > 0:
                    vals = vals.clip(
                        lower=mean - self.config.winsorize_n * std,
                        upper=mean + self.config.winsorize_n * std,
                    )

            # --- Standardize ---
            valid_after = vals.dropna()
            if len(valid_after) < 2:
                return vals

            if self.config.standardize_method == "rank":
                # Rank percentile scaled to approximate N(0,1)
                ranked = vals.rank(pct=True, na_option="keep")
                vals = (ranked - 0.5) * 3.46
            else:  # zscore
                mean = valid_after.mean()
                std = valid_after.std()
                if std > 0:
                    vals = (vals - mean) / std

            return vals

        result[col] = result.groupby(level="datetime")[col].transform(_process_group)
        return result

    def mask_returns(
        self, returns: pd.DataFrame, tradable_mask: pd.Series
    ) -> pd.DataFrame:
        """Set forward returns to NaN where stocks are untradable.

        Parameters
        ----------
        returns : DataFrame with (datetime, instrument) MultiIndex.
        tradable_mask : Boolean Series aligned to returns index; True = tradable.

        Returns
        -------
        DataFrame with same shape; untradable rows set to NaN.
        """
        result = returns.copy()
        result.loc[~tradable_mask] = np.nan
        return result

    def neutralize(
        self,
        factor: pd.DataFrame,
        market_cap: Optional[pd.DataFrame] = None,
        industry: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """Optionally neutralize factor for market cap and/or industry exposure.

        Regresses factor values on ln(market_cap) and/or industry dummies
        cross-sectionally and returns the residuals.

        Parameters
        ----------
        factor : DataFrame with (datetime, instrument) MultiIndex.
        market_cap : DataFrame with $market_cap column, same index structure.
        industry : DataFrame with industry code column, same index structure.

        Returns
        -------
        Neutralized (residualized) DataFrame, or unchanged factor if disabled.
        """
        if self.config.neutralize_mode == "none":
            return factor

        need_mcap = self.config.neutralize_mode in ("market_cap", "both")
        need_ind = self.config.neutralize_mode in ("industry", "both")

        # Warn and short-circuit when required data is entirely missing
        mcap_available = market_cap is not None
        ind_available = industry is not None

        if need_mcap and not mcap_available:
            logger.warning(
                "neutralize_mode=%s but market_cap data not provided — skipping",
                self.config.neutralize_mode,
            )
            if not need_ind or not ind_available:
                return factor

        if need_ind and not ind_available:
            logger.warning(
                "neutralize_mode=%s but industry data not provided — skipping industry",
                self.config.neutralize_mode,
            )
            if not need_mcap or not mcap_available:
                return factor

        result = factor.copy()
        col = result.columns[0]

        for dt in result.index.get_level_values("datetime").unique():
            # Slice rows for this date
            dt_slice = result.index.get_level_values("datetime") == dt
            group_factor = result.loc[dt_slice, col]
            valid = group_factor.dropna()
            if len(valid) < 10:
                continue

            # Instruments for the valid rows
            valid_instruments = valid.index.get_level_values("instrument")

            X_parts = []

            if need_mcap and mcap_available:
                mcap_dates = market_cap.index.get_level_values("datetime")
                if dt in mcap_dates:
                    mcap_group = market_cap.loc[market_cap.index.get_level_values("datetime") == dt]
                    mcap_col = mcap_group.columns[0]
                    # Re-index by instrument to align with valid instruments
                    mcap_by_inst = mcap_group.copy()
                    mcap_by_inst.index = mcap_by_inst.index.get_level_values("instrument")
                    mcap_vals = mcap_by_inst[mcap_col].reindex(valid_instruments)
                    mcap_vals = mcap_vals.fillna(mcap_vals.median())
                    log_mcap = np.log(mcap_vals.clip(lower=1.0).values)
                    X_parts.append(log_mcap.reshape(-1, 1))

            if need_ind and ind_available:
                ind_dates = industry.index.get_level_values("datetime")
                if dt in ind_dates:
                    ind_group = industry.loc[industry.index.get_level_values("datetime") == dt]
                    ind_col = ind_group.columns[0]
                    ind_by_inst = ind_group.copy()
                    ind_by_inst.index = ind_by_inst.index.get_level_values("instrument")
                    ind_vals = ind_by_inst[ind_col].reindex(valid_instruments).fillna(-1)
                    dummies = pd.get_dummies(ind_vals, drop_first=True).values
                    if dummies.shape[1] > 0:
                        X_parts.append(dummies.astype(float))

            if not X_parts:
                continue

            X = np.hstack(X_parts)
            X = np.column_stack([np.ones(len(X)), X])
            y = valid.values.astype(float)

            try:
                beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
                residuals = y - X @ beta
                result.loc[valid.index, col] = residuals
            except np.linalg.LinAlgError:
                pass

        return result

    def preprocess_for_ic(
        self,
        factor: pd.DataFrame,
        returns: pd.DataFrame,
        volume: Optional[pd.DataFrame] = None,
        close: Optional[pd.DataFrame] = None,
        limit_up: Optional[pd.DataFrame] = None,
        limit_down: Optional[pd.DataFrame] = None,
        market_cap: Optional[pd.DataFrame] = None,
        industry: Optional[pd.DataFrame] = None,
    ):
        """Full preprocessing pipeline before Spearman IC calculation.

        Steps:
        1. build_tradable_mask  (skipped if no auxiliary data provided)
        2. clean_factor_values
        3. neutralize           (skipped when neutralize_mode == "none")
        4. mask_returns

        Parameters
        ----------
        factor : Raw factor DataFrame with (datetime, instrument) MultiIndex.
        returns : Forward-return DataFrame with same index structure.
        volume, close, limit_up, limit_down : Optional auxiliary data for masking.
        market_cap, industry : Optional data for neutralization.

        Returns
        -------
        (cleaned_factor, masked_returns) tuple.
        """
        # Build tradable mask only when auxiliary data is available
        aux_data = [volume, close, limit_up, limit_down]
        if any(d is not None for d in aux_data):
            mask = self.build_tradable_mask(
                volume=volume,
                close=close,
                limit_up=limit_up,
                limit_down=limit_down,
            )
        else:
            # No auxiliary data: all stocks are considered tradable
            mask = pd.Series(True, index=returns.index)

        cleaned_factor = self.clean_factor_values(factor)

        if self.config.neutralize_mode != "none":
            cleaned_factor = self.neutralize(
                cleaned_factor, market_cap=market_cap, industry=industry
            )

        masked_returns = self.mask_returns(returns, mask)

        return cleaned_factor, masked_returns
