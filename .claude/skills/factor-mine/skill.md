---
name: factor-mine
description: 自主因子挖掘 orchestrator——只做 Phase 0 situational assessment + loop control + Agent dispatch，单批细节发生在 /factor-batch subagent 的独立 context
user_invocable: true
---

# /factor-mine — 自主挖掘 Orchestrator

**本 skill 只做编排**——每轮通过 `Agent(subagent_type=general-purpose, prompt=调用 /factor-batch)` 把整批 Phase 1→4 扔进一个**独立 context** 跑，拿回 ≤50 行 summary。主 agent 迭代 N 轮 context 不线性累积——这是自主跑长循环不被 compaction 打断的根本。

## 架构

```
主 agent (orchestrator)             subagent 1 (factor-batch)
  │                                   │
  ├─ Phase 0 Situational Assessment   │
  │   └─ refresh-index / doctor / 读 INDEX cockpit + HOT-TOPICS-LLM
  │                                   │
  ├─ 循环 N 轮:                       │
  │   ├─ 决定本轮方向 / 策略          │
  │   ├─ Agent(→ /factor-batch) ────▶ │   Phase 1 /factor-idea
  │                                   │   Phase 2 research execute
  │                                   │   Phase 3 /factor-judge (fan-out 6 judges)
  │                                   │   Phase 4 archive + report dispatch
  │   ◀─── 返回 ≤50 行 summary ─────── │
  │                                   × (context 丢弃)
  │   ├─ 读 summary.consolidation_trigger → 可能调 /factor-consolidate
  │   └─ 读 summary.calibration_trigger → 可能暂停循环做校准诊断
  │
  └─ 退出条件: 到 N 轮 / 方向枯竭 / 系统级错误
```

## Phase 0 — Situational Assessment（**启动必做**）

每次 `/factor-mine` 启动（含中断重启）先跑：

```bash
# 1. 刷新 cockpit（扫 state + frontmatter + config 触发）
PYTHONPATH=src python3 -m research memory refresh-index

# 2. drift 检测
PYTHONPATH=src python3 -m research doctor
```

然后：

3. **Read `vault/INDEX.md`** 顶部 `<!-- BEGIN COCKPIT -->` 块 + `<!-- BEGIN HOT-TOPICS-LLM -->` 块：state.phase + current_batch + last_batch 摘要 + rounds_since_consolidation + zero_admit_streak + **🎯 下一步**，以及 Phase C Pattern Scout 维护的 **🔥 Hot Topics**。

4. **Pattern Scout 触发**：若 `rounds_since_consolidation ≥ 3` 且 `batches_dir` 有 ≥5 批历史 → 执行 `research pattern-scout --recent 10`（Python 侧写 packet），然后 `Agent(subagent_type=general-purpose, prompt="调用 /pattern-scout skill 读 packet，并只改写 INDEX.md 的 HOT-TOPICS-LLM sentinel 块，返回 ≤10 行 summary")`。拿到 summary 后跑 `research audit index --repair`，再回读 INDEX。首次启动 / 无 pattern 变化时可跳过。

5. **（按需）Read 上一批相关 direction.md 的 Narrative Log 最新一段**——含 `**下一步**:` 字段，是 /factor-judge 上轮写入的 forward-looking 建议。权威源是 direction.md，不冗余存储。

6. **严格按 cockpit 第 1 条建议执行** 分支：

   - `🔄 断点续跑` → 下一轮 dispatch 在 prompt 里加 `resume_from_phase={X}`
   - `⚠️ 修空报告` → dispatch 专门的补 report subagent（不走 factor-batch）
   - `📚 触发 consolidation` → 直接 `/factor-consolidate`（见 §Phase 5），**不走 loop**
   - `🧪 阈值校准` → 按 `lessons.md#Threshold Calibration` 人工 / 半人工流程
   - `📄 新论文 intake` → 跑 `/factor-paper` 处理待 intake 的 paper
   - `▶️ 继续同方向` / `🆕 选新方向` → 进 §Loop

## Loop（核心循环）

每轮：

