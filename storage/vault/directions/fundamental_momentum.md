---
direction_tag: fundamental_momentum
status: dead
priority: low
rounds: 1
admits: 0
last_batch: batch_022
last_admits: []
last_goal: 首批 4 DSL 候选探索 PE/PB/PS 变化率作为 cross-section signal。Edge 来自 earnings drift
  + valuation mean-reversion；与 value_liquidity_interaction 的 PE×turnover 交互不同——这里是纯单一指标的变化率。目标
  ≥1 admit。
last_activity: '2026-04-20T20:09:07Z'
created_batch: batch_022
members: []
retired_members: []
merged_into: null
---
# fundamental_momentum

## Hypothesis

PE/PB/PS 变化率（rate of change）携带超出绝对水平的预测信息。Edge 来源：
- **Earnings drift**: PE 变化反映 earnings expectation 修正；A 股散户对 EPS 修订反应慢，drift 持续 5-20 天
- **Mean reversion of valuation**: 极端 PE/PB 变化（无论方向）通常被反向修正
- **Cross-sectional rotation**: 持续 PE 上升的股票（被持续高估）跑输

value_liquidity_interaction 方向已测试 PE/PB rate × turnover 交互（全 reject），但 **未单独测试 PE/PB 纯变化率**作为 cross-section 信号。本方向填补此缺口。

## Current Focus

**新方向首批 batch_022**：扫 PE / PB / PS 在不同窗口的变化率，建立基线 IC 并比较与 F002 (pb_amount_ratio) 的库相关度。

## Threads

### T001: PE 变化率 [✗ DISPROVEN batch_022]
**Question**: PE 20d 变化率是否携带 forward IC？
**Evidence trail**:
- [[batches/batch_022/candidates/C001|batch_022 C001]]: 20d PE rate → ic=-0.025 ls_t=-1.22 mono=-0.30 r²=0.512 incr=-0.024 → reject
- [[batches/batch_022/candidates/C003|batch_022 C003]]: PE rank trend → ic=-0.022 ls_t=-1.81 mono=-0.70 r²=0.315 incr=-0.021 → reject
**Conclusion**: PE rate weak (ls_t<2)，rank-based variant 改善 mono 但 ls_t 仍弱。

### T002: PB / PS 变化率 [✗ DISPROVEN batch_022]
**Evidence trail**:
- [[batches/batch_022/candidates/C002|batch_022 C002]]: 20d PB rate → ic=-0.032 ls_t=-1.49 r²=**0.811** catastrophic → reject
**Conclusion**: PB rate r²=0.811 暴露其几乎完全 vol_20d 衍生。

### T003: 综合估值变化 [✗ DISPROVEN batch_022]
**Evidence trail**:
- [[batches/batch_022/candidates/C004|batch_022 C004]]: 综合 PE+PB+PS rate → ls_t=-1.27 → reject
**Conclusion**: 等权聚合不救弱信号。

## Known Failures
- C001 (batch_022): 20d PE rate — ls_t=-1.22 weak + mono=-0.30 + r²=0.512 poor + incr_ic=-0.024 库 reducer
- C002 (batch_022): 20d PB rate — ls_t=-1.49 weak + r²=**0.811 catastrophic** (vol_20d 衍生)
- C003 (batch_022): PE rank trend — ls_t=-1.81 仍 weak + incr_ic=-0.021 (rank-based 改善 mono 但救不了 ls_t)
- C004 (batch_022): 综合 PE+PB+PS rate — ls_t=-1.27 weak (聚合不救弱信号)

## Related
- [[value_liquidity_interaction]]  (已测 PE/PB rate × turnover 交互，但未单独测纯变化率)
- [[barra_residual_alpha]]  (saturated；本方向 hypothesis 上 ep_ratio 已是 Barra style)

## Narrative Log
### 2026-04-21 [[batches/batch_022/judge|batch_022]]
**admit=0 / reserve=0 / reject=4 — direction status: exploring → dead**

PE/PB/PS 变化率全部 weak (ls_t -1.22 to -1.81，全 < 2) + library reducer (incr_ic 全负) + r² 普遍 poor。Rank-based variant 改善 mono 但仍弱。

**核心元教训**：A 股 csi1000 universe 的 fundamental ratio rates 不构成独立 alpha——市场 reaction 速度可能快于 20d 能 capture 的水平。F002 (PB/amount 绝对水平) 已成功证明绝对 fundamental ratios 可用，但变化率不行。

**Direction operations**: status `exploring → dead`；priority `medium → low`。不进入 retry pool。
