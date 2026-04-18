---
generated_at: 2026-04-18T18:27:41Z
round: 2
total_active_directions: 1
total_factors_admitted: 1
last_batch: batch_002
last_consolidation_round: null
---

# Factor Research Index

> MOC (Map of Content)：所有研究方向和 admitted 因子的总览。
> 上半段由 LLM 维护；下半段由 Python 自动刷新。

## 活跃方向

### [[directions/amount_volatility_signal|成交额波动率信号]] `productive` `high`
累计 3 batches，18 候选 → 1 admit / 6 reserve / 11 reject（admit 率 **5.6%** 接近 saturated 临界）。[[batches/batch_003/judge|batch_003]] **第三次确认结构瓶颈**：18/18 dominant_style=vol_20d；分位数 (C003/C004) + 归一化 Slope (C002) + sign-only Corr (C005) 四条子路径 alpha_survival < 0.60 全部 poor；Sign×amount 条件均值 (C001) mono_flip hard_gate。**F001 不可撼动 anchor**。下轮决策树：方案 A 开辟 turnover_structural_signal 新方向 / 方案 B Python 逃生口做 vol_20d residual / 方案 C 拉长 horizon 重测 C005。

## 最近 Batch

- [[batches/batch_003/judge|batch_003]] (amount_volatility_signal): 5 候选 → admit=0 / reserve=4 / reject=1。core finding: **DSL 实现空间对 vol_20d 无解**，T002/T004 四子路径全落；C005 sign-only Corr max_corr=0.07@F001 首证非-CV 独立机制但 PnL 坍塌。下轮需跳出方向内 DSL 家族。
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

| Metric | Value |
|---|---|
| Total factors admitted | 1 |
| Current round | 2 |
| Last consolidation | — |

<!-- END AUTO-SECTION -->
