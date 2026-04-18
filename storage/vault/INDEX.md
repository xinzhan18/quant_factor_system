---
generated_at: 2026-04-18T18:07:33Z
round: 1
total_active_directions: 1
total_factors_admitted: 1
last_batch: batch_001
last_consolidation_round: null
---

# Factor Research Index

> MOC (Map of Content)：所有研究方向和 admitted 因子的总览。
> 上半段由 LLM 维护；下半段由 Python 自动刷新。

## 活跃方向

### [[directions/amount_volatility_signal|成交额波动率信号]] `productive` `high`
累计 2 batches (batch_001 + [[batches/batch_002/judge|batch_002]])，13 候选 → 1 admit / 4 reserve / 8 reject。[[batches/batch_002/judge|batch_002]] 完成 **T001 窗口扫描**：10d (F001) 为 CV 全局最优（5d/20d/MAD 全部 reserve 或 hard_gate）；T002 "延长窗口" 子路径 (60d Max/Mean) 被 regime-dep 证伪；T004 "幅度版 Corr" 子路径被证伪。**方向级结构加强**：13/13 候选 dominant_style=vol_20d — 下批必做 vol_20d orthogonalize（Python 逃生口或跨 DSL 实现），否则 anchor rule 持续压顶。

## 最近 Batch

- [[batches/batch_002/judge|batch_002]] (amount_volatility_signal): 5 候选 → admit=0 / reserve=2 / reject=3。core finding: **T001 窗口扫描答案 = 10d 最优**（F001 anchor 地位确立）；T002 60d 延长 / T004 幅度 Corr 两子路径证伪；下批转向 robust tail + sign-preserved NaN-safe + vol_20d 正交化。
- [[batches/batch_001/judge|batch_001]] (amount_volatility_signal): 8 候选 → admit=1 / reserve=2 / reject=5。core finding: 短窗口 CV (C001) 强 alpha + 完美单调，但全方向 dominant_style=vol_20d 需下轮 orthogonalize。

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
| amount_volatility_signal | productive | high | 2 | 1 | 2 | batch_002 |

| Metric | Value |
|---|---|
| Total factors admitted | 1 |
| Current round | 1 |
| Last consolidation | — |

<!-- END AUTO-SECTION -->
