---
tags: [family, saturated]
factor_count: 4
origin: L004
---

# FM rel_tur_encoding

> pv_corr x Div(CsRank(tur), CsRank(vol)) 家族 | 4 factors | Origin: [[L004 量价背离]]

## Core Mechanism

`Mul(Corr($close, $amount, N), Div(CsRank($turnover_rate), CsRank($volume)))`
rel-tur 编码 = 竞争强度指标。比单纯 CsRank(tur) 产生更高 alpha。

## Members

| Factor | Variant | alpha_surv | Barra_res_ICIR |
|--------|---------|------------|----------------|
| F008 | pv_corr 20d x rel-tur | **0.496** | -0.347 |
| F010 | amount 20d x rel-tur | **0.513** | -0.343 |
| F011 | amount vol-competition | 0.362 | -0.270 |
| F012 | 7d amount x rel-tur | 0.462 | -0.402 |

## Key Insight

rel-tur 编码是 batch_039 发现的新范式。F008 和 F010 是全系统 alpha_surv 最高的因子。

## Related

- [[FM price_volume_divergence]] — 基础版家族
- [[L008 量能竞争强度]] — 试图将 rel-tur 独立于 pv_corr 使用
- [[L004 量价背离]] — 产出假设
