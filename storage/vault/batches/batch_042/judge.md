---
batch_id: batch_042
direction: vwap_proxy_signals
judged_at: 2026-04-24T01:45:00Z
candidates:
  - {candidate_id: C001, verdict: reserve}
  - {candidate_id: C002, verdict: reserve}
  - {candidate_id: C003, verdict: reserve}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 3, reject: 3}
admit_count: 0
reject_count: 3
reserve_count: 3
candidate_count: 6
mt_bucket: high
---

# batch_042 Judge Summary

> [!abstract]+ batch_042 · [[directions/vwap_proxy_signals]] · 6 candidates
> ❌ **reject=3** (C004/C005/C006) · ⏸ **reserve=3** (C001/C002/C003) · ✅ **admit=0**
> **核心发现**: HLC 位置锚点 (C001/C002) IC 强但 **max_corr@F014=0.887** ——VWAP-HLC-位置 在 A 股 10% 涨跌幅约束下与 VWAP-prev_close 尺度高度重合，未真正解耦；C001 与 C002 是仿射等价（metrics 到六位小数一致）。T003 五类锚点中只剩"orthogonalize by F014/vol_20d" 路径尚未尝试。
> **MT Budget**: cumulative 210 → **216** · direction 6 → **12** · bucket `high`（封顶，search_adjusted 推回 `medium`）· 本批 low=1 / med=5 / high=0

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ⏸ reserve | 🟠·🟠·🟠·🔴·🟢 | IC=0.032 ls_t=2.72 mono 0.6→0.7 **max_corr=0.887@F014** cum_mdd=-2.04 | VWAP-HLC 位置—IC 独立 ✓ 但统计空间与 F014 79% 重叠；等 orthogonalize 路径 | [[batches/batch_042/candidates/C001]] |
| C002 | ⏸ reserve | 🟠·🟠·🟠·🔴·🟢 | 同 C001（affine：C002 = C001 - 0.5） | **与 C001 仿射等价**，rank-order 恒等；不独立 | [[batches/batch_042/candidates/C002]] |
| C003 | ⏸ reserve | 🟠·🔴·🟠·🔴·🔴 | IC=0.009 ls_t=-0.67 sign/IC 反转 zero_ratio=0.857 | Sign+5d agg 把 85.7% 压零 → 边际丢失；F014 锚点 signed 通道已饱和 | [[batches/batch_042/candidates/C003]] |
| C004 | ❌ reject | 🟠·🔴·🔴·🟡·🟠 | mono 0.9→**-0.3** (flip), Q inverse-U, style_r²=0.68, cum_mdd=-73 | VWAP 20d 均值回归锚点失败，IC 来自截面尾部非稳健梯度 | [[batches/batch_042/candidates/C004]] |
| C005 | ❌ reject | 🟠·🔴·🟢·🟡·🟠 | mono -0.8→-0.3 decay, ls_t=-1.53, cum_mdd=-70, edge 近 3 年衰减 | Sign × Sign AND-gate 丢 magnitude + 历史失效严重 | [[batches/batch_042/candidates/C005]] |
| C006 | ❌ reject | 🟠·🔴·🔴·🔴·🟢 | ls_t=0.96, alpha_surv=0.29 poor, mono_is=0.10 一桨, max_corr=0.894@F014 | C001 5d agg——均值化反丢 CP04 alpha_surv | [[batches/batch_042/candidates/C006]] |

## 跨候选对比

