---
direction_tag: nonlinear_autocorr_entropy
status: probing
priority: high
rounds: 2
admits: 0
last_batch: batch_104
last_admits: []
last_goal: 'Round 104 / nonlinear_autocorr_entropy NEW direction 首批. 库内 28 admit 100%
  用

  Mean/Std/Mul/Div/CsRank/TsRank/Corr/Cov 8 个基础 op; DSL 注册 25 custom op 中 ~10

  几何独立 op (TsAutoCorr/TsEntropy/TsDecay/WMA/Tanh/Sigmoid/SignedPower/RealizedVol/

  TsSkew/TsKurt) 完全 0 admit. 核心假说: vol_20d Barra-absorption 律是 LINEAR OLS

  投影律 (lessons.md "non-linear absorption" 段), 所以 Tanh / SignedPower / TsDecay /

  非线性 envelope 理论上能 break absorption. 6 候选刻意覆盖 ≥3 op family: (a) Tanh-envelope

  bounded close-position (C001), (b) TsAutoCorr regime classifier (C002), (c) TsEntropy

  turnover concentration (C003), (d) SignedPower momentum sqrt (C004), (e) WMA-vs-Mean

  bias (C005), (f) RealizedVol short/long ratio (C006). Anti-recap: (1) 不与 F002

  vwap_close / F004 std_vol / F010 hhi_vol 等已 admit 重叠 — 全部用未引用 op + 新参数;

  (2) 不踩 P004-deep 累积形式律 (无 Sum/Mean(residual,N) 顶层); (3) 不踩 b099/b101

  binarize 重演路径 (无 Gt/Lt × Mean event-rate); (4) 不踩 b068 vol_20d 显式吸收路径

  (RealizedVol 用 ratio 形式而非 raw). 关键观察点: alpha_surv > 1.0 + incr_ic > 0.005

  + max_corr<0.40 三角验证 vol_20d Barra basis 在非线性变换后是否仍吸收. P030/P033 全候选

  inline; min_listing_days ≥ 60 + coverage ≥ 0.80 hard_gate.'
last_activity: '2026-05-16T12:11:11Z'
created_batch: batch_104
members: []
---
# Nonlinear / AutoCorr / Entropy

> [!abstract]+ 方向概要
> - **状态**　🟡 `probing` · priority `high` · rounds = 1 · admits = 0
> - **最近**　batch_104 → admit=0 reserve=1 (C006 RV ratio) reject=5
> - **一句话**　测 DSL 注册但 0 admit 的非线性 op 族 (Tanh / SignedPower / TsDecay / WMA) + 时序统计 op (TsAutoCorr / TsEntropy / RealizedVol) 是否能 break vol_20d Barra-absorption 律

---

## Hypothesis

`vol_20d` Barra-absorption 律是 **LINEAR OLS 投影律** (lessons.md "non-linear absorption" 段). 库内 28 admit 100% 用 8 个基础 op (Mean/Std/Mul/Div/CsRank/TsRank/Corr/Cov), 而 DSL 注册的 25 custom op 中约 10 个**几何独立 op 完全 0 admit**:

- **Tanh / Sigmoid / SignedPower** — 非线性 envelope, |x| 大时进入饱和, 理论上 cap heavy tail 让 OLS β 投影不再吃满
- **TsAutoCorr** — autocorrelation regime (second-order time-series moment, 与 vol level 正交)
- **TsEntropy** — distribution shape information, 不是 magnitude
- **TsDecay / WMA** — 权重型 MA, 与 Mean 是 first-moment 但 weighting 不同
- **RealizedVol** — proper sqrt(sum sq) 形式; raw ≡ vol_20d 但 ratio 形式 cancel common mode
- **TsSkew / TsKurt** — third/fourth moments
- **HHI** — 仅 F010 admit, 其它字段 untouched

**核心待证**: 非线性变换 (Tanh / SignedPower) + 二阶/分布 op (TsAutoCorr / TsEntropy / TsSkew) **是否在 csi1000 daily forward return 上 alpha_surv > 1.0 且 incr_ic > 0.005** — 即是否携带 vol_20d basis 不能吸收的独立残差.

**batch_104 部分回答**：
- 单调 envelope (Tanh/SignedPower) → **disproven** (rank 同构 / 保 sign 加深 style 投影)
- ts-level autocorr/entropy → **disproven for csi1000 daily** (无 cs-spread / regime drift)
- **ratio 形式 (RV 5d/20d) → confirmed structurally** (alpha_surv=1.20, style_r²=0.072) 但 cs-rank 强度不够 admit；T004 锚点继续探索

