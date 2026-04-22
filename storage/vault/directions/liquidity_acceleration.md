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
> **一句话**　流动性加速度 rank-order 极强 (mono=-1.00) 但 incr_ic 全负 → 被 F001 (amount CV) 结构性吸收。

---

## Hypothesis

> [!note]+ 🔵 exploring · 理论正交但实证重叠
> 流动性指标（amount, turnover_rate）的**加速度**（rate-of-change，非水平）携带超出 F001 (amount CV 离散度) 之外的信号。
> - amount/turnover 突变 → 关注度切换（事件驱动 vs 失去兴趣）
> - F001 测稳定性，本方向测**变化方向**——理论正交
> - 实证：batch_023 rank-order 强却 incr_ic 全负，与 F001 **同向冲突**

---

## Threads

### T001: 5d/60d ratio 长窗加速度 [◉ ACTIVE]

> [!success]+ rank-order 完美但被 F001 吸收
> **Question**: amount / turnover 的 5d/60d ratio 是否能在 F001 之外独立贡献 forward IC？
> **Evidence trail**:
> - [[batches/batch_023/candidates/C001|batch_023 C001]]　5d/60d amount → ic=-0.043 ls_t=-2.92 mono=-1.00 incr_ic=-0.030 corr=0.299@F001 → **reserve**
> - [[batches/batch_023/candidates/C003|batch_023 C003]]　5d/60d turnover → ic=-0.042 ls_t=-3.27 mono=-1.00 incr_ic=-0.026 → **reserve**（60d 分母比 5/20 更稳）
>
> **结论**：双 mono=-1.00 + ls_t ≈ -3 strong，但 corr ≈ 0.30 + incr_ic 全负——库 reducer pattern，等待 F001 退役后复活。
>
> **Next probes**: 更长 horizon（10d/120d）或换 base（volume 替代 amount/turnover）以绕开 F001 相关性。

### T002: 短窗 normalized acceleration [✗ CLOSED]

> [!failure]+ 短窗 delta mono 弱
> **Question**: 5d-20d turnover normalized acceleration 是否可用？
> **Evidence trail**:
> - [[batches/batch_023/candidates/C002|batch_023 C002]]　5d-20d normalized accel → mono=-0.50 weak + 与 batch_004 C003 同源 → **reject**
>
> **结论**：短窗 normalized delta 形式 mono 不稳，需长分母（60d+）才能压住噪声。

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_023/candidates/C002\|C002]] | 5d-20d turnover normalized acceleration | mono=-0.50 weak + batch_004 C003 同源 |

---

## Lessons (direction-level)

- **5d/60d ratio** 比 5d-20d delta 稳定得多——长分母压住噪声
- **F001 吸收流动性 family**：corr ≈ 0.30 + incr_ic 全负 = 结构性约束，不是 over-rejection
- 短窗 normalized acceleration (mono ≤ 0.5) 直接 skip，首选 60d+ 分母

---

## Related

- 🟢 [[amount_volatility_signal]] — F001 (amount CV) 所在方向；核心 reserve 原因
- 🔴 [[fundamental_momentum]] `dead` — 同为"变化率" family，但 rank-order 弱；本方向 rank-order 强证明有结构性 edge

---

## Narrative Log

> [!quote]+ 2026-04-21 · [[batches/batch_023/judge|batch_023]]
> **admit=0 / reserve=2 (C001+C003) / reject=1 (C002)**
> C001/C003 双 mono=-1.00 + ls_t -2.92/-3.27，但 corr≈0.30@F001 + incr_ic 全负 → reserve。C002 mono=-0.50 reject。
> **核心发现**：A 股流动性加速度 rank-order 极强但被 F001 吸收——结构性约束；F001 退役后 C001/C003 可复活。
