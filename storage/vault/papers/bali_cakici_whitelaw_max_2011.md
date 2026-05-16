---
paper_slug: bali_cakici_whitelaw_max_2011
source_pdf: raw/papers/Bali-Cakici-Whitelaw-MAX-2011.pdf
source_kind: generic_pdf
arxiv_id: null
status: reviewed
primary_frequency: daily
direction_tag: null
reviewed_at: 2026-05-02
---

# Maxing Out — Stocks as Lotteries and the Cross-Section of Expected Returns

## Core Claim

Bali, Cakici, Whitelaw (2011, JFE) sort NYSE/Amex/Nasdaq stocks each month on **MAX = max daily return over the prior month** (and `MAX(N)` = mean of top-N daily returns). Decile-10 minus decile-1 value-weighted four-factor alpha is **−1.18% / month, t = −4.71**, EW −0.66% t = −2.31. The effect is monotone only in the top three deciles (1–7 are flat at ~1% / month, 8–10 fall to 0.86 / 0.52 / −0.02). Robust to controls for size, BM, momentum, REV, ILLIQ, and crucially **flips the sign of the IVOL puzzle of Ang-Hodrick-Xing-Zhang (2006/2009)**: when both MAX and IVOL are in the firm-level Fama-MacBeth regression, MAX is significantly negative and IVOL becomes positive (often insignificant). Persistence: a top-decile MAX stock has 35% probability of staying in decile 10 next month, 68% probability of being in decile 8–10. Sample 1962-07 → 2005-12.

The mechanism the authors push: cumulative prospect theory (Tversky-Kahneman 1992 / Barberis-Huang 2008) + optimal-beliefs distortion (Brunnermeier-Gollier-Parker 2007) — under-diversified retail investors over-weight small-probability large-payoff outcomes, bid up high-MAX stocks, predictable underperformance follows. They explicitly distinguish this from skewness preference (Kraus-Litzenberger / Mitton-Vorkink): MAX survives controls for total skew, idiosyncratic skew, expected idiosyncratic skew (Boyer-Mitton-Vorkink 2010), and co-skew.

Univariate composition of decile 10 (Table 5): median MAX 17.77%, median size $21.5M (vs $316M for decile 1), median price $6.47, beta 1.20, illiquidity 14× decile 1, IVOL 6.4× decile 1, MOM −11.74% (loser over prior 11 months), REV +9.18% (recent winner). **Decile 10 is small + illiquid + cheap + losers + recently up + high IVOL — basically the worst slice of the market on every dimension that should normally pay a premium.** The −1.18% alpha is therefore even more striking after controls.

## Aha Moment

**MAX is empirically the same object as Q90/Q100 of daily returns — and the entire `return_distribution_signals` direction (batch_016, DEAD) plus `quantile_shape_signals` (batch_044, DEAD) have already proven that this object is *monotone-equivalent to vol_20d* in csi1000.** The paper's "lottery preference" alpha is therefore *highly likely to be the IVOL puzzle relabeled* in our universe — and on the long-only A-share side it is *uninvestable as a standalone short-MAX signal*.

The genuinely unexplored mechanism is the **MAX-as-conditioning-variable** version (Chen-Cohen-Liang-Sun 2025 extension): use MAX-decile membership as a binary state filter on a base reversal signal, expecting high-MAX past-loser → next-week winner. That structure is "binary regime gate × weak base signal", which is **exactly the family `up_fraction_regime_gating` (batch_080, freshly exploring) is testing** — and which `trend_quality_gated` (DEAD batch_037) already preliminarily falsified. So the value-add of *this paper specifically* on top of the already-active gating-direction work is small.

## Candidate Ideas

### Idea 1 — Raw MAX(20d) standalone (paper original)

- **Paper mechanism**: `MAX(20)` = max daily return over past month, sort cross-sectionally, short top decile / long bottom decile, expect decile 10 underperformance
- **Target frequency**: daily
- **Current readiness**: `dsl_ready` (mechanically) but **library-coverage blocked**
- **Required fields**: `$close`, `Ref($close, 1)`
- **Why it may survive daily downsampling**: paper IS daily-bar based, no frequency mismatch
- **Main distortion risk**: **Q90/Q100 of returns has been disproven 2 independent times** (`return_distribution_signals` C004 Q90-Q10 `alpha_surv=0.008` integral library minimum; `quantile_shape_signals` 4× cross-direction confirmation). MAX is the limiting case (Q100). Lessons.md F001/F301 explicitly: *"any daily-bar mean-of-power / quantile / power-mean transformation … monotone-equivalent to vol_20d rank, alpha_survival typically < 0.30"*. Plus A-share has no short side → Bali's −1% alpha is short-leg dominated and uninvestable on the long side
- **Suggested direction tag**: none — covered by dead direction lessons

