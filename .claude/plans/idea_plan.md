````markdown
---
name: factor-idea
description: 消费 logic schedule，将市场逻辑拆成 research routes，用训练期内 probe 过滤垃圾，并生成正式候选批次
user_invocable: true
---

# 因子创意生成 — /idea v2

`factor-idea` 是整个自动因子研究系统的**中层执行器**。  
它不负责创建新的市场逻辑，而负责：

- 读取 `/logic schedule` 给出的 exploration contract
- 将 active logic 拆成本轮 research routes
- 为每条 route 设计 probe forms
- 在训练期内用轻量 probe 过滤垃圾
- 选择值得继续投资的 routes
- 将通过的 routes 展开成正式 candidates
- 输出 batch manifest 与 idea report

---

## 核心定位

在整条链路中：

- `logic` 决定：**研究什么大方向**
- `idea` 决定：**围绕这个方向，这一轮具体怎么做实验**
- `execute` 决定：**这些候选在统一协议下表现如何**
- `judge` 决定：**录取什么，并把经验回写到系统**

所以 `idea` 的本质不是“想更多方向”，而是：

> **把 logic 给出的研究命题和预算，转成这一轮可执行的 research routes，再把通过 probe 的 routes 转成正式候选。**

---

## 核心原则

### 原则 1：`idea` 不决定研究主题
研究主题由 `/logic schedule` 决定。  
`idea` 只能在当前 active logic 及其 contract 范围内展开。

### 原则 2：`idea` 的基本单位是 route
每条 route 都是某个 logic 下的一条本轮研究路线，必须回答一个具体研究问题。

### 原则 3：`idea` 必须受预算控制
每个 logic 的 route 数和 candidate 数必须受以下字段约束：

- `direction_quota`
- `candidate_quota`

### 原则 4：probe 只负责过滤垃圾
probe 不做正式评估，不碰正式样本外，不试图预测最终录取。  
probe 的唯一目标是：

- 过滤明显垃圾 route
- 留下值得送去 `/execute` 的 route

### 原则 5：probe 只能使用训练期
如果正式样本外从 `2024-01-01` 开始，则 probe 不得使用 2024 及之后数据。  
probe 只能使用训练期内部数据，并做轻量分段检查。

### 原则 6：candidate expansion 必须模板化
route 通过 probe 后，必须按 `route_type` 使用预定义模板展开 candidate，不得无限制自由发散。

### 原则 7：默认优先 DSL
若某条 route 可以被当前 DSL 自然表达，则必须优先使用 DSL。  
Python 只在 route 结构上明显不适合 DSL 时才允许使用。

### 原则 8：`idea` 不负责长期状态治理
`idea` 可以输出 route/probe 的反馈 artifact，  
但不得直接修改 logic 生命周期、全局 state 或长期 memory 索引。

---

# 一、输入：必须消费 logic schedule

`/idea` 的起点必须是 `/logic schedule` 输出的 snapshot 和 exploration contract。

## Step 0：读取本轮上下文

读取：

```bash
cat storage/logic/latest_schedule_snapshot.yaml
cat storage/logic/registry.yaml
cat storage/logic/cards/*.yaml
cat storage/system/capability_registry.yaml
cat storage/library/library.yaml
cat storage/memory/forbidden.yaml
cat storage/memory/mining-lessons.md
````

## 必须读取的核心字段

对每个 `eligible_this_round: true` 的 logic，至少读取：

* `logic_id`
* `priority`
* `direction_quota`
* `candidate_quota`
* `preferred_mode`
* `preferred_families`
* `suggested_ops`
* `required_fields`
* `avoid_patterns`
* `current_focus_question`

## 这一步的目标

明确三件事：

1. 本轮到底开几个 logic
2. 每个 logic 最多开几条 route
3. 每个 logic 这轮最主要在回答什么问题

---

# 二、本轮预算与 logic 选择

## Step 1：确定本轮 research budget

不是所有 active logic 都必须本轮展开。
`idea` 必须根据 schedule 的结果，确定本轮真正进入执行的 logic。

## 推荐默认策略

### 小库早期（library < 20）

* 本轮最多展开 1 个 logic

### 中期（20 <= library < 50）

* 1 个主 logic + 1 个副 logic

### 后期（library >= 50）

* 最多 2~3 个 logic

## 全局预算建议

* 总 route 数不超过 3
* 总 candidate 数不超过 6~8

## 每个 logic 的预算定义

* `direction_quota`：该 logic 本轮最多展开几条 route
* `candidate_quota`：该 logic 本轮最多产出几个 candidate

---

# 三、核心对象：Route

## Route 的定义

route 是 `idea` 的核心单位。
它表示：

> **某个 logic 下，本轮准备怎么验证这个研究命题的一条具体研究路线。**

它不是 logic，也不是 candidate，而是位于两者之间的“研究设计层”。

## Route Schema

```yaml
route_id: R021_01
logic_id: L021
family_id: FM_breakout
route_type: genesis   # genesis / mutate / crossover / repair / decorrelate
priority: high

