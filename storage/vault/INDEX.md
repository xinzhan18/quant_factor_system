---
generated_at: 2026-04-18T00:00:00Z
round: 0
total_active_directions: 0
total_factors_admitted: 0
last_batch: null
last_consolidation_round: null
---

# Factor Research Index

> MOC (Map of Content)：所有研究方向和 admitted 因子的总览。
> 上半段由 LLM 维护；下半段由 Python 自动刷新。

## 活跃方向

### [[directions/amount_volatility_signal|成交额波动率信号]] `productive` `high`
首批 [[batches/batch_001/judge|batch_001]] 8 候选 → 1 admit (C001 `amount_cv_10`) / 2 reserve / 5 reject。T001 短窗口 CV 确认为 core edge（ICIR_OOS=-0.716，9 年同号），T002 尾部信号待 vol_20d 正交化，T003 当前算子族失败（Log 发散 / Corr 分位翻转）→ 新开 T004 替代实现。**方向级结构发现**：8/8 候选 dominant_style=vol_20d，下批优先 orthogonalize 验证。

## 最近 Batch

- [[batches/batch_001/judge|batch_001]] (amount_volatility_signal): 8 候选 → admit=1 / reserve=2 / reject=5。core finding: 短窗口 CV (C001) 强 alpha + 完美单调，但全方向 dominant_style=vol_20d 需下轮 orthogonalize。

## 因子库

_（Phase 4 分配 F{id} 后刷新；本批 admit C001 `amount_cv_10` 将在 Phase 4 归档后列出）_

---

## Statistics (machine-generated)

<!-- BEGIN AUTO-SECTION -->

| Direction | Status | Priority | Rounds | Admits | Threads | Last batch |
|---|---|---|---|---|---|---|
| amount_volatility_signal | productive | high | 1 | 1 | 2 | batch_001 |

| Metric | Value |
|---|---|
| Total factors admitted | 1 |
| Current round | 0 |
| Last consolidation | — |

<!-- END AUTO-SECTION -->
