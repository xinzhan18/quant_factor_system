---
batch_id: batch_082
direction: anchor_proximity_momentum
judged_at: 2026-05-02T16:00:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reserve}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: admit, factor_name: daily_close_position_tsrank_60}
batch_summary: {total: 6, admit: 1, reserve: 1, reject: 4}
admit_count: 1
reject_count: 4
reserve_count: 1
candidate_count: 6
mt_bucket: medium
---

# batch_082 Judge Summary

> [!abstract]+ batch_082 · [[directions/anchor_proximity_momentum]] · 6 candidates
> ✅ **admit=1** (C006→F{next} `daily_close_position_tsrank_60`) · ⏸ **reserve=1** (C002 — C006 数学镜像) · ❌ **reject=4** (C001/C003/C004/C005)
> **核心发现**: P008 escape **跨 direction 复现成功** — `TsRank((c-l)/(h-l), 60)` 在 anchor_proximity_momentum 方向打出 alpha_surv=1.13 + mono_oos=-1.0 PERFECT + ls_t=-6.31，验证 b081 C006 hl_norm_sym (对称版 alpha_surv=0.99) 不是单例 fluke 而是**结构性 generalizable 路径**：bounded [0,1] dimless close-anchor proximity ratio + TsRank 60d 是 csi1000 daily 上跨 direction 可复用 alpha 生成器。**关键约束**：分母必须是 daily range 或 monotone envelope (单日 (h-l) / 跨日 60d_max 这类) — 而**不是 60d 双边 range** (TsMax(high)-TsMin(low)) 或 dynamic mean (Mean($close,60))。前者 (C002/C006 daily) 逃 vol_20d，后者 (C001/C003/C004/C005 跨日) 全部失败。
> **MT Budget**: cumulative_candidates 450 → **456** · direction_candidates 0 → **6** · bucket `medium`（mt_score=0.68，base score 0.68，search_adjusted 0.59）· 本批 low=0 / med=6 / high=0

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🟡·🔴·🔴·🟢·🟢 | ic_oos=-0.027 ls_t=-1.98 mono=-0.4 style_r²=0.36 | 60d 双边 range stochastic position TsRank 包装**未** P008 escape — 重演 stochastic_position DEAD 同律；分母 `TsMax(high)-TsMin(low)` 被 vol 主动撑大 | [[batches/batch_082/candidates/C001]] |
| C002 | ⏸ reserve | 🟢·🟢·🟢·🟡·🟢 | ic_oos=0.046 ls_t=6.40 mono=1.0 alpha_surv=1.20 style_r²=0.062 | 自身**完全够 admit**，但与 C006 数学完美镜像 (恒等式 (h-c)+(c-l)=h-l → corr≈-1)；admit C006 canonical, C002 reserve 等下轮独立性测试 | [[batches/batch_082/candidates/C002]] |
| C003 | ❌ reject | 🟡·🔴·🔴·🟢·🟢 | ic_oos=-0.036 ls_t=-2.87 mono=-0.3 style_r²=0.448 | `Mean($close,60)` dynamic-mean 分母被 vol 撑大 — 不是 monotone envelope；style_r²=0.45 远超 poor 阈 | [[batches/batch_082/candidates/C003]] |
| C004 | ❌ reject | 🟢·🟠·🔴·🟢·🟢 | ic_oos=-0.026 ls_t=-2.14 mono=-0.7 style_r²=0.327 vol_exp=**19.82** | PTA 60d **短窗口** envelope 未逃 vol_20d (exposure 19.82 本批最高)——论文 250d 长窗口期 envelope 更刚性，下轮可保留 PTA 250d 探索 | [[batches/batch_082/candidates/C004]] |
| C005 | ❌ reject | 🟡·🔴·🔴·🟢·🟢 | ic_oos=-0.032 ls_t=-2.39 mono=-0.2 style_r²=0.387 | PTL 60d floor envelope 与 PTA 同律失败；PTL 与 PTA 同号 ic 反驳 H3 mirror disposition asymmetry | [[batches/batch_082/candidates/C005]] |
| C006 | ✅ admit | 🟢·🟢·🟢·🟡·🟢 | ic_oos=-0.046 ls_t=-6.31 mono=**-1.0 PERFECT** alpha_surv=1.13 style_r²=0.068 | P008 escape 跨 direction **复现核心证据**；mono_oos=-1.0 完美单调 + alpha 残差空间 (alpha_surv=1.13) | [[batches/batch_082/candidates/C006]] · [[factors/F026]] |

