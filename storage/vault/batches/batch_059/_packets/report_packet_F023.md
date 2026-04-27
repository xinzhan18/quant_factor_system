---
factor_id: F023
direction: overnight_intraday_split
admitted_in_batch: batch_059
---

# Report Packet — F023

## Factor YAML Summary

```yaml
name: gap_body_magnitude_amount_rd_20
expression: Sub(CsRank(Mean(Mul(Sub($open,Ref($close,1)),Sub($close,$open)),20)),CsRank(Mean($amount,60)))
source_type: dsl
family_tag: overnight_intraday_split
validation_metrics:
  ic_mean: 0.044194211928159685
  ic_ir: 0.37357777451849034
  ic_win_rate: 0.6508264462809917
  monotonicity: 0.9999999999999999
  long_short_mean: 0.0016591570770400693
risk_metrics:
  style_r_squared: 0.351445406037448
  alpha_survival_ratio: 0.4092
```

## Judge Synthesis

---
candidate_id: C004
batch_id: batch_059
direction: overnight_intraday_split
expression: "Sub(CsRank(Mean(Mul(Sub($open,Ref($close,1)),Sub($close,$open)),20)),CsRank(Mean($amount,60)))"
verdict: admit
thread_id: T011
factor_id: F023
factor_name: gap_body_magnitude_amount_rd_20
key_metrics_short: "ic_oos=0.044 icir=0.37 ls_t=4.89 mono=1.0/1.0 max_corr=0.57@F012 incr_ic=0.018 alpha_surv=0.41"
reject_reason_short: null
---

# C004 — Gap × body magnitude × amount_60

