---
tags:
  - index
  - factor-library
updated: "2026-04-08"
---

# Factor Library

共 **14 个录取因子**（F001-F014），均来自新系统（evaluation_version=v2）。

## Hypotheses (Logic Cards)

| Logic | Name | Status | Admits | Hit Rate |
|-------|------|--------|--------|----------|
| [[L001 蜡烛图微观结构\|L001]] | 蜡烛图微观结构 x 流动性 | parked | 3 | 5.3% |
| [[L002 跨字段协方差\|L002]] | 跨字段协方差异象 | parked | 0 | 0% |
| [[L003 成交量分布动态\|L003]] | 成交量分布动态 | parked | 1 | 12.5% |
| [[L004 量价背离\|L004]] | 量价背离 | saturated | 10 | 26.3% |
| [[L005 跨截面成交量异常\|L005]] | 跨截面成交量异常 | parked | 0 | 0% |
| [[L006 A股涨跌停微结构\|L006]] | A股涨跌停微结构 | parked | 0 | 0% |
| [[L007 聪明钱流量持续性\|L007]] | 聪明钱流量持续性 | parked | 0 | 0% |
| [[L008 量能竞争强度\|L008]] | 量能竞争强度 x 估值 | active | 0 | 0% |

## Factor Families

| Family | Factors | Origin | Status |
|--------|---------|--------|--------|
| [[FM price_volume_divergence]] | F003-F007, F009 | [[L004 量价背离\|L004]] | saturated |
| [[FM rel_tur_encoding]] | F008, F010-F012 | [[L004 量价背离\|L004]] | saturated |
| [[FM shadow_liquidity]] | F002 | [[L001 蜡烛图微观结构\|L001]] | saturated |
| [[FM timing_range]] | F013-F014 | [[L001 蜡烛图微观结构\|L001]] | saturated |
| [[FM volume_autocorrelation]] | F001 | [[L003 成交量分布动态\|L003]] | saturated |

## 因子总览

| ID | 名称 | 分级 | 得分 | Logic | Family | 批次 | 报告 |
|----|------|------|------|-------|--------|------|------|
| [[F001 amount_autocorr_20\|F001]] | amount_autocorr_20 | B | 63.2 | [[L003 成交量分布动态\|L003]] | [[FM volume_autocorrelation]] | batch_001 | ✓ |
| [[F002_shadow_amihud_20\|F002]] | shadow_amihud_20 | A | 75.8 | [[L001 蜡烛图微观结构\|L001]] | [[FM shadow_liquidity]] | batch_003 | ✓ |
| [[F003_pv_corr_x_tur_rank\|F003]] | pv_corr_x_tur_rank | A | 76.8 | [[L004 量价背离\|L004]] | [[FM price_volume_divergence]] | batch_003 | ✓ |
| [[F004 pv_corr_10d_x_tur_rank\|F004]] | pv_corr_10d_x_tur_rank | ==A== | 78.1 | [[L004 量价背离\|L004]] | [[FM price_volume_divergence]] | batch_038 | ✓ |
| [[F005 pv_amount_corr_20d_x_tur_rank\|F005]] | pv_amount_corr_20d_x_tur_rank | ==A== | 77.6 | [[L004 量价背离\|L004]] | [[FM price_volume_divergence]] | batch_038 | ✓ |
| F006 | pv_corr_5d_x_tur_rank | — | — | [[L004 量价背离\|L004]] | [[FM price_volume_divergence]] | batch_039 | — |
| F007 | pv_amount_corr_10d_x_tur_rank | — | — | [[L004 量价背离\|L004]] | [[FM price_volume_divergence]] | batch_039 | — |
| F008 | pv_corr_rel_tur_rank | — | — | [[L004 量价背离\|L004]] | [[FM rel_tur_encoding]] | batch_039 | — |
| F009 | pv_amount_corr_5d_x_tur_rank | — | — | [[L004 量价背离\|L004]] | [[FM price_volume_divergence]] | batch_040 | — |
| F010 | pv_amount_corr_rel_tur_conditioning | — | — | [[L004 量价背离\|L004]] | [[FM rel_tur_encoding]] | batch_040 | — |
| F011 | amount_vol_competition_corr | — | — | [[L004 量价背离\|L004]] | [[FM rel_tur_encoding]] | batch_041 | — |
| F012 | amount_x_rel_tur_7d | — | — | [[L004 量价背离\|L004]] | [[FM rel_tur_encoding]] | batch_044 | — |
| F013 | vol_range_timing_5d_x_pe | — | — | [[L001 蜡烛图微观结构\|L001]] | [[FM timing_range]] | batch_052 | — |
| F014 | vol_range_timing_5d_amount_x_pe | — | — | [[L001 蜡烛图微观结构\|L001]] | [[FM timing_range]] | batch_055 | — |
