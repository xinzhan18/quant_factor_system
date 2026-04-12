---
batch_id: batch_003
direction: candlestick_liquidity
n_candidates: 8
sample_policy_version: v3
mt_budget:
  cumulative_candidates: 16
  direction_candidates: 16
  validation_exposure: 2
  n_batches_scanned: 2
---

# Batch batch_003 — Judge Packet

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

### C001 — `Mul(Div(Sub(If(Lt($close, $open), $close, $open), $low), Sub($high, $low)), CsRank(Mul($pb_ratio, -1)))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9508 sign=1
- **CP03 (strength)**: ic_mean_val=0.0104 ic_ir_val=0.1013 ic_win_rate_val=0.5310 ls_mean=-0.0004 mono_val=-1.0000 mt_score=0.4254 mt_bucket=medium search_adjusted=0.4407
- **CP04 (risk)**: style_r2=0.2446 barra_residual_ic=-0.0161 alpha_survival=1.5524 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.5302 nearest=F003 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.6105 train_val_sign_ok=true train_val_decay=1.3832

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=0.0075 ic_ir_IS=0.0702 ic_win_rate=0.5065
- **D1 年度IC**: 2015=0.0243 2016=0.0211 2017=0.0091 2018=-0.0076 2019=-0.0008 2020=-0.0007 2021=0.0082
- **D2 稳健性**: oos_decay_ratio=1.3832 ic_autocorr=0.1071 ic_max_drawdown=-5.0944 worst_quarter=-0.0176 best_quarter=0.0436
- **D3 经济一致**: mono_IS=-0.5000 mono_OOS=-1.0000 ls_return=-0.0001 ls_tstat=-0.4427 sign_consistent=1
- **D3 分组IS**: q1=0.0007 q2=0.0004 q3=0.0002 q4=0.0005 q5=0.0004
- **D4 衰减与换手**: factor_turnover=0.6492 factor_autocorr=0.3508
- **D5 分布**: coverage=1.0000 zero_ratio=0.0074 skew=1.3142 kurtosis=1.4201 extreme_ratio=0.0148
- **D6 独特性**: max_lib_corr=0.5302 nearest=F003 expr_depth=8

### C002 — `Mul(Mul(Sub($high, If(Gt($close, $open), $close, $open)), Sub(If(Lt($close, $open), $close, $open), $low)), CsRank(Mul($pe_ratio, -1)))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9881 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0481 ic_ir_val=-0.4401 ic_win_rate_val=0.3333 ls_mean=-0.0018 mono_val=-1.0000 mt_score=0.4254 mt_bucket=medium search_adjusted=0.7086
- **CP04 (risk)**: style_r2=0.1569 barra_residual_ic=-0.0181 alpha_survival=0.3757 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.9455 nearest=F002 exceeds_threshold=true
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.1407 train_val_sign_ok=true train_val_decay=1.3512

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0356 ic_ir_IS=-0.2704 ic_win_rate=0.3576
- **D1 年度IC**: 2015=-0.0250 2016=-0.0450 2017=-0.0403 2018=-0.0319 2019=-0.0305 2020=-0.0308 2021=-0.0447
- **D2 稳健性**: oos_decay_ratio=1.3512 ic_autocorr=-0.0481 ic_max_drawdown=-59.3231 worst_quarter=-0.0760 best_quarter=0.0189
- **D3 经济一致**: mono_IS=-0.9000 mono_OOS=-1.0000 ls_return=-0.0029 ls_tstat=-11.5664 sign_consistent=1
- **D3 分组IS**: q1=0.0021 q2=0.0012 q3=0.0000 q4=0.0002 q5=-0.0002
- **D4 衰减与换手**: factor_turnover=0.6243 factor_autocorr=0.3757
- **D5 分布**: coverage=1.0000 zero_ratio=0.0200 skew=0.8254 kurtosis=-0.9698 extreme_ratio=0.0000
- **D6 独特性**: max_lib_corr=0.9455 nearest=F002 expr_depth=10

