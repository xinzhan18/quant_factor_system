---
batch_id: batch_005
direction: fundamental_technical_cov
n_candidates: 8
sample_policy_version: v3
mt_budget:
  cumulative_candidates: 32
  direction_candidates: 0
  validation_exposure: 4
  n_batches_scanned: 4
---

# Batch batch_005 — Judge Packet

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

### C001 — `Cov($turnover_rate, $pe_ratio, 60)` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9769 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0177 ic_ir_val=-0.2250 ic_win_rate_val=0.4194 ls_mean=-0.0005 mono_val=-0.8000 mt_score=0.2933 mt_bucket=low search_adjusted=0.7280
- **CP04 (risk)**: style_r2=0.0785 barra_residual_ic=-0.0047 alpha_survival=0.2655 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.2294 nearest=F001 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.4054 train_val_sign_ok=true train_val_decay=1.4502

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0122 ic_ir_IS=-0.1173 ic_win_rate=0.4466
- **D1 年度IC**: 2015=-0.0014 2016=-0.0150 2017=-0.0191 2018=-0.0089 2019=-0.0110 2020=-0.0143 2021=-0.0155
- **D2 稳健性**: oos_decay_ratio=1.4502 ic_autocorr=-0.0022 ic_max_drawdown=-21.2874 worst_quarter=-0.0389 best_quarter=0.0215
- **D3 经济一致**: mono_IS=-0.7000 mono_OOS=-0.8000 ls_return=-0.0005 ls_tstat=-3.6932 sign_consistent=1
- **D3 分组IS**: q1=0.0007 q2=0.0010 q3=0.0008 q4=0.0006 q5=0.0001
- **D4 衰减与换手**: factor_turnover=0.0159 factor_autocorr=0.9841
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=0.0809 kurtosis=0.0077 extreme_ratio=0.0000
- **D6 独特性**: max_lib_corr=0.2294 nearest=F001 expr_depth=1

### C002 — `Cov($turnover_rate, $pb_ratio, 60)` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9769 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0371 ic_ir_val=-0.2610 ic_win_rate_val=0.4174 ls_mean=-0.0008 mono_val=-0.9000 mt_score=0.2933 mt_bucket=low search_adjusted=0.7680
- **CP04 (risk)**: style_r2=0.3221 barra_residual_ic=-0.0074 alpha_survival=0.1998 crowding=high dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.3629 nearest=F001 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.2547 train_val_sign_ok=true train_val_decay=1.6443

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0226 ic_ir_IS=-0.1602 ic_win_rate=0.4290
- **D1 年度IC**: 2015=-0.0040 2016=-0.0225 2017=-0.0287 2018=-0.0162 2019=-0.0271 2020=-0.0304 2021=-0.0290
- **D2 稳健性**: oos_decay_ratio=1.6443 ic_autocorr=0.0255 ic_max_drawdown=-38.8500 worst_quarter=-0.0578 best_quarter=0.0296
- **D3 经济一致**: mono_IS=-1.0000 mono_OOS=-0.9000 ls_return=-0.0008 ls_tstat=-3.6383 sign_consistent=1
- **D3 分组IS**: q1=0.0009 q2=0.0009 q3=0.0007 q4=0.0006 q5=0.0001
- **D4 衰减与换手**: factor_turnover=0.0116 factor_autocorr=0.9884
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=0.4554 kurtosis=-0.1760 extreme_ratio=0.0000
- **D6 独特性**: max_lib_corr=0.3629 nearest=F001 expr_depth=1

### C003 — `Corr($turnover_rate, $pe_ratio, 20)` (dsl)

**Hard Gate (CP01)**: `reject`
  - compute_error: ValueError: preprocessed factor is empty (all NaN)

_Numeric hints omitted — hard gate failed._

