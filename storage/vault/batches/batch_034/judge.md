---
batch_id: batch_034
direction: value_liquidity_interaction
judged_at: 2026-04-23T16:20:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
batch_summary: {total: 5, admit: 0, reserve: 0, reject: 5}
admit_count: 0
reserve_count: 0
reject_count: 5
candidate_count: 5
mt_bucket: medium
---

# batch_034 Judge Summary

> [!abstract]+ batch_034 · [[directions/value_liquidity_interaction]] · 5 candidates
> ❌ **admit=0** · ⏸ **reserve=0** · ❌ **reject=5** (C001/C002/C003/C004/C005)
> **核心发现**: `value_liquidity_interaction` 在 direction 文档里明确保留的唯一 Python Barra residual 逃生口已经跑完，而且结果比 batch_009 更收束: **5/5 全部死于 coverage < 0.80，其中 T001 额外出现 sign_flip / decay collapse，T003/T006 虽保留统计强度却仍过不了可用性硬闸。** 这不是“还差一轮工程提纯”，而是“方向在当前日频数据空间已经走到头”。
> **MT Budget**: cumulative 163 → **168** · direction 22 → **27** · bucket `medium` · 本批 low=0 / medium=0 / high=0 / hard_gate=5

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | coverage=0.706 sign_flip +0.0014→-0.0060 decay=-4.141 | C007 的 turnover-PE residual probe 一旦剥掉 `vol_20d/turnover_20d`，只剩覆盖不足且翻转的弱噪声，T001 escape hatch 失效 | [[batches/batch_034/candidates/C001]] |
| C002 | ❌ reject | hard_gate | coverage=0.706 sign_flip +0.0009→-0.0064 decay=-7.403 | 在 C001 上继续剥 `str_1m` 没有提纯信号，只把 T001 的 residual 进一步打成负 decay 噪声 | [[batches/batch_034/candidates/C002]] |
| C003 | ❌ reject | hard_gate | coverage=0.712 ic=-0.0069 decay=1.268 corr=0.027@F009 | 跨基本面 rank-diff residual 仍保持库空间低相关，但 OOS 强度太弱，T007 悖论没有变成可执行 alpha | [[batches/batch_034/candidates/C003]] |
| C004 | ❌ reject | hard_gate | coverage=0.712 ic=-0.0209 alpha_surv=1.092 incr=-0.0188 | T003 最干净的 PE self-rate baseline 在残差层依旧成立，但问题已从风格吞噬转为样本可用性不足 | [[batches/batch_034/candidates/C004]] |
| C005 | ❌ reject | hard_gate | coverage=0.712 ic=-0.0196 alpha_surv=1.205 incr=-0.0186 | T006 合成 escape hatch 也留下了干净残差，但 residual composite 仍无法跨过 coverage 硬闸 | [[batches/batch_034/candidates/C005]] |

**档位编码**: `hard_gate` 表示 CP01 已阻断，CP02-CP06 不再进入正式分档。

## 跨候选对比

- **Python residualization 修掉的不是主矛盾**: C004/C005 的 `alpha_survival` 都超过 1.0，C003 也有 `max_corr=0.027` 的极低库相关，说明这轮并不是“又被 Barra 吞噬”。真正卡死本批的是所有候选共同的 `coverage ≈ 0.706-0.712` 天花板。
- **T001 被明确证伪**: C001/C002 针对 batch_009 C007 的 residual probes 不只 coverage 不够，还同时出现 sign_flip 与负 decay。也就是说，T001 的 rank-diff 强度本身依赖被剥离掉的风格载体，而不是残差化后仍可独立存在的机制。
- **T003/T006 变成“统计上存在、工程上不可用”**: C004/C005 都通过了 `ic_oos_min`、`oos_decay`、`sign_flip` 和 `near_duplicate`，且 `barra_residual_ic` 与 raw IC 接近，说明 residual signal 的方向是真实的；但 hard gate 明确给出结论: 这种真实信号在当前日频数据里依然没有足够覆盖率。
- **不触发 threshold calibration**: 本批没有 `potential over-rejection` flag。5 个候选全部是 hard-gate reject；即便最接近可讨论的 C004/C005，`incremental_ic` 也分别为 -0.0188 / -0.0186，不满足“库空间独立且正增量”的错杀诊断条件。

## Thread 进展

> [!failure]+ T001 [[directions/value_liquidity_interaction#T001]] — `[✗ DISPROVEN batch_034]`
> batch_009 C007 留下的“turnover-PE rank-diff 在 Python residual 后也许能转成 admit”假设，本轮被 C001/C002 直接关闭。两种剥离方案都落在 coverage 不足、sign_flip、负 decay 的组合上，说明 T001 的剩余 edge 没有脱离原始 style 载体而独立存活。

> [!failure]+ T003 [[directions/value_liquidity_interaction#T003]] — `[✗ DISPROVEN batch_034]`
> C004 证明 PE 自归一化变化率在 residual 层仍有真实负向 OOS IC，但这条路径最终卡死在 coverage 0.712。T003 的结论因此从“DSL 封闭”升级为“Python residual 也不能把它变成可落地因子”。

> [!success]- T006 [[directions/value_liquidity_interaction#T006]] — `[✓ ANSWERED batch_006]`
> C005 补充了一个明确的负面工程结论：三基本面 rate 合成在 residual 层依旧有 rank-order，但仍被 coverage 硬闸阻断。T006 的知识价值继续保留在“机制存在、PnL 不兑现”这一层，不再有继续挖掘的必要。

> [!failure]+ T007 [[directions/value_liquidity_interaction#T007]] — `[✗ DISPROVEN batch_034]`
> C003 是对 batch_009 C003 的 Python residual 复验。它保留了极低库相关和稳定符号，却仍因 coverage+ic_oos 双失败而 reject，意味着 T007 的“跨基本面 rank-diff 或许能在干净环境中兑现”假设也已关闭。

## 方向级反思

`value_liquidity_interaction` 现在可以正式从 `productive` 收束到 `saturated`。这一轮补齐了 batch_009 明确留下的唯一出口，而出口结论非常统一：

1. DSL 路径此前已经证明会在 `vol_20d` / `turnover_20d` 或 `str_1m` 空间里打转
2. Python residualization 这次确实把老的风格吞噬问题显著减弱了
3. 但减弱之后暴露出来的不是新 alpha，而是日频 residual probes 的共同 coverage 上限

这说明方向的剩余知识密度已经耗尽。继续在这一方向追加 batch，大概率只会重复生产“统计上还有影子、工程上不可执行”的 reject。

**方向操作**: 建议 `status: productive → saturated`，`priority: high → low`。

**复活条件**:
1. 底层字段或数据频率发生变化，使 residual probes 的 coverage 能稳定超过 0.80。
2. 可用更细粒度的 fundamentals / order-flow 数据，不再依赖日频 proxy 重建 value-liquidity interaction。
3. 因子库结构未来发生显著变化，再重新评估 C004/C005 这类“残差真实但 coverage 不足”的工程边界。
