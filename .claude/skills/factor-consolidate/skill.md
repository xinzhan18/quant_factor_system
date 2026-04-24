---
name: factor-consolidate
description: Phase 5 CONSOLIDATION — LLM 周期性重写 memory markdown 文件
user_invocable: true
---

# /factor-consolidate — Phase 5 记忆整理

## 职责

周期性**整体重写**（不是增量 append）`storage/vault/` 里的 memory markdown——合并同类 lesson、压缩过长 narrative、删除被证伪内容、升格反复被引用的经验。单次执行产生**一个独立 commit**，可原子回退。

## 执行模型

| 角色 | 动作 |
|---|---|
| 主 agent | 调 Python 前置 + prepack → dispatch 并行 subagent 写 lessons/direction md → 调 Python refresh-index + commit |
| Python CLI | (1) 前置检查 (2) prepack packet (3) INDEX 全骨架刷新且保留 HOT-TOPICS-LLM (4) 原子 commit（含 state.yaml） |
| Subagent | 读 1 份 packet → 写 1 份 vault md（沙箱）|

**LLM rewrite 不在 CLI 里发生**——`research consolidate` 不 dispatch subagent，只做机械步骤；真正的重写由本 skill 在会话里驱动。

## 触发条件

任一满足触发（全量重写——下半段统计依赖 direction frontmatter 变化，不支持局部）：

- `rounds_since_last_consolidation ≥ auto_triggers.rounds_since_last`（默认 10）
- `vault/lessons.md` ≥ `auto_triggers.lessons_max_lines`（默认 400）
- 任一 `vault/directions/*.md` ≥ `auto_triggers.direction_max_lines`（默认 500）
- active direction ≥ `auto_triggers.total_active_directions`（默认 20，附带触发归档）
- 手动 `/factor-consolidate` 或 `research consolidate`

```bash
PYTHONPATH=src python3 -m research consolidate [--target TARGET] [--dry-run]
# --target: lessons | direction:{tag}   显式限定（仍同时刷 INDEX）
# --dry-run: 只写 packets 到 _consolidation/ 供预览，不 rewrite 不 commit
```

## 前置条件（Python 硬检查）

- `state.current_batch is None`（batch DAG 保证不与 P1-P4 并发）
- `git status --porcelain` 为空
- `_consolidation/backup/` **不**存在（存在 = 上次失败未回滚，拒绝继续）

任一失败 → `Phase5PreconditionError`。

## 流程（2-stage）

本 skill 使用**两阶段 distillation→writer** 架构，避免旧版"24 个 silo rewriter 合起来做不出跨方向结论"的缺陷。

```
Stage A — 4 并行 distillation specialists
──────────────────────────────────────────
Step 1  Python   前置检查（state idle / git clean / 无 stale backup）
Step 2  Python   prepack_specialists — 写 4 份 packet_specialist_{name}.md
Step 3  主 agent 单条消息并行 dispatch 4 subagent：
                  - /consolidate-pattern-analyst
                  - /consolidate-library-gap
                  - /consolidate-calibration
                  - /consolidate-hypothesis-promoter
                每个写 N 份 _consolidation/findings/F{NNN}.md

Stage B — 按 findings scope 的 targeted writers
──────────────────────────────────────────
Step 4  Python   load_findings → 计算 touched_directions (union of affected)
                 + 判是否 touches_lessons
Step 5  Python   backup (lessons if touched + touched directions)
Step 6  Python   prepack_writers — 把 filtered findings 塞进对应 writer packet
Step 7  主 agent 并行 dispatch writers（通常 3-7 个，非全 24）
Step 8  Python   refresh_index（保留 INDEX HOT-TOPICS-LLM 块）+ mark_consolidated + commit
Step 9  Python   删 backup + packet files（findings 进 commit 保留）
```

**任一 Stage A 失败** → findings/ 可能含部分文件，vault 未动，raise（下次重跑先清 findings/）。
**任一 Stage B 失败** → Python 从 backup 恢复所有 writer 目标 → raise。

对比旧版：24 个 silo rewriter → **新版 4 specialists + 3-7 writers = 典型 9-11 subagent**，且产 cross-direction findings 沉淀。

## 原子性保证

- **state.yaml 进同一 commit**：`mark_consolidated()` 必须在 `stage_files` 之前，否则 state 变化漂出 commit，下次 git 仍 dirty
- **commit 一次成**：rewritten + state + consolidation_log 同在一个 `[consolidate]` commit
- **失败回滚**：Python 管从 backup 拷回原文；subagent 不做 git 操作

## Subagent 沙箱

两类 subagent，不同沙箱：

**Stage A — distillation specialist**（4 种，见 `/consolidate-*` skills）

