---
batch_id: batch_059
direction: overnight_intraday_split
judged_at: 2026-04-25T12:35:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reserve}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: admit, factor_name: gap_body_magnitude_amount_rd_20}
  - {candidate_id: C005, verdict: reserve}
  - {candidate_id: C006, verdict: reject}
batch_summary: {total: 6, admit: 1, reserve: 2, reject: 3}
admit_count: 1
reject_count: 3
reserve_count: 2
candidate_count: 6
mt_bucket: high
---

# batch_059 Judge Summary

> [!abstract]+ batch_059 · [[directions/overnight_intraday_split]] · 6 candidates
> ✅ **admit=1** (C004 → F{next} `gap_body_magnitude_amount_rd_20`) · ⏸ **reserve=2** (C002/C005) · ❌ **reject=3** (C001/C003/C006)
> **核心发现**: T011 sign-product **magnitude-weighted 短窗救活**实证 — C004 (gap × body magnitude product 20d × amount_60) ic_oos=0.044 ICIR=0.37 ls_t=4.89 mono=1.0/1.0 完美 + 9/9 年同号 + IC anti-decay (OOS>IS) + worst_quarter=+0.0019 永正 + cum_ic_mdd=-1.72 库内最浅 + incremental_ic=0.018 远超 F203 0.015 borderline corr 阈值。同时验证 (a) **center-position LHS 是 close-position 仿射变体** (C006 与 F022 corr=0.93 hard_gate near_dup);(b) **sign(close-direction) 离散化未脱 F022 几何 cluster** (C005 corr=0.82 — 与 b049 sign vs magnitude corr=0.37 不同律,reserve 候选升格 lessons 候选);(c) **circ_mktcap_60 不适合 rank-diff RHS** (C001/C003 alpha_surv=23.19/3.08 极端 + Barra log_circ_cap 直接吞噬);(d) **sign-product 60d 是长 horizon 现象** (C003 1d IC=0.0016 但 20d IC=0.030 — 在 primary_horizon=1 evaluation policy 下 thread 面临 structural mismatch,T011 sign-only 路径基本封闭)。
> **MT Budget**: cumulative 312 → **318** · direction 27 → **33** · bucket `high` (search_adjusted → medium) · 本批 low=0 / med=0 / high=6 (direction.exposure 已饱和)

## 候选一览

| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | hard_gate | ic_oos=-0.0004 + oos_decay=0.08 fail | center×circ_mktcap_60 — Barra log_circ_cap 完全吞噬 (alpha_surv=23.19 极端 + style_r²=0.57) | [[batches/batch_059/candidates/C001]] |
| C002 | ⏸ reserve | 🟡·🟠·🟠·🟢·🟡 | ic=-0.027 mono=0/-1 ls_t=-2.24 max_corr=0.35@F006 | center×amount_60/20 — 库内首次 negative 方向 close-position rank-diff,IS mono=0 → OOS=-1.0 emergent regime,9/9 年同号但 cum_ic_mdd=-60 深;CP03 borderline + CP04 borderline | [[batches/batch_059/candidates/C002]] |
| C003 | ❌ reject | hard_gate | ic_oos=0.0016 + oos_decay=0.15 fail | sign-product 60d×circ_mktcap_60 — 1d IC 弱但 20d IC=0.030,T011 长 horizon 现象在 primary_horizon=1 mismatch | [[batches/batch_059/candidates/C003]] |
| C004 | ✅ admit | 🟢·🟢·🟠·🟡·🟢 | ic=0.044 ICIR=0.37 ls_t=4.89 mono=1.0 incr=0.018 | gap × body **magnitude-weighted product** — T011 短窗救活;9 admit 来到方向 + 第一个 second-order interaction (overnight×intraday joint magnitude 而非 sign) | [[batches/batch_059/candidates/C004]] · [[factors/F023]] |
| C005 | ⏸ reserve | 🟡·🔴·🟢·🔴·🟢 | ic=0.026 mono=0.7 ls_t=1.88 max_corr=0.82@F022 incr=0.0049 | sign(close偏向)×turnover_5/60 — sign 离散化未脱 F022 cluster (corr=0.82 vs b049 sign-magnitude 0.37),CP05 high 档 reserve 决策 | [[batches/batch_059/candidates/C005]] |
| C006 | ❌ reject | hard_gate | near_dup max_corr=0.93@F022 | center×turnover_5/60 — center=close_pos 仿射 (差常数 1/2),CsRank 后等价 | [[batches/batch_059/candidates/C006]] |

