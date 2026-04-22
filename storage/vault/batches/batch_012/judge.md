---
batch_id: batch_012
direction: barra_residual_alpha
judged_at: 2026-04-19T14:50:00Z
candidates:
  - {candidate_id: C001, verdict: admit, factor_name: barra_residual_return}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reserve}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
batch_summary: {total: 5, admit: 1, reserve: 1, reject: 3}
admit_count: 1
reject_count: 3
reserve_count: 1
candidate_count: 5
mt_bucket: low
---

# batch_012 Judge Summary

> [!abstract]+ batch_012 · [[directions/barra_residual_alpha]] · 5 candidates
> ✅ **admit=1** (C001→F{next}) · ⏸ **reserve=1** (C003) · ❌ **reject=3** (C002 C004 C005)
> **核心发现**: Barra residual alpha 方向首批验证假设成立——C001 Barra_residual_IC=0.033 > raw IC=0.024，alpha_surv=1.35；但 C003/C004/C005 均因 IC/OOS 不足被截断；C002 因 sign_flip+decay 双杀拒绝
> **MT Budget**: cumulative 67 → **68** · direction 0 → **1** · bucket `low`（上界）· 本批 low=1 / med=0 / high=0

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ✅ admit | 🟢·🟢·🟡·🟢·🟡 | ICIR=0.293 ls_t=7.34 | Barra residual 方向首个 admit； Barra_residual_IC=0.033 > raw IC=0.024，验证假设 | [[batches/batch_012/candidates/C001]] · [[factors/F004]] |
| C002 | ❌ reject | hard_gate | sign_flip+oos_decay | sign_flip+decay 双杀；IS→OOS alpha 逆转，不稳健 | [[batches/batch_012/candidates/C002]] |
| C003 | ⏸ reserve | 🟢·🟡·🔴·🟡·🟡 | ICIR=0.072 ls_t=3.44 | Barra residual 方向验证假设成立；但 style_r²=0.289（poor）、vol_20d exposure=15.6 严重耦合；reserve 等待 C001 对比 | [[batches/batch_012/candidates/C003]] |
| C004 | ❌ reject | hard_gate | ic_oos=0.007 < 0.008 | 5d rolling mean residual IC 太弱，低于阈值 | [[batches/batch_012/candidates/C004]] |
| C005 | ❌ reject | hard_gate | ic_oos=-0.0035 < 0.008 | 20d momentum residual IC 为负，方向反转 | [[batches/batch_012/candidates/C005]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🟠 边际 · 🔴 阻断档（misaligned/weak/poor/high/unstable）· `hard_gate` reject 该列写 `hard_gate` 不填色。整列飘红 = 方向级警示（对比本批 vs 历史快速诊断）。

## 跨候选对比

- **Barra residual 机制验证**：C001 Barra_residual_IC=0.033 > raw IC=0.024，alpha_surv=1.35 → Barra 风格因子吸收后残差仍有独立 alpha，假设验证成立
- **style 耦合问题**：C003/C004/C005 均显示 dominant_style=vol_20d，exposure 8.7~15.6；C001 相对较轻（vol_20d exposure=4.4，style_r²=0.038 clean）
- **MT 预算**：direction_candidates 0 → 1，bucket=low，本批仅 C001 消耗 MT
- **正交性**：C001 incremental_ic=0.032 max_corr=0.15（F002），全新机制空间

## Thread 进展

> [!success]+ T001 [[directions/barra_residual_alpha#T001]] — `[✓ ANSWERED batch_012]`
> admit C001。Barra residual alpha = Regress(Returns ~ Barra styles) → Residuals 的 IC=0.024（ICIR=0.293）， Barra_residual_IC=0.033 > raw IC，证明残差携带独立 alpha

> [!note]+ T002 [[directions/barra_residual_alpha#T002]] — `[◉ ACTIVE]`
> C001 incremental_ic=0.032 > 0，max_corr=0.15（F002），证明 Barra residual 与现有因子正交

> [!note]- T003 [[directions/barra_residual_alpha#T003]] — `[◉ ACTIVE]`（本批无推进）

## 方向级反思

Barra residual alpha 假设验证成功：C001 Barra_residual_IC=0.033 > raw IC=0.024，证明风格因子吸收后仍有独立 alpha。

下轮建议：
1. **正向候选**：C003 虽 reserve，但其 Barra_residual_IC=0.033 与 C001 相当——若下一批改善 style_r²（当前 0.289 > 0.25 threshold），可考虑 admit
2. **机制扩展**：尝试 Barra residual + volume 交互（类似 value_liquidity_interaction）
3. **监控 2021 后衰减**：ic_by_year 显示 2021-2023 edge 衰减（0.026→0.010），需持续跟踪

若下一轮 admit 率仍 < 20%，方向 status: productive → saturated。
