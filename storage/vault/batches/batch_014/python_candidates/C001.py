"""
C001 — Pure vol_20d Barra Style as Alpha Signal

Tests probe #2 from direction.md: "纯 vol_20d 信号 vs Barra residual 哪个 IC 更高？"
Reads vol_20d directly from Barra cache as the factor value (no residualization).
Baseline: if pure vol_20d carries higher IC than F004 residual, then "alpha" is
just a Barra style; if F004 wins, residualization is the value-add.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

REQUIRED_FIELDS = ["$close"]
VECTORIZED = True

BARRA_CACHE = "storage/cache/barra_factors.parquet"


def compute(df: pd.DataFrame) -> pd.Series:
    barra: pd.DataFrame = pd.read_parquet(BARRA_CACHE)

    ret = df["$close"].unstack("instrument")
    forward_idx = ret.shift(-1).stack("instrument").index
    forward_idx.names = ["datetime", "instrument"]

    common_idx = forward_idx.intersection(barra.index)
    vol = barra.loc[common_idx, "vol_20d"]

    return vol.reindex(forward_idx)
