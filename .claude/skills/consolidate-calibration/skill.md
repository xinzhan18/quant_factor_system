---
name: consolidate-calibration
description: Phase 5 Distillation Specialist — (A) 扫最近 judge.md 提阈值调整建议 + (B) 全 reserve pool retro triage 提复活路径；产出 findings/calibration/{NNN}.md
user_invocable: false
---

# /consolidate-calibration — 阈值调整 + reserve 复活路径 distillation（subagent）

**本 skill 在 subagent 独立 context 中跑**，Phase 5 4 specialist 之一。职责双轨：
- **(A) Trigger-driven**: 从最近判决轨迹里提出**有证据的阈值提案**——哪条 config.yaml 阈值该调到哪个值，有多少历史 reserve 会因此翻转。
- **(B) Asset-driven**: 扫**全部历史 reserve pool**，识别**单边缘卡的潜在错杀**——4+ CP 顶级仅 1 个边缘阈值阻断的候选，提**复活路径建议**（不调阈值，改 RHS basis / Python residualize / 窗口扫等）。

**两条轨道都必须各产至少 1 个 finding**——asset-driven 路径补足了 trigger-driven 视角的盲区（trigger 要全条件双立才立，单边缘卡永远漏）。

## 输入

Read `storage/vault/_consolidation/packet_specialist_calibration.md` 全文——含：
- Task 描述
- 最近 N 批 judge.md 全文（关注 `## 阈值校准诊断` + `reserve_audit` 段）—— **(A) 用**
- **`## Reserve Pool Retro Audit` 段**：全部历史 reserve 在当前 config 下的重判结果（`research audit reserves` 输出）—— **(B) 用**

## 输出

写到本 specialist 自己的子文件夹：`storage/vault/_consolidation/findings/calibration/{NNN}.md`，**一个 finding 一个文件**。

- `NNN` 从 `001` 开始，3 位 zero-padded，已有则接续
- 子文件夹 = 命名空间，避免和其他 specialist 撞号
- 路径如不存在请创建（mkdir -p）

**(A) Trigger-driven schema（阈值提案）**：

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

**(B) Asset-driven schema（reserve 复活路径）**：

```markdown
---
finding_id: 007
specialist: calibration
severity: high                           # 反映可复活候选数量
affected_directions: [tsrank_candlestick_ratio, institutional_flow_proxy]
touches_lessons: false                   # 复活路径不动 lessons，除非伴生 family-aware 阈值改动
batches_referenced: [batch_072, batch_076]
revival_recommendations:
  - candidate: batch_076/C005
    expression: "TsRank(Div(Mul(Add($high,$low),0.5), $close), 60)"
    blocking_threshold: max_corr=0.45@F008
    cp_top_metrics: [alpha_surv=1.43 (顶级), incr_ic=+0.042 (强POS), mono=+0.90, ls_t=+4.84]
    suggested_revival_path: |
      改 RHS basis: 当前 atom is midprice/close (LHS family) — F008 是 Mean
      upper_shadow_3d (不同 LHS family). 建议加 Python wrapper residualize
      (atom, [F008_values, vol_20d, log_market_cap]) 后再走 CP05; 或者
      改原表达式 RHS = `Add($high,$low)/(2*Mean($close,5))` 让 LHS atom
      在 Mean(close,5) 上去掉趋势成分.
    expected_outcome: "max_corr 应降至 <0.30, alpha_surv 不变, admit"
  - candidate: batch_072/C006
    expression: "TsRank(Div($amount, $num_trades), 60)"
    blocking_threshold: incr_ic=-0.018
    cp_top_metrics: [ls_t=-7.54 (整库顶级), mono=-1.00 PERFECT, max_corr=0.24]
    suggested_revival_path: |
      window sweep 30d/120d 看 incr_ic 是否 POS 化; 或 rank-diff form
      `Sub(CsRank(TsRank(amount/num_trades,60)), CsRank(F009))` 测 reducer
      reverse.
    expected_outcome: "至少一个 window 应实证 incr_ic ≥ +0.005"
---

# calibration/007 · Asset-driven reserve pool 复活池 (round NN)

## 证据

`research audit reserves` 全量扫出 51 flip-candidate / 80 reserve. 其中
4+ CP 顶级仅 1 边缘卡的强候选 5 个（trigger #2 都不立——因要求全条件双
立）：

[列出每个候选 + 关键指标 + 卡位 + 复活路径]

## 为什么 trigger-driven 漏掉

trigger #2 要求 `max_corr<0.30 + incr_ic>+0.010 + alpha_surv≥0.40 +
sign-stable` 全立才算"错杀火种"。本批 5 候选每个都有 1 个边缘卡——
单边缘永远 trigger 不到，必须 asset-driven 显化。

## 复活路径汇总

[每个候选给出具体的 revival_path——不调阈值，改表达式 / 加 Python
wrapper / 改窗口]

## 实现建议

- 下批 /factor-batch 时，把 5 个 revival_path 作为 candidate hint
- **不动 config.yaml** — 复活靠改表达式不靠改阈值
```

