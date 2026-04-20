---
batch_id: batch_025
direction: overnight_intraday_split
judged_at: 2026-04-21T06:25:00Z
candidates:
  - {candidate_id: C001, verdict: admit, factor_name: overnight_intraday_spread_5d}
  - {candidate_id: C002, verdict: admit, factor_name: overnight_return_persistence_5d}
  - {candidate_id: C003, verdict: reject}
batch_summary: {total: 3, admit: 2, reserve: 0, reject: 1}
---

# batch_025 Judge Summary

> [!abstract]+ batch_025 · [[directions/overnight_intraday_split]] · 3 candidates (direction 首批)
> ✅ **admit=2** (C001 overnight_intraday_spread_5d, C002 overnight_return_persistence_5d) · ❌ **reject=1** (C003 corr sign_flip)
> **核心发现**: **首批 DOUBLE ADMIT**——overnight/intraday 分解是全新 cross-section 维度。C002 ls_t=7.50 是整库最强之一；C001 incr_ic=+0.044 是库增值最强候选之一 (4× F007 的 0.023)。
> **MT Budget**: cumulative 119 → **122** · direction 0 → **3** · bucket `low`

## 候选一览

| ID | Verdict | 档位 | Key | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ✅ **admit** | 🟢·🟢·🟢·🔴·🟢 | ic=+0.047 ls_t=5.18 mono=+1.00 corr=0.708@F007 incr=+0.044 | overnight-intraday spread 强机构 vs 散户信号 | [[batches/batch_025/candidates/C001]] · [[factors/F009]] |
| C002 | ✅ **admit** | 🟢·🟢·🟢·🟡·🟢 | ic=+0.024 ls_t=7.50 mono=+1.00 corr=0.424@F003 incr=+0.019 | 5d overnight return persistence — ls_t 整库最强 | [[batches/batch_025/candidates/C002]] · [[factors/F010]] |
| C003 | ❌ reject | hard_gate | sign_flip 20d corr | overnight-intraday correlation 跨期不稳 | [[batches/batch_025/candidates/C003]] |

## 跨候选对比

- **方向 hypothesis 完整验证**：C001 spread + C002 pure overnight 双 admit，证明 overnight 段在 cross-section 上**独立于 intraday 信号**——aggregation 形式 (mean) 有效，correlation 形式 (C003) 失败。
- **Library 双新增**：batch_025 是**本 session 第二个 double-admit batch** (前为 batch_018 中的单 admit F007)。F006/F007/F008 已建立 OHLC 基础；F009 (spread) + F010 (overnight mean) 扩展到 overnight-intraday 分解维度。
- **ls_t=7.50 整库最强**：C002 超过 F007 (3.22) + F006 (3.20)。5d overnight aggregation 是非常稳定的信号。
- **MT 预算**：direction 3, cumulative 122。

## Thread 进展

> [!success]+ T001 [[directions/overnight_intraday_split#T001]] — `[✓ ANSWERED batch_025]`
> overnight/intraday spread (C001) + pure overnight (C002) 双 admit — 方向 hypothesis 完整验证。

> [!failure]+ T003 [[directions/overnight_intraday_split#T003]] — `[✗ DISPROVEN batch_025]`
> 20d overnight-intraday corr hard_gate sign_flip — correlation 形式失败，但 mean aggregation 成功。

## 方向级反思

batch_025 **首批 double admit** → direction status `exploring → productive`！admit 率 2/3 = 67% 是所有首批最高。

**核心发现**：A 股 overnight 段携带独立于 intraday 的持久性信号。机构 pre-market 决策 + 隔夜信息吸收 + 开盘集中执行 → overnight return 比 intraday return 更"稳定 + 持久"。

**Calibration**：不触发 (positive outcome)。

**下批决策（batch_026）**：
1. 同方向 deepen — 3d/10d overnight aggregation；overnight × intraday 乘积；overnight 符号频率
2. 预计方向剩余容量 2-3 admit（分解维度新）
