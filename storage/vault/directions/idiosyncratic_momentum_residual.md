---
direction_tag: idiosyncratic_momentum_residual
status: exploring
priority: medium
rounds: 0
admits: 0
last_batch: batch_080
last_admits: []
last_goal: null
last_activity: '2026-05-02T00:00:00Z'
created_batch: batch_080
members: []
retired_members: []
merged_into: null
---
# idiosyncratic_momentum_residual

> [!abstract]+ 方向概要
> - **状态**　🔵 `exploring` · priority `medium` · rounds = 0 · admits = 0
> - **最近**　— · 新建于 [[batches/batch_080]]
> - **一句话**　把 [[barra_residual_alpha]] F004 的**单日**残差扩展为 N 日**累积残差**（path integral）—— 海通-37 IMom 在 A 股月频 RankIC 3.98% 的机制能否在 csi1000 日频被重现，且 incremental over F004 / F005。

---

## Hypothesis

> [!note]+ Hypothesis · path integral 维度补全 (本地化重写自 海通-37)
> 海通证券 选股因子系列 37（2018-08）证明 A 股月频 IMom = `Sum(ε_{t-12..t-1}) / Std(ε)` 上正交后 RankIC = 3.98%、IR = 2.04，其中 ε = FF3 月度回归残差。本仓库 [[barra_residual_alpha]] F004 已在 csi1000 日频 admit 了**单日** Barra 残差（IC=0.024, ICIR=0.293, incr_ic=0.032），但 **N 日累积残差**未测——单日残差 rank ≠ N 日累积残差 rank（线性叠加不保 cross-section rank invariant）。
>
> **三条经济学线索**
> 1. **Path memory ≠ point estimate**：F004 是单日切片，cumulative sum over 60-250d 的 rank 排序由 path 全程信息驱动，与单日 rank 在数学结构上独立。海通论文的 IC 跳升正源于此 path 维度（论文未明说，但月度残差累积本质就是这个）。
> 2. **Confounding style 已被剥离**：raw return momentum 在 csi1000 全 dead（[[return_momentum_acceleration]] / [[asymmetric_momentum]] / [[fundamental_momentum]] dead 三方向）的本质原因 = vol/turnover 反向暴露吃光信号；residualized return 的累积绕过这条吸收路径，理论上 incremental over raw momentum 失败原因。
> 3. **海通正交后 IC × 4 倍 lift** 是 N 日 path × style stripping 的复合效应，单纯 1 日残差（F004）只兑现了一半（style stripping 部分），path 部分尚未试。
>
> `cumulative_idio_momentum = Sum(barra_residual_return, N)  for N in {60, 120, 250}`
>
> 或 vol-normalized: `risk_adj_imom = Div(Sum(barra_residual_return, N), Std(barra_residual_return, N))`

> [!warning]+ ⚠️ 已知陷阱与 prior 失败规避
> 1. **csi1000 coverage 0.71 << 0.80 hard_gate** ([[F008]] / [[F202]])：[[barra_residual_alpha]] T014 batch_054 5/5 候选独立确认 Python residual + rolling 在 csi1000 系统性 coverage 0.71-0.73。Cumulative sum 比 single-day 更敏感于 NaN 传播（窗口越长，NaN 概率越高），本方向首批预期 coverage ≤ 0.65。**首批必须把 coverage 当头号风险**。Mitigation：(a) forward-fill ε NaN; (b) 用 expanding sum + min_periods 容错; (c) 申请 direction-aware threshold 0.65（[[F202]] proposal 复用）。
> 2. **F300 rate-form default-skip 律**：raw `Sum / Std` 不是 rate-of-change（同分子分母都来自 ε 序列，magnitude 标量化）——结构上不在 F300 禁止范围，但仍需 alpha_surv + incr_ic 双正才能 admit。
> 3. **F004 / F005 自身高 corr 风险**：N 日累积残差与单日残差在 long horizon 上可能渐近共线（中心极限）。max_corr@F004 必须 < 0.50 才算 incremental；< 0.30 才安全。
> 4. **rank-diff × residual T014 disprove 4 律**：本方向 T003 的 rank-diff 候选 LHS 是 path integral（Sum），区别于 T014 的 point statistic LHS（|res|_std / EMA(res) / autocorr）——是否能突破 T014 的 4 律是经验问题，不能预设成功。
> 5. **vol_20d 几何吸收 (P004 律)**：barra_residual 已剥离 vol_20d；但 cumulative sum 可能因 path memory 重新累积 vol exposure。**alpha_surv ≥ 0.40 + dom_style ≠ vol_20d** 是必查项。
> 6. **β 估计窗口未知**：海通月频用 36 月窗口；日频降阶到 60-120 日 β 估计 high variance，残差本身噪音化。首批用 vectorized_barra.py 的现成 60d 窗口（与 F004 一致），不重新设计 β 窗口。
> 7. **lookahead 防线**：N 日 cumulative 必须严格用 t-N..t-1 残差，不可包含 t 期 ε（否则与 forward residual leak）；hard_gate AST 扫描 + ls_max_dd=0 / win_rate=1.0 sentinel 必须通过。
> 8. **csi1000 是论文里 IMom 最弱 universe**：海通自报"中证 800 以外" IC 仅 1.67% （vs 沪深 300 IC 4.56%）；样本期 2011-2018 不含 2019-2024 风格剧变。本方向 effect size 期望值应**低于** F004（IC=0.024）/F005，不是更高。Admit 门槛仍按系统标准（incr_ic ≥ 0.015 + |ls_t| > 2 + max_corr < 0.50 + alpha_surv ≥ 0.30）。

