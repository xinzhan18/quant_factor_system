---
direction_tag: idiosyncratic_momentum_residual
status: dead
priority: low
rounds: 1
admits: 0
last_batch: batch_089
last_admits: []
last_goal: 'Round 89 NEW direction first batch (orchestrator-suggested cov_ratio_long_window
  已 archived

  + tsrank_timeseries_ratio saturated, pivot to paper-backed Haitong-37 IMom direction).

  Path-integral 维度补全 over admitted F004 单日 Barra 残差: test whether N-day cumulative

  Barra residual return carries incremental alpha vs F004 point-estimate. Six candidates

  cover (a) T001 window ablation 60d/120d/250d raw cumulative, (b) T002 vol-normalized

  Sum/Std at 120d (paper strict definition), (c) T003 rank-diff path-integral vs raw

  cumulative return at 120d (突破 T014 rank-diff×residual paradigm 4 律 attempt with

  path-integral LHS), (d) T004 low-IVOL gated cumulative at 60d (vol_20d residual
  leak

  test). Hard targets: ≥1 admit with incr_ic@F004>0.015 + max_corr<0.50 + alpha_surv≥0.40

  + ic_by_year sign-stable. T005 横向监控 coverage; if 5/6<0.65 → coverage rerun proposal,

  not direction-dead. Baseline-first 例外: 15 untouched TTM fundamental fields completely

  orthogonal to Barra-residualized return path-integral mechanism — explicitly skip.'
last_activity: '2026-05-04T16:41:40Z'
created_batch: batch_080
members: []
retired_members: []
merged_into: null
status_changed_at: '2026-05-04T16:45:00Z'
status_change_reason: b089 6/6 reject 首批反向证伪 — H1/H2/H3/H4 四子假设全 DISPROVEN (T001 三窗
  + T002 vol-normalize + T003 rank-diff + T004 IVOL gating). P004 律深层扩展实证 — Barra
  residualization 是 single-step 线性算子, N-day path-integral form 重累积 vol_20d basis (path
  memory β-shift). 海通-37 paper transferability 4 层独立失效 (方向反号 + frequency mismatch
  + universe weakness + library overlap). 方向 form 维度全测毕无未探 frontier, 直接归 dead.
---
# idiosyncratic_momentum_residual

> [!abstract]+ 方向概要
> - **状态**　🪦 `dead` (round 89 首批反向证伪 + P004 律 path-integral 深层扩展 + paper transfer 4 层失效) · priority `low` · rounds = 1 · admits = 0
> - **最近**　[[batches/batch_089/judge|batch_089]] · 2026-05-04 · 0/0/6（首批即方向证伪）
> - **一句话**　海通-37 IMom path-integral 假设在 csi1000 daily 上**整体反向 (paper momentum → mean-reversion) + Barra basis 越累越深 (alpha_surv 0.42→0.37→0.36 单调衰减) + 4 子假设全证伪** — Barra residualization 单步线性算子有效但 N-day 累积形式无效, path memory β-shift 重累积 vol_20d basis 是 P004 律的更深层次.

---

