---
name: consolidate-hypothesis-promoter
description: Phase 5 Distillation Specialist — 扫所有 direction 找 dead/saturated 方向中值得升格到 lessons.md 的元教训，产出 findings/hypothesis_promoter/{NNN}.md
user_invocable: false
---

# /consolidate-hypothesis-promoter — Hypothesis → Lessons 升格（subagent）

**本 skill 在 subagent 独立 context 中跑**，Phase 5 4 specialist 之一。职责：扫 **dead / saturated** 方向的 hypothesis + narrative log，找出**可迁移到未来方向的元教训**——在 lessons.md 里升格为系统级事实。

## 输入

Read `storage/vault/_consolidation/packet_specialist_hypothesis_promoter.md` 全文——含所有 direction md body。

## 输出

写到本 specialist 自己的子文件夹：`storage/vault/_consolidation/findings/hypothesis_promoter/{NNN}.md`，**一个 finding 一个文件**。

- `NNN` 从 `001` 开始，3 位 zero-padded，已有则接续
- 子文件夹 = 命名空间，避免和其他 specialist 撞号
- 路径如不存在请创建（mkdir -p）

```markdown
---
finding_id: 001
specialist: hypothesis_promoter
severity: high
affected_directions: [return_distribution_signals, asymmetric_momentum, vol_shock_signals]
touches_lessons: true
batches_referenced: [batch_012, batch_018, batch_023]
suggested_lesson_text: |
  sign-conditional daily return 拆分在日频自然放大 regime 敏感度——
  无条件聚合（如 F010）更稳。证据：return_distribution_signals /
  asymmetric_momentum / vol_shock_signals 三个 dead 方向都在这一点撞墙。
promotes_from_directions: [return_distribution_signals, asymmetric_momentum]
suggests_direction_status_change:
  return_distribution_signals: dead → archived   # 经验已升格，方向可归档
---

# hypothesis_promoter/001 · Sign-conditional return 拆分放大 regime 敏感度

## 该升格的 narrative 元素

- `return_distribution_signals` Hypothesis 的 ⚠️ 证伪段
- `asymmetric_momentum` narrative batch_018 结论
- `vol_shock_signals` T002 DISPROVEN 结论

## 建议 lessons.md 位置

放在 `## Structural Constraints` 段末尾，紧接 "magnitude-based vol shock" 条目。

## 该 finding 触及的 direction

...
```

## 识别启发

- **dead / saturated 方向的 hypothesis 段**：被 ⚠️ 证伪且含 "元教训" 字段
- **反复出现在 narrative log 的经验**：≥2 方向的 narrative 转折点引用同一观察 → 可升格
- **与 pattern_analyst 的差异**：pattern_analyst 找"正在形成中"的失败律；本 skill 找"已证伪方向里沉淀出的元教训"——前者**还没写进 direction 的 Hypothesis ⚠️**，后者**已经写进去**但分散在多方向里

## severity 判据

- `high`：≥2 dead 方向独立得出同一元教训
- `medium`：1 方向的元教训，但普适性强（跨字段 / 跨时间尺度）
- `low`：单次、范围有限

## `suggests_direction_status_change`（可选字段）

若经验已充分升格到 lessons，原方向可归档（`dead → archived`，不再出现在 snapshot / INDEX 的活跃列表中）。是否归档由后续人工 / orchestrator 决定——本 finding 只给建议。

## 返回给 orchestrator

```
# hypothesis_promoter summary
findings_written: 2
- F007 high: sign-conditional return 拆分元教训 (3 dead dirs)
- F008 medium: PE/PB/PS 纯变化率无独立 alpha (1 dir)
archival_suggestions: [return_distribution_signals, asymmetric_momentum]
```

## 纪律

- **只处理 dead / saturated 方向**（active / productive / exploring 不碰——它们还在变化）
- **不重写 direction body**——本 skill 只产 finding；direction writer 做 rewrite
- **suggested_lesson_text 必须是成品措辞**（lessons writer 可直接粘）
- **不与 pattern_analyst 抢活**：区分"现象识别"（pattern）vs "升格建议"（promoter）
