---
name: consolidate-calibration
description: Phase 5 Distillation Specialist — 扫最近 judge.md 的阈值校准诊断段，提出具体阈值调整建议；产出 findings/calibration/{NNN}.md
user_invocable: false
---

# /consolidate-calibration — 阈值调整提案 distillation（subagent）

**本 skill 在 subagent 独立 context 中跑**，Phase 5 4 specialist 之一。职责：**不调阈值本身**（那是人工决策），而是从最近判决轨迹里**提出有证据的阈值提案**——哪条 config.yaml 阈值该调到哪个值，有多少历史 reserve 会因此翻转。

## 输入

Read `storage/vault/_consolidation/packet_specialist_calibration.md` 全文——含：
- Task 描述
- 最近 N 批 judge.md 全文（关注 `## 阈值校准诊断` + `reserve_audit` 段）

## 输出

写到本 specialist 自己的子文件夹：`storage/vault/_consolidation/findings/calibration/{NNN}.md`，**一个 finding 一个文件**。

- `NNN` 从 `001` 开始，3 位 zero-padded，已有则接续
- 子文件夹 = 命名空间，避免和其他 specialist 撞号
- 路径如不存在请创建（mkdir -p）

```markdown
---
finding_id: 001
specialist: calibration
severity: medium
affected_directions: [range_structure, quantile_shape_signals]
touches_lessons: true
batches_referenced: [batch_043, batch_044]
suggested_threshold_change:
  key: error_kill.mono_is_min
  current_value: null                   # not currently enforced
  proposed_value: 0.6
  rationale: "防 IS→OOS 异常放大非稳健机制——见证据"
  candidates_affected_retro: [batch_043/C004, batch_044/C005]
---

# calibration/001 · 阈值校准加 mono_is ≥ 0.6 第五要件

## 证据

batch_043 C004 出现 4 个 error-kill 指标全过（max_corr=0.117 / 
incr_ic=+0.014 / mono_oos=+1.00 / cum_mdd=-2.01 最浅）但 mono_is=0.30 弱 →
阈值校准诊断为"非真错杀"。batch_044 C005 类似 pattern。

若加 `mono_is ≥ 0.6` 第五要件：两个候选直接排除出"真错杀"池，不再浪费
校准讨论成本。

## 实现建议

- `config.yaml.thresholds.error_kill.mono_is_min: 0.6`
- `lessons.md#Threshold Calibration` 更新"真错杀 5 要件"表
```

## 识别启发

- **重复的"非真错杀"诊断**：同一形态（如 IS→OOS 异常放大）反复出现 → 提议阈值收紧
- **重复的"潜在错杀"flag**：subagent 多次 flag "potential over-rejection" + 统计显示假阳性 → 提议某档放宽
- **库空间 max_corr 阈值**：若 admitted 库在某区间密集，`near_duplicate` 阈值可能过松/过紧
- **`config.yaml.thresholds` / `rubric 档位` / `error_kill 4/5 要件` 三层都是合法目标**

## severity 判据

- `high`：阈值 mis-calibration 导致 ≥5 个候选 retro 翻转
- `medium`：2-4 个 retro 翻转
- `low`：1 个或仅推测性

## 返回给 orchestrator

```
# calibration summary
findings_written: 1
- F006 medium: 加 mono_is ≥ 0.6 第五要件 (2 retro affect)
proposed_threshold_keys: [error_kill.mono_is_min]
```

## 纪律

- **提案必须有 retro 证据**：`candidates_affected_retro` 列出哪些历史候选会因此改判——没有证据的提案 = 噪声
- **不直接改 config.yaml**——finding 是建议，人工 review 后决定
- **不重复 pattern_analyst**：不报失败律；只报阈值
- **不重复 hypothesis_promoter**：不升格 narrative；只升格阈值
