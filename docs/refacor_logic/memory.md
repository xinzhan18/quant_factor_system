# Research Memory

## 1. 目标

这份文档定义的是研究系统的 memory 制度。

目标不是“多存几个 yaml”，而是建立一套稳定的研究状态系统，让：

- `logic` 知道当前该研究什么
- `idea` 知道当前批次该展开哪些实验切片
- `research_execute` 知道自己要按什么制度产出证据
- `research_judge` 知道什么可以回写，什么不能直接升级

当前 memory 设计必须同时服务两条回路：

1. 会话内快速研究回路
2. 正式 admission 回路

这里不讨论生产交易层 memory。

还必须额外服务两类治理对象：

1. `logic lifecycle arbitration`
2. `guarded writeback`

并补一个关键追踪对象：

3. `experiment lineage`

---

## 2. 总原则

### 原则 1：规则、状态、对象放 yaml

会被系统直接读取并用于决策的内容，必须进入结构化对象：

- yaml

### 原则 2：解释、复盘、报告放 md

叙事性内容进入：

- markdown

### 原则 3：memory 必须区分“证据”与“制度升级”

这是最关键的一条。

研究系统里很多东西都可以回写，但不是所有回写都应该升级为全局规则。

必须区分：

1. 本轮证据
2. 局部状态更新
3. 全局制度升级候选

### 原则 4：单轮 validation 不能直接升级核心 policy

单轮 batch 的 validation 结果，可以：

- 更新 candidate / route / logic 状态

但不能直接：

- 升级 `forbidden.yaml` 核心规则
- 升级 `implementation_policy.yaml` 全局规则
- 升级 hypothesis doctrine

这些必须经过重复证据积累。

### 原则 5：LLM 不直接写治理对象

`forbidden.yaml`、`implementation_policy.yaml`、`final logic status` 这类治理对象，
不能由 LLM 直接编辑。

正式升级只能通过程序化 `guarded writer`：

- 先读 judge output
- 再校验升级条件
- 最后决定是否真正写入治理对象

### 原则 5.1：`guarded_writer` 必须是程序对象，不是口头约定

`guarded_writer` 不是抽象概念，必须被定义成统一可调用接口。

推荐实现形态：

1. Python 模块
2. CLI 包装层

最小接口约定：

```yaml
guarded_write_request:
  request_id: GW_20260405_001
  actor: research_judge
  write_level: level_1 | level_2
  target_object: factor_registry | logic_card | research_state | forbidden | implementation_policy
  action: append | update | propose_upgrade | reassess | retire
  payload_ref: storage/results/batch_XXX_judge_report.yaml
  target_ref: storage/registry/factors/factor_XXX.yaml
  evidence_refs:
    - storage/results/batch_XXX_research_result.yaml
    - storage/ledger/search_ledger.yaml
```

输出必须标准化：

```yaml
guarded_write_receipt:
  request_id: GW_20260405_001
  status: accepted | rejected
  written_paths: []
  rejection_reason_codes: []
  followup_required: false
```

执行规则：

1. `research_judge` 只生成 request，不直接改治理对象
2. `guarded_writer` 校验权限、升级门槛、对象所有权
3. 若 `status = rejected`，skill 只能保留 report / ledger，不得绕过写入
4. 一级回写不要求走 full writer 校验，只要求追加 audit receipt
5. 二级升级必须显式经过 full writer，校验重复证据与 reassessment 条件

一级回写的 audit receipt 默认追加到：

- `storage/ledger/write_audit_log.yaml`

---

## 3. Memory 的 6 个核心对象层

### 3.1 Research State

全局运行状态。

回答：

- 当前 batch 是什么
- 当前 active logic 是什么
- 当前活跃研究主题是什么
- 当前主要 bottleneck 是什么
- 当前样本制度版本是什么

### 3.2 Logic Memory

研究命题层。

回答：

- 每个 logic 的 hypothesis 是什么
- 当前 lifecycle 是什么
- 哪些 family 已有效
- 哪些方向已接近饱和

### 3.3 Experiment Lineage

