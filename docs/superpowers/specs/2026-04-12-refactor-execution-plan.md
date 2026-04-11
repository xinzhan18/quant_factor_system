# 因子挖掘系统重构 — 执行 Plan

> Spec date: 2026-04-12
> North-star design: `docs/refactor_plan.md`(17 节,宪法 R1-R8 + 5 phase + schema + cleanup list)
> Source discussion: `docs/walkthrough_qa.md`(Q1-Q47)
> Checklist(live progress): `docs/refactor_checklist.md`

## 1. 本文档的定位

`docs/refactor_plan.md` 已经是**设计 spec**(what to build)。本文档是**执行 spec**(how to build it) — 回答:

- 按什么顺序实施?
- 任务切成几块?每块的 Definition of Done?
- 老代码什么时候删?
- Checklist 怎么维护?

## 2. 执行策略:Refactor-First, Rewrite-When-Necessary + Implement-Then-Delete

用户明确指令:**不做向后兼容,不保留老数据,但允许参考并重构老代码 — 核心数学/算法不用从头写,只需要把它们挪到新架构里并按新宪法(R1-R9)重塑结构**。

### 2.1 老代码的三种命运

每个老文件/模块在 Part 执行时归入以下三档,新的 checklist subtask 里必须标明该条目属于哪一档:

**档 A — 原样保留或轻改**(按 refactor_plan §15 "保留改造"):
- `src/research/compute/operators.py`(Qlib 自定义算子,不动)
- `src/research/compute/data_provider.py`(轻改)
- `src/research/domain/` 里的基础 dataclass(简化)
- 大部分 `tests/` 里的 fixture 数据和 pytest 辅助

**档 B — 抽核心逻辑 + 重塑结构**(refactor,不是 rewrite):
- `src/research/stats/*.py` → 抽 IC / monotonicity / stability 的纯数学公式,按向量化形态塞进 `compute/vectorized_*.py`
- `src/research/risk/exposures.py` → 抽 Barra OLS 的矩阵运算,重写为 `np.einsum` 批量版本
- `src/research/redundancy/pairwise.py` → 核心 `corrwith` 逻辑抽出,简化到 `vectorized_redundancy.py`
- `src/research/feasibility/*.py` → 抽 coverage / half_life / turnover 公式,向量化
- `src/research/execute/precheck.py` → 抽 DSL 白名单常量,塞进新 `phase1_start.py`
- `src/research/execute/sample_policy.py` → 简化后塞进新 `phases/` 或 `storage/`
- `src/report/analytics/*.py` 6 个 analyzer → 抽纯数学函数,按新 "消费 result.yaml.derived_analytics 不重算" 的原则重写
- `src/report/charts/*.py` → 大部分 plotly 代码可直接用,只调整输入接口
- `src/report/data_prep.py` / `scorer.py` → 抽评分逻辑,简化

**档 C — 彻底废弃,不参考**(refactor_plan §15 "完全删除"):
- `src/research/logic/`(LogicCard / Scheduler / Lifecycle / FamilyRegistry 所有概念废弃)
- `src/research/governance/` 大部分(guarded_writer / forbidden_manager / cycle_controller / batch_scheduler / cold_start)
- `src/research/judge/candidate_judge.py`(死代码)+ `mechanism_alignment.py` + `replace_protocol.py`
- `src/research/storage/{finalizer,consistency,candidate_store,packet_store,result_store,ledger_store}.py`(过度工程)
- `src/research/execute/{judge_packet_builder,execution_gate,compute_implementations}.py`
- `src/report/renderer.py` + `src/report/templates/`(1423 行死代码)
- 所有 `storage/{logic,governance,registry}/` 老数据(P7 统一 rm 或 → `_legacy/`)

### 2.2 执行原则

