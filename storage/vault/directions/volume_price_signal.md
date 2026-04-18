---
direction_tag: volume_price_signal
status: exploring
priority: high
rounds: 1
admits: 1
last_batch: batch_001
last_activity: '2026-04-18T10:52:05Z'
created_batch: batch_001
members:
- F001
merged_into: null
last_admits:
- F001
last_goal: 'Baseline T001/T002/T003 on CSI1000 at 20d lookback: compare price-vs-return
  forms and $volume-vs-$amount swap.'
---
# Volume-Price Signal

## Hypothesis

A-share markets are retail-driven and momentum-prone, which means informed trading leaves traceable footprints in the **co-movement of price and volume**. When price moves are confirmed by volume (high volume on up days, low on down) it typically marks crowding; when they diverge (low volume on up days, high on down) it typically marks exhaustion and mean-reversion. Classic ICs on `Corr($close, $volume, lookback)` in CSI1000 are modest but stable (ICIR ≈ 0.15–0.30), and these signals tend to survive Barra residualisation because size/beta do not carry the same volume-correlation information.

The initial 20-day lookback is the canonical choice; sub-threads will probe shorter/longer windows, return-volume vs price-volume formulations, and $amount vs $volume (the former is yuan-denominated and therefore implicitly size-normalised).

## Current Focus

After batch_001: the four canonical 20d formulations all carry real edge (ICIR_oos 0.36–0.40, 9-year same-sign ic_by_year) but are structurally overlapping with Barra `vol_20d` — `alpha_survival_ratio` 0.31–0.46, all below the 0.60 clean threshold. Next focus (T004) is explicitly **how to extract PV-correlation alpha that survives Barra vol_20d residualisation** — lookback variation, style-residualised inputs, vol-neutralised denominators.

## Threads

### T001: Price-vs-return correlation formulation [✓ ANSWERED batch_001]
**Question**: Is `Corr($close, $volume)` more or less informative than `Corr(Delta($close,1), $volume)` on CSI1000? The former captures trend-volume alignment; the latter captures return-volume alignment day-by-day.
**Answer**: price-level formulation wins decisively. Both `Corr($close, flow)` candidates (C001, C003) passed hard_gate with mono_oos = -1.0 (perfect); both `Corr(Delta($close,1), flow)` candidates (C002, C004) failed hard_gate on `mono_sign_flip` (IS=+0.60 → OOS=-0.90 or -0.70). IC sign stayed negative in both forms, but the return-form's day-to-day noise broke cross-sectional rank stability. For this direction, stick to `Corr($close, flow, lookback)`.
**Evidence trail**:
- [[batches/batch_001/candidates/C001|batch_001 C001]]: ICIR_oos=-0.389 ls_t=-3.54, mono_oos=-1.0 → **reserve** (CP04 poor)
- [[batches/batch_001/candidates/C002|batch_001 C002]]: hard_gate fail mono_sign_flip → **reject**
- [[batches/batch_001/candidates/C003|batch_001 C003]]: ICIR_oos=-0.398 ls_t=-3.55, mono_oos=-1.0 → **reserve** (CP04 poor)
- [[batches/batch_001/candidates/C004|batch_001 C004]]: hard_gate fail mono_sign_flip → **reject**

### T002: $volume vs $amount as the flow proxy [◉ ACTIVE]
**Question**: Does `$amount` (yuan-denominated) dominate `$volume` (share-denominated) because it absorbs intraday price drift? Or is share-volume the cleaner flow signal?
**Evidence trail**:
- [[batches/batch_001/candidates/C001|batch_001 C001]] ($volume): ICIR_oos=-0.389, alpha_survival=0.388, vol_20d exposure=12.75
- [[batches/batch_001/candidates/C003|batch_001 C003]] ($amount): ICIR_oos=-0.398, alpha_survival=0.308, vol_20d exposure=14.78
Initial read at 20d: $amount gives marginally tighter ICIR but **worse** alpha_survival and larger vol_20d exposure. Statistical strength is a near-tie; risk-cleanness favors $volume. Inconclusive until longer lookback + vol-residualisation tested.
**Next probes**: longer lookback (60d, 120d) for $amount; repeat the swap test after T004 delivers a Barra-clean baseline.

