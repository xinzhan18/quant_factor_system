---
batch_id: batch_014
direction: barra_residual_alpha
judged_at: 2026-04-21T01:35:00Z
candidates:
  - {candidate_id: C001, verdict: reserve}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 1, reject: 5}
---

# batch_014 Judge Summary

> [!abstract]+ batch_014 · [[directions/barra_residual_alpha]] · 6 candidates
> ❌ **admit=0** · ⏸ **reserve=1** (C001) · ❌ **reject=5** (C002 C003 C004 C005 C006)
> **核心发现**: **vol_20d 是残差空间唯一主导维度**——C002（vol_20d-keep）corr=0.987 / C005（size-only-keep）corr=0.906 双向证明剥不剥 vol_20d 决定残差走向，size 仅边际贡献。**C003 暴露系统级 lookahead 盲区**：`close.shift(-5)/close - 1` 把 t+5 累计收益作为因子值，hard_gate 全过但 ic_oos=0.386/ls_t=83/ls_max_dd=0 是构造泄漏 artifact，非 alpha。
> **MT Budget**: cumulative 71 → **77** · direction 4 → **10** · bucket `medium` · 本批 low=0 / med=2 (C001/C003) / high=0

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ⏸ reserve | 🟡·🟡·🔴·🟡·🟡 | ic_oos=-0.063 icir=-0.42 mono=-0.7 style_r²=0.999 | 纯 vol_20d 本体 \|IC\| 大于 F004 残差 \|IC\| 但 style_r²=0.999——residualization 是 12× 清洁度 value-add | [[batches/batch_014/candidates/C001]] |
| C002 | ❌ reject | hard_gate | near_dup F004 corr=0.987 | EMA 平滑只动时序不动横截面，与 F004 cross-sectional 几乎相同 | [[batches/batch_014/candidates/C002]] |
| C003 | ❌ reject | hard_gate ✓ 但构造泄漏 | ic_oos=0.386 ls_t=83 ls_max_dd=0 (artifact) | **5d forward cumulative return 嵌入因子值**——构造性 lookahead，非真 alpha；hard_gate 时序检测盲区 | [[batches/batch_014/candidates/C003]] |
| C004 | ❌ reject | hard_gate | sign_flip + ic_oos_too_low + oos_decay=-0.37 | momentum-only strip：IS→OOS 翻号，momentum 簇带强 regime 依赖，无法单独剥离 | [[batches/batch_014/candidates/C004]] |
| C005 | ❌ reject | hard_gate | near_dup F004 corr=0.906 | size-only-keep ≈ F004——log_circ_cap 在 7-style basis 中只贡献边际信息 | [[batches/batch_014/candidates/C005]] |
| C006 | ❌ reject | hard_gate | ic_oos=0.0071 < 0.008 | residual × Sign(Δvolume_5d) 把 F004 IC 0.024 稀释到 0.007，attention-confirmation hypothesis 证伪 | [[batches/batch_014/candidates/C006]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🟠 边际 · 🔴 阻断档（misaligned/weak/poor/high/unstable）· `hard_gate` reject 不填色。

## 跨候选对比

- **vol_20d 残差空间主导（互补对照）**：
  - C002 (strip 6 styles, KEEP vol_20d) → corr 0.987 with F004 — 不剥 vol_20d ≈ 不做 residual
  - C005 (strip 6 styles, KEEP log_circ_cap) → corr 0.906 with F004 — 剥 6 个 ≈ 剥全部
  - 合流推论：**F004 的 residual 信号几乎完全来自剥离 vol_20d 这一个动作**，其余 6 个 styles 加起来贡献 < 10% 的可分离方差。下一批不必再在 7-style basis 上调整剥离子集。
- **momentum cluster 不可单独剥离（C004）**：strip(str_1m + mom_12_1) → IS +0.020 / OOS -0.0073 翻号 + ic_by_year 2021→2023 由 +0.004 衰减到 -0.012。momentum 簇是 regime-dependent factor，**Barra residual 价值来自联合剥离不是任意子集**。
- **C003 lookahead 系统盲区**：8 项 hard_gate 全过但 ic_oos=0.386 / ls_max_dd=0 / win_rate=1.0。构造问题——`close.shift(-HORIZON)/close - 1` 把 t+5 累计收益作为 t 时刻因子值，evaluator 用 returns_1d 计算 IC ⇒ 共享 close[t+1]−close[t] 项，按构造重合 ~0.45。F004 没此问题因 y 用 close 价格（非归一化）。**这是方向级元教训**：Python factor 应禁 `shift(-k)` 出现在因子值路径；hard_gate 应增 "too good to be true" 哨兵（\|ic_oos\|>0.10 / icir>1.5 / sortino=inf / max_dd=0 / win_rate=1.0 任一触发→suspicion）。
- **C001 "纯风格作为 alpha" 反例**：vol_20d 本体 \|IC\|=0.063 > F004 \|IC\|=0.024 magnitude，但 style_r²=0.999 + alpha_surv=0.54——magnitude 大不等于可用，residualization 把不可投资的 risk factor 转成可投资 alpha。reserve 痕迹但不入库（与 F004 隐性风格重复，incremental_ic=-0.046 库 reducer）。
- **MT 预算**：direction_candidates 4→10（首次跨 medium 阈值），cumulative 71→77。本批高 hard_gate fail rate（4/6）反映候选设计与现有库结构高度同源。

## Thread 进展

> [!note]+ T001 [[directions/barra_residual_alpha#T001]] — `[✓ ANSWERED batch_012]`（已回答，C003 触及但作为 spec error 不更改状态）
> C003 试图扩展 T001 假设到 5d horizon 但暴露 lookahead leak——证伪的不是 hypothesis，是构造方式。

> [!note]+ T002 [[directions/barra_residual_alpha#T002]] — `[◉ ACTIVE]`
> 5 候选全部 reject + 1 reserve（C001）：T002 的核心发现 = **vol_20d 是 residual alpha 的几乎唯一来源**（C002+C005 双向证明）。下一步必须改变 residualization 维度（不是改 7-style basis 子集），如：robust regression（quantile/median）、非线性 residualization（kernel）、新 style 加入（intraday vol/HF microstructure）。

> [!note]+ T003 [[directions/barra_residual_alpha#T003]] 🆕 — `[◉ ACTIVE]`
> 新建 thread：**Lookahead detection / construction safety**。C003 暴露 hard_gate 时序约束盲区，需要系统级哨兵。短期解：human review 高 IC 候选；长期解：AST 扫描 negative shift + 哨兵指标。

## 方向级反思

batch_014 是 barra_residual_alpha 方向首批 0 admit。组合证据：

1. **vol_20d 主导残差空间**：6 候选中 4 个（C001/C002/C005/C006）直接或间接验证了"vol_20d 是 F004 alpha 的主要承载维度"。这意味着 `barra_residual_alpha` 方向不能再靠"调整 7-style basis 子集"创新——剩余探索路径必须改残差化方法（OLS → robust regression / kernel / 新 styles）。
2. **C003 lookahead 是方法论事故**：构造错误而非信号问题。**该候选的指标必须从所有方向级 ICIR/IC 统计中排除**——否则会污染 cross-batch 比较。Phase 4 不该 admit、Phase 5 consolidation 应明确标注为 "discarded due to spec error"。
3. **C001 reserve 的处理**：subagent 给的 reserve 在 rubric 上守住了——但实际上 C001 不应当 admit 成 F{id}（CP04 poor + style_r²=0.999 + incremental_ic=-0.046 三项硬反对）。reserve 留 trace 即可，不进入 retroactive admit 候选池。
4. **方向状态**：仍 `productive`（F004 admit + batch_013 C002 reserve 仍在），但本批 0 admit 把 admit 率从 33%→25%（4 batches/2 admits），下一批若再 0 admit 应转 saturated 或开新方向。

**下批决策（batch_015）**：

- 路径 A — 同方向但换残差化方法：robust regression（Huber/quantile）、kernel residualization、加入 intraday vol style 重新 fit
- 路径 B — 开新方向：跨字段交互（PE × Barra residual / volume momentum × residual）、microstructure（intraday H-L / overnight gap × style residual）
- 选 A：barra_residual_alpha 方向 ROI 仍正，T002 仍 active，路径 A 在该方向内自然延续

无 calibration trigger（错杀 flag=0；连续零 admit=1 batch；reserve 积压 N/A；悖论复现 = vol_20d 主导是发现非悖论）。

若 batch_015 仍 0 admit，方向 `productive → saturated`，开新方向。
