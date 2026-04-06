---
name: factor-reflect
description: 认知状态更新器：读取 judge_report，生成结构化 belief delta，原子更新 logic card + reflection.md
user_invocable: true
---

# Factor Reflect — 认知状态更新

## 目标

将 judge 产出的局部裁决 **编译** 成每个 logic 的 belief state 更新。这是认知闭环的核心环节：judge 产出证据 → reflect 更新信念 → idea 基于新信念探索。

## 触发条件

/judge 完成后立即调用。由 /mine Phase 3.5 编排。

## 输入

**每个 logic 的输入（按顺序读取）：**
```
storage/batches/batch_XXX/judge_report.yaml    # 主输入：裁决结果
storage/logic/cards/LXXX.yaml                  # 当前执行态
storage/logic/reflections/LXXX.md              # 当前认知叙事
```

## 流程

### Step 1：读取 judge_report

提取每个涉及的 logic_id 的：
- `candidate_verdicts`（含 reason_codes、detail）
- `route_verdicts`（含 verdict: continue/pause/kill）
- `logic_recommendations`（含 recommended_status、reason）
- `logic_diagnostics`（厚诊断 memo：thesis_update, evidence_for/against, failure_boundary, open_questions, next_best_probes）
- `new_lessons`（含 ST/FP/NM 标识）
- `discovery_flags`（含 escalation_status）
- `batch_summary`（admitted/rejected 计数）

### Step 2：生成 LogicBeliefDelta（每个 logic 一个）

基于 judge_report + 当前 card + 当前 reflection，为每个 logic 生成结构化 delta：

**必须使用枚举的字段：**
- `status_change`: proposed|active|warm|productive|saturated|parked|dead
- thread `priority`: high|medium|low
- thread `status`: active|answered|parked

**允许自由文本的字段：**
- `bottleneck_update`
- thread `question` / `why_matters`
- `next_actions`

#### Judge Diagnosis 的消费原则

reflect 不能只看短 verdict；必须把 `logic_diagnostics` 当作主诊断输入。

消费顺序：
1. `logic_diagnostics[logic_id].thesis_update`
   - 用于判断 `focus_question_update`
   - 用于写入 reflection.md 的 “本轮学到了什么”
2. `evidence_for` / `evidence_against`
   - 用于生成 `bottleneck_update`
   - 用于更新 `productive_families` / `failed_families` 的机制解释
3. `failure_boundary`
   - 用于补充 `contract.avoid_patterns`
   - 用于在 reflection.md 中明确“不要再试什么”
4. `open_questions`
   - 用于生成或更新 `deepening_threads`
5. `next_best_probes`
   - 用于生成 `next_actions`
   - 如果 probe 明确回答某个 open question，优先挂到对应 thread 上
6. `factor_roles`
   - 用于把关键因子/失败候选作为 supporting evidence 写入 thread 或 reflection

如果 `logic_diagnostics` 缺失或过薄，reflect 应视为 judge 输出不完整；不要只靠 20 个字 reason
强行脑补整轮认知更新。

**关键计数规则：**
- `generated_this_batch` = 该 logic 在本 batch 的 **总候选数**（不是 admits）
- `admits_this_batch` = 该 logic 在本 batch 的 **录取数**
- 两者分开计数，**绝对不能用 admits 近似 generated**

**Contract 更新规则：**
- `families_to_remove`: route verdict = kill 对应的 family
- `families_to_add`: judge 发现有效的新 family（从 admits 的 family_id 推断）
- `ops_to_add`: 成功因子使用的新算子
- `avoid_patterns_to_add`: 优先从 `logic_diagnostics.failure_boundary` 提取，其次参考 `new_lessons`
- `focus_question_update`: 优先基于 `logic_diagnostics.thesis_update + open_questions` 收窄或转向

**Deepening Thread 规则：**
- 新增 thread: 当 `logic_diagnostics.open_questions` 中出现值得持续追问的机制问题（不是具体候选）
- 更新 thread: 当本 batch 的 `evidence_for/evidence_against/factor_roles` 回答了 thread 的部分问题（更新 supporting_evidence 和 next_probes）
- Park thread: 当 stop_condition 满足或连续 2 batch 无进展

### Step 3：生成 GlobalEscalationDelta

跨 logic 分析：
- 多个 logic 是否收敛到同一失败模式（reason_codes 集中度）
- discovery_flags 中是否有 escalation_status=escalated
- 是否存在全局饱和信号（所有 active logic 的 rounds_without_admit ≥ 2 且 active threads = 0）
- 是否应该提案新 logic（基于跨 logic 证据）

### Step 4：执行写入

**严格按以下顺序，每步单文件原子写入：**

1. **对每个 logic**：调用 `apply_belief_delta(card_path, delta, registry_path)` — card.yaml 单次落盘
   ```python
   from research.logic.reflect import apply_belief_delta
   # LLM 构造 delta，然后调用
   apply_belief_delta(card_path, delta, registry_path)
   ```
2. **对每个 logic**：调用 `write_reflection_md(reflection_path, delta, narrative)` — 追加叙事
3. 调用 `save_global_escalation(path, escalation_delta)` — 持久化跨 logic 信号
4. 调用 `recompute_research_state(cards_dir, state_store)` — 重算派生状态
5. 追加 `proposed_lessons` 到 `research_lessons.md`（软经验，不是硬禁令）

### Step 4a：从 diagnosis 写 narrative，而不是从 verdict 拼句子

`write_reflection_md()` 的 narrative 不应只是 route/candidate 的裁决摘要，而应主要来自
`logic_diagnostics`：

- `thesis_update` → 本轮信念变化
- `evidence_for/evidence_against` → 为什么这样变
- `failure_boundary` → 已确认的边界
- `open_questions` → 仍未回答的问题
- `next_best_probes` → 下一轮探索建议

也就是说：
- `judge_report` 提供厚诊断
- `reflect` 把厚诊断压缩成 belief state
- `reflection.md` 保留解释层叙事

### Step 5：输出摘要

打印每个 logic 的变更摘要：
- status 是否变化
- contract 哪些字段更新了
- 新增/更新/park 了哪些 threads
- next_actions 是什么

## 写权限边界

| 可写 | 不可写 |
|------|--------|
| logic/cards/*.yaml（via apply_belief_delta） | batch artifacts（judge 的领域）|
| logic/reflections/*.md | governance/ledger.yaml（judge 的领域）|
| state/global_escalation.yaml | governance/research_config.yaml forbidden_patterns（ForbiddenManager 的领域）|
| state/research_state.yaml（via recompute） | |
| governance/research_lessons.md（append soft only） | |

## 关键约束

- reflect 不做新实验，不重新计算统计指标
- reflect 的输出必须是结构化的，枚举字段不能用自由文本替代
- 每个 card.yaml 只写一次（apply_belief_delta 保证单次 load+save）
- GlobalEscalationDelta 使用状态机（pending→consumed→applied|dismissed），不删除
- proposed_forbidden 不直接写入 research_config.yaml，只作为提案存在于 GlobalEscalationDelta
- **生产环境禁止直接调用 LifecycleManager.transition()** — 所有 status 变更通过 apply_belief_delta()
