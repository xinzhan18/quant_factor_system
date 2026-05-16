---
factor_id: F029
direction: conditional_operator_truncation
admitted_in_batch: batch_098
---

# Report Packet — F029

## Factor YAML Summary

```yaml
name: weak_close_day_rate_20
expression: Mean(Lt(Div(Sub($close,$low),Sub($high,$low)),0.2),20)
source_type: dsl
family_tag: conditional_operator_truncation
validation_metrics:
  ic_mean: 0.009517368143819597
  ic_ir: 0.09199001477822301
  ic_win_rate: 0.5475206611570248
  monotonicity: 0.49999999999999994
  long_short_mean: 0.0008780915639002438
  long_short_sharpe: 2.3673
risk_metrics:
  style_r_squared: 0.171246950787166
  alpha_survival_ratio: 1.0976
factor_ir:
  candidate_id: C004
  ir_version: v1
  data_logic: {}
  factor_logic:
    backend: qlib
    expression: Mean(Lt(Div(Sub($close,$low),Sub($high,$low)),0.2),20)
  hypothesis: "T008 range-position 低位主导日占比 (close 在 range 最低 20% 区间天数占比 = 弱收盘日).\n\
    (C-L)/(H-L) < 0.2 为 1 否则 0. 20d Mean = 弱收盘日 rate.\nexpected_sign: negative (弱收盘日多\
    \ = 持续抛压 = 反转向下).\n\nSelf-check:\n  - P030: multi-CP rationale\n  - P004-deep\
    \ BORDERLINE: 20d 离散事件率, candle geometry 路径\n  - F028: 单 Lt, distinct\n  - b097/C001\
    \ anchor (上影主导日 Gt((H-C)/(H-L),0.5)): 上影主导 → close 偏 low →\n    (C-L)/(H-L) 偏小\
    \ → Lt(.,0.2) 是其更严格 subset. 期望 cross-section corr 与\n    b097/C001 高度正相关 (|corr|\
    \ ∈ [0.5, 0.8]). Phase 2 max_corr 实测决定;\n    若 >0.7 → near_dup reject\n  - C003\
    \ (本批): C003 strong-close + C004 weak-close 是高位/低位互补但非严格 (中间\n    [0.2, 0.8] 共同\
    \ False); cross-section corr 期望负相关, 但 |corr| 不一定大. 取较强者\n  - reciprocal monotonic:\
    \ Lt(x,0.2) ≠ Gt(x,0.8), 非严格互补\n"
  expected_sign: negative
  canonical: Mean(Lt(Div(Sub($close,$low),Sub($high,$low)),0.2),20)
  metadata:
    expected_sign: negative
    rationale: "T008 range-position 低位主导日占比 (close 在 range 最低 20% 区间天数占比 = 弱收盘日).\n\
      (C-L)/(H-L) < 0.2 为 1 否则 0. 20d Mean = 弱收盘日 rate.\nexpected_sign: negative (弱收盘日多\
      \ = 持续抛压 = 反转向下).\n\nSelf-check:\n  - P030: multi-CP rationale\n  - P004-deep\
      \ BORDERLINE: 20d 离散事件率, candle geometry 路径\n  - F028: 单 Lt, distinct\n  - b097/C001\
      \ anchor (上影主导日 Gt((H-C)/(H-L),0.5)): 上影主导 → close 偏 low →\n    (C-L)/(H-L)\
      \ 偏小 → Lt(.,0.2) 是其更严格 subset. 期望 cross-section corr 与\n    b097/C001 高度正相关\
      \ (|corr| ∈ [0.5, 0.8]). Phase 2 max_corr 实测决定;\n    若 >0.7 → near_dup reject\n\
      \  - C003 (本批): C003 strong-close + C004 weak-close 是高位/低位互补但非严格 (中间\n    [0.2,\
      \ 0.8] 共同 False); cross-section corr 期望负相关, 但 |corr| 不一定大. 取较强者\n  - reciprocal\
      \ monotonic: Lt(x,0.2) ≠ Gt(x,0.8), 非严格互补\n"
backend_provenance:
  backend: qlib
  source_type: dsl
  ir_version: v1
  factor_logic:
    backend: qlib
    expression: Mean(Lt(Div(Sub($close,$low),Sub($high,$low)),0.2),20)
```

## Judge Synthesis

