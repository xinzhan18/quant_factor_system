"""Generate golden reference fixtures for P1 vectorized compute tests.

One-shot script. Run once with the OLD (pre-P1) pure-function math modules,
commits the output parquet/yaml files to git, and then P1 vectorized code
must match them within 1e-6.

Usage:
    PYTHONPATH=src python3 tests/research/compute/_fixtures/generate_golden.py

Design:
* Deterministic synthetic data — seeded RNG, no DB / Qlib / network.
* 600 trading days × 200 symbols = small enough to be fast (<5s),
  large enough to exercise the code paths (IC significance, quintile
  boundaries, stability splits, Barra OLS per-day).
* Dates are synthetic (business-day range starting 2018-01-02). Train/val
  split roughly 60/40 so split_stability has 4 × 60d chunks in val.
* Factor = deterministic signal + noise, so IC is nonzero and stable.
* Returns = alpha × factor + market + idio noise, so effect_strength is
  real but not extreme.
* Library signals = factor variants (correlated / independent), used to
  test pairwise redundancy bucket boundaries.
* Style matrix = 7 Barra styles built from the same market + noise, so
  exposures are non-trivial but not perfectly collinear.

This script imports from the CURRENT (soon-to-be-legacy) src/core and
src/research/{stats,redundancy,feasibility,risk} — those are pure-function
modules per refactor_plan's "档 A / 档 B" classification and must NOT
import StoragePaths (verified via grep before writing this script).
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

# Suppress spurious BLAS strided-matmul FP flag warnings on some numpy builds.
# The Barra OLS path in src/research/risk/exposures.py emits these on every
# lstsq call even when inputs are well-conditioned and outputs are finite
# (verified empirically: cond(X)=3.46, |beta|<0.12, |X@beta|<0.3).
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*matmul.*")

# Resolve src/ for imports without needing PYTHONPATH
REPO_ROOT = Path(__file__).resolve().parents[4]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Old pure-function math (档 A / 档 B source references)
from core.factor_stats import (  # noqa: E402
    daily_cross_sectional_ic,
    ic_summary,
    monotonicity,
    quintile_returns,
)
from research.feasibility.concentration import (  # noqa: E402
    compute_small_cap_concentration,
    compute_tail_concentration,
)
from research.feasibility.liquidity import compute_liquidity_coverage  # noqa: E402
from research.feasibility.proxy_portfolio import build_proxy_portfolio  # noqa: E402
from research.feasibility.stress import (  # noqa: E402
    compute_half_life,
    compute_holding_period_proxy,
    compute_rebalance_stress,
)
from research.redundancy.pairwise import compute_pairwise_redundancy  # noqa: E402
from research.risk.exposures import compute_barra_exposures  # noqa: E402
from research.stats.stability import compute_split_stability  # noqa: E402
from research.stats.support_windows import check_support_windows  # noqa: E402


# Configuration — any change invalidates all golden files
SEED = 20260412
N_DAYS = 600
N_SYMBOLS = 200
START_DATE = "2018-01-02"
TRAIN_END_IDX = 359   # days 0..359 are train (360 days)
VAL_END_IDX = 599     # days 360..599 are validation (240 days)

FIXTURES_ROOT = Path(__file__).parent
INPUTS_DIR = FIXTURES_ROOT / "inputs"
OUTPUTS_DIR = FIXTURES_ROOT / "outputs"


def _mkdirs() -> None:
    INPUTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def _synthetic_panel(seed: int) -> dict[str, Any]:
    """Build all synthetic inputs in one place for reproducibility.

    Returns dict of DataFrames with consistent (time, symbol) shape.
    """
    rng = np.random.default_rng(seed)

    dates = pd.bdate_range(start=START_DATE, periods=N_DAYS)
    symbols = [f"SYM{i:04d}" for i in range(N_SYMBOLS)]

    # MultiIndex for wide-style inputs
    mi = pd.MultiIndex.from_product([dates, symbols], names=["datetime", "instrument"])

    # Factor value: AR(1) per symbol, shared market component.
    # phi=0.5 keeps the process tightly bounded (steady-state std ≈ 0.58)
    # so per-date OLS in compute_barra_exposures never overflows.
    market = rng.standard_normal(N_DAYS) * 0.3
    base = np.zeros((N_DAYS, N_SYMBOLS))
    phi = 0.5
    for t in range(N_DAYS):
        eps = rng.standard_normal(N_SYMBOLS) * 0.5
        if t == 0:
            base[t] = eps + market[t] * 0.2
        else:
            base[t] = phi * base[t - 1] + eps + market[t] * 0.2
    factor_wide = pd.DataFrame(base, index=dates, columns=symbols)
    factor_wide.index.name = "time"

    # Forward returns: alpha × factor + market shock + idio noise
    alpha = 0.003
    market_shock = rng.standard_normal(N_DAYS)[:, None] * 0.015
    idio = rng.standard_normal((N_DAYS, N_SYMBOLS)) * 0.02
    ret_wide = factor_wide.values * alpha + market_shock + idio
    returns_wide = pd.DataFrame(ret_wide, index=dates, columns=symbols)
    returns_wide.index.name = "time"

    # Flat [time, symbol, value] for factor_stats functions
    factor_flat = factor_wide.stack().rename("value").reset_index()
    factor_flat.columns = ["time", "symbol", "value"]
    returns_flat = returns_wide.stack().rename("value").reset_index()
    returns_flat.columns = ["time", "symbol", "value"]

    # Library factors for redundancy tests:
    #   F001: copy of factor (perfect corr ≈ 1.0)
    #   F002: 0.3 × factor + noise (medium corr)
    #   F003: independent random walk (≈0 corr)
    f001 = factor_wide.copy()
    f002 = factor_wide * 0.3 + rng.standard_normal(factor_wide.shape) * 0.4
    f003 = pd.DataFrame(
        rng.standard_normal(factor_wide.shape), index=factor_wide.index, columns=symbols
    ).cumsum()

    def _wide_to_mi(w: pd.DataFrame, col_name: str = "value") -> pd.DataFrame:
        s = w.stack()
        s.index.names = ["datetime", "instrument"]
        return s.to_frame(col_name)

    library_mi = {
        "F001": _wide_to_mi(f001),
        "F002": _wide_to_mi(f002),
        "F003": _wide_to_mi(f003),
    }
    candidate_mi = _wide_to_mi(factor_wide)

    # Tradable mask: 95% tradable, random 5% gaps (stable coverage metric)
    mask_arr = rng.random((N_DAYS, N_SYMBOLS)) > 0.05
    tradable_wide = pd.DataFrame(mask_arr, index=dates, columns=symbols)
    tradable_mi = _wide_to_mi(tradable_wide, col_name="tradable")

    # Amount data: lognormal around 10^8, some daily fluctuation
    amt_base = np.exp(rng.normal(18.0, 0.5, size=(N_DAYS, N_SYMBOLS)))
    amount_wide = pd.DataFrame(amt_base, index=dates, columns=symbols)
    amount_mi = _wide_to_mi(amount_wide, col_name="amount")

    # Market cap: lognormal, fairly stable per symbol
    cap_base = np.exp(rng.normal(22.0, 0.8, size=(1, N_SYMBOLS))).repeat(N_DAYS, axis=0)
    cap_wide = pd.DataFrame(cap_base, index=dates, columns=symbols)
    cap_mi = _wide_to_mi(cap_wide, col_name="market_cap")

    # Style matrix: 7 Barra styles built from INDEPENDENT random components.
    # We intentionally avoid a shared market component — if all styles share
    # the same driver, the per-date OLS design matrix becomes ill-conditioned
    # and lstsq returns huge betas that overflow X @ beta on some dates. The
    # old code silently drops those dates via `np.all(np.isfinite(resid))`,
    # which would make the golden non-reproducible by the new `pinv`-based
    # implementation. Independent styles eliminate the conditioning issue
    # entirely and give both implementations identical date coverage.
    style_names = [
        "log_circ_cap",
        "book_to_price",
        "mom_12_1",
        "str_1m",
        "vol_20d",
        "turnover_20d",
        "ep_ratio",
    ]
    style_arrays = {}
    for i, name in enumerate(style_names):
        style_arrays[name] = rng.standard_normal((N_DAYS, N_SYMBOLS)) * (
            0.3 + 0.02 * i
        )
    style_wide_per_name = {
        name: pd.DataFrame(arr, index=dates, columns=symbols)
        for name, arr in style_arrays.items()
    }
    # Combine into MultiIndex DataFrame: columns=style_names, index=(date, symbol)
    style_mi = pd.concat(
        {name: _wide_to_mi(w)["value"] for name, w in style_wide_per_name.items()},
        axis=1,
    )
    style_mi.index.names = ["datetime", "instrument"]

    # Benchmark returns (for regime stability if we include it later)
    bench_returns = pd.Series(market_shock.squeeze(), index=dates, name="ret")

    return {
        "dates": dates,
        "symbols": symbols,
        "factor_flat": factor_flat,
        "returns_flat": returns_flat,
        "candidate_mi": candidate_mi,
        "library_mi": library_mi,
        "tradable_mi": tradable_mi,
        "amount_mi": amount_mi,
        "cap_mi": cap_mi,
        "style_mi": style_mi,
        "bench_returns": bench_returns,
    }


def _dump_inputs(panel: dict[str, Any]) -> None:
    """Persist synthetic inputs as parquet for P1 tests to load."""
    panel["factor_flat"].to_parquet(INPUTS_DIR / "factor_values.parquet", index=False)
    panel["returns_flat"].to_parquet(
        INPUTS_DIR / "forward_returns.parquet", index=False
    )
    panel["candidate_mi"].to_parquet(INPUTS_DIR / "candidate_signal.parquet")
    for fid, df in panel["library_mi"].items():
        df.to_parquet(INPUTS_DIR / f"library_{fid}.parquet")
    panel["tradable_mi"].to_parquet(INPUTS_DIR / "tradable_mask.parquet")
    panel["amount_mi"].to_parquet(INPUTS_DIR / "amount_data.parquet")
    panel["cap_mi"].to_parquet(INPUTS_DIR / "market_cap_data.parquet")
    panel["style_mi"].to_parquet(INPUTS_DIR / "style_matrix.parquet")
    panel["bench_returns"].to_frame().to_parquet(INPUTS_DIR / "bench_returns.parquet")


def _compute_effect_strength(panel: dict[str, Any]) -> dict[str, Any]:
    """Split → IC train / IC val / ic_summary / quintile / mono."""
    dates = panel["dates"]
    train_mask = (panel["factor_flat"]["time"] <= dates[TRAIN_END_IDX])
    val_mask = (
        (panel["factor_flat"]["time"] > dates[TRAIN_END_IDX])
        & (panel["factor_flat"]["time"] <= dates[VAL_END_IDX])
    )
    fv_train = panel["factor_flat"][train_mask].copy()
    fr_train = panel["returns_flat"][train_mask].copy()
    fv_val = panel["factor_flat"][val_mask].copy()
    fr_val = panel["returns_flat"][val_mask].copy()

    ic_train = daily_cross_sectional_ic(fv_train, fr_train, min_obs=30)
    ic_val = daily_cross_sectional_ic(fv_val, fr_val, min_obs=30)

    train_stats = ic_summary(ic_train)
    val_stats = ic_summary(ic_val)

    qret_val, daily_ls_val = quintile_returns(
        fv_val, fr_val, n_quantiles=5, min_obs=30
    )
    mono_val = monotonicity(qret_val)

    # Persist IC series
    ic_train.rename("ic").to_frame().to_parquet(OUTPUTS_DIR / "ic_series_train.parquet")
    ic_val.rename("ic").to_frame().to_parquet(OUTPUTS_DIR / "ic_series_validation.parquet")
    pd.Series(daily_ls_val, name="ls").to_frame().to_parquet(
        OUTPUTS_DIR / "long_short_daily_validation.parquet"
    )

    return {
        "train": {
            "ic_mean": train_stats["ic_mean"],
            "ic_std": train_stats["ic_std"],
            "ic_ir": train_stats["ic_ir"],
            "ic_win_rate": train_stats["ic_win_rate"],
            "n_days": int(len(ic_train)),
        },
        "validation": {
            "ic_mean": val_stats["ic_mean"],
            "ic_std": val_stats["ic_std"],
            "ic_ir": val_stats["ic_ir"],
            "ic_win_rate": val_stats["ic_win_rate"],
            "n_days": int(len(ic_val)),
        },
        "quintile_returns_validation": {k: float(v) for k, v in qret_val.items()},
        "monotonicity_validation": float(mono_val),
        "long_short_mean_validation": float(np.nanmean(daily_ls_val))
        if daily_ls_val
        else float("nan"),
        "long_short_n_days": int(len(daily_ls_val)),
    }


def _compute_stability(panel: dict[str, Any]) -> dict[str, Any]:
    """split_stability on the validation IC series + support-window flip check."""
    ic_val_df = pd.read_parquet(OUTPUTS_DIR / "ic_series_validation.parquet")
    ic_val = ic_val_df["ic"]

    split = compute_split_stability(ic_val, n_splits=4, min_days=40)

    # Support windows — split validation into two halves
    dates = panel["dates"]
    primary_mean = float(ic_val.mean())
    primary_sign = 1.0 if primary_mean > 0 else -1.0

    windows = [
        {
            "window_id": "val_first_half",
            "range": [str(dates[360].date()), str(dates[479].date())],
        },
        {
            "window_id": "val_second_half",
            "range": [str(dates[480].date()), str(dates[VAL_END_IDX].date())],
        },
    ]
    support = check_support_windows(
        panel["factor_flat"],
        panel["returns_flat"],
        primary_sign=primary_sign,
        windows=windows,
        min_obs=30,
    )

    return {
        "split_stability": {
            "split_ic_means": [float(x) for x in split["split_ic_means"]],
            "sign_consistency": float(split["sign_consistency"])
            if not pd.isna(split["sign_consistency"])
            else None,
            "dispersion": float(split["dispersion"])
            if not pd.isna(split["dispersion"])
            else None,
            "bucket": split["bucket"],
            "n_splits": int(split["n_splits"]),
        },
        "support_windows": {
            "checks": [
                {
                    "window_id": c["window_id"],
                    "ic_mean_support": (
                        float(c["ic_mean_support"])
                        if not pd.isna(c["ic_mean_support"])
                        else None
                    ),
                    "sign_consistent": bool(c["sign_consistent"]),
                }
                for c in support["checks"]
            ],
            "warning": support["warning"],
        },
    }


def _compute_redundancy(panel: dict[str, Any]) -> dict[str, Any]:
    result = compute_pairwise_redundancy(
        panel["candidate_mi"], panel["library_mi"], threshold=0.7
    )
    return {
        "max_lib_corr": float(result["max_lib_corr"]),
        "nearest_factor_id": result["nearest_factor_id"],
        "is_near_duplicate": bool(result["is_near_duplicate"]),
        "exceeds_threshold": bool(result["exceeds_threshold"]),
        "all_correlations": {
            k: (float(v) if not pd.isna(v) else None)
            for k, v in result["all_correlations"].items()
        },
    }


def _compute_feasibility(panel: dict[str, Any]) -> dict[str, Any]:
    proxy = build_proxy_portfolio(
        panel["candidate_mi"], panel["tradable_mi"], long_pct=0.2, short_pct=0.2
    )

    turnover_mean = float(proxy.turnover.mean())

    liquidity = compute_liquidity_coverage(
        proxy.abs_weights, panel["amount_mi"], window=20, pct=0.30
    )
    tail = compute_tail_concentration(proxy.abs_weights, top_k=10)
    small_cap = compute_small_cap_concentration(
        proxy.abs_weights, panel["cap_mi"], pct=0.30
    )
    half_life = compute_half_life(panel["candidate_mi"], max_lag=20)
    holding_bucket = compute_holding_period_proxy(half_life)
    stress = compute_rebalance_stress(
        turnover_mean, tail, liquidity
    )

    return {
        "turnover_mean": turnover_mean,
        "liquidity_coverage": float(liquidity),
        "tail_concentration": float(tail),
        "small_cap_concentration": float(small_cap),
        "half_life": float(half_life),
        "holding_period": holding_bucket,
        "rebalance_stress": {
            "proxy": float(stress["rebalance_stress_proxy"]),
            "bucket": stress["rebalance_stress_bucket"],
        },
    }


def _compute_barra(panel: dict[str, Any]) -> dict[str, Any]:
    # raw IC from validation (re-read the already-computed series)
    ic_val_df = pd.read_parquet(OUTPUTS_DIR / "ic_series_validation.parquet")
    raw_ic = float(ic_val_df["ic"].mean())

    result = compute_barra_exposures(
        panel["factor_flat"],
        panel["style_mi"],
        panel["returns_flat"],
        raw_view_ic=raw_ic,
        min_obs=50,
    )

    # Convert numpy floats / None to plain Python scalars
    def _scalar(v):
        if v is None:
            return None
        if isinstance(v, (float, np.floating)):
            return float(v) if np.isfinite(v) else None
        return v

    return {
        "style_exposures": {
            k: _scalar(v) for k, v in result["style_exposures"].items()
        },
        "style_r_squared": _scalar(result["style_r_squared"]),
        "barra_residual_ic": _scalar(result["barra_residual_ic"]),
        "barra_residual_icir": _scalar(result["barra_residual_icir"]),
        "alpha_survival_ratio": _scalar(result["alpha_survival_ratio"]),
        "dominant_style_exposure": result["dominant_style_exposure"],
        "style_crowding_risk": result["style_crowding_risk"],
    }


def _dump_outputs(outputs: dict[str, Any]) -> None:
    """Persist all scalar outputs to a single yaml bundle."""
    with open(OUTPUTS_DIR / "golden.yaml", "w") as f:
        yaml.dump(
            outputs,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )


def main() -> None:
    print(f"[golden] seed={SEED} days={N_DAYS} symbols={N_SYMBOLS}")
    _mkdirs()

    print("[golden] building synthetic panel ...")
    panel = _synthetic_panel(SEED)

    print("[golden] dumping inputs ...")
    _dump_inputs(panel)

    outputs: dict[str, Any] = {
        "metadata": {
            "seed": SEED,
            "n_days": N_DAYS,
            "n_symbols": N_SYMBOLS,
            "start_date": START_DATE,
            "train_end_idx": TRAIN_END_IDX,
            "val_end_idx": VAL_END_IDX,
            # No generated_at — keeps diffs empty across deterministic reruns.
        },
    }

    print("[golden] effect strength (daily IC + quintile + mono) ...")
    outputs["effect_strength"] = _compute_effect_strength(panel)

    print("[golden] stability (split + support windows) ...")
    outputs["stability"] = _compute_stability(panel)

    print("[golden] redundancy (pairwise) ...")
    outputs["redundancy"] = _compute_redundancy(panel)

    print("[golden] feasibility (liquidity + concentration + half-life + stress) ...")
    outputs["feasibility"] = _compute_feasibility(panel)

    print("[golden] barra (7 styles, per-date OLS) ...")
    outputs["barra"] = _compute_barra(panel)

    _dump_outputs(outputs)

    print(f"[golden] done. outputs under {OUTPUTS_DIR}")


if __name__ == "__main__":
    main()
