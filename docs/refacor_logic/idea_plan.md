---
name: factor-idea
description: 消费 logic schedule，将研究命题拆成 routes，用 train 内 probe 过滤垃圾，并生成正式 candidate batch
user_invocable: true
---

# 因子创意生成 — `idea` Research Design v3

## 1. 目标

`idea` 是研究系统里的中层设计器。

它只负责三件事：

1. 把 `logic` 给出的研究命题拆成有限、可验证的 batch 内实验切片
2. 用 `train` 内的轻量 probe 过滤明显垃圾路线
3. 把少量值得继续验证的实验切片冻结成正式 candidates

它不负责：

- 创建新 logic
- 做正式统计评估
- 做 admit / reject / replace
- 更新全局 policy
- 更新长期 memory

这些属于 `logic`、`research_execute` 和 `research_judge`。

---

## 2. 核心原则

### 原则 1：`idea` 不决定研究主题

研究主题由 `logic schedule` 决定。
`idea` 只能在当前 active logic 的 contract 内展开。

### 原则 2：`idea` 的基本单位是 route

`route` 在当前版本里不再是长期治理对象。

它只是 batch 内的设计标签，用来回答：

- 这一轮围绕当前 hypothesis 试哪个切片
- 哪几条 candidate 属于同一组实验上下文

也就是说：

> `route = batch-local experiment group`

而不是长期持久化的行政中间层。

### 原则 3：probe 只负责过滤垃圾

probe 的目标不是证明 route 优秀，而是淘汰明显不值得继续投入的路线。

probe 不做：

- 正式统计裁决
- validation 判断
- holdout 判断
- 最终录取预测

### 原则 4：probe 只能使用 `train`

`idea` 阶段只能使用：

- `train`

不能使用：

- `validation`
- `holdout`

### 原则 5：少做评分，多做约束

`idea` 不应该把 route 选择做成一个伪精确 ranking 模型。

更成熟的做法是：

- 先用硬约束过滤
- 再做少量、粗粒度排序
- 最后按 quota 选出本轮进入 `research_execute` 的 route

### 原则 6：candidate expansion 必须模板化

route 一旦通过 probe，只能按 `route_type` 的模板有限展开，不能自由发散。

### 原则 7：默认优先 DSL

只要当前 DSL 能自然表达，就必须优先 DSL。
Python 只允许作为受控例外。

### 原则 8：必须保留会话内快速回路

在 candidate freeze 之前，`idea` 允许和 quick execute 做小步往返：

- probe 判断明显失真
- 表达式语法错误
- 路线切片过粗或过细

这些都允许在同一会话内直接修正。

只有被冻结进 `batch_XXX.yaml` 的 candidate，才进入正式 `research_execute / research_judge` 回路。

---

## 3. 输入对象

`idea` 至少读取：

```text
storage/logic/snapshots/latest_schedule_snapshot.yaml
storage/logic/registry.yaml
storage/logic/cards/*.yaml
storage/policy/capability_registry.yaml
storage/policy/implementation_policy.yaml
storage/registry/factors/index.yaml
storage/memory/forbidden.yaml
storage/notes/mining-lessons.md
storage/ledger/search_ledger.yaml
```

若存在 family registry，可以读取；
但它不再是 `idea` 的硬前置依赖。

对每个 `eligible_this_round: true` 的 logic，至少读取：

- `logic_id`
- `priority`
- `direction_quota`
- `candidate_quota`
- `preferred_mode`
- `preferred_families`
- `suggested_ops`
- `required_fields`
- `avoid_patterns`
- `current_focus_question`

`idea` 不能把 `family_id` 写成伪精确结论。

它只能：

1. 复用 `family_registry.yaml` 中已注册的 `family_id`
2. 对不稳定的新机制暂用 `PF_*` provisional family
3. 在完全不确定时使用 `FM_unknown`

---

## 4. 研究样本制度

研究系统固定采用三层样本：

1. `train`
2. `validation`
3. `holdout`

其中：

- `idea` 只允许看 `train`
- `research_execute` 日常看 `train + validation`
- `holdout` 不进入 `idea` 的日常设计循环

因此，`idea report` 中必须显式写清楚：

