---
generated_at: 2026-04-24T19:22:38Z
round: 46
total_active_directions: 13
total_factors_admitted: 14
last_batch: batch_046
last_consolidation_round: null
---

# 🗺️ Factor Research Index

> [!info] MOC · Map of Content
> 路口页。人看下方 Bases 三表；**LLM 启动读此文件顶部 Cockpit 块**（派生状态 + 下一步指令）；拿数据用 `PYTHONPATH=src python3 -m research memory snapshot`。

<!-- BEGIN COCKPIT -->

> [!note]+ 🧭 LLM Cockpit
> **状态** · round=**46** · phase=`null` (idle) · no batch in flight
> **上一批** · [[batches/batch_046/judge|batch_046]] → [[directions/microstructure_illiquidity]] · admit=**1**/6 (reserve=1, reject=4) · direction.status=`productive`
> **健康** · rounds_since_consolidation=**2** · active_directions=**13**
> **⚠️ 预警** · 空 factor.md: F015
>
> **🎯 下一步（按优先级）**
> 1. ⚠️ **修空报告**：F015 的 `.md` 为空或缺 H1 → 对每个 F{id} 重新 dispatch `/factor-report` subagent
> 2. 🧭 **硬性前置**：`research doctor`（drift 检测）→ `snapshot`（数据）→ 读目标 `directions/{tag}.md` → 进 `/factor-idea`

<!-- END COCKPIT -->

<!-- BEGIN HOT-TOPICS-LLM -->
> [!warning]- 🔥 Hot Topics（LLM 维护）
> 当前无活跃跨批模式。`/pattern-scout` 只允许改写本块。
<!-- END HOT-TOPICS-LLM -->

<!-- BEGIN INSIGHT -->
> [!tip] 💡 最近洞察 · 2026-04-23 round 29（trigger: manual — 首次 consolidation，deferred at batch_021）
> **Rewrite targets**: `lessons.md` + 13 `directions/*.md`（全量重写；INDEX 上半段由 Python cockpit 维护，无 LLM rewrite）
>
> **Key changes**:
> - **lessons.md**：精简冗余、升格反复出现的经验；Data Facts / Operator Registry / Path Selection / Structural Constraints / Metric Semantics 五段硬事实原样保留
> - **证伪后改写 hypothesis（加 ⚠️ 标记）**：`asymmetric_momentum` / `fundamental_momentum` / `return_distribution_signals` / `return_momentum_acceleration` / `turnover_structural_signal` / `vol_shock_signals` —— 5 个 dead 方向，元教训升格为系统级
> - **部分证伪（保留方向但加 scope）**：`intraday_price_formation` / `overnight_intraday_split` —— saturated 方向的"日内对称抵消律"、"数学结构吸收律"升格至 Lessons
> - **新方向摘要**：`barra_residual_alpha` 从散 thread 合并为 5 类 orthogonalization 路径；`value_liquidity_interaction` 7 个 threads 压缩 narrative 至 58%
> - **升格的系统级经验**：
>   - sign-conditional daily return 拆分在日频自然放大 regime 敏感度 —— 无条件聚合（如 F010）更稳
>   - magnitude-based vol shock 在 A 股 csi1000 全部被 `vol_20d` 结构性吸收（4 次跨方向独立确认）
>   - PE/PB/PS 纯变化率（rate of change）在 csi1000 不构成独立 alpha，alpha_survival 普遍 < 0.60
>   - Turnover 结构稳定性（CV / rank-std）优势在二阶算子下被抹掉 —— 仅 `变化率` 维度存活
>   - `Std / Mean` 与 `amount CV` 同源；`corr=0.999` 是 near_duplicate 明确信号
>
> **体积**：lessons 167 行保持 / directions 累计从 ~1850 行压到 ~1680 行（约 91%，目标 ≤80% 未完全达标；叙事密度高的 dead 方向保留 evidence trail 导致行数偏高）
>
> **触发**：手动 —— batch_021 时因 context budget 跳过了自动触发（`[skip-consolidate] reset rounds_since_last=0`），之后 8 轮未再达标；本次一次性消化累积 8 批（batch_022-029）的经验
>
> **Commit**: —（待本次 commit 后填入）
> — [[_meta/consolidation_log|完整总结]]
<!-- END INSIGHT -->

## 🎯 方向总览 (Bases)

![[_bases/directions.base]]

## 📚 因子库 (Bases)

![[_bases/factors.base]]

## 📊 最近 Batch (Bases)

![[_bases/recent_batches.base]]

---

> [!abstract]- 系统状态
> - Round: **46** · Admitted: **14** · Active directions: **13**
> - Last batch: **batch_046**
> - Last consolidation: **—**
> - 格式 audit：运行 `research audit index` 检查漂移
