---
direction_tag: gap_acceptance_structure
status: saturated
priority: low
rounds: 6
admits: 3
last_batch: batch_062
last_admits: []
last_goal: "T007 推进 + 守 6 anchor cluster 防线 + higher-moment LHS 跨窗扩展。当前 rank-diff\
  \ 6 admit 跨 5 family\n(F015-F020), gap_acceptance 仅 F020 (Std gap_ret × body_ratio_20)\
  \ admit + F013 retired。T007 ACTIVE\n揭示 cross-ratio LHS (raw |gap|/|body|) 在 rank-diff\
  \ 几何下 alpha_surv=0.005 极端 collapse — Barra\n完全吸收。本批回答 T007 future probes 两条逃路 +\
  \ 同时探一条新 LHS 范式 + 一条 RHS 维度。\n\n6 候选硬约束：\n(1) 每候选 LHS 唯一 atomic gap 表达，6 LHS 不重复；\n\
  (2) 严避 F010/F011 Mean(gap_ret,3/5) 同形 + 不复用 body_ratio_20 / price_vol_20 / amount_20\
  \ /\n    overnight_5 / turnover_5 / pb_60 (alpha_surv=0.005 collapse) / amount_60\
  \ (F023 RHS) dead RHS;\n(3) 不重演 T001 disproven (sign×sign aggregation) / T003 disproven\
  \ (gap 分母变体 corr@F003=0.96) /\n    T006 disproven (60d Std 多 regime sign_flip);\n\
  (4) 4 anchor pre-check (F002/F012/F020/F022): 候选不可同时撞 LHS/RHS anchor;\n(5) 全 DSL,\
  \ CsRank 内层仅 Mean/Std/Abs/Sub/Div/Sign/Ref (不外包 Custom Op AmihudIlliq/HHI);\n(6)\
  \ 避开 Qlib bug Corr($close,$turnover_rate,N) 跨 base-field broadcast — 用 Mean/Med/Std\n\
  \    of single field 作 RHS proxy。\n\nC001 T007 follow-up A — RANK-TRANSFORMED ratio:\
  \ LHS=Sub(CsRank(Mean(Abs(gap),20)),CsRank(Mean(Abs(body),20)))\n  aggregated rank-diff\
  \ 替代 raw ratio (C004 alpha_surv=0.005 collapse) — 测 ratio of two CsRank-ed\n  magnitudes\
  \ 是否避开 OHLC magnitude affine cluster + Barra style projection;\n  RHS=CsRank(Std($turnover_rate,20))\
  \ liquidity higher-moment 全新 RHS 维度 (turnover_5 dead 但 Std,20 未试);\n  预期 max_corr@F020<0.4\
  \ (LHS 是 magnitude rank-diff 而非 Std gap_ret) + alpha_surv@T007 vs C004\n  cross-ratio\
  \ 决定 rank-diff geometry 是否真避 Barra。\n\nC002 T007 follow-up B — ratio + sign 复合:\
  \ LHS=Mean(Mul(Sign(Sub($open,Ref($close,1))),\n  Div(Abs(Sub($open,Ref($close,1))),\
  \ Add(Abs(Sub($close,Ref($close,1))),0.0001))),20)\n  signed gap-magnitude relative\
  \ to total daily move (gap+intraday) — 区别 C004 用 |body| 分母,\n  本候选用 |daily-return|\
  \ 分母 + 加 sign 提供方向信号 (T001 disproven pure sign 但本候选是\n  sign × magnitude 复合, 非 pure\
  \ sign);\n  RHS=CsRank(Mean($pe_ratio,20)) 短窗 fundamental rank — 区别 pb_60 死路 (regime\
  \ sign-flip 风险\n  低于 60d), pe_20 在库内未充当 RHS;\n  预期 max_corr@F003<0.4 (signed magnitude\
  \ 与 |gap|/range 不同) + 验证 sign 复合是否破 T007 Barra trap。\n\nC003 higher-moment LHS 跨窗扩展\
  \ — Std(gap_ret,10): LHS=Std(Div(Sub($open,Ref($close,1)),Ref($close,1)),10)\n \
  \ 短窗 10d Std gap_ret (vs F020 LHS 是 Std,20 — 不同窗口测 higher-moment LHS axis 是否跨 10d\
  \ 仍存活);\n  RHS=CsRank(Mean(Abs(Div(Sub($close,Ref($close,1)),Ref($close,1))),60))\
  \ Amihud 分子 |return|_60\n  (新 RHS, 之前未用, 是 amihud_illiq 的纯 |return| 项不含 amount 分母);\n\
  \  预期 max_corr@F020<0.5 (10d vs 20d 同 LHS atom 跨窗 rank corr) — 这是关键 dedup 检查,\n\
  \  若 max_corr ≥0.7 即 rank-diff 第 3 律违反 (同字段跨窗口禁止) → 自动 reject。\n\nC004 gap-direction\
  \ concentration (HHI-like): LHS=Mean(Div(Sub($open,Ref($close,1)),Sub($high,$low)),20)\n\
  \  gap relative to intraday range (与 C001 b051 不同处: C001 b051 是 Mean(gap/(H-L))\
  \ 5d,\n  本候选 20d 长窗 + 已知 b051 C001 reserve, 测 20d 是否跨 reserve→admit 边界);\n  RHS=CsRank(Mean(Abs(Sub($close,Ref($close,1))),20))\
  \ 20d daily-return-magnitude rank\n  (区别 |return|_60 in C003);\n  预期 max_corr@F020<0.4\
  \ (Mean vs Std of gap) + max_corr@F003<0.5 (gap/(H-L) vs |gap|/Mean($high,5))。\n\
  \nC005 gap acceptance asymmetry — IF-conditional aggregation:\n  LHS=Mean(Mul(Sign(Sub($open,Ref($close,1))),\
  \ Mul(Sub($close,Ref($close,1)),Sign(Sub($open,Ref($close,1))))),20)\n  展开为 sign(gap)\
  \ × signed daily-return on gap-direction (上 gap 后 t 日是否同向跟随 / 下 gap 后是否同向跟随,\n \
  \ 捕捉 gap 持续性 — 区别 T001 sign×sign 因为带 magnitude); 等价于\n  Mean(Mul(Sub($close,Ref($close,1)),\
  \ Sign(Sub($open,Ref($close,1)))),20) /\n  上式经数学化简 = sign(gap) × daily_return ×\
  \ sign(gap) × Sign(Sub($open,Ref($close,1)))\n  实际表达式简化为 LHS= Mean(Mul(Sub($close,Ref($close,1)),Sign(Sub($open,Ref($close,1)))),20)\n\
  \  (sign×sign×magnitude → sign×magnitude when sign² = 1);\n  RHS=CsRank(Std($amount,20))\
  \ amount higher-moment (区别 amount_60 F023 RHS 用 Mean);\n  预期 max_corr@F013<0.5 (F013\
  \ 是 sign×sign×log-amount, 本是 sign×magnitude×amount-vol) +\n  破 T001 因带 magnitude\
  \ 不是纯 sign。\n\nC006 gap × volatility-of-volatility complex — 新 LHS family:\n  LHS=Std(Div(Abs(Sub($open,Ref($close,1))),Add(Mean(Abs(Sub($open,Ref($close,1))),20),0.0001)),20)\n\
  \  rolling-std of normalized |gap| (gap magnitude 相对 20d gap-magnitude 均值的 rolling\
  \ 离散度);\n  完全新 LHS atom — gap \"volatility of normalization\", 测 second-order gap\
  \ structure;\n  RHS=CsRank(Mean(Sub($high,$low),20)) 20d intraday range mean (新\
  \ RHS 维度, range 而非 vol);\n  预期 max_corr@F020<0.5 (本 LHS 是 normalized gap 的二阶矩 vs\
  \ F020 是 raw gap_ret 的 Std) +\n  max_corr@F019<0.5 (F019 LHS 是 Std body_ratio, 本是\
  \ Std normalized |gap|, atomic 不同)。"