### C003 — `TsRank(Mul(Sub($high, If(Gt($close, $open), $close, $open)), Sub(If(Lt($close, $open), $close, $open), $low)), 20)` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9887 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0299 ic_ir_val=-0.4989 ic_win_rate_val=0.3064 ls_mean=-0.0015 mono_val=-0.9000 mt_score=0.4254 mt_bucket=medium search_adjusted=0.7086
- **CP04 (risk)**: style_r2=0.0242 barra_residual_ic=-0.0282 alpha_survival=0.9426 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.7428 nearest=F002 exceeds_threshold=true
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.1470 train_val_sign_ok=true train_val_decay=0.9246

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0324 ic_ir_IS=-0.3067 ic_win_rate=0.3046
- **D1 年度IC**: 2015=-0.0192 2016=-0.0395 2017=-0.0404 2018=-0.0309 2019=-0.0308 2020=-0.0310 2021=-0.0333
- **D2 稳健性**: oos_decay_ratio=0.9246 ic_autocorr=-0.0876 ic_max_drawdown=-53.7717 worst_quarter=-0.0632 best_quarter=0.0243
- **D3 经济一致**: mono_IS=-0.9000 mono_OOS=-0.9000 ls_return=-0.0027 ls_tstat=-12.9360 sign_consistent=1
- **D3 分组IS**: q1=0.0019 q2=0.0010 q3=0.0001 q4=0.0005 q5=-0.0004
- **D4 衰减与换手**: factor_turnover=0.8588 factor_autocorr=0.1412
- **D5 分布**: coverage=1.0000 zero_ratio=0.0209 skew=-0.0214 kurtosis=-1.1613 extreme_ratio=0.0000
- **D6 独特性**: max_lib_corr=0.7428 nearest=F002 expr_depth=8

### C004 — `TsRank(Div(Sub(If(Lt($close, $open), $close, $open), $low), Sub($high, $low)), 20)` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9641 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0236 ic_ir_val=-0.2946 ic_win_rate_val=0.3595 ls_mean=-0.0014 mono_val=-0.9000 mt_score=0.4254 mt_bucket=medium search_adjusted=0.7086
- **CP04 (risk)**: style_r2=0.0258 barra_residual_ic=-0.0170 alpha_survival=0.7227 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.7079 nearest=F003 exceeds_threshold=true
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.2691 train_val_sign_ok=true train_val_decay=5.5770

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0042 ic_ir_IS=-0.0499 ic_win_rate=0.4363
- **D1 年度IC**: 2015=0.0300 2016=0.0127 2017=-0.0049 2018=-0.0203 2019=-0.0152 2020=-0.0129 2021=-0.0163
- **D2 稳健性**: oos_decay_ratio=5.5770 ic_autocorr=-0.0684 ic_max_drawdown=-17.5025 worst_quarter=-0.0412 best_quarter=0.0389
- **D3 经济一致**: mono_IS=-0.7000 mono_OOS=-0.9000 ls_return=-0.0005 ls_tstat=-3.0208 sign_consistent=1
- **D3 分组IS**: q1=0.0010 q2=0.0005 q3=0.0002 q4=0.0004 q5=0.0003
- **D4 衰减与换手**: factor_turnover=0.9483 factor_autocorr=0.0517
- **D5 分布**: coverage=1.0000 zero_ratio=0.0108 skew=-0.0589 kurtosis=-0.7957 extreme_ratio=0.0004
- **D6 独特性**: max_lib_corr=0.7079 nearest=F003 expr_depth=6

### C005 — `Mul(Div(Sub(If(Lt($close, $open), $close, $open), $low), Sub($high, $low)), Div($turnover_rate, Mean($turnover_rate, 20)))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9516 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0357 ic_ir_val=-0.4094 ic_win_rate_val=0.3326 ls_mean=-0.0018 mono_val=-0.9000 mt_score=0.4254 mt_bucket=medium search_adjusted=0.7086
- **CP04 (risk)**: style_r2=0.0497 barra_residual_ic=-0.0399 alpha_survival=1.1176 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.7443 nearest=F003 exceeds_threshold=true
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.1723 train_val_sign_ok=true train_val_decay=1.2554

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0284 ic_ir_IS=-0.3319 ic_win_rate=0.3280
- **D1 年度IC**: 2015=0.0073 2016=-0.0247 2017=-0.0288 2018=-0.0510 2019=-0.0451 2020=-0.0287 2021=-0.0263
- **D2 稳健性**: oos_decay_ratio=1.2554 ic_autocorr=0.0580 ic_max_drawdown=-50.4429 worst_quarter=-0.0717 best_quarter=0.0224
- **D3 经济一致**: mono_IS=-0.9000 mono_OOS=-0.9000 ls_return=-0.0010 ls_tstat=-7.1232 sign_consistent=1
- **D3 分组IS**: q1=0.0009 q2=0.0007 q3=0.0003 q4=0.0006 q5=-0.0004
- **D4 衰减与换手**: factor_turnover=0.8949 factor_autocorr=0.1051
- **D5 分布**: coverage=1.0000 zero_ratio=0.0074 skew=1.4180 kurtosis=2.4380 extreme_ratio=0.0203
- **D6 独特性**: max_lib_corr=0.7443 nearest=F003 expr_depth=8

