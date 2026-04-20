---
direction_tag: ohlc_temporal_aggregation
status: productive
priority: high
rounds: 1
admits: 1
last_batch: batch_017
last_admits:
- F006
last_goal: 首批 5 DSL 候选探索多日 OHLC 聚合 patterns. 单日 body/shadow 已在 intraday_price_formation
  全 mono_sign_flip——本批测试 smoothed (5d/20d mean) 版本是否 reveal persistent intraday flow。同时测
  close-strength (close/high) 和 sign-frequency 路径。目标 ≥1 admit；首批失败则方向 dead。
last_activity: '2026-04-20T18:40:56Z'
created_batch: batch_017
members:
- F006
retired_members: []
merged_into: null
---
# ohlc_temporal_aggregation

## Hypothesis

Single-day OHLC body/shadow signals (intraday_price_formation 方向) 全部 mono_sign_flip 失败——单日内 noise 太大，盖过任何稳定信号。但 **多日 smoothed/aggregated** 版本可能 reveal persistent intraday flow patterns：连续 N 天 close > open 反映 sustained buying pressure，与单日的 random walk 完全不同性质。

经济直觉：
- 单日 body 是 noisy 的（开盘到收盘是 random walk + microstructure noise）
- 5d/20d mean(body) 累加同向偏移 = persistent order flow asymmetry
- Trend-following 的反向：高 mean body → 持续买入 → 已 stretched → 短期反转

## Current Focus

**新方向首批 batch_017**：测试 5d/20d 聚合的 body / 强度 / 方向一致性 是否携带超出 single-day 的信号。

## Threads

### T001: 多日 smoothed body 是否产生信号 [✓ ANSWERED batch_017]
**Question**: Mean(body, 5) 和 Mean(body, 20) 是否 OOS IC > 0.008？sign 是否稳定？
**Evidence trail**:
- [[batches/batch_017/candidates/C001|batch_017 C001]]: 5d signed body → ic=-0.043 ls_t=-2.87 alpha_surv=1.076 (Barra-clean) 但 incr_ic=-0.050 (库 reducer) + cum_dd=-105 → reject
- [[batches/batch_017/candidates/C002|batch_017 C002]]: 20d signed body → ic=-0.042 ls_t=-2.62 r²=0.638 (vol-coupled) → reject
**Conclusion**: 5d signed body Barra-clean 但与库 F003 反向冲突；20d 加深 vol_20d 耦合。Hypothesis 部分成立——5d 保留 idiosyncratic 信号但与现库不正交。

### T002: Sign-of-body 频率信号 [◉ ACTIVE]
**Question**: 多日内 close>open 的频率（bullish bar count）是否 forward-predictive？
**Evidence trail**:
- [[batches/batch_017/candidates/C003|batch_017 C003]]: 5d Mean(Sign(close-open)) → ic=-0.033 ls_t=-3.55 mono=-0.80 alpha_surv=1.014 incr_ic=-0.031 → **reserve** (CP02-04 完美但 incr_ic 负)
**Next probes**: C003 与 C005 admit symmetric——下批做 C005-C003 对称信号或 spread

### T003: Close-vs-high 强度信号 [✓ ANSWERED batch_017]
**Question**: 5d mean(close/high) 测度 intraday close strength；持续 close 接近 high 是 sustained demand，是否 forward-predictive？
**Evidence trail**:
- [[batches/batch_017/candidates/C004|batch_017 C004]]: Mean(close/high, 5) → ic=+0.052 mono=+0.9 但 alpha_surv=0.003 catastrophic + ls_t=1.91<2 → reject (vol_20d 衍生)
- [[batches/batch_017/candidates/C005|batch_017 C005]]: Mean(upper-shadow, 5) → ic=+0.024 ls_t=3.20 mono=+0.90 alpha_surv=1.508 incr_ic=+0.031 cum_dd=-3.5 → **admit → upper_shadow_persistence_5d**
**Conclusion**: Close-vs-high 强度 hypothesis 完整验证——upper-shadow 形式（持续抛压 → 反转涨）是有效载体；close/high 形式被 vol_20d 完全解释。

## Known Failures
- C001 (batch_017): 5d signed body — incr_ic=-0.050 库 reducer + cum_dd=-105 整库最深
- C002 (batch_017): 20d signed body — style_r²=0.638 poor + incr_ic=-0.039
- C004 (batch_017): 5d close/high — alpha_surv=0.003 catastrophic (vol_20d derivative) + ls_t=1.91 weak

## Related
- [[lessons#Structural Constraints]]
- [[intraday_price_formation]]  （saturated；单日 body/shadow 已穷尽）
- [[return_distribution_signals]]  （dead；同样 vol_20d 主导）

## Narrative Log
### 2026-04-21 [[batches/batch_017/judge|batch_017]]
**admit=1 / reserve=1 / reject=3 — direction status: exploring → productive (首 admit)**

**4 轮 0-admit 之后的关键突破**：
- **C005 admit → upper_shadow_persistence_5d**：5d mean upper-shadow ratio (high-close)/(high-low)。alpha_surv=1.508 (residual stronger than raw)、incr_ic=+0.031 库 adder、cum_dd=-3.5（库内最浅）、9 年 IC 全正。机制：持续 close 远低 day-high = 持续抛压 → 反转上涨。
- **C003 reserve**：5d sign-of-body frequency。CP02-04 perfect (alpha_surv=1.014, mono=-0.80)，但 incr_ic=-0.031 库 reducer。与 C005 镜像。
- **C001/C002 reject**：signed body 5d/20d，longer window 加深 vol_20d 耦合（r² 0.234→0.638）；5d Barra-clean 但 incr_ic 负。
- **C004 reject**：close/high 5d，alpha_surv=0.003 catastrophic 暴露其本质 ≡ vol_20d monotone derivative。

**核心元发现（系统层级）**：
1. **alpha_survival 是新关键判别量**：4 轮以来 18 个 reject 中部分被错过的"vol_20d 衍生" pattern 在本批通过 C004 vs C005 对照得到清晰区分——alpha_surv > 1.0 = "Barra 空间独立载体"，<< 0.40 = "vol 衍生"。**C005 admit 的核心证据是 alpha_survival=1.508，不是 ls_t/mono 单独**。
2. **5d aggregation 是 sweet spot**：单日 (intraday_price_formation 全 saturated) 与 20d (vol-coupled) 之间的 5d 窗口是 OHLC 信号的 sweet spot——既保留 idiosyncratic flow 又过滤噪声。
3. **upper-shadow 机制独立性**：C005 max_corr=0.069 with F003 (overnight gap)——OHLC 空间内 intraday-shadow 与 overnight-gap 完全机制正交。

**Direction operations**：
- status `exploring → productive`（首 admit）
- priority `medium → high`（productive 方向应提升优先级）

**下一步（batch_018）**：
1. 同方向 deepen — 5d 窗口的 OHLC pattern 变体：lower-shadow、body-position-in-range、signed body × range、跨日 body 一致性
2. C005 + C003 symmetric pair design — 5d frequency-asymmetry 信号
3. **观察**: 该方向是否能持续产 admit （alpha_surv > 1 + incr_ic > 0 是关键指标）
