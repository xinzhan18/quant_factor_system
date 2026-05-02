---
factor_id: F028
direction: alpha191_universal_subset
admitted_in_batch: batch_085
---

# Report Packet — F028

## Factor YAML Summary

```yaml
name: dmi_down_ratio_12
expression: Div(Sum(Mul(Lt(Add($high,$low),Add(Ref($high,1),Ref($low,1))),Greater(Abs(Sub($high,Ref($high,1))),Abs(Sub($low,Ref($low,1))))),12),Add(Sum(Mul(Lt(Add($high,$low),Add(Ref($high,1),Ref($low,1))),Greater(Abs(Sub($high,Ref($high,1))),Abs(Sub($low,Ref($low,1))))),12),Sum(Mul(Gt(Add($high,$low),Add(Ref($high,1),Ref($low,1))),Greater(Abs(Sub($high,Ref($high,1))),Abs(Sub($low,Ref($low,1))))),12)))
source_type: dsl
family_tag: alpha191_universal_subset
validation_metrics:
  ic_mean: 0.032646020442404666
  ic_ir: 0.23460769368568346
  ic_win_rate: 0.6053719008264463
  monotonicity: 0.7
  long_short_mean: 0.0010894697317916106
  long_short_sharpe: 2.1846
risk_metrics:
  style_r_squared: 0.4438465383904988
  alpha_survival_ratio: 0.6598
```

## Judge Synthesis

---
candidate_id: C003
batch_id: batch_085
direction: alpha191_universal_subset
expression: "Div(Sum(Mul(Lt(Add($high,$low),Add(Ref($high,1),Ref($low,1))),Greater(Abs(Sub($high,Ref($high,1))),Abs(Sub($low,Ref($low,1))))),12),Add(Sum(Mul(Lt(Add($high,$low),Add(Ref($high,1),Ref($low,1))),Greater(Abs(Sub($high,Ref($high,1))),Abs(Sub($low,Ref($low,1))))),12),Sum(Mul(Gt(Add($high,$low),Add(Ref($high,1),Ref($low,1))),Greater(Abs(Sub($high,Ref($high,1))),Abs(Sub($low,Ref($low,1))))),12)))"
verdict: admit
thread_id: T003
factor_id: F028
factor_name: dmi_down_ratio_12
key_metrics_short: "IC_oos=0.033 ICIR=0.23 ls_t=3.03 alpha_surv=0.66"
reject_reason_short: null
---

# C003 — DMI Down Ratio 12d (Alpha 049)

