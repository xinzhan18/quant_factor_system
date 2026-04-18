---
name: factor-report
description: Phase 4 后台 subagent — 为 admitted 因子写 Obsidian Markdown 深度报告
user_invocable: true
---

# /factor-report — 因子深度报告（后台 subagent）

## 职责

为每个 admitted 因子生成 `vault/factors/F{id}.md` 深度分析报告。在 Phase 4 ARCHIVE 的 Step 3 作为**后台 subagent** 被 `/factor-mine` dispatch。

## 前置条件（由 Phase 4 生成）

| 资源 | 位置 | 生成者 | 必选 |
|---|---|---|---|
| `vault/factors/F{id}.yaml` | factor metadata | `factor_writer.allocate_and_write_factor` (Step 1) | ✅ |
| `_packets/report_packet_F{id}.md` | 单一输入 packet | `report_packer.write_report_packet` (Step 2) | ✅ |
| `vault/factors/F{id}/report_data.json` | 6-analyzer 完整指标 | `ReportDataBuilder.save_for_vault` (Step 2b) | ⚠️ 可缺 |
| `vault/factors/F{id}/*.png` | Plotly 图表 | `ReportDataBuilder.save_for_vault` (Step 2b) | ⚠️ 可缺 |

如果 `chart_builder` 未注入或运行失败，packet 的 `## Available Charts` 会明确声明"无图可嵌"——此时写纯文字报告，**绝不**用 `![[...]]` 语法引用不存在的图。

## 数据流向

```
Phase 4 Step 1:  factor.yaml 分配 F{id}
              ↓
Phase 4 Step 2a: ReportDataBuilder（可选 chart_builder 回调）
                 ├── Qlib 取 factor + price
                 ├── 6 analyzer（IC / Profit / Decay / Uniqueness / Scorer / ...）
                 ├── → vault/factors/F{id}/report_data.json
                 └── → vault/factors/F{id}/*.png
              ↓
Phase 4 Step 2b: report_packer
                 ├── 读 factor.yaml + judge.md#C{id} + direction.md#Hypothesis
                 ├── 扫 vault/factors/F{id}/*.png 生成 available_charts 列表
                 └── → _packets/report_packet_F{id}.md（内嵌 available_charts）
              ↓
Phase 4 Step 3:  /factor-report subagent（本 skill）
                 ├── 读 packet（R3 单一输入）
                 └── → vault/factors/F{id}.md
```

## 两层数据源

| 数据源 | 生成者 | 内容 | 用途 |
|---|---|---|---|
| `report_packet_F{id}.md` | Phase 4 Python | factor YAML + judge 判决摘要 + direction 上下文 + **available_charts 白名单** | Section 0（指标卡）+ Section 8（判决追溯）+ Section 10（研究上下文） |
| `report_data.json` | ReportDataBuilder（6-analyzer pipeline） | 完整指标（IC 时序、分组收益、衰减、分布、独特性、综合评分） | Section 1-7 分析段（可选：缺失则退化为纯文字） |
| `*.png` | ReportDataBuilder（Plotly 图表） | PNG 图表（IC 时序、月度热力图、分组、净值、衰减、雷达等） | `![[F{id}/chart.png]]` 嵌入，**仅限 packet `## Available Charts` 列出的文件名** |

## 沙箱协议（5 条规则）

| # | 规则 | 说明 |
|---|---|---|
| 1 | **唯一输入** | `_packets/report_packet_F{id}.md`（含 available_charts 白名单）+ 该 packet 明确列出的 `vault/factors/F{id}/*.png` 图表文件。**不读其他文件**（特别是 result.yaml / judge.md / registry YAML） |
| 2 | **唯一输出** | `vault/factors/F{id}.md` — 不写其他位置，不修改 YAML/图表 |
| 3 | **禁止外部调用** | 不调 Qlib / DB / 网络 / subprocess；不自己算指标 |
| 4 | **禁止 Follow link** | 不跟踪 packet 中的 `[[wiki link]]`（packet 已内嵌所有需要的上下文） |
| 5 | **失败隔离** | on_failure → 写 `_subagent_failures.log`，主循环不受影响 |

完成后执行：`research commit-report F{id}`（独立 commit，不合并进主 archive commit）。

## 图表白名单规则（最高优先级）

Packet 的 `## Available Charts` 段声明 **vault/factors/F{id}/ 里真实存在的 PNG**。Subagent 必须严格遵守：

