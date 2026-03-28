---
name: factor-report
description: 为已录取因子生成 Obsidian Markdown 分析报告（含 LLM 叙事分析和 PNG 图表）
user_invocable: true
---

# 因子报告生成器（Obsidian Vault 版）

生成包含 7 章分析 + LLM 叙事的 Obsidian Markdown 因子报告，输出到 `storage/vault/`。

## 用法

```
/factor-report 001          # 单因子报告
/factor-report all          # 所有因子报告
```

## 管道流程

### 第1阶段：构建报告数据 + 导出 PNG（Python）

**单因子：**
```bash
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
PYTHONPATH=src python3 -m report.builder --factor-id FACTOR_ID --vault
```

**全部因子：**
```bash
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
PYTHONPATH=src python3 -c "
import psycopg2
from mining.config import MiningConfig
conn = psycopg2.connect(MiningConfig().system.database.connection_string)
cur = conn.cursor()
cur.execute(\"SELECT factor_id FROM factor_meta WHERE status = 'admitted'\")
ids = [r[0] for r in cur.fetchall()]
conn.close()
print(' '.join(ids))
" | xargs -n1 -I{} bash -c 'echo "Building F{}..." && PYTHONPATH=src python3 -m report.builder --factor-id {} --vault'
```

这会在 `storage/vault/assets/FXXX/` 下生成 18 张 PNG 图表和 `report_data.json`。

### 第2阶段：生成 Obsidian Markdown（LLM）

对每个因子，读取 `storage/vault/assets/FXXX/report_data.json`，然后用 Write 工具生成 Obsidian Markdown 文件。

**文件路径**: `storage/vault/factors/FXXX <name>.md`

**report_data.json 结构（v2 schema）：**
```
factor            — 基本元数据
predictive_power  — IC 分析 (ICAnalyzer)
profitability     — 分组收益 (ProfitAnalyzer)
risk_attribution  — 风险归因 (L0 时为 null)
conditional       — 条件分析 (ConditionalAnalyzer)
decay_tradability — 衰减与可交易性 (DecayAnalyzer)
uniqueness        — 独特性 (UniquenessAnalyzer)
composite         — 综合评分 (CompositeScorer)
```

**Markdown 模板结构：**

