---
factor_id: F011
direction: overnight_intraday_split
admitted_in_batch: batch_026
---

# Report Packet — F011

## Factor YAML Summary

```yaml
name: overnight_return_persistence_3d
expression: Mean(Div(Sub($open, Ref($close, 1)), Ref($close, 1)), 3)
source_type: dsl
family_tag: overnight_intraday_split
validation_metrics:
  ic_mean: 0.025013594706387688
  ic_ir: 0.42206749806581134
  ic_win_rate: 0.6797520661157025
  monotonicity: 0.9999999999999999
  long_short_mean: 0.0015210083181368985
risk_metrics:
  style_r_squared: 0.05394670418139946
  alpha_survival_ratio: 0.7264
```

## Judge Synthesis

---
candidate_id: C001
batch_id: batch_026
direction: overnight_intraday_split
expression: "Mean(Div(Sub($open, Ref($close, 1)), Ref($close, 1)), 3)"
verdict: admit
thread_id: T001
factor_id: F011
factor_name: overnight_return_persistence_3d
key_metrics_short: "ic_oos=+0.025 ls_t=7.98 mono=+1.00 alpha_surv=0.726 incr_ic=+0.020 corr=0.756@F010"
reject_reason_short: null
---

# C001 — 3d Overnight Return Persistence (F010 ablation)

