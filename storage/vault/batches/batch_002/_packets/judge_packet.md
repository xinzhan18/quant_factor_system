---
batch_id: batch_002
direction: candlestick_liquidity
n_candidates: 8
sample_policy_version: v3
mt_budget:
  cumulative_candidates: 8
  direction_candidates: 8
  validation_exposure: 1
  n_batches_scanned: 1
---

# Batch batch_002 — Judge Packet

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

### C001 — `CsRank(Div(Sub(If(Lt($close, $open), $close, $open), $low), Sub($high, $low)))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9516 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0181 ic_ir_val=-0.2133 ic_win_rate_val=0.4070 ls_mean=-0.0013 mono_val=-0.9000 mt_score=0.3272 mt_bucket=low search_adjusted=0.7207
- **CP04 (risk)**: style_r2=0.0308 barra_residual_ic=-0.0186 alpha_survival=1.0275 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.5963 nearest=F001 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.4126 train_val_sign_ok=true train_val_decay=4.1057

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0044 ic_ir_IS=-0.0504 ic_win_rate=0.4674
- **D1 年度IC**: 2015=0.0302 2016=0.0069 2017=-0.0057 2018=-0.0255 2019=-0.0144 2020=-0.0088 2021=-0.0116
- **D2 稳健性**: oos_decay_ratio=4.1057 ic_autocorr=0.0391 ic_max_drawdown=-17.2493 worst_quarter=-0.0453 best_quarter=0.0390
- **D3 经济一致**: mono_IS=-0.7000 mono_OOS=-0.9000 ls_return=-0.0003 ls_tstat=-2.0469 sign_consistent=1
- **D3 分组IS**: q1=0.0009 q2=0.0005 q3=0.0001 q4=0.0004 q5=0.0002
- **D4 衰减与换手**: factor_turnover=0.9872 factor_autocorr=0.0128
- **D5 分布**: coverage=1.0000 zero_ratio=0.0076 skew=0.0104 kurtosis=-1.2059 extreme_ratio=0.0000
- **D6 独特性**: max_lib_corr=0.5963 nearest=F001 expr_depth=6

### C002 — `CsRank(Mul(Sub($high, If(Gt($close, $open), $close, $open)), Sub(If(Lt($close, $open), $close, $open), $low)))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9890 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0536 ic_ir_val=-0.4214 ic_win_rate_val=0.3333 ls_mean=-0.0020 mono_val=-1.0000 mt_score=0.3272 mt_bucket=low search_adjusted=0.7528
- **CP04 (risk)**: style_r2=0.1709 barra_residual_ic=-0.0304 alpha_survival=0.5672 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=1.0000 nearest=F002 exceeds_threshold=true
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.1425 train_val_sign_ok=true train_val_decay=1.3344

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0402 ic_ir_IS=-0.2766 ic_win_rate=0.3576
- **D1 年度IC**: 2015=-0.0270 2016=-0.0516 2017=-0.0489 2018=-0.0380 2019=-0.0347 2020=-0.0322 2021=-0.0476
- **D2 稳健性**: oos_decay_ratio=1.3344 ic_autocorr=-0.0378 ic_max_drawdown=-67.0174 worst_quarter=-0.0829 best_quarter=0.0232
- **D3 经济一致**: mono_IS=-0.9000 mono_OOS=-1.0000 ls_return=-0.0030 ls_tstat=-11.1998 sign_consistent=1
- **D3 分组IS**: q1=0.0021 q2=0.0013 q3=0.0001 q4=0.0003 q5=-0.0005
- **D4 衰减与换手**: factor_turnover=0.6163 factor_autocorr=0.3837
- **D5 分布**: coverage=1.0000 zero_ratio=0.0202 skew=0.0685 kurtosis=-1.2704 extreme_ratio=0.0000
- **D6 独特性**: max_lib_corr=1.0000 nearest=F002 expr_depth=8

### C003 — `Mul(Div(Sub(If(Lt($close, $open), $close, $open), $low), Sub($high, $low)), CsRank($amount))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9516 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0591 ic_ir_val=-0.6073 ic_win_rate_val=0.2831 ls_mean=-0.0023 mono_val=-0.9000 mt_score=0.3272 mt_bucket=low search_adjusted=0.7528
- **CP04 (risk)**: style_r2=0.2245 barra_residual_ic=-0.0347 alpha_survival=0.5866 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.6842 nearest=F001 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.1731 train_val_sign_ok=true train_val_decay=1.4669

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0403 ic_ir_IS=-0.4352 ic_win_rate=0.2995
- **D1 年度IC**: 2015=-0.0189 2016=-0.0469 2017=-0.0294 2018=-0.0557 2019=-0.0480 2020=-0.0388 2021=-0.0432
- **D2 稳健性**: oos_decay_ratio=1.4669 ic_autocorr=0.0687 ic_max_drawdown=-68.3050 worst_quarter=-0.0751 best_quarter=0.0047
- **D3 经济一致**: mono_IS=-0.9000 mono_OOS=-0.9000 ls_return=-0.0015 ls_tstat=-9.0083 sign_consistent=1
- **D3 分组IS**: q1=0.0012 q2=0.0008 q3=0.0002 q4=0.0003 q5=-0.0004
- **D4 衰减与换手**: factor_turnover=0.7239 factor_autocorr=0.2761
- **D5 分布**: coverage=1.0000 zero_ratio=0.0074 skew=1.3426 kurtosis=1.5838 extreme_ratio=0.0161
- **D6 独特性**: max_lib_corr=0.6842 nearest=F001 expr_depth=7

