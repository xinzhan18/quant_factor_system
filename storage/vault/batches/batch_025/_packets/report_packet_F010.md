---
factor_id: F010
direction: overnight_intraday_split
admitted_in_batch: batch_025
---

# Report Packet — F010

## Factor YAML Summary

```yaml
name: overnight_return_persistence_5d
expression: Mean(Div(Sub($open, Ref($close, 1)), Ref($close, 1)), 5)
source_type: dsl
family_tag: overnight_intraday_split
validation_metrics:
  ic_mean: 0.023776330009776633
  ic_ir: 0.395731219525978
  ic_win_rate: 0.6632231404958677
  monotonicity: 0.9999999999999999
  long_short_mean: 0.0013937206004653896
risk_metrics:
  style_r_squared: 0.07164335404385458
  alpha_survival_ratio: 0.6021
```

## Judge Synthesis

---
candidate_id: C002
batch_id: batch_025
direction: overnight_intraday_split
expression: "Mean(Div(Sub($open, Ref($close, 1)), Ref($close, 1)), 5)"
verdict: admit
thread_id: T001
factor_id: F010
factor_name: overnight_return_persistence_5d
key_metrics_short: "ic_oos=+0.024 ls_t=7.50 mono=+1.00 alpha_surv=0.602 incr_ic=+0.019 corr=0.424@F003"
reject_reason_short: null
---

# C002 — 5d Mean Overnight Return

