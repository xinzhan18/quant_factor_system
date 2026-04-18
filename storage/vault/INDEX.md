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

### [[directions/volume_price_signal|Volume-Price Signal]] `exploring→productive` `high`
batch_001 首批 6 候选 (T001/T002/T003 baselines) → admit 1 (C005, T003 vol-weighted anchor), reserve 3, reject 2. T001 answered (price-level wins over return-level). 核心阻塞是 CP04 — 全家族 `alpha_survival_ratio` 0.31–0.46 低于 0.60 clean 阈值，`dominant_style_exposure=vol_20d`。T004 (Barra-vol 脱敏) 新增为 batch_002 首要议题。

## 最近 Batch

- [[batches/batch_001/judge|batch_001]] (volume_price_signal): 6 candidates → 1 admit / 3 reserve / 2 reject。核心发现：PV correlation family 整体是 vol_20d 风格代理，edge 存在但 alpha_survival 不过关。

## 因子库

- **batch_001 admitted (pending F{id} allocation)**: C005 `Mul(Corr($close, $volume, 20), Std($volume, 20))` — T003 anchor, ICIR_oos=-0.362 ls_t=-3.68, CP04 poor but admitted as direction reference.

---

## Statistics (machine-generated)

<!-- BEGIN AUTO-SECTION -->

| Direction | Status | Priority | Rounds | Admits | Threads | Last batch |
|---|---|---|---|---|---|---|
| volume_price_signal | exploring | high | 1 | 1 | 3 | batch_001 |

| Metric | Value |
|---|---|
| Total factors admitted | 1 |
| Current round | 0 |
| Last consolidation | — |

<!-- END AUTO-SECTION -->
