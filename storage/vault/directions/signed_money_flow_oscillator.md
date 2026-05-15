---
direction_tag: signed_money_flow_oscillator
status: dead
priority: medium
rounds: 2
admits: 0
last_batch: batch_088
last_admits: []
last_goal: 'Round 88 — signed_money_flow_oscillator new_direction first batch (cockpit
  hint: 切换 productive direction 全 saturated; 探测 paper-vetted 广发金工 42 signed money-flow
  oscillator family). 库内 28 admit 全为 second-moment (Corr/Cov/Std/CV cluster F001/F008/F009)
  或 first-moment magnitude (Mean of |X| F010/F012) 或 range-position (F006/F007/F021/F022/F026)
  — first-moment signed × Vol 累积 family (Sum / EMA of signed_atom × Vol) 在库内零 admit,
  是结构性新空间. 本批 6 候选覆盖三条 paper-vetted 子路径 + 关键 ablation: (a) Chaikin Oscillator EMA(AD,3)-EMA(AD,10)
  signed close-position × Vol money-flow EMA 差 (paper |IC|=1.84%, 多空胜率 102 因子第 2 名);
  (b) AD cumulative Sum 20d (Chaikin base, 同 atom 不同时间聚合); (c) PVT Sum N=20/60 signed_return
  × Vol 累积 (paper N=6 |IC|=2.16%, csi1000 daily 改长窗); (d) Chaikin EMA(6)-EMA(20) 长窗
  ablation; (e) PVT 60d rank-diff salvage (P008 frontier escape 路径预先尝试 — 若 raw PVT
  落入 vol_20d 吸收, rank-diff + amount fresh RHS 可能 salvage). ASI(20/60) 4-branch IF
  Wilder swing 在 daily DSL 不可达 (需 4-branch conditional + Max-driven scaling 必须 python_runner),
  本批不入. 关键 hypothesis: H1 (family 真度) signed money-flow 累积几何不同于 F009 second-moment
  correlation 与 F008 second-moment covariance, 期望 ≥1 候选 alpha_surv ≥0.40 + max_corr<0.50
  incremental_ic≥0.010; H2 (Vol-dependent path) Chaikin/AD/PVT 全部依赖 Vol, 测 Vol-dependent
  first-moment signed 是否被 F001 vol_20d 吸收律覆盖; H3 (vol_20d 吸收律 first-moment 例外) 若 raw
  PVT/Chaikin/AD 6/6 dominant_style=vol_20d 全 reject → F001 升级为"任何 N-day 聚合 magnitude
  形态 (含 first-moment signed) 全吞噬", 若 ≥1 first-moment signed alpha_surv >0.5 → F001
  收紧为"second-moment 专属吞噬律". 全候选严守 P019 Corr-safe (Chaikin/AD/PVT 双端均 ∈ {$close, $open,
  $high, $low, $volume, $amount}, 不用 Cov/Corr atom 故 cross-field bug 不适用), 避 P016
  cap-denominator (无 market_cap), 避 P004 cross-product Mul 跨字段塌缩 (本候选 Mul 是 signed_atom
  × Vol 同 atom-class 价量乘积, 与 b074 dead Mul cross-product 几何不同). Hard targets: ≥1 admit
  alpha_surv≥0.40 + max_corr<0.50 + incr_ic≥0.010 + ls_t_oos≥2 + sign_consistency=1.0.
  Fail (6/6 reject) → 升格 F001 lesson 边界 ("first-moment signed 累积也被 vol_20d 吞噬"), 直接
  trigger consolidation_trigger (rounds_since_consolidation=7, 临近 10 阈值; zero_admit_streak=5).'
last_activity: '2026-05-03T08:57:12Z'
created_batch: batch_081
members: []
merged_into: null
---
# signed_money_flow_oscillator

