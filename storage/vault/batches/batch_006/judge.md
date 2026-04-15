---
batch_id: batch_006
judged_at: 2026-04-13T02:30:00Z
direction: fundamental_technical_cov

candidates:
  - candidate_id: C001
    verdict: admit
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: borderline, CP04: acceptable, CP05: low, CP06: stable}
    factor_id: F007
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C002
    verdict: reserve
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: weak, CP04: acceptable, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C003
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: borderline, CP04: borderline, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C004
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: borderline, CP04: borderline, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C005
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: borderline, CP04: borderline, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C006
    verdict: reserve
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: weak, CP04: acceptable, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C007
    verdict: reserve
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: weak, CP04: borderline, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C008
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: weak, CP04: acceptable, CP05: high, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]

batch_summary:
  total: 8
  admit: 1
  reserve: 3
  reject: 4
  new_factors: [F007]
---

# batch_006 判决报告

> [!abstract] 总览
> [[../../directions/fundamental_technical_cov|Fundamental×Technical Cov]] 第二轮。8 候选 → ==1 admit==, 3 reserve, 4 reject。
> T001(Cov) 的短窗口版本 C001 style_r2=0.099 通过 CP04。新方向 T004(fundamental momentum rank delta) style_r2 极低(0.04)但信号太弱——需要更好的表达式。

| 候选 | ICIR | style_r² | corr | 裁决 |
|---|---|---|---|---|
| **C001** | -0.316 | ==0.099== | 0.234 | ==**admit → [[../../factors/F007\|F007]]**== |
| C002 | -0.278 | 0.075 | 0.185 | reserve |
| C003 | -0.346 | 0.281 | 0.420 | reject (CP04) |
| C004 | 0.312 | 0.273 | 0.675 | reject (CP04) |
| C005 | -0.339 | 0.269 | 0.423 | reject (CP04) |
| C006 | 0.160 | ==0.043== | 0.154 | reserve (CP03 弱) |
| C007 | 0.218 | 0.272 | ==0.121== | reserve |
| C008 | 0.236 | 0.104 | ==0.790== | reject (CP05 冗余 F006) |

---

## C001 — ==ADMIT== → [[../../factors/F007|F007]] Cov(换手率, PE, 20天)

### CP01
Hard gates: ==all_pass==。coverage=0.95, sign=-1。

### CP02
机制对齐：**aligned**。Cov(turnover_rate, pe_ratio, 20) 衡量近 20 天内换手率与 PE 的协方差。负 IC → 高协方差（换手和估值同步上升）的股票后续表现差。机制：==换手率和 PE 同步上升 = "投机推升估值泡沫"——短期内看涨但中期反转==。20 天窗口比 60 天更灵敏，捕捉更快的投机脉冲。

### CP03
统计强度：**borderline**。IC=-0.024, ICIR=-0.316（刚过 0.30 阈值）。mt_bucket=low。ls_tstat=-6.2（显著）。D1 年度 IC 6/7 年同方向。不是最强的信号但方向一致性很好。

### CP04
风险干净度：**acceptable**。==style_r2=0.099==——低于 0.12 阈值，干净。协方差是二阶统计量，Barra 因子（一阶的 level/rank）解释不了。

### CP05
冗余：**low**。max_corr=0.234——与全部 6 个现有因子正交。这是一个全新的信号结构。

### CP06
稳定性：**stable**。split_bucket=high, sign_consistency=1.0。

---

## C002 — RESERVE

### CP01
Hard gates: all_pass。

### CP02
**aligned**。Cov(amount, PE, 60) 用成交额替代换手率。

### CP03
**weak**。ICIR=-0.278，未达 0.30。mt_bucket=low。但 style_r2=0.075 是 batch 最干净。Reserve 等 T001 进一步变体。

### CP04
**acceptable**。style_r2=0.075。

### CP05
**low**。max_corr=0.185。

### CP06
**stable**。

---

## C003 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP04 style_r2=0.281
> CsRank(EPS变化) × CsRank(换手率) 被 vol+value 风格共同污染。

---

## C004 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP04 style_r2=0.273 + CP05 corr=0.675（接近阈值）
> CsRank(EPS变化) × CsRank(-PB) 与 F006 高度相关（0.675）。EPS 和 Revenue 的变化率截面排名高度共线。

---

## C005 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP04 style_r2=0.269
> 营收增长 × CsRank(换手率) 的 value 风格暴露偏高。

---

## C006 — RESERVE

### CP01
Hard gates: all_pass。

### CP02
**aligned**。PE rank delta = 估值排名在 60 天内的变化趋势。

### CP03
**weak**。ICIR=0.160。mt_bucket=low。但 ==style_r2=0.043, max_corr=0.154==——极度干净且正交。这个方向有潜力，需要更好的表达式来提升 IC。

### CP04
**acceptable**。style_r2=0.043。

### CP05
**low**。max_corr=0.154。

### CP06
**stable**。

---

## C007 — RESERVE

### CP01
Hard gates: all_pass。

### CP02
**aligned**。PB rank delta。

### CP03
**weak**。ICIR=0.218。mt_bucket=low。

### CP04
**borderline**。style_r2=0.272（PB delta 被 book_to_price 风格吃掉一部分）。

### CP05
**low**。==max_corr=0.121==——全 batch 最低冗余。

### CP06
**stable**。

---

## C008 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP05 max_corr=0.790 (>0.70) vs F006
> 营收增长 × CsRank(-PS) 与 F006 营收增长 × CsRank(-PB) 高度冗余——PS 和 PB 的截面排名高度共线。