research_question: "量能压缩条件是否能显著提升 breakout 的独立性"
hypothesis_slice: "compression condition + breakout family"

origin:
  source: logic_native
  parent_routes: []
  parent_factors: []

route_structure:
  requires_branching: false
  estimated_branch_count: 0
  requires_multi_state_logic: false
  requires_multi_stage_pipeline: false
  intermediate_variable_count: 2
  dsl_naturalness: high

probe_plan:
  core_probe_form: "..."
  neighbor_probe_form: "..."
  probe_profile: probe_v2_train_only

expansion_template:
  candidate_target_count: 3
  allowed_variations:
    - window_variation
    - rank_transform
    - residual_volume_gate
  forbidden_variations:
    - pure_price_only_breakout
```

---

# 四、route 规划

## Step 2：为每个 logic 规划 routes

对每个被选中的 logic：

* 按 `direction_quota` 生成不超过 quota 条 route
* route 必须围绕 `current_focus_question`
* route 必须落在 `preferred_families` 内
* route 不得命中 `avoid_patterns`

## route 来源类型

### 1. logic-native genesis

从 logic 的 thesis / mechanism / preferred_families 直接展开。

### 2. logic-scoped mutation

仅允许从该 logic 相关的：

* admitted factor
* productive family
* near miss route
  中做 mutation。

### 3. logic-approved crossover

只有 contract 允许时，才可做 crossover。

---

# 五、route_type 判定规则

`route_type` 不是看表达式形式，而是看**研究目标**。

## 1. `genesis`

表示：

* 新 logic 的原生实现路线
* 第一次在某个 family 中验证 hypothesis
* 不是沿已有 admitted factor 改出来的

## 2. `mutate`

表示：

* 围绕已有有效或接近有效的结构做局部变形
* 比如窗口变化、rank/zscore 变体、轻条件门控

## 3. `crossover`

表示：

* 将两个已有逻辑/家族的结构做组合
* 比如 additive / gated / interaction

## 4. `repair`

表示：

* 某条 route 不是完全错误，而是存在明确缺陷
* 例如 coverage 太低、复杂度太高、不稳、proxy 不佳

## 5. `decorrelate`

表示：

* 某条 route 基本有效，但与已有库/已有 family 太像
* 本轮目标是降低 overlap，而不是提升原始 IC

## route_type 判定顺序

### 若 route 直接来自 logic-native hypothesis

* 通常为 `genesis`

### 若 route 来源于已有 factor / productive family / near miss

再看研究目标：

* 局部增强/变形 → `mutate`
* 修问题 → `repair`
* 降相似度 → `decorrelate`

### 若 route 来源于两个已有结构的组合

* `crossover`

---

# 六、实现形式选择（DSL / Python）

`idea` 在 candidate expansion 阶段，必须为每个 route 选择实现形式：

* `source_type: dsl`
* `source_type: python`

实现形式选择不是自由判断，而必须遵守 `storage/system/capability_registry.yaml` 中的 `implementation_policy`。

## 原则

### 原则 1：默认优先 DSL

如果某条 route 可以被当前 DSL 自然表达，则必须优先使用 DSL。

### 原则 2：Python 是受控例外

Python 只在 route 的核心价值来自流程逻辑、状态逻辑或复杂中间变量结构时才允许使用。

### 原则 3：不是“能写成 Python”就用 Python

如果 Python 只是“写起来更顺手”，但 DSL 已足够自然表达，则必须坚持 DSL。

### 原则 4：实现形式是初判，不是最终真理

`idea` 负责给出实现形式初判；
若形式选择错误，后续由 `execute` 暴露工程问题，由 `judge` 总结并抽象成长期实现政策。

## route 结构标注

在选择实现形式之前，必须先为每条 route 生成结构标注：

* `requires_branching`
* `estimated_branch_count`
* `requires_multi_state_logic`
* `requires_multi_stage_pipeline`
* `intermediate_variable_count`
* `dsl_naturalness`

## DSL 优先使用的场景

默认使用 DSL 的 route：

* breakout
* reversal
* momentum
* compression_spread
* rank_spread
* rolling_corr
* volatility_proxy
* simple_conditional_route
* liquidity_proxy_route

并且同时满足：

* 不需要多阶段 pipeline
* 不需要多状态切换
* 分支复杂度低
* 中间变量数量有限
* DSL operators 足够自然表达

## 允许 Python 的场景

只有当 route 满足以下任一条件时，才允许使用 Python：

* `requires_multi_stage_pipeline = true`
* `requires_multi_state_logic = true`
* `estimated_branch_count > 1`
* `dsl_naturalness = low`
* route_type 属于：

  * `repair`
  * `decorrelate`
  * `multi_stage_pipeline`
  * `multi_state_switching`
  * `structurally_asymmetric_route`

## Python 限制

即使 route 满足 Python 条件，也必须同时满足 capability contract 的限制，例如：

* `max_code_lines <= 30`
* `max_branch_count <= 3`
* `max_param_count <= 3`
* `max_intermediate_variable_count <= 6`
* 只能使用白名单 `ops.*` helper
* 不允许任意 import
* 不允许网络调用
* 不允许文件 IO

若超出限制，则：

* 优先尝试重写为 DSL
* 或将 route 降复杂度
* 或直接 reject

---

# 七、Probe 设计

## Step 3：为每条 route 设计 probe forms

每条 route 至少设计两个 probe：

* `core_probe_form`
* `neighbor_probe_form`

## probe 的目标

probe 的唯一目标是：

> **过滤垃圾 route，而不是证明优秀。**

probe 不做正式评估，不负责决定最终录取，也不负责定义实现制度。

## probe form 要求

* `core_probe_form`：反映 route 的核心研究问题
* `neighbor_probe_form`：route 的局部邻近变体，而不是完全不同结构
* 不做复杂优化
* 不碰正式样本外

---

# 八、Probe 运行规则

## Step 4：运行 probe（只在训练期内）

### 数据范围

probe **只能使用训练期**。
如果正式样本外是 `2024-01-01` 之后，则 probe 推荐使用：

* 训练期全段：`2019-01-01 ~ 2023-12-31`
* 分段 A：`2019-01-01 ~ 2021-12-31`
* 分段 B：`2022-01-01 ~ 2023-12-31`

### probe 最少输出字段

#### 表达式层

* `computable`
* `valid_ratio`
* `variance_ok`

#### 信号层

* `ic_mean_full`
* `ic_mean_seg_a`
* `ic_mean_seg_b`

#### route 层

* `forbidden_hit`
* `overlap_risk_hint`
* `neighbor_consistency`

---

# 九、Probe 的检查逻辑

probe 只做四类检查。

## 1. 可计算性检查

* 表达式可正常计算
* 非全 NaN / 非近似常数
* 覆盖率不过低

## 2. 基础信号检查

* 训练期内部 `abs(ic_mean_full)` 不能太低

## 3. 轻量一致性检查

* 分段 A / B 不能明显翻脸到完全不可用
* core / neighbor probe 不能一强一彻底塌掉

## 4. 脏路线检查

* forbidden 命中
* 明显高重复风险
* 已知坏模板

## 推荐最小 fail 规则

满足任意一条则 `route_verdict = fail`：

* `computable = false`
* `valid_ratio < 0.30`
* `abs(ic_mean_full) < 0.01`
* seg_a / seg_b 明显反向且都不强
* neighbor probe 完全崩掉
* 命中 forbidden

## verdict 定义

* `pass`
* `borderline`
* `fail`

---

# 十、Route 选择

## Step 5：选择要继续展开的 routes

Step 5 选择的对象是 **route**，不是 candidate。

## 5a. 先做硬过滤

过滤以下 route：

* `route_verdict = fail`
* 不符合 contract
* 命中 forbidden
* 复杂度过高
* 明显重复

## 5b. 对剩余 route 打分

推荐使用：

```text
route_select_score =
0.35 * probe_quality_score
+ 0.20 * contract_alignment_score
+ 0.15 * novelty_score
+ 0.15 * local_robustness_score
+ 0.10 * logic_priority_score
+ 0.05 * diversity_bonus
```

### 各项解释

* `probe_quality_score`：基于 IC、分段表现、覆盖率
* `contract_alignment_score`：是否在回答当前 logic 的 focus question
* `novelty_score`：是否与已有 logic/family/library 过于相似
* `local_robustness_score`：core/neighbor probe 是否都还行
* `logic_priority_score`：继承 logic schedule 的优先级
* `diversity_bonus`：避免本轮所有 route 都是同一种结构

## 5c. 按 quota 选

对每个 logic：

* 按 `route_select_score` 排序
* 最多只选前 `direction_quota` 条 route
* 其余 route 记为 `reserved` 或 `rejected`

---

# 十一、Candidate Expansion

## Step 6：模板化展开正式 candidates

只对通过 Step 5 的 route 展开 candidate。

## route_type 对应的默认 expansion template

### `genesis`

* 2 个窗口变体
* 1 个 rank / 标准化变体
* 总数不超过 3

### `mutate`

* 1 个参数变体
* 1 个稳定性修复变体
* 1 个 decorrelate 变体

### `crossover`

* 1 个 additive
* 1 个 gated
* 1 个 interaction
* 必须限制复杂度

### `repair`

* 降复杂度
* 调整条件阈值
* 替换 proxy
* 修复 overlap

### `decorrelate`

* 引入 residualization
* 替换条件变量
* 改 family 结构但保留逻辑核心

## candidate 约束

* 不得超过该 logic 的 `candidate_quota`
* 不得命中 `avoid_patterns`
* 不得与 route 目标无关
* 默认表达式深度受限
* Python candidate 仅在 DSL 无法合理表达时使用

---

# 十二、Candidate Schema

每个 candidate 必须保留完整上下文：

```yaml
candidate_id: C042_03
logic_id: L021
route_id: R021_01
family_id: FM_breakout
route_type: genesis
source_type: dsl   # dsl / python

