---
title: Factor Library
tags:
  - index
---

# Factor Library

> 36 factors | Last updated: 2026-04-01

## 汇总表

| ID | Name | Category | IC (OOS) | ICIR (OOS) | Grade | Score | Link |
|----|------|----------|----------|------------|-------|-------|------|
| 001 | std_returns_20 | volatility | -0.0469 | -0.304 | B | 65.5 | [[F001 std_returns_20]] |
| 002 | delta_volume_5 | volume | -0.0323 | — | — | — | [[F002 delta_volume_5]] |
| 003 | vol_regime_reversal | regime | -0.0435 | — | — | — | [[F003 vol_regime_reversal]] |
| 004 | std_volume_20 | volume | -0.0392 | — | — | — | [[F004 std_volume_20]] |
| 006 | resi_close_5 | trend | -0.0325 | — | — | — | [[F006 resi_close_5]] |
| 007 | vol_regime_resi_vs_slope | regime | -0.0340 | — | — | — | [[F007 vol_regime_resi_vs_slope]] |
| 008 | ret_vol_cov_20 | volume | -0.0327 | — | — | — | [[F008 ret_vol_cov_20]] |
| 009 | pv_corr_times_vol | volume | -0.0521 | — | — | — | [[F009 pv_corr_times_vol]] |
| 010 | hhi_volume_20 | volume | -0.0341 | — | — | — | [[F010 hhi_volume_20]] |
| 011 | williams_r_variant | candlestick | +0.0695 | — | — | — | [[F011 williams_r_variant]] |
| 013 | alpha038 | candlestick | +0.0355 | — | — | — | [[F013 alpha038]] |
| 014 | alpha023 | momentum | +0.0296 | — | — | — | [[F014 alpha023]] |
| 015 | alpha053 | candlestick | +0.0234 | — | — | — | [[F015 alpha053]] |
| 016 | alpha010 | momentum | +0.0171 | — | — | — | [[F016 alpha010]] |
| 017 | alpha034 | volatility | +0.0194 | — | — | — | [[F017 alpha034]] |
| 018 | alpha017 | momentum | +0.0231 | — | — | — | [[F018 alpha017]] |
| 019 | rank_ret_times_rank_vol | volume | -0.0410 | — | — | — | [[F019 rank_ret_times_rank_vol]] |
| 020 | intraday_vs_overnight | momentum | -0.0376 | — | — | — | [[F020 intraday_vs_overnight]] |
| 021 | alpha024 | momentum | +0.0487 | — | — | — | [[F021 alpha024]] |
| 022 | range_compression_60 | candlestick | -0.0422 | — | — | — | [[F022 range_compression_60]] |
| 023 | signed_sqrt_return | momentum | -0.0318 | — | — | — | [[F023 signed_sqrt_return]] |
| 024 | atr_like_14 | volatility | -0.0443 | — | — | — | [[F024 atr_like_14]] |
| 025 | vol_confirmed_reversal_5 | volume | +0.0301 | +0.260 | B | 64.1 | [[F025 vol_confirmed_reversal_5]] |
| 026 | pv_corr_times_vol_5 | volume | -0.0367 | -0.325 | B | 71.1 | [[F026 pv_corr_times_vol_5]] |
| 027 | turnover_vol_10 | liquidity | -0.0471 | — | — | — | [[F027 turnover_vol_10]] |
| 028 | inverse_pb | valuation | +0.0278 | — | — | — | [[F028 inverse_pb]] |
| 029 | mean_turnover_20 | liquidity | -0.0379 | — | — | — | [[F029 mean_turnover_20]] |
| 030 | turnover_change_5 | liquidity | -0.0216 | — | — | — | [[F030 turnover_change_5]] |
| 031 | turnover_vol_20 | liquidity | -0.0436 | — | — | — | [[F031 turnover_vol_20]] |
| 032 | turnover_vol_60 | liquidity | -0.0351 | — | — | — | [[F032 turnover_vol_60]] |
| 033 | mean_turnover_5 | liquidity | -0.0455 | — | — | — | [[F033 mean_turnover_5]] |
| 034 | pb_ratio_rank_60 | valuation | -0.0379 | — | — | — | [[F034 pb_ratio_rank_60]] |
| 035 | pb_x_reversal_10 | valuation | +0.0331 | — | — | — | [[F035 pb_x_reversal_10]] |
| 036 | turnover_level_x_reversal_20 | liquidity | +0.0286 | — | — | — | [[F036 turnover_level_x_reversal_20]] |
| 037 | inverse_ps | valuation | +0.0180 | — | — | — | [[F037 inverse_ps]] |
| 038 | size_x_pb | other | +0.0315 | — | — | — | [[F038 size_x_pb]] |
| 039 | size_x_ps | other | +0.0206 | — | — | — | [[F039 size_x_ps]] |

> [!note] Grade/Score 仅对已用新 pipeline 重建报告的因子有值；其余因子运行 `/factor-report <id>` 生成完整报告后自动更新。

## 按类别分布

| Category | Count | Avg \|IC\| | Best Factor |
|----------|-------|-----------|-------------|
| volume | 8 | 0.0388 | 009 pv_corr_times_vol (0.0521) |
| liquidity | 6 | 0.0399 | 027 turnover_vol_10 (0.0471) |
| momentum | 6 | 0.0313 | 021 alpha024 (0.0487) |
| candlestick | 4 | 0.0426 | 011 williams_r_variant (0.0695) |
| volatility | 3 | 0.0369 | 001 std_returns_20 (0.0575 IS) |
| valuation | 4 | 0.0292 | 035 pb_x_reversal_10 (0.0331) |
| regime | 2 | 0.0388 | 003 vol_regime_reversal (0.0435) |
| other | 3 | 0.0246 | 038 size_x_pb (0.0315) |
| trend | 1 | 0.0325 | 006 resi_close_5 (0.0325) |

## 评分分布

| Grade | Count | Factors |
|-------|-------|---------|
| S | 0 | — |
| A | 0 | — |
| B | 3 | 001 (65.5), 025 (64.1), 026 (71.1) |
| C | 0 | — |
| D | 0 | — |
| 未评级 | 33 | 运行 `/factor-report all` 生成全量报告 |

## 信号空间状态

| 维度 | 状态 | 已录因子数 |
|------|------|----------|
| OHLCV（价格/成交量） | 🔴 EXHAUSTED | 26 |
| Fundamental（基本面） | 🟡 ACTIVE | 10 |
| Alpha101 | 🟡 PARTIALLY (45/100) | — |
| 技术指标 | 🔴 EXHAUSTED | — |

> **下一步**：继续挖掘 size_value_crossover、valuation_pe_ps、alpha101_composites 方向。
