---
direction_tag: gap_acceptance_structure
status: productive
priority: high
rounds: 4
admits: 3
last_batch: batch_051
last_admits:
- F020
last_goal: "T013 rank-diff 范式第 6 次跨家族泛化——测 gap-based scale-invariant signals × 非 overnight/turnover/amount\
  \ RHS 的 rank-diff 几何。\n\n当前 rank-diff 5 admit 跨 4 family (microstructure×2 / overnight×2\
  \ / OHLC×1 = F015/F016/F017/F018/F019)。\ngap_acceptance_structure 仅 F013 (log_amount_weighted\
  \ sign aggregation)，max_corr=0.085 整库低集中度，rank-diff\nparadigm 完全未测。本批检验：gap LHS\
  \ 能否在 rank-diff 几何中独立兑现？若 admit 则 6 跨家族 tipping point\n正式确认 (Phase 5 consolidation\
  \ 几乎必然触发)。\n\n设计硬约束：\n(1) 每候选 LHS 唯一 — 6 LHS 全不同 atomic gap 表达；\n(2) 严避免 F010/F011\
  \ 的 Mean(gap_ret, 3/5) 同形 — 用不同 normalizer (gap/(H-L) 而非 gap/Ref(close,1)) 或不同 moment\
  \ (Std vs Mean) 或不同时窗 (60d);\n(3) RHS 端避开 RHS 共振饱和律已标 endpoints (overnight_5/turnover_5/amount_20)，选\
  \ RV_60 / body_ratio_20 / amount_60 / pb_60 / price_vol / |return|_60 等非饱和 basis;\n\
  (4) 不用 CsRank 外包 AmihudIlliq/HHI/RealizedVol (operators.py:428 bug)；CsRank 内层全标准\
  \ DSL (Mean/Std/Abs/Sub/Div/Sign/Ref);\n(5) 不重演 T001 disproven (sign(gap)*sign(body)\
  \ pure aggregation) 也不重演 T003 disproven (gap magnitude 分母变体 → corr@F003=0.96);\n\
  (6) 不重演 b049/b050 disproven random walk LHS (intraday body sign / intraday return\
  \ mean).\n\nC001 gap_acceptance_ratio_20 × RV_60 — LHS=Mean(($open-Ref($close,1))/($high-$low),\
  \ 20) gap 归一化 intraday range\n  (与 F003 不同：F003 LHS 是 |gap|/Mean($high,5)，本 C001\
  \ 用 (H-L) 同期 range 而非历史 high mean)；\n  RHS=CsRank(RealizedVol($close,60)) 长窗 price\
  \ vol basis，区别 amount/turnover/overnight。\n  预期 max_corr@F010<0.4 (overnight pct\
  \ vs gap range-norm 量纲不同) + max_corr@F003<0.5 (5d high vs 1d range).\n\nC002 gap_return_volatility_20\
  \ × body_ratio_20 — LHS=Std(($open-Ref($close,1))/Ref($close,1), 20) higher moment\n\
  \  of gap return (vs F010/F011 Mean 是不同 moment family，b050 教训 \"Mean vs Std of same\
  \ atomic 不冗余\")；\n  RHS=CsRank(Mean(Div(Abs(Sub($close,$open)),Sub($high,$low)),20))\
  \ body_ratio_20 OHLC structural basis。\n  预期 max_corr@F010/F011<0.4 (Std vs Mean\
  \ independent) + max_corr@F019<0.5 (F019 LHS=Std(body_ratio), 本 C002 LHS=Std(gap_ret)).\n\
  \nC003 abs_gap_magnitude_60 × amount_60 — LHS=Mean(Abs(Sub($open,Ref($close,1))),\
  \ 60) absolute gap magnitude\n  长窗 (60d 非 20d，不是 sign 也不是 ratio，是 raw |gap| 长期均值)；\n\
  \  RHS=CsRank(Mean($amount,60)) amount 长窗 basis 避开 F018 amount_20。\n  预期 max_corr@F003<0.5\
  \ (F003 是 |gap|/range 标准化，C003 是 raw |gap| 无标准化 + 长窗 60d).\n\nC004 gap_to_body_cross_ratio\
  \ × pb_60 — LHS=Mean(Div(Abs(Sub($open,Ref($close,1))), Add(Abs(Sub($close,$open)),0.0001)),\
  \ 20)\n  跨日 gap 相对 intraday body 的相对幅度 (cross-session magnitude ratio, 0.0001 防\
  \ zero division 不构成 hack\n  因为是确定性常数偏置，不依据数据)；RHS=CsRank(Mean($pb_ratio,60)) fundamental\
  \ value 长窗。\n  预期 max_corr@F003/F010<0.4 (cross-ratio 完全新 atomic 表达).\n\nC005 gap_acceptance_ratio_5\
  \ × price_vol_20 — LHS=Mean(($open-Ref($close,1))/($high-$low), 5) C001 short-window\n\
  \  对照 (5d vs 20d, 测 window-window covariance with rank-diff geometry)；\n  RHS=CsRank(Mean(Std($close,5),20))\
  \ 价格 vol 聚合 basis (F019 的 RHS 复用，但 LHS 完全不同)。\n  预期 max_corr@F019<0.4 (LHS gap vs\
  \ body_ratio std 完全不同 atomic).\n\nC006 long_window_gap_vol × abs_return_60 — LHS=Std(Div(Sub($open,Ref($close,1)),Ref($close,1)),\
  \ 60) 长窗 60d\n  gap return vol (与 C002 的 20d Std 不同窗口 — 测 gap_vol 在 60d 是否仍独立)；\n\
  \  RHS=CsRank(Mean(Abs(Div(Delta($close,1),Ref($close,1))),60)) abs daily return\
  \ mean 60d (Amihud 分子部分,\n  不是 amount/turnover —— 全新 RHS 维度)。\n  预期 max_corr@F015\
  \ (amihud_cv) <0.4 (RHS 是 |return|_60 而非 amihud cv)."
