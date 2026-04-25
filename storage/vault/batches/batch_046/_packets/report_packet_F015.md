---
factor_id: F015
direction: microstructure_illiquidity
admitted_in_batch: batch_046
---

# Report Packet — F015

## Factor YAML Summary

```yaml
name: amihud_cv_rank_diff_20
expression: Sub(CsRank(Mean(Div(Abs(Div(Delta($close, 1), Ref($close, 1))), $amount),
  20)), CsRank(Div(Std($amount, 10), Mean($amount, 10))))
source_type: dsl
family_tag: microstructure_illiquidity
validation_metrics:
  ic_mean: 0.05397926964924133
  ic_ir: 0.5441030154456679
  ic_win_rate: 0.7086776859504132
  monotonicity: 0.9999999999999999
  long_short_mean: 0.0016966479331228983
risk_metrics:
  style_r_squared: 0.35340326197844907
  alpha_survival_ratio: 0.6582
```

## Judge Synthesis

---
candidate_id: C003
batch_id: batch_046
direction: microstructure_illiquidity
expression: "Sub(CsRank(Mean(Div(Abs(Div(Delta($close, 1), Ref($close, 1))), $amount), 20)), CsRank(Div(Std($amount, 10), Mean($amount, 10))))"
verdict: admit
thread_id: T006
factor_id: F015
factor_name: amihud_cv_rank_diff_20
key_metrics_short: "ic_oos=0.054 mono_oos=1.0 ls_t=6.63 alpha_surv=0.66 incr_ic=0.031 max_corr=0.65"
reject_reason_short: null
---

# C003 — rank-diff Amihud minus amount CV

