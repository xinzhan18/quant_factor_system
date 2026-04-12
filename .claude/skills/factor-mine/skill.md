---
name: factor-mine
description: 5-phase 自主因子挖掘循环：START → EXECUTE → JUDGE → ARCHIVE → CONSOLIDATION
user_invocable: true
---

# /factor-mine — 自主挖掘主循环

## 概述

线性 5 阶段循环，每轮产出一个 batch（manifest → result → judge → factor.yaml + commit）。全自主模式运行，不停下来问用户确认（见 CLAUDE.md "Autonomous Mining Mode"）。

## 流程

### Phase 1 — START + DESIGN
1. 读 `vault/INDEX.md` 选方向（优先级最高的 active direction）
2. 读 `vault/directions/{direction}.md` 了解 hypothesis + 活跃 threads
3. 读 `vault/lessons.md` 了解 structural constraints
4. 设计 5-10 个候选表达式（DSL 或 Python R8 escape hatch）
5. Python 冻结 `batches/batch_{N}/manifest.yaml`（DSL whitelist + 重复检测 + batch_goal ≥ 30 字符）

### Phase 2 — EXECUTE
纯 Python，零 LLM。`phase2_execute.py` 批量跑向量化指标 → 写 `result.yaml`。

### Phase 3 — JUDGE
1. Python 跑 CP01 hard gates
2. Python 扫 `batches/` 算 §7.MT 多重检验预算（`mt_budget`）
3. Python pre-pack `_packets/judge_packet.md`（单一输入，含 numeric_hint per checkpoint）
4. LLM 读 packet → 写 `judge.md`（frontmatter structured verdicts + body 6 CP reasoning）
5. Python audit `judge.md`（6 结构检查，含 CP03 body 必须引用 `mt_bucket`）

### Phase 4 — ARCHIVE
1. Python 分配 F{id} + 写 `factor.yaml`
2. Python 生成 report_packet → dispatch 后台 subagent 写 `factor.md`
3. LLM 更新 `directions/{direction}.md` 的 Narrative Log
4. Python 更新 direction frontmatter + 刷新 INDEX.md + 主 git commit

### Phase 5 — CONSOLIDATION（条件触发）
触发条件（任一满足）：`rounds_since_last ≥ 10` / `lessons.md > 400 行` / `direction.md > 500 行` / `active_directions ≥ 20`。
并行 subagent 重写 lessons + directions → 同步重写 INDEX 上半段 → 单一 commit。

## 关键约束

- **R5 向量化**：Phase 2 的所有指标用 `vectorized_*.py` 模块，Barra 用 3D tensor `pinv+einsum`
- **§7.MT**：CP03 numeric_hint 必含 `mt_bucket`，audit 强制 grep 验证
- **Q32 幂等**：State DAG 强制 `designed → executing → judged → archived → idle`，双重 archive 自动 raise
- **R3 单一输入**：LLM judge 只读一份 `judge_packet.md`，不自行 grep 其他文件

## 自主模式行为

- 方向自动选取，不问"要选哪个？"
- 候选验证失败自动跳过
- judge 严格按 6 CP + mt_budget 执行
- admitted 因子自动 dispatch report subagent
- 一轮结束检查 consolidation 触发，有则自动执行
- **只在系统级错误时停下**