last_activity: '2026-04-24T23:05:44Z'
created_batch: null
members:
- F013
- F{next}
- F020
merged_into: null
---
# gap_acceptance_structure

> [!abstract]+ 方向概要
> - **状态**　🟢 `productive` · priority `high` · rounds = 4 · admits = 3 (F013 / F020 / + log-amt path)
> - **最近**　[[batches/batch_051/judge|batch_051]] · 2026-04-25 · 1/1/4（T005 admit 触发 6 跨 5 family rank-diff tipping point）
> - **一句话**　pure paper-sign 不 transfer (T001 证伪)；存活两路：log(abnormal $amount) 加权 acceptance (F013) + rank-diff geometry × higher-moment gap LHS (F020)；下一步守 F002/F305 7 律 + F200/F203 阈值

---

## Hypothesis

> [!warning] ⚠️ Hypothesis 部分证伪（batch_035）+ 升格律
> 原假设"sign(gap) × sign(body) 的 20d 聚合在 csi1000 上携带独立 alpha"**被硬性证伪**——pure sign interaction 在 10/20/60d 三个窗口同步 sign_flip + ic_oos_too_low，2015-2020 全正 → 2021-2023 全负，regime 转折把符号吸收律从 "持续性" 翻成 "反转"。paper CSI 300 大盘 Rank IC 0.0744 不可迁移到 csi1000 小盘（[[lessons#Paper Transferability|F302/F006]] 已升格为 default 律，跨 trend_quality_gated 二次确认）。
>
> **存活两路**：
> 1. **log(abnormal $amount) 加权 acceptance**（T002 → F013）—— mono_OOS 0.30 → 0.60，IC_OOS=0.0094 ~8x paper 衰减但结构稳；线性 ratio / CsRank / 40d 窗口 5/5 全 reject。
> 2. **rank-diff geometry × higher-moment gap LHS**（T005 → F020）—— `Sub(CsRank(Std(gap_ret,20)), CsRank(Mean(body_ratio,20)))`，IC_OOS=-0.040 mono=-1.0/-1.0 完美 + 9/9 年同号 + max_corr=0.246@F016 整库唯一<0.30，是 [[lessons#Rank-Diff Geometry|F305]] "higher-moment LHS independence axis" 在 gap 家族的 family-agnostic 复现。
>
> **元教训汇编**（已升格 lessons.md）：
> - **A 股日频 sign aggregation 需 underlying drift 支持**（[[lessons#Sign Aggregation Drift|F006]]）：overnight 有 institutional accumulation drift（F018 admit），intraday body / gap sign 在 csi1000 是 random walk → pure sign 必死，需 log(amount) drift proxy 加权才可救。
> - **rank-diff 设计 7 硬约束**（[[lessons#Rank-Diff Geometry|F002/F305]]）：两端 scale-invariance / raw field 独立 / 同字段跨窗口禁止 / Sub 对偶 dedup / 同批 LHS anchor 至多 1 admit / RHS 共振饱和动态（已 dead RHS endpoints: overnight_5/turnover_5/amount_20/body_ratio_20/price_vol_20）/ saturated 方向 anchor cluster（F002/F012/F020）锁死。
> - **A 股 10% 涨跌幅 + OHLC algebraic mirror 双律**（[[lessons#OHLC Family Defaults|F005/F306]]）：gap 分母变体 (H-L / prev_close / Std(ret,20)) 都被 F003 主导（corr 0.79–0.96）；本方向 candidates 起手前必做 affine-equivalence 检查 + 避 H-L 分母 + 避 prev_close 分母组合，用 body_ratio_20 / |return|_60 等非 OHLC-co-moving RHS。
> - **Meta-pattern 跨方向迁移先验底层 alive**（[[lessons#Meta-pattern Transfer|F303]]）：log-compression 救 F013 是因 sign 已规整二值 + 噪声集中 magnitude 尾部；同款 log 在 value × liquidity 6/6 fail（底层 PB/PS/PE rank 已死）。本方向新 sign-based 候选必须先验 underlying field 的 rolling mean drift 显著非零。
> - **Threshold 校准**（[[lessons#Threshold Calibration|F200/F203]]）：rank-diff geometry candidates 因 structural vol_20d exposure 在 alpha_surv 0.30–0.40 区间是真实 alpha + 必然 style coupling，alpha_surv_min.rank_diff=0.30；max_corr ∈ [0.30, 0.70] borderline 时 incr_ic ≥ 0.015 才有 admit 资格。

---

## Current Focus

- **rank-diff 路径继续**：T007（cross-ratio LHS Barra 吸收律）active —— C004 alpha_surv=0.005 极端 collapse 揭示 ratio of two raw OHLC magnitudes 在 rank-diff 几何中是 style projection 的 rank rotation；下批可探 ratio of two **rank-transformed** magnitudes 是否同病、或 ratio + sign 复合是否破解
- **新 RHS 设计空间**：body_ratio_20 已被 F020 占用（dead RHS endpoint），下批寻找新 non-vol-class non-OHLC-co-moving RHS（候选：CsRank(Mean(|return|, 60)) Amihud 分子 / fundamental higher-moment / cross-stock dispersion 等）
- **避开已封 thread**：T001 纯 sign / T003 分母变体 / T004 窗口扫描 / T006 60d 长窗——四个 thread 已封闭；新候选起手须 pre-check 7 条 rank-diff 硬约束 + alpha_surv ≥ 0.30 + incr_ic ≥ 0.015 (max_corr borderline) 双门
- **F013 路径已 harvest**：T002 完成；新 sign-based 候选必须先验 underlying drift 才入候选集

---

## Threads

### T001: Gap × body sign interaction 的独立 alpha [✗ DISPROVEN batch_035]

> [!failure]+ Thread 结论
> **Question**: `sign(open - prev_close) × sign(close - open)` 的 20d 均值（或波动率归一版本）是否在 csi1000 上携带独立于 F009 spread / F010 persistence / F003 magnitude 的 cross-sectional alpha？
>
> **Answer**: 否。pure sign interaction 在 10d/20d/60d 三窗口同步 sign_flip——2015-2020 IC 全正、2021-2023 IC 全负，`ic_by_year` 展示 clean regime break。csi1000 小盘 universe 上 gap 符号本身在 2021 后噪声过大，符号对称抵消律**反向**（不是相消到零，是反号）。已升格 [[lessons#Sign Aggregation Drift|F006]]。
>
> **Evidence trail**:
> - [[batches/batch_035/candidates/C001|batch_035 C001]]　20d pure sign, IC_OOS=-0.0033 sign_flip + oos_decay=-0.47 → **reject (hard_gate)**
> - [[batches/batch_035/candidates/C002|batch_035 C002]]　10d pure sign, IC_OOS=-0.0020 sign_flip + oos_decay=-0.24 → **reject (hard_gate)**
> - [[batches/batch_035/candidates/C003|batch_035 C003]]　60d pure sign, IC_OOS=-0.0058 sign_flip + oos_decay=-1.03 → **reject (hard_gate)**
> - [[batches/batch_035/candidates/C006|batch_035 C006]]　magnitude×sign 混合 IC_OOS=0.0058<0.008 + mono=0.30 → **reject (hard_gate)**

### T002: Acceptance × abnormal volume 加权 [✓ ANSWERED batch_036]

> [!success]+ Thread 结论
> **Question**: 将 T001 的 acceptance 信号加权 `$amount / Mean($amount, 20)` 或 `$volume / Mean($volume, 20)`（strong participation 加重），是否比纯 acceptance 提供 incremental alpha？
>
> **Answer**: 是，**但仅在 log 非线性压缩下**。线性 ratio 加权（amount / volume / turnover TS-norm）在 csi1000 上全部 fail OOS（2021 regime break 把线性权重变成噪声放大器）；CsRank 变体把 magnitude 信息压平，也 fail。**log(abnormal_amount) 压缩尾部后** mono_OOS 从 0.30 翻倍到 0.60，IC_OOS=0.0094 通过阈值，9 年 8/9 年 IC 同号，anti-decay=1.36（OOS > IS）。教训已升格 [[lessons#Meta-pattern Transfer|F303]] —— log-compression 救 sign×body 是因 sign 已规整二值，跨方向不能机械复用。
>
> **Evidence trail**:
> - [[batches/batch_035/candidates/C004|batch_035 C004]]　`$turnover_rate` 直加权 20d acceptance, IC_OOS=0.0082 ls_t=3.90 mono_OOS=0.30 max_corr=0.054@F002 incr_ic=0.0098 → **reserve**（rank-order "avoid worst barbell"，非 monotonic）
> - [[batches/batch_036/candidates/C001|batch_036 C001]]　$amount 线性 ratio 加权 IC_OOS=0.0016 → **reject**（线性加权在 2021+ regime 放大噪声）
> - [[batches/batch_036/candidates/C002|batch_036 C002]]　$volume 线性 ratio 加权 IC_OOS=0.0013 → **reject**
> - [[batches/batch_036/candidates/C003|batch_036 C003]]　$turnover TS-norm 加权 IC_OOS=0.0013 → **reject**
> - [[batches/batch_036/candidates/C004|batch_036 C004]]　**log(abnormal amount) 加权** IC_OOS=0.0094 ls_t=3.23 **mono_OOS=0.60** incr=0.0071 → **admit → [[factors/F013]]**
> - [[batches/batch_036/candidates/C005|batch_036 C005]]　C001 40d 窗口扩展 IC_OOS=0.0022 → **reject**（超 signal_half_life=19d）
> - [[batches/batch_036/candidates/C006|batch_036 C006]]　CsRank($turnover) 加权 IC_OOS=0.0058 → **reject**（rank 化压平 magnitude）

### T003: TR-normalized gap 与 F003 的 near_duplicate 风险 [✗ DISPROVEN batch_035]

> [!failure]+ Thread 结论
> **Question**: `Div(Sub($open, Ref($close,1)), ...)` 系列以"非 Mean($high,N)"分母（paper 的 true range 归一，我们用 Std(ret,20) 代理）与 F003 的 cross-sectional corr 是否 < 0.7？
>
> **Answer**: 否。C005 用 `Std($close - Ref($close,1), 20)` 分母（与 F003 `Mean($high, 5)` 量纲正交），实测 corr=0.964@F003——gap magnitude 的分母量纲变体都会被 F003 的"分子主导"结构吸收。子空间 definitively closed。已升格 [[lessons#OHLC Family Defaults|F005]] 10% 涨跌幅 + OHLC algebraic mirror 双律。
>
> **Evidence trail**:
> - [[batches/batch_035/candidates/C005|batch_035 C005]]　Std(ret,20) 分母，max_corr=0.9635@F003 → **reject (hard_gate near_duplicate)**

### T004: 窗口敏感性与小盘 universe 特性 [✗ DISPROVEN batch_035]

> [!failure]+ Thread 结论
> **Question**: Paper 在 CSI 300 用 20d 聚合得到 Rank IC 0.0744，但 csi1000 小盘股流动性不足可能导致 gap 符号本身噪声过大 — 20d 是否仍是最优窗口？10d / 40d / 60d 如何？
>
> **Answer**: 窗口扫描无 "sweet spot"——10d / 20d / 60d 同步 hard_gate fail。csi1000 上 pure sign interaction 不是窗口问题，是**机制问题**（T001 同步 disproven）。长窗 60d 反而放大 regime 反号（C003 oos_decay=-1.03 最严重），短窗 10d 也无短记忆回救。
>
> **Evidence trail**:
> - [[batches/batch_035/candidates/C001|batch_035 C001]]　20d, hard_gate fail (与 T001 同源)
> - [[batches/batch_035/candidates/C002|batch_035 C002]]　10d, hard_gate fail (短窗同病)
> - [[batches/batch_035/candidates/C003|batch_035 C003]]　60d, hard_gate fail (长窗最重)

### T005: rank-diff 范式 × gap 家族第 6 次跨家族泛化 [✓ ANSWERED batch_051]

> [!success]+ Thread 结论
> **Question**: rank-diff geometry (CsRank(LHS) - CsRank(RHS)) 在前 4 family 5 admit (microstructure×2 / overnight×2 / OHLC×1) 后能否在 gap 家族独立兑现？若 admit → 6 跨家族 tipping point 正式确认 → Phase 5 consolidation 升格 lessons.md "rank-diff geometry" 通用规则.
>
> **Answer**: **是**。C002 (`Sub(CsRank(Std(gap_ret,20)), CsRank(Mean(body_ratio,20)))`) admit 为 F020 `gap_vol_body_ratio_rank_diff_20` — IC_OOS=-0.040 ICIR=-0.49 ls_t(IS)=-9.68 mono=-1.0/-1.0 完美 + 9/9 年同号负 + max_corr=**0.246@F016** 整库唯一 <0.30 + 与 5 admitted rank-diff (F015-F019) 全 |corr|<0.25 + 与同字段 F010/F011 corr 仅 -0.076/-0.073. **6 跨 5 family tipping point 确认** (microstructure×2 + overnight×2 + OHLC×1 + gap×1). 已升格 [[lessons#Rank-Diff Geometry|F305]] 五律 + F002 7 条硬约束。
>
> **三个关键 admit 维度同时满足**:
> 1. **higher-moment LHS** (Std vs F010/F011 Mean) — 验证 b050 T012 "Mean vs Std of same atomic 不冗余" 律在 gap 家族复现. **higher-moment LHS independence axis 横跨 family 兑现**.
> 2. **新 RHS 安全类目 body_ratio_20** — 扩展 RHS 共振饱和律白名单, body_ratio (OHLC structural) 非 vol-class basis 可脱 cluster（注：F020 admit 后 body_ratio_20 已成 dead RHS endpoint，b052 C002 复用即 cluster）.
> 3. **窗口适中 20d** 在 signal_half_life 内 (vs C006 的 60d sign_flip).
>
> **Evidence trail**:
> - [[batches/batch_051/candidates/C001|batch_051 C001]]　Mean(gap/(H-L),20) × Mean(Std($close,5),60), IC_OOS=+0.049 ls_t=3.75 mono=1.0/1.0 max_corr=0.55@F018 → **reserve** (rank-diff cluster co-resonance + incr_ic=0.008 边际)
> - [[batches/batch_051/candidates/C002|batch_051 C002]]　**Std(gap_ret,20) × Mean(body_ratio,20), IC_OOS=-0.040 mono=-1.0/-1.0 max_corr=0.246@F016 incr=-0.013** → **admit → [[factors/F020]]**
> - [[batches/batch_051/candidates/C005|batch_051 C005]]　Mean(gap/(H-L),5) × price_vol_20, IC_OOS=+0.049 但 max_corr=**0.696@F017** + incr_ic=0.003 → **reject** (短窗 LHS+RHS 加剧 cluster 共振)

### T006: gap 家族长窗 60d 边界律 [✗ DISPROVEN batch_051]

> [!failure]+ Thread 结论
> **Question**: gap 家族 atomic (raw |gap| / Std(gap_ret)) 在 60d 长窗下 rank-diff 几何能否兑现？测 signal_half_life 上限.
>
> **Answer**: 否. 60d 窗口在 gap 家族下双重失效:
> 1. **raw |gap| 60d (C003)**: IC_OOS≈0.0006 完全 dilution — 无 normalization + 60d 双重稀释让 rank 退化到 cross-sectional log_market_cap rank
> 2. **Std(gap_ret) 60d (C006)**: sign_flip train=-0.008 → val=+0.014 — 60d 包含 2-3 regime cycle, **Std 算子比 Mean 算子对窗口长度更敏感** (Std 测 dispersion 需稳定 sample, 多 regime 直接污染).
>
> **T002 b036 教训第 N 次复现**: gap 家族在 csi1000 上必须 (a) scale-free normalization (b) 窗口 ≤20d. 长窗在 rank-diff 几何中无救.
>
> **Evidence trail**:
> - [[batches/batch_051/candidates/C003|batch_051 C003]]　Mean(\|gap\|,60) × amount_60, IC≈0.0006 → **hard_gate ic_oos_too_low**
> - [[batches/batch_051/candidates/C006|batch_051 C006]]　Std(gap_ret,60) × \|return\|_60, sign_flip → **hard_gate**

### T007: cross-ratio LHS Barra 吸收律 [◉ ACTIVE batch_051]

> [!info]+ Thread 进行中
> **Question**: cross-ratio LHS (|gap|/|body| 跨 OHLC magnitude 比) 在 rank-diff geometry 下能否避开 Barra style 吸收?
>
> **Answer (initial)**: 不能. C004 (`Mean(|gap|/(|body|+0.0001),20) × pb_60`) **alpha_survival=0.005 极端 collapse** (本批最低, 整库罕见) — 两个 OHLC magnitude 折叠后投影完全在 Barra book-to-price + vol_20d 子空间. **rank-diff geometry 不替代 Barra orthogonality** (与 [[lessons#Threshold Calibration|F007]] "Barra-clean ≠ library-clean" 律对偶——该候选 Barra-dirty 而非 library-cluster).
>
> **新失败模式**: ratio of two raw magnitudes (cross-session 或 within-session) 在 rank-diff 几何中是 style projection 的 rank rotation, 非新 alpha. 下批可探: ratio of two **rank-transformed** magnitudes 是否同病; 或 ratio + sign 复合是否破解.
>
> **Evidence trail**:
> - [[batches/batch_051/candidates/C004|batch_051 C004]]　Mean(\|gap\|/(\|body\|+0.0001),20) × pb_60, alpha_surv=**0.005** + incr_ic=0.002 → **reject** (Barra 完全吸收 + F019 已捕获 92%)

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_035/candidates/C001\|C001]] | `Mean(Mul(Sign(Sub($open, Ref($close,1))), Sign(Sub($close,$open))), 20)` | hard_gate: sign_flip + ic_oos_too_low + oos_decay |
| [[batches/batch_035/candidates/C002\|C002]] | `Mean(Mul(Sign(Sub($open, Ref($close,1))), Sign(Sub($close,$open))), 10)` | hard_gate: sign_flip + ic_oos_too_low + oos_decay |
| [[batches/batch_035/candidates/C003\|C003]] | `Mean(Mul(Sign(Sub($open, Ref($close,1))), Sign(Sub($close,$open))), 60)` | hard_gate: sign_flip + ic_oos_too_low + oos_decay (最严重 cum_dd=-4.18) |
| [[batches/batch_035/candidates/C005\|C005]] | `Div(Sub($open, Ref($close,1)), Std(Sub($close, Ref($close,1)), 20))` | hard_gate: near_duplicate corr=0.964@F003 |
| [[batches/batch_035/candidates/C006\|C006]] | `Mean(Mul(Div(Sub($open, Ref($close,1)), Mean($high, 5)), Sign(Sub($close,$open))), 20)` | hard_gate: ic_oos_too_low (0.0058 < 0.008, mono=0.30) |
| [[batches/batch_036/candidates/C001\|C001]] | `Mean(Mul(Mul(Sign(gap), Sign(body)), Div($amount, Mean($amount, 20))), 20)` | hard_gate: ic_oos_too_low + oos_decay（线性 amount ratio 加权） |
| [[batches/batch_036/candidates/C002\|C002]] | `Mean(Mul(Mul(Sign(gap), Sign(body)), Div($volume, Mean($volume, 20))), 20)` | hard_gate: ic_oos_too_low + oos_decay（线性 volume ratio 加权） |
| [[batches/batch_036/candidates/C003\|C003]] | `Mean(Mul(Mul(Sign(gap), Sign(body)), Div($turnover_rate, Mean($turnover_rate, 20))), 20)` | hard_gate: ic_oos_too_low + oos_decay（TS norm turnover 加权） |
| [[batches/batch_036/candidates/C005\|C005]] | C001 formula @ 40d window | hard_gate: ic_oos_too_low（超 signal half-life 19d，稀释） |
| [[batches/batch_036/candidates/C006\|C006]] | `Mean(Mul(Mul(Sign(gap), Sign(body)), CsRank($turnover_rate)), 20)` | hard_gate: ic_oos_too_low（rank 化压平 magnitude）|
| [[batches/batch_051/candidates/C003\|C003]] | `Sub(CsRank(Mean(\|gap\|,60)),CsRank(Mean($amount,60)))` | hard_gate: ic_oos_too_low (raw \|gap\| 60d 双 dilution) |
| [[batches/batch_051/candidates/C004\|C004]] | `Sub(CsRank(Mean(\|gap\|/(\|body\|+0.0001),20)),CsRank(Mean($pb_ratio,60)))` | alpha_surv=0.005 (Barra 完全吸收) + incr_ic=0.002 + ls_t=1.17 三 dealbreaker |
| [[batches/batch_051/candidates/C005\|C005]] | `Sub(CsRank(Mean(gap/(H-L),5)),CsRank(Mean(Std($close,5),20)))` | max_corr=0.696@F017 cluster 共振 + alpha_surv=0.20 + incr_ic=0.003 |
| [[batches/batch_051/candidates/C006\|C006]] | `Sub(CsRank(Std(gap_ret,60)),CsRank(Mean(\|return\|,60)))` | hard_gate sign_flip (60d 多 regime cycle Std 失稳) |

---

## Related

- 🟢 [[overnight_intraday_split]] `productive` — F009 spread / F010-F011 persistence / F017/F018 rank-diff；本方向 T005 与 F018 (Mean(Sign(overnight)) × amount) 共享 sign aggregation drift dependency 律（F006），F020 与 F017/F018 全 |corr|<0.25 正交
- 🟡 [[intraday_price_formation]] `saturated` — F003 gap magnitude baseline + F020 anti-anchor 锁死 LHS 同源几何（b053 C001 max_corr=-0.694@F020）；T003 + T007 共同验证 OHLC 派生 candidate 的 affine cluster trap
- 🟢 [[ohlc_temporal_aggregation]] `productive` — F019 (Std body_ratio × price_vol) 是 higher-moment LHS independence axis 在 OHLC 家族首例；本方向 F020 在 gap 家族复现，跨 family 验证 family-agnostic 律
- 🔵 [[microstructure_illiquidity]] `productive` — F015/F016 rank-diff 起点；F020 max_corr=0.246@F016 是 rank-diff cluster 内最低集中度
- 🟡 [[value_liquidity_interaction]] `saturated` — F002 anchor cluster 边界律来源；本方向 RHS 设计须避 PB/PS 长窗类（C004 pb_60 + alpha_surv=0.005 验证）
- 🔴 [[trend_quality_gated]] `dead` — paper Channel 3 transfer 失败二次确认；与本方向 T001 Channel 1 失败一起升格 F302 paper transferability default 律
- 🔴 [[log_value_liquidity]] `dead` — meta-pattern 跨方向失败对照；F303 验证 log-compression 救 F013 不能机械复用
- 🔴 [[vol_shock_signals]] `dead` — magnitude-based vol 信号全 collapse 到 vol_20d；本方向 candidates dominant_style 多为 vol_20d 但 style_r² 低（F020 ≈0.30），rank-diff structural exposure 而非主阻断
- 📖 [[papers/arxiv_2602_07085v2]] — paper intake 种子；T001 反证 paper CSI 300 → csi1000 transfer 失败，T002/T005 找出两条本地存活路径
- 📖 [[lessons#Paper Transferability]] · [[lessons#Sign Aggregation Drift]] · [[lessons#Rank-Diff Geometry]] · [[lessons#OHLC Family Defaults]] · [[lessons#Meta-pattern Transfer]] · [[lessons#Threshold Calibration]] — 本方向贡献 / 引用的 6 个 lessons 段

---

## Narrative Log

> [!quote]+ 2026-04-25 · [[batches/batch_051/judge|batch_051]]
> **T005 ANSWERED · 第二个 admit：F020 gap_vol_body_ratio_rank_diff_20** · admit=1 (C002) / reserve=1 (C001) / reject=4
>
> - **rank-diff 范式第 6 次跨家族泛化兑现 — gap_acceptance_structure 首次 in family**: C002 LHS=Std(gap_ret,20) higher-moment + RHS=body_ratio_20 新 basis, IC_OOS=-0.040 ICIR=-0.49 ls_t(IS)=-9.68 mono=**-1.0/-1.0 完美** + 9/9 年同号负 + max_corr=**0.246@F016** 整库唯一<0.30 + 与 5 admitted rank-diff (F015-F019) 全 |corr|<0.25
> - **6 跨 5 family tipping point 已超 b050 标记的 5-family**: microstructure×2 (F015/F016) + overnight×2 (F017/F018) + OHLC×1 (F019) + gap×1 (F020) — Phase 5 consolidation 升格 lessons.md "Rank-Diff Geometry" 段（F002 7 条硬约束 + F305 五律 + F200 alpha_surv_min.rank_diff=0.30 阈值 + F203 incr_ic_min_when_corr_borderline=0.015 阈值）
> - **higher-moment LHS independence axis 横跨 family 兑现**: b050 在 OHLC 家族 (F019 Std body_ratio) 验证, 本批在 gap 家族 (C002 Std gap_ret) 复现 — Std vs Mean of same atomic 的 corr structure 完全不同律是 family-agnostic
> - **新 RHS 安全类目 body_ratio_20 → 退化为 dead endpoint**: F020 admit 后 body_ratio_20 进入 RHS 共振饱和黑名单（b052 C002 复用即 cluster 验证）
> - **新 dead RHS 类目 price_vol_20**: C005 max_corr=0.696@F017 与 F017/F010/F011 短窗 cluster 共振
> - **C001 reserve 而非 admit**: rank-diff cluster co-resonance + incr_ic=0.008 边际, alpha_surv=0.31 正落 F200 新阈值 0.30 上方但 incr_ic 不达 F203 0.015 标准
> - **T006 disproven (gap 60d 长窗双失效)**: C003 raw |gap| 60d ic≈0 + C006 Std(gap_ret) 60d sign_flip — **Std 算子比 Mean 算子对窗口长度更敏感**
> - **T007 active (cross-ratio LHS Barra 吸收律)**: C004 alpha_surv=0.005 极端 collapse — rank-diff geometry 不替代 Barra orthogonality
> - MT budget　cumulative 264 → **270** · direction 12 → **18** · bucket `high` (search_adjusted → medium)
>
> **Operations**　direction `saturated → productive` 重启 + `priority: medium → high` (admit=2 后扩展) · T005 `[新建] → [✓ ANSWERED batch_051]` · T006 `[新建] → [✗ DISPROVEN batch_051]` · T007 `[◉ ACTIVE]` 留作下批 follow-up · Python 在 Phase 4 backfill F020 链接

> [!quote]- 2026-04-24 · [[batches/batch_036/judge|batch_036]]
> **T002 ANSWERED · 首个 admit：F013 log_amount_weighted_acceptance_20** · admit=1 (C004) / reserve=0 / reject=5
>
> - log(abnormal $amount) 非线性压缩是关键：mono_OOS 从 batch_035 C004 的 0.30 翻倍到 **0.60**，IC_OOS=0.0094 · ls_t=3.23 · anti-decay=1.36（OOS > IS，极罕见）
> - 5 reject 候选覆盖 (amount / volume / turnover TS-norm / CsRank / 40d window) 五个正交变体 → T002 future_probes preemptively closed
> - 线性 ratio 加权在 csi1000 2021+ regime 下是"噪声放大器"，CsRank 化压平 magnitude，窗口扩展超 signal half-life=19d——只有 log 压缩同时保住 magnitude 信号 + 抑制极端天权重
> - paper 0.0744 Rank IC (CSI 300) → 我们 0.0094 (csi1000)，~8x 衰减，但结构稳健（mono + 9 年同号 + anti-decay）足以 admit
> - MT budget　cumulative 174 → **180** · direction 6 → **12** · bucket `medium`（C004 search_adjusted raw `high` → adjusted `medium`）
>
> **Operations**　T002 `[◉ ACTIVE] → [✓ ANSWERED batch_036]` · Python 在 Phase 4 会写 status 并 backfill F013 链接 · 方向维持 `saturated`（T001/T003/T004 早封闭 + T002 admit 单果）

> [!quote]- 2026-04-24 · [[batches/batch_035/judge|batch_035]]
> **首批即完成 T001/T003/T004 三 thread 信息性封闭** · admit=0 / reserve=1 (C004) / reject=5
>
> - T001 pure sign interaction 在 10/20/60d 三窗口同步 sign_flip + ic_oos_too_low + oos_decay——`ic_by_year` 2015-2020 全正 → 2021-2023 全负，regime 硬证伪
> - T003 `Std($close-Ref($close,1), 20)` 分母变体 corr=0.964@F003，确认"gap magnitude 分母量纲变体皆 near_duplicate F003"
> - T004 10/20/60d 无窗口 sweet spot，符号本身机制失效
> - T002 C004 是唯一正面证据：turnover 加权后过全部 hard gate，9 年 IC 同号全正、库独立，但 mono=0.3 的 "avoid worst barbell" 使 reserve 而非 admit——方向生路但形状待优化
> - 核心隐藏假设被实测印证：paper 0.0744 Rank IC 不 transfer 到 csi1000 小盘
> - MT budget　cumulative 168 → **174** · direction 0 → **6** · bucket `medium`
>
> **Operations**　`priority: high → medium`（T001/T003/T004 关闭，ROI 下调；保留 exploring 给 T002 变体探索一次机会）
