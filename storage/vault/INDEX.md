---
generated_at: 2026-04-19T12:41:09Z
round: 7
total_active_directions: 3
total_factors_admitted: 2
last_batch: batch_007
last_consolidation_round: null
---

# Factor Research Index

> MOC (Map of Content)：所有研究方向和 admitted 因子的总览。
> 上半段由 LLM 维护；下半段由 Python 自动刷新。

## 活跃方向

### [[directions/amount_volatility_signal|成交额波动率信号]] `productive` `high`
累计 4 batches，24 候选 → 1 admit / 10 reserve / 13 reject（admit 率 **4.2%**）。[[batches/batch_008/judge|batch_008]] **第 4 次确认 vol_20d 结构性瓶颈**：19/19 非 hard_gate 候选 100% dominant_style=vol_20d。C003 最强 rank-order(mono=-1.0, max_corr=0.07@F001) 但 alpha_surv=0.24 触 CP04 poor。**DSL 空间已物理封闭**，唯一逃生口：Python vol_20d Barra residual。

### [[directions/turnover_structural_signal|换手率结构信号]] `saturated` `low`
首批 [[batches/batch_004/judge|batch_004]] 即触发 saturated：5 候选 5/5 `dominant_style=vol_20d`，"换手率脱离 vol_20d 风格空间"hypothesis 证伪。仅 C003 加速度 (alpha_survival=1.085) 突破 dealbreaker reserve，四 thread 全部证伪。C001 turnover CV 与 F001 相关 0.955 → shares 短窗近常数 CV 结构等价。

### [[directions/value_liquidity_interaction|价值 × 流动性交互]] `productive` `high`
累计 3 batches，15 候选 → **1 admit (F002)** / 7 reserve / 7 reject。**2026-04-19 追溯升级**：C005_b5 `Div($pb, Mean($amount, 20))` 原判 reject（alpha_survival=0.30 触旧 0.60 硬闸），rubric / config 放宽后重审为 **F002 admit** — max_corr@F001=0.029 正交 + incremental_ic=+0.027 + mono=+1.0 + ls_t=+4.68 + 9 年全正 + cum_dd=-2.17 全库最浅 + 方向互补（F001 负号 / F002 正号）。其他发现：C004_b5 PE rate alpha_survival=0.92 dom=str_1m + T006 PE/PB/PS rate 三点通用性 + C005_b7 首个 ls_t>2；"静态正交 ≠ 动态正交" 悖论 — 指向下批 Python residual R8。

## 最近 Batch

- **[RETROACTIVE 2026-04-19]** [[batches/batch_005/judge|batch_005]] C005 reject → **admit F002 `pb_amount_ratio_20`**。触发：config `alpha_surv_min` 0.60→0.40；rubric CP04 档位放宽；direction-level 自设硬规则（alpha_survival<0.60 一律 reject + dom=vol_20d 一律 reject）已删除。
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
<!-- END FACTOR-LIBRARY -->

---

## Statistics (machine-generated)

<!-- BEGIN AUTO-SECTION -->

| Direction | Status | Priority | Rounds | Admits | Threads | Last batch |
|---|---|---|---|---|---|---|
| amount_volatility_signal | productive | high | 5 | 1 | 1 | batch_008 |
| turnover_structural_signal | saturated | low | 1 | 0 | 0 | batch_004 |
| value_liquidity_interaction | productive | high | 4 | 1 | 1 | batch_005 |

| Metric | Value |
|---|---|
| Total factors admitted | 2 |
| Current round | 7 |
| Last consolidation | — |

<!-- END AUTO-SECTION -->
