---
name: factor-report
description: Phase 4 后台 subagent — 为 admitted 因子写 Obsidian Markdown 深度报告
user_invocable: true
---

# /factor-report — 因子深度报告（后台 subagent）

## 职责

为每个 admitted 因子生成 `vault/factors/F{id}.md` 深度分析报告。在 Phase 4 ARCHIVE 的 Step 3 作为**后台 subagent** 被 `/factor-mine` dispatch。

## 前置条件

- `vault/factors/F{id}.yaml` 已存在（Phase 4 Step 1 已分配 F{id}）
- `_packets/report_packet_F{id}.md` 已存在（Phase 4 Step 2 Python 已生成）
- `vault/factors/F{id}/report_data.json` 已存在（ReportDataBuilder 生成，含 6-analyzer 完整数据）
- `vault/factors/F{id}/*.png` 已存在（ReportDataBuilder 生成，14 张 Plotly 图表）
- 如果缺失，先跑 `PYTHONPATH=src python3 -m report.builder --factor-id {id} --vault`

## 两层数据源

| 数据源 | 生成者 | 内容 | 用途 |
|---|---|---|---|
| `report_packet_F{id}.md` | Phase 4 Python | judge 判决摘要 + factor YAML + direction 上下文 | Section 3 判决追溯 + Section 4 研究上下文 |
| `report_data.json` | ReportDataBuilder（6-analyzer pipeline） | 完整指标（IC 时序、分组收益、衰减、分布、独特性、综合评分） | Section 0-2 全部分析段 |
| `*.png` | ReportDataBuilder（Plotly 图表） | 14 张图（IC 时序、月度热力图、分组、净值、衰减、雷达等） | 全部 `![[F{id}/chart.png]]` 嵌入 |

## 沙箱协议（5 条规则）

| # | 规则 | 说明 |
|---|---|---|
| 1 | **唯一输入** | `_packets/report_packet_F{id}.md` — 不读其他文件 |
| 2 | **输出** | `vault/factors/F{id}.md` + `vault/factors/F{id}/*.png`（图表） — 不写其他位置 |
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

目标长度：**300-400 行**。每个分析段用 "第一...第二...第三..." 的编号论证风格，不只复述数字——要**解读**。

### Section 0 — Top Insight + 核心指标卡

```markdown
> [!abstract] 核心洞察
> 一句话说清楚这个因子为什么赚钱。

> [!tip] 毒舌点评
> 基于因子公式本身的犀利评论——指出明显的缺陷、过度拟合风险、或经济机制的弱点。

| Metric | Train | Validation | 评级 |
|---|---|---|---|
| Rank IC Mean | ... | ... | — |
| ICIR | ... | ... | strong/medium/weak |
| Win Rate | ... | ... | — |
| L/S t-stat | — | ... | — |
| Monotonicity | ... | ... | — |
| Alpha Survival | — | ... | good/borderline/poor |
| Max Lib Corr | — | ... | low/medium/high |
| Style R² | — | ... | clean/borderline/poor |
```

### Section 1 — 预测能力（Predictive Power）
- 数据源：`report_data.json → predictive_power` + `result.yaml → report_card.ic_by_year`
- IC 均值在 IS/OOS 的一致性
- 年度 IC 逐年分析：哪些年份强/弱？是否依赖特定市场制度？
- 月度 IC 分布：是否有季节性？
- 嵌入 `![[F{id}/ic_timeseries.png]]` + `![[F{id}/monthly_heatmap.png]]`

### Section 2 — 盈利能力（Profitability）
- 数据源：`report_data.json → profitability`
- IS/OOS 分组收益对比（Q1-Q5）
- L/S 策略特征：Sharpe、Sortino、Calmar、最大回撤
- 年度分组收益分解
- 嵌入 `![[F{id}/quintile_bar.png]]` + `![[F{id}/cumulative_returns.png]]` + `![[F{id}/annual_group_returns.png]]`

### Section 3 — 风险归因（Risk Attribution）
- 数据源：`result.yaml → barra` + `report_card`
- Barra 7 因子暴露分析（哪个 style 主导？）
- 三层 alpha 剥离：raw IC → cap-industry neutral → Barra residual
- alpha_survival_ratio 解读
- 嵌入 `![[F{id}/radar.png]]`

### Section 4 — 信号稳定性（Stability）
- 数据源：`result.yaml → stability` + `report_card → D2`
- 分段 IC 稳定性
- Train→Validation 衰减链
- IC max drawdown + worst/best quarter
- 嵌入 `![[F{id}/rolling_ic.png]]` + `![[F{id}/cumulative_ic.png]]`

### Section 5 — 衰减与可交易性（Decay & Tradability）
- 数据源：`report_data.json → decay_tradability`
- IC 按持有期衰减 [1,2,5,10,20,60 天]
- 半衰期 + 最优换仓频率
- 因子自相关 + 换手率
- 嵌入 `![[F{id}/ic_decay.png]]`

### Section 6 — 独特性（Uniqueness）
- 数据源：`report_data.json → uniqueness` + `report_card → D6`
- 与库内因子逐一相关性对比
- 增量 IC（在已有因子基础上的增量预测力）
- 嵌入 `![[F{id}/correlation_bar.png]]`

### Section 7 — 分布与覆盖（Distribution）
- 数据源：`report_data.json → decay_tradability.distribution` + `report_card → D5`
- IS/OOS 分布对比（均值、标准差、偏度、峰度）
- 极端值占比
- 嵌入 `![[F{id}/distribution.png]]` + `![[F{id}/coverage.png]]`

### Section 8 — 判决追溯
- 数据源：`report_packet → Judge Synthesis`
- 6 个 CP 的判决结果和推理
- Override 记录和监控条件

### Section 9 — 批判性审查
- **毒舌一句话**：尖锐总结该因子的核心缺陷
- **核心弱点**：3-5 个带编号的深度分析段
- **改进方向**：具体的下一步实验建议
- **使用警告**：实盘部署需注意的风险

### Section 10 — 研究上下文
- Direction hypothesis wikilink
- Thread 引用
- 同批因子对比
- Batch 详情 wikilink

## 关键约束

- **数据来源**：`report_data.json`（完整 6-analyzer 数据 + 14 张图表）+ `report_packet`（judge 摘要 + direction 上下文）
- **不自行计算指标**：所有数字来自已有数据文件
- **不读 result.yaml 原文件**：report_data.json 已包含所有需要的指标
- **Obsidian 格式**：`==highlight==`、`> [!note]` / `> [!warning]` / `> [!danger]` callout、`[[F{id}]]` wikilink、`![[F{id}/chart.png]]` 图表嵌入
- **中文为主**：分析叙述用中文，关键术语保留英文（IC、ICIR、Sharpe、Barra 等）
