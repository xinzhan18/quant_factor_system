---
name: factor-judge
description: Phase 3 JUDGE — per-candidate deep analysis + batch summary, rubric-driven, bidirectional-linked knowledge graph
user_invocable: true
---

# /factor-judge — Phase 3 判决

本 skill 是**主 agent 的手册**。subagent（单个候选判决）的完整手册在同目录 [`candidate-rubric.md`](./candidate-rubric.md)。

## 架构

**一候选 = 一 markdown**。每个 candidate 产出 `batches/{batch_id}/candidates/C{id}.md`（6 CP 深度分析）。batch 层面的 `judge.md` 做汇总 + 跨候选反思 + 方向级洞察。全部文件用 vault-root 相对 wikilink 互连，形成可导航知识图。

```
result.yaml ──(Python pre-hint)──▶ _hints.yaml (唯一持久化源, ~1200 行)
                                           │
                          ┌────────────────┼────────────────┐
                          ▼                ▼                ▼
                 research hints    research hints    research hints
                   {batch} summary   {batch}           {batch} full
                                     candidate {CID}
                  (主 agent Bash)   (subagent Bash)   (audit / debug)
                  stdout ~30 行     stdout ~200 行    stdout 全量
                                           │
                                           ▼
                               (并行 subagents 各写一个 C{id}.md)
                                           │
                                           ▼
                                  candidates/C001.md ...
                                           │
                                           ▼
                         (主 agent 汇总 → 写 judge.md)
                                           │
                                           ▼
                 (主 agent 更新 direction.md；INDEX 由 Python refresh/audit 维护)
                                           │
                                           ▼
                      Python audit (16 checks) → Pass
```

## 数据边界（Why CLI projection）

`result.yaml` 每 batch 几百 KB，含原始时序数组；rubric 真正用到的只是 ~12 个 scalar。Python pre-hint 一次性扁平化 + 加 hard gate 独立结果 + MT budget → 写到 `_hints.yaml`（唯一持久化源）。**LLM 不直接读 `_hints.yaml`**——改用 `research hints` CLI 的 stdout 投影；遵守 R3 单一数据源，避免冗余落盘。

| CLI 调用 | 谁用 | stdout 行数 |
|---|---|---|
| `research hints {batch} summary` | 主 agent——批次级 mt_counts + 每候选 4 字段 (expression / hard_gate_passed / verdict_hint / key_metric) | ~30 |
| `research hints {batch} candidate {CID}` | 对应 subagent——单候选 self-contained（hard_gate / mt_budget / metrics + batch-level mt_counts） | ~200 |
| `research hints {batch} full` | audit / debug | ~1200 |

R3 单一数据源 + R4 不重算 + 迭代隔离三者叠加：主 agent hints 开销 1200 行 → 30 行；subagent 1200 行 → 200 行。

**日内 primitive provenance**：若 `result.yaml.primitive_materialization` 非空，Python pre-hint / `research hints` 投影必须把候选依赖的 primitive 摘要带给 judge。LLM 判决时不重新计算、不读原始分钟数据，只检查：

- primitive construction 是否支持候选 hypothesis
- `available_time` 是否与 label/decision time 匹配
- cache/materialization 状态是否正常
- primitive 是否只是 turnover / volatility / liquidity 的 proxy
- spec_hash / source_freq / template 是否可追溯

- **主 agent 读**：`Bash(PYTHONPATH=src python3 -m research hints {batch} summary)` + `directions/{direction}.md`
- **Subagent 读**（见 rubric.md）：rubric.md + `Bash(research hints {batch} candidate {CID})` + direction.md + 可选 factors/{nearest}.md
- **都不读**：`_hints.yaml` 文件本身 / result.yaml / lessons.md / 父 skill.md

## 职责分工

