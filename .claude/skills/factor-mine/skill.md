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
- **current_batch 不为空** → 上一轮未完成，先完成它（继续 /execute 或 /judge）
- **pending_holdout_count > 0** → 优先处理 holdout review
- **两者都为空** → 可以开始新一轮

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
- 读取 active logic 的 card.yaml + reflection.md → 设计 batch-local routes（带 experiment_lineage_tag）
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

### Phase 3.5：/factor-reflect（认知状态更新）

调用 `/factor-reflect` skill：

1. 读取 judge_report + 当前 card.yaml + 当前 reflection.md
2. LLM 生成 LogicBeliefDelta（结构化，枚举字段）
3. LLM 生成 GlobalEscalationDelta（跨 logic 分析）
4. 对每个 logic：`apply_belief_delta()` → card.yaml 单次原子写入
5. 对每个 logic：`write_reflection_md()` → 追加认知叙事
6. `save_global_escalation()` → 持久化跨 logic 信号（status=pending）
7. `recompute_research_state()` → 重算派生状态
8. 追加 proposed_lessons 到 research_lessons.md（软经验）

### Phase 4：/factor-report（仅在有 admit 时，后台并行）

如果 `admitted_count > 0`，为每个 admitted 因子启动**后台 subagent**：

```
对每个 admitted factor_id:
  Agent(run_in_background=true, description="Report F{id}"):
    "为因子 F{id}（batch_{batch_id}）生成报告。
     执行: PYTHONPATH=src python3 -m report.builder --factor-id {id} --vault
     然后读取 report_data.json 生成 Obsidian Markdown。"
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
| Phase 3.5 (/reflect) | judge_report, card.yaml, reflection.md | card.yaml（via apply_belief_delta）, reflection.md, global_escalation.yaml, research_state（派生）, research_lessons.md（追加软经验） |
| Phase 4 (/report) | — | — |

## 关键约束

- 快速回路只能看 **train**，不能看 validation/holdout
- 冻结后进入正式回路，不可回退修改
- 宇宙、日期范围等从 `storage/governance/research_config.yaml` 读取，不 hardcode
- judge 不直接修改治理对象，必须通过 guarded_writer