```yaml
sample_policy:
  train_range: ["2015-01-01", "2021-12-31"]
  validation_used: false
  holdout_used: false
  policy_version: research_sample_v3
```

---

## 5. 本轮预算

### 5.1 全局预算

建议保持小而硬的预算控制：

- 总 route 数不超过 3
- 总 candidate 数不超过 6~8

### 5.2 每个 logic 的预算

- `direction_quota`：该 logic 本轮最多开几条 route
- `candidate_quota`：该 logic 本轮最多产出几个 candidate

### 5.3 预算纪律

预算的意义不是节省算力，而是控制：

- 多重检验强度
- 路径依赖失控
- 垃圾候选泛滥

---

## 6. Route 对象

### 6.1 定义

route 是某个 logic 在本轮的一条 batch-local 研究路线。

它服务于：

- 批次内分组
- idea report 解释
- candidate lineage

它不再默认对应：

- 长期 `route card`
- route lifecycle 持久化
- 独立 route memory

它至少包含：

```yaml
route_id: R021_01
logic_id: L021
family_id: FM_breakout
route_type: genesis
experiment_lineage_tag: ELT_L021_breakout_compression_gate_v1
priority: high

research_question: "量能压缩条件是否提升 breakout 的独立性"
hypothesis_slice: "compression gate + breakout family"

origin:
  source: logic_native
  parent_experiment_tags: []
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
  probe_profile: probe_train_only_v3

expansion_template:
  candidate_target_count: 3
  allowed_variations:
    - window_variation
    - rank_transform
    - residual_gate
  forbidden_variations:
    - pure_price_only_breakout
```

`experiment_lineage_tag` 是跨 batch 追踪同一研究切片的最小对象。

它不是 route card，也不是 family。
它只回答：

- 这组实验在多轮里是不是同一个切片
- 这个切片过去是 continue / pause / kill 还是有 admit

推荐生成规则：

- `logic_id + hypothesis_slice + route_type + key_conditioning`

但不能直接做自由字符串拼接。

必须先做归一化：

1. `hypothesis_slice`
   - 统一小写
   - 去空格
   - 同义词映射到固定词表
2. 组成字段顺序固定为：
   - `logic_id`
   - `route_type`
   - `mechanism_anchor`
   - `conditioning_anchor`
   - `family_anchor`
3. 多个 conditioning / anchor 必须先按字典序排序
4. 最终 tag 推荐形如：
   - `ELT_L021_genesis_breakout_compression_volume_v1`

如果实现层发现：

- 新生成 tag 与历史 tag 只在词序上不同
- 或 anchor 集合完全相同

则写入 `search_ledger` 前必须优先复用历史 tag，
而不是创建新的 ELT。

这样 `route` 即使只活一个 batch，跨 batch 的连续性仍可由 `experiment_lineage_tag` 追踪。

### 6.2 route 来源

只允许三类来源：

1. `logic_native`
2. `logic_scoped_mutation`
3. `logic_approved_crossover`

不允许脱离当前 logic contract 自由发散。

如果 contract 中存在：

- `adjacent_discovery_route_quota > 0`

则 `idea` 必须优先为该 logic 预留对应数量的相邻 discovery route。

### 6.3 family_id 分配规则

`family_id` 是渐进式标签，不是 blocking gate。

规则如下：

1. 若 registry 中已有合适 family，则直接使用
2. 若只知道“大致属于某类机制”，允许使用 `PF_*`
3. 若当前确实无法可靠命名，则使用 `FM_unknown`

正式 execute / judge 仍可继续进行，只是在 family-level redundancy 上采取保守模式。

---

## 7. Route 类型

`route_type` 看的是研究目标，不是表达式长相。

### `genesis`

- 首次验证某个 hypothesis slice
- 原生机制路线

### `mutate`

- 围绕已有有效或 near-miss 结构做局部变形

### `crossover`

- 在 contract 允许下组合两个已有结构

### `repair`

- 修复已有 route 的明确缺陷

### `decorrelate`

- 在保留逻辑核心下主动降低 overlap

---

## 8. 实现形式选择

### 8.1 默认优先 DSL

