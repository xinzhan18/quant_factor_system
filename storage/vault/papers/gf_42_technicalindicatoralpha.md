---
paper_slug: gf_42_technicalindicatoralpha
source_pdf: raw/papers/GF-42-TechnicalIndicatorAlpha.pdf
source_kind: generic_pdf
arxiv_id: null
status: converted
primary_frequency: daily
direction_tag: signed_money_flow_oscillator
reviewed_at: 2026-05-02
---

# 广发金工 42 — 海量技术指标掘金 Alpha 因子（102 个经典技术指标 A 股横截面排序回测）

## Core Claim

广发金工系列报告之四十二在 2010-01-01 至 2021-06-15 中证 500 universe 上对 **8 大类、62 小类、共 102 个经典技术指标**（趋向 / 反趋向 / 能量 / 成交量 / 量价 / 摆动 / 强弱 / 其他）做 cross-sectional 排序法回测：周度换仓，标准化后取暴露 top 20% / bottom 20% 构造多空，统计 IC、ICIR、多头年化收益率、多空胜率、最大回撤等。**结论是一张 102-行排名表**——按 |IC| 排序前 15 名为 BIAS(6) 3.43% / VSTD(20) 3.02% / BBI_Close 2.74% / ASI(SI) 2.71% / VSTD(10) 2.70% / 成交金额方差(20) 2.59% / MACD 2.58% / 价格线性回归系数(6) 2.55% / VEMA 2.52% / BIAS(12) 2.30% / 成交金额方差(6) 2.29% / 已实现偏度 2.22% / ROC(6) 2.21% / PVT(6) 2.16% / BIAS(24) 2.06%；按多空胜率前 15 名头部为已实现偏度 67.58% / Chaikin Oscillator 62.12% / 成交金额方差(6) 61.26% / ASI(SI) 61.09% / AD 60.58% / 成交金额方差(20) 60.41% / 价格线性回归系数(6) 59.90% / BIAS(6) 59.39% / VSTD(20) 59.39% / AD(6) 59.22% / 成交金额(20) 59.22% / VSTD(10) 59.22% / VRSI 59.04% / VEMA 58.70% / ACD(6) 58.53%。

报告本质是 **catalog**——没有原创信号，没有特定 mechanism，价值在于**把 102 个经典技术指标的 IC/ICIR 真值排成一个单一表格**，让后人可以看到：(a) 哪些经典指标在 A 股 weekly cross-section 上有显著 |IC|；(b) 哪些经典名号（KDJ、RSI、ROC 25、UOS、DMI、Aroon、Hurst、Mass Index、TRIX）实际上 |IC| < 0.005 几乎为 0。这张表对当前仓库的真正用法是 **"反向裁剪"**——库内 25 个 admitted 因子已经覆盖了 BIAS（→ F021 / F022 range_compression）、VSTD（→ F004 std_vol_20、F010 hhi_vol_20）、成交金额方差（→ F001 std_returns_20、F002）、价格线性回归系数（→ Slope 已是白名单算子，F015/F018 alpha053 系列）、ROC/MTM（→ asymmetric_momentum DEAD、return_momentum_acceleration DEAD）、KDJ（→ stochastic_position SATURATED）、RSI/已实现偏度（→ return_distribution_signals DEAD）、W%R / Williams %R（→ anchor_proximity_momentum 刚开）、ATR（→ vol_shock_signals DEAD）。**剩下未覆盖的 IC 高分指标**几乎集中在一族：**signed money-flow oscillator family**——ASI（Wilder accumulated swing index）、Chaikin Oscillator（EMA(AD,3)−EMA(AD,10)）、AD（William's accumulation/distribution）、PVT（price-volume trend cumulative）、MACD（dual-EMA-of-close difference）。这族的几何共性是 **"signed close-position-in-range × volume → cumulative or smoothed difference"**，与库内 F009 pv_corr_times_vol（**correlation** 形式）和 F008 ret_vol_cov（**covariance** 形式）数学结构上不同。

回测设定：universe 中证 500、周频换仓、标准化后排序、IC 等于 cross-sectional Spearman、未做 Barra style neutralize、未做 csi1000 small-cap 测试。

---

## Aha Moment