```markdown
---
id: "XXX"
name: <factor_name>
category: <category>
expression: "<qlib_expression>"
batch: <batch>
admitted_at: <date>
data_level: L0
ic_mean_is: <predictive_power.summary.is.rank_ic_mean>
ic_mean_oos: <predictive_power.summary.oos.rank_ic_mean>
icir_is: <predictive_power.summary.is.icir>
icir_oos: <predictive_power.summary.oos.icir>
monotonicity: <profitability.monotonicity>
ls_sharpe: <profitability.ls_stats.sharpe>
composite_score: <composite.composite_score>
composite_grade: <composite.composite_grade>
tags:
  - factor
  - <category>
---

# FXXX <factor_name>

> [!info] 基本信息
> **表达式**：`<qlib_expression>`
> **类别**：<category> | **批次**：<batch> | **录取日期**：<date>
> **数据等级**：L0（OHLCV）| **综合评分**：<composite_score> (<composite_grade>)

## KPI 摘要

| 指标 | IS | OOS |
|------|-----|-----|
| RankIC (Spearman) | <is.rank_ic_mean> ± <is.rank_ic_std> | <oos.rank_ic_mean> ± <oos.rank_ic_std> |
| IC (Pearson) | <is.ic_mean> ± <is.ic_std> | <oos.ic_mean> ± <oos.ic_std> |
| ICIR | <is.icir> | <oos.icir> |
| IC > 0 Win Rate | <is.win_rate> | <oos.win_rate> |
| t-statistic | <is.t_stat> (p=<is.p_value>) | <oos.t_stat> (p=<oos.p_value>) |
| 多空 Sharpe | — | <ls_stats.sharpe> |
| 单调性 | — | <monotonicity> |
| 综合评分 | — | <composite_score> (<composite_grade>) |

## 构造逻辑与经济解读

### 表达式拆解

（逐步拆解 Qlib 表达式的每个操作符和参数，200+ 字）

### 经济理论

（因子背后的学术理论和市场机制，200+ 字，3-4 个不同理论角度）

### A股市场背景

（T+1、涨跌停、融券限制等制度因素如何影响该因子，150+ 字）

---

## 1. 预测能力 — "这个信号有多强？"

![[FXXX/ic_timeseries.png]]
![[FXXX/ic_distribution.png]]
![[FXXX/rolling_ic.png]]
![[FXXX/cumulative_ic.png]]
![[FXXX/monthly_heatmap.png]]

> [!note]- 年度明细
> | 年份 | RankIC Mean | ICIR | Win Rate | 市场环境 |
> |------|------------|------|----------|----------|
> | (从 predictive_power.annual 数据填充，regime 来自 conditional 的 merge) |

（LLM 叙事：对比 IS 与 OOS 的 IC 和 ICIR，解读 t 检验显著性结果，分析时序趋势、年度波动和月度规律。必须引用具体数字。）

**结论**：（一句话回答"这个信号有多强？"）

---

## 2. 盈利能力 — "信号能稳定赚钱吗？"

![[FXXX/quintile_bar.png]]
![[FXXX/cumulative_returns.png]]
![[FXXX/long_short.png]]
![[FXXX/is_vs_oos_bar.png]]
![[FXXX/annual_group_returns.png]]

> [!note]- 分组统计
> | 指标 | Q1 | Q2 | Q3 | Q4 | Q5 | L/S |
> |------|----|----|----|----|----|----|
> | 年化收益 | | | | | | |
> | Sharpe | | | | | | |
> | 最大回撤 | | | | | | |
> | (从 profitability.stats 填充) |

（LLM 叙事：分析 L/S 收益来源（long vs short contribution），讨论 A 股融券限制对空头端的影响，评估单调性和 IS/OOS 一致性。必须引用具体数字。）

**结论**：（一句话回答"信号能稳定赚钱吗？"）

---

## 3. 风险归因 — "这是 Alpha 还是 Beta？"

> [!info] 风险归因需要行业和市值数据（L1）
> 当前数据等级为 L0（OHLCV），无法进行量化风险归因。以下为基于因子表达式的定性分析。

（LLM 叙事：分析因子表达式可能暴露的风格因子（size, momentum, volatility, liquidity），推断行业偏好。150+ 字。）

**结论**：（一句话回答"这是 Alpha 还是 Beta？"——基于定性分析）

---

## 4. 条件分析 — "信号什么时候管用？"

![[FXXX/conditional_ic.png]]
![[FXXX/annual_ic.png]]

> [!note]- 市场环境 IC
> | 环境 | IC Mean | 观察天数 |
> |------|---------|---------|
> | 牛市 | | |
> | 震荡 | | |
> | 熊市 | | |
> | (从 conditional.regime_ic 填充) |

> [!note]- 波动率环境 IC
> | 环境 | IC Mean | 观察天数 |
> |------|---------|---------|
> | 高波动 | | |
> | 低波动 | | |
> | (从 conditional.vol_regime_ic 填充) |

（LLM 叙事：给出具体的使用建议——什么市场环境下应该加仓/减仓该因子，而非仅描述现象。必须引用具体数字。）

**结论**：（一句话回答"什么时候应该使用/回避这个因子？"）

---

## 5. 衰减与可交易性 — "信号能撑多久？"

![[FXXX/ic_decay.png]]
![[FXXX/autocorrelation.png]]
![[FXXX/distribution.png]]
![[FXXX/coverage.png]]

> [!note]- IC 衰减表
> | 持仓周期 | IC | IC 比率 (vs 1d) |
> |---------|-----|-----------------|
> | 1d | | 1.00 |
> | 2d | | |
> | 5d | | |
> | 10d | | |
> | 20d | | |
> | 60d | | |
> | (从 decay_tradability.ic_by_period 填充) |

（LLM 叙事：基于半衰期给出明确的换仓频率建议，分析因子自相关对换手率的影响，评估因子值分布和覆盖率。必须引用具体数字。）

**结论**：推荐换仓频率：X 天

---

## 6. 独特性 — "因子库还需要这个因子吗？"

![[FXXX/correlation_bar.png]]

> [!note]- 库内相关性
> | 因子 | 相关系数 |
> |------|---------|
> | (从 uniqueness.top5 填充) |
>
> **最大相关性**：<max_corr> (与 <max_corr_factor>)

（LLM 叙事：评估该因子是否提供增量信息，与最相关因子的区别何在。如果 max_corr 接近 0.7 阈值，讨论风险。）

**结论**：（一句话回答"因子库还需要这个因子吗？"）

---

## 7. 综合评分

![[FXXX/radar.png]]

> [!note]- 评分明细
> | 维度 | 得分 | 权重 | 数据可用 |
> |------|------|------|---------|
> | 预测能力 | | 25% | |
> | 信号稳定性 | | 20% | |
> | 盈利能力 | | 15% | |
> | 单调性 | | 10% | |
> | OOS 稳健性 | | 15% | |
> | 独特性 | | 10% | |
> | 衰减抗性 | | 5% | |
> | (从 composite.dimensions 填充) |
>
> **综合评分**：<composite_score> / 100 (<composite_grade>)

（LLM 叙事：解读雷达图形态，分析该因子的核心优势和最大短板。）

---

## 批判性审查

> [!danger] 一句话毒舌
> （一句尖锐的总结，必须提及具体数字）

（3-4 段实质性批评，必须引用报告中的具体数字。涵盖：实际信号强度评估、因子拥挤度风险、结构性弱点、IS/OOS 一致性。300+ 字。）

> [!warning]- 关键弱点
> - **弱点1**：具体数字说明
> - **弱点2**：具体数字说明
> - **弱点3**：具体数字说明

> [!tip]- 改进方向
> - 可操作的建议1
> - 可操作的建议2
> - 可操作的建议3
```

