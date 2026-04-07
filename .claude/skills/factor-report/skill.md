---
name: factor-report
description: 为已录取因子生成 Obsidian Markdown 深度分析报告（富格式 + 逐图叙事 + 经济学解读）
user_invocable: true
---

> **⚠️ 自主模式**：本 skill 执行时不得停下来询问用户。图表缺失跳过该图继续生成。只在系统级错误时停止。

# Factor Report — 深度资产报告

## 目标

为 **已录取因子**（admit / replace）生成正式 Obsidian Markdown 深度分析报告。三个核心要求：

1. **分层阅读** — 顶部快速概览（30 秒决策）+ judge 裁决 + 折叠式证据（5 分钟评审）+ 折叠式深度分析
2. **Obsidian 富格式** — callout、highlight、foldable、math、tag 全部用上
3. **逐图深度叙事** — 每张图单独嵌入，配 2-3 段深度分析

## 用法

单因子：`/factor-report R005`
全部因子：`/factor-report all`
批次摘要：`/factor-report summary batch_003`

## 执行流程

### Step 1：构建数据 + PNG

```bash
PYTHONPATH=src python3 -m report.builder --factor-id FACTOR_ID --vault
```

输出 `storage/evidence/vault/assets/FXXX/` 下的 `report_data.json` 和所有 PNG。

### Step 2：收集上下文

读取以下文件，为叙事提供完整语境：

| 来源 | 路径 | 用途 |
|------|------|------|
| report_data.json | `assets/FXXX/report_data.json` | 所有数值、图表路径、available_charts |
| factor registry | `storage/registry/factors/factor_FXXX.yaml` | 元数据 |
| research_result | `storage/batches/{batch}/research_result.yaml` | execute evidence 全量 |
| judge_report | `storage/batches/{batch}/judge_report.yaml` | 裁决理由 |
| logic card | `storage/logic/cards/{logic_id}.yaml` | hypothesis / thesis |
| manifest | `storage/batches/{batch}/manifest.yaml` | 实验设计 |

### Step 3：生成 Obsidian Markdown

输出：`storage/evidence/vault/factors/FXXX <name>.md`

---

## ⚠️ 条件图表嵌入规则（最高优先级）

```
CRITICAL: 读取 report_data.json → available_charts 列表。
ONLY embed charts whose name appears in that list.
如果某张图 NOT in available_charts → 跳过该图的 ![[]] 嵌入 AND 其叙事段落。
永远不要为不存在的图写 ![[]]。

Pattern:
- "ic_timeseries" in available_charts → ![[assets/FXXX/ic_timeseries.png|600]]
- "ic_timeseries" NOT in available_charts → 完全跳过该小节
```

这条规则适用于所有章节中的所有图表嵌入。

---

## 写作规范

### Obsidian 格式要求

| 元素 | 用法 | 示例 |
|------|------|------|
| `> [!tip]` | 关键发现、正面信号 | OOS 增强、高 Sharpe |
| `> [!warning]` | 风险提示、弱点 | Short-side 依赖、高相关 |
| `> [!info]` | 背景知识、方法说明 | 什么是 ICIR、为什么用 MAD |
| `> [!example]-` | 可折叠数据表（默认折叠）| 年度明细、完整相关矩阵 |
| `> [!danger]` | 致命弱点 | gate fail、sign flip |
| `> [!abstract]` | 章节摘要（每章开头） | 2-3 句话提炼本章核心 |
| `> [!success]` | Admit 裁决 | Judge verdict = admit |
| `> [!fail]` | Reject 裁决 | Judge verdict = reject |
| `==text==` | 高亮关键数字 | ==IC = -0.033==、==Sharpe 3.42== |
| `$formula$` | 数学公式 | $IC = \text{corr}(r_{factor}, r_{forward})$ |
| `%%comment%%` | 生成备注（阅读视图不可见） | %%data source: report_data.json%% |

### 逐图叙事规范

**禁止**连续嵌入多张图。每张图必须单独出现，配以下结构：

```markdown
#### 图表标题（中文描述性标题）

> [!info]- 阅读指南
> 这张图展示的是……横轴代表……纵轴代表……

![[assets/FXXX/chart_name.png|宽度]]

**第一，……**（具体数字 + 经济含义）

**第二，……**（与其他图表/指标的交叉验证）

**第三，……**（对实盘的含义）
```

### 叙事深度要求

每段叙事必须体现三层：

1. **数据层**：引用具体数字，用 `==highlight==` 标出关键值
2. **机制层**：解释为什么这个数字是这样的，连接到经济逻辑
3. **实践层**：对组合构建、风控、再平衡有什么启示

---

## 报告结构模板

### Frontmatter

