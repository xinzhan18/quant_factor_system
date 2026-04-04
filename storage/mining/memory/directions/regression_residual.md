---
name: regression_residual
status: active
category: trend
source: baseline
parent_factor: null
attempts: 0
best_ic: null
last_batch: null
priority: high
created: '2026-03-28'
---

Resi($close, N) as mean-reversion signal

## Rationale
Baseline: Resi(close,5) IC=-0.041, normalized_residual IC=-0.035. Short windows stronger.

## Probe Records
2026-04-01 | Resi($close, 10) | IC=-0.0007 ICIR=-0.005 WinRate=49.2% | pre-batch_024 (no signal)

## Candidate History
