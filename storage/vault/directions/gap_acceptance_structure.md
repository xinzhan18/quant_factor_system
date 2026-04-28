---
direction_tag: gap_acceptance_structure
status: saturated
priority: low
rounds: 6
admits: 3
last_batch: batch_062
last_admits: []
last_goal: "T007 推进 + 守 6 anchor cluster 防线 + higher-moment LHS 跨窗扩展。当前 rank-diff\
  \ 6 admit 跨 5 family\n(F015-F020), gap_acceptance 仅 F020 (Std gap_ret × body_ratio_20)\
  \ admit + F013 retired。T007 ACTIVE\n揭示 cross-ratio LHS (raw |gap|/|body|) 在 rank-diff\
  \ 几何下 alpha_surv=0.005 极端 collapse — Barra\n完全吸收。本批回答 T007 future probes 两条逃路 +\
  \ 同时探一条新 LHS 范式 + 一条 RHS 维度。\n\n6 候选硬约束：\n(1) 每候选 LHS 唯一 atomic gap 表达，6 LHS 不重复；\n\
  (2) 严避 F010/F011 Mean(gap_ret,3/5) 同形 + 不复用 body_ratio_20 / price_vol_20 / amount_20\
  \ /\n    overnight_5 / turnover_5 / pb_60 (alpha_surv=0.005 collapse) / amount_60\
  \ (F023 RHS) dead RHS;\n(3) 不重演 T001 disproven (sign×sign aggregation) / T003 disproven\
  \ (gap 分母变体 corr@F003=0.96) /\n    T006 disproven (60d Std 多 regime sign_flip);\n\
  (4) 4 anchor pre-check (F002/F012/F020/F022): 候选不可同时撞 LHS/RHS anchor;\n(5) 全 DSL,\
  \ CsRank 内层仅 Mean/Std/Abs/Sub/Div/Sign/Ref (不外包 Custom Op AmihudIlliq/HHI);\n(6)\
  \ 避开 Qlib bug Corr($close,$turnover_rate,N) 跨 base-field broadcast — 用 Mean/Med/Std\n\
  \    of single field 作 RHS proxy。\n\nC001 T007 follow-up A — RANK-TRANSFORMED ratio:\
  \ LHS=Sub(CsRank(Mean(Abs(gap),20)),CsRank(Mean(Abs(body),20)))\n  aggregated rank-diff\
  \ 替代 raw ratio (C004 alpha_surv=0.005 collapse) — 测 ratio of two CsRank-ed\n  magnitudes\
  \ 是否避开 OHLC magnitude affine cluster + Barra style projection;\n  RHS=CsRank(Std($turnover_rate,20))\
  \ liquidity higher-moment 全新 RHS 维度 (turnover_5 dead 但 Std,20 未试);\n  预期 max_corr@F020<0.4\
  \ (LHS 是 magnitude rank-diff 而非 Std gap_ret) + alpha_surv@T007 vs C004\n  cross-ratio\
  \ 决定 rank-diff geometry 是否真避 Barra。\n\nC002 T007 follow-up B — ratio + sign 复合:\
  \ LHS=Mean(Mul(Sign(Sub($open,Ref($close,1))),\n  Div(Abs(Sub($open,Ref($close,1))),\
  \ Add(Abs(Sub($close,Ref($close,1))),0.0001))),20)\n  signed gap-magnitude relative\
  \ to total daily move (gap+intraday) — 区别 C004 用 |body| 分母,\n  本候选用 |daily-return|\
  \ 分母 + 加 sign 提供方向信号 (T001 disproven pure sign 但本候选是\n  sign × magnitude 复合, 非 pure\
  \ sign);\n  RHS=CsRank(Mean($pe_ratio,20)) 短窗 fundamental rank — 区别 pb_60 死路 (regime\
  \ sign-flip 风险\n  低于 60d), pe_20 在库内未充当 RHS;\n  预期 max_corr@F003<0.4 (signed magnitude\
  \ 与 |gap|/range 不同) + 验证 sign 复合是否破 T007 Barra trap。\n\nC003 higher-moment LHS 跨窗扩展\
  \ — Std(gap_ret,10): LHS=Std(Div(Sub($open,Ref($close,1)),Ref($close,1)),10)\n \
  \ 短窗 10d Std gap_ret (vs F020 LHS 是 Std,20 — 不同窗口测 higher-moment LHS axis 是否跨 10d\
  \ 仍存活);\n  RHS=CsRank(Mean(Abs(Div(Sub($close,Ref($close,1)),Ref($close,1))),60))\
  \ Amihud 分子 |return|_60\n  (新 RHS, 之前未用, 是 amihud_illiq 的纯 |return| 项不含 amount 分母);\n\
  \  预期 max_corr@F020<0.5 (10d vs 20d 同 LHS atom 跨窗 rank corr) — 这是关键 dedup 检查,\n\
  \  若 max_corr ≥0.7 即 rank-diff 第 3 律违反 (同字段跨窗口禁止) → 自动 reject。\n\nC004 gap-direction\
  \ concentration (HHI-like): LHS=Mean(Div(Sub($open,Ref($close,1)),Sub($high,$low)),20)\n\
  \  gap relative to intraday range (与 C001 b051 不同处: C001 b051 是 Mean(gap/(H-L))\
  \ 5d,\n  本候选 20d 长窗 + 已知 b051 C001 reserve, 测 20d 是否跨 reserve→admit 边界);\n  RHS=CsRank(Mean(Abs(Sub($close,Ref($close,1))),20))\
  \ 20d daily-return-magnitude rank\n  (区别 |return|_60 in C003);\n  预期 max_corr@F020<0.4\
  \ (Mean vs Std of gap) + max_corr@F003<0.5 (gap/(H-L) vs |gap|/Mean($high,5))。\n\
  \nC005 gap acceptance asymmetry — IF-conditional aggregation:\n  LHS=Mean(Mul(Sign(Sub($open,Ref($close,1))),\
  \ Mul(Sub($close,Ref($close,1)),Sign(Sub($open,Ref($close,1))))),20)\n  展开为 sign(gap)\
  \ × signed daily-return on gap-direction (上 gap 后 t 日是否同向跟随 / 下 gap 后是否同向跟随,\n \
  \ 捕捉 gap 持续性 — 区别 T001 sign×sign 因为带 magnitude); 等价于\n  Mean(Mul(Sub($close,Ref($close,1)),\
  \ Sign(Sub($open,Ref($close,1)))),20) /\n  上式经数学化简 = sign(gap) × daily_return ×\
  \ sign(gap) × Sign(Sub($open,Ref($close,1)))\n  实际表达式简化为 LHS= Mean(Mul(Sub($close,Ref($close,1)),Sign(Sub($open,Ref($close,1)))),20)\n\
  \  (sign×sign×magnitude → sign×magnitude when sign² = 1);\n  RHS=CsRank(Std($amount,20))\
  \ amount higher-moment (区别 amount_60 F023 RHS 用 Mean);\n  预期 max_corr@F013<0.5 (F013\
  \ 是 sign×sign×log-amount, 本是 sign×magnitude×amount-vol) +\n  破 T001 因带 magnitude\
  \ 不是纯 sign。\n\nC006 gap × volatility-of-volatility complex — 新 LHS family:\n  LHS=Std(Div(Abs(Sub($open,Ref($close,1))),Add(Mean(Abs(Sub($open,Ref($close,1))),20),0.0001)),20)\n\
  \  rolling-std of normalized |gap| (gap magnitude 相对 20d gap-magnitude 均值的 rolling\
  \ 离散度);\n  完全新 LHS atom — gap \"volatility of normalization\", 测 second-order gap\
  \ structure;\n  RHS=CsRank(Mean(Sub($high,$low),20)) 20d intraday range mean (新\
  \ RHS 维度, range 而非 vol);\n  预期 max_corr@F020<0.5 (本 LHS 是 normalized gap 的二阶矩 vs\
  \ F020 是 raw gap_ret 的 Std) +\n  max_corr@F019<0.5 (F019 LHS 是 Std body_ratio, 本是\
  \ Std normalized |gap|, atomic 不同)。"
