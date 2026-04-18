---
direction_tag: amount_volatility_signal
status: productive
priority: high
rounds: 1
admits: 1
last_batch: batch_001
last_admits:
- F001
last_goal: 首轮切入 amount_volatility_signal 方向：以 $amount（成交额）为核心信号源，三条 thread 并发测试 ——
  T001 CV 窗口比值（短/长资金稳定性断层）、T002 分布形状（偏度/峰度/尖峰度）、T003 价量一致性（相关性/斜率）。目的：建立 $amount 派生因子的基线
  alpha 强度谱、过滤市值代理、定位下一轮 deepen 的 thread。
last_activity: '2026-04-18T14:46:12Z'
created_batch: batch_001
members:
- F001
merged_into: null
---
# amount_volatility_signal

## Hypothesis

`$amount`（成交额 = price × volume）比原始 `$volume` 更忠实地反映**资金参与强度**——同等 volume 在高价股和低价股上意味着完全不同的资金规模。由此，`$amount` 的**二阶统计量**（波动率、偏度、峰度、尖峰度）编码了"谁在交易、交易得多稳定"的微观结构信息，而非单纯的流动性水平。

三条经济学线索：

1. **资金参与稳定性断层**：机构资金倾向于持续稳定流入（低 CV），散户 / 事件驱动资金则表现为突发异动（高 CV）。短窗口 CV 相对长窗口 CV 的抬升，标记了资金结构的"断层"。
2. **分布尾部的信息含量**：峰度和偏度揭示异常大单的发生频率。右偏+高峰度 = 少数几天的巨额交易主导均值 —— 可能是信息驱动进场，也可能是拉尾盘 / 砸盘的技术性噪声。
3. **方向与资金的一致性**：`$amount` 与 `Delta($close)` 的相关性区分了 trend-confirming（放量跟随）、absorption（放量逆势 = 接盘 / 抛压）、以及 divergence（缩量变盘）三种市场状态。

**Scale-invariance 优先**：候选必须是 `$amount` 的比值 / 形状 / 相关性变换，避免直接用 `$amount` 水平值 —— 后者与 `$market_cap` 强相关，触 lessons.md 的市值代理红线。

## Current Focus

首批 batch_001 结果定位：**T001 短窗口 CV 是 core edge**（admit C001 amount_cv_10，ICIR_OOS=-0.716 / mono=-1.0 / 9 年同号），T002 尾部信号需 vol_20d 正交化才能判定独立性，T003 当前算子族失败（Log 发散 / Corr 分位翻转）需新建 T004 替代实现。**全方向 8/8 候选 dominant_style=vol_20d** —— 下一批优先 vol_20d orthogonalize 验证。

## Threads

### T001: Amount CV 跨窗口比值 [✓ ANSWERED batch_001]
**Question**: $amount 变异系数（CV = Std/Mean）在短 vs 长窗口的比值，能否稳定刻画资金参与"断层"并产生 alpha？断层向上（短 CV > 长 CV）对应 contrarian 还是 momentum？
**Answer (batch_001)**: 短窗口 CV (10d) 单独是 core edge —— admit C001 amount_cv_10（ICIR_OOS=-0.716 / mono_OOS=-1.0 / ls_t=-3.78 / 9 年同号），负号（高 CV → 未来低收益）与 A 股散户性事件异动反转 hypothesis 一致。60d CV (C002) 只给长基线，ls_t 仅 -0.85 且 OOS 分位崩溃。**比值构造被证伪**：C003 `CV10/CV60` hard_gate 挂（mono_flip IS=0.10 OOS=-1.00），说明断层信号的 alpha 不来自比值结构，而来自短窗口水平值本身。
**Evidence trail**:
- [[batches/batch_001/candidates/C001|batch_001 C001]]: ICIR_OOS=-0.716 ls_t=-3.78 mono=-1.0 → **admit → [[factors/F001]]** (factor_name: amount_cv_10)
- [[batches/batch_001/candidates/C002|batch_001 C002]]: ICIR_OOS=-0.214 ls_t=-0.85 mono_OOS=0.0 → **reserve**
- [[batches/batch_001/candidates/C003|batch_001 C003]]: mono_flip IS=0.10→OOS=-1.00 → **reject (hard_gate)**

**Next probes**: cv_5 / cv_20 / cv_30 lookback 扫描定位最优窗口；MAD 版 `Div(Mad($amount, 10), Med($amount, 10))` 测抗离群值变体。

### T002: Amount 分布形状 [◉ ACTIVE]
**Question**: 成交额的偏度、峰度、max/mean 比值是否携带独立于 CV 的尾部信息？高峰度对应的异常大单有前瞻性（contrarian 反转），还是同步性（noise）？
**Evidence trail**:
- [[batches/batch_001/candidates/C004|batch_001 C004]]: Skew_20 IC_OOS=-0.003 太弱 + mono_flip → **reject (hard_gate)**
- [[batches/batch_001/candidates/C005|batch_001 C005]]: Max/Mean_20 ICIR_OOS=-0.539 mono=-1.0 但 vol_20d 暴露 32.0 + cum_ic_mdd=-73.7 → **reserve**
- [[batches/batch_001/candidates/C008|batch_001 C008]]: Kurt_20 四重失败（sign+ic+decay+mono）→ **reject (hard_gate)**

**Partial Answer**：20d 窗口下高阶矩（skew/kurt）噪声过大不可用，仅尾部 max/mean 比值（C005）是"信号完整"代表，但 vol_20d 暴露吞噬信号。

