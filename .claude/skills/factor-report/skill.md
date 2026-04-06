---
name: factor-report
description: 为已录取因子生成 Obsidian Markdown 深度分析报告（富格式 + 逐图叙事 + 经济学解读）
user_invocable: true
---

# Factor Report — 深度资产报告

## 目标

为 **已录取因子**（admit / replace）生成正式 Obsidian Markdown 深度分析报告。两个核心要求：

1. **Obsidian 富格式** — callout、highlight、foldable、math、tag 全部用上，让 Obsidian 阅读视图赏心悦目
2. **逐图深度叙事** — 每张图单独嵌入，配 3-5 段深度分析：看到什么、为什么、意味着什么、对实盘有什么含义

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
| report_data.json | `assets/FXXX/report_data.json` | 所有数值、图表路径 |
| factor registry | `storage/registry/factors/factor_FXXX.yaml` | 元数据 |
| research_result | `storage/batches/{batch}/research_result.yaml` | execute evidence 全量 |
| judge_report | `storage/batches/{batch}/judge_report.yaml` | 裁决理由 |
| logic card | `storage/logic/cards/{logic_id}.yaml` | hypothesis / thesis |
| manifest | `storage/batches/{batch}/manifest.yaml` | 实验设计 |

### Step 3：生成 Obsidian Markdown

输出：`storage/evidence/vault/factors/FXXX <name>.md`

---

## 写作规范

### Obsidian 格式要求

| 元素 | 用法 | 示例 |
|------|------|------|
| `> [!tip]` | 关键发现、正面信号 | OOS 增强、高 Sharpe |
| `> [!warning]` | 风险提示、弱点 | Short-side 依赖、高相关 |
| `> [!info]` | 背景知识、方法说明 | 什么是 ICIR、为什么用 MAD |
| `> [!example]-` | 可折叠数据表 | 年度明细、完整相关矩阵 |
| `> [!danger]` | 致命弱点 | gate fail、sign flip |
| `> [!abstract]` | 章节摘要（每章开头） | 2-3 句话提炼本章核心 |
| `==text==` | 高亮关键数字 | ==IC = -0.033==、==Sharpe 3.42== |
| `$formula$` | 数学公式 | $IC = \text{corr}(r_{factor}, r_{forward})$ |
| `%%comment%%` | 生成备注（阅读视图不可见） | %%data source: report_data.json%% |
| foldable callout `-` | 详细数据表格（默认折叠）| 年度 IC 明细、全因子相关矩阵 |

### 逐图叙事规范

**禁止**连续嵌入多张图。每张图必须单独出现，配以下结构：

```markdown
#### 图表标题（中文描述性标题）

> [!info]- 阅读指南
> 这张图展示的是……横轴代表……纵轴代表……颜色编码是……

![[assets/FXXX/chart_name.png|宽度]]

这张图揭示了三个关键信息：

**第一，……**（具体数字 + 经济含义）

**第二，……**（与其他图表/指标的交叉验证）

**第三，……**（对实盘的含义：什么时候有效、什么时候失效、怎么用）

> [!warning] 注意事项（如有）
> 某某异常值 / 某某时期需要特别关注……
```

### 叙事深度要求

每段叙事必须体现以下三层理解：

1. **数据层**：引用具体数字，用 `==highlight==` 标出关键值。"IC 从 IS 期的 ==-0.0273== 增强到 OOS 的 ==-0.0325=="
2. **机制层**：解释为什么这个数字是这样的。连接到因子的经济逻辑。"这说明成交量峰值时机信号在样本外并未衰减，因为其捕捉的是一种持久的行为偏差——散户倾向于在放量上涨日追高买入"
3. **实践层**：对组合构建、风控、再平衡有什么启示。"对于月度再平衡策略，这意味着无需担心信号过快衰减；但短边 73% 的收益贡献意味着必须确保做空执行通畅"

---

