"""Support-window stress checks and sign-flip detection.

Pure vectorized functions. No I/O, no Qlib.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from core.factor_stats import daily_cross_sectional_ic


def check_support_windows(
    factor_values: pd.DataFrame,
    forward_returns: pd.DataFrame,
    primary_sign: float,
    windows: List[Dict[str, Any]],
    min_obs: int = 30,
) -> Dict[str, Any]:
    """Run IC checks on support validation windows and detect sign flips.

    Args:
        factor_values: Flat DataFrame [time, symbol, value].
        forward_returns: Flat DataFrame [time, symbol, value].
        primary_sign: Sign of IC from the primary validation window
            (+1 or -1).  Used as reference for flip detection.
        windows: List of dicts, each with keys ``window_id`` and ``range``
            (a 2-element list/tuple of date strings [start, end]).
        min_obs: Minimum cross-sectional observations per day.

    Returns:
        Dict with ``checks`` (per-window results) and ``warning``
        (none / single_flip / repeated_flip).
    """
    checks: List[Dict[str, Any]] = []
    n_flips = 0

    for win in windows:
        wid = win["window_id"]
        start, end = win["range"][0], win["range"][1]

        fv = factor_values.loc[
            (factor_values["time"] >= pd.Timestamp(start))
            & (factor_values["time"] <= pd.Timestamp(end))
        ]
        fr = forward_returns.loc[
            (forward_returns["time"] >= pd.Timestamp(start))
            & (forward_returns["time"] <= pd.Timestamp(end))
        ]

        ic_series = daily_cross_sectional_ic(fv, fr, min_obs=min_obs)
        if ic_series.empty:
            checks.append({
                "window_id": wid,
                "ic_mean_support": np.nan,
                "sign_consistent": False,
            })
            continue

        ic_mean = float(ic_series.mean())
        sign_ok = bool(np.sign(ic_mean) == np.sign(primary_sign)) if abs(ic_mean) > 1e-10 else False
        if not sign_ok:
            n_flips += 1

        checks.append({
            "window_id": wid,
            "ic_mean_support": round(ic_mean, 6),
            "sign_consistent": sign_ok,
        })

    # Warning level
    if n_flips == 0:
        warning = "none"
    elif n_flips == 1:
        warning = "single_flip"
    else:
        warning = "repeated_flip"

    return {"checks": checks, "warning": warning}
