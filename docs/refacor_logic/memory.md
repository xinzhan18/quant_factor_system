下面给你一版**最新的 memory 管理方法**。
这不是文件清单，而是一套能支撑你现在这条链路的**统一研究状态架构**：

* `logic`
* `idea`
* `execute`
* `judge`
* `report`

目标很明确：

> **让 LLM 能在一个稳定、可回写、可持续学习的状态系统里，自主探索、自主维护。**

---

# 一、先给总原则

不要再按“yaml 还是 md”来管理 memory。
要按**用途**来管理。

## 结构化 memory

给机器读写、给 skill 决策用。
用 **yaml**。

## 叙事型 memory

给人看、给复盘、给报告解释用。
用 **md**。

一句话：

> **规则、状态、对象放 yaml；解释、总结、复盘放 md。**

---

# 二、最新 memory 架构：6 个核心对象层

我建议现在正式定成这 6 层。

## 1. Research State

全局运行状态。

回答：

* 现在在第几轮
* 当前 active logic 是谁
* 当前 active route 是谁
* 当前 bottleneck 是什么
* 当前 system flags 是什么

这是**所有 skill 的统一入口状态**。

---

## 2. Logic Memory

研究命题层。

回答：

* 当前有哪些 logic
* 每个 logic 的 hypothesis 是什么
* status / priority / budget 是什么
* 哪些 family 已有效
* 当前 bottleneck 是什么
* 下一步该做什么

这是**外循环主对象**。

---

## 3. Route Memory

中层探索层。

回答：

* 某个 logic 下有哪些 route
* 每条 route 在回答什么问题
* probe 结果怎样
* execute/judge 后发生了什么
* 失败模式是什么
* 下一步继续还是停止

这是**你们现在最该补的一层**。

---

## 4. Factor Memory

资产层。

回答：

* 已录取因子是什么
* 来自哪个 logic / route
* 用 DSL 还是 Python
* 在什么评估口径下成立
* 是否替换过别人
* 报告在哪里

这是**library 的正式索引层**。

---

## 5. Policy Memory

规则层。

回答：

* 哪些字段/算子/实现能用
* 默认 DSL 还是 Python
* 哪些模式 forbidden
* 哪些 failure 怎么定义
* execute 用什么 profile

这是**系统制度层**。

---

## 6. Narrative Memory

叙事层。

回答：

* 这轮发生了什么
* 为什么形成这条 policy
* 这个因子到底在干什么
* 某次失败的复盘是什么

这是**给人看的解释层**。

---

# 三、最新推荐目录结构

```text
storage/
  state/
    research_state.yaml

  logic/
    registry.yaml
    cards/
      L001.yaml
      L002.yaml

  routes/
    registry.yaml
    cards/
      R001.yaml
      R002.yaml

  registry/
    factors/
      index.yaml
      factor_001.yaml
      factor_002.yaml

  policy/
    capability_registry.yaml
    implementation_policy.yaml
    failure_taxonomy.yaml

  evaluation_profiles/
    universe/
      all_a_share.yaml
      csi1000.yaml
    tradability/
      china_a_daily_tradeable_v1.yaml
    preprocess/
      default_preprocess_v1.yaml
    neutralization/
      none.yaml
      industry_cap.yaml
    style_barra/
      barra_cn_v1.yaml
    evaluation/
      standard_eval_v2.yaml

  memory/
    forbidden.yaml

  history/
    batch_001.yaml
    batch_002.yaml

  reports/
    batch/
      batch_001_summary.md
    factors/
      F001 xxx.md
      F002 yyy.md

  notes/
    mining-lessons.md
    postmortems/
      2026-04-route-overlap.md
```

---

# 四、每个核心 memory 具体怎么管

---

## A. `research_state.yaml`

这是总控状态。

### 用途

所有 skill 在开工前都应该先读它。

### 建议字段

