# Factor Report

## 1. 定位

`report` 是研究系统里的资产文档生成层。

它不负责：

- 生成新因子
- 重新评估因子
- 裁决录取
- 复跑 execute

它只负责：

- 仅对**已落库因子**生成正式 Obsidian Markdown 报告
- 将 `execute / judge / logic / route / implementation` 的上下文整理成知识资产
- 更新 `Factor Library` 总览页
- 可选生成 batch summary

一句话：

> `report` 负责把“这个因子是什么、从哪里来、为什么被录取、在什么制度下成立、对系统意味着什么”讲清楚。

---

## 2. 核心原则

### 原则 1：正式 factor report 只在落库时触发

正式 factor report 只对以下事件触发：

- `admit`
- `replace`

若本轮 `admitted_count == 0`，则不生成正式 factor report。

### 原则 2：批次过程信息不进入正式 factor report

以下内容不生成正式 factor report：

- `reject`
- `near_miss`
- `overlap_blocked`
- `performance_rejected`
- `implementation_blocked`
- `screened but not admitted`

这些只进入：

- `batch_XXX_idea_report.yaml`
- `batch_XXX_execute_report.yaml`
- `batch_XXX_judge_report.yaml`
- batch history
- lessons / forbidden / implementation policy

### 原则 3：report 不重新计算评估

`report` 不重新执行 candidate 逻辑，不重新计算 factor values，不重新计算 factor correlation。

它只消费上游已经准备好的结构化结果：

- `report_data.json`
- `batch_XXX_research_result.yaml`
- `batch_XXX_judge_report.yaml`
- `batch_XXX_judge_packet.yaml`
- logic / route / lineage / factor registry

### 原则 4：report 是资产层，不是日志层

正式 factor report 的对象必须是：

- 已拥有正式 `factor_id`
- 已被 `research_judge` 接纳进入 library 的因子

### 原则 5：report 必须和新架构对齐

正式 factor report 不只写“这个因子表现不错”，还必须写清楚：

- 它来自哪个 logic
- 来自哪条 batch-local route label
- 来自哪个 `experiment_lineage_tag`
- 属于哪类 `route_type`
- 为什么被录取
- 在什么 execute profile 下成立
- 它对系统学到了什么

### 原则 6：report 只读取 final registry，不替 judge 做治理判断

对于以下治理字段，report 只能读取最终生效值：

- `family_id`
- `logic.status`

不能把：

- `family_registration_request`
- `family_correction_request`
- `judge.logic_recommendation`

当成最终真值写进正式 report。

同样地：

- `quick execute`
- `freeze_recommendation`

只能作为研究脉络说明，不得被写成 admit 证据。

### 原则 7：report 只读取 writer 落地后的最终状态

若某个对象存在：

- judge recommendation
- controller queue 状态
- guarded writer 落地后的最终状态

则正式 report 只能使用最终状态。

例如：

- `logic.status` 取 final logic card
- `family_id` 取 final factor registry
- `holdout_review_result` 取 final ledger / factor snapshot

不允许把中间 recommendation 当成正式结论。

---

## 3. 触发规则

### 3.1 触发正式 factor report 的事件

#### `admit`

新因子录取入库时，生成正式 factor report。

#### `replace`

新因子替换旧因子时，生成新因子的正式 factor report；
并在旧因子档案中记录被替换历史。

### 3.2 不触发正式 factor report 的事件

以下情况不生成正式 factor report：

- `reject`
- `near_miss`
- `screened but not admitted`
- `performance_rejected`
- `duplicate_rejected`
- `library_corr_rejected`
- `hard_rejected`

这些只进入 batch summary 或 lessons。

### 3.3 默认工作模式

#### `/factor-report FACTOR_ID`

为单个已入库因子生成正式 report。

#### `/factor-report all`

为所有已入库因子重建正式 report。

#### `/factor-report batch BATCH_ID`

只为该批次中最终 `admitted / replaced-in` 的因子生成正式 report。

#### `/factor-report summary BATCH_ID`

只生成该批次的 batch summary，不生成正式 factor report。

---

## 4. 输入来源

