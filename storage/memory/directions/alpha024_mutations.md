---
name: alpha024_mutations
status: exhausted
category: momentum
source: batch_020
parent_factor: factor_021
attempts: 1
best_ic: 0.033
last_batch: batch_020
priority: low
created: '2026-03-29'
---

Window and threshold mutations of alpha024 (F021, IC=+0.049)

## Rationale
Alpha024 is 2nd strongest factor. Window/threshold mutations might decorrelate.

## Probe Records
- 2026-03-29: alpha024_window_20 → IC=+0.022, ICIR=0.156, WinRate=62.0%

## Candidate History
- batch_020: alpha024_window_20 REJECTED (IC=0.033 OK but corr=0.807 with F021)
- batch_020: alpha024_window_40 REJECTED (corr=0.936 with F021)
- batch_020: alpha024_low_threshold REJECTED (corr=1.000 with F021 — threshold change has zero effect)

## Lesson
Alpha024's conditional structure (If/Less with moving average trend) is robust to parameter changes:
- 20d window: corr=0.81, 40d: corr=0.94, threshold change: corr=1.0
- The signal is fundamentally determined by the Min($close, N) component, not the threshold.
- Window mutations on alpha024 are futile — the factor is already optimal at 60d.
