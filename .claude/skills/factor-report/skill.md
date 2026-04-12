---
name: factor-report
description: Phase 4 后台 subagent — 为 admitted 因子写 Obsidian Markdown 深度报告
user_invocable: true
---

# /factor-report — 因子深度报告（后台 subagent）

## 职责

为每个 admitted 因子生成 `vault/factors/F{id}.md` 深度分析报告。在 Phase 4 ARCHIVE 的 Step 3 作为**后台 subagent** 被 `/factor-mine` dispatch。

## 沙箱协议（5 条规则）

| # | 规则 | 说明 |
|---|---|---|
| 1 | **唯一输入** | `_packets/report_packet_F{id}.md` — 不读其他文件 |
| 2 | **唯一输出** | `vault/factors/F{id}.md` — 不写其他位置 |
| 3 | **禁止外部调用** | 不调 Qlib / DB / 网络 / subprocess |
| 4 | **禁止 Follow link** | 不跟踪 packet 中的 `[[wiki link]]`（packet 已内嵌所有需要的上下文） |
| 5 | **失败隔离** | on_failure → 写 `_subagent_failures.log`，主循环不受影响 |

完成后执行：`research commit-report F{id}`（独立 commit，不合并进主 archive commit）。

## report_packet 的 frontmatter schema

```yaml
factor_id: F020
direction: fundamental_price_divergence
admitted_in_batch: batch_103
```

## report_packet 的 body 结构

```markdown
# Report Packet — F020

## Factor YAML Summary
```yaml
name: triple_product_80d_pb
expression: "Mul(Corr($pe_ratio, Mean($close, 80), 80), $turnover_rate)"
source_type: dsl
family_tag: fundamental_price_divergence
validation_metrics:
  ic_mean: 0.016
  ic_ir: 0.338
  ic_win_rate: 0.607
  monotonicity: 0.95
  long_short_mean: 0.007
risk_metrics:
  style_r_squared: 0.08
  alpha_survival_ratio: 0.691
```

## Direction Context
<hypothesis + most-recent thread excerpt>

## Judge Synthesis
<从 judge.md 里摘出的 ## C{id} 段，包含录取推理>

## Library Context
Nearest: F012 (corr=0.30) — 简要说明差异

## Instructions
Write a deep analytical report on F{id}. Cover the economic mechanism,
the validation evidence, the risk cleanness, and the library positioning.
Use only the information in this packet.
```

## factor.md 输出结构

使用 Obsidian 格式（`==highlight==`、`> [!warning]` callout、`[[F{id}]]` wikilink）。

### Section 0 — Top Insight
- 核心洞察一句话（一个 sentence 说清楚这个因子为什么赚钱）
- 经济学逻辑（2-3 段，解释 expression 背后的行为学/微观结构机制）
- 毒舌评论（基于因子公式本身，不是基于指标——指出明显的缺陷或过度拟合风险）
- 核心指标卡片：

```
| 维度 | 值 | 评级 |
|---|---|---|
| IC mean (val) | 0.016 | — |
| ICIR (val) | 0.338 | strong |
| Monotonicity | 0.95 | excellent |
| Alpha survival | 0.691 | good |
| Max lib corr | 0.30 vs F012 | low |
| Style R² | 0.08 | clean |
```

### Section 1 — 6 维度指标
IC / Quintile / Stability / Redundancy / Feasibility / Risk 逐维深度分析。每个维度写 2-3 段，不要只复述数字——要**解读**（比较同类因子、解释异常值、指出边界风险）。

### Section 2 — 逐图解读
对 report_packet 中的每类指标写图文并茂的叙事。主要图类型：
- IC 时序（什么时间段信号最强/最弱）
- 分组收益柱状图（Q1-Q5 排列是否严格单调，收益差异幅度）
- IC 衰减曲线（信号在不同 horizon 的衰减速度）
- Barra 暴露雷达图（7 个 style 的暴露分布）

### Section 3 — Judge Verdict Trail
从 report_packet 的 Judge Synthesis 段摘取录取推理。说明哪些 CP 是 strong、哪些是 borderline、是否有 override。

### Section 4 — Research Context
- Direction hypothesis 引用（使用 `[[directions/{direction}#Hypothesis]]` wikilink）
- Library positioning（与最近邻因子的差异分析）
- Open questions（如果有的话，来自 judge.md 的 `concerns` 字段）

## 关键约束

- **R4 不重算**：所有指标直接消费 report_packet 中的 Phase 2 result.yaml 数值，**绝不重新跑 IC/Barra/quintile**
- **不读 result.yaml 原文件**：只读 report_packet（report_packet 已把 result.yaml 的关键字段内嵌为 YAML code block）
- **不读 judge.md 原文件**：只读 report_packet 里的 Judge Synthesis 段
- **Obsidian 格式**：使用 `==highlight==`、`> [!note]` / `> [!warning]` callout、`[[F{id}]]` wikilink
