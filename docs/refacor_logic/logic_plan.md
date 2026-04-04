---
name: factor-logic
description: 管理研究命题 hypothesis：提案、审查、立项、调度、生命周期管理
user_invocable: true
---

# Logic Management

## 1. 目标

`logic` 是研究系统的 hypothesis 管理层。

它不直接生成因子，也不做正式统计裁决。
它负责的是：

1. 管理哪些市场机制值得研究
2. 判断哪些新想法应该升格为正式 logic
3. 给 `idea` 提供高层研究边界和预算意图
4. 根据累计研究证据更新 logic 生命周期
5. 接收轻量 discovery escalation 上报的新 direction / logic proposal

它不负责：

- 生成 candidate
- 运行正式评估
- admit / reject / replace factor
- 直接升级全局 forbidden / implementation policy
- 维护细粒度 route 持久化对象
- 担任 family taxonomy 的唯一管理员
- 担任 research cycle controller 的执行器

这些属于 `idea`、`research_execute`、`research_judge`。

## 1.1 双速回路与外部控制器

系统必须明确区分两条回路：

1. 会话内快速研究回路
2. 正式 admission 回路

`logic` 只服务第二条正式回路。

批次频率与下一轮触发，归外部 `research_cycle_controller` 管。

它内部应拆成两个子职责：

1. `batch_scheduler`
2. `holdout_queue_manager`

`batch_scheduler` 负责：

1. 在 `judge` 完成后决定是否开启下一轮正式 batch
2. 触发下一次 `logic schedule`
3. 控制 batch 频率

`holdout_queue_manager` 负责：

1. 维护 `pending_holdout_queue`
2. 决定何时运行 holdout review
3. 判断超时和 supersede

这里必须强制分开两类职责：

1. 调度决策
2. queue 状态管理

也就是说，`research_cycle_controller` 可以是总称，
但实现上至少应拆成两个程序对象：

1. `batch_scheduler`
2. `holdout_queue_manager`

它们可以由同一个入口统一触发，
但不应由同一段自由叙事逻辑同时修改“下一轮是否启动”和“queue 明细状态”。

最小输入：

- `storage/state/research_state.yaml`
- `storage/state/pending_holdout_queue.yaml`
- `storage/results/batch_XXX_judge_report.yaml`
- `storage/ledger/holdout_review_ledger.yaml`
- `storage/ledger/search_ledger.yaml`

最小输出：

- 下一轮是否启动
- 下一轮 batch 的 `logic_ids`
- 是否先执行 holdout review
- `state/pending_holdout_queue.yaml` 的状态更新

默认规则：

- `judge` 和 memory update 完成后，由 controller 触发下一轮 `logic schedule`
- 若本轮 `admitted_count = 0` 且 `all_routes_killed = true`，默认进入人工确认
- 若只是无 admit 但仍有高质量 reserve / active route，则允许自动进入下一轮
- 默认 batch 频率建议不高于每周 `1-2` 次

### 1.2 冷启动协议

在系统进入 `bootstrap_phase` 时，controller 和 logic 都必须降级运行。

最低保护期条件：

- `completed_batches < 5`
  或
- `admitted_factor_count < 10`

这只是最低保护期，不是全局硬切换开关。

更合理的做法是逐项解锁：

1. `family_overlap`：
   - `family_size >= 3` 时才进入正常解释
2. `subspace_redundancy`：
   - `basis_factor_count >= 2` 时才进入正常解释
3. `promote_family`：
   - 跨 `2` 个 batch 有连续证据时才生效
4. `policy / forbidden` 升级：
   - 只有 `policy_upgrade_ledger` 达标时才可升级
5. `productive / saturated / dead`：
   - 只有累计 admit / failure 达到各自门槛时才启用

在最低保护期内：

1. 不启用 `productive / saturated / dead` 这类强累计 lifecycle
2. `logic` 只允许在：
   - `active`
   - `warm`
   - `parked`
   之间切换
3. `promote_family` 只记录，不正式生效
4. `policy_upgrade_ledger` 只积累证据，不升级 forbidden
5. `multiple_testing` 相关判断必须更多依赖本轮规模，而不是历史累计值

### 1.3 Holdout queue 规则

`holdout_review_required = true` 的 candidate 不允许无限期悬挂。

controller 必须维护一个 `pending_holdout_queue`，至少包含：

