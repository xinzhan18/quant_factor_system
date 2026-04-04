# Research Judge

## 1. 目标

`research_judge` 是研究系统里的正式裁决层。

它只回答三类问题：

1. candidate 是否录取
2. 本 batch 内的实验切片是否值得继续
3. logic 是否继续获得研究预算

它不负责：

- 重新计算因子
- 修改 candidate 主逻辑
- 自由重写 hypothesis
- 直接把 validation 结果升级成全局 doctrine

---

## 2. 输入对象

`research_judge` 至少读取：

```text
storage/packets/batch_XXX_judge_packet.yaml
storage/results/batch_XXX_research_result.yaml
storage/results/batch_XXX_execute_report.yaml
storage/candidates/batch_XXX.yaml
storage/logic/cards/*.yaml
storage/registry/factors/index.yaml
storage/memory/forbidden.yaml
storage/policy/implementation_policy.yaml
storage/policy/failure_taxonomy.yaml
storage/policy/policy_upgrade_ledger.yaml
storage/state/research_state.yaml
storage/state/pending_holdout_queue.yaml
storage/ledger/search_ledger.yaml
storage/ledger/batch_usage.yaml
```

输入优先级：

1. 优先读取 `batch_XXX_judge_packet.yaml`
2. 仅在需要 drill-down 时再回看原始 result / execute report / candidate manifest

`judge_packet` 是主输入，不是附属输入。

---

## 3. 核心原则

### 原则 1：`judge` 基于 validation 证据裁决

日常 `judge` 的正式依据来自：

- `research_execute` 产出的 `train + validation` 证据

不是来自：

- 新的自由试验
- 人工临时加测
- `holdout` 高频查看

### 原则 2：`judge` 必须结构化，不允许只写叙事

每个 verdict 必须至少包含：

- verdict
- reason codes
- evidence summary

不能只有自然语言总结。

### 原则 3：`judge` 的回写必须分级

`judge` 可以直接回写局部研究状态。

但以下内容不能因为单轮 validation 结果就直接升级：

- 全局 forbidden 核心规则
- 全局 implementation policy
- 全局 hypothesis doctrine

这些必须基于跨批次、重复出现的证据。

### 原则 3.1：正式回写必须经过 guarded writer

`research_judge` 不应直接修改治理对象原文件。

正式 writeback 必须经过统一 `guarded writer`，至少校验：

- 当前 skill 是否有该对象写权限
- 是否命中二级升级条件
- 是否试图越权升级 `forbidden / implementation_policy / final logic status`

没有程序化 writer 的情况下，分级回写只能算文档约束，不能算执行制度。

最小调用约定：

```yaml
guarded_write_request:
  request_id: GW_20260405_001
  actor: research_judge
  write_level: level_1 | level_2
  target_object: factor_registry | logic_card | research_state | forbidden | implementation_policy
  action: append | update | propose_upgrade | reassess
  payload_ref: storage/results/batch_XXX_judge_report.yaml
  target_ref: storage/registry/factors/factor_XXX.yaml
  evidence_refs:
    - storage/results/batch_XXX_research_result.yaml
    - storage/ledger/search_ledger.yaml
```

输出只允许：

```yaml
guarded_write_receipt:
  request_id: GW_20260405_001
  status: accepted | rejected
  written_paths: []
  rejection_reason_codes: []
```

规则：

- 一级回写默认不走 full writer 校验，只要求追加 audit receipt
- 二级回写必须显式校验升级条件
- 若 writer 拒绝写入，skill 只能保留 judge report，不得绕过重写治理对象

最小错误处理：

1. 若 `guarded_write_receipt.status = rejected`
   - `research_judge` 只能保留：
     - `batch_XXX_judge_report.yaml`
     - `policy_upgrade_ledger` 提案
   - 不得自行补写目标对象
2. 若 rejection 原因是：
   - `insufficient_repeated_evidence`
   - `owner_mismatch`
   - `forbidden_reassessment_required`
   则必须把这些 reason codes 原样写回 judge report
