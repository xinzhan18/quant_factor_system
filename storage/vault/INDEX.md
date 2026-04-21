---
generated_at: 2026-04-21T16:42:28Z
round: 29
total_active_directions: 8
total_factors_admitted: 10
last_batch: batch_029
last_consolidation_round: null
---

# Factor Research Index

> MOC (Map of Content)：所有研究方向和 admitted 因子的总览。
> 上半段由 LLM 维护；下半段由 Python 自动刷新。

## 活跃方向

<!-- BEGIN NARRATIVE-DIRECTIONS -->

### [[directions/amount_volatility_signal|amount_volatility_signal]] `productive` `high`
累计 5 rounds · **1 admits** · last batch_008.
**admit=0 · reserve=4 (C002 C003 C004 C005) · reject=2 (C001 C006)**。方向第 4 次确认 vol_20d 结构性瓶颈。

### [[directions/value_liquidity_interaction|value_liquidity_interaction]] `productive` `high`
累计 6 rounds · **1 admits** · last batch_009.
**admit=0 · reserve=2 (C003 C007) · reject=5 (C001 C002 C004 C005 C006)**。方向第 5 批零 admit。

### [[directions/liquidity_acceleration|liquidity_acceleration]] `exploring` `medium`
累计 1 rounds · **0 admits** · last batch_023.
**admit=0 / reserve=2 (C001 + C003) / reject=1 (C002)**

### [[directions/intraday_price_formation|intraday_price_formation]] `saturated` `high`
累计 4 rounds · **2 admits** · last batch_011.
8 候选 → admit=0 / reserve=0 / reject=8。方向 status → saturated。

### [[directions/overnight_intraday_split|overnight_intraday_split]] `saturated` `high`
累计 3 rounds · **3 admits** · last batch_027.
**admit=0 / reserve=0 / reject=3 — direction status: productive → saturated**

### [[directions/ohlc_temporal_aggregation|ohlc_temporal_aggregation]] `saturated` `medium`
累计 5 rounds · **3 admits** · last batch_021.
**admit=0 / reserve=1 / reject=2 — direction status: productive → saturated**

### [[directions/barra_residual_alpha|barra_residual_alpha]] `saturated` `low`
累计 6 rounds · **1 admits** · last batch_015.
**admit=0 / reserve=0 / reject=5**

### [[directions/turnover_structural_signal|turnover_structural_signal]] `saturated` `low`
累计 1 rounds · **0 admits** · last batch_004.
**admit=0 · reserve=1 (C003 加速度) · reject=4** — **方向首批即触发 saturated**。status `exploring → saturated`；priority `high → low`。

<!-- END NARRATIVE-DIRECTIONS -->

## 最近 Batch

<!-- BEGIN NARRATIVE-RECENT -->

