"""FactorValueCache — parquet-backed disk cache keyed by content hash.

Key rule (refactor_plan §11):

    key = sha256(f"{expression}|{sample_policy_version}|{preprocess_version}")[:16]

Changing *any* of the three components invalidates the cache automatically.
No TTL, no automatic cleanup — stale entries are removed manually via the
``research cache`` CLI (P6). Manual control keeps the rule simple and
avoids the classic "cleanup logic has a bug and wipes live data" failure
mode documented in the old ``cleanup()`` path.

Cache files live at
``storage/cache/factor_values/{key}.parquet``.

Concurrent writes are not expected (Phase 2 runs single-process) but writes
are atomic-ish via ``to_parquet`` followed by a rename if the target exists
to prevent torn files.

Usage:

    cache = FactorValueCache(paths.factor_values_cache_dir)
    key = cache.make_key("Std($close, 20)", "v3", "p1")
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
    def make_key(
        expression: str,
        sample_policy_version: str,
        preprocess_version: str,
    ) -> str:
        """Return a 16-char hex digest of the three cache components.

        The first 16 hex chars of SHA-256 give ~64 bits of entropy — more
        than enough to avoid collisions for any realistic cache size, and
        short enough to keep filenames readable.
        """
        raw = f"{expression}|{sample_policy_version}|{preprocess_version}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

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