| 角色 | 职责 |
|---|---|
| **Python CLI** | 扫历史 batches + hard gates + MT + 扁平化 rubric → 写 `_hints.yaml`（唯一持久化源）；`research hints` 提供 summary / candidate / full 投影；最终批量 audit |
| **主 agent** | 并行派发 subagent；收集 verdicts；写 `judge.md`（4 层反思）；更新 `direction.md` |
| **Subagent（并行）** | 按 rubric.md 对单个候选做 6 CP 推理 → 写 `candidates/C{id}.md`，返回结构化摘要 |

日内 primitive 候选的子代理摘要必须额外包含一段 `Primitive Provenance`，列出 `feature_id`、template、available_time、预期机制和主要风险。主 agent 写 `judge.md` 时把该段汇总到批次级 primitive 反思中。

## 流程

### Step 1 — Python: pre-hint

```bash
PYTHONPATH=src python3 -m research judge batch_{N} pre-hint
```

产出 `_hints.yaml`（唯一持久化源）。前置：Phase 2 已写 result.yaml。投影由 `research hints` 按需产生，不落盘。

### Step 2 — 主 agent: 读全局

```bash
PYTHONPATH=src python3 -m research hints batch_{N} summary
```

Bash stdout ~30 行——批次级 `mt_counts` + 每候选 4 字段 (expression / hard_gate_passed / verdict_hint / key_metric)。另 Read `storage/vault/directions/{direction}.md`（hypothesis + 活跃 threads）。

**不 Read `_hints.yaml` 文件**——用 CLI 投影。详细指标在 subagent 的 `research hints ... candidate {CID}` 里。

### Step 3 — 主 agent: 并行派发 subagents

在**单条消息**里一次 call N 个 `Agent` 工具（`subagent_type=general-purpose`），每个对应一个 candidate_id。每个 subagent 的 prompt（逐字，替换占位符）：

```
你是子代理，负责判决候选 {CID}（{BATCH_ID}，方向 `{DIRECTION}`）。

完整判决手册：.claude/skills/factor-judge/candidate-rubric.md

按该手册的"你读什么 / 你写什么 / 返回格式 / 自我校验"执行：
- 读手册全文 + `Bash(PYTHONPATH=src python3 -m research hints {BATCH_ID} candidate {CID})` stdout (~200 行，self-contained，含 mt_counts) + storage/vault/directions/{DIRECTION}.md
- 写一份 storage/vault/batches/{BATCH_ID}/candidates/{CID}.md（唯一产出；除了上面的 hints 投影 Bash 外不跑其它 Bash）
- 返回结构化摘要（非一行，非整份 md）给主 agent——主 agent 会直接把这段拼进 judge.md，素材要够

所有数值都在 `research hints ... candidate {CID}` 的 stdout 里，直接抄，不要自己算。不要去 Read `_hints.yaml` 文件——用 CLI 投影。rubric 未覆盖的额外规范不要加。
```

**为什么 dispatch prompt 只是占位符壳子**：rubric.md 是 subagent 的单一真理来源。若此处复制一份，两边漂移 = audit 红灯。

### Step 4 — 主 agent: 写 `judge.md`（4 层反思）

`judge.md` 不是简单的 verdict 列表——它是本批的**知识沉淀入口**。在汇总之上做四层思考：

1. **候选一览**（表格 + 一句 reflection）：除了 metric，一句"这个候选告诉我们关于方向/hypothesis 的什么"
2. **跨候选对比**：候选间是否共享 style 暴露？mutually high corr？本批把 MT 预算从什么档推到什么档？
3. **Thread 进展**（按 thread 分组）：每个 thread 本批进展——ANSWERED / 仍 ACTIVE / DISPROVEN / 新增 T{n+1}
4. **方向级反思**：本方向的 edge 还够不够？下轮往哪走？何时该 saturated？

信息来源：
- Step 2 已读的 `research hints {batch} summary` stdout（含 mt_counts + 6 候选 verdict_hint）
- subagent 返回的结构化摘要
- 必要时 Read 个别 `candidates/C{id}.md` 的 **frontmatter**（不读 body，避免 context 膨胀）

