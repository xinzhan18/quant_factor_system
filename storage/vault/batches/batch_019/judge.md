---
batch_id: batch_019
direction: ohlc_temporal_aggregation
judged_at: 2026-04-21T03:10:00Z
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
mt_bucket: medium
---

# batch_019 Judge Summary

> [!abstract]+ batch_019 · [[directions/ohlc_temporal_aggregation]] · 4 candidates
> ❌ **admit=0** · ⏸ **reserve=0** · ❌ **reject=4**
> **核心发现**: 5d OHLC aggregation 在 F006 (close 端) + F007 (open 端) 之外**剩余维度无独立 alpha**。Range 演化 (C001) rank 噪声大；流动性调整 range (C002) corr=0.746@F002；volume-weighted body (C003) corr=0.721@F007；离散 count (C004) hard_gate sign_flip。**方向接近 saturated**——5d 窗口的 directional ratio 空间被 F006/F007 饱和。
> **MT Budget**: cumulative 97 → **101** · direction 10 → **14** · bucket `medium`

## 候选一览

| ID | Verdict | 档位 | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🟢·🔴·🟢·🟡·🟡 | ls_t=-0.89 mono=-0.30 | range expansion ratio rank 噪声大；Barra-clean 但 IC 不真 | [[batches/batch_019/candidates/C001]] |
| C002 | ❌ reject | 🟡·🟡·🔴·🔴·🟡 | corr=0.746@F002 r²=0.348 | range/amount → amount 主导，与 F002 高度重叠 | [[batches/batch_019/candidates/C002]] |
| C003 | ❌ reject | 🟡·🟢·🟡·🔴·🟡 | corr=0.721@F007 incr=-0.039 | volume-weighted body → F007 mirror，无独立信息 | [[batches/batch_019/candidates/C003]] |
| C004 | ❌ reject | hard_gate | sign_flip 异号 | 二值化丢失 magnitude → IS/OOS 不一致 | [[batches/batch_019/candidates/C004]] |

## 跨候选对比

- **5d 直接维度饱和**：F006/F007 已覆盖 close-end 与 open-end signed ratio；本批所有候选要么 noise 要么 redundant：
  - C001 (range 演化) → 信号噪声压垮（mono=-0.30）
  - C002 (流动性 range) → 落入 F002 amount-dominated cluster
  - C003 (volume × body) → 落入 F007 open-position cluster (corr 0.721)
  - C004 (discrete count) → sign_flip 暴露离散化损失
- **discretization 失败**：C004 (>0.9 阈值) sign_flip 表明 5d 内 binary 0/1 count 不能保留 magnitude 必要的信号——continuous Mean(ratio) (F006/F007) 是正确形式。
- **库容量约束**：corr=0.746/0.721 与现有 F002/F007 高重叠——OHLC 5d aggregation 空间在加入 F006/F007 后**库容量已接近饱和**。

## Thread 进展

> [!note]- T002 [[directions/ohlc_temporal_aggregation#T002]] — `[◉ ACTIVE]`（本批 C004 试 discrete count 但 sign_flip）
> sign-of-body frequency 的 binary count 形式失败；连续形式 (C003 batch_017 reserve) 仍 active 但与新 admits F007 关系待复核。

> [!note]- T003 [[directions/ohlc_temporal_aggregation#T003]] — `[✓ ANSWERED batch_017+018]`（本批 C001/C002/C003 全 reject 进一步收紧）
> 5d directional ratio 空间被 F006+F007 饱和；剩余 ratio 形式 (range expansion / volume-weighted) 全部 redundant 或 noisy。

## 方向级反思

batch_019 是 ohlc_temporal_aggregation **第三轮 0 admit**。结合 batch_017/018 累积 9 candidates → 2 admit (F006/F007)，本批 4 候选全 reject = **方向 admit 率从 22%→15%**。

**饱和判断**：
- 已成功探明 2 个独立维度（close-end F006 + open-end F007）
- 本批 4 候选探完剩余主要 ratio 维度（range / volume-weighted / discrete）
- 库 corr 已开始与新 admits 重叠（C002 0.746@F002, C003 0.721@F007）
- 唯一未饱和路径：3d/10d 窗口 ablation（但与 5d 窗口 expected near-dup）；跨日 pattern (engulfing, inside bars) — 复杂度高、信号弱
- **结论**：方向**接近 saturated** 但未到 fully saturated。决策：再 1 轮试跨日 pattern + window ablation；若再 0 admit 转 saturated。

**Calibration**：
- 错杀 flag = 0 ✓
- 累计 9 candidates / 2 admits + 1 reserve / 6 reject = admit 率 22%（高于 calibration 阈值）
- Reserve 积压：cumulative 101 / 累计 reserve ~14 = 14% < 40% ✓
- 不触发任何 calibration

**下批决策（batch_020）**：
1. 跨日 pattern：3d 内 high 上升趋势 + 5d body sign 一致性
2. window ablation：3d/10d upper-shadow 是否 near-dup F006（确认 5d 是 sweet spot）
3. 同时**准备方向 saturated 转换**：若 batch_020 仍 0 admit → status productive → saturated
