---
name: pattern-scout
description: 跨批模式侦察 subagent——扫最近 N 批 judge 摘录，识别重复失败律 / style 吸收律 / 机制同构，直接更新 INDEX.md 的 HOT-TOPICS-LLM 块
user_invocable: false
---

# /pattern-scout — 跨批模式侦察（subagent entry）

**本 skill 只在 subagent 独立 context 中跑**，由 `/factor-mine` orchestrator 在 Phase 0 通过 `Agent(subagent_type=general-purpose)` 调用。职责：看过去 10 批的"方向级反思"和"跨候选对比"找出正在形成的系统级 pattern，并直接改写 `storage/vault/INDEX.md` 的 `HOT-TOPICS-LLM` 块——这样主 agent 启动只读 INDEX 顶部就能看到"连续 4 批因同一 vol_20d 律失败"。

## 工作流

### Step 1 — 让 Python 准备数据

调用：

```bash
PYTHONPATH=src python3 -m research pattern-scout --recent 10
```

Python 会覆盖写一份 `storage/vault/_meta/pattern_scout_packet.md`（400-600 行），包含：
- 任务描述 + 输出契约
- 识别启发（vol_20d 吸收 / magnitude 共线 / 近邻饱和 等）
- Active directions frontmatter 表
- 最近 10 批的 judge.md 关键段（方向级反思 / 跨候选对比 / Thread 进展）逐批摘录

### Step 2 — Read packet 并分析

`Read storage/vault/_meta/pattern_scout_packet.md` 全文。然后按识别启发扫：

1. **同一 `dominant_style` 反复出现**：≥3 批 + 跨 ≥2 方向 → confidence=high
2. **同一 rejection 形态重复**：magnitude / ratio / power-mean 等反复撞墙 → confidence=medium+
3. **直系 cross-direction fallacy**：某方向的 zero-admit 可以用另一方向已证伪的同族理由解释 → confidence=medium
4. **max_corr 饱和**：多批 hard-gate `max_corr` 命中同一 F{id} → 库空间该位置饱和

每个 pattern 的 confidence 分级：
- `high`：≥3 批独立确认 + 跨 ≥2 方向
- `medium`：≥2 批确认，或 1 批但机制清晰
- `low`：仅 1 批出现但具强预测性

### Step 3 — 改写 `INDEX.md` 的 `HOT-TOPICS-LLM` 块

只允许替换以下 sentinel 内的内容：

```markdown
<!-- BEGIN HOT-TOPICS-LLM -->
> [!warning]+ 🔥 Hot Topics（LLM 维护）
> - 🔴 **P001 vol_20d 吸收 2nd-moment 空间** · dirs: stochastic_position, range_structure → 避免 magnitude/ratio/power-mean
>   evidence: [[batches/batch_041/judge|batch_041]], [[batches/batch_044/judge|batch_044]]
<!-- END HOT-TOPICS-LLM -->
```

约束：最多 5 条 topic；每条包含 id / confidence icon / title / affected directions / action_hint / 1-2 个证据 wikilink。若无 active topic，保留 sentinel，写一行"当前无活跃跨批模式"。

## 返回给 orchestrator

**不是整份 INDEX.md**，而是 ≤10 行的 structured summary：

```
# pattern-scout summary
patterns_detected: 3
- P001 high: vol_20d 吸收 2nd-moment  · dirs=4
- P002 medium: A 股 10% 涨跌幅约束 · dirs=2
- P003 medium: error-kill 四件套不足 · dirs=2
new_since_last_scan: [P003]
removed_since_last_scan: []
key_takeaway: "本次新发现 mono_is 硬下界建议，其他两条仍是已知痛点"
```

## 约束 / 纪律

- **只改 `storage/vault/INDEX.md` 的 `HOT-TOPICS-LLM` sentinel 块**（+ 允许 Read packet / judge.md / direction.md 作为验证）
- **禁止改 INDEX frontmatter / COCKPIT / INSIGHT / Bases embeds / 其它 sentinel**
- **不改 judge.md / direction.md / lessons.md**——那些是各自 owner 的职责
- **不跑 Bash 做计算**——仅允许读文件；若 Python 的 packet 缺数据，bubble 给 orchestrator 不自己补
- **confidence 宁可保守**：`high` 是指"已经明确到可以写进 lessons"级别；一批事件不够
- **pattern id 稳定**：若上次 INDEX hot-topics 块已有 P001 标题相同，保留 id（id 一致性便于主 agent 关联）

## 失败处理

- packet 文件不存在 / 空 → bubble 错误给 orchestrator，不自建 dummy topic
- 读到异常 judge.md（frontmatter 破损）→ 跳过该批，在 body narrative 里标记"batch_XXX 数据损坏"
- 没有任何 pattern 达到 confidence ≥ low → 保留 sentinel，写"当前无活跃跨批模式"
