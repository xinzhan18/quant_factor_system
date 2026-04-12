---
batch_id: batch_001
judged_at: 2026-04-12T19:35:00Z
direction: candlestick_liquidity

candidates:
  - candidate_id: C001
    verdict: reserve
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: poor, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C002
    verdict: admit
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: acceptable, CP05: low, CP06: stable}
    overrides: [{checkpoint: CP04, from: borderline, to: acceptable}]
    factor_id: F001
    referenced_context: [lessons.md#Structural Constraints]
    concerns: [{checkpoint: CP04, if: "alpha_survival < 0.50", then: "重审 override"}]
  - candidate_id: C003
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: poor, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C004
    verdict: admit
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: borderline, CP05: low, CP06: stable}
    factor_id: F002
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C005
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: unclear, CP03: weak, CP04: acceptable, CP05: low, CP06: unstable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C006
    verdict: reserve
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: weak, CP04: acceptable, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C007
    verdict: reserve
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: borderline, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]
  - candidate_id: C008
    verdict: reject
    hard_gate_result: all_pass
    checkpoint_positions: {CP01: all_pass, CP02: aligned, CP03: strong, CP04: poor, CP05: low, CP06: stable}
    referenced_context: [lessons.md#Structural Constraints]

batch_summary:
  total: 8
  admit: 2
  reserve: 3
  reject: 3
  new_factors: [F001, F002]
---

# batch_001 判决报告

> [!abstract] 总览
> 方向 [[../../directions/candlestick_liquidity|K线微观结构×流动性]] 首轮探索。8 候选 → ==2 admit==, 3 reserve, 3 reject。
> 核心发现：影线信号 IC 强劲但 Barra vol 暴露普遍偏高（style_r2 0.21~0.61）。

| 候选 | 信号 | ICIR | Mono | style_r² | 裁决 |
|---|---|---|---|---|---|
| C001 | 上影线×换手 | -0.444 | -1.0 | 0.35 | reserve |
| **C002** | **下影线×换手** | ==-0.576== | -1.0 | 0.36 | ==admit → [[../../factors/F001\|F001]]== |
| C003 | 平方区间×换手 | -0.498 | -0.9 | 0.46 | reject |
| **C004** | **影线乘积** | -0.418 | -1.0 | ==0.21== | ==admit → [[../../factors/F002\|F002]]== |
| C005 | body ratio 均值 | 0.014 | 1.0 | 0.10 | reject |
| C006 | body ratio 波动 | 0.155 | 0.7 | 0.04 | reserve |
| C007 | 区间压缩 5/60 | -0.339 | -0.9 | 0.25 | reserve |
| C008 | 区间×换手 | -0.457 | -0.9 | 0.61 | reject |

---

## C001 — RESERVE

### CP01
Hard gates: ==all_pass==。coverage=0.95, sign=-1。

### CP02
机制对齐：**aligned**。上影线比例衡量日内卖方试探——价格被推高后无法维持。乘以换手率放大高流动性下的信号。

### CP03
统计强度：**strong**。IC_val=-0.051, ICIR=-0.444, mono=-1.0（完美单调）。mt_bucket=low（首批，累计候选=0）。search_adjusted=0.90。

### CP04
风险干净度：**poor**。style_r2=0.35，远超 0.12 阈值。alpha_survival=0.39。本质上是==波动率代理==。Reserve 而非 reject：原始信号很强，值得 vol-neutralized 变体重测。

### CP05
冗余：**low**。max_lib_corr=0.00。

### CP06
稳定性：**stable**。split_bucket=high, sign_consistency=1.0, dispersion=0.15。

---

## C002 — ==ADMIT== → [[../../factors/F001|F001]] 下影线×换手率

### CP01
Hard gates: ==all_pass==。coverage=0.95, sign=-1。

### CP02
机制对齐：**aligned**。下影线比例衡量日内买方承接——价格探底后反弹。乘以换手率捕捉"放量探底"。负 IC 说明高换手下的下影线是==主力试探出货==的痕迹，非散户支撑。

### CP03
统计强度：**strong**。IC_val=-0.064, ==ICIR=-0.576==（batch 最强）, mono=-1.0。mt_bucket=low。search_adjusted=0.90。

### CP04
风险干净度：**borderline → acceptable**（==override==）。style_r2=0.36, alpha_survival=0.61。

> [!warning] Override 理由与监控条件
> (1) ICIR=-0.576 异常强劲 (2) 机制与纯 vol 不同 (3) alpha_survival > 0.60
> **监控**：后续 batch alpha_survival < 0.50 → 重审。

### CP05
冗余：**low**。max_lib_corr=0.00。

### CP06
稳定性：**stable**。split_bucket=high, sign_consistency=1.0, dispersion=0.10, ==train_val_decay=1.62==（验证期更强）。

---

## C003 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP04 不可接受
> style_r2=0.46, alpha_survival=0.58（< 0.60）。平方区间算子 = 实现波动率度量 = ==Barra vol 代理==。

---

## C004 — ==ADMIT== → [[../../factors/F002|F002]] 影线乘积

### CP01
Hard gates: ==all_pass==。==coverage=0.99==（batch 最高）。sign=-1。

### CP02
机制对齐：**aligned**。影线乘积量化"十字星"程度——多空双方剧烈试探后回撤——==犹豫不决的微观结构==预示短期负收益。

### CP03
统计强度：**strong**。IC_val=-0.052, ICIR=-0.418, mono=-1.0。mt_bucket=low。coverage 最高、机制最纯。

### CP04
风险干净度：**borderline**（无 override）。==style_r2=0.21==（batch 最干净）。alpha_survival=0.44 偏低，但这是==纯价格结构信号==——不含 turnover 条件。Barra 污染来自物理正相关，非设计缺陷。

### CP05
冗余：**low**。max_lib_corr=0.00。

### CP06
稳定性：**stable**。split_bucket=high, sign_consistency=1.0, train_val_decay=1.32。

---

## C005 — REJECT

### CP01
Hard gates: all_pass。

> [!failure] 拒绝：CP03 无信号
> IC_val=0.001, ICIR=0.014。纯噪声。

---

## C006 — RESERVE

### CP01
Hard gates: all_pass。

### CP02
机制对齐：**aligned**。body ratio 波动率衡量 K 线结构不稳定性。

### CP03
统计强度：**weak**。ICIR=0.155，低于 0.30 阈值。mt_bucket=low。Reserve 观察。

### CP04
风险干净度：**acceptable**。==style_r2=0.04==（batch 最干净）。

### CP05
冗余：**low**。

### CP06
稳定性：**stable**。train_val_decay=2.74（验证期大幅增强）。

---

## C007 — RESERVE

### CP01
Hard gates: all_pass。

### CP02
机制对齐：**aligned**。短/长区间比（5d/60d）捕捉区间压缩/扩张。

### CP03
统计强度：**strong**。ICIR=-0.339——刚过 0.30 阈值。mt_bucket=low。

### CP04
风险干净度：**borderline**。style_r2=0.25, alpha_survival=0.67。信号有趣但不够强。

### CP05-CP06
冗余 low，稳定性 stable（train_val_decay=1.02——IS/OOS 近乎完美一致）。

---

## C008 — REJECT

### CP01
Hard gates: all_pass。

> [!danger] 拒绝：CP04 严重污染
> ==style_r2=0.61==（batch 最差）。区间×换手 = volatility × liquidity = ==Barra 完全覆盖==。