- `candidate_id`
- `logic_id`
- `requested_at_batch`
- `deadline_batch`
- `priority`
- `superseded_by_candidate_id`
- `status`

默认规则：

1. 进入 queue 后，必须在接下来 `1` 个正式 batch 内，或 `7` 天内触发 holdout review
2. 若同一 `logic_id + family_id` 下出现更强的新 candidate，可将旧 candidate 记为：
   - `superseded`
3. 被 supersede 的 candidate 不再保留 holdout review 优先权
4. 超过 deadline 仍未 review，则自动记为：
   - `expired_holdout_pending`
   - candidate 维持 `reserve`
5. `expired_holdout_pending` 不允许无限复活，除非新的 batch 再次触发同类升级请求

这意味着：

- holdout review 由 controller 触发
- 不依赖人工临时想起
- 也不允许无限期把 reserve 因子挂在那里

写入边界：

- `pending_holdout_queue` 只允许由 `holdout_queue_manager` 写
- `logic` 和 `research_judge` 只能提出 request，不直接改 queue 状态
- `batch_scheduler` 只能决定是否启动下一轮，不直接改 queue 明细

正式存储位置固定为：

- `storage/state/pending_holdout_queue.yaml`

---

## 2. 核心原则

### 原则 1：logic 是 hypothesis，不是方向碎片

不是所有新想法都应该创建为 logic。

很多东西只是：

- direction
- family mutation
- route
- candidate variation

logic 只保留真正值得长期跟踪的机制命题。

### 原则 2：logic 只给高层边界，不做微观编排

每个 logic 都必须输出明确 contract，至少约束：

- 当前研究问题
- 预算
- 可用 family
- 推荐字段与算子
- 避免的模式

但它不应该直接编排：

- 每条 route 的生命周期
- 每个 candidate 的细粒度试错步骤
- 每一轮的技术性 rerun

### 原则 3：logic 必须有生命周期

每个 logic 必须处于以下状态之一：

- `proposed`
- `active`
- `warm`
- `productive`
- `saturated`
- `parked`
- `dead`

### 原则 4：logic 必须由累计证据更新，而不是单轮印象更新

logic 的更新依据必须来自：

- `experiment_lineage_tag` 累计结果
- candidate admit / reserve / reject 分布
- family 的重复成功或重复失败
- `search_ledger`
- `policy_upgrade_ledger`

而不是单轮 batch 的偶然表现。

### 原则 4.1：logic 是 lifecycle 最终裁决者

`research_judge` 可以给出 `logic recommendation`，
但最终 `logic.status` 的写回权只属于 `logic`。

### 原则 4.2：family 只做渐进治理，不做硬前置门槛

`logic` 可以声明：

- `preferred_families`
- `disliked_families`
- `adjacent_families`

但不能要求：

- 每个新 candidate 在进入 execute 前都拥有完全正确的正式 `family_id`

当前阶段 family 应采用：

- `registered family`
- `provisional family`
- `FM_unknown`

的渐进式治理。

### 原则 5：必须保留少量 discovery 预算

如果 logic 只做 exploitation，系统会越来越强路径依赖。

因此每轮 schedule 必须保留一小部分预算给：

- `adjacent discovery`

也就是：

- 仍围绕当前 logic
- 但允许探索相邻 family、相邻 proxy、相邻机制切片

如果某个 logic 已处于：

- `productive`
- `saturated`

且 `direction_quota >= 2`，则默认至少保留：

- `1` 条 adjacent discovery route quota

---

## 3. 核心对象

## 3.0 Family Labels

系统必须维护：

```text
storage/registry/families/family_registry.yaml
```

它至少包含：

```yaml
families:
  - family_id: FM_breakout
    mechanism_class: breakout
    family_thesis: "directional continuation after breakout confirmation"
    parent_family_id: null
    child_family_ids: []
    allowed_structure_templates: [plain, gated, residualized]
    allowed_conditioning_types: [none, volume, vol]
    allowed_horizon_buckets: [short, mid]
    status: active
    aliases: []
    merged_into: null
```

其中：

- `family_id` 是机制级主键
- `parent_family_id / child_family_ids` 表达层级
- `merged_into` 用于合并后的历史纠偏

但当前规模下，family registry 不是 admission 的硬前提。

允许三类状态：

1. `registered`
2. `provisional`
3. `unknown`

新 family 可以先以 `PF_*` 形式进入 provisional 状态。
execute 和 judge 不能因为 family 仍是 provisional，就阻断正式统计评估；
它们只需要在 redundancy 解释上更保守。