> [!abstract]+ 方向概要
> - **状态**　⚫ `dead` · priority `medium` · rounds = 1 · admits = 0
> - **最近**　batch_088 0/6 admit + 0/6 reserve — H1/H3 验证完毕, F001 vol_20d 律 first-moment 累积扩展实证
> - **一句话**　测试 **first-moment signed × Vol 累积/平滑**（Wilder ASI、Chaikin Oscillator、AD、PVT）在 csi1000 daily 上是否独立于库内 F009 pv_corr_times_vol 的 second-moment correlation 簇 — **DISPROVEN**: Chaikin/AD/PVT (Vol-dependent 子路径) 4/4 落入 vol_20d 吸收律 + close-position cluster, 仅 ASI (OHLC-only Vol-independent) 因 daily DSL 不可达未测

---

## Hypothesis

广发金工 42 在中证 500 + weekly + 102 经典技术指标 cross-section 上排出 |IC| top 15 与 多空胜率 top 15。库内 25 admitted 因子已覆盖 BIAS / VSTD / 成交金额方差 / 价格线性回归 / KDJ / RSI / ROC / W%R / ATR / 已实现偏度 / DMI / Aroon / Hurst / Mass / Ulcer / TRIX / Chande / CCI（全部 reduced 或 dead）；**剩下未被覆盖的高 IC 信号集中在一个数学族**——**signed money-flow oscillator family**：

- **ASI** (Wilder accumulated swing index): 4-branch IF on `(|H-LC|, |L-LC|, |H-Ref(L,1)|)` + `Max(AA, BB)` driven scaling，N=20 累加。|IC|=2.71% 多空胜率 61.09%。**纯 OHLC 不依赖 Vol**，但是 8-OHLC 摆动符号累积。
- **Chaikin Oscillator**: `EMA(AD, 3) − EMA(AD, 10)`，其中 `AD = Vol * (2C - H - L) / (H - L)` = signed close-position-in-range × volume。|IC|=1.84% 多空胜率 **62.12% (102 因子第 2 名)**。
- **AD**: 同 Chaikin 的 base，6/20 日累加。|IC|≈1.2-1.4% 多空胜率 60.58%。
- **PVT**: `Sum((C - Ref(C,1))/Ref(C,1) * Vol, N)`，N=6 时 |IC|=2.16% 多空胜率 56.66%；N 全期 |IC|=1.98% 多空胜率 57.34%。

**核心几何区别于库内已 admitted 的"价量协同"族**：
- F009 pv_corr_times_vol = `Corr($close, $volume, N) * $volume` = **second-moment correlation** × Vol（去均值后两序列同步性）
- F008 ret_vol_cov_20 = `Cov(returns, $volume, 20)` = **second-moment covariance**
- 本方向 4 个候选都是 **first-moment signed × cumulative**：sign(daily_OHLC_swing 或 daily_return 或 close-position) × Vol → 时间累加 / EMA 平滑 / EMA 差。**不去均值**，含正负号累积。

**A 股本地化核心假设（H1, family 真度）**：
signed money-flow 累积 family 几何上不同于 F009 second-moment correlation；与 vol_20d 的关系不像"std-of-X"那样必然吞噬，因为：(a) ASI / PVT 的累加是 net signed flow 而非 magnitude squared；(b) Chaikin / AD 的 `(2C-H-L)/(H-L)` 是 [-1, +1] 有界 close-position 项，乘 Vol 后仍是 signed 量。先验 ~45% 概率至少 1 个 candidate 进入 reserve / admit 形态。

**A 股本地化核心假设（H2, ASI vs Chaikin/AD/PVT 是两条独立子路径）**：
ASI **不依赖 Vol**（仅 OHLC + prev_OHLC 8 个量），与 Chaikin/AD/PVT（**全部依赖 Vol**）正交。若两条子路径同时 admit，证明"signed accumulation"几何骨架真实；若只 ASI admit，提示 Vol-dependent money-flow 在 csi1000 上仍被 F009/F008 cluster；若只 Chaikin/AD/PVT admit，提示 ASI 的 4-branch IF 复杂度反而稀释 alpha。

