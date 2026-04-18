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
| 主 agent | 调 Python 前置 + prepack → dispatch 并行 subagent 写 vault md → dispatch INDEX subagent → 调 Python commit |
| Python CLI | (1) 前置检查 (2) prepack packet (3) INDEX 下半段刷新 (4) 原子 commit（含 state.yaml） |
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

## 流程

```
Step 1  Python   前置检查 + backup 所有目标 md 到 _consolidation/backup/
Step 2  Python   prepack — 为每个目标生成 _consolidation/packet_{target}.md
Step 3  主 agent 并行 dispatch subagent（lessons + 各 direction），等全部成功
Step 4  主 agent dispatch INDEX subagent（Step 3 全部返回后单次同步）
Step 5  Python   refresh_index 刷 <!-- BEGIN AUTO-SECTION --> 块
Step 6  Python   mark_consolidated() 写 state.yaml（rounds_since_last=0）
Step 7  Python   git add {rewritten + state.yaml + consolidation_log.md} → 单次 commit
Step 8  Python   删 _consolidation/backup/ 和 packets/
```

**任一 Step 3-5 失败** → Python 从 backup 恢复所有已写目标 → 删 `_consolidation/` → raise。不会留下半新半旧的 vault。

## 原子性保证

- **state.yaml 进同一 commit**：`mark_consolidated()` 必须在 `stage_files` 之前，否则 state 变化漂出 commit，下次 git 仍 dirty
- **commit 一次成**：rewritten + state + consolidation_log 同在一个 `[consolidate]` commit
- **失败回滚**：Python 管从 backup 拷回原文；subagent 不做 git 操作

## Subagent 沙箱

每个 consolidation subagent：

- **输入**：`_consolidation/packet_{target}.md`（唯一）
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
- subagent 可把 frontmatter.status 改为 archived（archived 不进 INDEX 上半段）

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
| `INDEX.md` 上半段 | frontmatter、`## 因子库` 的 `<!-- BEGIN/END FACTOR-LIBRARY -->` 块 | 按 status 分区；active direction 3-5 行 summary；archived 不列 |
| `INDEX.md` 下半段 | `<!-- BEGIN/END AUTO-SECTION -->` 块 | Python 专管，subagent 绝不改 |

INDEX 的三块 Python 专管区域是硬边界——frontmatter、FACTOR-LIBRARY、AUTO-SECTION：packet 给 subagent 完整当前 INDEX（保风格一致），但块内容原样保留。

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
