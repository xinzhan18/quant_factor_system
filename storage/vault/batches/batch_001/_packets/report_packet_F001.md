---
factor_id: F001
direction: amount_volatility_signal
admitted_in_batch: batch_001
---

# Report Packet — F001

## Factor YAML Summary

```yaml
name: amount_cv_10
expression: Div(Std($amount, 10), Mean($amount, 10))
source_type: dsl
family_tag: amount_volatility_signal
validation_metrics:
  ic_mean: -0.040376913506727244
  ic_ir: -0.7158056873727735
  ic_win_rate: 0.23760330578512398
  monotonicity: -0.9999999999999999
  long_short_mean: -0.0006727336273970725
risk_metrics:
  style_r_squared: 0.11406013504438384
  alpha_survival_ratio: 0.7612
```

## Judge Synthesis

---
candidate_id: C001
batch_id: batch_001
direction: amount_volatility_signal
expression: "Div(Std($amount, 10), Mean($amount, 10))"
verdict: admit
thread_id: T001
factor_id: F001
factor_name: amount_cv_10
key_metrics_short: "IC_OOS=-0.040 ICIR=-0.716 ls_t=-3.78 Mono_OOS=-1.0"
reject_reason_short: null
---

# C001 — Div(Std($amount, 10), Mean($amount, 10))

