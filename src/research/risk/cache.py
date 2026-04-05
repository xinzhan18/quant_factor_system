"""Risk-specific cache for style factor matrix.

Uses FactorValueCache with a dedicated subdirectory and universe-aware keys.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from research.compute.cache import FactorValueCache
from .constants import CACHE_SUBDIR, STYLE_VERSION


class RiskCache:
    """Cache the style factor matrix to parquet.

    Key format includes style version and universe ID to prevent
    cross-universe cache collisions.
    """

    def __init__(self, base_cache: Optional[FactorValueCache] = None) -> None:
        if base_cache is not None:
            self._cache = base_cache
        else:
            from pathlib import Path
            risk_cache_dir = str(Path("storage/runtime/cache/research") / CACHE_SUBDIR)
            self._cache = FactorValueCache(cache_dir=risk_cache_dir)

    def _make_key(self, universe_name: str, start: str, end: str) -> str:
        return self._cache.make_key(
            f"_barra_{STYLE_VERSION}_{universe_name}", start, end
        )

    def get_style_matrix(
        self, universe_name: str, start: str, end: str
    ) -> Optional[pd.DataFrame]:
        key = self._make_key(universe_name, start, end)
        return self._cache.get(key)

    def put_style_matrix(
        self, universe_name: str, start: str, end: str, matrix: pd.DataFrame
    ) -> None:
        key = self._make_key(universe_name, start, end)
        self._cache.put(key, matrix)