- **输入**：`_consolidation/packet_specialist_{name}.md`
- **输出**：`_consolidation/findings/F{NNN}.md`（一 subagent 可写多个 finding）
- **禁止**：改 vault md / 读其它 packet
- **findings 格式契约**：Markdown + YAML frontmatter，frontmatter 必含 `finding_id` / `specialist` / `severity` / `affected_directions` / `touches_lessons` / `batches_referenced`，见 `src/research/memory/finding_filter.py::FindingMeta`

**Stage B — writer**（lessons / direction）

- **输入**：`_consolidation/packet_{target}.md`（含自己当前 md + 过滤过的 findings）
- **输出**：对应 vault md（唯一）
- **禁止**：读其它文件 / 调 Qlib / 调 DB / follow `[[wikilink]]`
- **异常**：抛出 → 主 agent 捕获 → Python 回滚

## packet 结构

```markdown
# Consolidation Packet — {target}

## 任务
完全重写 {target}。

## 当前文件内容（原文）
[完整复制现有 md]

## 最近证据（Python 预选，最近 5 batches）
- admits>0 的 batch 摘要
- mt_bucket 升/降级事件
- 反复出现的 reject 模式

## 相关 factor 概要（direction packet only）
- member F{id} 一行：ICIR / ls_tstat / mono / Grade

## 证伪信号（direction packet only）
[Python 扫 recent batches：反对本 direction.hypothesis 的候选 ≥ 3 个 → 列出]
- 空 → hypothesis 段必须保留不变
- 非空 → 允许改写 hypothesis，开头加 ⚠️证伪 标记

## 归档候选（active directions ≥ 20 时才有）
- status=saturated 或 last_batch 晚于最近 60 轮 → 列入
- subagent 可把 frontmatter.status 改为 archived（archived 不进 INDEX 的 active Bases 视图）

## Consolidation 规则
1. 合并同类 lesson / thread
2. 按"证伪信号"删除被证伪的内容
3. 升级反复被引用的经验
4. 压缩 narrative log（保留关键转折点，删流水账）
5. 目标 ≤ 原文 80%（上限建议，清晰度优先）
6. 输出完整 md
```

## 各目标自由度

| 文件 | 固定不变 | 可重组 |
|---|---|---|
| `lessons.md` | Data Facts / Operator Registry / Path Selection / Structural Constraints 四段 | 其它段落 |
| `directions/{tag}.md` | hypothesis 段（除非证伪信号 ≥ 3）| threads 合并/删除/简化，narrative log 压缩；frontmatter 由 Python 管 |
| `INDEX.md` | 除 `<!-- BEGIN/END HOT-TOPICS-LLM -->` 外全部 Python 专管 | 本 skill 不重写；Python refresh 后自动反映 direction/frontmatter 变化 |

INDEX 的硬边界：frontmatter / COCKPIT / INSIGHT / Bases embeds / system status 全部 Python 专管；LLM 只能通过 `/pattern-scout` 维护 `HOT-TOPICS-LLM` 块。

## 死链处理

factor.md 不进 consolidation（一次性产物）。direction rename/merge 会让 factor.md 里的 `[[directions/old|...]]` 变死链。consolidate 完成后 Python 自动跑 `research audit links`：

- 扫所有 `vault/factors/*.md` 的 wikilink
- 目标不存在 → 写 `_consolidation/dead_links.md` 供人工修
- 不自动改 factor.md（LLM 一次性产物语境已失，人工判断更稳）

该步失败不阻塞 commit。

## dry-run 与回退

```bash
# 预览 LLM 将要看到的输入
PYTHONPATH=src python3 -m research consolidate --dry-run
# 只写 packets 到 _consolidation/，不 backup / 不 dispatch / 不 commit

# 预览 LLM 输出：直接正常跑一次 → commit 完成后 `git show HEAD` 看 diff，不满意 revert

# 回退
git revert --no-edit <consolidate-commit-hash>
# 用 revert 而非 reset --hard——保留历史且对"commit 不在 HEAD"的情况安全
```

## consolidation_log.md

每次成功 append 一段到 `vault/_meta/consolidation_log.md`，**与主 commit 原子**：

```markdown
## 2026-04-15 round 45（trigger: rounds_since_last=10）

**Rewrite targets**: lessons.md + 8 directions/*.md + INDEX.md

**Key changes**:
- lessons.md: 新增 "Rank on denominator 注意"
- fundamental_price_divergence.md: T001 answered, narrative 6→2 段
- volume_autocorrelation.md: productive → saturated（归档）

**Commit**: abc1234
**Rollback**: `git revert --no-edit abc1234`
```
