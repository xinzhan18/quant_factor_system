---
batch_id: batch_011
direction: intraday_price_formation
judged_at: '2026-04-19T13:55:00Z'
candidates:
  - {candidate_id: C001, verdict: reject, hard_gate_reason: ic_oos_too_low + mono_sign_flip}
  - {candidate_id: C002, verdict: reject, hard_gate_reason: mono_sign_flip}
  - {candidate_id: C003, verdict: reject, hard_gate_reason: mono_sign_flip}
  - {candidate_id: C004, verdict: reject, hard_gate_reason: ic_oos_too_low + mono_sign_flip}
  - {candidate_id: C005, verdict: reject, hard_gate_reason: near_duplicate}
  - {candidate_id: C006, verdict: reject, hard_gate_reason: near_duplicate}
  - {candidate_id: C007, verdict: reject, factor_name: null}
  - {candidate_id: C008, verdict: reject, hard_gate_reason: mono_sign_flip}
batch_summary: {total: 8, admit: 0, reserve: 0, reject: 8}
admit_count: 0
reject_count: 8
reserve_count: 0
candidate_count: 8
mt_bucket: medium
---

# batch_011 Judge Summary

> [!abstract]+ batch_011 · [[directions/intraday_price_formation]] · 8 candidates
> ❌ **admit=0** · ⏸ **reserve=0** · ❌ **reject=8** (7 hard_gate + 1 rubric reject)
> **核心发现**: batch_010 F003 overnight_gap 的窗口扩展（Ref2-5 / MeanHigh2-10）全部失效——2个 ic_oos_too_low、5个 mono_sign_flip；C005/C006 near-duplicate F003（corr=0.999）；C007 EMA($close,5) 通过 hard_gate 但 CP04 alpha_surv=0.085 + incr_ic=-0.022 + 负 IC 方向，rubric reject。**F003 隔夜跳空是最优解，扩展窗口和 EMA 类信号均无法超越**
> **MT Budget**: cumulative 59 → **60** · direction 8 → **9** · bucket `medium`（本批 low=0 / med=1 / high=0）

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | ic_oos=-0.0073+mono_flip | 隔夜缺口2天版本：IC太弱且IS/OOS单调反转 | [[batches/batch_011/candidates/C001]] |
| C002 | ❌ reject | hard_gate | mono_sign_flip | 隔夜缺口3天版本：IS正向，OOS负向 | [[batches/batch_011/candidates/C002]] |
| C003 | ❌ reject | hard_gate | mono_sign_flip | 隔夜缺口5天版本：IS几乎0（0.10），OOS负 | [[batches/batch_011/candidates/C003]] |
| C004 | ❌ reject | hard_gate | ic_oos=-0.0072+mono_flip | 缺口2天+10天波幅：IC不足且单调反转 | [[batches/batch_011/candidates/C004]] |
| C005 | ❌ reject | hard_gate | near_dup F003 | F003的5天均值版本：与F003相关性0.999，无增量价值 | [[batches/batch_011/candidates/C005]] |
| C006 | ❌ reject | hard_gate | near_dup F003 | F003的EMA版本：与F003相关性0.999，无增量价值 | [[batches/batch_011/candidates/C006]] |
| C007 | ❌ reject | 🔴·🟡·🔴·🔴·🟡 | IC=-0.036 alpha_surv=0.085 incr_ic=-0.022 | EMA趋势信号通过hard_gate但CP04双重poor（alpha_surv=0.085 + style_r²=0.314）+ incr_ic=-0.022库reducer + 负IC方向 | [[batches/batch_011/candidates/C007]] |
| C008 | ❌ reject | hard_gate | mono_sign_flip | EMA偏差比：IS正向，OOS负向 | [[batches/batch_011/candidates/C008]] |

## 跨候选对比

- **F003 护城河**：C005/C006 与 F003 near_duplicate（corr=0.999）——F003 overnight_gap_normalized 的隔夜机制在 extended windows 和 EMA 变体上都无增量信号
- **mono_sign_flip 集中爆发**：C002/C003/C008 因 IS→OOS 单调性反转被拒；隔夜缺口随 lookback 拉长而信号衰减
- **EMA 信号陷阱**：C007/C008 EMA 类信号全部 reject（一个 near_dup F003，一个 mono_sign_flip）——纯 EMA trend 信号不属于 intraday_price_formation 方向

## Thread 进展

> [!failure]+ T001 [[directions/intraday_price_formation#T001]] — `[✗ DISPROVEN batch_011]`
> batch_010 回答隔夜缺口有效；batch_011 扩展窗口（C001-C004）+ EMA 变体（C006）全部 reject。**结论：F003 隔夜跳空机制是局部最优，扩展窗口和 EMA 变体无法超越**

> [!note]+ T002 [[directions/intraday_price_formation#T002]] — `[◉ ACTIVE]`
> reject C008 (EMA 偏差比)。纯趋势信号（EMA deviation）与 hypothesis（日内价格形成）机制不符，C007 EMA($close,5) 也因 alpha_surv=0.085 证伪。**下一步**：该方向 DSL 空间实质穷尽，需考虑 Python Barra residual 或全新 hypothesis

## 方向级反思

batch_011 是 intraday_price_formation 方向第二批，8候选全部 reject。核心洞察：
1. **F003 overnight_gap 是局部最优**：扩展 Ref(close,2-5) + Mean(high,2-10) 窗口后信号衰减甚至消失；C005/C006 near_duplicate F003 证明机制本身不可扩展
2. **intraday_price_formation DSL 空间穷尽**：K线身体比（batch_010）、EMA趋势（batch_011 C007/C008）、波动率锚定（batch_010 C003/C005）全部证伪；唯一 admit 是隔夜缺口
3. **方向 ROI 归零**：intraday_price_formation hypothesis 的"纯价格信号正交于 vol_20d"仅部分成立（F003），其余路径全部失败

**下轮决策**：
- `intraday_price_formation` 方向 status → saturated
- 下一方向需全新 hypothesis：Python Barra residual 或跨字段融合
