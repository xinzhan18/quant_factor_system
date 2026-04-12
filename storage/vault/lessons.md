---
version: 1
last_consolidated_at: 2026-04-12T00:00:00Z
source: seeded from storage/governance/research_lessons.md during P0 refactor
---

# Research Lessons

System-level hard-won facts. Read at the start of every mining cycle.
Rewritten periodically by Phase 5 CONSOLIDATION. Do NOT append per-batch lessons here — those live in `directions/{direction}.md`.

## Data Facts

- **Data split (inviolable)**:
  - Train: `[2015-01-01, 2021-12-31]`
  - Validation: `[2022-01-01, 2023-12-31]`
  - Holdout: `[2024-01-01, 2024-12-31]` (NEVER visible to Phase 2 / Phase 3; only `research holdout-review` sees it)
  - 2025+: never touch
- **Primary universe**: `csi1000` for all CP01-CP06 judging; `csi300` / `csi500` / `all` are reference-only
- **`$vwap` field is zero** in current data source — forbidden in precheck
- **`$amount` HAS data** (confirmed) — usable
- **`index_constituents` table**: 2.7M rows, contains `csi300` / `csi500` / `csi1000` daily membership
- **A-share constraint**: No short-side alpha. Factors must generate alpha from the long side.
- **Market-cap proxy guardrail**: Reject factors with `abs(corr)` > 0.3 to `$market_cap` or `$circ_market_cap`.

## Operator Registry

- **Whitelist only**: DSL operators / fields must appear in `src/research/execute/precheck.py` whitelist (single source of truth)
- **Available fields**: `$open, $high, $low, $close, $volume, $amount, $pe_ratio, $pb_ratio, $ps_ratio, $market_cap, $circ_market_cap, $turnover_rate`
- **Custom operators registered** (require `C.kernels = 1`): `TsRank`, `TsMax`, `TsMin`, `TsAutoCorr`, `TsDecay`, `TsMomentum`, `RealizedVol`, `CsRank`, `CsZscore`, `CsDemean`, `AmihudIlliq`, `HHI`, `SignedPower`, `Tanh`, `Exp`, `Sigmoid`
- **Unavailable / forbidden operators**: `Neg` (use `Mul($x, -1)`), `SMA` (use `EMA` or `Mean`)
- **Cross-sectional operators** (`CsRank`, `CsZscore`, `CsDemean`) always compute over `D.instruments("all")` regardless of mining universe

## Path Selection (DSL vs Python)

- **Default: DSL**. Express the factor in Qlib expression language unless DSL cannot express the idea.
- **Python escape hatch (R8)** when:
  - The idea needs a non-trivial loop that cannot be vectorized in DSL (rare)
  - The idea needs cross-sectional operations DSL cannot express
  - The idea is an explicit reproduction of a published Python reference implementation
- **Python factor contract**:
  - Signature: `def compute(df: pd.DataFrame) -> pd.Series` where df has MultiIndex (time, symbol)
  - Must declare `REQUIRED_FIELDS: list[str]` and `VECTORIZED: bool = True` at module level
  - Must be pure (no I/O, no DB, no network)
  - Import whitelist only: `numpy`, `pandas`, `scipy`; forbidden: `subprocess`, `os`, `sys`, `eval`, `open`

## Structural Constraints

- **No market-cap shortcut**: Factors strongly correlated (`|corr| > 0.3`) with `$market_cap` or `$circ_market_cap` are rejected — these are size-factor proxies, not alpha.
- **No holdout leakage**: Phase 2 / Phase 3 code must never read 2024 data. Holdout is physically isolated in `storage/_holdout_private/`.
- **Vectorization (R5)**: No `for` loop over rows / dates / symbols. Use `groupby` / broadcasting / `einsum` / `np.linalg.pinv`.
- **Barra residual baseline**: Factor alpha is measured AFTER removing Barra style exposures, not before. `style_r²` and `alpha_survival` are the relevant metrics for CP04 Risk Cleanness.
- **Redundancy guardrail (CP05)**: Reject if `max_lib_corr > 0.70` against an already-admitted factor.
- **Sample policy versioning**: Upgrading `sample_policy_version` in `config.yaml` (e.g., `v3 → v4`) resets the `validation_exposure` counter in §7.MT multiple testing budget. Do not upgrade lightly.

## Prior Signal Space Knowledge (from legacy library, for reference only)

The legacy system's 75+ factor library was built around these themes. New batches don't need to replicate these — assume they are covered.

- **Price-volume correlation**: `pv_corr_times_vol` family (covered)
- **Volume CV ratios**: `amount_cv_10_60`, `amount_cv_5_20` (covered)
- **Volatility measures**: `hhi_vol_20`, `std_vol_20` (covered)
- **Williams %R variant** (covered)
- **Turnover volatility** (covered)

**Exhausted**:
- OHLCV daily at `corr < 0.7` is near-saturated
- Alpha101 formulae are mostly Grade D
- Simple price momentum is crowded

**Promising unexplored**:
- Candlestick microstructure × liquidity interactions
- Higher-order cross-field covariance (fundamentals × technicals)
- Timing signals (`IdxMax` / `IdxMin` based)
