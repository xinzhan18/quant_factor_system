---
batch_id: batch_029
direction: return_momentum_acceleration
judged_at: 2026-04-21T07:05:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
batch_summary: {total: 3, admit: 0, reserve: 0, reject: 3}
admit_count: 0
reject_count: 3
reserve_count: 0
candidate_count: 3
mt_bucket: low
---

# batch_029 Judge Summary

> [!abstract]+ batch_029 · [[directions/return_momentum_acceleration]] · 3 candidates (direction 首批)
> ❌ **admit=0** · ❌ **reject=3**
> **核心发现**: return momentum 变化率 3/3 ls_t<1 (C001=-0.81, C003=-0.49) 或 mono_sign_flip (C002)。**price return rate 与 fundamental rate 同源失败**——rate 形式不携稳定 alpha。
> **MT Budget**: cumulative 131 → **134** · direction 0 → **3** · bucket `low`

## 候选一览

| ID | Verdict | Key | Detail |
|---|---|---|---|
| C001 | ❌ reject | 5d-20d spread ls_t=-0.81 | [[batches/batch_029/candidates/C001]] |
| C002 | ❌ reject | 5d/20d ratio mono_sign_flip | [[batches/batch_029/candidates/C002]] |
| C003 | ❌ reject | Δ5d of 5d mean ls_t=-0.49 | [[batches/batch_029/candidates/C003]] |

## 方向级反思

direction `exploring → dead` — 与 fundamental_momentum 失败原理相同：**rate/delta 形式对信号稳定性不利**，而 level/mean 形式保留更多可用结构（F010 vs C001 对比：F010 ls_t=7.50；C001 ls_t=-0.81）。

**元教训固化**：第 5 次观察 **rate/delta form 失败** 模式（前有 fundamental_momentum / return_distribution / liquidity_acceleration ratio / asymmetric_momentum ratio / 本 batch）。**一阶/二阶 rate-of-change 在 A 股 csi1000 cross-section 不携稳定 alpha**。
