---
batch_id: batch_004
direction: candlestick_liquidity
n_candidates: 8
sample_policy_version: v3
mt_budget:
  cumulative_candidates: 24
  direction_candidates: 24
  validation_exposure: 3
  n_batches_scanned: 3
---

# Batch batch_004 — Judge Packet

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

### C001 — `Mul(Div(Sub($high, If(Gt($close, $open), $close, $open)), $close), Mul(Div($close, Ref($close, 10)), -1))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9827 sign=1
- **CP03 (strength)**: ic_mean_val=0.0387 ic_ir_val=0.4216 ic_win_rate_val=0.6570 ls_mean=0.0013 mono_val=1.0000 mt_score=0.4870 mt_bucket=medium search_adjusted=0.6809
- **CP04 (risk)**: style_r2=0.1363 barra_residual_ic=0.0117 alpha_survival=0.3028 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.9984 nearest=F004 exceeds_threshold=true
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.2137 train_val_sign_ok=true train_val_decay=1.2361

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=0.0313 ic_ir_IS=0.2197 ic_win_rate=0.6386
- **D1 年度IC**: 2015=0.0250 2016=0.0344 2017=0.0334 2018=0.0183 2019=0.0294 2020=0.0368 2021=0.0413
- **D2 稳健性**: oos_decay_ratio=1.2361 ic_autocorr=-0.0390 ic_max_drawdown=-3.2698 worst_quarter=-0.0002 best_quarter=0.0628
- **D3 经济一致**: mono_IS=0.7000 mono_OOS=1.0000 ls_return=0.0021 ls_tstat=7.0407 sign_consistent=1
- **D3 分组IS**: q1=-0.0005 q2=0.0005 q3=0.0007 q4=0.0003 q5=0.0016
- **D4 衰减与换手**: factor_turnover=0.7512 factor_autocorr=0.2488
- **D5 分布**: coverage=1.0000 zero_ratio=0.0049 skew=-1.5464 kurtosis=2.4068 extreme_ratio=0.0250
- **D6 独特性**: max_lib_corr=0.9984 nearest=F004 expr_depth=8

### C002 — `Mul(Div(Sub($high, If(Gt($close, $open), $close, $open)), $close), Mul(Div($close, Ref($close, 20)), -1))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9765 sign=1
- **CP03 (strength)**: ic_mean_val=0.0392 ic_ir_val=0.4233 ic_win_rate_val=0.6632 ls_mean=0.0013 mono_val=0.9000 mt_score=0.4870 mt_bucket=medium search_adjusted=0.6809
- **CP04 (risk)**: style_r2=0.1634 barra_residual_ic=0.0108 alpha_survival=0.2762 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.9956 nearest=F004 exceeds_threshold=true
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.1918 train_val_sign_ok=true train_val_decay=1.2690

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=0.0309 ic_ir_IS=0.2179 ic_win_rate=0.6352
- **D1 年度IC**: 2015=0.0253 2016=0.0325 2017=0.0312 2018=0.0190 2019=0.0302 2020=0.0364 2021=0.0413
- **D2 稳健性**: oos_decay_ratio=1.2690 ic_autocorr=-0.0476 ic_max_drawdown=-3.2155 worst_quarter=-0.0017 best_quarter=0.0596
- **D3 经济一致**: mono_IS=0.7000 mono_OOS=0.9000 ls_return=0.0019 ls_tstat=6.4722 sign_consistent=1
- **D3 分组IS**: q1=-0.0006 q2=0.0004 q3=0.0007 q4=0.0003 q5=0.0014
- **D4 衰减与换手**: factor_turnover=0.7447 factor_autocorr=0.2553
- **D5 分布**: coverage=1.0000 zero_ratio=0.0049 skew=-1.5589 kurtosis=2.3974 extreme_ratio=0.0254
- **D6 独特性**: max_lib_corr=0.9956 nearest=F004 expr_depth=8

### C003 — `Mul(Div(Sub(If(Lt($close, $open), $close, $open), $low), $close), Mul(Div($close, Ref($close, 5)), -1))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9858 sign=1
- **CP03 (strength)**: ic_mean_val=0.0582 ic_ir_val=0.6355 ic_win_rate_val=0.7686 ls_mean=0.0021 mono_val=0.9000 mt_score=0.4870 mt_bucket=medium search_adjusted=0.6809
- **CP04 (risk)**: style_r2=0.1154 barra_residual_ic=0.0401 alpha_survival=0.6892 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.7709 nearest=F003 exceeds_threshold=true
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.1373 train_val_sign_ok=true train_val_decay=1.4515

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=0.0401 ic_ir_IS=0.3121 ic_win_rate=0.6997
- **D1 年度IC**: 2015=-0.0075 2016=0.0368 2017=0.0447 2018=0.0538 2019=0.0548 2020=0.0469 2021=0.0464
- **D2 稳健性**: oos_decay_ratio=1.4515 ic_autocorr=-0.0854 ic_max_drawdown=-4.1194 worst_quarter=-0.0351 best_quarter=0.0778
- **D3 经济一致**: mono_IS=0.9000 mono_OOS=0.9000 ls_return=0.0020 ls_tstat=7.6293 sign_consistent=1
- **D3 分组IS**: q1=-0.0004 q2=0.0007 q3=0.0002 q4=0.0008 q5=0.0015
- **D4 衰减与换手**: factor_turnover=0.7952 factor_autocorr=0.2048
- **D5 分布**: coverage=1.0000 zero_ratio=0.0121 skew=-1.4289 kurtosis=2.4312 extreme_ratio=0.0207
- **D6 独特性**: max_lib_corr=0.7709 nearest=F003 expr_depth=8

