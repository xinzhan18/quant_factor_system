---
factor_id: F004
direction: barra_residual_alpha
admitted_in_batch: batch_012
---

# Report Packet — F004

## Factor YAML Summary

```yaml
name: barra_residual_return
expression: null
source_type: python
family_tag: barra_residual_alpha
validation_metrics:
  ic_mean: 0.024137849522787524
  ic_ir: 0.2929806081686563
  ic_win_rate: 0.6024844720496895
  monotonicity: 0.9999999999999999
  long_short_mean: 0.0019396953067214923
risk_metrics:
  style_r_squared: 0.0384476828278949
  alpha_survival_ratio: 1.3534
python_path: storage/vault/batches/batch_012/python_candidates/C001.py
```

## Direction Context

---
direction_tag: barra_residual_alpha
status: productive
priority: high
rounds: 4
admits: 4
last_batch: batch_013
last_admits:
- F005
last_goal: 'Extend Barra residual hypothesis: vol_20d-only residual + size-neutral
  residual + residual×turnover interaction (round 2)'
last_activity: '2026-04-19T15:13:34Z'
created_batch: batch_012
members:
- F004
- F{next}
- F005
merged_into: null
---
# barra_residual_alpha

## Hypothesis

All existing directions hit vol_20d/str_1m style coupling as structural bottleneck — every DSL candidate either has Barra dominant style exposure or is near-duplicate of existing factors. The residual from regressing returns on Barra style factors represents idiosyncratic alpha orthogonal to known risk.

** Barra residual alpha  = Regress(Returns ~ vol_20d + str_1m + turnover_20d + log_circ_cap + book_to_price + mom_12_1 + ep_ratio) → Residuals

经济直觉：Barra 风格因子吸收了市场 common risk；如果 residual 仍携带 IC，说明存在风格无法解释的异质波动。

## Current Focus

**新方向首批 batch**：测试 Barra residual IC 是否 > 0 且独立于现有因子库（F001/F002/F003）。

## Threads

### T001: Barra residual 有效性 [✓ ANSWERED batch_012]
**Question**: Barra residual returns是否携带独立于风格因子的 alpha？
**Evidence trail**:
- [[batches/batch_012/candidates/C001|batch_012 C001]]: IC=0.024 ICIR=0.293 ls_t=7.34 Barra_residual_IC=0.033 > raw IC=0.024 → **admit → [[factors/F004]]**
- [[batches/batch_012/candidates/C003|batch_012 C003]]: Barra_residual_IC=0.033（与 C001 相当）但 style_r²=0.289 + vol_20d exposure=15.6 耦合严重 → **reserve**
**Next probes**: 扩展 Barra residual + volume 交互候选

