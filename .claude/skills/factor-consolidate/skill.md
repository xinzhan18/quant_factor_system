---
name: factor-consolidate
description: Phase 5 CONSOLIDATION — LLM 周期性重写 memory markdown 文件
user_invocable: true
---

# /factor-consolidate — Phase 5 记忆整理

## 职责

周期性重写 `vault/` 里的 memory markdown 文件：合并同类 lesson、压缩过长的 direction narrative、去除被证伪的内容、升级被反复引用的经验。**整体重构而非增量 append**。

## 触发条件（任一满足）

- `state.yaml.rounds_since_last_consolidation ≥ 10`（auto-trigger）
- `vault/lessons.md` 行数 ≥ 400
- 任何 `vault/directions/*.md` 行数 ≥ 500
- active direction 数量 ≥ 20（需要归档老的）
- 手动触发：`/factor-consolidate` 或 `research consolidate`

```bash
PYTHONPATH=src python3 -m research consolidate [--target TARGET] [--dry-run]
# --target: lessons | directions | direction:{tag} | 不指定 = 全部
# --dry-run: 只生成 consolidation_packet，不重写
```

## 前置条件

- `git status` clean（上一轮 Phase 4 commit 完成）
- `state.current_batch == null`（不在 batch 中途）
- 没有 pending `_subagent_failures.log`（后台 report 都成功）

不满足任一条 → raise，让用户先处理未完成的事。

## 流程

```
Step 1  Python: 前置检查 + 触发判断
Step 2  Python: 为每个目标 md 生成独立的 consolidation_packet
Step 3  并行 subagent: 重写 lessons.md + 各 direction.md
          每个 subagent 只读一份 packet，写一份目标 md
Step 4  最后一步: 重写 INDEX.md
          等所有 direction subagent 完成后
          LLM subagent 写 INDEX 上半段（叙事 summary）
          Python 写 INDEX 下半段（统计表）
Step 5  Python: 单一 commit [consolidate] + 清理临时文件
```

## Subagent 沙箱协议

每个 consolidation subagent：
- **输入**：`_consolidation/packet_{target}.md`（唯一输入）
- **输出**：对应的 vault md 文件（唯一输出）
- **禁止**：读其他文件 / 调 Qlib / 调 DB / Follow [[wiki link]]
- **失败**：整个 consolidation 硬 fail（不保留部分产物），用户 `git reset --hard HEAD^` 回退

## consolidation_packet 结构

```markdown
# Consolidation Packet — {target}

## 任务
完全重写 {target}。

## 当前文件内容（原文）
[完整复制现有 md]

## 最近 N batches 的相关发现
[从 judge.md + narrative 摘取]

## 相关 factor 概要（如果是 direction）
[member F{id} 的一行摘要]

## Consolidation 规则
1. 合并同类 lesson / thread
2. 删除被证伪的内容
3. 升级反复被引用的
4. 压缩 narrative log（保留关键转折点，删流水账）
5. 更新 frontmatter（status 可能变化）
6. 输出完整 md，长度控制在原文的 60-80%
```

## LLM 重写的自由度

- **lessons.md**：system-level facts 段不变，其他可自由重组
- **direction.md**：hypothesis 段不变（除非被证伪），threads 可合并/删除/简化，narrative log 可压缩
- **INDEX.md 上半段**：按 status 分区、每个 direction 3-5 行 summary

## 关键约束

- consolidation 是**独立 commit**，回滚只需 `git reset --hard HEAD^`
- **factor.md 不进 consolidation**（因子报告是一次性产物，Section 4 用 [[link]] 引用 direction）
- 所有 subagent 并行（每个读独立 packet），INDEX 必须最后写
- `state.yaml.rounds_since_last_consolidation` 重置为 0

## consolidation_log.md

每次 consolidation 自动在 `vault/_meta/consolidation_log.md` append 一段：

```markdown
## 2026-04-15 round 45（auto-trigger: rounds_since_last=10）

**Rewrite targets**: lessons.md + 8 directions/*.md + INDEX.md

**Key changes**:
- lessons.md: 新增 "Rank on denominator 注意" 一行
- fundamental_price_divergence.md: T001 answered, narrative 压缩 6→2 段
- volume_autocorrelation.md: productive → saturated

**Commit**: abc1234
**Rollback**: `git reset --hard HEAD^`
```