### C004 — `Mul(Div(Sub($high, $close), $close), Mul(Div($close, Ref($close, 5)), -1))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9858 sign=1
- **CP03 (strength)**: ic_mean_val=0.0210 ic_ir_val=0.1655 ic_win_rate_val=0.5847 ls_mean=0.0006 mono_val=0.1000 mt_score=0.4870 mt_bucket=medium search_adjusted=0.5282
- **CP04 (risk)**: style_r2=0.1818 barra_residual_ic=-0.0090 alpha_survival=0.4278 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.5993 nearest=F004 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.6273 train_val_sign_ok=true train_val_decay=1.0082

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=0.0208 ic_ir_IS=0.1178 ic_win_rate=0.5895
- **D1 年度IC**: 2015=0.0372 2016=0.0224 2017=0.0248 2018=0.0034 2019=0.0093 2020=0.0291 2021=0.0200
- **D2 稳健性**: oos_decay_ratio=1.0082 ic_autocorr=-0.1084 ic_max_drawdown=-3.4862 worst_quarter=-0.0025 best_quarter=0.0998
- **D3 经济一致**: mono_IS=0.7000 mono_OOS=0.1000 ls_return=0.0027 ls_tstat=7.4060 sign_consistent=1
- **D3 分组IS**: q1=-0.0006 q2=0.0005 q3=0.0008 q4=0.0003 q5=0.0019
- **D4 衰减与换手**: factor_turnover=0.7091 factor_autocorr=0.2909
- **D5 分布**: coverage=1.0000 zero_ratio=0.0035 skew=-1.3195 kurtosis=2.0948 extreme_ratio=0.0203
- **D6 独特性**: max_lib_corr=0.5993 nearest=F004 expr_depth=6

### C005 — `Mul(CsRank(Div(Sub($high, If(Gt($close, $open), $close, $open)), $close)), CsRank(Mul(Div($close, Ref($close, 5)), -1)))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9858 sign=1
- **CP03 (strength)**: ic_mean_val=0.0209 ic_ir_val=0.1735 ic_win_rate_val=0.5723 ls_mean=0.0008 mono_val=0.9000 mt_score=0.4870 mt_bucket=medium search_adjusted=0.6508
- **CP04 (risk)**: style_r2=0.1271 barra_residual_ic=0.0345 alpha_survival=1.6521 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.5213 nearest=F004 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.3606 train_val_sign_ok=true train_val_decay=0.6814

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=0.0306 ic_ir_IS=0.1918 ic_win_rate=0.5894
- **D1 年度IC**: 2015=0.0238 2016=0.0406 2017=0.0278 2018=0.0495 2019=0.0437 2020=0.0125 2021=0.0159
- **D2 稳健性**: oos_decay_ratio=0.6814 ic_autocorr=0.0228 ic_max_drawdown=-5.9712 worst_quarter=-0.0327 best_quarter=0.0846
- **D3 经济一致**: mono_IS=-0.1000 mono_OOS=0.9000 ls_return=-0.0009 ls_tstat=-2.8116 sign_consistent=1
- **D3 分组IS**: q1=0.0013 q2=-0.0001 q3=0.0004 q4=0.0008 q5=0.0006
- **D4 衰减与换手**: factor_turnover=0.5239 factor_autocorr=0.4761
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=1.1178 kurtosis=0.6551 extreme_ratio=0.0084
- **D6 独特性**: max_lib_corr=0.5213 nearest=F004 expr_depth=10

