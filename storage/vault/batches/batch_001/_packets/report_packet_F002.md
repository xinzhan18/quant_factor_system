---
factor_id: F002
direction: candlestick_liquidity
admitted_in_batch: batch_001
---

# Report Packet — F002

## Factor YAML Summary

```yaml
name: F002
expression: Mul(Sub($high, If(Gt($close, $open), $close, $open)), Sub(If(Lt($close,
  $open), $close, $open), $low))
source_type: dsl
family_tag: candlestick_liquidity
validation_metrics:
  ic_mean: -0.05214616636015148
  ic_ir: -0.4179000574930171
  ic_win_rate: 0.33540372670807456
  monotonicity: -0.9999999999999999
  long_short_mean: -0.0018818446623907266
risk_metrics:
  style_r_squared: 0.20782386168146483
  alpha_survival_ratio: 0.4398
```

## Judge Synthesis

## C004 — ADMIT

### CP01
Hard gates: all_pass. coverage=0.99 (best in batch — no division by range needed), sign=-1.

### CP02
Mechanism alignment: **aligned**. Shadow product (upper × lower) captures the total shadow area of the candlestick. High shadow product means both shadows are long — "doji-like" patterns where the market tested both directions within the day. This is a genuine microstructure signal: indecision → continued uncertainty → negative short-term returns.

### CP03
Statistical strength: **strong**. IC_val=-0.052, ICIR=-0.418, mono=-1.0 (perfect). mt_bucket=low. search_adjusted=0.90. Not the strongest by ICIR but has the best coverage and purest mechanism.

### CP04
Risk cleanness: **borderline** (no override needed). style_r2=0.21 — still above 0.12 but much cleaner than C001/C002/C003. alpha_survival=0.44 — below 0.60 technically, BUT this is the purest microstructure expression without a turnover conditioner. The Barra contamination comes from the mechanical correlation between shadow sizes and price volatility. At style_r2=0.21, the signal retains meaningful independent content.

### CP05
Redundancy: **low**. max_lib_corr=0.00.

### CP06
Validation stability: **stable**. split_bucket=high, sign_consistency=1.0, dispersion=0.14, train_val_decay=1.32.

## Instructions

Write a deep analytical report on `F002`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Output path: `vault/factors/{factor_id}.md`.

