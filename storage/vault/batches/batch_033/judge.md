---
batch_id: batch_033
direction: amount_volatility_signal
judged_at: 2026-04-23T15:45:00Z
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

# batch_033 Judge Summary

> [!abstract]+ batch_033 · [[directions/amount_volatility_signal]] · 5 candidates
> ❌ **admit=0** · ⏸ **reserve=0** · ❌ **reject=5** (C001/C002/C003/C004/C005)
> **核心发现**: `amount_volatility_signal` 唯一剩余的 Python `vol_20d` residualization 逃生口也失败了，而且失败模式高度一致: **5/5 全部先死于 coverage < 0.80**。其中 C003/C005 甚至保留了不错的 OOS IC 和 decay，但在可用性硬闸前没有判决资格，说明这个方向不是“还差一轮提纯”，而是“在当前数据与实现空间里已经收束”。
> **MT Budget**: cumulative 158 → **163** · direction 24 → **29** · bucket `medium` · 本批 low=0 / medium=0 / high=0 / hard_gate=5

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | coverage=0.680 ic=0.0028 incr=0.0038 corr=0.068@F004 | cross-field residual 只留下边缘独立性，但覆盖和 OOS 强度都不够，T005 逃生口未打开 | [[batches/batch_033/candidates/C001]] |
| C002 | ❌ reject | hard_gate | coverage=0.680 sign_flip +0.0030→-0.0006 decay=-0.208 | 加上 `mom_12_1` 控制后直接把残余信号打成符号翻转噪声，说明不是简单多控一个 style 就能救 | [[batches/batch_033/candidates/C002]] |
| C003 | ❌ reject | hard_gate | coverage=0.697 ic=-0.0157 decay=1.174 corr=0.111@F012 | sign-only Corr residual 仍有真实 rank-order，但样本可用性没过线，Python 逃生口被 coverage 卡死 | [[batches/batch_033/candidates/C003]] |
| C004 | ❌ reject | hard_gate | coverage=0.711 ic=-0.0062 ls_t=-3.30 incr=-0.0018 | amount acceleration 残差版延续了历史的负向 PnL，但 OOS IC 已弱到低于硬闸 | [[batches/batch_033/candidates/C004]] |
| C005 | ❌ reject | hard_gate | coverage=0.685 ic=-0.0244 decay=0.883 corr=0.267@F001 | residualized slope 是本批统计上最像“可留样本”的 probe，却仍被覆盖率拦下，说明方向已无可执行出口 | [[batches/batch_033/candidates/C005]] |

**档位编码**: `hard_gate` 表示 CP01 已阻断，CP02-CP06 不再进入正式分档。

## 跨候选对比

- **失败模式高度同质**: 5/5 全部 `coverage < 0.80`，区间仅 0.680-0.711。这不是某个表达式偶然写坏，而是 residualization 路径在当前数据基底上的共同可用性上限。
- **T004 比 T005 更接近“有信号但不可用”**: C003/C005 都通过了 `ic_oos_min`、`oos_decay`、`sign_flip` 和 `near_duplicate`，其中 C005 还有 `ic_oos=-0.0244`、`decay=0.8827`；但由于 coverage 硬闸，主结论只能是“残差化留下了统计影子，却没有留下可入库的可交易载体”。
- **T005 被明确证伪**: C001/C002 这组 cross-field residual probes 不仅 coverage 同样不足，C002 还出现 `sign_flip` 与负 decay，说明 batch_008 C003 那条“跨字段相关性 residual 后可能脱身”的想法没有落地价值。
- **CP04 已不再是主矛盾**: 与 batch_003/batch_008 相比，本批候选的 `style_r_squared` 普遍降到 0.07-0.29，`alpha_survival` 也不差，说明 Python residualization 确实修掉了“被 vol_20d 吞噬”的老问题；但修掉风格吞噬后，暴露出来的是更根本的可用性约束。
- **不触发 threshold calibration**: 本批没有 `potential over-rejection` flag。C003/C005 虽有统计亮点，但都被 `coverage` 硬闸阻断，且 `incremental_ic` 分别为 -0.0139 / -0.0133，不满足“库空间独立 + 正增量”的错杀诊断条件。

## Thread 进展

> [!failure]+ T004 [[directions/amount_volatility_signal#T004]] — `[✗ DISPROVEN batch_033]`
> batch_003 / batch_008 留下的三个 reserve（sign-only Corr / amount acceleration / normalized slope）在 Python residualization 后仍然全部 hard-gate reject。C003/C005 证明假设里确实有 rank-order 影子，但 coverage 0.697 / 0.685 使这条 escape hatch 无法转成可执行因子。**T004 到此不是“机制不存在”，而是“当前数据空间内没有可落地实现”**。

> [!failure]+ T005 [[directions/amount_volatility_signal#T005]] — `[✗ DISPROVEN batch_033]`
> batch_008 C003 曾是 T005 最有希望的 reserve。batch_033 用两种 residualization 复验后，C001 落在 coverage+ic_oos 双失败，C002 更进一步出现 sign_flip 和负 decay。cross-field interaction 路径并没有在 Python 侧打开新轴，线程可判为关闭。

## 方向级反思

`amount_volatility_signal` 可以在这一轮正式从 `productive` 收束到 `saturated`。关键不是“本批又零 admit”这么简单，而是**方向文档里明确写着的唯一逃生口已经被完整验证过**：

1. DSL-native 空间此前已被证实反复落回 `vol_20d` 载体
2. Python residualization 的确修掉了 CP04 风格吞噬
3. 但修掉之后留下的是低 coverage / 低可用性，而不是新的可入库 alpha

这意味着后续再往这个方向继续加 batch，只会产生更多“统计上有影子、工程上不可用”的 reject，不会增加知识密度。

**方向操作**: 建议 `status: productive → saturated`，`priority: high → low`。

**复活条件**:
1. 底层数据可用性改善，能把 residualized probes 的 coverage 提到 0.80 以上。
2. 换更高频或更细粒度的数据，不再依赖日频 `$amount` proxy。
3. 库结构变化后，重新评估 batch_033 里 C003/C005 这类“有统计影子但 coverage 不达标”的残差信号。
