---
batch_id: batch_028
direction: asymmetric_momentum
judged_at: 2026-04-21T06:55:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
batch_summary: {total: 3, admit: 0, reserve: 0, reject: 3}
---

# batch_028 Judge Summary

> [!abstract]+ batch_028 · [[directions/asymmetric_momentum]] · 3 candidates (direction 首批)
> ❌ **admit=0** · ❌ **reject=3** (全 hard_gate)
> **核心发现**: up/down momentum 分解 **全 IS/OOS sign/mono 反转**——IS 有效的方向在 OOS 完全反转，证明 loss aversion 信号在 A 股市场 **regime-dependent**，不构成稳定 cross-section alpha。Direction 首批 dead。
> **MT Budget**: cumulative 128 → **131** · direction 0 → **3** · bucket `low`

## 候选一览

| ID | Verdict | Key | Detail |
|---|---|---|---|
| C001 | ❌ reject | 5d down-only, sign_flip train-0.004/val+0.017 | [[batches/batch_028/candidates/C001]] |
| C002 | ❌ reject | 5d up-only, mono_sign_flip IS+0.70/OOS-0.60 | [[batches/batch_028/candidates/C002]] |
| C003 | ❌ reject | abs(down)/up ratio, mono_sign_flip IS-0.70/OOS+0.60 | [[batches/batch_028/candidates/C003]] |

## 方向级反思

direction status `exploring → dead` — 3/3 hard_gate + 三个不同角度都 IS/OOS 反转，loss aversion / disposition effect 信号在该 universe 不稳定。

**元教训**：conditional aggregation (up-only, down-only) 引入 regime-dependence——不同市场状态下 up/down 的预测力完全反转。aggregate 不作条件分离稳定性更好（F010 mean overnight return 整库最强，ls_t=7.50）。
