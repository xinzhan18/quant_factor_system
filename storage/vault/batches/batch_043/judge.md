---
batch_id: batch_043
direction: range_structure
judged_at: 2026-04-24T02:10:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reserve}
  - {candidate_id: C004, verdict: reserve}
  - {candidate_id: C005, verdict: reserve}
  - {candidate_id: C006, verdict: reserve}
batch_summary: {total: 6, admit: 0, reserve: 4, reject: 2}
admit_count: 0
reject_count: 2
reserve_count: 4
candidate_count: 6
mt_bucket: medium
---

# batch_043 Judge Summary

> [!abstract]+ batch_043 · [[directions/range_structure]] · 6 candidates
> ❌ **reject=2** (C001/C002) · ⏸ **reserve=4** (C003/C004/C005/C006) · ✅ **admit=0**
> **核心发现**: 方向首批即撞到分裂结论——**magnitude/ratio** 路径 (C005/C006) 被 vol_20d 吞噬（exposure 13–28，incremental_ic 全负），而 **distribution-shape** 路径 (C004 skew) 库独立（max_corr=0.117@F012, incremental_ic=+0.014, mono_oos=+1.0）但 alpha_survival=0.141 poor 构成悖论组合，subagent flag potential over-rejection——**触发阈值校准诊断**。
> **MT Budget**: cumulative 216 → **222** · direction 0 → **6** · bucket `medium`（search_adjusted 0.24-0.62）· 本批 low=1 / med=5 / high=0

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🟢·🔴·🟢·🟡·🟠 | mono_oos=-0.90 一桨 Q5, ls_t=-1.40, **incr_ic=-0.008** | IdxMax 时序 alpha_surv=0.89 clean 但库减值 | [[batches/batch_043/candidates/C001]] |
| C002 | ❌ reject | 🟠·🔴·🔴·🟡·🟠 | vol_20d exposure=**47.9**, alpha_surv=0.23, incr_ic=-0.019 | 高 range 频率阈值仍在 vol_20d 空间；**T001 freq-high 子路径 DISPROVEN** | [[batches/batch_043/candidates/C002]] |
| C003 | ⏸ reserve | 🟢·🔴·🟡·🟢·🟠 | IC=+0.010 ls_t=-0.23 mono_oos=0.0 U-shape, **incr_ic=+0.013 max_corr=0.16@F002** | 低 range 频率机制独立但信号太弱；Bollinger squeeze 思路沉淀 | [[batches/batch_043/candidates/C003]] |
| C004 | ⏸ reserve ⚠️ | 🟢·🟡·🟠·🟢·🟢 | **mono_oos=+1.00 完美** ls_t=+2.46 **incr_ic=+0.014 max_corr=0.117@F012** cum_mdd=-2.01 但 **alpha_surv=0.141 poor** + **mono_is=0.30 弱** | **悖论组合：4 个 error-kill 指标满足但 mono IS→OOS 异常放大 → 诊断非真错杀** | [[batches/batch_043/candidates/C004]] |
| C005 | ⏸ reserve | 🟠·🟡·🟠·🔴·🟠 | IC=-0.038 本批最强 ls_t=-2.18 mono=-0.6→-0.9 9 年同号, 但 **vol_20d exp=27.7, incr_ic=-0.025 NEGATIVE**, cum_mdd=-82 | 短/长 range ratio 机制对但被 F001/F009 吸收；等 orthogonalize | [[batches/batch_043/candidates/C005]] |
| C006 | ⏸ reserve | 🟠·🔴·🟠·🔴·🟢 | ls_t=-2.74 但 mono_is=-0.7→mono_oos=-0.10 崩塌, **incr_ic=-0.017 NEGATIVE** | range 变化率—Q5 一桨驱动 + 库负冗余 | [[batches/batch_043/candidates/C006]] |

## 跨候选对比