回答：

- 同一研究切片跨 batch 是否仍在继续
- 哪个切片持续 `continue / pause / kill`
- 哪个切片反复产出 admit / reserve

当前版本不单独维护 `storage/lineage/`。

`experiment_lineage_tag` 的正式存储固定为：

1. batch 内原始对象
   - `storage/candidates/batch_XXX.yaml`
   - `storage/candidates/batch_XXX_idea_report.yaml`
   - `storage/results/batch_XXX_judge_report.yaml`
2. 跨 batch 聚合视图
   - `storage/ledger/search_ledger.yaml` 的 `by_experiment_tag`

因此：

- batch artifact 保存原始 tag
- ledger 保存跨 batch 聚合结果
- `logic` 不应在每次 schedule 前重新扫描所有历史 judge report 手工聚合 ELT

### 3.4 Factor Memory

研究资产层。

回答：

- 当前 admitted factor 有哪些
- 各自来自哪个 logic / batch-local route label
- 在什么研究评估制度下被 admit

### 3.5 Policy Memory

制度层。

回答：

- capability 边界
- implementation 规则
- failure taxonomy
- forbid 升级候选

### 3.6 Search Ledger And Packets

搜索审计层。

回答：

- 某个 logic / family 累计试了多少次
- 当轮试了多少 candidate
- 历史 admit 率如何
- 当前这次成功是否可能只是数据挖掘偶然
- `judge` 需要读取的压缩上下文是什么

---

## 4. 推荐目录结构

```text
storage/
  state/
    research_state.yaml
    pending_holdout_queue.yaml

  logic/
    registry.yaml
    cards/
      L001.yaml
      L002.yaml
    snapshots/
      latest_schedule_snapshot.yaml
      schedule_YYYYMMDD_HHMMSS.yaml

  registry/
    factors/
      index.yaml
      factor_001.yaml
      factor_002.yaml
    families/
      family_registry.yaml
      family_requests.yaml

  policy/
    capability_registry.yaml
    implementation_policy.yaml
    failure_taxonomy.yaml
    policy_upgrade_ledger.yaml

  ledger/
    search_ledger.yaml
    batch_usage.yaml
    holdout_review_ledger.yaml
    write_audit_log.yaml

  packets/
    batch_XXX_judge_packet.yaml
    batch_XXX_context_snapshot.yaml

  memory/
    forbidden.yaml

  results/
    batch_XXX_research_result.yaml
    batch_XXX_execute_report.yaml
    batch_XXX_judge_report.yaml

  notes/
    mining-lessons.md
    postmortems/
      2026-04-route-overlap.md
```

---

## 5. 每个对象怎么定义

## A. `state/research_state.yaml`

这是统一入口状态。

```yaml
research_state:
  current_batch: batch_042

  sample_policy:
    version: research_sample_v3
    data_start: "2015-01-01"
    active_train_range: ["2015-01-01", "2021-12-31"]
    active_validation_range: ["2022-01-01", "2023-12-31"]
    support_validation_windows:
      - {window_id: val_2020_2021, range: ["2020-01-01", "2021-12-31"]}
      - {window_id: val_2021_2022, range: ["2021-01-01", "2022-12-31"]}
      - {window_id: val_2022_2023, range: ["2022-01-01", "2023-12-31"]}
    holdout_pool_range: ["2024-01-01", "2025-12-31"]

  active_logic_ids:
    - L021
    - L008

  active_experiment_groups:
    - "L021/compression_breakout/core"
    - "L021/compression_breakout/decorrelate"
    - "L008/regime_switch/repair"

  current_focus:
    - "compression breakout 独立性验证"
    - "regime repair helper化评估"

  current_bottlenecks:
    - overlap_too_high
    - validation_instability
    - helper_missing_for_regime_designs

  current_validation_window_id: val_2022_2023

  policy_flags:
    prefer_dsl: true
    python_only_helper_based: true
    vectorization_required: true
    use_barra_view: true

  last_updated_at: "2026-04-04T12:00:00"
```

谁写：