正式 factor report 至少整合以下四类来源。

### 4.1 因子定义层输入

回答“这是什么”。

来源：

- `storage/registry/factors/factor_XXX.yaml`
- `storage/candidates/batch_XXX.yaml`

字段：

- `factor_id`
- `name`
- `category`
- `source_type`
- `expression` 或 `code` 摘要
- `lineage`
- `family_id`
- `route_type`
- `experiment_lineage_tag`

### 4.2 正式评估层输入

回答“表现怎样”。

来源：

- `storage/evidence/vault/assets/FXXX/report_data.json`
- `batch_XXX_research_result.yaml`
- `storage/packets/batch_XXX_judge_packet.yaml`

字段：

- predictive power
- profitability
- risk attribution
- conditional analysis
- decay / tradability
- uniqueness
- composite score
- pipeline trace
- similarity / replacement 信息
- `support_window_checks`
- `support_window_warning`

### 4.3 裁决层输入

回答“为什么被录取”。

来源：

- `batch_XXX_judge_report.yaml`
- `storage/packets/batch_XXX_judge_packet.yaml`
- decision artifact

字段：

- `decision`
- `decision_type`
- `main_reasons`
- `red_flags`
- `replace_target_id`
- route feedback
- logic feedback
- implementation learning

### 4.4 研究脉络输入

回答“从哪里来、意味着什么”。

来源：

- logic card / logic registry
- batch-local route label / route feedback
- factor registry
- `batch_XXX_idea_report.yaml`

字段：

- `logic_id`
- `route_id`
- `route_type`
- `experiment_lineage_tag`
- `current_focus_question`
- `logic bottleneck`
- `next_actions`
- `implementation_reason`
- `freeze_boundary_context`

### 4.5 统一字段契约

`report.md` 既是报告规范，也承担字段契约角色。

也就是说，后续实现：

- `report.builder`
- LLM Markdown 生成
- vault 文档更新

都应以这份文档里的字段口径为准，不再另起一份独立 schema 文档。

硬规则：

1. 同一个字段只能有一套定义
2. report 中出现的字段，必须能回溯到上游结构化对象
3. narrative 不能发明新字段，也不能改写字段含义

### 4.6 字段来源映射

正式 factor report 的字段来源固定如下：

#### 因子身份字段

来源：

- `storage/registry/factors/factor_XXX.yaml`

字段：

- `factor_id`
- `name`
- `category`
- `source_type`
- `expression`
- `lineage`
- `family_id`
- `logic_id`
- `route_id`
- `route_type`
- `experiment_lineage_tag`

#### 执行制度字段

来源：

- `batch_XXX_research_result.yaml`
- `batch_XXX_execute_report.yaml`

字段：

- `universe_profile`
- `tradability_profile`
- `preprocess_profile`
- `neutralization_profile`
- `sample_policy_version`
- `data_start`
- `active_train_range`
- `active_validation_range`
- `validation_window_id`
- `support_validation_windows`
- `holdout_used`

#### 统计证据字段

来源：

- `storage/evidence/vault/assets/FXXX/report_data.json`
- `batch_XXX_research_result.yaml`

字段：

- `ic_mean_train`
- `ic_ir_train`
- `ic_mean_validation`
- `ic_ir_validation`
- `ic_win_rate_validation`
- `monotonicity_validation`
- `split_stability`
- `regime_stability`
- `train_validation_decay_ratio`
- `expanding_window_ic_stability`
- `expanding_window_sign_consistency`
- `expanding_window_pass`
- `bootstrap_stability_score`
- `bootstrap_status`
- `purged_walk_forward_score`
- `purged_walk_forward_status`
- `multiple_testing_risk_bucket`
- `search_adjusted_strength_bucket`
- `support_window_checks`
- `support_window_warning`

#### 冗余与替代字段

来源：

- `batch_XXX_research_result.yaml`
- `batch_XXX_execute_report.yaml`
- `batch_XXX_judge_report.yaml`

字段：