### C004 — `Cov(Div(Abs(Sub($close, $open)), Sub($high, $low)), Div($close, Ref($close, 1)), 20)` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9635 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0285 ic_ir_val=-0.2694 ic_win_rate_val=0.4091 ls_mean=-0.0007 mono_val=-0.3000 mt_score=0.3272 mt_bucket=low search_adjusted=0.7110
- **CP04 (risk)**: style_r2=0.4028 barra_residual_ic=-0.0021 alpha_survival=0.0722 crowding=high dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.0989 nearest=F001 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.1793 train_val_sign_ok=true train_val_decay=1.1519

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0248 ic_ir_IS=-0.2304 ic_win_rate=0.3840
- **D1 年度IC**: 2015=-0.0134 2016=-0.0367 2017=-0.0190 2018=-0.0321 2019=-0.0351 2020=-0.0151 2021=-0.0218
- **D2 稳健性**: oos_decay_ratio=1.1519 ic_autocorr=0.0162 ic_max_drawdown=-43.2172 worst_quarter=-0.0511 best_quarter=0.0051
- **D3 经济一致**: mono_IS=-0.1000 mono_OOS=-0.3000 ls_return=-0.0002 ls_tstat=-1.1007 sign_consistent=1
- **D3 分组IS**: q1=0.0004 q2=0.0006 q3=0.0006 q4=0.0006 q5=0.0001
- **D4 衰减与换手**: factor_turnover=0.0600 factor_autocorr=0.9400
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=0.5624 kurtosis=2.1585 extreme_ratio=0.0175
- **D6 独特性**: max_lib_corr=0.0989 nearest=F001 expr_depth=7

### C005 — `Sub(Mean(Div(Abs(Sub($close, $open)), Sub($high, $low)), 5), Mean(Div(Abs(Sub($close, $open)), Sub($high, $low)), 20))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9582 sign=1
- **CP03 (strength)**: ic_mean_val=0.0071 ic_ir_val=0.0980 ic_win_rate_val=0.5165 ls_mean=0.0006 mono_val=1.0000 mt_score=0.3272 mt_bucket=low search_adjusted=0.4086
- **CP04 (risk)**: style_r2=0.0234 barra_residual_ic=0.0042 alpha_survival=0.5988 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.1700 nearest=F002 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=medium split_sign_consistency=0.7500 split_dispersion=1.1101 train_val_sign_ok=true train_val_decay=1.0624

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=0.0067 ic_ir_IS=0.1069 ic_win_rate=0.5424
- **D1 年度IC**: 2015=0.0004 2016=0.0048 2017=0.0132 2018=0.0077 2019=0.0044 2020=0.0078 2021=0.0083
- **D2 稳健性**: oos_decay_ratio=1.0624 ic_autocorr=0.0716 ic_max_drawdown=-1.2352 worst_quarter=-0.0112 best_quarter=0.0266
- **D3 经济一致**: mono_IS=0.9000 mono_OOS=1.0000 ls_return=0.0005 ls_tstat=4.2254 sign_consistent=1
- **D3 分组IS**: q1=0.0002 q2=0.0005 q3=0.0007 q4=0.0007 q5=0.0007
- **D4 衰减与换手**: factor_turnover=0.2499 factor_autocorr=0.7501
- **D5 分布**: coverage=1.0000 zero_ratio=0.0021 skew=0.0257 kurtosis=0.2850 extreme_ratio=0.0037
- **D6 独特性**: max_lib_corr=0.1700 nearest=F002 expr_depth=11

