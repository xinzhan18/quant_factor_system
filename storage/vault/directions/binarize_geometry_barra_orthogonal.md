---
direction_tag: binarize_geometry_barra_orthogonal
status: dead
priority: high
rounds: 1
admits: 0
last_batch: batch_101
last_admits: []
last_goal: 'library_gap finding 023 follow-up — F029 admit 验证 conditional binarize
  ⊥ Barra basis 路径但 family-space 是 sparse axis (仅 F028 F029). 6 候选系统化 sweep 6 axes
  围绕 single-day candle binarize 几何 ⊥ Barra basis 假设: (C001) middle-body proximity
  (close 靠近中点, 非 tail 几何, T001); (C002) 弱上影日反 F029 mirror (Lt(H-C)/(H-L), 0.2, 上影微小
  = close 接近 high, 反 F029 close-low 几何, T002); (C003) 弱 open 低位日 (字段切换 open + Lt(O-L)/(H-L),
  0.2, 不同 tail, T003 — 注意 b099/C004 已测 (H-O)/(H-L) Lt 0.2 dead, 本候选是 reciprocal (O-L)/(H-L)
  信号底层不同); (C004) inside-bar 跨日 range pattern (Mul(Lt H, Gt L) 20d, pure range geometry,
  T004); (C005) 弱收盘 × 低换手 cross-field compound (turnover 用 self-baseline 避免 b099/C006
  amplitude≡vol_20d 复合陷阱, T005); (C006) 大实体日 Gt(|C-O|/(H-L), 0.7) (Gt 强端 + 高阈, 不同于
  b098/C002 small-body 0.3 dead, T006). 全候选每个引用 1 thread. Anti-recap full check: (a)
  F029 7-axis 邻域 disprove 不重演 (本批 0 个 candidate 是 close-position × Lt × 0.2 × 20d
  × Mean); (b) F006/F007/F008 continuous shadow/open persistence Mean(magnitude, N)
  几何 vs 本批 Lt/Gt full binarize Mean rate — distinct; (c) b099/C006 amplitude × close-pos
  compound 用 amplitude binarize≡vol_20d, C005 改用 turnover self-baseline 不同 basis 路径;
  (d) b099/C004 open (H-O)/(H-L) Lt 0.2 dead, C003 改用 reciprocal (O-L)/(H-L) 不同 tail.
  Baseline-first 守则: 本方向纯 OHLCV+turnover binarize, 与 15 untouched fundamental TTM
  字段完全不相关, 显式 skip baseline-first 配额.'
last_activity: '2026-05-16T07:37:19Z'
created_batch: batch_101
members: []
---
# Binarize Geometry Barra Orthogonal

> [!abstract]+ 方向概要
> - **状态**　🔴 `dead` · priority `low` · rounds = 1 · admits = 0
> - **最近**　[[batches/batch_101/judge|batch_101]] · 2026-05-16 · 0/0/6
> - **一句话**　首轮 6 axes sweep 全 reject, hypothesis "family-space 非孤立" 被证伪 — F029 是 single-day candle binarize ⊥ basis 在 csi1000 daily 上的 hyper-isolated 唯一 admissible point

---

## Hypothesis

库 28 admit 中条件算子族仅 2 个 (F028 DMI ratio + F029 weak_close rate). conditional_operator_truncation 方向已 saturated, 其结论:

> **conditional truncation 路径 admit 充分条件 = binarize 内容 ⊥ Barra style basis** (不是形式独特性)

且 F029 = close-position × Lt × 0.2 × 20d × Mean × 单 condition 在 **7 维约束**下 quasi-isolated singularity, 邻域内全部 fail (b099 6 维度扩展全 reject).

**本方向原核心 hypothesis**: 但**家族空间不是孤立的** — single-day candle geometry 还有大量 ⊥ Barra basis 的子族**信号底层与 F029 完全不同** (middle-body / 弱上影 / 弱 open / inside-bar / cross-field compound / threshold sign-dependent).

> [!warning] ⚠️ Hypothesis 已证伪 (batch_101)
> batch_101 首轮 6 axes sweep 全 reject (0/6 admit), 6 子族全部 ≡ Barra basis (vol_20d 4 + str_1m 2 主导吸收) 或重演 F029 superset (C005 max_corr=0.726 + 库 reducer). hypothesis "family-space 非孤立" 在 csi1000 daily 线性 binarize 路径上被实证证伪.
>
> **元教训**: F029 = close-position × Lt × 0.2 × 20d × Mean 是 single-day candle binarize ⊥ Barra basis 在 csi1000 daily 上的**hyper-isolated 唯一 admissible point**, 邻近 6 个不同 axis (middle-body / 上影 mirror / open mirror / inside-bar / cross-field compound / body Gt 强端) 全部被 vol_20d / str_1m basis 共振吃干. **single-day candle binarize 路径 csi1000 daily 真饱和**; F029 + b097/C001 reserve 是仅有 2 个临界 admissible point, 进一步搜索无 ROI.