模板见 §judge.md Template。

### Step 5 — 主 agent: 更新 `direction.md`

按 §Direction.md 更新 把本轮结果写进 Threads / Known Failures / Narrative Log。**必做**——audit c14/c16/c20 硬校验。所有 wikilink 用 **vault-root**（禁 `../` 前缀）。`INDEX.md` 是 Python-owned MOC/cockpit；不要在 Phase 3 手写 INDEX。

### Step 6 — Python: audit

```bash
PYTHONPATH=src python3 -m research judge batch_{N} audit
```

16 项结构检查，失败返回**全部违规列表**（不短路）。见 §Audit Checks + §恢复逻辑。

---

## judge.md Template

**Frontmatter**：

```yaml
---
batch_id: batch_009
direction: timing_signals
judged_at: 2026-04-18T05:50:00Z
candidates:
  - {candidate_id: C001, verdict: admit, factor_name: pv_corr_20d_vol20d}   # admit 必带 factor_name
  - {candidate_id: C002, verdict: reserve}                                   # reserve/reject 不带
  - {candidate_id: C003, verdict: reject}
batch_summary: {total: 3, admit: 1, reserve: 1, reject: 1}
---
```

**`factor_name`**（admit 专用）：主 agent 从 subagent 返回摘要里抄过来，`snake_case` / 3–40 字符 / 反映机制。Phase 4 依此写 `factor.yaml.name` 与 `python_factors/F{id}_{name}.py` 文件名。命名规则与唯一性约束见 `candidate-rubric.md`。

**Body**（4 层结构 + Obsidian callout 视觉脚手架）：

