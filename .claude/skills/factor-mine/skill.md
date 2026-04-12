---
name: factor-mine
description: 5-phase 自主因子挖掘循环：START → EXECUTE → JUDGE → ARCHIVE → CONSOLIDATION
user_invocable: true
---

# /factor-mine — 自主挖掘主循环

## 概述

线性 5 阶段循环，每轮产出一个 batch（manifest → result → judge → factor.yaml + commit）。全自主模式运行，不停下来问用户确认（见 CLAUDE.md "Autonomous Mining Mode"）。

**Skill 调度链**：mine 是编排器，按顺序调用 4 个子 skill：

```
/factor-mine
  ├── Phase 1: 调用 /factor-idea (候选设计 + manifest 冻结)
  ├── Phase 2: 调用 /factor-execute (纯 Python 向量化计算)
  ├── Phase 3: 调用 /factor-judge (6 checkpoint 判决)
  ├── Phase 4: Python 归档 + 后台调用 /factor-report (深度报告 subagent)
  └── Phase 5: (条件触发) 直接执行 consolidation，不需要单独 skill
```

每个 Phase 完成后检查 state.yaml 的 phase 状态是否正确推进，再进入下一个 Phase。

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

### Step 3 — 调用 `/factor-execute`（Phase 2 EXECUTE）
按 `/factor-execute` skill 的流程：
1. `PYTHONPATH=src python3 -m research execute batch_{N}`（或直接调用 Phase 2 Python orchestrator）
2. 纯 Python，零 LLM 参与
3. 产出 `batches/batch_{N}/result.yaml`
4. 验证：`state.yaml.current_batch_phase == "executing"` → 推进到 `"judged"`

### Step 4 — 调用 `/factor-judge`（Phase 3 JUDGE）
按 `/factor-judge` skill 的流程：
1. Python 跑 CP01 hard gates + §7.MT 多重检验预算 + pre-pack `judge_packet.md`
2. LLM 读 `_packets/judge_packet.md` → 写 `batches/batch_{N}/judge.md`
3. Python audit `judge.md`（6 结构检查）
4. 如果 audit 失败 → LLM 重写 judge.md → 重新 audit（最多 3 次）
5. 验证：`judge.md` 通过 audit

### Step 5 — Phase 4 ARCHIVE
Python 主导：
1. 分配 F{id} + 写 `vault/factors/F{id}.yaml`
2. 为每个 admit 生成 report_packet → **后台调用 `/factor-report`**（subagent 沙箱协议）
3. LLM 更新 `vault/directions/{direction}.md` 的 Narrative Log（追加本轮发现）
4. Python 更新 direction frontmatter（rounds++, admits++, members append）
5. Python 刷新 `vault/INDEX.md` 下半段统计表
6. Python 执行主 git commit：`[mine] batch_{N} | {direction} | admits=X ...`
7. 验证：`state.yaml.current_batch == null`（finish_batch 已执行）

### Step 6 — Phase 5 CONSOLIDATION（条件检查）
检查 `config.yaml.consolidation.auto_triggers`：
- `rounds_since_last_consolidation ≥ 10` → 触发
- `vault/lessons.md` 行数 ≥ 400 → 触发
- 任何 `vault/directions/*.md` 行数 ≥ 500 → 触发
- active directions 数量 ≥ 20 → 触发

如果触发：
1. 并行 subagent 重写 lessons.md + 各 direction.md
2. 同步重写 INDEX.md 上半段
3. Python 刷新 INDEX.md 下半段 + 单一 commit
4. `state.yaml.rounds_since_last_consolidation` 重置为 0

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
