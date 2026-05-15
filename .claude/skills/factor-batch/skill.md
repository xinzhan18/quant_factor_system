---
name: factor-batch
description: 执行一整批的 Phase 1→4（设计 / 执行 / 判决 / 归档），供 /factor-mine orchestrator 通过 Agent tool dispatch 调用，返回 ≤50 行 summary。
user_invocable: false
---

# /factor-batch — 单批执行器（subagent entry）

**本 skill 在 subagent 独立 context 中跑**。`/factor-mine` orchestrator 通过 `Agent(subagent_type=general-purpose)` 调用，一次完成 Phase 1→4，返回结构化 summary 后 context 被丢弃——这是主 agent 不被污染的根本机制。

## 输入约定

Orchestrator dispatch prompt 里给：

- `direction_tag`：本批目标 direction（必填）
- `batch_strategy`：`continue_direction` / `new_direction` / `resume_phase_{N}`（含断点续跑）
- `resume_from_phase`：断点续跑时的 phase（可选：`designed` / `executing` / `judged` / `archived`）
- `cockpit_hints`：orchestrator 的 Phase 0 cockpit 给的结构化提示（上一批结论 + INDEX HOT-TOPICS-LLM 等）——**本 skill 不重读 INDEX cockpit**，信任 orchestrator 给的

## 输出约定

subagent 任务完成返回**一段纯文本**给 orchestrator，≤50 行：

```
# batch_{NNN} summary
- direction: {tag}
- phase_reached: archived | failed_at_phase_{N}
- verdicts: admit={X} reserve={Y} reject={Z}
- admitted_factors: [F{id}, ...] | []
- direction_status_changed: {from}→{to} | none
- mt_bucket: low | medium | high
- key_finding: "{1-2 句本批最强结论——orchestrator 本轮决策用，不落盘；权威源是 /factor-judge 写入 direction.md Narrative Log 的同一结论}"
- consolidation_trigger: true | false  # rounds_since_last ≥ 10 或其它
- calibration_trigger: true | false    # 错杀侦测触发
- next_hint: "{给下一批的建议——1 句}"
- new_dead_patterns: ["...", ...]  # 若本批揭示可交给 /pattern-scout 或 Phase 5 升格的模式
```

返回以外**不写额外文件**（judge.md / direction.md / factor.md 等照常写，那是正常产出）。

## State DAG 与断点恢复

| state.phase | 上一步 | 本 skill 入口 |
|---|---|---|
| `null` | P4 finished / fresh | Phase 1 从头 |
| `designed` | P1 done | 跳 Phase 2 |
| `executing` | P2 在途 | 重跑 Phase 2（幂等）|
| `judged` | P2 done | 跳 Phase 3 |
| `archived` | P3 done | 跳 Phase 4 |

违反 DAG → `InvalidPhaseTransition`，subagent 把异常内容 bubble 回 orchestrator。

## 正常流程

### Phase 1 — /factor-idea

1. 从 orchestrator 给的 `direction_tag` 读 `vault/directions/{tag}.md` Threads + narrative log；若 `batch_strategy=new_direction` 先走 snapshot 选方向 + 读 `lessons.md` Promising Unexplored
2. 调 `/factor-idea`，按该 skill 的 6 步执行（Step 4.5 是内联反重演自检，不生成 `_meta/*` packet）

校验：`state.current_batch_phase == "designed"`。

### Phase 2 — research execute

```bash
PYTHONPATH=src python3 -m research execute batch_{N}
```

纯 Python 向量化（R5），产出 `batches/batch_{N}/result.yaml`。单候选异常 → 写 `compute_error`，不中断 batch。Holdout 绝不计算。

**Pre-Phase2 日内 primitive materialization**：若 manifest 中任一候选包含 `primitive_dependencies`，`research execute` 会在正式 Phase2 前执行：

```text
ensure_primitives_materialized()
  -> 解析 registry / proposed_primitives
  -> 检查 primitive cache
  -> 批量物化缺失 daily primitive
  -> 导出到 Qlib daily backend
  -> 在 result.yaml.primitive_materialization 记录 provenance
```

这一步属于 Phase 2 的 Python 前置步骤，不需要 LLM 直接读分钟数据或写物化代码。没有 `primitive_dependencies` 的传统日频 batch 走 no-op。

**stdout 处理**：bash 工具层如有 log redirect 机制则走 log file，否则直接吃 stdout（不进 summary 字段）。

校验：`state.current_batch_phase == "judged"`。

**⚠️ 执行约束（历史踩坑）**：

- **禁止 `run_in_background=true`**。Subagent 一旦返回，runtime 会杀掉它启动的后台 shell——compute 进程连带死亡，state 卡在 `executing`，result.yaml 不生成。**必须在一次 Bash 同步调用里跑完**（Bash `timeout: 1800000` = 30min，配合 `BASH_MAX_TIMEOUT_MS=1800000` 环境变量；如未配置请先读 `~/.claude/settings.json`）。
- **禁止返回 interim summary**。Agent 调用契约是"完成任务一次性返回"——不要返回"Phase 2 仍在跑，稍后 check back"这种中间状态，主 agent 没有 `SendMessage` 可以恢复你。必须在同一轮 invocation 里跑完 Phase 1/2/3/4，才返回。
- **若 Phase 2 compute 超过 30min**（极少数宽窗 rolling Skew/Kurt 的边界情形）→ 不 run_in_background，而是拆分调用（例如先跑前 3 候选再跑后 3 候选，只要 Python CLI 支持 subset 参数；目前 `research execute` 不支持，那就只能单次长 bash）。真出现 >30min 需要用户手动介入的系统级情形，**summary 报 `phase_reached=failed_at_phase_2` + 异常摘要**，让 orchestrator 决定。