last_activity: '2026-04-28T07:28:19Z'
created_batch: null
members:
- F013
- F{next}
- F020
merged_into: null
---
# gap_acceptance_structure

> [!abstract]+ 方向概要
> - **状态**　🟡 `saturated` · priority `low` · rounds = 6 · admits = 2 (F013 / F020)
> - **最近**　[[batches/batch_062/judge|batch_062]] · 2026-04-28 · 0/0/6 — T007 终结性 disproven · 7/7 thread resolved
> - **一句话**　两路 alpha 收完 (F013 log-amt sign agg + F020 rank-diff higher-moment gap)；T007 cross-ratio 全谱 dead-end；direction thread 闭合, anchor cluster (F002/F012/F020/F022) 锁死, 等外部 reactivation
> - **Anchor lock**: F020 已锁 LHS=Std(gap_ret,20); admit-anchor 占位律生效 — 同 family 任何新 candidate 必须脱 anchor cluster + alpha_surv ≥0.30 + incr_ic ≥0.015 才有 admit 资格

---

## Hypothesis

> [!warning] ⚠️ Hypothesis 部分证伪 + 升格律
> 原假设 "sign(gap) × sign(body) 20d 聚合在 csi1000 携带独立 alpha" **被硬性证伪** (T001+T003+T004 联立 disproven)：pure sign 在 10/20/60d 同步 sign_flip (2015-20 正 → 21-23 负 regime break)；分母变体 (Std(ret,20)) corr=0.964@F003；窗口扫描无 sweet spot。Paper CSI 300 Rank IC 0.0744 不可迁移到 csi1000 小盘 (升格 [[lessons#Paper Transferability|F302/F006]] default 律)。
>
> **存活两路**：
> 1. **F013 log(abnormal $amount) 加权 acceptance** (T002)：mono_OOS 0.30 → 0.60, IC_OOS=0.0094 anti-decay=1.36, 9/9 年同号；线性 ratio / CsRank / 40d 全 reject。
> 2. **F020 rank-diff geometry × higher-moment gap LHS** (T005)：`Sub(CsRank(Std(gap_ret,20)),CsRank(Mean(body_ratio,20)))`, IC_OOS=-0.040 mono=-1.0/-1.0 max_corr=0.246@F016 整库唯一<0.30, 是 [[lessons#Rank-Diff Geometry|F305]] higher-moment LHS independence axis 在 gap 家族复现。
>
> **元教训汇编**（已升格 lessons.md）：
> - **Sign aggregation 需 underlying drift** ([[lessons#Sign Aggregation Drift|F006]])：A 股日频 intraday body / gap 是 random walk, 必须 log(amount) drift proxy 加权才救。
> - **Rank-diff 7 硬约束** ([[lessons#Rank-Diff Geometry|F002/F305]])：scale-invariance / raw field 独立 / 同字段跨窗口禁止 / Sub 对偶 dedup / 同批 LHS anchor ≤1 admit / RHS 共振饱和动态 (dead RHS endpoints: overnight_5 / turnover_5 / amount_20 / body_ratio_20 / price_vol_20) / saturated 方向 anchor cluster (F002/F012/F020) 锁死。
> - **OHLC family defaults** ([[lessons#OHLC Family Defaults|F005/F306]])：gap 分母变体 (H-L / prev_close / Std(ret,20)) 全被 F003 主导 corr 0.79–0.96；起手前必做 affine-equivalence 检查。
> - **Meta-pattern transfer 先验底层 alive** ([[lessons#Meta-pattern Transfer|F303]])：log-compression 救 F013 是因 sign 已规整二值；同款 log 在 value × liquidity 6/6 fail (底层 PB/PS/PE rank 已死)。
> - **Threshold 校准** ([[lessons#Threshold Calibration|F200/F203]])：rank-diff alpha_surv_min=0.30；max_corr ∈ [0.30, 0.70] borderline 时 incr_ic ≥0.015 才 admit。
> - **Cross-ratio LHS 全谱 dead-end** (T007 升格)：ratio of two OHLC magnitudes (任何 sign/rank/ranged 复合) 在 rank-diff 几何 = ranked Barra style projection — sign 是 reflection symmetry, ranged normalize 是 ranked realized vol proxy；ranged-norm Mean 聚合窗口与 vol_20d 吸收单调正相关 (5d ≈0.30 → 20d+ ≈0.25 必收)。
> - **P006 library-reducer 第 7 次跨 family 复现 (gap_acceptance 首次)**：alpha_surv≥0.40 + library-reducer 双重检测必要 — Barra orthogonality ≠ library independence。

---

## Current Focus

- **Direction thread 完全闭合 (b062, 7/7 resolved)** · status `saturated` priority `low`
- **Harvested**: F013 (T002 log-amt sign agg) + F020 (T005 rank-diff higher-moment) — 不再 in-direction 探索
- **Anchor lock**: F020 占位 Std(gap_ret,20) LHS — 同 family 新 candidate 必须脱 anchor + alpha_surv ≥0.30 + incr_ic ≥0.015
- **Reactivation 触发**: (a) 新 paper 提供 atom-level 维度 (b) minute-bar 数据接入打开 intraday gap variance (c) F013/F020 退役释放 cluster 空间

---

## Threads

### T001+T003+T004: Paper-direct sign interaction 全谱 [✗ DISPROVEN batch_035]

> [!failure]+ 三 thread 联合结论 (合并)
> **Question (合并)**: paper acceptance signal `sign(gap) × sign(body)` N-day 聚合在 csi1000 上携带独立 alpha 吗 — pure sign / 分母量纲变体 / 窗口敏感性三轴。
>
> **Answer**: 否, 三轴同步证伪。
> - **T001 pure sign**: 10/20/60d hard_gate fail — 2015-20 正 → 21-23 负 regime break, csi1000 小盘 gap 符号是 random walk, 符号对称律**反号** (不抵消到零)
> - **T003 分母变体**: `Std($close-Ref($close,1),20)` 与 F003 corr=0.964 — gap magnitude 任意分母都被 F003 分子主导吸收, 子空间 closed
> - **T004 窗口扫描**: 10/20/60d 同病, 长窗 60d 反而放大 regime 反号 (oos_decay=-1.03 最重) — 是机制问题不是窗口问题
>
> **升格**: [[lessons#Sign Aggregation Drift|F006]] + [[lessons#OHLC Family Defaults|F005]] + [[lessons#Paper Transferability|F302]]
>
> **Evidence**: b035 C001 (20d) / C002 (10d) / C003 (60d) / C006 (magnitude×sign) 全 sign_flip+ic_oos_too_low+oos_decay; b035 C005 (Std-ret 分母) corr=0.964@F003 → 全 reject hard_gate

### T002: Acceptance × abnormal volume 加权 [✓ ANSWERED batch_036 → F013]

> [!success]+ Thread 结论
> **Question**: T001 acceptance 加权 `$amount/Mean($amount,20)` 或 `$volume/Mean(...)` 是否提供 incremental alpha?
>
> **Answer**: 仅在 **log 非线性压缩**下成立。线性 ratio (amount/volume/turnover TS-norm) + CsRank + 40d 全 fail；log(abnormal_amount) 压尾后 mono_OOS 0.30→**0.60**, IC_OOS=0.0094, anti-decay=1.36, 9/9 年同号 → admit F013。Paper 0.0744 → 0.0094 ~8x 衰减但结构稳。升格 [[lessons#Meta-pattern Transfer|F303]] (log-compression 救 sign×body 是因 sign 已规整二值, 跨方向不能机械复用)。
>
> **Evidence**: b035 C004 turnover 直加权 reserve (mono=0.30 barbell); b036 C001-C006 — C004 log(abnormal amount) admit → [[factors/F013]], C001/C002/C003 (linear ratio) reject, C005 (40d) reject (超 half-life=19d), C006 (CsRank turnover) reject (rank 化压平 magnitude)

### T005: rank-diff × gap 家族第 6 跨 family 兑现 [✓ ANSWERED batch_051 → F020]

> [!success]+ Thread 结论
> **Question**: rank-diff geometry 在 4 family 5 admit 后能否在 gap 家族独立兑现 → 6 跨 5 family tipping point?
>
> **Answer**: **是**。b051 C002 (`Sub(CsRank(Std(gap_ret,20)),CsRank(Mean(body_ratio,20)))`) admit 为 F020 — IC_OOS=-0.040 ICIR=-0.49 ls_t(IS)=-9.68 mono=-1.0/-1.0 + 9/9 年同号负 + max_corr=**0.246@F016** 整库唯一<0.30 + 与 5 admitted rank-diff (F015-F019) 全 |corr|<0.25。**6 跨 5 family confirmed** (microstructure×2 + overnight×2 + OHLC×1 + gap×1)。
>
> **三关键 admit 维度同时满足**: (1) higher-moment LHS (Std vs F010/F011 Mean) 跨 family 兑现 (2) 新 RHS body_ratio_20 (admit 后即 dead endpoint) (3) 窗口 20d 在 signal_half_life 内。
>
> 升格 [[lessons#Rank-Diff Geometry|F305]] 五律 + F002 7 条硬约束 + F200 alpha_surv_min.rank_diff=0.30 + F203 incr_ic_min=0.015 borderline 阈值。
>
> **Evidence**: b051 C001 (gap/(H-L) 20d × Std($close,5),60) reserve (max_corr=0.55@F018 + incr_ic=0.008 边际); C002 admit → [[factors/F020]]; C005 (gap/(H-L) 5d × price_vol_20) reject (max_corr=0.696@F017 cluster 共振)

### T006+T007: Rank-diff 长窗 + cross-ratio LHS 全谱 [✗ DISPROVEN batch_051+062]

> [!failure]+ 双 thread 联合结论 (合并)
> **Question (合并)**: gap atomic 在 60d 长窗下 rank-diff 能否兑现 (T006) + cross-ratio LHS (|gap|/|body| 跨 OHLC magnitude 比) 在 rank-transformed / sign / ranged 复合下能否破 Barra 吸收 (T007)?
>
> **Answer**: 全谱 dead-end。
> - **T006 60d 长窗双失效 (b051)**: raw |gap| 60d IC≈0.0006 完全 dilution (退化 log_market_cap rank); Std(gap_ret) 60d sign_flip (60d 含 2-3 regime cycle, **Std 比 Mean 对窗长更敏感**)。gap 家族 csi1000 必须 (a) scale-free normalization (b) 窗口 ≤20d。
> - **T007 cross-ratio Barra 全谱 (b051+b062, 4 类 follow-up)**: raw |gap|/|body| (alpha_surv=0.005 极端) → rank-transformed (b062 C001 ic_too_low 退化噪声) → signed cross-ratio (C002 alpha_surv=0.21 + incr_ic≈0, sign 是 cross-section reflection symmetry 不脱 Barra) → ranged-normalized 长窗 (C004 alpha_surv=0.26 + vol_20d=42.86 极端, 长窗放大 vol_20d 累积吸收) → signed daily-change × amount-Std (C005 alpha_surv=0.51 唯一 ≥0.40 BUT incr_ic=-0.0021 NEG, **P006 library-reducer 第 7 次跨 family**) → self-normalized 二阶 (C006 alpha_surv=0.019 critical + mono FLIP IS=-0.4 OOS=+1.0 regime-driven false discovery)。
>
> **3 升格律**: (1) cross-ratio LHS 全谱 dead-end — sign/rank/ranged 任意复合 = ranked Barra style projection; (2) ranged-normalized Mean 窗口与 vol_20d 吸收单调正相关 (5d ≈0.30 → 20d ≈0.25); (3) P006 第 7 次跨 family — Barra orthogonality 与 library independence 是两独立 cleanness 维度。
>
> **higher-moment 三模式互补**: (a) sign-flip 短窗跨 regime sample 不足 (b) mono cross-sample reversal — 二阶聚合放大 normalizer 自身 regime drift (c) regime-stable persistent loss — atom 单日嵌入 vol_20d 几何 (P003)。
>
> **Evidence**: b051 C003 (raw |gap| 60d) hard_gate; b051 C006 (Std gap_ret 60d) sign_flip; b051 C004 (cross-ratio raw, alpha_surv=0.005); b062 C001-C006 全 reject (详见 Known Failures)

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_035/candidates/C001\|b035 C001]] | `Mean(Sign(gap)×Sign(body), 20)` | hard_gate: sign_flip + ic_oos_too_low + oos_decay |
| [[batches/batch_035/candidates/C002\|b035 C002]] | 同 C001 @ 10d | hard_gate (短窗同病) |
| [[batches/batch_035/candidates/C003\|b035 C003]] | 同 C001 @ 60d | hard_gate (cum_dd=-4.18 最严重) |
| [[batches/batch_035/candidates/C005\|b035 C005]] | `Div(gap, Std(close-Ref(close,1),20))` | near_duplicate corr=0.964@F003 |
| [[batches/batch_035/candidates/C006\|b035 C006]] | `Mean(Div(gap, Mean($high,5))×Sign(body), 20)` | ic_oos_too_low (0.0058, mono=0.30) |
| [[batches/batch_036/candidates/C001-C003,C005,C006\|b036 C001/C002/C003/C005/C006]] | `Sign(gap)×Sign(body)` × {amount/volume/turnover linear ratio, 40d 窗, CsRank turnover} | 全 ic_oos_too_low (线性放大噪声 / 超 half-life / rank 化压平 magnitude) |
| [[batches/batch_051/candidates/C003\|b051 C003]] | `Sub(CsRank(Mean(\|gap\|,60)),CsRank(Mean($amount,60)))` | ic_oos_too_low (raw \|gap\| 60d 双 dilution) |
| [[batches/batch_051/candidates/C004\|b051 C004]] | `Sub(CsRank(Mean(\|gap\|/(\|body\|+ε),20)),CsRank(Mean($pb_ratio,60)))` | alpha_surv=0.005 + incr_ic=0.002 + ls_t=1.17 三 dealbreaker |
| [[batches/batch_051/candidates/C005\|b051 C005]] | `Sub(CsRank(Mean(gap/(H-L),5)),CsRank(Mean(Std($close,5),20)))` | max_corr=0.696@F017 cluster + alpha_surv=0.20 + incr_ic=0.003 |
| [[batches/batch_051/candidates/C006\|b051 C006]] | `Sub(CsRank(Std(gap_ret,60)),CsRank(Mean(\|return\|,60)))` | sign_flip (60d 多 regime cycle Std 失稳) |
| [[batches/batch_062/candidates/C001\|b062 C001]] | `Sub(CsRank(Mean(\|gap\|,20)),CsRank(Mean(\|body\|,20)))` | ic_oos_too_low (raw rank-diff 退化噪声) |
| [[batches/batch_062/candidates/C002\|b062 C002]] | signed cross-ratio × pe_20 | alpha_surv=0.21 + incr_ic=+0.0009 (sign 不脱 Barra) |
| [[batches/batch_062/candidates/C003\|b062 C003]] | `Sub(CsRank(Std(gap_ret,10)),CsRank(Mean(\|return\|,60)))` | hard_gate 三连 (Std 短窗 10d 跨 regime 不稳) |
| [[batches/batch_062/candidates/C004\|b062 C004]] | `Sub(CsRank(Mean(gap/(H-L),20)),CsRank(Mean(\|daily_change\|,20)))` | alpha_surv=0.26 + vol_20d=42.86 + incr_ic=0.0086 (长窗放大吸收) |
| [[batches/batch_062/candidates/C005\|b062 C005]] | `Sub(CsRank(Mean(daily_change×sign(gap),20)),CsRank(Std($amount,20)))` | alpha_surv=0.51 BUT incr_ic=-0.0021 NEG (P006 第 7 次跨 family) |
| [[batches/batch_062/candidates/C006\|b062 C006]] | self-normalized 二阶 × Mean(H-L,20) | alpha_surv=0.019 + mono FLIP (regime false discovery) |

---

## Related

- 🟢 [[overnight_intraday_split]] `productive` — F009/F010-F011/F017/F018; T005 与 F018 共享 F006 sign aggregation drift 律, F020 与 F017/F018 全 |corr|<0.25 正交
- 🟡 [[intraday_price_formation]] `saturated` — F003 gap baseline + F020 anti-anchor; T003+T007 共同验证 OHLC affine cluster trap
- 🟢 [[ohlc_temporal_aggregation]] `productive` — F019 (Std body_ratio) 是 higher-moment LHS axis OHLC 首例, F020 在 gap 家族复现 (family-agnostic 验证)
- 🔵 [[microstructure_illiquidity]] `productive` — F015/F016 rank-diff 起点; F020 max_corr=0.246@F016 cluster 内最低集中度
- 🟡 [[value_liquidity_interaction]] `saturated` — F002 anchor cluster 边界律; RHS 设计避 PB/PS 长窗 (b051 C004 alpha_surv=0.005 验证)
- 🔴 [[trend_quality_gated]] `dead` — paper Channel 3 transfer 失败二次确认 (与 T001 联立升格 F302)
- 🔴 [[log_value_liquidity]] `dead` — meta-pattern 跨方向失败对照 (F303 验证 log-compression 不可机械复用)
- 🔴 [[vol_shock_signals]] `dead` — magnitude vol 全 collapse 到 vol_20d; F020 dominant_style=vol_20d 但 style_r²≈0.30 (rank-diff structural exposure 非主阻断)
- 📖 [[papers/arxiv_2602_07085v2]] — paper intake 种子; T001 反证 transfer 失败, T002/T005 找出本地存活两路
- 📖 [[lessons#Paper Transferability]] · [[lessons#Sign Aggregation Drift]] · [[lessons#Rank-Diff Geometry]] · [[lessons#OHLC Family Defaults]] · [[lessons#Meta-pattern Transfer]] · [[lessons#Threshold Calibration]] — 贡献/引用 6 段

---

## Narrative Log

> [!quote]+ 2026-04-28 · [[batches/batch_062/judge|batch_062]] · 0/0/6 — T007 终结性 disproven, 7/7 thread 闭合
> - **T007 全谱 disproven**: 4 类 follow-up (raw rank-diff / signed cross-ratio / ranged 长窗 / signed-daily-change × amount-Std + Std-norm 二阶) 全 reject — sign 是 cross-section reflection symmetry, ranged norm 是 ranked realized vol proxy
> - **P006 library-reducer 第 7 次跨 family (gap_acceptance 首次)**: C005 alpha_surv=0.51 ≥0.40 BUT incr_ic=-0.0021 NEG — Barra ⊥ library 是两独立 cleanness 维度
> - **higher-moment 三失败模式互补**: sign-flip (短窗 sample 不足) / mono cross-sample reversal (二阶聚合放大 normalizer regime drift) / regime-stable persistent loss (atom 嵌入 vol_20d)
> - **Ranged-norm 窗口律**: vol_20d 吸收 monotone ↑ (5d≈0.30 → 20d+≈0.25 必收)
> - MT　cum 324→**330** · dir 24→**30** · bucket high→search_adjusted medium
> - **Ops**: status `productive→saturated` · priority `high→low` · T007 ACTIVE→DISPROVEN · zero_admit_streak 2→3 (b060/b061/b062) · 4 升格 lessons 候选

> [!quote]- 2026-04-25 · [[batches/batch_051/judge|batch_051]] · 1/1/4 — T005 ANSWERED → F020
> - **F020 admit** (`Sub(CsRank(Std(gap_ret,20)),CsRank(Mean(body_ratio,20)))`) IC_OOS=-0.040 mono=-1.0/-1.0 max_corr=0.246@F016 整库唯一<0.30 → 6 跨 5 family rank-diff tipping point confirmed
> - **三 admit 维度**: higher-moment LHS (Std vs Mean) 跨 family 兑现 + 新 RHS body_ratio_20 (admit 后即 dead) + 20d 在 half-life 内
> - **T006 disproven**: raw |gap| 60d IC≈0 + Std(gap_ret) 60d sign_flip — Std 比 Mean 对窗长敏感
> - **T007 active**: cross-ratio C004 alpha_surv=0.005 极端 collapse — 留 b062 follow-up
> - 升格 [[lessons#Rank-Diff Geometry|F305]] 五律 + F002 7 硬约束 + F200/F203 阈值
> - MT　cum 264→**270** · dir 12→**18** · **Ops**: saturated→productive 重启 + priority medium→high (admit=2)

> [!quote]- 2026-04-24 · [[batches/batch_036/judge|batch_036]] · 1/0/5 — T002 ANSWERED → F013
> - **F013 admit** log(abnormal $amount) 加权: mono_OOS 0.30→**0.60** IC_OOS=0.0094 anti-decay=1.36 (OOS>IS 极罕见) ls_t=3.23, 9/9 年同号
> - 5 reject 覆盖正交变体 (amount/volume/turnover linear, CsRank, 40d) → T002 future_probes preemptively closed
> - 关键: 线性 ratio 在 csi1000 2021+ regime 是噪声放大器, CsRank 压平 magnitude, 超 half-life=19d 稀释 — 仅 log 压尾保 magnitude + 抑极端
> - paper 0.0744 → 0.0094 ~8x 衰减但结构稳 (mono+9 年同号+anti-decay)
> - MT　cum 174→**180** · dir 6→**12** · **Ops**: T002 ACTIVE→ANSWERED · 维持 saturated

> [!quote]- 2026-04-24 · [[batches/batch_035/judge|batch_035]] · 0/1/5 — T001/T003/T004 联立 disproven 首批
> - **T001 pure sign 三窗口同步 sign_flip + ic_oos_too_low + oos_decay**: 2015-20 正 → 21-23 负 regime hard-disprove
> - **T003 分母变体**: Std-ret 分母 corr=0.964@F003 — gap magnitude 任意分母都 near_duplicate F003
> - **T004 窗口扫描**: 10/20/60d 同病, 60d 最重 — 是机制问题不是窗口问题
> - **T002 唯一正面证据**: C004 turnover 加权过全部 hard gate, mono=0.3 barbell → reserve 而非 admit, 留生路给 b036
> - paper 0.0744 Rank IC 不 transfer 到 csi1000 印证
> - MT　cum 168→**174** · dir 0→**6** · **Ops**: priority high→medium (T001/T003/T004 关闭, 留 T002 探索一次)