### C006 — `Mul(Std(Div(Abs(Sub($close, $open)), Sub($high, $low)), 20), CsRank(Mul($pb_ratio, -1)))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9630 sign=1
- **CP03 (strength)**: ic_mean_val=0.0420 ic_ir_val=0.2873 ic_win_rate_val=0.6095 ls_mean=0.0009 mono_val=0.9000 mt_score=0.4254 mt_bucket=medium search_adjusted=0.7086
- **CP04 (risk)**: style_r2=0.6820 barra_residual_ic=0.0105 alpha_survival=0.2507 crowding=high dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.3431 nearest=F002 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.0880 train_val_sign_ok=true train_val_decay=1.8580

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=0.0226 ic_ir_IS=0.1720 ic_win_rate=0.5593
- **D1 年度IC**: 2015=0.0172 2016=0.0356 2017=0.0273 2018=0.0197 2019=0.0178 2020=0.0084 2021=0.0324
- **D2 稳健性**: oos_decay_ratio=1.8580 ic_autocorr=0.0964 ic_max_drawdown=-1.9006 worst_quarter=-0.0270 best_quarter=0.0572
- **D3 经济一致**: mono_IS=0.9000 mono_OOS=0.9000 ls_return=0.0005 ls_tstat=2.0354 sign_consistent=1
- **D3 分组IS**: q1=0.0001 q2=0.0004 q3=0.0006 q4=0.0006 q5=0.0006
- **D4 衰减与换手**: factor_turnover=0.0048 factor_autocorr=0.9952
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=0.1557 kurtosis=-0.9133 extreme_ratio=0.0004
- **D6 独特性**: max_lib_corr=0.3431 nearest=F002 expr_depth=8

### C007 — `Mul(Mul(Sub($high, If(Gt($close, $open), $close, $open)), Sub(If(Lt($close, $open), $close, $open), $low)), Mul(Div($close, Ref($close, 5)), -1))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9858 sign=1
- **CP03 (strength)**: ic_mean_val=0.0521 ic_ir_val=0.4189 ic_win_rate_val=0.6667 ls_mean=0.0018 mono_val=1.0000 mt_score=0.4254 mt_bucket=medium search_adjusted=0.7086
- **CP04 (risk)**: style_r2=0.2076 barra_residual_ic=0.0238 alpha_survival=0.4558 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.9944 nearest=F002 exceeds_threshold=true
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.1441 train_val_sign_ok=true train_val_decay=1.3801

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=0.0378 ic_ir_IS=0.2627 ic_win_rate=0.6386
- **D1 年度IC**: 2015=0.0231 2016=0.0474 2017=0.0430 2018=0.0371 2019=0.0339 2020=0.0314 2021=0.0469
- **D2 稳健性**: oos_decay_ratio=1.3801 ic_autocorr=-0.0381 ic_max_drawdown=-3.7050 worst_quarter=-0.0228 best_quarter=0.0763
- **D3 经济一致**: mono_IS=1.0000 mono_OOS=1.0000 ls_return=0.0026 ls_tstat=9.8329 sign_consistent=1
- **D3 分组IS**: q1=-0.0003 q2=0.0001 q3=0.0002 q4=0.0012 q5=0.0017
- **D4 衰减与换手**: factor_turnover=0.6281 factor_autocorr=0.3719
- **D5 分布**: coverage=1.0000 zero_ratio=0.0196 skew=-0.8255 kurtosis=-0.9712 extreme_ratio=0.0000
- **D6 独特性**: max_lib_corr=0.9944 nearest=F002 expr_depth=11

### C008 — `Mul(Div(Sub($high, If(Gt($close, $open), $close, $open)), $close), Mul(Div($close, Ref($close, 5)), -1))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9858 sign=1
- **CP03 (strength)**: ic_mean_val=0.0384 ic_ir_val=0.4181 ic_win_rate_val=0.6612 ls_mean=0.0013 mono_val=0.9000 mt_score=0.4254 mt_bucket=medium search_adjusted=0.7086
- **CP04 (risk)**: style_r2=0.1269 barra_residual_ic=0.0118 alpha_survival=0.3080 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.6066 nearest=F002 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.2048 train_val_sign_ok=true train_val_decay=1.1847

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=0.0324 ic_ir_IS=0.2268 ic_win_rate=0.6462
- **D1 年度IC**: 2015=0.0256 2016=0.0364 2017=0.0375 2018=0.0190 2019=0.0294 2020=0.0373 2021=0.0413
- **D2 稳健性**: oos_decay_ratio=1.1847 ic_autocorr=-0.0396 ic_max_drawdown=-3.2671 worst_quarter=0.0008 best_quarter=0.0682
- **D3 经济一致**: mono_IS=0.7000 mono_OOS=0.9000 ls_return=0.0024 ls_tstat=8.0877 sign_consistent=1
- **D3 分组IS**: q1=-0.0005 q2=0.0005 q3=0.0007 q4=0.0003 q5=0.0019
- **D4 衰减与换手**: factor_turnover=0.7556 factor_autocorr=0.2444
- **D5 分布**: coverage=1.0000 zero_ratio=0.0049 skew=-1.5328 kurtosis=2.3971 extreme_ratio=0.0246
- **D6 独特性**: max_lib_corr=0.6066 nearest=F002 expr_depth=8