last_activity: '2026-04-28T07:28:19Z'
created_batch: null
members:
- F013
- F{next}
- F020
merged_into: null
---
# gap_acceptance_structure

> [!abstract]+ 方向概要
> - **状态**　🟡 `saturated` · priority `low` · rounds = 5 · admits = 3 (F013 / F020 / + log-amt path)
> - **最近**　[[batches/batch_062/judge|batch_062]] · 2026-04-28 · 0/0/6（T007 终结性 disproven · 7/7 thread 全 resolved）
> - **一句话**　两路 alpha harvested (F013 log-amt sign aggregation + F020 rank-diff higher-moment gap)；T007 cross-ratio Barra 吸收律全谱 disproven (rank-transformed/signed/ranged/signed-daily-change 全无救)；方向 thread 闭合, 等待外部条件 reactivation (paper / minute-bar / lib retire)

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

- **方向 thread 闭合 (b062)**：7 thread 全 resolved (T001/T003/T004/T006/T007 disproven + T002/T005 answered)；direction status `productive → saturated`, priority `high → low`
- **T007 终结性 disproven (b062)**：4 类 follow-up (raw rank-diff / signed cross-ratio / ranged Mean 长窗 / signed daily-change × amount-Std + Std normalized) 全 reject — cross-ratio LHS 在 csi1000 daily-bar rank-diff 几何下 dead-end
- **harvested alpha**：F013 (log-amt sign aggregation × T002) + F020 (rank-diff higher-moment Std(gap_ret,20) × body_ratio_20 × T005) — 两路 admit 已收, 不再继续 in-direction 探索
- **reactivation 条件**：(a) 新论文/教程提供 atom-level 新维度 (b) minute-bar 数据接入打开 intraday gap variance 路径 (c) 已 admitted gap factor 退役后 rank-diff cluster 有空间

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

