---
factor_id: F003
direction: intraday_price_formation
admitted_in_batch: batch_010
---

# Report Packet — F003

## Factor YAML Summary

```yaml
name: overnight_gap_normalized
expression: Div(Sub($open, Ref($close, 1)), Mean($high, 1))
source_type: dsl
family_tag: intraday_price_formation
validation_metrics:
  ic_mean: 0.023045048345342673
  ic_ir: 0.3793180939268973
  ic_win_rate: 0.6549586776859504
  monotonicity: 0.9999999999999999
  long_short_mean: 0.0016248438121181622
risk_metrics:
  style_r_squared: 0.03333985267478512
  alpha_survival_ratio: 0.8213
```

## Judge Synthesis

---
candidate_id: C004
batch_id: batch_010
direction: intraday_price_formation
expression: "Div(Sub($open, Ref($close, 1)), Mean($high, 1))"
verdict: admit
thread_id: T001
factor_id: F003
factor_name: overnight_gap_normalized
key_metrics_short: "IC=0.023 ICIR=0.379 ls_t=8.36"
reject_reason_short: null
---

# C004 — Div(Sub($open, Ref($close, 1)), Mean($high, 1))

> [!success]+ Verdict: **ADMIT** · thread [[directions/intraday_price_formation#T001|T001]]
> **档位**: CP01 ✓ · CP02 `aligned` · CP03 `strong` · CP04 `acceptable` · CP05 `low` · CP06 `stable`
> **OOS**: IC=**==0.023==** · ICIR=**==0.379==** · ls_t=**==8.36==** · style_r²=0.033 · alpha_surv=**==0.821==** · max_corr=0.058 · mt_bucket=`low`
> **机制一句话**: 隔夜跳空幅度 / 近1日均价 — 捕捉 overnight gap 的相对大小，不依赖成交量

> [!info] Parent: [[batches/batch_010/judge|batch_010 judge]] · Direction: [[directions/intraday_price_formation]] · Nearest: [[factors/F002]]

## 表达式解读

`Div(Sub($open, Ref($close, 1)), Mean($high, 1))` = (今日开盘价 - 昨日收盘价) / 近1日最高价的均值

这是**隔夜跳空幅度**（overnight gap）的相对度量：分子是 overnight return（反映隔夜信息冲击），分母用近1日均高过滤掉绝对价格水平效应。信号为正则表示高开，为负表示低开。

经济直觉：隔夜信息（财报/新闻/外盘）导致的跳空幅度相对于近期日内波动率Normalized，反映市场对隔夜信息的反应强度——**纯 OHLCV 字段，不依赖成交量/金额**，正交于 amount/vol_20d 空间。

## CP01 Hard Gates ✓

8 项 gate 全过：
- ✓ compute_error
- ✓ coverage: 0.9883 ≥ 0.80
- ✓ sign_flip: train +0.0296 / val +0.0230（同号）
- ✓ forbidden
- ✓ ic_oos_min: 0.0230 ≥ 0.008
- ✓ oos_decay: 0.7782 ≥ 0.20
- ✓ mono_flip: train 1.0 / val 1.0（同号）
- ✓ near_duplicate: max_corr 0.058 < 0.9（nearest F002）

## CP02 Mechanism Alignment · `aligned`

**机制**：本候选捕捉**隔夜跳空相对强度**——个股在非交易时段积累的信息通过开盘价一次性实现，跳空幅度相对于近期日内高点均值 Normalized。这个信号编码了"市场对隔夜信息的整体反应程度"，本质是**价格发现效率**的代理变量。

**与 hypothesis 一致性**：[[directions/intraday_price_formation#Hypothesis]] 假设 OHLCV-only 纯价格指标可携带独立于 vol_20d 的 alpha；本候选使用 `$open / Ref($close, 1) / Mean($high, 1)` 三者组合，**完全不使用成交量/金额字段**，且 IC=0.023 证明存在真实 alpha。完全吻合 Hypothesis 第 4 条"缺口信号"的预期。

**持续性**：隔夜信息不对称是A股持续存在的结构性现象（涨跌停板限制、T+1 制度、隔夜新闻），gap signal 在每个交易日重复出现，不依赖特定市场环境。9年 IC 一致为正佐证了这一点。

**失效场景**：科创板/创业板新上市前几日（无 Ref($close, 1) 意义）；ETF/期权等衍生品关联股票（开盘价锚定效应弱）；高频停牌后复牌初期（价格发现过程异常）。

**与近邻差异**：[[factors/F002]]（`Div($pb_ratio, Mean($amount, 20))`）捕捉价值/流动性交互，机制上属于基本面+资金流；本候选完全基于价格路径，不涉及价值比率或金额字段。符号方向上 F002 IC 为负（低价值/高金额 → 跌），本候选 IC 为正（高隔夜跳空 → 涨），两者在 Barra 因子层面都暴露 vol_20d 但 **alpha 机制正交**。

→ **aligned**

## CP03 Statistical Strength · `strong`

| 指标 | IS | OOS | 档位 | 阈值 |
|---|---|---|---|---|
| IC | 0.0296 | **==0.023==** | strong | \|x\|>0.015 |
| ICIR | 0.267 | **==0.379==** | strong | \|x\|>0.30 |
| ls_t | 15.66 | **==8.36==** | strong | \|x\|>3 |
| decay | — | 0.778 | moderate | >0.8 |

**Rank-order 验证**：monotonicity_oos = **==1.0==**（完美单调，|x| > 0.8 → 强单调）。Q1..Q5 梯度 (OOS): q1=-0.00116, q2=0.00008, q3=0.00014, q4=0.00036, q5=0.00044 → **单调递增**，五档无反向，每档差距量级与 ls_mean=0.00162 一致。IS 同期 Q1..Q5 同样单调递增（q1=-0.00134 → q5=0.00232）。**完全非"一桨驱动"**，是真实 rank-order 信号。

**样本量**：n_days_oos=484（>> 200，统计显著性充足）。

**MT 调整**：`mt_bucket = low`；`search_adjusted = 0.7408`（bucket: high）。low bucket 规则：原档保留，无降档。batch_010 是 `intraday_price_formation` 方向首批，direction_candidates=0，cumulative_candidates=51，此时 direction 全新，无 MT pressure。

→ **strong**

## CP04 Risk Cleanness · `acceptable`

| 指标 | 值 | 档位 | 阈值 |
|---|---|---|---|
| style_r_squared | **==0.033==** | clean | <0.12 |
| alpha_survival | **==0.821==** | borderline | clean>0.50 |
| extreme_ratio | 0.0245 | borderline | clean<0.01 |
| barra_residual_ic | **==0.019==** | — | — |
| dominant_style | `vol_20d` | — | — |

**Alpha killer**（按 `metrics.cp04.style_contributions` 排序）：
- `vol_20d`: delta_ic=**==11.0==** (主导 style，joint effect 极大)
- `turnover_20d`: delta_ic=1.71
- `str_1m`: delta_ic=0.62
- 其余 styles |delta_ic| < 0.5

 Barra joint effect 解释：gap signal 与 vol_20d 联合分布相关联——高波动股票隔夜跳空绝对幅度更大，但这不等于 gap signal 无 alpha（ Barra residual IC=0.019 > 0，说明控住 vol_20d 后仍有独立信号）。

两项 clean 一项 borderline（alpha_surv=0.821，extreme_ratio=0.0245 边界）→ **acceptable**。CP04 纯粹描述性，不自动阻断 admit（rubric 2026-04-19 放宽规则）。

## CP05 Redundancy · `low`

- `max_lib_corr` = **==0.058==** → low 档（< 0.30）
- `is_near_duplicate` = false（硬闸未触发）
- nearest = [[factors/F002]]（`Div($pb_ratio, Mean($amount, 20))`）
- `incremental_ic` = **==0.031==**（> 0.005，库增值极清晰）

→ **low**。admit 增值：本候选是 pure OHLCV gap signal，与库中所有 amount/vol 族因子均保持极低相关（max_corr<0.06），且 incremental_ic=0.031 说明加入后显著提升组合 IC — **direction hypothesis 的首个正向验证**，对探索 OHLCV 新空间有结构性价值。

## CP06 Validation Stability · `stable`

| 指标 | 值 | 档位 |
|---|---|---|
| sign_consistency | **==1.0==** | stable |
| train_validation_decay | **==0.778==** | mixed (0.5–0.8) |

**时序稳健**：
- `ic_autocorr_lag1` = 0.0048（|x|<0.15 → IC 日独立，ICIR 置信高）
- `cum_ic_max_drawdown` = **==-1.15==**（> -30，极浅回撤；最佳样本之一）
- `worst_quarter_ic` = -0.0036 / `best_quarter_ic` = 0.0995（同号且 worst ≈ 1/6 |best|，极健康）
- `ic_by_year`：**2015–2023 全部同号（正）**，2019=0.034 / 2020=0.034 高点，2021=0.016 最低点仍为正——9年无一年失效，**edge 极为稳健**

→ **stable**（核心两项一 stable 一 mixed；时序 9年全正、cum_mdd 仅 -1.15，不降档）

## Feasibility 注释

- `small_cap_concentration` = 0.309（边界高于 0.4 警戒线，但低于 0.4 无需特别说明）
- `rebalance_stress` = medium（`turnover_mean=2.91` 属中等换手）
- `ic_half_life_days` = null（metric 未计算出但 IC 9年稳定不依赖半衰期假设）

> [!success]+ Verdict: ADMIT
> **核心理由**: C004 是 `intraday_price_formation` 方向（OHLCV-only 假设）的首个 strong 候选。CP03 三指标（IC=0.023 / ICIR=0.379 / ls_t=8.36）全部 strong，monotonicity_oos=1.0 五档完美单调，9年 IC 全正未见衰减，cum_mdd 仅 -1.15。CP05 max_lib_corr=0.058 且 incremental_ic=0.031，为 direction hypothesis 提供实质性正向证据。CP04 虽有 vol_20d dominant style（alpha_surv=0.821 borderline），但 Barra residual IC=0.019 证明控住 vol 后仍有独立 alpha，不阻碍 admit。
>
> **风险旗标**: alpha_survival_ratio=0.821 处于 borderline 上沿（clean>0.50）；extreme_ratio=0.0245 略超 0.01 边界；vol_20d 是 dominant style exposure（joint effect 强）；small_cap_concentration=0.309 偏高但不超标。CP04 档位 `acceptable` 不触发阻断，CP06 稳健性全部健康。
>
> F{id} 由 Phase 4 分配，本文件 frontmatter `factor_id: null`。

## Detailed Metrics

All numeric fields from Phase 2 / Phase 3 for this candidate. Tables in the report should cite these directly — do not mark fields as `—` if they appear below.

```yaml
metrics:
  cp03:
    ic_oos: 0.023045048345342673
    icir_oos: 0.3793180939268973
    ls_tstat_oos: 8.3631
    ic_is: 0.029611591811194382
    icir_is: 0.26740302749528944
    ic_std_is: 0.11073768344569704
    ic_std_oos: 0.06075388628780768
    n_days_is: 1703
    n_days_oos: 484
    ic_win_rate_is: 0.6793893129770993
    ic_win_rate_oos: 0.6549586776859504
    monotonicity_is: 0.9999999999999999
    monotonicity_oos: 0.9999999999999999
    quintile_returns_is:
      q1: -0.0013369944645091891
      q2: 0.0006643593078479171
      q3: 0.0007776528946124017
      q4: 0.0007919595227576792
      q5: 0.002315645106136799
    quintile_returns_oos:
      q1: -0.0011557132238522172
      q2: 7.651410851394758e-05
      q3: 0.00014240846212487668
      q4: 0.00036204405478201807
      q5: 0.0004377219302114099
    ls_mean_is: 0.00392097678809598
    ls_mean_oos: 0.0016248438121181622
    ls_sharpe_oos: 6.0283
    ls_sortino_oos: 12.0329
    ls_calmar_oos: 5.9736
    ls_max_dd_oos: -0.0685
    ls_sharpe_is: 6.0263
    ls_tstat_is: 15.6614
    ls_max_dd_is: -17.2397
    ic_by_horizon:
      1:
        ic_is: 0.029611591811194382
        icir_is: 0.26740302749528944
        win_rate_is: 0.6793893129770993
        ic_oos: 0.023045048345342673
        icir_oos: 0.3793180939268973
        win_rate_oos: 0.6549586776859504
      3:
        ic_is: 0.03378010269679288
        icir_is: 0.33482926520174683
        win_rate_is: 0.7011156782149148
        ic_oos: 0.02598606074373708
        icir_oos: 0.46002196876717577
        win_rate_oos: 0.6942148760330579
      5:
        ic_is: 0.03217251716305066
        icir_is: 0.3237925934864625
        win_rate_is: 0.7034644744568409
        ic_oos: 0.028342967037366065
        icir_oos: 0.5041728098625997
        win_rate_oos: 0.7231404958677686
      10:
        ic_is: 0.0323312442950156
        icir_is: 0.3575463693600865
        win_rate_is: 0.7322372284204345
        ic_oos: 0.0304043364516578
        icir_oos: 0.5232394735214881
        win_rate_oos: 0.7169421487603306
      20:
        ic_is: 0.03280790312092319
        icir_is: 0.3902862764431068
        win_rate_is: 0.7310628302994715
        ic_oos: 0.031963714067674134
        icir_oos: 0.5704741125520107
        win_rate_oos: 0.743801652892562
  cp04:
    style_r_squared: 0.03333985267478512
    alpha_survival_ratio: 0.8213
    extreme_ratio: 0.024534
    barra_residual_ic: 0.018926
    barra_residual_icir: 0.352564
    dominant_style_exposure: vol_20d
    style_crowding_risk: medium
    style_exposures:
      log_circ_cap: 0.04815337634898285
      book_to_price: 0.11987707868841183
      mom_12_1: 0.10625964140264267
      str_1m: 0.6155594015392062
      vol_20d: 11.00578828268693
      turnover_20d: 1.706831736742858
      ep_ratio: 0.36926909580907685
    distribution_skew: 0.037
    distribution_kurt: 2.5051
    distribution_zero_ratio: 0.000336
  cp05:
    max_lib_corr: 0.0583
    is_near_duplicate: false
    incremental_ic: 0.031399
    nearest_factor_id: F002
    nearest_factor_expression: Div($pb_ratio, Mean($amount, 20))
    all_correlations:
      F001: -0.03501986410187027
      F002: 0.05826332573918791
    exceeds_threshold: false
  cp06:
    sign_consistency: 1.0
    train_validation_decay: 0.7782
    sign_consistent: true
    ic_by_year:
      2015: 0.05239054098313742
      2016: 0.018594173080082148
      2017: 0.022879227698165073
      2018: 0.030014189315478737
      2019: 0.03419432543201564
      2020: 0.03351595035732319
      2021: 0.015840661731480545
      2022: 0.022917410384004296
      2023: 0.02317268630668106
    worst_quarter_ic: -0.003563
    best_quarter_ic: 0.099536
    ic_autocorr_lag1: 0.004834
    cum_ic_max_drawdown: -1.14734
    split_ic_means:
    - 0.025504705444885152
    - 0.020330115323123434
    - 0.016069316957764947
    - 0.030276055655597166
    split_dispersion: 0.232
    n_splits: 4
  feasibility:
    turnover_mean: 2.9090272855090102
    liquidity_coverage: 0.730140842728991
    tail_concentration: 0.006870323610731263
    small_cap_concentration: 0.308654728297336
    signal_half_life: 1.0
    signal_autocorr_lag1: 0.0664
    rebalance_stress:
      value: 0.027372744646353503
      rebalance_stress_bucket: medium
    ic_half_life_days: null
mt_budget:
  score: 0.3538
  bucket: low
  terms:
    family: 0.617678156795038
    direction: 0.0
    exposure: 0.225
  search_adjusted:
    raw: 0.9
    adjusted: 0.7408
    bucket: high
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
      value: 0.9883
      threshold: 0.8
    sign_flip:
      passed: true
      train_ic: 0.029611591811194382
      val_ic: 0.023045048345342673
    ic_oos_min:
      passed: true
      value: 0.023045048345342673
      threshold: 0.008
    oos_decay:
      passed: true
      value: 0.7782
      threshold: 0.2
    mono_flip:
      passed: true
      train: 0.9999999999999999
      validation: 0.9999999999999999
    near_duplicate:
      passed: true
      max_corr: 0.0583
      nearest: F002
coverage: 0.9883
expression: Div(Sub($open, Ref($close, 1)), Mean($high, 1))
```

## Available Charts

The following PNG charts exist in `vault/factors/F003/` and may be embedded via `![[F003/<name>.png]]`. **Do not embed any chart name that is not on this list** — the file would not exist.

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

Write a deep analytical report on `F003`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Embed only charts listed in the **Available Charts** section (skip any section whose chart is unavailable). Output path: `vault/factors/F003.md`.