## Threads

### T001 — Nonlinear envelope (Tanh / SignedPower) `[✗ DISPROVEN batch_104]`

> [!failure]+ Thread 结论
> **Question**: 有界压缩函数 (Tanh / Sigmoid) 或 power-cap (SignedPower) 是否让极端样本贡献饱和, 破 linear OLS absorption?
>
> **Evidence trail**:
> - [[batches/batch_104/candidates/C001|batch_104 C001]] Tanh(close/MA-1) → max_corr=**0.934@F027** (hard_gate near_duplicate) → **reject**。单调 envelope 顶层不改 cs-rank order。
> - [[batches/batch_104/candidates/C004|batch_104 C004]] SignedPower(20d ret, 0.5) → alpha_surv=**0.236** (poor), style_r²=**0.83** (poor), dom=**str_1m** exp=8.80, max_corr=**0.69@F027**, incr_ic=**-0.014** → **reject**。sqrt 保 sign 反而被 str_1m 更深吸收。
>
> **结论**: 单调 envelope 顶层套用与原信号 cs-rank 几何同构 (rank-identity) 或保 sign 加深 style absorption。要 break linear absorption 必须 (a) 配合 cross-term 改变 rank，或 (b) 在 aggregator 之前做 transform (Mean(SignedPower(ret_1d), 20) 而非 SignedPower(Mean(ret, 20)))。**Thread closed; lesson 候选写入 batch_104 judge.md 待 Phase 5 升格**。

### T002 — Second-order / distribution statistics `[✗ DISPROVEN batch_104]`

> [!failure]+ Thread 结论
> **Question**: autocorrelation / entropy / RealizedVol 是高阶时序统计, 几何与 vol level (first-order magnitude) 正交, 是否在 csi1000 daily 上携带独立 cs-spread alpha?
>
> **Evidence trail**:
> - [[batches/batch_104/candidates/C002|batch_104 C002]] TsAutoCorr(return_1d, 60) → ic_oos=**-0.0059** < 0.008 hard_gate fail; max_corr=0.13 库独立但 IS IC 也仅 -0.008 几乎噪音；vol_20d_exp=**18.18** 仍被深度 Barra 吃尽 → **reject**。autocorr 是 ts-level 而非 cs-level signal。
> - [[batches/batch_104/candidates/C003|batch_104 C003]] TsEntropy($turnover_rate, 60) → sign_flip train +0.0084 vs val -0.0076 + oos_decay=**-0.90** (反号) + ic_oos too low → **reject**。**2020-2021 regime drift**：低 entropy 从 attention pulse signal 翻为 crowding signal。
>
> **结论**: TsAutoCorr 在 csi1000 daily 上 cs-spread 不足（autocorr 是个股层面分布过窄）；TsEntropy on turnover 有真实 cs-spread (IS ICIR=0.13) 但 regime-time-variant，不适合静态 sign factor。**Thread closed for daily forward return** — 若坚持探索需 sliding sign-adaptive 形式 或 cs-difference transform。

### T003 — Weighted MA / Vol ratio (二阶组合形式) `[◉ ACTIVE]`

> [!note]+ Thread 当前
> **Question**: 通过差/比的形式让共同 vol 模式 cancel，是否产生独立 alpha?
>
> **Evidence trail**:
> - [[batches/batch_104/candidates/C005|batch_104 C005]] (WMA(10)-Mean(20))/Mean(20) → max_corr=**0.79@F028** (CMO 类), alpha_surv=**0.158**, style_r²=**0.74**, vol_20d exp=9.85, incr_ic=**-0.011** → **reject**。WMA-SMA 顶层差分被 cs-rank 抹平，与库内 close-position family 同构。
> - [[batches/batch_104/candidates/C006|batch_104 C006]] RV(5)/RV(20) → **alpha_surv=1.20**, style_r²=**0.072**, max_corr=**0.21@F022**, ic_oos=-0.017 (borderline), ls_t=-2.12 (边缘), mono_oos=-0.30 (Q5 一桨), incr_ic=-0.009 (微负) → **reserve**。**ratio 形式首次结构性 break vol_20d absorption**，但 cs-rank 强度不够 admit。
>
> **Next probes**: T004 接续做 RV ratio 参数扫描 (RV(3)/RV(20), RV(5)/RV(60), RV(10)/RV(40)) + cross-term (RV ratio × $amount / $turnover_rate)。本 thread 保 ACTIVE 因 C006 reserve 是锚点，下批可在此机制基础上提强度。