**A 股本地化核心假设（H3, vol_20d 吞噬律的 first-moment 例外）**：
lessons F001 / F301 vol_20d 吞噬律的所有验证案例都是 **second-moment** 形态（std / variance / Quantile / power-mean / Skew / Kurt 全部）。first-moment signed accumulation **从未被独立测试过**——本方向是 lessons F001 的边界探针：如果 first-moment signed 累加也被 vol_20d 吞噬（ASI / PVT / Chaikin 全 dominant_style=vol_20d），则把 F001 升级为"任何 N-day 聚合的 magnitude 形态都吞噬"；如果至少一个 first-moment signed 候选 alpha_survival > 0.5，则把 F001 收紧为"second-moment 专属吞噬律"。

**先验预期**:
- 概率 ~30% Chaikin Oscillator (Idea 2) baseline 真度成立（hard_gate 通过 + max_corr@F009 < 0.7）
- 概率 ~25% ASI (Idea 1) 真度成立（cross-section dispersion 不被涨跌停日 truncated SI 主导）
- 概率 ~25% PVT(6) (Idea 4) 真度成立
- 概率 ~30% 6/6 全 reject 且 dominant_style=vol_20d → 本方向落入 second-moment 同律 → 升格 F001 边界 lesson

**A 股投资约束（必须明确）**:
广发 paper 的多头年化 13.45-14.82% 是中证 500 + 周频换仓 + 自融多空。csi1000 daily 横截面 + T+1 + 无裸卖空 → 只用 long 端 top quintile，且 weekly → daily 标签 horizon 切换会让 |IC| 衰减 ~50%。读 paper 时不能把 |IC|=2.71% / 多空胜率 61% 直接外推到本仓库 hard_gate 预期。

---

## Current Focus

首批 batch_081 设计 6 候选覆盖 4 条子路径 + 关键 ablation:
- 1 个 ASI(20) (T001 Wilder swing baseline，python_runner 路径)
- 1 个 Chaikin Oscillator(3, 10) (T002 main — money-flow EMA 差)
- 1 个 AD(6) cumulative (T002 ablation — 同 base 不同时间聚合)
- 1 个 PVT(6) (T003 main — signed return × Vol 6 日累加)
- 1 个 PVT(12) (T003 窗口对照)
- 1 个 ASI(60) (T001 长窗口对照 — paper 仅测 20 日，60 日是 anchor-period 探针)

**首批关键 adjacency 自检**（在 design 阶段就要写进 rationale）:
- 必须验证 `Corr(Chaikin_Osc, F009_pv_corr_times_vol)` < 0.7 — 否则方向是 F009 换皮
- 必须验证 `Corr(PVT_6d, F008_ret_vol_cov_20)` < 0.7 — 否则与 F008 cov 同构
- 必须验证 `Corr(ASI_20, F021_upper_shadow_disp_range_compress_rd_20)` < 0.6 — 否则 ASI 退化为 range-position 信号
- 必须验证 `Corr(AD_6d, Chaikin_Osc)` 介于 0.5-0.85（如果 < 0.5 说明 AD 与 Chaikin 几何上 decoupled，two ablations；如果 > 0.85 说明只 Chaikin 一条独立）

**下一步若首批 ≥1 admit → 转 active，开 batch_082 探索**:
- (a) Chaikin / AD 的 vol-orthogonalize 版本 (lessons F001 mandated salvage)
- (b) PVT 与 OBV (sign-only 版) 对照
- (c) ASI 的窗口曲线 10/20/40/60 寻找 sweet spot

**若首批 6/6 全 reject + dominant_style=vol_20d** → status `exploring → dead`，升格 F001 lesson 边界为"包括 first-moment signed accumulation 在内的所有 N-day OHLC/V 聚合都 vol_20d 吞噬"。

---

## Threads

