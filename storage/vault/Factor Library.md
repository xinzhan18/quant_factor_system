---
title: Factor Library
tags:
  - index
updated: 2026-04-02
---

# Factor Library

> **30 factors** | 最后更新：2026-04-02 | 清理后版本（移除 7 个无效因子）

## 汇总表

| ID | Name | Category | IC (IS) | IC (OOS) | ICIR (OOS) | LS Sharpe | Mono | Score | Grade | Link |
|----|------|----------|---------|---------|------------|-----------|------|-------|-------|------|
| 009 | pv_corr_times_vol | volume | -0.0330 | -0.0407 | -0.457 | 2.77 | -0.9 | 79.9 | A | [[F009 pv_corr_times_vol]] |
| 011 | williams_r_variant | candlestick | +0.0441 | +0.0524 | +0.414 | 2.26 | +0.9 | 78.2 | A | [[F011 williams_r_variant]] |
| 026 | pv_corr_times_vol_5 | volume | -0.0332 | -0.0367 | -0.463 | 2.92 | -0.9 | 76.0 | A | [[F026 pv_corr_times_vol_5]] |
| 010 | hhi_volume_20 | volume | -0.0341 | -0.0288 | -0.468 | 3.77 | -1.0 | 74.2 | B | [[F010 hhi_volume_20]] |
| 004 | std_volume_20 | volume | -0.0318 | -0.0327 | -0.343 | 2.84 | -0.9 | 73.1 | B | [[F004 std_volume_20]] |
| 008 | ret_vol_cov_20 | volume | -0.0293 | -0.0325 | -0.429 | 2.41 | -0.7 | 73.0 | B | [[F008 ret_vol_cov_20]] |
| 027 | turnover_vol_10 | liquidity | -0.0376 | -0.0453 | -0.301 | 2.59 | -1.0 | 72.8 | B | [[F027 turnover_vol_10]] |
| 025 | vol_confirmed_reversal_5 | volume | +0.0345 | +0.0301 | +0.440 | 4.11 | +0.9 | 71.3 | B | [[F025 vol_confirmed_reversal_5]] |
| 033 | mean_turnover_5 | liquidity | -0.0350 | -0.0438 | -0.259 | 2.18 | -1.0 | 68.9 | B | [[F033 mean_turnover_5]] |
| 031 | turnover_vol_20 | liquidity | -0.0336 | -0.0413 | -0.256 | 2.35 | -1.0 | 68.0 | B | [[F031 turnover_vol_20]] |
| 001 | std_returns_20 | volatility | -0.0290 | -0.0469 | -0.304 | 1.22 | -0.9 | 65.5 | B | [[F001 std_returns_20]] |
| 022 | range_compression_60 | candlestick | -0.0339 | -0.0280 | -0.362 | 2.28 | -0.7 | 62.6 | B | [[F022 range_compression_60]] |
| 021 | alpha024 | momentum | +0.0277 | +0.0342 | +0.281 | 1.19 | +0.7 | 62.2 | B | [[F021 alpha024]] |
| 029 | mean_turnover_20 | liquidity | -0.0263 | -0.0379 | -0.214 | 1.63 | -1.0 | 61.4 | B | [[F029 mean_turnover_20]] |
| 002 | delta_volume_5 | volume | -0.0347 | -0.0228 | -0.342 | 3.38 | -0.7 | 59.5 | C | [[F002 delta_volume_5]] |
| 032 | turnover_vol_60 | liquidity | -0.0241 | -0.0338 | -0.189 | 1.64 | -1.0 | 58.8 | C | [[F032 turnover_vol_60]] |
| 028 | inverse_pb | valuation | +0.0196 | +0.0337 | +0.242 | 1.28 | +1.0 | 57.6 | C | [[F028 inverse_pb]] |
| 024 | atr_like_14 | volatility | -0.0222 | -0.0387 | -0.241 | 1.10 | -0.9 | 56.9 | C | [[F024 atr_like_14]] |
| 038 | size_x_pb | other | +0.0217 | +0.0270 | +0.162 | 1.59 | +1.0 | 56.4 | C | [[F038 size_x_pb]] |
| 034 | pb_ratio_rank_60 | valuation | -0.0299 | -0.0243 | -0.233 | 1.28 | -0.7 | 56.2 | C | [[F034 pb_ratio_rank_60]] |
| 039 | size_x_ps | other | +0.0168 | +0.0210 | +0.141 | 1.49 | +1.0 | 53.4 | C | [[F039 size_x_ps]] |
| 020 | intraday_vs_overnight | momentum | -0.0374 | -0.0214 | -0.229 | 2.97 | -0.9 | 52.1 | C | [[F020 intraday_vs_overnight]] |
| 035 | pb_x_reversal_10 | valuation | +0.0246 | +0.0230 | +0.212 | 0.70 | +0.3 | 49.5 | C | [[F035 pb_x_reversal_10]] |
| 036 | turnover_level_x_reversal_20 | liquidity | +0.0284 | +0.0187 | +0.164 | 1.65 | +0.3 | 46.6 | C | [[F036 turnover_level_x_reversal_20]] |
| 030 | turnover_change_5 | liquidity | -0.0236 | -0.0126 | -0.210 | 3.07 | -0.3 | 43.9 | D | [[F030 turnover_change_5]] |
| 015 | alpha053 | candlestick | +0.0095 | +0.0073 | +0.093 | 14.37 | -0.4 | 36.9 | D | [[F015 alpha053]] |
| 018 | alpha017 | momentum | +0.0092 | +0.0068 | +0.077 | 2.17 | -0.6 | 34.4 | D | [[F018 alpha017]] |
| 019 | rank_ret_times_rank_vol | volume | -0.0291 | -0.0200 | -0.225 | 0.01 | +0.1 | 30.0 | D | [[F019 rank_ret_times_rank_vol]] |
| 014 | alpha023 | momentum | +0.0233 | +0.0095 | +0.103 | 0.02 | +0.4 | 24.1 | D | [[F014 alpha023]] |
| 013 | alpha038 | candlestick | +0.0259 | +0.0125 | +0.121 | 0.15 | -0.3 | 23.2 | D | [[F013 alpha038]] |

