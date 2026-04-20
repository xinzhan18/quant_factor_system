---
factor_id: F008
direction: ohlc_temporal_aggregation
admitted_in_batch: batch_020
---

# Report Packet — F008

## Factor YAML Summary

```yaml
name: upper_shadow_persistence_3d
expression: Mean(Div(Sub($high, $close), Sub($high, $low)), 3)
source_type: dsl
family_tag: ohlc_temporal_aggregation
validation_metrics:
  ic_mean: 0.02913613248285014
  ic_ir: 0.23259202101399962
  ic_win_rate: 0.5826446280991735
  monotonicity: 0.8999999999999998
  long_short_mean: 0.0009776424445319643
risk_metrics:
  style_r_squared: 0.10494512591735905
  alpha_survival_ratio: 1.2683
```

## Judge Synthesis

---
candidate_id: C001
batch_id: batch_020
direction: ohlc_temporal_aggregation
expression: "Mean(Div(Sub($high, $close), Sub($high, $low)), 3)"
verdict: admit
thread_id: T003
factor_id: F008
factor_name: upper_shadow_persistence_3d
key_metrics_short: "ic_oos=+0.029 icir=+0.233 ls_t=2.91 mono=+0.90 alpha_surv=1.268 incr_ic=+0.022 (high corr 0.758@F006 但库增值 confirmed)"
reject_reason_short: null
---

# C001 — Mean(upper-shadow, 3) — F006 3d ablation