```yaml
---
id: "FXXX"
name: <name>
tags:
  - factor
  - <category>
  - <family_id>
  - grade-<A|B|C|D>
category: <category>
source_type: <dsl|python>
logic_id: <logic_id>
route_type: <route_type>
experiment_lineage_tag: <ELT>
family_id: <family_id>
expression: "<expression>"
direction: <long|short>
batch: <batch>
admitted_at: <date>
decision: <admit|replace>
composite_grade: <S|A|B|C|D>
sample_policy_version: <version>
validation_window_id: <window>
verdict: <admit|reserve|reject|replace>
judge_reason_codes: "<top 3 codes, comma-separated>"
holdout_review_required: <true|false>
ic_mean_validation: <value>
ic_ir_validation: <value>
monotonicity_validation: <value>
alpha_survival_ratio: <value>
max_lib_corr: <value>
risk_model_review_bucket: <bucket>
---
```

---

### Tier 1：Quick Reference（始终可见）

这是报告最重要的部分——读者 30 秒内做出判断。

```markdown
# FXXX — <name>

> [!success] Verdict: ADMIT | Grade: ==A== (==78.3/100==)
> <一句话总结：因子本质 + 核心发现 + 综合评级>

| Metric | In-Sample | Out-of-Sample |
|--------|-----------|---------------|
| Rank IC Mean | … | ==…== |
| Rank ICIR | … | ==…== |
| Win Rate | … | … |
| t-stat | … | ==…== |
| n_days | … | … |
| Monotonicity | — | ==…== |

> [!tip] 核心判断
> <IS→OOS 增强/衰减？衰减比 = X。对实盘意味着什么？>
```

注意：
- Verdict callout 类型取决于裁决：`> [!success]` for admit, `> [!fail]` for reject, `> [!warning]` for reserve
- 如果 "radar" in available_charts，在 KPI 表后嵌入：`![[assets/FXXX/radar.png|500]]`

---

### Tier 2：Judge Verdict（始终可见，NEW）

**数据来源**：`report_data.json → judge` section

```markdown
## Judge Verdict

> [!abstract] 6-Dimension Assessment
> Effect=<bucket>, Stability=<bucket>, Redundancy=<bucket>,
> Feasibility=<bucket>, Risk Model=<bucket>, Mechanism=<bucket>
```

#### 6D 评估雷达图

如果 "verdict_radar_6d" in available_charts：

```markdown
![[assets/FXXX/verdict_radar_6d.png|500]]

<解读每个维度的评分：哪些是强项（3/3），哪些是短板（1/3 或 2/3）。
与 composite score 的维度得分交叉验证。>
```

#### Reason Codes

从 `judge.candidate_verdict.reason_codes` 渲染表格：

```markdown
### Reason Codes

| Code | Severity | Implication |
|------|----------|-------------|
| strong_validation_effect | info | IC/ICIR 通过强度阈值 |
| moderate_style_exposure | medium | 部分信号被 Barra 风格吸收 |
```

如果 "reason_code_bar" in available_charts：
```markdown
![[assets/FXXX/reason_code_bar.png|500]]
```

#### Holdout Review

仅当 `judge.candidate_brief.holdout_ic_mean` 不为 null 且 "holdout_comparison" in available_charts 时包含此节：

```markdown
### Holdout Review

![[assets/FXXX/holdout_comparison.png|500]]

<叙事：Validation IC vs Holdout IC 对比。
Decay ratio = X，含义是什么？holdout 是否确认了信号？>
```

---

### Tier 3：Evidence Sections（折叠式，评审用）

每个 section 包裹在 `> [!example]- 标题` 中，默认折叠。

**重要**：每个小节内的图表仍然遵循"逐图叙事"规范——每张图单独嵌入 + 2-3 段分析。但整体比 Tier 4 更简洁。

#### 3.1 预测能力

```markdown
> [!example]+ 预测能力（Predictive Power）
>
> 图表：ic_timeseries, cumulative_ic, rolling_ic, ic_distribution, monthly_heatmap
>
> （以下每张图 only if in available_charts）
>
> #### IC 时序走势
>
> > [!info]- 阅读指南
> > 横轴为交易日，纵轴为每日截面 Rank IC。蓝色为训练期，红色为验证期。
>
> ![[assets/FXXX/ic_timeseries.png|600]]
>
> **第一，……**
> **第二，……**
> **第三，……**
>
> ---
>
> #### 累积 IC
>
> ![[assets/FXXX/cumulative_ic.png|600]]
>
> <叙事>
>
> ---
>
> #### 滚动 IC（20/60/120 日窗口）
>
> ![[assets/FXXX/rolling_ic.png|600]]
>
> <叙事>
>
> ---
>
> #### IC 分布
>
> ![[assets/FXXX/ic_distribution.png|600]]
>
> <叙事>
>
> ---
>
> #### 月度 IC 热力图
>
> ![[assets/FXXX/monthly_heatmap.png|700]]
>
> > [!example]- 年度 IC 明细
> > | Year | IC | ICIR | Win Rate |
> > |------|-----|------|----------|
> > | ... | ... | ... | ... |
>
> <叙事>
```

