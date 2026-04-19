---
generated_at: 2026-04-19T06:07:04Z
round: 6
total_active_directions: 3
total_factors_admitted: 1
last_batch: batch_006
last_consolidation_round: null
---

# Factor Research Index

> MOC (Map of Content)：所有研究方向和 admitted 因子的总览。
> 上半段由 LLM 维护；下半段由 Python 自动刷新。

## 活跃方向

### [[directions/amount_volatility_signal|成交额波动率信号]] `productive` `high`
累计 3 batches，18 候选 → 1 admit / 6 reserve / 11 reject（admit 率 **5.6%** 接近 saturated 临界）。**F001 不可撼动 anchor**，18/18 候选 dominant_style=vol_20d。方向内 DSL 实现空间事实上封闭，复活需 Python 逃生口 Barra residual。

### [[directions/turnover_structural_signal|换手率结构信号]] `saturated` `low`
首批 [[batches/batch_004/judge|batch_004]] 即触发 saturated：5 候选 5/5 `dominant_style=vol_20d`，"换手率脱离 vol_20d 风格空间"hypothesis 证伪。仅 C003 加速度 (alpha_survival=1.085) 突破 dealbreaker reserve，四 thread 全部证伪。C001 turnover CV 与 F001 相关 0.955 → shares 短窗近常数 CV 结构等价。

### [[directions/value_liquidity_interaction|价值 × 流动性交互]] `exploring` `high`
累计 2 batches，10 候选 → 0 admit / 5 reserve / 5 reject。[[batches/batch_006/judge|batch_006]] **T006 三点通用性确立** — PE/PB/PS 自归一化速率 (C004_b5 / C001 / C002) 在 rank-order 层形态高度一致（alpha_survival 0.92/0.79/0.72、dom=**str_1m**）跨 valuation 普适；但 **ls_t 全部弱 <2**，PnL 层未兑现。T001 "分母去市值" 路径证伪（C003 vs C005_b5 诊断）。**C004_b6 极端悖论**：style_r²=0.08 clean + alpha_survival=0.0009 poor — "低 style_r² ≠ barra-clean" 标本。下轮 batch_007 方案 A+B：合成 + 秩差 DSL 内验证 PnL 转化；若失败转 Python Barra residual (R8)。

## 最近 Batch

- [[batches/batch_006/judge|batch_006]] (value_liquidity_interaction): 5 候选 → admit=0 / reserve=3 / reject=2。core finding: **T006 PE/PB/PS 自归一化速率三点通用性确立**（alpha_survival 0.92/0.79/0.72 全 dom=str_1m）但 ls_t 全弱<2；T001 "分母去市值" 路径证伪；C004_b6 极端悖论（低 style_r² + 极低 alpha_survival）。
- [[batches/batch_005/judge|batch_005]] (value_liquidity_interaction): 5 候选 → admit=0 / reserve=1 / reject=4。core finding: **C004 首次跳出流动性风格天花板**（dom=str_1m, alpha_survival=0.92）+ **C005 首个 positive IC+perfect mono**。
- [[batches/batch_004/judge|batch_004]] (turnover_structural_signal): 5 候选 → admit=0 / reserve=1 / reject=4。core finding: **turnover 同样撞 vol_20d 天花板**——"field 换方向"非"维度切换"。方向 status saturated。
- [[batches/batch_003/judge|batch_003]] (amount_volatility_signal): 5 候选 → admit=0 / reserve=4 / reject=1。core finding: **DSL 实现空间对 vol_20d 无解**，T002/T004 四子路径全落。
- [[batches/batch_002/judge|batch_002]] (amount_volatility_signal): 5 候选 → admit=0 / reserve=2 / reject=3。core finding: **T001 窗口扫描答案 = 10d 最优**（F001 anchor 地位确立）。
- [[batches/batch_001/judge|batch_001]] (amount_volatility_signal): 8 候选 → admit=1 / reserve=2 / reject=5。core finding: 短窗口 CV (C001) 强 alpha + 完美单调，但全方向 dominant_style=vol_20d。

## 因子库

> Python 自动维护 —— 请勿手改 sentinel 之间内容。

<!-- BEGIN FACTOR-LIBRARY -->
- [[factors/F001|amount_cv_10]] `A` · amount_volatility_signal · ICIR_oos=-0.716, Mono=-1.00 · `Div(Std($amount, 10), Mean($amount, 10))`
<!-- END FACTOR-LIBRARY -->

---

## Statistics (machine-generated)

<!-- BEGIN AUTO-SECTION -->

| Direction | Status | Priority | Rounds | Admits | Threads | Last batch |
|---|---|---|---|---|---|---|
| amount_volatility_signal | productive | high | 3 | 1 | 0 | batch_003 |
| turnover_structural_signal | saturated | low | 1 | 0 | 0 | batch_004 |
| value_liquidity_interaction | exploring | high | 2 | 0 | 1 | batch_006 |

| Metric | Value |
|---|---|
| Total factors admitted | 1 |
| Current round | 6 |
| Last consolidation | — |

<!-- END AUTO-SECTION -->