3. writer 不负责重新裁决，它只负责：
   - 权限检查
   - 升级门槛检查
   - 对象所有权检查

也就是说：

- `level_1` 的价值主要是审计
- `level_2` 的价值才是治理保护

`level_1` 默认只要求追加：

- `storage/ledger/write_audit_log.yaml`

中的 receipt 记录。

### 原则 4：`judge` 不是万能决策器

`judge` 负责研究录取，不负责：

- 真实交易可行性定价
- 成本建模
- 容量测算

在当前研究系统里，交易相关只作为 feasibility evidence 的一部分。

### 原则 5：score 不能主导 admit / reject

任何 score、bucket、composite 指标都不能单独触发：

- `admit`
- `reject`
- `replace`

它们最多只允许用于：

- 同层 candidate 的辅助排序
- `reserve` 队列优先级
- report 展示与解释

真正主导裁决的，仍然是：

- hard gate
- 结构化证据分维度判断
- reason codes

### 原则 6：`judge` 只推荐 logic lifecycle，不直接提交最终状态

`research_judge` 可以对 logic 输出 lifecycle recommendation，
但不能直接写最终 `logic.status`。

最终 lifecycle authority 归：

- `logic`

原因：

- `judge` 更接近单批次局部证据
- `logic` 才掌握跨 batch、跨 route、跨预算的全局上下文

---

## 4. 裁决对象

`research_judge` 同时裁决三个层级：

1. candidate
2. batch-local route label
3. logic（recommendation only）

### 4.1 Candidate Verdict

每个 candidate 必须落在以下之一：

- `admit`
- `reserve`
- `reject`
- `replace`

### 4.2 Route Verdict

每个 route 必须落在以下之一：

- `continue`
- `pause`
- `kill`
- `promote_family`

### 4.3 Logic Recommendation

每个 logic recommendation 必须落在以下之一：

- `active`
- `warm`
- `productive`
- `saturated`
- `parked`
- `dead`

---

## 5. Candidate 裁决协议

### 5.1 证据维度

每个 candidate 的裁决必须显式查看六类证据：

1. `mechanism_alignment`
2. `statistical_strength`
3. `stability`
4. `redundancy`
5. `feasibility`
6. `risk_model_review`

### 5.1.1 `mechanism_alignment` 的操作定义

`mechanism_alignment` 不能只靠自由叙事。

它必须基于以下 4 个结构化检查：

1. `logic_thesis_match`
2. `route_question_match`
3. `sign_and_behavior_match`
4. `non_style_only_explanation`

定义：

- `logic_thesis_match`
  - candidate 是否仍在回答当前 logic thesis
- `route_question_match`
  - candidate 是否仍在回答本 batch experiment group 的研究问题
- `sign_and_behavior_match`
  - 信号方向、触发条件、主要行为是否与假设一致
- `non_style_only_explanation`
  - 结果不能主要由单一 style / beta 残留解释

输出只允许：

- `mechanism_aligned`
- `mechanism_unclear`
- `mechanism_drifted`

建议判定：

- `mechanism_aligned`
  - 四项中至少三项通过
  - 且 `non_style_only_explanation = pass`
- `mechanism_unclear`
  - 只有两项通过
  - 或存在明显解释歧义
- `mechanism_drifted`
  - thesis / route question 已对不上
  - 或主要只能被风格残留解释

### 5.1.2 冷启动阶段的裁决降级

若系统仍处于 `bootstrap_phase`，judge 必须显式降级解释力度。

默认规则：

1. `multiple_testing_risk_bucket` 只做弱风险提示
2. `family_overlap / subspace_redundancy` 若历史不足，只能记为：
   - `insufficient_family_history`
3. 不输出：
   - `promote_family`
   - `productive`
   - `saturated`
   这类强累计结论
4. `policy_upgrade_ledger` 只积累，不做正式 forbidden 升级建议

也就是说，前几轮系统可以 admit / reserve / reject，
但不应该假装自己已经拥有成熟的累计治理证据。

补充：

- `bootstrap_phase` 只是最低保护期
- 具体机制应按各自成熟条件逐项解锁
- judge 不应把某个全局阈值当成“所有累计机制同时生效”的开关

