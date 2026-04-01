# Performance Optimization: Preprocessing Vectorization + Cache Layer

**Date**: 2026-03-31
**Branch**: feature/report-redesign
**Goal**: Reduce `/mine` batch evaluation from 15–30 min to ~3–6 min per 8-candidate batch.

---

## Problem Statement

A full `/mine` iteration takes 15–30 minutes on a 10-core Mac mini. Profiling reveals three Python loops that dominate runtime:

1. **`preprocessing.py:142` — `clean_factor_values`**: `groupby().transform(python_callback)` fires a Python function once per trading date (~1250 dates per IS window). Runs for every factor in every stage.

2. **`preprocessing.py:213` — `neutralize`**: `for dt in dates.unique()` — 1250 Python iterations, each doing a DataFrame slice + numpy lstsq. Default `neutralize_mode = "market_cap"`, so this runs for every candidate in Stage 2 and Stage 3.

3. **`evaluator.py:554` — `_compute_lib_corrs_sampled`**: Two nested Python loops: `for fname in lib_factor_names (34)` × `for _, grp in merged.groupby("time") (60)` = 2040 Python iterations per candidate in Stage 2.

Additional waste: Stage 2 and Stage 3 both call `preprocess_for_ic` on the same IS-window data for the same candidate, doing `clean_factor_values` + `neutralize` twice.

---

## Solution: Plan A + B

### Plan A — Vectorize the Three Hot Paths

#### 1. `clean_factor_values` (preprocessing.py)

Replace the Python groupby callback with vectorized pandas groupby operations. The existing `len(valid) < 3` guard must be preserved: after computing cross-sectional stats, rows belonging to dates with fewer than 3 valid values are left unchanged (not clipped or z-scored).

```python
# Step 1: inf → NaN (unchanged)
result[col] = result[col].replace([np.inf, -np.inf], np.nan)

# Step 2: per-date valid count — used to mask out sparse dates
n_valid = result.groupby(level="datetime")[col].transform("count")

# Step 3: MAD winsorize — vectorized, but only applied where n_valid >= 3
med = result.groupby(level="datetime")[col].transform("median")
mad = (result[col] - med).abs().groupby(level="datetime").transform("median") * 1.4826
mad = mad.replace(0, np.nan)
lo = med - config.winsorize_n * mad
hi = med + config.winsorize_n * mad
clipped = result[col].clip(lo, hi)
result[col] = result[col].where(n_valid < 3, clipped)  # preserve sparse dates

# Step 4: zscore — vectorized, only where n_valid >= 3 (and n_valid >= 2 for std)
mean = result.groupby(level="datetime")[col].transform("mean")
std  = result.groupby(level="datetime")[col].transform("std").replace(0, np.nan)
zscored = (result[col] - mean) / std
result[col] = result[col].where(n_valid < 3, zscored)
```

For `standardize_method = "rank"` (non-default), keep existing logic as a fallback branch — it is rarely used and not a performance bottleneck.

**Expected speedup**: 3–5× on this function.

#### 2. `neutralize` (preprocessing.py)

Replace the date-loop + per-date lstsq with a batched matrix approach. The existing `len(valid) < 10` guard must be preserved: dates with fewer than 10 valid stocks are skipped and their factor values are left unchanged.

**For `market_cap` mode only** (the common case, no variable-length industry dummies):

1. Accept a pre-computed `log_mcap_wide: np.ndarray` parameter (shape `(n_dates, n_stocks)`) alongside the raw `market_cap` DataFrame. This is pre-pivoted by `_load_aux_data` (see Plan B below). `neutralize`'s signature gains an optional `log_mcap_wide` kwarg; callers that don't provide it fall back to the existing per-date pivot logic.
2. Pivot `factor` to `(n_dates × n_stocks)` numpy array.
3. Build a `(n_dates, n_stocks, 2)` design matrix `X = [ones, log_mcap_wide]`.
4. Compute batched OLS using `np.einsum`:
   - `XTX = einsum('tsi,tsj->tij', X, X)` → shape `(n_dates, 2, 2)`
   - `XTy = einsum('tsi,ts->ti', X, factor_wide)` → shape `(n_dates, 2)`
   - `beta = solve(XTX, XTy)` via `np.linalg.solve` (vectorized over dates)
   - `residuals = factor_wide - einsum('tsi,ti->ts', X, beta)`
