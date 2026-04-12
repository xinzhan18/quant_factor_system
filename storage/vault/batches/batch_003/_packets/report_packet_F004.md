---
factor_id: F004
direction: candlestick_liquidity
admitted_in_batch: batch_003
---

# Report Packet — F004

## Factor YAML Summary

```yaml
name: F004
expression: Mul(Div(Sub($high, If(Gt($close, $open), $close, $open)), $close), Mul(Div($close,
  Ref($close, 5)), -1))
source_type: dsl
family_tag: candlestick_liquidity
validation_metrics:
  ic_mean: 0.03837571762947871
  ic_ir: 0.4181326250085168
  ic_win_rate: 0.6611570247933884
  monotonicity: 0.8999999999999998
  long_short_mean: 0.0012609204477334708
risk_metrics:
  style_r_squared: 0.12692365183189935
  alpha_survival_ratio: 0.308
```

## Judge Synthesis

## C008 — ==ADMIT== → [[../../factors/F004|F004]] 上影线/close × 负5日收益

### CP01
Hard gates: ==all_pass==。coverage=0.95, sign=+1（正方向！）。

### CP02
机制对齐：**aligned**。上影线/close 衡量日内抛压的相对强度（normalized by close）。乘以负5日收益（-ret_5d）→ 因子值在"近期下跌 + 长上影线"时最大。经济机制：==连续下跌中出现的长上影线 = 反弹失败 = 下跌延续确认信号==。正 IC 意味着因子值高（近期跌+长上影）的股票反而表现好——这是一个**动量反转 × 微观结构确认**信号。

### CP03
统计强度：**strong**。IC=0.038, ICIR=0.418。mt_bucket=low。D1 年度 IC 一致性好（5/7年同方向）。ls_tstat=8.1（高度显著）。D3 mono_IS=0.5（中等——Q1-Q3 平坦，Q4-Q5 跳升，"pick winners"型信号）。

### CP04
风险干净度：**borderline**。style_r2=0.127——比 shadow/turnover 类候选干净很多（0.2-0.6）。dominant_style=vol_20d。alpha_survival 待确认。这是一个新机制方向（momentum reversal × candlestick），风格暴露模式应该和纯 shadow 信号不同。

### CP05
冗余：**low**。max_corr=0.607 vs F001。==低于 0.70 阈值==——与现有因子库有效正交。这是一个全新的信号方向。

### CP06
稳定性：**stable**。split_bucket=high, sign_consistency=1.0。factor_turnover=0.72（偏高但可接受）。

## Instructions

Write a deep analytical report on `F004`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Output path: `vault/factors/{factor_id}.md`.

