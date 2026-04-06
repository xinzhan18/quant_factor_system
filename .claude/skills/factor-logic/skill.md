---
name: factor-logic
description: 管理研究命题 hypothesis：提案、审查、立项、调度、生命周期管理
user_invocable: true
---

# Factor Logic — Hypothesis 管理

> 边界说明：`logic` 是一级入口；`discovery` 只是其异常升级子流程，不应继续作为平行系统扩张。

## 目标

管理市场机制假设的生命周期：提案 → 审查 → 立项 → 调度 → lifecycle 更新。

## 子命令

### `/logic sync`

**Post-judge 治理同步**。在 `/factor-judge` 完成后调用，消费 judge_report 中的 recommendations 并回写到 logic 对象。

> 注意：正常流程中，judge 的 Step 7a 已经完成了这些回写。`/logic sync` 是备用入口，用于：
> (1) 验证 Step 7a 是否完整执行
> (2) 补做遗漏的回写
> (3) 跨会话修复历史遗留的不一致

**流程**：
1. 读取最新 judge_report（`storage/batches/{last_completed_batch}/judge_report.yaml`）
2. 对比 judge_report 的 `logic_recommendations` 与 `storage/logic/cards/*.yaml` 的当前 status
3. 对比 judge_report 的 `new_lessons` 与 `storage/governance/research_lessons.md`
4. 对比 judge_report 的 `discovery_flags` 与 `storage/governance/ledger.yaml` 的 discovery_candidates
5. 报告差异，如有遗漏则补写

**读取**：
```
storage/batches/{batch}/judge_report.yaml
storage/logic/cards/*.yaml
storage/logic/registry.yaml
storage/logic/snapshots/latest_schedule_snapshot.yaml
storage/governance/research_lessons.md
storage/governance/research_config.yaml
storage/governance/ledger.yaml
storage/registry/families/family_registry.yaml
storage/state/research_state.yaml
```

### `/logic list`

```bash
PYTHONPATH=src python3 -m research logic list
```

显示所有 logic 及其状态（proposed / active / warm / productive / saturated / parked / dead）。

### `/logic schedule`

**调度前必读经验教训**：
```
storage/governance/research_lessons.md
```

```bash
PYTHONPATH=src python3 -m research logic schedule
```

生成 schedule snapshot，确定本轮：
- active_pool（带 direction_quota, candidate_quota）
- warm_pool, parked_pool, blocked_pool
- adjacent discovery 预算

**产出后更新 state**（将 active pool 的 logic ID 写入）：
```bash
PYTHONPATH=src python3 -m research state set active_logic_ids '["L001","L002"]'
```

调度维度（7 项）：priority, lifecycle, productivity, saturation, bottleneck, discovery_need, validation_exposure。

调度前必读 `storage/governance/ledger.yaml`：
- `search_ledger.by_logic` — 各 logic 的累计搜索预算消耗，用于 saturation 判断
- `search_ledger.by_experiment_tag` — ELT 的 verdict 分布，kill 的不再分配预算
- `holdout_reviews` — 是否有 pending holdout review 需优先处理
- `search_ledger.discovery_candidates` — escalated 的异常是否需要新 logic 立项

### `/logic new`

创建新 logic 提案流程：

1. **评估覆盖** — 读取 `storage/logic/registry.yaml`，识别空白类别
1b. **消费异常发现** — 读取 `ledger.yaml` 的 `search_ledger.discovery_candidates` 中 `escalation_status=escalated` 的条目，作为 logic proposal 的候选输入。对每个 escalated 异常决定：ignore / 合并到已有 logic 的新 direction / 立项为新 logic proposal
2. **生成 Proposal** — 为每个空白类别（及 escalated 异常）设计 hypothesis（condition, behavior, timeframe）
3. **4 维审查**：
   - mechanism_review: 是否有独立市场机制
   - feasibility_review: 当前字段/DSL 能否支撑
   - novelty_review: 与已有 logic 是否过度重叠
   - research_value_review: 是否值得占预算
4. **裁决**: create_logic / downgrade_to_direction / park / reject
5. **写入**：
   - `storage/logic/proposals/proposal_XXX.yaml`
   - `storage/logic/reviews/review_XXX.yaml`
   - `storage/logic/cards/logic_LXXX.yaml`（如果 create_logic）
   - 更新 `storage/logic/registry.yaml`

## Logic Card Schema

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
  required_fields: [$volume, $close, $high, $low]
  avoid_patterns: [pure_price_only_breakout]
discovery_budget:
  adjacent_discovery_route_quota: 1
evidence_summary:
  productive_families: []
  failed_families: []
  current_bottleneck: null
```

## Lifecycle 状态机

- proposed → active（审查通过）
- active → warm（暂时非主方向）
- active → productive（跨 batch 持续 admit）
- productive → saturated（边际价值下降）
- active/warm → parked（当前不值得投预算）
- any → dead（长期无产出）
- parked → active（新证据出现）

## Family 渐进治理

- `FM_*`: 已注册 family（完整冗余分析）
- `PF_*`: 临时 family（弱比较）
- `FM_unknown`: 未知（仅 pairwise）

Family 不是 admission 的硬前提。

## 关键约束

- Logic 是 lifecycle 最终裁决者（judge 只推荐）
- 单轮 validation 不直接升级全局 policy（需重复证据）
- 必须保留 adjacent discovery 预算（防路径依赖）
- 冷启动期不启用 productive / saturated / dead