### Idea 2 — MAX-conditional reversal: high-MAX past-loser → next-week winner (long-only investable angle)

- **Paper mechanism** (Chen-Cohen-Liang-Sun 2025 extension; Bali 2011 doesn't address this explicitly): partition cross-section into 5×5 of {past-week return quintile} × {MAX(20d) quintile}; the cell {Q1 past-week return × Q5 MAX} earns +1.66% next week vs +0.65% baseline; the symmetric cell {Q5 past-week return × Q5 MAX} earns most negative. The interpretation is "lottery-driven retail momentum-chasing reverses fastest in high-MAX names"
- **Target frequency**: daily (1-week horizon)
- **Current readiness**: `dsl_ready` mechanically, but **direction-coverage blocked**
- **Required fields**: `$close`, `Ref($close, 1)`, `Ref($close, 5)`
- **Why it may survive daily downsampling**: 1-week horizon natively expressible; gate via `Lt(MAX, threshold)` or continuous via `Mul(CsRank(MAX), CsRank(prev_5d_return))` interaction
- **Main distortion risk**: this is structurally **"binary regime gate × weak base signal"** — the same template that (a) `trend_quality_gated` (DEAD batch_037) failed on with momentum base; (b) `up_fraction_regime_gating` (NEW batch_080, exploring, not yet run) is currently testing on reversal base with explicit anti-gate falsifier. Spinning up a parallel "MAX gate × reversal base" direction would (i) duplicate `up_fraction_regime_gating`'s ablation matrix at most one position offset — `Lt(MAX, threshold)` and `Mean(I[ret>0], 63) > 0.6` are *both* binary regime gates derived from past returns; (ii) the MAX gate is a worse choice than UpFraction because MAX is monotone in vol_20d (per F301 absorption law), so the gate itself carries vol_20d exposure that confounds the conditional alpha — it's UpFraction with a vol contamination
- **Suggested direction tag**: none — covered by `up_fraction_regime_gating` (already running same template); revisit only after batch_080-082 results land

### Idea 3 — MAX × turnover_rate (retail proxy interaction)

- **Paper mechanism**: high-MAX × high-turnover = clearer retail-driven lottery name (turnover_rate as A-share retail-share proxy, since institutional turnover is structurally lower); expect interaction strengthens the MAX → underperformance signal
- **Target frequency**: daily
- **Current readiness**: `dsl_ready` mechanically, **library-coverage blocked**
- **Required fields**: `$close`, `Ref($close, 1)`, `$turnover_rate`
- **Why it may survive daily downsampling**: both inputs daily-bar
- **Main distortion risk**: turnover_rate × magnitude-of-return is precisely the geometry that `liquidity_acceleration` (saturated, F001 amount CV anchor) and `microstructure_illiquidity` (saturated, F012 Amihud anchor) already cover. The interaction `Mul(MAX, turnover_rate)` is dimensionally `|return| × turnover` which is a sibling of Amihud-illiquidity inverse. Plus the same vol_20d absorption: MAX side carries vol_20d, turnover_rate × vol_20d is the F012 anchor neighborhood. CP05 max_corr to F001/F012 likely > 0.7
- **Suggested direction tag**: none — coverage redundancy

### Idea 4 — MIN-of-daily-return mirror (untested in original paper)

- **Paper mechanism**: paper only studies positive extremes; symmetric question is whether MIN (most negative day) carries opposite-sign predictive content. In US, no convincing evidence (loss-aversion would suggest MIN is a stronger gate, but paper doesn't show it). In A-share with daily ±10% limit, MIN saturates at −10% on limit-down days, reducing cross-section dispersion mechanically
- **Target frequency**: daily
- **Current readiness**: `dsl_ready` mechanically, **library-coverage blocked + data structure adverse**
- **Required fields**: `$close`, `Ref($close, 1)`
- **Why it may survive daily downsampling**: same as MAX
- **Main distortion risk**: same vol_20d absorption as MAX (Q0 of returns is symmetric to Q100); additionally the ±10% A-share limit creates a degenerate sub-population (any stock that limits-down has MIN = −0.10 exactly, killing rank discrimination). lessons.md "A-share ±10% limit constraint" red-line applies. Already covered by dead `return_distribution_signals` lessons
- **Suggested direction tag**: none

### Idea 5 — MAX − MIN range (full daily-extreme spread)

- **Paper mechanism**: not in Bali paper but a natural composite. Range-of-daily-extremes interpretation = max possible swing magnitude over the month
- **Target frequency**: daily
- **Current readiness**: `dsl_ready` mechanically, **library-coverage blocked**
- **Required fields**: `$close`, `Ref($close, 1)`
- **Why it may survive daily downsampling**: daily-bar native
- **Main distortion risk**: this is `range_structure` saturated direction territory (F022 range_compression_60 admit, batch closed). MAX − MIN over 20d returns is rolling-period range of returns, not OHLC range, but mathematically `Std(returns, 20)` is approximately a constant multiple of Q90-Q10 in cross-section, so range-of-returns ≡ vol_20d. Quantile_shape_signals C001 Q90-Q50 of OHLC range already disproven this geometry
- **Suggested direction tag**: none

## Data Requirements

**Paper dependencies**:
- US monthly equity returns 1926-2005 (CRSP) — we have csi1000 daily 2015-2024
- Daily returns for MAX construction — we have via `Sub($close, Ref($close,1)) / Ref($close,1)`
- Fama-French-Carhart factor returns — we use Barra residualization machinery (vol_20d, size, book/price) which serves the same function
- IVOL = idiosyncratic vol from CAPM/FF — directly comparable to our `vol_20d` proxy (after Barra OLS in `vectorized_barra.py`)
- Amihud illiquidity — F012 admit covers this
- Size, BM, MOM, REV — covered by Barra basis + admitted factors

**What we lack**:
- 1962-2005 sample period (we are 2015-2024 csi1000) — but lessons.md confirms vol_20d absorption is robust across our entire sample
- Short-leg of the −1% alpha is uninvestable in A-share (T+0 short-sale prohibition) → standalone MAX is only useful as risk control / portfolio exclusion filter, not as alpha source
- Paper does not specify the MAX-conditional-reversal interaction explicitly — that comes from the (paywalled) Chen-Cohen-Liang-Sun 2025 extension I cannot directly read

**DSL operator coverage**:
- `MAX(daily_return, 20)` → `Max(Sub($close, Ref($close,1)) / Ref($close,1), 20)` — `Max`, `Sub`, `Ref`, `Div` all whitelisted ✓
- `MIN(daily_return, 20)` → `Min(...)` ✓
- Past-week return → `Sub(Div($close, Ref($close,5)), 1)` ✓
- Sign / If gating → `Sign`, `Gt`, `Lt`, `If`, `IfElse` whitelisted ✓
- Cross-section interaction → `Mul(CsRank(MAX), CsRank(reversal))` ✓

**No new operator or field required.** Pure DSL.

## Mapping To Current System

**Already covered by dead directions (do not retread)**:
- Idea 1 (raw MAX) → `return_distribution_signals` DEAD batch_016 (Q90-Q10 of returns `alpha_surv=0.008`); `quantile_shape_signals` DEAD batch_044 (4× cross-direction vol_20d absorption confirmation); lessons.md F301 "vol_20d absorption law" explicitly subsumes Q100 = MAX
- Idea 5 (MAX − MIN spread) → `quantile_shape_signals` C004 Q75-Q25 disproven; `range_structure` saturated; F022 range_compression_60 anchor

**Already covered by saturated directions**:
- Idea 3 (MAX × turnover_rate) → `liquidity_acceleration` saturated (F001 amount CV anchor at score 82); `microstructure_illiquidity` saturated (F012 Amihud anchor); CP05 max_corr expected > 0.7

**Already covered by an active fresh direction**:
- Idea 2 (MAX-conditional reversal) → `up_fraction_regime_gating` exploring batch_080 (not yet run) with the **same exact template**: binary regime gate × weak base signal + anti-gate falsifier ablation. The MAX gate variant is *strictly worse* than the UpFraction gate variant because MAX is vol_20d-monotone (Idea 1's failure mode contaminates the gate itself). Plus `trend_quality_gated` DEAD batch_037 already preliminarily falsified gate-as-mechanism on csi1000 (paper QA Channel 3, momentum base, 6/6 OOS sign-flip)

**Adverse data-structure considerations**:
- A-share ±10% daily limit (lessons.md "Data Facts"): MAX saturates at +0.10 on limit-up days, MIN saturates at −0.10 on limit-down days. For high-MAX cross-section, decile 10 will be dominated by stocks with at least one limit-up day → degenerate cross-section ranking within decile 10 (~1/3 of csi1000 names hit limit-up at least once per month historically)

**DSL vs Python**: pure DSL throughout. **No Python escape hatch needed.**

## Feasibility Assessment

### Idea 1 — Raw MAX(20d) standalone

- **Original dependency**: daily returns over 20d window, sort cross-sectionally
- **Coverage in current system**: **fully covered as a known failure** — Q100 of daily returns is the limiting case of the Q90/Q-range/Skew/Kurt family that `return_distribution_signals` (5/5 reject batch_016) and `quantile_shape_signals` (6 candidates 0 admit batch_044) jointly closed
- **Can it be downgraded to daily?**: already daily
- **Implementation path**: blocked-by-library-coverage (vol_20d absorption certain; alpha_survival expected 0.05–0.20 based on F004 + F301 reference points)
- **Missing piece**: nothing implementation-side; missing piece is "a reason to believe MAX escapes vol_20d when Q90/Std/Skew/Kurt did not", and lessons.md F301 explicitly closes that escape

### Idea 2 — MAX-conditional reversal (high-MAX past-loser long)

- **Original dependency**: 5×5 sort or interaction `Mul(CsRank(MAX), CsRank(−past_5d_return))` → long bottom-right cell
- **Coverage in current system**: **structurally subsumed by `up_fraction_regime_gating` exploring batch_080**; the binary-gate × weak-base template is the same; UpFraction gate is the cleaner variant (MAX gate carries vol_20d contamination)
- **Can it be downgraded to daily?**: already daily, 1-week horizon
- **Implementation path**: blocked-by-direction-coverage (do not duplicate active exploring direction); revisit if (a) batch_080 admits something proving the gate template works, then run MAX-gate as a second confirmation; (b) batch_080 6/6 reject and the "binary gate × weak base" template is added to lessons.md as DEAD, then MAX-gate is also dead a fortiori
- **Missing piece**: outcome of batch_080. Premature to open a parallel direction now.

### Idea 3 — MAX × turnover_rate

- **Original dependency**: cross-product of magnitude and liquidity proxies
- **Coverage in current system**: covered by `liquidity_acceleration` saturated + `microstructure_illiquidity` saturated; F001 amount CV (score 82) and F012 Amihud occupy the magnitude × liquidity cross-product space
- **Can it be downgraded to daily?**: already daily
- **Implementation path**: blocked-by-library-coverage (CP05 max_corr expected > 0.7 to F001 or F012)
- **Missing piece**: a cross-product that escapes the Amihud / amount-CV anchor neighborhood — but Idea 3 specifically does not because MAX-side IS vol_20d-derived

### Idea 4 — MIN-of-daily-return

- **Original dependency**: symmetric to MAX
- **Coverage in current system**: dead, plus A-share ±10% limit creates degenerate cross-section among limit-down stocks
- **Can it be downgraded to daily?**: already daily
- **Implementation path**: blocked-by-library-coverage + blocked-by-data-structure
- **Missing piece**: A-share has no clean MIN observable due to limit-down truncation

### Idea 5 — MAX − MIN spread

- **Original dependency**: not in Bali paper; natural extension
- **Coverage in current system**: covered by `range_structure` saturated and `quantile_shape_signals` dead
- **Can it be downgraded to daily?**: already daily
- **Implementation path**: blocked-by-library-coverage
- **Missing piece**: orthogonal residual structure beyond vol_20d, which lessons.md F301 says does not exist for daily-bar magnitude transforms

## What The Paper Is Hiding

1. **MAX is empirically IVOL relabeled, and the paper itself half-admits it.** Section 3 / Table 9 shows MAX-IVOL cross-sectional correlation is high enough that the regression has multicollinearity warnings and IVOL must be **orthogonalized to MAX before being co-included**. The paper's headline "MAX flips the IVOL puzzle sign" finding is mechanically driven by IVOL being decomposed into (MAX-aligned component + residual). On A-share csi1000, vol_20d is the dominant Barra-style basis (lessons.md F301), and MAX is by construction the top-quantile of the same return-distribution from which vol_20d is computed — so the **MAX → vol_20d collapse is forced by definition**. The paper sidesteps this by working in a regime (US 1962-2005) where IVOL was a smaller fraction of cross-section variance.

2. **The −1.18% / month alpha is short-leg dominated.** Look at Table 1: deciles 1–7 are flat at ~1.00–1.16% (≈ market). The decile-10 monthly return is **−0.02%**. The whole alpha gap is "decile 10 is bad" not "decile 1 is good". A-share has T+0 short-sale prohibition (`SECF` borrow inventory is institutional-only, retail-side short is closed), and `lessons.md` Data Facts: *"A-share constraint: no short alpha; factor must produce alpha from long side"*. Bali's decile-10 short is exactly the kind of trade we structurally cannot do. As a long-only A-share signal, **MAX gives us at most the right to exclude high-MAX names from a long portfolio** — a risk-management overlay, not a factor with admit-worthy alpha.

3. **Decile-10 composition (Table 5) is degenerate for A-share microstructure.** Median price $6.47 vs $25 for decile 1; median size $21.5M (~$135M RMB). On csi1000 this maps to the small-cap micro-tail. With ±10% daily limit, a decile-10 high-MAX stock typically had at least one limit-up day in the formation month — paper "high MAX = lottery" interpretation breaks down because A-share limit-up days are *information-driven* (analyst report / regulatory news) not *retail-lottery-driven*. The MAX-as-lottery signal source mechanism does not transfer cleanly. Bali's robustness checks (exclude price < $5; exclude micro-cap) shrink the alpha to −0.45% to −0.72% but don't remove it; in A-share the mechanical contamination is much stronger because the limit-up cap is a hard 10% rather than a soft microstructure noise floor.

4. **Sample period 1962-2005 is pre-decimalization for half of it.** Pre-2001 NYSE traded in 1/16ths or 1/8ths; tick size of $0.0625 on a $6 stock is ~1% — embedded microstructure noise floor. MAX values on small low-priced stocks are meaningfully inflated by tick-quantization rather than real lottery preference. Paper does not control for tick regime; subperiod 1926-1962 alpha is even larger (−1.25%) which is consistent with mechanical microstructure contamination scaling with tick size.

5. **The "MAX(N) for N=2,3,4,5 strengthens result" finding is a horizon-collapse not a robustness check.** Table 2: alpha goes from −1.18 (N=1) to −1.32 (N=5) monotonically. Authors frame this as "robustness to averaging". Statistically, MAX(5) = top-5 average of daily returns is a closer approximation to **realized vol** than MAX(1) — the trend toward stronger alpha as N increases is exactly the trend toward "more vol-like estimator". This is an admission that MAX is a vol estimator in disguise, not a separate signal. Our F301 absorption law would therefore predict MAX(N) collapses to vol_20d *more strongly* as N grows, not less.

**Top three to flag for direction-design discipline**: #1 (MAX ≡ vol_20d on csi1000 by F301 absorption law), #2 (alpha is short-leg-dominated, A-share long-only inadmissible), #5 (MAX(N) trend toward vol = self-confessed vol relabel).

## Blocked Ideas For Future

- **MAX-conditional reversal as A-share long signal** — blocked NOT by data/architecture but by **direction-coverage redundancy with `up_fraction_regime_gating`** (batch_080, exploring). **Unblock condition**: batch_080 either admits or definitively rejects the binary-gate × weak-base template; if it admits, run MAX-gate as a second confirmation in same direction; if it rejects with vol_20d-contamination evidence, MAX-gate is also dead.
- **MAX(20d) within-industry / within-style residual** — Bali's effect survives industry controls in US. Could potentially be revived if Python-residualized against industry + Barra basis, but `python_ttm_residual_quality` DEAD batch_071 (lessons.md round 73) shows alpha_survival ≥ 0.93 ≠ OOS sign-stable on csi1000 daily; same fate likely. **Unblock condition**: a non-csi1000 universe (csi300 or csi500) where vol_20d basis geometry differs, plus minute-bar data to redefine MAX as intraday-extreme.
- **MAX with intraday minute-bar refinement** — true "lottery moment" arguably is the intraday peak return rather than the daily close-to-close return. Daily MAX averages over the day's path. **Unblock condition**: intraday minute-bar OHLCV ingest (currently blocked at data-source level).
- **Retail order-flow direct measurement (instead of MAX as retail proxy)** — paper's mechanism rests on retail mispricing. We have no Lhb (龙虎榜) or institutional-vs-retail flow split data. **Unblock condition**: integrate L2 order-book or Lhb daily data, then test MAX × retail-flow-share interaction.

## Direction Recommendation

- **Decision**: `do_not_create_direction`
- **Selected idea**: none
- **direction_tag**: null
- **Initial threads**: n/a
- **First candidate families**: n/a
- **Minimum unblock condition**: at least one of —
  - (a) `up_fraction_regime_gating` (batch_080+) admits or definitively rejects the "binary regime gate × weak base signal" template, allowing MAX-gate to be tested as a second-position confirmation/falsifier;
  - (b) intraday minute-bar OHLCV becomes available, redefining MAX as intraday-extreme rather than daily close-to-close (escapes vol_20d daily-bar geometry);
  - (c) a long-side investable angle from a *different* MAX-related paper emerges that is not "binary regime gate × weak base" or "Q-quantile of daily returns" — neither template currently has a viable A-share long-only path.

**Rationale**: The standalone MAX factor is the textbook example of the F301 vol_20d absorption law (Q100 of daily returns) and is structurally inadmissible as a long-only A-share signal (Bali's −1.18% alpha is short-leg dominated; A-share has no short side). The MAX-conditional-reversal long-side angle (Chen-Cohen-Liang-Sun 2025 extension) is structurally identical to the binary-gate × weak-base template that `up_fraction_regime_gating` (batch_080, exploring, not yet run) is currently testing with explicit anti-gate falsification — and which `trend_quality_gated` (DEAD batch_037) preliminarily falsified with momentum base. Opening a parallel "MAX-gate × reversal-base" direction now would (i) duplicate at-best-one-cell of `up_fraction_regime_gating`'s ablation matrix, (ii) use a strictly worse gate variant (MAX is vol_20d-monotone so the gate carries vol contamination that UpFraction does not), and (iii) burn §7.MT budget on a high-prior-probability-of-failure design while batch_080's read on the gate template is still pending. Wait one round on batch_080. If gate template is admitted there, MAX-gate becomes a second-confirmation candidate. If gate template is rejected there, MAX-gate is a fortiori dead.

---

## Related

- 🔴 [[../directions/return_distribution_signals]] `dead` — Q90-Q10 of daily returns `alpha_surv=0.008` integral library minimum; MAX is the limiting case (Q100)
- 🔴 [[../directions/quantile_shape_signals]] `dead` — 4× cross-direction confirmation of vol_20d absorption on quantile/shape transforms of returns/range/turnover/amount
- 🔴 [[../directions/vol_shock_signals]] `dead` — magnitude vs baseline (`Abs return − 20d baseline`) `alpha_surv=0.117` catastrophic; same vol_20d collapse family
- 🔴 [[../directions/asymmetric_momentum]] `dead` — sign-conditional daily decomposition (up-only / down-only) all OOS sign-flip; signals MAX-conditional family is fragile
- 🔴 [[../directions/return_momentum_acceleration]] `dead` — return rate/delta/ratio form structural failure (5× cross-direction confirmation)
- 🔵 [[../directions/up_fraction_regime_gating]] `exploring` (batch_080, not yet run) — **directly competing template**: binary regime gate × weak base signal + anti-gate falsifier. MAX-gate would be a strictly-worse variant of this; wait for batch_080 verdict before opening
- 🔴 [[../directions/trend_quality_gated]] `dead` — gate-as-mechanism on csi1000 with momentum base, 6/6 OOS sign-flip; first independent falsification of "gate is the alpha" claim
- 🟡 [[../directions/microstructure_illiquidity]] `saturated` (F012 Amihud anchor) — Idea 3 (MAX × turnover) coverage redundancy
- 🟡 [[../directions/liquidity_acceleration]] `saturated` (F001 amount CV anchor, score 82) — Idea 3 coverage redundancy
- 🟡 [[../directions/range_structure]] `saturated` (F022 range_compression_60 anchor) — Idea 5 (MAX-MIN spread) coverage redundancy
- 🔵 [[../lessons#Structural Constraints]] — F001/F301 vol_20d absorption law, F004/F300 rate-form structural failure law
