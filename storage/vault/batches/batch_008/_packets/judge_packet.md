---
batch_id: batch_008
direction: timing_signals
n_candidates: 8
sample_policy_version: v3
mt_budget:
  cumulative_candidates: 56
  direction_candidates: 0
  validation_exposure: 7
  n_batches_scanned: 7
---

# Batch batch_008 — Judge Packet

Direction: **timing_signals**

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

### C001 — `IdxMax($close, 20)` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9893 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0227 ic_ir_val=-0.2019 ic_win_rate_val=0.4013 ls_mean=-0.0000 mono_val=-0.1000 mt_score=0.3510 mt_bucket=low search_adjusted=0.6184
- **CP04 (risk)**: style_r2=0.3681 barra_residual_ic=-0.0127 alpha_survival=0.5598 crowding=high dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.2526 nearest=F005 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.2966 train_val_sign_ok=true train_val_decay=1.1164

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0203 ic_ir_IS=-0.1665 ic_win_rate=0.4093
- **D1 年度IC**: 2015=0.0019 2016=-0.0273 2017=-0.0248 2018=-0.0214 2019=-0.0418 2020=-0.0137 2021=-0.0143
- **D2 稳健性**: oos_decay_ratio=1.1164 ic_autocorr=-0.0255 ic_max_drawdown=-34.6917 worst_quarter=-0.0706 best_quarter=0.0154
- **D3 经济一致**: mono_IS=-0.1000 mono_OOS=-0.1000 ls_return=0.0003 ls_tstat=1.0314 sign_consistent=1
- **D3 分组IS**: q1=0.0000 q2=0.0008 q3=0.0018 q4=-0.0000 q5=0.0005
- **D4 衰减与换手**: factor_turnover=0.1281 factor_autocorr=0.8719
- **D5 分布**: coverage=1.0000 zero_ratio=0.0584 skew=0.1131 kurtosis=-0.6787 extreme_ratio=0.0011
- **D6 独特性**: max_lib_corr=0.2526 nearest=F005 expr_depth=1

### C002 — `IdxMin($close, 20)` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9893 sign=1
- **CP03 (strength)**: ic_mean_val=0.0164 ic_ir_val=0.1367 ic_win_rate_val=0.5603 ls_mean=0.0003 mono_val=0.2000 mt_score=0.3510 mt_bucket=low search_adjusted=0.5226
- **CP04 (risk)**: style_r2=0.3261 barra_residual_ic=-0.0048 alpha_survival=0.2899 crowding=high dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.0937 nearest=F001 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=0.7500 split_dispersion=0.7030 train_val_sign_ok=true train_val_decay=2.7560

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=0.0060 ic_ir_IS=0.0466 ic_win_rate=0.5227
- **D1 年度IC**: 2015=0.0160 2016=0.0027 2017=-0.0074 2018=0.0021 2019=0.0176 2020=0.0050 2021=0.0084
- **D2 稳健性**: oos_decay_ratio=2.7560 ic_autocorr=0.1074 ic_max_drawdown=-3.3578 worst_quarter=-0.0207 best_quarter=0.0418
- **D3 经济一致**: mono_IS=-0.6000 mono_OOS=0.2000 ls_return=-0.0022 ls_tstat=-8.1109 sign_consistent=1
- **D3 分组IS**: q1=0.0008 q2=0.0009 q3=0.0012 q4=0.0006 q5=-0.0008
- **D4 衰减与换手**: factor_turnover=0.1254 factor_autocorr=0.8746
- **D5 分布**: coverage=1.0000 zero_ratio=0.1751 skew=0.0689 kurtosis=-0.0516 extreme_ratio=0.0033
- **D6 独特性**: max_lib_corr=0.0937 nearest=F001 expr_depth=1

