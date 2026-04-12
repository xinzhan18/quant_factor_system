---
factor_id: F005
direction: candlestick_liquidity
admitted_in_batch: batch_004
---

# Report Packet — F005

## Factor YAML Summary

```yaml
name: F005
expression: Mul(IdxMax(Div(Sub($high, If(Gt($close, $open), $close, $open)), $close),
  20), Mul(Div($close, Ref($close, 5)), -1))
source_type: dsl
family_tag: candlestick_liquidity
validation_metrics:
  ic_mean: 0.021014870436410045
  ic_ir: 0.3859639401208343
  ic_win_rate: 0.6590909090909091
  monotonicity: 0.7
  long_short_mean: 0.0003453200622384767
risk_metrics:
  style_r_squared: 0.051877785977455626
  alpha_survival_ratio: 0.7924
```

## Judge Synthesis

## C007 — ==ADMIT== → [[../../factors/F005|F005]] IdxMax(上影线,20) × 负5日收益

### CP01
Hard gates: ==all_pass==。coverage=0.95, sign=+1。

### CP02
机制对齐：**aligned**。IdxMax(上影线/close, 20) 返回"过去 20 天中上影线最长的那一天距今几天"。值越大=最大抛压发生在越久以前。乘以 (-5日ret)：如果近期在跌 且 最大抛压已经是很久以前的事 → 因子值大 → 高收益。机制：==抛压已经释放完毕 + 近期下跌 = 错杀后的反弹机会==。这是一个 timing signal（"抛压时机"）× momentum reversal 的复合信号。

### CP03
统计强度：**strong**。IC=0.021, ICIR=0.386。mt_bucket=low。ls_tstat=? D1 年度 IC 5/7 年同方向。IdxMax 是离散整数值（0-19），信号比较粗糙但稳定。

### CP04
风险干净度：**acceptable**。==style_r2=0.052==——**全库最干净**。Barra 风格几乎无法解释这个因子。IdxMax 是纯时序结构特征，不是 level（价格/成交量级别），所以天然正交于 Barra 的 level 因子。

### CP05
冗余：**low**。==max_corr=0.233==——**全库最低冗余**。IdxMax timing 信号与所有现有 shadow/turnover 因子截面排序完全不同。这是一个真正独立的新维度。

### CP06
稳定性：**stable**。split_bucket=high。IdxMax 的离散性使得 IC 序列波动较大（日级别），但方向一致。

---

## Instructions

Write a deep analytical report on `F005`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Output path: `vault/factors/{factor_id}.md`.