- **分裂结论**：magnitude/ratio 路径（C005 短长比 / C006 变化率 / C002 高频 threshold）**全部负 incremental_ic** (-0.019 到 -0.025) 且 dom_style=vol_20d exposure 13.9–47.9——range 的 power-mean transformation 沿用 vol_20d 空间；distribution-shape 路径（C004 skew 60d / C003 低频 threshold）**正 incremental_ic** (+0.014 / +0.013) 且 max_corr@库 低于 0.16——shape 层面真正独立。
- **悖论组合（C004）**：subagent 触发 rubric §错杀侦测四要件全过（库空间独立 + rank-order 完美 + 符号稳健 + 机制正交）+ flagged POTENTIAL OVER-REJECTION。按 /factor-mine 阈值校准触发 #1/#2/#3 全中（详见方向级反思 §阈值校准诊断）。
- **Style cluster**：5/6 候选 dominant_style=vol_20d（exposure 3.9–47.9）；C001 例外（exposure 低 alpha_surv=0.89 clean，但 IdxMax 时序信号太弱 ls_t=-1.40）。vol_20d 结构吸收律**跨 3 方向（stochastic_position / vwap_proxy_signals / range_structure）重现**——升格方向族级教训。
- **cum_ic_mdd 分化**：C003/C004 shape 路径 cum_mdd 浅（-4.57 / -2.01），C005/C006 magnitude 路径深（-65 / -82）；印证 shape 类机制时序稳健性远强于 magnitude 类。
- **MT 预算推进**：direction_candidates 0 → 6；bucket 推到 medium，search_adjusted 压到 0.24–0.62。

## Thread 进展

