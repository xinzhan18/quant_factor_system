---
generated_at: 2026-04-20T23:06:14Z
round: 28
total_active_directions: 10
total_factors_admitted: 11
last_batch: batch_028
last_consolidation_round: null
---

# Factor Research Index

> MOC (Map of Content)：所有研究方向和 admitted 因子的总览。
> 上半段由 LLM 维护；下半段由 Python 自动刷新。

## 活跃方向

### [[directions/intraday_price_formation|日内价格形成]] `saturated` `high`
累计 2 batches，16 候选 → **1 admit (F003)** / 0 reserve / 15 reject。[[batches/batch_011/judge|batch_011]] **F003 扩展窗口全灭**：Ref2-5+MeanHigh2-10 全部 ic_oos_too_low 或 mono_sign_flip；C005/C006 near_duplicate F003（corr=0.999）。**方向 DSL 空间穷尽**，status → saturated；下一方向需 Python Barra residual。

### [[directions/amount_volatility_signal|成交额波动率信号]] `productive` `high`
累计 4 batches，24 候选 → 1 admit / 10 reserve / 13 reject（admit 率 **4.2%**）。[[batches/batch_008/judge|batch_008]] **第 4 次确认 vol_20d 结构性瓶颈**：19/19 非 hard_gate 候选 100% dominant_style=vol_20d。C003 最强 rank-order(mono=-1.0, max_corr=0.07@F001) 但 alpha_surv=0.24 触 CP04 poor。**DSL 空间已物理封闭**，唯一逃生口：Python vol_20d Barra residual。

### [[directions/turnover_structural_signal|换手率结构信号]] `saturated` `low`
首批 [[batches/batch_004/judge|batch_004]] 即触发 saturated：5 候选 5/5 `dominant_style=vol_20d`，"换手率脱离 vol_20d 风格空间"hypothesis 证伪。仅 C003 加速度 (alpha_survival=1.085) 突破 dealbreaker reserve，四 thread 全部证伪。C001 turnover CV 与 F001 相关 0.955 → shares 短窗近常数 CV 结构等价。

### [[directions/value_liquidity_interaction|价值 × 流动性交互]] `productive` `high`
累计 5 batches，22 候选 → **1 admit (F002)** / 10 reserve / 11 reject。[[batches/batch_009/judge|batch_009]] self-norm rate×turnover 路径全灭(4/4 sign_flip)；C005 **dom=str_1m breakthrough**（方向首次非 vol_20d）但 incr_ic=-0.033(库 reducer) reject；C007 ls_t=-2.43(最强 PnL) 但 vol_20d=18.8 极端。**DSL 空间实质穷尽**，下批必须 Python Barra residual。

### [[directions/barra_residual_alpha|Barra Residual Alpha]] `saturated` `low`
累计 4 batches，21 候选 → **2 admit (F004)** / 3 reserve / 16 reject。[[batches/batch_015/judge|batch_015]] **方向 saturated**：5 个 method-switch 候选 4/4 全部 collapse 到 F004（Huber=0.907 / hetero-norm=0.927 / winsor=0.941 / vol×turn=0.997）+ 1 compute_error。**实验性建立 F004 不动点定理**：F004 是该 7-style basis × OLS-family 上的几何不变量。复活路径：加非 Barra basis / 非参数残差化 / 与库其他因子非线性 ensemble。

### [[directions/return_distribution_signals|收益分布信号]] `dead` `low` 🆕
首批 [[batches/batch_016/judge|batch_016]] 即 dead：5 候选全 reject (skew 20d/60d/×vol + kurt 20d + Q90-Q10)。**核心证伪**：higher-order moments (skew/kurt/Q-range) 在 cross-section 都 collapse 到 vol_20d——alpha_surv 0.008-0.177 远低 threshold。C004 mono=-0.9 ls_t=-2.28 看似强但 alpha_surv=0.008 暴露其本质 ≡ vol_20d monotone 变换。