## 按类别分布

| Category | Count | Avg \|IC\| OOS | Best Factor | Best Score |
|----------|-------|----------------|-------------|------------|
| volume | 8 | 0.0305 | pv_corr_times_vol (A) | 79.9 |
| liquidity | 7 | 0.0333 | turnover_vol_10 (B) | 72.8 |
| candlestick | 4 | 0.0250 | williams_r_variant (A) | 78.2 |
| momentum | 4 | 0.0180 | alpha024 (B) | 62.2 |
| valuation | 3 | 0.0270 | inverse_pb (C) | 57.6 |
| volatility | 2 | 0.0428 | std_returns_20 (B) | 65.5 |
| other | 2 | 0.0240 | size_x_pb (C) | 56.4 |

## 评分分布

| Grade | Count | Factors |
|-------|-------|---------|
| A | 3 | pv_corr_times_vol, williams_r_variant, pv_corr_times_vol_5 |
| B | 11 | hhi_volume_20, std_volume_20, ret_vol_cov_20, turnover_vol_10, vol_confirmed_reversal_5, mean_turnover_5, turnover_vol_20, std_returns_20, range_compression_60, alpha024, mean_turnover_20 |
| C | 10 | delta_volume_5, turnover_vol_60, inverse_pb, atr_like_14, size_x_pb, pb_ratio_rank_60, size_x_ps, intraday_vs_overnight, pb_x_reversal_10, turnover_level_x_reversal_20 |
| D | 6 | turnover_change_5, alpha053, alpha017, rank_ret_times_rank_vol, alpha023, alpha038 |

## 清理记录（2026-04-02）

本轮共移除 **7 个因子**（从 37 → 30），原因：

| 移除因子 | IC_OOS | 原因 |
|---------|--------|------|
| [016] alpha010 | +0.017 (IS only) | 无 OOS 验证，最弱因子 |
| [037] inverse_ps | +0.018 | 与 inverse_pb 概念冗余 |
| [003] vol_regime_reversal | -0.011 | 全期 OOS 近乎为零 |
| [006] resi_close_5 | -0.002 | OOS 实际为零，mining IC 来自噪音 |
| [007] vol_regime_resi_vs_slope | -0.003 | 同上 |
| [023] signed_sqrt_return | -0.003 | 平方根变换无效，OOS 归零 |
| [017] alpha034 | +0.005 (p=0.16) | OOS 统计不显著 |

## ⚠️ 需要关注的因子

**Grade D 因子**（建议下一轮评估是否留存）：
- **F013 alpha038** (Score=23): OOS IC 仅 0.013，LS Sharpe 0.15，接近无效
- **F014 alpha023** (Score=24): OOS IC 0.010，LS Sharpe 0.02，几乎不创造收益
- **F019 rank_ret_times_rank_vol** (Score=30): Profitability=9.6，单调性=0.1，分组无序
- **F018 alpha017** (Score=34): OOS p=0.09，统计边缘显著

**高相关聚簇**（portfolio 中只应选代表因子）：
- 换手率波动群: F027/F031/F033/F032（相关 0.79-0.92）→ 建议仅保留 F027
- 价量乘积: F009/F026（相关 0.63）→ 可共存
- 市值×估值: F038/F039（相关 0.73）→ 接近阈值，谨慎
