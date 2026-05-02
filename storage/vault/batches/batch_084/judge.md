---
batch_id: batch_084
direction: anchor_proximity_momentum
judged_at: 2026-05-02T17:10:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 0, reserve: 0, reject: 6}
admit_count: 0
reject_count: 6
reserve_count: 0
candidate_count: 6
mt_bucket: high
---
# batch_084 Judge Summary

> [!abstract]+ batch_084 · [[directions/anchor_proximity_momentum]] · 6 candidates
> ❌ **reject=6** (C001-C006) · ⏸ **reserve=0** · ✅ **admit=0**
> **核心发现**: **PTA 长窗口 envelope (250d) 在 csi1000 daily 上系统性失败** — 无论 TsRank wrap (C001) 或 CsRank-rank-diff (C006) 或 Mean-anchor 替代 (C005 z-score) 形式，alpha_surv 全部 < 0.40 hard 阈或 style_r² > 0.12；同时 **P008 escape "wrapper-conditional" 假设证伪**：CsRank-wrapper 替代 TsRank wrap (C004) 不足以维持 daily-resolution dim-less ratio 的 alpha；**T005 wick-asymmetry 边界变体 (C003) 是 F025 colinear 投影** (max_corr=0.89)，不构成独立几何。
> **MT Budget**: cumulative 462 → **468** · direction 6 → **12** · bucket `high` (本批 mt_score=0.81 high)；本批 low=2 (C004/C006) / med=4 (C001/C002/C003/C005) / high=0
> **方向状态**: anchor_proximity_momentum 维持 productive (F026 已 admitted)；本批 0/6 表明 daily F026 之外的扩展几何受 vol_20d 吞噬 + F025/F026 cluster colinearity 双重约束。

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🟢·🟡·🔴·🟢·🟡 | ic=-0.018 alpha_surv=**0.10** ls_t=-2.48 mono=-0.7 | T004 PTA 250d TsRank 长窗口 envelope alpha_surv 0.10 << 0.40 hard 阈下深陷 vol_20d；论文 250d 长窗口 hypothesis 在 csi1000 daily disprove | [[batches/batch_084/candidates/C001]] |
| C002 | ❌ reject | 🟢·🟢·🟢·🟠·🟡 | ic=-0.024 alpha_surv=1.92 max_corr=**0.68@F026** incr=-0.006 | T002 CsRank-rank-diff PTA × past-winner; LHS atom 是 F026 daily snapshot (close-position from low)；max_corr=0.68 + incr_ic NEG → 设计层无独立新几何，是 F026 重复 | [[batches/batch_084/candidates/C002]] |
| C003 | ❌ reject | 🟢·🟢·🟢·🔴·🟢 | ic=+0.019 alpha_surv=1.14 mono=**+1.0** style=0.026 max_corr=**0.89@F025** | T005 wick-asymmetry 非对称版本 (upper_wick/lower_wick) → F025 midpoint geometry colinear 投影；max_corr 0.89 > 0.70 near_duplicate threshold；几何并非独立新空间 | [[batches/batch_084/candidates/C003]] |
| C004 | ❌ reject | 🟢·🟡·🔴·🟠·🟡 | ic=-0.011 alpha_surv=0.90 style=0.279 dom=vol_20d HIGH max_corr=0.55@F022 incr=-0.018 | T005 P008 wrapper-conditional 测试结果：CsRank wrap (无 TsRank) **失败** — daily 同 atom (c-l)/(h-l) 在 CsRank Mean(20) 下 vol_20d HIGH crowding，与 F026 TsRank 60d wrap 完全不同结果。**P008 答案：必须 TsRank wrapper** | [[batches/batch_084/candidates/C004]] |
| C005 | ❌ reject | 🟢·🟢·🔴·🟢·🟡 | ic=-0.031 alpha_surv=0.56 style=**0.403** dom=vol_20d HIGH ls_t=-2.37 | T004 z-score 60d (Std-normalized distance from MA60) 假设：z-score 形式绕过 P008 atom-specific 限制 — DISPROVEN. style_r²=0.403 远超 poor 阈 0.12，分母 Std 显式 vol normalize 反而加深 vol_20d 暴露 | [[batches/batch_084/candidates/C005]] |
| C006 | ❌ reject | 🟢·🔴·🔴·🟢·🟢 | ic=+0.025 alpha_surv=**0.15** ls_t=**0.35** mono=+0.1 style=0.404 vol_20d=30.3 | T004 PTA 250d CsRank-rank-diff (vs Std60 vol-level subtractor) 失败：alpha_surv 0.15 + ls_t≈0 + mono≈0；vol_20d_exp 30.3 本批最高 — rank-diff 减去 vol_60 仍未净化 vol_20d 主成分；C001/C006 双形式失败 → PTA 250d 在 csi1000 daily 不可行 | [[batches/batch_084/candidates/C006]] |

