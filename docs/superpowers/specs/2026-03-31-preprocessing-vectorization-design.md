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

Replace the Python groupby callback with a chain of vectorized pandas groupby operations:

```python
# Step 1: inf → NaN (unchanged)
result[col] = result[col].replace([np.inf, -np.inf], np.nan)

# Step 2: MAD winsorize — fully vectorized
med = result.groupby(level="datetime")[col].transform("median")
mad = (result[col] - med).abs().groupby(level="datetime").transform("median") * 1.4826
mad = mad.replace(0, np.nan)
lo = med - config.winsorize_n * mad
hi = med + config.winsorize_n * mad
result[col] = result[col].clip(lo, hi)

# Step 3: zscore — fully vectorized
mean = result.groupby(level="datetime")[col].transform("mean")
std  = result.groupby(level="datetime")[col].transform("std").replace(0, np.nan)
result[col] = (result[col] - mean) / std
```

For `standardize_method = "rank"` (non-default), keep existing logic as a fallback branch.

**Expected speedup**: 3–5× on this function.

#### 2. `neutralize` (preprocessing.py)

Replace the date-loop + per-date lstsq with a batched matrix approach:

1. Pivot `factor` and `log_mcap` to `(n_dates × n_stocks)` numpy arrays once.
2. For each date row: `X = [1, log_mcap[t]]`, `y = factor[t]` — but instead of a Python loop, use numpy broadcasting to build a `(n_dates, n_stocks, 2)` design matrix and solve via batched pseudo-inverse.
3. For the market_cap-only case (no industry dummies, fixed X shape), the OLS solution is analytically `beta = (X^T X)^{-1} X^T y` and can be computed for all dates at once using `np.einsum`.
4. When industry dummies are present (variable X shape per date due to NaN instruments), fall back to a `groupby(...).apply(...)` approach — this is less common and already slow today.

**Pre-pivot in `_load_aux_data`**: Store `log_mcap_wide` (pre-pivoted, pre-log-transformed `(date × instrument)` numpy array) alongside raw market_cap in `_aux_cache`. `neutralize` reads the pre-computed matrix directly, eliminating per-call reindex overhead.

**Expected speedup**: 10–20× on `neutralize` for the `market_cap` mode.

#### 3. `_compute_lib_corrs_sampled` (evaluator.py)

Replace the 2-level Python loop with a fully vectorized matrix operation:

1. Fetch the 3-month library data from TimescaleDB (unchanged — already a single batched query).
2. Pivot `lib_df` to a `(n_dates × n_stocks × n_lib_factors)` array using `pivot_table`.
3. Rank cross-sectionally (axis=1) for both candidate and all library factors simultaneously.
4. Compute Pearson correlation of ranks (= Spearman IC) for all `(date, lib_factor)` pairs using the same vectorized matrix approach already used in `daily_cross_sectional_ic`.
5. `nanmean` over dates → `(n_lib_factors,)` result vector.

This reuses the existing `daily_cross_sectional_ic` logic by calling it in a loop over lib factors, OR by a single matrix broadcast. The loop-over-lib-factors approach is simpler and already 10× faster than the current groupby loop (eliminating the inner date loop per factor).

**Expected speedup**: 5–10× on Stage 2 correlation check.

---

### Plan B — Preprocessing Cache Layer

#### Problem

The call chain for a single candidate in `evaluate_batch`:

```
Stage 2: _compute_factor(c, IS) → _compute_ic_from_frames() → preprocess_for_ic()  [clean + neutralize]
Stage 3: _compute_factor(c, IS) ← hits _factor_cache (raw values cached)
         → _compute_ic_from_frames() → preprocess_for_ic()  [clean + neutralize AGAIN]
```

`preprocess_for_ic` on the IS window is called twice per candidate. With 8 candidates, that's 8 wasted `neutralize` executions.

#### Solution

Add `_preprocessed_cache: Dict[str, Tuple[pd.DataFrame, pd.DataFrame]]` to `FactorMiningEvaluator`:

- **Key**: `f"{cache_key}_{window_start}_{window_end}"` where `cache_key` is the expression or code hash.
- **Value**: `(cleaned_factor, masked_returns)` — the output of `preprocess_for_ic`.
- **Scope**: In-memory, valid for one `evaluate_batch()` call only. Cleared between batches.

#### Integration Points

- `_compute_daily_ics`: Before calling `_preprocessor.preprocess_for_ic`, check `_preprocessed_cache`. On miss, call preprocess and store result. On hit, use cached values directly.
- OOS window data cached separately (different key suffix).
- Cache is never serialized to disk (avoids stale data issues across batches).

#### Pre-Pivot market_cap

In `_load_aux_data`, when `market_cap` data is loaded, immediately compute:
```python
log_mcap_wide = np.log(mcap_df.unstack("instrument").clip(lower=1.0).fillna(method="ffill"))
aux["log_mcap_wide"] = log_mcap_wide  # pre-pivoted numpy array
```
`neutralize` reads `log_mcap_wide` directly instead of slicing and reindexing per date.

---

## Files Changed

| File | Change |
|------|--------|
| `src/mining/preprocessing.py` | Vectorize `clean_factor_values`; rewrite `neutralize` with batched lstsq |
| `src/mining/evaluator.py` | Add `_preprocessed_cache`; hook into `_compute_daily_ics`; pre-pivot mcap in `_load_aux_data`; vectorize `_compute_lib_corrs_sampled` |
| `src/core/factor_stats.py` | No changes required — `daily_cross_sectional_ic` already vectorized |

---

## What Is NOT Changed

- Qlib `D.features()` calls remain sequential (thread safety constraint documented in CLAUDE.md).
- `evaluate_batch` public API unchanged.
- `MiningConfig` unchanged — no new config fields.
- Test suite unchanged — all existing tests cover the modified code paths.

---

## Expected Outcome

| Stage | Before | After | Speedup |
|-------|--------|-------|---------|
| `clean_factor_values` per candidate | ~8s | ~2s | 4× |
| `neutralize` per candidate (mcap) | ~20s | ~1–2s | 10–15× |
| Stage 2 corr check (8 candidates) | ~5–8 min | ~30–60s | 6–10× |
| Stage 3 preprocessing (8 candidates) | ~3–5 min | ~0s (cache hit) | ∞ |
| **Full batch (8 candidates)** | **15–30 min** | **3–6 min** | **5–8×** |

---

## Out of Scope

- Parallelizing Qlib `D.features()` calls (unsafe).
- Shortening the train window (quality tradeoff, not needed if vectorization is sufficient).
- Disk-based caching of preprocessed values (memory cache is sufficient for one batch).