> [!failure]+ **Round 91 consolidation outcome — 全方向 dead, 元教训升格 P004-deep**
> b088 6/6 reject + 4 子假设 H1/H2/H3 全证伪 + Chaikin(3,10)/Chaikin(6,20)/AD/PVT(20)/PVT(60)/PVT-60-rank-diff 4/4 子路径 dead. **H3 vol_20d 律 first-moment 例外假设 DISPROVEN** — PVT(20)/PVT(60) alpha_surv=0.11/0.16 << 0.40 floor, dom=vol_20d 直接吸收, F001 vol_20d 律边界扩展实证. **alpha_surv > 1.0 单边形式独立 ≠ library 充分条件** (C001/C005 alpha_surv=1.35/1.57 但 incr_ic=-0.007/-0.005 NEG + max_corr=0.61-0.63@F026/F008 cluster). 三方向 (本方向 + idiosyncratic_momentum_residual + price_conditional_amplitude) 共享同一深层失败律 P004-deep (path-integral / N-day 累积形式 path-memory β-shift 重涌 vol_20d basis), 已 round 91 升格至 `lessons.md#vol_20d 结构性吸收律` 段. 元教训详见 [[_consolidation/findings/hypothesis_promoter/020]] + [[_consolidation/findings/pattern_analyst/028]] + [[lessons#vol_20d 结构性吸收律]]. **方向无残余探索价值, 建议下次 consolidation dead → archived**. ASI Wilder swing python_runner 路径已无价值 (H2 全证伪 + P004-deep 律覆盖 N-day 累积形式).

### T001: ASI (Wilder accumulated swing index) — 8-OHLC 摆动累积是否独立 [✗ DEFERRED-irrelevant-after-P004-deep]

> [!note]+ Thread 当前
> **Question**: ASI 的 4-branch IF + Max-driven scaling（不含 Vol 但含 prev_O / prev_L）是否在 csi1000 daily cross-section 上携带库内 25 admitted 之外的独立 alpha？关键审计：style_r²、dominant_style、与 F021/F022 range_compression 系列的 max_corr。
>
> **Evidence trail**:
> - （待 batch_081 首批结果填入 — C001 ASI(20), C006 ASI(60)）
>
> **Next probes**: baseline 通过则 batch_082 测窗口曲线 10/40 ablation；不通过则验证是否 100% 重演 range_structure 同律（dominant_style=vol_20d + alpha_surv<0.4）。

### T002: Chaikin Oscillator + AD (signed close-pos × Vol → 累积/EMA 差) — 是否独立于 F009 second-moment correlation [✗ DISPROVEN batch_088]

> [!note]+ Thread 当前
> **Question**: `Vol * (2C - H - L) / (H - L)` 这种 signed close-position-in-range × volume 的 first-moment 累积形式是否与 F009 pv_corr 的 second-moment correlation 形式 cross-section 独立？EMA-差（Chaikin）vs 纯累加（AD）哪个更稳？
>
> **Evidence trail**:
> - （待 batch_081 首批结果填入 — C002 Chaikin Osc, C003 AD(6) cumulative）
>
> **Next probes**: 若 Chaikin admit 而 AD reject → momentum-of-money-flow 维度是真信号；若两者同 reserve → first-moment signed × Vol family 真度成立；若两者同 reject → first-moment 累积也被 vol_20d 吞噬（升格 F001 边界 lesson）。

### T003: PVT (signed return × Vol cumulative) — 是否独立于 F008 ret_vol_cov [✗ DISPROVEN batch_088]

> [!note]+ Thread 当前
> **Question**: `Sum((C - Ref(C,1))/Ref(C,1) * Vol, N)` 这种 daily-return × Vol 的 N 日累积是否与 F008 Cov(returns, Vol, 20) 的去均值乘积均值 cross-section 独立？6 日 vs 12 日窗口哪个更优？
>
> **Evidence trail**:
> - （待 batch_081 首批结果填入 — C004 PVT(6), C005 PVT(12)）
>
> **Next probes**: 若 PVT(6) admit 而 PVT(12) reject → 短窗 first-moment signed 累积是 sweet spot；若两者都 reserve → 窗口稳健；若都 reject → first-moment signed × return × Vol 与 F008/F009 cluster 同构。

### T004: vol-orthogonalized Chaikin salvage (lessons F001 mandated) [◉ DEFERRED to batch_082]

> [!note]+ Thread 当前
> **Question**: 若 T002 Chaikin 在首批因 vol_20d 吞噬被 reject，`Div(Chaikin_Osc, Mean($volume, 20))` 这种 vol-level 归一化是否能 salvage？lessons F001 明列 "scale-free / vol-orthogonalize 是 vol_20d 吞噬律 4 条逃离路径之一"。
>
> **Evidence trail**:
> - （deferred）
>
> **Next probes**: 仅在 T002 reject 且 dominant_style=vol_20d 明确时启动；否则视 T002 admit 路径决定是否需要。

---

## Known Failures

| Batch | Candidate | Pattern | 原因 |
|---|---|---|---|
| batch_088 | C001 | `Sub(EMA(AD,3),EMA(AD,10))` Chaikin Oscillator paper 标准窗 | alpha_surv=1.35 (Barra-cleanest) + 9/9 年负 + sign_consistency=1.0 但 incr_ic=-0.007 NEG + max_corr=0.63@F026 (TsRank close-position 60d) — library_reducer hard_block (alpha_surv > 1.0 形式独立 ≠ library 充分条件 候选律 b086/b087/b088 第 3 次实证). paper csi500 weekly +信号 → csi1000 daily 反号 + 反向被库内 close-position cluster (F006/F008/F026) capture. |
| batch_088 | C002 | `Sum(AD, 20)` AD-Sum-20 Chaikin base atom 累计 | max_corr=0.36 LOW (本批最干净) + alpha_surv=0.466 刚过 0.40 floor 但 mono_oos=-0.10 OOS quintile 结构破坏 + sign_consistency=0.75 + style_r²=0.27 接近 poor + incr_ic=-0.004 NEG — 4/5 borderline fail, 不满足 reserve fire 4 要件 (max_corr<0.30 + style_r² clean + sign_cons=1.0 + incr_ic borderline+). |
| batch_088 | C003 | `Sum((C-prev_C)/prev_C × Vol, 20)` PVT(20) 短窗 | alpha_surv=0.11 << 0.40 floor (3.6x 缺口) + dom=vol_20d (exposure=7.4) — F001 vol_20d 律 first-moment 扩展实证 (律边界从"second-moment magnitude"扩展到"任何 N-day 累积形式 含 first-moment signed × Vol Sum"). |
| batch_088 | C004 | `Sum((C-prev_C)/prev_C × Vol, 60)` PVT(60) 长窗 | alpha_surv=0.16 << 0.40 floor + dom=vol_20d + max_corr=0.35@F002 — 长窗未 salvage, F001 律 N=20/60 双窗实证一致. |
| batch_088 | C005 | `Sub(EMA(AD,6),EMA(AD,20))` Chaikin Oscillator 长窗 | 与 C001 同律 — alpha_surv=1.57 整批最高 + 9/9 年负 + sign_consistency=1.0 但 incr_ic=-0.005 NEG + max_corr=0.61@F008 (upper_shadow_persistence_3d). C001 vs C005 窗口 ablation 同律: Chaikin EMA-差 family 整体 form-independent + library-overlapping. |
| batch_088 | C006 | `Sub(CsRank(PVT_60),CsRank(Mean(amount,60)))` PVT 60d rank-diff salvage | hard_gate sign_flip catastrophic (train_ic=-0.0099 vs val_ic=+0.0111 翻号) — PVT raw 已被 vol_20d 吸收 (C003/C004 实证), rank-diff salvage 失败. lessons "rank-diff salvage 仅当 numerator 自身 alive" 律一致. |

---

## Anti-Recap

- **避免 stochastic_position (batch_041) 6 reject 候选** — 不重 `(close - TsMin) / (TsMax - TsMin)` 双边 range %K；不重 `TsRank($close, N)`。本方向是 signed accumulation 而非 close 在 range 内的位置。
- **避免 range_structure 17 reject 候选** — 不重 `Std((H-L)/C, N)`、`Skew/Kurt((H-L)/C, N)`、`Quantile((H-L)/C, N, q)`、rank-diff geometry 等已 saturated 形态。本方向是 cumulative signed flow 而非 range magnitude/shape。
- **避免 return_distribution_signals DEAD 形态** — 不重 daily-return 的 std/skew/kurt/quantile；本方向 PVT 用 return 但作为乘子（× Vol 累积），不是 return 自身的 moments。
- **避免 amount_volatility_signal saturated 形态** — 不重 amount/turnover 的 std/CV/HHI；本方向 Chaikin/AD/PVT 用 Vol 作 weight，不是 Vol 自身的 dispersion。
- **红线 1**：本方向**所有候选必须**在 design 阶段写明与 F009 (pv_corr_times_vol) 和 F008 (ret_vol_cov_20) 的 max_corr 预期；候选必须能描述自己的 first-moment signed accumulation 几何为何不会与 second-moment correlation/covariance 簇 cluster。
- **红线 2**：本方向**禁止**用 `Std`、`Var`、`Skew`、`Kurt`、`Quantile` 作 LHS 顶层算子（这些是 second-moment / higher-moment 形态，已在 lessons F001 vol_20d 吞噬律下默认 reject）。本方向 LHS 顶层只能是 `Mean`（累加形式）、`EMA`（平滑形式）、`Sub`（EMA-差形式）、`Sum`（纯累加形式）。
- **红线 3**：rate-form failure (lessons F300) — 本方向**禁止** Delta(Chaikin) / Δ(PVT) 等变化率形式。所有候选必须是 level/cumulative/EMA 形式，rate 形式默认跳过。
- **红线 4**：H-L 涨跌停 epsilon 处理 — Chaikin / AD 的分母 `H - L` 在涨跌停日可能为 0；DSL 候选必须用 `Div(numerator, Add(Sub($high, $low), 1e-6))` 或同等 epsilon 处理；python_runner 候选必须显式 winsorize。

---

## Related

- 🟢 [[ohlc_temporal_aggregation]] `saturated` — F009 pv_corr_times_vol Grade A score 79.9 占据 second-moment correlation 生态位；本方向 first-moment signed accumulation 必须 max_corr@F009 < 0.7
- 🟢 [[ohlc_temporal_aggregation]] `saturated` — F008 ret_vol_cov_20 占据 second-moment covariance 生态位；本方向 PVT 必须 max_corr@F008 < 0.7
- 🔴 [[stochastic_position]] `saturated` — KDJ family 全 DEAD (paper KDJ K/J/D 也 |IC|<0.015 cross-confirm)
- 🟡 [[range_structure]] `saturated` — BIAS / range magnitude family 完整覆盖 (paper 头名 BIAS(6) |IC|=3.43% 在库内已是 F021 占位)
- 🟡 [[anchor_proximity_momentum]] `exploring` — W%R Williams family（paper W%R(9/15/20) |IC|<0.01 弱信号），与本方向无重叠
- 🔴 [[return_distribution_signals]] `dead` · 🔴 [[return_momentum_acceleration]] `dead` · 🔴 [[asymmetric_momentum]] `dead` — RSI / ROC / MTM / 已实现偏度 全 DEAD（paper 同族均不可挖）
- 🔴 [[vol_shock_signals]] `dead` — ATR / Mass / Ulcer / Hurst 同律 DEAD
- 🟡 [[amount_volatility_signal]] `saturated` — VSTD / 成交金额方差 family 完整覆盖（paper VSTD(20) |IC|=3.02% 在库内已是 F004/F010 占位）
- 🟡 [[liquidity_acceleration]] `saturated` — turnover acceleration family 已 reduced
- 📖 [[lessons#Structural Constraints]] — F001 / F301 vol_20d 吞噬律边界探针：本方向是 first-moment signed accumulation **从未被独立测试**的边界
- 📖 [[lessons#OHLC Family Defaults]] — F005 OHLC algebraic mirror（决定 CCI 是 BIAS reducer 不进首批）
- 📖 [[lessons#Forbidden Patterns]] — F300 rate-form failure（PVT/Chaikin 是 cumulative/EMA 形式，**不撞**该律）

---

## Narrative Log

> [!quote]+ 2026-05-02 · seeded from [[papers/gf_42_technicalindicatoralpha|广发金工 42]]
> Direction created from 102-indicator catalog paper intake. 经过库内 25 admitted 因子的"反向 join"——剩下未被覆盖的 high-|IC| / 高多空胜率指标集中在一个 family：**signed money-flow oscillator**。代表性候选：
>
> - ASI |IC|=2.71% 多空胜率 61.09% — Wilder 8-OHLC 摆动累积，**纯 OHLC 不含 Vol**
> - Chaikin Oscillator |IC|=1.84% 多空胜率 **62.12% (102 因子全表第 2)** — `EMA(AD, 3) - EMA(AD, 10)` 其中 `AD = Vol * (2C - H - L) / (H - L)`
> - AD |IC|=1.44% 多空胜率 60.58% — Chaikin 的 base 累加形式
> - PVT(6) |IC|=2.16% 多空胜率 56.66% — `Sum((C - prev_C)/prev_C * Vol, 6)`
>
> **几何与库内已 admitted 的关键差分**:
> - F009 pv_corr_times_vol: second-moment Correlation × Vol（去均值同步性）
> - F008 ret_vol_cov_20: second-moment Covariance（去均值乘积均值）
> - 本方向: first-moment signed cumulative（不去均值，带正负号累积）
>
> **lessons F001 vol_20d 吞噬律的边界探针**: 所有已记录验证都是 second-moment / higher-moment（std/var/skew/kurt/quantile）；本方向 first-moment signed accumulation **从未被独立测试**——结果将决定是否升格 F001 为"包括 first-moment signed accumulation 在内的所有 N-day 聚合都吞噬"或收紧为"second-moment 专属吞噬律"。
>
> **Operations**　`status: exploring (new)` · `priority: medium`（paper 是 catalog 性 102 指标横扫，非 single-mechanism；csi1000 上 first-moment signed accumulation 在 vol_20d 边界探针上风险高，不开 high）· `created_batch: batch_081`

> [!failure]+ 2026-05-03 · [[batches/batch_088/judge|batch_088]] — DISPROVEN, 方向翻 dead
> **batch_088 verdict**: 0 admit / 0 reserve / 6 reject. H1/H3 验证完毕, F001 vol_20d 律 first-moment 累积扩展实证.
>
> **关键证据**:
> - **C001 Chaikin(3,10)** alpha_surv=1.35 (Barra-cleanest) + 9/9 年负 + sign_consistency=1.0 + ls_t=-6.03 强 — **形式独立但 max_corr=0.63@F026 + incr_ic=-0.007 NEG → library_reducer hard_block**. paper |IC|=1.84% csi500 weekly → csi1000 daily ic_oos=-0.036 **反号**, 反向被库内 close-position cluster (F006/F008/F026) capture, 无独立 alpha.
> - **C005 Chaikin(6,20)** 同律 — alpha_surv=1.57 + max_corr=0.61@F008 + incr_ic=-0.005 NEG. C001 vs C005 窗口 ablation 同律: Chaikin EMA-差 family 整体 form-independent + library-overlapping.
> - **C002 AD-Sum-20** max_corr=0.36 LOW (整批最干净) + alpha_surv=0.466 刚过 0.40 floor — 但 mono_oos=-0.10 OOS quintile 结构破坏 + sign_consistency=0.75 + style_r²=0.27 poor + incr_ic=-0.004 NEG. **不满足 reserve fire 4 要件** (max_corr<0.30 + style_r² clean + sign_cons=1.0 + incr_ic borderline+).
> - **C003 PVT(20) / C004 PVT(60)** alpha_surv 0.11 / 0.16 << 0.40 floor + dom=vol_20d → first-moment signed × Vol Sum 直接落入 vol_20d 吸收律. **F001 律 first-moment 扩展实证** — 律边界从 second-moment magnitude 扩展到任何 N-day 累积形式.
> - **C006 PVT 60d rank-diff salvage** hard_gate sign_flip — PVT raw 已 dead, rank-diff wrap 失败, 与 lessons "rank-diff salvage 仅当 numerator 自身 alive" 律一致.
>
> **三 hypothesis 结论**:
> - **H1 (family 真度)** PARTIAL-DISPROVEN: form-level Barra-residual 独立成立 (alpha_surv 1.35-1.57) 但 cross-section rank 与库内 close-position cluster 同构, 无独立 alpha.
> - **H2 (Vol-dependent vs Vol-independent 子路径)** 仅 1 边证据: Chaikin/AD/PVT (Vol-dependent) 4/4 dead, ASI (Vol-independent OHLC-only) 因 daily DSL 不可达本批未测.
> - **H3 (vol_20d 吸收律 first-moment 例外)** DISPROVEN: PVT N=20/60 双窗 alpha_surv 0.11/0.16 << 0.40 floor → first-moment signed × Vol N-day Sum 也被吸收. 律边界扩展到"任何 N-day 累积形式 (含 first-moment signed × Vol)".
>
> **Thread 状态**:
> - T001 ASI: `[◉ DEFERRED → 不再测试]` — Vol-independent 子路径 python_runner 工程成本高 + 单一子路径不足以 sustain direction productive (其他 3 子路径已 dead).
> - T002 Chaikin/AD: `[✗ DISPROVEN-form-independent-but-library-overlap]`
> - T003 PVT: `[✗ DISPROVEN-vol_20d-absorbed-N=20-and-60]`
> - T004 vol-orthogonalized Chaikin salvage: `[✗ DISPROVEN-precondition-not-met]` — Chaikin numerator 自身 OOS 与库重叠, vol-ortho salvage 前提不满足.
>
> **方向翻 dead 充分理由**: round 1 0/6 admit + 0/6 reserve + 4/4 子路径 (Chaikin/AD/PVT 长短窗 + rank-diff salvage) DISPROVEN + T004 salvage 前提不满足 + T001 ASI 边界探针风险高且工程成本高且即使 alive 不足以 sustain. 不再投入 batch_089.
>
> **方向产出三条 lessons 升格证据 (Phase 5 consolidation 处理)**:
> 1. **F001 vol_20d 律 first-moment 扩展**: PVT(20)/PVT(60) C003/C004 alpha_surv 0.11/0.16 双窗实证, 律边界从"second-moment magnitude"扩展到"任何 N-day 累积形式 (含 first-moment signed × Vol Sum/EMA-差)".
> 2. **alpha_surv > 1.0 形式独立 ≠ library 充分条件 候选律第 3 次实证 (b086/b087/b088)**: C001/C005 alpha_surv 1.35/1.57 + incr_ic NEG + max_corr 0.61-0.63. 应升格"alpha_survival > 1.0 必配 incremental_ic > 0 双门槛".
> 3. **paper transferability 反号 + library overlap 双失败 (Chaikin 是新例)**: csi500 weekly multi-quantile +信号 → csi1000 daily 反号 + 反向被库内 close-position-only capture. lessons "Paper transferability" 段新增 close-position × Vol 反号律.
>
> **Operations**　`status: exploring → dead` · `rounds: 0 → 1` · `last_batch: batch_088` · `last_admits: []`
