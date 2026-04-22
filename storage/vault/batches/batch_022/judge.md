---
batch_id: batch_022
direction: fundamental_momentum
judged_at: 2026-04-21T04:10:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
batch_summary: {total: 4, admit: 0, reserve: 0, reject: 4}
admit_count: 0
reject_count: 4
reserve_count: 0
candidate_count: 4
mt_bucket: low
---

# batch_022 Judge Summary

> [!abstract]+ batch_022 · [[directions/fundamental_momentum]] · 4 candidates (direction 首批)
> ❌ **admit=0** · ❌ **reject=4**
> **核心发现**: PE/PB/PS 变化率作为 cross-section 信号**全部弱**——4/4 ls_t<2 + mono≤-0.70 + 全 library reducer (incr_ic 全负)。Rank-based variant (C003) 改善 mono 但仍 weak。**fundamental rate hypothesis 直接证伪**。
> **MT Budget**: cumulative 109 → **113** · direction 0 → **4** · bucket `low`

## 候选一览

| ID | Verdict | Key | 反思 | Detail |
|---|---|---|---|---|
| C001 | ❌ reject | PE rate 20d, ls_t=-1.22 r²=0.512 | hypothesis 弱 | [[batches/batch_022/candidates/C001]] |
| C002 | ❌ reject | PB rate 20d, ls_t=-1.49 **r²=0.811** | PB rate 几乎完全 vol_20d 衍生 | [[batches/batch_022/candidates/C002]] |
| C003 | ❌ reject | PE rank trend, ls_t=-1.81 mono=-0.70 | rank-based 改善但仍弱 | [[batches/batch_022/candidates/C003]] |
| C004 | ❌ reject | Composite PE+PB+PS rate, ls_t=-1.27 | 等权聚合不救弱信号 | [[batches/batch_022/candidates/C004]] |

## 跨候选对比

- **fundamental rates 弱信号一致性**：4/4 ls_t ∈ [-1.81, -1.22]，全部 < 2。**变化率信息已被市场快速消化**——A 股市场对 PE/PB/PS 修订 reaction 快，drift 不足 5d
- **rank-based vs absolute**：C003 (rank trend) mono=-0.70 vs C001 (absolute rate) mono=-0.30 — rank 形式更稳但 ls_t 没显著提升
- **library reducer pattern**：4/4 incr_ic 负，与 F006/F007 (positive intraday signals) 反向——基本面变化率与 intraday flow 信号在 cross-section 互相对消
- **MT budget**：首批 4 候选，direction bucket low

## Thread 进展

> [!failure]+ T001 [[directions/fundamental_momentum#T001]] — `[✗ DISPROVEN batch_022]` PE rate
> C001 + C003 双 reject → PE rate 不携独立 alpha (ls_t<2)

> [!failure]+ T002 [[directions/fundamental_momentum#T002]] — `[✗ DISPROVEN batch_022]` PB/PS rate
> C002 r²=0.811 catastrophic — PB rate 几乎完全 Barra-derived

> [!failure]+ T003 [[directions/fundamental_momentum#T003]] — `[✗ DISPROVEN batch_022]` 综合 rate
> C004 等权聚合不救弱信号

## 方向级反思

batch_022 是 fundamental_momentum **首批 0 admit + 全 thread DISPROVEN**。

**Direction 操作**：status `exploring → dead`（首批彻底证伪 hypothesis）。priority `medium → low`。

**核心元教训**：A 股 csi1000 universe 上的 fundamental ratio rates (PE/PB/PS Δ/level) 不构成独立 alpha——市场对 fundamental 修订 reaction 速度可能快于 20d aggregation 能 capture 的水平。如果要做 fundamental signal，需要：
1. 更短窗口 (5d-10d) — 但短窗噪声大
2. 更长窗口 (60d+) — 检查是否已 priced
3. **绝对水平** (不是 rate) — F002 (PB/amount) 已成功，证明绝对水平可用

**Calibration**：不触发任何 trigger（admit 率仍可观；非系统性错杀）。

**下批决策（batch_023）**：fundamental_momentum dead，开新方向或 retire。考虑：
1. **lib_factor_combinations** — F006 - F007 spread / F006 × F002
2. **liquidity_term_structure** — 不同窗口 amount/turnover 比较
3. **暂停 mining** — context 紧，已成功扩库 8→10 (待 F008 后续)
