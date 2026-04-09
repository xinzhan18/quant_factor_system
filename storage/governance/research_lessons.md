# Research Lessons

Accumulated hard-won lessons from factor research. Read this at the start of every mining cycle.

## Forbidden Patterns

- **$vwap**: Field is zero in current data — do not use
- **Neg()**: Operator not registered — use `Mul($x, -1)` instead
- **SMA()**: Operator not registered — use EMA or Mean instead

## A-Share Constraints

- **No short-side alpha**: Factors must generate alpha from the long side (Q1). A-shares cannot be shorted.
- **No market-cap proxies**: Reject factors with abs(corr) > 0.3 to $market_cap or $circ_market_cap.

## Data Split (Inviolable)

- Train: ≤ 2023-12-31
- OOS/Validation: 2024-01-01 to 2024-12-31
- 2025+ data: NEVER touch

## Operator Gotchas

- Custom operators (TsRank, TsMax, TsMin, CsRank, CsZscore) must be registered before use — `C.kernels = 1` required
- CsRank/CsZscore always compute over full market (`D.instruments("all")`), regardless of mining universe

## Prior Signal Space Knowledge (from legacy library)

### Strong signals (Grade A/B from legacy)
- Price-volume correlation variants (pv_corr_times_vol, ret_vol_cov)
- Volume CV ratios (amount_cv_10_60, amount_cv_5_20)
- Volatility measures (hhi_vol_20, std_vol_20)
- Williams %R variant
- Turnover volatility

### Exhausted directions
- OHLCV daily at corr<0.7: near-exhausted
- Alpha101 formulae: mostly Grade D, avoid
- Simple price momentum: crowded

### Promising unexplored
- Candlestick microstructure × liquidity interactions
- Higher-order cross-field covariance (Cov of fundamentals × technicals showed perfect monotonicity in legacy)
- Timing signals (IdxMax/IdxMin based)

## Batch 001 Soft Lessons (2026-04-06)

- **NM_001**: TsAutoCorr($amount, 20) confirmed as novel signal class
- **FP_001 (candidate)**: Cov(turnover_rate, pe_ratio, *) appears to be Barra value x turnover proxy
- **ST_001**: Shadow ratio x CsRank(turnover_rate) produces style_r2>0.38, crowding=HIGH

## Batch 040 Soft Lessons (2026-04-07)

- **FP_040_L002_dead**: All Cov variants (amt,tur; amt,pb; tur,range; tur,ps_ratio) produce positive Barra residuals. L002 has 0 admits across 4 batches. L002 is dead.
- **NM_040_amount_rel_tur**: Amount x rel-tur conditioning: alpha_surv=0.513(session best), Barra_res=-0.343(session cleanest). Session's best signal.

## Batch 039 Soft Lessons (2026-04-07)

- **NM_039_rel_tur**: Rel-tur conditioning (Div(CsRank(tur),CsRank(vol))) → alpha_surv=0.496(session best), Barra_res=-0.347(session cleanest). Volume competition encoding is new mechanism.
- **FP_039_short_shadow**: Shadow×Amihud at 10d and 5d fails (ICIR collapse, mono≈0). 20d is confirmed minimum viable window.

## Batch 038 Soft Lessons (2026-04-07)

- **NM_038_scale**: 10d pv_corr×CsRank(tur) > 20d > 40d (ICIR: -0.558 > -0.530 > -0.446). Divergence is short-horizon — longer windows capture regime not transients.
- **NM_038_amount**: $amount (price×volume) produces orthogonal signal to $volume in multiplicative conditioning. Smart money proxy confirmed.
- **NM_038_shadow_incr**: Shadow adds ~20% incremental IC over pure Amihud. Confirmed non-redundant.
- **FP_038_40d_shadow**: 40d shadow×Amihud weaker than 20d on all metrics. Sweet spot 10-20d.
- **FP_038_40d_pv**: 40d pv_corr×CsRank upper bound confirmed. Do not expand beyond 30d.

## Batch 003 Soft Lessons (2026-04-06)