```yaml
research_state:
  current_batch: batch_042

  active_logic_ids:
    - L021
    - L008

  active_route_ids:
    - R021_01
    - R021_02
    - R008_01

  current_focus:
    - "compression breakout 独立性验证"
    - "regime repair route helper化评估"

  current_bottlenecks:
    - overlap_too_high
    - helper_missing_for_regime_routes
    - size_drift_risk

  policy_flags:
    prefer_dsl: true
    python_only_helper_based: true
    vectorization_required: true
    use_barra_view: true

  last_updated_at: "2026-04-04T12:00:00"
```

### 谁写

主要由：

* `logic`
* `judge`

更新。

### 谁读

所有 skill 都读。

---

## B. Logic Memory

分成：

* `logic/registry.yaml`
* `logic/cards/LXXX.yaml`

### `logic/registry.yaml`

只做索引。

建议字段：

```yaml
logics:
  - logic_id: L021
    name: compression_breakout
    category: volume_price
    status: active
    priority: high

  - logic_id: L008
    name: regime_switch_repair
    category: volatility
    status: warm
    priority: medium
```

### `logic/cards/LXXX.yaml`

这是完整对象。

建议字段：

```yaml
logic_id: L021
name: compression_breakout
category: volume_price
status: active
priority: high

hypothesis:
  condition: "量能压缩、波动收敛"
  behavior: "后续突破延续"
  timeframe: "5-20d"
  direction: long_on_breakout

preferred_families:
  - breakout
  - compression_spread

productive_families:
  - breakout

failed_families:
  - plain_rank_only

current_bottleneck: overlap_too_high
next_actions:
  - "尝试 decorrelate breakout route"
  - "测试 residual volume gate"

implementation_space:
  execution_style: dsl_preferred
  vectorization_risk: low
  style_drift_risk: medium

stats:
  probe_attempts: 5
  eval_attempts: 3
  admits: 1
  near_miss: 2
  best_ic: 0.013
  best_incremental_ic: 0.008
```

### 谁写

* `logic`
* `judge`

### 谁读

* `logic`
* `idea`
* `judge`
* `report`

---

## C. Route Memory

分成：

* `routes/registry.yaml`
* `routes/cards/RXXX.yaml`

### `routes/registry.yaml`

索引。

```yaml
routes:
  - route_id: R021_01
    logic_id: L021
    family_id: FM_breakout
    route_type: genesis
    status: active

  - route_id: R021_02
    logic_id: L021
    family_id: FM_breakout
    route_type: decorrelate
    status: warm
```

### `routes/cards/RXXX.yaml`

完整 route 对象。

```yaml
route_id: R021_01
logic_id: L021
family_id: FM_breakout
route_type: genesis
status: active

research_question: "量能压缩条件是否能显著提升 breakout 的独立性"
hypothesis_slice: "compression condition + breakout family"

route_structure:
  requires_branching: false
  requires_multi_stage_pipeline: false
  requires_multi_state_logic: false
  dsl_naturalness: high
  vectorizable: true
  helper_required: false
  size_drift_risk: medium

probe_history:
  - batch_id: batch_042
    core_probe_ic: 0.014
    neighbor_probe_ic: 0.012
    verdict: pass

execute_outcomes:
  eval_attempts: 3
  admits: 1
  near_miss: 1
  overlap_blocked: 1
  style_drift_blocked: 0

primary_failure_mode: overlap_too_high
implementation_preference: dsl
next_action: decorrelate
```

### 为什么 route memory 是核心升级点

因为很多最有价值的学习不是 logic 级，也不是 factor 级，而是：

* 哪类 route probe 总过但 execute 总死
* 哪类 route 总 overlap 高
* 哪类 route 容易 drift 到 size/style
* 哪类 route 需要 helper

这些必须沉在 route memory。

### 谁写

* `idea`
* `judge`

### 谁读

* `idea`
* `judge`
* `report`

---

## D. Factor Memory

分成：