**档位编码**：🟢 最优档（aligned/strong/good/low/stable）· 🟡 次档（mixed/borderline/acceptable/medium）· 🟠 边际（borderline）· 🔴 阻断档（misaligned/weak/poor/high/unstable）

## 跨候选对比

- **几何分类两簇**：
  - **Daily-resolution 单日 anchor proximity**（C002, C006）：分母 = 单日 `(h-l)` 即 daily range — bounded [0,1]，单日 close 在自身 range 内位置；TsRank 60d 量纲化。**两候选 alpha_surv > 1.0、style_r² < 0.10、mono_oos = ±1.0 PERFECT**。**P008 escape 确认成功**。
  - **Cross-day 60d-window anchor proximity**（C001, C003, C004, C005）：分母 = 跨日 60d 窗口尺度 — 60d 双边 range / 60d mean / 60d max envelope / 60d min floor。**所有 4 候选 alpha_surv ∈ [0.52, 0.80]、style_r² ∈ [0.33, 0.45]、vol_20d exposure 10.79 - 19.82 high crowding**。**全部失败**。

- **关键 finding**：**daily-resolution 几何**（C002 / C006）成功逃 vol_20d 吞噬，**cross-day 60d-window 几何**全部被 vol_20d 主动撑大。原因——单日 (h-l) 是即时实现 vol 不被未来 60d vol 状态污染；60d 跨日尺度的 envelope/range/mean 都受 60d 内累积 vol 漂移影响（即使是单调非降的 `TsMax($close, 60)` envelope 在短窗口下仍然 follow vol regime）。**P008 escape 的关键机制不是 "TsRank 60d wrapper" 而是 "atom 不被未来累积 vol 污染"**。

- **C002 / C006 数学镜像**：(h-c)/(h-l) + (c-l)/(h-l) ≡ 1 恒等式 + TsRank monotone-invariance → 两候选时序 corr ≈ -1（exact）。**库空间不应同 admit**——选 C006 (mono_oos=-1.0 perfect, canonical sign convention) admit, C002 reserve 等下轮 cross-correlation 实测决定独立性。

- **Style 聚合**：6 候选 dominant_style 全部 vol_20d，但 exposure 分两档：medium (8.76 / 11.04) 对应 admit/reserve 候选；high (10.79 - 19.82) 对应 reject 候选。**vol exposure 是结构性指标**——< 12 + alpha_surv > 1.0 是 P008 escape 的双重条件。

- **MT 预算推进**：cumulative 450 → 456，direction 0 → 6，bucket 维持 medium（base score 0.68）；本批 6 候选全 medium 分档（family novelty 0.96 高 + direction 累计 0 低 + exposure 1.0 已饱和）。预算健康。

## Thread 进展

