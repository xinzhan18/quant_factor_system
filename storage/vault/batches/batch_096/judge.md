---
batch_id: batch_096
direction: rank_diff_liquidity_microstructure
judged_at: 2026-05-15T23:25:00Z
candidates:
  - {candidate_id: C001, verdict: reserve}
  - {candidate_id: C002, verdict: reserve}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reserve}
batch_summary: {total: 6, admit: 0, reserve: 3, reject: 3}
admit_count: 0
reject_count: 3
reserve_count: 3
candidate_count: 6
mt_bucket: medium
---

# batch_096 Judge Summary

> [!abstract]+ batch_096 · [[directions/rank_diff_liquidity_microstructure]] · 6 candidates
> ✅ **admit=0** · ⏸ **reserve=3** (C001/C002/C006) · ❌ **reject=3** (C003/C004/C005)
> **核心发现**: DSL-only revival path (Python residualize 不可用, 降级 manifest 已标注) 在 T005 smoothing wraps + T001 sub-axis 验证：**ls_t admit floor 3.0 瓶颈在 cross-section dispersion 不在 time-series noise**——Mean/EMA wrap 不能 boost ls_t（C001 -2.46 / C002 -2.52，与 b095/C006 5d Mean -2.50 几乎一致）；T001 1.5:1 ratio (C006) 实证"窗口比窄化降低 style 但压制 ls_t" trade-off。EMA wrap (C002) 是 reserve cluster 最强 alpha_surv (0.49)；60/40 (C006) 是最低 style_r² (0.06)。
> **MT Budget**: cumulative 534 → **540** · direction 6 → **12** · bucket `medium`（上界，search_adjusted 0.44-0.51）· 本批 low=0 / medium=3 / high=0
> **Python residualize 降级**: 本批 6 候选全 DSL，因 `src/research/daily_templates/registry.py` 仅注册 `quantile_split_spread` 和 `conditional_rolling_mean` 两个模板，**无 residualize 模板**。manifest batch_goal 显式标注 "degrading to DSL-only revival paths"。

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ⏸ reserve | 🟢·🟡·🟡·🟢·🟢 | ls_t=-2.46 alpha_surv=0.36 mc=0.19 | 10d Mean wrap 比 b095/C006 5d 没 boost ls_t——证 smoothing 深度不破瓶颈 | [[batches/batch_096/candidates/C001]] |
| C002 | ⏸ reserve | 🟢·🟡·🟢·🟢·🟢 | ls_t=-2.52 alpha_surv=**0.49** mc=0.19 | EMA 衰减加权升 alpha_surv +36% 但 ls_t 几乎未动——operator type 调节限制在 risk-cleanness 域 | [[batches/batch_096/candidates/C002]] |
| C003 | ❌ reject | 🟡·🔴·🟡·🟢·🟡 | ls_t=-0.75 alpha_surv=0.94 vol=34 | $turnover_rate LHS swap 失败：ls_t weak + alpha_surv 临 P030 边缘 + Q1-Q5 中段非线性 + 2015 sign-flip | [[batches/batch_096/candidates/C003]] |
| C004 | ❌ reject | hard_gate | train_ic≈0 oos_decay=-278 | 120/60 sub-axis 长窗稀释 train period——证 b091 "window-sweep 长窗衰减"律 | [[batches/batch_096/candidates/C004]] |
| C005 | ❌ reject | hard_gate | sign_flip+ic_oos<0.008 | Slope-on-rank-diff sub-axis disproven——rank space 不支持稳定 derivative 提取（升格 candidate）| [[batches/batch_096/candidates/C005]] |
| C006 | ⏸ reserve | 🟢·🟡·🟢·🟢·🟢 | ls_t=-2.13 style_r²=**0.06** mc=0.14 | 1.5:1 ratio 最干净 (style/corr 本批最低) 但最弱 ls_t——窗口窄化 trade-off | [[batches/batch_096/candidates/C006]] |

**档位编码**：🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档 · `hard_gate` reject 不填色。

## 跨候选对比

