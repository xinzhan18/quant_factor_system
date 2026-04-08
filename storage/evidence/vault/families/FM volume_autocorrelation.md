---
tags: [family, saturated]
factor_count: 1
origin: L003
---

# FM volume_autocorrelation

> TsAutoCorr($amount) 家族 | 1 factor | Origin: [[L003 成交量分布动态]]

## Core Mechanism

`TsAutoCorr($amount, 20)`
成交额的时间序列自相关性。高自相关 = 机构持续买入/卖出。

## Members

| Factor | Expression | ICIR | mono |
|--------|------------|------|------|
| [[F001 amount_autocorr_20\|F001]] | TsAutoCorr($amount, 20) | -0.439 | -1.0 (perfect) |

## Non-Extendable

- $volume / $turnover TsAutoCorr = F001 clone (corr>0.45)
- PE/PS conditioning = ep_ratio absorbed ([[L007 聪明钱流量持续性]])
- 20d 唯一有效窗口

## Related

- [[L003 成交量分布动态]] — 产出假设
- [[L007 聪明钱流量持续性]] — 试图扩展此信号，失败
