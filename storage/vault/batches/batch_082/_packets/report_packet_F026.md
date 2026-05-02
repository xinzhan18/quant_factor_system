---
factor_id: F026
direction: anchor_proximity_momentum
admitted_in_batch: batch_082
---

# Report Packet — F026

## Factor YAML Summary

```yaml
name: daily_close_position_tsrank_60
expression: TsRank(Div(Sub($close, $low), Sub($high, $low)), 60)
source_type: dsl
family_tag: anchor_proximity_momentum
validation_metrics:
  ic_mean: -0.04634101926304937
  ic_ir: -0.377948482777722
  ic_win_rate: 0.34297520661157027
  monotonicity: -0.9999999999999999
  long_short_mean: -0.0019560053670145804
  long_short_sharpe: -4.5494
risk_metrics:
  style_r_squared: 0.06779633264508711
  alpha_survival_ratio: 1.1262
```

## Judge Synthesis

---
candidate_id: C006
batch_id: batch_082
direction: anchor_proximity_momentum
expression: TsRank(Div(Sub($close, $low), Sub($high, $low)), 60)
verdict: admit
thread_id: T001
factor_id: F026
factor_name: daily_close_position_tsrank_60
key_metrics_short: "ic_oos=-0.046 icir_oos=-0.378 ls_t=-6.31 mono_oos=-1.0 alpha_surv=1.13 style_r²=0.068 max_corr=0.48@F008 — PERFECT MONO + 极强 alpha 残差独立性 + P008 escape 跨 direction 复现首证"
reject_reason_short: null
---

# C006 — TsRank(Div(Sub($close, $low), Sub($high, $low)), 60)

> [!success]+ Verdict: **ADMIT**
> **档位**: CP01 ✓ · CP02 `aligned` · CP03 `strong` · CP04 `good` · CP05 `medium` · CP06 `stable`
> **OOS**: IC=**==-0.046==** · ICIR=**==-0.378==** · ls_t=**==-6.31==** · mono=**==-1.0==** (PERFECT) · style_r²=**==0.068==** · alpha_surv=**==1.13==** · max_corr=0.48@F008 · mt_bucket=`medium`
> **机制一句话**: 60d 时序 rank 的 daily close-position 比率 (c-l)/(h-l) — close 在单日 range 内位置的自身 60d 分位（intraday anchor proximity 的时序聚合）。
> **P008 escape 跨 direction 复现**：anchor_proximity_momentum 方向**首次** alpha_surv > 1.0 + max_corr < 0.50 + mono_oos = -1.0 perfect + sign_consistency = 1.0——bounded [0,1] dimless close-anchor proximity ratio 经 TsRank 60d 量纲化成功逃 vol_20d 吞噬律。

> [!info] Parent: [[batches/batch_082/judge|batch_082 judge]] · Direction: [[directions/anchor_proximity_momentum]] · Nearest: [[factors/F008]]

## 表达式解读

`TsRank(Div(Sub($close, $low), Sub($high, $low)), 60)` = 单日 close-position ratio (c-l)/(h-l) ∈ [0,1] 的 60 日时序 self-rank。

机制：(c-l)/(h-l) 是 close 距 daily-low 的 shadow 占整个 daily range 的份额——值越大 = close 越接近 high = 当日上涨力强（buyer dominant，close 推高至 high 附近）；值越小 = close 越接近 low = 当日下跌（seller dominant）。TsRank 60d 把单日 raw level 替换为个股自身 60d 分位，逃 cross-section vol 吸收。

**这是 anchor proximity 的 daily-resolution 版本**——anchor 在每日 high/low（"昨日的 reference"），与 60d-window stochastic position（C001 跨日 anchor）几何不同。signal direction：高 close-position = 当日强势 → 但 IC 为 negative 表示**短期 mean-revert**——当日强势后 1-day forward 反而弱化（一致于 short-term reversal 学术 stylized fact）。

## CP01 Hard Gates ✓

8 项 gate 全过：
- ✓ compute_error
- ✓ coverage: 0.9999 ≥ 0.80
- ✓ sign_flip: train -0.0329 / val -0.0463（同号 negative，OOS 强化）
- ✓ forbidden
- ✓ ic_oos_min: |-0.0463| ≥ 0.008
- ✓ oos_decay: 1.410 ≥ 0.20（OOS > IS 强化型）
- ✓ mono_flip: train -0.70 / val **-1.00 PERFECT**（同号 |x|≥0.5 阈，validation 完美单调）
- ✓ near_duplicate: max_corr 0.481 < 0.9（nearest [[factors/F008]]）