### T002: 残差与其他因子正交性 [◉ ACTIVE]
**Question**: Barra residual 与 F001/F002/F003 的增量 IC 是否 > 0？vol-20d-only residual 是否可行？
**Evidence trail**:
- [[batches/batch_012/candidates/C001|batch_012 C001]]: incremental_ic=0.032 max_corr=0.15（F002） → 正交
- [[batches/batch_013/candidates/C001|batch_013 C001]]: Barra_residual_alpha_60d → admit (ICIR=0.293 ls_t=7.34)；vol_20d dominant style (coef=4.44) 但 residual IC=0.033 > raw IC=0.024
- [[batches/batch_013/candidates/C002|ba

## Judge Synthesis

---
candidate_id: C001
batch_id: batch_012
direction: barra_residual_alpha
expression: storage/vault/batches/batch_012/python_candidates/C001.py
verdict: admit
thread_id: T001
factor_id: F004
factor_name: barra_residual_return
key_metrics_short: "IC=0.024 ICIR=0.293 ls_t=7.34"
reject_reason_short: null
---

# C001 — Barra Residual Alpha (Python)

> [!success]+ Verdict: **ADMIT** · thread [[directions/barra_residual_alpha#T001|T001]]
> **档位**: CP01 ✓ · CP02 `aligned` · CP03 `strong` · CP04 `acceptable` · CP05 `low` · CP06 `stable`
> **OOS**: IC=**==0.024==** · ICIR=**==0.293==** · ls_t=**==7.34==** · style_r²=0.038 · alpha_surv=**==1.35==** · max_corr=0.15 · mt_bucket=`low`
> **机制一句话**: Barra风格因子残差项——剥离 vol_20d/str_1m/turnover_20d 等7个风格因子后的残余异质收益率，携带独立于已知风险的alpha。

> [!info] Parent: [[batches/batch_012/judge|batch_012 judge]] · Direction: [[directions/barra_residual_alpha]] · Nearest: [[factors/F002]]

## 表达式解读

本候选为 Python 实现（`C001.py`），属于 Barra residual alpha 方向的首批探测。表达式通过回归 7 个 Barra 风格因子（vol_20d、str_1m、turnover_20d、log_circ_cap、book_to_price、mom_12_1、ep_ratio）于日收益率，提取残差作为因子值——该残差代表风格因子无法解释的异质波动。

经济直觉：Barra 风格因子吸收了市场 common risk；如果 residual 仍携带 IC，说明存在风格无法解释的异质 alpha。本候选是方向 hypothesis 的首个直接验证。

## CP01 Hard Gates ✓

8 项 gate 全过：
- ✓ compute_error
- ✓ coverage: 0.9997 ≥ 0.80
- ✓ sign_flip: train +0.0349 / val +0.0241（同号）
- ✓ forbidden
- ✓ ic_oos_min: |0.0241| ≥ 0.008
- ✓ oos_decay: 0.6908 ≥ 0.20
- ✓ mono_flip: train 1.0 / val 1.0（同号，完美单调）
- ✓ near_duplicate: max_corr 0.1503 < 0.9（nearest F002）

## CP02 Mechanism Alignment · `aligned`

**机制**：本候选通过回归 Barra 风格因子族提取残差收益率——直接量化"风格无法解释的异质 alpha"。这是该方向的定义性机制，与 hypothesis 完全一致。

**与 hypothesis 一致性**：[[directions/barra_residual_alpha#Hypothesis]] 假设"Barra 风格因子吸收了市场 common risk；如果 residual 仍携带 IC，说明存在风格无法解释的异质波动"。本候选正是该假设的直接操作化，barra_residual_ic=0.0327、alpha_survival=1.35 均证实 residual 携带独立 alpha。

**持续性**： Barra 风格因子结构相对稳定（vol/turnover/size/valuation 都是慢变量），残差 alpha 的 edge 不会因短期市场噪声消失；ic_by_year 2015-2023 全部同号（0.031→0.019，缓慢衰减但从未反向）验证了这一点。

**失效场景**： 风格结构突变（如 2021 年后散户化、2022 年宏观风险重构）可能导致残差性质改变；但 style_r² 仅 0.038（几乎无风格锁定），说明残差本身对风格切换有天然抗性。

**与近邻差异**： [[factors/F002]]（Div($pb_ratio, Mean($amount, 20))）捕捉价值-流动性交互——是经验性 DSL 因子；本候选是 Barra 残差的机制性提取，方向完全不同（F002 残差回归 Barra 后仍携带 alpha，与本候选互为独立方向）。

→ **aligned**

## CP03 Statistical Strength · `strong`

| 指标 | IS | OOS | 档位 | 阈值 |
|---|---|---|---|---|
| IC | 0.0349 | **==0.024==** | strong | \|x\|>0.015 |
| ICIR | 0.611 | **==0.293==** | borderline | \|x\|>0.30 |
| ls_t | 22.69 | **==7.34==** | strong | \|x\|>3 |
| decay | — | 0.691 | moderate | >0.8 |

**Rank-order 验证**：monotonicity_oos = **==1.0==**（|x| > 0.8 → 完美单调）。Q1..Q5 梯度 (OOS): q1=-0.00130, q2=-0.00029, q3=+0.00025, q4=+0.00053, q5=+0.00063 → 严格单调递增，非"一桨驱动"，long-short 收益由全档位梯度贡献。

**样本量**：n_days_oos=483（>> 200，统计显著性充足）。

**MT 调整**：`mt_bucket = low`；`search_adjusted = 0.7268`（bucket=high）。low 档原档保留，无须降档。

→ **strong**（IC strong + ls_t 远超阈值，ICIR borderline 但 ls_t=7.34 独立验证了信号真实性）

## CP04 Risk Cleanness · `acceptable`

| 指标 | 值 | 档位 | 阈值 |
|---|---|---|---|
| style_r_squared | **==0.038==** | clean | <0.12 |
| alpha_survival | **==1.35==** | clean | >0.50 |
| extreme_ratio | 0.027 | borderline | <0.01 |
| barra_residual_ic | **==0.0327==** | — | — |
| dominant_style | `vol_20d` | — | — |

**Alpha killer**（按 style_contributions 归因，leave-one-out 风格）：
- `vol_20d`: delta_ic=**+0.025** (65.8%)——控 vol_20d 后 IC 损失最大，说明 vol_20d 是主要遮蔽因子
- `turnover_20d`: delta_ic=+0.008 (21.1%)
- 总 killer 占比: ~87%；剩余 ~13% 分散于其它因子或 joint effect

两项 clean 一项 borderline → **acceptable**

> [!WARNING] Barra residual 遮蔽结构：本候选 vol_20d 风格暴露高达 4.44（log_circ_cap 仅 0.09），说明残差中仍携带 vol_20d 异质波动。下轮需考虑对 vol_20d 做 orthogonalize 或 quantile-normalize，以进一步提纯。

## CP05 Redundancy · `low`

- `max_lib_corr` = **==0.150==** → low 档（< 0.30）
- `is_near_duplicate` = false（硬闸未触发）
- nearest = [[factors/F002]]
- `incremental_ic` = **==0.032==**（> 0.005，库增值显著）

→ **low**。admit 增值：本候选 Barra residual 机制与库中所有 DSL 因子正交（max_corr 仅 0.15），且 incremental_ic=0.032 远超阈值，代表全新机制空间的 alpha 提取。

## CP06 Validation Stability · `stable`

| 指标 | 值 | 档位 |
|---|---|---|
| sign_consistency | **==1.0==** | stable |
| train_validation_decay | **==0.691==** | mixed (0.5–0.8) |

**时序稳健**：
- `ic_autocorr_lag1` = 0.0885（|x|<0.15 → IC 日独立，ICIR 置信度高）
- `cum_ic_max_drawdown` = **==-0.639==**（>-30，轻度回撤）
- `worst_quarter_ic` = 0.0126 / `best_quarter_ic` = 0.0545（**同号**，worst ≈ 2× |ic_oos|，在容忍范围）
- `ic_by_year`（2015→2023）：0.031→0.029→0.032→0.040→0.042→0.041→0.030→0.029→0.019——**全部同号，缓慢衰减**，2021 年后 edge 轻度下降但从未变号

→ **stable**（核心两项 sign_consistency=1.0 稳定；train_validation_decay=0.69 处于 mixed 边界但不触发 unstable；ic_by_year 9 年同号是最佳佐证）

## Feasibility（警示标记）

- `signal_autocorr_lag1` = **==0.9947==**（极高自相关 → 信号半衰期虽标注 20d，但实际由高持续性成分主导，非 pure mean-reversion）
- `ic_half_life_days` = 3.96（< 5 天，短半衰期，与 high autocorrelation 共振，说明信号存在快速衰减成分）
- `small_cap_concentration` = 0.250（< 0.4，正常）
- `liquidity_coverage` = 0.749（> 0.5，正常）

**结论**：信号持续性依赖高自相关成分，非纯粹的独立日效应。需注意组合构建中信号衰减速度偏快，但 Barra residual 本身的 alpha 性质独立于换手率问题。

## Verdict Summary

> [!success]+ Verdict: ADMIT
>
> **核心理由**: C001 是 barra_residual_alpha 方向的首个候选，直接验证 hypothesis——Barra 残差携带独立 alpha（IC=0.024, ls_t=7.34）。CP03 strong（IC + tstat 双重验证）、CP05 low（库增值清晰，incremental_ic=0.032）、CP06 stable（9 年 IC 同号，sign_consistency=1.0）。 Barra residual_ic=0.033 证明残差确实携带风格外 alpha。唯一关注点：signal_autocorr_lag1=0.995 暗示高持续性成分，但这是 Barra residual 的固有特性（风格正交 + 日频信号），不影响 alpha 有效性。
>
> **风险旗标**:
> - CP06 decay=0.69 处于 mixed 边界（0.5-0.8），主因 IC OOS/IS 比值，并非 sign flip，9 年同号佐证稳定
> - CP04 extreme_ratio=0.027 borderline，但 style_r²=0.038 + alpha_surv=1.35 双clean，说明残差边缘分布可控
> - Feasibility: signal_autocorr_lag1=0.995 标记为黄色（不阻断，但组合构建需关注衰减速度）
>
> F{id} 由 Phase 4 分配，本文件 frontmatter `factor_id: null`。

## Detailed Metrics

All numeric fields from Phase 2 / Phase 3 for this candidate. Tables in the report should cite these directly — do not mark fields as `—` if they appear below.

```yaml
metrics:
  cp03:
    ic_oos: 0.024137849522787524
    icir_oos: 0.2929806081686563
    ls_tstat_oos: 7.3384
    ic_is: 0.03494417936321482
    icir_is: 0.6110105968169841
    ic_std_is: 0.05719079103579221
    ic_std_oos: 0.08238719167683756
    n_days_is: 1705
    n_days_oos: 483
    ic_win_rate_is: 0.7366568914956012
    ic_win_rate_oos: 0.6024844720496895
    monotonicity_is: 0.9999999999999999
    monotonicity_oos: 0.9999999999999999
    quintile_returns_is:
      q1: -0.0005548667395487428
      q2: 0.00021502860181499273
      q3: 0.0006888446514494717
      q4: 0.00111021613702178
      q5: 0.0018823841819539666
    quintile_returns_oos:
      q1: -0.0012987038353458047
      q2: -0.0002856311039067805
      q3: 0.000251195568125695
      q4: 0.0005250171525403857
      q5: 0.0006267931894399226
    ls_mean_is: 0.002466879675763624
    ls_mean_oos: 0.0019396953067214923
    ls_sharpe_oos: 5.2952
    ls_sortino_oos: 10.8807
    ls_calmar_oos: 9.7315
    ls_max_dd_oos: -0.0502
    ls_sharpe_is: 8.7188
    ls_tstat_is: 22.6854
    ls_max_dd_is: -2.1806
    ic_by_horizon:
      1:
        ic_is: 0.03494417936321482
        icir_is: 0.6110105968169841
        win_rate_is: 0.7366568914956012
        ic_oos: 0.024137849522787524
        icir_oos: 0.2929806081686563
        win_rate_oos: 0.6024844720496895
      3:
        ic_is: 0.020321200388319815
        icir_is: 0.33982386275370224
        win_rate_is: 0.6199413489736071
        ic_oos: 0.01828447329268999
        icir_oos: 0.2088729806518091
        win_rate_oos: 0.5859213250517599
      5:
        ic_is: 0.014415620043228048
        icir_is: 0.23202042169399487
        win_rate_is: 0.5888563049853373
        ic_oos: 0.016853299725019828
        icir_oos: 0.19929951684134606
        win_rate_oos: 0.5859213250517599
      10:
        ic_is: 0.005861432578421294
        icir_is: 0.08887745875170228
        win_rate_is: 0.5448680351906159
        ic_oos: 0.010681248847919489
        icir_oos: 0.14576553571047404
        win_rate_oos: 0.5714285714285714
      20:
        ic_is: -0.0032151377614464986
        icir_is: -0.04734568541712943
        win_rate_is: 0.4797653958944281
        ic_oos: 0.004016337675903354
        icir_oos: 0.062147747816688276
        win_rate_oos: 0.5217391304347826
  cp04:
    style_r_squared: 0.0384476828278949
    alpha_survival_ratio: 1.3534
    extreme_ratio: 0.026752
    barra_residual_ic: 0.032669
    barra_residual_icir: 0.514591
    dominant_style_exposure: vol_20d
    style_crowding_risk: medium
    style_exposures:
      log_circ_cap: 0.0893331572101889
      book_to_price: 0.3767492441972965
      mom_12_1: 0.13605414762694423
      str_1m: 0.37845879537747706
      vol_20d: 4.443626892878715
      turnover_20d: 2.103752325596926
      ep_ratio: 0.361659966765294
    distribution_skew: 1.2507
    distribution_kurt: 2.6915
    distribution_zero_ratio: 0.0
  cp05:
    max_lib_corr: 0.1503
    is_near_duplicate: false
    incremental_ic: 0.032119
    nearest_factor_id: F002
    nearest_factor_expression: Div($pb_ratio, Mean($amount, 20))
    all_correlations:
      F001: -0.044344349702167385
      F002: 0.1503430635890472
      F003: 0.017354535789916515
    exceeds_threshold: false
  cp06:
    sign_consistency: 1.0
    train_validation_decay: 0.6908
    sign_consistent: true
    ic_by_year:
      2015: 0.03148063772313457
      2016: 0.02936471312869685
      2017: 0.03181221748922152
      2018: 0.04026769090024178
      2019: 0.04152919270981236
      2020: 0.04056546173452365
      2021: 0.02961234579268367
      2022: 0.02928762932823729
      2023: 0.018966701336402284
    worst_quarter_ic: 0.012627
    best_quarter_ic: 0.054517
    ic_autocorr_lag1: 0.088503
    cum_ic_max_drawdown: -0.639499
    split_ic_means:
    - 0.033453896033433815
    - 0.02512136262304077
    - 0.02393050847293512
    - 0.013961529140398339
    split_dispersion: 0.2868
    n_splits: 4
  feasibility:
    turnover_mean: 0.1756110727902536
    liquidity_coverage: 0.7489889970506287
    tail_concentration: 0.006870323610731263
    small_cap_concentration: 0.2495623897223869
    signal_half_life: 20.0
    signal_autocorr_lag1: 0.9947
    rebalance_stress:
      value: 0.0016108446244840772
      rebalance_stress_bucket: low
    ic_half_life_days: 3.9649
mt_budget:
  score: 0.3848
  bucket: low
  terms:
    family: 0.6596145233104855
    direction: 0.0
    exposure: 0.275
  search_adjusted:
    raw: 0.9
    adjusted: 0.7268
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
      value: 0.9997
      threshold: 0.8
    sign_flip:
      passed: true
      train_ic: 0.03494417936321482
      val_ic: 0.024137849522787524
    ic_oos_min:
      passed: true
      value: 0.024137849522787524
      threshold: 0.008
    oos_decay:
      passed: true
      value: 0.6908
      threshold: 0.2
    mono_flip:
      passed: true
      train: 0.9999999999999999
      validation: 0.9999999999999999
    near_duplicate:
      passed: true
      max_corr: 0.1503
      nearest: F002
coverage: 0.9997
expression: storage/vault/batches/batch_012/python_candidates/C001.py
```

## Available Charts

The following PNG charts exist in `vault/factors/F004/` and may be embedded via `![[F004/<name>.png]]`. **Do not embed any chart name that is not on this list** — the file would not exist.

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

Write a deep analytical report on `F004`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Embed only charts listed in the **Available Charts** section (skip any section whose chart is unavailable). Output path: `vault/factors/F004.md`.

