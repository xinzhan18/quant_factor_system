---
batch_id: batch_006
direction: fundamental_technical_cov
n_candidates: 8
sample_policy_version: v3
mt_budget:
  cumulative_candidates: 40
  direction_candidates: 8
  validation_exposure: 5
  n_batches_scanned: 5
---

# Batch batch_006 — Judge Packet

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

### C001 — `Cov($turnover_rate, $pe_ratio, 20)` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9656 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0235 ic_ir_val=-0.3161 ic_win_rate_val=0.3926 ls_mean=-0.0007 mono_val=-0.7000 mt_score=0.4657 mt_bucket=medium search_adjusted=0.6904
- **CP04 (risk)**: style_r2=0.0992 barra_residual_ic=-0.0115 alpha_survival=0.4915 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.2341 nearest=F001 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.3480 train_val_sign_ok=true train_val_decay=1.1163

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0210 ic_ir_IS=-0.2005 ic_win_rate=0.4090
- **D1 年度IC**: 2015=-0.0150 2016=-0.0220 2017=-0.0286 2018=-0.0226 2019=-0.0216 2020=-0.0170 2021=-0.0203
- **D2 稳健性**: oos_decay_ratio=1.1163 ic_autocorr=-0.0129 ic_max_drawdown=-35.7168 worst_quarter=-0.0477 best_quarter=0.0089
- **D3 经济一致**: mono_IS=-0.7000 mono_OOS=-0.7000 ls_return=-0.0009 ls_tstat=-6.2064 sign_consistent=1
- **D3 分组IS**: q1=0.0008 q2=0.0011 q3=0.0008 q4=0.0007 q5=-0.0001
- **D4 衰减与换手**: factor_turnover=0.0538 factor_autocorr=0.9462
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=0.1131 kurtosis=-0.0224 extreme_ratio=0.0000
- **D6 独特性**: max_lib_corr=0.2341 nearest=F001 expr_depth=1

### C002 — `Cov($amount, $pe_ratio, 60)` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9885 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0232 ic_ir_val=-0.2783 ic_win_rate_val=0.3760 ls_mean=-0.0007 mono_val=-0.7000 mt_score=0.4657 mt_bucket=medium search_adjusted=0.6904
- **CP04 (risk)**: style_r2=0.0751 barra_residual_ic=-0.0028 alpha_survival=0.1191 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.1848 nearest=F002 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.2431 train_val_sign_ok=true train_val_decay=1.4792

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0157 ic_ir_IS=-0.1428 ic_win_rate=0.4313
- **D1 年度IC**: 2015=-0.0133 2016=-0.0223 2017=-0.0186 2018=-0.0103 2019=-0.0123 2020=-0.0128 2021=-0.0203
- **D2 稳健性**: oos_decay_ratio=1.4792 ic_autocorr=0.0122 ic_max_drawdown=-26.6499 worst_quarter=-0.0492 best_quarter=0.0183
- **D3 经济一致**: mono_IS=-0.7000 mono_OOS=-0.7000 ls_return=-0.0008 ls_tstat=-4.5798 sign_consistent=1
- **D3 分组IS**: q1=0.0006 q2=0.0014 q3=0.0009 q4=0.0005 q5=-0.0002
- **D4 衰减与换手**: factor_turnover=0.0127 factor_autocorr=0.9873
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=0.1078 kurtosis=0.1170 extreme_ratio=0.0000
- **D6 独特性**: max_lib_corr=0.1848 nearest=F002 expr_depth=1

### C003 — `Mul(CsRank(Sub(Div($close, $pe_ratio), Div(Ref($close, 60), Ref($pe_ratio, 60)))), CsRank($turnover_rate))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9201 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0369 ic_ir_val=-0.3456 ic_win_rate_val=0.3781 ls_mean=-0.0006 mono_val=-0.4000 mt_score=0.4657 mt_bucket=medium search_adjusted=0.6904
- **CP04 (risk)**: style_r2=0.2811 barra_residual_ic=-0.0107 alpha_survival=0.2907 crowding=high dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.4204 nearest=F001 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.1866 train_val_sign_ok=true train_val_decay=1.6318

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0226 ic_ir_IS=-0.1866 ic_win_rate=0.4049
- **D1 年度IC**: 2015=-0.0161 2016=-0.0343 2017=-0.0190 2018=-0.0211 2019=-0.0225 2020=-0.0165 2021=-0.0270
- **D2 稳健性**: oos_decay_ratio=1.6318 ic_autocorr=0.0207 ic_max_drawdown=-37.0508 worst_quarter=-0.0584 best_quarter=0.0041
- **D3 经济一致**: mono_IS=-0.7000 mono_OOS=-0.4000 ls_return=-0.0002 ls_tstat=-1.1111 sign_consistent=1
- **D3 分组IS**: q1=0.0003 q2=0.0004 q3=0.0004 q4=0.0002 q5=0.0002
- **D4 衰减与换手**: factor_turnover=0.0745 factor_autocorr=0.9255
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=0.9182 kurtosis=-0.0060 extreme_ratio=0.0029
- **D6 独特性**: max_lib_corr=0.4204 nearest=F001 expr_depth=8