> [!success]+ Verdict: **ADMIT** · thread [[directions/overnight_intraday_split#T001|T001]]
> **档位**: CP01 ✓ · CP02 `aligned` · CP03 `strong` · CP04 `good` · CP05 **`high`** · CP06 stable
> **OOS**: IC=+0.025 ls_t=**7.98** mono=**+1.00** r²=0.054 a_surv=0.726 corr=**0.756**@F010 incr_ic=+0.020 mt_bucket=medium search_adjusted=medium

> [!info] Parent: [[batches/batch_026/judge|batch_026 judge]] · Direction: [[directions/overnight_intraday_split]] · Nearest: [[factors/F010]]

## CP01 ✓
## CP02 [[directions/overnight_intraday_split#T001]] aligned — F010 3d window ablation，与 F008 对 F006 的 3d ablation 同源 pattern；**aligned**
## CP03 strong — ls_t=7.98 极强 + mono=+1.00 perfect；`mt_bucket=medium` `search_adjusted=medium`
## CP04 good — r²/a_surv/extreme 全 clean
## CP05 **high** — corr=0.756@F010 high (0.70-0.90) + incr_ic=+0.020 > 0.005 allows admit (与 F008 admit 高-corr 先例一致)
## CP06 stable

> [!success]+ Verdict: ADMIT
> 核心：ls_t=7.98 整库第 2 强（仅 F010 ls_t=7.50 之上）+ mono=+1.00 完美 + incr_ic=+0.020 库 adder。与 F008 相同 "3d window ablation of 5d admit" pattern。高 corr 与 F010 (0.756) 是同机制不同 phase 必然结果。

## Detailed Metrics

All numeric fields from Phase 2 / Phase 3 for this candidate. Tables in the report should cite these directly — do not mark fields as `—` if they appear below.

```yaml
metrics:
  cp03:
    ic_oos: 0.025013594706387688
    icir_oos: 0.42206749806581134
    ls_tstat_oos: 7.9809
    ic_is: 0.02595444408169331
    icir_is: 0.24187293474115876
    ic_std_is: 0.1073061114070847
    ic_std_oos: 0.05926444187485722
    n_days_is: 1704
    n_days_oos: 484
    ic_win_rate_is: 0.6643192488262911
    ic_win_rate_oos: 0.6797520661157025
    monotonicity_is: 0.8999999999999998
    monotonicity_oos: 0.9999999999999999
    quintile_returns_is:
      q1: -0.000981272547505796
      q2: 0.0005980671267025173
      q3: 0.0007907010731287301
      q4: 0.0007499530329369009
      q5: 0.0020563816651701927
    quintile_returns_oos:
      q1: -0.0011239820159971714
      q2: 4.2162944737356156e-05
      q3: 0.00021136211580596864
      q4: 0.0003450672375038266
      q5: 0.0003885586920659989
    ls_mean_is: 0.0033054549525067087
    ls_mean_oos: 0.0015210083181368985
    ls_sharpe_oos: 5.7528
    ls_sortino_oos: 10.3171
    ls_calmar_oos: 10.3903
    ls_max_dd_oos: -0.0369
    ls_sharpe_is: 5.3344
    ls_tstat_is: 13.8754
    ls_max_dd_is: -5.6853
    ic_by_horizon:
      1:
        ic_is: 0.02595444408169331
        icir_is: 0.24187293474115876
        win_rate_is: 0.6643192488262911
        ic_oos: 0.025013594706387688
        icir_oos: 0.42206749806581134
        win_rate_oos: 0.6797520661157025
      3:
        ic_is: 0.030145100339509994
        icir_is: 0.2979103746637031
        win_rate_is: 0.6919014084507042
        ic_oos: 0.028854840351432327
        icir_oos: 0.4961433449401892
        win_rate_oos: 0.6942148760330579
      5:
        ic_is: 0.029994850213546562
        icir_is: 0.3067911117909173
        win_rate_is: 0.7012910798122066
        ic_oos: 0.029169124610364444
        icir_oos: 0.5061383872120427
        win_rate_oos: 0.6942148760330579
      10:
        ic_is: 0.03380336198273434
        icir_is: 0.37468867711366116
        win_rate_is: 0.7382629107981221
        ic_oos: 0.03513297175481028
        icir_oos: 0.6028583912608805
        win_rate_oos: 0.71900826446281
      20:
        ic_is: 0.03496790302219139
        icir_is: 0.42369345441495526
        win_rate_is: 0.7318075117370892
        ic_oos: 0.03776773367093946
        icir_oos: 0.6939740324722268
        win_rate_oos: 0.7582644628099173
  cp04:
    style_r_squared: 0.05394670418139946
    alpha_survival_ratio: 0.7264
    alpha_surv_min_threshold: 0.4
    extreme_ratio: 0.030122
    barra_residual_ic: 0.018171
    barra_residual_icir: 0.358838
    dominant_style_exposure: vol_20d
    style_crowding_risk: medium
    style_exposures:
      log_circ_cap: 0.051084609479177284
      book_to_price: 0.13247045116655665
      mom_12_1: 0.11479455255601494
      str_1m: 0.8839562346547021
      vol_20d: 13.56560979848497
      turnover_20d: 2.4704084168149336
      ep_ratio: 0.4190488705053505
    distribution_skew: 0.01
    distribution_kurt: 2.6952
    distribution_zero_ratio: 0.0
  cp05:
    max_lib_corr: 0.756
    is_near_duplicate: false
    incremental_ic: 0.019951
    nearest_factor_id: F010
    nearest_factor_expression: Mean(Div(Sub($open, Ref($close, 1)), Ref($close, 1)),
      5)
    all_correlations:
      F001: -0.0278956797435694
      F002: 0.08961367432340839
      F003: 0.5462483950062322
      F006: 0.0796379080799436
      F007: 0.22916911090511574
      F008: 0.04499110369402128
      F009: 0.44141368771447725
      F010: 0.7560194461129839
      F004: 0.02227262420443897
      F005: 0.02227262420443897
    exceeds_threshold: true
  cp06:
    sign_consistency: 1.0
    train_validation_decay: 0.9637
    sign_consistent: true
    ic_by_year:
      2015: 0.03185377300620516
      2016: 0.025720639217001174
      2017: 0.03082769887770038
      2018: 0.021463498799441694
      2019: 0.027455988662465923
      2020: 0.026337929648237154
      2021: 0.017996308778447406
      2022: 0.022063024665817006
      2023: 0.02796416474695837
    worst_quarter_ic: 0.003689
    best_quarter_ic: 0.069859
    ic_autocorr_lag1: 0.032537
    cum_ic_max_drawdown: -2.13331
    split_ic_means:
    - 0.020405325598615645
    - 0.02372072373301837
    - 0.02756534217046569
    - 0.028362987323451046
    split_dispersion: 0.1274
    n_splits: 4
  feasibility:
    turnover_mean: 1.5721945834060431
    liquidity_coverage: 0.7335555742401885
    tail_concentration: 0.0068700718701725175
    small_cap_concentration: 0.31074823551207736
    signal_half_life: 2.0
    signal_autocorr_lag1: 0.6604
    rebalance_stress:
      value: 0.014724296510299368
      rebalance_stress_bucket: medium
    ic_half_life_days: null
mt_budget:
  score: 0.5998
  bucket: medium
  terms:
    family: 0.7597101525727913
    direction: 0.3163591818795646
    exposure: 0.625
  search_adjusted:
    raw: 0.9
    adjusted: 0.6301
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
      train_ic: 0.02595444408169331
      val_ic: 0.025013594706387688
    ic_oos_min:
      passed: true
      value: 0.025013594706387688
      threshold: 0.008
    oos_decay:
      passed: true
      value: 0.9637
      threshold: 0.2
    mono_flip:
      passed: true
      train: 0.8999999999999998
      validation: 0.9999999999999999
      min_magnitude: 0.5
    near_duplicate:
      passed: true
      max_corr: 0.756
      nearest: F010
coverage: 0.9884
expression: Mean(Div(Sub($open, Ref($close, 1)), Ref($close, 1)), 3)
```

## Available Charts

The following PNG charts exist in `vault/factors/F011/` and may be embedded via `![[F011/<name>.png]]`. **Do not embed any chart name that is not on this list** — the file would not exist.

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

Write a deep analytical report on `F011`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Embed only charts listed in the **Available Charts** section (skip any section whose chart is unavailable). Output path: `vault/factors/F011.md`.

