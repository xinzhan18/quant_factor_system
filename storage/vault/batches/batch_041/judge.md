---
batch_id: batch_041
direction: stochastic_position
judged_at: 2026-04-24T01:20:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reserve}
  - {candidate_id: C005, verdict: reserve}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 2, reject: 4}
admit_count: 0
reject_count: 4
reserve_count: 2
candidate_count: 6
mt_bucket: medium
---

# batch_041 Judge Summary

> [!abstract]+ batch_041 · [[directions/stochastic_position]] · 6 candidates
> ❌ **reject=4** (C001/C002/C003/C006) · ⏸ **reserve=2** (C004, C005) · ✅ **admit=0**
> **核心发现**: 整个 stochastic %K 家族在 csi1000 OOS 遭遇 **rank-order 系统性崩塌**（5/6 候选 mono_oos ≤ 0.40，3/6 翻号）；所有 6 候选 dominant_style=`vol_20d` 且 exposure 8.7–16.5，说明 %K 在本样本本质是 vol_20d 代理而非独立 alpha。
> **MT Budget**: cumulative 204 → **210** · direction 0 → **6** · bucket `medium`（search_adjusted 0.48–0.60）· 本批 low=0 / med=6 / high=0

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🔴·🔴·🟠·🔴·🟠 | mono 0.90→0.10, ls_t_oos=0.15, incr_ic=**-0.014** | 经典 %K 20d 被 OHLC shape 簇（F006-F009）覆盖；负库增值 | [[batches/batch_041/candidates/C001]] |
| C002 | ❌ reject | 🟠·🔴·🔴·🟡·🟠 | mono 0.6→**-0.4**, ls_t_oos=-0.20, cum_mdd=-55.9 | 60d 长窗口跨 regime，Q1/Q5 双尾塌陷、奇异结构 | [[batches/batch_041/candidates/C002]] |
| C003 | ❌ reject | 🟠·🔴·🔴·🟡·🟠 | mono 0.7→0.0, Q2 独高非单调, incr_ic=**-0.021** | TsRank 20d 与反转簇 0.49 冗余；OOS"中间独大"奇异结构 | [[batches/batch_041/candidates/C003]] |
| C004 | ⏸ reserve | 🟠·🔴·🟠·🟡·🟠 | mono 0.7→**-0.3**, ls_t_oos=-0.72, residual_icir=**-0.399** | 残差 ICIR 本批最强，但 mono 翻号 + cum_mdd=-62.6；留作 orthogonalize by vol_20d 再测 | [[batches/batch_041/candidates/C004]] |
| C005 | ⏸ reserve | 🟠·🔴·🔴·🟡·🟠 | mono **1.00→0.40** (本批最优), decay=1.02, ls_t_oos=1.09 | close-only 边界 vs C001 low/high 边界：略胜；但 vol_20d exposure=16.5 压倒性 | [[batches/batch_041/candidates/C005]] |
| C006 | ❌ reject | 🟢·🔴·🟠·🟡·🟠 | mono 0.9→**-0.4**, ls_sharpe 2.13→-0.60 符号翻盘 | 5d 平滑反而恶化（vs C001 的 0.10）；Barra 吸收 38% | [[batches/batch_041/candidates/C006]] |

## 跨候选对比

- **Style 共因**: 6/6 候选 `dominant_style_exposure=vol_20d`，exposure 8.7–16.5，`style_crowding_risk=high`——本方向核心载体是波动率，不是"rolling price position"。与 [[lessons#Data Facts]] 对 vol_20d 结构吸收律的观察一致。
- **Rank-order 系统性崩塌**: IS mono 平均 0.80，OOS mono 平均 -0.10——**5/6 候选 mono 符号翻盘或崩塌**。这是 rank-order 机制证伪的硬证据，不是个案。
- **Incremental_ic 集体为负**: 6 候选 incremental_ic 全部在 -0.012 到 -0.022（无一正值），说明本方向加入库**等于减值**。
- **Cluster 同质化**: 6 候选互相 IS 相关 ~0.7+（未显式计算，但 all_correlations 对 F006-F009 的负相关模式高度相似 [-0.28, -0.46]），且都指向反转簇——说明 %K/TsRank 这类"位置"指标本质与 OHLC shape 同空间。
- **20d 优于 60d**: C001 vs C002, C003 vs C004 两对比较，20d 窗口 OOS 指标略好但都不达标；长窗口稀释 regime 敏感度反而更差。
- **MT 预算推进**: direction_candidates 0 → 6（本方向首批）；cumulative 204 → 210；bucket 仍在 medium 上界。

## Thread 进展

> [!failure]+ T001 [[directions/stochastic_position#T001]] — `[✗ DISPROVEN batch_041]`
> 4 候选（C001 20d low/high, C002 60d low/high, C005 20d close-only, C006 5d 平滑）覆盖经典 %K 形式。ls_t_oos 均 < 2（-0.83 到 1.09），mono_oos 均 ≤ 0.40，incremental_ic 全部为负。回答：**"(close - TsMin(N)) / (TsMax(N) - TsMin(N)) 不携带独立 alpha"**，在 csi1000 样本下被 vol_20d 吞噬并在 OHLC shape 簇内冗余。

> [!failure]+ T002 [[directions/stochastic_position#T002]] — `[✗ DISPROVEN batch_041]`
> 2 候选（C003 20d, C004 60d）覆盖 TsRank($close, N) 形式。mono_oos 同样崩塌（0.0 / -0.3），与 F007 相关 0.37–0.49。回答：**"TsRank 与 %K 机制等价，两者共享被 vol_20d + OHLC shape 簇吸收的宿命"**，非正交。

> [!note]+ T003 [[directions/stochastic_position#T003]] 🆕 — `[◉ ACTIVE]`
> 是否存在"对 vol_20d orthogonalized 的 %K 残差"能在 csi1000 OOS 恢复 rank-order？候选 C004 residual_ic=-0.0183、residual_icir=-0.399（本批最强）是潜在入口，但需要 Python 端先实现 `orthogonalize` 算子或 barra_residual_signal 再挖。优先级低——C005 残差 alpha_surv=1.16 暗示有但 raw 已 reserve 即可。

## 方向级反思

本方向**首批即遭方向级证伪**。T001/T002 两条主 thread 同时 DISPROVEN，剩余 T003（orthogonalization salvage）需要工具链支持，短期不可达。

- `incremental_ic` 中位数 **-0.017**——本方向加入库**系统性减值**，远劣于近期 batch_040 vwap_proxy_signals 的正值（ls_t=3.89）。
- 与 [[directions/intraday_price_formation]] saturated 结论一致：单日 `(close-low)/(high-low)` 已 mono_sign_flip；本方向多日 rolling 是区别点，但区别**仅在数学形式**，经济本质仍是"价格位置被 vol 吞噬"——**日内与跨日的 price position 都失效**，升格为方向族级 lessons。
- 保留 C004/C005 为 reserve 是为了留"residual 路径"种子（T003），若下轮引入 vol_20d orthogonalize 工具可再测。
- **状态转换**: `status: exploring → saturated`（无 admit 首批 + 两条 thread 同时 DISPROVEN + 核心机制被 vol_20d 吞噬）。
- **下一步**: 切换方向，不建议在 stochastic_position 投新 thread。

**阈值校准侦测**: 无触发（batch_040 有 admit 未形成零-admit 3 连；reserve 均不满足库空间独立条件 `max_lib_corr<0.30 + incremental_ic>0.010`；无悖论组合出现——所有候选 mono 崩塌 + vol 吞噬是一致信号）。