### T004 — Vol-of-vol ratio family 参数扫描 + cross-term 🆕 `[◉ ACTIVE]`

> [!note]+ Thread 当前
> **Question**: RV(short)/RV(long) ratio 已 confirm "cancel common vol mode" 结构性成立 (C006 alpha_surv=1.20)。能否通过 (a) 参数扫描找到 cs-rank 更强的窗口对 或 (b) cross-term (volume / amount / turnover) 让 vol-of-vol regime 信号穿越 cs-rank 阈值?
>
> **Evidence trail**:
> - (锚点) [[batches/batch_104/candidates/C006|batch_104 C006]] RV(5)/RV(20) — structural confirm + stat thin
>
> **Next probes**:
> - 参数扫描: RV(3)/RV(20), RV(5)/RV(60), RV(10)/RV(40), Std(ret,5)/Std(ret,20)
> - Cross-term: Mul(RV(5)/RV(20), CsRank($turnover_rate)), Div(RV(5)/RV(20), $amount/Ref($amount,20))
> - 替代分子: CV (Std/Mean) ratio 取代 RV ratio，cancel 共同 magnitude 而非共同 vol

## Adjacent dead patterns (反重演)

- **b099/b101 binarize × Mean event-rate**: 本批 0 个 Gt/Lt + Mean(binary, N) 形式 ✓
- **b068 vol_20d denominator absorption**: 本批 RealizedVol 用 ratio (C006) 不用 raw ✓ (实测 ratio 形式确实 break absorption)
- **P004-deep cumulative residual**: 无 Sum/Mean(residual, N) 顶层 ✓
- **F002/F010/F011/F021 已 admit 路径**: max_corr 重点查这几个 — 实测 C001/C004/C005 与 F027/F028 (close-position family) 高 corr，本方向**避开 F027/F028 子空间**

## Known Failures

- C001 `Tanh(Mul(Sub(Div($close, Mean($close, 20)), 1), 10))` — near_duplicate F027 (corr=0.934)
- C002 `TsAutoCorr(Sub(Div($close, Ref($close, 1)), 1), 60)` — ic_oos -0.0059 < 0.008
- C003 `TsEntropy($turnover_rate, 60)` — sign_flip train +0.008 / val -0.008 + oos_decay -0.90
- C004 `SignedPower(Mean(Sub(Div($close, Ref($close, 1)), 1), 20), 0.5)` — CP04 poor (alpha_surv=0.236, dom=str_1m) + max_corr=0.69@F027 + incr_ic=-0.014
- C005 `Div(Sub(WMA($close, 10), Mean($close, 20)), Mean($close, 20))` — CP04 poor (alpha_surv=0.158, vol_20d exp=9.85) + max_corr=0.79@F028 + incr_ic=-0.011

## Narrative Log

### 2026-05-16 [[batches/batch_104/judge|batch_104]]
admit=0 / reserve=1 (C006 RV 5d/20d ratio) / reject=5

**核心发现**：
1. **三种 absorption-failure 模式分类**：(a) 单调变换 ≡ rank 同构 [C001 Tanh]; (b) 单调变换保 sign 加深吸收 [C004 SignedPower]; (c) Top-level diff/bias 仍同 family 同构 [C005 WMA-SMA].
2. **ratio 形式是唯一 break vol_20d absorption 的结构** (C006 RV 5d/20d: alpha_surv=1.20, style_r²=0.072, max_corr=0.21 三角成立) — 首次在本系统结构性验证 [[lessons]] "non-linear absorption" 段提到的"分子分母 cancel common mode"猜想。但 cs-rank 强度仅 borderline 不够 admit。
3. **TsAutoCorr / TsEntropy on csi1000 daily forward return 无独立 alpha**：autocorr cs-spread 不足，entropy regime drift。这两 op 应转向 ts-level signal 或 sign-adaptive form。

**Thread 进展**：
- T001 nonlinear envelope: `DISPROVEN`（单调变换不破 absorption）
- T002 second-order ts statistics: `DISPROVEN for daily csi1000`
- T003 vol ratio: `ACTIVE` (C006 锚点 reserve)
- T004 vol-of-vol ratio family 参数扫描 + cross-term: 🆕 ACTIVE

**下一步**：batch_105 在 T003/T004 vol-of-vol ratio family 做参数扫描 + cross-term (RV ratio × turnover / amount)，目标把 cs-rank 强度从 ls_t=2.12 推到 3+。本方向 edge 仍存（T004 锚点 + lesson 候选），不进 saturated。
