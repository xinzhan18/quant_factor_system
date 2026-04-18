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
result.yaml ──(Python pre-hint)──▶ _hints.yaml（curated 数值 + gate 明细 + MT + nearest expr）
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
                 (主 agent 更新 direction.md + INDEX.md 上半段)
                                           │
                                           ▼
                      Python audit (16 checks) → Pass
```

## 数据边界（Why `_hints.yaml`）

`result.yaml` 每 batch 几百 KB，含原始时序数组；rubric 真正用到的只是 ~12 个 scalar。Python pre-hint 把这些字段**扁平化**到 `_hints.yaml.per_candidate.{id}.metrics`，外加 8 项 hard gate 独立结果、MT budget、nearest factor expression。R3 单一数据源 + R4 不重算，LLM 端只跟 hints 打交道。

- **主 agent 读**：`_hints.yaml` 全文 + `directions/{direction}.md`
- **Subagent 读**（见 rubric.md）：rubric.md + 自己那块 `per_candidate.{CID}` + direction.md + 可选 factors/{nearest}.md
- **都不读**：result.yaml / lessons.md / 父 skill.md

## 职责分工

| 角色 | 职责 |
|---|---|
| **Python CLI** | 扫历史 batches + hard gates + MT + 扁平化 rubric → 写 `_hints.yaml`；最终批量 audit |
| **主 agent** | 并行派发 subagent；收集 verdicts；写 `judge.md`（4 层反思）；更新 `direction.md` + `INDEX.md` |
| **Subagent（并行）** | 按 rubric.md 对单个候选做 6 CP 推理 → 写 `candidates/C{id}.md`，返回结构化摘要 |

## 流程

### Step 1 — Python: pre-hint

```bash
PYTHONPATH=src python3 -m research judge batch_{N} pre-hint
```

产出 `storage/vault/batches/batch_{N}/_hints.yaml`。前置：Phase 2 已写 result.yaml。

### Step 2 — 主 agent: 读全局

Read：
- `storage/vault/batches/batch_{N}/_hints.yaml`（全文——批次级 `mt_counts` + 每候选 hard_gate/metrics 一览）
- `storage/vault/directions/{direction}.md`（hypothesis + 活跃 threads）

### Step 3 — 主 agent: 并行派发 subagents

在**单条消息**里一次 call N 个 `Agent` 工具（`subagent_type=general-purpose`），每个对应一个 candidate_id。每个 subagent 的 prompt（逐字，替换占位符）：

```
你是子代理，负责判决候选 {CID}（{BATCH_ID}，方向 `{DIRECTION}`）。

完整判决手册：.claude/skills/factor-judge/candidate-rubric.md

按该手册的"你读什么 / 你写什么 / 返回格式 / 自我校验"执行：
- 读手册全文 + storage/vault/batches/{BATCH_ID}/_hints.yaml 里的 per_candidate.{CID} 块 + storage/vault/directions/{DIRECTION}.md
- 写一份 storage/vault/batches/{BATCH_ID}/candidates/{CID}.md（唯一产出；不跑 Bash）
- 返回结构化摘要（非一行，非整份 md）给主 agent——主 agent 会直接把这段拼进 judge.md，素材要够

所有数值都在 _hints.yaml 里，直接抄，不要自己算。rubric 未覆盖的额外规范不要加。
```

**为什么 dispatch prompt 只是占位符壳子**：rubric.md 是 subagent 的单一真理来源。若此处复制一份，两边漂移 = audit 红灯。

### Step 4 — 主 agent: 写 `judge.md`（4 层反思）

`judge.md` 不是简单的 verdict 列表——它是本批的**知识沉淀入口**。在汇总之上做四层思考：

1. **候选一览**（表格 + 一句 reflection）：除了 metric，一句"这个候选告诉我们关于方向/hypothesis 的什么"
2. **跨候选对比**：候选间是否共享 style 暴露？mutually high corr？本批把 MT 预算从什么档推到什么档？
3. **Thread 进展**（按 thread 分组）：每个 thread 本批进展——ANSWERED / 仍 ACTIVE / DISPROVEN / 新增 T{n+1}
4. **方向级反思**：本方向的 edge 还够不够？下轮往哪走？何时该 saturated？

信息来源：
- Step 2 已读的 `_hints.yaml`（含 mt_counts）
- subagent 返回的结构化摘要
- 必要时 Read 个别 `candidates/C{id}.md` 的 **frontmatter**（不读 body，避免 context 膨胀）

模板见 §judge.md Template。

### Step 5 — 主 agent: 更新 `direction.md` + `INDEX.md`

按 §Direction.md 更新 把本轮结果写进 Threads / Known Failures / Narrative Log，同步 INDEX.md 上半段对应方向条目。**必做**——audit c14/c15/c16 硬校验。所有 wikilink 用 **vault-root**（禁 `../` 前缀）。

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

## Direction.md 更新（audit c14/c15/c16 强制）

必须在跑 `judge audit` **之前**把 `directions/{direction}.md` 和 `INDEX.md` 更新好。wikilink **vault-root**（禁 `[[../...]]`）。

### 1. Threads — evidence trail

对每个非-hard-gate-reject 候选，在其 `thread_id` 对应的 `### T{n}` 段 `**Evidence trail**` 下追加：

