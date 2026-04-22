---
batch_id: batch_020
direction: ohlc_temporal_aggregation
judged_at: 2026-04-21T03:35:00Z
candidates:
  - {candidate_id: C001, verdict: admit, factor_name: upper_shadow_persistence_3d}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
batch_summary: {total: 5, admit: 1, reserve: 0, reject: 4}
admit_count: 1
reject_count: 4
reserve_count: 0
candidate_count: 5
mt_bucket: high
---

# batch_020 Judge Summary

> [!abstract]+ batch_020 · [[directions/ohlc_temporal_aggregation]] · 5 candidates
> ✅ **admit=1** (C001 → upper_shadow_persistence_3d) · ⏸ **reserve=0** · ❌ **reject=4** (C002 C003 C004 C005)
> **核心发现**: **F006 window ablation 找到 3d phase variant**——C001 (3d upper-shadow) ic=+0.029 ls_t=2.91 mono=+0.90 alpha_surv=1.268 incr_ic=+0.022 admit；max_corr=0.758@F006 high 但 incr_ic 显示真实库增值。10d 窗口 (C002) mono_sign_flip 反转——**确认 3d-5d 是 sweet spot 区间**。Cross-day signs (C003/C004) 和 Donchian (C005) 全 reject——20d 范围信号失败。
> **MT Budget**: cumulative 101 → **106** · direction 14 → **19** · bucket `high`（接近 saturated 但未到）

## 候选一览

| ID | Verdict | 档位 | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ✅ **admit** | 🟢·🟢·🟢·🔴·🟢 | ic=+0.029 ls_t=2.91 mono=+0.90 corr=0.758@F006 incr=+0.022 | 3d upper-shadow F006 ablation：phase variant 携独立增量 | [[batches/batch_020/candidates/C001]] · [[factors/F008]] |
| C002 | ❌ reject | hard_gate | mono_sign_flip IS=-0.60 OOS=+0.90 | 10d 窗口 rank 反转，跨过 phase 阈值 | [[batches/batch_020/candidates/C002]] |
| C003 | ❌ reject | hard_gate | sign_flip 跨日 sign agreement | engulfing-like 信号 IS/OOS 不稳 | [[batches/batch_020/candidates/C003]] |
| C004 | ❌ reject | hard_gate | sign_flip gap-up freq | discretization 5d 不稳 (与 batch_019 C004 同源) | [[batches/batch_020/candidates/C004]] |
| C005 | ❌ reject | 🟡·🔴·🔴·🟡·🟡 | ls_t=1.09 r²=0.477 corr=0.459@F007 | 20d Donchian — vol-derived + 与 F007 部分重叠 | [[batches/batch_020/candidates/C005]] |

## 跨候选对比

- **F006 window ablation 关键发现**：3d (C001 admit) → 5d (F006 admit) → 10d (C002 reject mono_flip)。**5d 是上界**。3d 之下未测但应该相似 phase variant。
- **库 corr 0.758 admit 的判决先例**：C001 突破 0.30 low 阈值进入 high (0.70-0.90) 区间但 incr_ic=+0.022 > 0.005，rubric 允许 admit。**这是 high-corr admit 的首例**——需监控后续是否成为标准路径。
- **5d 跨日 patterns 全失败**：C002 (10d window flip) + C003 (cross-day sign agreement) + C004 (gap-up freq) 全 hard_gate。**multi-bar 复杂 patterns 在 5d/10d 窗口下不稳定**——简单 mean(ratio) 是有效形式，复杂 sign-product/threshold-count 不是。
- **MT 预算**：direction 19 (high bucket 接近 saturated)，cumulative 106。

## Thread 进展

> [!success]+ T003 [[directions/ohlc_temporal_aggregation#T003]] — `[◉ ACTIVE]`（已 ANSWERED + 持续探索）
> 3d upper-shadow (C001) **admit** — F006 ablation 成功；window range [3d, 5d] 都有效，10d 反转。

> [!failure]+ T002 [[directions/ohlc_temporal_aggregation#T002]] — `[✗ DISPROVEN batch_020]` 跨日 sign patterns
> C003/C004 双 sign_flip 进一步证伪 sign-frequency 路径——本批最终关闭 T002。

## 方向级反思

batch_020 是 ohlc_temporal_aggregation **第 3 个 admit** (F006 + F007 + C001/F008)。方向 admit 率 3/14 = 21% 维持强势。

**方向阶段总结（4 batches）**：
- F006 (5d upper-shadow 收盘抛压) + F007 (5d open-position 开盘买盘) + F008 (3d upper-shadow 短期 phase variant)
- F006/F007 机制正交 (max_corr=0.276)；F008/F006 同机制 windows variant (max_corr=0.758)
- magnitude-only 路径全失败；discrete count 路径全 sign_flip；20d 窗口 sign reversal
- **5d 窗口是 sweet spot；3d 是 phase variant 补充；10d 失败**

**饱和判断**：
- 已探明 close-end + open-end + window variant 三个 admit
- batch_019/020 各 1 admit + 大量 reject 表明剩余空间狭窄
- direction 19 候选已进入 mt_bucket high
- 后续 admit 概率显著下降，但 ROI 仍正

**Calibration**：
- 错杀 flag = 0 ✓
- admit 率 21% 持续，无连续零 admit ✓
- 不触发 calibration

**下批决策（batch_021）**：
1. 同方向最后一探：3d open-position 镜像 (F007 ablation)、3d body magnitude
2. 若 0 admit → status `productive → saturated`
3. 准备开新方向（calendar effects / lib factor combinations）