- `nearest_factor_id`
- `max_lib_corr`
- `family_overlap_score`
- `family_overlap_bucket`
- `same_family_corr_p90`
- `structure_overlap_score`
- `residual_survival_ratio`
- `subspace_redundancy_score`
- `residual_incremental_ic`
- `basis_factor_ids`
- `subspace_confidence`
- `replace_target_id`

#### 风险与可实现性字段

来源：

- `report_data.json`
- `batch_XXX_research_result.yaml`

字段：

- `raw_view_ic`
- `cap_industry_neutral_ic`
- `barra_residual_ic`
- `alpha_survival_ratio`
- `dominant_style_exposure`
- `style_crowding_risk`
- `turnover`
- `coverage`
- `half_life`
- `holding_period_proxy`
- `liquidity_coverage_ratio`
- `tail_trade_concentration`
- `small_cap_concentration`
- `rebalance_stress_proxy`

#### 裁决字段

来源：

- `batch_XXX_judge_report.yaml`
- `storage/logic/cards/logic_LXXX.yaml`

字段：

- `decision`
- `decision_type`
- `candidate_verdict`
- `route_verdict`
- `logic_status`
- `judge_reason_codes`
- `main_reasons`
- `red_flags`
- `holdout_review_required`
- `holdout_review_result`

### 4.7 缺失字段降级规则

如果某字段当前上游还没有产出，report 不允许静默省略。

必须二选一：

1. 在 frontmatter 中留空，但在正文明确写 `数据待补充`
2. 用 Obsidian callout 标记该章节暂缺

不允许：

- 用 narrative 猜测补齐
- 用旧版字段偷换新字段

---

## 5. 输出对象

### A. 正式 factor report

输出路径：

```text
storage/evidence/vault/factors/FXXX <name>.md
```

这是已录取因子的正式知识资产。

### B. Factor Library 总览页

输出路径：

```text
storage/evidence/vault/Factor Library.md
```

用于：

- 汇总所有已录取因子
- 提供统一导航入口
- 提供类别分布、评分分布、索引跳转

### C. Batch summary

输出路径：

```text
storage/evidence/vault/batches/batch_XXX summary.md
```

这是过程报告，不是正式 factor report。

用于：

- 记录本轮 `admit / reject / replace` 摘要
- 记录 logic / route / implementation 学习
- 帮助复盘，不进入正式资产层

---

## 6. 正式 factor report 的目标

一份好的正式 factor report，必须同时完成四件事。

### 6.1 解释清晰度

读完后，人能回答：

- 这个因子到底在做什么
- 它和普通动量 / 反转 / breakout 有什么不同

### 6.2 决策支撑度

读完后，人能回答：

- 为什么系统录了它
- 为什么不是录别的
- 它和库里已有东西是什么关系

### 6.3 制度对齐度

读完后，人能回答：

- 它是在什么 `universe / tradability / preprocess / neutralization` 口径下成立的

### 6.4 系统学习价值

读完后，人能回答：

- 这个因子验证了哪个 logic
- 哪类 route 更有效
- 哪类 implementation 更合适
- 后续应该继续什么、停止什么

---

## 7. 正式 factor report 的结构

### 7.1 Frontmatter

```yaml
id: "XXX"
name: <factor_name>
category: <category>
source_type: <dsl|python>
logic_id: <logic_id>
route_id: <route_id>
route_type: <genesis|mutate|crossover|repair|decorrelate>
experiment_lineage_tag: <elt>
family_id: <family_id>
expression: "<qlib_expression_or_summary>"
batch: <batch>
admitted_at: <date>
decision: <admit|replace>
replace_target_id: <optional>
universe_profile: <profile_name>
tradability_profile: <profile_name>
preprocess_profile: <profile_name>
neutralization_profile: <profile_name>
data_start: 2015-01-01
sample_policy_version: research_sample_v3
validation_window_id: <validation_window_id>
ic_mean_validation: <value>
ic_ir_validation: <value>
monotonicity_validation: <value>
ls_sharpe: <value>
multiple_testing_risk_bucket: <value>
search_adjusted_strength_bucket: <value>
tags:
  - factor
  - <category>
  - <route_type>
```

#### Frontmatter 硬规则