> [!failure] ⚠️ Hypothesis 完全证伪 + 方向归档 (b089 首批反向证伪)
> 原假设四层 (T001 path-integral raw / T002 vol-normalize / T003 rank-diff / T004 IVOL gating) **全证伪**. b089 6/6 reject 首批反向证伪.
>
> **6/6 reject 实测**:
> - **T001 raw cumulative 60d/120d/250d (C001/C002/C003)**: 三窗 alpha_surv 单调衰减 0.42→0.37→0.36 (CP04 floor 0.40 三立 borderline-FAIL), ic_oos 全 NEG -0.054/-0.049/-0.041 (paper momentum → csi1000 mean-reversion **方向反号**), incr_ic 全 NEG -0.018/-0.015/-0.011 (库内 F027 multi_ma_reversion / F002 pb_amount 已 capture mean-reversion 几何), dom_style **全部恢复 = vol_20d** exposure 19.6-23.2 (path memory β-shift 重累积 vol_20d basis).
> - **T002 vol-normalized 120d Sum/Std (C004)**: paper Haitong-37 strict definition. alpha_surv=0.332 vs C002 raw=0.373, **vol-normalize 反而恶化** — 分母 Std(ε,120) 共线于 vol_20d basis. paper IR=2.04 配方在 csi1000 daily 完全失效.
> - **T003 rank-diff path-integral vs raw return (C005)**: alpha_surv=1.054 form-independent + max_corr=0.15 LOW 完美 form 独立, 但 ls_t=-0.28 + mono_oos=-0.20 + ic_oos=-0.013 信号 ~zero. T014 disprove 4 律对 path-integral LHS 同样 holds. **alpha_survival > 1.0 单边不足律第 5 次实证**.
> - **T004 IVOL-gated salvage (C006)**: ls_t 从 C001 -6.19 衰减到 -1.58 (信号 strength 不足), incr_ic 仍 NEG. vol_20d path memory 是结构性律不可通过 LHS 0/1 mask 切除.
>
> **3 律升格 (lessons.md, Phase 5 待 consolidate)**:
> 1. **P004 律 path-integral 深层扩展 (新升格)**: F004 单日 Barra-residual admit (alpha_surv=1.41 dom 已剥) ↔ 本批 N-day cumulative residual 6/6 reject (alpha_surv 0.33-0.42 全衰减 + dom=vol_20d 全恢复). **Barra residualization 是 single-step 线性算子有效, 但 N-day path-integral form (Sum/Mean/Sum-over-Std/rank-diff/IVOL-gated 任何累积) 在 csi1000 daily 上 dom_style 全部恢复 = vol_20d, alpha_surv 衰减至 floor — path-memory β-shift 是 P004 律比已知 Linear OLS Polynomial 不破律更深的层次**. 实操: cumulative residual form 默认 reject; 若需 isolate residual alpha, stay at single-step (F004 模式) + multi-day evaluation horizon 替代 multi-day LHS aggregation.
> 2. **paper transferability 4 层独立失效律新例 (海通-37)**: csi500 monthly RankIC 3.98% IR=2.04 → csi1000 daily 6/6 reject. 4 层独立机制: (a) 方向反号 (momentum → mean-reversion); (b) frequency mismatch (monthly path memory ≠ daily); (c) universe weakness (paper 自承 csi500 → csi1000 IC 衰减 2.4x); (d) library overlap (csi1000 admitted F027 / F002 mean-reversion 几何 capture). 与 b088 Chaikin / b069-b072 PIT/TTM paper 同律.
> 3. **alpha_survival > 1.0 单边不足律第 5 次实证 (跨 b072+b086+b087+b088+本批)**: alpha_surv > 1.0 + max_corr < 0.30 LOW + sign_consistency=1.0 三立 form 独立性时, 仍须 ls_t ≥ 1.5 或 incr_ic > 0 至少一项才可 reserve, 否则默认 reject. form 独立 = necessary 不 sufficient — 信号 strength 是 admit/reserve 的 second necessary gate.
>
> **复活路径** (转交其他方向 / 后续 evaluation):
> - (a) **F004/F005 single-step 残差 stay** + multi-day horizon evaluation (h>1d): 不在 LHS 累积 but 在 evaluation 端用 forward h-day return 替换 1-day return. 转交 [[directions/long_horizon_alpha_eval]] (library_gap/012 提议).
> - (b) **ASI Wilder OHLC-only Vol-independent residual**: 与 b088 signed_money_flow_oscillator T001 ASI deferred 同 — 4-branch IF + Max-driven scaling python_runner. 但本方向 dead 后, ASI 复活路径优先级降低 (Vol-independent 不解 P004 path-memory 律).
> - (c) **Python residualize on F004**: F024 absorbing prototype 路径 (finding/013 high), 但 F004 已 admit 自身就在库内, residualize on F004 等同 over-fitting library cluster.

## Hypothesis (DISPROVEN — preserved as anti-pattern record)

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

