---
batch_id: batch_007
direction: fundamental_technical_cov
n_candidates: 8
sample_policy_version: v3
mt_budget:
  cumulative_candidates: 48
  direction_candidates: 16
  validation_exposure: 6
  n_batches_scanned: 6
---

# Batch batch_007 — Judge Packet

Direction: **fundamental_technical_cov**

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

### C001 — `Cov($amount, $pe_ratio, 20)` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9878 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0280 ic_ir_val=-0.3733 ic_win_rate_val=0.3285 ls_mean=-0.0009 mono_val=-0.4000 mt_score=0.5282 mt_bucket=medium search_adjusted=0.6623
- **CP04 (risk)**: style_r2=0.1124 barra_residual_ic=-0.0099 alpha_survival=0.3550 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.8551 nearest=F007 exceeds_threshold=true
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.2072 train_val_sign_ok=true train_val_decay=1.2531

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0223 ic_ir_IS=-0.1852 ic_win_rate=0.4143
- **D1 年度IC**: 2015=-0.0147 2016=-0.0275 2017=-0.0293 2018=-0.0224 2019=-0.0250 2020=-0.0141 2021=-0.0232
- **D2 稳健性**: oos_decay_ratio=1.2531 ic_autocorr=-0.0229 ic_max_drawdown=-37.8793 worst_quarter=-0.0485 best_quarter=0.0087
- **D3 经济一致**: mono_IS=-0.4000 mono_OOS=-0.4000 ls_return=-0.0010 ls_tstat=-6.0837 sign_consistent=1
- **D3 分组IS**: q1=0.0006 q2=0.0014 q3=0.0010 q4=0.0006 q5=-0.0004
- **D4 衰减与换手**: factor_turnover=0.0452 factor_autocorr=0.9548
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=0.1291 kurtosis=0.0220 extreme_ratio=0.0000
- **D6 独特性**: max_lib_corr=0.8551 nearest=F007 expr_depth=1

### C002 — `Cov($turnover_rate, $ps_ratio, 20)` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9653 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0483 ic_ir_val=-0.3937 ic_win_rate_val=0.3616 ls_mean=-0.0011 mono_val=-0.7000 mt_score=0.5282 mt_bucket=medium search_adjusted=0.6623
- **CP04 (risk)**: style_r2=0.3218 barra_residual_ic=-0.0136 alpha_survival=0.2824 crowding=high dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.5878 nearest=F007 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.2227 train_val_sign_ok=true train_val_decay=1.4775

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0327 ic_ir_IS=-0.2463 ic_win_rate=0.3920
- **D1 年度IC**: 2015=-0.0182 2016=-0.0311 2017=-0.0359 2018=-0.0304 2019=-0.0413 2020=-0.0359 2021=-0.0358
- **D2 稳健性**: oos_decay_ratio=1.4775 ic_autocorr=-0.0015 ic_max_drawdown=-55.5512 worst_quarter=-0.0627 best_quarter=0.0087
- **D3 经济一致**: mono_IS=-1.0000 mono_OOS=-0.7000 ls_return=-0.0013 ls_tstat=-6.1380 sign_consistent=1
- **D3 分组IS**: q1=0.0011 q2=0.0010 q3=0.0008 q4=0.0006 q5=-0.0002
- **D4 衰减与换手**: factor_turnover=0.0500 factor_autocorr=0.9500
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=0.3595 kurtosis=-0.3993 extreme_ratio=0.0000
- **D6 独特性**: max_lib_corr=0.5878 nearest=F007 expr_depth=1

### C003 — `Cov($turnover_rate, $pb_ratio, 20)` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9656 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0499 ic_ir_val=-0.4045 ic_win_rate_val=0.3533 ls_mean=-0.0011 mono_val=-0.7000 mt_score=0.5282 mt_bucket=medium search_adjusted=0.6623
- **CP04 (risk)**: style_r2=0.3722 barra_residual_ic=-0.0165 alpha_survival=0.3301 crowding=high dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.5859 nearest=F007 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.2046 train_val_sign_ok=true train_val_decay=1.4193

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0352 ic_ir_IS=-0.2600 ic_win_rate=0.3820
- **D1 年度IC**: 2015=-0.0230 2016=-0.0340 2017=-0.0356 2018=-0.0332 2019=-0.0449 2020=-0.0375 2021=-0.0381
- **D2 稳健性**: oos_decay_ratio=1.4193 ic_autocorr=-0.0078 ic_max_drawdown=-59.8034 worst_quarter=-0.0668 best_quarter=0.0049
- **D3 经济一致**: mono_IS=-1.0000 mono_OOS=-0.7000 ls_return=-0.0013 ls_tstat=-6.1186 sign_consistent=1
- **D3 分组IS**: q1=0.0012 q2=0.0010 q3=0.0008 q4=0.0006 q5=-0.0002
- **D4 衰减与换手**: factor_turnover=0.0484 factor_autocorr=0.9516
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=0.4025 kurtosis=-0.2495 extreme_ratio=0.0000
- **D6 独特性**: max_lib_corr=0.5859 nearest=F007 expr_depth=1