1. frontmatter 只放稳定索引字段，不放大段 narrative
2. frontmatter 中的数值字段必须来自结构化结果，不能由 LLM 自己总结
3. 若是 `replace`，必须包含 `replace_target_id`
4. 若上游没有 `validation_window_id`，不能自行编造
5. `composite_score / composite_grade` 不进入 frontmatter，只在正文展示

### 7.2 标题区

```md
# FXXX <factor_name>

> [!info] 基本信息
> **表达式/实现**：`<expression or concise code summary>`
> **类别**：<category> | **来源**：<source_type> | **批次**：<batch> | **录取日期**：<date>
> **Logic / Route**：<logic_id> / <route_id> | **Route Type**：<route_type>
> **Experiment Tag**：`<experiment_lineage_tag>`
> **综合评分**：<composite_score> (<composite_grade>)
```

### 7.3 因子身份卡

回答：

- 这个因子是什么
- 它是 DSL 还是 Python
- 它来自哪条 research route

建议包含：

- `factor_id`
- `logic_id`
- `route_id`
- `experiment_lineage_tag`
- `family_id`
- `source_type`
- `implementation_reason`
- lineage 简述

### 7.4 构造逻辑与研究脉络

必须回答：

- 这个因子来自哪个 logic
- 它在回答什么 research question
- 它为什么是 `genesis / mutate / repair / decorrelate / crossover`
- 它的 lineage 是什么
- 它是如何从快速回路被冻结进正式回路的

建议小节：

#### 7.4.1 研究命题来源

- logic 的核心 hypothesis
- 当前 focus question

#### 7.4.2 本轮 route 设计

- 为什么会开这条 route
- route 属于哪个 family
- route 的研究目标是什么

#### 7.4.3 因子构造路径

- 最终 candidate 如何从 route 展开而来
- 若是 `mutate / repair / decorrelate`，原对象是谁

#### 7.4.4 Freeze Boundary 摘要

- 该 candidate 是如何通过 `probe + candidate_freeze_check`
- freeze 前有哪些关键修正
- 注意：这里只解释研究过程，不把 quick execute 当 admit 证据

### 7.5 评估制度说明

必须说明：

- `universe_profile`
- `tradability_profile`
- `preprocess_profile`
- `neutralization_profile`
- `delay / horizon`
- `sample_policy_version`
- `data_start: 2015-01-01`
- `train / validation / holdout` 配置
- `support_validation_windows`

目的：

避免 report 脱离 execute 口径。

### 7.6 KPI 摘要

这是在正式 execute profile 下得到的结果。

```md
## KPI 摘要

| 指标 | Train | Validation |
|------|-------|------------|
| RankIC | <...> | <...> |
| IC | <...> | <...> |
| ICIR | <...> | <...> |
| IC > 0 Win Rate | <...> | <...> |
| 多空 Sharpe | — | <...> |
| 单调性 | — | <...> |
| 综合评分 | — | <...> |
```

#### KPI 字段映射

- `RankIC / IC / ICIR / Win Rate` 优先来自 `report_data.json.predictive_power`
- `多空 Sharpe / 分组收益` 优先来自 `report_data.json.profitability`
- `综合评分` 只来自 `report_data.json.composite`
- 若 `report_data.json` 与 `batch_XXX_research_result.yaml` 不一致，以 batch 结果中的正式录取口径为准，并在 report 中注明

### 7.7 构造逻辑与经济解读

保留，但更明确区分：

- 信号定义层解释
- 研究脉络层解释
- A 股制度背景

建议小节：

#### 7.7.1 表达式 / 程序拆解

#### 7.7.2 经济理论

#### 7.7.3 A 股市场背景

结合：

- T+1
- 涨跌停
- 融券限制
- 小盘股交易约束
- 量价制度特征

### 7.8 预测能力

回答：

> “这个信号有多强？”

保留图表与 narrative：

- `ic_timeseries`
- `ic_distribution`
- `rolling_ic`
- `cumulative_ic`
- `monthly_heatmap`

要求：