**广发用 |IC| / 多空胜率排序 102 经典技术指标后，A 股 weekly cross-section 上"幸存者长尾"集中在一个数学形态相同的小族——signed close-position-in-range × volume → cumulative/smoothed → difference (or pure cumulative)**：ASI、Chaikin Oscillator、AD、PVT 同享 `Mul(Sign-of-something, Vol_or_money)` × 时间累加 / EMA 平滑 的几何骨架，与 F009 pv_corr 的 `Corr(Δ价, Δ量)` 完全不同。F009 测**同步性**（去均值后两序列相关），ASI/Chaikin/AD/PVT 测**signed 累积流向**（带方向的 dollar/volume 累积）；前者是 second-moment correlation，后者是 first-moment signed accumulation。库内 25 admitted 因子里**没有任何一个**是"signed × cumulative volume"形态，所以这一族在 csi1000 上有真实的 prior 概率携带 vol_20d-orthogonal 的 alpha——尤其是 ASI 的 4-branch IF 切换 + 二阶混合（`Max(AA,BB)`-driven scaling）几何复杂度远高于库内任意因子，恰恰可能逃出 csi1000 daily-bar 上反复发生的 vol_20d 吞噬律。

---

## Candidate Ideas

### Idea 1 — ASI (Accumulated Swing Index, Wilder)
- **Paper mechanism**: 表103 |IC|=2.71% (rank #4)、多空胜率 61.09% (rank #4)、ICIR=-0.250、多头年化 13.45%、多空年化 20.44%。Wilder 1978 创立。原始公式（paper Page 13）：
  ```
  LC = Ref(C, 1)
  AA = |H − LC|; BB = |L − LC|; CC = |H − Ref(L,1)|; DD = |LC − Ref(O,1)|
  R = if AA > BB and AA > CC: AA + BB/2 + DD/4
       elif BB > CC and BB > AA: BB + AA/2 + DD/4
       else: CC + DD/4
  X = C − LC + (C − O)/2 + LC − Ref(O, 1)
  SI = 16 * X / R * Max(AA, BB)
  ASI = Sum(SI, N)        # paper 用 N = 20
  ```
  机制叙事：把每日 OHLC 与 prev_OHLC 的 8 个差量整合成一个带符号的"摆动单位"，再 N 日累加。
- **Target frequency**: daily
- **Current readiness**: `python_ready`（branched IF on three conditions 不易用纯 DSL 表达；用 `Max/Sub/Abs/Sign` 嵌套可勉强但 readability 差，python_runner 更干净）
- **Required fields**: `$open, $high, $low, $close`（不含 volume；这是 ASI 与下面 4 个 money-flow 兄弟的关键差分——ASI 是纯 OHLC swing，不依赖成交量）
- **Why it may survive daily downsampling**: 全部用日 OHLC，不需要分钟级数据；4-branch IF + Max-driven scaling 是 csi1000 库内未出现的几何，与 vol_20d 的 power-mean 同构关系不显然。
- **Main distortion risk**: 累加形式 `Sum(SI, N)` 受 csi1000 涨跌停 ±10% 限制——单只极端日的 SI 会被 truncate，cross-section 排名可能在大波动时段被 censored。需要先验证 N=20 的 SI 累加值在 cross-section 上不被极少数极端日主导（先看 Skew of |SI| within 20-day window）。
- **Suggested direction tag**: `signed_money_flow_oscillator`（main thread T001）

### Idea 2 — Chaikin Oscillator (signed money-flow EMA difference)
- **Paper mechanism**: 表103 |IC|=1.84% (rank #18 by |IC| but rank #2 by 多空胜率 62.12%)、ICIR=0.181（注意：paper 表中 IC 为正、ICIR 为正且 magnitude 偏小，但多空胜率全表第 2 仅次于已实现偏度，提示 sign-stability 极强）。原始公式（paper Page 14）：
  ```
  AD = Vol * [(C − L) − (H − C)] / (H − L)        # signed close-position weighted by Vol
  Chaikin Oscillator = EMA(AD, 3) − EMA(AD, 10)   # short-term EMA minus long-term EMA of AD
  ```
  机制叙事：Williams' AD 已经把"close 在日内 H-L 范围里的 signed 位置"用成交量加权（C 偏 L 时 AD<0，C 偏 H 时 AD>0），Chaikin 再做"短 EMA − 长 EMA"差，等价于 AD 的 MACD 形式——抓 money flow 的加速度。
- **Target frequency**: daily
- **Current readiness**: `dsl_ready`
- **Required fields**: `$close, $high, $low, $volume`
- **Why it may survive daily downsampling**: 全部日频；多空胜率 62% 在 102 因子中几乎最高，提示信号 sign-consistency 远强于 IC 量级（这是 ICIR 偏低但胜率偏高的典型 "weak-signal-but-stable" 模式，正是 csi1000 daily 上需要的）。AD 的 `(C-L)-(H-C)` = `2C-H-L` = "close-mid_of_HL" 的 2 倍，所以 AD = `Vol * (2C - H - L) / (H - L)` —— 这是 close 在 H-L 中的 signed 位置 × Vol，库内**没有**任何 admitted 因子用这一几何。Chaikin 的 EMA-差再加一层 momentum-of-money-flow。
- **Main distortion risk**: 与 F009 pv_corr_times_vol（Grade A, score 79.9）的 max_corr 是关键检测点——F009 的 `Corr($close, $volume, N) * $volume` 测的是价量同步性，与 AD 的 signed close-position × vol 是两条不同物理路线，但 cross-section 上可能因都重 vol-load 而 cluster。设计候选时必须在 generator 阶段算 Corr(Chaikin_Osc, F009)；若 > 0.70 直接弃选。次要风险：分母 `H-L` 在涨跌停日可能很小（H ≈ L）导致 outlier，需要在 python_runner 中用 `H - L + epsilon` 或 winsorize。
- **Suggested direction tag**: `signed_money_flow_oscillator`（main thread T002）

### Idea 3 — AD (Williams Accumulation/Distribution, no EMA wrapper)
- **Paper mechanism**: 表103 AD 指标 |IC|=1.44% (rank ~25)、多空胜率 60.58% (rank #5)；AD(20) |IC|=1.30% 多空胜率 55.12%；AD(6) |IC|=1.19% 多空胜率 59.22%（paper 测了 3 个窗口长度 + 无窗口的纯累加版）。AD(6) 最优。原始公式（同 Idea 2 的 AD 子项）：
  ```
  AD_t = Vol_t * [(C_t − L_t) − (H_t − C_t)] / (H_t − L_t)
  AD_factor = Sum(AD, 6)        # 6-day cumulative
  ```
- **Target frequency**: daily
- **Current readiness**: `dsl_ready`
- **Required fields**: `$close, $high, $low, $volume`
- **Why it may survive daily downsampling**: 是 Idea 2 的 AD 原料 + 简单累加而非 EMA-差；如果 Idea 2 的"加速度"形式与 Idea 3 的"水平"形式都进 reserve/admit，提示 family 结构稳健；若 Idea 2 admit 而 Idea 3 reject，提示 EMA-差的 momentum 维度才是真信号。
- **Main distortion risk**: 同 Idea 2 的 H-L 涨跌停 epsilon 问题；与 Idea 2 的 Chaikin Oscillator 在数学上必然高 corr（同一 AD base + 不同时间聚合），所以 Idea 2 / Idea 3 应**对称设计**作为消融对照而非两个独立 admit 候选——若 Idea 2 admit，Idea 3 应作为 ablation 留 batch_081。
- **Suggested direction tag**: `signed_money_flow_oscillator`（T002 ablation）

### Idea 4 — PVT (Price-Volume Trend, signed dollar momentum cumulative)
- **Paper mechanism**: 表103 PVT |IC|=1.98% 多空胜率 57.34%、PVT(6) |IC|=2.16% (rank #14) 多空胜率 56.66%、PVT(12) |IC|=1.48% 多空胜率 51.88%。PVT(6) 综合最优。原始公式（paper Page 20）：
  ```
  PVT_t = (C_t − Ref(C, 1)) / Ref(C, 1) * Vol_t
  PVT_factor = Sum(PVT, 6)        # 6-day rolling cumulative
  ```
  机制叙事：每日 daily-return × Vol = "signed 成交量"，N 日累加得到一段时间的 net signed dollar flow（与 OBV 类似但 OBV 是 sign(ret)*Vol，PVT 是 ret*Vol，含幅度信息）。
- **Target frequency**: daily
- **Current readiness**: `dsl_ready`
- **Required fields**: `$close, $volume`
- **Why it may survive daily downsampling**: 全部日频，几何上是 `Sum(daily_return * Vol, N)`——与库内 F009 `Corr * Vol` 几何不同（F009 是去均值后的 second-moment 同步，PVT 是 first-moment signed 累积）；与 F008 `Cov` 也不同（Cov 是去均值后乘积均值，PVT 是含正负号的累加，不去均值）。
- **Main distortion risk**: PVT 与 OBV (paper 也测了，OBV |IC|=1.42% 多空胜率 57.68%) 几何高度相关——若 PVT admit 应同时确认 OBV 不是更强候选（paper 数据点：OBV 多空胜率 57.68% > PVT(12) 51.88% 但 < PVT(6) 56.66% < PVT 全样 57.34%；OBV 是 sign-only，PVT 含幅度，理论上 PVT 应携 OBV 的子信息+幅度信息）。涨跌停日 daily_return 被 cap 在 ±10%，导致 PVT 的极值 truncate——需先 sanity check 6 日累加值的 cross-section dispersion。
- **Suggested direction tag**: `signed_money_flow_oscillator`（main thread T003）

### Idea 5 — Chaikin Oscillator × volume-orthogonalize variant (long-tail extension, NOT in paper)
- **Paper mechanism**: paper 没直接测，但是 Idea 2 的几何延伸——既然 AD 已经把 `Vol` 嵌入分子，再做 EMA-差后**额外除以** `Mean(Vol, 20)` 做 vol-level 归一化，可能进一步消除 vol_20d 的 style loading（这是当前仓库 lessons F001 / F301 vol_20d 吞噬律明确指出的"逃离路径之一：scale-free / vol-orthogonalize"）。具体：
  ```
  AD_t = Vol * (2*C - H - L) / (H - L)
  Chaikin = EMA(AD, 3) - EMA(AD, 10)
  Chaikin_norm = Chaikin / Mean(Vol, 20)        # vol-level 归一化
  ```
- **Target frequency**: daily
- **Current readiness**: `dsl_ready`
- **Required fields**: `$close, $high, $low, $volume`
- **Why it may survive daily downsampling**: paper 没测但是基于本仓库 lessons 系统化"防 vol_20d 吞噬"原则的 modification——若 Idea 2 raw Chaikin 在 csi1000 上 dominant_style=vol_20d 暴露 > 5（按 stochastic_position 8.7-16.5、range_structure 反复出现的同一律先验），则 vol-orthogonal 版本是 salvage 路径；若 Idea 2 已经低 vol_20d 暴露（<3），则本 Idea 是冗余对照。
- **Main distortion risk**: 加分母 `Mean(Vol, 20)` 后单位变成 `(2C-H-L)/(H-L) * Vol/Vol_mean × EMA-diff`，可能与 F033/F029 mean_turnover 类信号通过 `Vol_t/Mean(Vol)` 这一项产生 medium corr。
- **Suggested direction tag**: `signed_money_flow_oscillator`（T002 salvage path，留 batch_081）

### Idea 6 — CCI (Commodity Channel Index — typical-price normalized by MAD, NOT cleanly novel but worth noting)
- **Paper mechanism**: 表103 CCI |IC|=1.67% 多空胜率 55.97%。原始公式（paper Page 14）：
  ```
  TYP = (H + L + C) / 3
  CCI = (TYP - MA(TYP, M)) / (0.015 * MeanAbsDev(TYP, M))
  ```
- **Target frequency**: daily
- **Current readiness**: `dsl_ready`（MAD 用 `Mean(Abs(Sub(TYP, Mean(TYP, M))), M)` 表达）
- **Required fields**: `$high, $low, $close`
- **Why it may survive daily downsampling**: TYP=(H+L+C)/3 与 close 的 corr 在 csi1000 上必然 > 0.99（lessons F005 OHLC algebraic 共动律），所以 CCI 实际上 ≈ `BIAS(C, M) / (0.015 * MeanAbsDev(C, M))`——相当于 BIAS 除以一个"close 的离差均值"。BIAS 已被 F021/F022 range_compression 系列覆盖；CCI 的"创新"仅在分母——这个分母本身是 vol_20d 的同构（`MeanAbsDev` ≈ `0.798 * Std`，cross-section 上必然高度 vol-load）。即 CCI = `BIAS / vol_proxy`，是"BIAS scale-free 化"，但 lessons F001 已经反复验证 scale-free 不能单独脱离 vol_20d 吞噬（range_structure b045 C006 例）。
- **Main distortion risk**: max_corr@F021 / F022 / BIAS-family 大概率 > 0.6；alpha_survival 大概率 < 0.3——本 Idea 几乎确定是"BIAS reducer"。**不推荐**作为本方向首批候选；列在这里是为了告诉未来重读者"这条路被 lesson F001 + F005 双重证伪，不要再造"。
- **Suggested direction tag**: `(blocked_by_library_coverage + blocked_by_lessons F001/F005)`

---

## Data Requirements

**论文依赖**:
- 日频 OHLC + Vol（`open, high, low, close, volume`）— 全部在白名单
- 周频换仓 + 中证 500 universe — paper 用周频，本仓库默认日频；候选可以用 daily-bar 跑 IC（横截面 frequency 不变，标签依然是 N 日 forward return），不需要切换 universe
- 标准化（cross-sectional zscore）— Phase 2 默认行为
- IC = cross-sectional Spearman / 多空收益、多头年化 — Phase 2 已有

**我们缺什么**:
- 无（所有字段全在白名单；ASI 的分支 IF 在 DSL 上需嵌套 `Max/Sub/Abs/Sign`，python_runner 路径更干净，但都不算缺）

**DSL 算子对照**（paper 侧 → 我们侧）:
- `MA, SMA, EMA` → `Mean, EMA`（白名单 SMA 不可用，论文里的 `SMA(x, N, 1)` 含权重参数 1，等价于 EMA-style 的 Wilder smoothing；我们用 `EMA` 替代）
- `REF` → `Ref`
- `ABS` → `Abs`
- `MAX, MIN`（标量两数取大）→ `Max, Min`
- `IF` 条件分支 → DSL 用 `Mul(Sign(...), ...)` 组合或退到 `python_runner`
- `SUM(x, N)` 滚窗求和 → `Mul(Mean(x, N), N)` 或直接 `RollSum`（若已注册）；若无 RollSum，用 `Mean × N`
- `LLV / HHV`（rolling min/max of low/high）→ `TsMin / TsMax`
- `AVEDEV(TYP, M)` 平均绝对离差 → `Mean(Abs(Sub(TYP, Mean(TYP, M))), M)`
- 涨跌停日的分母小数 → 加 epsilon 或 winsorize（在 python_runner 中处理）

---

## Mapping To Current System

**已被覆盖（不开新方向 / 不进首批）**:
- BIAS(6/12/24)、价格线性回归系数(6/12) → range_structure / trend_residual_geometry / F021/F022 已占位
- VSTD(10/20)、成交金额方差(6/20)、成交金额(20) → F001/F002/F004/F010/F043 amount_volatility_signal 完整覆盖
- KDJ(K/J/D)、StochRSI、W%R(9/15/20) → stochastic_position SATURATED + anchor_proximity_momentum 刚开 (T001 close-anchor envelope)
- RSI(6/12/24)、已实现偏度、已实现峰度、Chande、ROC(6/20)、MTM、MTMMA、SRMI、TRIX → return_distribution_signals DEAD + asymmetric_momentum DEAD + return_momentum_acceleration DEAD
- ATR(6/12)、Mass Index、Hurst、Ulcer、Coppock → vol_shock_signals DEAD + range_structure / Kurt salvage 路径已封闭
- PSY、Aroon、JDQS、UOS、TRI、DPTB → 比例 / count-based 弱 IC（paper |IC| < 0.005）已知不可挖
- VEMA、VOSC、VR、VROC、VRSI、VMACD、Klinger → mean/EMA/diff 量信号；VEMA 仅 EMA(Vol) 太 trivial 与 F033/F029 mean_turnover 重叠
- CCI、DBCD、DDI(DIZ/DIF) → BIAS / Chande 同构（CCI 是 BIAS / MAD 即 vol_20d-normalized BIAS）
- DMI(ADX/ADXR)、Coppock、TEMA、ADTM、AD-derivatives → 趋向 / 多空力道，多数与 BBI / 趋势线性回归同源

**未被覆盖（NEW angle）**:
- **ASI（Wilder swing index）** → 4-branch IF + Max-driven scaling 的 8-OHLC 摆动累积 → Idea 1
- **Chaikin Oscillator + AD（signed close-pos × Vol）** → `Vol*(2C-H-L)/(H-L)` 的 signed money flow + EMA 差 → Idea 2 + Idea 3 + Idea 5
- **PVT（signed return × Vol cumulative）** → `Sum((C-prev_C)/prev_C * Vol, N)` first-moment 累积 → Idea 4
- 这一族共有几何骨架："signed (close-position 或 return) × Vol → 时间累积 / EMA 平滑 / EMA 差"——库内 F009 (`Corr(P,V) * V`)、F008 (`Cov(P,V)`) 都是 second-moment（去均值后乘积/相关），**没有 first-moment signed accumulation 形式**。

**最优落点**: 新开 `signed_money_flow_oscillator`，主线 Idea 1 (ASI) + Idea 2 (Chaikin Oscillator) + Idea 4 (PVT 6-day)；Idea 3 (AD pure cumulative) 作为 Idea 2 的 ablation；Idea 5 (Chaikin vol-norm) 作为 vol_20d 吞噬律 salvage 留 batch_081。

**DSL 还是 Python**: ASI 倾向 python_runner（IF 分支 + Max-conditioned 公式表达不够干净；DSL 嵌套可读性差）；Chaikin/AD/PVT/CCI 全部 dsl_ready。

---

## Feasibility Assessment

### Idea 1 — ASI
- **Original dependency**: 日频 OHLC + Ref(prev_OHLC)
- **Coverage in current system**: 完全未覆盖；4-branch IF + Max-driven scaling 几何独一无二
- **Can it be downgraded to daily?**: 已经是日频（paper 用日 OHLC + 20 日累加）
- **Implementation path**: python（DSL 表达 4-branch IF 太丑；python_runner AST whitelist 支持）
- **Missing piece**: 无技术阻塞；首批要先验证 N=20 累加值的 cross-section dispersion 不被涨跌停日 truncated SI 主导

### Idea 2 — Chaikin Oscillator
- **Original dependency**: 日频 H/L/C/V
- **Coverage in current system**: AD base 几何未覆盖；EMA-差 momentum-of-money-flow 形式未覆盖
- **Can it be downgraded to daily?**: 已是日频
- **Implementation path**: dsl
- **Missing piece**: 无；表达式: `Sub(EMA(Div(Mul($volume, Sub(Sub(Mul(2, $close), $high), $low)), Sub($high, $low)), 3), EMA(Div(Mul($volume, Sub(Sub(Mul(2, $close), $high), $low)), Sub($high, $low)), 10))`

### Idea 3 — AD pure cumulative
- **Original dependency**: 同 Idea 2
- **Coverage in current system**: 同 Idea 2，同 base 不同聚合
- **Can it be downgraded to daily?**: 已是日频
- **Implementation path**: dsl
- **Missing piece**: 无；表达式 6-day 累加: `Mul(Mean(Div(Mul($volume, Sub(Sub(Mul(2, $close), $high), $low)), Sub($high, $low)), 6), 6)`

### Idea 4 — PVT(6)
- **Original dependency**: 日频 close + volume
- **Coverage in current system**: 未覆盖；first-moment signed × cumulative 形式独一无二
- **Can it be downgraded to daily?**: 已是日频
- **Implementation path**: dsl
- **Missing piece**: 无；表达式: `Mul(Mean(Mul(Div(Sub($close, Ref($close, 1)), Ref($close, 1)), $volume), 6), 6)`

### Idea 5 — Chaikin vol-norm salvage
- **Original dependency**: Idea 2 + 加分母 Mean(Vol, 20)
- **Coverage in current system**: 不直接，但若 Idea 2 vol_20d 暴露大，本 Idea 是 lessons-mandated salvage
- **Can it be downgraded to daily?**: 是
- **Implementation path**: dsl
- **Missing piece**: 无；留 batch_081

### Idea 6 — CCI
- **Original dependency**: 日频 H/L/C
- **Coverage in current system**: BIAS / range_structure family 完整覆盖；CCI 实际上是 vol-normalized BIAS
- **Can it be downgraded to daily?**: 是
- **Implementation path**: blocked-by-library-coverage（lessons F001 + F005）
- **Missing piece**: 不应作为新方向候选

---

## What The Paper Is Hiding

1. **中证 500 ≠ csi1000，paper 完全没有小盘 robustness**：所有 102 个指标的 IC / 多空胜率都是中证 500（中盘大票）的 cross-section。csi1000 散户占比更高 + 流动性更差 + 涨跌停约束相对更剧烈，本仓库反复验证过的 vol_20d 吞噬律是**csi1000-specific** 现象（中证 500 上要弱很多）。所以 paper 的 ASI |IC|=2.71% 在 csi1000 上**几乎确定会衰减**到 1-2% 甚至更低；多空胜率 61% 在 csi1000 上可能滑到 53-55%。这是判断每个 Idea 时都必须打折扣的最大 hidden assumption。

2. **周度换仓 ≠ 日频排序，标签 horizon 不一样**：paper 用 weekly rebalance 计算 IC（信号在每周一计算，持有 5 个交易日），而本仓库 csi1000 默认 daily horizon（next-1d / next-5d / next-20d）。weekly horizon 通常比 daily horizon 容易出 IC（噪音被低频平均），所以 paper 的 |IC| 数字**结构性偏高**——把 paper 的 |IC|=2.71% 折算到 daily horizon 大致等于 |IC|≈1.0-1.4%，而本仓库 hard_gate 要求 ic_oos ≥ 0.008（即 0.8%），所以折算后这些指标**仍可能擦边过 hard_gate**，但 ICIR 会更弱。

3. **没有 Barra style neutralize，IC 都是 raw IC**：paper 的所有 IC 数值都是未做 size / value / mom / vol_20d 中性化的 raw cross-section IC。库内已 admitted 的 25 个因子 + 反复出现的 vol_20d 吞噬律说明，**raw IC 高的因子在 Barra residual 后可能掉到 alpha_survival < 0.3**——尤其是 ASI 含 `Max(AA, BB)` scaling 和 Chaikin 的 EMA-差，都有 vol-load 嫌疑。**Barra residual 必须在判决阶段强制看**，不能只看 raw IC。

4. **paper 的"|IC|=3.43% BIAS(6) 第一名"对当前仓库无价值——BIAS 在 csi1000 csi1000 已被 range_structure 反复测过近饱和**：paper 把 BIAS 列为头名是因为 weekly + 中证 500 的样本偏好（mean-reversion 在中盘大票上特别强）；csi1000 上 BIAS 早已被 F021 upper_shadow_disp_range_compress_rd_20 等吃干。读者若把 paper 头名当 admit 直觉是误读——库内 BIAS-family 已 saturated，paper 头部 IC 排名应该和库内 admit 状态做"反向 join"才能找到真正未覆盖的 niche（即 ASI / Chaikin Oscillator / PVT 长尾）。

5. **102 个因子之间 cross-correlation 极高，paper 没报矩阵**：BIAS(6/12/24)、VSTD(10/20)、成交金额方差(6/20)、AD(全/20/6)、PVT(全/12/6)、KDJ(K/J/D)、Chande(SD/SU)、Aroon(上升/下降/差)——同一个 base 不同窗口 / 不同子项的多个版本被分别列入 102 个，所以"top 15"实际可能只有 5-6 个独立维度。报告把它们 hyperparameter-explore 出来一字排开，没做 hierarchical clustering，让"幸存者"看起来比实际多。读者需要自己做 family de-duplication。

6. **2010-2021 包含 2014-2015 创业板牛市 + 2018 大熊市 + 2019-2021 茅指数行情**：paper 没有按市场风格分段报 IC。某些指标（尤其 ASI、Chaikin）在 2015 高波动牛熊上 IC 可能 dominantly 来自单一年度；本仓库 hard_gate 要求 ic_by_year 多年同号，这一致性在 paper 数据下**未知**——首批结果如果 ic_by_year 出现 2 年以上反号，应直接判 reject 而非 reserve。

---

## Blocked Ideas For Future

- **102 因子之间的 hierarchical clustering 矩阵** — paper 没做；如果将来仓库自己跑出 102 个因子的 pairwise corr 矩阵，可以直接 prune 掉冗余维度，找到真正独立的 5-8 个 family。**Unblock 条件**: 跑一次 102 因子 pairwise correlation （Phase 2 全市场全期 + 简单 batch evaluation 工具，不依赖 admit）。

- **csi1000 上的 ASI vol-orthogonalized 残差** — Idea 1 raw ASI 若 vol_20d 暴露 > 5，需要 Barra residual 拯救；目前 barra_residual_alpha 工具链在 Python coverage<0.80 受限。**Unblock 条件**: 修复 F010 coverage<0.80 + 实现 `orthogonalize_by_style` 算子。

- **paper 缺失但常见的 Bollinger Bands 频道指标** — paper 102 个因子里**没有显式 Bollinger Band %B 或 Bollinger Bandwidth**（虽然 BBI 是另一种指标）。Bollinger %B = `(C - MA(C,20)) / (2 * Std(C,20))` 与 BIAS 仅分母不同（BIAS 分母 MA，Bollinger 分母 2σ），是 vol-normalized BIAS。已被 lessons F001 + range_structure b045 C006 同律证伪——**not blocked, just dead**。

- **多技术指标 ensemble / voting** — paper 主线就是单一指标的 IC 排序，没做多指标 ensemble；如果仓库未来引入 portfolio-level ensemble layer，paper 的 top 15 表可以作为 ensemble 候选池。**Unblock 条件**: Phase 2 ensemble evaluation 架构（不是单指标 IC，而是 K 指标加权后的 IC）。

---

## Direction Recommendation

- **Decision**: `create_direction`
- **Selected idea**: Idea 2 (Chaikin Oscillator) 为主线 + Idea 1 (ASI Wilder swing index) 为强力对照 + Idea 4 (PVT 6-day) 为第三线；Idea 3 (AD pure cumulative) 作为 Idea 2 的 ablation；Idea 5 (vol-norm Chaikin) 留 batch_081 lesson-driven salvage
- **direction_tag**: `signed_money_flow_oscillator`
- **Initial threads**:
  - T001: ASI (Wilder swing index) — 8-OHLC 摆动累积是否携带库内 25 admitted 之外的独立 alpha？是否被 vol_20d 吞噬？
  - T002: Chaikin Oscillator (signed close-position × Vol → EMA 差) + AD ablation — money-flow first-moment signed 累积形式是否独立于 F009 pv_corr 的 second-moment correlation？
  - T003: PVT (signed return × Vol cumulative) — daily-return × Vol 的 6 日累积是否独立于 F008 Cov 的去均值乘积均值？
  - T004 (deferred to batch_081 if T002 vol_20d-loaded): Chaikin vol-orthogonalized salvage path
- **First candidate families** (DSL 草图，留给 `/factor-idea` 细化):
  1. **ASI_20d** (python_runner): 4-branch IF on (AA, BB, CC) for R; SI = 16 * X / R * Max(AA, BB); 累加 N=20。
  2. **Chaikin_Oscillator** (DSL): `Sub(EMA(Div(Mul($volume, Sub(Mul(2, $close), Add($high, $low))), Sub($high, $low)), 3), EMA(Div(Mul($volume, Sub(Mul(2, $close), Add($high, $low))), Sub($high, $low)), 10))`
  3. **AD_6d_cumulative** (DSL ablation): `Mul(Mean(Div(Mul($volume, Sub(Mul(2, $close), Add($high, $low))), Sub($high, $low)), 6), 6)`
  4. **PVT_6d** (DSL): `Mul(Mean(Mul(Div(Sub($close, Ref($close, 1)), Ref($close, 1)), $volume), 6), 6)`
  5. **PVT_12d** (DSL ablation 窗口对照): same as 4 with N=12
  6. (留 batch_081) **Chaikin_vol_norm**: `Div(<Idea2 expr>, Mean($volume, 20))`
- **Minimum unblock condition**: 不涉及（所有字段与算子均在白名单内；ASI 通过 python_runner 路径走 AST whitelist 无障碍）

---

## Related

- [[../directions/signed_money_flow_oscillator]] — 本 paper 衍生的新方向
- [[../directions/stochastic_position]] `saturated` — KDJ family DEAD；本 paper KDJ(K/J/D) 全部低 IC 也 cross-confirm
- [[../directions/range_structure]] `saturated` — BIAS family（paper 头名）已完整覆盖；提示 paper 头部 IC 在 csi1000 已被吃干
- [[../directions/anchor_proximity_momentum]] — W%R Williams family；paper W%R(9/15/20) 全部 |IC|<0.01，与本方向无重叠
- [[../directions/return_distribution_signals]] `dead` · [[../directions/return_momentum_acceleration]] `dead` · [[../directions/asymmetric_momentum]] `dead` — RSI / 已实现偏度 / ROC / MTM 全 DEAD；paper 同族指标无救
- [[../directions/vol_shock_signals]] `dead` — ATR / Mass / Ulcer / Hurst 同律 DEAD
- [[../directions/amount_volatility_signal]] `saturated` — VSTD / 成交金额方差 family 完整覆盖
- [[../directions/ohlc_temporal_aggregation]] `saturated` — F006-F009 candle/pv 占位，CCI / Chande / DBCD 同律 reduced
- [[../lessons#Structural Constraints]] — F001 / F301 vol_20d 吞噬律（决定 Idea 1/2/4 的 alpha_survival 上界）
- [[../lessons#OHLC Family Defaults]] — F005 OHLC algebraic mirror（决定 Idea 6 CCI 必然 BIAS reducer）