> [!note]+ T001 [[directions/range_structure#T001]] — `[◉ ACTIVE → shape 部分存活 / freq-high DISPROVEN]`
> - C001 IdxMax timing：机制 alpha_survival=0.89 clean 但 ls_t=-1.40 弱 + incr_ic 负 → reject。**timing 形式在 20d 窗口信噪比不足**。
> - C002 高 range 频率：vol_20d exposure=47.9 + alpha_surv=0.23 poor → reject。**freq-high threshold 仍在 vol_20d 空间**——**子路径 DISPROVEN**。
> - C003 低 range 频率：max_corr=0.16@F002 独立但 mono_oos=0.0 + ls_t=-0.23 → reserve。compression 机制存活但信号弱。
> - **C004 range skew**：shape 层面机制**库独立 + rank-order 完美 + cum_mdd 最浅**——触发错杀侦测（详见 §诊断）。
>
> **本批结论**：timing 与 freq-high 已两条子路径封闭；shape(skew/低频) 路径存活等重新设计。

> [!note]+ T002 [[directions/range_structure#T002]] — `[✗ DISPROVEN batch_043]`
> C005 短/长 range ratio 与 C006 变化率：9 年 IC 稳定但 **incremental_ic 全部为负** (-0.025 / -0.017)，vol_20d exposure 13.9–27.7——**range ratio/velocity 在 csi1000 与 F001/F009 共享同一反转簇载体**，与 [[directions/liquidity_acceleration]] batch_032 结论同构。T002 answered = "range 的 magnitude/ratio 形态与流动性簇同源，不独立"。

## 方向级反思

本方向**首批即遇到"shape vs magnitude 分裂"**：
- **Magnitude/ratio 路径全败**：5 候选 dom=vol_20d + incremental_ic 负——与 `return_distribution_signals` dead 结论 **"mean-of-power transformation 坍缩到 vol rank"** 在 range 字段上**再次实证**（第 3 次跨方向独立确认）
- **Shape 路径意外存活**：Skew(range, 60) 与低频 threshold 两候选 max_corr < 0.16，incremental_ic 正值 0.013–0.014——分布偏度是 range 的**三阶矩信息**，与 vol_20d 的二阶 std 数学不等价
- 与 [[directions/stochastic_position]] batch_041 / [[directions/vwap_proxy_signals]] batch_042 共同确认：**csi1000 的 cross-section 几何被 vol_20d 主导 2nd-moment 空间，逃离路径必须走 shape (3rd/4th moment) 或时序离散 (timing/freq) 而非 ratio/delta**

### 阈值校准诊断（C004 error-kill flag）

**触发条件**：
- ✅ **#1 错杀 flag**：C004 subagent 主动 flag potential over-rejection（rubric 错杀侦测四要件全过）
- ✅ **#2 零 admit 3 连**：batch_041 (0) + batch_042 (0) + batch_043 (0) 累计 admit=0，且 C004 满足 `max_lib_corr<0.30 + incremental_ic>0.010` 库空间独立条件
- ✅ **#3 Reserve 积压**：累计 reserve/judged 率 4/6=67% > 40% + 零 admit

**Step 1 诊断** — C004 是否真被错杀？

| 错杀要件 | C004 数值 | 通过 |
|---|---|---|
| 库空间独立 | max_corr=0.117@F012 (<0.30) + incr_ic=+0.0138 (>0.010) | ✓ |
| rank-order 完美 | mono_oos=+1.00 (≥0.80) | ✓ |
| 符号稳健 | sign_consistency=1.0, cum_ic_mdd=-2.01 (库最浅) | ✓ |
| 机制互补 | F012 amihud (1st moment 液性) vs C004 (3rd moment range shape) 机制正交 | ✓ |

**但深度诊断发现反证据**：
1. **IS→OOS mono 异常放大**：mono_is=0.30 (1704 天训练期仅弱单调) → mono_oos=+1.00 (484 天 OOS 完美单调)。正常 alpha IS mono ≥ OOS mono（decay 方向）；OOS 反而远强于 IS 说明 **OOS 期的 regime 特殊偶然或小样本统计波动**，不是稳健机制
2. **统计显著度中等**：ICIR_OOS=0.177 / ls_t_OOS=2.46 / IC_OOS=0.010——均 moderate 档，不是 strong
3. **split_dispersion=0.654 + ic_by_year 衰减**：4 split IC 均值 0.020 / 0.013 / 0.006 / 0.002 单调下降——edge 在历史中慢速弱化
4. **alpha_survival=0.141 << 0.40**：vol_20d 吞噬 86%——即便 shape 信号理论独立，实盘 Barra risk model 下**可投资部分不足 15%**

**结论**：C004 的 4 numeric criteria met 但**实质检验不达 error-kill 标准**。rubric 错杀侦测公式缺少"IS mono 同样达 0.80+"的 gate——未来应升格为 **五要件**（加入 mono_is 硬下界 0.6，防止 OOS 运气型 rank）。

**Step 2-4**：**不调阈，不追溯**。保持 C004 reserve（非 admit）、不修改 rubric、不 retroactive archive。但记录此次诊断为 lessons.md#Threshold Calibration 新条目候选（下次 consolidation 合并）：
> 2026-04-24 (batch_043) — **C004 skew(range, 60) 悖论组合诊断为非真错杀**。原因：mono_is=0.30 (OOS 1.00 反而远强)，违反 alpha 应有的"IS 强→OOS 部分 decay"规律；升格建议：错杀侦测要件 #2 (rank-order 完美) 应要求 **mono_is × mono_oos 同时 ≥ 0.60** 或 **mono_is ≥ 0.60**，防 OOS-only 统计波动。

### ROI 评估与下步

- direction 1 round / 6 candidates / 0 admit / 4 reserve——首批即证伪 2 子路径（freq-high / magnitude ratio）
- **状态**：`status: exploring` 保持（首批不足判 saturated）
- **priority**：`medium → low`（剩余活路 shape 路径需重新设计 - Skew 变体 / Kurt / Quantile-based shape，且 mono IS 硬下界后测试）
- **下一步**：
  1. 短期切换其它方向（不投 range_structure Round 2，等 shape 路径重新设计）
  2. lessons.md 升级错杀侦测要件（下次 consolidation）
  3. C004 reserve 保留作 shape 重设计的对照锚点
