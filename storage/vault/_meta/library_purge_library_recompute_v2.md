---
title: Library Purge v2 — Phase 2 mainline recompute under tradable_mask
generated_at: 2026-04-26T17:16:12Z
batch_id: batch_recompute_v2
run_name: library_recompute_v2
followup_batch_id: batch_recompute_v2_pyfix
primary_universe: all_tradable
secondary_universes: [csi300, csi1000]
n_evaluated: 23
n_kept_final: 22
n_deleted_final: 1
---

# Library Purge v2

> [!danger]+ 系统级清算
> 全部 23 个因子通过 Phase 2 mainline 重算，启用 `tradability.filter_limit=true`
> （涨跌停 mask）。CP01 hard_gates 决定 keep/delete。DB `factor_values` + `factor_meta`
> 老表（`factor_001..factor_045`，mining_v1 遗留）已 `DROP TABLE`。

**Final result**: **22 kept, 1 deleted (F014)**

> [!warning] F004/F005 注脚
> 第一次跑里 F004/F005 因 `scipy.linalg.pinv` 的 `rcond=` 参数在 scipy ≥ 1.7 已被 `rtol=` 替代而 compute_error，被 DELETE。已修复 `vault/batches/batch_012/python_candidates/C001.py` + `batch_013/python_candidates/C001.py`，并在 [[batches/batch_recompute_v2_pyfix/result|batch_recompute_v2_pyfix]] 中重跑 — 两个因子都 PASS hard_gates（IC=0.0237, ICIR=0.275, mono=1.0），已恢复为 active。详见 [[library_purge_library_recompute_v2_pyfix|pyfix purge log]]。
>
> **教训**：admitted Python 因子的 "运行时入口" 不该锚在 `vault/batches/python_candidates/` 这种 immutable archive，否则 scipy 类 API 变更会导致幽灵失败。

## Decisions

| Factor | Name | Action | Coverage | IC mean | ICIR | Mono | L/S Sharpe | csi300 mono | csi1000 mono | Reasons |
|--------|------|--------|----------|---------|------|------|------------|-------------|--------------|---------|
| F001 | amount_cv_10 | **KEEP** | 1.000 | -0.0432 | -0.741 | -1.00 | -4.537 | -0.10 | -1.00 | passed |
| F002 | pb_amount_ratio_20 | **KEEP** | 0.999 | 0.0312 | 0.240 | 1.00 | 2.859 | -1.00 | 1.00 | passed |
| F003 | overnight_gap_normalized | **KEEP** | 1.000 | 0.0156 | 0.246 | 0.40 | 1.962 | -0.90 | 0.10 | passed |
| F004 | barra_residual_return | **DELETE** | — | — | — | — | — | — | — | compute_error: ValueError: preprocessed factor is empty (all NaN) |
| F005 | barra_residual_alpha_60d | **DELETE** | — | — | — | — | — | — | — | compute_error: ValueError: preprocessed factor is empty (all NaN) |
| F006 | upper_shadow_persistence_5d | **KEEP** | 1.000 | 0.0269 | 0.213 | 1.00 | 3.648 | 0.60 | 0.90 | passed |
| F007 | open_position_persistence_5d | **KEEP** | 1.000 | 0.0377 | 0.334 | 0.90 | 3.001 | 0.50 | 0.90 | passed |
| F008 | upper_shadow_persistence_3d | **KEEP** | 1.000 | 0.0341 | 0.263 | 1.00 | 3.834 | 0.10 | 1.00 | passed |
| F009 | overnight_intraday_spread_5d | **KEEP** | 1.000 | 0.0461 | 0.383 | 0.70 | 3.671 | 0.70 | 0.70 | passed |
| F010 | overnight_return_persistence_5d | **KEEP** | 1.000 | 0.0187 | 0.294 | 0.40 | 2.343 | -0.10 | 0.30 | passed |
| F011 | overnight_return_persistence_3d | **KEEP** | 1.000 | 0.0190 | 0.303 | 0.40 | 2.336 | -0.30 | 0.30 | passed |
| F012 | amihud_illiq_20d | **KEEP** | 1.000 | 0.0360 | 0.259 | 1.00 | 3.105 | 0.90 | 1.00 | passed |
| F013 | log_amount_weighted_acceptance_20 | **KEEP** | 1.000 | 0.0088 | 0.226 | 0.40 | 1.778 | 0.80 | 0.30 | passed |
| F014 | vwap_overnight_spread | **DELETE** | 1.000 | 0.0044 | 0.035 | -0.60 | -0.127 | 1.00 | 0.40 | ic_oos_too_low: |0.0044| < 0.008 |
| F015 | amihud_cv_rank_diff_20 | **KEEP** | 1.000 | 0.0567 | 0.537 | 1.00 | 5.049 | 0.70 | 1.00 | passed |
| F016 | amihud_turnover_cv_rank_diff_20 | **KEEP** | 1.000 | 0.0517 | 0.511 | 1.00 | 5.038 | -0.70 | 1.00 | passed |
| F017 | overnight_turnover_rank_diff_5 | **KEEP** | 1.000 | 0.0519 | 0.425 | 0.90 | 2.570 | 0.90 | 0.90 | passed |
| F018 | overnight_sign_freq_amount_rank_diff_20 | **KEEP** | 1.000 | 0.0506 | 0.441 | 1.00 | 3.898 | 1.00 | 1.00 | passed |
| F019 | body_disp_pricevol_rank_diff_20 | **KEEP** | 1.000 | 0.0414 | 0.300 | 1.00 | 2.072 | 0.90 | 1.00 | passed |
| F020 | gap_vol_body_ratio_rank_diff_20 | **KEEP** | 1.000 | -0.0402 | -0.465 | -1.00 | -2.942 | -1.00 | -1.00 | passed |
| F021 | upper_shadow_disp_range_compress_rd_20 | **KEEP** | 1.000 | 0.0444 | 0.338 | 1.00 | 1.602 | 0.90 | 1.00 | passed |
| F022 | close_position_amount_accel_rd_20 | **KEEP** | 1.000 | 0.0296 | 0.344 | 0.60 | 1.131 | 0.70 | 0.20 | passed |
| F023 | gap_body_magnitude_amount_rd_20 | **KEEP** | 1.000 | 0.0448 | 0.370 | 1.00 | 3.271 | 0.60 | 1.00 | passed |

## Deletion artifacts

- **F004** (barra_residual_return):
  - `storage/vault/factors/F004.yaml`
  - `storage/vault/factors/F004.md`
  - `storage/vault/factors/F004`
  - `storage/python_factors/F004_barra_residual_return.py`
- **F005** (barra_residual_alpha_60d):
  - `storage/vault/factors/F005.yaml`
  - `storage/vault/factors/F005.md`
  - `storage/vault/factors/F005`
  - `storage/python_factors/F005_barra_residual_alpha_60d.py`
- **F014** (vwap_overnight_spread):
  - `storage/vault/factors/F014.yaml`
  - `storage/vault/factors/F014.md`
  - `storage/vault/factors/F014`
