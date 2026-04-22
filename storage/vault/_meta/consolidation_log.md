# Consolidation Log

Append-only history of Phase 5 CONSOLIDATION runs.

## 2026-04-23 round 29（trigger: manual — 首次 consolidation，deferred at batch_021）

**Rewrite targets**: `lessons.md` + 13 `directions/*.md`（全量重写；INDEX 上半段由 Python cockpit 维护，无 LLM rewrite）

**Key changes**:
- **lessons.md**：精简冗余、升格反复出现的经验；Data Facts / Operator Registry / Path Selection / Structural Constraints / Metric Semantics 五段硬事实原样保留
- **证伪后改写 hypothesis（加 ⚠️ 标记）**：`asymmetric_momentum` / `fundamental_momentum` / `return_distribution_signals` / `return_momentum_acceleration` / `turnover_structural_signal` / `vol_shock_signals` —— 5 个 dead 方向，元教训升格为系统级
- **部分证伪（保留方向但加 scope）**：`intraday_price_formation` / `overnight_intraday_split` —— saturated 方向的"日内对称抵消律"、"数学结构吸收律"升格至 Lessons
- **新方向摘要**：`barra_residual_alpha` 从散 thread 合并为 5 类 orthogonalization 路径；`value_liquidity_interaction` 7 个 threads 压缩 narrative 至 58%
- **升格的系统级经验**：
  - sign-conditional daily return 拆分在日频自然放大 regime 敏感度 —— 无条件聚合（如 F010）更稳
  - magnitude-based vol shock 在 A 股 csi1000 全部被 `vol_20d` 结构性吸收（4 次跨方向独立确认）
  - PE/PB/PS 纯变化率（rate of change）在 csi1000 不构成独立 alpha，alpha_survival 普遍 < 0.60
  - Turnover 结构稳定性（CV / rank-std）优势在二阶算子下被抹掉 —— 仅 `变化率` 维度存活
  - `Std / Mean` 与 `amount CV` 同源；`corr=0.999` 是 near_duplicate 明确信号

**体积**：lessons 167 行保持 / directions 累计从 ~1850 行压到 ~1680 行（约 91%，目标 ≤80% 未完全达标；叙事密度高的 dead 方向保留 evidence trail 导致行数偏高）

**触发**：手动 —— batch_021 时因 context budget 跳过了自动触发（`[skip-consolidate] reset rounds_since_last=0`），之后 8 轮未再达标；本次一次性消化累积 8 批（batch_022-029）的经验

**Commit**: —（待本次 commit 后填入）
