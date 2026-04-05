"""FactorEngine -- DSL and Python factor execution.

Combines Qlib expression-based computation (DSL) with sandbox-based
Python factor execution into a single interface.

Usage:
    engine = FactorEngine(provider=DataProvider(), preprocessor=Preprocessor())

    # DSL expression
    result = engine.compute_dsl("Rank($close)", "2020-01-01", "2024-12-31")

    # Python factor code
    result = engine.compute_python(
        code="return ops.cs_rank(df['close'].pct_change(params['period']))",
        start="2020-01-01",
        end="2024-12-31",
        params={"period": 20},
    )
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

import pandas as pd

from research.compute.data_provider import DataProvider
from research.compute.preprocess import Preprocessor
from research.compute.sandbox import SandboxError, run_factor_in_sandbox

logger = logging.getLogger(__name__)


class FactorEngine:
    """Unified factor computation for DSL expressions and Python code.

    Parameters
    ----------
    provider : DataProvider, optional
        Data provider for Qlib features.  Created with defaults if omitted.
    preprocessor : Preprocessor, optional
        Preprocessing pipeline.  Created with defaults if omitted.
    sandbox_timeout : int
        Timeout in seconds for Python factor sandbox execution.
    """

    def __init__(
        self,
        provider: Optional[DataProvider] = None,
        preprocessor: Optional[Preprocessor] = None,
        sandbox_timeout: int = 60,
    ) -> None:
        self.provider = provider or DataProvider()
        self.preprocessor = preprocessor or Preprocessor()
        self.sandbox_timeout = sandbox_timeout

    # ------------------------------------------------------------------
    # DSL expression execution
    # ------------------------------------------------------------------

    def compute_dsl(
        self,
        expression: str,
        start: str,
        end: str,
        preprocess: bool = False,
    ) -> pd.DataFrame:
        """Compute a Qlib DSL expression.

        Parameters
        ----------
        expression : str
            Qlib expression string (e.g. ``"Rank($close)"``).
        start, end : str
            Date range in ``"YYYY-MM-DD"`` format.
        preprocess : bool
            If True, apply the preprocessing pipeline to the result.

        Returns
        -------
        pd.DataFrame
            Factor values with (datetime, instrument) MultiIndex.
        """
        df = self.provider.get_factor_values(expression, start, end)

        if preprocess:
            df = self.preprocessor.run(df, tradability_check=False)

        return df

    # ------------------------------------------------------------------
    # Python factor execution via sandbox
    # ------------------------------------------------------------------

    def compute_python(
        self,
        code: str,
        start: str,
        end: str,
        params: Optional[Dict] = None,
        fields: Optional[list] = None,
        preprocess: bool = False,
    ) -> pd.DataFrame:
        """Execute Python factor code in a sandboxed subprocess.

        Parameters
        ----------
        code : str
            Python snippet that receives ``df``, ``params``, ``ops`` and
            returns a ``pd.Series``.
        start, end : str
            Date range.
        params : dict, optional
            Hyper-parameters passed into the factor code.
        fields : list, optional
            Market data fields to load (default: OHLCV + amount).
        preprocess : bool
            If True, apply preprocessing to the result.

        Returns
        -------
        pd.DataFrame
            Factor values with (datetime, instrument) MultiIndex.

        Raises
        ------
        SandboxError
            On syntax error, forbidden import, timeout, or runtime error.
        """
        if params is None:
            params = {}
        if fields is None:
            fields = [
                "$open",
                "$high",
                "$low",
                "$close",
                "$volume",
                "$amount",
            ]

        market_df = self.provider.get_market_data(fields, start, end)

        # Rename columns to strip '$' prefix for factor code convenience
        rename_map = {c: c.lstrip("$") for c in market_df.columns}
        input_df = market_df.rename(columns=rename_map)

        result_series = run_factor_in_sandbox(
            code=code,
            df=input_df,
            params=params,
            timeout=self.sandbox_timeout,
        )

        result_df = result_series.to_frame(name="factor")

        if preprocess:
            result_df = self.preprocessor.run(result_df, tradability_check=False)

        return result_df
