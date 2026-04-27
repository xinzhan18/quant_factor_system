#!/usr/bin/env python3
"""Recompute admitted-factor metrics under the tradability mask.

This is an audit tool: it writes comparison files under
``storage/cache/recompute_audit/<run_name>/`` and never overwrites
``storage/vault/factors/F*.yaml``.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from core.factor_stats import multiindex_to_flat
from research.compute.cache import FactorValueCache
from research.compute.data_bridge import (
    CACHE_FULL_END,
    CACHE_FULL_START,
    DEFAULT_DECAY_HORIZONS,
    _returns_col,
    eval_dsl_expression,
    init_qlib,
    load_market_data,
    load_stock_status,
)
from research.compute.masks import build_tradable_mask, combine_masks, load_universe_mask
from research.compute.preprocess import PreprocessConfig, preprocess_factor
from research.compute.vectorized_ic import compute_multi_horizon_ic
from research.compute.vectorized_quintile import (
    compute_long_short_stats,
    compute_quintile_returns,
)
from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml

logger = logging.getLogger(__name__)


def _load_factor_series(
    meta: dict[str, Any],
    *,
    paths: StoragePaths,
    market: pd.DataFrame,
    start: str,
    end: str,
) -> pd.Series:
    source_type = meta.get("source_type", "dsl")
    cache = FactorValueCache(paths.factor_values_cache_dir)

    if source_type == "dsl":
        expr = meta.get("expression")
        if not expr:
            raise ValueError(f"{meta.get('factor_id')}: missing expression")
        key = cache.make_key(expr)
        hit = cache.get_slice(key, start=start, end=end)
        if hit is None or hit.empty:
            full = eval_dsl_expression(expr, start=CACHE_FULL_START, end=CACHE_FULL_END)
            full_df = full.to_frame(name="value")
            full_df.index.names = ["datetime", "instrument"]
            cache.put(key, full_df)
            hit = cache.get_slice(key, start=start, end=end)
        if hit is None or hit.empty:
            raise ValueError(f"{meta.get('factor_id')}: empty factor cache")
        return hit.iloc[:, 0]

    if source_type == "python":
        from research.compute.python_runner import load_python_candidate, run_python_factor

        py_path = meta.get("python_path")
        if not py_path:
            raise ValueError(f"{meta.get('factor_id')}: missing python_path")
        loaded = load_python_candidate(py_path)
        series = run_python_factor(loaded, market)
        level0 = pd.to_datetime(series.index.get_level_values(0))
        return series.loc[(level0 >= pd.Timestamp(start)) & (level0 <= pd.Timestamp(end))]

    raise ValueError(f"{meta.get('factor_id')}: unsupported source_type={source_type!r}")


def _returns_flat(market: pd.DataFrame, horizon: int) -> pd.DataFrame:
    col = _returns_col(horizon)
    df = market[[col]].reset_index()
    df.columns = ["time", "symbol", "value"]
    df["time"] = pd.to_datetime(df["time"])
    return df


def _metrics_for_universe(
    *,
    series: pd.Series,
    mask: pd.Series,
    returns_flat: pd.DataFrame,
    train_range: tuple[str, str],
    validation_range: tuple[str, str],
    preprocess_config: PreprocessConfig,
    primary_horizon: int,
) -> dict[str, Any]:
    clean = preprocess_factor(series, preprocess_config, tradable_mask=mask)
    factor_df = clean.dropna().to_frame("value")
    if factor_df.empty:
        return {"error": "empty_after_mask"}
    factor_flat = multiindex_to_flat(factor_df)
    by_horizon = compute_multi_horizon_ic(
        factor_flat,
        {primary_horizon: returns_flat},
        train_range=train_range,
        validation_range=validation_range,
    )
    primary = by_horizon[primary_horizon]

    def _slice_flat(start: str, end: str) -> pd.DataFrame:
        return factor_flat[
            (factor_flat["time"] >= pd.Timestamp(start))
            & (factor_flat["time"] <= pd.Timestamp(end))
        ]

    ret_train = returns_flat[
        (returns_flat["time"] >= pd.Timestamp(train_range[0]))
        & (returns_flat["time"] <= pd.Timestamp(train_range[1]))
    ]
    ret_val = returns_flat[
        (returns_flat["time"] >= pd.Timestamp(validation_range[0]))
        & (returns_flat["time"] <= pd.Timestamp(validation_range[1]))
    ]
    q_train = compute_quintile_returns(_slice_flat(*train_range), ret_train)
    q_val = compute_quintile_returns(_slice_flat(*validation_range), ret_val)
    ls_val = compute_long_short_stats(q_val["long_short_daily"])

    denom = int(mask.reindex(series.index, fill_value=False).astype(bool).sum())
    coverage = float(clean.notna().sum() / denom) if denom > 0 else 0.0
    return {
        "coverage": coverage,
        "n_eval_rows": int(clean.notna().sum()),
        "ic_train": primary["train"],
        "ic_validation": primary["validation"],
        "quintile_train": {
            **q_train["quintile_returns"],
            "monotonicity": q_train["monotonicity"],
            "ls_mean": q_train["long_short_mean"],
        },
        "quintile_validation": {
            **q_val["quintile_returns"],
            "monotonicity": q_val["monotonicity"],
            "ls_mean": q_val["long_short_mean"],
            "ls_stats": ls_val,
        },
    }


def _factor_paths(paths: StoragePaths, factor_ids: list[str] | None) -> list[Path]:
    if factor_ids:
        return [paths.factor_yaml_file(fid) for fid in factor_ids]
    return sorted(paths.factors_dir.glob("F*.yaml"))


def run_audit(args: argparse.Namespace) -> Path:
    paths = StoragePaths()
    config = load_yaml(paths.config_file) or {}
    qlib_dir = config.get("qlib_data_dir", "~/.qlib/qlib_data/cn_data_1d")
    init_qlib(qlib_dir)

    sample = config.get("sample_policy", {})
    train_range = tuple(sample.get("train_range", ["2015-01-01", "2021-12-31"]))
    validation_range = tuple(sample.get("validation_range", ["2022-01-01", "2023-12-31"]))
    full_start, full_end = train_range[0], validation_range[1]

    eval_cfg = config.get("evaluation", {})
    primary_horizon = int(eval_cfg.get("primary_horizon", 1))
    decay_horizons = eval_cfg.get("decay_horizons", DEFAULT_DECAY_HORIZONS)
    if primary_horizon not in decay_horizons:
        decay_horizons = sorted({*decay_horizons, primary_horizon})

    market = load_market_data(
        start=full_start,
        end=full_end,
        cache_path=paths.market_daily_cache,
        decay_horizons=decay_horizons,
    )
    stock_status = load_stock_status(full_start, full_end)
    tradability = build_tradable_mask(
        market,
        stock_status=stock_status,
        config=config.get("tradability", {}),
    )
    returns_flat = _returns_flat(market, primary_horizon)
    preprocess_config = PreprocessConfig(
        winsorize_mad_k=config.get("preprocess", {}).get("winsorize_mad_k", 5),
        winsorize_mad_scale=config.get("preprocess", {}).get("winsorize_mad_scale", 1.4826),
        zscore=config.get("preprocess", {}).get("zscore", True),
    )

    out_dir = paths.cache_dir / "recompute_audit" / args.run_name
    out_dir.mkdir(parents=True, exist_ok=True)
    universe_names = args.universes
    universe_masks = {
        name: load_universe_mask(name, market.index, qlib_dir=qlib_dir)
        for name in universe_names
    }

    rows: list[dict[str, Any]] = []
    for factor_path in _factor_paths(paths, args.factors):
        if not factor_path.exists():
            logger.warning("factor yaml missing: %s", factor_path)
            continue
        meta = load_yaml(factor_path) or {}
        fid = meta.get("factor_id", factor_path.stem)
        logger.info("auditing %s", fid)
        try:
            series = _load_factor_series(
                meta,
                paths=paths,
                market=market,
                start=full_start,
                end=full_end,
            )
            per_universe = {}
            for name, universe_mask in universe_masks.items():
                mask = combine_masks(
                    tradability,
                    universe_mask,
                    index=series.index,
                )
                per_universe[name] = _metrics_for_universe(
                    series=series,
                    mask=mask,
                    returns_flat=returns_flat,
                    train_range=train_range,
                    validation_range=validation_range,
                    preprocess_config=preprocess_config,
                    primary_horizon=primary_horizon,
                )

            old = meta.get("validation_metrics") or {}
            record = {
                "factor_id": fid,
                "name": meta.get("name"),
                "source_type": meta.get("source_type"),
                "old_validation_metrics": old,
                "new_metrics_by_universe": per_universe,
            }
            (out_dir / f"{fid}.yaml").write_text(
                yaml.dump(record, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )

            primary_name = universe_names[0]
            primary = per_universe.get(primary_name, {})
            val = primary.get("ic_validation", {}) if isinstance(primary, dict) else {}
            qv = primary.get("quintile_validation", {}) if isinstance(primary, dict) else {}
            rows.append(
                {
                    "factor_id": fid,
                    "name": meta.get("name"),
                    "universe": primary_name,
                    "old_ic_mean": old.get("ic_mean"),
                    "new_ic_mean": val.get("ic_mean"),
                    "delta_ic_mean": (
                        None
                        if old.get("ic_mean") is None or val.get("ic_mean") is None
                        else val.get("ic_mean") - old.get("ic_mean")
                    ),
                    "old_ic_ir": old.get("ic_ir"),
                    "new_ic_ir": val.get("ic_ir"),
                    "old_mono": old.get("monotonicity"),
                    "new_mono": qv.get("monotonicity"),
                    "old_ls_mean": old.get("long_short_mean"),
                    "new_ls_mean": qv.get("ls_mean"),
                    "coverage": primary.get("coverage") if isinstance(primary, dict) else None,
                    "n_eval_rows": primary.get("n_eval_rows") if isinstance(primary, dict) else None,
                }
            )
        except Exception as exc:  # noqa: BLE001 - audit should keep moving
            logger.exception("audit failed for %s: %s", fid, exc)
            rows.append({"factor_id": fid, "error": f"{type(exc).__name__}: {exc}"})

    pd.DataFrame(rows).to_csv(out_dir / "summary.csv", index=False)
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-name", default="tradable_mask_v1")
    parser.add_argument("--factors", nargs="*", default=None, help="e.g. F009 F019")
    parser.add_argument(
        "--universes",
        nargs="+",
        default=["all_tradable", "csi300", "csi1000"],
        help="First universe is used for summary.csv old/new deltas.",
    )
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    out = run_audit(args)
    print(f"wrote audit: {out}")


if __name__ == "__main__":
    main()