> [!success]+ Verdict: **ADMIT** · thread [[directions/amount_volatility_signal#T001|T001]]
> **档位**: CP01 ✓ · CP02 `aligned` · CP03 `strong` · CP04 **`borderline`** · CP05 `low` · CP06 `stable`
> **OOS**: IC=**==-0.040==** · ICIR=**==-0.716==** · ls_t=**==-3.78==** · style_r²=**==0.114==** · alpha_surv=**==0.761==** · max_corr=0.0 · mt_bucket=`low`
> **机制一句话**: 10 日成交额变异系数（资金参与稳定性），高 CV = 资金断层大 = 未来收益低。

> [!info] Parent: [[batches/batch_001/judge|batch_001 judge]] · Direction: [[directions/amount_volatility_signal]] · Nearest: 库空

## 表达式解读

`Div(Std($amount, 10), Mean($amount, 10))` 是 10 个交易日内成交额的**变异系数**（Coefficient of Variation, CV = σ/μ）。它度量资金参与强度的**稳定性**：分母去除规模效应（大盘股 vs 小盘股的绝对成交额差几个量级），分子捕捉最近 10 日日度成交额的离散程度。

CV 高 → 近 10 日内至少有 1–2 天出现与均值显著偏离的成交额峰谷，代表资金进出**不稳定 / 断层**（典型：事件驱动、散户集中买卖、消息面冲击）。CV 低 → 资金进出**连续平稳**（典型：机构持续建仓或稳定换手）。负 IC 表明市场倾向于奖励"稳定参与"（低 CV）、惩罚"突发参与"（高 CV）。

## CP01 Hard Gates ✓

8 项 gate 全过：
- ✓ compute_error
- ✓ coverage: 0.9632 ≥ 0.80
- ✓ sign_flip: train IC=-0.0400 / val IC=-0.0404（同号，几乎一致）
- ✓ forbidden
- ✓ ic_oos_min: |-0.0404| ≥ 0.008
- ✓ oos_decay: 1.008 ≥ 0.20（IS/OOS 几乎无衰减）
- ✓ mono_flip: train -1.00 / val -1.00（完美同号单调）
- ✓ near_duplicate: max_corr 0.0 < 0.9（库为空，首批因子）

## CP02 Mechanism Alignment · `aligned`

**机制**：10 日成交额 CV 捕捉**资金参与强度的稳定性**。高 CV 意味着近 10 日出现异常放量 / 缩量的不对称分布；低 CV 意味着资金参与平稳持续。经济上，前者对应散户、事件驱动或技术性砸盘/拉升；后者对应机构稳定建仓或均衡换手。

**与 hypothesis 一致性**：[[directions/amount_volatility_signal#Hypothesis]] 假设 `$amount` 的二阶统计量编码"谁在交易、交易得多稳定"的微观结构信息，并强调 scale-invariance 以避规市值代理红线。C001 正是最直接的 scale-invariant 实现（Std/Mean 量纲消去），对应 hypothesis 的"经济学线索 1：资金参与稳定性断层"，是 T001 的 baseline。

**持续性**：CV 高低与投资者结构（机构 vs 散户 vs 事件驱动资金）绑定，这种微观结构差异是 A 股制度性/结构性特征（涨跌停、T+1、散户占比高），不会因单一套利资金进场而快速失效。ic_by_year 9 年（2015–2023）同号负 IC 也实证了这种结构性持续性。

**失效场景**：
1. **极端牛市普涨阶段**（如 2015 上半年、2020 Q2–Q3），资金无差别涌入，CV 可能无信息；
2. **停牌 / ST / 科创板上市首日打板**等流动性断裂场景（由 coverage 0.96 部分过滤）；
3. **全市场 regime 剧变期**（政策、流动性拐点），IC 短期可能衰减但不翻号。

**与近邻差异**：库为空（max_corr=0.0，nearest_factor_id=null），无近邻可比。批内近邻 C002（60 日 CV）window 更长、信号更慢（ICIR_OOS 仅 -0.21，ls_tstat -0.84），说明**短窗口 10 日的"断层"信号显著强于长窗口的"平均粘性"**，C001 代表该 thread 的最强单侧 baseline。

→ **aligned**

## CP03 Statistical Strength · `strong`

| 指标 | IS | OOS | 档位 | 阈值 |
|---|---|---|---|---|
| IC | -0.0400 | **==-0.0404==** | strong | \|x\|>0.015 |
| ICIR | -0.482 | **==-0.716==** | strong | \|x\|>0.30 |
| ls_t | -4.15 | **==-3.78==** | strong | \|x\|>3 |
| decay | — | 1.008 | healthy | >0.8 |

**Rank-order 验证**：`monotonicity_oos = -1.0`（完美负单调，|x|>0.8 → 强单调）。Q1..Q5 梯度 (OOS): q1=**0.000321**, q2=0.000133, q3=-0.000035, q4=-0.000142, q5=**-0.000347** → 严格单调下降，q1–q5 差 ≈ 6.7e-4 与 ls_mean_oos(-6.7e-4) 量级严格一致。**非"一桨驱动"，是全谱对称梯度**。win_rate_oos=0.238（days-of-same-sign），呼应 ICIR 的强信号。

**样本量**：n_days_oos=484 >> 200，统计显著性充足；n_days_is=1704 同样充分。

**IS/OOS decay**：ic_is=-0.040 vs ic_oos=-0.040，decay=1.008（OOS 反而比 IS 略强）；ls_sharpe_is=-1.60 vs ls_sharpe_oos=-2.73，ls_tstat_is=-4.15 vs ls_tstat_oos=-3.78 → 全线健康，无 OOS 衰减。

**MT 调整**：`mt_bucket = low`（首批，累计候选=0、方向候选=0），原档保留。但 `search_adjusted` 内部 bucket=`high`（raw=0.9, adjusted=0.9）反映本候选家族搜索压力被标记——由于 mt_budget.bucket=low 是权威字段（首批保护），仍按 low 档判决，**不降档**。

→ **strong**

## CP04 Risk Cleanness · **`borderline`**

| 指标 | 值 | 档位 | 阈值 |
|---|---|---|---|
| style_r_squared | **==0.114==** | borderline | clean<0.08, poor>0.12 |
| alpha_survival | **==0.761==** | clean | >0.70 |
| extreme_ratio | 0.0231 | borderline | clean<0.01, poor>0.03 |
| barra_residual_ic | -0.0307 | — | — |
| dominant_style | `vol_20d` | — | — |
| style_crowding | medium | — | — |

**Alpha killer**（`style_exposures` 按暴露量降序，_hints 未提供 leave-one-out `style_contributions`，以原始暴露度为代理）：
- `vol_20d`: 暴露 = **==24.48==**（压倒性主导）
- `turnover_20d`: 暴露 = 3.34
- `str_1m`: 暴露 = 1.28
- 总体：本因子被 **vol_20d** 严重吞噬（暴露量级远超其它 style 一个数量级），barra 残差 IC 从 raw |-0.040| 被压缩到 |-0.031|，衰减约 23% → 大部分 alpha 保留（alpha_survival=0.761 clean），但残差 IC 的绝对幅度已接近 style_r² 的解释阈值。下轮需对 **vol_20d** 做 orthogonalize 或 normalize（除以 Std(ret, 20)）以清洁暴露。

两项 borderline（style_r²、extreme_ratio）+ 一项 clean（alpha_survival 0.761）→ **borderline**。  
**非 dealbreaker**：alpha_survival_ratio=0.761 > 0.60，不触发 CP04 dealbreaker；verdict 仍可 admit，但须在风险旗标中明记 vol_20d 交叠。

→ **borderline**

## CP05 Redundancy · `low`

- `max_lib_corr` = **==0.0==** → 机械 low（库为空，首批批次）
- `is_near_duplicate` = false（硬闸未触发）
- nearest = 无（nearest_factor_id=null）
- `incremental_ic` = null（库为空无法计算）

→ **low**（机械值）。按 candidate-rubric："首批（empty library）例外：CP05 `max_lib_corr=0` 机械 low 不能单独支持 admit，admit 判断此时倾向更严格"——本候选 admit 的**支撑不来自 CP05**，而来自 CP03 strong（三指标全强 + 完美单调 + 零 decay）+ CP06 stable（9 年同号）+ CP02 aligned。CP05 在此不加分亦不减分，作为方向 anchor 的 uniqueness 由 hypothesis 的原创性（amount-based scale-invariant CV）提供。

## CP06 Validation Stability · `stable`

| 指标 | 值 | 档位 |
|---|---|---|
| sign_consistency | **==1.0==** | stable |
| train_validation_decay | **==1.008==** | stable (>0.8) |

**时序稳健**：
- `ic_autocorr_lag1` = 0.086（|x|<0.15 → IC 日独立，ICIR=-0.716 置信高，未被 regime-动量夸大）
- `cum_ic_max_drawdown` = **-87.72**（< -50 → **长期失效区间存在**，需警觉；但回撤后恢复，整体 IC 仍强）
- `worst_quarter_ic` = -0.060 / `best_quarter_ic` = -0.006（**同号**，worst 仅 1.5× |ic_oos|，非尾部单季驱动）
- `ic_by_year`：2015: -0.034, 2016: -0.040, 2017: -0.039, 2018: -0.056, 2019: -0.052, 2020: -0.039, 2021: -0.021, 2022: -0.037, 2023: -0.043 → **9 年全部同号负 IC**，2018–2019 最强（熊市波动），2021 最弱（小盘普涨后），2022–2023 回升。**edge 稳定存在，无衰减趋势**。
- `split_dispersion` = 0.160，4 split 全部同号（-0.045, -0.029, -0.042, -0.044）→ 离散度低，split 之间一致。

→ **stable**（核心两项都 stable；ic_autocorr / 逐年 / split 全部健康；唯一 `cum_ic_max_drawdown=-87.7` 触红线但未使档位下调——因为整体 IC 水位强、恢复明显、9 年同号，回撤反映 2021 小盘普涨特殊 regime 而非结构性失效）

**Feasibility**（触发提醒）：
- turnover_mean = 0.80（低换手，日内调仓无压力）
- liquidity_coverage = 0.685（样本仅覆盖 68.5% 可投标的，偏小盘）
- small_cap_concentration = 0.317（偏小盘，与 CP04 未列出的 log_circ_cap 暴露 0.087 一起看，整体尚可）
- signal_half_life = 5.0（短半衰期但 turnover 低 → 信号快速衰减由 CV 窗口滚动自然处理）
- rebalance_stress bucket = low

> [!success]+ Verdict: ADMIT
> **核心理由**: CP03 全 strong（IC/ICIR/ls_t 三指标齐强，完美 -1.0 单调，Q1–Q5 对称梯度非尾部驱动，9 年同号无 decay），CP06 stable（IC 日独立、split 一致、全样本同号），CP02 与 hypothesis T001 完美对齐且是 scale-invariant 的最直接实现。CP04 borderline 与 CP05 首批机械 low 的两处瑕疵不足以否决 strong alpha + perfect monotonicity + 9-year-same-sign 的组合证据。作为方向 anchor 入库，后续可以此为基线扩展 MAD 版、更长窗口、交互因子。
>
> **风险旗标**:
>   - **CP04 borderline（vol_20d 交叠）**：style_r²=0.114、extreme_ratio=0.023 双 borderline，dominant_style=vol_20d 暴露 24.48（远超其它 style 一个数量级）。下一轮需做 vol_20d orthogonalize，并生成"CV × Vol20d residual"交互变体，排除 volatility 交叠后的净 alpha。
>   - **CP06 cum_ic_max_drawdown = -87.7**：存在一段长期失效历史（推测 2021 小盘普涨期），虽已恢复且 9 年同号，但在类似 regime（极端小盘行情）下可能再度失效，需监控 regime 指标。
>   - **CP05 首批机械 low**：max_lib_corr=0 因库空，不能单独支持 admit；本次 admit 主要由 CP03+CP06 支撑。后续同方向候选需真实 corr 检验。
>   - **liquidity_coverage = 0.685**：样本仅覆盖 68.5% 可投标的（小盘偏倚），CSI1000 backtest 表现可能与实盘全市场表现有偏差，需后续做 top-500 / all-市值的 robust 检验。
>
> F{id} 由 Phase 4 分配，本文件 frontmatter `factor_id: null`。

## Detailed Metrics

All numeric fields from Phase 2 / Phase 3 for this candidate. Tables in the report should cite these directly — do not mark fields as `—` if they appear below.

```yaml
metrics:
  cp03:
    ic_oos: -0.040376913506727244
    icir_oos: -0.7158056873727735
    ls_tstat_oos: -3.7843
    ic_is: -0.04004418106211288
    icir_is: -0.48172873554379253
    ic_std_is: 0.08312599624539646
    ic_std_oos: 0.05640764556498972
    n_days_is: 1704
    n_days_oos: 484
    ic_win_rate_is: 0.29518779342723006
    ic_win_rate_oos: 0.23760330578512398
    monotonicity_is: -0.9999999999999999
    monotonicity_oos: -0.9999999999999999
    quintile_returns_is:
      q1: 0.0010619276436045766
      q2: 0.0008339190972037613
      q3: 0.0006254572654142976
      q4: 0.0004945727996528149
      q5: 0.00024907413171604276
    quintile_returns_oos:
      q1: 0.0003210604772903025
      q2: 0.00013297864643391222
      q3: -3.481439489405602e-05
      q4: -0.00014195236144587398
      q5: -0.00034738032263703644
    ls_mean_is: -0.0007637604726945758
    ls_mean_oos: -0.0006727336273970725
    ls_sharpe_oos: -2.7278
    ls_sortino_oos: -4.0491
    ls_calmar_oos: -0.557
    ls_max_dd_oos: -0.3044
    ls_sharpe_is: -1.595
    ls_tstat_is: -4.1489
    ls_max_dd_is: -1.219
    ic_by_horizon:
      1:
        ic_is: -0.04004418106211288
        icir_is: -0.48172873554379253
        win_rate_is: 0.29518779342723006
        ic_oos: -0.040376913506727244
        icir_oos: -0.7158056873727735
        win_rate_oos: 0.23760330578512398
      3:
        ic_is: -0.04983309343447962
        icir_is: -0.6188605082364005
        win_rate_is: 0.24061032863849766
        ic_oos: -0.04586614146264643
        icir_oos: -0.8274010348503718
        win_rate_oos: 0.20454545454545456
      5:
        ic_is: -0.05570282224452761
        icir_is: -0.6950769198937773
        win_rate_is: 0.20598591549295775
        ic_oos: -0.04834339985160634
        icir_oos: -0.8615521385202736
        win_rate_oos: 0.20867768595041322
      10:
        ic_is: -0.05834931583898565
        icir_is: -0.7550903468581993
        win_rate_is: 0.18896713615023475
        ic_oos: -0.0509140038362134
        icir_oos: -0.8912080678760036
        win_rate_oos: 0.17768595041322313
      20:
        ic_is: -0.05519812850697503
        icir_is: -0.7796462954066856
        win_rate_is: 0.18368544600938966
        ic_oos: -0.052985877902134625
        icir_oos: -0.904588203868677
        win_rate_oos: 0.2024793388429752
  cp04:
    style_r_squared: 0.11406013504438384
    alpha_survival_ratio: 0.7612
    extreme_ratio: 0.023111
    barra_residual_ic: -0.030734
    barra_residual_icir: -0.459204
    dominant_style_exposure: vol_20d
    style_crowding_risk: medium
    style_exposures:
      log_circ_cap: 0.08733688498510546
      book_to_price: 0.13425923700583997
      mom_12_1: 0.19727198242653837
      str_1m: 1.2759691191651095
      vol_20d: 24.484617761482863
      turnover_20d: 3.335654712662005
      ep_ratio: 0.3788559109862046
    distribution_skew: 1.4372
    distribution_kurt: 2.2755
    distribution_zero_ratio: 0.0
  cp05:
    max_lib_corr: 0.0
    is_near_duplicate: false
    incremental_ic: null
    nearest_factor_id: null
    nearest_factor_expression: null
    all_correlations: {}
    exceeds_threshold: false
  cp06:
    sign_consistency: 1.0
    train_validation_decay: 1.0083
    sign_consistent: true
    ic_by_year:
      2015: -0.03356329171650554
      2016: -0.04031696626166032
      2017: -0.03910205951466245
      2018: -0.05564254150916523
      2019: -0.05204551512217917
      2020: -0.038627692471904715
      2021: -0.02096456710327177
      2022: -0.03741906004266764
      2023: -0.04333476697078686
    worst_quarter_ic: -0.060104
    best_quarter_ic: -0.00608
    ic_autocorr_lag1: 0.086023
    cum_ic_max_drawdown: -87.715542
    split_ic_means:
    - -0.04549030500264493
    - -0.029347815082690354
    - -0.042248972559393465
    - -0.04442056138218026
    split_dispersion: 0.1603
    n_splits: 4
  feasibility:
    turnover_mean: 0.8014093016745716
    liquidity_coverage: 0.6846498297515107
    tail_concentration: 0.007160010349375038
    small_cap_concentration: 0.31723869523767767
    signal_half_life: 5.0
    signal_autocorr_lag1: 0.8942
    rebalance_stress:
      value: 0.00838107108878996
      rebalance_stress_bucket: low
    ic_half_life_days: null
mt_budget:
  score: 0.0
  bucket: low
  terms:
    family: 0.0
    direction: 0.0
    exposure: 0.0
  search_adjusted:
    raw: 0.9
    adjusted: 0.9
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
      value: 0.9632
      threshold: 0.8
    sign_flip:
      passed: true
      train_ic: -0.04004418106211288
      val_ic: -0.040376913506727244
    ic_oos_min:
      passed: true
      value: -0.040376913506727244
      threshold: 0.008
    oos_decay:
      passed: true
      value: 1.0083
      threshold: 0.2
    mono_flip:
      passed: true
      train: -0.9999999999999999
      validation: -0.9999999999999999
    near_duplicate:
      passed: true
      max_corr: 0.0
      nearest: null
coverage: 0.9632
expression: Div(Std($amount, 10), Mean($amount, 10))
```

## Available Charts

The following PNG charts exist in `vault/factors/F001/` and may be embedded via `![[F001/<name>.png]]`. **Do not embed any chart name that is not on this list** — the file would not exist.

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

Write a deep analytical report on `F001`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Embed only charts listed in the **Available Charts** section (skip any section whose chart is unavailable). Output path: `vault/factors/F001.md`.