以下场景默认优先 DSL：

- breakout
- reversal
- momentum
- compression_spread
- rank_spread
- rolling_corr
- volatility_proxy
- simple_conditional_route

并且同时满足：

- 不需要复杂分支
- 不需要多状态切换
- 不需要多阶段 pipeline
- `dsl_naturalness != low`

### 8.2 允许 Python 的条件

仅当以下任一成立，才允许 Python：

- `requires_multi_stage_pipeline = true`
- `requires_multi_state_logic = true`
- `estimated_branch_count > 1`
- `dsl_naturalness = low`

### 8.3 Python 限制

即使允许 Python，也必须满足：

- `max_code_lines <= 30`
- `max_branch_count <= 3`
- `max_param_count <= 3`
- `max_intermediate_variable_count <= 6`
- 只允许白名单 `ops.*`
- 不允许任意 import
- 不允许网络调用
- 不允许文件 IO

如果超出限制，则：

1. 优先重写为 DSL
2. 或降复杂度
3. 或直接放弃该 route

---

## 9. Probe 设计

### 9.1 默认单 probe，neighbor 仅在高风险 route 启用

默认只要求：

- `core_probe_form`

只有以下情况才追加：

- `neighbor_probe_form`

触发条件：

- route 复杂度高
- route 涉及 regime / multi-stage 结构
- route 属于 `repair / decorrelate`
- 当前 logic 明显处于高重叠区域

### 9.2 Probe 的唯一目标

probe 只回答：

- 这条 route 是否明显垃圾
- 是否值得进入正式 `research_execute`

probe 不回答：

- 这是不是 admitted factor
- 这条 route 最终值不值得录取
- 它在 validation 上是否成立

### 9.3 probe form 要求

- `core_probe_form` 必须反映 route 的核心问题
- `neighbor_probe_form` 若启用，必须是局部邻近变体
- 不做复杂参数优化
- 不做 validation 预演

---

## 10. Probe 运行规则

### 10.1 数据范围

probe 只能使用 `train`。

例如：

```yaml
train_range:
  start: 2015-01-01
  end: 2020-12-31

train_splits:
  - [2015-01-01, 2017-12-31]
  - [2018-01-01, 2020-12-31]
```

### 10.2 最少输出字段

#### 表达式层

- `computable`
- `valid_ratio`
- `variance_ok`

#### 轻量信号层

- `signal_strength_hint`
- `split_consistency_hint`
- `neighbor_consistency`

#### route 层

- `forbidden_hit`
- `duplicate_risk_hint`
- `complexity_ok`

### 10.3 probe 不输出正式 IC 证据包

`idea` 可以保留很粗的强弱提示，但不应输出看起来像正式评估的完整统计包。

建议：

- 不把 `probe` 设计成迷你版 execute
- 不在这里做 `ic_ir_validation`、`oos_decay_ratio` 之类字段

---

## 11. Probe 的检查逻辑

probe 只做最小垃圾过滤，不应发展成迷你版 execute。

### 11.1 可计算性检查

- 表达式能正常计算
- 非全空
- 非近常数
- 覆盖率不过低

### 11.2 轻量强度检查

- 在 `train` 内不是完全无信号
- 不要求给出精细强弱排序

### 11.3 轻量稳定性检查

- train 内部分段不完全翻脸
- core / neighbor probe 不应一边完全崩塌

### 11.4 脏路线检查

- 命中 forbidden
- 复杂度过高
- 明显重复
- 命中已知坏模板

### 11.5 verdict

probe verdict 只允许：

- `pass`
- `reserve`
- `fail`

含义如下：

- `pass`：可进入正式 candidate expansion
- `reserve`：暂时保留，只有 budget 足够才进入扩展
- `fail`：本轮不再继续

### 11.6 最小 fail 规则

满足任意一条即可 `fail`：

- `computable = false`
- `valid_ratio < 0.30`
- `variance_ok = false`
- `forbidden_hit = true`
- `complexity_ok = false`
- `duplicate_risk_hint = high`
- `signal_strength_hint = none`
- `split_consistency_hint = broken`

这里不再使用类似 `abs(ic_mean_full) < 0.01` 这种伪精确阈值作为 probe 主裁决。

