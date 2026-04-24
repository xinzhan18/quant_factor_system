---
batch_id: batch_037
direction: trend_quality_gated
judged_at: 2026-04-24T02:10:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reserve}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 1, reject: 5}
admit_count: 0
reserve_count: 1
reject_count: 5
candidate_count: 6
mt_bucket: medium
---

# batch_037 Judge Summary

> [!abstract]+ [[directions/trend_quality_gated]] · 6 candidates
> ❌ **admit=0** · ⏸ **reserve=1** (C002) · ❌ **reject=5**
> **核心发现**: Direction hypothesis **完全反向证伪**——paper Channel 3 预测 gated momentum 在 csi1000 复活成 trend continuation（Rank IC +0.05），实测全部 6 候选 IC_OOS 在 -0.025 至 -0.033 区间，mono 全负，9 年 IC 全负，**signal 实质是 reversal 而非 trend**。所有 candidates incremental_ic 负值（-0.011 至 -0.020），与 F006/F007/F009 overnight 反转簇负相关 0.18-0.44，是库 reducer 而非 contributor。Direction 应转 dead。
> **MT Budget**: cumulative 180 → **186** · direction 0 → **6** · bucket `medium` · 本批 low=0 / medium=6 / high=0

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🔴·🟡·🔴·🔴·🟡 | IC_OOS=-0.033 mono=-0.4 incr=-0.020 | 线性 amount gate；signal 反向 | [[batches/batch_037/candidates/C001]] |
| C002 | ⏸ reserve | 🔴·🟡·🔴·🟢·🟢 | IC_OOS=-0.033 mono=-0.7 incr=-0.017 9 年同号 | log amount gate；统计强但方向反向，等 sister direction 收容 | [[batches/batch_037/candidates/C002]] |
| C003 | ❌ reject | 🔴·🔴·🔴·🟡·🟡 | IC_OOS=-0.027 mono=-0.4 incr=-0.015 | residual-vol 分母 = Barra vol_20d 设计共线，直接吃掉 | [[batches/batch_037/candidates/C003]] |
| C004 | ❌ reject | 🔴·🟡·🟡·🟡·🟡 | IC_OOS=-0.025 mono=-0.7 incr=-0.011 | composite gate；alpha_surv=0.44 勉强过；signal 仍反向 | [[batches/batch_037/candidates/C004]] |
| C005 | ❌ reject | 🔴·🔴·🔴·🟡·🟢 | IC_OOS=-0.026 mono=-0.4 ls_t=-1.77 | 5d momentum + vol 分母；ls_t<2 弱 | [[batches/batch_037/candidates/C005]] |
| C006 | ❌ reject | 🔴·🔴·🔴·🔴·🟡 | IC_OOS=-0.033 mono=-0.4 incr=-0.020 | turnover 变体；与 C001 同病 | [[batches/batch_037/candidates/C006]] |

**档位编码**：🟢 最优档 · 🟡 次档 · 🔴 阻断档

## 跨候选对比

- **方向 hypothesis 整批反向证伪**：6/6 候选 IC_OOS 在 -0.025 至 -0.033 区间，全部为负；mono_OOS 全部 -0.4 或 -0.7，方向一致负。Hypothesis 假设 gated momentum 在 csi1000 复活成 trend continuation，**实测是 reversal 信号**。这与 dead 方向 `return_momentum_acceleration` / `asymmetric_momentum` 已证伪的"raw momentum 在 csi1000 失效"结论一致——区别仅在本方向证明 **gate 不能救回 trend，反而把 reversal 信号叠厚**。
- **设计级共线 (C003/C005)**：T002 用 `Std(daily_return, 20)` 作为分母 = Barra `vol_20d` 风格的定义，导致 `style_r² = 0.346-0.519`、vol_20d exposure 12-28、alpha_survival 0.50-0.83 但残差 IC 仍为反转。**meta-lesson**：用 daily-return std 做分母 = 把 Barra vol_20d 写进信号设计里，无法 orthogonalize。
- **库角色 reducer (全员)**：6/6 incremental_ic ∈ [-0.011, -0.020] 全部负值。这些信号与 F009 overnight_intraday_spread 形成 0.30-0.44 的 cross-section 相关，与 F001 amount_cv_10 / F006-F008 shadow factors 也都形成 0.18-0.33 共线——本质是同一个 csi1000 反转因子簇的不同写法。Admit 任一会减少组合 IC。
- **C002 reserve 例外**：log-compressed gate 给出 9 年同号 + cum_ic_mdd=-53 + decay=1.53（OOS > IS）的统计稳健性，是本批最干净的"反转载体"。但 admit 进 trend_quality_gated direction 等于 hypothesis 与产物相反——因此 reserve 等待是否新开 sister direction `gated_reversal` 收容（或并入 dead reversal lessons）。
- **MT budget**：direction 0 → 6，方向首批即决定性证伪，无需继续探。

## Thread 进展

> [!failure]+ T001 [[directions/trend_quality_gated#T001]] — `[✗ DISPROVEN batch_037]`
> C001 / C002 (reserve, 待 sister direction) / C006 全部反向 IC。流动性 gate（amount linear / log / turnover）不能让 momentum 翻正，反而放大反转。

> [!failure]+ T002 [[directions/trend_quality_gated#T002]] — `[✗ DISPROVEN batch_037]`
> C003 / C005 全部反向。residual-vol 分母 = Barra vol_20d 设计共线，"低噪声 gate" 在 csi1000 等于"低 vol_20d 子集"，已被 Barra basis 覆盖。

> [!failure]+ T003 [[directions/trend_quality_gated#T003]] — `[✗ DISPROVEN batch_037]`
> C004 composite gate 也反向。叠 gate 不解决方向问题，只把噪声放大。

## 方向级反思

`trend_quality_gated` 一批 6 候选**完全证伪 direction hypothesis**——paper QuantaAlpha Channel 3 的 CleanTrend / OrderlyTrend 信号在 csi1000 上**符号完全翻转**。这与 dead 方向 `return_momentum_acceleration` / `asymmetric_momentum` 已建立的事实呼应：**csi1000 小盘 universe 的 short/mid-horizon momentum 是反转载体，不是趋势载体**。Gate（流动性 / 残差噪声 / composite）不能改变这一点。

**方向操作**：
- `status: exploring → dead`（不可逆）
- 元教训升格至 lessons.md 候选：「csi1000 上 short/mid-horizon (5-10d) momentum × any liquidity/vol gate 仍是反转载体；gate 不能把反转翻成 continuation；paper 的 Channel 3 CSI 300 大盘结果在 csi1000 不可迁移」
- C002 reserve 待评估是否值得开 sister direction `gated_reversal` 收容；目前先保持 reserve，下一轮决定

**Calibration**：本批 5 reject + 1 reserve，无 over-rejection——signal 都是反向 + 库 reducer，不是阈值过严。不触发校准。