#### 3.2 盈利能力

```markdown
> [!example]+ 盈利能力（Profitability）
>
> 图表：quintile_bar, quintile_returns_oos, cumulative_returns, long_short, annual_group_returns
>
> #### 分组年化收益
> ![[assets/FXXX/quintile_bar.png|600]]
> <叙事：Q1→Q5 梯度、单调性、long/short contribution>
>
> ---
>
> #### 验证期分组收益（Execute Evidence）
> （only if "quintile_returns_oos" in available_charts）
> ![[assets/FXXX/quintile_returns_oos.png|600]]
> <叙事>
>
> ---
>
> #### 累积净值曲线
> ![[assets/FXXX/cumulative_returns.png|600]]
> <叙事>
>
> ---
>
> #### 多空策略表现
> ![[assets/FXXX/long_short.png|600]]
> <叙事>
>
> > [!warning] 做空风险
> > <如果 short_contribution 高，讨论做空执行风险>
>
> ---
>
> #### 年度分组收益热力图
> ![[assets/FXXX/annual_group_returns.png|700]]
>
> > [!example]- 完整分组统计
> > <quintile stats 表格>
>
> <叙事>
```

#### 3.3 风险归因

```markdown
> [!example]+ 风险归因（Risk Attribution）
>
> 图表：style_exposure_bar, alpha_waterfall（均来自 execute evidence，conditional）
>
> #### Barra 风格因子暴露
> （only if "style_exposure_bar" in available_charts）
> ![[assets/FXXX/style_exposure_bar.png|600]]
> <叙事：哪个风格暴露最大？R² 意味什么？>
>
> ---
>
> #### Alpha 存活瀑布图
> （only if "alpha_waterfall" in available_charts）
> ![[assets/FXXX/alpha_waterfall.png|600]]
> <叙事：Raw IC → Cap-Neutral → Residual 各层损失>
```

#### 3.4 信号稳定性

```markdown
> [!example]+ 信号稳定性（Stability）
>
> 图表：support_window_ic, stability_summary（均来自 execute evidence，conditional）
>
> #### 多验证窗口 IC 一致性
> （only if "support_window_ic" in available_charts）
> ![[assets/FXXX/support_window_ic.png|600]]
> <叙事：sign consistency、最弱窗口>
>
> ---
>
> #### 稳定性总览
> （only if "stability_summary" in available_charts）
> ![[assets/FXXX/stability_summary.png|700]]
> <叙事：IS→OOS 衰减比、4 维稳定性得分>
```

#### 3.5 衰减与可交易性

```markdown
> [!example]+ 衰减与可交易性（Decay & Tradability）
>
> 图表：ic_decay, distribution, coverage, feasibility_dashboard
>
> #### IC 衰减曲线
> ![[assets/FXXX/ic_decay.png|600]]
> <叙事：衰减/反衰减、半衰期、再平衡频率含义>
>
> ---
>
> #### 因子值分布
> ![[assets/FXXX/distribution.png|600]]
> <叙事：IS vs OOS 分布对比、偏度/峰度>
>
> ---
>
> #### 数据覆盖率
> ![[assets/FXXX/coverage.png|600]]
> <叙事>
>
> ---
>
> #### 交易可行性仪表盘
> （only if "feasibility_dashboard" in available_charts）
> ![[assets/FXXX/feasibility_dashboard.png|600]]
> <叙事：各项指标绿灯/红灯>
>
> > [!example]- IC 衰减明细
> > | 持有期 | IC | 衰减比 |
> > |--------|-----|--------|
> > | ... | ... | ... |
```

#### 3.6 独特性

```markdown
> [!example]+ 独特性（Uniqueness）
>
> #### 因子库相关矩阵
> ![[assets/FXXX/correlation_bar.png|700]]
> <叙事：最高相关因子是谁？为什么高？替代风险？>
>
> > [!example]- 完整相关矩阵
> > | Factor | Correlation |
> > | ... | ... |
```

#### 3.7 综合评分

```markdown
> [!example]+ 综合评分（Composite Score）
>
> ![[assets/FXXX/radar.png|600]]
>
> | 维度 | 得分 | 等级 | 解读 |
> |------|------|------|------|
> | Predictive Power | X | ? | <一句话> |
> | Signal Stability | X | ? | <一句话> |
> | Profitability | X | ? | <一句话> |
> | Monotonicity | X | ? | <一句话> |
> | OOS Robustness | X | ? | <一句话> |
> | Uniqueness | X | ? | <一句话> |
> | Decay Resistance | X | ? | <一句话> |
>
> <最强/最弱维度分析，木桶效应>
```

