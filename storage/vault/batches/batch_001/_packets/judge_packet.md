---
batch_id: batch_001
direction: candlestick_liquidity
n_candidates: 8
sample_policy_version: v3
mt_budget:
  cumulative_candidates: 0
  direction_candidates: 0
  validation_exposure: 0
  n_batches_scanned: 0
---

# Batch batch_001 — Judge Packet

Direction: **candlestick_liquidity**

## Lessons Excerpt

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

- **Default: DSL

## Candidates

### C001 — `Mul(Div(Sub($high, If(Gt($close, $open), $close, $open)), Sub($high, $low)), $turnover_rate)` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9516 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0507 ic_ir_val=-0.4441 ic_win_rate_val=0.3409 ls_mean=-0.0018 mono_val=-1.0000 mt_score=0.0000 mt_bucket=low search_adjusted=0.9000
- **CP04 (risk)**: style_r2=0.3498 barra_residual_ic=-0.0197 alpha_survival=0.3881 crowding=high dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.0000 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.1519 train_val_sign_ok=true train_val_decay=1.2203

### C002 — `Mul(Div(Sub(If(Lt($close, $open), $close, $open), $low), Sub($high, $low)), $turnover_rate)` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9516 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0644 ic_ir_val=-0.5757 ic_win_rate_val=0.2831 ls_mean=-0.0021 mono_val=-1.0000 mt_score=0.0000 mt_bucket=low search_adjusted=0.9000
- **CP04 (risk)**: style_r2=0.3562 barra_residual_ic=-0.0394 alpha_survival=0.6127 crowding=high dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.0000 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.0998 train_val_sign_ok=true train_val_decay=1.6154

### C003 — `Mul(Mul(Div(Sub($high, $low), $close), Div(Sub($high, $low), $close)), $turnover_rate)` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9562 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0737 ic_ir_val=-0.4981 ic_win_rate_val=0.3450 ls_mean=-0.0015 mono_val=-0.9000 mt_score=0.0000 mt_bucket=low search_adjusted=0.9000
- **CP04 (risk)**: style_r2=0.4574 barra_residual_ic=-0.0425 alpha_survival=0.5768 crowding=high dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.0000 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.1420 train_val_sign_ok=true train_val_decay=1.0920

### C004 — `Mul(Sub($high, If(Gt($close, $open), $close, $open)), Sub(If(Lt($close, $open), $close, $open), $low))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9890 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0521 ic_ir_val=-0.4179 ic_win_rate_val=0.3354 ls_mean=-0.0019 mono_val=-1.0000 mt_score=0.0000 mt_bucket=low search_adjusted=0.9000
- **CP04 (risk)**: style_r2=0.2078 barra_residual_ic=-0.0229 alpha_survival=0.4398 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.0000 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.1416 train_val_sign_ok=true train_val_decay=1.3195

### C005 — `Mean(Div(Abs(Sub($close, $open)), Sub($high, $low)), 20)` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9666 sign=1
- **CP03 (strength)**: ic_mean_val=0.0011 ic_ir_val=0.0141 ic_win_rate_val=0.5021 ls_mean=0.0004 mono_val=1.0000 mt_score=0.0000 mt_bucket=low search_adjusted=0.2429
- **CP04 (risk)**: style_r2=0.0985 barra_residual_ic=0.0109 alpha_survival=9.9469 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.0000 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=low split_sign_consistency=0.5000 split_dispersion=6.8390 train_val_sign_ok=true train_val_decay=0.1279

### C006 — `Std(Div(Abs(Sub($close, $open)), Sub($high, $low)), 20)` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9641 sign=1
- **CP03 (strength)**: ic_mean_val=0.0059 ic_ir_val=0.1548 ic_win_rate_val=0.5806 ls_mean=0.0003 mono_val=0.7000 mt_score=0.0000 mt_bucket=low search_adjusted=0.5505
- **CP04 (risk)**: style_r2=0.0412 barra_residual_ic=0.0083 alpha_survival=1.4077 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.0000 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.1195 train_val_sign_ok=true train_val_decay=2.7444

### C007 — `Div(Mean(Div(Sub($high, $low), $close), 5), Mean(Div(Sub($high, $low), $close), 60))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9771 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0381 ic_ir_val=-0.3387 ic_win_rate_val=0.3450 ls_mean=-0.0007 mono_val=-0.9000 mt_score=0.0000 mt_bucket=low search_adjusted=0.9000
- **CP04 (risk)**: style_r2=0.2493 barra_residual_ic=-0.0254 alpha_survival=0.6660 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.0000 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.1380 train_val_sign_ok=true train_val_decay=1.0240

### C008 — `Mul(Div(Sub($high, $low), $close), Mean($turnover_rate, 5))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9604 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0723 ic_ir_val=-0.4574 ic_win_rate_val=0.3678 ls_mean=-0.0016 mono_val=-0.9000 mt_score=0.0000 mt_bucket=low search_adjusted=0.9000
- **CP04 (risk)**: style_r2=0.6067 barra_residual_ic=-0.0385 alpha_survival=0.5329 crowding=high dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.0000 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.1205 train_val_sign_ok=true train_val_decay=1.2080

