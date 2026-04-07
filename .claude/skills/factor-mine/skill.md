---
name: factor-mine
description: 双速编排器：快速循环（working_theme → draft → quick_execute → rerun）与正式循环（logic_schedule → /idea → /execute → /judge → /report）
user_invocable: true
---

# Factor Mine — 双速研究循环编排器

## 总览

`/mine` 编排完整的因子挖掘迭代。系统有两条回路：

1. **快速回路**（会话内）：working_theme → expression draft → quick execute（train-only）→ feedback → rerun
2. **正式回路**（跨会话）：logic schedule → /idea → 评估阶段（`/execute` + `/judge`）→ /report

快速回路用于半小时内反复试错。只有被冻结进 `batch_XXX/manifest.yaml` 的 candidate 才进入正式回路。

## 正式回路流程

### Phase 0：调度前检查

读取经验教训（**每轮第一步**）：
```
storage/governance/research_lessons.md
```

读取研究状态：
```bash
PYTHONPATH=src python3 -m research state
```

根据输出决定：
- **current_batch 不为空** → 上一轮未完成，先完成它（继续 /execute 或 /judge 或 finalize-batch）
- **pending_holdout_count > 0** → 优先处理 holdout review
- **两者都为空** → 可以开始新一轮

**注意**：读取 `schedulable_logic_ids`（而非 `active_logic_ids`）判断可用 logic。
`schedulable_logic_ids` = active + productive + warm，`productive` 是可继续挖掘的状态（调度器给 0.9 分）。
`active_logic_ids` 可能为空（因为主力 logic 已是 productive），但 `schedulable_logic_ids` 不为空。

**消费 GlobalEscalationDelta**：读取 `storage/state/global_escalation.yaml`，筛选 `status=pending` 的条目：
- `saturation_signal` 强（≥2 logics 收敛到同一失败模式）→ 调用 `/factor-logic new` 创建新 logic
- `logic_proposals` 非空 → 逐条 review（accept/reject/defer）
- `proposed_forbidden` 累积 ≥2 batch 证据 → 通过 ForbiddenManager 正式添加
- 消费后将条目 status 转为 `consumed`（带 consumed_at 时间戳）
- 行动完成后将条目 status 转为 `applied` 或 `dismissed`（带 resolution 原因）
- **永远不删除条目** — 它们构成 outer-loop 决策的审计链

确认可以开始后，读取调度：
```bash
PYTHONPATH=src python3 -m research logic schedule
```

### Phase 1：/factor-idea（候选生成）

调用 `/factor-idea` skill：
- 读取 schedulable logic 的 card.yaml + reflection.md → 设计 batch-local routes（带 experiment_lineage_tag）
- Probe 过滤垃圾（train-only）：`PYTHONPATH=src python3 -m research probe "expression"`
- Quick execute overlay → freeze boundary 判断
- 冻结 candidates → 写入 `storage/batches/batch_XXX/manifest.yaml`

### Phase 2：/factor-execute（正式评估）

调用 `/factor-execute` skill：
```bash
PYTHONPATH=src python3 -m research execute storage/batches/batch_XXX/manifest.yaml
```
产出：`storage/batches/batch_XXX/research_result.yaml` + `storage/batches/batch_XXX/judge_packet.yaml`

### Phase 3：/factor-judge（结构化裁决）

调用 `/factor-judge` skill：
- 读取 judge_packet（主输入）
- 6 维度裁决：mechanism_alignment, statistical_strength, stability, redundancy, feasibility, risk_model_review
- 候选 verdict: admit / reserve / reject / replace
- 路线 verdict: continue / pause / kill / promote_family
- 所有写入通过 guarded_writer

### Phase 3.5a：finalize-batch（硬闭环，**必须**）

judge 完成后，**立即**运行 finalize-batch 命令：
```bash
PYTHONPATH=src python3 -m research state finalize-batch batch_XXX
```

这保证最小闭环：
- 读取 judge_report → apply_belief_delta 到 cards（status、counters、avoid_patterns、next_actions）
- recompute_research_state（更新 schedulable_logic_ids）
- 设置 current_batch=None, current_batch_phase=finalized, last_completed_batch=batch_XXX
- 追加 audit entry 到 ledger

**这一步不可跳过。** 即使后续 reflect 被跳过，state 和 cards 也处于一致状态。

### Phase 3.5b：/factor-reflect（增强层，可选）

调用 `/factor-reflect` skill 补充 richer cognition：

1. 读取 judge_report + 当前 card.yaml + 当前 reflection.md
2. LLM 生成更精细的 LogicBeliefDelta（thread 细粒度更新、focus question 演化）
3. LLM 生成 GlobalEscalationDelta（跨 logic 分析）
4. 对每个 logic：`apply_belief_delta()` → card.yaml 补充更新
5. 对每个 logic：`write_reflection_md()` → 追加认知叙事
6. `save_global_escalation()` → 持久化跨 logic 信号（status=pending）
7. 追加 proposed_lessons 到 research_lessons.md（软经验）