## 章节模板

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
ic_mean_validation: <value>
ic_ir_validation: <value>
alpha_survival_ratio: <value>
max_lib_corr: <value>
risk_model_review_bucket: <bucket>
---
```

### 1. 概览与核心洞察

**不是**元数据表格。而是一段 3-5 句话的叙事开场，让读者立刻理解这个因子是什么、为什么有效、值不值得关注。

```markdown
# FXXX — <name>

> [!abstract] 一句话
> <因子本质>——<核心发现>——<综合评级>

<3-5 句叙事：这个因子用什么数据、捕捉什么市场现象、经济机制是什么、
OOS 表现如何、在因子库中处于什么位置>

> [!example]- 基本信息
> | 字段 | 值 |
> |------|-----|
> | Factor ID | FXXX |
> | Expression | `<expr>` |
> | Direction | <long/short> |
> | ... | ... |
```

关键：基本信息表格**折叠**，叙事**展开**。读者第一眼看到的是故事，不是表格。

### 2. 研究脉络与经济机制

这是整篇报告最重要的叙事章节。必须回答：

1. **这个因子在捕捉什么市场现象？** 不是复述表达式，而是翻译成市场行为。
2. **为什么这个现象会产生 alpha？** 行为金融 / 市场微观结构 / 信息不对称 / 流动性溢价——选一个或多个理论框架。
3. **这个 alpha 为什么不会被套利掉？** 容量限制 / 执行成本 / 认知偏差持久性。
4. **Route type 的选择逻辑**：为什么是 genesis / decorrelate / variant？这条路径如何从 logic hypothesis 自然推导出来？

```markdown
## 研究脉络

> [!abstract] 本章摘要
> ……

### 市场假说

**Logic [[L001]]** 的核心命题：……

### 经济机制

<深度叙事：2-3 段，每段一个论点>

### 实验设计

**Route = <type>** 的选择理由：……

> [!info] 为什么不选其他 route？
> ……（对比其他可能的 route，解释排除原因）
```

### 3. 评估制度

简洁表格 + 一段说明为什么选择这些参数。

```markdown
## 评估制度

| 参数 | 设置 | 理由 |
|------|------|------|
| Universe | CSI 1000 | …… |
| Preprocess | MAD(5) + Zscore | …… |
| Neutralization | None | …… |
| Sample Policy | Train ≤ 2023, Val = 2024 | …… |
```

### 4. KPI 总览

IS vs OOS 对比表 + 一个 callout 总结"一句话"判断。

```markdown
## KPI 总览

| Metric | In-Sample | Out-of-Sample |
|--------|-----------|---------------|
| Rank IC Mean | … | ==…== |
| ICIR | … | ==…== |
| Win Rate | … | … |
| t-stat | … | ==…== |
| Monotonicity | … | ==…== |

> [!tip] 核心判断
> <IS→OOS 是增强/衰减/崩溃？衰减比 = X。这意味着……>
```

### 5. 预测能力（5 张图，逐张分析）

```markdown
## 预测能力

> [!abstract] 本章摘要
> ……

#### IC 时序走势

> [!info]- 阅读指南
> 横轴为交易日，纵轴为每日截面 Rank IC。蓝色区域为训练期（≤2023），
> 红色区域为验证期（2024）。叠加 MA20（短期趋势）和 MA60（中期趋势）。

![[assets/FXXX/ic_timeseries.png|600]]

<3-5 段逐图叙事>

---

#### 累积 IC

> [!info]- 阅读指南
> ……

![[assets/FXXX/cumulative_ic.png|600]]

<叙事：斜率变化意味什么、有无平台期、OOS 斜率是否延续>

---

#### 滚动 IC（20/60/120 日窗口）

![[assets/FXXX/rolling_ic.png|600]]

<叙事：三条线的分歧程度、是否有结构性断裂、窗口选择对信号的影响>

---

#### IC 分布

![[assets/FXXX/ic_distribution.png|600]]

<叙事：IS vs OOS 分布形状对比、是否有厚尾、中心偏移方向>