- [[batches/batch_029/judge|batch_029]] — batch_029 · [[directions/return_momentum_acceleration]] · 3 candidates (direction 首批) · ❌ **admit=0** · ❌ **reject=3** · **核心发现**: return momentum 变化率 3/3 ls_t<1 (C001=-0.81, C003=-0.49) 或 mono_sign_flip (C002)。**price return rate 与 fundamental rate 同源失败**——rate 形式不携稳定 alpha。 · **MT Budget**: cumulative 131 → **134** · direction 0 → **3** · bucket `low`
- [[batches/batch_028/judge|batch_028]] — batch_028 · [[directions/asymmetric_momentum]] · 3 candidates (direction 首批) · ❌ **admit=0** · ❌ **reject=3** (全 hard_gate) · **核心发现**: up/down momentum 分解 **全 IS/OOS sign/mono 反转**——IS 有效的方向在 OOS 完全反转，证明 loss aversion 信号在 A 股市场 **regime-dependent**，不构成稳定 cross-section alpha。Direction 首批 dead。 · **MT Budget**: cumulative 128 → **131** · direction 0 → **3** · bucket `low`
- [[batches/batch_027/judge|batch_027]] — batch_027 · [[directions/overnight_intraday_split]] · 3 candidates · ❌ **admit=0** · ❌ **reject=3** · **核心发现**: pure intraday return 3/3 corr 0.65-0.89 @F009 + library reducer。**intraday 段不独立于 F009 spread**——F009 = overnight - intraday 所以 intraday ≈ overnight - F009，数学相关必然。Direction 进一步 saturated。 · **MT Budget**: cumulative 125 → **128** · direction 6 → **9** · bucket `medium`
- [[batches/batch_026/judge|batch_026]] — batch_026 · [[directions/overnight_intraday_split]] · 3 candidates · ✅ **admit=1** (C001 → overnight_return_persistence_3d) · ⏸ **reserve=1** (C002 10d 库 bloat) · ❌ **reject=1** (C003 mono=+0.10) · **核心发现**: F010 3d ablation 成功 (ls_t=7.98 整库第 2 强)；10d reserve 因库 bloat；product form 破坏 mono rank。 · **MT Budget**: cumulative 122 → **125** · direction 3 → **6** · bucket `low`
- [[batches/batch_025/judge|batch_025]] — batch_025 · [[directions/overnight_intraday_split]] · 3 candidates (direction 首批) · ✅ **admit=2** (C001 overnight_intraday_spread_5d, C002 overnight_return_persistence_5d) · ❌ **reject=1** (C003 corr sign_flip) · **核心发现**: **首批 DOUBLE ADMIT**——overnight/intraday 分解是全新 cross-section 维度。C002 ls_t=7.50 是整库最强之一；C001 incr_ic=+0.044 是库增值最强候选之一 (4× F007 的 0.023)。 · **MT Budget**: cumulative 119 → **122** · direction 0 → **3** · bucket `low`
- [[batches/batch_024/judge|batch_024]] — batch_024 · [[directions/vol_shock_signals]] · 3 candidates (direction 首批) · ❌ **admit=0** · ❌ **reject=3** · **核心发现**: vol shock 信号 3/3 失败——C001 库 reducer (incr_ic=-0.027) + C002 hard_gate mono_sign_flip + C003 **alpha_surv=0.117 catastrophic 第 4 次出现 vol-derived 签名**。Direction 首批即 **dead**。 · **MT Budget**: cumulative 116 → **119** · direction 0 → **3** · bucket `low`
- [[batches/batch_023/judge|batch_023]] — batch_023 · [[directions/liquidity_acceleration]] · 3 candidates (direction 首批) · ❌ **admit=0** · ⏸ **reserve=2** (C001 5d/60d amount; C003 5d/60d turnover) · ❌ **reject=1** (C002 normalized accel) · **核心发现**: 流动性加速度信号 mono=-1.00 完美 + ls_t strong (-2.92 to -3.27) — **rank-order 在方向首批就强**。但 max_corr 集中 0.27-0.32@F001 (low-medium) + incr_ic 全负 (-0.021 to -0.030)。**与 F001 (amount CV) 部分重叠 + library reducer**——admit 会稀释 F001 信号。 · **MT Budget**: cumulative 113 → **116** · direction 0 → **3** · bucket `low`
- [[batches/batch_022/judge|batch_022]] — batch_022 · [[directions/fundamental_momentum]] · 4 candidates (direction 首批) · ❌ **admit=0** · ❌ **reject=4** · **核心发现**: PE/PB/PS 变化率作为 cross-section 信号**全部弱**——4/4 ls_t<2 + mono≤-0.70 + 全 library reducer (incr_ic 全负)。Rank-based variant (C003) 改善 mono 但仍 weak。**fundamental rate hypothesis 直接证伪**。 · **MT Budget**: cumulative 109 → **113** · direction 0 → **4** · bucket `low`
- [[batches/batch_021/judge|batch_021]] — batch_021 · [[directions/ohlc_temporal_aggregation]] · 3 candidates · ❌ **admit=0** · ⏸ **reserve=1** (C002 7d upper-shadow) · ❌ **reject=2** · **核心发现**: F007 (5d open-position) 不像 F006 那样有 3d phase variant —— C001 3d open-position **mono_sign_flip 完全反转** (IS=-1.00 OOS=+0.90)。**open-position 信号是 5d-only stability**。C002 7d upper-shadow alpha_surv=1.685 极 clean 但 corr=0.834@F006 太 high 转 reserve（库 bloat）。C003 turnover-weighted body 是 F007 noisy 版本。 · **MT Budget**: cumulative 106 → **109** · direction 19 → **22** · bucket `high`
- [[batches/batch_020/judge|batch_020]] — batch_020 · [[directions/ohlc_temporal_aggregation]] · 5 candidates · ✅ **admit=1** (C001 → upper_shadow_persistence_3d) · ⏸ **reserve=0** · ❌ **reject=4** (C002 C003 C004 C005) · **核心发现**: **F006 window ablation 找到 3d phase variant**——C001 (3d upper-shadow) ic=+0.029 ls_t=2.91 mono=+0.90 alpha_surv=1.268 incr_ic=+0.022 admit；max_corr=0.758@F006 high 但 incr_ic 显示真实库增值。10d 窗口 (C002) mono_sign_flip 反转——**确认 3d-5d 是 sweet spot 区间**。Cross-day signs (C003/C004) 和 Donchian (C005) 全 reject——20d 范围信号失败。 · **MT Budget**: cumulative 101 → **106** · direction 14 → **19** · bucket `high`（接近 saturated 但未到）
- [[batches/batch_019/judge|batch_019]] — batch_019 · [[directions/ohlc_temporal_aggregation]] · 4 candidates · ❌ **admit=0** · ⏸ **reserve=0** · ❌ **reject=4** · **核心发现**: 5d OHLC aggregation 在 F006 (close 端) + F007 (open 端) 之外**剩余维度无独立 alpha**。Range 演化 (C001) rank 噪声大；流动性调整 range (C002) corr=0.746@F002；volume-weighted body (C003) corr=0.721@F007；离散 count (C004) hard_gate sign_flip。**方向接近 saturated**——5d 窗口的 directional ratio 空间被 F006/F007 饱和。 · **MT Budget**: cumulative 97 → **101** · direction 10 → **14** · bucket `medium`
- [[batches/batch_018/judge|batch_018]] — batch_018 · [[directions/ohlc_temporal_aggregation]] · 5 candidates · ✅ **admit=1** (C003 → open_position_persistence_5d) · ⏸ **reserve=0** · ❌ **reject=4** (C001 C002 C004 C005) · **核心发现**: **方向连续两批 admit** —— C003 open-position 5d (ic=+0.037 ls_t=3.22 mono=+0.90 alpha_surv=0.637 incr_ic=+0.023 cum_dd=-1.5) 与 F006 (upper-shadow) 机制正交（max_corr=0.276）。**OHLC 5d aggregation 在开盘+收盘两端独立载 alpha**。C001 lower-shadow corr=1.000 与 F006 algebraic 等价（reject）；C004 signed-range corr=0.544 与 F006 部分重叠；C005 overnight-gap-magnitude alpha_surv=0.164 暴露另一个 vol-derived pattern。 · **MT Budget**: cumulative 92 → **97** · direction 5 → **10** · bucket `medium` (上界)
- [[batches/batch_017/judge|batch_017]] — batch_017 · [[directions/ohlc_temporal_aggregation]] · 5 candidates (direction 首批) · ✅ **admit=1** (C005 → upper_shadow_persistence_5d) · ⏸ **reserve=1** (C003 bullish-freq) · ❌ **reject=3** (C001 C002 C004) · **核心发现**: **方向假设验证成立** —— 5 日聚合 OHLC patterns 在 close-strength 维度（C005 upper-shadow / C004 close/high）携带**真正独立的 alpha**（与单日 saturated 形成对比）。**关键判别**：alpha_survival 区分"独立载体"（C005=1.508 ✓）vs "vol_20d 镜像"（C004=0.003 ✗）——这是方向首次出现 Barra-clean 信号。**4 轮以来首个 admit！** · **MT Budget**: cumulative 87 → **92** · direction 0 → **5**（首批） · bucket `low`
- [[batches/batch_016/judge|batch_016]] — batch_016 · [[directions/return_distribution_signals]] · 5 candidates (direction 首批) · ❌ **admit=0** · ⏸ **reserve=0** · ❌ **reject=5** · **核心发现**: **方向假设直接证伪——所有高阶矩 (skew/kurt/Q-range) 在 cross-section 上都 collapse 到 vol_20d**。C004 quantile range mono=-0.9 + ls_t=-2.28 看似强，但 style_r²=0.845 + alpha_survival=0.008 暴露其本质就是 vol_20d 的 monotone 变换。Skew/kurt 不是独立维度。 · **MT Budget**: cumulative 82 → **87** · direction 0 → **5**（首批） · bucket `low`
- [[batches/batch_015/judge|batch_015]] — batch_015 · [[directions/barra_residual_alpha]] · 5 candidates · ❌ **admit=0** · ⏸ **reserve=0** · ❌ **reject=5** (C001–C005 全部 hard_gate) · **核心发现**: **F004 是该 7-style basis 上 OLS-family 残差的唯一不动点**——5 个变体（Huber 鲁棒 / 5d HL 8th style / 标准化 / Winsor / vol×turn 交互）4 个 corr=0.907–0.997 with F004，1 个 compute_error。**barra_residual_alpha 方向 saturated** — 在同 7-basis + OLS-family 内不可能产生独立 alpha。 · **MT Budget**: cumulative 77 → **82** · direction 10 → **15** · bucket `medium`

