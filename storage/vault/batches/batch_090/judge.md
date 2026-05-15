---
batch_id: batch_090
direction: price_conditional_amplitude
judged_at: 2026-05-16T03:35:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 0, reject: 6}
admit_count: 0
reject_count: 6
reserve_count: 0
candidate_count: 6
mt_bucket: medium
---

# batch_090 Judge Summary

> [!abstract]+ batch_090 · [[directions/price_conditional_amplitude]] · 6 candidates
> ❌ **reject=6** · ⏸ reserve=0 · ✅ admit=0
> **核心发现**: rank-conditional aggregation 工艺在 csi1000 daily 上**全方位失败**——paper-original / DSL-soft / P008-stack / RHS-swap 4 条路径一致被 vol_20d 重度吞噬（残差吞噬 63-75%），且 6/6 incremental_ic ≤ 0.003（5/6 显著负）→ 信号在当前库已被反转/turnover/amount_cv 系列完全覆盖。
> **MT Budget**: cumulative 498 → **504** · direction 0 → **6** · bucket `medium`（本批 low=0 / med=6 / high=0）

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🟢·🟢·🔴·🔴·🟡 | IC=-0.053 mono=-1.0 ls_t=-6.04 alpha_surv=0.34 incr_ic=-0.011 | paper raw 信号最强但完全被 vol_20d (35×) 吞噬；负库增值 | [[batches/batch_090/candidates/C001]] |
| C002 | ❌ reject | 🟢·🟠·🔴·🔴·🟡 | IC=-0.040 ICIR=-0.35 alpha_surv=0.25 incr_ic=-0.012 | N=60 比 N=20 alpha_surv 更差，P008 长尺度未解 crowding | [[batches/batch_090/candidates/C002]] |
| C003 | ❌ reject | 🟢·🟠·🔴·🔴·🟡 | IC=-0.043 mono=-0.60 max_corr=0.86@F027 incr_ic=-0.013 | DSL-soft 本质是 F027 反转的几何变形，corr=-0.86 高度共线 | [[batches/batch_090/candidates/C003]] |
| C004 | ❌ reject | 🟢·🟠·🔴·🟡·🟡 | IC=-0.041 mono=-0.30 alpha_surv=0.27 incr_ic=-0.004 | DSL-soft N=60 单调性崩溃 mono=-0.30 → Q5 一桨驱动 | [[batches/batch_090/candidates/C004]] |
| C005 | ❌ reject | 🟠·🔴·🔴·🟡·🟡 | IC=-0.027 ICIR=-0.21 alpha_surv=0.29 incr_ic=0.003 | P008 完整 stack 反而稀释 alpha 60%；vol_20d 暴露不降反升 | [[batches/batch_090/candidates/C005]] |
| C006 | ❌ reject | 🟢·🟠·🔴·🔴·🟡 | IC=-0.051 mono=-0.90 alpha_surv=0.38 incr_ic=-0.010 | RHS-swap (turnover) 同样卡在 alpha_surv=0.38 阈下；负 incr_ic | [[batches/batch_090/candidates/C006]] |

**档位编码**：🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档

## 跨候选对比

- **Style 一致性**：6/6 候选 `dominant_style_exposure = vol_20d`，暴露范围 8.84-35.26；本批揭示 rank-conditional aggregation 工艺**整体易被 vol_20d 吞噬**——无论 numerator (amp/turnover)、rank window (20/60)、是否加 TsRank 包装都未脱敏
- **Alpha killer 共性**：6/6 候选 Barra 残差 IC 比 raw IC 衰减 63-75%（C001=66%、C002=75%、C003=19%但被反转 cluster 覆盖、C004=73%、C005=70%、C006=63%）
- **Cluster 同源化**：C003/C004/C005 三个 DSL-soft 共同与 F027 close/MA 反转 cluster 高度相关 (corr 0.59-0.86)；C001/C002/C006 Python wrapper 走 F016/F017/F018 turnover/amount 微观节奏 cluster
- **Incremental IC 共性**：6 候选 incr_ic 分布 = [-0.013, -0.012, -0.011, -0.010, -0.004, +0.003]，5/6 显著负值 → **本批整体降低组合 alpha**，没有库增值候选
- **MT 预算推进**：direction_candidates 0 → 6（首批用满中度预算）；bucket 全 medium，validation_exposure 89 → 95

## Thread 进展

