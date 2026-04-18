---
direction_tag: amount_volatility_signal
status: productive
priority: high
rounds: 2
admits: 1
last_batch: batch_002
last_admits: []
last_goal: 'Deepen amount_volatility_signal: (T001) window scan cv_5/cv_20 + MAD-robust
  variant to validate F001''s 10d optimum and抗离群; (T002) longer-window max/mean_60
  to escape 20d vol_20d crowding discovered in batch_001; (T004) NaN-safe amplitude
  corr to re-test T003 hypothesis without Log divergence.'
last_activity: '2026-04-18T18:07:33Z'
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

batch_002 完成 T001 窗口扫描：**10d (F001) 正式为 CV 机制全局最优窗口** — 5d (C001 reserve) / 20d (C002 reserve) / MAD_10 (C003 reject near_dup) 全部确认不开辟新维度。T002 60d 延长尝试 (C004) 触硬闸、T004 幅度版 Corr (C005) 信号过薄。**方向内 13/13 候选全部 dominant_style=vol_20d** 得到强化验证 → 下批必须做 vol_20d orthogonalize（跨方向或 Python 逃生口），同族窗口扫描已封闭。候选数收窄 ≤ 5，search_adjusted 持续 high。

## Threads

### T001: Amount CV 跨窗口比值 + lookback 扫描 [✓ ANSWERED batch_002]
**Question**: $amount 变异系数（CV = Std/Mean）在短 vs 长窗口的比值，能否稳定刻画资金参与"断层"并产生 alpha？断层向上（短 CV > 长 CV）对应 contrarian 还是 momentum？最优窗口是多少？是否存在鲁棒算子替代？
**Answer (batch_001→002)**: 短窗口 CV (10d) 单独是 core edge —— admit C001 amount_cv_10（ICIR_OOS=-0.716 / mono_OOS=-1.0 / ls_t=-3.78 / 9 年同号）。**比值构造被证伪**：C003_b1 `CV10/CV60` hard_gate 挂（mono_flip IS=0.10 OOS=-1.00）。**窗口扫描完成 (batch_002)**：5d (C001_b2) 信号完整但 rebalance_stress medium + turnover×1.8；20d (C002_b2) 全维劣化 + vol_20d 吞噬升级；**10d 是"alpha 强度 × 风格干净度 × 换手成本"三者平衡的全局最优**，F001 的 anchor 地位正式确立。**算子替换封闭**：MAD/Med_10 (C003_b2) 与 F001 corr=0.967 → 鲁棒算子替换在右偏 $amount 分布上不开辟新子空间。
**Evidence trail**:
- [[batches/batch_001/candidates/C001|batch_001 C001]]: ICIR_OOS=-0.716 ls_t=-3.78 mono=-1.0 → **admit → [[factors/F001]]** (factor_name: amount_cv_10)
- [[batches/batch_001/candidates/C002|batch_001 C002]]: ICIR_OOS=-0.214 ls_t=-0.85 mono_OOS=0.0 → **reserve**
- [[batches/batch_001/candidates/C003|batch_001 C003]]: mono_flip IS=0.10→OOS=-1.00 → **reject (hard_gate)**
- [[batches/batch_002/candidates/C001|batch_002 C001]]: ICIR_OOS=-0.623 ls_t=-3.58 mono=-1.0 max_corr=0.57@F001 → **reserve** (cv_5)
- [[batches/batch_002/candidates/C002|batch_002 C002]]: ICIR_OOS=-0.579 ls_t=-3.43 vol_20d=37.5 alpha_surv=0.649 → **reserve** (cv_20)
- [[batches/batch_002/candidates/C003|batch_002 C003]]: corr=0.967@F001 → **reject (hard_gate near_dup)** (MAD/Med_10)

**Next probes**: T001 已答——进一步窗口扫描 / 算子替换空间封闭；如需复活需走 vol_20d orthogonalize 后的残差版本。

