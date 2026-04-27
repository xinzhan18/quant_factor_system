---
batch_id: batch_056
direction: range_structure
judged_at: 2026-04-25T18:00:00Z
candidates:
  - {candidate_id: C001, verdict: reserve}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 1, reject: 5}
admit_count: 0
reject_count: 5
reserve_count: 1
candidate_count: 6
mt_bucket: high
---

# batch_056 Judge Summary

> [!abstract]+ batch_056 · [[directions/range_structure]] · 6 candidates
> ✅ **admit=0** · ⏸ **reserve=1** (C001) · ❌ **reject=5** (C002/C003/C004/C005/C006)
> **核心发现**: **T003 沿 C005 衍生 intraday position dispersion family 首轮全 0 admit，但 C001 (open lower-shadow position dispersion × VWAP magnitude) reserve 验证 family 部分可扩展**。6 候选 incremental_ic 模式：1 正 (C001 +0.0085) / 1 ≈ 0 (C006 +0.001) / 4 负 (C002 N/A 硬闸 / C003 -0.006 / C004 -0.0024 / C005 N/A 硬闸)——P005 RHS basis 共振饱和律持续，但 C001 在 (O-L)/(H-L) atom 与 amount/volume RHS 上拿到 incr_ic=+0.0085 库增值，证明 open-anchored intraday position 维度仍有空间。C002/C005 双 hard_gate fail (sign_flip / IC_too_low)，C003 daily-return-per-range 完整命中 vol_20d 吸收律 (vol_20d=47.2 + max_corr=0.65@F014)，C004 incr_ic 负但 mono+ls_t 强——library reducer 第 5 次复现，C006 alpha_surv=0.0725 极端 poor 表面 IC 假象 — vol_20d 完全吞噬。
> **MT Budget**: cumulative 288 → **294** · direction 12 → **18** · bucket `high`（adj `medium`）· 本批 low=0 / med=0 / high=6

## 候选一览

| ID   | Verdict   | 档位 (CP2·3·4·5·6)        | Key Metric                                                                | 反思                                                       | Detail                                |
| ---- | --------- | ----------------------- | ------------------------------------------------------------------------ | -------------------------------------------------------- | ------------------------------------- |
| C001 | ⏸ reserve | 🟢·🟡·🔴·🟡·🟢          | ic_oos=+0.021 mono=+1.0 incr=+0.0085 max_corr=0.50@F019 cum_mdd=-4.06 极浅 | open lower-shadow position 维度首突破 + alpha_surv=0.24 待诊断   | [[batches/batch_056/candidates/C001]] |
| C002 | ❌ reject  | 🔴 (CP01 hard_gate)     | sign_flip train+0.002 vs val-0.008 + oos_decay=-4.34                     | upper-shadow-of-open × ROE proxy 在 csi1000 IS/OOS 完全反转    | [[batches/batch_056/candidates/C002]] |
| C003 | ❌ reject  | 🟡·🔴·🔴·🔴(incr-)·🟡   | mono collapse -0.90→-0.10 + incr=-0.006 + vol_20d=47.2 + max_corr=0.65   | daily-return-per-range 完整命中 hypothesis vol_20d 吸收律警告     | [[batches/batch_056/candidates/C003]] |
| C004 | ❌ reject  | 🟡·🔴·🔴·🟡(incr-)·🟡   | ls_t=4.62 strong + mono=+1.0 完美 + incr=-0.0024 NEG + alpha_surv=0.27   | "strong-mono+strong-ls_t but library reducer" 第 5 次复现     | [[batches/batch_056/candidates/C004]] |
| C005 | ❌ reject  | 🔴 (CP01 hard_gate)     | ic_oos=-0.0042 < 0.008 + mono_oos=-0.90 strong-but-weak-IC + sign_consis=0.75 | high-overnight-gap-per-range × turnover/pb IC 量级不足通过门槛    | [[batches/batch_056/candidates/C005]] |
| C006 | ❌ reject  | 🟡·🔴·🔴·🟡(incr≈0)·🟡  | ic_oos=+0.025 表面 strong 但 alpha_surv=0.0725 极端 + ls_t=0.90 weak + vol_20d=30.67 | composite midpoint Std × turnover-by-value：vol_20d IC 假象典型 | [[batches/batch_056/candidates/C006]] |

## 跨候选对比

**Style 聚合 (本批 6 候选共性)**：
- 6 候选 `dominant_style_exposure` 全部 = `vol_20d`，exposure 范围 **7.96 (C001) – 47.2 (C003)**
- C001 vol_20d exp 最低 (7.96)、style_r²=0.17 borderline、alpha_surv=0.24 poor 但 incr_ic=+0.0085 正——这是 reserve 与全 reject 的关键差分
- C003 vol_20d=47.2 极端 + str_1m=1.15 + ep_ratio=1.78 → 三 style 灾难
- C006 vol_20d=30.67 极端 + turnover_20d=4.13 + str_1m=0.98 → 双 style + IC 假象典型
- C004 ep_ratio exp=1.30 + alpha_surv=0.27 poor + incr_ic=-0.0024 → "strong-mono + strong-ls_t but library reducer" 第 5 次复现 (b042 C005 / b043 C005-C006 / b045 C006 / b055 C002 / 本批 C004)

