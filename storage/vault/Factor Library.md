---
title: Factor Library
tags:
  - index
---

# Factor Library

> 26 factors | Last updated: 2026-03-29

## 汇总表

| ID | Name | Category | IC (OOS) | ICIR | Grade | Score | Mono | L/S Sharpe | Link |
|----|------|----------|----------|------|-------|-------|------|------------|------|
| 001 | std_returns_20 | volatility | -0.0612 | -0.17 | B | 74.8 | -0.9 | 1.01 | [[F001 std_returns_20]] |
| 002 | delta_volume_5 | volume | -0.0471 | -0.41 | B | 71.0 | -0.9 | 4.53 | [[F002 delta_volume_5]] |
| 003 | vol_regime_reversal | regime | -0.0384 | -0.27 | B | 66.3 | -0.4 | 1.30 | [[F003 vol_regime_reversal]] |
| 004 | std_volume_20 | volume | -0.0453 | -0.38 | B+ | 79.2 | -1.0 | 3.32 | [[F004 std_volume_20]] |
| 005 | upper_shadow_ratio | candlestick | +0.0190 | +0.25 | B | 66.2 | -0.6 | 1.73 | [[F005 upper_shadow_ratio]] |
| 006 | resi_close_5 | trend | -0.0097 | -0.10 | C+ | 58.5 | +0.3 | -1.65 | [[F006 resi_close_5]] |
| 007 | vol_regime_resi_vs_slope | regime | -0.0150 | -0.11 | C+ | 55.0 | +0.3 | -1.40 | [[F007 vol_regime_resi_vs_slope]] |
| 008 | ret_vol_cov_20 | volume | -0.0543 | -0.39 | B+ | 79.4 | -0.7 | 3.28 | [[F008 ret_vol_cov_20]] |
| 009 | pv_corr_times_vol | volume | -0.0692 | -0.52 | A- | 83.6 | -0.9 | 4.91 | [[F009 pv_corr_times_vol]] |
| 010 | hhi_volume_20 | volume | -0.0414 | -0.44 | A- | 85.2 | -1.0 | 3.55 | [[F010 hhi_volume_20]] |
| 011 | williams_r_variant | candlestick | +0.0815 | +0.56 | B | 71.9 | +0.9 | -4.55 | [[F011 williams_r_variant]] |
| 012 | up_day_count_20 | momentum | +0.0136 | +0.09 | C+ | 57.5 | 0.0 | 0.00 | [[F012 up_day_count_20]] |
| 013 | alpha038 | candlestick | +0.0368 | +0.25 | C | 48.4 | 0.0 | -0.26 | [[F013 alpha038]] |
| 014 | alpha023 | momentum | +0.0305 | +0.20 | C | 52.4 | +0.3 | -0.83 | [[F014 alpha023]] |
| 015 | alpha053 | candlestick | +0.0334 | +0.15 | C | 45.4 | 0.0 | 0.00 | [[F015 alpha053]] |
| 016 | alpha010 | momentum | +0.0105 | +0.13 | C- | 38.0 | 0.0 | 0.59 | [[F016 alpha010]] |
| 017 | alpha034 | volatility | +0.0133 | +0.17 | C | 46.5 | -0.1 | 0.19 | [[F017 alpha034]] |
| 018 | alpha017 | momentum | +0.0228 | +0.15 | C | 50.8 | -0.1 | 1.49 | [[F018 alpha017]] |
| 019 | rank_ret_times_rank_vol | volume | -0.0443 | -0.33 | B- | 64.1 | -0.6 | 1.64 | [[F019 rank_ret_times_rank_vol]] |
| 020 | intraday_vs_overnight | momentum | -0.0401 | -0.43 | B+ | 76.4 | -1.0 | 5.15 | [[F020 intraday_vs_overnight]] |
| 021 | alpha024 | momentum | +0.0563 | +0.29 | B | 70.5 | +0.7 | -1.82 | [[F021 alpha024]] |
| 022 | range_compression_60 | candlestick | -0.0514 | -0.41 | B | 66.3 | -1.0 | 3.51 | [[F022 range_compression_60]] |
| 023 | signed_sqrt_return | momentum | -0.0168 | -0.18 | C | 46.9 | 0.0 | -1.90 | [[F023 signed_sqrt_return]] |
| 024 | atr_like_14 | volatility | -0.0541 | -0.25 | A- | 83.4 | -1.0 | 3.01 | [[F024 atr_like_14]] |
| 025 | vol_confirmed_reversal_5 | volume | +0.0301 | +0.26 | B | 64.1 | +0.9 | 4.11 | [[F025 vol_confirmed_reversal_5]] |
| 026 | pv_corr_times_vol_5 | volume | -0.0367 | -0.32 | B | 71.1 | -0.9 | 2.92 | [[F026 pv_corr_times_vol_5]] |

## 按类别分布

| Category | Count | Avg |IC| | Best Factor |
|----------|-------|---------|-------------|
| volume | 9 | 0.0454 | F009 pv_corr_times_vol (A-, 83.6) |
| momentum | 8 | 0.0294 | F020 intraday_vs_overnight (B+, 76.4) |
| candlestick | 5 | 0.0444 | F011 williams_r_variant (B, 71.9) |
| volatility | 3 | 0.0429 | F024 atr_like_14 (A-, 83.4) |
| regime | 2 | 0.0267 | F003 vol_regime_reversal (B, 66.3) |
| trend | 1 | 0.0097 | F006 resi_close_5 (C+, 58.5) |

## 评分分布

| Grade | Count | Factors |
|-------|-------|---------|
| A- | 3 | F009, F010, F024 |
| B+ | 3 | F004, F008, F020 |
| B | 8 | F001, F002, F003, F005, F011, F021, F022, F026 |
| B- | 1 | F019 |
| C+ | 3 | F006, F007, F012 |
| C | 6 | F013, F014, F015, F017, F018, F023 |
| C- | 1 | F016 |

## 关键统计

- **最强 IC**：F009 pv_corr_times_vol (|IC| = 0.0692, ICIR = -0.52)
- **最高评分**：F010 hhi_volume_20 (85.2, A-)
- **最高 L/S Sharpe**：F020 intraday_vs_overnight (5.15)
- **完美单调性**：F004, F010, F020, F022, F024 (|mono| = 1.0)
- **Volume 因子占比**：9/26 = 34.6% — 需警惕方向集中度
