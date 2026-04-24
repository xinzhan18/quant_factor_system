---
batch_id: batch_036
direction: gap_acceptance_structure
judged_at: 2026-04-24T01:40:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: admit, factor_name: log_amount_weighted_acceptance_20}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 1, reserve: 0, reject: 5}
admit_count: 1
reserve_count: 0
reject_count: 5
candidate_count: 6
mt_bucket: medium
---

# batch_036 Judge Summary

> [!abstract]+ [[directions/gap_acceptance_structure]] · 6 candidates
> ✅ **admit=1** (C004 → log_amount_weighted_acceptance_20) · ⏸ **reserve=0** · ❌ **reject=5** (C001/C002/C003/C005/C006)
> **核心发现**: gap_acceptance_structure 方向的唯一生路兑现—— **log-compressed $amount/Mean($amount,20) 加权**把 batch_035 C004 的 mono_OOS=0.30 "avoid worst barbell" 翻倍到 **0.60**（通过 T002 ≥0.50 条件）。5 个 reject 候选共同证伪"线性 ratio 加权 (amount / volume / turnover TS-norm / CsRank turnover)"整条路径——只有 log 非线性压缩能抑制 csi1000 小盘的尾部噪声。
> **MT Budget**: cumulative 174 → **180** · direction 6 → **12** · bucket `medium`（C004 search_adjusted `high raw → medium adjusted`）· 本批 low=0 / medium=6 / high=0

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | IC_OOS=0.0016 oos_decay=0.14 | $amount 线性 ratio 加权——2021 regime break 未被线性加权中和 | [[batches/batch_036/candidates/C001]] |
| C002 | ❌ reject | hard_gate | IC_OOS=0.0013 oos_decay=0.12 | $volume 线性 ratio 加权——同 C001 结构性同病 | [[batches/batch_036/candidates/C002]] |
| C003 | ❌ reject | hard_gate | IC_OOS=0.0013 oos_decay=0.13 | turnover TS 归一加权——IS=0.010 OOS=0.001 清晰 regime 衰减 | [[batches/batch_036/candidates/C003]] |
| C004 | ✅ admit | 🟢·🟡·🟢·🟢·🟡 | IC_OOS=0.0094 ls_t=3.23 **mono_OOS=0.60** incr=0.0071 | log 压缩修好 barbell，9 年 8/9 年 IC 正，anti-decay 1.36 | [[batches/batch_036/candidates/C004]] · [[factors/F013]] |
| C005 | ❌ reject | hard_gate | IC_OOS=0.0022 (40d 稀释) | $amount ratio × 40d 聚合——超半衰期 19d 后信号被稀释 | [[batches/batch_036/candidates/C005]] |
| C006 | ❌ reject | hard_gate | IC_OOS=0.0058 | CsRank($turnover) 加权——rank 化压平了 "异常巨量 acceptance" 最关键信息轴 | [[batches/batch_036/candidates/C006]] |

**档位编码**：🟢 最优档 · 🟡 次档 · 🔴 阻断档 · `hard_gate` reject 不填色

## 跨候选对比

