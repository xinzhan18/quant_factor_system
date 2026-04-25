---
batch_id: batch_049
direction: overnight_intraday_split
judged_at: 2026-04-25T05:15:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: admit, factor_name: overnight_sign_freq_amount_rank_diff_20}
batch_summary: {total: 6, admit: 1, reserve: 0, reject: 5}
admit_count: 1
reject_count: 5
reserve_count: 0
candidate_count: 6
mt_bucket: high
---

# batch_049 Judge Summary

> [!abstract]+ batch_049 · [[directions/overnight_intraday_split]] · 6 candidates
> ✅ **admit=1** (C006→F{next} `overnight_sign_freq_amount_rank_diff_20`) · ⏸ reserve=0 · ❌ **reject=5** (C001/C002/C004/C005 CP05 high; C003 hard_gate ic_oos_too_low)
> **核心发现**：direction.md hypothesis 复活条件 "overnight sign frequency (方向而非 magnitude)" 首次 ANSWERED——C006 Sign 聚合几何正交于库内 magnitude 聚合 (F009/F010/F011)，成为 rank-diff 范式第 4 次跨家族兑现（batch_046/047 microstructure + batch_048 overnight_turnover + 本批 sign_freq × amount）。tipping point 达到：建议触发 Phase 5 consolidation 升格 lessons.md 通用几何规则。
> **MT Budget**: cumulative 252 → **258** · direction 15 → **21** · bucket `high` (search_adjusted → medium) · 本批 low=0 / med=0 / high=6

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🟡·🟡·🔴·🔴·🟢 | ic_oos=-0.055 max_corr=0.826@F017 incr=-0.012 | L1 Mean\|ret\| rank-diff 被 F017 吸收；扩展 "RHS 共享已入库 rank-diff 一端" 律 | [[batches/batch_049/candidates/C001]] |
| C002 | ❌ reject | 🟡·🟡·🔴·🔴·🟢 | ic_oos=-0.042 max_corr=0.713@F010 incr=-0.006 | pb × overnight rank-diff 被 F010 吸收（RHS=overnight_5 饱和） | [[batches/batch_049/candidates/C002]] |
| C003 | ❌ reject | hard_gate | ic_oos=-0.0069 (差 0.0011) max_corr=0.422 incr=+0.021 | signed×magnitude 异质结构脱离 overnight LHS 后信号强度塌缩，**反向证 overnight >> \|intraday\| signal 强度** | [[batches/batch_049/candidates/C003]] |
| C004 | ❌ reject | 🟡·🟡·🟡·🔴·🟢 | ic_oos=-0.039 max_corr=0.725@F010 incr=+0.004 | volume HHI rank-diff incr 勉强过 0.003 但 <0.005；同批 C006 主导让位 | [[batches/batch_049/candidates/C004]] |
| C005 | ❌ reject | 🟡·🟡·🔴·🔴·🟢 | ic_oos=-0.055 max_corr=0.824@F017 incr=-0.009 | L2 RealizedVol ≈ L1 Mean\|ret\| (csi1000 日频)；同批 AmihudIlliq+RealizedVol 冗余 pair | [[batches/batch_049/candidates/C005]] |
| C006 | ✅ **admit** | 🟢·🟢·🟡·🟡·🟢 | **ic_oos=+0.051 ls_t=+5.98 mono=+1.0 incr=+0.015 9/9yr+** cum_mdd=-1.53 整库最浅 | **命中 hypothesis 文字级复活条件**；rank-diff 第 4 次跨家族兑现 tipping point | [[batches/batch_049/candidates/C006]] · [[factors/F018]] |

**档位编码**：🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档 · `hard_gate` reject 不填色。整列飘红 = 方向级警示。

## 跨候选对比

**共 RHS=overnight_5 饱和证据**（C001/C002/C004/C005 全部 RHS = `Mean(overnight_pct, 5)`）：
- max_corr 都落在 0.71-0.83 区间（F010 或 F017）
- incremental_ic 或负（C001 -0.012, C002 -0.006, C005 -0.009）或勉强过 0.003（C004 +0.004）
- → rank-diff RHS=overnight_5 在当前库状态（F010 overnight persistence + F017 overnight×turnover rank-diff）下**已饱和**，4 候选共占位。

**LHS 多元化失败原因**：cockpit 硬约束"每个候选 LHS 必须不同"在本批被严格执行（Amihud/pb/turnover_cv/HHI/RealizedVol/sign_freq 6 LHS 唯一）——但 **LHS 独立 ≠ admit 独立**，真正决定 admit 的是 **RHS 结构是否共已入库因子**（F010/F017 RHS=overnight_5）。本批 5/6 RHS 共享 overnight_5 → 4 reject + 1 hard_gate fail。

**C006 成功的结构学**：
1. RHS 换成 `Mean($amount, 20)` 流动性 basis（非 overnight_5）→ 绕过 F010/F017 RHS 饱和
2. LHS 换成 `Mean(Sign(overnight), 20)`（sign 聚合而非 magnitude）→ 与 F009/F010/F011 几何正交（不仅数值正交）
3. 文字级命中 direction.md hypothesis 列出的"复活条件"——非随机组合

