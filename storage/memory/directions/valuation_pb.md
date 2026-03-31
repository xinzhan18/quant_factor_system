---
name: valuation_pb
status: active
category: valuation
source: batch_021
parent_factor: null
attempts: 1
best_ic: 0.038
last_batch: batch_021
priority: high
created: '2026-03-29'
---

P/B ratio and book-to-price — classic value factors

## Rationale
Low PB (high book-to-price) = value stocks = outperform in A-shares. New signal dimension from fundamental data.

## Probe Records
- 2026-03-29: Rank($pb_ratio, 60) → IC=-0.025, ICIR=-0.146 — GOOD
- 2026-03-29: Div(1, $pb_ratio) → IC=+0.028 (OOS=+0.033) — GOOD, OOS improvement

## Candidate History
- batch_021: inverse_pb ADMITTED as F028 (IC=+0.028, ICIR=0.262, max_corr=0.559, OOS_mono=1.0)
- batch_021: pb_ratio_rank_60 ADMITTED as F034 (IC=-0.038, ICIR=-0.293, max_corr=0.570)