### [[directions/ohlc_temporal_aggregation|多日 OHLC 聚合]] `saturated` `medium` 🆕
5 batches，21 候选 → 3 admit (F006/F007/F008) + 2 reserve + 16 reject。[[batches/batch_021/judge|batch_021]] **方向 saturated**：F007 3d ablation mono_sign_flip 反转（open-position 是 5d-only signal）；7d upper-shadow alpha_surv=1.685 但 corr=0.834@F006 转 reserve（库 bloat）；turnover-weighted body 是 F007 noisy 版本。**信号家族 multi-window 不对称**：upper-shadow [3d,7d] 都稳，open-position 仅 5d。admit 率 14% (3/21)。

### [[directions/fundamental_momentum|基本面变化率]] `dead` `low` 🆕
首批 [[batches/batch_022/judge|batch_022]] 即 dead：4 候选 PE/PB/PS rate 全 weak (ls_t -1.22 to -1.81<2) + r² poor (0.31-0.81) + 全 library reducer。**fundamental rate hypothesis 直接证伪**。

### [[directions/overnight_intraday_split|隔夜/日内分解]] `productive` `medium` 🆕
2 batches，6 候选 → **3 admit** (F009/F010/F011) + 1 reserve + 2 reject。admit 率 50%。[[batches/batch_026/judge|batch_026]] F011 3d overnight_return_persistence admit (ls_t=7.98 整库第 2 强)；C002 10d reserve 库 bloat；C003 product form 破坏 mono。overnight 家族已占库 4 slot 达到 bloat 上限，priority 降至 medium。

## 最近 Batch