> [!failure]+ T001 [[directions/price_conditional_amplitude#T001]] — `[✗ DISPROVEN batch_090]`
> reject C001 (paper N=20) + C002 (P008 N=60)。**结论**: paper-original V_high(0.25)−V_low(0.25) raw 信号确实存在 (mono=-1.0 ls_t=-6.04) 但完全被 vol_20d (暴露 35×) + 库内 amount_cv/turnover_cv (F001/F017) 共同覆盖。alpha_survival 0.25-0.34 远低于方向阈 0.40，incremental_ic 全负。N=20 → N=60 时间尺度调整无法解救。
>
> 决断点回答：`incr_ic > 0`? **NO** (-0.011, -0.012)；`max_corr < 0.30`? marginal (0.23-0.40)；`style_R²(vol_20d) ≤ 0.20`? **NO** (0.24-0.31)。三条决断点 0/3。

> [!failure]+ T002 [[directions/price_conditional_amplitude#T002]] — `[✗ DISPROVEN batch_090]`
> reject C003 (DSL-soft N=20) + C004 (DSL-soft N=60)。**结论**: DSL-soft baseline 数值上达成 |IC|=0.041-0.043（满足 T002 决断点"|IC|≥0.015"），但 max_corr=0.63-0.86 表明 DSL-soft 本质是库内 F027 close/MA 反转 cluster 的几何变形——`Mul((H/L-1), 2·TsRank($close,N)-1)` 在 cross-section 等价于"价格相对 MA 高出多少"的反转信号。**工艺并不带来独立信号家族**。N=20 单调性 mono=-0.60 + N=60 mono=-0.30 一致提示 Q5 一桨驱动。

> [!failure]+ T005 [[directions/price_conditional_amplitude#T005]] — `[✗ DISPROVEN batch_090]`
> reject C005 (TsRank-60 wrap)。**结论**: P008 完整 escape stack 三条件 (dim-less ratio × micro-only × TsRank≥60d) **在 rank-conditional aggregation 方向不构成 vol_20d-escape**。TsRank 包装让 IC 从 C004 的 -0.041 衰减到 -0.027 (60% loss)，ICIR 落到 weak 档 0.21；vol_20d 暴露反而从 8.84 升到 10.77。需在 [[lessons]] 记录"P008 律对 rank-conditional aggregation 方向无效"。

> [!failure]+ T003 [[directions/price_conditional_amplitude#T003]] — `[✗ DISPROVEN batch_090]`
> reject C006 (turnover RHS-swap)。**结论**: 把 numerator 从 amp 换成 turnover_rate 同样卡在 alpha_surv=0.38 (方向阈 0.40 下方)，incremental_ic=-0.010 负值。**工艺本身（rank-conditional aggregation）不创造独立性**——无论 numerator 是 amp 还是 turnover，alpha_surv 都在 0.25-0.38 区间 + incr_ic 都负。原计划"T003 只有 T001 admit 后才推进"被打破（本批首次冻结时已包含 C006 作为提前验证）。

> [!note]- T004 [[directions/price_conditional_amplitude#T004]] — `[◉ ACTIVE]`（本批无候选，T001 未 admit 故未触发救援路径）

## 方向级反思

**direction status: exploring → 建议 dead**。本批 6/6 候选全 reject + Thread T001/T002/T003/T005 四条线**一致证伪**，无残余可探空间。

**核心证据**：
1. **vol_20d 风格吸收律对该方向系统性失败**：6/6 候选 dominant_style=vol_20d，Barra 残差吞噬 63-75%，量级与历史 vol_20d-fail 候选一致
2. **库覆盖完备**：F001 (amount_cv) + F017 (turnover_rank_diff) + F027 (close/MA 反转) + F025 (shadow_asymmetry) 共同覆盖本方向所有几何形态；incremental_ic 5/6 显著负
3. **P008 律不适用**：TsRank≥60d 包装让 alpha 衰减而非 crowding 剥离，否决了"P008 是 vol_20d-escape 唯一正路径"在该方向的适用性

**关键发现入档建议**（可由 /factor-consolidate 升格到 lessons）：
- **Pattern**: rank-conditional aggregation 工艺（按 close-rank 切割聚合 amp/turnover 等 numerator）在 csi1000 daily 上**整体被 vol_20d cluster 覆盖**，无法成为独立信号家族
- **Mechanism**: 高/低价段差值聚合本质是"价格相对位置"的二次衍生，与 close/MA 反转 cluster 共享几何空间

**direction status 转换建议**：`exploring → dead` (而非 saturated，因为方向种子已彻底否定，非饱和)。

**下一步**：等 orchestrator 触发 /factor-consolidate 升格本批结论，并把 [[lessons]] 加入"rank-conditional aggregation = vol_20d 重度吸收族"教训；新方向需绕开 close-rank-conditioned aggregation 几何空间。

**Anchor rule 检查**：6 候选全 reject，无 admit；同 dominant_style (vol_20d) 但因全 reject 不触发 anchor rule cap。

**错杀侦测**：6 候选自检全部不构成错杀（max_corr / incr_ic / mono 三项至少一项不满足"库空间独立"判定）。`potential over-rejection` flag = 0。
