---
tags: [family, saturated]
factor_count: 2
origin: L001
---

# FM timing_range

> Volume Timing Range x PE 家族 | 2 factors | Origin: [[L001 蜡烛图微观结构]]

## Core Mechanism

`Mul(Sub(IdxMax($volume, 5), IdxMin($volume, 5)), CsRank($pe_ratio))`
成交量峰谷时序差 x PE ranking。

## Members

| Factor | Variant | alpha_surv |
|--------|---------|------------|
| [[F013 vol_range_timing_5d_x_pe\|F013]] | volume timing 5d x PE | **1.204** (system best) |
| F014 | amount timing 5d x PE | admitted |

## Discovery Story

batch_050 中 TsAutoCorr($vol) 复现 F001 时，**意外发现** timing_range 信号。这是系统中最强的因子(alpha=1.204)。

## Key Constraints

- 3d 太快 (decay<1)
- PS/PB conditioning 无效，只有 PE 有效
- Expression-level blend fails (mono=0.0)
- Amihud conditioning 无效 (与 shadow 家族相反!)

## Related

- [[FM shadow_liquidity]] — L001 的另一个家族，Amihud 对 timing_range 无效但对 shadow 有效
- [[L001 蜡烛图微观结构]] — 产出假设