### C004 — `Mul(CsRank(Sub(Div($close, $pe_ratio), Div(Ref($close, 60), Ref($pe_ratio, 60)))), CsRank(Mul($pb_ratio, -1)))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9507 sign=1
- **CP03 (strength)**: ic_mean_val=0.0309 ic_ir_val=0.3121 ic_win_rate_val=0.6198 ls_mean=0.0007 mono_val=1.0000 mt_score=0.4657 mt_bucket=medium search_adjusted=0.6904
- **CP04 (risk)**: style_r2=0.2725 barra_residual_ic=0.0098 alpha_survival=0.3186 crowding=high dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.6751 nearest=F006 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.1277 train_val_sign_ok=true train_val_decay=1.3938

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=0.0221 ic_ir_IS=0.2735 ic_win_rate=0.5915
- **D1 年度IC**: 2015=0.0197 2016=0.0239 2017=0.0278 2018=0.0205 2019=0.0250 2020=0.0139 2021=0.0235
- **D2 稳健性**: oos_decay_ratio=1.3938 ic_autocorr=0.1016 ic_max_drawdown=-0.9323 worst_quarter=-0.0081 best_quarter=0.0434
- **D3 经济一致**: mono_IS=1.0000 mono_OOS=1.0000 ls_return=0.0007 ls_tstat=4.9603 sign_consistent=1
- **D3 分组IS**: q1=-0.0001 q2=0.0002 q3=0.0004 q4=0.0005 q5=0.0006
- **D4 衰减与换手**: factor_turnover=0.0383 factor_autocorr=0.9617
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=1.0204 kurtosis=0.3247 extreme_ratio=0.0052
- **D6 独特性**: max_lib_corr=0.6751 nearest=F006 expr_depth=9

### C005 — `Mul(CsRank(Div(Div($close, $ps_ratio), Div(Ref($close, 60), Ref($ps_ratio, 60)))), CsRank($turnover_rate))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9198 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0380 ic_ir_val=-0.3387 ic_win_rate_val=0.3926 ls_mean=-0.0005 mono_val=-0.9000 mt_score=0.4657 mt_bucket=medium search_adjusted=0.6904
- **CP04 (risk)**: style_r2=0.2694 barra_residual_ic=-0.0119 alpha_survival=0.3129 crowding=high dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.4233 nearest=F001 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.1779 train_val_sign_ok=true train_val_decay=1.6038

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0237 ic_ir_IS=-0.1872 ic_win_rate=0.4055
- **D1 年度IC**: 2015=-0.0153 2016=-0.0342 2017=-0.0228 2018=-0.0238 2019=-0.0227 2020=-0.0164 2021=-0.0286
- **D2 稳健性**: oos_decay_ratio=1.6038 ic_autocorr=0.0160 ic_max_drawdown=-38.8424 worst_quarter=-0.0602 best_quarter=0.0020
- **D3 经济一致**: mono_IS=-1.0000 mono_OOS=-0.9000 ls_return=-0.0003 ls_tstat=-1.5125 sign_consistent=1
- **D3 分组IS**: q1=0.0004 q2=0.0004 q3=0.0003 q4=0.0002 q5=0.0002
- **D4 衰减与换手**: factor_turnover=0.0738 factor_autocorr=0.9262
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=0.9488 kurtosis=0.0432 extreme_ratio=0.0028
- **D6 独特性**: max_lib_corr=0.4233 nearest=F001 expr_depth=8

