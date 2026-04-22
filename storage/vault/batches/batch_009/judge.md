---
batch_id: batch_009
direction: value_liquidity_interaction
judged_at: 2026-04-19T21:10:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reserve}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
  - {candidate_id: C007, verdict: reserve}
batch_summary: {total: 7, admit: 0, reserve: 2, reject: 5}
admit_count: 0
reject_count: 5
reserve_count: 2
candidate_count: 7
mt_bucket: medium
---

# batch_009 Judge Summary

> [!abstract]+ batch_009 · [[directions/value_liquidity_interaction]] · 7 candidates
> ❌ **admit=0** · ⏸ **reserve=2** (C003 C007) · ❌ **reject=5** (C001 C002 C004 C005 C006)
> **核心发现**: 4 个 self-normalized rate × turnover_rate_of_change 候选(C001/C004/C006) 全部 sign_flip + regime collapse；C005(PE+PB rate 等权平均)突破 dom=str_1m(历史首次)但 incremental_ic=-0.033(库 reducer) reject；C007(turnover_rank vs PE rank) ls_t=-2.43 最强 PnL 但 vol_20d=18.8 极端暴露。
> **MT Budget**: cumulative 44 → **51** · direction 15 → **22** · bucket `medium` · 本批 low=0 / med=2 / high=0

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | sign_flip + ic_oos_too_low + oos_decay=-1.3 | PE_rate 60d self-norm — self-normalization 放大 regime 漂移 | [[batches/batch_009/candidates/C001]] |
| C002 | ❌ reject | hard_gate | mono_sign_flip IS=-0.60 OOS=0.90 | CsRank(PE)-CsRank(PB) rank-diff 撞 Asymmetric shift（rate vs level 不兼容） | [[batches/batch_009/candidates/C002]] |
| C003 | ⏸ reserve | 🟢·🟡·🔴·🟢·🟠 | ic_oos=+0.0165 icir=+0.166 ls_t=0.47 | 9年全正+cum_dd=-1.54(方向最浅)+max_corr=0.112(极干净) 但 ls_t=0.47 弱 + Q3 非单调 | [[batches/batch_009/candidates/C003]] |
| C004 | ❌ reject | hard_gate | sign_flip + ic_oos_too_low + oos_decay=-16.9 | PE_rate / turnover_rate_of_change — ratio 结构放大 sign 不稳定性 | [[batches/batch_009/candidates/C004]] |
| C005 | ❌ reject | 🟢·🟡·🔴·🔴·🟠 | icir=-0.194 ls_t=-1.25 alpha_surv=0.883 **dom=str_1m** | **历史首次 dom=str_1m** 但 incremental_ic=-0.033(库 reducer) + cum_mdd=-70 定性 reject | [[batches/batch_009/candidates/C005]] |
| C006 | ❌ reject | hard_gate | sign_flip + ic_oos_too_low + oos_decay=-32.5 | PB_rate / turnover_rate_of_change — 同样 ratio 结构崩溃 | [[batches/batch_009/candidates/C006]] |
| C007 | ⏸ reserve | 🟢·🟢·🟡·🟡·🔴 | icir=-0.503 ls_t=-2.43 mono=-1.0 | 方向 PnL 最强(ls_t=-2.43)+完美 rank-order(mono=-1.0) 但 vol_20d=18.8(极端)+incr_ic=-0.035(库冲突) | [[batches/batch_009/candidates/C007]] |

## 跨候选对比

- **Self-normalized rate × turnover 结构全部失败**：C001/C004/C006 三个 `Div(rate, turnover_rate_of_change)` 候选全部 sign_flip + oos_decay collapse——ratio 结构放大 regime 不稳定性，self-normalization 不解决跨期漂移
- **str_1m breakthrough**: C005 是方向 22 候选中**首个 dominant_style=str_1m**（alpha_surv=0.883），但 incremental_ic=-0.033（库 reducer）定性 reject—— Barra 层干净但组合负增值
- **C003 vs C007 镜像对比**：C003 库空间极干净(incr_ic=+0.019, max_corr=0.112)但 PnL 极弱(ls_t=0.47)；C007 PnL 极强(ls_t=-2.43)但库冲突(incr_ic=-0.035)——两者互补但无法同时 admit
- **MT 预算**：direction_candidates 15→22；reserve=2 落在 `medium` bucket

## Thread 进展

> [!note]+ T001 [[directions/value_liquidity_interaction#T001]] — `[◉ ACTIVE]`
> C002 rank-diff(PE-PB) mono_sign_flip reject；C007(turnover_rank vs PE) reserve(ls_t=-2.43 最强)。**乘法/除法/fund-rank 结构全部证伪或 reserve**。T001 DSL 路径实质封闭。

> [!note]- T003 [[directions/value_liquidity_interaction#T003]] — `[◉ ACTIVE]`（本批无新进展）

> [!note]+ T006 [[directions/value_liquidity_interaction#T006]] — `[◉ ACTIVE]`（本批无新进展）
> C005(PE+PB 等权平均) dom=str_1m breakthrough + alpha_surv=0.883，但 incremental_ic=-0.033 库 reducer reject。**rate 自归一化三点通用性在 str_1m 层确立，但 PnL 层全部失败**。

> [!note]+ T007 [[directions/value_liquidity_interaction#T007]] 🆕 — `[◉ ACTIVE]`
> 跨基本面 rank-diff 新方向：C002 PE-PB rank-diff 失败(非对称 shift)，C003 PE_rate-PB_rate rank-diff reserve(IC 强但 ls_t 极弱)。**跨基本面 rank-diff 路径有效但 PnL兑现需要 Barra residual**。

## 方向级反思

**方向第 5 批零 admit**。22 候选后 DSL 空间实质性穷尽——6 种结构化路径(乘法/除法/rate/合成/rank-diff/self-norm)全覆盖。

**两个方向级发现**：
1. **C005 dom=str_1m breakthrough**：方向历史首次非 vol_20d dominant——证明"基本面字段 × 某种结构"可以跳出 Barra 天花板。但 incremental_ic=-0.033 与库冲突。
2. **C007 ls_t=-2.43**：方向 22 候选 PnL 最强，但 vol_20d=18.8 极端暴露。

**悖论结构确立**：C003(库干净但 PnL 弱 ls_t=0.47) vs C007(PnL 强但库冲突)—— Barra orthogonality 和 PnL 在 DSL 空间互斥。

**下轮唯一出口：Python Barra residual**。C003(incr_ic=+0.019 库增值真实)或 C007(ls_t=-2.43 最强 PnL)残差化验证独立 alpha。若 Python 残差版仍无 admit，方向转 `saturated`，开第 4 方向。

若下一批 admit=0，方向 `productive → saturated`。
