---
name: factor-mine
description: 5-phase 自主因子挖掘循环：START → EXECUTE → JUDGE → ARCHIVE → CONSOLIDATION
user_invocable: true
---

# /factor-mine — 自主挖掘主循环

**/factor-mine 是编排器**——本 skill 只负责排兵布阵，各 phase 的细节在对应子 skill。自主模式运行，不问确认，只在系统级错误时停（CLAUDE.md "Autonomous Mining Mode"）。

## 架构

```
/factor-mine
  ├─ Phase 1 → /factor-idea           LLM 设计候选 + Python 冻结 manifest
  ├─ Phase 2 → research execute        纯 Python 向量化 → result.yaml
  ├─ Phase 3 → /factor-judge           pre-hint + 并行 subagent 判决 + audit
  ├─ Phase 4 → Python archive          F{id} 分配 + backfill + 画图 + 后台 /factor-report
  └─ Phase 5 → /factor-consolidate     条件触发；LLM 重写 memory
```

## State DAG

`state.yaml.current_batch_phase` 在 `src/research/storage/state.py` 强制推进：

```
null → designed → executing → judged → archived → null
 ↑       (P1)       (P2 start)  (P2 end) (P3 end)  (P4 finish)
```

**命名注意**：`judged` 指"P2 已完成，ready for P3"（时态陷阱 — 读起来像"已 judge 过"，实际是"等 P3 来 judge"）；`archived` 指"P3 已完成，P4 在途"。违反 DAG → `InvalidPhaseTransition`。

**Python CLI 提供的流程 helper**（R2：Python 管流程、LLM 管内容）：

| CLI | 作用 |
|---|---|
| `research doctor` | 校验 state ↔ vault 一致性，orphan 检查，给修复建议 |
| `research state` | 查看当前 state（无子命令） |
| `research state next-batch-id` | 纯查询下一个 `batch_NNN`，不改 state |
| `research state set KEY VALUE` | 低层改字段（YAML literal 解析） |
| `research state reset --confirm` | **破坏性**：state 归零（vault 被 `git rm` 后用来对齐） |
| `research memory refresh-index` | 重刷 `INDEX.md` 下半 auto-section |
| `research phase1 freeze <spec.yaml>` | P1 一步到位：allocate batch_id + begin_batch + freeze_manifest + refresh INDEX；失败自动回滚 state |
| `research execute <batch>` | Phase 2 纯 Python 向量化 |
| `research judge <batch> {pre-hint\|audit}` | Phase 3 的 Python 两端 |
| `research archive <batch>` | Phase 4 归档（F{id} 分配 + backfill + 画图 + 打 packet + commit） |
| `research consolidate [--target ...]` | Phase 5 |

## 流程

### Phase 0 — Situational Assessment（**启动必做**）

**每次 /factor-mine 启动（含中断重启）必须先跑这四步，按 INDEX cockpit 指令行动**：

```bash
# 1. 刷新 cockpit 数据（扫 state + frontmatter + config 触发）
PYTHONPATH=src python3 -m research memory refresh-index

# 2. drift 检测
PYTHONPATH=src python3 -m research doctor
```

然后：

3. **Read `vault/INDEX.md`** — 顶部 `<!-- BEGIN COCKPIT -->` 块给出：
   - `state.phase` + `current_batch`：是否正在某 phase 中断
   - `last_batch` 摘要 + `last_direction.status`：上一批结果与方向状态
   - `rounds_since_consolidation` / `zero_admit_streak` / `empty factor.md` 预警
   - **🎯 下一步（按优先级）**：cockpit 已把规则跑过一遍，给出排序建议

4. **严格按 cockpit 第 1 条建议执行**。可能的分支：
   - `🔄 断点续跑` → 跳对应 phase（见下表）
   - `⚠️ 修空报告` → 按提示重 dispatch `/factor-report` subagent（把缺 `.md` 的 F{id} 补齐）
   - `📚 触发 consolidation` → 先调 `/factor-consolidate`，回来再读 cockpit
   - `🧪 阈值校准` → 走 `lessons.md#Threshold Calibration` 扫 reserve，确认后才继续
   - `▶️ 继续同方向` → 读 `directions/{last_direction}.md` 的 Threads 决定下一 thread → Phase 1
   - `🆕 选新方向` → Phase 1 走 snapshot + lessons 选方向