### Phase 3 — /factor-judge

按 `/factor-judge` 全流程执行：

1. `research judge batch_{N} pre-hint` → 产出 `_hints_summary.yaml`（subagent 主读）+ `_hints/C{CID}.yaml`（内层 candidate judge 各读）
2. **单条消息并行** dispatch 6 个 candidate judge subagent（三层 agent 中的最内层）
3. 合成 `judge.md` + 更新 `direction.md`（不手写 INDEX）
4. `research judge batch_{N} audit` → 失败最多 3 轮重试，按违规分类处理

audit 通过后，推进 state 到 `archived`。

### Phase 3.5 — 阈值校准触发（仅检查，不跑）

audit 通过后立刻检查四个 calibration trigger（见底部 §阈值校准）；命中任一 → **不进 Phase 4**，在 summary 里设 `calibration_trigger=true` + `next_hint="走校准诊断"`，让 orchestrator 决定（orchestrator 可能下轮专门 dispatch calibration 流程）。

### Phase 4 — Python archive + 后台 /factor-report

纯 Python 编排，本 subagent 仅：

1. `research archive batch_{N}` — 一条命令做完 F{id} 分配 / backfill / 画图 / commit（完整逻辑在 `src/research/phases/phase4_archive.py`）
2. 每个 admitted F{id} **单条消息并行** dispatch `/factor-report` subagent；返回后 **Python 侧验收**：
   - 扫 `vault/factors/F{id}.md` 非空 + 含 `# F{id}` H1
   - 失败 → append `_subagent_failures.log` + 重 dispatch 一次
   - 二次仍失败 → log 记载，summary 里标 `next_hint="F{id} report 人工兜底"`
3. 归档 commit message：`[mine] batch_{N} | {direction} | admits=X rejects=Y reserves=Z`

**不含 factor.md 的 commit**（Step 2 后台独立 commit，由 `/factor-report` 自己负责）。

Phase 3↔4 分工：**direction.md body** 在 Phase 3 写完；Phase 4 只动 frontmatter 计数器。

校验：`state.current_batch == null`。

### 返回 summary

汇总关键字段生成 §输出约定 的文本 → subagent 结束，orchestrator 读 summary。

---

## 阈值校准（仅检查，命中则让 orchestrator 处理）

每 Phase 3 audit 通过后检查：

1. **错杀 flag**：judge.md 跨候选反思段含"potential over-rejection"
2. **连续零 admit 警戒**：本批 admit=0 + 最近 3 批累计 admit=0 + 累计 reserve 有 ≥1 个满足库空间独立（`max_lib_corr<0.30` + `incremental_ic>0.010`）
3. **Reserve 积压**：累计 reserve/judged > 40% 且零 admit
4. **悖论复现**：同一反直觉指标组合（低 style_r² + 低 alpha_survival 等）≥ 2 次独立出现

命中 → `calibration_trigger=true`，跳过 Phase 4 archive，summary 报告。**不在 subagent 内执行 Step 1-4 remediation**——那是 orchestrator 决策的事（可能需要人工 approve 阈值改动或追溯 admit）。

**绝对禁止**：在"连续零 admit"信号下**未经诊断就放宽**——必须确认存在"真实被错杀候选"，而不是"信号真的都不够好"。

---

## 失败 / 异常处理

- **单候选 compute_error**：不中断 batch，写 `compute_error` 字段，Phase 3 正常判决该候选为 hard_gate reject
- **Phase 2 全批失败**（DB 断 / Qlib 崩）：subagent 写 summary `phase_reached=failed_at_phase_2` + 异常摘要 → 返回 orchestrator
- **audit 3 轮都失败**：summary `phase_reached=failed_at_phase_3` + 违规清单
- **Report subagent 二次失败**：不阻塞，summary 记 `next_hint="F{id} report 人工兜底"`
- **系统级异常**（文件损坏 / DB 永久断）：throw，让 orchestrator 捕获——不自行恢复

---

## 可用 CLI helper 速查

| CLI | 作用 |
|---|---|
| `research doctor` | 校验 state ↔ vault 一致性 |
| `research phase1 freeze <spec.yaml>` | P1 一步到位 |
| `research execute <batch>` | P2 计算 |
| `research judge <batch> pre-hint\|audit` | P3 Python 两端 |
| `research archive <batch>` | P4 归档 |
| `research memory snapshot --recent 10` | Phase 1 选方向时用 |
| `research memory refresh-index` | 手动刷 cockpit（本 skill 一般不调，orchestrator 管）|

---

## 不做的事

- **不读 INDEX cockpit**：orchestrator 已在 Phase 0 读过并把关键结论传进 dispatch prompt
- **不写任何 `_meta/*` 文件**，也不写 `INDEX.md HOT-TOPICS-LLM` 块——那是 `/pattern-scout` 的专职产出，本 skill 不越界
- **不触发 Phase 5 consolidation**：检测到触发条件仅标 `consolidation_trigger=true`，orchestrator 下轮决定
- **不自己做阈值校准 remediation**：见 §阈值校准