### T002: Amount 分布形状 [◉ ACTIVE]
**Question**: 成交额的偏度、峰度、max/mean 比值是否携带独立于 CV 的尾部信息？高峰度对应的异常大单有前瞻性（contrarian 反转），还是同步性（noise）？
**Evidence trail**:
- [[batches/batch_001/candidates/C004|batch_001 C004]]: Skew_20 IC_OOS=-0.003 太弱 + mono_flip → **reject (hard_gate)**
- [[batches/batch_001/candidates/C005|batch_001 C005]]: Max/Mean_20 ICIR_OOS=-0.539 mono=-1.0 但 vol_20d 暴露 32.0 + cum_ic_mdd=-73.7 → **reserve**
- [[batches/batch_001/candidates/C008|batch_001 C008]]: Kurt_20 四重失败（sign+ic+decay+mono）→ **reject (hard_gate)**
- [[batches/batch_002/candidates/C004|batch_002 C004]]: Max/Mean_60 ic_oos=-0.0078 hard_gate, OOS 量级衰至前期 1/5 → **reject (hard_gate ic_oos_too_low)** → **延长窗口子路径 `[✗ DISPROVEN batch_002]`**

**Partial Answer**：20d 窗口下高阶矩（skew/kurt）噪声过大不可用，仅尾部 max/mean 比值（C005_b1）是"信号完整"代表，但 vol_20d 暴露吞噬信号。**延长窗口至 60d 不是出路**（C004_b2 regime-dependent，OOS 熄灭）。T002 hypothesis 整体仍 ACTIVE。

**Next probes**: robust tail 指标 —— `Div(Mean(TsMax($amount, 3), 20), Mean($amount, 20))` top-3 mean 替换 single max；按 20d 内 Skew($amount) 正负分组看条件 CV；或对 C005_b1 做 vol_20d residual 残差版本（需走 Python 逃生口或跨向量实现）。

### T003: Amount 与 return 方向一致性 [✗ DISPROVEN batch_001] (partial — 算子实现层)
**Question**: Corr($amount, Delta($close)) 和 Slope(Log($amount)) 能否捕捉 absorption / trend-confirming 的市场状态，并在跨期产生 alpha？符号预期：
- 负相关（放量逆势 → 承接信号）→ long absorption pattern
- 正趋势斜率（资金持续流入）→ momentum
**Evidence trail**:
- [[batches/batch_001/candidates/C006|batch_001 C006]]: Corr(amount,Δclose,20) mono_flip IS=0.60→OOS=-0.70 → **reject (hard_gate)**
- [[batches/batch_001/candidates/C007|batch_001 C007]]: Slope(Log(amount),20) coverage 0.327 + mono_flip → **reject (hard_gate)**

**Disproven (算子层)**：两个当前 baseline 实现都触结构性失败 —— Corr 分位跨期翻转（regime-dependent），Log-Slope 遇 0 成交额发散（NaN 传播压缩样本到 32.7%）。**hypothesis 本身（资金与价格方向一致性）未被证伪**，但当前 DSL 表达式族失败，需新开 T004 替代实现。

### T004: Amount-return 一致性的 NaN-safe 算子族 [◉ ACTIVE]
**Question**: 在避免 Log 发散 + 分位稳定的前提下，能否用归一化 slope / 幅度 corr / 多窗口 robust 实现捕捉 T003 的经济假设？
**Evidence trail**:
- [[batches/batch_002/candidates/C005|batch_002 C005]]: Corr(amount, |Δclose|, 20) ic_oos=-0.0037 信号过薄 → **reject (hard_gate ic_oos_too_low)** → **幅度版 Corr 子路径 `[✗ DISPROVEN batch_002]`**

**Partial Answer**：幅度-only 实现去方向化丢失 T003 原本希望保留的"资金与价格方向一致性"信息。T004 整体 hypothesis 仍 ACTIVE——保留符号的 NaN-safe 实现应优先。

**Next probes**:
- `Slope(Div($amount, Mean($amount, 20)), 20)` —— 归一化后 Slope（规避 Log(0)）**← 优先**
- `Mul(Sign(Delta($close, 1)), $amount)` 条件均值（上涨日放量 vs 下跌日放量）**← 优先**
- 多窗口 Corr：5d / 60d 看分位稳定性（保留符号）
- 降权：幅度-only Corr（已被 batch_002 证伪）

## Known Failures

