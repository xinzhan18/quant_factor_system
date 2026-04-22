---
batch_id: batch_024
direction: vol_shock_signals
judged_at: 2026-04-21T06:15:00Z
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

# batch_024 Judge Summary

> [!abstract]+ batch_024 · [[directions/vol_shock_signals]] · 3 candidates (direction 首批)
> ❌ **admit=0** · ❌ **reject=3**
> **核心发现**: vol shock 信号 3/3 失败——C001 库 reducer (incr_ic=-0.027) + C002 hard_gate mono_sign_flip + C003 **alpha_surv=0.117 catastrophic 第 4 次出现 vol-derived 签名**。Direction 首批即 **dead**。
> **MT Budget**: cumulative 116 → **119** · direction 0 → **3** · bucket `low`

## 候选一览

| ID | Verdict | Key | 反思 | Detail |
|---|---|---|---|---|
| C001 | ❌ reject | today/20d range ratio, incr=-0.027 | library reducer | [[batches/batch_024/candidates/C001]] |
| C002 | ❌ reject | 5d/60d vol ratio hard_gate | mono_sign_flip IS=+0.70→OOS=-1.00 | [[batches/batch_024/candidates/C002]] |
| C003 | ❌ reject | Abs return shock, a_surv=0.117 | catastrophic — classical vol_20d signature | [[batches/batch_024/candidates/C003]] |

## 跨候选对比

- **vol_20d-derived 第 4 次出现**：C003 alpha_surv=0.117 与 batch_016 C004 (Q90-Q10 a_surv=0.008) + batch_017 C004 (close/high a_surv=0.003) + batch_018 C005 (|gap|/range a_surv=0.164) 同源。**任何 vol magnitude-based 信号在 cross-section 都 collapse to vol_20d**，无论如何 normalize
- **mono_sign_flip trap**: C002 5d/60d vol ratio IS/OOS 完全反转，证明短窗/长窗比值不是稳定信号
- **MT 预算**：首批 3 候选，direction bucket low

## Thread 进展

> [!failure]+ T001 [[directions/vol_shock_signals#T001]] — `[✗ DISPROVEN batch_024]`
> 今日 range/baseline + abs return shock 都失败：前者 library reducer，后者 a_surv catastrophic (vol 衍生)

> [!failure]+ T002 [[directions/vol_shock_signals#T002]] — `[✗ DISPROVEN batch_024]`
> 5d/60d vol ratio hard_gate mono_sign_flip

## 方向级反思

vol_shock_signals 首批 0 admit + 全 thread DISPROVEN → **direction status: exploring → dead**。

**元教训（第 4 次观察）**：**abs/magnitude-based vol signals 在 A 股 csi1000 cross-section 全部 collapse 到 vol_20d**。这条规律已在 4 个方向独立观察过 (batch_016 return_distribution_signals, batch_017/018 ohlc_temporal_aggregation magnitude probes, batch_024 vol_shock_signals)。后续 direction 设计应**绝对避开 magnitude-only vol signals**。

**Calibration**：不触发。

**下批决策**：vol_shock_signals dead。