- **ST-L001-003**: Shadow signal collapses (alpha_surv<0.10) when paired with vol or turnover. Only survives with Amihud (amount/volume) as conditioning dimension. Confirmed across 3 batches.
- **NM-L003-003**: TsAutoCorr on volume/turnover reproduces F001 at corr=0.45-0.62. Mechanism is field-specific to amount, NOT general autocorr. vol/tur variants are near-duplicates.
- **FP-L004-003**: Pv_corr change rate (Sub(Corr,Ref(Corr))) is a reversal signal (str_1m dominant=0.338), NOT a divergence change mechanism. Do not probe further.
- **FP-L002-003**: Cov(amt,tur) Barra_residual_ICIR=0.178 — 7.8× worse than admitted. Intra-liquidity covariance is absorbed by turnover_20d. Barra residual confirms style contamination.

## Batch 041 Soft Lessons (2026-04-07)

- **FP-L004-pure-vol-competition**: Pure vol-competition (Div(CsRank(amount),CsRank(volume)) without pv_corr) fails holdout with sign flip (mono_val=-0.9 → mono_ho=+0.5). The pv_corr component is essential — volume competition alone is insufficient mechanism.
- **NM-L004-amount-vol-competition**: Amount×vol-competition (amount_rank/vol_rank) is a new mechanism distinct from F010's tur_rank/vol_rank. C002 admits: Barra_res=-0.270, Mono=-0.9 on both val and holdout.
- **ST-duplicate-expression**: C001 identical to F010, C004 identical to F002. Expression dedup check missing in probe/manifest pipeline — wastes budget on duplicates.

## Batch 042 Soft Lessons (2026-04-07)

- **FP-L001-shadow-x-pv-corr**: Shadow x pv_corr (alpha_surv=0.138) absorbed by turnover_20d style. pv_corr does not provide orthogonal conditioning for shadow — only Amihud works.
- **FP-L001-shadow-x-vol-competition**: Shadow x vol-competition mono sign flip, dominant_style=log_circ_cap (size proxy). Not a shadow mechanism — vol-competition is a size signal.

## Batch 043 Soft Lessons (2026-04-07)

- **FP-L004-10d-amount-redundant**: 10d amount x rel-tur (C001): max_lib_corr=0.8994 vs F004 (10d vol). 10d amount x vol-competition (C003): max_lib_corr=0.8475. 10d is the ceiling for amount x vol-competition — too slow, collapses into existing 10d vol pathway. Do not probe 10d amount x vol-competition/rel-tur.
- **FP-L004-10d-duplicate-F011**: C002 is expression duplicate of F011 (both 20d amount vol-competition). 10d is not a shorter viable window of F011 — it's a different mechanism space (vol pathway).
- **NM-L004-5d-scale-floor**: 5d amount x rel-tur (C004) is the scale floor: Barra_res=-0.019 (cleanest in batch), max_lib_corr=0.517 vs F009. 3d and 7d are the next probes to find genuine scale floor vs 10d ceiling.

## Batch 044 Soft Lessons (2026-04-07)

- **FP-L001-5d-shadow-collapse**: 5d shadow x Amihud holdout collapse (ls_tstat_ho=-0.17, ICIR_ho=-0.144, >50% decay). Shadow requires ≥10d averaging to denoise microstructure. 5d is too fast for shadow mechanism. Confirmed: shadow is a slow signal.
- **NM-L004-7d-scale-midpoint**: 7d amount x rel-tur (F012) admits: ICIR_ho=-0.402, mono_ho=-0.9, Barra_res=-0.024. Scale map complete: 3d(reserve) / 5d(reserve) / 7d(admit) / 10d(reject-redundant) / 20d(admit-F011).

## Batch 045 Soft Lessons (2026-04-07)

- **FP-L004-hhi-concentration-fail**: HHI($amount/$volume) × CsRank($turnover) is a style trap. All 3 variants (5d/20d HHI_amount, 20d HHI_volume) produce mono_ho=0.0 to -0.1 (severe sign flip). HHI measures concentration correlated with turnover regime — cannot be orthogonalized by multiplicative conditioning. Do not probe HHI-based signals.

