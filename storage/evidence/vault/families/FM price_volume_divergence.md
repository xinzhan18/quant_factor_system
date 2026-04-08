---
tags: [family, saturated]
factor_count: 6
origin: L004
---

# FM price_volume_divergence

> pv_corr x CsRank($turnover_rate) 家族 | 6 factors | Origin: [[L004 量价背离]]

## Core Mechanism

`Mul(Corr($close, $volume/$amount, N), CsRank($turnover_rate))`
乘法正交化将 pv_corr 从 Barra turnover 中分离。

## Members

| Factor | Window | Field | ICIR | alpha_surv |
|--------|--------|-------|------|------------|
| [[F003_pv_corr_x_tur_rank\|F003]] | 20d | $volume | -0.427 | 0.393 |
| [[F004 pv_corr_10d_x_tur_rank\|F004]] | 10d | $volume | -0.482 | 0.401 |
| [[F005 pv_amount_corr_20d_x_tur_rank\|F005]] | 20d | $amount | -0.424 | 0.364 |
| F006 | 5d | $volume | -0.455 | 0.379 |
| F007 | 10d | $amount | -0.469 | 0.373 |
| F009 | 5d | $amount | -0.450 | 0.359 |

## Saturation

Window 5d-20d 全覆盖。10d saturation corr=0.85-0.90。无新变体空间。

## Related

- [[FM rel_tur_encoding]] — 升级版，用 rel-tur 替代 CsRank(tur)，alpha 更高
- [[L004 量价背离]] — 产出假设
