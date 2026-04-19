---
generated_at: 2026-04-19T05:28:19Z
round: 3
total_active_directions: 2
total_factors_admitted: 1
last_batch: batch_003
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

## 最近 Batch

- [[batches/batch_004/judge|batch_004]] (turnover_structural_signal): 5 候选 → admit=0 / reserve=1 / reject=4。core finding: **turnover 同样撞 vol_20d 天花板**——"field 换方向"非"维度切换"，Barra basis 覆盖所有流动性-波动率派生量。方向 status saturated / priority low。
- [[batches/batch_003/judge|batch_003]] (amount_volatility_signal): 5 候选 → admit=0 / reserve=4 / reject=1。core finding: **DSL 实现空间对 vol_20d 无解**，T002/T004 四子路径全落；C005 sign-only Corr max_corr=0.07@F001 首证非-CV 独立机制但 PnL 坍塌。
- [[batches/batch_002/judge|batch_002]] (amount_volatility_signal): 5 候选 → admit=0 / reserve=2 / reject=3。core finding: **T001 窗口扫描答案 = 10d 最优**（F001 anchor 地位确立）；T002 60d 延长 / T004 幅度 Corr 两子路径证伪。
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

| Metric | Value |
|---|---|
| Total factors admitted | 1 |
| Current round | 3 |
| Last consolidation | — |

<!-- END AUTO-SECTION -->
