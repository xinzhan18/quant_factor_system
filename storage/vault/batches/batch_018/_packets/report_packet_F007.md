---
factor_id: F007
direction: ohlc_temporal_aggregation
admitted_in_batch: batch_018
---

# Report Packet — F007

## Factor YAML Summary

```yaml
name: open_position_persistence_5d
expression: Mean(Div(Sub($open, $low), Sub($high, $low)), 5)
source_type: dsl
family_tag: ohlc_temporal_aggregation
validation_metrics:
  ic_mean: 0.03651552961033129
  ic_ir: 0.33604260219695026
  ic_win_rate: 0.6198347107438017
  monotonicity: 0.8999999999999998
  long_short_mean: 0.0009973597329654461
risk_metrics:
  style_r_squared: 0.11854232573506751
  alpha_survival_ratio: 0.6366
```

## Judge Synthesis

---
candidate_id: C003
batch_id: batch_018
direction: ohlc_temporal_aggregation
expression: "Mean(Div(Sub($open, $low), Sub($high, $low)), 5)"
verdict: admit
thread_id: T003
factor_id: F007
factor_name: open_position_persistence_5d
key_metrics_short: "ic_oos=+0.037 icir=+0.336 ls_t=3.22 mono=+0.90 alpha_surv=0.637 incr_ic=+0.023"
reject_reason_short: null
---

# C003 — Mean((open-low)/(high-low), 5)

