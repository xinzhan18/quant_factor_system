---
batch_id: batch_040
direction: vwap_proxy_signals
judged_at: 2026-04-24T03:35:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: admit, factor_name: vwap_overnight_spread}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 1, reserve: 0, reject: 5}
admit_count: 1
reserve_count: 0
reject_count: 5
candidate_count: 6
mt_bucket: medium
---

# batch_040 Judge Summary

> [!abstract]+ [[directions/vwap_proxy_signals]] · 6 candidates
> ✅ **admit=1** (C004 → vwap_overnight_spread) · ⏸ **reserve=0** · ❌ **reject=5**
> **核心发现**: Synthesized VWAP = `$amount/$volume` 通道首批即兑现——**跨 session VWAP-prevclose** (C004) 通过 admit 标准 (IC_OOS=0.011 mono=0.60 ls_t=3.79 alpha_surv=0.68 incr=0.012 max_corr=0.17@F002)。**纯日内 VWAP-close** (C001-C003/C006) 全部 mono=0.10 weak rank-order——日内 VWAP/close 没有 cross-section 可聚合持续偏离，跨 session 加入 overnight 维度才解锁信号。
> **MT Budget**: cumulative 198 → **204** · direction 0 → **6** · bucket `medium`（C004 mt_bucket=low 唯一豁免）

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🟡·🔴·🟡·🟢·🟡 | IC=+0.027 mono=0.10 ls_t=1.65 | raw VWAP-close: 强 IC + weak mono = Q1 一桨驱动 | [[batches/batch_040/candidates/C001]] |
| C002 | ❌ reject | 🟡·🔴·🟡·🟢·🟢 | IC=+0.021 mono=0.10 ls_t=1.04 | C001 5d agg, IC↓ | [[batches/batch_040/candidates/C002]] |
| C003 | ❌ reject | 🟡·🔴·🔴·🟡·🟢 | IC=+0.018 mono=0.10 alpha_surv=0.32 | C001 20d agg, 持续偏离假设证伪 | [[batches/batch_040/candidates/C003]] |
| C004 | ✅ admit | 🟢·🟡·🟡·🟢·🟡 | IC=+0.011 **mono=+0.60** ls_t=+3.79 incr=+0.012 max_corr=0.17 | 跨 session VWAP-prevclose 整合 overnight + 日内 | [[batches/batch_040/candidates/C004]] · [[factors/F014]] |
| C005 | ❌ reject | 🟢·🟡·🔴·🔴·🟡 | IC=-0.017 mono=-0.90 incr=-0.013 | VWAP-open 5d clean reversal 但 F012 reducer | [[batches/batch_040/candidates/C005]] |
| C006 | ❌ reject | 🟡·🔴·🔴·🟡·🟢 | IC=+0.018 mono=0.10 | 与 C003 数学等价 (X/c vs (X-c)/c) | [[batches/batch_040/candidates/C006]] |

## 跨候选对比

- **C001-C003/C006 共同 weak mono**：4 个纯日内 VWAP-close 形态（raw, 5d agg, 20d agg, ratio agg）全部 mono_oos=0.10。强 IC + weak mono = "横截面相关性靠少数 outlier，rank-order 不成立"。证伪 hypothesis 中"日内 VWAP/close 偏离 5d/20d 聚合"假设。
- **C004 跨 session 维度突破**：把 same-day close 换成 prev close 引入 overnight 信号 → mono 从 0.10 跳到 **0.60**，ls_t 从 1.04 涨到 3.79，alpha_surv 从 0.32-0.49 涨到 0.68，max_corr 从 0.20 降到 0.17。这是 hypothesis 中"VWAP gap"形态的兑现——synthesized VWAP 在 cross-session 维度才有 alpha。
- **C005 反转旗：clean 但不可 admit**：mono_OOS=-0.90 是批内最强 rank-order，OOS_t=-3.03 显著反转，但 incr_ic=-0.013 是 F012 amihud 的 reducer。"sign-flipped 强信号 + 库 reducer" 同症状已在 batch_037 / batch_038 / batch_039 见过——csi1000 reversal cluster 的另一种载体。
- **Generator dedup 缺陷 (C003/C006)**：`(X-c)/c` 与 `X/c` 加法常数不变性下 cross-section rank 等价（4-5 位精度一致），未去重浪费 1 个 mt_budget 槽。建议 generator 增加常数不变性 dedup。
- **方向兑现**：1/6 admit，且 admit 的是预期方向（VWAP gap = paper-derived overnight maxim）。

## Thread 进展

> [!success]+ T001 [[directions/vwap_proxy_signals#T001]] — `[✓ ANSWERED batch_040]`
> C004 admit → **vwap_overnight_spread**。VWAP-prevclose (跨 session) 是 hypothesis 中 spread 形态的兑现。VWAP-close / VWAP-open 同 thread 子形态（C001/C005）全部 fail（weak mono / library reducer）。

> [!failure]+ T002 [[directions/vwap_proxy_signals#T002]] — `[✗ DISPROVEN batch_040]`
> C002/C003/C006 价格归一化聚合 5d/20d 全部 mono=0.10 weak。"VWAP/close ratio 5d/20d 聚合" 假设证伪——日内 VWAP-close 偏离没有 cross-section 可聚合持续性。

## 方向级反思

`vwap_proxy_signals` 方向首批 1 admit + T001 ANSWERED + T002 DISPROVEN。**核心机制**：synthesized VWAP `$amount/$volume` 在跨 session 维度（vs prev close）才解锁 alpha；同 session VWAP-close 偏离不携带 cross-section 信息。F014 是当前库第 13 个独立 admit，max_corr 全部 ≤ 0.18，独立性最强。

**方向操作**：T001 ANSWERED + T002 DISPROVEN，方向 saturated（仅 6 candidates 即决出）。Python 在 Phase 4 frontmatter 自动 update。

**Calibration**：C005 clean reversal 被 incr_ic 负 reject，符合 lessons 中"library reducer = 不能 admit" 准则。无错杀。