**L1 vs L2 vol-family 冗余揭示**（C001 vs C005）：
- C001 `Mean(|daily_ret|, 20)` vs C005 `sqrt(Σdaily_ret², 20)` 
- 两者指标几乎完全相同（IC -0.055 / -0.055，max_corr 0.826 / 0.824）
- 说明 **在 csi1000 日频 + 低 kurt 样本下，L1 和 L2 vol 等价**
- 未来不应同批 AmihudIlliq + RealizedVol 组合（浪费候选预算）

**Style 聚合**：6 候选中 4 个 dominant_style=vol_20d（C001/C004/C005/C006），但只有 C001/C005 crowding=high；C004/C006 medium。本方向天然与 vol_20d 暴露相关。

**MT 预算推进**：direction_candidates 15 → 21；bucket 仍 high（search_adjusted medium）——本方向 rank-diff 探测预算接近上限，下轮应暂停 rank-diff 模式改探其它结构。

## Thread 进展

> [!success]+ T008 [[directions/overnight_intraday_split#T008]] 🆕 — `[✓ ANSWERED batch_049]`
> rank-diff 范式第 4 次跨家族兑现——但关键发现不是"admit"本身，而是**RHS 共享饱和律**：当已入库 factors 占据 rank-diff RHS（F010/F017 均 RHS=overnight_5），新候选 LHS 再多元化也会被 RHS 端吸收。C001/C002/C004/C005 四候选 5/6 全共 RHS=overnight_5 全部 reject 证明此律。**rank-diff admit 路径=RHS 换新 basis + LHS 几何正交**（本批 C006 admit = 换 RHS=amount + 换 LHS=sign 聚合）。

> [!failure]+ T009 [[directions/overnight_intraday_split#T009]] 🆕 — `[✗ DISPROVEN batch_049]`
> asymmetric signed×magnitude 异质结构脱离 overnight LHS 后塌缩到 noise——batch_048 C006 reserve 的 signed×magnitude 潜在 alpha 主要来自 overnight LHS 端，而非 signed×magnitude 函数形式本身。反向证据：overnight signal 强度 >> |intraday| signal 强度。

> [!success]+ T010 [[directions/overnight_intraday_split#T010]] 🆕 — `[✓ ANSWERED batch_049]`
> direction.md Hypothesis 复活条件 "(c) overnight sign frequency（方向而非 magnitude）" 首次 ANSWERED——C006 Mean(Sign(overnight),20) rank vs amount rank-diff = ic_oos=+0.051 ls_t=+5.98 mono=+1.0 incr=+0.015，cum_ic_mdd=-1.53 整库最浅级别 + 9/9 年全正 + 近年最强。证明 **sign 聚合与 magnitude 聚合几何正交**——F010 overnight_magnitude_5d 相关仅 0.37。

> [!note]- T005 [[directions/overnight_intraday_split#T005]] — `[◉ ACTIVE]`（本批 partial-answered → 继续 active）
> rank-diff 跨 direction 泛化仍 ACTIVE。本批 C001/C002/C004/C005 rank-diff 跨 direction 尝试全 reject（RHS=overnight_5 饱和），但 C006 用 sign 聚合 + amount RHS 达成第二种跨 direction 路径。T005 下一步：避开 RHS=overnight_5，转攻 sign 聚合 × 其它 basis。

## 方向级反思

本方向的 edge 结构进一步清晰：

**已确认饱和的 rank-diff 子空间**：
- RHS=overnight_5 + 任意 LHS（4 候选证据，F010/F017 双占位）
- 同字段跨窗口 rank-diff（batch_048 C005 DISPROVEN）
- signed×magnitude 异质结构脱离 overnight LHS（本批 C003 DISPROVEN）

**仍开放的 rank-diff 子空间**：
- sign 聚合 × 非 overnight RHS（C006 admit 首探，下一步泛化）
- overnight 长 horizon（20d+）sign_freq 是否 escape 5d magnitude
- overnight × intraday 非线性交互（hypothesis 复活条件 (c) 第二条，尚未探测）

**方向状态**：productive（连续 2 批 admit，batch_048 F017 + batch_049 F{new}——**5 slot 达到**）。下轮若 sign 聚合范式再 admit 则方向 status→可能重新定位为 **high-yield** 重点；若 reject 则 saturated。

**Library 健康度**：overnight_intraday_split = 5/(17+1) ≈ 28%（本批 admit 后），已成库最大方向。需警觉方向内冗余 —— C006 max_corr@F017 = 0.427 属可接受（<0.70）。

**T008 rank-diff tipping point**：
- batch_046/047 microstructure 内部 2 admit（F015/F016）
- batch_048 overnight_turnover 1 admit（F017）
- batch_049 本批 sign_freq × amount 1 admit（C006→F{new}）
- **4 次跨家族兑现**达到 consolidation 触发阈值 → 建议 Phase 5 升格 lessons.md 新 section "rank-diff geometry"

**下一轮 direction-specific next_step**：
1. 避开 RHS=overnight_5 rank-diff（饱和证明）
2. 测试 sign_freq × 其它 basis（turnover / pb / volume）泛化 T010
3. 测试 overnight × intraday **非线性交互**（hypothesis 复活条件 (c) 第二条，如 `overnight_5 * Sign(intraday_5)` 或 `overnight_5 * TsRank(intraday_magnitude, 20)`）