### C003 — `IdxMax($volume, 20)` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9893 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0256 ic_ir_val=-0.3732 ic_win_rate_val=0.3554 ls_mean=-0.0004 mono_val=-0.7000 mt_score=0.3510 mt_bucket=low search_adjusted=0.7420
- **CP04 (risk)**: style_r2=0.0757 barra_residual_ic=-0.0271 alpha_survival=1.0606 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.3571 nearest=F005 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.0520 train_val_sign_ok=true train_val_decay=0.9305

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0275 ic_ir_IS=-0.2789 ic_win_rate=0.3427
- **D1 年度IC**: 2015=0.0067 2016=-0.0326 2017=-0.0366 2018=-0.0427 2019=-0.0456 2020=-0.0277 2021=-0.0139
- **D2 稳健性**: oos_decay_ratio=0.9305 ic_autocorr=0.0204 ic_max_drawdown=-49.8450 worst_quarter=-0.0552 best_quarter=0.0182
- **D3 经济一致**: mono_IS=-1.0000 mono_OOS=-0.7000 ls_return=-0.0012 ls_tstat=-4.9157 sign_consistent=1
- **D3 分组IS**: q1=0.0010 q2=0.0009 q3=0.0008 q4=0.0008 q5=-0.0002
- **D4 衰减与换手**: factor_turnover=0.1611 factor_autocorr=0.8389
- **D5 分布**: coverage=1.0000 zero_ratio=0.0020 skew=0.1399 kurtosis=-1.0894 extreme_ratio=0.0000
- **D6 独特性**: max_lib_corr=0.3571 nearest=F005 expr_depth=1

### C004 — `IdxMax($turnover_rate, 20)` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9692 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0252 ic_ir_val=-0.3668 ic_win_rate_val=0.3595 ls_mean=-0.0005 mono_val=-0.7000 mt_score=0.3510 mt_bucket=low search_adjusted=0.7420
- **CP04 (risk)**: style_r2=0.0785 barra_residual_ic=-0.0241 alpha_survival=0.9553 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.2863 nearest=F005 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.0675 train_val_sign_ok=true train_val_decay=0.8834

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0285 ic_ir_IS=-0.3921 ic_win_rate=0.3241
- **D1 年度IC**: 2015=-0.0201 2016=-0.0336 2017=-0.0294 2018=-0.0313 2019=-0.0451 2020=-0.0271 2021=-0.0129
- **D2 稳健性**: oos_decay_ratio=0.8834 ic_autocorr=0.0492 ic_max_drawdown=-49.1750 worst_quarter=-0.0561 best_quarter=0.0175
- **D3 经济一致**: mono_IS=-0.9000 mono_OOS=-0.7000 ls_return=-0.0012 ls_tstat=-8.3314 sign_consistent=1
- **D3 分组IS**: q1=0.0010 q2=0.0009 q3=0.0008 q4=0.0009 q5=-0.0002
- **D4 衰减与换手**: factor_turnover=0.1658 factor_autocorr=0.8342
- **D5 分布**: coverage=1.0000 zero_ratio=0.0023 skew=0.1332 kurtosis=-1.0751 extreme_ratio=0.0000
- **D6 独特性**: max_lib_corr=0.2863 nearest=F005 expr_depth=1

### C005 — `Mul(IdxMax($close, 20), Div($close, Ref($close, 5)))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9858 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0281 ic_ir_val=-0.2414 ic_win_rate_val=0.3988 ls_mean=-0.0002 mono_val=-0.4000 mt_score=0.3510 mt_bucket=low search_adjusted=0.7420
- **CP04 (risk)**: style_r2=0.4028 barra_residual_ic=-0.0156 alpha_survival=0.5543 crowding=high dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.2679 nearest=F005 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.2049 train_val_sign_ok=true train_val_decay=1.2090

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0232 ic_ir_IS=-0.1885 ic_win_rate=0.3982
- **D1 年度IC**: 2015=0.0044 2016=-0.0290 2017=-0.0235 2018=-0.0309 2019=-0.0468 2020=-0.0177 2021=-0.0186
- **D2 稳健性**: oos_decay_ratio=1.2090 ic_autocorr=-0.0218 ic_max_drawdown=-42.2144 worst_quarter=-0.0716 best_quarter=0.0235
- **D3 经济一致**: mono_IS=0.3000 mono_OOS=-0.4000 ls_return=0.0005 ls_tstat=2.1768 sign_consistent=1
- **D3 分组IS**: q1=0.0002 q2=0.0007 q3=0.0006 q4=0.0006 q5=0.0007
- **D4 衰减与换手**: factor_turnover=0.1447 factor_autocorr=0.8553
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=0.2838 kurtosis=-0.5932 extreme_ratio=0.0013
- **D6 独特性**: max_lib_corr=0.2679 nearest=F005 expr_depth=4

