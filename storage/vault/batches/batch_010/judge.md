---
batch_id: batch_010
direction: intraday_price_formation
judged_at: '2026-04-19T13:35:00Z'
candidates:
  - {candidate_id: C001, verdict: reject, hard_gate_reason: mono_sign_flip}
  - {candidate_id: C002, verdict: reject, hard_gate_reason: mono_sign_flip}
  - {candidate_id: C003, verdict: reject, hard_gate_reason: sign_flip + oos_decay}
  - {candidate_id: C004, verdict: admit, factor_name: overnight_gap_normalized}
  - {candidate_id: C005, verdict: reject, hard_gate_reason: mono_sign_flip}
  - {candidate_id: C006, verdict: reject, hard_gate_reason: mono_sign_flip}
  - {candidate_id: C007, verdict: reject, hard_gate_reason: mono_sign_flip}
  - {candidate_id: C008, verdict: reject, hard_gate_reason: ic_oos_too_low + mono_sign_flip}
batch_summary: {total: 8, admit: 1, reserve: 0, reject: 7}
admit_count: 1
reject_count: 7
reserve_count: 0
candidate_count: 8
mt_bucket: low
---

# batch_010 Judge Summary

> [!abstract]+ batch_010 · [[directions/intraday_price_formation]] · 8 candidates
> ✅ **admit=1** (C004→F003) · ⏸ **reserve=0** · ❌ **reject=7** (7 hard_gate)
> **核心发现**: 首批 OHLCV-only DSL 候选中，overnight_gap_normalized (C004) 唯一通过全部 hard gates，ls_t=8.36 + 完美单调 + 9年 IC 全正，证明隔夜跳空信息携带独立 alpha；其余 7/8 全部折戟于 mono_sign_flip 或 sign_flip，说明纯价格比率类指标在 A 股市场不稳定
> **MT Budget**: cumulative 51 → **52** · direction 0 → **1** · bucket `low`（本批 low=1 / med=0 / high=0）

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | mono_sign_flip | 收盘-均高比日内逻辑合理但训练/验证单调性相反 | [[batches/batch_010/candidates/C001]] |
| C002 | ❌ reject | hard_gate | mono_sign_flip | 收盘-最低价比 / C001 镜像，同一问题 | [[batches/batch_010/candidates/C002]] |
| C003 | ❌ reject | hard_gate | sign_flip+oos_decay | 收益/波幅比日内信号方向在验证期反转，且 decay 为负 | [[batches/batch_010/candidates/C003]] |
| C004 | ✅ admit | 🟢·🟢·🟡·🟢·🟢 | ICIR=0.379 ls_t=8.36 mono=1.0 | overnight_gap_normalized：隔夜缺口相对昨日波幅的标准化，8项 hard gates 全过，9年 IC 全正 | [[batches/batch_010/candidates/C004]] · [[factors/F003]] |
| C005 | ❌ reject | hard_gate | mono_sign_flip | 收益 CV 在 20d 窗口上 IS/OOS 单调性反转 | [[batches/batch_010/candidates/C005]] |
| C006 | ❌ reject | hard_gate | mono_sign_flip | 收盘-EMA 差/EMA 比值在验证期单调性失效 | [[batches/batch_010/candidates/C006]] |
| C007 | ❌ reject | hard_gate | mono_sign_flip | 上影线比例 / C001 镜像，同一问题 | [[batches/batch_010/candidates/C007]] |
| C008 | ❌ reject | hard_gate | ic_oos_too_low+mono_sign_flip | close/open 相关性 20d IC 太弱（0.0016），且跨期反转 | [[batches/batch_010/candidates/C008]] |

## 跨候选对比

- **Style 聚合**：8 候选中 vol_20d 仍是 dominant style（6/7 非 hard_gate 候选 style_r² 0.07-0.64），C004 style_r²=0.033 相对最低
- **mono_sign_flip 集中爆发**：7/8 候选因 IS/OOS 单调性反转被拒——说明 OHLCV 纯价格比率类指标在 A 股验证期普遍不稳定
- **唯一幸存者 C004 特殊机制**：隔夜跳空 / 昨日波幅 —— 纯价格关系中唯一不需要日内持仓周期假设的信号

## Thread 进展

> [!success]+ T001 [[directions/intraday_price_formation#T001]] — `[✓ ANSWERED batch_010]`
> admit C004。回答了"K线身体比、收盘位置等纯价格指标是否携带独立于流动性因子的 alpha"——部分回答：隔夜跳空信号有效，但日内价格比率指标（K线身体比/上影线比例/EMA偏差）因 mono_sign_flip 全部失效

> [!note]+ T002 [[directions/intraday_price_formation#T002]] — `[◉ ACTIVE]`
> reject C003/C005/C006。波动率锚定价格信号（Std/Mean 类）全部 mono_sign_flip。下一步：C004 的 overnight_gap 机制值得深挖——当前 lookback=1（Ref($close,1) + Mean($high,1)），可测试 Ref($close,2)/Mean($high,3) 等变体

## 方向级反思

batch_010 是 `intraday_price_formation` 方向的首批，8候选中 1 admit（C004 overnight_gap_normalized），7 reject 全部 hard_gate。核心洞察：
1. **隔夜缺口是最稳定的 OHLCV-only 信号**：open 与前收的关系（gap）不受日内波动影响，ls_t=8.36 + 9年 IC 全正 + cum_mdd 仅 -1.15
2. **日内纯价格比率（body/range 类）全部 mono_sign_flip**：这类指标在训练期有效但验证期失效，说明它们过度适应了特定市场微观结构
3. **DSL OHLCV-only 空间可以产生 admit**：证明 hypothesis 部分成立，但路径比预期窄

下轮方向建议：
1. 深挖 C004 变体：Ref($close,2-5) + Mean($high,2-10) 不同窗口组合
2. 避开日内比率：转向 EMA偏离度、Slope类（趋势类）——C006 EMA差比已证伪
3. 方向 status 维持 `exploring`（首批即 admit，ROI 高）