---

## 12. Route 选择

### 12.1 Step 1：硬过滤

直接过滤：

- `probe_verdict = fail`
- 不符合 logic contract
- 命中 forbidden
- 明显重复
- 复杂度超限

### 12.2 Step 2：粗粒度分组

剩余 route 只分三档：

- `priority_pass`
- `normal_pass`
- `reserve`

建议规则：

- `priority_pass`：机制对焦明确、probe pass、结构干净
- `normal_pass`：probe pass，但新意或稳定性提示一般
- `reserve`：probe reserve，或虽 pass 但与现有 route 过近

### 12.3 Step 3：少量排序

只有在同一档位内部，才允许做少量排序。

排序依据只允许使用粗粒度字段：

- `contract_alignment`
- `novelty_bucket`
- `structure_simplicity`
- `diversity_need`

不再使用线性加权总分。

### 12.4 Step 4：按 quota 选择

对每个 logic：

- 优先选 `priority_pass`
- 再选 `normal_pass`
- 最后在 budget 有余时考虑 `reserve`
- 超出 quota 的 route 记为 `reserved` 或 `rejected`

---

## 13. Candidate Expansion

只有通过 route 选择的 route 才能展开 candidate。

### 13.1 `genesis`

- 2 个窗口变体
- 1 个 rank / standardize 变体
- 总数不超过 3

### 13.2 `mutate`

- 1 个参数变体
- 1 个稳定性修复变体
- 1 个 decorrelate 变体

### 13.3 `crossover`

- 1 个 additive
- 1 个 gated
- 1 个 interaction
- 必须严格限制复杂度

### 13.4 `repair`

- 降复杂度
- 调条件阈值
- 换 proxy
- 修 coverage / overlap

### 13.5 `decorrelate`

- 引入 residualization
- 替换条件变量
- 保留逻辑核心但改 family 结构

### 13.6 candidate 约束

- 不得超过该 logic 的 `candidate_quota`
- 不得命中 `avoid_patterns`
- 不得与 route 目标无关
- 默认深度受限
- Python 只在 DSL 不自然时使用

---

## 14. Quick Execute

`quick execute` 是快速回路中的 candidate-freeze overlay。

它不是新的长期治理对象，也不是正式 execute 的简化别名。

它的目标只有一个：

> 在 candidate freeze 之前，快速判断当前表达式是否值得送进正式回路。

### 14.1 样本边界

`quick execute` 默认只允许看：

- `train`

不允许看：

- `active validation`
- `holdout`

这样它和正式回路保持样本隔离。

### 14.2 它和 probe 的区别

- `probe`
  - 面向 route / experiment slice
  - 判断这条研究路线是不是垃圾
- `quick execute`
  - 面向具体 candidate draft
  - 判断这个表达式草稿是否已经足够稳定，可以冻结

在实现上，`quick execute` 可以直接建立在 probe 输出之上。

更准确地说：

- `probe` 负责 route 级垃圾过滤
- `quick execute` 只是在 candidate draft 上追加：
  - `turnover_hint`
  - `nearest_factor_hint`
  - `freeze_recommendation`

因此当前版本不要求把 `quick execute` 实现成独立 skill 或独立长期对象。
它可以被视为：

> `probe + candidate_freeze_check`

### 14.3 最小输出

```yaml
quick_execute_result:
  candidate_draft_id: D042_03
  train_ic_hint: weak_to_medium
  train_sign_consistency: acceptable
  coverage_hint: acceptable
  turnover_hint: acceptable
  nearest_factor_hint: F011
  computable: true
  freeze_recommendation: revise   # revise / freeze_candidate / drop
```

字段解释：

- `train_ic_hint`
  - 只回答 train 内是否完全无效、边缘、还是已有基本信号
- `train_sign_consistency`
  - 只回答 train 内部分段是否大体同向
- `coverage_hint`
  - 只回答覆盖率是否明显过低
- `turnover_hint`
  - 只回答是否出现明显过高换手风险
- `nearest_factor_hint`
  - 只做非常粗的最近库内对象提示，不做正式 redundancy 裁决