> [!success]+ Verdict: **ADMIT** · thread [[directions/overnight_intraday_split#T001|T001]]
> **档位**: CP01 ✓ · CP02 `aligned` · CP03 `strong` · CP04 `good` · CP05 `medium` · CP06 stable
> **OOS**: IC=**==+0.0238==** · ls_t=**==+7.50==** · mono=**==+1.00==** · r²=**==0.072==** · alpha_surv=**==0.602==** · max_corr=**==0.424==**@F003 · incr_ic=**==+0.0185==** · mt_bucket=medium search_adjusted=medium

> [!info] Parent: [[batches/batch_025/judge|batch_025 judge]] · Direction: [[directions/overnight_intraday_split]] · Nearest: [[factors/F003]]

## CP01 Hard Gates ✓

## CP02 Mechanism Alignment · `aligned`
[[directions/overnight_intraday_split#T001]] 纯 overnight return 5d aggregation。持续 overnight 强 = 机构 pre-market 持续 bullish → 信息集中在开盘前释放 → 5d 内 momentum continuation。与 F003 (overnight gap normalized by high) 机制部分重叠但 aggregation 窗口不同。

## CP03 Statistical Strength · `strong`
ls_t=**7.50** 极强 + mono=+1.00 完美；IC=+0.024 strong。`mt_bucket=medium` `search_adjusted=medium`。
→ **strong**

## CP04 Risk Cleanness · `good`
r²=0.072 clean + a_surv=0.602 clean + extreme clean。alpha 在 Barra 空间保留 60%——比 F003 单日形式干净。
→ **good**

## CP05 Redundancy · `medium`
max_corr=0.424@F003 medium (0.30-0.70) + incr_ic=+0.019 positive library adder。与 F003 (overnight gap magnitude) 分享 overnight mechanism 但 aggregation window 不同 (5d vs 1d)。
→ **medium**

## CP06 Validation Stability · `stable`

> [!success]+ Verdict: ADMIT
> **核心理由**: ls_t=7.50 是整库最强之一 + mono=+1.00 + a_surv=0.602 clean + incr_ic=+0.019 库 adder + CP05 medium (0.424) 所有指标支持 admit。与 F003 不同: F003 = 单日 overnight gap / high range；本候选 = 5d 平均 overnight return。**aggregation 带来稳定性提升**。

## Detailed Metrics

All numeric fields from Phase 2 / Phase 3 for this candidate. Tables in the report should cite these directly — do not mark fields as `—` if they appear below.

```yaml
metrics:
  cp03:
    ic_oos: 0.023776330009776633
    icir_oos: 0.395731219525978
    ls_tstat_oos: 7.4955
    ic_is: 0.022005984235507987
    icir_is: 0.2080852985310542
    ic_std_is: 0.10575463231115226
    ic_std_oos: 0.060082017381031576
    n_days_is: 1704
    n_days_oos: 484
    ic_win_rate_is: 0.6326291079812206
    ic_win_rate_oos: 0.6632231404958677
    monotonicity_is: 0.9999999999999999
    monotonicity_oos: 0.9999999999999999
    quintile_returns_is:
      q1: -0.0008247726364061236
      q2: 0.00047346248175017536
      q3: 0.000773081963416189
      q4: 0.0008504788856953382
      q5: 0.0019419969758018851
    quintile_returns_oos:
      q1: -0.0010318815475329757
      q2: 3.7023030017735437e-05
      q3: 0.0002159176510758698
      q4: 0.0002862602414097637
      q5: 0.00035591149935498834
    ls_mean_is: 0.002956844010266206
    ls_mean_oos: 0.0013937206004653896
    ls_sharpe_oos: 5.4029
    ls_sortino_oos: 9.6997
    ls_calmar_oos: 8.8781
    ls_max_dd_oos: -0.0396
    ls_sharpe_is: 4.7825
    ls_tstat_is: 12.4398
    ls_max_dd_is: -3.4495
    ic_by_horizon:
      1:
        ic_is: 0.022005984235507987
        icir_is: 0.2080852985310542
        win_rate_is: 0.6326291079812206
        ic_oos: 0.023776330009776633
        icir_oos: 0.395731219525978
        win_rate_oos: 0.6632231404958677
      3:
        ic_is: 0.025704719124781696
        icir_is: 0.25354697449550156
        win_rate_is: 0.6578638497652582
        ic_oos: 0.026290046881046483
        icir_oos: 0.430858806442057
        win_rate_oos: 0.6797520661157025
      5:
        ic_is: 0.027037905858004096
        icir_is: 0.2757465729529759
        win_rate_is: 0.6766431924882629
        ic_oos: 0.02925792337254695
        icir_oos: 0.4809957249232473
        win_rate_oos: 0.6921487603305785
      10:
        ic_is: 0.03250697317124077
        icir_is: 0.35024024679504
        win_rate_is: 0.7235915492957746
        ic_oos: 0.036007747768283464
        icir_oos: 0.5875487664947832
        win_rate_oos: 0.7128099173553719
      20:
        ic_is: 0.033950349933208404
        icir_is: 0.4127180820338451
        win_rate_is: 0.721830985915493
        ic_oos: 0.03822188916281832
        icir_oos: 0.7148389917868018
        win_rate_oos: 0.7355371900826446
  cp04:
    style_r_squared: 0.07164335404385458
    alpha_survival_ratio: 0.6021
    alpha_surv_min_threshold: 0.4
    extreme_ratio: 0.030027
    barra_residual_ic: 0.014316
    barra_residual_icir: 0.293252
    dominant_style_exposure: vol_20d
    style_crowding_risk: medium
    style_exposures:
      log_circ_cap: 0.05362464556882079
      book_to_price: 0.13965564335374187
      mom_12_1: 0.11933444267403912
      str_1m: 1.1968397788246374
      vol_20d: 14.816837838089445
      turnover_20d: 2.9711007763423165
      ep_ratio: 0.4543307809518487
    distribution_skew: -0.0226
    distribution_kurt: 2.7019
    distribution_zero_ratio: 0.0
  cp05:
    max_lib_corr: 0.424
    is_near_duplicate: false
    incremental_ic: 0.018473
    nearest_factor_id: F003
    nearest_factor_expression: Div(Sub($open, Ref($close, 1)), Mean($high, 1))
    all_correlations:
      F001: -0.0201533438673905
      F002: 0.10353288575700433
      F003: 0.423979322750245
      F006: 0.06157819590728688
      F007: 0.26442770877554966
      F008: 0.02389690950762055
      F004: 0.023102909191030786
      F005: 0.023102909191030786
    exceeds_threshold: false
  cp06:
    sign_consistency: 1.0
    train_validation_decay: 1.0804
    sign_consistent: true
    ic_by_year:
      2015: 0.034452229288260645
      2016: 0.018001790274187874
      2017: 0.02947806106418727
      2018: 0.01610320239341944
      2019: 0.019747432901292057
      2020: 0.019084247991918254
      2021: 0.017169949062314494
      2022: 0.019766664621756733
      2023: 0.027785995397796533
    worst_quarter_ic: -0.003723
    best_quarter_ic: 0.064028
    ic_autocorr_lag1: 0.069479
    cum_ic_max_drawdown: -1.508342
    split_ic_means:
    - 0.019842702744150825
    - 0.019690626499362637
    - 0.02840639009617576
    - 0.027165600699417296
    split_dispersion: 0.1697
    n_splits: 4
  feasibility:
    turnover_mean: 1.1705011155911815
    liquidity_coverage: 0.7358038380833957
    tail_concentration: 0.006869861134133042
    small_cap_concentration: 0.3119521159535367
    signal_half_life: 3.0
    signal_autocorr_lag1: 0.7923
    rebalance_stress:
      value: 0.010928429161778634
      rebalance_stress_bucket: medium
    ic_half_life_days: null
mt_budget:
  score: 0.498
  bucket: medium
  terms:
    family: 0.7560317476694317
    direction: 0.0
    exposure: 0.6
  search_adjusted:
    raw: 0.9
    adjusted: 0.6759
    bucket: medium
hard_gate:
  passed: true
  reasons: []
  gate_results:
    compute_error:
      passed: true
    forbidden:
      passed: true
    coverage:
      passed: true
      value: 0.9884
      threshold: 0.8
    sign_flip:
      passed: true
      train_ic: 0.022005984235507987
      val_ic: 0.023776330009776633
    ic_oos_min:
      passed: true
      value: 0.023776330009776633
      threshold: 0.008
    oos_decay:
      passed: true
      value: 1.0804
      threshold: 0.2
    mono_flip:
      passed: true
      train: 0.9999999999999999
      validation: 0.9999999999999999
      min_magnitude: 0.5
    near_duplicate:
      passed: true
      max_corr: 0.424
      nearest: F003
coverage: 0.9884
expression: Mean(Div(Sub($open, Ref($close, 1)), Ref($close, 1)), 5)
```

## Available Charts

The following PNG charts exist in `vault/factors/F010/` and may be embedded via `![[F010/<name>.png]]`. **Do not embed any chart name that is not on this list** — the file would not exist.

- `ic_timeseries`
- `rolling_ic`
- `ic_distribution`
- `monthly_heatmap`
- `quintile_bar`
- `cumulative_returns`
- `annual_group_returns`
- `style_exposure_bar`
- `alpha_waterfall`
- `stability_panel`
- `ic_decay`
- `factor_distribution`
- `coverage`
- `correlation_bar`
- `radar`

## Instructions

Write a deep analytical report on `F010`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Embed only charts listed in the **Available Charts** section (skip any section whose chart is unavailable). Output path: `vault/factors/F010.md`.