- 明确对比 train 与 validation
- 解释 IC、ICIR、胜率、稳定性
- 结合 expanding-window 与 regime 解释可靠性
- 如有 `support_window_checks`，必须单独说明它们只是辅助稳定性观察

### 7.9 盈利能力

回答：

> “信号能稳定赚钱吗？”

保留：

- `quintile_bar`
- `cumulative_returns`
- `long_short`
- `is_vs_oos_bar`
- `annual_group_returns`

并明确：

- long / short 收益来源
- 单调性
- A 股空头端限制的影响
- validation 稳健性

### 7.10 风险归因

回答：

> “这是 alpha 还是 beta？”

说明这是在当前 neutralization 制度下观察到的现象，而不是绝对真相。

可包含：

- 行业 IC 分布
- 市值暴露
- 风格相关
- `barra_residual_ic`
- `alpha_survival_ratio`

若数据不可用，则给出定性分析与缺失说明。

### 7.11 条件分析

回答：

> “什么时候管用？”

保留：

- `regime IC`
- `vol regime IC`
- `annual IC`

叙事必须升级为使用建议：

- 什么环境下可加大使用
- 什么环境下应谨慎
- 这是否影响 logic 的后续 route 设计

### 7.12 衰减与可交易性

回答：

> “信号能撑多久？”

保留：

- `ic_decay`
- `autocorrelation`
- `distribution`
- `coverage`

并结合 tradability profile 解释：

- 半衰期
- 换仓建议
- `turnover`
- 中国市场制度下的现实可交易性代理

### 7.13 独特性与替代关系

这是新架构下的关键章节之一。

必须回答：

- 它和 `nearest_factor` 的关系
- 是否提供增量信息
- 若是 `replace`，它替换了谁、为什么
- 它是否解决了 overlap 问题

应至少整合：

- `max_lib_corr`
- `family_overlap_score`
- `family_overlap_bucket`
- `subspace_redundancy_score`
- `residual_incremental_ic`
- `replacement` 结论

硬规则：

- 不能只展示 `max_lib_corr`
- 必须同时给出 family 级和 subspace 级结论
- 若是 `replace`，必须单独写一段“为什么旧因子被替换”

### 7.14 综合评分

保留雷达图和各维度分解。

narrative 不能只说哪个维度高低，而要说明：

- 为什么最终还能被录取
- 它是均衡型因子还是长板型因子
- judge 为什么接受它的不完美之处

硬规则：

- `composite_score` 只用于展示和横向比较
- 不能被解释成 admit 的直接原因
- 正式 admit 理由必须回到 `judge_reason_codes` 与结构化证据

### 7.15 实现形式与工程可行性

这是新架构下新增的重要章节。

回答：

- 它为什么是 DSL 还是 Python
- 这种实现形式是否自然
- 是否依赖特殊 helper / custom op
- 是否存在复杂度 / 性能 / 维护性风险

目标：

让人理解：

- 系统为什么接受这种实现
- 未来是否值得把这类逻辑 helper 化
- 是否有 implementation policy 启示

### 7.16 批判性审查

建议分成：

#### 7.16.1 一句话毒舌

必须有数字支撑。

#### 7.16.2 关键弱点

至少列：

- 信号弱点
- overlap / uniqueness 风险
- regime 风险
- implementation 风险

#### 7.16.3 改进方向

必须可操作，并能映射回：

- logic
- route
- implementation
- helper abstraction

### 7.17 系统意义与后续方向

这是新版 report 最重要的新增章节之一。

必须回答：

- 这个因子验证了什么
- 它说明哪个 `logic / family / route` 是有效的
- 它对 implementation policy 有什么启发
- 后续应该继续什么
- 是否提示新增 helper / custom op
- 是否意味着某类 route 可以停止探索

---

## 8. 图表与素材来源

### 第 1 阶段：构建报告数据 + 导出 PNG

单因子：

```bash
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
PYTHONPATH=src python3 -m report.builder --factor-id FACTOR_ID --vault
```

全部因子：

```bash
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
for id in $(ls storage/registry/factors/factor_*.yaml | sed 's/.*factor_//;s/.yaml//'); do
  echo "Building F${id}..." && PYTHONPATH=src python3 -m report.builder --factor-id "$id" --vault
done
```