## Batch 046 Soft Lessons (2026-04-07)

- **FP-L004-ts-entropy-turnover-trap**: TsEntropy($amount/$volume, 10/20d) × CsRank($turnover_rate) is a turnover regime trap. mono_ho=-0.1 (near-zero) across all windows. TsEntropy captures distribution shape correlated with turnover regime — same pattern as HHI × tur (batch_045). Do not probe TsEntropy × tur in any form. The conditioning paradigm requires X to be orthogonal to turnover_20d. BP/EP rank is the next candidate.

## Batch 047 Soft Lessons (2026-04-07)

- **NM-L004-pe-ps-condition-breaks-trap**: PE/PS rank conditioning BREAKS the turnover regime trap. C001/C002 show dominant_style=str_1m/log_circ_cap (NOT turnover_20d). Turnover_20d exposure only 0.218 vs 0.448 in HHI/TsEntropy. PE/PS are orthogonal to turnover — breakthrough mechanism. 20d is minimum viable window. Reserved for holdout confirmation.
- **FP-L004-additive-pathology**: Add(Corr($close,$amount,20),Div(CsRank($turnover_rate),CsRank($amount))) produces expanding_window_pass=FALSE, kurtosis=133. Additive paradigm creates pathological distributions. Do not probe Add() conditioning.
- **FP-L004-10d-too-fast**: 10d pv_corr × PE conditioning shows hidden sign flip (mono_ho=-0.7 stable but all quintiles positive). 20d is minimum viable window for fundamental conditioning.

## Batch 048 Soft Lessons (2026-04-07)

- **FP-L001-body-ratio-weak**: Candlestick body ratio (close-open)/(high-low) × tur_rank/amount_rank produces severe holdout collapse (decay_ratio=0.30-0.45). Body ratio is too noisy as primary signal. Cov(body, tur) co-movement absorbed by size style (log_circ_cap=0.319). PE conditioning breakthrough does NOT transfer to body patterns. Body ratio patterns are dead for L001.

## Batch 050 Soft Lessons (2026-04-07)

- **NM-L001-timing-range**: IdxMax-IdxMin range (volume/turnover peak-trough distance) × PE conditioning: mono_ho=-1.0, decay_ratio>1.8, alpha_surv=0.44-0.45. Most promising L001 signal since F002 shadow×Amihud (alpha_surv=0.377). Requires holdout confirmation.
- **FP-L001-tsautocorr-volume-duplicate**: TsAutoCorr($volume,20) × PE/PS conditioning reproduces F001 at max_lib_corr=0.89/0.86. Volume autocorrelation is the same mechanism as amount autocorrelation. Do not probe TsAutoCorr on volume-derived fields at 20d.

## Batch 051 Soft Lessons (2026-04-07)

- **NM-L001-timing-range-window-optimization**: 10d timing_range × PE: alpha_surv=0.879, 2× better than 20d timing_range (0.44-0.45). Window parameter is decisive — shortest viable window = optimal. For timing_range: shorter windows preserve more alpha before str_1m absorption.
- **NM-L001-timing-range-conditioning-reversal**: 20d timing_range × Amihud FAILS (near-flat ranking, alpha_surv=0.17-0.20). Amihud conditioning does NOT work for timing_range — opposite of shadow where Amihud is essential. Fundamental conditioning (PE/PB) > cost-of-trading (Amihud) for timing_range.

## Batch 052 Soft Lessons (2026-04-07)

- **ADMIT-L001-F013**: F013 (5d timing_range × PE) admitted as first L001 factor in 9 rounds. alpha_surv=1.204, mono_ho=-0.9, Barra_res=-0.014, dominant_style=turnover_20d=0.152. L001 now has 2 productive families: F002 (shadow×Amihud) and F013 (5d timing_range×PE).
- **FP-L001-timing-range-pb-conditioning**: 10d timing_range × PB conditioning: mono_ho=+0.1 (sign flip). PB conditioning does NOT work for timing_range — only PE/PS works.
- **NM-L001-timing-range-window-hierarchy**: Timing_range window hierarchy: 5d (1.204) > 7d (1.049) > 10d (0.879) > 20d (0.438). Shorter = better for timing_range. 5d also avoids str_1m trap (turnover_20d=0.15 dominant instead).

