---
direction_tag: gap_acceptance_structure
status: saturated
priority: medium
rounds: 1
admits: 0
last_batch: batch_035
last_admits: []
last_goal: 'T001 + T003 + T004 baseline: probe pure sign-interaction acceptance (gap_sign
  × body_sign) at 10/20/60d windows on csi1000; test TR-via-realized-vol normalization
  against F003; seed turnover-weighted acceptance and a gap_magnitude × body_sign
  hybrid for orthogonality check against F003/F009/F010.'
last_activity: '2026-04-23T17:32:53Z'
created_batch: null
members: []
merged_into: null
---
# gap_acceptance_structure

> [!abstract]+ 方向概要
> - **状态**　🔵 `exploring` · priority `medium` · rounds = 0 · admits = 0
> - **最近**　[[batches/batch_035/judge|batch_035]] · 2026-04-24 · 0/1/5（首批 5 reject + 1 reserve C004）
> - **一句话**　paper CSI 300 大盘结果不 transfer 到 csi1000；T001/T003/T004 首批即封闭，唯一生路是 T002 turnover 加权（C004）

---

## Hypothesis

> [!warning] ⚠️ Hypothesis 部分证伪（batch_035）
> 原假设"sign(gap) × sign(body) 的 20d 聚合在 csi1000 上携带独立 alpha"**被硬性证伪**——pure sign interaction 在 10/20/60d 三个窗口同步 sign_flip + ic_oos_too_low，2015-2020 全正 → 2021-2023 全负，regime 转折把符号吸收律从 "持续性" 翻成 "反转"。paper CSI 300 大盘 Rank IC 0.0744 不可迁移。
>
> **存活**：turnover 加权的 acceptance（T002）—— C004 通过全部 hard gate，9 年 IC 同号全正，库独立 max_corr=0.054@F002，但 rank-order 为 "avoid worst barbell"（Q1 极负、Q5 也负、Q2-Q4 正），mono=0.3，非 monotonic alpha。方向唯一剩余探索角度。
>
> **元教训**：A 股日频 pure sign 乘积在小盘 universe 普遍存在 regime 翻号风险；需量能（turnover / $amount / abnormal vol）加权把噪声天数权重压低才有可能留住 edge。

---

## Current Focus

- 方向生路仅剩 T002：C004 已证 `$turnover_rate` 直接加权可过 hard gate 但 mono=0.3；下一批对照 `$amount / Mean($amount, 20)` 加权 / `$volume / Mean($volume, 20)` 加权 / normalized turnover 三变体，择优替换 C004 reserve
- 若 T002 后续 ≥2 批 0 admit 且对比变体全部 mono < 0.5，方向从 exploring 直接转 saturated；若 T002 变体中出现 mono_oos ≥ 0.5 且 Q5 转正 → 方向 pivot 为 turnover-weighted acceptance 专线
- 不再探 T001 纯 sign / T003 分母变体 / T004 窗口扫描——三个 thread 首批已封闭

---

## Threads

### T001: Gap × body sign interaction 的独立 alpha [✗ DISPROVEN batch_035]

> [!failure]+ Thread 结论
> **Question**: `sign(open - prev_close) × sign(close - open)` 的 20d 均值（或波动率归一版本）是否在 csi1000 上携带独立于 F009 spread / F010 persistence / F003 magnitude 的 cross-sectional alpha？
>
> **Answer**: 否。pure sign interaction 在 10d/20d/60d 三窗口同步 sign_flip——2015-2020 IC 全正、2021-2023 IC 全负，`ic_by_year` 展示 clean regime break。csi1000 小盘 universe 上 gap 符号本身在 2021 后噪声过大，符号对称抵消律**反向**（不是相消到零，是反号）。
>
> **Evidence trail**:
> - [[batches/batch_035/candidates/C001|batch_035 C001]]　20d pure sign, IC_OOS=-0.0033 sign_flip + oos_decay=-0.47 → **reject (hard_gate)**
> - [[batches/batch_035/candidates/C002|batch_035 C002]]　10d pure sign, IC_OOS=-0.0020 sign_flip + oos_decay=-0.24 → **reject (hard_gate)**
> - [[batches/batch_035/candidates/C003|batch_035 C003]]　60d pure sign, IC_OOS=-0.0058 sign_flip + oos_decay=-1.03 → **reject (hard_gate)**
> - [[batches/batch_035/candidates/C006|batch_035 C006]]　magnitude×sign 混合 IC_OOS=0.0058<0.008 + mono=0.30 → **reject (hard_gate)**

