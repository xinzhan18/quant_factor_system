"""FactorValueCache — parquet-backed disk cache for computed factor values.

Cache files use human-readable names: ``{slug}__{hash8}.parquet``
where *slug* is a sanitized excerpt of the expression and *hash8* is
an 8-char MD5 for uniqueness.

Cleanup: ``cleanup(keep_batches=2)`` removes entries older than the
last N completed batches (reads ledger to determine cutoff).

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
import re
import time
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

_DEFAULT_CACHE_DIR = Path("storage/runtime/cache/research")


def _slugify(expression: str, max_len: int = 50) -> str:
    """Turn an expression into a short filesystem-safe slug.

    Examples:
        "Mul(Corr($close,$volume,20),Std($volume,20))" → "mul_corr_close_vol_std_vol_20"
        "Ref($close,1)/$close-1"                       → "ref_close_1_close_1"
        "_returns_5d"                                   → "returns_5d"
    """
    s = expression.lower()
    # Strip $ prefixes
    s = s.replace("$", "")
    # Replace non-alphanumeric with underscore
    s = re.sub(r"[^a-z0-9]+", "_", s)
    # Collapse multiple underscores
    s = re.sub(r"_+", "_", s).strip("_")
    # Truncate
    if len(s) > max_len:
        s = s[:max_len].rstrip("_")
    return s or "expr"


class FactorValueCache:
    """Parquet disk cache with readable names and batch-aware cleanup.

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
        """Compute a readable cache key: ``{slug}__{hash8}``.

        The hash ensures uniqueness even if two expressions produce
        the same slug after sanitization.
        """
        raw = f"{expression}|{start}|{end}"
        hash8 = hashlib.md5(raw.encode()).hexdigest()[:8]
        slug = _slugify(expression)
        # Include date range in slug for clarity
        start_short = start[:4]  # year only
        end_short = end[:4]
        return f"{slug}__{start_short}_{end_short}__{hash8}"

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional[pd.DataFrame]:
        """Return cached DataFrame or None if cache miss.

        Also checks for old-style pure-hash keys for backward compat.
        """
        path = self.cache_dir / f"{key}.parquet"
        if path.exists():
            return self._read_safe(path)

        # Backward compat: try old pure-hash key
        raw_for_hash = key  # can't reverse, but check if hash file exists
        for f in self.cache_dir.glob("*.parquet"):
            if f.stem == key or f.stem.endswith(f"__{key[:8]}"):
                return self._read_safe(f)

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
        # Also clear subdirectories (e.g. risk/)
        for f in self.cache_dir.rglob("*.parquet"):
            f.unlink()
            count += 1
        return count

    def size(self) -> int:
        """Return the number of cached entries."""
        return sum(1 for _ in self.cache_dir.rglob("*.parquet"))

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def cleanup(self, keep_batches: int = 2) -> int:
        """Remove cache entries older than *keep_batches* completed batch cycles.

        Reads the ledger to find the timestamp of the Nth-last completed
        batch, then deletes files with mtime before that.

        Falls back to age-based cleanup (14 days) if ledger is unavailable.

        Returns the number of files removed.
        """
        cutoff = self._compute_cutoff_time(keep_batches)
        removed = 0
        for f in self.cache_dir.rglob("*.parquet"):
            if f.stat().st_mtime < cutoff:
                f.unlink()
                removed += 1
                logger.debug("Cache cleanup: removed %s", f.name)
        if removed:
            logger.info("Cache cleanup: removed %d stale entries", removed)
        return removed

    @staticmethod
    def _compute_cutoff_time(keep_batches: int) -> float:
        """Determine the mtime cutoff from ledger batch history."""
        try:
            import yaml
            ledger_path = Path("storage/governance/ledger.yaml")
            if not ledger_path.exists():
                # Fallback: 14 days ago
                return time.time() - 14 * 86400

            with open(ledger_path) as f:
                ledger = yaml.safe_load(f) or {}

            batches = ledger.get("batch_usage", {}).get("batches", [])
            # Filter to completed/judged batches
            completed = [
                b for b in batches
                if b.get("phase") in ("judged", "completed")
            ]

            if len(completed) <= keep_batches:
                # Not enough history, don't delete anything
                return 0.0

            # The cutoff is "before the Nth-last batch was created"
            # Use batch_id ordering as proxy for time
            completed_sorted = sorted(completed, key=lambda b: b.get("batch_id", ""))
            cutoff_batch = completed_sorted[-(keep_batches + 1)]
            # Parse batch creation from validation_range end date as time proxy
            val_range = cutoff_batch.get("validation_range", [])
            if val_range:
                from datetime import datetime
                dt = datetime.strptime(val_range[-1], "%Y-%m-%d")
                return dt.timestamp()

            # Fallback: 14 days ago
            return time.time() - 14 * 86400

        except Exception:
            # Any failure: fallback to 14 days
            return time.time() - 14 * 86400

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _read_safe(path: Path) -> Optional[pd.DataFrame]:
        try:
            return pd.read_parquet(path)
        except Exception:
            logger.warning("Corrupt cache entry %s, removing", path.name)
            path.unlink(missing_ok=True)
            return None