### C004 — `Cov($amount, $ps_ratio, 60)` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9882 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0457 ic_ir_val=-0.3359 ic_win_rate_val=0.3698 ls_mean=-0.0014 mono_val=-1.0000 mt_score=0.2933 mt_bucket=low search_adjusted=0.7680
- **CP04 (risk)**: style_r2=0.2711 barra_residual_ic=-0.0019 alpha_survival=0.0425 crowding=high dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.2572 nearest=F002 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.1739 train_val_sign_ok=true train_val_decay=1.8436

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0248 ic_ir_IS=-0.1692 ic_win_rate=0.4085
- **D1 年度IC**: 2015=-0.0135 2016=-0.0324 2017=-0.0254 2018=-0.0141 2019=-0.0276 2020=-0.0267 2021=-0.0338
- **D2 稳健性**: oos_decay_ratio=1.8436 ic_autocorr=0.0202 ic_max_drawdown=-42.0852 worst_quarter=-0.0634 best_quarter=0.0233
- **D3 经济一致**: mono_IS=-1.0000 mono_OOS=-1.0000 ls_return=-0.0015 ls_tstat=-5.5111 sign_consistent=1
- **D3 分组IS**: q1=0.0012 q2=0.0010 q3=0.0008 q4=0.0005 q5=-0.0002
- **D4 衰减与换手**: factor_turnover=0.0082 factor_autocorr=0.9918
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=0.5528 kurtosis=-0.2834 extreme_ratio=0.0000
- **D6 独特性**: max_lib_corr=0.2572 nearest=F002 expr_depth=1

### C005 — `Mul(CsRank($pe_ratio), CsRank($turnover_rate))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9554 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0454 ic_ir_val=-0.3294 ic_win_rate_val=0.3946 ls_mean=-0.0010 mono_val=-0.9000 mt_score=0.2933 mt_bucket=low search_adjusted=0.7680
- **CP04 (risk)**: style_r2=0.3807 barra_residual_ic=-0.0213 alpha_survival=0.4696 crowding=high dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.4610 nearest=F001 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.2024 train_val_sign_ok=true train_val_decay=1.2235

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0371 ic_ir_IS=-0.2331 ic_win_rate=0.3859
- **D1 年度IC**: 2015=-0.0263 2016=-0.0506 2017=-0.0531 2018=-0.0329 2019=-0.0329 2020=-0.0254 2021=-0.0385
- **D2 稳健性**: oos_decay_ratio=1.2235 ic_autocorr=0.0242 ic_max_drawdown=-64.0951 worst_quarter=-0.0838 best_quarter=-0.0068
- **D3 经济一致**: mono_IS=-0.9000 mono_OOS=-0.9000 ls_return=-0.0018 ls_tstat=-6.8300 sign_consistent=1
- **D3 分组IS**: q1=0.0015 q2=0.0007 q3=0.0008 q4=0.0006 q5=-0.0002
- **D4 衰减与换手**: factor_turnover=0.0373 factor_autocorr=0.9627
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=0.7936 kurtosis=-0.4268 extreme_ratio=0.0001
- **D6 独特性**: max_lib_corr=0.4610 nearest=F001 expr_depth=3

### C006 — `Mul(CsRank(Mul($pb_ratio, -1)), CsRank($turnover_rate))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9554 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0149 ic_ir_val=-0.1571 ic_win_rate_val=0.4463 ls_mean=0.0001 mono_val=0.4000 mt_score=0.2933 mt_bucket=low search_adjusted=0.6264
- **CP04 (risk)**: style_r2=0.3032 barra_residual_ic=-0.0267 alpha_survival=1.7931 crowding=high dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.3001 nearest=F001 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.5386 train_val_sign_ok=true train_val_decay=0.5760

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0259 ic_ir_IS=-0.2647 ic_win_rate=0.3842
- **D1 年度IC**: 2015=-0.0194 2016=-0.0233 2017=-0.0314 2018=-0.0259 2019=-0.0317 2020=-0.0332 2021=-0.0163
- **D2 稳健性**: oos_decay_ratio=0.5760 ic_autocorr=-0.0080 ic_max_drawdown=-44.2050 worst_quarter=-0.0613 best_quarter=0.0075
- **D3 经济一致**: mono_IS=-1.0000 mono_OOS=0.4000 ls_return=-0.0017 ls_tstat=-9.2263 sign_consistent=1
- **D3 分组IS**: q1=0.0015 q2=0.0006 q3=0.0006 q4=0.0005 q5=0.0001
- **D4 衰减与换手**: factor_turnover=0.0657 factor_autocorr=0.9343
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=0.9341 kurtosis=0.4717 extreme_ratio=0.0078
- **D6 独特性**: max_lib_corr=0.3001 nearest=F001 expr_depth=4

