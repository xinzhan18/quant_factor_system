---
direction_tag: barra_residual_alpha
status: productive
priority: high
rounds: 2
admits: 2
last_batch: batch_012
last_admits:
- F004
last_goal: Test whether Barra style residuals carry alpha orthogonal to vol_20d/str_1m
  — escape hatch from all exhausted DSL directions
last_activity: '2026-04-19T14:54:44Z'
created_batch: batch_012
members:
- F004
merged_into: null
---
# barra_residual_alpha

## Hypothesis

All existing directions hit vol_20d/str_1m style coupling as structural bottleneck — every DSL candidate either has Barra dominant style exposure or is near-duplicate of existing factors. The residual from regressing returns on Barra style factors represents idiosyncratic alpha orthogonal to known risk.

** Barra residual alpha  = Regress(Returns ~ vol_20d + str_1m + turnover_20d + log_circ_cap + book_to_price + mom_12_1 + ep_ratio) → Residuals

经济直觉：Barra 风格因子吸收了市场 common risk；如果 residual 仍携带 IC，说明存在风格无法解释的异质波动。

## Current Focus

**新方向首批 batch**：测试 Barra residual IC 是否 > 0 且独立于现有因子库（F001/F002/F003）。

## Threads

### T001: Barra residual 有效性 [✓ ANSWERED batch_012]
**Question**: Barra residual returns是否携带独立于风格因子的 alpha？
**Evidence trail**:
- [[batches/batch_012/candidates/C001|batch_012 C001]]: IC=0.024 ICIR=0.293 ls_t=7.34 Barra_residual_IC=0.033 > raw IC=0.024 → **admit → [[factors/F004]]**
- [[batches/batch_012/candidates/C003|batch_012 C003]]: Barra_residual_IC=0.033（与 C001 相当）但 style_r²=0.289 + vol_20d exposure=15.6 耦合严重 → **reserve**
**Next probes**: 扩展 Barra residual + volume 交互候选

### T002: 残差与其他因子正交性 [◉ ACTIVE]
**Question**: Barra residual 与 F001/F002/F003 的增量 IC 是否 > 0？
**Evidence trail**:
- [[batches/batch_012/candidates/C001|batch_012 C001]]: incremental_ic=0.032 max_corr=0.15（F002） → 正交
**Next probes**: 下一批验证 C003 incremental_ic=0.022 是否 admit

## Known Failures
- C002: sign_flip + oos_decay 双杀（IS→OOS alpha 逆转）
- C004: 5d rolling residual IC=0.007 < 0.008（太弱）
- C005: 20d momentum residual IC=-0.0035（方向反转）

## Narrative Log
### 2026-04-19 [[batches/batch_012/judge|batch_012]]
**admit=1 / reserve=1 / reject=3**

Barra residual alpha 方向首批验证假设成立：
- **C001 admit**（barra_residual_return）：IC=0.024 ICIR=0.293 ls_t=7.34 Barra_residual_IC=0.033 > raw IC=0.024；incremental_ic=0.032 全新机制空间
- **C003 reserve**：Barra_residual_IC=0.033 但 style_r²=0.289 + vol_20d exposure=15.6，耦合严重
- **C002/C004/C005 reject**：IC 不足或 sign_flip

**Thread 进展**：
- T001 answered：Barra residual alpha 假设验证成立
- T002 active：C001 证明增量 IC=0.032 > 0

**下一步**：
1. 下一批扩展 Barra residual + volume 交互候选
2. 监控 C003（若 style_r² 改善可 admit）
3. 注意 2021 后 Barra residual edge 衰减趋势

## Related
- [[lessons#Structural Constraints]]  （Barra style coupling 教训）
- [[amount_volatility_signal]]  （vol_20d 天花板）
- [[value_liquidity_interaction]]  （DSL 空间穷尽）
