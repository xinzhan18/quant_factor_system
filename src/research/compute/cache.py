"""FactorValueCache — parquet-backed disk cache for computed factor values.

Keys are derived from an MD5 hash of the factor expression (or code) plus
the date range, so identical computations are served from disk on subsequent
runs.

Cache directory layout::

    <cache_dir>/
      <hex_hash>.parquet       # one file per unique (expression, start, end)

Usage:
    cache = FactorValueCache()
    key = cache.make_key("Rank($close)", "2020-01-01", "2024-12-31")
    df = cache.get(key)
    if df is None:
        df = expensive_compute(...)
        cache.put(key, df)
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

_DEFAULT_CACHE_DIR = Path("storage/runtime/cache/research")


class FactorValueCache:
    """Parquet disk cache keyed by MD5 hash.

    Parameters
    ----------
    cache_dir : str or Path
        Directory for cached parquet files.
    """

    def __init__(self, cache_dir: Optional[str] = None) -> None:
        self.cache_dir = Path(cache_dir) if cache_dir else _DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Key generation
    # ------------------------------------------------------------------

    @staticmethod
    def make_key(expression: str, start: str, end: str) -> str:
        """Compute a deterministic MD5 hex key for the given parameters."""
        raw = f"{expression}|{start}|{end}"
        return hashlib.md5(raw.encode()).hexdigest()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional[pd.DataFrame]:
        """Return cached DataFrame or None if cache miss."""
        path = self.cache_dir / f"{key}.parquet"
        if not path.exists():
            return None
        try:
            return pd.read_parquet(path)
        except Exception:
            logger.warning("Corrupt cache entry %s, removing", key)
            path.unlink(missing_ok=True)
            return None

    def put(self, key: str, df: pd.DataFrame) -> None:
        """Store a DataFrame to the cache."""
        path = self.cache_dir / f"{key}.parquet"
        df.to_parquet(path)

    def invalidate(self, key: str) -> bool:
        """Remove a single cache entry.  Returns True if it existed."""
        path = self.cache_dir / f"{key}.parquet"
        if path.exists():
            path.unlink()
            return True
        return False

    def clear(self) -> int:
        """Remove all cached entries.  Returns the number of files removed."""
        count = 0
        for f in self.cache_dir.glob("*.parquet"):
            f.unlink()
            count += 1
        return count

    def size(self) -> int:
        """Return the number of cached entries."""
        return sum(1 for _ in self.cache_dir.glob("*.parquet"))
