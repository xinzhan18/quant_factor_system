from report.composite import compute_composite


def test_composite_returns_seven_dimensions():
    candidate = {
        "ic": {
            "validation": {"ic_mean": -0.065, "ic_ir": -0.54, "ic_win_rate": 0.34},
            "train_validation_decay": 1.089,
            "by_horizon": {
                1: {"validation": {"ic_mean": -0.049}},
                5: {"validation": {"ic_mean": -0.073}},
                20: {"validation": {"ic_mean": -0.095}},
                60: {"validation": {"ic_mean": -0.107}},
            },
        },
        "quintile": {
            "validation": {"monotonicity": -0.9},
            "ls_stats": {"validation": {"sharpe": 3.66, "tstat": -6.27}},
        },
        "uniqueness": {"max_lib_corr": 0.345, "is_near_duplicate": False},
        "stability": {"split_stability": {"sign_consistency": 1.0}},
        "barra": {"alpha_survival_ratio": 0.364, "style_r_squared": 0.335},
    }
    c = compute_composite(candidate)
    assert set(c.keys()) == {
        "predictive_power", "signal_stability", "profitability",
        "monotonicity", "oos_robustness", "uniqueness", "decay_resistance",
        "score", "grade",
    }
    for k in ("predictive_power", "signal_stability", "profitability",
              "monotonicity", "oos_robustness", "uniqueness", "decay_resistance"):
        assert 0 <= c[k] <= 100, f"{k}={c[k]}"
    assert 0 <= c["score"] <= 100
    assert c["grade"] in {"A", "B", "C", "D"}


def test_composite_handles_missing_fields():
    # Empty-ish candidate — no explosion, all sub-scores default to sensible values
    c = compute_composite({})
    assert set(c.keys()) >= {"predictive_power", "grade"}
    assert 0 <= c["score"] <= 100


def test_composite_flags_near_duplicate_as_zero_uniqueness():
    candidate = {
        "uniqueness": {"max_lib_corr": 0.95, "is_near_duplicate": True},
    }
    c = compute_composite(candidate)
    assert c["uniqueness"] == 0.0
