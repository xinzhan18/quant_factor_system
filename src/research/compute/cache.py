"""FactorValueCache — parquet-backed disk cache keyed by expression hash.

    key = sha256(expression)[:16]

Cache files live at ``storage/cache/factor_values/{key}.parquet``.

No TTL, no automatic cleanup — stale entries are removed manually via the
``research cache`` CLI. If upstream policy (sample range, preprocessing)
changes, the user clears the cache explicitly. Manual control keeps the
rule simple and avoids a cleanup-logic bug wiping live data.

Concurrent writes are not expected (Phase 2 runs single-process) but writes
are atomic via ``to_parquet`` → ``os.replace`` to prevent torn files.

Usage:

    cache = FactorValueCache(paths.factor_values_cache_dir)
    key = cache.make_key("Std($close, 20)")
    df = cache.get(key)
    if df is None:
        df = expensive_compute(...)
        cache.put(key, df)
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class FactorValueCache:
    """Content-addressed parquet cache for factor values.

    Parameters
    ----------
    cache_dir
        Directory where ``{key}.parquet`` files live. Created on demand.
    """

    def __init__(self, cache_dir: str | Path) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Key generation
    # ------------------------------------------------------------------

    @staticmethod
    def make_key(expression: str) -> str:
        """Return a 16-char hex digest of the expression.

        The first 16 hex chars of SHA-256 give ~64 bits of entropy — more
        than enough to avoid collisions for any realistic cache size, and
        short enough to keep filenames readable.
        """
        return hashlib.sha256(expression.encode("utf-8")).hexdigest()[:16]

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def _path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.parquet"

    def contains(self, key: str) -> bool:
        return self._path(key).exists()

    def get(self, key: str) -> pd.DataFrame | None:
        """Load a cached DataFrame, or ``None`` on miss / corrupt file.

        Corrupt entries are silently removed so the next ``put`` can
        succeed without manual intervention.
        """
        path = self._path(key)
        if not path.exists():
            return None
        try:
            return pd.read_parquet(path)
        except Exception as exc:  # pragma: no cover - hard to trigger
            logger.warning("cache: corrupt entry %s removed (%s)", path.name, exc)
            try:
                path.unlink()
            except OSError:
                pass
            return None

    def get_slice(
        self,
        key: str,
        start: str | pd.Timestamp,
        end: str | pd.Timestamp,
    ) -> pd.DataFrame | None:
        """Load cache entry and slice to the ``[start, end]`` date window.

        Returns ``None`` only on true miss (file doesn't exist or is
        corrupt). An empty slice is a valid cached result — callers should
        treat empty-but-not-None as "cache hit, no data in window".

        Assumes the DataFrame has a MultiIndex whose first level is a
        datetime-like axis. If the first level isn't a DatetimeIndex it
        falls back to the full frame.
        """
        full = self.get(key)
        if full is None:
            return None
        if not isinstance(full.index, pd.MultiIndex):
            return full
        level0 = full.index.get_level_values(0)
        if not pd.api.types.is_datetime64_any_dtype(level0):
            return full
        start_ts = pd.Timestamp(start)
        end_ts = pd.Timestamp(end)
        mask = (level0 >= start_ts) & (level0 <= end_ts)
        return full.loc[mask]

    def put(self, key: str, df: pd.DataFrame) -> None:
        """Write a DataFrame to the cache.

        Writes to a sibling temp file and atomically ``os.replace`` onto
        the target so a crash mid-write cannot leave a half-written parquet.
        """
        target = self._path(key)
        tmp = target.with_suffix(".parquet.tmp")
        try:
            df.to_parquet(tmp)
            os.replace(tmp, target)
        except BaseException:
            if tmp.exists():
                try:
                    tmp.unlink()
                except OSError:
                    pass
            raise

    def invalidate(self, key: str) -> bool:
        """Remove a single entry. Returns ``True`` if it existed."""
        path = self._path(key)
        if not path.exists():
            return False
        path.unlink()
        return True

    def clear(self) -> int:
        """Remove every cached entry under ``cache_dir``. Returns count."""
        count = 0
        for f in self.cache_dir.glob("*.parquet"):
            f.unlink()
            count += 1
        return count

    def size(self) -> int:
        """Return the number of parquet files currently in the cache."""
        return sum(1 for _ in self.cache_dir.glob("*.parquet"))
