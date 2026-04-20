---
batch_id: batch_023
direction: liquidity_acceleration
judged_at: 2026-04-21T04:18:00Z
candidates:
  - {candidate_id: C001, verdict: reserve}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reserve}
batch_summary: {total: 3, admit: 0, reserve: 2, reject: 1}
---

# batch_023 Judge Summary

> [!abstract]+ batch_023 · [[directions/liquidity_acceleration]] · 3 candidates (direction 首批)
> ❌ **admit=0** · ⏸ **reserve=2** (C001 5d/60d amount; C003 5d/60d turnover) · ❌ **reject=1** (C002 normalized accel)
> **核心发现**: 流动性加速度信号 mono=-1.00 完美 + ls_t strong (-2.92 to -3.27) — **rank-order 在方向首批就强**。但 max_corr 集中 0.27-0.32@F001 (low-medium) + incr_ic 全负 (-0.021 to -0.030)。**与 F001 (amount CV) 部分重叠 + library reducer**——admit 会稀释 F001 信号。
> **MT Budget**: cumulative 113 → **116** · direction 0 → **3** · bucket `low`

## 候选一览

| ID | Verdict | Key | 反思 | Detail |
|---|---|---|---|---|
| C001 | ⏸ reserve | 5d/60d amount, ic=-0.043 ls_t=-2.92 mono=-1.00 incr=-0.030 | 完美 rank 但库 reducer | [[batches/batch_023/candidates/C001]] |
| C002 | ❌ reject | turnover 5d-20d normalized, mono=-0.50 | 与 batch_004 C003 同源、normalized 不构进步 | [[batches/batch_023/candidates/C002]] |
| C003 | ⏸ reserve | 5d/60d turnover, ic=-0.042 ls_t=-3.27 mono=-1.00 incr=-0.026 | 60d horizon 比 5/20 稳；与 C001 同 pattern | [[batches/batch_023/candidates/C003]] |

## 跨候选对比

- **mono=-1.00 完美 cluster (C001/C003)**：5d/60d 比值（amount + turnover）双 mono 完美——**60d horizon 是 liquidity acceleration 的稳定窗口**。但 incr_ic 全负 + max_corr 0.27-0.32@F001 表明这与 F001 (amount CV) 部分重叠。
- **batch_004 C003 (turnover 5d/20d) reserve 至今未 admit** — C003 batch_023 是其 longer-horizon (5/60) 变体，性能略好但仍 incr_ic 负
- **MT 预算**：首批 3 候选，direction bucket low

## Thread 进展

> [!note]+ T001 [[directions/liquidity_acceleration#T001]] — `[◉ ACTIVE]`
> C001 amount 5d/60d reserve mono=-1.00；保留待 library 重组。

> [!note]+ T002 [[directions/liquidity_acceleration#T002]] — `[◉ ACTIVE]`
> C003 turnover 5d/60d reserve mono=-1.00；C002 normalized 与 batch_004 C003 同源。

## 方向级反思

batch_023 是 liquidity_acceleration **首批**：admit=0 reserve=2 reject=1。

- **正面**：流动性加速度信号 rank-order 极强（mono=-1.00 双候选），CP02-CP03 admit-quality
- **负面**：与 F001 同向冲突（incr_ic 全负），admit 会稀释 F001
- **decisions**：reserve C001/C003 不 admit；direction status `exploring` 维持，不转 dead

**Calibration**：
- 错杀 flag = 0 ✓（reserve 候选 max_lib_corr<0.30 但 incr_ic 负，不满足 4 条件）
- 累计 reserve 全库已 4-5 个 (batch_004 C003 + batch_009 C003/C007 + 本批 C001/C003 + 历史) — 接近 30%-40% 阈值
- **不触发 calibration**（reserve 都因相同库 reducer 模式，非系统过严）

**下批决策**：流动性加速度方向首批结果与历史 reserve pattern 一致——**reserve pattern 不可 admit 是结构性约束**：A 股 liquidity 加速度信号与 amount CV 在 cross-section 同向。