**图表名称对照（18 张 PNG）：**

| 章节 | 图表名称 | 来源 |
|------|---------|------|
| Ch1 预测能力 | ic_timeseries, ic_distribution, rolling_ic, cumulative_ic, monthly_heatmap | ICAnalyzer |
| Ch2 盈利能力 | quintile_bar, cumulative_returns, long_short, is_vs_oos_bar, annual_group_returns | ProfitAnalyzer |
| Ch4 条件分析 | conditional_ic, annual_ic | ConditionalAnalyzer |
| Ch5 衰减 | ic_decay, autocorrelation, distribution, coverage | DecayAnalyzer |
| Ch6 独特性 | correlation_bar | UniquenessAnalyzer |
| Ch7 综合评分 | radar | CompositeScorer |

**LLM 叙事质量关键规则：**
- 以**资深量化分析师**视角撰写，所有叙事用**中文**，技术术语保留英文
- 每段必须引用 report_data.json 中的具体数字（IC 值、Sharpe、回撤等）
- 每章以决策问题开头，叙事围绕回答该问题展开
- 经济解释提供 3-4 个不同的理论角度
- 包含 A 股市场特定背景（T+1、涨跌停、融券限制）
- 批评审查必须尖锐、机智、有数据支撑
- 图片嵌入用 `![[FXXX/chart_name.png]]`（Obsidian wikilink 语法）
- **只嵌入** report_data.json 中各章节 charts 字段实际存在的图片

### 第3阶段：重建总览页（LLM）

读取所有因子的 report_data.json，用 Write 工具生成/更新 `storage/vault/Factor Library.md`。

**总览页结构：**

```markdown
---
title: Factor Library
tags:
  - index
---

# Factor Library

> <N> factors | Last updated: <date>

## 汇总表

| ID | Name | Category | IC (OOS) | ICIR | Grade | Score | Link |
|----|------|----------|----------|------|-------|-------|------|
| (从各因子 report_data.json 聚合) |

## 按类别分布

| Category | Count | Avg |IC| | Best Factor |
|----------|-------|----------|-------------|
| (按类别聚合统计) |

## 评分分布

| Grade | Count | Factors |
|-------|-------|---------|
| S | | |
| A | | |
| B | | |
| C | | |
| D | | |
```

### 第4阶段：报告完成

告知用户：
- 因子报告路径：`storage/vault/factors/FXXX <name>.md`
- 总览页路径：`storage/vault/Factor Library.md`
- 提示用户在 Obsidian 中打开 `storage/vault/` 作为 vault