name: "compression_rank_breakout_10"
expression: "..."
rationale: "在压缩条件下测试 breakout 是否更稳"
implementation_reason: "simple conditional breakout; naturally supported by IfElse + TsRank + Std"

lineage:
  parent_logic: L021
  parent_routes: [R021_01]
  parent_factors: []
  mutation_type: genesis
```

如果是 Python candidate，则必须改为：

```yaml id="c8fj7j"
candidate_id: C042_07
logic_id: L008
route_id: R008_02
family_id: FM_regime_switch
route_type: repair
source_type: python

name: "vol_regime_switch_repair"
params:
  vol_window: 20
  thresh: 0.8
param_space:
  vol_window: [10, 20, 40]
  thresh: [0.6, 0.8, 0.9]
code: |
  def compute_factor(df, params, ops):
      vol = ops.realized_vol(df["close"], params["vol_window"])
      trend = ops.ts_mean(df["close"].pct_change(), 5)
      rev = -ops.delta(df["close"], 5)
      high_vol = ops.cs_rank(vol) > params["thresh"]
      signal = trend.copy()
      signal[~high_vol] = rev[~high_vol]
      return signal

rationale: "修复原 DSL route 在状态切换上的表达扭曲"
implementation_reason: "requires regime branching; DSL unnatural"