<!-- END NARRATIVE-RECENT -->

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
| asymmetric_momentum | dead | medium | 1 | 0 | 0 | batch_028 |
| barra_residual_alpha | saturated | low | 6 | 1 | 1 | batch_015 |
| fundamental_momentum | dead | low | 1 | 0 | 0 | batch_022 |
| intraday_price_formation | saturated | high | 4 | 2 | 1 | batch_011 |
| liquidity_acceleration | exploring | medium | 1 | 0 | 2 | batch_023 |
| ohlc_temporal_aggregation | saturated | medium | 5 | 3 | 1 | batch_021 |
| overnight_intraday_split | saturated | high | 3 | 3 | 1 | batch_027 |
| return_distribution_signals | dead | low | 1 | 0 | 0 | batch_016 |
| return_momentum_acceleration | dead | medium | 1 | 0 | 0 | batch_029 |
| turnover_structural_signal | saturated | low | 1 | 0 | 0 | batch_004 |
| value_liquidity_interaction | productive | high | 6 | 1 | 2 | batch_009 |
| vol_shock_signals | dead | low | 1 | 0 | 0 | batch_024 |

| Metric | Value |
|---|---|
| Total factors admitted | 10 |
| Current round | 29 |
| Last consolidation | — |

<!-- END AUTO-SECTION -->
