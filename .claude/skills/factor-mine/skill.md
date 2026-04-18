---
name: factor-mine
description: 5-phase 自主因子挖掘循环：START → EXECUTE → JUDGE → ARCHIVE → CONSOLIDATION
user_invocable: true
---

# /factor-mine — 自主挖掘主循环

## 概述

线性 5 阶段循环，每轮产出一个 batch（manifest → result → judge → factor.yaml + commit）。全自主模式运行，不停下来问用户确认（见 CLAUDE.md "Autonomous Mining Mode"）。

**Skill 调度链**：mine 是编排器，按顺序调用 3 个子 skill + 1 条裸命令：

```
/factor-mine
  ├── Phase 1: 调用 /factor-idea (候选设计 + manifest 冻结)
  ├── Phase 2: 跑 `research execute batch_{N}` (纯 Python, 无 LLM, 不需要 skill)
  ├── Phase 3: 调用 /factor-judge (6 checkpoint 判决)
  ├── Phase 4: Python 归档 + LLM 更新 direction + 后台调用 /factor-report (深度报告 subagent)
  └── Phase 5: (条件触发) 调用 /factor-consolidate (周期性 memory 重写)
```

每个 Phase 完成后检查 state.yaml 的 phase 状态是否正确推进，再进入下一个 Phase。

## 恢复逻辑（重要）

启动时先读 `state.yaml`。如果 `current_batch_phase` 不为 null，从断点继续：

| `current_batch_phase` | 含义 | 恢复动作 |
|---|---|---|
| `null` | 空闲 | Phase 1 从头开始 |
| `designed` | Phase 1 已完成 | 跳到 Step 3 (Phase 2 EXECUTE) |
| `executing` | Phase 2 中断 | 重跑 Step 3 |
| `judged` | Phase 3 已完成 | 跳到 Step 5 (Phase 4 ARCHIVE) |
| `archived` | Phase 4 已完成 | 跳到 Step 6 (Phase 5 check) |

**不要重复已完成的 Phase**。state.py 的 phase DAG 会 raise `InvalidPhaseTransition`。

## 执行步骤

### Step 1 — 选方向
1. 读 `vault/INDEX.md` 的统计表，找 `rounds` 最少 + `status=active` 的 direction
2. 如果没有 active direction，先创建一个（读 `vault/lessons.md` 的 "Promising unexplored" 段）
3. 确定本轮 `direction` 和 `batch_goal`

### Step 2 — 调用 `/factor-idea`（Phase 1 START + DESIGN）
按 `/factor-idea` skill 的流程：
1. 读 `vault/directions/{direction}.md` 了解 hypothesis + 活跃 threads
2. 读 `vault/lessons.md` 了解 structural constraints + forbidden patterns
3. 设计 5-10 个候选（DSL 优先，Python R8 escape hatch 只在 DSL 无法表达时用）
4. Python 验证 + 冻结 → 产出 `batches/batch_{N}/manifest.yaml`
5. 验证：`state.yaml.current_batch_phase == "designed"`

### Step 3 — Phase 2 EXECUTE（裸命令，无 LLM）

```bash
PYTHONPATH=src python3 -m research execute batch_{N}
```

- 纯 Python 向量化计算，产出 `batches/batch_{N}/result.yaml`（schema 见 `phase2_execute.py`）
- Holdout 绝不计算（架构硬约束，见 `vault/lessons.md` "No holdout leakage"）
- Multi-horizon / Multi-universe 行为由 `config.yaml.evaluation` 驱动
- 验证：`state.yaml.current_batch_phase` 推进到 `"judged"`
- 单候选异常不中断 batch，该候选仅保留 `compute_error` 字段

### Step 4 — 调用 `/factor-judge`（Phase 3 JUDGE）
按 `/factor-judge` skill 的流程（详见该 skill，此处只列骨架）：
1. Python 前置：
   ```bash
   PYTHONPATH=src python3 -m research judge batch_{N} pre-hint
   ```
   产出 `batches/batch_{N}/_hints.yaml`（hard_gate + MT 计数 + 每候选 mt_budget）
2. 主 agent 读 `_hints.yaml` + `result.yaml` + `directions/{dir}.md` + `lessons.md`
3. 主 agent **并行派发 subagents**：每个 candidate_id 一个 `general-purpose` subagent，按 `/factor-judge` 的 "Subagent 调用模板" 注入 prompt，产出 `batches/batch_{N}/candidates/C{id}.md`
4. 主 agent 汇总 subagent 返回的 verdict，写 `batches/batch_{N}/judge.md`（索引 + 跨候选观察）
5. Python 批量审计：
   ```bash
   PYTHONPATH=src python3 -m research judge batch_{N} audit
   ```