### C007 — `Mul(Sub(Div($close, $pe_ratio), Div(Ref($close, 60), Ref($pe_ratio, 60))), CsRank($turnover_rate))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9201 sign=1
- **CP03 (strength)**: ic_mean_val=0.0029 ic_ir_val=0.0528 ic_win_rate_val=0.5455 ls_mean=0.0000 mono_val=0.0000 mt_score=0.2933 mt_bucket=low search_adjusted=0.1168
- **CP04 (risk)**: style_r2=0.0898 barra_residual_ic=0.0094 alpha_survival=3.2507 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.0724 nearest=F002 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=low split_sign_consistency=0.7500 split_dispersion=1.8717 train_val_sign_ok=true train_val_decay=0.3878

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=0.0074 ic_ir_IS=0.1307 ic_win_rate=0.5647
- **D1 年度IC**: 2015=0.0010 2016=-0.0022 2017=0.0137 2018=0.0072 2019=0.0148 2020=0.0131 2021=0.0029
- **D2 稳健性**: oos_decay_ratio=0.3878 ic_autocorr=0.1617 ic_max_drawdown=-1.3508 worst_quarter=-0.0150 best_quarter=0.0252
- **D3 经济一致**: mono_IS=0.7000 mono_OOS=0.0000 ls_return=0.0007 ls_tstat=6.6560 sign_consistent=1
- **D3 分组IS**: q1=-0.0002 q2=0.0003 q3=0.0005 q4=0.0004 q5=0.0005
- **D4 衰减与换手**: factor_turnover=0.0782 factor_autocorr=0.9218
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=-0.0021 kurtosis=0.7661 extreme_ratio=0.0000
- **D6 独特性**: max_lib_corr=0.0724 nearest=F002 expr_depth=7

### C008 — `Mul(CsRank(Div(Div($close, $ps_ratio), Div(Ref($close, 60), Ref($ps_ratio, 60)))), CsRank(Mul($pb_ratio, -1)))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9504 sign=1
- **CP03 (strength)**: ic_mean_val=0.0297 ic_ir_val=0.3305 ic_win_rate_val=0.6260 ls_mean=0.0007 mono_val=1.0000 mt_score=0.2933 mt_bucket=low search_adjusted=0.7680
- **CP04 (risk)**: style_r2=0.2722 barra_residual_ic=0.0069 alpha_survival=0.2323 crowding=high dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.1668 nearest=F002 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.1328 train_val_sign_ok=true train_val_decay=1.4527

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=0.0204 ic_ir_IS=0.2659 ic_win_rate=0.5824
- **D1 年度IC**: 2015=0.0204 2016=0.0239 2017=0.0234 2018=0.0167 2019=0.0233 2020=0.0137 2021=0.0216
- **D2 稳健性**: oos_decay_ratio=1.4527 ic_autocorr=0.0931 ic_max_drawdown=-0.7261 worst_quarter=-0.0035 best_quarter=0.0420
- **D3 经济一致**: mono_IS=1.0000 mono_OOS=1.0000 ls_return=0.0007 ls_tstat=4.8003 sign_consistent=1
- **D3 分组IS**: q1=-0.0001 q2=0.0003 q3=0.0003 q4=0.0005 q5=0.0006
- **D4 衰减与换手**: factor_turnover=0.0421 factor_autocorr=0.9579
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=0.9828 kurtosis=0.2613 extreme_ratio=0.0054
- **D6 独特性**: max_lib_corr=0.1668 nearest=F002 expr_depth=9