**允许退化**：如果 Phase 3.5b 被跳过，card 只有最小更新（来自 finalize-batch），
认知状态会"弱反射"——thread 不会精细更新，narrative 不会追加。闭环不断但认知深度降低。

### Phase 4：/factor-report（仅在有 admit 时，后台并行）

如果 `admitted_count > 0`，为每个 admitted 因子启动**后台 subagent**。

**两步流程**：
1. `report.builder` — 生成 report_data.json + PNG 图表
2. `/factor-report` skill — 消费 report_data.json 生成 Obsidian Markdown

```
对每个 admitted factor_id:
  Agent(run_in_background=true, description="Report F{id}"):
    "为因子 F{id}（batch_{batch_id}）生成完整报告。

     Step 1: 运行数据构建
     PYTHONPATH=src python3 -m report.builder --factor-id {id} --vault
     产出: storage/evidence/vault/assets/{id}/report_data.json + PNG 图表

     Step 2: 读取 report_data.json，按照 /factor-report skill 模板
     生成 Obsidian Markdown 写入:
     storage/evidence/vault/factors/{id} <name>.md

     注意：
     - 图表嵌入路径格式: ![[assets/{id}/chart_name.png|width]]
     - 只嵌入 available_charts 列表中存在的图
     - 遵循逐图叙事规范（每张图单独嵌入 + 2-3 段分析）"
```

**不要串行等待**——report 每个要 5-8 分钟，后台并行不阻塞主流程。
完成通知会自动返回。

## 快速回路

在 Phase 1 之前或期间，可以随时进入快速回路：

1. 给出 working_theme（基于 logic contract）
2. 设计表达式草稿
3. Quick execute：`PYTHONPATH=src python3 -m research probe "expression"`
4. 检查 IC hint、coverage、turnover
5. 迭代修改 → 直到 freeze_recommendation = freeze_candidate
6. 冻结进 batch manifest

## Ledger 生命周期

`storage/governance/ledger.yaml` 贯穿正式回路全流程，各 phase 的读写职责：

| Phase | 读 | 写 |
|---|---|---|
| Phase 0 (调度) | card.yaml（全部）, global_escalation.yaml | global_escalation.yaml（status 转换） |
| Phase 1 (/idea) | card.yaml, reflection.md, research_config | manifest, idea_report（含 strategy_decision） |
| Phase 2 (/execute) | manifest | research_result, judge_packet |
| Phase 3 (/judge) | judge_packet, ledger | judge_report, ledger（search_ledger 计数, audit_log, holdout_reviews, batch_usage, discovery_candidates） |
| Phase 3.5a (finalize) | judge_report, card.yaml | card.yaml（via apply_belief_delta: status, counters, avoid_patterns, next_actions）, research_state（schedulable_logic_ids 派生）, ledger audit entry |
| Phase 3.5b (/reflect) | judge_report, card.yaml, reflection.md | card.yaml（thread 细粒度更新, focus question）, reflection.md, global_escalation.yaml, research_lessons.md（追加软经验） |
| Phase 4 (/report) | report_data.json, registry factor detail | vault/factors/*.md, vault/assets/{id}/*.png |

## 自主运行模式（Autonomous Mode）

**本 skill 在执行时不得停下来询问用户。** 所有决策点自行判断并继续：

| 决策点 | 自主行为 |
|---|---|
| 选择 logic / 主题 | 按 schedule 优先级自动选取最高优先级条目 |
| probe 结果不理想 | 跳过该候选，记录原因，尝试下一个 |
| 候选数量不足 | 用已有候选冻结 batch（哪怕只有 1 个），不要等凑满 |
| batch 冻结确认 | 满足 freeze 条件直接冻结 |
| execute 某个因子报错 | 跳过该因子，继续处理 batch 中其他因子 |
| judge 裁决 | 严格按 6 维标准执行，不需人工复核 |
| reflect 更新 | 自动执行，不问 |
| report 生成 | admitted 因子自动后台并行生成 |
| 本轮结束 | 检查 schedule 是否还有条目，有则自动开始下一轮 |
| **唯一停止条件** | 系统级错误：DB 挂了、磁盘满、Python 异常无法恢复 |

**禁止输出**以下类型的问句：
- "要继续吗？" / "是否确认？" / "你觉得呢？"
- "选择 A 还是 B？" → 自己选最优的
- "需要我生成报告吗？" → 有 admit 就自动生成

**每轮结束时输出简短状态摘要**（不超过 5 行），格式：
```
[Round N] logic=L00X | batch=batch_0XX | candidates=N | admitted=N | rejected=N | next=L00Y
```

## 关键约束

- 快速回路只能看 **train**，不能看 validation/holdout
- 冻结后进入正式回路，不可回退修改
- 宇宙、日期范围等从 `storage/governance/research_config.yaml` 读取，不 hardcode
- judge 不直接修改治理对象，必须通过 guarded_writer