### C006 — `Mul(Div(Sub($high, If(Gt($close, $open), $close, $open)), $close), Div($volume, Mean($volume, 20)))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9676 sign=-1
- **CP03 (strength)**: ic_mean_val=-0.0444 ic_ir_val=-0.5382 ic_win_rate_val=0.3037 ls_mean=-0.0017 mono_val=-0.9000 mt_score=0.4870 mt_bucket=medium search_adjusted=0.6809
- **CP04 (risk)**: style_r2=0.1009 barra_residual_ic=-0.0249 alpha_survival=0.5598 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.9456 nearest=F004 exceeds_threshold=true
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.2112 train_val_sign_ok=true train_val_decay=0.8872

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=-0.0501 ic_ir_IS=-0.4820 ic_win_rate=0.2720
- **D1 年度IC**: 2015=-0.0636 2016=-0.0629 2017=-0.0562 2018=-0.0324 2019=-0.0427 2020=-0.0467 2021=-0.0463
- **D2 稳健性**: oos_decay_ratio=0.8872 ic_autocorr=-0.0492 ic_max_drawdown=-84.8425 worst_quarter=-0.0947 best_quarter=-0.0243
- **D3 经济一致**: mono_IS=-0.7000 mono_OOS=-0.9000 ls_return=-0.0036 ls_tstat=-16.2268 sign_consistent=1
- **D3 分组IS**: q1=0.0026 q2=0.0004 q3=0.0008 q4=0.0005 q5=-0.0009
- **D4 衰减与换手**: factor_turnover=0.7626 factor_autocorr=0.2374
- **D5 分布**: coverage=1.0000 zero_ratio=0.0046 skew=1.5151 kurtosis=1.4869 extreme_ratio=0.0049
- **D6 独特性**: max_lib_corr=0.9456 nearest=F004 expr_depth=7

### C007 — `Mul(IdxMax(Div(Sub($high, If(Gt($close, $open), $close, $open)), $close), 20), Mul(Div($close, Ref($close, 5)), -1))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9858 sign=1
- **CP03 (strength)**: ic_mean_val=0.0210 ic_ir_val=0.3860 ic_win_rate_val=0.6591 ls_mean=0.0003 mono_val=0.7000 mt_score=0.4870 mt_bucket=medium search_adjusted=0.6809
- **CP04 (risk)**: style_r2=0.0519 barra_residual_ic=0.0167 alpha_survival=0.7924 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.2326 nearest=F004 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=high split_sign_consistency=1.0000 split_dispersion=0.1158 train_val_sign_ok=true train_val_decay=1.0955

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=0.0192 ic_ir_IS=0.1968 ic_win_rate=0.6418
- **D1 年度IC**: 2015=-0.0063 2016=0.0250 2017=0.0297 2018=0.0204 2019=0.0313 2020=0.0190 2021=0.0147
- **D2 稳健性**: oos_decay_ratio=1.0955 ic_autocorr=-0.0317 ic_max_drawdown=-4.1355 worst_quarter=-0.0404 best_quarter=0.0399
- **D3 经济一致**: mono_IS=0.6000 mono_OOS=0.7000 ls_return=0.0010 ls_tstat=4.2300 sign_consistent=1
- **D3 分组IS**: q1=0.0001 q2=0.0006 q3=0.0006 q4=0.0006 q5=0.0010
- **D4 衰减与换手**: factor_turnover=0.1664 factor_autocorr=0.8336
- **D5 分布**: coverage=1.0000 zero_ratio=0.0000 skew=-0.1517 kurtosis=-0.9792 extreme_ratio=0.0002
- **D6 独特性**: max_lib_corr=0.2326 nearest=F004 expr_depth=9

### C008 — `Sub(Div(Sub($high, If(Gt($close, $open), $close, $open)), $close), Div(Sub(If(Lt($close, $open), $close, $open), $low), $close))` (dsl)

**Hard Gate (CP01)**: `all_pass`

**Numeric hints**:
- **CP01 (context)**: coverage=0.9890 sign=1
- **CP03 (strength)**: ic_mean_val=0.0056 ic_ir_val=0.0617 ic_win_rate_val=0.5393 ls_mean=0.0006 mono_val=0.3000 mt_score=0.4870 mt_bucket=medium search_adjusted=0.2686
- **CP04 (risk)**: style_r2=0.0315 barra_residual_ic=0.0139 alpha_survival=2.4731 crowding=medium dominant_style=vol_20d
- **CP05 (redundancy)**: max_lib_corr=0.6658 nearest=F004 exceeds_threshold=false
- **CP06 (stability)**: split_bucket=low split_sign_consistency=0.5000 split_dispersion=1.3028 train_val_sign_ok=true train_val_decay=3.3206

**6 维评估 (report_card)**:
- **D1 预测力**: ic_mean_IS=0.0017 ic_ir_IS=0.0168 ic_win_rate=0.5118
- **D1 年度IC**: 2015=-0.0260 2016=0.0032 2017=0.0010 2018=0.0193 2019=0.0115 2020=0.0049 2021=-0.0024
- **D2 稳健性**: oos_decay_ratio=3.3206 ic_autocorr=0.0026 ic_max_drawdown=-6.9427 worst_quarter=-0.0485 best_quarter=0.0308
- **D3 经济一致**: mono_IS=-0.3000 mono_OOS=0.3000 ls_return=-0.0004 ls_tstat=-2.3675 sign_consistent=1
- **D3 分组IS**: q1=0.0001 q2=0.0009 q3=0.0015 q4=0.0009 q5=-0.0002
- **D4 衰减与换手**: factor_turnover=0.9847 factor_autocorr=0.0153
- **D5 分布**: coverage=1.0000 zero_ratio=0.0025 skew=0.4190 kurtosis=2.1189 extreme_ratio=0.0196
- **D6 独特性**: max_lib_corr=0.6658 nearest=F004 expr_depth=9