## 跨候选对比

- **PTA 250d 长窗口双形式失败 (C001 + C006)**：T004 论文标定窗口 hypothesis 在 csi1000 daily **disprove**。无论 TsRank 250d wrap (C001 alpha_surv=0.10) 或 CsRank-rank-diff vs Std60 (C006 alpha_surv=0.15)，PTA 单边 envelope 250d 都 alpha_surv 远低于 0.40 hard 阈。机理：250d Max-envelope 在 csi1000 创新高频率低（日均 ~0.4% stock-day），导致大部分股票 PTA ≈ 1（钉在 envelope），cross-section 区分度差；vol_20d 反成 PTA 高低的代理（vol 高股震幅大，更易触及 envelope）。**T004 thread 应 close** with answer = "no PTA window in [60, 250] in csi1000 daily 形成 vol_20d-escape alpha"。

- **F025/F026 anchor cluster 占位律泛化** (C002 max_corr=0.68@F026 + C003 max_corr=0.89@F025)：daily-resolution dim-less ratio of intraday OHLC 几何空间被 F025+F026 双轴占据完整。任何 (a) close-from-low 类比例 (C002/C004) → F026 colinear；(b) midpoint/边界 wick-asymmetry → F025 colinear。**升格 lessons 候选**：anchor_proximity_momentum + tsrank_candlestick_ratio 两方向 daily intraday position/ratio geometry 已 saturated by F025+F026；新候选必须脱开 [0,1] bounded fraction-of-range 框架（如改 cross-day envelope, 但 b082-b084 已证 cross-day fail）。

- **P008 wrapper-conditional 已确认 (C004)**：F026 = TsRank((c-l)/(h-l), 60) 成功；C004 = CsRank(Mean((c-l)/(h-l), 20)) 失败（alpha_surv=0.90 borderline + style_r²=0.279 + vol_20d HIGH crowding）。证明 P008 escape 律必须 (a) atom 是 daily-resolution dim-less ratio (单日 (h-l) 分母) **AND** (b) outer wrapper 是 TsRank with window ≥ 60d（time-series rank 把 cross-section level 替换为"个股自身分位"）。CsRank cross-section rank 不构成 vol-escape 通道。**升格 lessons 候选**：P008 完整律为 "daily atom + TsRank ≥60d wrapper" 双条件，不可单独减项。

- **C005 z-score 形式 disprove**：假设 (close-Mean60)/Std60 + TsRank60 比 raw envelope/Mean ratio 更能逃 vol — DISPROVEN. style_r²=0.403 远超 poor 阈，dom=vol_20d HIGH crowding。机理：Std60 分母正比 vol，但分子 (close-Mean60) ~ vol×Z（Z 标准正态部分），cross-section ranking 后仍线性载 vol level，加之 TsRank 时序 rank 不破截面 vol basis。**P008 atom-specific 假设维持**：z-score 不是 daily-resolution ratio (用 60d Mean/Std)，所以不属 P008 适用域。

- **MT 预算推进**: cumulative 462→468 / direction (anchor_proximity_momentum) 6→12，仍 mt_bucket=high 但本批不引入 cumulative 增长；连续零 admit (含本批 + b083) zero_admit_streak=2 但**未触发 calibration**：reserve 池累积无独立性质 (C002/C006 reserve 都 max_corr 与库高度重叠或 style 高暴露)，无"被错杀候选"。