### 5.2 Admit

适用于：

- execution gate 未失败
- validation 证据达到当前 family 的最低录取标准
- `expanding_window_pass = true`
- `split_stability / regime_stability` 不差
- `bootstrap_stability_score` 若有输出则不能明显偏差
- 稳定性不过差
- 冗余可接受
- feasibility 不差
- 风格剥离后仍保留可接受 alpha
- `support_window_warning != repeated_sign_flip`

如果 `purged_walk_forward` 有输出，则它应支持 admit；
如果其状态是 `low_power`，不能单独构成 reject。

注意：

- `multiple_testing_risk_bucket`
- `search_adjusted_strength_bucket`

只能作为 admit 解释与 candidate 排序辅助，
不能替代上面的 hard gate 与分维度证据。

如果 `multiple_testing_risk_bucket = high`：

- 不构成自动 reject
- 也不构成自动 admit 阻断
- 默认只会把 candidate 推向：
  - `reserve`
  - 或 `reserve + holdout_review_required`

### 5.3 Reserve

适用于：

- 统计证据 borderline
- 或稳定性尚可但冗余偏高
- 或机制合理但本轮不足以直接 admit
- 或 `multiple_testing_risk_bucket = high`
- 或 `support_window_warning = repeated_sign_flip`
- 或需要 holdout review 才能升级

`reserve` 的作用是：

- 保留后续比较
- 不立即写入 admitted library
- 承接高数据挖掘风险或待 holdout 复核的候选

### 5.4 Reject

适用于：

- execution gate = fail_technical
- validation 上显著塌陷
- 与已有 family 明显重复且无新增价值
- feasibility 明显过差
- 属于已知坏模式
- 风格剥离后 alpha 基本消失

### 5.5 Replace

`replace` 不再采用 7 条全票通过制。

更合理的协议是：

#### A. 必须同时满足的硬条件

1. 与已有因子高度相近
2. 没有出现致命 regression
3. `residual_incremental_ic` 不能显著更差

其中“致命 regression”包括：

- validation sign flip
- 风格剥离后 alpha 明显消失
- technical invalidation

#### B. Replace 不再使用复杂加权总分

当前版本不再使用 `replace_advantage_score`。

原因：

- 权重没有可靠校准基础
- 子组件过多，不利于调试
- LLM 更容易在方向和归一化上算错

更朴素的协议是：

先做 5 个维度的离散比较，每个维度只允许：

- `better`
- `similar`
- `worse`

五个维度是：

1. `stability_compare`
2. `redundancy_compare`
3. `statistical_strength_compare`
4. `feasibility_compare`
5. `mechanism_cleanliness_compare`

定义如下：

```text
stability_compare:
- 若 split/regime 至少一项更好，且 decay_ratio 不更差 -> better
- 若没有明显改善，也没有明显退化 -> similar
- 若出现任一稳定性主项更差 -> worse

redundancy_compare:
- 若 family_overlap 更低，或 subspace_redundancy 更低，且 residual_incremental_ic 不更差 -> better
- 若冗余视图接近且 residual_incremental_ic 接近 -> similar
- 若更像已有库，或 residual_incremental_ic 更差 -> worse

statistical_strength_compare:
- 若 search_adjusted_strength / ic_ir / monotonicity 至少两项更好 -> better
- 若整体接近 -> similar
- 若主效果显著更弱 -> worse

feasibility_compare:
- 若 liquidity_coverage 更好，且 rebalance_stress / turnover 不更差 -> better
- 若整体可实现性接近 -> similar
- 若可实现性明显恶化 -> worse

mechanism_cleanliness_compare:
- 若 mechanism_alignment 更清楚，且 alpha_survival_ratio 更高 -> better
- 若解释力度接近 -> similar
- 若机制更脏或风格残留更重 -> worse
```

#### C. Replace 决策规则

在硬条件通过后：

1. 三个主维度  
   - `stability_compare`
   - `redundancy_compare`
   - `mechanism_cleanliness_compare`

