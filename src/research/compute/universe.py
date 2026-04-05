"""UniverseManager — stock universe resolution for the research pipeline.

Default universe is CSI 1000 (via Qlib's ``D.instruments("csi1000")``).
Falls back to ``"all"`` if the named benchmark is not available.

Usage:
    um = UniverseManager("csi1000")
    inst_dict = um.resolve()           # Qlib instrument dict for D.features()
    stock_list = um.stock_list()       # list of instrument codes
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class UniverseManager:
    """Resolve and cache a stock universe from Qlib.

    Parameters
    ----------
    name : str
        Benchmark name recognised by Qlib (e.g. ``"csi1000"``, ``"all"``).
    """

    def __init__(self, name: str = "csi1000") -> None:
        self.name = name.lower()
        self._inst_dict: Optional[Dict] = None
        self._stock_list: Optional[List[str]] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(self) -> Dict:
        """Return the Qlib instrument dict.  Caches the result."""
        if self._inst_dict is not None:
            return self._inst_dict

        from qlib.data import D

        try:
            self._inst_dict = D.instruments(self.name)
        except Exception:
            logger.warning(
                "Universe '%s' not found in Qlib, falling back to 'all'",
                self.name,
            )
            self._inst_dict = D.instruments("all")
        return self._inst_dict

    def stock_list(
        self,
        start_time: str = "2024-06-01",
        end_time: str = "2024-06-30",
    ) -> List[str]:
        """Return a list of instrument codes in the universe.

        Fetches a minimal feature (``$close``) over a short window to
        enumerate instruments actually present in the data.
        """
        if self._stock_list is not None:
            return self._stock_list

        from qlib.data import D

        inst_dict = self.resolve()
        df = D.features(
            instruments=inst_dict,
            fields=["$close"],
            start_time=start_time,
            end_time=end_time,
        )
        self._stock_list = (
            df.index.get_level_values("instrument").unique().tolist()
        )
        return self._stock_list

    def reset(self) -> None:
        """Clear cached results so the next call re-resolves."""
        self._inst_dict = None
        self._stock_list = None
