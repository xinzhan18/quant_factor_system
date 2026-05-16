"""Benchmark loader — equal-weight equity curves from index_constituents.

For a given index (csi1000 / csi300) and date range:
- read ``(time, symbol)`` membership from ``index_constituents``
- join market_daily parquet's ``$close`` to compute daily symbol returns
- per-date equal-weight mean of constituent returns → daily benchmark return
- cumulative compound starting at ``initial_capital`` → equity series

Vectorised: NO per-date or per-symbol loops; all groupby / unstack / cumprod.

If DB / market parquet missing, returns an empty Series and lets the caller
draw a placeholder.
"""
from __future__ import annotations

import logging
import os
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _db_dsn() -> dict:
    return dict(
        host=os.environ.get("TIMESCALE_HOST", "localhost"),
        port=int(os.environ.get("TIMESCALE_PORT", 5432)),
        dbname=os.environ.get("TIMESCALE_DB", "quant_data"),
        user=os.environ.get("TIMESCALE_USER", "postgres"),
        password=os.environ.get("TIMESCALE_PASSWORD", "postgres"),
    )


_MARKET_QFQ = Path("storage/cache/market_daily.parquet")
_MARKET_HFQ = Path("storage/cache/market_daily_hfq.parquet")


def _resolve_market_path(end: date) -> Path | None:
    """Pick qfq (uses ``$close``) or hfq (uses ``close``) depending on which
    covers the window. Returns None if neither exists or both are pre-2024.
    """
    # hfq usually has more recent data (extended on each resync). Try it
    # first for windows past 2023-12-31; fall back to qfq otherwise.
    if pd.Timestamp(end) > pd.Timestamp("2023-12-31") and _MARKET_HFQ.exists():
        return _MARKET_HFQ
    if _MARKET_QFQ.exists():
        return _MARKET_QFQ
    if _MARKET_HFQ.exists():
        return _MARKET_HFQ
    return None


def _read_close_panel(path: Path) -> pd.DataFrame | None:
    """Return single-column ``close`` panel with MultiIndex (time, symbol),
    handling either ``$close`` (qfq parquet) or ``close`` (hfq parquet).
    """
    try:
        # Try Qlib-style $close first
        return pd.read_parquet(path, columns=["$close"]).rename(
            columns={"$close": "close"}
        )
    except Exception:  # noqa: BLE001
        try:
            return pd.read_parquet(path, columns=["close"])
        except Exception as exc:  # noqa: BLE001
            logger.warning("benchmark: cannot read close from %s: %s", path, exc)
            return None


