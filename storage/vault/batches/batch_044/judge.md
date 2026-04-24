---
batch_id: batch_044
direction: quantile_shape_signals
judged_at: 2026-04-24T02:35:00Z
candidates:
  - {candidate_id: C001, verdict: reserve}
  - {candidate_id: C002, verdict: reserve}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reserve}
  - {candidate_id: C005, verdict: reserve}
  - {candidate_id: C006, verdict: reserve}
batch_summary: {total: 6, admit: 0, reserve: 5, reject: 1}
admit_count: 0
reject_count: 1
reserve_count: 5
candidate_count: 6
mt_bucket: medium
---

# batch_044 Judge Summary

> [!abstract]+ batch_044 · [[directions/quantile_shape_signals]] · 6 candidates
> ❌ **reject=1** (C003) · ⏸ **reserve=5** (C001/C002/C004/C005/C006) · ✅ **admit=0**
> **核心发现**: 方向 hypothesis "Quantile 差分逃离 vol_20d 主轴" **在 range 字段上部分证伪**——4 个 range Quantile 变体（C001/C004/C005/C006）均 style_r²>0.23 + dom_style=vol_20d（exposure 27–42），**6 候选 incremental_ic 全部为负**（+0.006 到 -0.044）；range Median/IQR/Q-diff 对 vol_20d 的 robust-免疫不等于 orthogonal。turnover Median/Mean 比（C002）IC 稳定但 ls 死。
> **MT Budget**: cumulative 222 → **228** · direction 0 → **6** · bucket `medium`（search_adjusted 0.47-0.62）· 本批 low=0 / med=6 / high=0

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ⏸ reserve | 🟢·🟢·🔴·🟢·🟢 | ic_oos=-0.052, mono -1/-0.9 严 ls_t=-2.64, incr=-0.036 | Q90-Q50 top-skew：rank 完美但 vol_20d exp=45 吞噬；等 orthogonalize | [[batches/batch_044/candidates/C001]] |
| C002 | ⏸ reserve | 🟠·🔴·🟡·🟡·🟠 | IC=+0.017 ICIR=+0.41 但 ls_t=+0.25，mono 1.0→0.1 U-shape, incr=+0.006 | turnover Med/Mean 比：IC 活 ls 死，OOS rank 崩 | [[batches/batch_044/candidates/C002]] |
| C003 | ❌ reject | 🔴·🟢·🔴·🔴·🟠 | max_corr=0.80@F012, alpha_surv=0.07, incr=-0.044 | amount IQR 坠入液性簇；方向假设"逃离 vol_20d"在 amount 字段完全失败 | [[batches/batch_044/candidates/C003]] |
| C004 | ⏸ reserve | 🟢·🟡·🔴·🟢·🟠 | ic_oos=-0.056, mono IS=OOS=-1.0 完美, ls_t=-2.65, incr=-0.037 | range IQR: rank 完美但 vol_20d exp=42 独霸 | [[batches/batch_044/candidates/C004]] |
| C005 | ⏸ reserve | 🟢·🔴·🔴·🟢·🟢 | ic_oos=-0.057, mono -1/-0.9 严, 但 ls_t=-1.93 weak, vol_20d exp=38 | range Median: location estimator 同样被 vol_20d 吞噬 | [[batches/batch_044/candidates/C005]] |
| C006 | ⏸ reserve | 🟠·🔴·🟠·🟢·🟠 | ic_oos=-0.031, mono -0.3→-0.1 崩塌, ls_t=-1.62 weak, incr=-0.020 | range Median 短/长比：比值形式比差分更易共变 | [[batches/batch_044/candidates/C006]] |

## 跨候选对比

- **hypothesis 证伪模式**：4 个 range Quantile 变体（C001 Q90-Q50 / C004 Q75-Q25 / C005 Median / C006 5d/60d Median 比）**全部 dominant_style=vol_20d**，exposure 27–42，style_r² 0.23–0.56——**Quantile 对尾部免疫 ≠ 对 vol_20d 正交**，robust location/spread estimator 仍然共线于 vol 主轴。
- **incremental_ic 全负**（仅 C002=+0.006 borderline 正）：6 候选入库皆减值，方向 ROI = 0。
- **rank-order vs tradable spread 反差**：C001/C004 mono_is=-1.0 + mono_oos=-0.9~-1.0（rank 完美）但 alpha_survival 0.31–0.37 poor + incr_ic 负——与 [[directions/return_distribution_signals]] 的 Q90-Q10 失败同构（rank-order 完美 ≠ alpha 真）。
- **Style cluster**：5/6 dom=vol_20d（非例外仅 C002 dom=vol_20d exposure=30 但 alpha_surv=1.03 clean）——vol_20d 结构吸收律第 4 次跨方向重现（stochastic / vwap_proxy / range_structure / quantile_shape）。
- **MT 预算推进**：direction_candidates 0 → 6；bucket 保持 medium。

