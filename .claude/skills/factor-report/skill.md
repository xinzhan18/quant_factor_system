---
name: factor-report
description: Phase 4 后台 subagent — 为 admitted 因子写 Obsidian Markdown 深度报告
user_invocable: true
---

# /factor-report — 因子深度报告（后台 subagent）

## 职责

为每个 admitted 因子生成 `vault/factors/F{id}.md` 深度分析报告。在 Phase 4 ARCHIVE 的 Step 3 作为**后台 subagent** 被 dispatch。

## 沙箱协议

- **输入**：`_packets/report_packet_F{id}.md`（单一文件，R3）
- **输出**：`vault/factors/F{id}.md`（单一文件）
- **禁止**：读任何其他文件 / 调 Qlib / 调 DB / 调网络 / Follow `[[wiki link]]`（packet 已内嵌所有需要的信息）
- **完成后**：`research commit-report F{id}`（独立 commit）
- **失败**：写 `_subagent_failures.log`，主循环不受影响

## 报告结构

```markdown
# F{id} — {name}

## Section 0 — Top Insight
核心洞察一句话 + 经济学逻辑 + 毒舌评论 + 核心指标卡片

## Section 1 — 6 维度指标
IC / Quintile / Stability / Redundancy / Feasibility / Risk 逐维深度分析

## Section 2 — 逐图解读
IC 时序、分组收益、衰减曲线、Barra 暴露雷达等

## Section 3 — Judge Verdict Trail
录取推理过程（从 report_packet 的 Judge Synthesis 段摘取）

## Section 4 — Research Context
Direction hypothesis 引用 + library positioning
```

## 关键约束

- **R4 不重算**：所有指标直接消费 report_packet 中的 Phase 2 result.yaml 数值，不重新跑 IC/Barra
- **report_packet 里已经内嵌了所有上下文**（direction excerpt + judge synthesis + nearest factor），不需要额外文件访问
- **Obsidian 格式**：使用 `==highlight==`、`> [!warning]` callout、`[[F{id}]]` wikilink 格式
