---
factor_id: F009
direction: overnight_intraday_split
admitted_in_batch: batch_025
---

# Report Packet — F009

## Factor YAML Summary

```yaml
name: overnight_intraday_spread_5d
expression: Mean(Sub(Div(Sub($open, Ref($close, 1)), Ref($close, 1)), Div(Sub($close,
  $open), $open)), 5)
source_type: dsl
family_tag: overnight_intraday_split
validation_metrics:
  ic_mean: 0.04728489487665639
  ic_ir: 0.4075200526200221
  ic_win_rate: 0.6508264462809917
  monotonicity: 0.9999999999999999
  long_short_mean: 0.0017461215340953767
risk_metrics:
  style_r_squared: 0.14027813486883922
  alpha_survival_ratio: 0.9254
```

## Judge Synthesis

---
candidate_id: C001
batch_id: batch_025
direction: overnight_intraday_split
expression: "Mean(Sub(Div(Sub($open, Ref($close, 1)), Ref($close, 1)), Div(Sub($close, $open), $open)), 5)"
verdict: admit
thread_id: T001
factor_id: F009
factor_name: overnight_intraday_spread_5d
key_metrics_short: "ic_oos=+0.047 ls_t=5.18 mono=+1.00 alpha_surv=0.925 incr_ic=+0.044 corr=0.708@F007"
reject_reason_short: null
---

# C001 — Mean(overnight_return - intraday_return, 5)