### T003: Volatility-weighted PV correlation [◉ ACTIVE]
**Question**: Does multiplying PV correlation by `Std($volume)` sharpen the signal by upweighting turbulent episodes where the correlation is more informative?
**Evidence trail**:
- [[batches/batch_001/candidates/C005|batch_001 C005]] (price form, Std-weighted): IS ICIR 0.236 → 0.389, OOS ICIR_oos=-0.362 ls_t=-3.68 → **admit → [[factors/F001]]** (direction anchor)
- [[batches/batch_001/candidates/C006|batch_001 C006]] (return form, Std-weighted): ICIR_oos=-0.390, mono_oos=-0.7, alpha_survival=0.460 → **reserve**
Std($volume) weighting boosted IS ICIR by ~65% for the price-form variant, but Barra residual IC stayed flat vs C001 (-0.0147 → -0.0151). Verdict: **hypothesis half-confirmed** — ICIR improvement is real, but the uplift is absorbed entirely into vol_20d exposure rather than contributing residual alpha. The weighting "sharpens" the style exposure, not the pure signal.
**Next probes**: test with Barra-residualised inputs to isolate whether weighting adds residual alpha or just concentrates style.

### T004: Barra-vol desensitisation of PV correlation [◉ ACTIVE] (new batch_001)
**Question**: Can any formulation of PV correlation survive `vol_20d` Barra residualisation with `alpha_survival_ratio ≥ 0.60`? Currently every non-reject candidate sits at 0.31–0.46.
**Evidence trail**: _(pending batch_002)_
**Next probes**: (1) `Div(Corr($close,$volume,20), Std($close,20))` — normalise by own price vol; (2) 60d/120d lookback — longer windows may decorrelate from short-term vol; (3) explicit Barra-residualised-input variant if DSL allows.

## Known Failures

- **C002** `Corr(Delta($close, 1), $volume, 20)` — hard_gate `mono_sign_flip` (IS=+0.60 / OOS=-0.90). Return-level PV correlation inherits day-to-day noise that breaks cross-sectional rank stability.
- **C004** `Corr(Delta($close, 1), $amount, 20)` — hard_gate `mono_sign_flip` (IS=+0.60 / OOS=-0.70). Same failure mode as C002; confirms `Corr(Delta($close,1), flow, 20)` is a structurally unstable formulation for this direction.

## Related

- [[lessons#Structural Constraints]]
- [[lessons#Data Facts]]

## Narrative Log

### 2026-04-18 [[batches/batch_001/judge|batch_001]]
First batch — 6 candidates covering T001/T002/T003 baselines at 20d lookback. **Verdicts**: 1 admit (C005, T003 anchor), 3 reserve (C001/C003/C006), 2 reject (C002/C004 — both hard_gate mono_sign_flip on the return-level formulation).

**Thread 进展**：
- T001 **ANSWERED** → price-level Corr wins; return-level is structurally unstable
- T002 still **ACTIVE** → $volume vs $amount a near-tie at 20d, $amount loses on alpha_survival
- T003 still **ACTIVE** → Std-weighting raises ICIR but gain is all vol_20d exposure
- T004 **new** — how to desensitise PV correlation from Barra vol_20d (the core blocker across the whole family)

**核心结构性发现**：all 4 non-reject candidates have `dominant_style_exposure = vol_20d` (exposures 10.2–28.5) and `alpha_survival_ratio ∈ [0.31, 0.46]`, below the 0.60 clean threshold. The direction has real OOS edge (ICIR 0.36–0.40, 9-year same-sign) but current formulations are vol_20d style proxies. batch_002 must lead with T004 vol-desensitisation variants.

**Status change**: `exploring → productive` because first admit (C005) landed; but CP04 risk-cleanness is the binding constraint on all further admits.

**下一步**：batch_002 opens with T004 vol-desensitised candidates (div-normalised, long lookback, or Barra-pre-residualised) + one T002 long-lookback revisit. Goal: produce at least one candidate with `alpha_survival_ratio ≥ 0.60`.