def load_benchmark_equity(
    start: date,
    end: date,
    kind: str = "csi1000",
    initial_capital: float = 1_000_000.0,
    market_parquet: Path | None = None,
) -> pd.Series:
    """Return DatetimeIndex equity series for an equal-weight index.

    Parameters
    ----------
    start, end
        Inclusive date range (Python ``date``).
    kind
        ``index_name`` value in ``index_constituents`` table.
    initial_capital
        Starting value of the equity series (first day).
    market_parquet
        Override path to the market_daily parquet cache (used in tests).

    Returns empty Series with DatetimeIndex if data unavailable.
    """
    market_path = market_parquet or _resolve_market_path(end)
    if market_path is None or not market_path.exists():
        logger.warning("benchmark: market_daily parquet missing (resolved=%s)", market_path)
        return pd.Series(dtype=float)

    # 1. Load membership from DB
    try:
        import psycopg2

        conn = psycopg2.connect(**_db_dsn())
        try:
            df_mem = pd.read_sql(
                "SELECT time::date AS time, symbol FROM index_constituents "
                "WHERE index_name = %s AND time >= %s AND time <= %s",
                conn,
                params=(kind, start, end),
            )
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        logger.warning("benchmark: index_constituents read failed (%s)", exc)
        return pd.Series(dtype=float)

    if df_mem.empty:
        logger.warning("benchmark: %s has no constituents in [%s, %s]", kind, start, end)
        return pd.Series(dtype=float)

    df_mem["time"] = pd.to_datetime(df_mem["time"])

    # 2. Load close prices for the window (lookback 1 day for pct_change)
    market = _read_close_panel(market_path)
    if market is None or market.empty:
        logger.warning("benchmark: close panel empty from %s", market_path)
        return pd.Series(dtype=float)
    if not isinstance(market.index, pd.MultiIndex):
        logger.warning("benchmark: market_daily not MultiIndex — bailing out")
        return pd.Series(dtype=float)

    # Coerce datetime
    market = market.copy()
    level0 = market.index.get_level_values(0)
    if not pd.api.types.is_datetime64_any_dtype(level0):
        market.index = market.index.set_levels(pd.to_datetime(market.index.levels[0]), level=0)
    market.index.names = ["time", "symbol"]

    # Filter to window + 5 day lookback to compute first-day return
    win_start = pd.Timestamp(start) - pd.Timedelta(days=10)
    win_end = pd.Timestamp(end)
    mask = (market.index.get_level_values(0) >= win_start) & (
        market.index.get_level_values(0) <= win_end
    )
    market = market.loc[mask]

    # 3. Wide close → daily returns
    close_wide = market["close"].unstack(level=-1).sort_index()
    rets_wide = close_wide.pct_change(fill_method=None)

    # 4. Pivot membership to (time × symbol) bool mask
    df_mem["member"] = True
    mem_wide = (
        df_mem.set_index(["time", "symbol"])["member"]
        .unstack(level=-1)
        .reindex(index=rets_wide.index, columns=rets_wide.columns)
        .fillna(False)
    )

    # 5. Mask returns by membership, equal-weight mean per date
    masked = rets_wide.where(mem_wide)
    daily_ret = masked.mean(axis=1, skipna=True)

    # Restrict to backtest window
    daily_ret = daily_ret.loc[
        (daily_ret.index >= pd.Timestamp(start))
        & (daily_ret.index <= pd.Timestamp(end))
    ]
    if daily_ret.empty:
        return pd.Series(dtype=float)

    # 6. Cumulative compound from initial_capital; first day uses 0% return
    daily_ret = daily_ret.fillna(0.0)
    daily_ret.iloc[0] = 0.0
    equity = initial_capital * (1.0 + daily_ret).cumprod()
    equity.name = f"benchmark_{kind}_eq"
    return equity


def compute_benchmark_metrics(
    strategy_equity: pd.Series,
    benchmark_equity: pd.Series,
) -> dict:
    """Compute excess return / IR / tracking error / alpha / beta.

    All series assumed daily; annualised by ×252. Returns dict with float
    values or zeros if benchmark missing.
    """
    if benchmark_equity is None or benchmark_equity.empty or strategy_equity.empty:
        return dict(
            excess_return_ann=0.0,
            info_ratio=0.0,
            tracking_error_ann=0.0,
            alpha=0.0,
            beta=0.0,
            available=False,
        )

    # Align indices (both to DatetimeIndex)
    s = strategy_equity.copy()
    b = benchmark_equity.copy()
    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index)
    if not isinstance(b.index, pd.DatetimeIndex):
        b.index = pd.to_datetime(b.index)
    s_ret = s.pct_change().dropna()
    b_ret = b.pct_change().dropna()
    joined = pd.concat({"s": s_ret, "b": b_ret}, axis=1).dropna()
    if joined.empty or len(joined) < 2:
        return dict(
            excess_return_ann=0.0,
            info_ratio=0.0,
            tracking_error_ann=0.0,
            alpha=0.0,
            beta=0.0,
            available=False,
        )

    diff = joined["s"] - joined["b"]
    ex_ann = float(diff.mean() * 252)
    te_ann = float(diff.std() * (252 ** 0.5))
    ir = ex_ann / te_ann if te_ann > 0 else 0.0

    # OLS alpha/beta (daily, annualised alpha)
    b_arr = joined["b"].values
    s_arr = joined["s"].values
    var_b = float(np.var(b_arr, ddof=1))
    if var_b > 0:
        cov_sb = float(np.cov(s_arr, b_arr, ddof=1)[0, 1])
        beta = cov_sb / var_b
    else:
        beta = 0.0
    alpha_daily = float(np.mean(s_arr) - beta * np.mean(b_arr))
    alpha_ann = alpha_daily * 252

    return dict(
        excess_return_ann=ex_ann,
        info_ratio=float(ir),
        tracking_error_ann=te_ann,
        alpha=float(alpha_ann),
        beta=float(beta),
        available=True,
    )
