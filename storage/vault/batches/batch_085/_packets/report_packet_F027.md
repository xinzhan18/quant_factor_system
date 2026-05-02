---
factor_id: F027
direction: alpha191_universal_subset
admitted_in_batch: batch_085
---

# Report Packet — F027

## Factor YAML Summary

```yaml
name: multi_ma_reversion_4w
expression: Div(Add(Add(Add(Mean($close,3),Mean($close,6)),Mean($close,12)),Mean($close,24)),Mul($close,4))
source_type: dsl
family_tag: alpha191_universal_subset
validation_metrics:
  ic_mean: 0.04946905842592712
  ic_ir: 0.3094711692835281
  ic_win_rate: 0.5909090909090909
  monotonicity: 0.7
  long_short_mean: 0.0018607199806955736
  long_short_sharpe: 3.1435
risk_metrics:
  style_r_squared: 0.558006499019543
  alpha_survival_ratio: 1.1256
```

## Judge Synthesis

---
candidate_id: C001
batch_id: batch_085
direction: alpha191_universal_subset
expression: "Div(Add(Add(Add(Mean($close,3),Mean($close,6)),Mean($close,12)),Mean($close,24)),Mul($close,4))"
verdict: admit
thread_id: T001
factor_id: F027
factor_name: multi_ma_reversion_4w
key_metrics_short: "IC_oos=0.049 ICIR=0.31 ls_t=4.36 alpha_surv=1.13"
reject_reason_short: null
---

# C001 — Div(Add(Add(Add(Mean($close,3),Mean($close,6)),Mean($close,12)),Mean($close,24)),Mul($close,4))

