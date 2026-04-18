import json
import pandas as pd
import numpy as np
import yaml
import pytest

from report.render import render_factor


@pytest.fixture
def fixture_vault(tmp_path):
    storage = tmp_path / "storage"
    vault = storage / "vault"
    (vault / "factors").mkdir(parents=True)
    (vault / "batches" / "batch_001").mkdir(parents=True)
    diag = storage / "cache" / "batch_diagnostics" / "batch_001" / "C001"
    diag.mkdir(parents=True)

    rng = np.random.default_rng(0)
    idx = pd.date_range("2020-01-01", periods=500, freq="B")
    ic = pd.concat({
        "train": pd.DataFrame({"ic": rng.normal(-0.02, 0.1, 400)}, index=idx[:400]),
        "validation": pd.DataFrame({"ic": rng.normal(-0.05, 0.1, 100)}, index=idx[400:]),
    }, names=["split"])
    ic.to_parquet(diag / "ic_daily.parquet")
    qt = pd.DataFrame(rng.normal(0, 0.01, (400, 5)),
                      columns=[f"q{i}" for i in range(1, 6)], index=idx[:400])
    qt.to_parquet(diag / "quantile_daily_train.parquet")
    qv = pd.DataFrame(rng.normal(0, 0.01, (100, 5)),
                      columns=[f"q{i}" for i in range(1, 6)], index=idx[400:])
    qv.to_parquet(diag / "quantile_daily_validation.parquet")
    ls = pd.concat({"train": pd.DataFrame({"long_short": (qt["q5"] - qt["q1"]).to_numpy()}, index=qt.index),
                    "validation": pd.DataFrame({"long_short": (qv["q5"] - qv["q1"]).to_numpy()}, index=qv.index)},
                   names=["split"])
    ls.to_parquet(diag / "long_short_daily.parquet")
    cov = pd.DataFrame({"coverage": np.linspace(0.92, 0.98, len(idx))}, index=idx)
    cov.index.name = "datetime"
    cov.to_parquet(diag / "coverage_daily.parquet")
    edges = np.linspace(-3, 3, 51)
    mids = (edges[:-1] + edges[1:]) / 2
    pd.DataFrame({
        "bin_edge_lo": edges[:-1], "bin_edge_hi": edges[1:],
        "is_freq": np.exp(-mids**2) / np.exp(-mids**2).sum(),
        "oos_freq": np.exp(-(mids - 0.2)**2) / np.exp(-(mids - 0.2)**2).sum(),
    }).to_parquet(diag / "factor_hist.parquet", index=False)

    (vault / "factors" / "F001.yaml").write_text(yaml.safe_dump({
        "factor_id": "F001", "name": "test_factor",
        "admitted_in_batch": "batch_001",
        "expression": "Std($close, 20)",
        "direction": "test_direction",
        "source_type": "dsl",
        "family_tag": "test",
    }))

    result = {
        "batch_id": "batch_001",
        "candidates": [{
            "candidate_id": "C001",
            "expression": "Std($close, 20)",
            "diagnostics_relpath": "cache/batch_diagnostics/batch_001/C001",
            "ic": {
                "train": {"ic_mean": -0.02, "ic_ir": -0.2, "ic_win_rate": 0.4, "tstat": -3.0, "n_days": 400},
                "validation": {"ic_mean": -0.05, "ic_ir": -0.4, "ic_win_rate": 0.34, "tstat": -4.5, "n_days": 100},
                "by_year": {2020: -0.04, 2021: -0.06},
                "by_horizon": {1: {"validation": {"ic_mean": -0.04}},
                               5: {"validation": {"ic_mean": -0.06}},
                               20: {"validation": {"ic_mean": -0.08}}},
                "train_validation_decay": 1.05,
            },
            "quintile": {
                "train": {"q1": 0.001, "q2": 0.001, "q3": 0.0, "q4": -0.001, "q5": -0.001,
                          "monotonicity": -0.9, "ls_mean": 0.002, "n_days": 400},
                "validation": {"q1": 0.002, "q2": 0.001, "q3": 0.0, "q4": -0.001, "q5": -0.002,
                               "monotonicity": -0.85, "ls_mean": 0.004, "n_days": 100},
                "ls_stats": {"train": {"mean": 0.002, "tstat": 3.2, "sharpe": 1.2, "maxdd": -0.05},
                             "validation": {"mean": 0.004, "tstat": 4.5, "sharpe": 2.5, "maxdd": -0.03}},
            },
            "stability": {"split_stability": {"split_ic_means": [-0.04, -0.05, -0.06, -0.05],
                                               "sign_consistency": 1.0, "dispersion": 0.08,
                                               "bucket": "low", "n_splits": 4}},
            "uniqueness": {"max_lib_corr": 0.3, "nearest_factor_id": None,
                           "is_near_duplicate": False, "exceeds_threshold": False,
                           "all_correlations": {"F002": 0.2, "F003": -0.1},
                           "incremental_ic": 0.012},
            "feasibility": {"turnover_mean": 0.07, "liquidity_coverage": 0.95,
                           "tail_concentration": 0.01, "small_cap_concentration": 0.25,
                           "signal_half_life": 5.0, "signal_autocorr_lag1": 0.8,
                           "rebalance_stress": {"rebalance_stress_proxy": 0.01, "rebalance_stress_bucket": "low"}},
            "barra": {"style_exposures": {"log_circ_cap": 0.05, "str_1m": 0.3, "vol_20d": 0.25, "turnover_20d": 0.28},
                     "style_r_squared": 0.3, "barra_residual_ic": -0.03,
                     "barra_residual_icir": -0.22, "alpha_survival_ratio": 0.6,
                     "dominant_style_exposure": "turnover_20d", "style_crowding_risk": "medium"},
            "distribution": {"mean": 0.0, "std": 1.0, "skew": 0.2, "kurt": 0.1,
                           "extreme_ratio": 0.008, "coverage": 0.96, "zero_ratio": 0.02},
        }],
    }
    (vault / "batches" / "batch_001" / "result.yaml").write_text(yaml.safe_dump(result))
    return storage


def test_render_factor_writes_charts_and_manifest(fixture_vault):
    manifest = render_factor("F001", storage_root=fixture_vault)
    assets = fixture_vault / "vault" / "factors" / "F001"
    pngs = list(assets.glob("*.png"))
    # expect 18 charts total (15 minimum gate)
    assert len(pngs) >= 15
    rep = json.loads((assets / "report.json").read_text())
    assert set(rep["charts"]).issuperset({"ic_timeseries", "quintile_bar", "radar"})
    assert rep["composite"]["grade"] in {"A", "B", "C", "D"}
    assert rep["factor_id"] == "F001"
    assert rep["batch_id"] == "batch_001"


def test_render_factor_manifest_scalars_present(fixture_vault):
    manifest = render_factor("F001", storage_root=fixture_vault)
    s = manifest["scalars"]
    assert s["ic_validation"]["ic_mean"] == -0.05
    assert s["uniqueness"]["max_lib_corr"] == 0.3
    assert s["barra"]["style_r_squared"] == 0.3


def test_render_factor_returns_manifest_dict(fixture_vault):
    manifest = render_factor("F001", storage_root=fixture_vault)
    assert isinstance(manifest, dict)
    assert "charts" in manifest
    assert "composite" in manifest