- [[batches/batch_018/judge|batch_018]] (ohlc_temporal_aggregation): 5 候选 → admit=1 (C003 open_position_persistence_5d) / reserve=0 / reject=4。**方向连续两批 admit**——open-position max_corr=0.276@F006 完全机制正交；C001 lower-shadow corr=1.000@F006 algebraic mirror trap；C002 magnitude-only 失败。
- [[batches/batch_017/judge|batch_017]] (ohlc_temporal_aggregation): 5 候选 → admit=1 (C005 upper_shadow_persistence_5d) / reserve=1 (C003 sign-frequency) / reject=3。**4 轮以来首 admit**——5d upper-shadow alpha_surv=1.508 + incr_ic=+0.031 + cum_dd=-3.5 库内最浅。
- [[batches/batch_016/judge|batch_016]] (return_distribution_signals): 5 候选 → admit=0 / reserve=0 / reject=5。**核心**：skew/kurt/Q-range 三类首批全部 collapse 到 vol_20d (alpha_surv 0.008-0.177)，方向首批即 dead。
- [[batches/batch_015/judge|batch_015]] (barra_residual_alpha): 5 候选 → admit=0 / reserve=0 / reject=5（全 hard_gate）。**核心**：5 个 method-switch 4/4 collapse 到 F004（Huber/hetero/winsor/vol×turn corr 0.91-0.997）。方向 saturated。
- [[batches/batch_014/judge|batch_014]] (barra_residual_alpha): 6 候选 → admit=0 / reserve=1 (C001) / reject=5。**核心**：C002+C005 corr 0.987/0.906 with F004 → vol_20d 唯一主导残差空间；**C003 lookahead 系统盲区**（5d 累计前向收益作为 t 时刻因子值，hard_gate 全过但 ic_oos=0.386 / ls_max_dd=0 是构造 artifact）；新建 T003 thread 跟踪。
- [[batches/batch_013/judge|batch_013]] (barra_residual_alpha): 5 候选 → admit=1 / reserve=1 / reject=3。**C001 admit** (barra_residual_alpha_60d, ICIR=0.293 ls_t=7.34)；**C002 reserve** (vol-20d-only residual, ICIR=0.243 alpha_surv=1.62)；C003/C004/C005 reject (sign_flip/redundant/compute_error)。
- [[batches/batch_012/judge|batch_012]] (barra_residual_alpha): 5 候选 → admit=1 / reserve=1 / reject=3。**Barra residual 假设验证成立**：C001 Barra_residual_IC=0.033 > raw IC=0.024 admit → F004；C003 reserve（style_r²=0.289 耦合）；C002/C004/C005 reject（IC 不足/sign_flip）。
- [[batches/batch_011/judge|batch_011]] (intraday_price_formation): 8 候选 → admit=0 / reserve=0 / reject=8。**F003 扩展窗口全灭**：C001-C004 全部 ic_oos_too_low 或 mono_sign_flip；C005/C006 near_duplicate F003（corr=0.999）；C007 EMA($close,5) CP04 alpha_surv=0.085 证伪。方向 status → saturated。
- [[batches/batch_010/judge|batch_010]] (intraday_price_formation): 8 候选 → admit=1 (F003 overnight_gap_normalized) / reserve=0 / reject=7。**首批 OHLCV-only 候选**：7/8 hard_gate 全部 mono_sign_flip 失效；C004 隔夜跳空/昨日波幅 ls_t=8.36 + 完美单调 + 9年 IC 全正，唯一 admit。
- **[RETROACTIVE 2026-04-19]** [[batches/batch_005/judge|batch_005]] C005 reject → **admit F002 `pb_amount_ratio_20`**。触发：config `alpha_surv_min` 0.60→0.40；rubric CP04 档位放宽；direction-level 自设硬规则（alpha_survival<0.60 一律 reject + dom=vol_20d 一律 reject）已删除。
- [[batches/batch_009/judge|batch_009]] (value_liquidity_interaction): 7 候选 → admit=0 / reserve=2 / reject=5。**self-norm rate×turnover 4/4 全灭**；C005 dom=str_1m breakthrough(历史首次) 但 incr_ic=-0.033(库 reducer) reject；C007 ls_t=-2.43(PnL 最强) vol_20d=18.8 极端。**DSL 空间穷尽**，唯一出口：Python Barra residual。
- [[batches/batch_008/judge|batch_008]] (amount_volatility_signal): 6 候选 → admit=0 / reserve=4 / reject=2。**第 4 次 vol_20d 瓶颈确认**：C003 最强 rank-order(mono=-1.0, max_corr=0.07@F001) 但 alpha_surv=0.24 触 CP04 poor；C002/C005 near-dup(style_r²=0.78)。DSL 封闭，**唯一逃生口：Python Barra residual**。
- [[batches/batch_007/judge|batch_007]] (value_liquidity_interaction): 5 候选 → admit=0 / reserve=3 / reject=2。core finding: **C005 首个 ls_t>2 PnL 显著** (-2.92) 但 "静态-动态正交悖论" 第 2 次复现 (alpha_surv=0.097)；**DSL 空间完全探尽**，下批必须 R8 Python Barra residual。
- [[batches/batch_006/judge|batch_006]] (value_liquidity_interaction): 5 候选 → admit=0 / reserve=3 / reject=2。core finding: **T006 PE/PB/PS 自归一化速率三点通用性确立**（alpha_survival 0.92/0.79/0.72 全 dom=str_1m）但 ls_t 全弱<2；T001 "分母去市值" 路径证伪；C004_b6 极端悖论。
- [[batches/batch_005/judge|batch_005]] (value_liquidity_interaction): 5 候选 → admit=1 (F002 retroactive) / reserve=1 / reject=3。core finding: **C004 首次跳出流动性风格天花板**（dom=str_1m, alpha_survival=0.92）+ **C005/F002 首个 positive IC+perfect mono**。
- [[batches/batch_004/judge|batch_004]] (turnover_structural_signal): 5 候选 → admit=0 / reserve=1 / reject=4。core finding: **turnover 同样撞 vol_20d 天花板**——"field 换方向"非"维度切换"。方向 status saturated。
- [[batches/batch_003/judge|batch_003]] (amount_volatility_signal): 5 候选 → admit=0 / reserve=4 / reject=1。core finding: **DSL 实现空间对 vol_20d 无解**，T002/T004 四子路径全落。
- [[batches/batch_002/judge|batch_002]] (amount_volatility_signal): 5 候选 → admit=0 / reserve=2 / reject=3。core finding: **T001 窗口扫描答案 = 10d 最优**（F001 anchor 地位确立）。
- [[batches/batch_001/judge|batch_001]] (amount_volatility_signal): 8 候选 → admit=1 / reserve=2 / reject=5。core finding: 短窗口 CV (C001) 强 alpha + 完美单调，但全方向 dominant_style=vol_20d。