### T002: Acceptance × abnormal volume 加权 [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: 将 T001 的 acceptance 信号加权 `$amount / Mean($amount, 20)` 或 `$volume / Mean($volume, 20)`（strong participation 加重），是否比纯 acceptance 提供 incremental alpha？要与 F007 open_position_persistence_5d、`liquidity_acceleration` 方向候选做 redundancy 对比。
>
> **Evidence trail**:
> - [[batches/batch_035/candidates/C004|batch_035 C004]]　`$turnover_rate` 直加权 20d acceptance, IC_OOS=0.0082 ls_t=3.90 mono_OOS=0.30 max_corr=0.054@F002 incr_ic=0.0098 → **reserve**（rank-order "avoid worst barbell"，非 monotonic）
>
> **Next probes**: `$amount / Mean($amount, 20)` 归一加权 vs `$volume / Mean($volume, 20)` 归一加权 vs abnormal vol 加权三变体对照；核心审计 mono_OOS 能否从 0.30 拉到 ≥ 0.50 同时保持 9 年 IC 同号；与 F007 turnover-weighted body（已 reject）对比 delta 在哪里——F007 缺的是跨 session gap 符号，C004 差的是连续 body 强度

### T003: TR-normalized gap 与 F003 的 near_duplicate 风险 [✗ DISPROVEN batch_035]

> [!failure]+ Thread 结论
> **Question**: `Div(Sub($open, Ref($close,1)), ...)` 系列以"非 Mean($high,N)"分母（paper 的 true range 归一，我们用 Std(ret,20) 代理）与 F003 的 cross-sectional corr 是否 < 0.7？
>
> **Answer**: 否。C005 用 `Std($close - Ref($close,1), 20)` 分母（与 F003 `Mean($high, 5)` 量纲正交），实测 corr=0.964@F003——gap magnitude 的分母量纲变体都会被 F003 的"分子主导"结构吸收。子空间 definitively closed。
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

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_035/candidates/C001\|C001]] | `Mean(Mul(Sign(Sub($open, Ref($close,1))), Sign(Sub($close,$open))), 20)` | hard_gate: sign_flip + ic_oos_too_low + oos_decay |
| [[batches/batch_035/candidates/C002\|C002]] | `Mean(Mul(Sign(Sub($open, Ref($close,1))), Sign(Sub($close,$open))), 10)` | hard_gate: sign_flip + ic_oos_too_low + oos_decay |
| [[batches/batch_035/candidates/C003\|C003]] | `Mean(Mul(Sign(Sub($open, Ref($close,1))), Sign(Sub($close,$open))), 60)` | hard_gate: sign_flip + ic_oos_too_low + oos_decay (最严重 cum_dd=-4.18) |
| [[batches/batch_035/candidates/C005\|C005]] | `Div(Sub($open, Ref($close,1)), Std(Sub($close, Ref($close,1)), 20))` | hard_gate: near_duplicate corr=0.964@F003 |
| [[batches/batch_035/candidates/C006\|C006]] | `Mean(Mul(Div(Sub($open, Ref($close,1)), Mean($high, 5)), Sign(Sub($close,$open))), 20)` | hard_gate: ic_oos_too_low (0.0058 < 0.008, mono=0.30) |

---

## Related

- 🟡 [[overnight_intraday_split]] `saturated` — F009 spread / F010-F011 persistence 已占 overnight aggregation；本方向填 T004 SUSPENDED 留下的"第三种函数形式"空缺（sign interaction），但该空缺经 batch_035 证实**在 csi1000 上不存在 alpha**
- 🟡 [[intraday_price_formation]] `saturated` — F003 gap magnitude baseline；T003 验证了 "gap 分母量纲变体皆 near_duplicate F003" 的普适结论
- 🟡 [[ohlc_temporal_aggregation]] `saturated` — F007 已测过 turnover-weighted body 被 reject（corr=0.579@F007），本方向 T002 C004 与 F007 不同是 **含跨 session gap 符号**；C004 max_corr=0.054@F002、F007 相关=0.026 确认正交
- 🔴 [[vol_shock_signals]] `dead` — magnitude-based vol 信号全 collapse 到 vol_20d；本方向 6/6 candidates dominant_style=vol_20d，但 style_r² 全在 0.02-0.05 低段，不是主阻断
- 🔵 [[microstructure_illiquidity]] `saturated` — F012 amihud_illiq_20d
- 📖 [[papers/arxiv_2602_07085v2]] — paper intake 种子；**T001 结果反证 paper CSI 300 → csi1000 transfer 失败**
- 📖 [[lessons#Structural Constraints]] — 市值代理红线 / 向量化约束 / Barra residual 基线

---

## Narrative Log

> [!quote]+ 2026-04-24 · [[batches/batch_035/judge|batch_035]]
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
