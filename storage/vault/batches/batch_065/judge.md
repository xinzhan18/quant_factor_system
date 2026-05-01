---
batch_id: batch_065
direction: trend_residual_geometry
judged_at: 2026-05-01T12:40:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reserve}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 1, reject: 5}
admit_count: 0
reject_count: 5
reserve_count: 1
candidate_count: 6
mt_bucket: medium
---

# batch_065 Judge Summary

> [!abstract]+ batch_065 · [[directions/trend_residual_geometry]] · 6 candidates
> ✅ **admit=0** · ⏸ **reserve=1** (C005 Rsquare/PS rank-diff) · ❌ **reject=5** (3 hard_gate fail + 2 soft fail)
> **核心发现**: T001 Slope-on-close 双侧失败 (短窗→str_1m 吸收 + incr_ic 负 / 长窗→regime drift sign_flip), T002 Resi-on-close 双路径 weak/sign_flip, T003 Rsquare standalone 接近零信号但 rank-diff 包装 (C005) 保留唯一 reserve. **Slope/Resi/Rsquare 三 0-admit operator-family 中只有 Rsquare-rank-diff 路径在 csi1000 cross-section 仍有微弱独立信号空间**.
> **MT Budget**: cumulative 348 → **354** · direction 0 → **6** · bucket `medium`（3 个 hard-gate fail 不计 mt_budget; 通过 hard gate 的 C001/C003/C005 都 medium 档）

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🟡·🟢·🔴·🔴·🟢 | ic_oos=-0.034 ls_t=-3.29 alpha_surv=0.24 incr_ic=-0.017 | 通过 hard gate 但 str_1m 重表达 + 库内已有同源载体 → 负库增值 | [[batches/batch_065/candidates/C001]] |
| C002 | ❌ reject | hard_gate | sign_flip + ic_oos<0.008 + decay<0.2 | Resi(60)+PB(60) 长窗组合 train→val IC 反向 | [[batches/batch_065/candidates/C002]] |
| C003 | ❌ reject | 🟡·🔴·🟡·🔴·🟡 | ic_oos=-0.0086 ls_t=-1.05 incr_ic=-0.018 | 弱 stat + 负库增值 + 逐年衰减（2023 IC 接近 0） | [[batches/batch_065/candidates/C003]] |
| C004 | ❌ reject | hard_gate | sign_flip + ic_oos<0.008 + decay<0.2 | Rsquare 60d standalone IC 几乎为 0，但 rank-order 形状强（mono=1.0/0.8） | [[batches/batch_065/candidates/C004]] |
| C005 | ⏸ reserve | 🟡·🔴·🟠·🟡·🟡 | ic_oos=+0.0155 ls_t=1.13 mono_oos=0.9 incr_ic=+0.002 | 唯一非负 IC + 强单调 + ic_by_year 2017+ 信号增强；但 alpha_surv 0.19 + ls_t weak 不足 admit | [[batches/batch_065/candidates/C005]] |
| C006 | ❌ reject | hard_gate | sign_flip + decay -1.297 | 长窗 Slope/PB rank-diff 多年方向反转（2015 -0.038 → 2023 +0.015 regime drift） | [[batches/batch_065/candidates/C006]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🟠 边际（borderline）· 🔴 阻断档（misaligned/weak/poor/high/unstable）· `hard_gate` reject 该列写 `hard_gate` 不填色。整列飘红 = 方向级警示。

## 跨候选对比

- **Style 聚合**：6 候选 5 个 dominant_style ∈ {vol_20d, str_1m}。C001 (str_1m beta=8.56, vol_20d beta=8.06) 短窗 Slope/Ref 是 **str_1m 重表达**；C002/C003/C004/C005/C006 (vol_20d beta 8-15.84) 长窗或 R² 类信号是 **vol_20d 重表达**——本方向 LHS atom 与 vol_20d 几何正交期望**整体破产**（manifest 第 1 条硬约束："LHS atom 必 vol_20d 几何正交"未达到，6 个候选 LHS 都被 vol_20d 显著吸收）
- **相关度 cluster**：候选间互相关 < 0.30（C006 与 F002 corr=0.42 是与库的相关，非候选互相关），无候选互相重叠；本批 6 候选互相**几何独立但同被风险因子吃掉**——典型 P004 vol_20d 结构性吸收复现
- **MT 预算推进**：cumulative_candidates 348→354；direction_candidates 0→6；3 个 candidates 进入 mt_budget 计算（hard_gate 通过的 C001/C003/C005），全部 medium bucket
- **关键观察**: C001 (short Slope) + C006 (long Slope) 双窗失败 → Slope-on-close 路径在 csi1000 上无独立 alpha；C002 (long Resi) + C003 (short Resi) 双窗失败 → Resi-on-close 路径同样 dead；C004 (standalone R²) 信号近 0 但 mono 完美 → C005 (rank-diff 包装) 是 R²-rank-diff 唯一存活路径

## Thread 进展

> [!failure]+ T001 [[directions/trend_residual_geometry#T001]] — `[✗ DISPROVEN batch_065]`
> reject C001 (短窗 Slope/Ref standalone, str_1m 吸收 + incr_ic 负) + reject C006 (长窗 Slope/PB rank-diff, sign_flip + regime drift)。**Slope-on-close 双窗双结构（standalone short + rank-diff long）皆失败**——LHS atom 信号本质 = str_1m (短窗) 或 vol_20d (长窗) 重表达。结论：`Slope($close, N)` operator-family 在 csi1000 cross-section 无独立 alpha 空间。

> [!failure]+ T002 [[directions/trend_residual_geometry#T002]] — `[✗ DISPROVEN batch_065]`
> reject C002 (Resi(60)+PB rank-diff, hard_gate sign_flip + decay) + reject C003 (Resi(20)+PE rank-diff, weak stat + negative incr_ic + 逐年衰减)。**Resi-on-close 双窗双 RHS 配置全失败**——time-series Resi atom 在 csi1000 cross-section 与 OHLC range 几何因子（F006, F008, F009）共同覆盖，信号空间太窄。结论：`Resi($close, N)` × fundamental level RHS 路径在当前库覆盖度下无 admit 空间。

> [!warning]+ T003 [[directions/trend_residual_geometry#T003]] — `[◉ ACTIVE]`（部分 ANSWERED）
> reject C004 (standalone Rsquare 60d, ic_oos≈0 but mono 完美) + reserve C005 (Rsquare/PS rank-diff, ic_oos=+0.0155 mono=0.9 ls_t=1.13)。Standalone Rsquare 信号几乎为 0 但 rank-order 形状完美——rank-diff 包装放大信号到边缘 admit 区。**T003 thread 部分 ANSWERED**：standalone disproven, rank-diff 路径仍 ACTIVE。下批应测 Rsquare × {PE level, PB level, raw close norm} 三路径中哪个最稳。

## 方向级反思

**核心律**：本批揭示 Slope/Resi/Rsquare 三 operator-family 在 csi1000 cross-section 上的整体困境——LHS atom 与 vol_20d 几何正交期望（manifest 硬约束第 1 条）**全面破产**：

- 5/6 候选 dom=vol_20d（beta 8.0-15.8），1/6 dom=str_1m（C001 beta=8.56）——**operator novelty 不等价 style novelty**：Slope/Resi/Rsquare 在 close 字段上的信号载体仍是标准 Barra 风险因子（vol_20d 长窗 / str_1m 短窗）
- 仅 C005 (Rsquare-rank-diff × PS level) 在 max_corr 0.21 + incremental_ic +0.002 上保留库空间微小独立性，但 ls_t=1.13 + alpha_surv=0.19 不足 admit
- 本方向 zero_admit 未打破 zero_admit_streak（5→6），但 reserve C005 提供下批 anchor 路径

**hot_topic P004 (vol_20d 结构性吸收) 复现**：本批进一步确认 vol_20d 在 long-window LHS 上的几何主导性。Slope/Resi/Rsquare 都是 long-window rolling-regression 信号，本质难脱 vol_20d；唯一缓解路径是 rank-diff 包装 + 估值 RHS 互补（C005 路径）

**hot_topic P006 (library_reducer trap) 部分复现**：C001 通过 hard gate 且 ls_t=-3.29 strong，但 max_corr=0.24 在 [0.30, 0.70] 死区**之外**（0.24<0.30），按 P006 预期不应被 reject——然而 incremental_ic=-0.017 negative 是更严格的反库增值证据，rubric 的 incremental_ic 双重 gate 起作用避免错杀风险

**下轮建议**：
1. **不再扩 Slope-on-close / Resi-on-close family**（T001/T002 双 DISPROVEN）
2. **保留 T003 Rsquare-rank-diff 路径**：下批用 C005 anchor 测 Rsquare(60d) × {PE60d, PB60d, no-RHS norm} 三路径，目标观察哪个 RHS 最稳
3. **operator-family novelty 切换路径**：考虑 Slope-on-other-fields ($turnover_rate, $amount, $volume) — 但 RHS 必避 F002/F017 anchor cluster
4. **方向 status 推进**：本批 admit=0 但 thread 进展明确（2 DISPROVEN + 1 部分 ANSWERED），方向**保持 exploring** 一批；若下批 C005-anchor 路径仍全 reject，**触发 status: exploring → dead**
5. **错杀侦测**：本批无候选触发错杀 flag（max_corr<0.30 + incremental_ic>0.010 + mono>0.8 + sign_consistency=1.0 + nearest IC 反号 五条件无候选全满足），无 calibration trigger
