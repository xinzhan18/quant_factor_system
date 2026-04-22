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

> [!abstract]+ 方向概要
> **状态**　🔴 dead · priority=low · rounds=1 · admits=0
> **最近**　[[batches/batch_022/judge|batch_022]] · 2026-04-21 · admit=0 / reserve=0 / reject=4
> **一句话**　PE/PB/PS 纯变化率在 A 股 csi1000 不构成独立 alpha，全 weak。

---

## Hypothesis

PE/PB/PS 变化率（rate of change）携带超出绝对水平的预测信息。Edge 来源：
- **Earnings drift**: PE 变化反映 earnings expectation 修正；A 股散户对 EPS 修订反应慢，drift 持续 5-20 天
- **Mean reversion of valuation**: 极端 PE/PB 变化（无论方向）通常被反向修正
- **Cross-sectional rotation**: 持续 PE 上升的股票（被持续高估）跑输

value_liquidity_interaction 方向已测试 PE/PB rate × turnover 交互（全 reject），但 **未单独测试 PE/PB 纯变化率**作为 cross-section 信号。本方向填补此缺口。

> [!warning] ⚠️ Hypothesis 已证伪（batch_022）
> 4 个 DSL 候选全 reject：ls_t 范围 -1.22 到 -1.81（全 <2），incr_ic 全负（库 reducer），r² 普遍 poor；C002 PB rate r²=0.811 catastrophic 暴露其几乎完全 vol_20d 衍生；rank-based variant (C003) 改善 mono=-0.70 但 ls_t 仍弱；等权聚合 (C004) 不救弱信号。市场 reaction 速度可能快于 20d 能 capture 的水平。
> **元教训**　A 股 csi1000 上 fundamental ratio rates（PE/PB/PS 纯变化率）不构成独立 alpha；F002 (PB/amount 绝对水平) 已证明绝对 fundamental ratios 可用，但变化率不行——下一次考察 fundamental 信号时默认跳过"变化率"形式，直接走 level-based 或 level × interaction。

---

## Threads

### T001: PE 变化率 [✗ DISPROVEN batch_022]

> [!failure]+ Thread 结论
> **Question**: PE 20d 变化率是否携带 forward IC？
> **Evidence trail**:
> - [[batches/batch_022/candidates/C001|batch_022 C001]]　20d PE rate → ic=-0.025 ls_t=-1.22 mono=-0.30 r²=0.512 incr=-0.024 → reject
> - [[batches/batch_022/candidates/C003|batch_022 C003]]　PE rank trend → ic=-0.022 ls_t=-1.81 mono=-0.70 r²=0.315 incr=-0.021 → reject
>
> **Conclusion**: PE rate weak (ls_t<2)；rank-based variant 改善 mono 但 ls_t 仍弱。

### T002: PB / PS 变化率 [✗ DISPROVEN batch_022]

> [!failure]+ Thread 结论
> **Question**: PB 或 PS 的 20d 变化率是否在 cross-section 上有独立预测力？
> **Evidence trail**:
> - [[batches/batch_022/candidates/C002|batch_022 C002]]　20d PB rate → ic=-0.032 ls_t=-1.49 r²=**0.811** catastrophic → reject
>
> **Conclusion**: PB rate r²=0.811 暴露其几乎完全 vol_20d 衍生——信号被波动率完全解释。

### T003: 综合估值变化 [✗ DISPROVEN batch_022]

> [!failure]+ Thread 结论
> **Question**: 等权聚合 PE + PB + PS 变化率是否能叠加成可用信号？
> **Evidence trail**:
> - [[batches/batch_022/candidates/C004|batch_022 C004]]　综合 PE+PB+PS rate → ls_t=-1.27 → reject
>
> **Conclusion**: 等权聚合不救弱信号；三个成分全 weak 则聚合依旧 weak。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_022/candidates/C001\|C001]] | 20d PE rate | ls_t=-1.22 weak + mono=-0.30 + r²=0.512 + incr_ic=-0.024 库 reducer |
| [[batches/batch_022/candidates/C002\|C002]] | 20d PB rate | ls_t=-1.49 weak + r²=**0.811 catastrophic** (vol_20d 衍生) |
| [[batches/batch_022/candidates/C003\|C003]] | PE rank trend | ls_t=-1.81 仍 weak + incr_ic=-0.021 (rank 改 mono 救不了 ls_t) |
| [[batches/batch_022/candidates/C004\|C004]] | 综合 PE+PB+PS rate | ls_t=-1.27 weak (等权聚合不救弱信号) |

---

## Related

- 🟡 [[value_liquidity_interaction]] `saturated` — 已测 PE/PB rate × turnover 交互（全 reject）；本方向填补其未单独测"纯变化率"的缺口，结论同样证伪
- 🟡 [[barra_residual_alpha]] `saturated` — 本方向 hypothesis 上 ep_ratio 已是 Barra style，天然受其约束

---

## Narrative Log

> [!quote]+ 2026-04-21 · [[batches/batch_022/judge|batch_022]]
> **admit=0 / reserve=0 / reject=4** — PE/PB/PS 变化率全部 weak (ls_t -1.22 到 -1.81，全 <2) + library reducer (incr_ic 全负) + r² 普遍 poor。Rank-based variant 改善 mono 但仍弱。
> - T001 PE 变化率：`[◉ ACTIVE] → [✗ DISPROVEN batch_022]`
> - T002 PB/PS 变化率：`[◉ ACTIVE] → [✗ DISPROVEN batch_022]`
> - T003 综合估值变化：`[◉ ACTIVE] → [✗ DISPROVEN batch_022]`
> - **核心元教训**：A 股 csi1000 universe 的 fundamental ratio rates 不构成独立 alpha——市场 reaction 速度可能快于 20d 能 capture 的水平。F002 (PB/amount 绝对水平) 已成功证明绝对 fundamental ratios 可用，但变化率不行。
> - **MT budget**: 本 batch 消耗 4 tests，全 reject，无 admit 占预算。
> - **Direction operations**: status `exploring → dead`（不可逆）；priority `medium → low`；不进入 retry pool。