**Incremental_ic 一览**（库增值真实性最关键指标）：
- ⏸ C001 = **+0.0085** (库增值, 唯一)
- ❌ C002 = N/A (hard_gate fail)
- ❌ C003 = -0.006, C004 = -0.0024, C005 = N/A (hard_gate fail), C006 ≈ +0.001
- **5/6 incremental_ic ≤ 0 或不适用**——本批延续 batch_055 P005 RHS basis 共振饱和律的动态性 (b055: 5/6 ≤ 0)。但 C001 incr=+0.0085 > 0 **打破"全负"模式**，表明在 (O-L)/(H-L) atom + amount/volume RHS 这条具体路径上库增值仍真实——open lower-shadow position 维度尚未饱和。

**MT 预算推进**：cumulative 288 → 294；direction 12 → 18；bucket high → search_adjusted medium。range_structure direction 在本批后 round=4, admits=1, reserves=1, status: `productive` 保持。

**ls_t IS/OOS 翻号 / 衰减**（Validation regime stability）：
- C001: IS+5.52 / OOS+2.51 (衰减 0.45，但同号且 OOS 仍 moderate)
- C002: IS+3.35 / OOS-2.13 (**翻号** + hard_gate fail)
- C003: IS-1.67 / OOS-0.86 (大幅衰减 0.51 + mono 崩塌)
- C004: IS+5.40 / OOS+4.62 (**OOS 增强 ratio 0.85**, 但 incr_ic 负 — strong-but-reducer)
- C005: IS-3.02 / OOS-3.78 (OOS 反向增强 + ic_oos 量级不足)
- C006: IS+2.56 / OOS+0.90 (大幅衰减 0.35 + ls 信号 weak)

C001 是**唯一同号且 OOS 仍 moderate** 的候选，配合 incr_ic+ + cum_mdd=-4.06 + ic_by_year U-shape 近 3 年同号加强 — 真实 alpha 嫌疑高于其他 5 个，但 alpha_survival=0.24 < threshold 0.40 阻止 admit → reserve。

## Thread 进展