- `logic`
- `research_cycle_controller`
- `guarded_writer`

字段级所有权应固定如下：

- `logic`
  - `active_logic_ids`
  - `active_experiment_groups`
  - `current_focus`
  - `current_bottlenecks`
- `research_cycle_controller`
  - `current_batch`
  - `current_validation_window_id`
  - batch 启停相关状态
- `guarded_writer`
  - admission / replace 后需要同步到 state 的最终快照字段
  - 但不负责日常调度字段

硬规则：

- 不允许三个 writer 任意重写整个 `research_state.yaml`
- 必须按字段所有权做局部更新
- 若出现字段所有权冲突，以对象 owner 为准

谁读：

- 所有 research skills

## A.1 `state/pending_holdout_queue.yaml`

`pending_holdout_queue` 必须是独立对象，不能继续内嵌在 `research_state.yaml`。

原因：

- `research_state.yaml` 会被多个模块读取/更新
- queue 明细状态只允许 `holdout_queue_manager` 维护
- 若把 queue 放回单一 state 文件，会制造字段级写权限冲突

```yaml
pending_holdout_queue:
  - candidate_id: C042_03
    logic_id: L021
    family_id: FM_breakout
    experiment_lineage_tag: ELT_L021_breakout_compression_gate_v1
    requested_at_batch: batch_042
    deadline_batch: batch_043
    status: pending
    priority: high
    superseded_by_candidate_id: null
```

谁写：

- `research_cycle_controller`

谁读：

- `logic`
- `research_judge`
- `research_execute`

---

## B. Logic Memory

分成：

- `logic/registry.yaml`
- `logic/cards/LXXX.yaml`

### `logic/registry.yaml`

只做索引。

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

stats:
  probe_attempts: 5
  execute_attempts: 3
  admits: 1
  reserves: 1
  rejects: 1

search_ledger_ref:
  logic_attempt_count_to_date: 64
  logic_admit_count_to_date: 5
```

谁写：

- `logic`
- `guarded_writer`

谁读：

- `logic`
- `idea`
- `research_judge`

---

## C. Batch Design Snapshot

当前版本不再默认维护长期 `route cards`。

route 只作为 batch 内的设计标签存在，保留在：

- `storage/candidates/batch_XXX.yaml`
- `storage/candidates/batch_XXX_idea_report.yaml`
- `storage/packets/batch_XXX_context_snapshot.yaml`

这层只回答：

- 本轮有哪些 experiment group
- 每组 candidate 共享什么研究问题
- 哪组在本轮被 judge 标记为 continue / pause / kill / promote_family

示例：

```yaml
batch_design_groups:
  - group_id: G042_01
    logic_id: L021
    route_label: genesis
    experiment_lineage_tag: ELT_L021_breakout_compression_gate_v1
    family_id: PF_breakout_volume_gate
    research_question: "量能压缩条件是否提升 breakout 的独立性"
    candidate_ids: [C042_01, C042_02, C042_03]
    judge_feedback:
      route_verdict: continue
      primary_failure_mode: high_family_overlap
      suggested_next_action: decorrelate
```

谁写：

- `idea`
- `research_judge`

谁读：

- `idea`
- `research_judge`
- `research_cycle_controller`

---

## D. Factor Memory

分成：

- `registry/factors/index.yaml`
- `registry/factors/factor_XXX.yaml`

### `index.yaml`

```yaml
factors:
  - factor_id: F013
    name: compression_rank_breakout_10
    logic_id: L021
    route_id: R021_01
    experiment_lineage_tag: ELT_L021_breakout_compression_gate_v1
    category: volume_price
```

### `factor_XXX.yaml`

```yaml
factor_id: F013
name: compression_rank_breakout_10
category: volume_price
source_type: dsl

logic_id: L021
route_id: R021_01
route_type: genesis
experiment_lineage_tag: ELT_L021_breakout_compression_gate_v1
family_id: FM_breakout

admitted_at: "2026-04-04"
decision: admit

evaluation_context:
  sample_policy_version: research_sample_v3
  eval_profile: research_eval_v1
  holdout_used: false