> [!success]+ T001 [[directions/anchor_proximity_momentum#T001]] — `[✓ ANSWERED batch_082]`
> admit C006、reserve C002、reject C001。**回答 T001 question** = "PTA / 单边 anchor envelope 是否独立于双边 range 归一族" 的更深解答：daily-resolution 单日 (h-l) anchor 几何 **YES** (C002/C006 alpha_surv>1.0 + style_r²<0.10)；60d 跨日 envelope/range/mean 几何 **NO** (C001/C003/C004 全 vol_20d 吞噬)。**关键 generalization**：P008 escape 不是 PTA 几何专属，而是 daily-resolution dim-less close-anchor ratio 的通用属性。

> [!failure]+ T003 [[directions/anchor_proximity_momentum#T003]] — `[✗ DISPROVEN batch_082]`
> reject C005 (PTL 60d)。**Hypothesis H3 mirror disposition asymmetry partial 反驳**：PTL 60d 与 PTA 60d (C004) 实测 ic 同号 negative，不是 mirror 异号；style 几乎一致 vol_20d 主导——PTL 与 PTA 不是独立维度，是同 vol_20d 吸收族的 sign-equivalent 投影。本批反驳仅限 60d 窗口；250d 窗口空间未测，T003 hypothesis 在长窗口仍开放。

> [!note]+ T004 [[directions/anchor_proximity_momentum#T004]] — `[◉ ACTIVE]`
> reject C004 (PTA 60d) + C003 (close/MA60)。**T004 question 部分回答**：60d 窗口下 PTA envelope 不够"刚性"（vol_20d exposure=19.82 本批最高），论文 250d 长窗口可能更对。下轮 batch_083 应保留 PTA 250d / PTA 120d 长窗口探索；T004 仍 ACTIVE 等长窗口实证。

> [!note]- T002 [[directions/anchor_proximity_momentum#T002]] — `[◉ ACTIVE]`（本批无推进——本批未含 PTA × past-winner 交互候选）

> [!note]+ T005 [[directions/anchor_proximity_momentum#T005]] 🆕 — `[◉ ACTIVE]`
> 承接 T001 主线遗留的 P008 escape 机制 distillation：**"daily-resolution dim-less anchor ratio + TsRank 60d 是结构性 alpha 生成器"** 跨方向 generalizability 进一步验证——下批应在 [[directions/intraday_price_formation]] / [[directions/ohlc_temporal_aggregation]] 等其它方向用 daily-resolution 单日 (h-l) 比率 + TsRank 60d 复现，确认这一律的边界。

## 方向级反思

**本方向 status: exploring → productive**（首次 admit，C006 daily_close_position_tsrank_60 第一个进入 anchor_proximity_momentum 库）。

**Direction-level distillation**：
1. **bounded dimless close-anchor proximity + TsRank 60d** 在 daily-resolution 几何下成功 P008 escape，是结构性的——alpha_surv > 1.0 来自 Barra 残差空间而非 raw style space
2. **60d 跨日尺度的 envelope / range / mean** 几何**普遍失败**（C001/C003/C004/C005 4/4 全 reject + dominant_style=vol_20d high crowding）—— 即使是单调非降 envelope (`TsMax($close, 60)`) 在短窗口下仍 follow vol regime；TsRank 60d wrapper 不能拯救
3. **C002/C006 数学镜像** = 库空间不能同 admit 两个完全互补的 sign-mirror（信息冗余）；admit canonical sign 即可（C006 mono_oos=-1.0 perfect）

**下轮 batch_083 priorities**：
1. **T002**: PTA × past-winner 交互的 daily 版本（论文 nested test 复现）—— 继续 ACTIVE，本批未测
2. **T004**: PTA 250d 长窗口 baseline ablation（论文标定窗口）—— 60d 不够长，250d 是 hypothesis 真正测试点
3. **T005 (新)**: 跨 direction 验证 "daily-resolution dim-less anchor ratio + TsRank 60d" 律的边界——尝试 [[directions/intraday_price_formation]] 等方向用同一 schema 复现
4. **避免**: 不要再设计 60d 跨日 envelope/range/mean 类候选——已证伪

**Saturation 判断**：本方向 1 admit / 6 candidates = 16.7% admit rate。距 saturation 阈值（连续 2+ batch reject > 80% 即触发 saturated）尚远；admit C006 是 productive 的硬证据，下轮应继续探索 T002/T004/T005 方向，至少跑 2-3 批后再判 saturation。

**Calibration trigger**: 无（本批 admit≥1，错杀 flag 无，reserve 积压不属于错杀类型，悖论复现无）。