```
1. 确定本轮 batch_strategy + direction_tag
   - 用 cockpit 推荐 + INDEX HOT-TOPICS-LLM 警示 + 目标 direction.md 的 Narrative Log `**下一步:**` 字段
   - 不重读 direction.md 全文——只取最近 1-2 段 Narrative Log 足以
   
2. dispatch 一轮:
   Agent(
     subagent_type: general-purpose,
     prompt: """
       调用 skill /factor-batch 执行下一批。
       
       direction_tag: {tag}
       batch_strategy: continue_direction | new_direction | resume_phase_{X}
       resume_from_phase: {null | designed | judged | archived}
       
       cockpit_hints:
         - zero_admit_streak: {N}
         - hot_topics:
           - {pattern_1}: {affected_directions}, action_hint: {...}
           - {pattern_2}: ...
         - rounds_since_consolidation: {N}
         - last_direction_next_step: "{direction.md Narrative Log 最近一段 **下一步:** 字段}"
       
       按 /factor-batch skill 流程跑完 Phase 1→4，返回 ≤50 行 summary。
     """
   )

3. 检查退出 / 分支（不落盘，主 agent 直接用 summary 决定）:
   - summary.consolidation_trigger=true → 跳出 loop，去 §Phase 5
   - summary.calibration_trigger=true → 跳出 loop，报告给用户 / 执行校准流程
   - summary.phase_reached != "archived" → 记录，按 summary.next_hint 决定重试 or abort
   - 迭代次数达标 → 退出
   - 方向全部 exhausted → 退出

4. 回 1（下一轮启动前 `research memory refresh-index` 让 cockpit 反映最新 state）
```

**No memo 文件**：本批 finding / next_hint 已经由 /factor-judge 在 Phase 3 写入 direction.md 的 Narrative Log（`**下一步:**` 字段）——那是权威源，orchestrator 按需 Read 即可，不做冗余存储。

## Phase 5 — /factor-consolidate（条件触发）

检查 `config.yaml.consolidation.auto_triggers`，任一满足即调 `/factor-consolidate`：

- `rounds_since_last_consolidation ≥ 10`
- `vault/lessons.md` ≥ 400 行
- 任一 `vault/directions/*.md` ≥ 500 行
- active directions ≥ 20

Consolidation 跑完后回 §Phase 0（重读 cockpit），再判断是否继续 loop。

## 自主模式

- 方向自动选取，不问"选哪个"——基于 cockpit + INDEX HOT-TOPICS-LLM + 目标 direction.md Narrative Log
- 候选验证失败 / batch 失败自动跳下一批（不 retry 同方向超过 2 次）
- admit 由 /factor-batch 内部处理 report subagent dispatch
- 一轮结束自动 check consolidation / calibration 触发
- **只在系统级错误时停下**（DB 永久断、文件损坏、Python 异常无法恢复 / Agent dispatch 无法启动）

## Context 纪律

本 skill 的核心设计目标是**主 agent context 不随迭代线性增长**：

- ✅ **读**：INDEX cockpit（轻）/ INDEX HOT-TOPICS-LLM（轻）/ 目标 direction.md Narrative Log 最新段（按需）/ Agent 返回的 summary（≤50 行）
- ❌ **不读**：_hints.yaml / judge.md / direction.md 全文 / candidates/*.md / bash 长输出 / subagent 内部产出
- ❌ **不写**：judge.md / direction.md / C{id}.md / factor.md / factor.yaml / manifest.yaml / 任何 `_meta/*` 文件——全由 subagent / Python CLI 负责
- ✅ **主 agent 不直接写任何 vault 文件**——所有持久化通过 subagent / Python CLI 间接发生

20 轮后主 agent context 目标 < 2000 行。

## 可用 CLI helper 速查

| CLI | 作用 |
|---|---|
| `research doctor` | Phase 0 drift 检测 |
| `research state` | 查 state |
| `research memory refresh-index` | Phase 0 刷 cockpit |
| `research memory snapshot --recent 10` | 选方向辅助（通常由 subagent 调）|
| `research consolidate [--target ...]` | Phase 5 |
| `research pattern-scout` | Phase C 落地后：Pattern Scout 的 Python 侧聚合 |

Phase 1-4 所需 CLI（`research phase1 freeze` / `execute` / `judge` / `archive`）**本 skill 不直接调**——由 /factor-batch subagent 调。

## State DAG 参考

`state.current_batch_phase` 推进（`src/research/storage/state.py` 强制）：

```
null → designed → executing → judged → archived → null
 ↑       (P1)       (P2 start)  (P2 end) (P3 end)  (P4 finish)
```

orchestrator 不直接推 DAG——由 subagent 内部的 Python CLI 推进。但 orchestrator 读 `state.current_batch_phase` 决定断点续跑策略（Phase 0 Step 6 `🔄 断点续跑` 分支）。