- **不向后兼容** — 新代码不 import 老模块,不做 adapter/shim,新数据 schema 完全替换老 schema
- **档 B 的重构方式**:开新文件,copy 老文件核心片段过来,按新结构重塑(不 edit 老文件原地改,因为老文件会整体删);commit 里写明 "reused from {old_path}"
- **先建后删** — 每个 Part 内:新代码(含档 A 保留 + 档 B 重构 + 必要新写)+ pytest 通过 → commit → 老代码当前保留(进 P7 统一清)
- **档 A 保留**不算新代码,不需要新 commit,P7 前保持原位即可
- **随时可回退** — 每个 Part 一个 commit,`git reset HEAD^` 即可回上一个稳定点
- **不管老数据** — `storage/registry/factors/F001-F019.yaml`、老 batches、老 logic cards 不迁移,P7 时整体搬到 `_legacy/` 或直接 rm

### 为什么不是"逐 Part 删老代码"?

三个原因:
1. **集中删风险更低**:一次性 rm 大量文件是强烈的单点操作,放在最后独立 commit,出问题直接 reset
2. **中途可对照**:建新代码时能随时翻老代码作为算法参考(特别是 Barra OLS / IC 计算 / Quintile 分组)
3. **避免尾巴**:逐步删容易漏掉某个老文件,最后还是要扫一遍;不如最后扫一次

### 为什么不是"先删光再建"(scorched earth)?

用户第二条指令明确要求保留老代码直到新代码完成。接受。

## 3. 宪法 — 新代码必须满足

(和 `refactor_plan.md` 第 1 节的 R1-R8 完全一致,这里不重复)

本 plan 额外追加一条执行级宪法:

**R9 — 新代码零老依赖**:Part 1-6 期间,新代码的 import 树不允许出现任何 deprecated 老包:
- `research.logic`, `research.governance`, `research.feasibility`, `research.redundancy`, `research.risk`, `research.stats`
- `research.judge.{candidate_judge,mechanism_alignment,replace_protocol}`
- `research.storage.{finalizer,consistency,*_store except yaml_io,state}`
- `research.execute.{judge_packet_builder,execution_gate,compute_implementations}`
- `report.{renderer,templates,analytics}`(P5 会写新的)

违反 R9 即 Part 不能 mark done。P7 最后一步会对新代码树跑一遍 grep 验证 R9。

## 4. 切分:8 个 Part

| # | Part | 核心产出 | 依赖 |
|---|---|---|---|
| **P0** | Infrastructure & Skeleton | `storage/{state,config}.yaml` 初始化 + `src/research/{phases,checkpoints,memory,archive}/` 空骨架 + `yaml_io/paths/state` 三个基础模块 + `docs/refactor_checklist.md` | — |
| **P1** | Phase 2 EXECUTE(计算层) | `compute/vectorized_{ic,barra,quintile,feasibility,redundancy,stability}.py` + `compute/cache.py` + `compute/preprocess.py` + `phases/phase2_execute.py` | P0 |
| **P2** | Phase 3 JUDGE(checkpoint 层)| `checkpoints/{hard_gates,generator,audit}.py` + `phases/phase3_judge.py` | P1 |
| **P3** | Phase 1 START + DESIGN | `phases/phase1_start.py`(DSL whitelist / python candidate validator / dedup / manifest freeze) | P0 |
| **P4** | Phase 4 ARCHIVE(Python 侧)| `archive/{factor_writer,report_packer,commit}.py` + `memory/{direction_updater,index_refresher}.py` + `phases/phase4_archive.py` 同步部分 | P2 |
| **P5** | Phase 4 ARCHIVE(LLM 侧)+ Report | 新向量化 report analytics + PNG 绘图 + `factor-report/skill.md` subagent 协议 + phase4 的 subagent 调度 | P4 |
| **P6** | Phase 5 CONSOLIDATION + Mine 主循环 | `phases/phase5_consolidate.py` + `cli/mine.py` + 新 `cli/main.py` 路由 + 新 `factor-mine/skill.md` + 其他 skill.md rewrite/delete | P1-P5 |
| **P7** | 老代码清理 + CLAUDE.md 重写 | rm 所有 deprecated 文件 + `storage/` 老目录 → `_legacy/` + 按 `refactor_plan.md` 第 17 节大纲重写 `CLAUDE.md` + 全量 pytest | P0-P6 全绿 |

## 5. 顺序的理由

