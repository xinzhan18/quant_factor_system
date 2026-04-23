---
batch_id: batch_032
direction: liquidity_acceleration
judged_at: 2026-04-23T15:35:00Z
candidates:
  - {candidate_id: C001, verdict: reserve}
  - {candidate_id: C002, verdict: reserve}
  - {candidate_id: C003, verdict: reserve}
  - {candidate_id: C004, verdict: reserve}
  - {candidate_id: C005, verdict: reserve}
  - {candidate_id: C006, verdict: reserve}
batch_summary: {total: 6, admit: 0, reserve: 6, reject: 0}
admit_count: 0
reserve_count: 6
reject_count: 0
candidate_count: 6
mt_bucket: medium
---

# batch_032 Judge Summary

> [!abstract]+ batch_032 · [[directions/liquidity_acceleration]] · 6 candidates
> ❌ **admit=0** · ⏸ **reserve=6** (C001/C002/C003/C004/C005/C006) · ❌ **reject=0**
> **核心发现**: volume base、10d/120d 长分母、以及 normalized acceleration 三条扩展路径全部复现了与 batch_023 相同的结构图景：**rank-order 真实，但 `incremental_ic` 全为负，仍是 F001/F002 吸收后的 library reducer**。这不是“还差一点 admit”，而是“方向在当前日频 DSL 空间已被 answer 掉”。
> **MT Budget**: cumulative 152 → **158** · direction 3 → **9** · bucket `medium` · 本批 low=0 / medium=6 / high=0

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ⏸ reserve | 🟢·🟢·🟡·🟡·🟢 | IC=-0.0425 incr=-0.0258 corr=0.304@F001 | 5d/60d volume 是本批最干净的代表性 reserve，但仍只是 F001 同族 reducer | [[batches/batch_032/candidates/C001]] |
| C002 | ⏸ reserve | 🟢·🟢·🔴·🟡·🟢 | 10d/120d volume alpha_surv=0.367 incr=-0.0224 | 长分母没有打开新轴，反而把 CP04 风格吞噬放大到 poor | [[batches/batch_032/candidates/C002]] |
| C003 | ⏸ reserve | 🟢·🟢·🔴·🟡·🟡 | 10d/120d amount alpha_surv=0.289 incr=-0.0242 | amount base 仍是最强统计、最差风格清洁度的老问题复写 | [[batches/batch_032/candidates/C003]] |
| C004 | ⏸ reserve | 🟢·🟢·🔴·🟡·🟢 | 10d/120d turnover alpha_surv=0.357 incr=-0.0186 | turnover 长窗比值和 batch_023 C003 同型，只是把 reserve pattern 拉长确认了一遍 | [[batches/batch_032/candidates/C004]] |
| C005 | ⏸ reserve | 🟢·🟡·🔴·🟡·🟡 | norm amount accel ICIR=-0.293 incr=-0.0192 | 长窗 normalized delta 修掉了短窗噪声，但没有修掉负增量和风格吞噬 | [[batches/batch_032/candidates/C005]] |
| C006 | ⏸ reserve | 🟢·🟢·🔴·🟡·🟢 | norm volume accel mono=-0.6 incr=-0.0174 | volume normalized 仍是尾部驱动 + 负增量，不能当成新路径继续挖 | [[batches/batch_032/candidates/C006]] |

**档位编码**：🟢 最优档 · 🟡 次档 · 🔴 阻断档。全批无 hard_gate fail，但 `incremental_ic < 0` 使所有候选都停在 reserve。

## 跨候选对比

- **全批同一模式**：6/6 候选都通过 hard gates，`sign_consistency=1.0`，且 OOS IC/ICIR/ls_t 普遍达到 strong 或 borderline，但 `incremental_ic` 全部为负（-0.017 至 -0.026）。这说明 liquidity acceleration 在统计上是真信号，但在现有库空间里只会减值，不会增值。
- **volume base 没能绕开 F001**：C001/C002/C006 是本批专门新增的 volume family，对应 batch_023 未测的 base。结果最好的 C001 仍是 `max_corr=0.3036@F001`、`incr_ic=-0.0258`；说明“换 field 到 `$volume`”并不构成新维度。
- **长分母恶化 CP04**：从 5d/60d 拉到 10d/120d 后，C002/C003/C004 的 `alpha_survival` 分别降到 0.3668/0.2892/0.3574，`style_r_squared` 升到 0.438/0.482/0.418。长分母只是在更稳定地复现同一个被 `vol_20d` 吞噬的信号。
- **normalized acceleration 不解决核心矛盾**：C005/C006 试图回答 batch_023 C002 的“短窗 delta 太噪”问题。结果 C005 仍 `incr_ic=-0.0192`，C006 虽 `alpha_surv=0.4056` 贴线过阈，但 `monotonicity_oos=-0.6`、`incr_ic=-0.0174`，说明问题不在短窗噪声，而在库空间吸收。
- **风格暴露高度同质**：6/6 的 `dominant_style_exposure` 都是 `vol_20d`，`style_r_squared` 全部 > 0.30。这个方向的日频 DSL 形态已经不再是“找下一个算子”，而是“再怎么换写法都落回同一个 Barra 载体”。

## Thread 进展

> [!failure]+ T001 [[directions/liquidity_acceleration#T001]] — `[✗ DISPROVEN batch_032]`
> batch_023 已证明 5d/60d ratio（amount / turnover）有真实 rank-order 但 `incr_ic < 0`。batch_032 再补上 volume base、10d/120d 长分母、以及 normalized acceleration 后，6 候选 **无一例外仍是负 incremental_ic**。结论已经足够明确：在当前日频 DSL 空间里，流动性加速度不是“尚未提纯的 admit 候选”，而是**被 F001 吸收后的 reserve family**。

> [!note]- T002 [[directions/liquidity_acceleration#T002]] — `[✗ DISPROVEN batch_023]`（本批无新增证据）

## 方向级反思

`liquidity_acceleration` 到此可以从 `exploring` 收束到 `saturated`。原因不是“信号不存在”，恰恰相反，**信号非常真实**：

- 9 个累计候选里，绝大多数都满足强或近强的 CP03
- 多个候选达到 `monotonicity_oos ≈ -1.0`
- 所有候选都保持 `sign_consistency=1.0`

真正的问题是它们**全部不能给现有库带来正边际**。也就是说，这个方向已经从“search”切换为“calibration of a known reducer family”。继续在日频 DSL 里新增 reserve 只会堆积同义证据，不会增加知识密度。

**方向操作**：建议 `status: exploring → saturated` · `priority: medium → low`。

**复活条件**：
1. F001 退役或库结构重组后，重新审视 batch_023 / batch_032 的 reserve 池。
2. 走 Python 真 residualization，而不是继续在 DSL 里换 ratio / delta / normalize 写法。
3. 引入更高频数据后，改用真正的 microstructure liquidity acceleration，而不是日频 OHLCV proxy。

**Calibration**：
- 本批无 `potential over-rejection` flag。6 个候选虽然统计强，但 `incremental_ic` 全负，不满足错杀诊断的第一条“库空间独立”条件。
- 不触发 threshold calibration；这不是阈值过严，而是库空间已经吸收。
