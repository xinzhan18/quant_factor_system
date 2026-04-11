# Golden Fixtures for P1 Vectorized Compute

This directory holds **ground-truth reference values** that the P1 vectorized
compute modules (`src/research/compute/vectorized_*.py`) must match within
`1e-6` tolerance.

## How it works

`generate_golden.py` is a one-shot generator that:

1. Builds a deterministic synthetic panel (seeded `np.random.default_rng`)
   with 600 trading days × 200 symbols of factor values, forward returns,
   library signals, tradable mask, amount / market cap data, and a 7-column
   Barra-style matrix.
2. Runs the **old / legacy** pure-function math modules
   (`src/core/factor_stats.py`, `src/research/stats/*.py`,
   `src/research/redundancy/pairwise.py`, `src/research/feasibility/*.py`,
   `src/research/risk/exposures.py`) on that panel.
3. Persists every input as parquet under `inputs/` and every scalar /
   series / DataFrame output under `outputs/`.

The generated files are committed to git and never edited by hand. P1 tests
load both the inputs and the golden outputs and assert numerical equivalence.

## Layout

```
_fixtures/
  generate_golden.py       # one-shot reference generator
  README.md                # this file
  inputs/                  # synthetic panel (.parquet)
    factor_values.parquet          [time, symbol, value] flat
    forward_returns.parquet        [time, symbol, value] flat
    candidate_signal.parquet       MultiIndex (datetime, instrument)
    library_{F001,F002,F003}.parquet  library factors for redundancy
    tradable_mask.parquet          MultiIndex bool
    amount_data.parquet            MultiIndex float
    market_cap_data.parquet        MultiIndex float
    style_matrix.parquet           MultiIndex × 7 style columns
    bench_returns.parquet          DatetimeIndex
  outputs/                 # ground truth from OLD code
    golden.yaml                       # all scalar outputs
    ic_series_train.parquet           # daily IC series, train period
    ic_series_validation.parquet      # daily IC series, validation period
    long_short_daily_validation.parquet  # daily LS return series
```

## Covered modules

`golden.yaml` contains:

- `effect_strength` — train/validation IC mean / std / IR / win_rate,
  quintile returns, monotonicity, long-short mean
- `stability.split_stability` — 4-way split IC means, sign_consistency,
  dispersion, bucket
- `stability.support_windows` — per-window IC mean + sign_consistent flag
- `redundancy` — max_lib_corr, nearest_factor_id, per-library correlations
- `feasibility` — turnover, liquidity_coverage, tail / small-cap
  concentration, half-life, holding period, rebalance stress
- `barra` — per-style exposures, style_r², residual IC / ICIR,
  alpha_survival_ratio, dominant style, crowding risk

## Regenerating

```
PYTHONPATH=src python3 tests/research/compute/_fixtures/generate_golden.py
```

The generator is deterministic and idempotent — running it twice in a row
produces byte-identical outputs (no timestamps, no random elements beyond
the seeded RNG). If you change `SEED`, `N_DAYS`, `N_SYMBOLS`, or
`START_DATE`, all golden files must be regenerated and re-committed.

## Why synthetic data and not real data

- **No DB / Qlib / network dependency** — the fixture runs anywhere
- **Deterministic across machines** — seeded numpy RNG is portable
- **Small and fast** — 600 × 200 = 120K rows finishes in ~2 seconds
- **Covers edge cases deliberately**:
  - IC is non-zero (signal embedded in returns)
  - Quintile returns are monotonic (tests monotonicity correctly)
  - Library factors cover three correlation tiers (1.0 / ~0.56 / ~0.0)
  - Styles are independent Gaussians → well-conditioned per-date OLS
  - Train/val split is 60/40 → split_stability has four ≥60d chunks

## Known quirks

The old `src/research/risk/exposures.py` path emits spurious BLAS
strided-matmul FP flag warnings on some numpy builds even when the input X
is well-conditioned (`cond(X)≈3.5`) and the output `X @ beta` is bounded
(`|X@beta| < 0.3`). These warnings are suppressed in the generator via
`warnings.filterwarnings("ignore", ..., message=".*matmul.*")`. The
resulting numeric outputs are correct and reproducible.

The new P1.2f `vectorized_barra.py` will use `np.linalg.pinv + np.einsum`
on a 3D tensor per refactor_plan §11 and must match these golden values
exactly.
