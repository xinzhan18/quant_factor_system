"""DataProvider — Qlib D.features wrapper with parquet caching.

Provides a unified interface for fetching factor values, forward returns,
and raw market data.  All results are cached to parquet via FactorValueCache
so repeated requests are served from disk.

Usage:
    provider = DataProvider(universe=UniverseManager("csi1000"))
    df = provider.get_factor_values("Rank($close)", "2020-01-01", "2024-12-31")
    ret = provider.get_returns("2020-01-01", "2024-12-31", horizon=1)
    mkt = provider.get_market_data(["$close", "$volume"], "2020-01-01", "2024-12-31")
"""

from __future__ import annotations

import logging
from typing import Callable, List, Optional

import pandas as pd

from research.compute.cache import FactorValueCache
from research.compute.universe import UniverseManager

logger = logging.getLogger(__name__)

_qlib_initialized = False


def ensure_qlib_init(qlib_dir: str = "~/.qlib/qlib_data/cn_data_1d") -> None:
    """Lazily initialize Qlib + register custom operators.  No-op after first call."""
    global _qlib_initialized
    if _qlib_initialized:
        return
    import os
    import qlib
    from qlib.config import C

    qlib.init(provider_uri=os.path.expanduser(qlib_dir))
    C.kernels = 1

    from research.compute.operators import register_custom_operators
    register_custom_operators()

    _qlib_initialized = True
    logger.info("Qlib initialized (provider_uri=%s)", qlib_dir)


class DataProvider:
    """Fetch Qlib features with transparent parquet caching.

    Parameters
    ----------
    universe : UniverseManager, optional
        Universe resolver.  Defaults to CSI 1000.
    cache : FactorValueCache, optional
        Disk cache.  A default instance is created if omitted.
    use_cache : bool
        Set False to bypass the cache entirely (useful for debugging).
    """

    def __init__(
        self,
        universe: Optional[UniverseManager] = None,
        cache: Optional[FactorValueCache] = None,
        use_cache: bool = True,
        qlib_dir: str = "~/.qlib/qlib_data/cn_data_1d",
    ) -> None:
        ensure_qlib_init(qlib_dir)
        self.universe = universe or UniverseManager()
        self.cache = cache or FactorValueCache()
        self.use_cache = use_cache

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------

    def _fetch_cached(
        self,
        key: str,
        fetch_fn: Callable[[], pd.DataFrame],
    ) -> pd.DataFrame:
        """Check cache, call *fetch_fn* on miss, store result."""
        if self.use_cache:
            cached = self.cache.get(key)
            if cached is not None:
                return cached

        df = fetch_fn()

        if self.use_cache:
            self.cache.put(key, df)

        return df

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_factor_values(
        self,
        expression: str,
        start: str,
        end: str,
    ) -> pd.DataFrame:
        """Compute a Qlib DSL expression and return a DataFrame.

        Cache hierarchy: parquet cache → DB factor_values → Qlib compute.

        Returns a DataFrame with (datetime, instrument) MultiIndex and a
        single column named after the expression.
        """
        key = self.cache.make_key(expression, start, end)

        def _fetch() -> pd.DataFrame:
            # Try DB factor_values first (pre-computed admitted factors)
            try:
                from research.storage.factor_db import read_factor_values
                db_df = read_factor_values(expression, start, end)
                if db_df is not None and not db_df.empty:
                    logger.debug("Factor values loaded from DB for '%s'", expression[:50])
                    return db_df
            except Exception:
                pass  # DB unavailable, fall through to Qlib

            # Fall back to Qlib computation
            from qlib.data import D

            inst_dict = self.universe.resolve()
            return D.features(
                instruments=inst_dict,
                fields=[expression],
                start_time=start,
                end_time=end,
            )

        return self._fetch_cached(key, _fetch)

    def get_returns(
        self,
        start: str,
        end: str,
        horizon: int = 1,
    ) -> pd.DataFrame:
        """Compute forward returns over *horizon* trading days.

        Returns a DataFrame with (datetime, instrument) MultiIndex and
        column ``return_{horizon}d``.
        """
        expr = f"Ref($close, -{horizon}) / $close - 1"
        col_name = f"return_{horizon}d"
        key = self.cache.make_key(f"_returns_{horizon}d", start, end)

        def _fetch() -> pd.DataFrame:
            from qlib.data import D

            inst_dict = self.universe.resolve()
            df = D.features(
                instruments=inst_dict,
                fields=[expr],
                start_time=start,
                end_time=end,
            )
            df.columns = [col_name]
            return df

        return self._fetch_cached(key, _fetch)

    def get_market_data(
        self,
        fields: List[str],
        start: str,
        end: str,
    ) -> pd.DataFrame:
        """Fetch raw market data fields (e.g. ``["$close", "$volume"]``).

        Returns a DataFrame with (datetime, instrument) MultiIndex.
        """
        fields_key = ",".join(sorted(fields))
        key = self.cache.make_key(f"_market_{fields_key}", start, end)

        def _fetch() -> pd.DataFrame:
            from qlib.data import D

            inst_dict = self.universe.resolve()
            return D.features(
                instruments=inst_dict,
                fields=fields,
                start_time=start,
                end_time=end,
            )

        return self._fetch_cached(key, _fetch)
