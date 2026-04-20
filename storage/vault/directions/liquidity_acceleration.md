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

## Hypothesis

流动性指标（amount, turnover_rate）的**加速度**（rate-of-change，非水平）携带超出 F001 (amount CV 离散度) 之外的信号。Edge：
- amount/turnover 突然加速反映关注度突变（事件驱动）；衰减反映市场失去兴趣
- F001 测稳定性，本方向测**变化方向**——理论上正交

## Current Focus

3 候选探索 amount/turnover 加速度信号。

## Threads

### T001: amount 加速度 [◉ ACTIVE]
**Question**: 5d/20d amount ratio 是否携带 forward IC？
**Evidence trail**:
- [[batches/batch_023/candidates/C001|batch_023 C001]]: 5d/60d amount → ic=-0.043 ls_t=-2.92 mono=-1.00 incr_ic=-0.030 corr=0.299@F001 → **reserve** (mono perfect 但库 reducer)

### T002: turnover 加速度 [◉ ACTIVE]
**Question**: turnover delta 是否独立于 F001 (amount CV)？
**Evidence trail**:
- [[batches/batch_023/candidates/C002|batch_023 C002]]: 5d-20d normalized accel → mono=-0.50 weak → reject (与 batch_004 C003 同源)
- [[batches/batch_023/candidates/C003|batch_023 C003]]: 5d/60d turnover → ic=-0.042 ls_t=-3.27 mono=-1.00 incr_ic=-0.026 → **reserve** (60d horizon 比 5/20 更稳)
**Conclusion**: 流动性加速度 rank-order 强 (mono=-1.00) 但 incr_ic 全负——与 F001 (amount CV) 同向冲突。

## Known Failures
- C002 (batch_023): 5d-20d turnover normalized acceleration — mono=-0.50 weak + 与 batch_004 C003 同源

## Related
- [[amount_volatility_signal]]
- [[fundamental_momentum]] (dead — fundamental rate 失败教训)

## Narrative Log
### 2026-04-21 [[batches/batch_023/judge|batch_023]]
**admit=0 / reserve=2 (C001 + C003) / reject=1 (C002)**

- C001/C003 (5d/60d amount, 5d/60d turnover) 双 mono=-1.00 完美 + ls_t -2.92/-3.27 strong，但 max_corr 0.30 + incr_ic 全负 → reserve (库 reducer pattern)
- C002 (5d-20d normalized) mono=-0.50 weak → reject

**核心发现**：A 股流动性加速度信号 rank-order 极强但与 F001 (amount CV) 同向冲突——**结构性约束**而非 over-rejection。reserve C001/C003 保留待 library 重组（若 F001 退役可复活）。

**Direction status**: `exploring` 维持。下一步可探索其他 horizon 或不同流动性 base (volume vs amount vs turnover)，但预期同 family 都会落入同 reserve pattern。
