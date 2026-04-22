---
direction_tag: liquidity_acceleration
status: exploring
priority: medium
rounds: 1
admits: 0
last_batch: batch_023
last_admits: []
last_goal: 首批 3 DSL 候选探索流动性变化率信号——amount 5d/20d 比值、turnover 5d delta、turnover 5d/60d
  比值。与 F001 (amount CV) 测稳定性正交，本批测变化方向。
last_activity: '2026-04-20T22:00:10Z'
created_batch: batch_023
members: []
retired_members: []
merged_into: null
---
# liquidity_acceleration

> [!abstract]+ 方向概要
> **状态**　🔵 exploring · priority=medium · rounds=1 · admits=0
> **最近**　[[batches/batch_023/judge|batch_023]] · 2026-04-21 · admit=0 / reserve=2 / reject=1
> **一句话**　流动性加速度 rank-order 极强 (mono=-1.00) 但与 F001 amount CV 同向冲突 → reserve。

---

## Hypothesis

流动性指标（amount, turnover_rate）的**加速度**（rate-of-change，非水平）携带超出 F001 (amount CV 离散度) 之外的信号。Edge：
- amount/turnover 突然加速反映关注度突变（事件驱动）；衰减反映市场失去兴趣
- F001 测稳定性，本方向测**变化方向**——理论上正交

---

## Current Focus

3 候选首轮探索 amount/turnover 加速度信号。batch_023 结果显示 5d/60d ratio 形式 mono=-1.00 完美但 incr_ic 全负（库 reducer）。下一步可探索其他 horizon（10d/120d？）或不同流动性 base（volume vs amount vs turnover），但预期同 family 都会落入同 reserve pattern——真正 breakthrough 需等 F001 退役后 reserve C001/C003 复活。

---

## Threads

### T001: amount 加速度 [◉ ACTIVE]

> [!note]+ Thread 进展
> **Question**: 5d/20d amount ratio 是否携带 forward IC？
> **Evidence trail**:
> - [[batches/batch_023/candidates/C001|batch_023 C001]]　5d/60d amount → ic=-0.043 ls_t=-2.92 mono=-1.00 incr_ic=-0.030 corr=0.299@F001 → **reserve** (mono perfect 但库 reducer)
>
> **Next probes**: 若 F001 退役则复活；或测试更长 horizon (10d/120d) 看是否逃离 F001 相关性。

### T002: turnover 加速度 [◉ ACTIVE]

> [!note]+ Thread 进展
> **Question**: turnover delta 是否独立于 F001 (amount CV)？
> **Evidence trail**:
> - [[batches/batch_023/candidates/C002|batch_023 C002]]　5d-20d normalized accel → mono=-0.50 weak → reject (与 batch_004 C003 同源)
> - [[batches/batch_023/candidates/C003|batch_023 C003]]　5d/60d turnover → ic=-0.042 ls_t=-3.27 mono=-1.00 incr_ic=-0.026 → **reserve** (60d horizon 比 5/20 更稳)
>
> **Conclusion**: 流动性加速度 rank-order 强 (mono=-1.00) 但 incr_ic 全负——与 F001 (amount CV) 同向冲突。
>
> **Next probes**: 换 base（volume 替代 amount/turnover）测试是否能绕开 F001 相关性。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_023/candidates/C002\|C002]] | 5d-20d turnover normalized acceleration | mono=-0.50 weak + 与 batch_004 C003 同源 |

---

## Related

- 🟢 [[amount_volatility_signal]] — F001 (amount CV) 所在方向；本方向加速度信号与 F001 同向冲突是核心 reserve 原因
- 🔴 [[fundamental_momentum]] `dead` — fundamental rate 失败教训；本方向同为"变化率"family 但 rank-order 证明有结构性 edge

---

## Narrative Log

> [!quote]+ 2026-04-21 · [[batches/batch_023/judge|batch_023]]
> **admit=0 / reserve=2 (C001 + C003) / reject=1 (C002)**
> - C001/C003 (5d/60d amount, 5d/60d turnover) 双 mono=-1.00 完美 + ls_t -2.92/-3.27 strong，但 max_corr 0.30 + incr_ic 全负 → reserve (库 reducer pattern)
> - C002 (5d-20d normalized) mono=-0.50 weak → reject
> - **核心发现**：A 股流动性加速度信号 rank-order 极强但与 F001 (amount CV) 同向冲突——**结构性约束**而非 over-rejection。reserve C001/C003 保留待 library 重组（若 F001 退役可复活）。
> - **Direction status**: `exploring` 维持。下一步可探索其他 horizon 或不同流动性 base (volume vs amount vs turnover)，但预期同 family 都会落入同 reserve pattern。
