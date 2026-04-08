---
tags: [family, saturated]
factor_count: 1
origin: L001
---

# FM shadow_liquidity

> Shadow x Amihud 家族 | 1 factor | Origin: [[L001 蜡烛图微观结构]]

## Core Mechanism

`Mul(Mean(shadow_ratio, 20), Amihud_ratio)`
影线比例 x Amihud 非流动性。20d 是唯一有效窗口。

## Members

| Factor | Expression | alpha_surv |
|--------|------------|------------|
| [[F002_shadow_amihud_20\|F002]] | shadow_amihud_20 | 0.377 |

## Exploration Dead-Ends

- 10d/5d shadow x Amihud: FAIL
- 40d shadow: weaker than 20d
- Shadow x pv_corr: F002 duplicate
- Shadow x vol-competition: FAIL
- Shadow x any non-Amihud: ALL FAIL

## Related

- [[FM timing_range]] — L001 的另一个成功家族
- [[L001 蜡烛图微观结构]] — 产出假设