这会在：

```text
storage/evidence/vault/assets/FXXX/
```

下生成图表和 `report_data.json`。

### `report_data.json` 仍然是核心素材层

保留原有 schema：

- `factor`
- `predictive_power`
- `profitability`
- `risk_attribution`
- `conditional`
- `decay_tradability`
- `uniqueness`
- `composite`

但正式 report 不应只依赖它。
还必须整合：

- judge report
- judge packet
- logic / route / lineage
- execute profile 信息

### 8.1 report_data 最小扩展要求

为了让正式 report 能完整生成，`report_data.json` 至少应补以下顶层块：

```yaml
admission:
  factor_id: F042
  decision: admit
  decision_type: new
  admitted_at: "2026-04-04"
  replace_target_id: null
  judge_reason_codes: [strong_validation_effect, good_split_stability]

protocol:
  sample_policy_version: research_sample_v3
  data_start: "2015-01-01"
  active_train_range: ["2015-01-01", "2021-12-31"]
  active_validation_range: ["2022-01-01", "2023-12-31"]
  validation_window_id: val_2022_2023
  universe_profile: cn_all_tradable_v1
  tradability_profile: cn_t1_limit_v1
  preprocess_profile: default_rank_v1
  neutralization_profile: cap_industry_barra_v1

research_context:
  logic_id: L021
  route_id: R021_01
  route_type: genesis
  experiment_lineage_tag: ELT_L021_breakout_compression_gate_v1
  family_id: FM_breakout
  implementation_reason: "DSL 自然表达，避免 helper 依赖"
  freeze_boundary_context:
    probe_verdict: pass
    freeze_entry: probe_plus_candidate_freeze_check

decision_context:
  candidate_verdict: admit
  route_verdict: continue
  logic_status: productive   # final status snapshot from logic card at report build time
  holdout_review_required: false
  holdout_review_result: null
  support_window_warning: none
```

如果 builder 暂时产不出这些字段，Markdown 生成阶段必须从：

- factor registry
- batch result
- judge report

中补齐。

---

## 9. 正式生成 Markdown

### 第 2 阶段：生成正式 factor report

对于每个 `admitted / replaced-in` factor：

1. 读取 `report_data.json`
2. 读取 factor registry / batch manifest
3. 读取 `batch_XXX_research_result.yaml`
4. 读取 `batch_XXX_judge_report.yaml`
5. 读取 `batch_XXX_judge_packet.yaml`
6. 读取 logic / route / implementation 上下文
7. 生成 Obsidian Markdown

输出路径：

```text
storage/evidence/vault/factors/FXXX <name>.md
```

### 9.1 Markdown 生成逻辑

正式 factor report 的生成逻辑固定为：

1. 先生成 frontmatter
2. 再生成 identity card
3. 再按章节顺序写：
   - 研究脉络
   - 制度说明
   - 统计证据
   - 风险与可实现性
   - 冗余与替代
   - 裁决与系统意义
4. 最后追加：
   - known weaknesses
   - review trigger

也就是说：

- 章节顺序先“是什么”，再“为什么成立”，最后“为什么录取”
- 不能先堆图，再让 LLM 自己拼故事

### 9.2 章节与字段映射

#### Identity Card

必须使用：

- `factor_id`
- `name`
- `logic_id`
- `route_id`
- `route_type`
- `family_id`
- `source_type`

#### 评估制度说明

必须使用：

- `sample_policy_version`
- `data_start`
- `active_train_range`
- `active_validation_range`
- `validation_window_id`
- `universe_profile`
- `tradability_profile`
- `preprocess_profile`
- `neutralization_profile`

#### 统计章节

必须使用：

- `ic_mean_validation`
- `ic_ir_validation`
- `monotonicity_validation`
- `split_stability`
- `regime_stability`
- `expanding_window_pass`
- `multiple_testing_risk_bucket`

#### 独特性章节

必须使用：

- `nearest_factor_id`
- `family_overlap_bucket`
- `subspace_redundancy_score`
- `residual_incremental_ic`