> [!failure]+ **Round 91 consolidation outcome — 全方向 dead, 元教训升格 P004-deep**
> b089 6/6 reject + T001/T002/T003/T004 4/4 子假设全证伪 + Barra residualization 是 single-step 线性算子律实证. **P004-deep 升格至 lessons**: Barra cross-sectional residualization 对 single-day ε admit-able (F004 反例 alpha_surv=1.41), 但 N-day path-integral / cumulative residual / vol-normalize / rank-diff / IVOL-gating 累积形式默认 reject (path-memory β-shift 重涌 vol_20d basis). 海通-37 paper transferability 4 层独立失效律 (从 round 73 3 件套扩展) 同样升格. **本方向无残余探索价值, 建议下次 consolidation dead → archived**. 元教训详见 [[_consolidation/findings/pattern_analyst/028]] + [[_consolidation/findings/hypothesis_promoter/020]] + [[_consolidation/findings/hypothesis_promoter/021]] + [[lessons#vol_20d 结构性吸收律]] + [[lessons#Paper Transferability]].

### T001 · Cumulative residual return raw form [✗ DISPROVEN batch_089]

> [!failure]+ Thread 结论
> **Question**: 60d / 120d / 250d 三窗口 `Sum(barra_residual_return, N)` raw 累积是否携带 incremental over F004 单日切片的 alpha（incr_ic > 0.015 + max_corr@F004 < 0.50）？最优窗口在哪一档？
>
> **Answer**: 否. 三窗 incr_ic 全 NEG (-0.018/-0.015/-0.011), 不存在 sweet spot, alpha_surv 单调衰减 0.42→0.37→0.36 (60d→250d). max_corr 反向归簇到库内 mean-reversion 几何 (F027/F002) 而非 F004 自身. **方向反号** csi1000 daily 上 cumulative residual = mean-reversion 不是 momentum.
>
> **Evidence trail**:
> - [[batches/batch_089/candidates/C001|b089 C001]] (60d) ic_oos=-0.054 alpha_surv=0.42 incr_ic=-0.018 → reject
> - [[batches/batch_089/candidates/C002|b089 C002]] (120d) ic_oos=-0.049 alpha_surv=0.37 incr_ic=-0.015 → reject
> - [[batches/batch_089/candidates/C003|b089 C003]] (250d) ic_oos=-0.041 alpha_surv=0.36 incr_ic=-0.011 → reject

### T002 · Risk-adjusted (vol-normalized) cumulative residual [✗ DISPROVEN batch_089]

> [!failure]+ Thread 结论
> **Question**: 论文严格定义 `Sum(ε)/Std(ε)` 是否比 raw Sum 更稳？vol-normalization 在 csi1000 是否产生 incremental signal lift（vs T001 raw 路径）？
>
> **Answer**: 否. C004 alpha_surv=0.332 vs C002 raw=0.373, vol-normalize **反而恶化**. 分母 Std(ε,120) 共线于 vol_20d basis, 除以噪声放大 Barra 项. paper IR=2.04 配方在 csi1000 daily 完全失效 — sampling frequency 决定 estimator alpha 性质.
>
> **Evidence trail**:
> - [[batches/batch_089/candidates/C004|b089 C004]] alpha_surv=0.332 ic_oos=-0.053 incr_ic=-0.014 → reject

### T003 · Rank-diff path integral vs T014 disprove [✗ DISPROVEN batch_089]

> [!failure]+ Thread 结论
> **Question**: rank-diff 包装 `CsRank(Sum(ε,120)) - CsRank(Sum(raw_ret,120))` 能否突破 [[barra_residual_alpha]] T014 rank-diff × residual paradigm 的 4 条 disprove 机制？
>
> **Answer**: 否. C005 alpha_surv=1.054 form-independent + max_corr=0.15 LOW 完美 form 独立, 但 **ls_t=-0.28 + mono_oos=-0.20 + ic_oos=-0.013 信号 ~zero**. T014 4 律对 path-integral LHS 同样 holds. **alpha_survival > 1.0 单边不足律第 5 次实证** (跨 b072/b086/b087/b088/本批 5 次).
>
> **Evidence trail**:
> - [[batches/batch_089/candidates/C005|b089 C005]] alpha_surv=1.05 max_corr=0.15 ls_t=-0.28 → reject

### T004 · Low-IVOL gating × cumulative residual [✗ DISPROVEN batch_089]

> [!failure]+ Thread 结论
> **Question**: `Sum(ε, 60) × If(RealizedVol(ret, 60) < median, 1, 0)` 在低波动子集上的 IMom 是否比全样本更稳？vol_20d 是否真已被 barra residualization 剥离干净？
>
> **Answer**: 否. ls_t 从 C001 -6.19 衰减到 -1.58 (信号 strength 不足), incr_ic 仍 NEG. **vol_20d path memory 是 cross-section 结构性律不可通过 LHS 0/1 mask 切除**. 关键 lesson: F004 单日残差 admit + 本批 6/6 path-integral reject 对照 → Barra residualization single-step 算子有效, N-day 累积/path-integral 形式无效, 律边界深于 P004 已知 'non-linear vol_20d absorption' (path-memory β-shift).
>
> **Evidence trail**:
> - [[batches/batch_089/candidates/C006|b089 C006]] alpha_surv=0.40 ls_t=-1.58 incr_ic=-0.009 dom=vol_20d_via_artifact → reject

### T005 · Coverage gate triage [✓ ANSWERED batch_089]

> [!success]+ Thread 结论
> **Question**: 6 候选 coverage 是否系统性 < 0.65？path integral cumulative 是否使 NaN 传播比 single-day 更严重？
>
> **Answer**: 否, **预测过保守**. 6/6 coverage ∈ [0.94, 1.00] (C001/C006=1.00, C002/C004/C005=0.98, C003=0.94). NaN 传播未发生显著恶化 — Barra cache 已覆盖完整时段, residualizer 用 dropna=False stack 保留 multi-index 完整性. **正面发现**: coverage 不是本方向限制因素, alpha 真饱和才是 (P004 律 path-integral 扩展).

---

## Known Failures

| 失败模式 | 候选 | 关键指标 | 升格 |
|---|---|---|---|
| Path-integral 60d short window | [[batches/batch_089/candidates/C001\|C001]] | ic_oos=-0.054 alpha_surv=0.42 dom=vol_20d exp=23.2 incr_ic=-0.018 nearest=F027 | P004 律 path-integral 深层扩展 |
| Path-integral 120d medium window | [[batches/batch_089/candidates/C002\|C002]] | alpha_surv=0.37 < floor + dom=vol_20d + incr_ic=-0.015 | P004 律实证 |
| Path-integral 250d long window (paper-equiv) | [[batches/batch_089/candidates/C003\|C003]] | alpha_surv=0.36 整批最低 + 反号 + incr_ic=-0.011 | paper transferability 4 层失效 |
| Vol-normalized Sum/Std 120d (paper strict) | [[batches/batch_089/candidates/C004\|C004]] | alpha_surv=0.33 vs raw 0.37 反而恶化 + dom=vol_20d | paper IR 配方失效律 |
| Rank-diff path-integral vs raw cum return | [[batches/batch_089/candidates/C005\|C005]] | alpha_surv=1.05 + max_corr=0.15 LOW 但 ls_t=-0.28 ~zero | alpha_surv>1.0 单边不足律第 5 次 |
| Low-IVOL gated cumulative residual | [[batches/batch_089/candidates/C006\|C006]] | ls_t=-1.58 信号弱 + incr_ic NEG + style_r²=0 是 artifact | path-memory 不可 LHS-mask 切除律 |

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

> [!quote]+ Round 89 / [[batches/batch_089/judge|batch_089]] (2026-05-04) — orchestrator dispatch (cov_ratio_long_window 已 archived → pivot), NEW direction 首批 → DEAD
>
> **Goal**: 海通-37 IMom path-integral 在 csi1000 daily 是否 incremental over F004 单日残差.
>
> **结果**: 6/6 reject 首批反向证伪. **方向反号** (paper momentum → csi1000 daily mean-reversion) + **alpha_surv 单调衰减** (60d→250d 0.42→0.36 接近 floor) + **library reducer 全 NEG** (incr_ic -0.018 to -0.009) + **dom=vol_20d 全恢复** (exposure 19.6-23.2 比 single-day F004 更深) + **vol-normalize 不仅没救反而恶化** (C004 0.33 vs C002 0.37) + **rank-diff salvage 信号 ~zero** (C005 ls_t=-0.28) + **IVOL gating 弱化信号** (C006 ls_t -1.58). **方向 4 子假设全 DISPROVEN, 无未测 frontier**.
>
> **3 律升格 (Phase 5 待 consolidate)**:
> 1. **P004 律 path-integral 深层扩展**: Barra residualization 是 single-step 线性算子, N-day path-integral 形式重累积 vol_20d basis (path-memory β-shift). 比已知 'Linear OLS Polynomial 不破 non-linear vol_20d' 更深的层次.
> 2. **paper transferability 4 层失效律新例 (海通-37)**: 方向反号 + frequency mismatch + universe weakness + library overlap 4 层独立失效, 与 b088 Chaikin / b069-b072 PIT/TTM 同律.
> 3. **alpha_survival > 1.0 单边不足律第 5 次实证**: 跨 b072/b086/b087/b088/本批 5 次累计证据, 应升格 lessons "Rank-Order ≠ Tradable Alpha" 子律.
>
> **状态轨迹**: exploring → **dead** (post-b089 6/6 reject H1/H2/H3/H4 全证伪).
>
> **复活路径** (转交):
> - F004/F005 single-step stay + multi-day h>1d evaluation → [[directions/long_horizon_alpha_eval]] (library_gap/012 提议)
> - ASI Wilder OHLC-only python_runner 路径 (与 b088 T001 deferred 同) — 优先级降低, 不解 P004 path-memory 律
> - Python residualize on F004 — 等同 over-fitting library cluster, 不推荐
>
> **Operations**　`status: exploring → dead` · `priority: medium → low` · 触发 consolidation_trigger (active_directions=22 + zero_admit_streak=4 + 3 律待升格).

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
