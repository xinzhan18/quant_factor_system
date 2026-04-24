---
batch_id: batch_038
direction: log_value_liquidity
judged_at: 2026-04-24T02:40:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 0, reject: 6}
admit_count: 0
reserve_count: 0
reject_count: 6
candidate_count: 6
mt_bucket: medium
---

# batch_038 Judge Summary

> [!abstract]+ [[directions/log_value_liquidity]] · 6 candidates
> ❌ **admit=0** · ⏸ **reserve=0** · ❌ **reject=6**
> **核心发现**: Meta-pattern 跨方向迁移**失败**——batch_036 F013 的 log-compression 元教训（解锁 sign × body acceptance）在 value × liquidity 维度不成立。6/6 候选全部 pass hard_gate 但 IC_OOS 负 (-0.023 至 -0.034)、mono 0 或 -0.1/-0.6、incr_ic 全负 (-0.016 至 -0.029) 作为 F009 overnight-intraday 反转簇的弱化载体。**元教训**：log 非线性压缩不是通用 edge extractor，在 sign × sign 结构上是 regime-noise-suppressor，在 value × liquidity 上反而**载入 reversal 簇**。
> **MT Budget**: cumulative 186 → **192** · direction 0 → **6** · bucket `medium`

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🔴·🔴·🟡·🔴·🟡 | IC_OOS=-0.029 mono=0.0 incr=-0.029 | CsRank(pb) × log(amt/mean); Q5 one-paddle | [[batches/batch_038/candidates/C001]] |
| C002 | ❌ reject | 🔴·🔴·🟡·🔴·🟡 | IC_OOS=-0.028 mono=-0.1 incr=-0.027 | CsRank(pb) × log(turnover/mean); F009 反转簇 | [[batches/batch_038/candidates/C002]] |
| C003 | ❌ reject | 🔴·🔴·🟡·🔴·🟡 | IC_OOS=-0.032 mono=-0.1 incr=-0.029 | CsRank(ps) × log(amt/mean); value 通道未载入 | [[batches/batch_038/candidates/C003]] |
| C004 | ❌ reject | 🔴·🔴·🟡·🔴·🟡 | IC_OOS=-0.034 mono=-0.6 incr=-0.028 | CsRank(pe) × log(turnover/mean); cum_dd=-87.8 | [[batches/batch_038/candidates/C004]] |
| C005 | ❌ reject | 🔴·🔴·🟡·🔴·🟡 | IC_OOS=-0.028 mono=0.0 incr=-0.028 | CsRank(pb) × log(vol/mean); 同病 | [[batches/batch_038/candidates/C005]] |
| C006 | ❌ reject | 🔴·🔴·🟡·🔴·🟡 | IC_OOS=-0.023 mono=0.0 incr=-0.016 | C001 + 5d smooth; 平滑没救 rank | [[batches/batch_038/candidates/C006]] |

## 跨候选对比

- **方向整批 disconfirmation**：6/6 IC_OOS 负，mono 0 或负，incr_ic 全负——log-compression 在 csi1000 value × liquidity 维度**反向**信号（不是 value × liquidity alpha，是 overnight-intraday 反转簇载体）。与 F009/F007/F006 family 整簇 -0.18 至 -0.26 负相关，机制级簇冗余。
- **元教训修正 batch_036 结论**：F013 log-compression 工作**仅**因为原始信号结构（sign × body）已在 csi1000 被规整为二值 ±1，log 权重的非线性只调整尾部；value × liquidity 中 value (CsRank) 已是 [0,1] 连续，log 对 liquidity 端的压缩不对应 edge—— value 端在 csi1000 小盘根本不载 alpha（CP04 vol_20d 主导 exposure 8-9，value 通道 book_to_price/ep_ratio ≈ 0.2-0.3 极弱）。
- **机制诊断**：log_value_liquidity 候选的真实载体 = CsRank(PB/PS/PE) 作分组器 × log(abnormal liquidity) 作反转触发器——小盘 PB 分散度低、PS/PE 噪声大，Value leg 退化为"分组器"，Liquidity leg 承载 short-term reversal，合成信号与 F009 overnight-intraday spread 整族反向共振。
- **方向级结论**：hypothesis "meta-pattern 跨方向迁移" 证伪。`log_value_liquidity` 首批即死，不值得第二批。

## Thread 进展

> [!failure]+ T001 [[directions/log_value_liquidity#T001]] — `[✗ DISPROVEN batch_038]`
> pb × log abnormal (amount/turnover/volume) 四变体 + 5d smooth 全部反向 IC、全部库 reducer。PB rank 在 csi1000 不载 value alpha。

> [!failure]+ T002 [[directions/log_value_liquidity#T002]] — `[✗ DISPROVEN batch_038]`
> ps × log(amt) + pe × log(turnover) 同病。横扩 ps/pe 维度未改变机制——log × value × liquidity 整体是 overnight-intraday 反转簇的 value-weighted 包装。

## 方向级反思

**hypothesis 完全证伪**：log_value_liquidity 首批即死，6/6 reject，direction 应 `exploring → dead`（与 trend_quality_gated 模式相同：单批即决定性证伪）。

**升格 lessons.md 候选**：
- **Meta-pattern 跨方向迁移需独立验证**：log-compression 在 sign × body acceptance (F013) 有效 ≠ 在 value × liquidity 有效；non-linear 压缩的 regime-robust 性质取决于**被压缩对象是否为独立的噪声源**，在 sign-structure 中 sign(body) 是规整二值、log(amount) 承载独立信息；在 value-liquidity 中 value leg 已是 cross-section rank 的连续变量、log 对 liquidity 端的压缩与 value 合成成"反转簇包装"
- **csi1000 小盘 value leg 基本失效**：PB/PS/PE cross-section rank 在小盘 universe 不载独立 alpha（value_liquidity_interaction T001/T003 同样结论）；log 包装无法复活

**Calibration**：6/6 reject，无 over-rejection——signal 都是反向 + 库 reducer + Q5 一桨驱动，reject 稳健。不触发校准。