**档位编码**: 🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档 · `hard_gate` reject 不填色。

## 跨候选对比

- **Style 聚合**: 6/6 候选 dominant_style_exposure=`vol_20d` (统一暴露)。本方向所有 admit (F009/F010/F011/F017/F018/F022/C004) 都共载 vol_20d — 这是 direction-level structural exposure,不是单批 anomaly。C001/C003 RHS=circ_mktcap_60 还叠加 log_circ_cap exposure (0.64/0.51) 双载体导致 hard_gate fail。
- **LHS atom 聚合**: 3/6 候选用 center-position `(C-mid)/(H-L)` 新 atom (C001/C002/C006)。C006 验证 center 是 F022 close-position 的仿射变体 (corr=0.93 near_dup),C001/C002 在 RHS 替换后保留独立性 (与 F022 corr=0.42/0.07) 但 C001 撞 Barra style hard_gate fail,C002 通过但 ls_t borderline。**center vs close-position 几何相同**升格 lessons 候选: "Phase 1 LHS 设计差常数项不构成有效绕开"。
- **sign-product / sign(close-direction) 双 sign 路径**: C003 (60d sign(o)*sign(i)) reject + C005 (20d sign(C-L vs H-C)) reserve。两候选验证不同**sign 离散化路径在 csi1000 cross-section rank-diff 下普遍未脱 magnitude cluster**——与 b049 F018 sign 与 magnitude corr=0.37 (低相关) 形成鲜明对比。**关键发现**: F018 sign-magnitude 正交是 LHS=sign(overnight) RHS=amount 的特定组合,**不可机械泛化**到 sign(close-direction) × turnover 或 sign(o)*sign(i) × circ_mktcap。
- **本批 magnitude-weighted product 救活短窗 thread**: C004 gap × body 直乘 (无 Sign) 在 20d 下 ls_t=4.89 完美,而 b058 C003 sign-only 同窗 ls_t=1.09 reject + b058 C005 sign-only 60d ls_t=1.91 reserve。**magnitude weighting 是短窗 sign-product 失败的解药**——本批最强结构发现。
- **MT 预算推进**: direction_candidates 27→33,family score 0.898 高位,direction score 0.760 高位,exposure score 1.0 满。 本批 6 候选全 raw bucket=high,search_adjusted 推回 medium 后 strong 档候选 (C004) 仍可保留。**direction 已 8 admits + 33 candidates**,接近 saturation 临界。

## Thread 进展