> [!success]+ Verdict: **ADMIT** · thread [[directions/overnight_intraday_split#T011|T011]]
> **档位**: CP01 ✓ · CP02 `aligned` · CP03 `strong` · CP04 `borderline` · CP05 `medium` · CP06 `stable`
> **OOS**: IC=**==0.044==** · ICIR=**==0.37==** · ls_t=**==4.89==** · style_r²=0.35 · alpha_surv=**==0.41==** · max_corr=0.57@F012 · incr_ic=**==0.018==** · mt_bucket=`high`
> **机制一句话**: overnight gap × intraday body magnitude 共方向乘积 20d 聚合 — T011 sign-product 短窗 magnitude-weighted 救活实证

> [!info] Parent: [[batches/batch_059/judge|batch_059 judge]] · Direction: [[directions/overnight_intraday_split]] · Nearest: [[factors/F012]]

## 表达式解读

LHS = `Mean( (Open - Ref(Close,1)) * (Close - Open), 20 )` = 20d Mean of (overnight gap) × (intraday body)。**magnitude × magnitude 直乘聚合**: 当 overnight gap 与 intraday body 同方向 (都涨或都跌) 且量级都大,乘积大正;反方向时乘积大负;平淡时乘积近零。

与 b058 C003/C005 的 `Sign(o)*Sign(i)` 纯 sign-product 区别: 本候选保留 magnitude 信息,共方向且量级大的 stocks 信号强,共方向但量级小的 stocks 信号弱——magnitude weighting 区分了 "强共振日" 与 "微小共振日"。

RHS = `Mean($amount, 60)` 60d amount level (与 F018 amount_20 / F022 amount_5/60 ratio 不同窗口结构)。

CsRank 做差: 共振强 + 60d amount level 高的 stocks 得 cross-section 高 rank → 未来 1d 正收益 (IC=0.044 9/9 年正)。

## CP01 Hard Gates ✓

8 项 gate 全过：
- ✓ `compute_error`
- ✓ `coverage`: 0.989 ≥ 0.80
- ✓ `sign_flip`: train_ic=0.035 / val_ic=0.044 (同号且 OOS > IS)
- ✓ `forbidden`
- ✓ `ic_oos_min`: |0.044| ≥ 0.008 (OOS IC = 5.5x 阈值)
- ✓ `oos_decay`: 1.28 ≥ 0.20 (OOS > IS,anti-decay 罕见健康)
- ✓ `mono_flip`: train=1.0 / val=1.0 (perfect mono 同号)
- ✓ `near_duplicate`: max_corr=0.575@F012 < 0.9

## CP02 Mechanism Alignment · `aligned`

**机制**: overnight gap 与 intraday body 都 = 价格变动信号,前者跨夜段 (close→open),后者日内段 (open→close)。两者**乘积 20d Mean 聚合**捕捉 "持续共振" — 即股票连续多日 overnight 与 intraday 同方向移动,这是 strong directional momentum 的精确刻画。**magnitude weighting** 让大幅度的共振主导 cross-section 排序。

**与 hypothesis 一致性**: [[directions/overnight_intraday_split#Hypothesis]] 假设 overnight 与 intraday 段携带独立可叠加信号。F009 (overnight − intraday spread) 捕捉**差异**, 本候选捕捉**同向共振**, 在数学上是不同的 second-order interaction (差 vs 乘),hypothesis fit 直接。

**持续性**: 共方向 momentum 在 csi1000 散户驱动市场持续存在 (买盘连续 → overnight 高开 + intraday 收高同时发生)。9 年逐年 IC 0.024-0.050 区间稳定,2023 年 IC=0.048 仍接近最强。

**失效场景**: 风格切换日 (大盘 reverse 日)、停牌后开盘日 (overnight gap 失真)、涨停 / 跌停 (intraday body 极端值)。但 csi1000 个股流动性 + reasonable size 让这些 corner case 不主导。

**与近邻差异**: [[factors/F012]] = `Mean(|return|/$amount, 20)` Amihud illiquidity 20d — 衡量单位成交额价格冲击。本候选 LHS 完全不同 (gap × body 共振 vs return / amount illiquidity),但 corr=0.575 — 共同点是两者都受 "高换手 + 大波动" 联合驱动 (低 amount 高 |return| ≈ 高 illiquidity ≈ 大共振日)。**机制本质不同**,corr 来自共同的市场微观结构暴露。incremental_ic=0.018 验证库增值。

→ **aligned**

## CP03 Statistical Strength · `strong`

| 指标 | IS | OOS | 档位 | 阈值 |
|---|---|---|---|---|
| IC | 0.035 | **==0.044==** | strong | \|x\|>0.015 |
| ICIR | 0.313 | **==0.374==** | strong | \|x\|>0.30 |
| ls_t | 10.67 | **==4.89==** | strong | \|x\|>3 |
| decay | — | **1.28** | anti-decay | >0.8 |

**Rank-order 验证**: monotonicity_oos=**1.0** (perfect monotone)。Q1..Q5 OOS: q1=-0.00109, q2=-0.00009, q3=0.000028, q4=0.000449, q5=0.000565 → 完美单调上升,q1 大幅下跌 (-0.00109) + q5 高位 (0.000565),ls_mean=0.00166,与 ls_tstat=4.89 一致。**双桨驱动** (q1 sell-off + q5 rally),非 "一桨"。

**IS/OOS 对比**: IC OOS=0.044 > IS=0.035 (anti-decay,罕见健康); ICIR OOS=0.37 > IS=0.31; ls_sharpe OOS=3.52 (vs IS 4.10)。decay=1.28 (OOS/IS) — 完全没有 OOS 衰减反而增强,极强健康信号。

**样本量**: n_days_oos=484 ✓ (远 > 200)。

**Cross-horizon**: ic_by_horizon 1d=0.044 → 5d=0.069 → 20d=0.118,信号在更长 horizon 显著放大 (ICIR 1d=0.37 → 20d=1.19),说明本因子是 **multi-horizon alpha** 不是单 horizon 噪声。

**MT 调整**: `mt_bucket=high` (raw 0.877, 受 family + direction 双高拖累),`search_adjusted=0.505` (adjusted bucket=medium)。high bucket 通常强制最高 borderline,但 search_adjusted 推回 medium 后允许 strong 保留,且 OOS IC=0.044 远超 strong 阈值 (0.015) 的 ~3 倍 + ls_t=4.89 远超 (3) 的 ~1.6 倍 + ICIR=0.37 > strong 阈值 0.30 + 9/9 年逐年正 + 跨 horizon 单调放大,**search adjustment 后仍稳健 strong**。

→ **strong**

## CP04 Risk Cleanness · `borderline`

| 指标 | 值 | 档位 | 阈值 |
|---|---|---|---|
| style_r_squared | **==0.351==** | poor | >0.25 |
| alpha_survival | **==0.409==** | borderline | clean>0.50 (threshold+0.10) |
| extreme_ratio | 0.0 | clean | <0.01 |
| barra_residual_ic | 0.018 | — | — |
| dominant_style | `vol_20d` | — | — |

**Alpha killer** (按 style_contributions 排序):
- `vol_20d`: exposure=9.79 (主载体)
- `turnover_20d`: exposure=6.39 (次载体)
- `str_1m`: exposure=0.62
- 总 killer: vol_20d + turnover_20d 主导,book_to_price=0.53、log_circ_cap=0.44 多 style 共载。本因子主要被 `vol_20d` + `turnover_20d` 联合吞噬 (~60% 风格暴露),但 alpha_surv=0.41 刚过 default threshold 0.40 → barra_residual_ic=0.018 仍 = raw IC 的 41%,**库空间内仍有结构性 alpha 残余**。下轮可考虑 vol_20d-orthogonalize 版本测试。

一项 poor (style_r²) 一项 borderline (alpha_surv) 一项 clean (extreme) → **borderline** (两项 borderline)。

**alpha_surv 是否阻断 admit?** 按 2026-04-19 放宽,CP04 档位纯描述性,不自动 reject。本候选 alpha_surv=0.41 > default threshold 0.40,且 max_lib_corr=0.575 不算 high (临界 0.70 以下),incremental_ic=0.018 >> 0.015 (F203 borderline corr 阈值),"Barra 空间内载体" 但 "库空间结构性独立"。Anchor rule 检查: 同批仅 C004 admit,不触发同 dom_style 多 admit 限制。

## CP05 Redundancy · `medium`

- `max_lib_corr` = **==0.575==** @ [[factors/F012]] → medium 档 (0.30-0.70)
- 次高: F018 (0.50, overnight sign × amount), F002 (0.45), F015 (0.39), F016 (0.38) — 与 F018 0.50 注意 (T011 sign-product family 与本候选 magnitude-product family 关联)
- `is_near_duplicate` = false
- `incremental_ic` = **==0.018==** (>>0.005 库增值清晰,>>0.015 F203 borderline corr 阈值)
- F022 (close-position rank-diff) corr=0.047 → 与 T012 admit 完全独立

→ **medium**。admit 增值: 与 F012 (illiquidity Mean) corr=0.57 但 incr_ic=0.018 验证 cross-section 排序结构不同;与 F018 (sign-product family 短窗 sign) corr=0.50 表明 magnitude-weighted 与 sign-only 仍部分相关 — 但 magnitude 信息让 cross-section rank 区分度提升。库增值 = "sign + magnitude joint information"。

## CP06 Validation Stability · `stable`

| 指标 | 值 | 档位 |
|---|---|---|
| sign_consistency | **==1.0==** | stable |
| train_validation_decay | **==1.28==** | stable (>0.8,且 OOS > IS) |

**时序稳健**:
- `ic_autocorr_lag1` = 0.024 (|x|<0.15 → IC 日独立,ICIR 置信高 ✓)
- `cum_ic_max_drawdown` = **-1.72** (浅,库内最浅之一 — 接近 F018 的 -1.53 / F019 的 -2.0 / F020 的 -2.2)
- `worst_quarter_ic` = **+0.0019** (永正,本批最稳!) / `best_quarter_ic` = 0.069
- `ic_by_year`: 2015 0.033, 2016 0.050, 2017 0.029, 2018 0.037, 2019 0.031, 2020 0.024, 2021 0.038, 2022 0.040, 2023 **0.048** → 9/9 年同号正且**近年 (2022-2023) 增强**, edge 不衰减反加强
- `split_ic_means` = [0.038, 0.042, 0.038, 0.058] dispersion=0.18 (<0.3 ✓ 4 split 全同号且方差小)

→ **stable** (核心两项都 stable,所有时序辅助项均 healthy + 多项库内最优)

> [!success]+ Verdict: ADMIT
> **核心理由**: T011 sign-product thread 在 b058 的 60d 版 (mono=1.0 但 alpha_surv 不足) reserve / 20d sign-only 版 (mono=0.4 cross-section 退化) reject 后,本候选用 **magnitude-weighted product** 替代纯 sign,在 20d 短窗下同时实现:(1) ls_t=4.89 远超 strong 阈值 + 9/9 年同号正 + IC anti-decay (OOS 0.044 > IS 0.035);(2) Q1 大幅下跌 + Q5 高位的 perfect mono=1.0 双桨结构;(3) cum_ic_mdd=-1.72 库内最浅之一 + worst_quarter=+0.0019 永正 + 2022/2023 近年 edge 增强;(4) max_corr=0.575@F012 medium + incremental_ic=0.018 远超 F203 0.015 borderline corr 阈值,库增值结构清晰;(5) hypothesis fit aligned (overnight × intraday joint magnitude 是 direction 第二个核心结构,与 F009 spread / F018 sign-freq 几何正交)。CP04 borderline (style_r²=0.35 + alpha_surv=0.41 刚过 default) 是已知 vol_20d 暴露,按 2026-04-19 放宽规则不阻断 admit。
>
> **风险旗标**:
>   - **CP04 borderline**: style_r²=0.35 poor (vol_20d=9.79 + turnover_20d=6.39 双载体),alpha_surv=0.41 刚过 default threshold 0.40 — Barra-space 残余 IC=0.018 仍是 raw 的 41%,但库 incr_ic=0.018 与 Barra 残余同量级,"Barra 载体 ∧ 库独立" 共存
>   - **CP05 medium**: max_corr=0.575@F012 borderline,与 F018 0.50 / F002 0.45 等多 factor 中等相关 — incr_ic=0.018 已超 F203 阈值,库增值清晰但需关注 cluster co-resonance
>   - **MT high bucket**: 本批 cumulative 312 推到 high,经 search_adjusted=0.505 推回 medium 允许 strong 保留;OOS IC=0.044 ≈ 3× strong 阈值,信号强度足以承受
>
> F{id} 由 Phase 4 分配,本文件 frontmatter `factor_id: null`。

## Detailed Metrics

All numeric fields from Phase 2 / Phase 3 for this candidate. Tables in the report should cite these directly — do not mark fields as `—` if they appear below.

```yaml
metrics:
  cp03:
    ic_oos: 0.044194211928159685
    icir_oos: 0.37357777451849034
    ls_tstat_oos: 4.8881
    ic_is: 0.03457067781383168
    icir_is: 0.3125139910995136
    ic_std_is: 0.11062121632443445
    ic_std_oos: 0.11829989614645098
    n_days_is: 1704
    n_days_oos: 484
    ic_win_rate_is: 0.6455399061032864
    ic_win_rate_oos: 0.6508264462809917
    monotonicity_is: 0.9999999999999999
    monotonicity_oos: 0.9999999999999999
    quintile_returns_is:
      q1: -0.0003895964182447642
      q2: 0.000325527013046667
      q3: 0.0005572923691943288
      q4: 0.0008269136887975037
      q5: 0.0018944281619042158
    quintile_returns_oos:
      q1: -0.001088648452423513
      q2: -8.992345101432875e-05
      q3: 2.793427847791463e-05
      q4: 0.00044902486843056977
      q5: 0.000564723159186542
    ls_mean_is: 0.0024316628138231935
    ls_mean_oos: 0.0016591570770400693
    ls_sharpe_oos: 3.5235
    ls_sortino_oos: 5.6016
    ls_calmar_oos: 3.4503
    ls_max_dd_oos: -0.1212
    ls_sharpe_is: 4.1026
    ls_tstat_is: 10.6715
    ls_max_dd_is: -4.7031
    ic_by_horizon:
      1:
        ic_is: 0.03457067781383168
        icir_is: 0.3125139910995136
        win_rate_is: 0.6455399061032864
        ic_oos: 0.044194211928159685
        icir_oos: 0.37357777451849034
        win_rate_oos: 0.6508264462809917
      3:
        ic_is: 0.045384101236938056
        icir_is: 0.40610880555628853
        win_rate_is: 0.6613849765258216
        ic_oos: 0.06045829238962142
        icir_oos: 0.5099925161498078
        win_rate_oos: 0.7066115702479339
      5:
        ic_is: 0.05223751579413609
        icir_is: 0.47076801185716466
        win_rate_is: 0.7001173708920188
        ic_oos: 0.06908672648804423
        icir_oos: 0.6051972906539906
        win_rate_oos: 0.743801652892562
      10:
        ic_is: 0.062271829435514195
        icir_is: 0.544949453542504
        win_rate_is: 0.710093896713615
        ic_oos: 0.08850565137975132
        icir_oos: 0.7850095946428653
        win_rate_oos: 0.7727272727272727
      20:
        ic_is: 0.0772319101555983
        icir_is: 0.6756868974521484
        win_rate_is: 0.7382629107981221
        ic_oos: 0.11752251231688927
        icir_oos: 1.189995387920707
        win_rate_oos: 0.859504132231405
  cp04:
    style_r_squared: 0.351445406037448
    alpha_survival_ratio: 0.4092
    alpha_surv_min_threshold: 0.4
    extreme_ratio: 0.0
    barra_residual_ic: 0.018086
    barra_residual_icir: 0.287391
    dominant_style_exposure: vol_20d
    style_crowding_risk: high
    style_exposures:
      log_circ_cap: 0.44063183348616225
      book_to_price: 0.5318730578598146
      mom_12_1: 0.2065838464537358
      str_1m: 0.6196202575870127
      vol_20d: 9.790958706130473
      turnover_20d: 6.389006117566486
      ep_ratio: 0.37132545128685374
    distribution_skew: -0.3121
    distribution_kurt: -0.5576
    distribution_zero_ratio: 0.0
  cp05:
    max_lib_corr: 0.5748
    is_near_duplicate: false
    incremental_ic: 0.018351
    nearest_factor_id: F012
    nearest_factor_expression: Mean(Div(Abs(Div(Delta($close, 1), Ref($close, 1))),
      $amount), 20)
    all_correlations:
      F001: 0.04712733187961891
      F002: 0.4527908782299938
      F003: 0.05721879493532591
      F006: -0.07565297282252322
      F007: 0.027951022407329742
      F008: -0.06319384497364149
      F009: 0.04702620665742021
      F010: 0.0842785075944845
      F011: 0.07753139587627127
      F012: 0.5747676213968899
      F013: 0.14897838382668957
      F014: 9.952417313951027e-05
      F015: 0.39294063372871163
      F016: 0.38439065878309253
      F017: 0.20144855204133086
      F018: 0.49581235645663524
      F019: 0.24246439342395693
      F020: -0.17263702180335852
      F021: 0.282087324670718
      F022: 0.04734417387888634
      F004: 0.04259347136767256
      F005: 0.04259347136767256
    exceeds_threshold: false
  cp06:
    sign_consistency: 1.0
    train_validation_decay: 1.2784
    sign_consistent: true
    ic_by_year:
      2015: 0.03283113645278814
      2016: 0.05032005357081139
      2017: 0.028678985032673184
      2018: 0.0373470719707721
      2019: 0.031385959419753744
      2020: 0.023518817325798098
      2021: 0.037885260164629404
      2022: 0.04028936323247759
      2023: 0.04809906062384178
    worst_quarter_ic: 0.001903
    best_quarter_ic: 0.06946
    ic_autocorr_lag1: 0.023783
    cum_ic_max_drawdown: -1.719276
    split_ic_means:
    - 0.038123892299106725
    - 0.04245483416584845
    - 0.038268164804801996
    - 0.057929956442881576
    split_dispersion: 0.1837
    n_splits: 4
  feasibility:
    turnover_mean: 0.36557579826393183
    liquidity_coverage: 0.6388893664666994
    tail_concentration: 0.006868282623238001
    small_cap_concentration: 0.31127781593914994
    signal_half_life: 13.0
    signal_autocorr_lag1: 0.9536
    rebalance_stress:
      value: 0.003930066822959711
      rebalance_stress_bucket: low
    ic_half_life_days: null
mt_budget:
  score: 0.8773
  bucket: high
  terms:
    family: 0.898275188293593
    direction: 0.7604254350734208
    exposure: 1.0
  search_adjusted:
    raw: 0.9
    adjusted: 0.5052
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
      value: 0.9885
      threshold: 0.8
    sign_flip:
      passed: true
      train_ic: 0.03457067781383168
      val_ic: 0.044194211928159685
    ic_oos_min:
      passed: true
      value: 0.044194211928159685
      threshold: 0.008
    oos_decay:
      passed: true
      value: 1.2784
      threshold: 0.2
    mono_flip:
      passed: true
      train: 0.9999999999999999
      validation: 0.9999999999999999
      min_magnitude: 0.5
    near_duplicate:
      passed: true
      max_corr: 0.5748
      nearest: F012
coverage: 0.9885
expression: Sub(CsRank(Mean(Mul(Sub($open,Ref($close,1)),Sub($close,$open)),20)),CsRank(Mean($amount,60)))
```

## Available Charts

The following PNG charts exist in `vault/factors/F023/` and may be embedded via `![[F023/<name>.png]]`. **Do not embed any chart name that is not on this list** — the file would not exist.

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

Write a deep analytical report on `F023`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Embed only charts listed in the **Available Charts** section (skip any section whose chart is unavailable). Output path: `vault/factors/F023.md`.