> [!success]+ Verdict: **ADMIT** · thread [[directions/alpha191_universal_subset#T001|T001]]
> **档位**: CP01 ✓ · CP02 `aligned` · CP03 `strong` · CP04 `poor` · CP05 `medium` · CP06 `stable`
> **OOS**: IC=**==0.049==** · ICIR=**==0.31==** · ls_t=**==4.36==** · style_r²=0.56 · alpha_surv=**==1.13==** · max_corr=0.54@F009 · incr_ic=**==0.034==** · mt_bucket=`medium`
> **机制一句话**: 4 窗 MA(3/6/12/24) 算术均值除以 4×close 的 mean-reversion 复合比，paper-vetted Du-Walter-Ulrich 三估计器 top.

> [!info] Parent: [[batches/batch_085/judge|batch_085 judge]] · Direction: [[directions/alpha191_universal_subset]] · Nearest: [[factors/F009]]

## 表达式解读

`(Mean($close,3) + Mean($close,6) + Mean($close,12) + Mean($close,24)) / (4 * $close)` — 把 spot price 与 4 个不同窗口移动均值的算术均值做比值。值 > 1 → spot 低于多窗均值（mean-reversion long signal）；值 < 1 → spot 高于多窗均值（mean-reversion short signal）。多窗 vote 使单窗 phase 噪声相互抵消，对短期 (3d/6d) 动量 vs 长期 (12d/24d) 趋势的相对位置同时编码。

## CP01 Hard Gates ✓

8 项 gate 全过：
- ✓ compute_error
- ✓ coverage: 1.00 ≥ 0.80
- ✓ sign_flip: train +0.067 / val +0.049（同号）
- ✓ forbidden
- ✓ ic_oos_min: |+0.049| ≥ 0.008
- ✓ oos_decay: 0.74 ≥ 0.20（健康衰减）
- ✓ mono_flip: train +0.7 / val +0.7（同号）
- ✓ near_duplicate: max_corr 0.54 < 0.9（nearest F009）

## CP02 Mechanism Alignment · `aligned`

**机制**：Multi-window MA composite mean-reversion ratio. 4 窗 (3d/6d/12d/24d) MA 算术均值除以 4×spot price，构造一个 dim-less ratio，量度 spot 相对中-长期组合 MA 的偏离程度。值偏 1 表示反转潜力。

**与 hypothesis 一致性**：[[directions/alpha191_universal_subset#Hypothesis]] 假设 paper-vetted 17 因子白名单中 multi-window MA composite 是库内未覆盖的 mechanism family。Du-Walter-Ulrich 2026 在 Alpha191 → SPX 跑 DS-LASSO 控制 151 fundamental 后，本因子在 3×2 t=3.68 / 5×5 t=4.33 / PCA t=5.29 / ENet t=4.34 三估计器同时显著（最强）。csi1000 散户主导小盘，paper 自身 narrative 推断"应更强"，本批实测 IC_oos=0.049 (vs paper SPX monthly t≈3.68 → 等价 daily IC ~0.03 量级) 验证了"reverse cross-market transfer"假设。

**持续性**：mean-reversion 在 csi1000 散户市的持续性来自 (a) 散户追涨卖跌过度反应; (b) 涨停板硬约束让短期 momentum 受限。多窗 vote 比单窗对 phase 噪声更鲁棒。

**失效场景**：(a) 趋势性单边市（牛尾/熊尾）时多窗均值无法围绕 spot 构成 reversion；(b) 行业突发事件冲击单股；(c) 涨跌停板长期挂单时 close 失真。

**与近邻差异**：[[factors/F009]] (overnight_intraday_spread_5d) 度量隔夜 gap 与日内 close-open spread 的差，是 5d 短窗 close-open / open-prev_close 隔夜机制；本候选 multi-window close MA reversion 是 close-only 中-长期 (3-24d) MA 几何，机制核心不同。max_corr=0.54 显示 cross-section 上有 ~30% variance 共享（隔夜 mean-reversion 元素 + 短窗 MA），但 incr_ic=**==0.034==**（远 > 0.005）证明库增值清晰。

→ **aligned**

## CP03 Statistical Strength · `strong`

| 指标 | IS | OOS | 档位 | 阈值 |
|---|---|---|---|---|
| IC | 0.067 | **==0.049==** | strong | \|x\|>0.015 |
| ICIR | 0.41 | **==0.31==** | strong | \|x\|>0.30 |
| ls_t | 6.49 | **==4.36==** | strong | \|x\|>3 |
| decay | — | 0.74 | healthy | >0.5（边界 healthy）|

**Rank-order 验证**：monotonicity_oos = 0.7（healthy 但非完美）。Q1..Q5 OOS 梯度: q1=-0.00157, q2=+0.00008, q3=+0.00033, q4=+0.00044, q5=+0.00030 → q1 强烈负收益, q2-q5 单调上升至 q4 后 q5 略回落。LS spread 由 q5-q1 = 0.00187 (= ls_mean_oos) 主导，符合 "long-short with q1 worst" 几何，非"一桨 q5 独大"。

**样本量**：n_days_oos=484（>> 200，统计显著性充足）。

**MT 调整**：`mt_bucket = medium` (raw_score 0.68, terms family=0.96 high / direction=0 / exposure=1.0)；`search_adjusted = 0.59` (raw 0.9 → adjusted 0.59, bucket medium)。本方向 direction_candidates=0 (首批) 所以 direction term=0 把 score 拉低。medium 档允许 strong 保留，经 search adjustment 后系数仍高于 strong 档下界，符合 MT budget。

→ **strong**

## CP04 Risk Cleanness · `poor`

| 指标 | 值 | 档位 | 阈值 |
|---|---|---|---|
| style_r_squared | **==0.56==** | poor | <0.12 clean |
| alpha_survival | **==1.13==** | clean | clean>0.50 (default 0.40+0.10) |
| extreme_ratio | 0.0159 | borderline | <0.01 clean |
| barra_residual_ic | 0.0557 | — | — |
| dominant_style | `vol_20d` | — | — |

**Alpha killer** (style_contributions 不在 stdout 直接给出 leave-one-out 列表，但 style_exposures 高位前 2-3 项可读为 dominant exposures):
- `vol_20d`: exposure 18.02 (顶级 — vol_20d 结构性吸收律 lessons P008)
- `str_1m`: exposure 7.42
- `turnover_20d`: exposure 1.72
- `ep_ratio`: exposure 0.48

**重点**：style_r²=0.56 极高（vol_20d dominate 18.0 暴露），属 lessons.md "vol_20d 结构性吸收律" 顶级吸收形态。然而 **alpha_survival_ratio=1.13** 远超 1.00 — 即 Barra residual IC = 0.056 比 raw IC = 0.049 还**高** — 说明剥离 Barra 风格暴露后 alpha 不仅未消亡，反而**轻微增强**。这是 lessons "vol_20d 结构性吸收律段(a) Python Barra residual orthogonalize" 在 numerator 自身有 OOS-stable alpha 时生效的实证（C001 ic_by_year 9 年同号且稳定）。

style_r² high + alpha_survival > 1.0 看似矛盾——实则 dominant_style basis 共线但 alpha 信号正交于 Barra 线性组合，符合 P008 escape 机制：linear OLS 不破 vol_20d 非线性吸收, 但 alpha 在 vol_20d 非线性 manifold 之外。

→ **poor**（按 rubric 严格分档：style_r² 0.56 > 0.25 poor）。但符合 CP04 与 verdict 关系（2026-04-19 relaxed）：alpha_survival>1.0 + library 增值 (incr_ic=0.034) → 不自动 reject。

## CP05 Redundancy · `medium`

- `max_lib_corr` = **==0.54==**@[[factors/F009]] → medium 档 (0.30-0.70)
- `is_near_duplicate` = false
- `incremental_ic` = **==0.034==**（>> 0.005, 库增值极强）
- 次高 corr: F007 (0.51) / F006 (0.48) / F008 (0.44) — overnight_intraday_split family 集群

→ **medium**。admit 增值：incr_ic=0.034 是 lessons.md `max_lib_corr_low` 阈值 0.30 上方 6.8 倍，比典型 "borderline" 增量 (~0.005) 高 7 倍量级。即使 max_corr=0.54 medium，引入 multi-window MA reversion 几何仍贡献清晰 alpha——库内此 mechanism family 完全空缺。

## CP06 Validation Stability · `stable`

| 指标 | 值 | 档位 |
|---|---|---|
| sign_consistency | **==1.0==** | stable |
| train_validation_decay | **==0.74==** | mixed (0.5-0.8) |

**时序稳健**：
- `ic_autocorr_lag1` = -0.034（|x|<0.15 → IC 日独立, ICIR 置信高）
- `cum_ic_max_drawdown` = -1.50（远 > -30, 几乎无回撤）
- `worst_quarter_ic` = +0.011 / `best_quarter_ic` = +0.129（同号 + 正向）— 全样本季度都正
- `ic_by_year` (2015-2023): 0.070→0.084→0.059→0.070→0.080→0.048→0.055→0.052→0.047 — 9 年**全部同号** (positive), 量级稳定 (0.05-0.08), 无衰减趋势
- `split_dispersion` = 0.20 (4-fold split mean dispersion 低)

→ **stable**（核心 sign_consistency stable + decay 0.74 处 mixed 上界，但时序稳健全面 healthy: cum_ic_mdd 仅 -1.50, 9 年同号无衰减, dispersion 低 → 整体 stable, decay mixed 不下调）

> [!success]+ Verdict: ADMIT
> **核心理由**: paper-vetted Alpha191 universal-subset 首批兑现首例。CP03 全 strong (IC=0.049 / ICIR=0.31 / ls_t=4.36), incr_ic=0.034 远超阈值, 9 年同号 + cum_ic_mdd 仅 -1.50 时序极稳。CP04 style_r²=0.56 poor 看似阻断, 但 alpha_survival=1.13>1.0 证明 alpha 在 vol_20d 非线性 manifold 之外, 符合 lessons P008 escape 机制层验证。库内无 multi-window MA composite mechanism family, 引入新几何无库重复。
>
> **风险旗标**:
>   - CP04 style_r² 0.56 极高 (vol_20d 暴露 18.0): vol_20d 结构性吸收律高位形态, 后续同 family 续探需走 cross-family rhs_change 或高阶 composition (P028 衍生律)
>   - CP05 max_corr=0.54@F009 medium-high: 与 overnight_intraday_split family 有 ~30% variance 共享; 后续若设计 multi-MA 衍生品需以 F009 为 anchor 验证独立性
>   - CP06 train_validation_decay 0.74 在 mixed 上界 (近 stable): 时序长尾 healthy 但 train_ic 0.067 → val_ic 0.049 衰减 26%, 线性外推 next regime 可能继续轻微衰减
>
> F{id} 由 Phase 4 分配，本文件 frontmatter `factor_id: null`。

## Detailed Metrics

All numeric fields from Phase 2 / Phase 3 for this candidate. Tables in the report should cite these directly — do not mark fields as `—` if they appear below.

```yaml
metrics:
  cp03:
    ic_oos: 0.04946905842592712
    icir_oos: 0.3094711692835281
    ls_tstat_oos: 4.361
    ic_is: 0.06659346719555365
    icir_is: 0.4076782420971764
    ic_std_is: 0.16334810229995073
    ic_std_oos: 0.1598502973328836
    n_days_is: 1665
    n_days_oos: 484
    ic_win_rate_is: 0.6792792792792792
    ic_win_rate_oos: 0.5909090909090909
    monotonicity_is: 0.7
    monotonicity_oos: 0.7
    quintile_returns_is:
      q1: -0.0010751429945230484
      q2: 0.0004904451780021191
      q3: 0.0007455286104232073
      q4: 0.0007795490091666579
      q5: 0.0007317794370464981
    quintile_returns_oos:
      q1: -0.0015717970672994852
      q2: 7.942952652228996e-05
      q3: 0.0003302758850622922
      q4: 0.00043679348891600966
      q5: 0.0002972697839140892
    ls_mean_is: 0.001738322370515384
    ls_mean_oos: 0.0018607199806955736
    ls_sharpe_oos: 3.1435
    ls_sortino_oos: 5.7554
    ls_calmar_oos: 5.0057
    ls_max_dd_oos: -0.0937
    ls_sharpe_is: 2.5241
    ls_tstat_is: 6.4901
    ls_max_dd_is: -1.2914
    ic_by_horizon:
      1:
        ic_is: 0.06659346719555365
        icir_is: 0.4076782420971764
        win_rate_is: 0.6792792792792792
        ic_oos: 0.04946905842592712
        icir_oos: 0.3094711692835281
        win_rate_oos: 0.5909090909090909
      3:
        ic_is: 0.05648625166526026
        icir_is: 0.37332611814105887
        win_rate_is: 0.6486486486486487
        ic_oos: 0.04557902831523621
        icir_oos: 0.3199809494412215
        win_rate_oos: 0.609504132231405
      5:
        ic_is: 0.05697010575607909
        icir_is: 0.38516418972261873
        win_rate_is: 0.6372372372372372
        ic_oos: 0.04504648989666678
        icir_oos: 0.33716288853416165
        win_rate_oos: 0.6446280991735537
      10:
        ic_is: 0.04819995771777677
        icir_is: 0.34195199820869265
        win_rate_is: 0.6198198198198198
        ic_oos: 0.04769342187666196
        icir_oos: 0.35228670832639186
        win_rate_oos: 0.6177685950413223
      20:
        ic_is: 0.05045018036015597
        icir_is: 0.36764138208072894
        win_rate_is: 0.6336336336336337
        ic_oos: 0.04972988868929828
        icir_oos: 0.36251001204455147
        win_rate_oos: 0.6053719008264463
  cp04:
    style_r_squared: 0.558006499019543
    alpha_survival_ratio: 1.1256
    alpha_surv_min_threshold: 0.4
    extreme_ratio: 0.015924
    barra_residual_ic: 0.055685
    barra_residual_icir: 0.558496
    dominant_style_exposure: vol_20d
    style_crowding_risk: high
    style_exposures:
      log_circ_cap: 0.05826221526227068
      book_to_price: 0.22235899574178614
      mom_12_1: 0.1707560586804362
      str_1m: 7.415586084268852
      vol_20d: 18.016280300083512
      turnover_20d: 1.7223369847585666
      ep_ratio: 0.4844792628629027
    distribution_skew: -0.3762
    distribution_kurt: 1.8837
    distribution_zero_ratio: 0.0
  cp05:
    max_lib_corr: 0.5443
    is_near_duplicate: false
    incremental_ic: 0.033663
    nearest_factor_id: F009
    nearest_factor_expression: Mean(Sub(Div(Sub($open, Ref($close, 1)), Ref($close,
      1)), Div(Sub($close, $open), $open)), 5)
    all_correlations:
      F001: -0.1610109507814883
      F002: -0.023673514873553105
      F003: -0.03164466614383974
      F006: 0.47650419936295735
      F007: 0.5115773333130449
      F008: 0.4376125222565769
      F009: 0.5443104593393899
      F010: -0.12921370723250353
      F011: -0.09422530038349052
      F012: -0.016116053081487225
      F013: 0.017300151520123208
      F015: 0.10951402883545264
      F016: 0.0487156566810087
      F017: -0.0230356565088462
      F018: -0.06039628943402269
      F019: -0.01619618480015228
      F020: -0.013448386099439939
      F021: -0.021109640372758556
      F022: 0.02520864881202049
      F023: -0.006991751140381155
      F024: 0.08237097106780486
      F025: -0.08946912842520675
      F026: -0.2661354243696503
      F004: 0.011408826028462018
      F005: 0.011408826028462018
    exceeds_threshold: false
  cp06:
    sign_consistency: 1.0
    train_validation_decay: 0.7429
    sign_consistent: true
    ic_by_year:
      2015: 0.06980409082875629
      2016: 0.08419046117520886
      2017: 0.059392221598665196
      2018: 0.0700645451846376
      2019: 0.0800486919193048
      2020: 0.04787646315452405
      2021: 0.05519492962954165
      2022: 0.051777914219854865
      2023: 0.04716020263199938
    worst_quarter_ic: 0.011314
    best_quarter_ic: 0.128905
    ic_autocorr_lag1: -0.034479
    cum_ic_max_drawdown: -1.498719
    split_ic_means:
    - 0.039136808995122105
    - 0.06441901944458762
    - 0.041576813537094734
    - 0.052743591726904016
    split_dispersion: 0.203
    n_splits: 4
  feasibility:
    turnover_mean: 1.3851483084898568
    liquidity_coverage: 0.8176788709790808
    tail_concentration: 0.00886019904609188
    small_cap_concentration: 0.25273839272906573
    signal_half_life: 4.0
    signal_autocorr_lag1: 0.7949
    rebalance_stress:
      value: 0.01500918044620917
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
      train_ic: 0.06659346719555365
      val_ic: 0.04946905842592712
    ic_oos_min:
      passed: true
      value: 0.04946905842592712
      threshold: 0.008
    oos_decay:
      passed: true
      value: 0.7429
      threshold: 0.2
    mono_flip:
      passed: true
      train: 0.7
      validation: 0.7
      min_magnitude: 0.5
    near_duplicate:
      passed: true
      max_corr: 0.5443
      nearest: F009
coverage: 1.0
expression: Div(Add(Add(Add(Mean($close,3),Mean($close,6)),Mean($close,12)),Mean($close,24)),Mul($close,4))
```

## Available Charts

The following PNG charts exist in `vault/factors/F027/` and may be embedded via `![[F027/<name>.png]]`. **Do not embed any chart name that is not on this list** — the file would not exist.

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

Write a deep analytical report on `F027`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Embed only charts listed in the **Available Charts** section (skip any section whose chart is unavailable). Output path: `vault/factors/F027.md`.