## 3.1 Logic Proposal

新 hypothesis 先进入 proposal，而不是直接入库。

```yaml
proposal_id: P021
schema_version: v3

name: compression_breakout
origin_type: canonical
category: volume_price

thesis: >
  当成交量持续收缩且价格波动压缩后，后续成交放大更可能伴随方向性价格发现。

mechanism: >
  压缩期通常对应分歧收敛与仓位静止，后续放量意味着信息进入、
  仓位重建或突破确认，因此价格更易延续。

observable_proxy:
  required_fields: [volume, close, high, low]
  optional_fields: [amount]

expected_horizon:
  formation_window: [5, 60]
  holding_window: [5, 20]

implementation_space:
  preferred_families: [breakout, compression_spread, gated_trend]
  suggested_ops: [Mean, Std, Rank, TsDecay]
  discouraged_ops: [deep_nested_interaction]

novelty_claim: >
  区别于纯价格突破逻辑，这里强调量能压缩与释放的条件触发。

relations_guess:
  overlaps_with: [L011]
  likely_adjacent_families: [breakout, compression_spread]
```

## 3.2 Logic Review

proposal 审查至少包括四类：

1. `mechanism_review`
2. `feasibility_review`
3. `novelty_review`
4. `research_value_review`

```yaml
proposal_id: P021

mechanism_review:
  verdict: pass
  reason_codes: [mechanism_clear]

feasibility_review:
  verdict: pass
  reason_codes: [fields_available, implementation_feasible]

novelty_review:
  verdict: borderline
  reason_codes: [partial_overlap_with_existing_logic]

research_value_review:
  verdict: pass
  reason_codes: [high_research_value, not_yet_saturated]
```

## 3.3 Logic Card

正式入库后的 logic 必须有 card。

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

contract:
  current_focus_question: "压缩条件是否提升 breakout 的独立性"
  direction_quota: 2
  candidate_quota: 4
  preferred_families: [breakout, compression_spread]
  suggested_ops: [Mean, Std, Rank, TsDecay]
  required_fields: [volume, close, high, low]
  avoid_patterns:
    - pure_price_only_breakout

discovery_budget:
  adjacent_discovery_route_quota: 1
  enabled: true
  min_discovery_ratio: 0.25

evidence_summary:
  productive_families: [breakout]
  failed_families: [plain_rank_only]
  current_bottleneck: overlap_too_high

search_ledger_ref:
  logic_attempt_count_to_date: 64
  logic_admit_count_to_date: 5
  logic_reserve_count_to_date: 7