> [!success]+ Verdict: **ADMIT** · thread [[directions/alpha191_universal_subset#T003|T003]]
> **档位**: CP01 ✓ · CP02 `aligned` · CP03 `borderline` · CP04 `poor` · CP05 `medium` · CP06 `stable`
> **OOS**: IC=**==0.033==** · ICIR=**==0.23==** · ls_t=**==3.03==** · style_r²=0.44 · alpha_surv=**==0.66==** · max_corr=0.38@F009 · incr_ic=**==0.020==** · mt_bucket=`medium`
> **机制一句话**: Welles Wilder DMI down ratio 12d, paper-vetted 三估计器同时显著, csi1000 sign 未翻转 + 库内无 directional pressure 同形.

> [!info] Parent: [[batches/batch_085/judge|batch_085 judge]] · Direction: [[directions/alpha191_universal_subset]] · Nearest: [[factors/F009]]

## 表达式解读

经典 Welles Wilder 1978 DMI 的 -DI/(+DI + -DI). 12d 累积:
- 分子 (Down DM): 当 (H+L) < (prev_H+prev_L) (即"中点下移"), 当日 directional move = max(|H-prev_H|, |L-prev_L|), 否则 0; 12d 求和.
- 分母 = Sum(down DM,12) + Sum(up DM,12) (用 (H+L) > (prev_H+prev_L) 同形对称).

值 ∈ [0,1], 度量"近 12 日下行 directional pressure 占总 directional 的比例". 高 = 下行 dominant, 应 predict 后续负 return (即与 IC 正相关于"反向" — IC sign 该为正只在 long high-DI = predict negative return = inverted IC).

## CP01 Hard Gates ✓

8 项 gate 全过:
- ✓ compute_error / coverage 1.00 / forbidden
- ✓ sign_flip: train +0.040 / val +0.033（同号）
- ✓ ic_oos_min: |+0.033| ≥ 0.008
- ✓ oos_decay: 0.82 ≥ 0.20（健康衰减）
- ✓ mono_flip: train +0.7 / val +0.7（同号 + |x|≥0.5）
- ✓ near_duplicate: max_corr 0.38 < 0.9 (nearest F009)

## CP02 Mechanism Alignment · `aligned`

**机制**：DMI down ratio 度量"过去 12 日中下行 (H+L 中点下移) 的 directional move magnitude 占总 directional magnitude 的比例". 经典 Welles Wilder 1978 趋势/震荡判定指标. 在 csi1000 上下行 directional pressure 高 → 后续负 return ⇒ raw factor 与 forward return 正相关 (即 high DMI-down → low forward return).

**与 hypothesis 一致性**：[[directions/alpha191_universal_subset#Hypothesis]] 引用 Du-Walter-Ulrich Alpha 049 (3×2 t=3.12 / 5×5 t=3.41 两估计器同时显著). [[directions/alpha191_universal_subset#T003]] thread 风险位是 "csi1000 散户震荡市 sign 是否翻转". **实测 sign 与 paper 同向** (train +0.040, val +0.033, 9 年同号正), 答案: csi1000 csi1000 上 directional pressure asymmetry 在小盘震荡市仍保持 paper 同向, 不需 abs(DMI) magnitude proxy.

**持续性**：DMI 是 magnitude × sign-conditional 的 dim-less ratio (∈[0,1]), cross-section 上度量"个股近期下行压力主导度", 与 vol-magnitude 解耦. 持续性来自 (a) trend-following 心理: 散户对持续下行的标的"卖跌"行为放大下行 directional move; (b) 风险偏好下降时下行 directional 更容易触发涨停板硬约束.

**失效场景**：(a) 强趋势单边市 — DMI ratio 接近 1 时 saturate; (b) 涨跌停连板时 H/L 失真; (c) 行业事件突变切换 trend regime.

**与近邻差异**：[[factors/F009]] (overnight_intraday_spread_5d) 度量隔夜 gap × 日内 close-open 5d 短窗几何, 是 close/open 反差; 本候选 DMI 是 H/L midpoint 12d 中长窗 directional 几何 — 完全不同 atom (H/L vs C/O) + 不同 horizon (12d vs 5d). max_corr=0.38 显示有 ~14% variance 共享但 incr_ic=0.020 (>>0.005) 库增值清晰.

→ **aligned**

## CP03 Statistical Strength · `borderline`

| 指标 | IS | OOS | 档位 | 阈值 |
|---|---|---|---|---|
| IC | 0.040 | **==0.033==** | strong | \|x\|>0.015 |
| ICIR | 0.30 | **==0.23==** | moderate | 0.15-0.30 |
| ls_t | 4.77 | **==3.03==** | strong | \|x\|>3 |
| decay | — | 0.82 | healthy | >0.8 |

**Rank-order 验证**：monotonicity_oos = 0.7 (healthy). Q1..Q5 OOS 梯度: q1=-0.00094, q2=-0.00006, q3=+0.00017, q4=+0.00024, q5=+0.00016 → q1 强负 + q2-q5 单调 + q5 略回落. ls_mean_oos=0.00109 (=q5-q1=0.00110) 与 ls_tstat 一致非"一桨驱动". healthy.

**样本量**：n_days_oos=484（充足）.

**MT 调整**: `mt_bucket = medium` (raw 0.68); `search_adjusted` 0.59 medium. medium 档允许 borderline (IC strong + ICIR moderate + ls_t strong → strong 一项不全, 降 borderline).

→ **borderline**（IC + ls_t strong, ICIR moderate, 经 search adjustment 后符合 MT budget medium 档）

## CP04 Risk Cleanness · `poor`

| 指标 | 值 | 档位 | 阈值 |
|---|---|---|---|
| style_r_squared | **==0.44==** | poor | <0.12 |
| alpha_survival | **==0.66==** | acceptable | > 0.40 threshold |
| extreme_ratio | 0.0031 | clean | <0.01 |
| barra_residual_ic | 0.0215 | — | — |
| dominant_style | `vol_20d` | — | — |

**Alpha killer**:
- `vol_20d`: exposure 14.16 (顶级)
- `str_1m`: exposure 6.41
- `turnover_20d`: exposure 1.57
- `ep_ratio`: exposure 0.60

**Barra residual**：raw IC=0.033 → residual IC=0.022, alpha_survival=0.66 (raw 33% 减半到残差 22%, 仍超 0.40 default threshold 0.10). DMI down ratio 在 vol_20d basis 上有显著线性相关 (down directional 大的 universe = high vol_20d), 但剥离后 alpha 仍保 66%. 这是 lessons "vol_20d 结构性吸收律 escape 路径 (a) Python Barra residual orthogonalize" 在 numerator 自身有 OOS-stable alpha 时的 partial work — 非 perfect escape (alpha_surv 仅 0.66 而非 1.0+) 但 acceptable.

→ **poor**（style_r² 0.44 single-poor; alpha_surv 0.66 acceptable; extreme clean. Rubric: 三项中两项 poor → poor; style_r²+alpha_surv 一 poor 一 acceptable + extreme clean → 应 borderline. **重判：borderline**, body 严格 follow rubric: style_r²=0.44 (>0.25 poor) + alpha_surv=0.66 (acceptable: > 0.40 threshold + 0.10 boundary 0.50 → > 0.50 即 clean, 0.66 是 clean) + extreme clean → 一项 poor 两项 clean = `borderline` 严格按 rubric. 我先前误判 alpha_surv=0.66 是 acceptable, 实际 rubric `> threshold + 0.10` = > 0.50 → clean）

**修正档位**: 一项 poor (style_r²) + 两项 clean (alpha_surv 0.66 > 0.50 clean, extreme 0.003 clean) → **borderline**.

## CP05 Redundancy · `medium`

- `max_lib_corr` = **==0.38==**@[[factors/F009]] → medium 档 (0.30-0.70), **接近 P008 frontier 阈值 0.40 下方**
- `is_near_duplicate` = false
- `incremental_ic` = **==0.020==**（>> 0.005, 库增值清晰）

→ **medium**. 库增值: incr_ic=0.020 是 medium corr 下 4 倍标准 (0.005), DMI directional pressure 几何在库内完全空缺 — F021 range_structure / F022 close_position 都是 magnitude/position 几何, 没有 directional sign-aggregated magnitude ratio.

## CP06 Validation Stability · `stable`

| 指标 | 值 | 档位 |
|---|---|---|
| sign_consistency | **==1.0==** | stable |
| train_validation_decay | **==0.82==** | stable (>0.8) |

**时序稳健**：
- `ic_autocorr_lag1` = -0.025 (|x|<0.15 → IC 日独立)
- `cum_ic_max_drawdown` = -1.23 (远 > -30, 几乎无回撤)
- `worst_quarter_ic` = +0.000 / `best_quarter_ic` = +0.083 (同号 worst≈0 但仍正)
- `ic_by_year` (2015-2023): 0.058→0.050→0.031→0.032→0.051→0.031→0.028→0.027→0.038 — 9 年同号, 量级 0.027-0.058 稳定, 后期仍正
- `split_dispersion` = 0.24

→ **stable**（核心两项 stable, 时序稳健全面 healthy: cum_ic_mdd 仅 -1.23, 9 年同号无衰减, dispersion 适中）

> [!success]+ Verdict: ADMIT
> **核心理由**: paper-vetted Alpha 049 DMI directional pressure 在 csi1000 sign 未翻转 (回答 T003 风险位), CP03 borderline 但 ls_t=3.03 + 9 年同号. 库内无 directional sign-aggregated magnitude ratio mechanism family, incr_ic=0.020 库增值 4 倍标准. CP04 修正后 borderline (单点 style_r² 0.44 poor, alpha_surv 0.66 clean, extreme clean). CP06 cum_ic_mdd 仅 -1.23 时序极稳. 与 C001 (multi-MA reversion close-only) atom 完全不同 (C003 是 H/L midpoint), 不触发 anchor rule.
>
> **风险旗标**:
>   - CP03 ICIR=0.23 borderline: 不及 strong 但符合 borderline rubric, OOS 484 days 样本充足, 持续性可观察
>   - CP04 vol_20d exposure=14.16 显著: 后续 DMI 衍生品 (window 变更 / atom 替换) 需 cross-family rhs_change 验证, P028 saturation 律预警
>   - CP05 max_corr=0.38@F009 接近 P008 frontier 上界: 不在 frontier 内 (0.40 下方但近), 后续若设计 DMI×amount 复合需重新评估 F009 cluster
>
> F{id} 由 Phase 4 分配，本文件 frontmatter `factor_id: null`。

## Detailed Metrics

All numeric fields from Phase 2 / Phase 3 for this candidate. Tables in the report should cite these directly — do not mark fields as `—` if they appear below.

```yaml
metrics:
  cp03:
    ic_oos: 0.032646020442404666
    icir_oos: 0.23460769368568346
    ls_tstat_oos: 3.0307
    ic_is: 0.03982121178037782
    icir_is: 0.3008075643851657
    ic_std_is: 0.1323810186149082
    ic_std_oos: 0.13915153390554316
    n_days_is: 1665
    n_days_oos: 484
    ic_win_rate_is: 0.6318318318318318
    ic_win_rate_oos: 0.6053719008264463
    monotonicity_is: 0.7
    monotonicity_oos: 0.7
    quintile_returns_is:
      q1: -0.0005040355608798563
      q2: 0.00041902894736267626
      q3: 0.0006297921645455062
      q4: 0.0006325150025077164
      q5: 0.0004952918388880789
    quintile_returns_oos:
      q1: -0.0009422404109500349
      q2: -5.744554800912738e-05
      q3: 0.00017275374557357281
      q4: 0.00023811921710148454
      q5: 0.00016111890727188438
    ls_mean_is: 0.001064251790797847
    ls_mean_oos: 0.0010894697317916106
    ls_sharpe_oos: 2.1846
    ls_sortino_oos: 3.5315
    ls_calmar_oos: 2.8385
    ls_max_dd_oos: -0.0967
    ls_sharpe_is: 1.854
    ls_tstat_is: 4.767
    ls_max_dd_is: -0.6876
    ic_by_horizon:
      1:
        ic_is: 0.03982121178037782
        icir_is: 0.3008075643851657
        win_rate_is: 0.6318318318318318
        ic_oos: 0.032646020442404666
        icir_oos: 0.23460769368568346
        win_rate_oos: 0.6053719008264463
      3:
        ic_is: 0.03748053559289639
        icir_is: 0.2887823533116217
        win_rate_is: 0.603003003003003
        ic_oos: 0.03700411986938691
        icir_oos: 0.3011061788829891
        win_rate_oos: 0.6425619834710744
      5:
        ic_is: 0.03677983179136025
        icir_is: 0.2886412598255518
        win_rate_is: 0.596996996996997
        ic_oos: 0.04006255704113042
        icir_oos: 0.33807196059242095
        win_rate_oos: 0.6487603305785123
      10:
        ic_is: 0.03334945098122257
        icir_is: 0.26318112625042045
        win_rate_is: 0.590990990990991
        ic_oos: 0.036953208403166474
        icir_oos: 0.3076816839346637
        win_rate_oos: 0.6033057851239669
      20:
        ic_is: 0.03954574518487466
        icir_is: 0.3110886909993851
        win_rate_is: 0.6114114114114114
        ic_oos: 0.04112487716825925
        icir_oos: 0.3038519830697905
        win_rate_oos: 0.5826446280991735
  cp04:
    style_r_squared: 0.4438465383904988
    alpha_survival_ratio: 0.6598
    alpha_surv_min_threshold: 0.4
    extreme_ratio: 0.003108
    barra_residual_ic: 0.02154
    barra_residual_icir: 0.281812
    dominant_style_exposure: vol_20d
    style_crowding_risk: high
    style_exposures:
      log_circ_cap: 0.08125761291264487
      book_to_price: 0.32809692170989785
      mom_12_1: 0.1605473146646335
      str_1m: 6.411320238618488
      vol_20d: 14.155405827302177
      turnover_20d: 1.5679850849645895
      ep_ratio: 0.6031288604977335
    distribution_skew: -0.0271
    distribution_kurt: 0.0013
    distribution_zero_ratio: 0.0
  cp05:
    max_lib_corr: 0.3809
    is_near_duplicate: false
    incremental_ic: 0.019833
    nearest_factor_id: F009
    nearest_factor_expression: Mean(Sub(Div(Sub($open, Ref($close, 1)), Ref($close,
      1)), Div(Sub($close, $open), $open)), 5)
    all_correlations:
      F001: -0.23287089236113775
      F002: 0.0011197060419500377
      F003: 0.024983155676198396
      F006: 0.26657843291292665
      F007: 0.3564782856268594
      F008: 0.1808037216305989
      F009: 0.3808777303672312
      F010: -0.00969221811298749
      F011: 0.01031046694721404
      F012: -0.0016787150164779402
      F013: 0.04139590073111268
      F015: 0.1731116802992187
      F016: 0.07551201561535821
      F017: 0.09982544788211783
      F018: 0.0017337625243805963
      F019: 0.018369619611290338
      F020: -0.04834449864848471
      F021: 0.020344232154899815
      F022: 0.09163883892504412
      F023: 0.015538078788132948
      F024: 0.05588683943867204
      F025: -0.09721008165773765
      F026: 0.0019965513767991653
      F004: 0.016461539236556404
      F005: 0.016461539236556404
    exceeds_threshold: false
  cp06:
    sign_consistency: 1.0
    train_validation_decay: 0.8198
    sign_consistent: true
    ic_by_year:
      2015: 0.05825757810101368
      2016: 0.05043214445666815
      2017: 0.030994848278865995
      2018: 0.03188369806393047
      2019: 0.05084475284319414
      2020: 0.03119887291636515
      2021: 0.028042802519756094
      2022: 0.027227942694845138
      2023: 0.0380640981899642
    worst_quarter_ic: 5.9e-05
    best_quarter_ic: 0.082673
    ic_autocorr_lag1: -0.025283
    cum_ic_max_drawdown: -1.22912
    split_ic_means:
    - 0.022783095053143514
    - 0.03167279033654677
    - 0.03136645686185219
    - 0.044761739518076216
    split_dispersion: 0.2405
    n_splits: 4
  feasibility:
    turnover_mean: 0.959592948056461
    liquidity_coverage: 0.7646572379157571
    tail_concentration: 0.00886019904609188
    small_cap_concentration: 0.25346279765101426
    signal_half_life: 6.0
    signal_autocorr_lag1: 0.911
    rebalance_stress:
      value: 0.01111894859738847
      rebalance_stress_bucket: medium
    ic_half_life_days: null
mt_budget:
  score: 0.6807
  bucket: medium
  terms:
    family: 0.9614929505174394
    direction: 0.0
    exposure: 1.0
  search_adjusted:
    raw: 0.9
    adjusted: 0.5937
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
      value: 1.0
      threshold: 0.8
    sign_flip:
      passed: true
      train_ic: 0.03982121178037782
      val_ic: 0.032646020442404666
    ic_oos_min:
      passed: true
      value: 0.032646020442404666
      threshold: 0.008
    oos_decay:
      passed: true
      value: 0.8198
      threshold: 0.2
    mono_flip:
      passed: true
      train: 0.7
      validation: 0.7
      min_magnitude: 0.5
    near_duplicate:
      passed: true
      max_corr: 0.3809
      nearest: F009
coverage: 1.0
expression: Div(Sum(Mul(Lt(Add($high,$low),Add(Ref($high,1),Ref($low,1))),Greater(Abs(Sub($high,Ref($high,1))),Abs(Sub($low,Ref($low,1))))),12),Add(Sum(Mul(Lt(Add($high,$low),Add(Ref($high,1),Ref($low,1))),Greater(Abs(Sub($high,Ref($high,1))),Abs(Sub($low,Ref($low,1))))),12),Sum(Mul(Gt(Add($high,$low),Add(Ref($high,1),Ref($low,1))),Greater(Abs(Sub($high,Ref($high,1))),Abs(Sub($low,Ref($low,1))))),12)))
```

## Available Charts

The following PNG charts exist in `vault/factors/F028/` and may be embedded via `![[F028/<name>.png]]`. **Do not embed any chart name that is not on this list** — the file would not exist.

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

Write a deep analytical report on `F028`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Embed only charts listed in the **Available Charts** section (skip any section whose chart is unavailable). Output path: `vault/factors/F028.md`.