### 断点恢复表（phase ≠ null 时）

| phase | 上一步 | 恢复动作 |
|---|---|---|
| `null` | P4 已完成或从未开始 | Phase 1 从头 |
| `designed` | P1 done | 跳到 Phase 2 |
| `executing` | P2 在途（中断）| 重跑 Phase 2（幂等）|
| `judged` | P2 done | 跳到 Phase 3 |
| `archived` | P3 done | 跳到 Phase 4 |

不要重复已完成的 phase——DAG 会 raise。

## 正常流程

### Phase 1 — /factor-idea

1. 从 Phase 0 cockpit 已确定的方向出发：
   - 若 cockpit 建议"继续同方向" → 读 `directions/{tag}.md` Threads + narrative log，选下一 thread
   - 若 cockpit 建议"选新方向" → `PYTHONPATH=src python3 -m research memory snapshot --recent 10`，从方向表选 `status=productive/exploring` 且 `rounds` 最少；配合 `vault/lessons.md` Promising Unexplored
2. 调 `/factor-idea`，按该 skill 的 6 步执行（选方向 / 定 batch_goal / 设计 5-10 候选 / Python 验证 / 冻结 manifest）

校验：`state.current_batch_phase == "designed"`。

### Phase 2 — research execute

```bash
PYTHONPATH=src python3 -m research execute batch_{N}
```

纯 Python 向量化（R5），产出 `batches/batch_{N}/result.yaml`。单候选异常 → 写 `compute_error` 字段，不中断 batch。Holdout 绝不计算。

校验：`state.current_batch_phase == "judged"`。

### Phase 3 — /factor-judge

按 `/factor-judge` 全流程执行：pre-hint → **单条消息**并行派发 subagent → 主 agent 写 `judge.md` + 更新 `direction.md` + `INDEX.md` → Python audit（失败最多 3 轮重试，按违规分类处理，见该 skill §恢复逻辑）。

校验：`state.current_batch_phase == "archived"`。

### Phase 4 — Python archive + 后台 /factor-report

纯 Python 编排，**主 agent 仅负责 dispatch 后台 report subagent**。完整实现在 `src/research/phases/phase4_archive.py`：

1. 升序分配 F{id}，写 `vault/factors/F{id}.yaml`
2. 机械 backfill：C{id}.md frontmatter / judge.md 表格 / direction.md evidence trail 回填 F{id}
3. `render_factor` 读 `cache/batch_diagnostics/` 画 15 张 PNG 图 + `report.json`（纯 plot，R4 无重算）
   - IC 家族 (4)：`ic_timeseries`（双面板：日 IC + 累积）/ `rolling_ic` / `ic_distribution` / `monthly_heatmap`
   - Profit 家族 (3)：`quintile_bar` / `cumulative_returns`（含 L/S 叠加）/ `annual_group_returns`
   - Risk 家族 (2)：`style_exposure_bar` / `alpha_waterfall`
   - Stability 家族 (1)：`stability_panel`（双面板：support windows + summary）
   - Decay 家族 (3)：`ic_decay` / `factor_distribution` / `coverage`
   - Uniqueness 家族 (1)：`correlation_bar`
   - Composite (1)：`radar`
4. `report_packer` 打包 `_packets/report_packet_F{id}.md`
5. 后台 dispatch `/factor-report` subagent per admitted F{id}——**主 agent 必做，不能跳过**。每个 admit 一个 Agent 工具调用（可在单条消息里并行 dispatch 所有 admits）。subagent 返回后，**Python 侧验收**：
   - 扫 `vault/factors/F{id}.md` 文件大小 > 0 且含 `# F{id}` H1
   - 失败（空文件 / 缺 H1） → append `_subagent_failures.log` + 重 dispatch 一次
   - 二次仍失败 → log 记载，不阻塞主循环；人工兜底
   - **过往经验**：batch_001 这一步被跳过导致 F001.md 空留，无 `_subagent_failures.log`——即"静默失败"。这个验收步骤就是为了杜绝这种哑 bug。