---

## Threads

### T001: middle-body proximity 几何 [✗ DISPROVEN batch_101]

> [!failure]+ Thread 结论
> **Question**: close 靠近 daily range 中点的日占比 (`Lt(|C-(H+L)/2|/(H-L), 0.3)` 20d Mean) 是否 ⊥ Barra basis 且 ⊥ library?
>
> **Answer**: 几何 regime-dependent dead — IS/OOS sign 翻号 (+0.0025 vs -0.0090) + 单调 sign 翻号 (+0.80 vs -0.70). middle-body event 在 IS 期为信号缺失日 (positive 选股) 但 OOS 期为弱势日, 不构成稳定 alpha 几何. vol_20d_exp=18.97 严重共振.
>
> **Evidence trail**:
> - [[batches/batch_101/candidates/C001|batch_101 C001]]　CP01 triple fail (sign_flip + oos_decay -3.65 + mono_sign_flip) → **reject**

### T002: weak upper shadow (anti-F029 mirror geometry) [✗ DISPROVEN batch_101]

> [!failure]+ Thread 结论
> **Question**: `Lt((H-C)/(H-L), 0.2)` 20d Mean (上影微小日占比) 是否复制 F029 阈值 sign-dependent 律 (Lt 弱端 thick-tail ⊥ basis)?
>
> **Answer**: 不成立 — sign 翻号 (-0.0085 vs +0.0012) + OOS 信号归零 (|0.0012|<0.008). F029 律 (Lt 弱端 thick-tail ⊥ basis) 在字段切换 (close-tail → upper-shadow-tail) 即破坏. **lesson candidate (a)**: 阈值 sign-dependent 律字段绑定, 不是抽象"close-tail 几何"本身, 而是 close-position 字段 anchor.
>
> **Evidence trail**:
> - [[batches/batch_101/candidates/C002|batch_101 C002]]　CP01 triple fail (sign_flip + ic_oos 0.001 + oos_decay -0.138); str_1m=2.91 mid vol_20d=6.58 mid → **reject**

### T003: weak open low-position rate (field switch + Lt tail) [✗ DISPROVEN batch_101]

> [!failure]+ Thread 结论
> **Question**: `Lt((O-L)/(H-L), 0.2)` 20d Mean (open 低位日 reciprocal of b099/C004 dead form) — 字段切换 open + Lt 弱端是否 ⊥ basis?
>
> **Answer**: 不 — alpha_surv=**0.070** catastrophic (str_1m_exp=3.36 + vol_20d_exp=15.06 双重 ≡ basis). 验证 conditional_operator_truncation hypothesis 第 4 条 (字段 — open vs close 切换即跨入 str_1m basis 吸收区) **不论 tail 方向** (b099/C004 high-end + b101/C003 low-end 双向 dead).
>
> **Evidence trail**:
> - [[batches/batch_101/candidates/C003|batch_101 C003]]　CP01 ok + CP03 borderline + CP04 **poor** (alpha_surv=0.070) → **reject**

### T004: inside-bar daily range pattern [✗ DISPROVEN batch_101]

> [!failure]+ Thread 结论
> **Question**: `Mul(Lt($high, Ref($high,1)), Gt($low, Ref($low,1)))` 20d Mean (inside-bar 跨日 range pattern rate) 是否 pure range geometry ⊥ basis?
>
> **Answer**: 不 — alpha_surv=**0.125** + vol_20d_exp=7.19. **max_corr=0.208 (low!) + mono_oos=-0.90 真实** 但 incr_ic≈0 — "static vs dynamic ⊥ Barra 悖论" 标准案例: 几何 distinct ≠ alpha distinct, inside-bar ≡ low vol regime proxy. 跨日 range pattern binarize 路径 dead.
>
> **Evidence trail**:
> - [[batches/batch_101/candidates/C004|batch_101 C004]]　CP01 ok + CP03 borderline + CP04 **poor** + CP05 low (max_corr=0.208) → **reject**

### T005: weak-close × low-turnover compound [✗ DISPROVEN batch_101]

