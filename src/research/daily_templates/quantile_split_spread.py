"""Rolling quantile split spread template."""

from __future__ import annotations

import numpy as np
import pandas as pd

from research.daily_templates.expression import evaluate_expression


def run(df: pd.DataFrame, params: dict) -> pd.Series:
    """Compute top/bottom rolling quantile spread.

    For each instrument and date, look back ``window`` daily observations,
    rank the window by ``sorter``, compute the mean of ``value`` in the top
    and bottom quantile slices, then return ``top_mean - bottom_mean``.
    """
    window = int(params.get("window", 20))
    top_q = float(params.get("top_quantile", 0.25))
    bottom_q = float(params.get("bottom_quantile", 0.25))
    min_count = int(params.get("min_count", max(1, int(window * min(top_q, bottom_q)))))
    output = params.get("output", "top_mean_minus_bottom_mean")
    if window <= 0:
        raise ValueError("window must be positive")
    if not (0 < top_q <= 1 and 0 < bottom_q <= 1):
        raise ValueError("top_quantile and bottom_quantile must be in (0, 1]")
    if output not in {"top_mean_minus_bottom_mean", "bottom_mean_minus_top_mean"}:
        raise ValueError(f"unsupported output: {output}")

    value = evaluate_expression(params["value"], df)
    sorter = evaluate_expression(params["sorter"], df)
    panel = pd.DataFrame({"value": value, "sorter": sorter}).sort_index()

    parts: list[pd.Series] = []
    for _, group in panel.groupby(level=-1, sort=False):
        parts.append(
            _run_one_instrument(
                group["value"],
                group["sorter"],
                window=window,
                top_q=top_q,
                bottom_q=bottom_q,
                min_count=min_count,
                reverse=(output == "bottom_mean_minus_top_mean"),
            )
        )
    return pd.concat(parts).sort_index().rename("value")


def _run_one_instrument(
    value: pd.Series,
    sorter: pd.Series,
    *,
    window: int,
    top_q: float,
    bottom_q: float,
    min_count: int,
    reverse: bool,
) -> pd.Series:
    out = pd.Series(np.nan, index=value.index, dtype=float)
    v = value.to_numpy(dtype=float)
    s = sorter.to_numpy(dtype=float)
    n = len(v)
    if n < window:
        return out

    for pos in range(window - 1, n):
        lo = pos - window + 1
        v_win = v[lo : pos + 1]
        s_win = s[lo : pos + 1]
        valid = np.isfinite(v_win) & np.isfinite(s_win)
        if int(valid.sum()) < min_count:
            continue
        v_ok = v_win[valid]
        s_ok = s_win[valid]
        top_threshold = np.nanquantile(s_ok, 1.0 - top_q)
        bottom_threshold = np.nanquantile(s_ok, bottom_q)
        top_values = v_ok[s_ok >= top_threshold]
        bottom_values = v_ok[s_ok <= bottom_threshold]
        if len(top_values) < min_count or len(bottom_values) < min_count:
            continue
        top_mean = float(np.nanmean(top_values))
        bottom_mean = float(np.nanmean(bottom_values))
        out.iloc[pos] = bottom_mean - top_mean if reverse else top_mean - bottom_mean
    return out