### T007: cross-ratio LHS Barra 吸收律 [✗ DISPROVEN batch_062]

> [!failure]+ Thread 终结性 disproven
> **Question**: cross-ratio LHS (|gap|/|body| 跨 OHLC magnitude 比) 在 rank-diff geometry 下能否避开 Barra style 吸收? rank-transformed 或 sign 复合是否破解?
>
> **Answer**: 否, 全谱不破解. b051 raw cross-ratio (alpha_surv=0.005 极端 collapse) → b062 4 类 follow-up 全 reject:
> 1. **C001 raw rank-diff (Mean|gap| × Mean|body|)**: hard_gate ic_oos_too_low (无 normalization 退化 log_market_cap proxy)
> 2. **C002 signed cross-ratio (sign(gap)×|gap|/|return| × pe_20)**: alpha_surv=0.21 critical + incr_ic=+0.0009 essentially zero — **sign 在 cross-section rank 是 reflection symmetry, 不脱 Barra str_1m+book_to_price+vol_20d 子空间**
> 3. **C004 ranged-normalized Mean (gap/(H-L) Mean 20d × |daily_change| Mean 20d)**: alpha_surv=0.26 + vol_20d=42.86 极端 + max_corr=0.579@F018 borderline + incr_ic=0.0086<0.015 — **长窗放大 vol_20d 累积吸收**, 比 b051 C001 5d (alpha_surv=0.31) 更恶
> 4. **C005 signed daily-change × amount-Std**: alpha_surv=0.51 唯一 ≥0.40 BUT incr_ic=-0.0021 NEG — **P006 library-reducer (Barra 干净不等于 library 独立)**
>
> **新失败模式 + 升格律 (3 条)**:
> 1. **cross-ratio LHS 全谱 dead-end**: ratio of two OHLC magnitudes (任意 sign/rank/ranged 复合) 在 rank-diff 几何中 = ranked Barra style projection — sign 复合是 reflection symmetry, ranged normalize 是 ranked realized vol proxy
> 2. **Ranged-normalized LHS Mean 聚合窗口与 vol_20d 吸收单调正相关**: 短窗 5d 边际 (~0.30), 长窗 20d+ 必收 (~0.25)
> 3. **P006 library-reducer 第 7 次跨 family 复现 (gap_acceptance 首次)**: alpha_surv≥0.40 + library-reducer 双重检测必要 — Barra orthogonality 与 library independence 是两个独立 cleanness 维度
>
> **Evidence trail**:
> - [[batches/batch_051/candidates/C004|batch_051 C004]]　Mean(\|gap\|/(\|body\|+0.0001),20) × pb_60, alpha_surv=**0.005** + incr_ic=0.002 → **reject** (Barra 完全吸收 + F019 已捕获 92%)
> - [[batches/batch_062/candidates/C001|batch_062 C001]]　Mean(\|gap\|,20) × Mean(\|body\|,20) raw rank-diff, IC_OOS=-0.0048 → **hard_gate reject (ic_oos_too_low)**
> - [[batches/batch_062/candidates/C002|batch_062 C002]]　sign(gap)×\|gap\|/(\|return\|+ε) × pe_20 signed cross-ratio, alpha_surv=0.21 incr_ic=+0.0009 → **reject** (sign 不脱 Barra)
> - [[batches/batch_062/candidates/C003|batch_062 C003]]　Std(gap_ret,10) × \|return\|_60 higher-moment 短窗, sign_flip → **hard_gate reject** (10d 窗口跨 regime 不稳)
> - [[batches/batch_062/candidates/C004|batch_062 C004]]　Mean(gap/(H-L),20) × Mean(\|daily_change\|,20) ranged 长窗, alpha_surv=0.26 vol_20d=42.86 incr_ic=0.0086 → **reject** (长窗放大 vol_20d 吸收)
> - [[batches/batch_062/candidates/C005|batch_062 C005]]　Mean(daily_change × sign(gap),20) × Std($amount,20), ls_t=4.52 mono=1.0/1.0 alpha_surv=0.51 BUT incr_ic=-0.0021 NEG → **reject** (P006 library-reducer 第 7 次跨 family 复现)
> - [[batches/batch_062/candidates/C006|batch_062 C006]]　Std(\|gap\|/Mean(\|gap\|,20)+ε,20) × Mean(H-L,20) self-normalized 二阶, alpha_surv=0.019 critical + mono FLIP IS=-0.4 OOS=+1.0 → **reject** (regime-driven false discovery)

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
| [[batches/batch_062/candidates/C001\|C001]] | `Sub(CsRank(Mean(\|gap\|,20)),CsRank(Mean(\|body\|,20)))` | hard_gate: ic_oos_too_low (raw magnitude rank-diff 无 normalization 退化噪声) |
| [[batches/batch_062/candidates/C002\|C002]] | `Sub(CsRank(Mean(sign(gap)×\|gap\|/(\|return\|+ε),20)),CsRank(Mean(pe,20)))` | alpha_surv=0.21 critical + incr_ic=+0.0009 essentially zero (sign cross-section reflection 不脱 Barra) |
| [[batches/batch_062/candidates/C003\|C003]] | `Sub(CsRank(Std(gap_ret,10)),CsRank(Mean(\|return\|,60)))` | hard_gate 三连: sign_flip + ic_oos_too_low + oos_decay (Std 短窗 10d 跨 regime 不稳) |
| [[batches/batch_062/candidates/C004\|C004]] | `Sub(CsRank(Mean(gap/(H-L),20)),CsRank(Mean(\|daily_change\|,20)))` | alpha_surv=0.26 + vol_20d=42.86 极端 + incr_ic=0.0086<0.015 (长窗放大 vol_20d 吸收) |
| [[batches/batch_062/candidates/C005\|C005]] | `Sub(CsRank(Mean(daily_change×sign(gap),20)),CsRank(Std($amount,20)))` | ls_t=4.52 mono=1.0/1.0 alpha_surv=0.51 BUT incr_ic=-0.0021 NEG (P006 library-reducer 第 7 次跨 family 复现) |
| [[batches/batch_062/candidates/C006\|C006]] | `Sub(CsRank(Std(\|gap\|/Mean(\|gap\|,20)+ε,20)),CsRank(Mean(H-L,20)))` | alpha_surv=0.019 critical extreme + mono FLIP IS=-0.4 OOS=+1.0 (regime-driven false discovery) |

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