> [!note]+ T011 [[directions/overnight_intraday_split#T011]] — `[◉ ACTIVE]` (重大进展)
> **C004 admit (magnitude-weighted product 救活短窗)** + C003 reject (sign-product 60d primary_horizon mismatch)。**T011 关键转折**: sign-only path 在短窗 (b058 C003 mono=0.4) + 长窗 (b058 C005 alpha_surv 不足) + 跨 family RHS (b059 C003 1d IC 弱) 三次受阻;magnitude-weighted product (gap × body 直乘,不取 Sign) 在 20d 短窗下 ls_t=4.89 + mono=1.0 + 9/9 年正 + anti-decay → admit。**核心发现**: "magnitude × magnitude 共方向乘积" 比 "sign × sign 频率" 更适合 csi1000 1d primary_horizon evaluation policy。Thread 转 `[✓ ANSWERED batch_059]` 由 C004 兑现。**T013 新建** 衔接 sign-only 路径残留 (C005 reserve 待 F022 退役评估 + 跨 horizon 重评估)。

> [!note]+ T012 [[directions/overnight_intraday_split#T012]] — `[◉ ACTIVE]` (LHS atom 几何边界)
> C001/C002/C006 三候选用 center-position `(C-mid)/(H-L)` 新 LHS atom。**center 是 F022 close-position 的仿射变体** (差常数 1/2): C006 直接 corr=0.93 hard_gate near_dup;C001 (RHS=circ_mktcap_60) hard_gate fail (Barra 吞噬);C002 (RHS=amount_60/20 倒置) reserve (库 corr=0.07 与 F022 仿射独立, 但 IS mono=0 异常)。**关键发现**: CsRank 对 LHS 内常数偏移不敏感 (center = close_pos − 1/2),**仿射变换不能创造新 cross-section rank** — 升格 lessons 候选: "Phase 1 LHS 设计的有效绕开必须改 numerator 结构或分母 normalization,不能仅减常数"。Thread 状态保持 ACTIVE 但 close-position atom 几何已穷尽,需新 normalization (如分母换成 60d range 而非当日 H-L 实现跨窗)。

> [!note]+ T013 [[directions/overnight_intraday_split#T013]] 🆕 — `[◉ ACTIVE]`
> 衔接 T011 sign-only 残留路径与 T012 close-position 离散化失败。Question: "csi1000 1d primary_horizon 下,sign-离散化 (Sign(close偏向) / Sign(o)*Sign(i)) 在 cross-section rank-diff 几何下是否普遍未脱 magnitude cluster?b049 F018 (sign-overnight × amount) 的 sign-magnitude 0.37 低相关是否为特定字段组合的 happy accident 而非家族律?" Evidence: b058 C003 (sign-prod 20d mono 退化) + b058 C005 (sign-prod 60d alpha_surv 不足) + b059 C003 (sign-prod 60d × circ_mktcap 1d 弱) + b059 C005 (sign(C-L vs H-C) 20d corr=0.82@F022)。Next: (a) 待 F022 退役后重测 C005 reserve;(b) 跨 horizon evaluation policy 修订前不再投 sign-product 候选 (T011 sign-only 路径暂时封闭);(c) 试 magnitude-weighted variant 在其它 LHS atom (如 sign(C-L vs H-C) magnitude version 加权)。

## 方向级反思

本方向第 9 批,8 admit (F009/F010/F011/F017/F018/F022 + 本批 C004),direction.score 0.76 偏高 + cumulative 0.90 偏高 + exposure 1.0 满 → MT bucket 已 high,所有候选都进入 high-pressure judging。`incremental_ic` 中位数: b058=0.012, b059 admit=0.018 (上升,但 reserve 0.005-0.012 偏低,显示库内增值空间在收窄);**reserve 积压检视**: b058 留 2 (C001/C005) + b059 留 2 (C002/C005) 累计 4 reserve,reserve/judged = 4/12=33% 接近 40% 警戒线但未越线。

**T011 magnitude-weighted product 路径开启新 thread 空间**: gap × body 直乘是 second-order interaction 的入口;下批可探索 (a) overnight × overnight_next-day (overnight-overnight 自相关), (b) volume-weighted magnitude product (body × volume_z), (c) absolute magnitude product (|gap| × |body|, 失去方向但保留共振)。

**T012 close-position atom 几何穷尽信号**: 当前 LHS=Mean((C-L)/(H-L),20) 的所有仿射 / 离散化变体都被 F022 吸收。下轮如要继续 close-position 路径,**必须改分母** (跨窗 range normalization) 或**非线性变换** (Tanh/Sigmoid wrap),不再投仿射变体。

**direction status 评估**: 仍 productive (本批 admit C004 强信号),但 priority 可考虑从 high → medium (8 admits + 33 candidates,新角度增量在 magnitude/multi-window 路径而非 close-position 微调)。本轮维持 productive + high,Phase 4 不调。