## Thread 进展

> [!note]+ T001 [[directions/quantile_shape_signals#T001]] — `[◉ ACTIVE → hypothesis 部分证伪]`
> - range 字段（C001/C004/C005/C006）：Quantile 差分/Median/短长比全部 dom=vol_20d + incr_ic 负 → **range 路径 DISPROVEN**
> - amount 字段（C003）：max_corr=0.80@F012 near-duplicate + alpha_surv=0.07 → **amount 路径 DISPROVEN**（坠入液性簇）
> - turnover 字段（C002）：IC 活 ICIR=+0.41 但 ls_t=+0.25 鸿沟，mono_oos U-shape → **turnover Med/Mean 比机制不够强**
>
> **本批结论**：3 字段上的 Quantile shape 路径**全面证伪**。唯一未撞墙的是 "shape-only location-free" 纯 Quantile 比例（如 Q90-Q10 除以 Q75-Q25 tail-ratio），未设计。

## 方向级反思

本方向**首批即遇到假设的根本性证伪**：
- Quantile 算子的 robust-to-outliers 属性**不等于** Barra vol_20d orthogonality——两个不同概念混淆在 hypothesis 设计中
- 与 [[directions/range_structure]] C005/C006 batch_043 结论一致：range 任何形态（magnitude/ratio/Median/Quantile/IQR）都坠入 vol_20d 吸收簇，**第 4 次跨方向独立确认**
- Learning：未来 shape 路径设计必须 **显式做 vol_20d orthogonalization 预处理**（需 Python 残差工具链），或换到 **非 return、非 range 的 shape 维度**（如 intraday order flow / fundamental event 事件密度——非当前 DSL 覆盖字段）

### 阈值校准诊断

**触发条件**：
- ⚠️ **#1 错杀 flag**：C001 subagent flag "Potential over-rejection 3/4 条"（非 4/4，cum_ic_mdd=-84 不达"库中位数更浅"条件；且 incremental_ic=-0.036 为负非 library-additive）
- ✅ **#2 零 admit 3 连**：batch_042/043/044 累计 admit=0
- ✅ **#3 Reserve 积压**：累计 reserve/judged 率 5/6=83% > 40%

**Step 1 诊断** — 本批任何 reserve 是否真错杀？

| 候选 | max_lib_corr<0.30 | incr_ic>0.010 | mono_oos≥0.80 | cum_ic_mdd 库最浅 | 结论 |
|---|---|---|---|---|---|
| C001 Q90-Q50 | ✓ 0.215 | ✗ **-0.036** | ✓ 0.9 | ✗ -84.19 | 不达 error-kill |
| C002 turnover Med/Mean | ✗ 0.404 | ✗ +0.006 | ✗ 0.1 | ✓ -0.96 | 不达 error-kill |
| C004 range IQR | ✓ 0.234 | ✗ **-0.037** | ✓ 1.0 | ✗ -86.53 | 不达 error-kill |
| C005 range Median | ✓ 0.221 | ✗ **-0.038** | ✓ 0.9 | ✗ -72.13 | 不达 error-kill |
| C006 range Med 短长比 | ✓ 0.214 | ✗ **-0.020** | ✗ 0.1 | ✗ -66.07 | 不达 error-kill |

**诊断结论**：**无真错杀**。5 个 reserve 候选中 4 个 incremental_ic 负（库负冗余，admit 会减值）；C002 唯一正但 +0.006 <0.010 低于阈值 + mono_oos=0.1 rank-order 不成立。

**Step 2-4**：**不调阈，不追溯**。所有 reserve 都属 "机制存活但库空间负冗余" 或 "rank 不成立" 两类——都不属"错杀"。记录观察：**本批强烈确认 csi1000 vol_20d 结构吸收律 + Quantile 算子不等于 orthogonalize**。

## 库容量警示

**此时状态**：
- batch_041→044 连续 4 批 0 admit（累计 9 reserve + 12 reject）
- 5 个最近直接活跃方向（stochastic / vwap_proxy / range / quantile_shape）全部因 vol_20d 吞噬而 saturated/dead-trending
- 阻塞根源：**csi1000 daily-bar 2nd-moment 空间被 vol_20d 彻底占据**，剩余 alpha 空间需要 (a) **Python 残差化工具链**（未构建），或 (b) **非 daily-bar 数据**（intraday / fundamental events）

**下步建议**：
1. 强烈触发 Phase 5 consolidation（rounds_since_consolidation=9→10 in batch_044）整理本次发现的"vol_20d 主导律"升级到 lessons 系统级
2. Consolidation 后跳出 daily-bar 二阶矩探索，尝试 (a) 实现简单 Barra orthogonalize Python 候选，或 (b) 探索未扩展的 CsRank / CsZscore 组合