- **P0 先做**:建骨架 + state/paths 基础设施,让后面所有 Part 都有干净的落点
- **P1 在 P3 之前**:Phase 2 是纯 Python 无 LLM 依赖,pytest 最容易,且决定了 `result.yaml` schema(Phase 3 消费)
- **P3 Phase 1 不是第一个**:manifest schema 要反过来配合 Phase 2 消费,所以先固化 Phase 2 接口再写 Phase 1
- **P5 从 P4 拆出**:Python 归档(同步,必须正确)和 LLM subagent + 可视化(异步,复杂)风险和复杂度差异大,分开验证
- **P7 独立 Part**:集中删大量文件是高风险操作,独立 commit 便于 reset

## 6. Definition of Done(每 Part 必须满足)

1. **新代码实现** — 按 `refactor_plan.md` 的 schema / 函数签名落地
2. **pytest 通过** — 该 Part 的单元测试全绿,且关键指标(IC / Barra / quintile)与老实现数值对齐(参考值从老 `research.stats`/`research.risk` 跑出来对齐一次)
3. **Lint 干净** — `ruff check src/research/ src/report/` 无新增错误
4. **R9 合规** — 新代码 import 树不引用 deprecated 包(grep 验证)
5. **Checklist 勾选** — `docs/refactor_checklist.md` 的该 Part subtask 全勾 `[x]` + 追加完成 commit hash
6. **Git commit** — message 格式 `[refactor] P{N}: {short desc}`,带 Co-Authored-By
7. **Part 间不回滚**:下一个 Part 开始前确认上一个 Part commit 在 HEAD,git status clean

## 7. Checklist 协议

### 文件位置
`docs/refactor_checklist.md`(进 git,在 P0 创建)

### 格式
```markdown
# Refactor Checklist

Last updated: {date}
Current Part: {P{N}}

## P0 — Infrastructure & Skeleton [status: in_progress|done|pending]
- [ ] subtask 1
- [ ] subtask 2
...
**Completed at**: commit {hash}

## P1 — Phase 2 EXECUTE [status: pending]
- [ ] subtask 1
...
```

### 更新时机
- **每完成一个 subtask**:立即把 `[ ]` 改为 `[x]`,**但不 commit**(避免每个 subtask 都一个 commit)
- **每完成一个 Part**:改 status 为 `done` + 追加 `Completed at: commit {hash}` + 和该 Part 的代码变更一起 commit
- **Part 开始时**:改下一个 Part 的 status 为 `in_progress`,单独 commit 一次

### 例外:P7 结束
P7 完成后,checklist 顶部追加 "ALL DONE" 标记 + 最终 commit hash + 整体重构 summary(admitted changes, deleted files count, etc.)

## 8. 风险与对策

| 风险 | 对策 |
|---|---|
| P1 向量化指标和老实现数值不一致 | Part 开始时先跑老实现生成 golden fixture,新实现必须数值对齐(容忍 1e-6) |
| Phase 4 subagent 协议在 Claude Code 环境下实际不工作 | P5 manual verify 时发现问题立即反馈,必要时 fallback 为"主进程同步写 factor.md" |
| pytest 覆盖率不够,P7 清理后才发现某个老函数仍被引用 | R9 grep 检查 + P7 开始前跑一次 `grep -rn 'from research.logic\|from research.governance\|...' src/` |
| Refactor 中途发现 refactor_plan 某节设计不合理 | 停下讨论 → 修 refactor_plan.md → 更新 checklist → 继续;不在执行中硬凑 |
| 跨 Part 依赖失效(如 P2 依赖 P1 的接口后来改了)| Part 边界冻结接口 schema,下游 Part 只消费不改上游 |

## 9. 不在本 plan 的范围

- **数据迁移**:F001-F019 老因子、老 batches 都不迁移。P7 整体搬到 `_legacy/` 保留(或 rm)
- **性能基准**:refactor_plan 已经要求全向量化,但不追加独立的 benchmark Part。如果某指标在 P1 测试中跑得过慢(e.g., > 30s for 1000 candidates),当场修
- **新 feature**:本 refactor 不引入 refactor_plan 之外的新 feature,严格按 17 节落地

## 10. 下一步

1. 本 spec 文档写完并 commit(这一步即将完成)
2. 写 `docs/refactor_checklist.md`(P0 的一部分,但提前创建以便立即追踪)
3. 开始 P0