* `registry/factors/index.yaml`
* `registry/factors/factor_XXX.yaml`

### `index.yaml`

索引。

```yaml
factors:
  - factor_id: F013
    name: compression_rank_breakout_10
    logic_id: L021
    route_id: R021_01
    category: volume_price

  - factor_id: F014
    name: regime_switch_repair_v2
    logic_id: L008
    route_id: R008_02
    category: volatility
```

### `factor_XXX.yaml`

完整资产对象。

```yaml
factor_id: F013
name: compression_rank_breakout_10
category: volume_price
source_type: dsl

logic_id: L021
route_id: R021_01
route_type: genesis
family_id: FM_breakout

lineage:
  parent_logic: L021
  parent_routes: [R021_01]
  parent_factors: []
  mutation_type: genesis

admitted_at: "2026-04-04"
decision: admit

evaluation_profile:
  universe: all_a_share
  tradability: china_a_daily_tradeable_v1
  preprocess: default_preprocess_v1
  neutralization: none
  style_barra: barra_cn_v1

metrics:
  ic_mean_oos: 0.013
  icir_oos: 0.18
  monotonicity: 0.74
  ls_sharpe: 1.21

style_summary:
  factor_size_corr: -0.31
  barra_residual_ic_mean: 0.005
  dominant_barra_style: size
  alpha_survival_ratio: 0.38
  style_warning: true

replacement_history: []
report_path: "storage/evidence/vault/factors/F013 compression_rank_breakout_10.md"
```

### 谁写

* `judge`

### 谁读

* `logic`
* `execute`
* `judge`
* `report`

---

## E. Policy Memory

这是整套系统的制度层。
建议至少分三块。

---

### 1. `capability_registry.yaml`

存能力边界。

包括：

* fields
* DSL operators
* Python helpers
* precheck policy
* vectorization constraints
* forbidden slow patterns

这部分你们已经讨论过很多次了。

---

### 2. `implementation_policy.yaml`

存实现形式规则。

建议字段：

```yaml
default:
  prefer_dsl: true
  python_only_helper_based: true
  vectorization_required: true

python_allowed_if:
  - route_requires_multi_stage_pipeline
  - route_requires_multi_state_logic
  - dsl_expression_unnatural
  - route_is_repair_or_decorrelate
  - helper_backed_complex_logic

python_discouraged_if:
  - simple_breakout
  - simple_reversal
  - simple_rank_spread
  - only_window_variation

helper_required_if:
  - repeated_performance_rejected_python_pattern
  - repeated_regime_route_needing_branching
  - repeated_decorrelate_route_needing_custom_op
```

---

### 3. `failure_taxonomy.yaml`

统一失败分类。

建议字段：

```yaml
failure_types:
  - weak_signal
  - high_overlap
  - hard_gate_rejected
  - implementation_blocked
  - performance_rejected
  - helper_required
  - regime_mismatch
  - unstable_oos
  - size_drift
  - style_repackaging
```

### 为什么这层重要

没有它，judge 的学习很难真正结构化。

---

## F. Forbidden Memory

`memory/forbidden.yaml`

存反复被证明低价值的东西。

```yaml
forbidden_patterns:
  - pattern_id: FP001
    type: expression_template
    summary: "plain_breakout_with_no_volume_context"
    reason: "重复多轮无增量"
    failure_mode: weak_signal

  - pattern_id: FP002
    type: implementation
    summary: "groupby_apply_custom_python"
    reason: "performance_rejected repeatedly"
    failure_mode: performance_rejected

  - pattern_id: FP003
    type: route_pattern
    summary: "pure_amount_breakout_no_residualization"
    reason: "repeated size/style drift"
    failure_mode: size_drift
```

### 谁写

* `judge`

### 谁读

* `logic`
* `idea`
* `execute`

---

# 五、哪些东西应该留在 md

md 不应该承担机器规则。
它应该承担“叙事层”。

---

## 应该保留为 md 的内容