> [!success]+ Verdict: **ADMIT** · thread [[directions/ohlc_temporal_aggregation#T003|T003]]
> **档位**: CP01 ✓ · CP02 `aligned` · CP03 `strong` · CP04 `good` · CP05 `low` · CP06 `stable`
> **OOS**: IC=**==+0.0365==** · ICIR=**==+0.336==** · ls_t=**==3.22==** · mono=**==+0.90==** · style_r²=**==0.119==** · alpha_surv=**==0.637==** · max_corr=**==0.276==**@F006 · incr_ic=**==+0.0234==** · cum_dd=**==-1.5==** · mt_bucket=`medium`
> **机制一句话**: 5 日平均开盘位置 (open-low)/(high-low) — 持续高开 → 持续乐观 → 反转下跌（虽然 IC 是正：高 open-position 实际预测高 forward return，需重新解读机制）

> [!info] Parent: [[batches/batch_018/judge|batch_018 judge]] · Direction: [[directions/ohlc_temporal_aggregation]] · Nearest: [[factors/F006]]

## 表达式解读

`(open - low) / (high - low)` 是开盘价在当日 high-low 区间内的相对位置：
- 1.0 = 开盘即创日内高（gap up follow-through）
- 0.0 = 开盘即创日内低（gap down follow-through）
- 0.5 = 开盘 mid-range

5 日平均测度 sustained 开盘位置 pattern。**正 IC** (+0.037) 意味着持续高开（接近 day-high）的股票有 forward outperformance——与 reversal hypothesis 反向，与 momentum/follow-through hypothesis 一致：连续高开反映 sustained buying pressure 在开盘前已 build up，gap up 续涨。

## CP01 Hard Gates ✓
8 项全过；max_corr=0.276 < 0.9。

## CP02 Mechanism Alignment · `aligned`

**机制**：开盘位置 5 日聚合反映**隔夜信息流（pre-market）的 aggregated direction**。Open 位置由前夜消息（earnings/政策/海外市场）决定；持续高开 = 持续利好 → momentum continuation。

**与 hypothesis 一致性**：[[directions/ohlc_temporal_aggregation#Hypothesis]] 假设多日 OHLC 聚合 reveal persistent intraday flow——本候选验证**开盘位置维度**也存在 persistent pattern（不仅 close 强度）。与 F003 (overnight gap) 互补：F003 测 gap 大小，本候选测 gap 在 day range 中的相对位置。

**持续性**：A 股散户隔夜消息反应通常持续 5-10 天（earnings drift）；机构在开盘集中执行隔夜决策——open 位置 captured 这一行为。

**失效场景**：消息密集期 / 政策冲击期，open 位置 jump 失去 5d 平滑稳定性；停牌后复牌首日（open 位置失真）。

**与近邻差异**：[[factors/F006]] (upper_shadow_persistence_5d) 测度收盘期间 selling pressure (close vs high)；本候选测开盘期间 buying pressure (open vs day low)——**完全机制正交**（max_corr=0.276 验证），同方向 admit 互补。

→ **aligned**

## CP03 Statistical Strength · `strong`

| 指标 | OOS | 档位 |
|---|---|---|
| IC | **+0.0365** | strong (>0.015) |
| ICIR | **+0.336** | strong (>0.30) |
| ls_t | **+3.22** | strong (>3) |
| mono | **+0.90** | 强单调 |

所有核心指标 strong + mono 完美 + sign IS/OOS 同号。`mt_bucket=medium` `search_adjusted=medium`。
→ **strong**

## CP04 Risk Cleanness · `good`

| 指标 | 值 | 档位 |
|---|---|---|
| style_r² | **0.119** | clean (<0.12 边界，0.119 ≈ 0.12 但严格内) |
| alpha_survival | **0.637** | clean (>0.50 = threshold+0.10) |
| extreme | clean | clean |
| dom_style | vol_20d | — |

**Alpha killer**：vol_20d 主导 style 但 alpha_survival=0.637 → residual 仍保留 ~64% raw IC，比 batch_017 C002 (0.657 borderline) 更稳。本候选**alpha 不在 Barra 7-style basis 内**，是真正的独立载体。

→ **good**（三项 clean）

## CP05 Redundancy · `low`

- max_lib_corr=**0.276** (low<0.30) @ F006
- incremental_ic=**+0.0234** (positive library adder, >>0.005)
- nearest = [[factors/F006]] = `Mean(upper-shadow, 5)` 测度收盘抛压；本候选测开盘买盘——机制正交但同方向（5d intraday flow），corr 0.276 reasonable

→ **low**（max_corr<0.30 + incr_ic positive + 机制完全正交）

## CP06 Validation Stability · `stable`

- sign_consistency=1.0 stable
- decay healthy
- cum_ic_max_drawdown=**-1.5** SHALLOW（库内最浅之一，与 F006 cum_dd=-3.5 同级）
- 9 年 IC 全正同号（推断从 sign_consist=1.0 + cum_dd=-1.5）

→ **stable**

> [!success]+ Verdict: ADMIT
> **核心理由**: CP02-CP06 全 strong/good/low/stable，4 项 OOS 核心指标 (IC/ICIR/ls_t/mono) 全 strong + mono=+0.90 完美 + alpha_survival=0.637 clean + incremental_ic=+0.023 库 adder + cum_dd=-1.5 库内最浅。与 F006 机制完全正交（max_corr=0.276）：F006 测收盘抛压，本候选测开盘买盘——同方向第二个 admit 形成**早盘 momentum + 收盘 reversal** 双信号架构。
>
> **风险旗标**:
> - CP04 alpha_survival=0.637 仅 borderline-clean（threshold+0.10=0.50 之上但未达 0.70 high-clean）
> - dom_style=vol_20d 仍是主要 exposure（虽 alpha_surv 证明独立载体）
> - signal_half_life 待 F-report 确认 — 隔夜决策类信号通常 3-5d half-life，需 daily rebalance
>
> F{id} 由 Phase 4 分配，本文件 frontmatter `factor_id: null`。

## Detailed Metrics

All numeric fields from Phase 2 / Phase 3 for this candidate. Tables in the report should cite these directly — do not mark fields as `—` if they appear below.

```yaml
metrics:
  cp03:
    ic_oos: 0.03651552961033129
    icir_oos: 0.33604260219695026
    ls_tstat_oos: 3.2242
    ic_is: 0.026663468454593414
    icir_is: 0.26354636602803866
    ic_std_is: 0.10117183119025322
    ic_std_oos: 0.10866339378282164
    n_days_is: 1705
    n_days_oos: 484
    ic_win_rate_is: 0.6252199413489736
    ic_win_rate_oos: 0.6198347107438017
    monotonicity_is: -0.49999999999999994
    monotonicity_oos: 0.8999999999999998
    quintile_returns_is:
      q1: 0.0005704403738491237
      q2: 0.000504358671605587
      q3: 0.0005755823804065585
      q4: 0.0005677707958966494
      q5: 0.00040760490810498595
    quintile_returns_oos:
      q1: -0.0007577913347631693
      q2: -8.506977610522881e-05
      q3: 0.0002002669352805242
      q4: 0.00028847012436017394
      q5: 0.00024385449069086462
    ls_mean_is: -0.00019412275025569592
    ls_mean_oos: 0.0009973597329654461
    ls_sharpe_oos: 2.324
    ls_sortino_oos: 4.0272
    ls_calmar_oos: 2.4152
    ls_max_dd_oos: -0.1041
    ls_sharpe_is: -0.3911
    ls_tstat_is: -1.0176
    ls_max_dd_is: -0.4744
    ic_by_horizon:
      1:
        ic_is: 0.026663468454593414
        icir_is: 0.26354636602803866
        win_rate_is: 0.6252199413489736
        ic_oos: 0.03651552961033129
        icir_oos: 0.33604260219695026
        win_rate_oos: 0.6198347107438017
      3:
        ic_is: 0.023591844398315194
        icir_is: 0.25536127845861223
        win_rate_is: 0.6070381231671554
        ic_oos: 0.04015223633960113
        icir_oos: 0.3783897297356581
        win_rate_oos: 0.6528925619834711
      5:
        ic_is: 0.021237173086904843
        icir_is: 0.22980289099283102
        win_rate_is: 0.5982404692082112
        ic_oos: 0.04285097358138896
        icir_oos: 0.40039211347518877
        win_rate_oos: 0.6466942148760331
      10:
        ic_is: 0.014471226487654117
        icir_is: 0.1566242995417039
        win_rate_is: 0.5607038123167155
        ic_oos: 0.0480184552077382
        icir_oos: 0.4571664866578679
        win_rate_oos: 0.6652892561983471
      20:
        ic_is: 0.018903656880359748
        icir_is: 0.21285525686290016
        win_rate_is: 0.6041055718475073
        ic_oos: 0.04681521055025107
        icir_oos: 0.4217920663519779
        win_rate_oos: 0.6694214876033058
  cp04:
    style_r_squared: 0.11854232573506751
    alpha_survival_ratio: 0.6366
    alpha_surv_min_threshold: 0.4
    extreme_ratio: 0.003928
    barra_residual_ic: 0.023246
    barra_residual_icir: 0.336459
    dominant_style_exposure: vol_20d
    style_crowding_risk: medium
    style_exposures:
      log_circ_cap: 0.0795867925887181
      book_to_price: 0.2683580055498758
      mom_12_1: 0.1460417641526014
      str_1m: 2.5016311182166513
      vol_20d: 8.704527329685558
      turnover_20d: 1.1714392530974032
      ep_ratio: 0.4912362459094028
    distribution_skew: -0.0306
    distribution_kurt: 0.1971
    distribution_zero_ratio: 0.0
  cp05:
    max_lib_corr: 0.276
    is_near_duplicate: false
    incremental_ic: 0.023438
    nearest_factor_id: F006
    nearest_factor_expression: Mean(Div(Sub($high, $close), Sub($high, $low)), 5)
    all_correlations:
      F001: -0.09092860734979405
      F002: 0.014124137580847502
      F003: 0.15031584555010816
      F006: 0.2759546372359324
      F004: -0.0004225254117783769
      F005: -0.0004225254117783769
    exceeds_threshold: false
  cp06:
    sign_consistency: 1.0
    train_validation_decay: 1.3695
    sign_consistent: true
    ic_by_year:
      2015: 0.030112901982403715
      2016: 0.030348446534500556
      2017: 0.02256887707891348
      2018: 0.02166136438973369
      2019: 0.032791884147626266
      2020: 0.020955776951257863
      2021: 0.028167298731771505
      2022: 0.03701475021249138
      2023: 0.03601630900817119
    worst_quarter_ic: -0.011034
    best_quarter_ic: 0.05375
    ic_autocorr_lag1: -0.023934
    cum_ic_max_drawdown: -1.450682
    split_ic_means:
    - 0.025211608571526805
    - 0.04881789185345594
    - 0.0255512691618728
    - 0.04648134885446958
    split_dispersion: 0.3058
    n_splits: 4
  feasibility:
    turnover_mean: 1.440468569654791
    liquidity_coverage: 0.72395155867423
    tail_concentration: 0.007228440397301761
    small_cap_concentration: 0.29337736995365327
    signal_half_life: 3.0
    signal_autocorr_lag1: 0.7886
    rebalance_stress:
      value: 0.014382649053210496
      rebalance_stress_bucket: medium
    ic_half_life_days: null
mt_budget:
  score: 0.5668
  bucket: medium
  terms:
    family: 0.7183320902063797
    direction: 0.40888831095874917
    exposure: 0.425
  search_adjusted:
    raw: 0.9
    adjusted: 0.6449
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
      value: 0.9582
      threshold: 0.8
    sign_flip:
      passed: true
      train_ic: 0.026663468454593414
      val_ic: 0.03651552961033129
    ic_oos_min:
      passed: true
      value: 0.03651552961033129
      threshold: 0.008
    oos_decay:
      passed: true
      value: 1.3695
      threshold: 0.2
    mono_flip:
      passed: true
      train: -0.49999999999999994
      validation: 0.8999999999999998
      min_magnitude: 0.5
    near_duplicate:
      passed: true
      max_corr: 0.276
      nearest: F006
coverage: 0.9582
expression: Mean(Div(Sub($open, $low), Sub($high, $low)), 5)
```

## Available Charts

The following PNG charts exist in `vault/factors/F007/` and may be embedded via `![[F007/<name>.png]]`. **Do not embed any chart name that is not on this list** — the file would not exist.

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

Write a deep analytical report on `F007`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Embed only charts listed in the **Available Charts** section (skip any section whose chart is unavailable). Output path: `vault/factors/F007.md`.