---

#### 月度 IC 热力图

![[assets/FXXX/monthly_heatmap.png|700]]

> [!example]- 年度 IC 明细
> | Year | IC | ICIR | Win Rate |
> |------|-----|------|----------|
> | ... | ... | ... | ... |

<叙事：季节性模式、异常年份、OOS 年份是否与历史一致>
```

### 6. 盈利能力（4+1 张图）

```markdown
## 盈利能力

> [!abstract] 本章摘要
> ……

#### 分组年化收益

![[assets/FXXX/quintile_bar.png|600]]

<叙事：Q1→Q5 收益梯度、单调性、多空分解、long_contribution vs short_contribution>

---

#### 验证期分组收益（Execute Evidence）

![[assets/FXXX/quintile_returns_oos.png|600]]

<叙事：这是 execute pipeline 独立计算的 OOS 期 Q1-Q5 年化收益，
与报告分析器的全期结果交叉验证……>

---

#### 累积净值曲线

![[assets/FXXX/cumulative_returns.png|600]]

<叙事：5 条曲线的分散程度、回撤同步性、Q5 的灾难性表现>

---

#### 多空策略表现

![[assets/FXXX/long_short.png|600]]

<叙事：夏普比、最大回撤、回撤恢复时间、关键回撤发生的市场背景>

> [!warning] 做空风险
> <如果 short_contribution 高，必须讨论做空执行风险>

---

#### 年度分组收益热力图

![[assets/FXXX/annual_group_returns.png|700]]

> [!example]- 完整分组统计
> <quintile stats 表格，折叠>

<叙事：哪些年份最强/最弱、弱效年份的市场背景是什么>
```

### 7. 风险归因（2 张新图）

```markdown
## 风险归因

> [!abstract] 本章摘要
> Alpha 存活率 = ==X%==，风格 R² = ==Y==。……

#### Barra 风格因子暴露

![[assets/FXXX/style_exposure_bar.png|600]]

<叙事：
- 哪个风格暴露最大？为什么这个因子会暴露在该风格上？
- R² = X 意味着什么？与库内其他因子对比如何？
- 对组合构建的启示：是否需要风格对冲？>

---

#### Alpha 存活瀑布图

![[assets/FXXX/alpha_waterfall.png|600]]

<叙事：
- Raw IC → Cap-Neutral IC 损失了多少？这说明因子有多少是 size/industry beta？
- Cap-Neutral → Barra Residual 又损失了多少？主要被哪个风格吸收？
- 最终存活率 = X%，在阈值 60% 以上/以下，含义是什么？
- 与 dominant_style_exposure 的一致性：最大暴露风格是否就是损失最大的那层？>

> [!tip] 或 [!warning]（根据 survival ratio 好坏选择）
> <存活率的一句话判断>
```

### 8. 信号稳定性（2 张新图）

```markdown
## 信号稳定性

> [!abstract] 本章摘要
> 分段稳定性 = <bucket>，行情稳定性 = <bucket>，扩展窗口通过 = <yes/no>

#### 多验证窗口 IC 一致性

![[assets/FXXX/support_window_ic.png|600]]

<叙事：
- 3 个验证窗口的 IC 是否同号？绝对值变化趋势？
- 绿色 = sign consistent, 红色 = sign flip。如有红色，必须深入讨论
- 与主验证窗口对比：最强/最弱的是哪个时期？为什么？>

---

#### 稳定性总览

![[assets/FXXX/stability_summary.png|700]]

<叙事：
- 左图：IS→OOS 衰减比。>0.7 为健康，<0.5 需要警惕
- 右图：4 个稳定性维度的得分。哪个最弱？
- 综合判断：这个信号是"稳如狗"还是"看天吃饭"？>
```

### 9. 衰减与可交易性（3+1 张图）

```markdown
## 衰减与可交易性

> [!abstract] 本章摘要
> 半衰期 = ==X 天==，最优再平衡 = ==Y 天==，覆盖率 = ==Z%==