---

## Current Focus

首批 6 候选探针 T001 + T002 + T003 baseline：
- T001 (×3): 60d / 120d / 250d 三窗口 raw cumulative residual return —— 窗口敏感性 + 与 F004 单日切片的 incremental IC
- T002 (×1): vol-normalized 120d 版本（论文严格定义）—— Sum/Std ratio 是否比 raw Sum 更稳
- T003 (×1): rank-diff `CsRank(Sum(ε,120)) - CsRank(Sum(raw_ret,120))` —— 突破 T014 rank-diff × residual paradigm 4 律的尝试，区别于 T014 的 point statistic LHS
- T004 (×1): low-IVOL gated 60d cumulative residual —— gating 探针，验证 IVOL 与 IMom 的相关性是否被剥离后仍有 confounding

不期待全 admit；**目标 ≥ 1 admit + coverage gate 全过**。如 5/6 coverage < 0.65 重演 b054 → 方向 saturated 等数据契约修复；如 coverage 全过但 0 admit → T001-T004 独立证伪 path integral 假设，方向 dead。

---

## Threads

### T001 · Cumulative residual return raw form [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: 60d / 120d / 250d 三窗口 `Sum(barra_residual_return, N)` raw 累积是否携带 incremental over F004 单日切片的 alpha（incr_ic > 0.015 + max_corr@F004 < 0.50）？最优窗口在哪一档？
>
> **Evidence trail**:
> - 待 batch_080 兑现
>
> **Next probes**: 首批 C001-C003 三窗口扫描；若全 reject 且短窗 (60d) 最强但仍 ls_t<2 → T001 DISPROVEN，path integral 假设在 raw form 上失败，转向 T002 vol-normalized。

### T002 · Risk-adjusted (vol-normalized) cumulative residual [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: 论文严格定义 `Sum(ε)/Std(ε)` 是否比 raw Sum 更稳？vol-normalization 在 csi1000 是否产生 incremental signal lift（vs T001 raw 路径）？
>
> **Evidence trail**:
> - 待 batch_080 C004 兑现
>
> **Next probes**: 单候选首批 (120d 中窗)；若 admit/reserve → 下批扩到 60d/250d；若 reject → 验证是否 ratio form 触 [[F300]] 律（不应触，需 manifest 注明 magnitude 不是 rate）。

### T003 · Rank-diff path integral vs T014 disprove [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: rank-diff 包装 `CsRank(Sum(ε,120)) - CsRank(Sum(raw_ret,120))` 能否突破 [[barra_residual_alpha]] T014 rank-diff × residual paradigm 的 4 条 disprove 机制？关键区别：本候选 LHS = path integral（Sum），不是 T014 的 point statistic LHS（|res|_std / EMA(res) / autocorr / SNR）。
>
> **Evidence trail**:
> - 待 batch_080 C005 兑现
>
> **Next probes**: 单候选首批；若 admit → path integral 是 rank-diff × residual paradigm 的有效 LHS subspace（T014 disprove 不是 universal 律），可扩 60d/250d 窗口；若 reject → T014 4 律对 path integral LHS 同样 holds，rank-diff × residual 范式整体 dead。

### T004 · Low-IVOL gating × cumulative residual [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: `Sum(ε, 60) × If(RealizedVol(ret, 60) < median, 1, 0)` 在低波动子集上的 IMom 是否比全样本更稳？vol_20d 是否真已被 barra residualization 剥离干净？
>
> **Evidence trail**:
> - 待 batch_080 C006 兑现
>
> **Next probes**: 单候选首批；若 alpha_surv ≥ 0.40 + dom_style ≠ vol_20d → IVOL gating 真有效；若 dom=vol_20d → barra residualization 已剥 vol_20d 但 cumulative sum 重新累积 vol exposure，path memory 把 style 又"积"回来，重要 lesson 升格。