- `freeze_recommendation`
  - `freeze_candidate`：可以送正式回路
  - `revise`：继续在快速回路微调
  - `drop`：当前草稿不值得继续

### 14.4 结果落点

`quick execute` 结果不进入：

- 正式 `research_result`
- `research_judge`
- 长期 memory
- search ledger 正式计数

它只允许存在于：

- 当前会话上下文
- 或 `batch_XXX_idea_report.yaml` 的临时附录

这意味着：

- `quick execute` 是高频工作流概念
- 不是独立 memory 对象
- 也不是 formal ledger 对象

---

## 15. Freeze Boundary

candidate 只有在满足以下条件时才允许冻结进 `batch_XXX.yaml`：

1. probe 不是 `fail`
2. `quick execute` 给出：
   - `freeze_recommendation = freeze_candidate`
3. 表达式已无语法 / 可计算问题
4. `implementation_reason` 已明确
5. 已经拿到一个稳定的 `experiment_lineage_tag`

默认规则：

- `pass + freeze_candidate`：自动冻结
- `pass + revise`：继续留在快速回路
- `reserve + freeze_candidate`：只有 budget 有余才冻结
- `drop`：不进入正式 batch

边缘情况处理：

- 若 `train_ic_hint = weak_to_medium` 但 `train_sign_consistency = acceptable`，
  默认优先 `revise`，而不是立即 freeze
- 只有当：
  - 表达式已经稳定
  - 研究问题明确
  - 当前 batch 预算允许
  时，才把 borderline 草稿送进正式回路

冻结边界的本质是：

- freeze 之前可以高频试错
- freeze 之后必须进入正式 execute/judge 协议

---

## 16. Candidate Schema

每个 candidate 必须保留完整上下文：

```yaml
candidate_id: C042_03
logic_id: L021
route_id: R021_01
family_id: FM_breakout
route_type: genesis
experiment_lineage_tag: ELT_L021_breakout_compression_gate_v1
source_type: dsl

name: compression_rank_breakout_10
expression: "..."
rationale: "在压缩条件下测试 breakout 是否更稳"
implementation_reason: "simple conditional breakout; naturally supported by DSL"

lineage:
  parent_logic: L021
  parent_experiment_tags: [ELT_L021_breakout_compression_gate_v1]
  parent_factors: []
  mutation_type: genesis
```

如果是 Python，则必须额外包含：

- `params`
- `param_space`
- `code`

---

## 17. Batch 级别控制

所有 candidates 生成完后，必须做 batch sanity check：

- 每个 logic 是否超过 `candidate_quota`
- 总 candidate 是否超过全局预算
- family 分布是否过于集中
- Python candidate 是否过多
- 是否存在近似重复候选

目标是让 batch 保持：

- 干净
- 受控
- 可解释
- 可追踪

---

## 18. 输出对象

### 18.1 Batch Manifest

写入：

```text
storage/candidates/batch_XXX.yaml
```

这是 `research_execute` 的正式输入。

### 18.2 Idea Report

写入：

```text
storage/candidates/batch_XXX_idea_report.yaml
```

至少记录：

- 读取的 logic schedule
- 本轮样本制度
- 本轮展开的 logic
- 每个 logic 的 route budget
- 每条 route 的 probe verdict
- 哪些 route 被过滤
- 哪些 route 被保留
- route 选择原因
- candidate expansion 分布
- DSL / Python 分布

---

## 19. 职责边界

`idea` 负责：

- 消费 logic contract
- 规划 route
- 设计 probe
- 过滤垃圾 route
- 选择继续展开的 route
- 生成正式 candidate
- 输出 batch 与 idea report

`idea` 不负责：

- 创建新 logic
- 看 validation / holdout
- 做正式统计评估
- 做 admit / reject / replace
- 更新全局 state
- 更新长期 policy

---

## 20. 最终原则

`idea` 的目标不是“多想几个方向”，而是：

1. 在 logic contract 约束下设计本轮实验
2. 用 `train` 内 probe 便宜地过滤垃圾
3. 把少量值得继续验证的 route 转成正式 candidates
4. 为 `research_execute` 提供干净、上下文完整、受控的输入