> [!failure]+ Thread 结论
> **Question**: `Mean(Mul(Lt((C-L)/(H-L), 0.2), Lt($turnover_rate, Mean($turnover_rate, 20))), 20)` (turnover self-baseline avoid b099/C006 amplitude 陷阱) cross-field compound 是否 ⊥ basis + 库 distinct?
>
> **Answer**: 不 — max_corr=**0.726@F029** + incr_ic=-0.0005 库 reducer. 关键发现: turnover self-baseline 复合 condition **未保护** ⊥ basis — 在 F029 已 ⊥ basis 母信号上叠加 selectivity (turnover-low) 条件, str_1m_exp 从 0.91 涨到 3.51, alpha_surv 从 1.10 退化到 0.33. **lesson candidate (b)**: 复合 condition 反吸引 basis 律 — selectivity 与 ⊥ basis 不兼容.
>
> **Evidence trail**:
> - [[batches/batch_101/candidates/C005|batch_101 C005]]　CP01 ok + CP03 borderline (IC+ls_t strong mono +0.90) + CP05 **high** max_corr=0.726@F029 + 库 reducer → **reject**

### T006: strong-body day rate (Gt 强端 + 高阈) [✗ DISPROVEN batch_101]

> [!failure]+ Thread 结论
> **Question**: `Mean(Gt(|C-O|/(H-L), 0.7), 20)` (大实体 trend-day rate) — body 几何 Gt 强端 + 高阈 0.7 mirror b098/C002 Lt 0.3 dead, 是否阈值 sign-dependent 律在 body 几何成立?
>
> **Answer**: 不成立 — ic_oos=0.0054<0.008 (CP01) + vol_20d_exp=**28.80** 史诗 (与 b099/C006 amplitude vol_exp=45 同等级) + incr_ic=-0.009 库 reducer. body 几何 binarize 跨阈值方向**双向 dead**: Lt 0.3 small-body (b098/C002) + Gt 0.7 large-body (b101/C006). **lesson candidate (c)**: body 几何 binarize family csi1000 daily 整体 dead, 阈值 sign-dependent 律仅适用 close-position 字段.
>
> **Evidence trail**:
> - [[batches/batch_101/candidates/C006|batch_101 C006]]　CP01 ic_oos<0.008 + vol_exp=28.80 + incr_ic=-0.009 → **reject**

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_101/candidates/C001\|C001]] | `Mean(Lt(\|C-(H+L)/2\|/(H-L), 0.3), 20)` | CP01 triple: sign_flip + oos_decay -3.65 + mono_sign_flip |
| [[batches/batch_101/candidates/C002\|C002]] | `Mean(Lt((H-C)/(H-L), 0.2), 20)` | CP01 triple: sign_flip + ic_oos 0.001 + oos_decay -0.138; F029 律字段切换破坏 |
| [[batches/batch_101/candidates/C003\|C003]] | `Mean(Lt((O-L)/(H-L), 0.2), 20)` | CP04 poor: alpha_surv=**0.070** str_1m_exp=3.36 + vol_20d_exp=15.06 |
| [[batches/batch_101/candidates/C004\|C004]] | `Mean(Mul(Lt(H,Ref(H,1)), Gt(L,Ref(L,1))), 20)` | CP04 poor: alpha_surv=**0.125** vol_20d_exp=7.19 (max_corr=0.208 但 incr_ic≈0 static vs dynamic 悖论) |
| [[batches/batch_101/candidates/C005\|C005]] | `Mean(Mul(Lt((C-L)/(H-L),0.2), Lt(turnover, Mean(turnover,20))), 20)` | CP05 high: max_corr=**0.726**@F029 + incr_ic=-0.0005 库 reducer |
| [[batches/batch_101/candidates/C006\|C006]] | `Mean(Gt(\|C-O\|/(H-L), 0.7), 20)` | CP01: ic_oos=0.0054<0.008; vol_20d_exp=**28.80** + incr_ic=-0.009 |

---

## Related