metrics_snapshot:
  ic_mean_validation: 0.010
  ic_ir_validation: 0.13
  monotonicity_validation: 0.39
  turnover: 0.34
  coverage: 0.86

strict_stats_snapshot:
  expanding_window_pass: true
  bootstrap_stability_score: 0.67
  purged_walk_forward_status: low_power
  multiple_testing_risk_bucket: medium
  search_adjusted_strength_bucket: medium

risk_review_snapshot:
  barra_residual_ic: 0.005
  alpha_survival_ratio: 0.50
  dominant_style_exposure: size

similarity_snapshot:
  nearest_factor_id: F011
  max_lib_corr: 0.64
  family_overlap_score: 0.72
  subspace_redundancy_score: 0.61
  residual_incremental_ic: 0.003
  family_redundancy_view:
    family_id: FM_breakout
    structure_template: gated
    conditioning_type: volume
    horizon_bucket: short
    same_family_corr_p90: 0.81
    structure_overlap_score: 0.67
    residual_survival_ratio: 0.24
    overlap_bucket: high
  subspace_redundancy_view:
    basis_method: local_ridge
    basis_factor_ids: [F011, F013, F018]
    subspace_redundancy_score: 0.61
    residual_incremental_ic: 0.003
    confidence: medium

feasibility_snapshot:
  holding_period_proxy: medium
  liquidity_coverage_ratio: 0.79
  tail_trade_concentration: 0.18
  rebalance_stress_proxy: medium
```

谁写：

- `guarded_writer`

谁读：

- `logic`
- `idea`
- `research_execute`
- `research_judge`

---

## E. Policy Memory

至少包括：

- `policy/capability_registry.yaml`
- `policy/implementation_policy.yaml`
- `policy/failure_taxonomy.yaml`
- `policy/policy_upgrade_ledger.yaml`

### `implementation_policy.yaml`

存实现规则，不存单轮 batch 的临时意见。

### `failure_taxonomy.yaml`

存统一失败分类，例如：

```yaml
failure_types:
  - weak_validation_effect
  - high_pairwise_overlap
  - high_family_overlap
  - implementation_blocked
  - performance_rejected
  - helper_required
  - validation_instability
  - size_drift
  - style_repackaging
```

### `policy_upgrade_ledger.yaml`

这份对象很重要。
它记录“哪些规则升级建议正在积累证据”，但不等于已经升级为正式 policy。

```yaml
policy_upgrade_candidates:
  - upgrade_id: PU001
    target: forbidden_candidate_pattern
    summary: pure_price_breakout_no_volume_context
    observed_batches: 5
    observed_routes: 11
    repeated_reason_codes:
      - high_family_overlap
      - validation_instability
    status: accumulating
    recommended_action: consider_forbidden_upgrade
```

谁写：

- `research_judge`

谁读：

- `logic`
- `idea`
- `research_judge`

---

## F. Forbidden Memory

`memory/forbidden.yaml`

只存已经被升级为正式规则的禁做模式。
不要把单轮失败直接写进这里。

```yaml
forbidden_patterns:
  - pattern_id: FP001
    type: expression_template
    summary: plain_breakout_with_no_volume_context
    reason: repeated_low_increment_across_batches
    failure_mode: weak_validation_effect
    status: active

  - pattern_id: FP002
    type: implementation
    summary: groupby_apply_custom_python
    reason: repeated_performance_rejected
    failure_mode: performance_rejected
    status: active