**Style 聚合**：4 个 hard_gate 过的候选 dominant_style **全是 vol_20d**——本方向 rank-diff axis 与 vol_20d basis 在 amount/num_trades family 存在系统性 partial overlap。Vol_20d exposure 阶梯：C006 12.53 < C001 17.74 < C002 18.65 < C003 34.01。**窗口比窄化 (C006 1.5:1) 显著降低 vol_20d exposure**——可能是未来 T001 thread 探索方向。

**相关度 cluster**：4 个过 hard_gate 候选互相 max_corr 都在 0.14-0.19（独立），nearest 全是 F018 (CsRank-diff overnight×amount)，证 TsRank-diff vs CsRank-diff 几何独立。C003 nearest F022 (close-position 类) 异于其它——LHS 字段 $turnover_rate 让 candidate 落到不同 cluster。

**MT 预算推进**：cumulative 534 → 540；direction 6 → 12 (翻倍)；bucket 仍 medium 上界，search_adjusted 全候选在 0.44-0.51。direction 内 MT 预算压力开始显著：累计 12 候选 / 0 admit。

**核心 trade-off 现象**（本批最有价值发现）：

| 候选 | smoothing op | alpha_surv | style_r² | ls_t | 解读 |
|---|---|---|---|---|---|
| b091/C004 | none | 0.36 | ? | -2.20 | baseline |
| b095/C006 | Mean(·,5) | ? | ? | -2.50 | 5d 平滑 |
| C001 | Mean(·,10) | 0.36 | 0.11 | -2.46 | 10d 平滑——alpha_surv 不变 |
| C002 | EMA(·,7) | **0.49** | 0.12 | -2.52 | EMA 加权——alpha_surv +36% 但 ls_t 几乎不动 |
| C006 | (no smooth) 60/40 | **0.51** | **0.06** | -2.13 | 窗口窄化——style+corr 都最低但 ls_t 也最低 |

**两条独立路径都不能 boost ls_t**：
1. **Smoothing wraps** (C001/C002): alpha_surv 可调，ls_t 不动 → smoothing 域操作仅影响 risk cleanness
2. **Window ratio narrowing** (C006): style+corr 全部降低但 ls_t 同时压制 → window 比影响 dispersion 量级

**结论**：ls_t < 3.0 admit floor 的瓶颈是 **rank-diff axis 本身的 cross-section dispersion 上限** —— smoothing 不动 dispersion；window 窄化降 dispersion 但同时降 signal magnitude → 永远 trade-off 不可达 ls_t ≥ 3.0。

## Thread 进展

