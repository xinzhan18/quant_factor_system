"""FactorEngine -- DSL and Python factor execution.

Combines Qlib expression-based computation (DSL) with file-based
Python factor execution into a single interface.

Usage:
    engine = FactorEngine(provider=DataProvider(), preprocessor=Preprocessor())

    # DSL expression
    result = engine.compute_dsl("Rank($close)", "2020-01-01", "2024-12-31")

    # Python factor file
    result = engine.compute_python(
        "storage/factors/python/my_factor.py",
        start="2020-01-01",
        end="2024-12-31",
        params={"period": 20},
    )
"""

from __future__ import annotations

import importlib.util
import logging
from typing import Dict, List, Optional

import pandas as pd

from research.compute.data_provider import DataProvider
from research.compute.preprocess import Preprocessor

logger = logging.getLogger(__name__)

DEFAULT_FIELDS: List[str] = [
    "$open", "$high", "$low", "$close", "$volume", "$amount",
]


class FactorEngine:
    """Unified factor computation for DSL expressions and Python files.

    Parameters
    ----------
    provider : DataProvider, optional
        Data provider for Qlib features.  Created with defaults if omitted.
    preprocessor : Preprocessor, optional
        Preprocessing pipeline.  Created with defaults if omitted.
    """

    def __init__(
        self,
        provider: Optional[DataProvider] = None,
        preprocessor: Optional[Preprocessor] = None,
    ) -> None:
        self.provider = provider or DataProvider()
        self.preprocessor = preprocessor or Preprocessor()

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

        Returns DataFrame with (datetime, instrument) MultiIndex.
        """
        df = self.provider.get_factor_values(expression, start, end)

        if preprocess:
            df = self.preprocessor.run(df, tradability_check=False)

        return df

    # ------------------------------------------------------------------
    # Python factor execution via .py file
    # ------------------------------------------------------------------

    def compute_python(
        self,
        module_path: str,
        start: str,
        end: str,
        params: Optional[Dict] = None,
        fields: Optional[list] = None,
        preprocess: bool = False,
    ) -> pd.DataFrame:
        """Execute a Python factor .py file.

        The file must define a ``compute(df, params)`` function that
        returns a ``pd.Series`` with the same MultiIndex as *df*.

        Parameters
        ----------
        module_path : str
            Path to the .py file.
        start, end : str
            Date range.
        params : dict, optional
            Hyper-parameters passed into the factor's compute().
        fields : list, optional
            Market data fields to load (default: OHLCV + amount).
        preprocess : bool
            If True, apply preprocessing to the result.

        Returns
        -------
        pd.DataFrame
            Factor values with (datetime, instrument) MultiIndex.
        """
        market_df = self.provider.get_market_data(fields or DEFAULT_FIELDS, start, end)
        input_df = market_df.rename(columns={c: c.lstrip("$") for c in market_df.columns})

        # Dynamic import of the factor module
        spec = importlib.util.spec_from_file_location("factor_module", module_path)
        if spec is None or spec.loader is None:
            raise FileNotFoundError(f"Cannot load factor module: {module_path}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        if not hasattr(mod, "compute"):
            raise AttributeError(f"Factor module {module_path} must define a compute(df, params) function")

        result_series = mod.compute(input_df, params or {})

        if not isinstance(result_series, pd.Series):
            raise TypeError(
                f"compute() must return pd.Series, got {type(result_series).__name__}"
            )

        result_df = result_series.to_frame(name="factor")

        if preprocess:
            result_df = self.preprocessor.run(result_df, tradability_check=False)

        return result_df