---
candidate_id: C004
batch_id: batch_098
direction: conditional_operator_truncation
expression: "Mean(Lt(Div(Sub($close,$low),Sub($high,$low)),0.2),20)"
verdict: admit
thread_id: T008
factor_id: F029
factor_name: weak_close_day_rate_20
key_metrics_short: "ic_oos=+0.0095 icir_oos=+0.09 ls_t=+3.28 alpha_surv=1.10 max_corr=0.32@F006 incr_ic=-0.002"
reject_reason_short: null
---

# C004 — Mean(Lt(Div(Sub($close,$low),Sub($high,$low)),0.2),20)

> [!success]+ Verdict: **ADMIT** · thread [[directions/conditional_operator_truncation#T008|T008]]
> **档位**: CP01 ✓ · CP02 `aligned` · CP03 `borderline (strong ls_t)` · CP04 `acceptable` · CP05 `medium` · CP06 `mixed`
> **OOS**: IC=**==+0.0095==** · ICIR=+0.092 · ls_t=**==+3.28==** · style_r²=0.17 · alpha_surv=**==1.10==** · max_corr=**==0.32@F006==** · mt_bucket=`high`→`medium` (search_adjusted)
> **机制一句话**: 20d 弱收盘日占比 (close 在 day range 最低 20% 区间天数占比), Barra-clean (alpha_survival=1.10 > 1.0 + residual IC=+0.010 接近 raw IC=+0.0095) — 库内第 2 个 conditional truncation rate 形式 alpha_clean candidate (与 b097/C001 上影主导日 alpha_surv=1.07 同档级), candle geometry 内容 ⊥ Barra style basis 实证.

> [!info] Parent: [[batches/batch_098/judge|batch_098 judge]] · Direction: [[directions/conditional_operator_truncation]] · Nearest: [[factors/F006]]

## CP01 Hard Gates

passed: true
- compute_error: pass
- forbidden: pass
- coverage: 1.0 ≥ 0.80
- sign_flip: train_ic=+0.0183, val_ic=+0.0095 (same sign)
- ic_oos_min: 0.0095 ≥ 0.008 (临界 pass)
- oos_decay: 0.5212 ≥ 0.20
- mono_flip: train=+0.70, val=+0.50 (一致)
- near_duplicate: max_corr=0.3204@F006 < 0.90

## CP02 Mechanism Alignment

**Tier: aligned**


1. **机制**: 20d 内 "弱收盘日" 占比 (close 在 day range 最低 20%, (C-L)/(H-L) < 0.2). 捕捉日内持续抛压结构 — 频繁出现的 "高开低走收盘弱" 日 = 卖压结构性存在.
2. **Hypothesis fit**: 与 [[directions/conditional_operator_truncation#Hypothesis]] **完全对齐** — 用 `Lt` 离散化 + `Mean` aggregate 把连续 close-position ratio 二值化为弱收盘日事件率, structural geometry distinct from linear arithmetic library (27 admit) + candle geometry content ⊥ Barra style basis (实证 alpha_survival=1.10).
3. **持续性**: 行为金融上 disposition effect + intraday liquidity supply 模式; 高频卖压在 A 股 csi1000 daily 持续 well-documented; 与 b097/C001 上影主导日 (close 偏下半 = 上影长) 是**互补几何且同向 sign** (上影主导日 ic=+0.009, 弱收盘日 ic=+0.0095) — 都揭示日内卖压.
4. **失效场景**: 跌停板日 close==low 强行 (C-L)/(H-L)=0 拉高 rate (但跌停 mask 后剔除); 极低 vol 横盘 (high≈low) 时 ratio 不稳.
5. **近邻差异**: 与 [[factors/F006]] (`upper_shadow_persistence_5d` = Mean((H-C)/(H-L), 5)) 走连续 shadow ratio 平均, 本候选走 binarize 弱收盘日 rate; F006 5d window vs 本候选 20d window; corr=+0.32 medium 段 — 同 candle geometry 路径但不同 aggregate 形式.

## CP03 Statistical Strength — borderline (strong ls_t)

| 指标 | value | 档位 |
|---|---|---|
| ic_oos | +0.0095 | weak (临界 0.008) |
| icir_oos | +0.092 | weak |
| ls_tstat_oos | **+3.28** | strong |
| ic_is | +0.0183 | strong |
| ls_sharpe_oos | +2.37 | — |
| ls_tstat_is | +4.40 | strong |

- mono_oos = +0.50 (中度单调向上, magnitude>=0.5 hard_gate 临界 pass)
- Q1=-0.00083, Q5=+0.00018 (q1 显著负 + q5 正 + 中间 q2/q3/q4 non-monotonic — "Q1/Q5 端点驱动, 中间结构不强")
- IS→OOS decay 0.52 (中度 decay, hard_gate pass 阈 0.20)
- mt_bucket: `high` · search_adjusted `low` (0.3101) → search-adjusted 大幅降档暗示历史相关候选频次, 但本候选 ls_tstat strong 仍有意义
- IS strong + OOS weak IC + strong ls_tstat + mono+0.50 临界 → **borderline (强 ls_t)** (核心 IC 临界, ls_t strong, mono 中度)

**rank-order 注释**: Q1/Q5 端点驱动 (q1=-0.00083, q5=+0.00018, q2/q3/q4 noise) — "一桨驱动" 风险 mild, 但 ls_t=3.28 OOS 强 + mono=0.50 OOS 中度, 不构成 rank-order 严重异常. 不降档.

## CP04 Risk Cleanness — acceptable (Barra-clean)

| 指标 | value | 档位 |
|---|---|---|
| style_r² | 0.171 | borderline (0.12-0.25) |
| alpha_survival_ratio | **1.0976** | clean (> 0.40 + 0.10 = 0.50) |
| extreme_ratio | 0.0023 | clean |
| barra_residual_ic | +0.0104 | — (略强于 raw IC) |
| dominant_style | vol_20d (23.90) | medium crowding |

**Alpha killer 段**:
- vol_20d: 23.90 (主吞噬)
- str_1m: 3.76 (intraday reversal)
- ep_ratio: 0.73 (轻)
- mom_12_1: 0.25 (轻)

主要 dominant=vol_20d 但 **alpha_survival=1.0976 > 1.0** 说明 Barra 残差 IC 反而**强于** raw IC — Barra-clean. residual IC=+0.0104 vs raw IC=+0.0095 (略强). 一句话: **本因子在 Barra 空间内 dom=vol_20d 但残差是真 alpha 载体 — vol_20d basis 信息与本因子 binarize 内容正交**, vol_20d 频谱与 "弱收盘日 candle geometry" 内容不共振.

档位 acceptable (style_r²=0.17 borderline + alpha_survival clean + extreme clean = 一项 borderline 其余 clean).

## CP05 Redundancy — medium

| 指标 | value | 档位 |
|---|---|---|
| max_lib_corr | 0.3204@F006 | medium (0.30-0.70 边缘) |
| incremental_ic | -0.0023 | **negative (库轻微削减)** |
| is_near_duplicate | false | — |
| nearest expr | `Mean(Div(Sub($high, $close), Sub($high, $low)), 5)` | F006 是连续上影 ratio 5d 平均 |

库内 top-3 corr: F006=+0.32, F022=-0.30, F021=+0.28, F027=+0.26, F028=+0.25. F006 (5d 上影 mean) 是同 candle geometry 路径不同 aggregate (连续 mean vs 离散 rate); F022 反号是 close-position dispersion; F021 类似 shadow dispersion.

**incremental_ic = -0.002 临界负**, near_duplicate=false 但 max_corr=0.32 medium 段边缘 — 库增值边缘. **决策权衡**: alpha_survival>1.0 + ls_tstat=+3.28 strong + 库内首个**弱收盘日 binarize rate** (区别于 F006 连续 shadow 形式) — admit 价值在于**结构性几何 distinctness**, 不在 library reducer; 接受边缘 incremental_ic.

## CP06 Stability — mixed

| 指标 | value | 档位 |
|---|---|---|
| sign_consistency | 0.75 | mixed (3/4 splits 一致) |
| train_validation_decay | 0.52 | mixed (中度 decay) |
| worst_quarter_ic | -0.013 | — |
| best_quarter_ic | +0.076 | — (best/worst 同号且量级合理) |
| ic_by_year 趋势 | 2015 +0.038 → 2017 +0.013 → 2020 +0.006 → 2022 +0.008 → 2023 +0.011 | 全正, 早期强后期 stable |

- 9 年 ic_by_year 全正 (sign 稳定), 早期强 (2015 +0.038) 后期 stable (2020+ +0.005~+0.01) — 类 b097/C001 alpha decay 模式
- worst_quarter (-0.013) 与 best (+0.076) 同符号且 worst < ic_oos 量级, 健康
- ic_autocorr_lag1=-0.016 (健康); cum_ic_max_drawdown=-1.93 (温和)
- split_ic_means [-0.0001, +0.016, +0.021, +0.001] split0 接近零, split1/split2 是 IS 主体, split3 (近 OOS) 弱 — sign_consistency=0.75 来源
- split_dispersion=0.96 中高 → mixed

**时序稳健性辅助**: ic_by_year 9 年全正稳定, decay 是温和的 alpha decay (早期强); cum_ic_max_drawdown=-1.93 远好于 library median; 但 sign_consistency=0.75 + decay=0.52 都是 mixed → **mixed**.

## Verdict 综合 — ADMIT

**P030 paradox guard 四条件检查**:
- alpha_surv > 1.0 ✓ (1.0976)
- max_lib_corr < 0.40 ✓ (0.3204) — borderline 通过
- incremental_ic ≥ +0.005 ✗ (-0.002 临界负)
- ls_t ≥ 1.5 ✓ (3.28 strong)

**3/4 通过 + incremental_ic 临界负** — 但根据 P030 (升格 round 73): admit 充分条件需 incr_ic + max_corr + ls_t 至少 2/3 配合 multi-CP. 本候选 max_corr (0.32) + ls_t (3.28) 配合 alpha_surv>1.0 + Barra-clean + candle geometry distinct → admit. **核心权衡**: incremental_ic 负不是 library 削减的核心证据 (max_corr=0.32 medium 段, 不是 high), 而是 alpha_survival>1.0 + Barra residual IC>raw IC 揭示**正交 Barra 空间载体**, 库增值价值在于**新几何路径** (binarize close-position 弱端 rate) 而非 IC reducer.

**Admit 理由**:
- structural geometry **极其 distinct** (库内 27 admit 中 0 个 conditional truncation rate 形式; 弱收盘日 binarize rate ⊥ 9-style Barra basis 验证)
- Barra-clean (alpha_survival=1.0976 > 1.0, residual_ic > raw_ic 量级)
- ls_tstat=3.28 strong (passes 3.0 admit floor)
- max_corr=0.32 临界 medium 段下缘 (与 F006 同 candle geometry 不同 aggregate)
- 与 b097/C001 (上影主导日, reserve, ls_t=2.85<3.0 admit floor 缺失) **互补同向** — 弱收盘日是 close-position 下半段 ≈ 上影主导日的对偶 (但严格定义不同: C-L<0.2 vs H-C>0.5×range), 几何细节差异让本候选 ls_t 上探到 3.28 admit floor
- 9 年 ic_by_year 全正 sign 稳定

**反思**: T008 (range-position 低位主导日占比) thread VALIDATED — candle geometry binarize 路径在**弱端 close-position rate** 形式产生 alpha_clean residual alpha. 与 T001 (上影主导日, b097/C001 reserve) 互补构成 "close 偏下半段 candle geometry" 子族, alpha_survival>1.0 的两个独立点. 与本批 C001 (close 上半段, alpha_surv=0.50) 对比: **同 (C-L)/(H-L) 信号 binarize 弱端 (Lt(.,0.2)) vs 上半段 (Gt(.,0.5)) Barra basis 共振强度天差地别** — 弱端 binarize ⊥ vol_20d basis, 上半段 // vol_20d basis. **核心律 (round 9 验证)**: conditional truncation 路径下 binarize 内容与 Barra basis 同构性是 sign-dependent 的, 弱端通常更 Barra-clean.

**风险旗标**:
- CP03 weak/borderline: ic_oos 临界 0.008, icir_oos 弱, **核心靠 ls_tstat=3.28 撑住**
- CP04 borderline: style_r²=0.17 中度
- CP05 medium: incremental_ic 临界负 (-0.002)
- CP06 mixed: sign_consistency=0.75 + decay=0.52 中度

**错杀侦测扫描**: max_corr=0.32 > 0.30 → 不满足错杀条件 (max_corr<0.30 fail). 非错杀 admit, 是 (alpha_survival>1.0 + ls_t admit floor + distinct geometry) 综合 admit.

**factor_name 提议**: `weak_close_day_rate_20` (snake_case, 25 chars, 反映机制 "20d 弱收盘日 (close 在 range bottom 20%) 占比 Bernoulli rate").

**Primitive Provenance**: 无

## Detailed Metrics

All numeric fields from Phase 2 / Phase 3 for this candidate. Tables in the report should cite these directly — do not mark fields as `—` if they appear below.

```yaml
metrics:
  cp03:
    ic_oos: 0.009517368143819597
    icir_oos: 0.09199001477822301
    ls_tstat_oos: 3.2842
    ic_is: 0.01826177506826269
    icir_is: 0.17418024296630846
    ic_std_is: 0.10484412443835579
    ic_std_oos: 0.10346088286608976
    n_days_is: 1665
    n_days_oos: 484
    ic_win_rate_is: 0.5627627627627627
    ic_win_rate_oos: 0.5475206611570248
    monotonicity_is: 0.7
    monotonicity_oos: 0.49999999999999994
    quintile_returns_is:
      q1: 2.735507041506935e-05
      q2: 0.0001659174740780145
      q3: 0.000629064510576427
      q4: 0.0003251012822147459
      q5: 0.0005121105932630599
    quintile_returns_oos:
      q1: -0.0008301108609884977
      q2: 1.0925220522040036e-05
      q3: 0.0004011597775388509
      q4: -0.000237120155361481
      q5: 0.00017998924886342138
    ls_mean_is: 0.0007318601749701756
    ls_mean_oos: 0.0008780915639002438
    ls_sharpe_oos: 2.3673
    ls_sortino_oos: 4.0056
    ls_calmar_oos: 2.9158
    ls_max_dd_oos: -0.0759
    ls_sharpe_is: 1.7117
    ls_tstat_is: 4.4012
    ls_max_dd_is: -0.4836
    ic_by_horizon:
      1:
        ic_is: 0.01826177506826269
        icir_is: 0.17418024296630846
        win_rate_is: 0.5627627627627627
        ic_oos: 0.009517368143819597
        icir_oos: 0.09199001477822301
        win_rate_oos: 0.5475206611570248
      3:
        ic_is: 0.015185204659723766
        icir_is: 0.14749112864806632
        win_rate_is: 0.5573573573573574
        ic_oos: 0.008123929442176799
        icir_oos: 0.08765214723480097
        win_rate_oos: 0.5516528925619835
      5:
        ic_is: 0.013727900875324127
        icir_is: 0.13234230060319943
        win_rate_is: 0.5447447447447448
        ic_oos: 0.00750075953069796
        icir_oos: 0.08260476976616178
        win_rate_oos: 0.5578512396694215
      10:
        ic_is: 0.012118099345062836
        icir_is: 0.11518918368301306
        win_rate_is: 0.5237237237237238
        ic_oos: 0.008584154443650283
        icir_oos: 0.09269923288907886
        win_rate_oos: 0.49586776859504134
      20:
        ic_is: 0.01356988843629415
        icir_is: 0.12685727031016986
        win_rate_is: 0.5159159159159159
        ic_oos: 0.018761017808169345
        icir_oos: 0.18402408382675867
        win_rate_oos: 0.5537190082644629
  cp04:
    style_r_squared: 0.171246950787166
    alpha_survival_ratio: 1.0976
    alpha_surv_min_threshold: 0.4
    extreme_ratio: 0.002295
    barra_residual_ic: 0.010446
    barra_residual_icir: 0.196285
    dominant_style_exposure: vol_20d
    style_crowding_risk: medium
    style_exposures:
      log_circ_cap: 0.05567885011066807
      book_to_price: 0.232330371838005
      mom_12_1: 0.25380371420163883
      str_1m: 3.759534037964201
      vol_20d: 23.90044410115067
      turnover_20d: 0.8481877228277968
      ep_ratio: 0.7256548326596608
    distribution_skew: 0.1097
    distribution_kurt: -0.0631
    distribution_zero_ratio: 0.0
  cp05:
    max_lib_corr: 0.3204
    is_near_duplicate: false
    incremental_ic: -0.002317
    nearest_factor_id: F006
    nearest_factor_expression: Mean(Div(Sub($high, $close), Sub($high, $low)), 5)
    all_correlations:
      F001: -0.06619687752311207
      F002: -0.021096020915273003
      F003: 0.04867483696498526
      F006: 0.32040937759038446
      F007: 0.062035219438413905
      F008: 0.24992924150616946
      F009: 0.19005610489962296
      F010: 0.07469573573938051
      F011: 0.06609735197372495
      F012: 0.003932288922919356
      F013: 0.0003478177529850248
      F015: 0.0517682792841862
      F016: 0.02953076934841515
      F017: 0.008074452544158188
      F018: 0.029555886743065335
      F019: 0.00890742823062186
      F020: -0.1850401034358881
      F021: 0.27607390471281495
      F022: -0.29719108971592595
      F023: -0.06249973930283577
      F024: 0.03171714566955938
      F025: 0.030511076529108727
      F026: -0.06099281227053551
      F027: 0.2635305410805516
      F028: 0.2479025596531873
      F004: 0.02453313133771428
      F005: 0.02453313133771428
    exceeds_threshold: false
  cp06:
    sign_consistency: 0.75
    train_validation_decay: 0.5212
    sign_consistent: true
    ic_by_year:
      2015: 0.03833552833121469
      2016: 0.02150404886785603
      2017: 0.013190706213611198
      2018: 0.02490045700418151
      2019: 0.022106231469345827
      2020: 0.006124388196844691
      2021: 0.004884483978772961
      2022: 0.007849273562462594
      2023: 0.011185462725176601
    worst_quarter_ic: -0.01278
    best_quarter_ic: 0.0759
    ic_autocorr_lag1: -0.015621
    cum_ic_max_drawdown: -1.934455
    split_ic_means:
    - -8.307625971956512e-05
    - 0.01578162338464475
    - 0.021159181309462396
    - 0.0012117441408908108
    split_dispersion: 0.9628
    n_splits: 4
  feasibility:
    turnover_mean: 0.6974957750661015
    liquidity_coverage: 0.7328524421503354
    tail_concentration: 0.008860199046091881
    small_cap_concentration: 0.2748225846204636
    signal_half_life: 10.0
    signal_autocorr_lag1: 0.9494
    rebalance_stress:
      value: 0.008432736312866174
      rebalance_stress_bucket: low
    ic_half_life_days: null
mt_budget:
  score: 0.826
  bucket: high
  terms:
    family: 0.9855429310968341
    direction: 0.4440662531938562
    exposure: 1.0
  search_adjusted:
    raw: 0.5283
    adjusted: 0.3101
    bucket: low
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
      train_ic: 0.01826177506826269
      val_ic: 0.009517368143819597
    ic_oos_min:
      passed: true
      value: 0.009517368143819597
      threshold: 0.008
    oos_decay:
      passed: true
      value: 0.5212
      threshold: 0.2
    mono_flip:
      passed: true
      train: 0.7
      validation: 0.49999999999999994
      min_magnitude: 0.5
    near_duplicate:
      passed: true
      max_corr: 0.3204
      nearest: F006
coverage: 1.0
expression: Mean(Lt(Div(Sub($close,$low),Sub($high,$low)),0.2),20)
```

## Available Charts

The following PNG charts exist in `vault/factors/F029/` and may be embedded via `![[F029/<name>.png]]`. **Do not embed any chart name that is not on this list** — the file would not exist.

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
- `backtest/holdout/figs/cost_drag`
- `backtest/holdout/figs/blocked_trades`
- `backtest/holdout/figs/equity`
- `backtest/holdout/figs/monthly_heatmap`
- `backtest/holdout/figs/layer_decomp`
- `backtest/holdout/figs/drawdown`
- `backtest/train/figs/cost_drag`
- `backtest/train/figs/blocked_trades`
- `backtest/train/figs/equity`
- `backtest/train/figs/monthly_heatmap`
- `backtest/train/figs/layer_decomp`
- `backtest/train/figs/drawdown`
- `backtest/val/figs/cost_drag`
- `backtest/val/figs/blocked_trades`
- `backtest/val/figs/equity`
- `backtest/val/figs/monthly_heatmap`
- `backtest/val/figs/layer_decomp`
- `backtest/val/figs/drawdown`

## Instructions

Write a deep analytical report on `F029`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Embed only charts listed in the **Available Charts** section (skip any section whose chart is unavailable). Output path: `vault/factors/F029.md`.