### C006 — `Mul(IdxMin($close, 20), Mul(Div($close, Ref($close, 5)), -1))` (dsl)

**Hard Gate (CP01)**: `reject`
  - sign_flip: train +0.001809 vs validation -0.010824

_Numeric hints omitted — hard gate failed._

### C007 — `Sub(IdxMax($close, 60), IdxMax($close, 5))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9890 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0135 ic_ir_val=-0.1107 ic_win_rate_val=0.4318 ls_mean=-0.0003 mono_val=0.0000 mt_score=0.3510 mt_bucket=low search_adjusted=0.3594
- **CP04 (risk)**: style_r2=0.2297 barra_residual_ic=0.0074 alpha_survival=0.5486 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.1111 nearest=F004 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.5065 train_val_sign_ok=true train_val_decay=1.3016

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0104 ic_ir_IS=-0.1003 ic_win_rate=0.4574
- **D1 年度IC**: 2015=-0.0021 2016=-0.0168 2017=-0.0100 2018=-0.0022 2019=-0.0152 2020=-0.0087 2021=-0.0158
- **D2 稳健性**: oos_decay_ratio=1.3016 ic_autocorr=-0.0056 ic_max_drawdown=-17.6036 worst_quarter=-0.0427 best_quarter=0.0216
- **D3 经济一致**: mono_IS=-0.7000 mono_OOS=0.0000 ls_return=-0.0007 ls_tstat=-3.3181 sign_consistent=1
- **D3 分组IS**: q1=0.0008 q2=0.0004 q3=0.0014 q4=0.0004 q5=0.0001
- **D4 衰减与换手**: factor_turnover=0.0655 factor_autocorr=0.9345
- **D5 分布**: coverage=1.0000 zero_ratio=0.0425 skew=0.2642 kurtosis=-0.4950 extreme_ratio=0.0022
- **D6 独特性**: max_lib_corr=0.1111 nearest=F004 expr_depth=3

### C008 — `Mul(IdxMax($volume, 20), Mul(Div($close, Ref($close, 5)), -1))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9858 sign=1
- **CP03 (strength)**: ic_mean_val=0.0285 ic_ir_val=0.3833 ic_win_rate_val=0.6612 ls_mean=0.0005 mono_val=0.9000 mt_score=0.3510 mt_bucket=low search_adjusted=0.7420
- **CP04 (risk)**: style_r2=0.1036 barra_residual_ic=0.0284 alpha_survival=0.9995 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.3747 nearest=F005 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.0301 train_val_sign_ok=true train_val_decay=1.0679

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=0.0267 ic_ir_IS=0.2641 ic_win_rate=0.6488
- **D1 年度IC**: 2015=-0.0112 2016=0.0314 2017=0.0313 2018=0.0436 2019=0.0474 2020=0.0270 2021=0.0164
- **D2 稳健性**: oos_decay_ratio=1.0679 ic_autocorr=0.0067 ic_max_drawdown=-4.4279 worst_quarter=-0.0245 best_quarter=0.0590
- **D3 经济一致**: mono_IS=0.4000 mono_OOS=0.9000 ls_return=0.0003 ls_tstat=1.3968 sign_consistent=1
- **D3 分组IS**: q1=0.0002 q2=0.0007 q3=0.0007 q4=0.0008 q5=0.0006
- **D4 衰减与换手**: factor_turnover=0.1552 factor_autocorr=0.8448
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=-0.3043 kurtosis=-0.7892 extreme_ratio=0.0008
- **D6 独特性**: max_lib_corr=0.3747 nearest=F005 expr_depth=5

