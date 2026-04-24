---
name: consolidate-pattern-analyst
description: Phase 5 Distillation Specialist — 扫最近 judge.md + 所有 direction 找跨方向模式（同一 dominant_style 吸收律 / 同构失败机制），产出 findings/F{NNN}.md
user_invocable: false
---

# /consolidate-pattern-analyst — 跨方向 pattern distillation（subagent）

**本 skill 在 subagent 独立 context 中跑**，由 Phase 5 两阶段 orchestrator 并行 dispatch（4 个 specialist 之一）。职责：从最近 judge + 所有 direction 里找**跨方向反复出现的失败律**——比"单方向 narrative 压缩"高一阶的抽象。

## 输入

Read `storage/vault/_consolidation/packet_specialist_pattern_analyst.md` 全文——含：
- Task 描述 + frontmatter 契约
- 最近 N 批 judge.md 全文（concat）
- 所有 direction md 全文（concat）

## 输出

把发现写成 `storage/vault/_consolidation/findings/F{NNN}.md`，**一个 finding 一个文件**（`NNN` 从 001 递增，若已有占用则接续）。每个文件：

```markdown
---
finding_id: F001
specialist: pattern_analyst
severity: high | medium | low
affected_directions: [stochastic_position, vwap_proxy_signals, range_structure, quantile_shape_signals]
touches_lessons: true
batches_referenced: [batch_041, batch_042, batch_043, batch_044]
suggested_lesson_text: |
  csi1000 daily-bar 的 2nd-moment 空间被 Barra vol_20d 结构性占据。
  任何 magnitude / ratio / power-mean / quantile-robust 形态都会被吸收。
  逃离路径仅二：(a) Python 残差化工具链 orthogonalize；(b) 非 daily-bar 数据。
---

# F001 · vol_20d 吸收 2nd-moment 空间

## Pattern（1 段描述）

...

## 证据链

- [[batches/batch_041/judge|batch_041]] stochastic_position：...
- [[batches/batch_043/judge|batch_043]] range_structure：...
- [[batches/batch_044/judge|batch_044]] quantile_shape_signals：...

## 建议的 direction 操作

- {affected_directions 每个}：Narrative Log 加 ⚠️，引用本 finding
```

## 识别启发

1. **同一 `dominant_style` 反复出现**：≥3 批 + 跨 ≥2 方向 → `severity: high`
2. **同一 rejection 形态**：magnitude / ratio / Skew / Quantile 差 反复撞墙 → `severity: medium+`
3. **横向相关**：一个方向的 zero-admit 可由另一方向已证伪的同族理由解释 → `severity: medium`
4. **max_corr 饱和**：多批 hard-gate max_corr 命中同一 F{id} → 库空间该位置饱和

## severity / touches_lessons 判据

- `severity=high`：≥3 批独立确认 + 跨 ≥2 方向 + 建议 lessons 升格（`touches_lessons: true`）
- `severity=medium`：≥2 批确认，或 1 批但机制清晰；是否 lessons 升格看是否跨方向适用
- `severity=low`：提示性发现，通常 `touches_lessons: false`

## 返回给 orchestrator

≤10 行 summary：

```
# pattern_analyst summary
findings_written: 3
- F001 high: vol_20d 吸收 2nd-moment (4 dirs)
- F002 medium: A 股 10% 涨跌幅使 range 共动 prev_close (2 dirs)
- F003 medium: error-kill 四件套不足 (2 dirs)
```

## 纪律

- **只写 `_consolidation/findings/F*.md`**；不改 direction / lessons / INDEX
- **不跑 Bash / Python 计算**
- **finding_id 从 F001 递增**，若 findings/ 已有文件则接续最大号
- **suggested_lesson_text 写"可直接粘进 lessons"的成品措辞**，不是"请 lessons writer 自己想"
- **affected_directions 要具体**，空 list 不合法（无方向 = 无跨方向 pattern）