## Batch 053 Soft Lessons (2026-04-07)

- **FP-L001-timing-range-3d-collapse**: 3d timing_range × PE: decay_ratio=0.876 (<1), ls_tstat_ho=-1.09, quintuple spread=0.0006. mono_ho=-1.0 is DECEPTIVE — all quintiles positive and compressed. 3d is TOO FAST. 5d is confirmed as the floor for timing_range × PE.
- **FP-L001-timing-range-ps-fails**: 5d timing_range × PS conditioning: mono_ho=+0.1 (SIGN FLIP), quintuple spread FLAT. PS conditioning does NOT work for timing_range. PE is UNIQUELY essential. Do not probe PS conditioning with timing_range.
- **NM-L001-timing-range-floor-confirmed**: 5d timing_range × PE confirmed as the floor. Window map complete: 3d(FAIL) / 5d(ADMIT-F013) / 7d(REJECT-weak) / 10d(REJECT-redundant) / 20d(REJECT-style). PE is the only viable conditioning partner for timing_range.

## Batch 054 Soft Lessons (2026-04-07)

- **FP-L001-pe-ps-ratio-dilutes**: 5d timing_range × PE/PS ratio: decay=0.75 (<1), alpha_surv=0.75, ls_tstat_ho=-1.14. PE alone (F013, decay=1.207) is clearly superior. PE/PS ratio DILUTES rather than enhances. Do not probe PE/PS ratio for timing_range.
- **FP-L001-blend-expression-level-fails**: Shadow×timing blend (F002×F013) at expression level: C002 (mul): mono_ho=0.0, kurtosis=2700. C003 (add): mono_ho=0.0, decay=0.59. Both multiplicative and additive expression-level blending collapse ranking. Orthogonal families must be combined at portfolio level (post-rank), not expression level.
- **NM-L001-orthogonal-blend-portfolio-level**: Orthogonal families (F002 shadow×Amihud, F013 timing_range×PE) cannot be blended at expression level. Next: test post-rank z-score blend or rank-space multiplication.

## Batch 055 Soft Lessons (2026-04-07)

