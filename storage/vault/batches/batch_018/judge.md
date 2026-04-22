---
batch_id: batch_018
direction: ohlc_temporal_aggregation
judged_at: 2026-04-21T02:55:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: admit, factor_name: open_position_persistence_5d}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
batch_summary: {total: 5, admit: 1, reserve: 0, reject: 4}
admit_count: 1
reject_count: 4
reserve_count: 0
candidate_count: 5
mt_bucket: medium
---

# batch_018 Judge Summary

> [!abstract]+ batch_018 · [[directions/ohlc_temporal_aggregation]] · 5 candidates
> ✅ **admit=1** (C003 → open_position_persistence_5d) · ⏸ **reserve=0** · ❌ **reject=4** (C001 C002 C004 C005)
> **核心发现**: **方向连续两批 admit** —— C003 open-position 5d (ic=+0.037 ls_t=3.22 mono=+0.90 alpha_surv=0.637 incr_ic=+0.023 cum_dd=-1.5) 与 F006 (upper-shadow) 机制正交（max_corr=0.276）。**OHLC 5d aggregation 在开盘+收盘两端独立载 alpha**。C001 lower-shadow corr=1.000 与 F006 algebraic 等价（reject）；C004 signed-range corr=0.544 与 F006 部分重叠；C005 overnight-gap-magnitude alpha_surv=0.164 暴露另一个 vol-derived pattern。
> **MT Budget**: cumulative 92 → **97** · direction 5 → **10** · bucket `medium` (上界)

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | near_dup F006 corr=1.000 | upper+body+lower=1，algebraic mirror 无独立信息 | [[batches/batch_018/candidates/C001]] |
| C002 | ❌ reject | hard_gate | ic=0.0067<0.008 | 无符号 body magnitude 失去方向性 | [[batches/batch_018/candidates/C002]] |
| C003 | ✅ **admit** | 🟢·🟢·🟢·🟢·🟢 | ic=+0.037 ls_t=3.22 mono=+0.90 alpha_surv=0.637 incr_ic=+0.023 cum_dd=-1.5 | open-position 5d；隔夜信息驱动开盘续涨 momentum | [[batches/batch_018/candidates/C003]] · [[factors/F007]] |
| C004 | ❌ reject | 🟡·🟢·🟡·🔴·🟠 | corr=0.544@F006 incr_ic=-0.039 cum_dd=-103 | signed-range 与 F006 部分重叠 + 库 reducer + 长期失效 | [[batches/batch_018/candidates/C004]] |
| C005 | ❌ reject | 🟡·🟢·🔴·🟢·🟡 | alpha_surv=0.164 incr_ic=-0.003 | gap-magnitude/range 又一个 vol-derived pattern | [[batches/batch_018/candidates/C005]] |

## 跨候选对比

- **方向第二个 admit + 机制正交确认**：C003 open-position 与 F006 upper-shadow max_corr=0.276，机制完全独立——一个测早盘买盘 (open vs day-low)，一个测收盘抛压 (close vs day-high)。**5d OHLC aggregation 在开盘端 + 收盘端独立载 alpha** 确立。
- **Algebraic 镜像 trap (C001)**：lower-shadow 与 upper-shadow 在 5d mean 下 corr=1.000——OHLC 三段 (upper+body+lower=1) 数学约束。**教训**：在已 admit OHLC 因子之后，任何"取相反端点"的 mirror 设计都会触发 near_dup hard_gate。
- **Magnitude vs sign 区分**：C002 (|body|/range) 和 C005 (|gap|/range) 都是无符号 magnitude，IC 都极弱（C002 hard_gate, C005 alpha_surv 0.164）。**OHLC 信号的预测力主要来自方向不是 magnitude**——C003 (signed open位置) + F006 (signed upper-shadow) 都是有方向意义的比值，C002/C005 失败证伪 magnitude-only 路径。
- **Interaction not orthogonal (C004)**：signed-range = body_sign × range/close，与 F006 corr=0.544 medium-high。**signed × magnitude 不产生新信息**——sign 已被 F006 / C003 各自捕捉，乘以 range 主要是放大 vol_20d 暴露。
- **MT 预算**：direction 10 (medium 中段)，cumulative 97。本批 admit 率 20%（vs 方向首批 17%），admit 率稳定。

## Thread 进展

> [!success]+ T003 [[directions/ohlc_temporal_aggregation#T003]] — `[✓ ANSWERED batch_018]`
> open-position 5d (C003) **admit** — 开盘位置维度独立载 alpha，与 close-strength 维度 (F006) 正交。**方向核心 hypothesis "OHLC aggregation 在多个端点都有独立信号" 完整验证**（首端 close 端 F006 + 第二端 open 端 F007）。

> [!note]- T002 [[directions/ohlc_temporal_aggregation#T002]] — `[◉ ACTIVE]`（本批无新进展）
> C003 batch_017 reserve 仍待复核；symmetric pair design 未在本批尝试。

## 方向级反思

batch_018 是 ohlc_temporal_aggregation **第二个 admit**——方向连续 2 批 admit，admit 率 22%（2 admit / 9 candidates）。这是该方向 productive 性的强证据。

**核心元发现**：
1. **OHLC aggregation 双端独立性确立**：open 端（C003 batch_018）+ close 端 (F006 batch_017) 都能独立 admit，且 max_corr=0.276 远低 0.30 阈值——**OHLC pattern 在 5d 窗口下至少有 2 个独立维度**。预期 high-low (range) 端 + body-position 端可能也独立——但本批 C002 (body magnitude) hard_gate fail 已证伪 magnitude 路径。
2. **C001 algebraic mirror trap (新规则)**：upper+body+lower=1 数学约束 → 镜像设计 corr=1.000 → 后续设计应避免直接对 admit 因子取 algebraic complement。
3. **vol-derived pattern 持续暴露**：C005 alpha_surv=0.164 是第 3 个本系列被识别的 vol_20d 镜像（前两个：batch_016 C004 Q90-Q10 / batch_017 C004 close/high）。**alpha_survival<0.20 + cp03 中等 + max_corr<0.30 = "vol-derived monotone" 强 signature**——此判别已稳定。

**Calibration triggers 检查**：
- 错杀 flag = 0 ✓
- 连续零 admit 中止（batch_017+018 连续 admit）✓
- Reserve 积压：cumulative 97 / 累计 reserve ~14 = 14% < 40% ✓
- 悖论复现 = 无 ✓

**下批决策（batch_019）**：
1. **优先**: ohlc_temporal_aggregation 方向第三轮 — 探索 5d 窗口剩余维度：`body position in range` (close vs midpoint)、跨日 body/shadow 一致性、3d/10d 窗口 ablation
2. **次选**: 检查 batch_017 C003 (sign-frequency reserve) 在 batch_019 是否能找 admit 路径
3. **观察**: 第三轮 admit 率是否维持——若 0 admit，方向接近 saturated；若再 1 admit，证明 OHLC 5d 空间至少 3 个独立维度