**Next probes**: 对 C005 做 vol-orthogonalization（残差 IC 是否独立？）；稳健尾部指标（top-3/top-5 mean over window）；延长 lookback 到 60d+ 的 kurt / skew；按正负 skew 分组看条件 IC。

### T003: Amount 与 return 方向一致性 [✗ DISPROVEN batch_001] (partial — 算子实现层)
**Question**: Corr($amount, Delta($close)) 和 Slope(Log($amount)) 能否捕捉 absorption / trend-confirming 的市场状态，并在跨期产生 alpha？符号预期：
- 负相关（放量逆势 → 承接信号）→ long absorption pattern
- 正趋势斜率（资金持续流入）→ momentum
**Evidence trail**:
- [[batches/batch_001/candidates/C006|batch_001 C006]]: Corr(amount,Δclose,20) mono_flip IS=0.60→OOS=-0.70 → **reject (hard_gate)**
- [[batches/batch_001/candidates/C007|batch_001 C007]]: Slope(Log(amount),20) coverage 0.327 + mono_flip → **reject (hard_gate)**

**Disproven (算子层)**：两个当前 baseline 实现都触结构性失败 —— Corr 分位跨期翻转（regime-dependent），Log-Slope 遇 0 成交额发散（NaN 传播压缩样本到 32.7%）。**hypothesis 本身（资金与价格方向一致性）未被证伪**，但当前 DSL 表达式族失败，需新开 T004 替代实现。

### T004: Amount-return 一致性的 NaN-safe 算子族 [◉ ACTIVE] 🆕
**Question**: 在避免 Log 发散 + 分位稳定的前提下，能否用归一化 slope / 幅度 corr / 多窗口 robust 实现捕捉 T003 的经济假设？
**Evidence trail**:
- （批次待跑）

**Next probes**:
- `Slope(Div($amount, Mean($amount, 20)), 20)` —— 归一化后 Slope（规避 Log(0)）
- `Corr($amount, Abs(Delta($close, 1)), 20)` —— 幅度版（放量即信息而非方向）
- 多窗口 Corr：5d / 60d 看分位稳定性
- 对比：同分组 Sign(Delta(close)) × $amount 条件均值（上涨日放量 vs 下跌日放量）

## Known Failures

- **C003** `Div(Div(Std($amount,10),Mean($amount,10)), Div(Std($amount,60),Mean($amount,60)))` — CV 比值构造 mono_sign_flip（IS=0.10 OOS=-1.00），断层信号不来自比值而来自短窗口水平值本身
- **C004** `Skew($amount, 20)` — 20d 高阶矩噪声过大，IC_OOS=-0.003 & mono 翻转，T002 下需换稳健尾部指标
- **C006** `Corr($amount, Delta($close, 1), 20)` — 线性 IC 稳定但分位跨期翻号（IS=0.60 OOS=-0.70），机制 regime-dependent
- **C007** `Slope(Log($amount), 20)` — Log 遇 0 成交额发散，coverage 掉到 0.327 + mono 翻转；T003 必须改用 NaN-safe 归一化算子
- **C008** `Kurt($amount, 20)` — 20d 窗口四阶矩样本太小，四重失败（sign+ic+decay+mono）；T002 下若测 kurt 需延长到 60d+ 或做条件 kurt

## Related
- [[lessons#Structural Constraints]]  （市值代理红线 / 向量化约束）
- [[lessons#Data Facts]]  （$amount 有数据；$vwap 全零）

## Narrative Log

### 2026-04-18 [[batches/batch_001/judge|batch_001]]
首批落锤：**admit=1 (C001 amount_cv_10) · reserve=2 (C002, C005) · reject=5**。方向从 `exploring` 转 `productive`（首次 admit 触发）。

**核心发现**：
1. T001 短窗口 CV 是 core edge —— C001 完美单调 (-1.0) + 9 年同号 + ICIR_OOS=-0.716；比值（C003）和长基线（C002）都不是 alpha 来源。
2. **8/8 候选 dominant_style=vol_20d**（平均暴露 ~17，C005 最高 32.0）—— 方向级结构发现：`$amount` 的多数二阶统计量在 Barra 空间中与 vol_20d 强共线，下轮必做 orthogonalization 验证独立 alpha。
3. T002 高阶矩（skew / kurt）20d 窗口噪声大不可用；仅 max/mean 比值保留"信号完整"但被 vol_20d 吞噬。
4. T003 当前 baseline 算子族（Log-Slope, Corr-Delta）双双因结构性问题挂掉，但 hypothesis 本身未被证伪，新开 T004 承接替代实现。

**Thread 进展**：
- T001: ANSWERED（短 CV 胜 / 长 CV 衰 / 比值伪）
- T002: ACTIVE（max/mean 保留，待 orthogonalize）
- T003: DISPROVEN 算子层（hypothesis 待 T004 重测）
- T004: 新增 ACTIVE（NaN-safe 归一化 + 幅度 corr 实现）

**下一步**（batch_002 候选池）：
1. C005 vol-orthogonalize 版本（验证 T002 是否独立于 vol_20d）
2. C001 lookback 扫描（cv_5/cv_20/cv_30）+ MAD 变体
3. T004 新算子族（归一化 slope / 幅度 corr）
4. 批次候选数 ≤ 5（search_adjusted 已 high，收窄搜索）