> [!success]+ Verdict: **ADMIT** · thread [[directions/microstructure_illiquidity#T006|T006]]
> **档位**: CP01 ✓ · CP02 `aligned` · CP03 `strong` · CP04 `acceptable` · CP05 `medium` · CP06 `strong`
> **OOS**: IC=**==0.054==** · ICIR=**==0.544==** · ls_t=**==6.63==** · style_r²=0.353 · alpha_surv=**==0.658==** · max_corr=**==0.655@F012==** · mt_bucket=`high`
> **机制一句话**: illiquidity rank − amount dispersion rank = 跨信号的截面位置差 alpha，非任一 level 的变体。
> **风险**: mt_bucket=high（cumulative 234 候选已累积）；dominant_style=vol_20d (exposure=18.28, 最高暴露)

> [!info] Parent: [[batches/batch_046/judge|batch_046 judge]] · Direction: [[directions/microstructure_illiquidity]] · Nearest: [[factors/F012]]

## 表达式解读

`CsRank(Amihud_20d) - CsRank(amount_CV_10d)`。两端 cross-section rank 化后做差：
- 高值 = illiquidity rank > amount CV rank（流动性差但成交额稳定 — "冷门但稳定"股）
- 低值 = amount CV rank > illiquidity rank（成交额波动大但冲击成本低 — "热门但深度好"股）

关键：**非 Amihud 或 F001 任一 level 的变体**——是两个独立 rank 位置的 relative position 信号。Scale-free（两端都是 pct rank）且几何对称，绕开 batch_031 T004 disproven 的 Div residualization 保序/量纲吞噬陷阱。

## CP01 Hard Gates ✓

全 8 项通过：coverage=0.9632 / sign_flip 同号 (train +0.050, val +0.054) / ic_oos_min 0.054 >> 0.008 / oos_decay=1.07 (OOS ≥ IS, 完美！) / mono_flip train=1.0 val=1.0（双端完美单调）/ near_duplicate max_corr=**0.655** < 0.7 硬闸。

## CP02 Mechanism Alignment · `aligned`

**机制**: 两个独立 signal family 的 cross-section rank 差是 **relative position signal**——低流动性股票本身承担 illiquidity premium，但如果 amount dispersion 也高（成交不稳定），那部分 premium 反映 trading noise 而非真实 illiquidity；rank-diff 把后者减掉，留下"高 illiq + 稳定成交"的真 illiquidity carrier。与 F012 (raw Amihud level) 区分：F012 是 absolute illiquidity level，C003 是 illiquidity 相对 trading stability 的 cross-section 位置。

**与 hypothesis 一致性**: [[directions/microstructure_illiquidity#Hypothesis]] 中"illiquidity premium 需要 return premium 补偿"；本候选进一步条件化 — 仅 amount 稳定（CV rank 低）的部分才兑现 premium。符合微结构理论中"illiquidity 信号需 disentangle from noise trading"。

**持续性**: rank-diff 结构是 scale-invariant，对 regime shift 稳健（2015-2023 9 年全正，best/worst 年 0.0353 / 0.0664，离散度低）。

**失效场景**: 全市场流动性危机（2015 股灾、2020 Q1 疫情）时 Amihud 和 amount CV rank 会同步上升，rank-diff 可能压缩失去区分度。

**与近邻差异**: F012 (raw Amihud) corr=0.655, F001 (amount_cv_10) corr=-0.654 — 两端对应源相关 0.65, 符号相反。F002 (pb/amount) corr=0.543（flip-side liquidity）。**差结构**的 rank-diff 与两个 raw level 都显著相关但**非近重复**（< 0.70 阈值），且 incremental_ic=0.031 远超 0.010 → rank-diff **确实携带两端独立的第三维信息**。

→ **aligned**（机制 + hypothesis fit + 独立性三层证据充分）

## CP03 Statistical Strength · `strong`

| 指标 | IS | OOS | 档位 | 阈值 |
|---|---|---|---|---|
| IC | 0.050 | **==0.054==** | strong | >0.04 |
| ICIR | 0.488 | **==0.544==** | strong | >0.30 |
| ls_t | 10.99 | **==6.63==** | strong | >3 |
| decay | — | 1.07 | excellent | OOS≥IS |

**Rank-order 验证**: mono_is = mono_oos = **1.0**（完美单调，Q1…Q5 OOS: -0.000857 / -0.000378 / -0.0000383 / +0.000368 / +0.000834 — 典型 double-paddle 结构）。

**IC by horizon**: 1d=0.054 → 3d=0.070 → 5d=0.080 → 10d=0.096 → 20d=**0.121**。信号强度随 horizon **单调递增**至 20d，ICIR 1d=0.54 → 20d=1.26——rank-diff 信号对持仓 horizon 有 premium，非短期 noise。

**IS/OOS 对比**: IC_oos/IC_is=1.07，ls_sharpe IS=4.22 → OOS=4.78（OOS 反而更强），**decay 不存在**。win rate OOS=70.9% vs IS=71.2% 稳定。n_days_oos=484。

**MT 调整**: mt_bucket=high (cumulative 234), search_adjusted 0.9 → 0.54 (medium)。raw bucket high 但 adjusted medium，**不需降档**。

→ **strong**（四项指标全部 strong + horizon 单调递增 + OOS > IS 极罕见）

## CP04 Risk Cleanness · `acceptable`

| 指标 | 值 | 档位 | 阈值 |
|---|---|---|---|
| style_r² | **==0.353==** | poor | >0.25 |
| alpha_survival | **==0.658==** | clean | > 0.40+0.10=0.50 |
| extreme_ratio | 2e-06 | clean | <0.01 |
| barra_residual_ic | 0.036 | — | — |
| dominant_style | **vol_20d** (18.28) | — | — |

**Alpha killer**: vol_20d exposure=18.28（最高，style_crowding_risk=high）；turnover_20d=4.24；str_1m=0.53; log_circ_cap=0.51。vol_20d 单项吃掉 18 单位 — 意料之中（illiquidity 天然与 vol 共变），但 **alpha_survival=0.658 > 0.40 + 0.10 = 0.50** 说明剥离 Barra 7-basis 后仍保留约 66% 原始 alpha。

**关键对比**: F012 (raw Amihud) alpha_surv=0.443。**C003 rank-diff 结构把 alpha_surv 从 F012 的 0.443 推到 0.658**（+48% 相对改善）——**证实 rank-diff 的 scale-free 属性实际上减轻了 vol_20d 共线**，即使 style_r² 仍 0.353 偏高。

**Barra residual IC=0.036**，与原 IC 0.054 比保留 66%；barra_residual_icir=0.692 仍 strong。

→ **acceptable**（style_r² poor + alpha_survival clean + extreme_ratio 极低 + barra_resid_icir strong → 3 pass 2 borderline → acceptable）

## CP05 Redundancy · `medium`

- `max_lib_corr` = **==0.655==** → medium（0.30 < x < 0.70）
- `is_near_duplicate` = false
- nearest = [[factors/F012]] (corr=+0.655), F001 (corr=-0.654 对称)
- `incremental_ic` = **==0.0306==**（>> 0.010 hard threshold，库增值明确）

→ **medium**。与 F012 corr 0.655（刚好在 high 0.7 阈下）+ F001 corr -0.654 对称——这是 rank-diff 结构的必然：两端 corr 刚好为 mid-range。但 incremental_ic=0.0306 是 batch_030 以来最高 (F012 admit 时 incr=0.034, 近似)，库增值清晰。

## CP06 Validation Stability · `strong`

| 指标 | 值 | 档位 |
|---|---|---|
| sign_consistency | **==1.0==** | strong（9/9 年正）|
| train_validation_decay | 1.07 | excellent（OOS ≥ IS）|
| split_dispersion | 0.111 | strong（<0.15）|
| worst_quarter_ic | 0.014 | strong（全正）|
| best_quarter_ic | 0.082 | — |
| cum_ic_mdd | -1.61 | strong（库 median -3~-5）|
| ic_autocorr_lag1 | 0.124 | good |

**ic_by_year**: 2015=0.071, 2016=0.066, 2017=0.038, 2018=0.056, 2019=0.050, 2020=0.036, 2021=0.036, 2022=0.049, 2023=0.059 — **9/9 全正**，2020 疫情年 / 2021 市场转折年都稳定。
**split_dispersion**: 0.111（4 splits 均值 0.049/0.049/0.054/0.064 — 时间分段 IC 非常稳定）。

→ **strong** → tier: **stable**（本批所有 CP 中最强档位，各项时序稳健指标库内前列）

> [!success]+ Verdict: ADMIT
> **核心理由**: 5 个软 CP 综合：CP02 aligned（rank-diff 机制 + hypothesis fit + 独立性充分）+ CP03 **strong**（IC/ICIR/ls_t 全部 strong + OOS ≥ IS + horizon 单调递增至 20d IC=0.121）+ CP04 acceptable（alpha_surv=0.658 比 F012 高 48%, Barra residual IC 仍 0.036）+ CP05 medium（max_corr=0.655 刚过 0.70 硬闸, incremental_ic=0.031 库增值高）+ CP06 **strong**（9/9 年同号 + split_dispersion=0.11 + cum_ic_mdd=-1.61 批内最强）。
>
> **机制价值**: rank-diff symmetric interaction 是 T006 revival condition (b) 的直接兑现——在 DSL 层开辟 F012 之外的新子空间，绕开 batch_031 T004 Div/CsZscore 全败陷阱。本候选是 microstructure_illiquidity 方向**第二个 admit**（F012 之后），证明"saturated" 定性可被正确假设的新结构部分推翻。
>
> **factor_name**: `amihud_cv_rank_diff_20` (snake_case, 23 char; 反映"Amihud rank 减 amount CV rank 20d"机制; 与库内 F001 amount_cv_10 / F012 amihud_illiq_20d 明确区分)。
>
> **风险旗标**:
> - CP04 style_r²=0.353 poor，vol_20d exposure=18.28 style_crowding_risk=high — 跟 F012 一样是 vol 共线家族，需 portfolio 层 Barra neutralize
> - CP05 max_corr=0.655 接近 0.70 硬闸；F012 retire 后 C003 即独立 head factor
> - MT bucket=high（cumulative 234），search_adjusted medium — 需警觉多重检验通胀
>
> F{id} 由 Phase 4 分配，本文件 frontmatter `factor_id: null`。

## Detailed Metrics

All numeric fields from Phase 2 / Phase 3 for this candidate. Tables in the report should cite these directly — do not mark fields as `—` if they appear below.

```yaml
metrics:
  cp03:
    ic_oos: 0.05397926964924133
    icir_oos: 0.5441030154456679
    ls_tstat_oos: 6.6263
    ic_is: 0.05038688744122192
    icir_is: 0.4876841443448472
    ic_std_is: 0.1033186910534306
    ic_std_oos: 0.09920781197109815
    n_days_is: 1704
    n_days_oos: 484
    ic_win_rate_is: 0.7124413145539906
    ic_win_rate_oos: 0.7086776859504132
    monotonicity_is: 0.9999999999999999
    monotonicity_oos: 0.9999999999999999
    quintile_returns_is:
      q1: -0.0003431547374930233
      q2: -5.53874951947364e-06
      q3: 0.0009014568058773875
      q4: 0.001116297789849341
      q5: 0.0015941319288685918
    quintile_returns_oos:
      q1: -0.0008574125240556896
      q2: -0.00037771696224808693
      q3: -3.833876326098107e-05
      q4: 0.0003682362148538232
      q5: 0.0008341378998011351
    ls_mean_is: 0.002113513727708607
    ls_mean_oos: 0.0016966479331228983
    ls_sharpe_oos: 4.7764
    ls_sortino_oos: 8.2095
    ls_calmar_oos: 4.268
    ls_max_dd_oos: -0.1002
    ls_sharpe_is: 4.224
    ls_tstat_is: 10.9871
    ls_max_dd_is: -3.7539
    ic_by_horizon:
      1:
        ic_is: 0.05038688744122192
        icir_is: 0.4876841443448472
        win_rate_is: 0.7124413145539906
        ic_oos: 0.05397926964924133
        icir_oos: 0.5441030154456679
        win_rate_oos: 0.7086776859504132
      3:
        ic_is: 0.06417668905713197
        icir_is: 0.5831331832338364
        win_rate_is: 0.7230046948356808
        ic_oos: 0.06990491029074719
        icir_oos: 0.6807617996484857
        win_rate_oos: 0.7252066115702479
      5:
        ic_is: 0.07411682255339302
        icir_is: 0.6620290288718805
        win_rate_is: 0.7400234741784038
        ic_oos: 0.07973912063297536
        icir_oos: 0.7807723459818022
        win_rate_oos: 0.7747933884297521
      10:
        ic_is: 0.08507175845693853
        icir_is: 0.7279996406908862
        win_rate_is: 0.7746478873239436
        ic_oos: 0.09606038331953876
        icir_oos: 0.9558711511220991
        win_rate_oos: 0.8388429752066116
      20:
        ic_is: 0.09280277561603854
        icir_is: 0.7493295064958362
        win_rate_is: 0.7705399061032864
        ic_oos: 0.12063554841337905
        icir_oos: 1.2630096847929695
        win_rate_oos: 0.9132231404958677
  cp04:
    style_r_squared: 0.35340326197844907
    alpha_survival_ratio: 0.6582
    alpha_surv_min_threshold: 0.4
    extreme_ratio: 2.0e-06
    barra_residual_ic: 0.035529
    barra_residual_icir: 0.692318
    dominant_style_exposure: vol_20d
    style_crowding_risk: high
    style_exposures:
      log_circ_cap: 0.5141287847144492
      book_to_price: 0.13154879250500617
      mom_12_1: 0.10813333599445393
      str_1m: 0.530889394770767
      vol_20d: 18.2760306655669
      turnover_20d: 4.237190434692618
      ep_ratio: 0.3344768947269337
    distribution_skew: 0.0975
    distribution_kurt: -0.5071
    distribution_zero_ratio: 0.0
  cp05:
    max_lib_corr: 0.6548
    is_near_duplicate: false
    incremental_ic: 0.0306
    nearest_factor_id: F012
    nearest_factor_expression: Mean(Div(Abs(Div(Delta($close, 1), Ref($close, 1))),
      $amount), 20)
    all_correlations:
      F001: -0.6540942643759062
      F002: 0.543033892227269
      F003: 0.044980297413633255
      F006: -0.02041918012717203
      F007: 0.07274618289577561
      F008: -0.02007414747797129
      F009: 0.09707718645084515
      F010: 0.052987357446973804
      F011: 0.051095334265819047
      F012: 0.6548292220870003
      F013: 0.016580507850858975
      F014: -0.09484718697080612
      F004: 0.13965900705958673
      F005: 0.13965900705958673
    exceeds_threshold: false
  cp06:
    sign_consistency: 1.0
    train_validation_decay: 1.0713
    sign_consistent: true
    ic_by_year:
      2015: 0.07063330335532703
      2016: 0.06622460680574081
      2017: 0.037737747167250965
      2018: 0.05581639965164219
      2019: 0.04982788992775869
      2020: 0.036284275907279735
      2021: 0.03617316795019148
      2022: 0.04907425674444111
      2023: 0.05888428255404155
    worst_quarter_ic: 0.013777
    best_quarter_ic: 0.082169
    ic_autocorr_lag1: 0.123765
    cum_ic_max_drawdown: -1.606646
    split_ic_means:
    - 0.049004881786840385
    - 0.04914363170204184
    - 0.05399271146228379
    - 0.06377585364579928
    split_dispersion: 0.1112
    n_splits: 4
  feasibility:
    turnover_mean: 0.612518489662324
    liquidity_coverage: 0.673648736081409
    tail_concentration: 0.007160112284529115
    small_cap_concentration: 0.32312960523190715
    signal_half_life: 6.0
    signal_autocorr_lag1: 0.9349
    rebalance_stress:
      value: 0.006510367981752471
      rebalance_stress_bucket: low
    ic_half_life_days: null
mt_budget:
  score: 0.8023
  bucket: high
  terms:
    family: 0.8534696813013
    direction: 0.5853340409128812
    exposure: 1.0
  search_adjusted:
    raw: 0.9
    adjusted: 0.5389
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
      value: 0.9632
      threshold: 0.8
    sign_flip:
      passed: true
      train_ic: 0.05038688744122192
      val_ic: 0.05397926964924133
    ic_oos_min:
      passed: true
      value: 0.05397926964924133
      threshold: 0.008
    oos_decay:
      passed: true
      value: 1.0713
      threshold: 0.2
    mono_flip:
      passed: true
      train: 0.9999999999999999
      validation: 0.9999999999999999
      min_magnitude: 0.5
    near_duplicate:
      passed: true
      max_corr: 0.6548
      nearest: F012
coverage: 0.9632
expression: Sub(CsRank(Mean(Div(Abs(Div(Delta($close, 1), Ref($close, 1))), $amount),
  20)), CsRank(Div(Std($amount, 10), Mean($amount, 10))))
```

## Available Charts

The following PNG charts exist in `vault/factors/F015/` and may be embedded via `![[F015/<name>.png]]`. **Do not embed any chart name that is not on this list** — the file would not exist.

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

Write a deep analytical report on `F015`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Embed only charts listed in the **Available Charts** section (skip any section whose chart is unavailable). Output path: `vault/factors/F015.md`.