### C004 — `Mul(Sub(CsRank(Mul($pe_ratio, -1)), CsRank(Mul(Ref($pe_ratio, 60), -1))), CsRank($turnover_rate))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9201 sign=1
- **CP03 (strength)**: ic_mean_val=0.0160 ic_ir_val=0.1972 ic_win_rate_val=0.5806 ls_mean=0.0004 mono_val=0.1000 mt_score=0.5282 mt_bucket=medium search_adjusted=0.4897
- **CP04 (risk)**: style_r2=0.0611 barra_residual_ic=0.0080 alpha_survival=0.4985 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.1515 nearest=F007 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.1961 train_val_sign_ok=true train_val_decay=0.6202

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=0.0258 ic_ir_IS=0.3440 ic_win_rate=0.6462
- **D1 年度IC**: 2015=0.0339 2016=0.0258 2017=0.0277 2018=0.0234 2019=0.0321 2020=0.0213 2021=0.0182
- **D2 稳健性**: oos_decay_ratio=0.6202 ic_autocorr=0.0492 ic_max_drawdown=-1.0306 worst_quarter=0.0083 best_quarter=0.0525
- **D3 经济一致**: mono_IS=1.0000 mono_OOS=0.1000 ls_return=0.0010 ls_tstat=7.1201 sign_consistent=1
- **D3 分组IS**: q1=-0.0004 q2=0.0003 q3=0.0005 q4=0.0006 q5=0.0006
- **D4 衰减与换手**: factor_turnover=0.0418 factor_autocorr=0.9582
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=-0.0487 kurtosis=1.1055 extreme_ratio=0.0000
- **D6 独特性**: max_lib_corr=0.1515 nearest=F007 expr_depth=8

### C005 — `Mul(Sub(CsRank(Mul($pe_ratio, -1)), CsRank(Mul(Ref($pe_ratio, 60), -1))), CsRank(Mul($pb_ratio, -1)))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9507 sign=1
- **CP03 (strength)**: ic_mean_val=0.0134 ic_ir_val=0.1638 ic_win_rate_val=0.5620 ls_mean=0.0003 mono_val=0.9000 mt_score=0.5282 mt_bucket=medium search_adjusted=0.5254
- **CP04 (risk)**: style_r2=0.0386 barra_residual_ic=0.0093 alpha_survival=0.6932 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.1462 nearest=F006 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.4685 train_val_sign_ok=true train_val_decay=0.5534

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=0.0242 ic_ir_IS=0.3212 ic_win_rate=0.6267
- **D1 年度IC**: 2015=0.0286 2016=0.0237 2017=0.0328 2018=0.0170 2019=0.0263 2020=0.0222 2021=0.0201
- **D2 稳健性**: oos_decay_ratio=0.5534 ic_autocorr=0.0601 ic_max_drawdown=-1.0329 worst_quarter=0.0032 best_quarter=0.0513
- **D3 经济一致**: mono_IS=1.0000 mono_OOS=0.9000 ls_return=0.0009 ls_tstat=6.6297 sign_consistent=1
- **D3 分组IS**: q1=-0.0001 q2=0.0002 q3=0.0003 q4=0.0005 q5=0.0008
- **D4 衰减与换手**: factor_turnover=0.0300 factor_autocorr=0.9700
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=0.0319 kurtosis=1.5239 extreme_ratio=0.0003
- **D6 独特性**: max_lib_corr=0.1462 nearest=F006 expr_depth=9

### C006 — `Corr($turnover_rate, $pb_ratio, 60)` (dsl)

**Hard Gate (CP01)**: `reject`
  - compute_error: ValueError: preprocessed factor is empty (all NaN)

_Numeric hints omitted — hard gate failed._

### C007 — `Corr($amount, $ps_ratio, 60)` (dsl)

**Hard Gate (CP01)**: `reject`
  - compute_error: ValueError: preprocessed factor is empty (all NaN)

_Numeric hints omitted — hard gate failed._

### C008 — `Cov(Div($close, Ref($close, 1)), $pe_ratio, 20)` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9872 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0208 ic_ir_val=-0.2214 ic_win_rate_val=0.4112 ls_mean=-0.0003 mono_val=-0.7000 mt_score=0.5282 mt_bucket=medium search_adjusted=0.6623
- **CP04 (risk)**: style_r2=0.0998 barra_residual_ic=-0.0069 alpha_survival=0.3339 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.5224 nearest=F007 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.2273 train_val_sign_ok=true train_val_decay=1.1765

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0177 ic_ir_IS=-0.1367 ic_win_rate=0.4245
- **D1 年度IC**: 2015=-0.0027 2016=-0.0232 2017=-0.0293 2018=-0.0258 2019=-0.0149 2020=-0.0075 2021=-0.0202
- **D2 稳健性**: oos_decay_ratio=1.1765 ic_autocorr=0.0133 ic_max_drawdown=-32.1806 worst_quarter=-0.0436 best_quarter=0.0160
- **D3 经济一致**: mono_IS=-0.9000 mono_OOS=-0.7000 ls_return=-0.0008 ls_tstat=-4.1089 sign_consistent=1
- **D3 分组IS**: q1=0.0008 q2=0.0012 q3=0.0006 q4=0.0005 q5=0.0001
- **D4 衰减与换手**: factor_turnover=0.0998 factor_autocorr=0.9002
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=0.1826 kurtosis=0.6392 extreme_ratio=0.0000
- **D6 独特性**: max_lib_corr=0.5224 nearest=F007 expr_depth=3