#### 最终裁决章节

必须使用：

- `decision`
- `candidate_verdict`
- `route_verdict`
- `logic_status`
- `judge_reason_codes`
- `main_reasons`
- `red_flags`

### LLM 叙事质量规则

- 以资深量化分析师视角撰写
- 所有叙事用中文
- 技术术语可保留英文
- 每一章必须引用具体数字
- 叙事围绕“回答决策问题”展开
- 不能只描述图，要做判断

必须显式说明：

- logic / route 来源
- execute profile
- admit / replace 理由
- 系统学习意义

### 9.3 LLM 禁止事项

LLM 不允许：

1. 发明不存在的字段
2. 把 `composite_score` 写成 admit 原因
3. 用 narrative 覆盖 `judge_reason_codes`
4. 在缺数据时自行脑补结论

---

## 10. Factor Library 总览页

### 第 3 阶段：重建总览页

读取所有已录取因子的 `report_data.json` 与 registry metadata，更新：

```text
storage/evidence/vault/Factor Library.md
```

建议结构：

```md
---
title: Factor Library
tags:
  - index
---

# Factor Library

> <N> factors | Last updated: <date>

## 汇总表

| ID | Name | Category | Route Type | Source | IC (Validation) | ICIR | Grade | Score | Link |
|----|------|----------|------------|--------|-----------------|------|-------|-------|------|

## 按类别分布

| Category | Count | Avg |IC| | Best Factor |
|----------|-------|----------|-------------|

## 按 Route Type 分布

| Route Type | Count | Avg Score | Best Factor |
|------------|-------|-----------|-------------|

## 按实现形式分布

| Source Type | Count | Avg Score | Notes |
|-------------|-------|-----------|-------|

## 评分分布

| Grade | Count | Factors |
|-------|-------|---------|
```

---

## 11. Batch Summary

### 第 4 阶段：生成 batch summary

若调用：

```text
/factor-report summary BATCH_ID
```

则生成：

```text
storage/evidence/vault/batches/batch_XXX summary.md
```

目标：

服务于研究过程复盘，而不是 library 资产管理。

可包含：

- 本轮 `admit / reject / replace` 摘要
- 主要 reject 原因
- route feedback 摘要
- logic feedback 摘要
- implementation learning 摘要
- 本轮 lessons

硬规则：

batch summary 不是正式 factor report，
也不替代正式因子资产文档。

---

## 12. 完成后的反馈

完成后应告知用户：

正式 factor report 路径：

```text
storage/evidence/vault/factors/FXXX <name>.md
```

总览页路径：

```text
storage/evidence/vault/Factor Library.md
```

若生成 batch summary：

```text
storage/evidence/vault/batches/batch_XXX summary.md
```

并提示：

- 使用 Obsidian 打开 `storage/evidence/vault/`
- 正式 factor report 仅对 `admitted / replaced-in` 因子生成
- 其余过程信息保存在 batch 层文档中

---

## 13. 质量衡量标准

一份正式 factor report 必须满足以下四项。

### 13.1 解释清晰度

读完后能回答：

- 这个因子在做什么

### 13.2 决策支撑度

读完后能回答：

- 为什么系统录了它

### 13.3 制度对齐度

读完后能回答：

- 它是在什么 execute 口径下成立的

### 13.4 系统学习价值

读完后能回答：

- 它对 `logic / route / implementation policy` 有什么启发

---

## 14. 最终目标

`factor-report v2` 的目标不是“把一堆指标写成好看的文档”，而是：

- 把已录取因子整理成真正可阅读的知识资产
- 让人理解“是什么、从哪里来、为什么被接纳、在什么制度下成立、对系统意味着什么”
- 让 factor library 成为研究资产库，而不是图表堆积区

---

## 15. 一句话总结

`factor-report v2` 应是一套：

> 仅在 `admit / replace` 时触发，为已入库因子生成包含研究脉络、评估制度、裁决理由和系统学习意义的正式 Obsidian 资产报告，并同步更新 `Factor Library` 总览页的知识资产生成系统。