```

升级进 `forbidden.yaml` 的前提至少应包括：

1. 跨 batch 重复出现
2. 原因代码稳定
3. 不是单一 route 偶发失败

`forbidden` 不是单向棘轮，必须允许 reassessment。

允许三种状态：

1. `active`
2. `under_review`
3. `retired`

触发 `forbidden_reassessment_request` 的条件至少包括：

1. 新 regime 下连续 `2` 个 batch 出现相反证据
2. 明显发现历史定义过宽，误杀有效候选
3. 发现当初升级依据存在错误或越权写入

reassessment 不直接删除规则。
它必须先进入：

- `policy_upgrade_ledger.yaml`

只有在 review 通过后，才允许把 `status` 从 `active` 改成：

- `under_review`
- 或 `retired`

推荐退役协议：

1. `under_review`
   - 已出现反证，但还不足以直接退休
2. `retired`
   - 最近 `2` 个以上相关 batch 不再支持该禁做规则
   - 或 rule 边界已被证实过宽
   - 或原升级过程存在错误

`retired` 不代表删除历史。
它只表示：

- 不再作为 active blocking policy 使用
- 历史原因与适用区间仍保留在 yaml 中供审计

谁写：

- `guarded_writer`

谁读：

- `logic`
- `idea`
- `research_execute`

---

## G. Search Ledger And Packets

这是当前必须补的一层。

分成：

- `ledger/search_ledger.yaml`
- `ledger/batch_usage.yaml`
- `ledger/holdout_review_ledger.yaml`
- `packets/batch_XXX_judge_packet.yaml`

### `search_ledger.yaml`

记录累计搜索强度。

```yaml
search_ledger:
  by_logic:
    L021:
      logic_attempt_count_to_date: 64
      admitted_count_to_date: 5
      reserve_count_to_date: 7
      validation_exposure_count_to_date: 12

  by_family:
    FM_breakout:
      family_attempt_count_to_date: 27
      admitted_count_to_date: 3
      reserve_count_to_date: 4

  by_experiment_tag:
    ELT_L021_breakout_compression_gate_v1:
      batches_seen: 3
      admitted_count_to_date: 1
      reserve_count_to_date: 1
      continue_count_to_date: 2
      pause_count_to_date: 0
      kill_count_to_date: 0
      latest_verdict: continue

```

`by_experiment_tag` 就是 Experiment Lineage 的正式聚合视图。

它必须承担：

1. 给 `logic` 提供跨 batch 的 ELT verdict 分布
2. 给 `research_judge` 提供 `continue / pause / kill / promote_family` 的累计背景
3. 避免每轮重新扫描全部历史 batch artifact

### `batch_usage.yaml`

记录每轮到底用了哪些样本和对象。

```yaml
batches:
  - batch_id: batch_042
    sample_policy_version: research_sample_v3
    train_range: ["2015-01-01", "2021-12-31"]
    validation_range: ["2022-01-01", "2023-12-31"]
    validation_window_id: val_2022_2023
    validation_exposure_count_before_run: 11
    validation_exposure_count_after_run: 12
    holdout_used: false
    logic_ids: [L021, L008]
    experiment_group_ids: [G042_01, G042_02, G042_03]
    candidate_count: 7
```

### `holdout_review_ledger.yaml`

记录低频 holdout review 的使用历史。

```yaml
holdout_reviews:
  - review_id: HR001
    batch_id: batch_042
    target_type: candidate
    target_id: C042_03
    trigger_reason: high_data_mining_risk
    status: completed
    outcome: confirmed

  - review_id: HR002
    batch_id: batch_043
    target_type: candidate
    target_id: C043_02
    trigger_reason: reserve_for_replace_review
    status: superseded
    outcome: null