```markdown
- [[batches/{batch}/candidates/C{id}|batch_{N} C{id}]]: {key_metrics_short} → {verdict}
```

admit 示例（不写 `[[factors/F{id}]]`——id 由 Phase 4 分配，Phase 4 回填）：
```markdown
- [[batches/batch_009/candidates/C001|batch_009 C001]]: ICIR=0.338 ls_t=3.89 → **admit**
```

Thread 状态标记转换：
- admit 回答了 Question → `[◉ ACTIVE]` 改 `[✓ ANSWERED batch_{N}]`
- 证据反驳假设 → `[◉ ACTIVE]` 改 `[✗ DISPROVEN batch_{N}]`
- 新子问题 → Threads 段末尾加 `### T{next}: ... [◉ ACTIVE]`

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

### 5. INDEX.md 上半段（统一三段式）

LLM 维护的上半段**固定三个 H2 段**，风格统一避免视觉混乱。三块 Python 专管，LLM 绝不动：
- frontmatter（首块 YAML）
- `## 因子库` 内的 `<!-- BEGIN/END FACTOR-LIBRARY -->` 块
- 末尾 `<!-- BEGIN/END AUTO-SECTION -->` 块

```markdown
# Factor Research Index

> MOC (Map of Content)：所有研究方向和 admitted 因子的总览。
> 上半段由 LLM 维护；下半段由 Python 自动刷新。

## 活跃方向

### [[directions/{tag}|{中文名}]] `{status}` `{priority}`
{2-3 句：最近发现 + 当前阻塞 + 下一步议题。须引用 `[[batches/batch_{N}/judge|batch_{N}]]`}

### [[directions/{tag2}|...]] ...
（每个 status ≠ dead/merged 的方向一段。dead/merged 不列。）

## 最近 Batch

- [[batches/batch_{N}/judge|batch_{N}]] ({direction}): {N} 候选 → {admit/reserve/reject 数}。{1 句核心发现}
- [[batches/batch_{N-1}/judge|batch_{N-1}]] (...): ...
（按时间倒序，保留最近 3-5 个）

## 因子库

> Python 自动维护 —— 请勿手改 sentinel 之间内容。

<!-- BEGIN FACTOR-LIBRARY -->
<!-- END FACTOR-LIBRARY -->
```

**风格硬约束**：
- 三段标题固定中文（`活跃方向 / 最近 Batch / 因子库`），不要翻译或重命名
- `活跃方向` 用 `###` + 段落（多段叙事），不是 bullet
- `最近 Batch` 是 bullet list，每行一个项
- `因子库` 块内容由 Python `refresh_index()` 从 `factors/F*.yaml` + `F*.md` 自动渲染；LLM 只能保留 sentinel 对（`<!-- BEGIN/END FACTOR-LIBRARY -->`），内部行不要碰，不要写 `pending F{id}` 占位
- status / priority 用 ``backtick``，直接取 frontmatter 当前值（不写 `exploring→productive` 过程态）
- 所有数字用当前 frontmatter / judge / factor.yaml 实际值，不留占位符或过期快照

---

## Audit Checks（16 项）

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
| 15 | INDEX 方向条目 | 对应方向 `###` 段后 1–3 行提到 `{batch_id}` |
| 16 | thread_id 交叉 | C{id}.frontmatter.thread_id 在 direction.md 以 `### T{n}` 存在 |

---

## 恢复逻辑

audit 失败按违规分类处理：

- **C{id}.md 违规**（c5-c11, c16）→ 重派该候选 subagent，prompt 末尾加"上一轮 audit 失败：{violations}，针对性修正"
- **judge.md / direction.md / INDEX.md 违规**（c1-c4, c12-c15）→ 主 agent 自己重写

重跑 audit。最多 3 轮；超过 → 挂起，报系统级错误。