6. `direction_updater` 刷 direction frontmatter（rounds/admits/members/last_batch）+ `index_refresher` 刷 INDEX 下半段
7. `cleanup_finished_packets(skip_batch=current)` — 删往批 `_packets/report_packet_F{id}.md` 中对应 `factor.md` 已写好的（当前批保留，subagent 可能还在读）
8. `research commit {batch_id}` → 单一主 commit，含 factor.yaml × n / backfill / packets / charts / frontmatter。**不含 factor.md**（Step 5 后台独立 commit）

手动清理可用 `research report cleanup-packets [--dry-run] [--skip-batch batch_X]`。

Phase 3↔4 分工：**direction.md body**（Narrative Log / Threads / Known Failures）在 Phase 3 写完；Phase 4 只动 frontmatter 计数器。

Commit message：`[mine] batch_{N} | {direction} | admits=X rejects=Y reserves=Z`

校验：`state.current_batch == null`。

### Phase 5 — /factor-consolidate（条件触发）

检查 `config.yaml.consolidation.auto_triggers`，任一满足即调 `/factor-consolidate`：

- `rounds_since_last_consolidation ≥ 10`
- `vault/lessons.md` ≥ 400 行
- 任一 `vault/directions/*.md` ≥ 500 行
- active directions ≥ 20

完整流程见该 skill。成功后 `rounds_since_last_consolidation = 0`。

### 循环判断

- 还有 active direction → 回到 Phase 1
- 所有 direction exhausted → 停，报"无可挖掘方向"
- 系统级错误 → 停，报异常
- **触发阈值校准**（见下节）→ 暂停继续 → 执行诊断 → 必要时追溯 admit → 继续循环

## 阈值校准触发（防止错杀）

每完成一轮 Phase 3 audit 后，**主 agent 必检**以下信号；任一命中 → **暂停 Phase 4 archive** → 走 [[vault/lessons#Threshold Calibration]] 诊断流程：

1. **错杀 flag**：本批 judge.md 跨候选反思段含"potential over-rejection"（subagent 主动 flag 的候选——rubric §"错杀侦测"）
2. **连续零 admit 警戒**：`last_batch.admits == 0` 且**最近 3 批累计 admit = 0** 且累计 reserve 候选中 ≥ 1 个满足库空间独立（`max_lib_corr<0.30` + `incremental_ic>0.010`）
3. **Reserve 积压**：`累计 reserve / 累计 judged > 40%` 且零 admit
4. **悖论复现**：同"反直觉指标组合"（如低 style_r² + 低 alpha_survival）≥ 2 次独立出现

**命中后的 remediation**（参考 `lessons.md` Threshold Calibration §Step 1-4 完整流程）：

```
Step 1 诊断    → 扫描 reserve + reject 识别被错杀候选（manual grep + metric 交叉核对）
Step 2 调阈    → 仅调必要层：direction.md 自设规则 → rubric 档位 → config.yaml
Step 3 追溯    → state set phase=judged → 改 judge.md + C.md → research archive → dispatch report
Step 4 审计    → lessons.md 历史校准记录追加一条，说明触发条件 + 新阈值
```

**绝对禁止**：在"连续零 admit"信号下**未经诊断就放宽** — 必须确认存在"真实被错杀候选"（满足库空间独立 + rank-order 完美 + 符号互补），而不是"信号真的都不够好"。混淆这两种情况 = 库质量稀释。

## 自主模式

- 方向自动选取，不问"选哪个"
- 候选验证失败自动跳下一个
- judge 严格按 6 CP + mt_budget，不人工复核
- admit 自动 dispatch 后台 report subagent
- 一轮结束自动 check consolidation 触发
- **错杀侦测自动运行**：每批 audit 后 check 4 个 calibration triggers；命中则暂停 Phase 4 进入诊断
- **只在系统级错误时停**：DB 断、文件损坏、Python 异常无法恢复
