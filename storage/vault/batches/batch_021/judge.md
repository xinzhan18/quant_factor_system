---
batch_id: batch_021
direction: ohlc_temporal_aggregation
judged_at: 2026-04-21T03:55:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reserve}
  - {candidate_id: C003, verdict: reject}
batch_summary: {total: 3, admit: 0, reserve: 1, reject: 2}
---

# batch_021 Judge Summary

> [!abstract]+ batch_021 · [[directions/ohlc_temporal_aggregation]] · 3 candidates
> ❌ **admit=0** · ⏸ **reserve=1** (C002 7d upper-shadow) · ❌ **reject=2**
> **核心发现**: F007 (5d open-position) 不像 F006 那样有 3d phase variant —— C001 3d open-position **mono_sign_flip 完全反转** (IS=-1.00 OOS=+0.90)。**open-position 信号是 5d-only stability**。C002 7d upper-shadow alpha_surv=1.685 极 clean 但 corr=0.834@F006 太 high 转 reserve（库 bloat）。C003 turnover-weighted body 是 F007 noisy 版本。
> **MT Budget**: cumulative 106 → **109** · direction 19 → **22** · bucket `high`

## 候选一览

| ID | Verdict | 档位 | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | mono_sign_flip IS=-1.00 OOS=+0.90 | 3d open-position rank 完全反转 — F007 是 5d-only | [[batches/batch_021/candidates/C001]] |
| C002 | ⏸ reserve | 🟢·🟡·🟢·🔴·🟢 | ic=+0.017 ls_t=2.33 mono=+0.90 alpha_surv=1.685 corr=0.834@F006 incr=+0.014 | 7d upper-shadow Barra clean 但库 bloat 风险 | [[batches/batch_021/candidates/C002]] |
| C003 | ❌ reject | 🟡·🟡·🟢·🔴·🟡 | mono=-0.30 corr=0.579@F007 incr=-0.032 | turnover-weighted body 是 F007 noisy 版本 | [[batches/batch_021/candidates/C003]] |

## 跨候选对比

- **F007 与 F006 window-stability 不对称**：F006 (5d) 有 F008 (3d) 稳定 phase variant，但 F007 (5d) 在 3d 窗口完全反转 (C001 mono IS=-1.00 / OOS=+0.90)。**open-position 是 single-window 信号；upper-shadow 是 multi-window 信号**——后者机制更稳。
- **库 bloat boundary 测试 (C002)**：alpha_surv=1.685 是整 OHLC family 最 clean，但 max_corr=0.834@F006 + 已有 F008 同 family，admit 后会在 10 因子库占 30% upper-shadow signals。Reserve 是库质量 vs 边际增量的权衡——rubric 形式允许 admit，practice 倾向 reserve。
- **turnover weighting 失败 (C003)**：turnover × body sign → corr 0.579@F007 + incr_ic=-0.032。turnover 与 F007 (open-position) 在 cross-section 上重叠——**turnover 不是新独立 axis**。

## Thread 进展

> [!note]+ T003 [[directions/ohlc_temporal_aggregation#T003]] — `[◉ ACTIVE]`
> 7d upper-shadow reserve；3d open-position 失败——open-position 是 5d-only 信号。

> [!failure]+ T002 [[directions/ohlc_temporal_aggregation#T002]] — `[✗ DISPROVEN batch_020/021]`
> turnover-weighted body sign (C003) corr 0.579@F007 + incr negative → T002 sign-frequency family 全面失败。

## 方向级反思

ohlc_temporal_aggregation **第 5 batch — admit=0 / reserve=1**。方向饱和明显：

- 累计 5 batches，22 候选 → 3 admit (F006/F007/F008) + 2 reserve + 17 reject = admit 率 14%（从 25% 降到 14%）
- 剩余 OHLC ratio 维度高度互相重叠
- C002 reserve 是 library bloat case，不是新维度

**Direction 操作**：
- status `productive → saturated`（admit 率持续下降 + 候选与现库 corr 普遍 > 0.5）
- priority `high → medium`
- F006/F007/F008 三 admit 已充分覆盖核心机制；后续探索 ROI 显著下降

**Calibration**：
- 错杀 flag = 0 ✓
- admit 率仍 14% > 0 ✓
- 不触发 calibration

**下批决策（batch_022）**：
1. **关键**：rounds_since_last_consolidation=10 → 触发 Phase 5 /factor-consolidate（先 consolidate 再开新 batch）
2. consolidation 后开新方向 — 候选：calendar_effects (day-of-week/month-end) / lib_factor_combinations (F006-F007 spread)
3. ohlc_temporal_aggregation 转 saturated，不再分配 batches
