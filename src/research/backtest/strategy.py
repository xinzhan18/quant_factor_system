"""Strategy ABC + concrete TopKLongOnly and QuintilePortfolio.

Both strategies treat NaN factor values as ineligible — symbols with NaN are
excluded from the candidate pool. The cross-sectional rank is computed on the
non-NaN subset only.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd


class Strategy(ABC):
    @abstractmethod
    def target_weights(
        self,
        decision_date: date,
        factor_values: pd.Series,
        universe: set[str],
        price_view: Any,
    ) -> pd.Series:
        """Return a Series indexed by symbol with weights summing to ≤ 1.0."""


@dataclass(frozen=True)
class TopKLongOnly(Strategy):
    holdings_n: int
    max_single_weight: float = 1.0

    def target_weights(self, decision_date, factor_values, universe, price_view):
        eligible = factor_values.dropna()
        eligible = eligible[eligible.index.isin(universe)]
        if eligible.empty:
            return pd.Series(dtype=float)
        ranked = eligible.sort_values(ascending=False)
        top = ranked.head(self.holdings_n)
        equal_weight = 1.0 / len(top)
        weight = min(equal_weight, self.max_single_weight)
        return pd.Series(weight, index=top.index)


@dataclass(frozen=True)
class QuintilePortfolio(Strategy):
    """Five sub-portfolios indexed q=0 (lowest factor) … q=4 (highest).

    The default :meth:`target_weights` returns the top quintile (q=4) so the
    class can be used as a vanilla long-only strategy if needed; the engine
    typically calls :meth:`target_for_quintile` once per q.
    """

    n_quintiles: int = 5

    def target_weights(self, decision_date, factor_values, universe, price_view):
        return self.target_for_quintile(
            self.n_quintiles - 1, factor_values, universe, price_view
        )

    def target_for_quintile(
        self,
        q: int,
        factor_values: pd.Series,
        universe: set[str],
        price_view: Any,
    ) -> pd.Series:
        if not (0 <= q < self.n_quintiles):
            raise ValueError(f"q must be in [0, {self.n_quintiles}); got {q}")
        eligible = factor_values.dropna()
        eligible = eligible[eligible.index.isin(universe)]
        if eligible.empty:
            return pd.Series(dtype=float)
        ranked = eligible.sort_values(ascending=False)
        n = len(ranked)
        size = n // self.n_quintiles
        if size == 0:
            return pd.Series(dtype=float)
        # In descending sort: top of array = highest factor (q = n_quintiles - 1).
        slot_from_top = self.n_quintiles - 1 - q
        start = slot_from_top * size
        end = start + size
        sliced = ranked.iloc[start:end]
        return pd.Series(1.0 / len(sliced), index=sliced.index)