- 🟡 [[conditional_operator_truncation]] `saturated` — F029/F028 来源方向, 本方向 follow-up; family-space 非孤立 hypothesis 被本方向证伪.
- 🟡 [[ohlc_temporal_aggregation]] `saturated` — F006/F007/F008 continuous shadow/open persistence (`Mean(magnitude, N)`, 非 binarize), cluster check 必读.
- 🟡 [[anchor_proximity_momentum]] `saturated` — F026 close_position TsRank 60d, 几何与 F029 同信号底层但 TsRank vs Lt-binarize.
- 🟡 [[gap_acceptance_structure]] `saturated` — gap binarize family 跨阈值 dead.
- 🔴 [[price_conditional_amplitude]] `dead` — conditional × continuous amplitude path-integral 路径 dead.
- [[lessons#Geometric absorbing-factor 律]] — anchor cluster precheck.
- [[lessons#P030 alpha_survival > 1.0 paradox guard]] — incr_ic / max_corr / ls_t 三 gate.
- [[_consolidation/findings/library_gap/023|library_gap 023]] — 本方向直接来源 finding; batch_101 已部分挑战 finding 023 的"family-space 非孤立"假设.

---

## Narrative Log

> [!quote]+ 2026-05-16 · [[batches/batch_101/judge|batch_101]] judge
> **首轮 6 axes 全 reject, hypothesis 整体证伪 → dead** · admit=0 / reserve=0 / reject=6
>
> - 6 axes 系统化 sweep: middle-body (T001 CP01 sign 翻号 + mono 翻号 regime-dependent) / 上影 mirror (T002 CP01 sign 翻号 + OOS 归零, F029 律字段切换破坏) / 弱 open (T003 alpha_surv=0.07 str_1m 直接吸收) / inside-bar (T004 alpha_surv=0.125 vol_20d 反向 proxy + static vs dynamic 悖论) / weak-close × low-turnover (T005 max_corr=0.726@F029 + 库 reducer, 复合 condition 反引入 str_1m=3.51) / 大实体 Gt 0.7 (T006 vol_exp=28.80 史诗 + incr_ic=-0.009).
> - **核心发现**: F029 不仅在 conditional_operator_truncation 方向 7 维 quasi-isolated, 在更广 single-day candle binarize 6 axes 邻域也是 hyper-isolated — **每个 axis 都被 vol_20d / str_1m basis 共振吃干**. finding 023 假设"family-space 非孤立"在 csi1000 daily 线性 binarize 路径上被证伪.
> - **3 条 lesson promotion candidate**: (a) 阈值 sign-dependent 律字段绑定 (F029 律仅在 close-position 成立, 字段切换即失效); (b) 复合 condition 反吸引 basis 律 (selectivity 与 ⊥ basis 不兼容, F029 母信号叠加 turnover-low 条件 str_1m_exp 从 0.91 涨到 3.51 alpha_surv 从 1.10 跌到 0.33); (c) body 几何 binarize family csi1000 daily 跨阈值方向双向 dead (Lt 0.3 small + Gt 0.7 large 双 dead).
> - **MT Budget**: cumulative 564 → **570** · direction 0 → **6** · bucket `medium` (新方向 direction-level exposure 仍 sparse).
>
> **Operations**　`status: exploring → dead` · priority `high → low` · rounds 0→1 · admits 0 · 1 batch sweep exhaust 主要 axis-wise hypothesis. 不再开新 batch.
> **下一步**: (a) lessons 升格 3 条; (b) F028 邻域 axis-wise 扩展 (DMI conditional ratio 几何与 candle binarize 完全不同, 是 conditional 路径剩下唯一未探索 anchor); (c) 跳出 conditional 路径转向新几何 (turnover-binarize / fundamental-binarize / momentum-binarize 等); (d) finding 023 可缩窄: F029 + b097/C001 reserve 是 single-day candle binarize ⊥ basis 在 csi1000 daily 上**仅有 2 个临界 admissible point**.

> [!quote]- 2026-05-16 · batch_101 design
> **新方向创建** — library_gap finding 023 提议. F029 admit 验证 conditional binarize ⊥ Barra basis 但 family-space 是 sparse axis (仅 F028 F029, direction-level exposure 低 → mt 可能 medium). 6 候选覆盖 6 axes: middle-body proximity (T001) / 弱上影反 F029 (T002) / 弱 open low-position (T003) / inside-bar 跨日 (T004) / weak-close × low-turnover compound (T005) / 大实体率 (T006). Self-check 全过: P030 multi-CP (alpha_surv 必配 incr_ic/max_corr/ls_t 2/3) / P031 7-dim conditional 守则 (full binarize + Mean rate + ⊥ basis + 字段+方向+阈值+窗口 单独考察) / P033 OOS sign-flip (DSL conditional 原生, 不走 Python residualize) / Anchor precheck: F029 Lt0.2 close-pos / F026 close-pos TsRank60 / F006-F008 continuous shadow Mean / F019 body Std rank-diff — 6 候选每个几何与 anchors 不同. baseline-first 守则: 本方向纯 OHLCV+turnover binarize, 与 15 untouched fundamental TTM 字段不相关, 显式 skip baseline-first 配额.
>
> **Operations**　`status: exploring (NEW)` · priority `high`