6. audit 失败 → 按违规列表重派对应 subagent（C{id}.md 问题）或主 agent 重写 judge.md；最多 3 轮
7. 主 agent 更新 `directions/{dir}.md`（Threads evidence trail + Known Failures + Narrative Log）

### Step 5 — Phase 4 ARCHIVE

**关键顺序**：LLM 写 direction body（Step 4）BEFORE Python 改 frontmatter（Step 6）。这防止 LLM 覆盖 Python 的计数器增量。

7 步流程：

**Step 1 — Python（阻塞）：归档 factor.yaml**
- 分配 F{id}（单调递增）
- 写 `vault/factors/F{id}.yaml`
- 如果 `source_type: python`，复制 .py 到 `python_factors/`

**Step 2 — Python（阻塞）：生成 report_packet**
- 算 Layer 2 derived analytics（按年/月聚合）
- 画图表到 `factors/F{id}/*.png`
- Pack 到 `_packets/report_packet_F{id}.md`

**Step 3 — Subagent（后台，不阻塞）：写 factor.md**
- 每个 admit 一个后台 subagent，调用 `/factor-report`
- 读 `report_packet_F{id}.md`（**R3 单一输入**），写 `vault/factors/F{id}.md`
- 完成时独立 commit：`[report] F{id} {name} report generated`
- 失败不阻塞主循环（factor.yaml 已 committed）

**Step 4 — LLM（阻塞）：更新 direction.md body**
- LLM 根据 judge.md 判决结果更新 direction.md（Narrative Log / Threads / Known Failures）
- 具体格式要求和 audit 规则见 `/factor-judge` "Direction Body 更新" 一节

**Step 5 — Python（阻塞）：主 commit**
- `research commit {batch_id}`
- Commit message 格式：`[mine] batch_{N} | {direction} | admits=X rejects=Y reserves=Z`
- 不含 factor.md（后台生成，独立 commit）
- pre-commit hook 失败 → raise 硬 fail，下一轮 mine 不启动

**Step 6 — Python（阻塞）：更新 direction frontmatter**
- `rounds` ++
- `admits` ++
- `members` append F{id}
- `last_batch` = batch_{N}
- `last_activity` = now

**Step 7 — Python（阻塞）：刷新 INDEX 下半段**
- 重新生成统计表（含 Category / Priority 列）
- 验证：`state.yaml.current_batch == null`（finish_batch 已执行）

### Step 6 — Phase 5 CONSOLIDATION（条件检查）
检查 `config.yaml.consolidation.auto_triggers`，任一满足即触发：
- `rounds_since_last_consolidation >= 10`
- `vault/lessons.md` 行数 >= 400
- 任何 `vault/directions/*.md` 行数 >= 500
- active directions 数量 >= 20

如果触发，调用 `/factor-consolidate`：
1. Python 前置检查（git status clean + state.current_batch is None）
2. Python 并行 pre-pack（lessons packet + direction packets）
3. 并行 subagent 重写 lessons.md + 各 direction.md
4. 同步 subagent 重写 INDEX.md 上半段（读刚重写的 direction md）
5. Python 刷新 INDEX.md 下半段 + 单一 commit
6. `state.rounds_since_last_consolidation` 重置为 0

### Step 7 — 循环判断
- 检查是否还有 active direction 可以继续挖掘
- 有 → 回到 Step 1 自动进入下一轮
- 没有 → 停止，报告"所有 direction 已 exhausted"
- 系统错误 → 停止，报告异常

## 关键约束

- **R5 向量化**：Phase 2 的所有指标用 `vectorized_*.py` 模块，Barra 用 3D tensor `pinv+einsum`
- **§7.MT**：CP03 numeric_hint 必含 `mt_bucket`，audit 强制 grep 验证，LLM 不能 override
- **Q32 幂等**：State DAG 强制 `designed → executing → judged → archived → idle`，双重 archive 自动 raise
- **R3 单一输入**：LLM judge 只读 `judge_packet.md`，report subagent 只读 `report_packet_F{id}.md`

## 自主模式行为

- 方向自动选取，不问"要选哪个？"
- 候选验证失败自动跳过，不问"要继续吗？"
- judge 严格按 6 CP + mt_budget 执行，不需人工复核
- admitted 因子自动 dispatch `/factor-report` 后台 subagent
- 一轮结束自动检查 consolidation 触发条件
- **只在系统级错误时停下**：DB 连接失败、文件损坏、Python 异常无法恢复
