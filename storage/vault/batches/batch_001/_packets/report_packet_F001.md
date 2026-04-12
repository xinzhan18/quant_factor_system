---
factor_id: F001
direction: candlestick_liquidity
admitted_in_batch: batch_001
---

# Report Packet — F001

## Factor YAML Summary

```yaml
name: F001
expression: Mul(Div(Sub(If(Lt($close, $open), $close, $open), $low), Sub($high, $low)),
  $turnover_rate)
source_type: dsl
family_tag: candlestick_liquidity
validation_metrics:
  ic_mean: -0.06437117416589917
  ic_ir: -0.5757328921670652
  ic_win_rate: 0.2830578512396694
  monotonicity: -0.9999999999999999
  long_short_mean: -0.00210057106963455
risk_metrics:
  style_r_squared: 0.35619116755550684
  alpha_survival_ratio: 0.6127
```

## Judge Synthesis

## C002 — ADMIT

### CP01
Hard gates: all_pass. coverage=0.95, sign=-1.

### CP02
Mechanism alignment: **aligned**. Lower shadow ratio measures intraday buying support — price dipped but recovered. With turnover conditioner, this captures "high-volume bottom-fishing" events. Negative IC means high lower-shadow-turnover stocks underperform — this is counterintuitive at first glance but makes sense: lower shadows in high-turnover stocks may indicate "failed buying attempts" where the support was tested but the stock is fundamentally weak.

### CP03
Statistical strength: **strong**. IC_val=-0.064 (highest magnitude in batch excluding C003), ICIR=-0.576 (best in batch), mono=-1.0 (perfect). mt_bucket=low. search_adjusted=0.90. This is a genuinely strong signal.

### CP04
Risk cleanness: **borderline → acceptable** (override). style_r2=0.36, alpha_survival=0.61. While style_r2 exceeds the 0.12 threshold, alpha_survival at 0.61 means 61% of the IC survives after Barra regression — this is above the 0.60 minimum. The override is justified because: (1) ICIR=-0.576 is exceptionally strong, (2) the mechanism is distinct from generic vol, and (3) alpha_survival > 0.60. Concern logged for future monitoring.

### CP05
Redundancy: **low**. max_lib_corr=0.00. First batch — no library to compare against.

### CP06
Validation stability: **stable**. split_bucket=high, sign_consistency=1.0, dispersion=0.10 (tight), train_val_decay=1.62 (validation stronger than train — the signal may be strengthening over time, good sign for A-share microstructure).

## Instructions

Write a deep analytical report on `F001`. Cover the economic mechanism, the validation evidence, the risk cleanness, and the library positioning. Use only the information in this packet — do not open other files, call Qlib, or reach the DB. Output path: `vault/factors/{factor_id}.md`.