**新 frontmatter 字段**：
- `revival_recommendations`: list（asset-driven finding 必有）—— 每项含 candidate / expression / blocking_threshold / cp_top_metrics / suggested_revival_path / expected_outcome
- `suggested_threshold_change`: 与 (A) 同（trigger-driven finding 必有；asset-driven 通常无）

## 识别启发

### (A) Trigger-driven（阈值提案）

- **重复的"非真错杀"诊断**：同一形态（如 IS→OOS 异常放大）反复出现 → 提议阈值收紧
- **重复的"潜在错杀"flag**：subagent 多次 flag "potential over-rejection" + 统计显示假阳性 → 提议某档放宽
- **库空间 max_corr 阈值**：若 admitted 库在某区间密集，`near_duplicate` 阈值可能过松/过紧
- **`config.yaml.thresholds` / `rubric 档位` / `error_kill 4/5 要件` 三层都是合法目标**

### (B) Asset-driven（reserve pool retro triage）

扫 `## Reserve Pool Retro Audit` 段（`research audit reserves` 全量输出）。重点关注：

- **`re-judge` flip-candidate 行 + flags 含 `ic_oos_clean` + `mono_strong`**：这是首批"潜在错杀"池
- **单边缘卡的强候选**：4+ CP 顶级（如 ls_t≥6 + mono≥0.85 + alpha_surv≥0.40 + sign-stable）但仅 1 个边缘阈值（如 incr_ic NEG / max_corr 0.40-0.50 / alpha_surv 0.30-0.40 borderline）阻断的候选 → trigger-driven 永远漏掉，必须 asset-driven 显化
- **lessons codify 之后的 legacy reserves**：早期批次（如 batches_001-046）alpha_surv borderline 但当前 floor 已下调（如 rank_diff_geometry=0.30）后变 PASS 的候选 → 应建议 retro re-judge
- **Family-aware 阈值演化**：若某 family（如 TsRank-quantization）admit 后续 reserve 全部 max_corr≥0.40 且 LHS atom 独立 → 提议 family-aware `max_corr_prefer_line` 分档
- **反向相关 = 互补不重复**：`max_corr` 绝对值过 0.30 但**符号为负**（如 -0.69@F020）= 反向耦合 = 互补，不应被 max_corr 单调判据 reject

asset-driven finding 的 `suggested_revival_path` 字段必须**具体且可执行**：
- "改 RHS basis from `Mean(turnover_rate,20)` to `Mean($num_trades,60)`"
- "Python residualize on F008 (vol_20d, log market_cap)"
- "window sweep 30d/120d, 检测是否 incr_ic POS 化"
- "rank-diff form: `Sub(CsRank(原 atom), CsRank(...))`"

## severity 判据

- `high`：阈值 mis-calibration 导致 ≥5 个候选 retro 翻转，**或** asset-driven 复活池含 ≥3 个 4+CP 顶级单边缘卡
- `medium`：2-4 个 retro 翻转，**或** 1-2 个 asset-driven 复活推荐
- `low`：1 个或仅推测性

## 返回给 orchestrator

```
# calibration summary
findings_written: 2
- 006 medium (trigger-driven): CP02 alpha_survival 配 ic_by_year 后期同号
- 007 high (asset-driven): reserve 复活池 5 候选, 含 b076/C005 b072/C006
  proposed_threshold_keys: []
  revival_recommendations: 5 candidates, 0 阈值改动
```

## 纪律

- **(A) trigger-driven 提案必须有 retro 证据**：`candidates_affected_retro` 列出哪些历史候选会因此改判——没有证据的提案 = 噪声
- **(B) asset-driven 复活推荐必须给具体 revival_path**：不能写"建议复活"——必须写"改 RHS basis from X to Y" / "Python residualize on F008" / "window 30d sweep"
- **不直接改 config.yaml** / **不直接改候选表达式**——finding 是建议，下批 /factor-batch 在人工 review 后才执行
- **不重复 pattern_analyst**：不报失败律；只报阈值 + 复活路径
- **不重复 hypothesis_promoter**：不升格 narrative；只升格阈值或复活池
- **必出至少一个 asset-driven finding**：即使 reserve pool retro 全部判 still-reserve / drop，也必须显式产出"reserve 池真饱和"的 finding 说明无可复活——asset-driven 视角不能因结论是 null 而省略
- **family-aware 阈值边界判定**：若同一 family（如 TsRank-quantization）跨多批 reserve max_corr 集中在 0.40-0.50 + 它们 LHS atom 各异 → 这是真 family 边界证据，应升格 (A) 阈值提案；不要简单当作 (B) 复活推荐