```

这层的意义是：

- 让 `research_judge` 看见多重检验背景
- 防止把单个 candidate 当成独立试验
- 让后续能审计 validation 被使用了多少次
- 让 holdout 不会被偷偷变成日常调参集
- 让 LLM 不必每轮直接读取十几个原始对象，而是优先读取压缩后的 `judge_packet`

谁写：

- `idea`
- `research_execute`
- `research_judge`
- `research_cycle_controller`

谁读：

- `research_judge`
- `logic`

### `packets/batch_XXX_judge_packet.yaml`

这是给 `research_judge` 的压缩上下文快照。

它不是新的权威对象，只是把本轮裁决真正需要的信息聚合成单一输入。

最小 schema 必须固定如下：

```yaml
judge_packet:
  batch_id: batch_042
  sample_policy_version: research_sample_v3
  evaluation_profile_id: research_eval_v1
  active_logic_ids: [L021, L008]
  candidate_briefs:
    - candidate_id: C042_01
      logic_id: L021
      route_id: R021_01
      route_type: genesis
      family_id: PF_breakout_volume_gate
      experiment_lineage_tag: ELT_L021_breakout_compression_gate_v1
      execution_gate_status: pass
      validation_effect_bucket: borderline
      stability_bucket: medium
      redundancy_bucket: high
      feasibility_bucket: acceptable
      support_window_warning: none
      holdout_review_recommended: false
  factor_registry_snapshot_ref: registry/factors/index.yaml
  policy_snapshot_ref:
    implementation_policy: policy/implementation_policy.yaml
    forbidden: memory/forbidden.yaml
  search_context:
    validation_window_id: val_2022_2023
    validation_exposure_count_before_run: 11
    validation_exposure_count_after_run: 12
    by_logic:
      L021:
        logic_attempt_count_to_date: 64
    by_family:
      FM_breakout:
        family_attempt_count_to_date: 27
    by_experiment_tag:
      ELT_L021_breakout_compression_gate_v1:
        batches_seen: 3
        latest_verdict: continue
  support_window_review:
    support_window_warning: none