### C006 — `Sub(CsRank(Mul($pe_ratio, -1)), CsRank(Mul(Ref($pe_ratio, 60), -1)))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9507 sign=1
- **CP03 (strength)**: ic_mean_val=0.0136 ic_ir_val=0.1604 ic_win_rate_val=0.5558 ls_mean=0.0003 mono_val=0.3000 mt_score=0.4657 mt_bucket=medium search_adjusted=0.5086
- **CP04 (risk)**: style_r2=0.0430 barra_residual_ic=0.0087 alpha_survival=0.6358 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.1539 nearest=F006 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.3084 train_val_sign_ok=true train_val_decay=0.5293

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=0.0257 ic_ir_IS=0.3193 ic_win_rate=0.6274
- **D1 年度IC**: 2015=0.0322 2016=0.0260 2017=0.0317 2018=0.0206 2019=0.0286 2020=0.0223 2021=0.0200
- **D2 稳健性**: oos_decay_ratio=0.5293 ic_autocorr=0.0511 ic_max_drawdown=-1.1435 worst_quarter=0.0041 best_quarter=0.0529
- **D3 经济一致**: mono_IS=1.0000 mono_OOS=0.3000 ls_return=0.0010 ls_tstat=5.7465 sign_consistent=1
- **D3 分组IS**: q1=-0.0002 q2=0.0001 q3=0.0004 q4=0.0006 q5=0.0007
- **D4 衰减与换手**: factor_turnover=0.0286 factor_autocorr=0.9714
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=-0.0299 kurtosis=1.8090 extreme_ratio=0.0018
- **D6 独特性**: max_lib_corr=0.1539 nearest=F006 expr_depth=6

### C007 — `Sub(CsRank(Mul($pb_ratio, -1)), CsRank(Mul(Ref($pb_ratio, 60), -1)))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9507 sign=1
- **CP03 (strength)**: ic_mean_val=0.0282 ic_ir_val=0.2184 ic_win_rate_val=0.5950 ls_mean=0.0006 mono_val=0.1000 mt_score=0.4657 mt_bucket=medium search_adjusted=0.5754
- **CP04 (risk)**: style_r2=0.2721 barra_residual_ic=0.0044 alpha_survival=0.1575 crowding=high dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.1208 nearest=F006 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.2042 train_val_sign_ok=true train_val_decay=0.8756

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=0.0323 ic_ir_IS=0.2562 ic_win_rate=0.6274
- **D1 年度IC**: 2015=0.0436 2016=0.0406 2017=0.0214 2018=0.0265 2019=0.0437 2020=0.0273 2021=0.0253
- **D2 稳健性**: oos_decay_ratio=0.8756 ic_autocorr=0.0525 ic_max_drawdown=-2.0199 worst_quarter=0.0010 best_quarter=0.0726
- **D3 经济一致**: mono_IS=1.0000 mono_OOS=0.1000 ls_return=0.0008 ls_tstat=3.4905 sign_consistent=1
- **D3 分组IS**: q1=-0.0001 q2=0.0002 q3=0.0004 q4=0.0005 q5=0.0006
- **D4 衰减与换手**: factor_turnover=0.0292 factor_autocorr=0.9708
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=-0.0609 kurtosis=2.2202 extreme_ratio=0.0232
- **D6 独特性**: max_lib_corr=0.1208 nearest=F006 expr_depth=6

### C008 — `Mul(CsRank(Div(Div($close, $ps_ratio), Div(Ref($close, 60), Ref($ps_ratio, 60)))), CsRank(Mul($ps_ratio, -1)))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9504 sign=1
- **CP03 (strength)**: ic_mean_val=0.0202 ic_ir_val=0.2357 ic_win_rate_val=0.5950 ls_mean=0.0006 mono_val=1.0000 mt_score=0.4657 mt_bucket=medium search_adjusted=0.6904
- **CP04 (risk)**: style_r2=0.1041 barra_residual_ic=0.0058 alpha_survival=0.2878 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.7898 nearest=F006 exceeds_threshold=true
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.2953 train_val_sign_ok=true train_val_decay=1.2474

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=0.0162 ic_ir_IS=0.2432 ic_win_rate=0.5769
- **D1 年度IC**: 2015=0.0128 2016=0.0164 2017=0.0228 2018=0.0117 2019=0.0185 2020=0.0136 2021=0.0165
- **D2 稳健性**: oos_decay_ratio=1.2474 ic_autocorr=0.0902 ic_max_drawdown=-0.8565 worst_quarter=-0.0074 best_quarter=0.0329
- **D3 经济一致**: mono_IS=1.0000 mono_OOS=1.0000 ls_return=0.0006 ls_tstat=5.3045 sign_consistent=1
- **D3 分组IS**: q1=-0.0001 q2=0.0003 q3=0.0004 q4=0.0005 q5=0.0005
- **D4 衰减与换手**: factor_turnover=0.0416 factor_autocorr=0.9584
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=0.9395 kurtosis=0.1046 extreme_ratio=0.0036
- **D6 独特性**: max_lib_corr=0.7898 nearest=F006 expr_depth=9