### C006 — `Div(Mean(Div(Sub($high, $low), $close), 10), Mean(Div(Sub($high, $low), $close), 60))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9772 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0333 ic_ir_val=-0.2844 ic_win_rate_val=0.3719 ls_mean=-0.0006 mono_val=-0.1000 mt_score=0.3272 mt_bucket=low search_adjusted=0.6273
- **CP04 (risk)**: style_r2=0.3139 barra_residual_ic=-0.0137 alpha_survival=0.4122 crowding=high dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.1690 nearest=F002 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.2308 train_val_sign_ok=true train_val_decay=1.1894

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0280 ic_ir_IS=-0.2242 ic_win_rate=0.3723
- **D1 年度IC**: 2015=-0.0076 2016=-0.0297 2017=-0.0279 2018=-0.0306 2019=-0.0461 2020=-0.0272 2021=-0.0262
- **D2 稳健性**: oos_decay_ratio=1.1894 ic_autocorr=-0.0285 ic_max_drawdown=-48.4858 worst_quarter=-0.0495 best_quarter=0.0063
- **D3 经济一致**: mono_IS=0.0000 mono_OOS=-0.1000 ls_return=-0.0007 ls_tstat=-2.6740 sign_consistent=1
- **D3 分组IS**: q1=0.0006 q2=0.0008 q3=0.0008 q4=0.0009 q5=-0.0000
- **D4 衰减与换手**: factor_turnover=0.0367 factor_autocorr=0.9633
- **D5 分布**: coverage=1.0000 zero_ratio=0.0040 skew=0.5678 kurtosis=2.3151 extreme_ratio=0.0188
- **D6 独特性**: max_lib_corr=0.1690 nearest=F002 expr_depth=7

### C007 — `Div(Mean(Div(Sub($high, $low), $close), 20), Mean(Div(Sub($high, $low), $close), 120))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9845 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0318 ic_ir_val=-0.2400 ic_win_rate_val=0.3843 ls_mean=-0.0005 mono_val=-0.7000 mt_score=0.3272 mt_bucket=low search_adjusted=0.7528
- **CP04 (risk)**: style_r2=0.4071 barra_residual_ic=-0.0023 alpha_survival=0.0721 crowding=high dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.1773 nearest=F002 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.2765 train_val_sign_ok=true train_val_decay=1.3919

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0228 ic_ir_IS=-0.1675 ic_win_rate=0.4047
- **D1 年度IC**: 2015=0.0057 2016=-0.0203 2017=-0.0165 2018=-0.0250 2019=-0.0392 2020=-0.0314 2021=-0.0309
- **D2 稳健性**: oos_decay_ratio=1.3919 ic_autocorr=0.0053 ic_max_drawdown=-41.1396 worst_quarter=-0.0465 best_quarter=0.0208
- **D3 经济一致**: mono_IS=-0.1000 mono_OOS=-0.7000 ls_return=-0.0006 ls_tstat=-1.8365 sign_consistent=1
- **D3 分组IS**: q1=0.0006 q2=0.0007 q3=0.0009 q4=0.0009 q5=0.0000
- **D4 衰减与换手**: factor_turnover=0.0118 factor_autocorr=0.9882
- **D5 分布**: coverage=1.0000 zero_ratio=0.0081 skew=0.5486 kurtosis=2.1921 extreme_ratio=0.0160
- **D6 独特性**: max_lib_corr=0.1773 nearest=F002 expr_depth=7

### C008 — `CsRank(Div(Sub($high, If(Gt($close, $open), $close, $open)), Sub($high, $low)))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9516 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0008 ic_ir_val=-0.0097 ic_win_rate_val=0.4959 ls_mean=-0.0002 mono_val=-0.4000 mt_score=0.3272 mt_bucket=low search_adjusted=0.1930
- **CP04 (risk)**: style_r2=0.0275 barra_residual_ic=0.0068 alpha_survival=8.3674 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.4106 nearest=F002 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=low split_sign_consistency=0.7500 split_dispersion=7.5035 train_val_sign_ok=true train_val_decay=0.2334

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0035 ic_ir_IS=-0.0446 ic_win_rate=0.4756
- **D1 年度IC**: 2015=-0.0340 2016=0.0000 2017=0.0005 2018=0.0112 2019=0.0113 2020=-0.0075 2021=-0.0066
- **D2 稳健性**: oos_decay_ratio=0.2334 ic_autocorr=0.0231 ic_max_drawdown=-9.6521 worst_quarter=-0.0569 best_quarter=0.0289
- **D3 经济一致**: mono_IS=-0.4000 mono_OOS=-0.4000 ls_return=-0.0011 ls_tstat=-7.3153 sign_consistent=1
- **D3 分组IS**: q1=0.0011 q2=0.0001 q3=0.0004 q4=0.0004 q5=0.0002
- **D4 衰减与换手**: factor_turnover=0.9989 factor_autocorr=0.0011
- **D5 分布**: coverage=1.0000 zero_ratio=0.0019 skew=0.0132 kurtosis=-1.2220 extreme_ratio=0.0000
- **D6 独特性**: max_lib_corr=0.4106 nearest=F002 expr_depth=6