## CP02 Mechanism Alignment · `aligned`

**机制**：单日 (c-l)/(h-l) close-position [0,1] 量纲化的 60d self-rank。daily-resolution intraday anchor proximity——anchor 是 daily high/low；TsRank 60d 把 cross-section level → individual 时序分位。

**与 hypothesis 一致性**：[[directions/anchor_proximity_momentum#Hypothesis]] H1 baseline 真度（bounded [0,1] dimless close-anchor proximity ratio + TsRank 60d 量纲化逃 vol_20d 吞噬律）——本候选**完美对齐**：style_r²=0.068 (clean<0.12) + alpha_surv=1.13 (>>1.0 阈) + dominant_style=vol_20d 但 exposure=11.04 medium crowding（与 C002 8.76 一致 medium，远低于 C001/C003/C004/C005 的 10.79-19.82 high crowding）。**P008 escape 路径在 anchor_proximity_momentum 方向**首次跨方向复现成功**（b081 C006 hl_norm_sym 是单例首证，本 C006 在不同 direction 上**复现 alpha_surv≈1.0**）。

**持续性**：daily close-position 反映"日内买卖盘最终博弈结果"，是市场微观博弈的稳定特征，跨 regime 持续；TsRank 60d 把 cross-section level → individual 60d 分位，逃 cross-section vol 吸收。机制有 deep 持续性。

**失效场景**：
- 涨停板：close=high → (c-l)/(h-l) = 1 强 push 因子上界，批量涨停日因子结构性扁平
- 停牌后复牌：60d window 含停牌期会造成 TsRank 异常
- 低换手票：单日 (c-l)/(h-l) 噪声大，但 TsRank 60d 可平滑

**与近邻差异**：[[factors/F008]] 是 `Mean(Div(Sub($high, $close), Sub($high, $low)), 3)` —— 3 日均值的 (h-c)/(h-l) (upper-shadow，**与本候选互补**)。本候选是 60 日 TsRank of (c-l)/(h-l) (lower-shadow / close-position)。corr=0.48 中等正相关——反应 daily 单层位置信号在 short-mean 与 long-rank 不同聚合下的部分重合；incremental_ic=-0.039 远高于阈，库增值清晰。

→ **aligned**

## CP03 Statistical Strength · `strong`

| 指标 | IS | OOS | 档位 | 阈值 |
|---|---|---|---|---|
| IC | -0.0329 | **==-0.0463==** | strong | \|x\|>0.015 |
| ICIR | -0.302 | **==-0.378==** | strong | \|x\|>0.30 |
| ls_t | -3.39 | **==-6.31==** | strong | \|x\|>3 |
| decay | — | 1.410 | healthy++ | OOS strengthen |

**Rank-order 验证**：mono_oos=**-1.0 PERFECT**。Q1..Q5 OOS 梯度: q1=0.00062, q2=0.00035, q3=0.00017, q4=-0.00022, q5=-0.00134 → **完美单调下降** q1>q2>q3>q4>q5；q1-q5=0.00196 ≈ -ls_mean_oos=0.00196，与 ls_tstat=-6.31 一致；non-trivial cross-section 5 档真实排序，非"一桨"型。

**样本量**：n_days_oos=484（充足）；ls_sharpe_oos=-4.55（|x|>3 strong），sortino_oos=-6.80（极强），calmar_oos=-0.77，ls_max_dd_oos=-0.638（深 drawdown 单边 short 端，但 long 端 q1=+0.00062 持续正收益）。

**MT 调整**：`mt_bucket = medium`（base score 0.68）；`search_adjusted = 0.595`（medium adjusted 档保留）。medium 档允许 strong 保留，经 search adjustment 后系数 0.595 仍在 strong 档下界以上，符合 MT budget 容忍阈值。

→ **strong**

## CP04 Risk Cleanness · `good`

| 指标 | 值 | 档位 | 阈值 |
|---|---|---|---|
| style_r_squared | **==0.068==** | clean | <0.12 |
| alpha_survival | **==1.13==** | clean | threshold 0.40 + 0.10 = 0.50；本候选 >> 0.50 (1.13) |
| extreme_ratio | 0.004 | clean | <0.01 |
| barra_residual_ic | -0.052 | — | — |
| dominant_style | `vol_20d` (exposure=11.04) | — | medium crowding |

**Alpha killer**（按 `style_contributions` 排序前 2-3 项）：
- `vol_20d`: exposure=11.04 (dominant 但 medium crowding)
- `str_1m`: 1.37
- `turnover_20d`: 1.15
- 三项 clean — barra_residual_ic=-0.052 略大于 raw ic_oos=-0.046（**残差比原信号还强**），alpha_surv=1.13 (>>1.0) 验证 alpha 主要来自 Barra 残差空间。total killer 占比极低。

→ **good**（三项全 clean；P008 escape 路径——dim-less anchor proximity ratio 通过 TsRank 60d 量纲化成功逃 vol_20d 吞噬律；与 C002 几乎对称的 clean profile）

## CP05 Redundancy · `medium`

- `max_lib_corr` = **==0.481==** (vs [[factors/F008]]) → medium 档 (0.30-0.70)
- `is_near_duplicate` = false（硬闸未触发）
- nearest = [[factors/F008]] (`Mean(Div(Sub($high, $close), Sub($high, $low)), 3)` — 3d mean of upper-shadow ratio)
- `incremental_ic` = **==-0.039==**（>> 0.005 阈，库增值极清晰）

→ **medium**。库相关 0.48 来自原子部分相同（F008 用 (h-c)/(h-l)，本候选用 (c-l)/(h-l) 镜像，单日恒等式 (h-c)+(c-l)=h-l 使两原子完全互补）；本候选 60d TsRank 的 long-window self-rank 维度与 F008 3d 短期 mean 完全不同的聚合方式。incremental_ic=-0.039 极高——admit 增值清晰。

注：与同批 [[batches/batch_082/candidates/C002|C002]] = `TsRank((h-c)/(h-l), 60)` 是数学完美镜像（恒等式 + TsRank monotone-invariance → corr ≈ -1）；选 C006 admit 因 mono_oos=-1.0 perfect & daily close-position 是更直觉 anchor proximity 表达，C002 reserve。

## CP06 Validation Stability · `stable`

| 指标 | 值 | 档位 |
|---|---|---|
| sign_consistency | **==1.0==** | stable |
| train_validation_decay | **==1.410==** | stable++ (OOS strengthen) |

**时序稳健**：
- `ic_autocorr_lag1` = -0.029（|x|<0.15 → IC 日独立，ICIR 置信高）
- `cum_ic_max_drawdown` = **-85.66**（< -50 警觉——本批最深，长期失效段历史显著；但 sign_consistency=1.0 表明虽有深 drawdown 但符号始终一致）
- `worst_quarter_ic` = -0.085 / `best_quarter_ic` = +0.067（worst ≈ 1.8× |ic_oos|，best 1.5× |ic_oos|；2015 年唯一 positive 0.034 是 stress 反例季度）
- `ic_by_year`：2015=+0.034 唯一 positive (regime exception), 2016-2023 全 negative -0.031~-0.066，符号稳定 8/9 年（与 C002 inverse symmetric pattern）

→ **stable**（核心两项稳定 + sign_consistency=1.0 + decay strengthen 1.41）；cum_ic_mdd 深但 sign 不翻是 acceptable risk。

> [!success]+ Verdict: ADMIT
> **核心理由**: 5 个软 CP 全档位最优档（aligned · strong · good · medium · stable），CP03 strong (IC=-0.046, ICIR=-0.378, ls_t=-6.31) + mono_oos=**-1.0 PERFECT** + Q1..Q5 完美单调下降 + CP04 alpha_surv=1.13 + style_r²=0.068 ——本候选自身完全够 admit 资格，**且作为 P008 escape 路径在 anchor_proximity_momentum 方向首次跨方向复现的核心证据**。daily close-position (c-l)/(h-l) + TsRank 60d 是 b081 C006 hl_norm_sym (对称版) alpha_surv≈0.99 的 daily-resolution 同律复现——证明 P008 escape 不是 b081 hl_norm_sym 单例 fluke，而是**结构性 generalizable** 路径："bounded [0,1] dimless close-anchor proximity ratio + TsRank 60d" 是 csi1000 daily 上跨 direction 可复用的 alpha 生成器。
>
> **风险旗标**:
> - CP05 medium: max_lib_corr=0.48 经 F008；与同批 C002 数学镜像 (corr≈-1) 但 C002 reserve、本候选 admit canonical sign
> - CP06 cum_ic_mdd=-85.66 极深（本批最深）但 sign_consistency=1.0 配合，是"持续 negative 但偶有反弹"型而非"flip"，acceptable
> - CP04 dom=vol_20d exposure=11.04 medium crowding（vol exposure 仍非零，但 alpha_surv=1.13 足以覆盖）
> - 数据契约：候选不用 fundamental TTM 字段；P019 / P021 / Geometric absorbing-factor 律全合规；与 F018 / F021 / F024 / F025 max_corr (0.48 vs F025=-0.38, F022=0.15, F008=-0.48) 均 < 0.50 满足红线
>
> F{id} 由 Phase 4 分配，本文件 frontmatter `factor_id: null`。

## Detailed Metrics

All numeric fields from Phase 2 / Phase 3 for this candidate. Tables in the report should cite these directly — do not mark fields as `—` if they appear below.

```yaml
metrics:
  cp03:
    ic_oos: -0.04634101926304937
    icir_oos: -0.377948482777722
    ls_tstat_oos: -6.3115
    ic_is: -0.03285588881599124
    icir_is: -0.3018076235747046
    ic_std_is: 0.1088636808667579
    ic_std_oos: 0.12261199971611826
    n_days_is: 1665
    n_days_oos: 484
    ic_win_rate_is: 0.34954954954954953
    ic_win_rate_oos: 0.34297520661157027
    monotonicity_is: -0.7
    monotonicity_oos: -0.9999999999999999
    quintile_returns_is:
      q1: 0.0005083197029307485
      q2: 0.000714591471478343
      q3: 0.0006471080123446882
      q4: 0.0003022220334969461
      q5: -0.00048160296864807606
    quintile_returns_oos:
      q1: 0.0006165861268527806
      q2: 0.00034616910852491856
      q3: 0.00016721825522836298
      q4: -0.00022140087094157934
      q5: -0.0013387908693403006
    ls_mean_is: -0.0006281671717230863
    ls_mean_oos: -0.0019560053670145804
    ls_sharpe_oos: -4.5494
    ls_sortino_oos: -6.8007
    ls_calmar_oos: -0.773
    ls_max_dd_oos: -0.6377
    ls_sharpe_is: -1.3194
    ls_tstat_is: -3.3924
    ls_max_dd_is: -2.2664
    ic_by_horizon:
      1:
        ic_is: -0.03285588881599124
        icir_is: -0.3018076235747046
        win_rate_is: 0.34954954954954953
        ic_oos: -0.04634101926304937
        icir_oos: -0.377948482777722
        win_rate_oos: 0.34297520661157027
      3:
        ic_is: -0.019046000896411622
        icir_is: -0.19700352824013792
        win_rate_is: 0.4078078078078078
        ic_oos: -0.029962354044005626
        icir_oos: -0.2692427564476477
        win_rate_oos: 0.378099173553719
      5:
        ic_is: -0.016923629426367843
        icir_is: -0.18014567262083436
        win_rate_is: 0.4252252252252252
        ic_oos: -0.020532445112577815
        icir_oos: -0.18377326105150646
        win_rate_oos: 0.4214876033057851
      10:
        ic_is: -0.005851815728224599
        icir_is: -0.06746906016877452
        win_rate_is: 0.47807807807807806
        ic_oos: -0.014161687067523993
        icir_oos: -0.1271939108890236
        win_rate_oos: 0.43388429752066116
      20:
        ic_is: -0.0023989445502796115
        icir_is: -0.029080916564051092
        win_rate_is: 0.48768768768768767
        ic_oos: -0.010053761307601052
        icir_oos: -0.08930136926171442
        win_rate_oos: 0.4359504132231405
  cp04:
    style_r_squared: 0.06779633264508711
    alpha_survival_ratio: 1.1262
    alpha_surv_min_threshold: 0.4
    extreme_ratio: 0.003746
    barra_residual_ic: -0.052189
    barra_residual_icir: -0.668087
    dominant_style_exposure: vol_20d
    style_crowding_risk: medium
    style_exposures:
      log_circ_cap: 0.08994362809916143
      book_to_price: 0.29958650180274093
      mom_12_1: 0.16483665406153386
      str_1m: 1.3712090174631841
      vol_20d: 11.038351066813647
      turnover_20d: 1.1469443377150332
      ep_ratio: 0.5794609092398141
    distribution_skew: 0.0577
    distribution_kurt: -0.1286
    distribution_zero_ratio: 0.0
  cp05:
    max_lib_corr: 0.4809
    is_near_duplicate: false
    incremental_ic: -0.03913
    nearest_factor_id: F008
    nearest_factor_expression: Mean(Div(Sub($high, $close), Sub($high, $low)), 3)
    all_correlations:
      F001: -0.028324854437565824
      F002: 0.026427281167914835
      F003: -0.013504197745087362
      F006: -0.3534151867145137
      F007: -0.10434534217187519
      F008: -0.4809307153396686
      F009: -0.17077322150362112
      F010: 0.011883149748106309
      F011: 0.0075986414431315884
      F012: 0.0033637034683860734
      F013: 0.020670273551512734
      F015: 0.022873542943695185
      F016: 0.03191383339314506
      F017: 0.033500377476198835
      F018: 0.04006824740843406
      F019: 0.006389662259423959
      F020: -0.04529142325178697
      F021: -0.014264469300134202
      F022: 0.15206670500247127
      F023: 0.011335410812284147
      F024: -0.06741909200108075
      F025: -0.38123437160743623
      F004: 0.016262531720791066
      F005: 0.016262531720791066
    exceeds_threshold: false
  cp06:
    sign_consistency: 1.0
    train_validation_decay: 1.4104
    sign_consistent: true
    ic_by_year:
      2015: 0.03375436933674402
      2016: -0.031344384641089774
      2017: -0.03110705717709345
      2018: -0.04790668655305536
      2019: -0.06568399969524376
      2020: -0.030772854195094828
      2021: -0.04611839544133547
      2022: -0.04900426616876239
      2023: -0.043677772357336345
    worst_quarter_ic: -0.084734
    best_quarter_ic: 0.06659
    ic_autocorr_lag1: -0.029272
    cum_ic_max_drawdown: -85.663513
    split_ic_means:
    - -0.035356280005439625
    - -0.06265225233208514
    - -0.0482258816358477
    - -0.039129663078825
    split_dispersion: 0.2269
    n_splits: 4
  feasibility:
    turnover_mean: 3.1447202602124045
    liquidity_coverage: 0.7388292098060892
    tail_concentration: 0.008862175506585091
    small_cap_concentration: 0.27094144329306175
    signal_half_life: 1.0
    signal_autocorr_lag1: 0.0371
    rebalance_stress:
      value: 0.03772057533084093
      rebalance_stress_bucket: medium
    ic_half_life_days: 5.2238
mt_budget:
  score: 0.6777
  bucket: medium
  terms:
    family: 0.9553751047612822
    direction: 0.0
    exposure: 1.0
  search_adjusted:
    raw: 0.9
    adjusted: 0.595
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
      value: 0.9999
      threshold: 0.8
    sign_flip:
      passed: true
      train_ic: -0.03285588881599124
      val_ic: -0.04634101926304937
    ic_oos_min:
      passed: true
      value: -0.04634101926304937
      threshold: 0.008
    oos_decay:
      passed: true
      value: 1.4104
      threshold: 0.2
    mono_flip:
      passed: true
      train: -0.7
      validation: -0.9999999999999999
      min_magnitude: 0.5
    near_duplicate:
      passed: true
      max_corr: 0.4809
      nearest: F008
coverage: 0.9999
expression: TsRank(Div(Sub($close, $low), Sub($high, $low)), 60)
```

## Available Charts

The following PNG charts exist in `vault/factors/F026/` and may be embedded via `![[F026/<name>.png]]`. **Do not embed any chart name that is not on this list** — the file would not exist.

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

Write a deep analytical report on `F026`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Embed only charts listed in the **Available Charts** section (skip any section whose chart is unavailable). Output path: `vault/factors/F026.md`.