lineage:
  parent_logic: L008
  parent_routes: [R008_02]
  parent_factors: [F013]
  mutation_type: repair
```

---

# 十三、Batch 级别控制

## Step 7：控制 candidate 总量与分布

在所有 candidate 生成完后，必须做一次 batch-level sanity check：

### 检查项

* 每个 logic 是否超过 `candidate_quota`
* 总 candidate 是否超过全局预算
* family 分布是否过于集中
* Python candidate 是否过多
* 是否存在近似重复候选

### 目标

让最终 batch：

* 干净
* 受控
* 可解释
* 可追踪

---

# 十四、写 batch manifest

## Step 8：写正式候选文件

将正式 candidates 写入：

```text
storage/candidates/batch_XXX.yaml
```

每个 candidate 必须包含：

* `candidate_id`
* `logic_id`
* `route_id`
* `family_id`
* `route_type`
* `source_type`
* `name`
* `expression` 或 `code`
* `implementation_reason`
* `rationale`
* `lineage`

这份文件是 `/execute` 的正式输入。

---

# 十五、写 idea report

## Step 9：写中间证据文件

除了 batch manifest，还必须输出：

```text
storage/candidates/batch_XXX_idea_report.yaml
```

## idea report 至少记录

* 本轮读取的 logic schedule
* 本轮展开了哪些 logic
* 每个 logic 分配了多少 route budget
* 每条 route 的 probe 结果
* 哪些 route 被淘汰
* 哪些 route 被继续展开
* route selection 的原因
* candidate expansion 的分布
* DSL / Python 的分布情况

## 作用

让后续 `/judge` 和 `/logic feedback` 能追踪：

* 问题出在 logic 层
* 还是 route 层
* 还是 candidate 展开层

---

# 十六、`idea` 的职责边界

## `idea` 负责

* 消费 logic contract
* 规划 route
* 设计 probe
* 过滤垃圾 route
* 选择继续展开的 route
* 生成正式 candidate
* 输出 batch 与 idea report

## `idea` 不负责

* 创建新 logic
* 修改 logic 生命周期
* 更新全局 state
* 做最终录取
* 做长期 memory 治理

这些事情属于 `/logic` 或 `/judge`。

---

# 十七、最终目标

`factor-idea v2` 的目标不是“多想几个新方向”，而是：

* 在 logic 约束下进行研究设计
* 用训练期内 probe 便宜地过滤垃圾
* 把值得继续投资的 route 转成正式 candidate
* 为 `/execute` 提供干净、可追踪、上下文完整的输入

---

# 十八、简短总结

> `factor-idea v2` 应该是一套“在 logic contract 约束下，将市场逻辑拆成 research routes，用训练期内 probe 过滤垃圾，再将通过的 routes 模板化展开成正式 candidates”的中层执行系统。

```
```