```markdown
# batch_009 Judge Summary

> [!abstract]+ batch_009 · [[directions/timing_signals]] · 3 candidates
> ✅ **admit=1** (C001→F{next}) · ⏸ **reserve=1** (C002) · ❌ **reject=1** (C003)
> **核心发现**: {1 句——本批最强的结构化结论，如"4/6 候选 CP04 全部 poor" 或 "price-corr 完胜 return-corr"}
> **MT Budget**: cumulative 45 → **48** · direction 8 → **11** · bucket `medium`（上界）· 本批 low=0 / med=3 / high=0

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ✅ admit | 🟢·🟢·🟡·🟢·🟢 | ICIR=0.338 ls_t=3.89 | 第一次打出 strong+aligned；机制辨识性强 | [[batches/batch_009/candidates/C001]] |
| C002 | ⏸ reserve | 🟢·🟡·🟡·🟡·🟢 | ICIR=0.21 MT high | CP03 borderline + MT 预算已满；再观察一批 | [[batches/batch_009/candidates/C002]] |
| C003 | ❌ reject | hard_gate | coverage=0.65 | 数据稀疏非机制问题；下轮可重设计 | [[batches/batch_009/candidates/C003]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🟠 边际 · 🔴 阻断档（misaligned/weak/poor/high/unstable）· `hard_gate` reject 该列写 `hard_gate` 不填色。整列飘红 = 方向级警示（对比本批 vs 历史快速诊断）。

## 跨候选对比

- **Style 聚合**：6 候选里 4 个 CP04 暴露 vol_20d（style_r² 0.07-0.10）——本方向易被波动率因子吸收
- **相关度 cluster**：C001/C004 相关 0.72，内部冗余，下轮考虑正交化
- **MT 预算推进**：direction_candidates 8 → 11；bucket 仍在 medium 上界

## Thread 进展

**每个 T{n} 提及必须 wikilink** 到 `[[directions/{direction}#T{n}]]`——包括本批无推进的、状态改变的、本批新建的。新建 thread 在 Step 5 同步写入 direction.md 的 `### T{n}` H3，链必解析。

callout 色码：`[!success]` ANSWERED · `[!note]` ACTIVE · `[!failure]` DISPROVEN。本批无推进的 thread 用 `-`（默认折叠）不占视线。

> [!success]+ T001 [[directions/timing_signals#T001]] — `[✓ ANSWERED batch_009]`
> admit C001。回答了"{子问题}" = {结论 1–2 句}

> [!note]+ T002 [[directions/timing_signals#T002]] — `[◉ ACTIVE]`
> reserve C002。{进展 1 句 + 下一步}

> [!note]- T003 [[directions/timing_signals#T003]] — `[◉ ACTIVE]`（本批无推进）

> [!note]+ T004 [[directions/timing_signals#T004]] 🆕 — `[◉ ACTIVE]`
> 承接 T002 遗留"纯 vol 暴露如何脱敏"。

## 方向级反思

本方向的 edge 逐步收窄：`incremental_ic` 中位数从 batch_007 的 **==0.013==** 降到本批 **==0.007==**。
6 候选中 4 个被 vol_20d 吸收 → 纯 vol 类信号饱和。下轮建议：
1. 切换 short-window + volume 组合看残差 alpha
2. 或 vol_20d 正交化后的信号

若下一轮 admit 率仍 < 20%，`status: productive → saturated`。
```

Audit c13 要求 body 里每个 candidate 都有 `[[batches/{batch_id}/candidates/{cid}]]`（表格 Detail 列已覆盖）。MT Budget 数字在顶部 `[!abstract]` callout，不单列 section（信息不冗余）。

---

## Direction.md 更新（audit c14/c16/c20 强制）

必须在跑 `judge audit` **之前**把 `directions/{direction}.md` 更新好。wikilink **vault-root**（禁 `[[../...]]`）。`INDEX.md` 结构另由 `research audit index --repair` 保证。

### 1. Threads — evidence trail（callout 排版 · c20 硬检查）

**Thread block 三件套**（c20 audit 硬检查——每个被本 batch 候选引用的 `### T{n}` 段都必须满足）：

1. **H3 行带状态标签**（三选一，spelling 固定）：
   - `[◉ ACTIVE]` / `[✓ ANSWERED batch_{N}]` / `[✗ DISPROVEN batch_{N}]`
2. **Body 有 `**Question**:` 行**（1–2 句问题陈述）
3. **Body 有 `**Evidence trail**:` 标题**（**禁用** bare `**Evidence**:`）

**视觉排版**：每个 Thread body 整段包在一个 Obsidian callout 里——按状态着色。详见 `.claude/skills/factor-idea/skill.md` §Body 模板，简要：

| H3 状态标签 | callout 类型 | 色 |
|---|---|---|
| `[◉ ACTIVE]` | `> [!note]+ Thread 当前` | 🔵 |
| `[✓ ANSWERED batch_X]` | `> [!success]+ Thread 结论` | 🟢 |
| `[✗ DISPROVEN batch_X]` | `> [!failure]+ Thread 结论` | 🔴 |

**追加 evidence 的操作**：对每个**非-hard-gate-reject** 候选，在其 `thread_id` 对应 Thread callout 的 `**Evidence trail**:` 下追加一行：

```markdown
### T001: <子问题摘要> [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: <...>
>
> **Evidence trail**:
> - [[batches/batch_009/candidates/C001|batch_009 C001]]　ICIR=0.338 ls_t=3.89 → **admit**
> - [[batches/batch_009/candidates/C002|batch_009 C002]]　mono_flip → **reject (hard_gate)**
>
> **Next probes**: <下一步>
```

（admit 不写 `[[factors/F{id}]]`——id 由 Phase 4 分配后回填。）

**Thread 状态转换（同步改 H3 tag + callout 类型）**：
- admit 回答了 Question → `[◉ ACTIVE]` 改 `[✓ ANSWERED batch_{N}]` + callout `[!note]` → `[!success]`
- 证据反驳假设 → `[◉ ACTIVE]` 改 `[✗ DISPROVEN batch_{N}]` + callout `[!note]` → `[!failure]`
- 新子问题 → Threads 段末尾加新 `### T{next}: ... [◉ ACTIVE]` + `[!note]+` callout（三件套必须齐全）

### 2. Known Failures — reject 条目

```markdown
- C{id} `{expression}` — {reject_reason_short}
```

### 3. Narrative Log — 本轮总结

```markdown
### {YYYY-MM-DD} [[batches/batch_{N}/judge|batch_{N}]]
{admit/reserve/reject 数 + 1-3 核心发现}

**Thread 进展**：
- T001: {进展一句}

**下一步**：{基于结果}
```

### 4. Status / Priority（可选，在 Narrative Log 写理由）

- 首次 admit → `status: exploring → productive`
- 连续 2+ batch reject > 80% → `status: productive → saturated`

### 5. INDEX.md 边界

Phase 3 **不手写 INDEX.md**。INDEX 是 Python-owned MOC/cockpit，由 `research memory refresh-index` 和 `research audit index --repair` 维护。唯一允许 LLM 直接维护的 INDEX 区域是 `/pattern-scout` 的 `HOT-TOPICS-LLM` sentinel 块，和本 `/factor-judge` 无关。

---

## Audit Checks（20 项）

实现见 `src/research/checkpoints/audit.py`。一次过，失败返回全部违规（不短路）。

| # | 对象 | 规则 |
|---|---|---|
| 1 | judge.md frontmatter | 有 batch_id / candidates list / batch_summary |
| 2 | verdict 枚举 | `admit \| reserve \| reject`（`replace` DEPRECATED） |
| 3 | 硬闸不可 override | `hard_gate.passed=false` → verdict 必须 reject |
| 4 | candidates 完整 | result.yaml 每个 candidate_id 都有对应 C{id}.md |
| 5 | C{id}.md frontmatter | 必填齐全；candidate_id 与文件名一致 |
| 6 | C{id}.md body sections | 非-reject 有 CP01–CP06；reject 有 CP01 |
| 7 | CP03 引用 mt_bucket | 非-reject CP03 literal 含 `mt_bucket` |
| 8 | CP03 引用 search_adjusted | 非-reject CP03 literal 含 `search_adjusted` |
| 9 | CP02 引用 hypothesis | 非-reject CP02 含 `[[directions/{direction}` |
| 10 | rubric 档位词 | 每 CP{2..6} body 含该 CP 的一个档位词 |
| 11 | wikilink 形状 | C{id}.md 全部 vault-root，禁 `../` |
| 12 | 候选集一致 | judge frontmatter candidate_id 集 == candidates/*.md 文件名集 |
| 13 | judge body 链接 | 每个 candidate 有 `[[batches/{batch}/candidates/{cid}]]` |
| 14 | direction.md 更新 | evidence trail + Narrative Log + Known Failures 到位，wikilink vault-root |
| 15 | INDEX 结构 | 不在 judge audit 中检查；由 `research audit index --repair` 负责 |
| 16 | thread_id 交叉 | C{id}.frontmatter.thread_id 在 direction.md 以 `### T{n}` 存在 |
| 17 | judge.md Thread 进展段 | 多 candidate/多 thread 时 body 有 `## Thread 进展` |
| 18 | judge.md 跨候选对比段 | `>1` candidate 时 body 有 `## 跨候选对比` |
| 19 | judge.md 候选一览表列 | `## 候选一览` 表头含 `档位` + `反思` 两列 |
| 20 | thread block 三件套 | 被引用的 `### T{n}` 有状态标签 + `**Question**:` + `**Evidence trail**:` |

---

## 恢复逻辑

audit 失败按违规分类处理：

- **C{id}.md 违规**（c5-c11, c16）→ 重派该候选 subagent，prompt 末尾加"上一轮 audit 失败：{violations}，针对性修正"
- **judge.md / direction.md 违规**（c1-c4, c12-c14, c16-c20）→ 主 agent 自己重写
- **INDEX 结构违规** → 跑 `research audit index --repair`；不要在本流程手改 INDEX

重跑 audit。最多 3 轮；超过 → 挂起，报系统级错误。