```

---

## 4. 新 logic 从哪里来

只允许以下来源：

- `canonical`
- `empirical_library`
- `near_miss_generalization`
- `crossover_hypothesis`
- `external_inspiration`
- `bottom_up_anomaly`
- `repeated_residual_pattern`

### 4.1 允许来源不代表自动立项

来源合法，只说明“可以进入 proposal”。
是否创建 logic，仍要经过 review。

其中：

- `bottom_up_anomaly`
- `repeated_residual_pattern`

必须额外经过：

- 简短 `escalation_note`

且必须在 `search_ledger.discovery_candidates` 中有可追溯记录。

### 4.2 Proposal 不应泛滥

每轮 proposal 数建议控制在：

- `2 ~ 5`

proposal 的作用是让 hypothesis 进入审查流程，不是批量堆概念。

---

## 5. Proposal 审查

## 5.1 Mechanism Review

判断：

- 是否存在独立市场机制
- 是否只是旧叙事的重新包装

## 5.2 Feasibility Review

判断：

- 当前字段能否支撑
- 当前 DSL / helper 能否合理表达
- 是否会迫使系统走极端复杂实现

## 5.3 Novelty Review

判断：

- 是否与现有 logic 过度重叠
- 是否其实更适合作为已有 logic 的 direction / route

## 5.4 Research Value Review

判断：

- 是否值得占用研究预算
- 是否有足够 headroom
- 是否已落入 saturated 区域

---

## 6. Proposal 裁决

proposal 审查后，只允许以下四种结果：

- `create_logic`
- `downgrade_to_direction`
- `park`
- `reject`

### 6.1 create_logic

适用于：

- 机制清晰
- 可实现
- 与已有 logic 区分明确
- 值得长期跟踪

### 6.2 downgrade_to_direction

适用于：

- 有研究价值
- 但不足以成为独立 hypothesis
- 更适合作为已有 logic 内的相邻切片

### 6.3 park

适用于：

- 想法可能成立
- 但当前预算不值得投入
- 或当前平台条件不成熟

### 6.4 reject

适用于：

- 机制不清
- 价值不足
- 完全重复
- 实现空间明显不合理

---

## 7. Logic Schedule

`logic schedule` 是 `logic` 的核心输出。

它回答：

- 本轮开哪些 logic
- 每个 logic 拿多少预算
- discovery 预算留给谁
- 哪些 discovery pattern 值得升格审查

## 7.1 schedule 输入

调度前至少读取：

```text
storage/state/research_state.yaml
storage/logic/registry.yaml
storage/logic/cards/*.yaml
storage/registry/factors/index.yaml
storage/policy/implementation_policy.yaml
storage/policy/failure_taxonomy.yaml
storage/policy/policy_upgrade_ledger.yaml
storage/memory/forbidden.yaml
storage/ledger/search_ledger.yaml
storage/ledger/batch_usage.yaml
```

## 7.2 schedule 维度

调度至少看六类信息：

1. `priority`
2. `lifecycle status`
3. `recent productivity`
4. `search saturation`
5. `current bottleneck`
6. `adjacent discovery need`
7. `validation exposure pressure`

### 7.2.1 priority

- 当前 hypothesis 的战略优先级

### 7.2.2 lifecycle status

- 当前是 `active`、`warm`、`productive`、`saturated` 还是 `parked`

### 7.2.3 recent productivity

看最近几轮是否持续产出 admit / reserve。

### 7.2.4 search saturation

从 `search_ledger` 看：

- 历史累计尝试次数是否过高
- admit 率是否持续下降
- 是否已经进入“试很多、增量很低”的状态

### 7.2.5 current bottleneck

例如：

- `high_family_overlap`
- `validation_instability`
- `implementation_blocked`

### 7.2.6 adjacent discovery need

若一个 logic 已高度 exploitation 化，就应强制保留一小部分相邻 discovery 预算。

### 7.2.7 validation exposure pressure

还必须看：

- 当前 validation window 已被使用多少次
- 某个 logic 是否对同一 validation window 过度依赖

## 7.3 schedule 输出

至少输出：

- `active_pool`
- `warm_pool`
- `parked_pool`
- `blocked_pool`
- 每个 active logic 的 budget
- 每个 active logic 的 discovery budget
- global constraints
- validation window switch suggestion

示例：

```yaml
schedule_snapshot:
  active_pool:
    - logic_id: L021
      direction_quota: 2
      candidate_quota: 4
      adjacent_discovery_route_quota: 1
      validation_window_id: val_2022_2023

  warm_pool:
    - logic_id: L008

  parked_pool:
    - logic_id: L017

  blocked_pool:
    - logic_id: L004
      reason: repeated_validation_instability

  global_constraints:
    validation_window_switch_recommended: false
    validation_window_switch_candidate_ids:
      - val_2021_2022
      - val_2020_2021
```

---

## 8. Logic 生命周期

logic 的状态必须由累计证据驱动。

### 8.1 `active`

适用于：

- 当前应继续拿研究预算
- hypothesis 仍有明确 headroom

### 8.2 `warm`

适用于：

- 仍值得保留
- 但不应成为主研究方向

### 8.3 `productive`

适用于：

- 已稳定产生 admit
- 对应 family 已多次被验证有效

### 8.4 `saturated`

适用于：

- hypothesis 仍成立
- 但当前库已高度覆盖
- 新增 route 的边际价值明显下降

### 8.5 `parked`

适用于：

- 当前不值得投入预算
- 但尚未被彻底证伪

### 8.6 `dead`

适用于：

- 长期无有效产出
- 或反复只产生坏模式
- 或机制本身被累计证据否定

---

## 9. Lifecycle 更新规则

logic 的状态变动必须结合：

- `experiment_lineage_tag` verdict 分布
- candidate admit / reserve / reject 分布
- family productive / failed 记录
- `search_ledger`
- `policy_upgrade_ledger`
- route 级 `promote_family` 建议

### 9.1 升到 `productive`

建议条件：

1. 跨多个 batch 持续出现 admit
2. admit 不是同构重复
3. validation 证据稳定
4. family 级别出现重复有效

### 9.2 降到 `saturated`

建议条件：

1. 历史尝试已很多
2. admit 率显著下降
3. 新 route 多数只是 overlap 变体
4. discovery budget 也未发现新增 headroom

### 9.3 降到 `parked`

建议条件：

1. 当前数轮产出不足
2. 但机制未被彻底否定
3. 更像是时点不佳或实现空间暂时受限

### 9.4 判为 `dead`

建议条件：

1. 累计尝试很多但长期无稳定 admit
2. 重复失败模式高度一致
3. 主要产出集中在 bad pattern / style repackaging / unstable validation

### 9.5 从 `parked` 回到 `active`

适用于：

- 相邻 logic 或相邻 family 出现了新的正证据
- implementation 能力补齐后重新变得可研究

### 9.6 Route `promote_family` 的消费规则

`research_judge.route_verdict = promote_family` 的直接消费者是 `logic`。

处理顺序固定为：

1. `logic` 在新一轮 schedule 前读取最近 batch 的 route verdict
2. 若 verdict 为 `promote_family`，则检查：
   - 同 family 是否跨至少 `2` 个 batch 有 admit / 高质量 reserve
   - 是否不存在 `high_subspace_redundancy` 主警报
   - 当前 logic 是否仍认可该 family 属于核心 hypothesis
3. 若接受，则更新：
   - `logic card.evidence_summary.productive_families`
   - 必要时提高该 family 的 route quota
4. 若拒绝，则必须记录：
   - `promote_family_rejected_by_logic`
   - `promote_family_reject_reason_codes`

`promote_family` 不自动修改 `family_registry.yaml`。
它只改变当前 logic 对该 family 的研究优先级。

它的跨 batch 连续性不由 `route_id` 追踪，
而由：

- `experiment_lineage_tag`
- `family_id`

联合承担。

---

### 9.7 Lifecycle 仲裁协议

若以下两者冲突：

- `research_judge` 的 `logic recommendation`
- `logic` 基于全局上下文推导出的 lifecycle decision

则按以下规则处理：

1. `judge` recommendation 必须被记录
2. `logic` 必须显式写出是否接受 recommendation
3. 最终写回 `logic card.status` 的值，以 `logic` 为准
4. 若 override，必须写：
   - `override_reason_codes`
   - `evidence_refs`

## 10. 与 `search_ledger` 的联动

logic 层必须读取累计搜索强度，而不是只看当前轮结果。

至少关注：

- `logic_attempt_count_to_date`
- `family_attempt_count_to_date`
- `admitted_count_to_date`
- `reserve_count_to_date`
- `validation_exposure_count_to_date`

这层的意义是：

- 防止继续给“高搜索、低产出”的 logic 盲目拨预算
- 让 `saturated` 和 `dead` 有结构化依据
- 让 discovery 预算的投放更有针对性

---

## 11. 与 `policy_upgrade_ledger` 的联动

logic 层不直接升级 policy。

但它必须感知：

- 哪些 pattern 正在重复失败
- 哪些实现类型正在累积负证据
- 哪些 hypothesis 切片频繁触发升级候选

如果某个 logic 下大量 route 持续命中同类升级候选，那么 schedule 应该：

- 降低 exploitation 预算
- 提高 adjacent discovery 比例
- 或直接降级 lifecycle

---

## 12. 输出对象

### 12.1 Proposal

保存到：

```text
storage/logic/proposals/proposal_XXX.yaml
```

### 12.2 Review

保存到：

```text
storage/logic/reviews/review_XXX.yaml
```

### 12.3 Logic Card

保存到：

```text
storage/logic/cards/logic_LXXX.yaml
```

### 12.4 Schedule Snapshot

保存到：

```text
storage/logic/snapshots/schedule_YYYYMMDD_HHMMSS.yaml
```

---

## 13. 职责边界

`logic` 负责：

- proposal
- review
- admit / downgrade / park / reject
- schedule
- lifecycle

`logic` 不负责：

- 生成 candidate
- 运行正式评估
- 判定 factor admit / replace
- 直接根据单轮 validation 升级全局 policy

---

## 14. 最终原则

`logic` 的目标不是“想更多方向”，而是：

1. 让 hypothesis 来源合法
2. 让 hypothesis 池保持少而强
3. 让 `idea` 的搜索空间受到控制
4. 让累计研究证据真正回流到 hypothesis 层
5. 在 exploitation 和 adjacent discovery 之间保持平衡