> [!quote]+ 2026-04-28 · [[batches/batch_062/judge|batch_062]]
> **T007 终结性 disproven · 方向 thread 完全闭合 (7/7 resolved)** · admit=0 / reserve=0 / reject=6
>
> - **T007 cross-ratio LHS Barra 吸收律 全谱 disproven**: 4 类 follow-up (raw rank-diff C001 / signed cross-ratio C002 / ranged Mean 长窗 C004 / signed daily-change × amount-Std C005 + Std normalized 二阶 C006) 全 reject — rank-transformed 与 sign 复合都不破解 Barra 吸收, sign 是 cross-section reflection symmetry, ranged normalize 是 ranked realized vol proxy. C003 hard_gate 三连 fail (Std 短窗 10d 跨 regime 不稳).
> - **P006 library-reducer 第 7 次跨 family 复现 (升格证据)**: C005 是 gap_acceptance 首次直接命中 P006 律 (前 6 次全在 microstructure_illiquidity). 6 lib factor corr ≥0.40, 5 ≥0.50 — 信号位置在 F002/F012/F015/F016 amount-Amihud + F018 overnight×amount + F023 multi-anchor cluster 中心. **alpha_surv=0.51 唯一 ≥0.40 BUT incr_ic=-0.0021 NEG** → Barra orthogonality 与 library independence 是两个独立 cleanness 维度.
> - **higher-moment LHS in ratio-of-magnitudes family 三种失败模式互补**:
>   1. **Sign-flip (C003 Std gap_ret 10d)**: 短窗跨 regime sample 不足 sign reversal
>   2. **Mono cross-sample reversal (C006 Std normalized |gap|)**: ratio-of-magnitudes 二阶聚合放大 normalizer 自身 regime drift, IS≈0 OOS 偶然正 false discovery
>   3. **Regime-stable persistent loss (b061 C002 Std atp-close-dev)**: atom 单日嵌入 vol_20d 几何 (P003)
> - **Ranged-normalized LHS Mean 聚合窗口与 vol_20d 吸收单调正相关**: b051 C001 5d (alpha_surv=0.31) → b062 C004 20d (alpha_surv=0.26 + vol_20d=42.86 极端) — 长窗放大 realized vol proxy, 而非 mitigate Barra 吸收
> - MT budget　cumulative 324 → **330** · direction 24 → **30** · bucket `high` (search_adjusted ≈ 0.49 → medium)
>
> **Operations**　direction `productive → saturated` + priority `high → low` (7/7 thread resolved 后自身可探索路径耗尽) · T007 `[◉ ACTIVE → ✗ DISPROVEN batch_062]` · zero_admit_streak 2 → 3 (b060/b061/b062) · 4 条升格 lessons 候选 (T007 全谱 dead-end + P006 第 7 次跨 family + higher-moment 三模式 + ranged-norm 窗口律) · calibration_trigger=false (累计 1 个独立 reserve 临界, 不达 ≥2 阈值)
>
> **复活路径**: (a) 论文/教程提供 atom-level 新维度 (b) minute-bar 数据接入打开 intraday gap variance (c) 已 admitted gap factor 退役后 rank-diff cluster 释放空间

> [!quote]- 2026-04-25 · [[batches/batch_051/judge|batch_051]]
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