- **NM-L001-timing-range-field-generalization**: Timing_range mechanism generalizes to $amount field. F014 admitted: max_lib_corr=0.073, Barra_res=-0.014, alpha_surv=1.063, mono_ho=-0.9, decay=1.17. $amount (price×volume monetary) equally valid as $volume. Mechanism is timing volatility broadly, not field-specific.
- **FP-L001-timing-range-turnover-weaker**: Turnover_rate timing_range: ICIR_val=-0.147 (weak), half_life=9.41d (slow vs amount's 5.0d), mono_ho=-0.8 (borderline). Turnover variant is weaker than amount. Reserve — admit only if amount variant stable across further holdouts.

## Batch 056 Soft Lessons (2026-04-07)

- **FP-L001-timing-range-close-style-trap**: Price-only timing_range ($close): alpha_surv=0.214 (POOR), str_1m=0.413 (HIGH style trap). Barra_res=-0.004 (clean) but style_r2=0.149 (elevated). Volume ($volume) and amount ($amount) variants produce str_1m=0.15, alpha_surv>1.0. Volume dimension is ESSENTIAL for clean timing signal — price-only is primarily a short-term reversal signal.

## Batch 057 Soft Lessons (2026-04-07)

- **FP-L001-idxmin-trough-not-independent**: IdxMin (trough-only) × any conditioning: WEAKENS on holdout (decay<1). C002: mono_ho=0.0 (FATAL), alpha_surv=0.005 (CATASTROPHIC). C001: decay=0.602, alpha_surv=0.333. Peak-trough DISTANCE (IdxMax-IdxMin) is essential — trough position alone is NOT a signal. L001 timing_range family SATURATED.

## Batch 058 Soft Lessons (2026-04-07)

- **FP-L004-ep-conditioning-style-trap**: EP conditioning (Div(1,$pe_ratio)) on pv_corr: alpha_surv=0.092 (POOR), str_1m=0.318 (style trap), style_r2=0.161. EP is too similar to PE — fundamental conditioning breaks turnover trap but introduces style trap. Do not probe EP alone as conditioner.

## Batch 089 Soft Lessons (2026-04-10)

- **FP-L012-autocorr-conditioning-all-fail**: PE conditioning AND soft-decorrelation on TsAutoCorr($amount,N) ALL produce style traps. 20d×PE: ep_ratio dominant (alpha_surv=9%). 20d soft-decorr: barra_res=+0.171 (WRONG direction), near-duplicate F001 (0.993). 10d×PE: vol_20d dominant (alpha_surv=12%). The pv_corr conditioning paradigm does NOT transfer to TsAutoCorr. TsAutoCorr has different Barra structure — conditioning reorganizes which style dominates rather than revealing clean alpha. L012 at DSL level is exhausted.

- **NM-L013-range-amount-novel-mechanism**: Corr(Div(Sub($high,$low),$close),$amount,10) confirmed as novel mechanism. max_lib=0.065 (most novel in v2 system), alpha_surv=0.734, barra_res=-0.201, style_r2=0.042. Range-amount captures institutional aggression (volatile days co-occurring with high monetary flow). Orthogonal to ALL pv_corr factors. 10d window is too slow (ICIR_ho=-0.144, decay=0.715). Next: 5d, 7d windows.

- **FP-L013-pe-conditioning-kills-range-amount**: PE conditioning on range-amount 10d: decay=0.312, mono_ho=-0.30 (catastrophic). PE conditioning is INCOMPATIBLE with range-amount mechanism. It adds ep_ratio style that dominates and causes holdout collapse. Do NOT probe PE conditioning with range-amount signals. Non-PE conditioning (e.g. CsRank($amount)) is the only viable path.

## Batch 090 Soft Lessons (2026-04-10)

- **NM-L013-amount-rank-amplifies-ic**: CsRank($amount) conditioning on range-amount 5d: ICIR_val jumps from -0.196 to -0.668 (3.4x!). But introduces book_to_price style (style_r2=0.14-0.18, alpha_surv=0.43). The amplification IS real (barra_res_icir=-0.331, mono_ho=-1.0 PERFECT). Need per-industry amount normalization to preserve amplification without book_to_price.

- **NM-L013-alpha-surv-gt1-5d-raw**: C004 (5d raw range-amount): alpha_surv=1.024, decay=1.066. Factor AMPLIFIED by Barra removal and STRENGTHENS on holdout. This means the raw IC understates true quality — vol_20d Barra has negative IC and its removal improves the signal. The 5d raw range-amount is a clean mechanism but needs IC amplification.

- **FP-L013-raw-window-plateau**: Raw Corr(range/close, amount, N) for N in [5,7,10]: ICIR_ho plateau at ~[-0.14,-0.16]. Window shortening alone cannot overcome this. Do not probe more raw window variants. Structural change (industry-normalized conditioning) required.

## Batch 091 Soft Lessons (2026-04-10)

- **FP-L013-turnover-rank-kills-mono**: CsRank($turnover_rate) conditioning on range-amount: mono_ho≈0 (quintile collapse) despite ICIR_ho=-0.37. Turnover_20d Barra style is fast-moving and flips at val/holdout boundary, destroying quintile structure. CsRank($amount) is better because book_to_price is slow-moving and preserves mono_ho=-1.0. Do NOT use CsRank($turnover_rate) or CsRank($volume) for range-amount conditioning.

- **FP-L013-range-turnover-corr-degenerate**: Corr(Div(Sub($high,$low),$close),$turnover_rate,5) = ICIRval=0. The range vs turnover_rate correlation is degenerate — no signal. Range-AMOUNT is the working mechanism, not range-turnover. The dollar flow ($amount) is essential, not the share velocity ($turnover_rate).

## Batch 092 Soft Lessons (2026-04-10)

- **NM-L013-rel60d-decay-gt1**: CsRank(Div($amount, Mean($amount, 60))) conditioning on 5d/7d range-amount: decay=1.13-1.17 (signal STRENGTHENS on holdout — unprecedented across all L013 batches). ls_t_ho=-3.1 to -3.6 (highly significant). mono_ho=-0.7 to -0.9 (preserved). The 60d relative normalization creates a stable "abnormal activity" signal size-neutral enough to persist into holdout. Block: alpha_surv=0.44-0.46 (below 0.5), str_1m style 14-17% of variance. This is the best found conditioning for range-amount — next: probe 30d/40d windows to push alpha_surv above 0.5.

- **FP-L013-rel20d-mono-collapse**: CsRank(Div($amount, Mean($amount, 20))) conditioning: mono_ho=-0.1 (quintile collapse) despite alpha_surv=0.680 (excellent!). The 20d relative amount is too momentum-like (str_1m) and reverses in 2024 holdout. For relative amount conditioning, lookback must be ≥40d to avoid str_1m instability. Do NOT probe shorter lookbacks (<30d).

## Batch 093 Soft Lessons (2026-04-10)

- **NM-L013-alpha-surv-gt05-milestone**: CsRank(Div($amount, Mean($amount, 30-40d))) conditioning achieves alpha_surv>0.5 for the first time in conditioned range-amount. C001 (5d×40d): 0.533, C002 (5d×30d): 0.589 (record high). All signals decay>1 (C002 decay=1.219, L013 record). mono_ho=-0.7 preserved. The 30-40d window is the alpha_surv sweet spot for relative amount conditioning.

- **FP-L013-str1m-nonmonotonic-intermediate-windows**: str_1m exposure across normalization windows is NON-MONOTONIC: 20d≈8% → 30d=37% → 40d=38-42% → 60d=14-17%. Intermediate windows (30-40d) produce 2-3x HIGHER str_1m than both shorter (20d) and longer (60d) windows. The 30d-40d regime captures cross-sectional momentum that loads heavily on str_1m. At 20d the signal IS momentum (reverting). At 60d the long baseline dilutes it. At 30-40d it's a stable (non-reversing) str_1m overlay that blocks acceptable risk bucket. Next: probe 50d window or Python residualization.



## Batch 094 Soft Lessons (2026-04-10)

- **NM-L013-str1m-soft-decorr-works**: DSL-level str_1m soft-decorrelation via Sub(CsRank(Div($amount,Mean($amount,50))), Mul(CsRank(Div($close,Ref($close,22))),0.3)) achieves risk=acceptable (alpha_surv=0.688) on range-amount signal. The 0.3 coefficient subtracts 30% of 1-month return rank from the relative-amount conditioner, neutralizing the intermediate-window momentum overlay. FIRST L013 ADMIT: F017. Approach generalizes to any factor where 30-50d normalization window produces str_1m=20-42% style load.

- **NM-L013-50d-transition-boundary**: 50d normalization window is the transition zone between intermediate str_1m regime (30-40d = 38-42%) and longer baseline (60d = 14-17%). At 50d, alpha_surv=0.500 (exact borderline/acceptable boundary), dom_style=None (str_1m dropped significantly but risk bucket still borderline). The raw 50d conditioning is at the critical boundary — DSL decorrelation pushes it to acceptable. Non-monotonic str_1m pattern boundary is: 20d=8% → 30-40d=37-42% → 50d=~20% → 60d=14-17%.

- **ST-L013-internal-norm-alpha-surv-universal**: Internal normalization family (Corr(range/close, amount/Mean(amount,N), 5)) consistently produces alpha_surv≈1.0 across ALL tested windows (20d: 1.001, 40d: 0.992, 50d: 0.983) but ICIRho is consistently weak (-0.14 to -0.16). This is a stable pattern: exceptional Barra residual profile but insufficient raw signal strength. Do not pursue internal normalization further as standalone signal — may serve as composite component.
