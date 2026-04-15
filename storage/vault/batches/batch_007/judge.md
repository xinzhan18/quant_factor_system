---
batch_id: batch_007
judged_at: 2026-04-15T00:30:00Z
direction: fundamental_technical_cov

candidates:
  - candidate_id: C001
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: acceptable, CP05: high, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C002
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: poor, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C003
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: poor, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C004
    verdict: reserve
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: weak, CP04: acceptable, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C005
    verdict: reserve
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: weak, CP04: acceptable, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C006
    verdict: reject
    hard_gate_result: compute_error
    checkpoint_positions: {CP01: fail}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C007
    verdict: reject
    hard_gate_result: compute_error
    checkpoint_positions: {CP01: fail}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C008
    verdict: reserve
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: weak, CP04: acceptable, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]

batch_summary:
  total: 8
  admit: 0
  reserve: 3
  reject: 5
  new_factors: []
---

# batch_007 判决报告

> [!abstract] 总览
> [[../../directions/fundamental_technical_cov|Fundamental×Technical Cov]] 第三轮。8 候选 → ==0 admit==, 3 reserve, 5 reject。
> 本轮无 admit——Cov 类信号的最佳表达已被 F007 占据（C001 corr=0.855），PS/PB 版本 style_r2 过高。Corr 信号再次 NaN。T004(rank delta) 依然干净正交但太弱。方向产出率下降明显。

| 候选 | ICIR | style_r² | corr | 裁决 |
|---|---|---|---|---|
| C001 | -0.373 | 0.112 | ==0.855== | reject (CP05 冗余 F007) |
| C002 | -0.394 | ==0.322== | 0.588 | reject (CP04) |
| C003 | -0.404 | ==0.372== | 0.586 | reject (CP04) |
| C004 | 0.197 | 0.061 | 0.151 | reserve |
| C005 | 0.164 | ==0.039== | 0.146 | reserve |
| C006 | ERROR | — | — | reject (CP01) |
| C007 | ERROR | — | — | reject (CP01) |
| C008 | -0.221 | 0.100 | 0.522 | reserve |

---

## C001 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP05 max_corr=0.855 vs F007
> Cov(amount,PE,20) 与 F007 Cov(turnover,PE,20) 截面排序高度重叠——amount 和 turnover_rate 在截面上高度共线。

---

## C002 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP04 style_r2=0.322
> Cov(turnover,PS,20) 的 PS ratio 与 ep_ratio Barra 因子有较高暴露。

---

## C003 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP04 style_r2=0.372
> Cov(turnover,PB,20) 与 book_to_price Barra 因子共线。PB conditioning 带来不可避免的 value style 暴露。

---

## C004 — RESERVE

### CP01
Hard gates: all_pass。

### CP02
**aligned**。PE rank delta × CsRank(turnover)。

### CP03
**weak**。ICIR=0.197，未达 0.30。mt_bucket=low。但 ls_tstat=7.1（显著）——分组极端组效应强。

### CP04
**acceptable**。style_r2=0.061。

### CP05
**low**。max_corr=0.151。

### CP06
**stable**。

---

## C005 — RESERVE

### CP01
Hard gates: all_pass。

### CP02
**aligned**。PE rank delta × CsRank(-PB)。

### CP03
**weak**。ICIR=0.164。mt_bucket=low。style_r2=0.039 是全 batch 最干净。max_corr=0.146 全系统最正交。但 IC 强度不够。

### CP04
**acceptable**。style_r2=0.039。

### CP05
**low**。max_corr=0.146。

### CP06
**stable**。

---

## C006 — REJECT

### CP01
Hard gates: ==compute_error==。Corr(turnover,PB,60) 预处理后全 NaN。PB 在 60 天内变动极小（季报更新频率），导致标准差趋零 → 相关系数 undefined。

---

## C007 — REJECT

### CP01
Hard gates: ==compute_error==。同 C006——Corr(amount,PS,60) 也因 PS 变动过小而 NaN。==结论：Corr 类信号在 fundamental 字段上不可行==（估值指标变化太慢，日频 Corr 的分母趋零）。

---

## C008 — RESERVE

### CP01
Hard gates: all_pass。

### CP02
**aligned**。Cov(日收益率, PE, 20) 是新的信号结构——衡量收益率与估值的短期协方差。

### CP03
**weak**。ICIR=-0.221。mt_bucket=low。

### CP04
**acceptable**。style_r2=0.100。

### CP05
**low**。max_corr=0.522（中等，未超标）。

### CP06
**stable**。