#### IC 衰减曲线

![[assets/FXXX/ic_decay.png|600]]

<叙事：IC 随持有期如何变化？是正常衰减还是反向增强？
半衰期对再平衡频率的含义？与交易成本的权衡?>

---

#### 因子值分布

![[assets/FXXX/distribution.png|600]]

<叙事：IS vs OOS 分布是否一致？偏度/峰度异常？
分布形状对分组收益的影响？极端值处理的效果?>

---

#### 数据覆盖率

![[assets/FXXX/coverage.png|600]]

<叙事：覆盖率随时间的稳定性、突降事件对应什么市场事件?>

---

#### 交易可行性仪表盘

![[assets/FXXX/feasibility_dashboard.png|600]]

<叙事：
- Coverage, Liquidity Coverage, Turnover, Concentration 各项含义
- 哪项是绿灯/红灯？红灯项对实盘的具体影响
- 换手率对交易成本的估算>

> [!example]- IC 衰减明细
> | 持有期 | IC | 衰减比 |
> |--------|-----|--------|
> | ... | ... | ... |
```

### 10. 独特性（1 张图）

```markdown
## 独特性

> [!abstract] 本章摘要
> 最高库内相关 = ==X== (vs FYYY)，……

#### 因子库相关矩阵

![[assets/FXXX/correlation_bar.png|700]]

<叙事：
- 最高相关因子是谁？为什么高？两者在经济逻辑上有什么关系？
- 相关性是否构成替代风险？还是互补关系？
- 与同 family 因子的相关 vs 跨 family 因子的相关>

> [!example]- 完整相关矩阵
> | Factor | Correlation |
> | ... | ... |
```

### 11. 综合评分（1 张图）

```markdown
## 综合评分

> [!abstract] 评级：==[GRADE]== (==[SCORE]/100==)

![[assets/FXXX/radar.png|600]]

| 维度 | 得分 | 等级 | 解读 |
|------|------|------|------|
| Predictive Power | X | ? | <一句话> |
| Signal Stability | X | ? | <一句话> |
| Profitability | X | ? | <一句话> |
| Monotonicity | X | ? | <一句话> |
| OOS Robustness | X | ? | <一句话> |
| Uniqueness | X | ? | <一句话> |
| Decay Resistance | X | ? | <一句话> |

<叙事：最强/最弱维度分析，木桶效应讨论，与同 Grade 因子横向对比>
```

### 12. 批判性审查

```markdown
## 批判性审查

> [!danger] 一句话毒舌
> <尖锐但准确的一句话总结，直击要害>

### 致命弱点

<编号列表，每条包含：弱点描述 + 数据支撑 + 最坏情况推演>

### 改进方向

<编号列表，每条包含：具体建议 + 预期效果 + 可行性评估>

> [!warning] 使用警告
> <对实盘使用此因子的风险提示和注意事项>
```

### 13. 系统意义

```markdown
## 系统意义

### 验证了什么

<这个因子对整个研究系统的贡献：验证了哪个 hypothesis？
打开了什么新方向？对 family 结构有什么启示？>

### 后续方向

<具体的 follow-up 建议，每条关联到 logic/family/route>

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
- composite_score 进 frontmatter（作为 `composite_grade`），正文展示完整分解
- report 只读取 guarded_writer 落地后的最终状态
- **每张图必须单独嵌入 + 单独叙事**，禁止连续堆叠
- 叙事中每个论点必须引用具体数字（==高亮==），不说"表现良好"这类空话
- evidence charts（style_exposure_bar, alpha_waterfall, support_window_ic, feasibility_dashboard, quintile_returns_oos, stability_summary）如果不存在则跳过对应小节，不报错

## 执行模式

**Report 生成应作为后台 subagent 执行**（5-8 分钟/因子）。调用方使用 `Agent(run_in_background=true)`。

批量模式：为每个 admitted factor 启动独立后台 subagent，并行生成。