5. Compute residuals for all dates, then restore original values for sparse dates:
   ```python
   residuals = factor_wide - einsum('tsi,ti->ts', X, beta)  # (n_dates, n_stocks)
   n_valid_per_date = (~np.isnan(factor_wide)).sum(axis=1)  # (n_dates,)
   sparse = n_valid_per_date < 10                            # (n_dates,) bool mask
   residuals[sparse] = factor_wide[sparse]                  # restore, do NOT residualize
   ```
   The mask is applied **after** computing residuals, restoring original rows. Applying it before would corrupt the batched einsum inputs.
6. Write `residuals` back into the original factor DataFrame.

**For `industry` or `both` mode** (variable X shape due to changing industry dummies per date): fall back to the existing per-date loop. This is not the default and is not a priority.

**Expected speedup**: 10–20× on `neutralize` for `market_cap` mode.

#### 3. `_compute_lib_corrs_sampled` (evaluator.py)

Replace the inner per-date Python loop with calls to the existing `daily_cross_sectional_ic` function (which is already fully vectorized). The outer loop over `lib_factor_names` is retained (34 iterations) but each iteration no longer has an inner Python date loop — it calls one vectorized function instead.

Concretely, replace:

```python
# OLD: for _, grp in merged.groupby("time"): rank + corr per date
for fname in lib_factor_names:
    ...
    for _, grp in merged.groupby("time"):  # ← eliminated
        rc = grp["value_c"].rank()
        rl = grp["value_l"].rank()
        daily_corrs.append(rc.corr(rl))
```

With:

```python
# NEW: per lib factor, call daily_cross_sectional_ic (vectorized, no date loop)
for fname in lib_factor_names:
    sub = lib_df[lib_df["factor_name"] == fname][["time", "symbol", "value"]]
    if sub.empty:
        continue
    corr_series = daily_cross_sectional_ic(cand, sub, method="spearman", min_obs=10)
    if not corr_series.empty:
        result[fname] = abs(float(corr_series.mean()))
```

This eliminates the inner 60-iteration date loop per factor. The outer loop over 34 factors remains but each call to `daily_cross_sectional_ic` is O(n_dates × n_stocks) matrix ops, not Python iteration.

**Expected speedup**: 5–10× on Stage 2 correlation check (eliminating 34 × 60 = 2040 Python iterations, replacing with 34 vectorized calls).

---

### Plan B — Preprocessing Cache Layer

#### Problem

The call chain for a single candidate in `evaluate_batch`:

```
Stage 2: _compute_factor(c, IS) → _compute_ic_from_frames() → preprocess_for_ic()  [clean + neutralize]
Stage 3: _compute_factor(c, IS) ← hits _factor_cache (raw values cached)
         → _compute_ic_from_frames() → preprocess_for_ic()  [clean + neutralize AGAIN]
```

`preprocess_for_ic` on the IS window is called twice per candidate — once in Stage 2 `_correlation_check`, once in Stage 3 `_compute_stats_and_rc`. With 8 candidates, that's 8 wasted `neutralize` executions.

Note: multi-horizon IC calls in Stage 3 (`_compute_daily_ics(vals_is, ret_h, ...)`) pass different `returns` DataFrames but the same `factor` data. Since `preprocess_for_ic` preprocesses the **factor** (not the returns), the cached cleaned factor is reusable across all horizons. The `masked_returns` varies per horizon, so only the factor side is cached.

#### Solution

Add `_preprocessed_factor_cache: Dict[str, pd.DataFrame]` to `FactorMiningEvaluator`:

- **Key**: `f"{stable_key}_{window_start}_{window_end}"` where `stable_key` is a proper SHA-256 hash of the full expression string or Python code (not truncated first-100-chars). This avoids the collision risk present in the current `_candidate_cache_key()` for Python factors that differ only past character 100.
- **Value**: The cleaned + neutralized factor `pd.DataFrame` (output of `clean_factor_values` + `neutralize` only — not the masked returns, which depend on the returns DataFrame).
- **Scope**: In-memory, valid for one `evaluate_batch()` call only. Cleared at the start of each `evaluate_batch()` call.

#### Integration

`_compute_daily_ics` is called with `(factor_values, returns, aux_data)`. The cache intercept lives here:

```python
def _compute_daily_ics(self, factor_values, returns, aux_data=None):
    if aux_data:
        cache_key = self._preproc_cache_key(factor_values, returns)
        if cache_key not in self._preprocessed_factor_cache:
            cleaned_factor, _ = self._preprocessor.preprocess_for_ic(
                factor=factor_values, returns=returns, **aux_data
            )
            self._preprocessed_factor_cache[cache_key] = cleaned_factor
        cleaned_factor = self._preprocessed_factor_cache[cache_key]
        # masked_returns still computed fresh (depends on returns, not factor)
        _, masked_returns = self._preprocessor.preprocess_for_ic(
            factor=factor_values, returns=returns, **aux_data
        )
    ...
```

Wait — this design is revised: split `preprocess_for_ic` into two sub-steps so the factor-cleaning path can be cached independently of the returns-masking path. See "Interface Change" below.

#### Interface Change: Split `preprocess_for_ic`

`preprocess_for_ic` currently returns `(cleaned_factor, masked_returns)`. To cache only the factor side:

1. Add `clean_factor(factor, aux_data) → pd.DataFrame` — runs `clean_factor_values` + `neutralize`. Cached.
2. `preprocess_for_ic` becomes: `clean_factor(...)` + `mask_returns(returns, tradable_mask)`. No behavioral change for callers.

#### Pre-Pivot market_cap in `_load_aux_data`

When `market_cap` data is loaded, immediately compute:

```python
mcap_df_wide = mcap_df.unstack("instrument").clip(lower=1.0).ffill()  # (n_dates × n_stocks)
log_mcap_wide = np.log(mcap_df_wide.values)  # numpy array
aux["log_mcap_wide"] = log_mcap_wide
aux["log_mcap_wide_columns"] = mcap_df_wide.columns.get_level_values("instrument").tolist()
```

`neutralize` receives `log_mcap_wide` via the `**aux_data` kwargs passed through `preprocess_for_ic`. The `neutralize` signature gains `log_mcap_wide: Optional[np.ndarray] = None` and `log_mcap_wide_columns: Optional[List[str]] = None`; when provided, it uses the batched einsum path; otherwise falls back to the existing per-date logic.

---

## New Tests Required

The existing test suite does not cover:
1. Vectorized `clean_factor_values` with dates having < 3 valid stocks (guard regression test).
2. Batched `neutralize` producing residuals identical to the per-date loop on the same input.
3. Cache hit returning correct cleaned factor; cache miss populating correctly.
4. Multi-horizon Stage 3 IC calls using cached factor data.
5. `_compute_lib_corrs_sampled` producing the same correlation values as the old path.

These tests go in `tests/mining/test_preprocessing_vec.py` (new file) and `tests/mining/test_evaluator.py` (new test methods).

---

## Files Changed

| File | Change |
|------|--------|
| `src/mining/preprocessing.py` | Vectorize `clean_factor_values` (with `n_valid < 3` guard); rewrite `neutralize` with batched lstsq for `market_cap` mode; add `log_mcap_wide` parameter |
| `src/mining/evaluator.py` | Add `_preprocessed_factor_cache`; split `preprocess_for_ic` into `clean_factor` + `mask_returns`; pre-pivot `log_mcap_wide` in `_load_aux_data`; replace `_compute_lib_corrs_sampled` inner loop with `daily_cross_sectional_ic` calls |
| `tests/mining/test_preprocessing_vec.py` | New: vectorized equivalence tests + edge case guards |
| `tests/mining/test_evaluator.py` | Add: cache correctness tests + multi-horizon IC cache tests |

---

## What Is NOT Changed

- Qlib `D.features()` calls remain sequential (thread safety constraint — CLAUDE.md).
- `evaluate_batch` public API unchanged.
- `MiningConfig` unchanged — no new config fields.
- `industry` and `both` neutralize modes: keep existing per-date loop (not default, not priority).
- `standardize_method = "rank"`: keep existing logic (not default).

---

## Expected Outcome

| Stage | Before | After | Speedup |
|-------|--------|-------|---------|
| `clean_factor_values` per candidate | ~8s | ~2s | ~4× |
| `neutralize` per candidate (mcap) | ~20s | ~1–2s | ~10–15× |
| Stage 2 corr check inner loop | ~5–8 min | ~30–60s | ~6–10× |
| Stage 3 IS preprocessing (cache hit) | ~25s × 8 | ~0s (factor cached) | large |
| **Full batch (8 candidates)** | **15–30 min** | **3–6 min** | **~5–8×** |

Note: Stage 3 multi-horizon returns masking is not cached (returns vary per horizon), but is cheap compared to `neutralize`.