```
For each chart you want to embed:
  IF chart_name IN packet.available_charts:
      embed ![[F{id}/chart_name.png]]
  ELSE:
      skip that entire section (narrative + image)
      DO NOT write ![[...]] — the file does not exist
```

**如果 available_charts 为空**：整份报告不得出现任何 `![[...]]` 嵌入。Section 1-7 退化为基于 `factor_record` 和 judge synthesis 的纯文字分析。

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
- 数据源：`report_data.json → predictive_power`（summary IS/OOS + daily_rank_ic + ic_by_year + ic_by_month）
- IC 均值在 IS/OOS 的一致性
- 年度 IC 逐年分析：哪些年份强/弱？是否依赖特定市场制度？
- 月度 IC 分布：是否有季节性？
- 尝试嵌入（需在 available_charts 中）：`ic_timeseries`、`monthly_heatmap`

### Section 2 — 盈利能力（Profitability）
- 数据源：`report_data.json → profitability`（quintile returns + ls_stats + monotonicity）
- IS/OOS 分组收益对比（Q1-Q5）
- L/S 策略特征：Sharpe、Sortino、Calmar、最大回撤
- 年度分组收益分解
- 尝试嵌入：`quintile_bar`、`cumulative_returns`、`annual_group_returns`

### Section 3 — 风险归因（Risk Attribution）
- 数据源：`report_packet → factor_record.risk_metrics`（`style_r_squared` / `alpha_survival_ratio`）+ `factor_record.validation_metrics.barra_residual_ic`（若有）
- Barra 风格暴露解读：`style_r_squared` 越高越拥挤
- `alpha_survival_ratio` 解读：Barra 残差 IC / raw IC
- **不嵌入图表**（当前 builder 未产出 risk/barra 图）
- **注意**：不要读 `result.yaml` 原始 barra 字段——所有风险数字都由 Phase 2 蒸馏进 factor.yaml 的 `risk_metrics` 然后进入 packet

### Section 4 — 信号稳定性（Stability）
- 数据源：`report_data.json → predictive_power.daily_rank_ic`（rolling IC 来自同一序列）
- Train→Validation 衰减：对比 `predictive_power.summary.is.rank_ic_mean` vs `.oos.rank_ic_mean`
- 月度 IC 中最差 / 最好的 quarter（从 ic_by_month 推）
- 尝试嵌入：`rolling_ic`、`cumulative_ic`（若 ic analyzer 产出）

### Section 5 — 衰减与可交易性（Decay & Tradability）
- 数据源：`report_data.json → decay_tradability`（ic_by_period + half_life + factor_turnover + factor_autocorr）
- IC 按持有期衰减 [1,2,5,10,20,60 天]
- 半衰期 + 最优换仓频率
- 因子自相关 + 换手率
- 尝试嵌入：`ic_decay`

### Section 6 — 独特性（Uniqueness）
- 数据源：`report_data.json → uniqueness`（max_corr + incremental_ic + per-factor correlation profile）
- 与库内因子逐一相关性对比
- 增量 IC（在已有因子基础上的增量预测力）
- 尝试嵌入：`correlation_bar`

### Section 7 — 分布与覆盖（Distribution）
- 数据源：`report_data.json → decay_tradability.distribution`（若 DecayAnalyzer 计算）
- IS/OOS 分布对比（均值、标准差、偏度、峰度）
- 极端值占比
- 尝试嵌入：`distribution`、`coverage`

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

- **数据来源**：`_packets/report_packet_F{id}.md`（唯一入口）+ `vault/factors/F{id}/report_data.json`（可选，由 ReportDataBuilder 产出的 5-analyzer 数据）
- **不自行计算指标**：所有数字来自 packet 的 YAML summary 或 report_data.json
- **不读 result.yaml / judge.md / factor.yaml 原文件**：packet 已蒸馏所有需要的信息
- **不读 registry / DB**：R3 单一输入原则
- **图表嵌入白名单**：`![[F{id}/<name>.png]]` 仅限 packet 的 `## Available Charts` 列出的 name。没有这个名字就跳过整段图表叙事
- **Obsidian 格式**：`==highlight==`、`> [!note]` / `> [!warning]` / `> [!danger]` callout、`[[F{id}]]` wikilink
- **中文为主**：分析叙述用中文，关键术语保留英文（IC、ICIR、Sharpe、Barra 等）