## 因子库

> Python 自动维护 —— 请勿手改 sentinel 之间内容。

<!-- BEGIN FACTOR-LIBRARY -->
- [[factors/F001|amount_cv_10]] `A` · amount_volatility_signal · ICIR_oos=-0.716, Mono=-1.00 · `Div(Std($amount, 10), Mean($amount, 10))`
- [[factors/F002|pb_amount_ratio_20]] `A` · value_liquidity_interaction · ICIR_oos=0.263, Mono=1.00 · `Div($pb_ratio, Mean($amount, 20))`
- [[factors/F003|overnight_gap_normalized]] `B` · intraday_price_formation · ICIR_oos=0.379, Mono=1.00 · `Div(Sub($open, Ref($close, 1)), Mean($high, 1))`
- [[factors/F004|barra_residual_return]] `B` · barra_residual_alpha · ICIR_oos=0.293, Mono=1.00
- [[factors/F006|upper_shadow_persistence_5d]] `C` · ohlc_temporal_aggregation · ICIR_oos=0.192, Mono=0.90 · `Mean(Div(Sub($high, $close), Sub($high, $low)), 5)`
- [[factors/F007|open_position_persistence_5d]] `B` · ohlc_temporal_aggregation · ICIR_oos=0.336, Mono=0.90 · `Mean(Div(Sub($open, $low), Sub($high, $low)), 5)`
- [[factors/F008|upper_shadow_persistence_3d]] `C` · ohlc_temporal_aggregation · ICIR_oos=0.233, Mono=0.90 · `Mean(Div(Sub($high, $close), Sub($high, $low)), 3)`
- [[factors/F009|overnight_intraday_spread_5d]] `B` · overnight_intraday_split · ICIR_oos=0.408, Mono=1.00 · `Mean(Sub(Div(Sub($open, Ref($close, 1)), Ref($close, 1)), Div(Sub($close, $open), $open)), 5)`
- [[factors/F010|overnight_return_persistence_5d]] `A` · overnight_intraday_split · ICIR_oos=0.396, Mono=1.00 · `Mean(Div(Sub($open, Ref($close, 1)), Ref($close, 1)), 5)`
- [[factors/F011|overnight_return_persistence_3d]] `B` · overnight_intraday_split · ICIR_oos=0.422, Mono=1.00 · `Mean(Div(Sub($open, Ref($close, 1)), Ref($close, 1)), 3)`
<!-- END FACTOR-LIBRARY -->

---

## Statistics (machine-generated)

<!-- BEGIN AUTO-SECTION -->

| Direction | Status | Priority | Rounds | Admits | Threads | Last batch |
|---|---|---|---|---|---|---|
| amount_volatility_signal | productive | high | 5 | 1 | 1 | batch_008 |
| asymmetric_momentum | exploring | medium | 1 | 0 | 2 | batch_028 |
| barra_residual_alpha | saturated | low | 6 | 1 | 1 | batch_015 |
| fundamental_momentum | dead | low | 1 | 0 | 0 | batch_022 |
| intraday_price_formation | saturated | high | 4 | 2 | 1 | batch_011 |
| liquidity_acceleration | exploring | medium | 1 | 0 | 2 | batch_023 |
| ohlc_temporal_aggregation | saturated | medium | 5 | 3 | 1 | batch_021 |
| overnight_intraday_split | productive | high | 3 | 3 | 1 | batch_027 |
| return_distribution_signals | dead | low | 1 | 0 | 0 | batch_016 |
| return_momentum_acceleration | exploring | medium | 1 | 0 | 1 | batch_029 |
| turnover_structural_signal | saturated | low | 1 | 0 | 0 | batch_004 |
| value_liquidity_interaction | productive | high | 6 | 1 | 2 | batch_009 |
| vol_shock_signals | dead | low | 1 | 0 | 0 | batch_024 |

| Metric | Value |
|---|---|
| Total factors admitted | 11 |
| Current round | 28 |
| Last consolidation | — |

<!-- END AUTO-SECTION -->