### 1. `mining-lessons.md`

保留高层经验总结。
不是规则库。

### 2. `batch summaries`

每轮复盘。

### 3. `factor reports`

正式资产文档。

### 4. `postmortems`

大故障、大转折、大设计复盘。

---

## 一条硬规则

> **机器依赖的规则不能只存在于 md。**

如果某条东西会被 `idea / execute / judge` 直接用来决策，就必须进入 yaml。

---

# 六、完整的读写流程

下面是你现在最需要的“谁读谁写”的统一逻辑。

---

## `logic`

### 读

* `research_state.yaml`
* `logic cards`
* `factor registry`
* `implementation_policy.yaml`
* `forbidden.yaml`
* `failure_taxonomy.yaml`

### 写

* `logic cards`
* `logic registry`
* `research_state.yaml`

---

## `idea`

### 读

* `research_state.yaml`
* `logic cards`
* `route cards`
* `factor registry`
* `capability_registry.yaml`
* `implementation_policy.yaml`
* `forbidden.yaml`

### 写

* `route cards`
* `batch_XXX.yaml`
* `batch_XXX_idea_report.yaml`

---

## `execute`

### 读

* `batch_XXX.yaml`
* `capability_registry.yaml`
* `evaluation_profiles/`
* `factor registry`
* `implementation_policy.yaml`

### 写

* `batch_XXX_result.yaml`
* `batch_XXX_values.pkl`
* `batch_XXX_execute_report.yaml`

### 备注

execute 不主写长期 memory。
它写的是 judge 后续要消费的证据。

---

## `judge`

### 读

* `batch_XXX_result.yaml`
* `batch_XXX_values.pkl`
* `batch_XXX.yaml`
* `logic cards`
* `route cards`
* `factor registry`
* `implementation_policy.yaml`
* `failure_taxonomy.yaml`

### 写

* `factor registry`
* `logic cards`
* `route cards`
* `forbidden.yaml`
* `implementation_policy.yaml`
* `research_state.yaml`
* `batch_XXX_judge_report.yaml`

### 备注

judge 是 memory 的**主更新器**。

---

## `report`

### 读

* `factor registry`
* `batch_XXX_result.yaml`
* `batch_XXX_judge_report.yaml`
* `logic cards`
* `route cards`
* `report_data.json`

### 写

* factor report（md）
* Factor Library 总览页（md）
* batch summary（md，可选）

---

# 七、最新 memory 管理方法的核心思想

如果压缩成几句话，就是：

## 1. 统一入口

所有 skill 先看 `research_state.yaml`。

## 2. 对象化

所有核心实体都要变成 card：

* logic card
* route card
* factor card

## 3. 规则化

所有机器依赖规则都进入 policy yaml：

* capability
* implementation
* failure taxonomy
* forbidden

## 4. judge 主回写

系统学习主要在 judge 后结构化沉淀。

## 5. md 只做叙事

不再让 md 承担机器规则。

---

# 八、如果你现在就要开始做，优先级怎么排

## P0 立刻做

1. `research_state.yaml`
2. `route cards`
3. `implementation_policy.yaml`

## P1 很快做

4. `failure_taxonomy.yaml`
5. `factor registry` 增强
6. `learning.md` 规则迁移

## P2 中期做

7. family registry
8. policy versioning
9. helper demand tracking

---

# 九、最短总结

最新的 memory 管理方法，不是“再多几个 yaml”，而是：

> **把 memory 重构成一套由 `research_state + logic cards + route cards + factor registry + policy registry + narrative notes` 组成的研究状态系统。**

这样 LLM 才能真正做到：

* 知道现在该做什么
* 知道以前做过什么
* 知道什么不能再做
* 知道失败该往哪回写
* 知道成功该如何沉淀
* 知道下一轮该如何更聪明地继续探索

如果你愿意，我下一步可以直接把这套 memory 再展开成**完整的 yaml schema 模板**。