---

### Tier 4：Deep Analysis（折叠式，深度阅读用）

#### 4.1 研究脉络与经济机制

```markdown
> [!note]- 研究脉络与经济机制
>
> ### 市场假说
>
> **Logic [[LXXX]]** 的核心命题：……
>
> ### 经济机制
>
> <深度叙事：2-3 段，每段一个论点。
> 1. 这个因子在捕捉什么市场现象？
> 2. 为什么这个现象会产生 alpha？行为金融 / 微观结构 / 信息不对称
> 3. 这个 alpha 为什么不会被套利掉？>
>
> ### 实验设计
>
> **Route = <type>** 的选择理由：……
>
> > [!info] 为什么不选其他 route？
> > ……
>
> ### 评估制度
>
> | 参数 | 设置 | 理由 |
> |------|------|------|
> | Universe | CSI 1000 | …… |
> | Preprocess | MAD(5) + Zscore | …… |
> | Sample Policy | Train ≤ 2023, Val = 2024 | …… |
```

#### 4.2 批判性审查

```markdown
> [!danger]- 批判性审查
>
> > [!danger] 一句话毒舌
> > <尖锐但准确的一句话总结，直击要害>
>
> ### 致命弱点
>
> <编号列表，每条：弱点描述 + 数据支撑 + 最坏情况推演>
>
> ### 改进方向
>
> <编号列表，每条：具体建议 + 预期效果 + 可行性评估>
>
> > [!warning] 使用警告
> > <对实盘使用此因子的风险提示和注意事项>
```

#### 4.3 系统意义

```markdown
> [!tip]- 系统意义
>
> ### 验证了什么
>
> <这个因子对研究系统的贡献：验证了哪个 hypothesis？
> 打开了什么新方向？对 family 结构有什么启示？>
>
> ### 后续方向
>
> <具体的 follow-up 建议，每条关联到 logic/family/route>
```

---

### 尾部

```markdown
---

> [!info] 资产目录
> 所有图表原始文件位于 `storage/evidence/vault/assets/FXXX/`

%%Report generated: <date>%%
```

### Step 4：更新 Factor Library 总览页

更新 `storage/evidence/vault/Factor Library.md`。

---

## 关键约束

- report 不重新计算评估，只消费上游结构化结果
- frontmatter 只放稳定索引字段，不放 narrative
- **数值必须来自结构化结果**（report_data.json / research_result.yaml），不由 LLM 编造
- **条件图表嵌入**：只嵌入 `available_charts` 中存在的图，不存在则跳过整个小节
- composite_score 进 frontmatter（作为 `composite_grade`），正文展示完整分解
- report 只读取 guarded_writer 落地后的最终状态
- **每张图必须单独嵌入 + 单独叙事**，禁止连续堆叠
- 叙事中每个论点必须引用具体数字（==高亮==），不说"表现良好"这类空话
- Judge 数据来自 `report_data.json → judge` section，不需要单独读 judge_report.yaml
- **所有 callout 默认展开**：使用 `> [!example]+`（加号）而非 `> [!example]-`（减号）

### 数据-图表一致性规则（CRITICAL）

**叙事引用的数字必须与对应图表的数据源一致**。不同图表使用不同数据源：

| 图表 | 数据源 | 单位 |
|------|--------|------|
| quintile_bar | `profitability.stats[].ann_return` | 年化收益率（如 12.8%） |
| quintile_returns_oos | `execute_evidence.evaluation.quintile_returns_holdout` | **日均收益率**（如 0.63%）——原始值为 decimal（0.006256），×100 转百分比 |
| cumulative_returns | `profitability.stats` 时间序列 | 累积净值 |
| annual_group_returns | `profitability.annual_group_returns` | 年度收益率（如 4.9%） |
| long_short | `profitability.ls_stats` | 年化（ann_return, sharpe, max_dd） |

**常见错误**：
- `quintile_returns_holdout` 的 decimal 值 0.006256 应表示为 ==0.63%==，**不是** 6.26%
- quintile_bar 图使用年化收益，quintile_returns_oos 图使用日均收益——不能混用
- 写某张图的叙事时，引用的数字必须与该图的数据源匹配

## 执行模式

**Report 生成应作为后台 subagent 执行**（5-8 分钟/因子）。调用方使用 `Agent(run_in_background=true)`。

批量模式：为每个 admitted factor 启动独立后台 subagent，并行生成。