### T005 · Coverage gate triage [◉ MONITORING]

> [!note]+ Thread 横向
> **Question**: 6 候选 coverage 是否系统性 < 0.65（重演 b054 5/5 KO）？若是，path integral cumulative 是否使 NaN 传播比 single-day 更严重？
>
> **Evidence trail**:
> - 待 batch_080 整批兑现后统计 coverage 分布
>
> **Next probes**: 若全 < 0.65 → 申请 direction-aware threshold 0.60 ([[F202]] proposal 复用) 或先做 NaN 预填充再重跑；若 ≥ 0.80 → coverage 不是阻碍，直接看 alpha 信号。

---

## Known Failures

- 待 batch_080 兑现

---

## Related

- 🟡 [[barra_residual_alpha]] `saturated` — F004 单日残差 admit；本方向是 path integral 维度补全；复用 vectorized_barra.py 7-style residualizer
- 🔴 [[return_momentum_acceleration]] `dead` — raw return rate/delta 全 dead；本方向用 residualized return + level sum form 应避开 [[F300]] 律
- 🔴 [[trend_residual_geometry]] `dead` — time-series Resi($close, N) 自回归残差几何；本方向是 cross-sectional Barra residual + path integral，几何完全不同
- 🔴 [[asymmetric_momentum]] `dead` — up-only / down-only return 分解全 dead；本方向不分方向，做对称累积
- 🔴 [[fundamental_momentum]] `dead` — fundamental rate form dead；本方向 LHS = price residual 不是 fundamental rate
- 📖 [[papers/haitong_37_idiosyncraticmomentum_2018]] — 论文原文 paper note，含 6 idea / feasibility / 隐藏假设
- 📖 [[lessons#Structural Constraints]] — F002 anchor / F008 coverage / F202 direction-aware threshold / F300 rate-form / F304 真 orthogonalization

---

## Narrative Log

### 2026-05-02 · 方向新建（来自 [[papers/haitong_37_idiosyncraticmomentum_2018]]）

新建依据：海通-37 论文测的 IMom = N 月累积 FF3 残差，与 [[barra_residual_alpha]] F004（单日 Barra 残差）在 path integral 维度独立——单日 rank 与 N 日累积 rank 是两个分布。F004 已确立"残差携带独立 alpha"的存在性，但 path 维度未试。本方向是**逻辑上未被回答的子问题**：cumulative residual return 是否在 csi1000 日频 admit。

**关键判定 vs 邻居方向**（paper note 已详述）：
- vs [[barra_residual_alpha]] saturated：F004 是单日切片，本方向是 N 日累积——point estimate vs path integral
- vs [[return_momentum_acceleration]] dead：raw return rate form 失败，本方向是 residualized return level sum form
- vs [[trend_residual_geometry]] dead：time-series 自回归残差，本方向是 cross-sectional Barra 残差 + 累积

**首批 6 候选粗稿**（留给 /factor-idea 细化）：
1. `Sum(barra_residual_return, 60)` — T001 短窗
2. `Sum(barra_residual_return, 120)` — T001 中窗
3. `Sum(barra_residual_return, 250)` — T001 ≈ 论文 12 月长窗
4. `Div(Sum(barra_residual_return, 120), Std(barra_residual_return, 120))` — T002 vol-normalized
5. `Sub(CsRank(Sum(barra_residual_return, 120)), CsRank(Sum(close.pct_change(1), 120)))` — T003 rank-diff
6. `Sum(barra_residual_return, 60) × If(RealizedVol(ret, 60) < CsQuantile(0.5), 1, 0)` — T004 low-IVOL gated

**最大已知风险**：
1. **Coverage 0.71 重演**（[[barra_residual_alpha]] T014 b054 5/5 KO）—— path integral 比 single-day NaN 传播更敏感，预期 coverage ≤ 0.65。T005 横向监控。
2. **csi1000 是论文里 IMom 最弱 universe**（论文中证 800 以外 IC 仅 1.67% vs 沪深 300 4.56%）+ 样本期不含 2019-2024 风格剧变 —— effect size 期望低于 F004，不是更高。
3. **F004 高 corr 风险**：长窗 cumulative 可能渐近共线 F004 单日；max_corr 必须 < 0.50。

**Operations**　`status: exploring` (新建) · `priority: medium` (path integral 维度独立 + barra residualizer 已就绪 + 论文严格定义可复刻；但 csi1000 universe weak + coverage 已知高风险 双重折扣) · rounds 0→1 (待 batch_080 落地后)