- **Affine equivalence 识破**：C001 `(VWAP-L)/(H-L)` 与 C002 `(VWAP-(H+L)/2)/(H-L)` = C001 - 0.5，rank-order 恒等。metrics（IC/ICIR/ls_t/mono/max_corr/incr_ic）六位小数级一致——**物理上是同一个信号**。未来设计规避：凡同分母仿射移位，freeze 前做 DSL canonical 去重。
- **F014 吸引 cluster**：C001/C002/C003/C006 四个 VWAP-锚点候选 max_corr@F014 ∈ [0.79, 0.89]——10% 涨跌幅约束 + 日成交密度使得 HLC 范围与 prev_close 尺度强相关；**"同分母不同分子的 VWAP spread" 几乎全部落到 F014 统计空间**。真正独立于 F014 的只有 C004（VWAP 自相关 mean-reverting）和 C005（sign × sign）——但二者都因机制其它缺陷 reject。
- **Style cluster**：6/6 候选 dominant_style=`vol_20d`（exposure 7.5–22.3）；3/6 style_r²>0.25（C001/C002/C006 poor）。与 batch_041 stochastic_position 同样被 vol_20d 吞噬——升级为**跨两方向交叉验证**的结构吸收律。
- **MT 预算推进**：direction_candidates 6 → 12；mt_bucket 推至 `high` 上界，search_adjusted 压回 `medium` 强制封顶（本批所有 CP03 档位 ≤ borderline 即此所致）。
- **sign consistency 全 1**：C001/C002/C004/C005/C006 全 sign_consistent=1.0，说明机制方向稳健——问题在 rank-order + style 吞噬，不在方向漂移。

## Thread 进展

> [!note]+ T001 [[directions/vwap_proxy_signals#T001]] — `[✓ ANSWERED batch_040]`（本批无推进）

> [!note]+ T002 [[directions/vwap_proxy_signals#T002]] — `[✗ DISPROVEN batch_040]`（本批无推进）

> [!note]+ T003 [[directions/vwap_proxy_signals#T003]] — `[◉ ACTIVE → 部分 DISPROVEN]`
> 5 类锚点中 4 类证伪/重复：
> - **HLC 位置**（C001/C002/C006）：IC 独立但 stat-space 与 F014 重合 0.79–0.89，不真正解耦——⚠️ DISPROVEN（同 T002 结构吸收）
> - **Signed 持久性**（C003）：Sign+5d agg 丢 magnitude + F014 已覆盖该锚——⚠️ DISPROVEN
> - **VWAP 均值回归**（C004）：mono_flip + style_r²=0.68 吞噬——⚠️ DISPROVEN
> - **方向一致性**（C005）：sign×sign 丢 magnitude + cum_ic_mdd=-70——⚠️ DISPROVEN
>
> 仅剩**未验证的第 5 子路径**："orthogonalize by F014 / vol_20d 后的 VWAP 残差" ——但需工具链支持（barra_residual_signal 或 orthogonalize 算子），短期阻塞。

## 方向级反思

本方向**第二批即撞到"VWAP 锚点的结构耦合墙"**：
- F014 占据的"跨 session VWAP gap"统计空间非常强势（max_corr 0.89 吸引 4 个候选）——即使是机制上独立的 HLC 位置/mean-reverting 形式都被实证打回同一簇
- 结构耦合根源：**A 股 10% 涨跌幅约束** 使得 daily HLC range 与 prev_close 尺度强相关；任何"VWAP 相对日内锚"的形式都隐含"VWAP 相对 prev_close"的信息
- 与 [[directions/stochastic_position]] batch_041 结论对偶：price-position 指标族（跨日 rolling 或日内 HLC）在 csi1000 都被 vol_20d / 已有 VWAP 信号吸收

**ROI 评估**：direction 2 rounds / 12 candidates / 1 admit (F014) / 6 reserve。首批 17% admit 率来自 T001 ANSWERED；第二批 0% 来自 T003 四子路径同时失败。

- **状态**：`status: productive` 保持（仅 2 rounds，不足以判 saturated；下一 round 若仍 0 admit 则转 saturated）
- **priority**：`medium → low`（T003 剩余路径阻塞于工具链）
- **下一步**：
  1. 方向短期挂起，等 vol_20d orthogonalize 工具链；C001 可在工具到位后作为 residual 种子
  2. 本轮教训升格 lessons：A 股 10% 涨跌幅约束导致 HLC range 与 prev_close 共动，"daily-anchor VWAP" 无法独立于"cross-session VWAP"

**阈值校准侦测**: 无触发（last-3-batch admit 累计 = 1，非 0 连 3；reserve 积压 3/6=50% 但无零-admit 累计条件；无 over-rejection flag；无悖论组合）。

**库空间独立性安全阈判断**：C001 是本批最强候选，但 max_corr=0.887 远超"错杀 safeguard"的 `max_lib_corr<0.30` 条件，且 F014 与 C001 同方向（正相关），非互补——reserve 合理，不走校准流程。