2. 两个辅维度  
   - `statistical_strength_compare`
   - `feasibility_compare`

判定规则：

- `replace`：
  - 主维度中至少 `2` 项为 `better`
  - 剩余主维度不能为 `worse`
  - 辅维度不能出现 `materially worse`
- `reserve_for_replace_review`：
  - 主维度只有 `1` 项 `better`
  - 或主维度全 `similar`，但辅维度有明确改善
  - 或 feasibility 略差但其余维度明显更好
- `no_replace`：
  - 任一主维度为明确 `worse`
  - 或统计强度与稳定性均未显示改善

这里的目标不是做精细打分，而是回答一句更可调试的话：

> 新因子是否在“更稳、更不重复、机制更干净”这三个核心维度里，至少有两项真正比旧因子更好。

这里的 `materially worse` 必须有操作定义。

它不是第四个离散比较值。

正确理解是：

- 基础比较仍然只有 `better / similar / worse`
- `materially worse` 是对 `worse` 的加强标记
- 也就是：
  - `materially worse` = `worse` 且达到升级阈值

默认定义：

- `feasibility_compare = worse`
  且同时出现：
  - `rebalance_stress_proxy` 恶化一个完整 bucket
  - 或 `liquidity_coverage_ratio` 下降超过 `0.10`
  - 或 `turnover` 上升超过 `25%`
- `statistical_strength_compare = worse`
  且同时出现：
  - `ic_ir_validation` 明显下降
  - 且 `search_adjusted_strength_bucket` 下降一个完整 bucket

若只是：

- 轻微 turnover 变差
- 或单一指标边缘下降

则只记为普通 `worse`，不记为 `materially worse`。

### 5.6 Family Assignment Boundary

若 candidate 的 `family_id` 未通过 family registry 校验，
则 `research_judge` 不能把 family-level redundancy 作为正式裁决依据。

此时只能：

- `reserve`
- 或在伴随其他硬失败时 `reject`

并必须输出：

- `family_assignment_pending`
- 或 `family_assignment_invalid`

---

## 6. Route 裁决协议

这里的 `route` 是 batch-local experiment group，不是长期 route card。

跨 batch 的连续性不由 `route_id` 承担，而由：

- `experiment_lineage_tag`

承担。

它的裁决重点不在单个 candidate，而在：

- 该研究切片在下一轮是否仍值得继续投入预算

### 6.1 Continue

适用于：

- route 下至少出现了 1 个 admit 或高质量 reserve
- 机制切片仍有展开空间
- 当前失败主要是实现细节，不是 hypothesis 本身错误

### 6.2 Pause

适用于：

- 当前证据不够强
- 但没有明确被证伪
- 适合后续等相邻 route 结果一起比较

### 6.3 Kill

适用于：

- route 连续多轮无有效候选
- validation 上系统性塌陷
- 与已有库高度冗余
- feasibility 长期过差
- 命中重复 bad pattern

### 6.4 Promote Family

适用于：

- 同一 `experiment_lineage_tag`
  或同一 family 下相邻切片
  持续产生多个高质量 admit / reserve
- 已足够说明该 family 值得作为 logic 内主方向

`promote_family` 不是直接修改 family registry。

它的下游消费者固定是：

1. `logic` 在下一轮 schedule 前读取该 route verdict
2. 若接受，则更新 `logic card.evidence_summary.productive_families`
3. 若不接受，则记录：
   - `promote_family_rejected_by_logic`
   - `promote_family_reject_reason_codes`

默认接受门槛：

- 至少 `2` 个 batch 中出现同 family 的 admit / 高质量 reserve
- 且不伴随 `high_subspace_redundancy`
- 且 `family_attempt_count_to_date` 尚未显示明显 saturated

---

## 7. Logic 裁决协议

`logic` 的状态不是按单个 batch 决定，而是按累计证据决定。

### 7.1 Active

- 当前轮应继续拿预算

### 7.2 Warm

- 暂时不作为主方向，但仍值得保留观察

### 7.3 Productive

- 已稳定产生有效 admitted factor

### 7.4 Saturated