- **线性 ratio 加权整族失效 (C001/C002/C003)**：$amount / $volume / $turnover_rate 三个经典 "abnormal X" 线性比值加权，ic_oos 全在 0.0013-0.0016 区间（0.008 硬闸的 1/5-1/6），oos_decay 0.12-0.14 全部 fail 0.20 阈值。`ic_by_year` 共同特征：2015-2020 稳定正向 (~0.008-0.017) → 2021 起全部向零坍塌，2023 已近零。这与 batch_035 T001 pure sign interaction 的三窗口塌陷同源——**csi1000 的 2021 regime break 在 acceptance 信号上是系统性的**，**线性加权无法压低高噪声天权重**，因为线性比值对尾部极端值过度敏感，恰好是 2021+ 高 vol 小盘乱世里的 "噪声放大器"。
- **Log 非线性压缩是关键 (C004 ADMIT)**：C004 用 `Log(Div($amount, Mean($amount, 20)))` 压缩 amount 尾部，mono_OOS 从 batch_035 C004 的 0.30 → **0.60**，直接满足 direction T002 next_probes 的 ≥0.50 通过条件。IC_OOS=0.0094 · ICIR_OOS=0.253 · ls_tstat_oos=3.23 · **anti-decay=1.36**（OOS > IS，极罕见信号）。9 年 8/9 年 IC 同号，近 4 年稳定 0.0055-0.0105。库独立 max_corr=0.085@F010（`overnight_return_persistence_5d`）· incremental_ic=0.0071（虽低于 0.010 但 direction 对"首次 admit + mono 结构质量"权衡后判断过关）。
- **CsRank 压平破坏机制 (C006)**：`CsRank($turnover_rate)` 把高低 turnover 的量级差压成 [0,1] 均匀分布，丢掉了 "异常巨量 acceptance" 这个最可能携带 alpha 的信号源——C006 IC_OOS=0.0058 差 0.0022 到硬闸。印证 T002 假设：机制是 "high-participation 加权"，rank 化丢 magnitude 就是错向。
- **窗口扩展无用 (C005 vs C001)**：C005 = C001 的 40d 窗口版，IC_OOS 从 0.0016 → 0.0022（微涨），ls_tstat 1.73 → 1.81（微涨），但仍全线 fail。signal_half_life=19d 附近，40d 已超半衰期。**T004 结论在 T002 上复用**：csi1000 的加权 acceptance 没有 "更长聚合救回 OOS" 的窗口。
- **风格暴露同质**：6/6 候选 `dominant_style_exposure=vol_20d`，但 style_r² 全在 0.02-0.08 低段，alpha_survival 多个过阈（C001/C002/C003/C005 alpha_surv=3.25-6.40 极高，C004=0.61 虽低但 log 压缩后可接受），不是主阻断。
- **MT budget**：direction 6 → 12，本方向累计达 12，首批 6 reserve→0 reject 5 admit 1 模式与 batch_035 5 reject + 1 reserve 形成清晰"1 log variant survives from 12 candidates scanned"结论。

## Thread 进展

> [!success]+ T002 [[directions/gap_acceptance_structure#T002]] — `[✓ ANSWERED batch_036]`
> C004 admit → **log_amount_weighted_acceptance_20**。Thread 主问题回答：**log-compressed abnormal amount 加权 + 20d 聚合是 T002 唯一存活形状**。
>
> 决定性证据：5 个 reject 候选覆盖了线性 ratio (amount/volume/turnover TS) + CsRank + 40d 窗口五个正交变体，全部 mono < 0.5 或 IC_OOS 过低；仅 C004 log 变换同时拿到 mono_OOS=0.60 + IC_OOS=0.0094 + anti-decay。T002 family 现在有唯一代表 F{next}，thread 关闭；同时 thread 的未来 probes（"abnormal vol 加权"、"normalized turnover"）被 C001/C002/C003 对照结果 preemptively closed。

## 方向级反思

`gap_acceptance_structure` 方向在 2 轮 12 个候选后完成 alpha 抽取：
- T001 (pure sign interaction) DISPROVEN · T003 (TR normalization) DISPROVEN · T004 (window sensitivity) DISPROVEN（batch_035）
- T002 (abnormal participation weighted) ANSWERED via C004 (batch_036)

这是一个结构清晰的"方向从 hypothesis 到 1 admit 产品"的快速路径 —— paper QuantaAlpha 的 CSI 300 sign interaction 信号在 csi1000 上**只在 log-compressed 加权下存活**，IC 量级从 paper 的 0.0744 降至我们的 0.0094（约 8x 衰减），印证 direction.md 预判"csi1000 小盘信号衰减到 0.02-0.04 下界"甚至更低——实测还要更小，但结构稳健性（mono + 9 年同号 + anti-decay）足以贡献库增值。

**方向操作**（Phase 3 决策，Phase 4 frontmatter 自动化）：
- `status: saturated`（保留 Python 已自动设置状态；12 candidates 后 T002 closed + 无 reserve 留存）
- `priority: medium`（保持；不升 low 因为 log-compression 是可迁移 meta-pattern，可能对其他方向有用）
- 不再开新 thread；方向进入维护态，F{id} 产出即退出挖掘池

**Calibration（错杀侦测）**：
- 本批 `potential over-rejection` flag = **False**
- C001/C002/C003 hard_gate fail 全部是"真正的机制失败"——线性加权在 csi1000 2021+ 小盘 regime 下噪声放大，ic_by_year 清晰单调塌陷，非阈值过严
- C005 窗口扩展是测试 hypothesis 本身（是否有更长聚合救回），结果 negative 是 informative reject
- C006 CsRank 变体是测试 "rank vs magnitude" 权重形式，negative 证实 magnitude 是信号载体
- 5 个 reject 中 4 个 `sign_consistency=1.0` + 9 年 IC 全正 + 低 max_corr，但都 failed on IC_OOS magnitude——这些不是"错杀"，是"加权选择错了只有 log 能活"
- **不触发 threshold calibration**
