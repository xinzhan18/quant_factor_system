---
batch_id: batch_005
judged_at: 2026-04-13T02:00:00Z
direction: fundamental_technical_cov

candidates:
  - candidate_id: C001
    verdict: reserve
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: weak, CP04: acceptable, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C002
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: weak, CP04: poor, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C003
    verdict: reject
    hard_gate_result: compute_error
    checkpoint_positions: {CP01: fail}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C004
    verdict: reserve
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: borderline, CP04: borderline, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C005
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: borderline, CP04: poor, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C006
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: unclear, CP03: weak, CP04: poor, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C007
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: weak, CP04: acceptable, CP05: low, CP06: unstable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C008
    verdict: admit
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: borderline, CP05: low, CP06: stable}
    factor_id: F006
    referenced_context: [lessons.md#Structural Constraints]

batch_summary:
  total: 8
  admit: 1
  reserve: 2
  reject: 5
  new_factors: [F006]
---

# batch_005 判决报告

> [!abstract] 总览
> ==新方向== [[../../directions/fundamental_technical_cov|Fundamental×Technical Covariance]] 首轮。8 候选 → ==1 admit==, 2 reserve, 5 reject。
> 新方向首批表现：Cov 类信号（T001）整体偏弱（ICIR 0.2-0.3），但 style 干净。CsRank 交互项（T002）被 vol 污染。==突破：C008 营收增长×低估值 ICIR=0.331, max_corr=0.167 — 与 candlestick 因子库完全正交的 fundamental 信号==。

| 候选 | 信号 | ICIR | style_r² | max_corr | 裁决 |
|---|---|---|---|---|---|
| C001 | Cov(turnover,PE,60) | -0.225 | ==0.078== | 0.229 | reserve (弱但干净) |
| C002 | Cov(turnover,PB,60) | -0.261 | 0.322 | 0.363 | reject (CP04) |
| C003 | Corr(turnover,PE,20) | ERROR | — | — | reject (CP01 compute_error) |
| C004 | Cov(amount,PS,60) | -0.336 | 0.271 | 0.257 | reserve (borderline) |
| C005 | CsRank(PE)×CsRank(tur) | -0.329 | 0.381 | 0.461 | reject (CP04) |
| C006 | CsRank(-PB)×CsRank(tur) | -0.157 | 0.303 | 0.300 | reject (CP03+CP04) |
| C007 | EPS变化×CsRank(tur) | 0.053 | 0.090 | ==0.072== | reject (CP03 无信号) |
| **C008** | **营收增长×CsRank(-PB)** | ==0.331== | 0.272 | ==0.167== | ==**admit → [[../../factors/F006\|F006]]**== |

---

## C001 — RESERVE

### CP01
Hard gates: all_pass。coverage=0.95, sign=-1。

### CP02
机制对齐：**aligned**。Cov(turnover_rate, pe_ratio, 60) 衡量换手率与 PE 在 60 天内的协方差。负 IC 说明高协方差（换手和估值同步变化）的股票短期表现差——可能是"投机炒作估值泡沫"的信号。

### CP03
统计强度：**weak**。IC=-0.018, ICIR=-0.225。mt_bucket=low。D1 年度 IC 不稳定。ls_tstat=-3.7（显著但偏低）。

### CP04
风险干净度：**acceptable**。==style_r2=0.078==——非常干净。协方差结构不是 Barra 能解释的。

### CP05
冗余：**low**。max_corr=0.229——与 candlestick 因子正交。

### CP06
稳定性：stable。

---

## C002 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP04 style_r2=0.322
> Cov(turnover, PB) 被 book_to_price 风格污染。

---

## C003 — REJECT

### CP01
Hard gates: ==compute_error==。Corr(turnover, PE, 20) 预处理后全为 NaN——可能是 20 天窗口内 PE 变动太小导致标准差为零。

---

## C004 — RESERVE

### CP01
Hard gates: all_pass。

### CP02
机制对齐：**aligned**。Cov(amount, PS, 60) 衡量成交金额与市销率的协方差。PS 是收入基础估值，比 PE 更稳定。

### CP03
统计强度：**borderline**。IC=-0.046, ICIR=-0.336。mt_bucket=low。ls_tstat=-5.5（显著）。

### CP04
风险干净度：**borderline**。style_r2=0.271。Reserve 等待更多证据。

### CP05
冗余：**low**。max_corr=0.257。

### CP06
稳定性：**stable**。

---

## C005 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP04 style_r2=0.381
> CsRank(PE) × CsRank(turnover) 两个排名的乘积被 vol + value 风格共同污染。

---

## C006 — REJECT

### CP01
Hard gates: all_pass。

> [!failure] 拒绝：CP03+CP04
> ICIR=-0.157 弱 + style_r2=0.303。但 ls_tstat=-9.2 异常高——可能是 Q1/Q5 极端组的效应（非单调的分组结构）。

---

## C007 — REJECT

### CP01
Hard gates: all_pass。

> [!failure] 拒绝：CP03 无信号
> EPS 绝对变化 × CsRank(turnover) IC=0.003, ICIR=0.053。但 max_corr=0.072——几乎完全正交！这个方向有潜力但表达式需要改进（可能需要 CsRank(EPS_change) 而非 raw 值）。

---

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