## Thread 进展

> [!note]+ T004 [[directions/anchor_proximity_momentum#T004]] 🔚 — `[✗ DISPROVEN]`（本批 close）
> 锚窗口曲线 60d → 120d → 250d → 500d 寻找 sweet spot — 本批补足 250d 双形式 (TsRank/CsRank-rank-diff) 全部 alpha_surv << 0.40 失败 + z-score 60d (C005) 失败。**结论**：csi1000 daily 上 PTA 在 [60d, 250d] 全窗口空间无 vol_20d-escape sweet spot；论文 12-month anchor effect 在 A 股 daily 频率 cross-section 不复现（论文 monthly horizon, A 股 daily 频率失活；A 股散户记忆周期 30-60d 但 60d 窗口已确证 fail）。500d 长窗口 ablation 不再值得测（机理上更稀释）。

> [!note]+ T002 [[directions/anchor_proximity_momentum#T002]] 🔚 — `[✗ DISPROVEN]`（本批 close）
> PTA × past-winner 嵌套交互 incremental IC over PTA alone — C002 CsRank-rank-diff form alpha_surv=1.92 + mono=-1.0 PERFECT 表面 strong，但 LHS = F026 atom 重复 (max_corr=0.68@F026) + incr_ic=-0.006 NEG → 设计层不构成新维度。论文 nested independence 在 csi1000 daily 不可证（PTA 单变量已饱和+colinear 库存因子）。

> [!note]+ T005 [[directions/anchor_proximity_momentum#T005]] ◉ — daily-resolution dim-less ratio + TsRank 60d 跨方向 generalizability 边界
> 本批两轨补足：(a) wick-asymmetry 非对称版本 (C003) 与 F025 midpoint 对称版本 max_corr=0.89 colinear → daily intraday wick-anchor 几何空间已被 F025 占据；(b) wrapper-conditional (C004) — CsRank 替 TsRank 失败，**P008 完整律 = daily atom + TsRank ≥60d 双条件**。**Next probes**: 跨方向 [[intraday_price_formation]] / [[ohlc_temporal_aggregation]] 测试 daily-resolution 不同 atom (e.g., body/range, 但需脱 F025/F026/F019/F022 cluster, max_corr<0.40)。

## P008 boundary distillation 累积 (b082+b083+b084)

- ✓ **success conditions**: 
  - daily-resolution dim-less ratio (单日 (h-l) 分母) - F025 shadow asymmetry midpoint, F026 close position low-anchor
  - TsRank wrapper window ≥ 60d
- ✗ **failure conditions**:
  - cross-day envelope/range/mean (b082 C001/C003/C004/C005, b084 C001/C006) - 60d/120d/250d 跨日 max envelope 全 vol-absorbed
  - raw range magnitude (b083 C001/C005) - vol-CV family colinear
  - outer Std-wrap (b083 C004) - 5d Std + TsRank 60d composite 反深陷 vol_20d
  - z-score form (b084 C005) - Std denominator 不解决 vol absorption
  - CsRank wrapper instead of TsRank (b084 C004) - cross-section rank 不构成 vol-escape
  - wick-asymmetry boundary version (b084 C003) - F025 midpoint colinear (corr=0.89)
  - PTA × past-winner CsRank-rank-diff (b084 C002) - LHS = F026 atom (corr=0.68)

**P008 完整律 (consolidation candidate)**: vol_20d-escape via daily-resolution close-anchor 几何 在 csi1000 daily 上 **必须** 同时满足：(a) atom 用单日 OHLC 上的 dim-less fraction-of-range ([0,1] bounded), (b) outer wrap 用 TsRank window ≥ 60d (time-series rank), (c) 几何脱 F025/F026 anchor cluster (max_corr<0.40)。三条件之一缺失即 fail。

**下一批建议**: anchor_proximity_momentum direction status 维持 productive 但 round 3 0/6 → 评估转 saturated;若 orchestrator 选 continue，应跨 direction (intraday_price_formation/ohlc_temporal_aggregation) 复用 P008 schema 但用未占据 atom (body/range, open-position, 等) 配 max_corr<0.40 cluster check。