- 机制仍成立，但当前研究库已高度覆盖
- 继续投入的边际价值明显下降

### 7.5 Parked

- 当前不值得投预算，但未被彻底证伪

### 7.6 Dead

- 累计证据表明 hypothesis 缺乏稳定研究价值
- 或长期只产生坏模式

---

## 8. 回写分级制度

这是 `research_judge` 最关键的部分。

### 8.1 一级回写：允许直接写

基于单轮 validation，可以直接写：

- candidate verdict
- route verdict
- logic 热度更新
- batch 级 judge report
- admit / reject history

### 8.2 二级回写：需要重复证据

以下内容不能因为单轮 validation 就直接升级：

- `forbidden.yaml` 核心规则
- `implementation_policy.yaml` 全局规则
- logic 层 doctrine

这些至少需要：

1. 跨 batch 重复出现
2. 原因代码一致
3. 有明确累计计数

必要时再触发：

- `holdout_review_required: true`

### 8.3 建议增加 policy_upgrade_ledger

```yaml
policy_upgrade_ledger:
  pattern_id: pure_price_breakout_no_volume_context
  observed_batches: 5
  observed_routes: 11
  repeated_reason_codes:
    - high_overlap_low_increment
    - validation_instability
  holdout_review_required: false
  recommended_action: add_to_forbidden_candidate_patterns
```

### 8.4 重复证据的操作定义

“重复证据”默认定义为：

- 至少 `3` 个 batch
- 且至少 `2` 条 route
- 且 fatal/high reason code 的主类别一致

若只满足：

- `2` 个 batch
- 但覆盖 `3` 条以上 route

则只能进入：

- `policy_upgrade_candidate`

不能直接升级正式 policy。

### 8.5 Forbidden Reassessment

`forbidden` 不允许只增不减。

`research_judge` 可以提出：

- `forbidden_reassessment_request`

但不能直接把 rule 从 `active` 改成 `retired`。

推荐触发条件：

1. 最近 `2` 个以上相关 batch 出现反向证据
2. 当前 rule 明显过宽，误杀有效 candidate
3. 升级原始证据存在错误或越权

writer 处理结果只允许：

- `status: under_review`
- `status: retired`
- `reassessment_rejected`

不允许物理删除历史 rule。

---

## 9. 多重检验控制如何接入裁决

`judge` 必须读取 `search_context`，不能把单个 candidate 当成独立试验。

至少应考虑：

- 同 route 当轮试了多少个 candidate
- 同 family 历史累计试了多少次
- 同 logic 历史 admit 率如何
- 当前结果相对历史成功基线是否真实突出

建议输出：

```yaml
multiple_testing_view:
  family_attempt_count_to_date: 27
  logic_attempt_count_to_date: 64
  current_batch_candidate_rank_in_route: 1
  data_mining_risk: medium
  validation_exposure_count: 12
  multiple_testing_risk_score: 0.64
  multiple_testing_risk_bucket: medium
  search_adjusted_strength_score: 0.51
  search_adjusted_strength_bucket: medium
```

当前阶段至少必须落地 `multiple_testing_risk_bucket` 与 `search_adjusted_strength_bucket`，
但它们都只应被解释为研究风险代理，不能伪装成严格 FDR 或严格 deflated t-stat。
`admit` 和 `replace` 必须显式查看：

- `multiple_testing_risk_bucket`
- `search_adjusted_strength_bucket`
- `validation_exposure_count`

这里的 score / bucket 解释一律以 [research_execute.md](/Users/xinzhan/.openclaw/workspace/quant_factor_system/docs/refacor_logic/research_execute.md) 中的固定映射为准，
不允许 judge 再次自由改阈值。

它们只能：

- 触发更保守的 verdict
- 触发 holdout review
- 改变排序优先级

不能单独生成：

- `admit`
- `reject`
- `replace`

---

## 10. Reason Codes

`judge` 必须使用标准化原因代码，而不是只写自然语言。

每个 reason code 必须带严重性等级。

严重性只允许以下四档：

- `fatal`
- `high`
- `medium`
- `info`