- **C003_b1** `Div(Div(Std($amount,10),Mean($amount,10)), Div(Std($amount,60),Mean($amount,60)))` — CV 比值构造 mono_sign_flip（IS=0.10 OOS=-1.00），断层信号不来自比值而来自短窗口水平值本身
- **C004_b1** `Skew($amount, 20)` — 20d 高阶矩噪声过大，IC_OOS=-0.003 & mono 翻转，T002 下需换稳健尾部指标
- **C006_b1** `Corr($amount, Delta($close, 1), 20)` — 线性 IC 稳定但分位跨期翻号（IS=0.60 OOS=-0.70），机制 regime-dependent
- **C007_b1** `Slope(Log($amount), 20)` — Log 遇 0 成交额发散，coverage 掉到 0.327 + mono 翻转；T003 必须改用 NaN-safe 归一化算子
- **C008_b1** `Kurt($amount, 20)` — 20d 窗口四阶矩样本太小，四重失败（sign+ic+decay+mono）；T002 下若测 kurt 需延长到 60d+ 或做条件 kurt
- **C003_b2** `Div(Mad($amount, 10), Med($amount, 10))` — MAD/Med 与 Std/Mean 在右偏 $amount 分布上相关 0.967，鲁棒算子替换不开辟新信号子空间；T001 "MAD 抗离群值"路径封闭
- **C004_b2** `Div(Max($amount, 60), Mean($amount, 60))` — 60d 尾部 Max/Mean 是 regime-dependent，OOS (2021+) 量级衰至前期 1/5，ic_oos_too_low (|-0.0078|<0.008)；T002 "延长窗口"路径封闭
- **C005_b2** `Corr($amount, Abs(Delta($close, 1)), 20)` — 幅度版 Corr 去方向后信号过薄（ic_oos=-0.0037），丢失资金与价格方向一致性信息；T004 幅度-only 分支封闭，优先 sign-preserved 实现

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

### 2026-04-19 [[batches/batch_002/judge|batch_002]]
**admit=0 · reserve=2 (C001 cv_5, C002 cv_20) · reject=3 (C003 near_dup, C004 ic_too_low, C005 ic_too_low)**。方向保持 `productive` —— 非 admit 不代表熄火，而是 T001 窗口扫描正式定案。

**核心发现**：
1. **T001 窗口扫描答案**：10d (F001) 是 CV 机制的全局最优窗口。5d (C001) 信号完整但换手×1.8 + half_life 减半 + rebalance_stress medium；20d (C002) 所有维度劣化 + vol_20d 暴露×1.5。F001 的 anchor 地位经跨窗口统计正式确立。
2. **T001 算子空间封闭**：C003 MAD/Med_10 与 F001 相关 0.967 — 鲁棒算子替换在右偏 $amount 分布上不开辟新子空间。
3. **T002 延长窗口子路径被证伪**：C004 (Max/Mean_60) OOS 量级衰至前期 1/5，2021+ 新 regime 下尾部信号 regime-dependent 失效。T002 整体 hypothesis 仍 ACTIVE，下一步转向 robust tail 指标。
4. **T004 幅度版 Corr 子路径被证伪**：C005 去方向化丢失 T003 方向一致性信息，信号过薄。下一步保留符号的 NaN-safe 实现（归一化 Slope / Sign×amount 条件均值）优先。
5. **方向级结构验证加强**：13/13 累计候选全部 dominant_style=vol_20d — vol_20d orthogonalize 不做就无法离开 anchor rule 束缚。

**Thread 进展**：
- T001: ANSWERED ✓（窗口扫描 + 算子替换均封闭）
- T002: ACTIVE（60d 延长子路径证伪；robust tail 方向未动）
- T003: DISPROVEN 算子层（不变）
- T004: ACTIVE（幅度-only 子路径证伪；sign-preserved 实现未动）

**下一步**（batch_003 候选池，≤ 5）：
1. **T004 sign-preserved 实现**：`Slope(Div($amount, Mean($amount, 20)), 20)` 归一化后 Slope + `Mul(Sign(Delta($close, 1)), $amount)` 条件均值
2. **T002 robust tail**：`Div(Mean(TsMax($amount, 3), 20), Mean($amount, 20))` top-3 mean + 按 Skew 正负分组的条件 CV（需跨 DSL 能力）
3. **vol_20d orthogonalize 尝试**：若 DSL 不支持 Barra residual，考虑 Python 逃生口实现（T002/F001 残差版）
4. 继续保持 ≤ 5 候选（search_adjusted=high 持续）
