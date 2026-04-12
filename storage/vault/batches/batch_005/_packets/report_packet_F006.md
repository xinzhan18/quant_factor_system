---
factor_id: F006
direction: fundamental_technical_cov
admitted_in_batch: batch_005
---

# Report Packet — F006

## Factor YAML Summary

```yaml
name: F006
expression: Mul(CsRank(Div(Div($close, $ps_ratio), Div(Ref($close, 60), Ref($ps_ratio,
  60)))), CsRank(Mul($pb_ratio, -1)))
source_type: dsl
family_tag: fundamental_technical_cov
validation_metrics:
  ic_mean: 0.0296733582469927
  ic_ir: 0.3305257233001534
  ic_win_rate: 0.6260330578512396
  monotonicity: 0.9999999999999999
  long_short_mean: 0.0007346671746061414
risk_metrics:
  style_r_squared: 0.2722119096459291
  alpha_survival_ratio: 0.2323
```

## Judge Synthesis

## C008 — ==ADMIT== → [[../../factors/F006|F006]] 营收增长率 × CsRank(-PB)

### CP01
Hard gates: ==all_pass==。coverage=0.95, sign=+1。

### CP02
机制对齐：**aligned**。CsRank(revenue_change_60d) × CsRank(-PB) = ==收入增长快 + 账面估值低 = 价值重估候选==。经济机制清晰：营收在改善但市场尚未在 PB 中反映——这是经典的 GARP (Growth at Reasonable Price) 思路。正 IC 说明这类股票未来表现好。

### CP03
统计强度：**strong**。IC=0.030, ICIR=0.331。mt_bucket=low。ls_tstat=4.8（显著）。D1 年度 IC 4/7 年同方向。这是一个中等强度的 fundamental 信号——不如 shadow 信号强（ICIR 0.4-0.6），但机制完全不同。

### CP04
风险干净度：**borderline**。style_r2=0.272。PB conditioning 必然带来 book_to_price 风格暴露。但 alpha_survival 待确认。对于 fundamental 因子，一定程度的 value 风格暴露是预期内的。

### CP05
冗余：**low**。==max_corr=0.167==——与全部 5 个 candlestick 因子几乎完全正交。这是一个真正独立的信号维度。

### CP06
稳定性：**stable**。split_bucket 和 sign_consistency 正常。

## Instructions

Write a deep analytical report on `F006`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Output path: `vault/factors/{factor_id}.md`.