> [!note]+ T003 [[directions/range_structure#T003]] — `[◉ ACTIVE]`
> **本批结果 (round 1 of T003)**：T003 假设"intraday position dispersion family 沿 C005 衍生"在本批 6 候选首轮**部分验证、部分证伪**。验证：C001 (Std((O-L)/(H-L), 20) × Mean(amount/volume, 60)) reserve，open-anchored lower-shadow position dispersion atom 拿到 incr_ic=+0.0085 + cum_mdd=-4.06 + 9 年 U-shape 同号 — 证实 family 在 open-anchored 维度可扩展。证伪：C003 (return-per-range) / C004 (overnight-gap-per-range) / C006 (composite midpoint) 三种 numerator 全部 reject，证明并非所有 LHS atom 变体都能逃脱 vol_20d；特别 C002/C005 双 hard_gate fail 表明 RHS basis (pe/pb 60d ROE proxy / turnover/pb 60d composite) 即使设计纪律到位仍可能在 csi1000 IS/OOS 完全反转。
>
> **Evidence trail (本批新增)**:
> - [[batches/batch_056/candidates/C001|batch_056 C001]] Sub(CsRank(Std((O-L)/(H-L),20)), CsRank(Mean(amount/volume,60))) — ic_oos=+0.021 mono=+1.0 cum_mdd=-4.06 incr=+0.0085 max_corr=0.50@F019 alpha_surv=0.24 → **reserve**
> - [[batches/batch_056/candidates/C002|batch_056 C002]] Sub(CsRank(Std((H-O)/(H-L),20)), CsRank(Mean(pe/pb,60))) — hard_gate fail (sign_flip + oos_decay=-4.34) → **reject**
> - [[batches/batch_056/candidates/C003|batch_056 C003]] Sub(CsRank(Std((C-prev_C)/(H-L),20)), CsRank(Mean(amount/(close*volume),60))) — mono collapse -0.90→-0.10 + incr=-0.006 + vol_20d=47.2 + max_corr=0.65@F014 → **reject**
> - [[batches/batch_056/candidates/C004|batch_056 C004]] Sub(CsRank(Std((O-prev_C)/(H-L),20)), CsRank(Mean(pe/ps,60))) — ls_t=4.62 + mono=+1.0 但 incr=-0.0024 + alpha_surv=0.27 (library reducer 第 5 次复现) → **reject**
> - [[batches/batch_056/candidates/C005|batch_056 C005]] Sub(CsRank(Std((H-prev_C)/(H-L),20)), CsRank(Mean(turnover/pb,60))) — hard_gate fail (ic_oos=-0.0042 < 0.008) → **reject**
> - [[batches/batch_056/candidates/C006|batch_056 C006]] Sub(CsRank(Std(((C+O)-(H+L))/(H-L),20)), CsRank(Mean(amount/market_cap,60))) — ic_oos=+0.025 表面 strong 但 alpha_surv=0.0725 极端 + ls_t=0.90 weak + vol_20d=30.67 → **reject** (vol_20d IC 假象典型)
>
> **下一步**：T003 thread 仍 ACTIVE，但应在 C001 reserve 真错杀诊断后再决定 round 2 方向。如 C001 是真实可 admit 信号 (诊断 alpha_survival=0.24 是否 vol_20d Barra orthogonalize 后改善)，则 round 2 沿 (O-L)/(H-L) atom 衍生其它 long-window scale-free RHS；如 C001 是 vol_20d 吸收伪 alpha (与 C006 同模式)，则 T003 sub-path "open-anchored position × VWAP magnitude" 封闭，转 (C-L)/(H-L) Std lower-shadow-close-position 等其它 anchor。

## 方向级反思

**range_structure direction 在 batch_056 round 4 后**：admit=0 / reserve=1 / reject=5；累计 admits=1 (F021 from b055 C005), reserves=2 (b043 C003 + 本批 C001), 已封闭路径增加到 5+ atom variants。本批揭示几个关键动态：

1. **rank-diff geometry library reducer 第 5 次复现** (b042 C005 / b043 C005-C006 / b045 C006 / b055 C002 / 本批 C004)：mono_oos=+1.0 + ls_t_oos=4.62 strong 但 incr_ic=-0.0024 + alpha_surv=0.27——"strong-but-negative-incr"陷阱第 5 次独立确认，应升格 lessons.md 的 Promising Patterns 反例段。该模式的判别要件已稳定：mono_oos≥0.9 + |ls_t_oos|≥3.0 + incr_ic<0 + alpha_surv<0.30。

2. **C006 alpha_survival 极端 poor (0.0725)** + ic_oos 表面 strong (+0.025) 揭示"vol_20d IC 假象"诊断要件的细化：当 alpha_survival << 0.10 (而非接近 threshold 0.40) 时，IC 几乎完全由 vol_20d + turnover_20d + str_1m 三大 style 解释——本批 vol_20d_exposure=30.67 + style_r²=0.21 仅 borderline，但 alpha_survival 跌至 0.0725——表明 style_r² 单一指标不充分（C006 style_r² 仅 borderline 但 alpha 全被 style 占走），alpha_survival 是更敏感的"残余 alpha 真实性"指标。

3. **C001 reserve 是否真错杀 (calibration trigger 候选)**：C001 满足 6 项 alpha-side 健康指标 (ic_oos=0.021 strong / mono_oos=+1.0 完美 / sign_consistency=1.0 / cum_mdd=-4.06 极浅 / incr_ic=+0.0085 库增值 / ic_by_year U-shape 近 3 年同号加强)；但 alpha_survival=0.24 < threshold 0.40 (CP04 poor) + style_r²=0.17 边界 + ICIR=0.17 weak (CP03 borderline) + max_lib_corr=0.50 medium 阻止 admit。**诊断**：dominant_style=vol_20d (exp=7.96) 在本 family 是最低 vol_20d exp，但 alpha_survival 仍仅 0.24——可能是真实"vol_20d 残余 alpha"被吞噬，或库重叠 (与 F019 max_corr=0.50) 把残余信号也分走。**建议**：等待 round 2 沿 C001 atom 衍生 1-2 个独立 RHS 候选 (避开 amount/volume，试 H/L 60d 几何 ratio 等)，再判断 C001 是否系统性错杀。

4. **下一步建议**:
   - **优先**：sub-path A — 沿 C001 (O-L)/(H-L) atom 衍生 × 不同 long-window scale-free RHS (H/L 60d 几何 / 其它 turnover-orthogonal 长窗 ratio)，验证 open lower-shadow position 维度是否可继续扩展
   - **优先**：sub-path B — (C-L)/(H-L) Std (lower-shadow-close-position) × C001 同款 long-window scale-free RHS，对比 close-anchored vs open-anchored 在 lower-shadow 几何上的差异
   - **避免**：daily return / overnight gap as numerator (b056 C003/C004/C005 教训)；composite midpoint deviation (b056 C006 教训)；pe/pb / pe/ps / turnover/pb 60d 类 fundamental 复合 RHS (b056 C002/C004/C005 三连 reject)
   - **TsKurt 路径**：operators.py:428 bug 仍阻塞——可考虑 Python escape hatch 路径在 sub-path A/B 完成后启动

5. **status 调整**：`status: productive` 保持（C001 reserve 维持 family 可扩展嫌疑 + 库增值数据点）；`priority: medium` 保持（admit=0 但 reserve 数据点真实，未达 saturated 触发）。

若 round 5 沿 C001/C005 衍生路径仍 0 admit + 80%+ candidate incremental_ic ≤ 0 → `productive → saturated`。