建议至少覆盖以下类别：

### Strength

- `strong_validation_effect`
- `borderline_validation_effect`
- `weak_validation_effect`

### Stability

- `good_split_stability`
- `poor_split_stability`
- `regime_instability`
- `sign_flip_detected`

### Redundancy

- `high_pairwise_overlap`
- `high_family_overlap`
- `high_subspace_redundancy`
- `low_incremental_value`

### Redundancy 解读规则

`research_judge` 对 redundancy 的解释顺序应固定为：

1. 先看 `pairwise duplication`
2. 再看 `family_overlap_bucket`
3. 最后看 `subspace_redundancy_view`

推荐解释规则：

- 若 `pairwise corr > 0.90`，直接按近重复处理
- 若 `family_overlap_bucket = high` 且 `residual_survival_ratio < 0.30`，按 family 内重复处理
- 若 `subspace_redundancy_score > 0.70` 且 `residual_incremental_ic / raw_incremental_ic_proxy < 0.30`，按子空间级重复处理
- 若 pairwise 不高、family overlap 不高、且 `residual_incremental_ic` 保留良好，才可认定为有新增信息

对于当前约 50 因子规模，`subspace_redundancy_score` 只能作为辅助证据，不能单独一票否决。

注意：

- `family_overlap_score` 和 `subspace_redundancy_score` 只是证据组件
- `high_family_overlap` 这类 reason code 不能仅由单一 score bucket 机械触发
- 至少还要结合：
  - `residual_incremental_ic`
  - `nearest_factor relation`
  - 是否存在真实 replace / value-add 解释

### Feasibility

- `feasibility_ok`
- `feasibility_borderline`
- `feasibility_poor`

### Mechanism

- `mechanism_aligned`
- `mechanism_unclear`
- `mechanism_drifted`

### Policy

- `known_bad_pattern`
- `implementation_too_complex`
- `holdout_review_required`
- `high_data_mining_risk`

### 严重性映射建议

- `sign_flip_detected`: `fatal`
- `known_bad_pattern`: `fatal`
- `family_assignment_invalid`: `high`
- `high_subspace_redundancy`: `high`
- `poor_split_stability`: `high`
- `regime_instability`: `medium`
- `feasibility_borderline`: `medium`
- `mechanism_unclear`: `medium`
- `high_data_mining_risk`: `medium`
- `good_split_stability`: `info`
- `mechanism_aligned`: `info`

---

## 11. Holdout Review Protocol

`holdout` 不是日常研究循环的一部分。
但以下情况必须进入 holdout review：

1. 准备将 candidate 作为高置信 admit / replace
2. 准备把重复失败升级为全局 forbidden / policy
3. `multiple_testing_risk_bucket = high`，但 validation 结果异常强

holdout review 只允许用于：

- promotion confirmation
- policy upgrade confirmation
- false positive 排查

对当前样本长度，`holdout` 的解释必须偏保守：

- 它更像 release veto，不像主要显著性来源
- 它可以否定明显坏结果，但不应单独制造强 admit
- 若 holdout 只有 1 至 2 年，应优先看 sign consistency 与 structural break，而不是追求显著性数字

### 11.1 时序关系

holdout review 默认是 `judge` 之后的异步复核步骤，不内嵌在日常 `research_judge` 同步裁决里。

统一协议：

1. `research_execute` 只能输出：
   - `holdout_review.recommended: true/false`
   - `trigger_reason_codes`
2. `research_judge` 结合 execute 推荐和裁决规则，输出：
   - `holdout_review_required: true/false`
3. 若 `holdout_review_required = true`，则当前 candidate 不能直接成为最终 `admit / replace`
4. 此时 candidate verdict 必须先记为：
   - `reserve`
   - 并附加 `holdout_review_required`
5. 后续单独运行 holdout review，结果只能是：
   - `supportive`
   - `neutral`
   - `contradictory`
6. 只有 `supportive / neutral` 且无 fatal 新问题时，candidate 才可从 reserve 升为 admit 或 replace

触发与时限：