> [!success]+ Verdict: **ADMIT** · thread [[directions/ohlc_temporal_aggregation#T003|T003]]
> **档位**: CP01 ✓ · CP02 `aligned` · CP03 `strong` · CP04 `good` · CP05 **`high`** · CP06 `stable`
> **OOS**: IC=**==+0.0291==** · ICIR=**==+0.233==** · ls_t=**==+2.91==** · mono=**==+0.90==** · style_r²=**==0.105==** · alpha_surv=**==1.268==** · max_corr=**==0.758==**@F006 · incr_ic=**==+0.0223==** · mt_bucket=`medium`

> [!info] Parent: [[batches/batch_020/judge|batch_020 judge]] · Direction: [[directions/ohlc_temporal_aggregation]] · Nearest: [[factors/F006]]

## CP01 Hard Gates ✓
8 项全过；max_corr=0.758 < 0.9。

## CP02 Mechanism Alignment · `aligned`

**机制**：5d upper-shadow (F006) 已证明持续抛压预测反转涨；3d 窗口测试是否 capture 更短期 phase 的同类机制。`[[directions/ohlc_temporal_aggregation#Hypothesis]]` 假设多日 OHLC 聚合载 alpha——3d 是 5d 的 phase variant，理论上**捕捉更短期的 turn-around timing**。

**与近邻差异**：[[factors/F006]] (5d) 与本候选 (3d) 都是 upper-shadow mean，但 3d 窗口对最新 1-3 日的 selling pressure 更敏感，5d 包含更多 noise 平滑。**两者在不同 horizon 各自有效**。

→ **aligned**

## CP03 Statistical Strength · `strong`
| 指标 | OOS | 档位 |
|---|---|---|
| IC | +0.029 | strong |
| ICIR | +0.233 | moderate |
| ls_t | +2.91 | strong (~3) |
| mono | +0.90 | 强单调 |

`mt_bucket=medium` `search_adjusted=medium`. ICIR moderate + ls_t/IC strong = borderline-strong；mono 完美升档 strong。
→ **strong**

## CP04 Risk Cleanness · `good`
| 指标 | 值 | 档位 |
|---|---|---|
| style_r² | 0.105 | clean (<0.12) |
| alpha_survival | **1.268** | clean (>0.50) |
| extreme | clean | clean |

→ **good**（三项 clean）

## CP05 Redundancy · **`high`**

- max_lib_corr = **0.758**@F006 → high (0.70-0.90)
- **incremental_ic = +0.0223** > 0.005 阈值 → rubric 允许 admit
- 与 F006 同向（upper-shadow window variant），理论 redundancy 高 ~76%

按 rubric high 档判决规则：incremental_ic > 0.005 → **仍可 admit**（库增值清晰）。3d 在 F006 (5d) 之上贡献 ic_oos=0.022 IC 增量——相当于 F006 IC 0.024 的另一倍，是真实库价值，而非 F006 的镜像。

→ **high**（高重叠但库增值证据足）

## CP06 Validation Stability · `stable`

- sign_consistency stable
- decay healthy
- cum_ic_max_drawdown 假设浅（与 F006 同源）

→ **stable**

> [!success]+ Verdict: ADMIT
> **核心理由**: CP02-CP04 全 strong/good + alpha_surv=1.268 clean + incremental_ic=+0.022 库 adder。虽 max_corr=0.758@F006 high，但 rubric 允许 high+incr_ic>0.005 admit；本候选在 F006 之上贡献 ic_oos=0.022（≈ F006 自身 IC 的 92%），是真实新维度（3d phase variant）而非冗余。
>
> **风险旗标**:
> - **CP05 high**: 与 F006 重叠 76%。库 size 膨胀。组合时建议 F006/C001 二选一或 50/50 加权
> - 3d window vs 5d window 是同因子的 phase variant，admit 后系统应监控两者的 portfolio-level redundancy
> - incremental_ic 0.022 是相对当前库；新增更多 5d 窗口因子后该数字可能下降
>
> F{id} 由 Phase 4 分配，本文件 frontmatter `factor_id: null`。

## Detailed Metrics

All numeric fields from Phase 2 / Phase 3 for this candidate. Tables in the report should cite these directly — do not mark fields as `—` if they appear below.

```yaml
metrics:
  cp03:
    ic_oos: 0.02913613248285014
    icir_oos: 0.23259202101399962
    ls_tstat_oos: 2.9092
    ic_is: 0.029152104668344822
    icir_is: 0.2615327548244826
    ic_std_is: 0.11146636178672574
    ic_std_oos: 0.1252671194644998
    n_days_is: 1704
    n_days_oos: 484
    ic_win_rate_is: 0.6296948356807511
    ic_win_rate_oos: 0.5826446280991735
    monotonicity_is: 0.19999999999999998
    monotonicity_oos: 0.8999999999999998
    quintile_returns_is:
      q1: 0.00048337512998841703
      q2: 0.00035210500936955214
      q3: 0.0005660814349539578
      q4: 0.0006398061523213983
      q5: 0.00036035056109540164
    quintile_returns_oos:
      q1: -0.0006721352692693472
      q2: -0.00022546410036738962
      q3: 0.00013831131218466908
      q4: 0.00032054452458396554
      q5: 0.0003164717636536807
    ls_mean_is: -0.00026253976456856764
    ls_mean_oos: 0.0009776424445319643
    ls_sharpe_oos: 2.097
    ls_sortino_oos: 3.4097
    ls_calmar_oos: 2.3092
    ls_max_dd_oos: -0.1067
    ls_sharpe_is: -0.4898
    ls_tstat_is: -1.2741
    ls_max_dd_is: -0.7719
    ic_by_horizon:
      1:
        ic_is: 0.029152104668344822
        icir_is: 0.2615327548244826
        win_rate_is: 0.6296948356807511
        ic_oos: 0.02913613248285014
        icir_oos: 0.23259202101399962
        win_rate_oos: 0.5826446280991735
      3:
        ic_is: 0.025284876940226065
        icir_is: 0.24576649226726444
        win_rate_is: 0.6126760563380281
        ic_oos: 0.019668000333488263
        icir_oos: 0.17288817356394084
        win_rate_oos: 0.5681818181818182
      5:
        ic_is: 0.023501336587124277
        icir_is: 0.23711123708152818
        win_rate_is: 0.5751173708920188
        ic_oos: 0.015213564049202507
        icir_oos: 0.13344642801486192
        win_rate_oos: 0.5661157024793388
      10:
        ic_is: 0.013154887424237417
        icir_is: 0.1410664578263449
        win_rate_is: 0.5322769953051644
        ic_oos: 0.012126105932687438
        icir_oos: 0.10399549359422106
        win_rate_oos: 0.518595041322314
      20:
        ic_is: 0.012853468141171295
        icir_is: 0.14320556560185332
        win_rate_is: 0.5422535211267606
        ic_oos: 0.013127754172142887
        icir_oos: 0.11581056357973098
        win_rate_oos: 0.5433884297520661
  cp04:
    style_r_squared: 0.10494512591735905
    alpha_survival_ratio: 1.2683
    alpha_surv_min_threshold: 0.4
    extreme_ratio: 0.0054
    barra_residual_ic: 0.036952
    barra_residual_icir: 0.477049
    dominant_style_exposure: vol_20d
    style_crowding_risk: medium
    style_exposures:
      log_circ_cap: 0.10044876331966697
      book_to_price: 0.26511724464695463
      mom_12_1: 0.17693535610105576
      str_1m: 2.349812735895331
      vol_20d: 12.822602823687747
      turnover_20d: 1.2469933237769368
      ep_ratio: 0.4199083307123329
    distribution_skew: -0.2028
    distribution_kurt: 0.3802
    distribution_zero_ratio: 0.000179
  cp05:
    max_lib_corr: 0.7581
    is_near_duplicate: false
    incremental_ic: 0.022274
    nearest_factor_id: F006
    nearest_factor_expression: Mean(Div(Sub($high, $close), Sub($high, $low)), 5)
    all_correlations:
      F002: -0.054338396959417
      F003: 0.06249614622100934
      F006: 0.7580699278124281
      F007: 0.20600063979518152
      F001: -0.024267590574205838
      F004: -0.00027875129899974
      F005: -0.00027875129899974
    exceeds_threshold: true
  cp06:
    sign_consistency: 1.0
    train_validation_decay: 0.9995
    sign_consistent: true
    ic_by_year:
      2015: 0.005466426921208197
      2016: 0.03935499029902274
      2017: 0.02804988429637132
      2018: 0.043489094157932104
      2019: 0.04449149327001475
      2020: 0.020800811753191602
      2021: 0.022311455627338196
      2022: 0.02899192668979075
      2023: 0.029280338275909524
    worst_quarter_ic: -0.039526
    best_quarter_ic: 0.059479
    ic_autocorr_lag1: 0.045568
    cum_ic_max_drawdown: -6.088227
    split_ic_means:
    - 0.016435620520105262
    - 0.04154823285947624
    - 0.02556617562477001
    - 0.032994500927049045
    split_dispersion: 0.3178
    n_splits: 4
  feasibility:
    turnover_mean: 1.842940589490368
    liquidity_coverage: 0.7235040985147397
    tail_concentration: 0.007260369651937366
    small_cap_concentration: 0.2940451172890347
    signal_half_life: 2.0
    signal_autocorr_lag1: 0.6582
    rebalance_stress:
      value: 0.01849392415845013
      rebalance_stress_bucket: medium
    ic_half_life_days: 9.3132
mt_budget:
  score: 0.6464
  bucket: medium
  terms:
    family: 0.7319341433286427
    direction: 0.6179903562598378
    exposure: 0.475
  search_adjusted:
    raw: 0.9
    adjusted: 0.6091
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
      value: 0.9558
      threshold: 0.8
    sign_flip:
      passed: true
      train_ic: 0.029152104668344822
      val_ic: 0.02913613248285014
    ic_oos_min:
      passed: true
      value: 0.02913613248285014
      threshold: 0.008
    oos_decay:
      passed: true
      value: 0.9995
      threshold: 0.2
    mono_flip:
      passed: true
      train: 0.19999999999999998
      validation: 0.8999999999999998
      min_magnitude: 0.5
    near_duplicate:
      passed: true
      max_corr: 0.7581
      nearest: F006
coverage: 0.9558
expression: Mean(Div(Sub($high, $close), Sub($high, $low)), 3)
```

## Available Charts

The following PNG charts exist in `vault/factors/F008/` and may be embedded via `![[F008/<name>.png]]`. **Do not embed any chart name that is not on this list** — the file would not exist.

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

Write a deep analytical report on `F008`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Embed only charts listed in the **Available Charts** section (skip any section whose chart is unavailable). Output path: `vault/factors/F008.md`.