```

省略规则：

1. 不放完整 timeseries
2. 不放可重算的原始 signal
3. 不放 report 展示专用字段
4. 只保留 judge 真正裁决所需的压缩证据和引用

---

## 6. 哪些东西应该放在 md

md 只承担叙事层：

- `mining-lessons.md`
- `batch summary`
- `factor reports`
- `postmortems`

一条硬规则：

> 会被 `logic / idea / research_execute / research_judge` 直接用于决策的内容，不能只存在于 md。

---

## 7. 读写边界

## `logic`

读：

- `state/research_state.yaml`
- `state/pending_holdout_queue.yaml`
- `logic cards`
- `registry/factors/*`
- `policy/implementation_policy.yaml`
- `memory/forbidden.yaml`
- `policy/failure_taxonomy.yaml`
- `ledger/search_ledger.yaml`
- `ledger/holdout_review_ledger.yaml`

写：

- `logic cards`
- `logic registry`
- `state/research_state.yaml`

备注：

`logic` 可以更新 lifecycle 与 focus，
但不直接维护 `pending_holdout_queue`。

## `research_cycle_controller`

读：

- `state/research_state.yaml`
- `state/pending_holdout_queue.yaml`
- `storage/results/batch_XXX_judge_report.yaml`
- `ledger/holdout_review_ledger.yaml`
- `ledger/search_ledger.yaml`

写：

- `state/pending_holdout_queue.yaml`
- `ledger/holdout_review_ledger.yaml`

备注：

只有 controller 可以修改：

- `pending_holdout_queue`
- holdout review 的调度状态
- batch 级启动/暂停状态

`research_cycle_controller` 是一个协调标签，不要求必须是单个 skill。
它可以由两个程序对象组成：

1. `batch_scheduler`
2. `holdout_queue_manager`

但对上层文档来说，二者合称同一个 controller 边界。

## `idea`

读：

- `state/research_state.yaml`
- `state/pending_holdout_queue.yaml`
- `logic cards`
- `registry/factors/*`
- `policy/capability_registry.yaml`
- `policy/implementation_policy.yaml`
- `memory/forbidden.yaml`
- `ledger/search_ledger.yaml`
- `ledger/holdout_review_ledger.yaml`

写：

- `storage/candidates/batch_XXX.yaml`
- `storage/candidates/batch_XXX_idea_report.yaml`
- `storage/packets/batch_XXX_context_snapshot.yaml`
- `ledger/batch_usage.yaml`

## `research_execute`

读：

- `storage/candidates/batch_XXX.yaml`
- `policy/capability_registry.yaml`
- `policy/implementation_policy.yaml`
- `registry/factors/*`
- `state/research_state.yaml`
- `state/pending_holdout_queue.yaml`

写：

- `storage/results/batch_XXX_research_result.yaml`
- `storage/results/batch_XXX_execute_report.yaml`
- `ledger/batch_usage.yaml`

备注：

`research_execute` 不主写长期对象 memory。
它允许追加写：

- 研究证据结果
- 使用审计 ledger

但不直接维护：

- factor registry
- logic cards
- policy objects

## `discovery`

读：

- `storage/results/batch_XXX_research_result.yaml`
- `storage/results/batch_XXX_execute_report.yaml`
- `storage/results/batch_XXX_judge_report.yaml`
- `ledger/search_ledger.yaml`
- `registry/factors/*`

写：

- `ledger/search_ledger.yaml`
- `storage/logic/proposals/proposal_XXX.yaml`

备注：

`discovery` 默认不维护独立 `pattern_buffer.yaml / discovery_ledger.yaml`。
重复异常只作为 `search_ledger` 中的 `discovery_candidates` section 存在。

## `research_judge`

读：

- `storage/packets/batch_XXX_judge_packet.yaml`
- `storage/results/batch_XXX_research_result.yaml`
- `storage/results/batch_XXX_execute_report.yaml`
- `storage/candidates/batch_XXX.yaml`
- `logic cards`
- `registry/factors/*`
- `policy/implementation_policy.yaml`
- `policy/failure_taxonomy.yaml`
- `policy/policy_upgrade_ledger.yaml`
- `memory/forbidden.yaml`
- `ledger/search_ledger.yaml`
- `ledger/batch_usage.yaml`
- `ledger/holdout_review_ledger.yaml`
- `state/pending_holdout_queue.yaml`

写：

- `policy/policy_upgrade_ledger.yaml`
- `storage/results/batch_XXX_judge_report.yaml`
- `ledger/search_ledger.yaml`
- `ledger/batch_usage.yaml`
- `ledger/holdout_review_ledger.yaml`

备注：

`research_judge` 是 memory 的主证据写入者，但不是治理对象的直接升级者。

`forbidden.yaml`、`implementation_policy.yaml`、`final logic status`
应由程序化 `guarded writer` 根据 judge output 再决定是否真正写入。

`research_judge` 只能发出 holdout request，
不能直接修改 queue 本身。

它也不应直接写：

- `registry/factors/*`
- `logic cards`
- `state/research_state.yaml`

这些都应通过：

- `guarded_writer`
- 或 `research_cycle_controller`

完成。

## `guarded_writer`

读：

- `storage/results/batch_XXX_judge_report.yaml`
- `storage/results/batch_XXX_research_result.yaml`
- `policy/policy_upgrade_ledger.yaml`
- `memory/forbidden.yaml`
- `logic cards`
- `registry/factors/*`
- `state/research_state.yaml`
- `ledger/search_ledger.yaml`

写：

- `registry/factors/*`
- `logic cards`
- `state/research_state.yaml`
- `memory/forbidden.yaml`
- `policy/implementation_policy.yaml`

备注：

`guarded_writer` 是唯一允许把 judge recommendation 兑现为正式治理对象变更的程序边界。

---

## 8. 回写分级制度

### 一级回写：允许直接写

单轮 validation 结果可以直接写：

- candidate verdict
- route verdict
- logic 热度更新
- admit / reserve / reject 历史
- batch judge report
- judge packet / context snapshot

### 二级回写：只能写入升级候选，不直接升级

单轮 validation 结果不能直接把以下内容升级成正式制度：

- `forbidden.yaml` 核心规则
- `implementation_policy.yaml` 全局规则
- hypothesis doctrine
- family taxonomy
- final logic lifecycle status

它们只能先进入：

- `policy_upgrade_ledger.yaml`

当满足重复证据条件时，才考虑升级为正式 policy 或 forbidden。

---

## 9. 最终原则

这套 memory 设计的重点不是“把信息都存下来”，而是：

1. 让研究状态可追踪
2. 让 `judge` 的回写受到约束
3. 让多重检验背景可见
4. 让 validation 结果不再无约束地制度化
5. 让 contract 外的重复异常有受控上行通道

如果这五点做不到，研究系统即使流程再完整，也会慢慢把噪声写进自己的长期记忆。