> [!success]+ Verdict: **ADMIT** · thread [[directions/overnight_intraday_split#T001|T001]]
> **档位**: CP01 ✓ · CP02 `aligned` · CP03 `strong` · CP04 `good` · CP05 **`high`** · CP06 stable
> **OOS**: IC=**==+0.0473==** · ICIR strong · ls_t=**==+5.18==** · mono=**==+1.00==** · r²=**==0.140==** · alpha_surv=**==0.925==** · max_corr=**==0.708==**@F007 · incr_ic=**==+0.0439==** · mt_bucket=medium search_adjusted=medium

> [!info] Parent: [[batches/batch_025/judge|batch_025 judge]] · Direction: [[directions/overnight_intraday_split]] · Nearest: [[factors/F007]]

## CP01 Hard Gates ✓
8 项全过；max_corr=0.708 < 0.9。

## CP02 Mechanism Alignment · `aligned`
[[directions/overnight_intraday_split#T001]] hypothesis 直接验证：分解 daily return 为 overnight (机构 pre-market 决策) 与 intraday (散户+算法)，**spread 作为两类参与者的相对强弱信号**。正 spread = 机构更 bullish → forward momentum continuation。

## CP03 Statistical Strength · `strong`
IC+ICIR+ls_t=5.18 全 strong + mono=+1.00 完美。`mt_bucket=medium` `search_adjusted=medium`。
→ **strong**

## CP04 Risk Cleanness · `good`
r²=0.140 borderline + a_surv=0.925 clean + extreme clean → borderline-good；alpha 在 Barra 空间保留 93%。
→ **good**

## CP05 Redundancy · **`high`**
max_corr=**0.708**@F007 (high 0.70-0.90) + **incr_ic=+0.044** (>>0.005，8× 阈值). 按 rubric high+incr_ic>0.005 admit。本候选与 F007 (5d open-position) 共享 overnight-driven dynamic，但分解形式不同：F007 测开盘在 day range 的位置，本候选测 overnight 超额的量级 — 机制互补但 cross-section 高重叠。
→ **high**（但库增值极强）

## CP06 Validation Stability · `stable`
sign stable + decay healthy。

> [!success]+ Verdict: ADMIT
> **核心理由**: ls_t=5.18 + mono=+1.00 完美 + incr_ic=+0.044 库 adder 显著 (4x F007 的 incr_ic)。虽 max_corr=0.708 high，但 incr_ic 证明真实增量大——8× 阈值。overnight 与 intraday 分解是 OHLC pattern 空间的新分析角度。
>
> **风险旗标**: CP05 high 0.708@F007 → 实盘组合时建议 F007/F009 择一或权重共享。

## Detailed Metrics

All numeric fields from Phase 2 / Phase 3 for this candidate. Tables in the report should cite these directly — do not mark fields as `—` if they appear below.

```yaml
metrics:
  cp03:
    ic_oos: 0.04728489487665639
    icir_oos: 0.4075200526200221
    ls_tstat_oos: 5.1771
    ic_is: 0.058410906870649294
    icir_is: 0.4620895315857517
    ic_std_is: 0.12640603796022104
    ic_std_oos: 0.1160308420963656
    n_days_is: 1704
    n_days_oos: 484
    ic_win_rate_is: 0.7095070422535211
    ic_win_rate_oos: 0.6508264462809917
    monotonicity_is: 0.9999999999999999
    monotonicity_oos: 0.9999999999999999
    quintile_returns_is:
      q1: -0.0007713513332419097
      q2: 0.0005205791094340384
      q3: 0.0006214682362042367
      q4: 0.0008414002950303257
      q5: 0.0020007079001516104
    quintile_returns_oos:
      q1: -0.0013109304709360003
      q2: 4.817617445951328e-05
      q3: 0.00032231470686383545
      q4: 0.00036994507536292076
      q5: 0.0004335870034992695
    ls_mean_is: 0.0029965245112308224
    ls_mean_oos: 0.0017461215340953767
    ls_sharpe_oos: 3.7318
    ls_sortino_oos: 6.7776
    ls_calmar_oos: 6.3535
    ls_max_dd_oos: -0.0693
    ls_sharpe_is: 4.7382
    ls_tstat_is: 12.3248
    ls_max_dd_is: -7.3069
    ic_by_horizon:
      1:
        ic_is: 0.058410906870649294
        icir_is: 0.4620895315857517
        win_rate_is: 0.7095070422535211
        ic_oos: 0.04728489487665639
        icir_oos: 0.4075200526200221
        win_rate_oos: 0.6508264462809917
      3:
        ic_is: 0.05728271317638956
        icir_is: 0.5028071904557841
        win_rate_is: 0.7136150234741784
        ic_oos: 0.04683908949923342
        icir_oos: 0.4355914817923152
        win_rate_oos: 0.6694214876033058
      5:
        ic_is: 0.05453672031540932
        icir_is: 0.48859979507981605
        win_rate_is: 0.6971830985915493
        ic_oos: 0.04841605809175722
        icir_oos: 0.4490414735958107
        win_rate_oos: 0.6694214876033058
      10:
        ic_is: 0.04866557628608506
        icir_is: 0.43548108848400446
        win_rate_is: 0.6866197183098591
        ic_oos: 0.057542012652763944
        icir_oos: 0.5534736933555854
        win_rate_oos: 0.7148760330578512
      20:
        ic_is: 0.05243411837612867
        icir_is: 0.49106326742885376
        win_rate_is: 0.7288732394366197
        ic_oos: 0.05913661553783378
        icir_oos: 0.5442138293838843
        win_rate_oos: 0.6900826446280992
  cp04:
    style_r_squared: 0.14027813486883922
    alpha_survival_ratio: 0.9254
    alpha_surv_min_threshold: 0.4
    extreme_ratio: 0.020664
    barra_residual_ic: 0.043756
    barra_residual_icir: 0.556463
    dominant_style_exposure: vol_20d
    style_crowding_risk: medium
    style_exposures:
      log_circ_cap: 0.06506101482797946
      book_to_price: 0.18194883254746821
      mom_12_1: 0.14391420354017853
      str_1m: 2.4991363191108973
      vol_20d: 10.765774408496215
      turnover_20d: 1.5309238130586147
      ep_ratio: 0.4924453879357702
    distribution_skew: -0.4624
    distribution_kurt: 2.3766
    distribution_zero_ratio: 0.0
  cp05:
    max_lib_corr: 0.7079
    is_near_duplicate: false
    incremental_ic: 0.043902
    nearest_factor_id: F007
    nearest_factor_expression: Mean(Div(Sub($open, $low), Sub($high, $low)), 5)
    all_correlations:
      F001: -0.11278296196971466
      F002: 0.050893794948037765
      F003: 0.2759515303679402
      F006: 0.5234935624255115
      F007: 0.7079040982466233
      F008: 0.3835696165520953
      F004: 0.019331397262952296
      F005: 0.019331397262952296
    exceeds_threshold: true
  cp06:
    sign_consistency: 1.0
    train_validation_decay: 0.8095
    sign_consistent: true
    ic_by_year:
      2015: 0.06494419664738696
      2016: 0.07054057636087406
      2017: 0.07107544926069884
      2018: 0.05685393838675458
      2019: 0.0609413371507907
      2020: 0.03710556097100806
      2021: 0.04730284222995199
      2022: 0.048089858036761086
      2023: 0.046479931716551695
    worst_quarter_ic: 0.006592
    best_quarter_ic: 0.093409
    ic_autocorr_lag1: -0.035856
    cum_ic_max_drawdown: -1.686713
    split_ic_means:
    - 0.03745114341139441
    - 0.05872857266212776
    - 0.040202607118633764
    - 0.05275725631446961
    split_dispersion: 0.1855
    n_splits: 4
  feasibility:
    turnover_mean: 1.277013688664843
    liquidity_coverage: 0.7464248196500913
    tail_concentration: 0.006869861134133042
    small_cap_concentration: 0.2985855354932041
    signal_half_life: 3.0
    signal_autocorr_lag1: 0.7807
    rebalance_stress:
      value: 0.011753235525618022
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
      train_ic: 0.058410906870649294
      val_ic: 0.04728489487665639
    ic_oos_min:
      passed: true
      value: 0.04728489487665639
      threshold: 0.008
    oos_decay:
      passed: true
      value: 0.8095
      threshold: 0.2
    mono_flip:
      passed: true
      train: 0.9999999999999999
      validation: 0.9999999999999999
      min_magnitude: 0.5
    near_duplicate:
      passed: true
      max_corr: 0.7079
      nearest: F007
coverage: 0.9884
expression: Mean(Sub(Div(Sub($open, Ref($close, 1)), Ref($close, 1)), Div(Sub($close,
  $open), $open)), 5)
```

## Available Charts

The following PNG charts exist in `vault/factors/F009/` and may be embedded via `![[F009/<name>.png]]`. **Do not embed any chart name that is not on this list** — the file would not exist.

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

Write a deep analytical report on `F009`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Embed only charts listed in the **Available Charts** section (skip any section whose chart is unavailable). Output path: `vault/factors/F009.md`.