- 触发者：`research_cycle_controller`
- 默认触发时点：下一轮正式 batch 之前
- 最晚截止：进入 queue 后 `1` 个正式 batch 或 `7` 天
- 超时未执行：candidate 记为 `expired_holdout_pending`，维持 reserve

冲突规则：

- 若等待 holdout review 期间，同 `logic + family` 下出现明显更强 candidate，
  旧 candidate 可被标记为 `superseded`
- 被 supersede 的 candidate 不再强制占用 holdout review 槽位

合并逻辑：

- execute 的 `recommended = true` 只是一条上游提示，不自动触发
- judge 才是 `required` 的正式决策点
- 若 execute 未推荐，但 judge 因 `high_data_mining_risk` 或 `reserve_for_replace_review` 判定需要，仍可要求 holdout review

补充规则：

- `holdout_review_required` 不能创造无限悬空状态
- 若 candidate 在 deadline 前未 review，默认维持：
  - `reserve`
  - 并记：
    - `expired_holdout_pending`
- 若后续出现同 `logic + family + experiment_lineage_tag` 的更强 candidate，
  老候选默认不再占用 holdout 槽位

## 12. Logic Lifecycle Arbitration

若 `research_judge.logic_recommendation` 与 `logic` 基于全局上下文推导出的 lifecycle decision 冲突，
必须按以下顺序仲裁：

1. `judge` recommendation 必须被记录
2. `logic` 读取 recommendation
3. `logic` 结合 `search_ledger / batch_usage / saturation evidence / discovery budget` 做最终判定
4. 最终写回 `logic card.status` 的值，以 `logic` 为准

推荐 reason codes：

- `judge_recommendation_overridden_by_scheduler`
- `judge_recommendation_accepted`
- `lifecycle_conflict_due_to_saturation`
- `lifecycle_conflict_due_to_budget_pressure`

不允许用于：

- 回到 `idea` 继续微调 route
- 回到 `execute` 继续改参数

---

## 13. 输出对象

### 13.1 Candidate Judge Record

```yaml
candidate_id: C042_03
candidate_verdict: reserve
reason_codes:
  - borderline_validation_effect
  - good_split_stability
  - high_family_overlap
  - feasibility_ok

evidence_summary:
  validation_effect: borderline
  stability: good
  redundancy: high
  feasibility: acceptable
  risk_model_review: acceptable
  support_window_warning: none
  redundancy_detail:
    family_overlap_bucket: high
    subspace_confidence: medium

actions:
  write_to_library: false
  keep_in_reserve_pool: true
  replace_target_id: null
  holdout_review_required: false
```

### 13.2 Route Judge Record

```yaml
route_id: R021_01
experiment_lineage_tag: ELT_L021_breakout_compression_gate_v1
route_verdict: continue
reason_codes:
  - one_candidate_admitted_or_reserved
  - mechanism_still_live
  - family_has_headroom
```

### 13.3 Logic Judge Record

```yaml
logic_id: L021
logic_recommendation: active
reason_codes:
  - repeated_positive_validation
  - family_becoming_productive
  - no_saturation_signal
```

### 13.4 Batch Judge Report

保存为：

```text
storage/results/batch_XXX_judge_report.yaml
```

至少记录：

- batch 基本信息
- admit / reserve / reject / replace 统计
- route continue / pause / kill 统计
- logic 状态变化
- policy 升级建议
- forbidden 升级建议
- holdout review 建议
- strict stats 风险摘要
- risk model review 摘要

---

## 14. 职责边界

`research_judge` 负责：

- 研究录取
- 研究替换
- route 与 logic 裁决
- 结构化经验回写

`research_judge` 不负责：

- 重新跑 execute
- 自由修改 candidate
- 直接以单轮 validation 结果升级全局 policy

---

## 15. 最终原则

`research_judge` 不是“人工凭感觉拍板”。

它应该是一套正式裁决协议，目标是：

1. 让 admit / reject / replace 可复现
2. 让 route / logic 的生命周期有明确规则
3. 让 memory 回写受到约束
4. 让研究系统不再把 validation 结果无约束地制度化