> [!note]+ T001 [[directions/rank_diff_liquidity_microstructure#T001]] — `[◉ ACTIVE]`
> 本批两候选 C004 (120/60, 2:1, hard_gate fail) + C006 (60/40, 1.5:1, reserve)。
> - 120/60 实证"等比 2:1 长窗"假设 disproven（IS train period 边界效应 + cross-section spread 零）
> - 60/40 实证"窗口窄化降 dispersion"——确认 alpha_surv↑+style_r²↓ trade-off ls_t↓
> - T001 sub-axis exhausted: 60/20 (b091), 60/10 (b095/C001), 90/30 (b095/C002), 120/60 (本批 C004 fail), 60/40 (本批 C006)——**T001 接近 saturated**
>
> **Next probes**: T001 几乎穷尽；下轮考虑 CLOSE T001 转 saturated。

> [!note]+ T005 [[directions/rank_diff_liquidity_microstructure#T005]] — `[◉ ACTIVE]`
> 本批三候选 C001 (10d Mean) + C002 (7d EMA) + C005 (Slope, hard_gate fail)。
> - C001 实证"Mean wrap 深度调节"——5d→10d 不 boost ls_t
> - C002 实证"EMA vs Mean operator type"——升 alpha_surv +36% 但 ls_t 仍不动
> - C005 实证"Slope/derivative wrap"——rank space ordinal 不支持稳定 derivative，升格 candidate
> - T005 已确认机制空间：smoothing-type wraps (Mean/EMA) 仅影响 risk cleanness，**不能突破 ls_t 瓶颈**
>
> **Next probes**: T005 smoothing-type wraps 已 explored；剩 (a) 非 smoothing wrap (e.g., Quantile wrap, CsRank with Python custom op fix per b095/T005 note); (b) close T005 转 saturated。

> [!failure]+ T006 [[directions/rank_diff_liquidity_microstructure#T006]] 🆕 — `[✗ DISPROVEN batch_096]`
> 本批新建 thread "rank-diff axis LHS field swap"——C003 ($turnover_rate) disproven。LHS 切到 dim-less rate field 实证 cross-section dispersion 不显著 (ls_t=-0.75)，Q1-Q5 中段非线性 + edge 2015 sign-flip drift。结合 T002 disproven (RHS field swap) 与 T003 disproven (raw atom)，**rank-diff axis 在 amount/num_trades family 之外的 LHS swap 路径基本封闭**。
>
> **Lessons-promotion candidate**: rank-diff axis 限定 ratio LHS = `numerator/denominator` where both numerator and denominator are 微观 flow fields ($amount, $num_trades, $volume) — 单一 rate/level field LHS 不构成有效 cross-section spread。

## 方向级反思

**本方向 edge 状态**：

- **rank-diff axis amount/num_trades family 实证 PASS 域已穷尽**：6 子轴（T001 4 个窗口比 + T005 3 个 wrappers + T002/T003/T006 disproven） — 12 候选累计 0 admit。
- **ls_t boost 路径全部 disproven on DSL**：T005 smoothing (Mean/EMA/无) 都不动 ls_t；T001 window ratio narrowing 降 ls_t；T006 LHS swap weak ls_t；T002 RHS swap hard_gate fail；T003 raw atom hard_gate fail；T004 HP-2nd-order hard_gate fail。
- **唯一未测：Python OLS cross-section residualize**（本批因 daily_templates registry 无 residualize 模板而降级）——这是 b095 next_hint 唯一未走完的复活路径。

**Reserve 池累计**（rank-diff axis cluster, ls_t∈[-2.13,-2.60]）：

| Candidate | Form | alpha_surv | style_r² | ls_t | max_corr |
|---|---|---|---|---|---|
| b091/C004 | 60/20 base | 0.862 | ? | -2.20 | 0.18 |
| b095/C001 | 60/10 | 0.77 | ? | -2.60 | 0.18 |
| b095/C002 | 90/30 | 0.68 | ? | -2.03 | 0.18 |
| b095/C006 | Mean5 wrap | 0.50 | ? | -2.50 | ? |
| b096/C001 | Mean10 wrap | 0.36 | 0.11 | -2.46 | 0.19 |
| b096/C002 | EMA7 wrap | **0.49** | 0.12 | -2.52 | 0.19 |
| b096/C006 | 60/40 (1.5:1) | **0.51** | **0.06** | -2.13 | **0.14** |

7 candidates in reserve pool — 库空间独立 (max_corr ≤ 0.19) + 错杀侦测 4 件套部分满足 (3-3.5/4) + admit floor ls_t 3.0 不破。

**下轮建议**：

1. **唯一未走路径**：Python OLS cross-section residualize on (F012 Amihud + F024 trade-density + vol_20d) —— b095 next_hint 原方案，本批因系统约束降级。需先在 src/data/primitive 或 src/research/daily_templates 增加 residualize 模板（开发任务），才能验证假设。
2. **方向 status 决策**：本方向 12 候选 0 admit + active threads T001/T005/T006 三个全部 partial-disproven 或 exhausted → **建议 status: exploring → saturated**（待 calibration trigger 处理）。
3. **calibration_trigger 已触发**：本批继续推 zero_admit_streak 7→8→9（最近 3 批 admit=0 + 累计 ≥ 1 reserve 满足"库空间独立"独立性条件）→ orchestrator 应 dispatch calibration 流程，可能复活 1-2 个 reserve 池候选（C002 EMA 或 C006 60/40 是首选）。

**核心结论**：rank-diff axis on amount/num_trades family **edge 真实存在** (consistent IC sign + |IC|>0.014 + mono OOS=-0.9~-1.0 + 7 候选 reserve cluster) 但 **cross-section dispersion 自然上限低于 ls_t=3.0 admit floor**。这是 axis 本身的几何约束，不是 design 问题。要打破需要 **(a) Python cross-section residualize (orthogonalize away vol_20d basis)** 或 **(b) calibration 流程对 reserve 池整体重新评估**。
