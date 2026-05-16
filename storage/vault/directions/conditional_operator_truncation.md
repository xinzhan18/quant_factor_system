---
direction_tag: conditional_operator_truncation
status: saturated
priority: medium
rounds: 5
admits: 2
last_batch: batch_099
last_admits: []
last_goal: 'Round 99 / final round of /factor-mine 10-loop — data-driven extension
  of b098 admit F029

  (weak_close_day_rate_20, Mean(Lt((C-L)/(H-L), 0.2), 20), alpha_surv=1.10, ls_t=3.28,

  max_corr=0.32@F006). 6 候选沿 F029 family 三轴扩展: window (20d→60d, C001/C003), threshold

  (0.2→0.15, C002), aggregate wrap (Mean→Std, C003), mirror geometry (lower-shadow
  Lt 0.2,

  C004), threshold direction sanity (Gt 0.8 short window, C005), compound signal-only
  filter

  (weak-close × significant amplitude, C006). 验证 binarize direction+threshold 律

  (b098 round 10 升格) 在 F029 family 内的 axis-wise 行为. Goal: ≥1 admit OR explicit

  axis-wise 律升格 (window sweet spot / threshold sensitivity / Std-of-rate productive).'
last_activity: '2026-05-16T01:06:02Z'
created_batch: batch_097
members:
- F029
---
# Conditional Operator Truncation

## Hypothesis

库 28 admit 中 **F028** 是唯一使用条件算子族 (IfElse/Greater/Lt/Gt/Mask) 的因子 (DMI-down ratio: `Lt(...) × Greater(...)` 计数事件占比);
其余 26 个 admit **100% 线性算术形式** (Mul/Div/Sub/Add/Mean/Std/TsRank/Corr/Cov)。

**结构性 gap 假设**: 条件算子族 truncation（把一边信号清零 / 计数事件率 / mask-conditional aggregation）
构成 cross-section 上 distinct geometry，可能与库内 27 个线性算术因子保持 max_corr < 0.30 的同时
提供独立的 incremental IC。

**核心机制猜想**:
1. **离散化截断**: `Greater(x, 0)` 把信号下半段清零，cross-section 上变成 "上半段排序 vs 共同零值"，
   与连续线性形式 geometric 距离非零；
2. **事件率 aggregate**: `Mean(Greater(x, threshold), N)` 衡量"过去 N 天满足条件的天数占比"，
   是离散概率而非连续 path-integral（区别于 P004-deep N-day 累积形式）；
3. **条件 mask × 现有 admit**: `Mask(condition, signal, 0)` 让 signal 只在 condition 满足时存在，
   可能撬动 F019/F024 等 admit 的隐藏 alpha；
4. **Threshold-symmetric**: `Greater(x, c)` 和 `Greater(-x, -c)` 在 cross-section 上不等价
   （vs 线性 Mul(-1, x) 等价），破坏了线性 group 对称性。

## Threads

### T001: 上影占比 truncation [◉ ACTIVE] (b097 reserve hold, b098 mirror failed)

> [!warning]+ Thread 结论 (partial)
> **Question**: 上影长度占当日 range 的比例离散化为事件率后的 20d 平均是否构成独立 alpha？
>
> **Answer (partial)**: **borderline reserve hold**. b097/C001 实测 alpha_survival=**1.07** (Barra-clean), ls_t=+2.85 moderate, mono_oos=+0.80 强, max_lib_corr=0.41@F022 但 incremental_ic=0.0030 临界 → reserve. **b098 reciprocal mirror 实测 (close 上半段 Gt(.,0.5)) alpha_survival=0.50 borderline + ic_oos sign 反** → reject. **关键洞察 (b098)**: T001 reciprocal mirror 路径不可推广 — close 上半 vs 下半在 Barra basis 同构性显著不同, sign-dependent + threshold-dependent. b097/C001 上影主导日仍 reserve 不变.
>
> **Evidence trail**:
> - [[batches/batch_097/candidates/C001|batch_097 C001]]　`Mean(Gt((H-C)/(H-L), 0.5), 20)`　alpha_surv=1.07, ls_t=2.85, ic_oos=0.0088, max_corr=0.41@F022 → **reserve** (P030 2/4)
> - [[batches/batch_098/candidates/C001|batch_098 C001]]　`Mean(Gt((C-L)/(H-L), 0.5), 20)`　alpha_surv=0.50, ic_oos=-0.012 (反 expected), incr_ic=-0.006 → **reject (mirror not portable)**
> - [[batches/batch_099/candidates/C004|batch_099 C004]]　`Mean(Lt((H-O)/(H-L), 0.2), 20)` open-position mirror　ic_oos=+0.022 strong + ls_t=2.67 + mono=0.90 但 alpha_surv=**0.15** catastrophic (// str_1m basis) + incr_ic=-0.0023 → **reject**. **字段维度 mirror 不可推广**: open vs close 切换即跨入 momentum (str_1m) basis 吸收区, 与 T004 上涨日 mirror confirmation. binarize content **三要素 (字段+方向+阈值)** 决定 ⊥ basis (不仅是 b098 round 10 的 direction+threshold 二要素).
>
> **Next probes**: (a) b097/C001 + Python residualize on vol_20d (b096 blocker, 等 daily_python 模板); (b) T001 reciprocal & 字段 mirror 两路径都不可推广 — 子问题向 daily_python residualize 路径迁移.

### T007: small-body 主导日 binarize [✗ DISPROVEN batch_098]

> [!failure]+ Thread 结论
> **Question**: small-body 主导日 (|body|/range < 30%) 20d 占比是否构成独立 alpha?
>
> **Answer**: **disproven**. b098/C002 hard_gate ic_oos_too_low (0.0021 < 0.008). small-body candle geometry 在 csi1000 daily cross-section 信号几乎平坦 + mono_oos=0.0. body 维度 binarize **结构性失败** — body 大小与 vol_20d 高度共线 (大 body=高 vol), binarize 后信号被吸收近零.
>
> **Evidence trail**:
> - [[batches/batch_098/candidates/C002|batch_098 C002]]　`Mean(Lt(|C-O|/(H-L), 0.3), 20)`　ic_oos=0.0021, mono_oos=0.0 → **reject (CP01 hard_gate)**

### T008: range-position 弱端 truncation [✓ ANSWERED batch_098] (admit C004)

> [!success]+ Thread 结论
> **Question**: close-position 弱端离散化 ((C-L)/(H-L) < 0.2) 20d Mean 是否构成独立 alpha?
>
> **Answer**: **YES, admit**. b098/C004 ic_oos=+0.0095 + ls_t=**+3.28** strong (passes 3.0 admit floor) + alpha_survival=**1.10** Barra-clean (residual IC=+0.010 ≈ raw IC=+0.0095) + max_corr=0.32@F006 medium + 9 年 ic_by_year 全正 + mono_oos=+0.50 临界. 库内**第 2 个 conditional truncation rate 形式 alpha-clean** (与 b097/C001 上影主导日 1.07 同档级). 与 b097/C001 互补构成 "close-position 弱端 candle geometry" 子族.
>
> **Evidence trail**:
> - [[batches/batch_098/candidates/C004|batch_098 C004]]　`Mean(Lt((C-L)/(H-L), 0.2), 20)`　alpha_surv=1.10, ls_t=3.28, ic_oos=+0.0095, max_corr=0.32@F006 → **admit → [[factors/F029]]** (factor_name=`weak_close_day_rate_20`)
>
> **同 thread high阈版本 [✗ DISPROVEN batch_098]**:
> - [[batches/batch_098/candidates/C003|batch_098 C003]]　`Mean(Gt((C-L)/(H-L), 0.8), 20)`　hard_gate sign_flip + ic_oos_min + oos_decay → **reject (CP01 triple fail)**. 高阈 (0.8) close-position binarize regime instability, 80% 阈值在涨停日 (close==high) 被强制拉满, 引入 trend/vol regime sensitivity.
>
> **关键升格律 (b098 round 9)**: 同 (C-L)/(H-L) 信号底层, 不同 binarize 端 alpha_survival 显著不同 (Gt(.,0.5) 上半 0.50, Gt(.,0.8) 强端 hard_gate fail, Lt(.,0.2) 弱端 1.10) — binarize 方向 + 阈值都 sign/threshold dependent. left-tail thick (弱端) 是 robust escape, right-tail (强端) 是 vol_20d basis 共振更深.
>
> **batch_099 F029-family axis-wise extension (全 reject, 律密集升格)**:
> - [[batches/batch_099/candidates/C001|b099 C001]]　`Mean(Lt((C-L)/(H-L),0.2),60)` 60d 长窗　hard_gate sign_flip + ic_oos≈0 + oos_decay_neg → **reject**. F029 family **window 上限 < 60d**, 20d 是 sweet spot.
> - [[batches/batch_099/candidates/C002|b099 C002]]　`Mean(Lt(.,0.15),20)` 阈值 0.15　ic_oos=0.0080 borderline, max_corr=**0.82**@F029, incr_ic=**-0.0003** 负 → **reject (CP05 high)**. F029 在 threshold 维度是 **quasi-isolated point**, 0.2 微调即触发 near_dup.
> - [[batches/batch_099/candidates/C003|b099 C003]]　`Std(Lt(.,0.2),60)` Std 60d wrap　hard_gate fail, max_corr=0.6163 与 C001 数值同步 → **reject**. **Std-of-binarize ≡ Mean-of-binarize 60d 数学几乎等价** (Var(Bernoulli)=p(1-p) 在低事件率区与 p 共线), aggregate wrap 轴 dead.
> - [[batches/batch_099/candidates/C005|b099 C005]]　`Mean(Gt(.,0.8),10)` 短窗 10d　hard_gate ic_oos_too_low (-0.0040 < 0.008) → **reject**. **Gt 0.8 强端 binarize 在 10d & 20d 都 fail, b098 律 window-invariant**, window 不是 Gt 强端 escape 的关键维度.
> - [[batches/batch_099/candidates/C006|b099 C006]]　`Mean(Mul(Lt(.,0.2),Gt((H-L)/C,0.02)),20)` 复合 filter　hard_gate sign_flip + oos_decay_neg, vol_20d_exp=**45.18** 史诗 → **reject**. **Gt(amplitude) ≡ vol_20d direct proxy**, AND 复合时 vol_20d-isomorphic condition 主导 Barra basis 同构性, F029 ⊥ basis 优势被覆盖.
>
> **综合 family-space 拓扑结论 (b099 升格)**: F029 是 close-position × Lt × 0.2 阈值 × 20d × Mean × 单 condition 的**6 维约束孤立 admissible point**; 任一维度扰动 (window / threshold / aggregate / direction / compound) 即跨出 ⊥ basis 区. F029 周围邻域全 dead.
>
> **Next probes**: (a) T008 family-space 已 systematically mapped, exhausted; (b) F028 (DMI conditional) 邻域 axis-wise 扩展 (尚未做); (c) **跳出 candle-geometry binarize 子族**: 探索 turnover-binarize / fundamental-binarize / momentum-binarize 等其它 conditional content; (d) b097/C001 reserve hold 等 daily_python residualize 模板.

### T009: 跨日 candle-pattern (engulfing reversal) [✗ DISPROVEN batch_098]

> [!failure]+ Thread 结论
> **Question**: 跨日反向 body pattern (一阴一阳 reversal) 60d 占比是否构成 alpha?
>
> **Answer**: **disproven**. b098/C006 hard_gate sign_flip + oos_decay_neg. **跨日 candle-pattern 是 regime-dependent, 不构成 stable cross-section signal**. candle-pattern binarize 路径有效性**仅限单日内 geometry** (shadow, close-position), 跨日 pattern dead.
>
> **Evidence trail**:
> - [[batches/batch_098/candidates/C006|batch_098 C006]]　`Mean(Gt((C-O)×(Ref(O,1)-Ref(C,1)), 0), 60)`　hard_gate sign_flip + oos_decay → **reject**

### T002: gap event rate (cross-day) [✗ DISPROVEN batch_098]

> [!failure]+ Thread 结论
> **Question**: 60d gap-up 事件率是否构成独立 alpha (跨阈值)？
>
> **Answer**: **definitively disproven, 跨阈值 family-wide dead**. b097/C002 (0.5% 阈, alpha_surv=0.13 + vol_20d=27.6) + b098/C005 (1.5% 阈, alpha_surv=**0.030** + vol_20d=**35.4**) — **提高阈值反而恶化** alpha_survival (0.13 → 0.03, 恶化 4×) + vol_20d_exp 反而上升 (27.6 → 35.4). gap-event 内容自身 ≡ vol_20d basis 信号 source (overnight gap 自身是 daily vol marker), threshold tuning 不解决. T002 family **任何 gap-threshold binarize + Mean aggregate 都 // vol_20d basis**, 结构性 dead.
>
> **Evidence trail**:
> - [[batches/batch_097/candidates/C002|batch_097 C002]]　`Mean(Gt($open/Ref($close,1), 1.005), 60)`　alpha_surv=0.13, vol_20d=27.6, ls_t=-0.61 → **reject (CP04 catastrophic)**
> - [[batches/batch_098/candidates/C005|batch_098 C005]]　`Mean(Gt($open/Ref($close,1) - 1, 0.015), 60)`　alpha_surv=**0.030**, vol_20d=**35.4**, style_r²=0.335 → **reject (P004-deep 跨阈值实证)**
>
> **Lessons-promotion candidate**: "T002 gap-event rate family 跨阈值结构性 dead: gap content // vol_20d basis 是 source-level 同构 (overnight gap 自身是 daily vol marker), threshold tuning 不解决"

### T003: mask × raw turnover [✗ DISPROVEN batch_097]

> [!failure]+ Thread 结论
> **Question**: `Mul(Gt(TsRank60,0.8), $turnover_rate)` mask + raw magnitude 是否构成独立 alpha？
>
> **Answer**: **disproven**. C003 alpha_survival=0.15 + vol_20d_exp=37.4 catastrophic + style_r²=0.52 poor → **partial truncation (mask × raw_magnitude) ≠ full binarize event rate**. 保留 raw turnover magnitude 信息 → 100% vol_20d basis 吸收. 必须 **full binarize 才可能产生 distinct geometry**.
>
> **Evidence trail**:
> - [[batches/batch_097/candidates/C003|batch_097 C003]]　`Mean(Mul(Gt(TsRank($turn,60),0.8), $turn), 20)`　alpha_surv=0.15, vol_20d=37.4 → **reject (CP04 catastrophic)**
>
> **Lessons-promotion candidate**: "partial truncation (mask × raw_magnitude) ≠ full binarize event rate — 前者保留连续 magnitude 信息被 style basis 吸收"

### T004: 上涨日占比 (win rate) [✗ DISPROVEN batch_097]

> [!failure]+ Thread 结论
> **Question**: 20d 上涨日占比是否构成独立 alpha？
>
> **Answer**: **disproven**. C004 alpha_survival=**0.07** (本批最低 catastrophic) + str_1m_exp=5.45 (本批最高) → **上涨日占比 ≈ str_1m basis 的 direct proxy**. return-sign 与 short-term reversal style 同构, full binarize 不能逃脱 basis 吸收 IF binarized content 同构 basis.
>
> **Evidence trail**:
> - [[batches/batch_097/candidates/C004|batch_097 C004]]　`Mean(Gt($close/Ref($close,1), 1.0), 20)`　alpha_surv=0.07, str_1m=5.45 → **reject (CP04 catastrophic)**

### T005: 低振幅日占比 [✗ DISPROVEN batch_097]

> [!failure]+ Thread 结论
> **Question**: 60d 低振幅日 (相对振幅<3%) 占比是否构成独立"压缩期" alpha？
>
> **Answer**: **disproven**. C005 ic_oos=+0.057 (本批最强 IC magnitude) 但 alpha_survival=0.22 + vol_20d_exp=**46.8** (本批最高, 是 catastrophic 的 catastrophic) + max_corr=0.66@F021 → **低振幅日占比 ≈ vol_20d basis 反向 direct proxy**. 即使 ic 强 + mono 强, Barra 残差 alpha 几乎不存在.
>
> **Evidence trail**:
> - [[batches/batch_097/candidates/C005|batch_097 C005]]　`Mean(Lt((H-L)/$close, 0.03), 60)`　ic_oos=0.057, vol_20d=46.8, max_corr=0.66 → **reject (CP04 catastrophic + CP05 high)**

### T006: PV-corr gated momentum [✗ DISPROVEN batch_097]

> [!failure]+ Thread 结论
> **Question**: 10d PV-corr>0 期间取 20d momentum 是否构成独立 alpha？
>
> **Answer**: **disproven**. C006 ic_oos=-0.035, ls_t=-3.57 strong CP03, **but** style_r²=**0.71** catastrophic (本批最高) + str_1m_exp=7.77 + max_corr=0.55@F027 → **conditional observation (If × continuous signal) 当 continuous signal 与 Barra style 同构时, gating 仅 filter sample 不破 absorption**. P030 paradox guard 反例: alpha_surv=0.83 看似 OK + style_r²=0.71 catastrophic 同存, 验证 alpha_surv 单看不够必须 combined 检查.
>
> **Evidence trail**:
> - [[batches/batch_097/candidates/C006|batch_097 C006]]　`If(Gt(Corr(C,V,10),0), 20d_mom, 0)`　style_r²=0.71, str_1m=7.77, alpha_surv=0.83 paradox → **reject (CP04 catastrophic)**
>
> **Lessons-promotion candidate**: "Conditional observation (If × continuous signal) 不破 absorption — gating 仅 filter sample, 必须 aggregate to event rate (full binarize + Mean) 才可能产生 distinct geometry"

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_097/candidates/C002\|C002]] | `Mean(Gt($open/Ref($close,1),1.005),60)` | CP04 catastrophic: alpha_surv=0.13 + vol_20d_exp=27.6; 60d binarized gap rate 仍被 vol_20d basis 吸收 |
| [[batches/batch_097/candidates/C003\|C003]] | `Mean(Mul(Gt(TsRank($turn,60),0.8),$turn),20)` | CP04 catastrophic: alpha_surv=0.15 + vol_20d_exp=37.4 + style_r²=0.52; partial truncation 保留 raw magnitude → 100% basis 吸收 |
| [[batches/batch_097/candidates/C004\|C004]] | `Mean(Gt($close/Ref($close,1),1.0),20)` | CP04 catastrophic: alpha_surv=**0.07** (本批最低) + str_1m_exp=5.45; return-sign 与 str_1m basis 同构 |
| [[batches/batch_097/candidates/C005\|C005]] | `Mean(Lt(($high-$low)/$close,0.03),60)` | CP04 catastrophic + CP05 high: alpha_surv=0.22 + vol_20d_exp=**46.8** (本批最高) + max_corr=0.66@F021; 低振幅日占比 ≈ vol_20d 反向 proxy |
| [[batches/batch_098/candidates/C001\|b098 C001]] | `Mean(Gt((C-L)/(H-L),0.5),20)` | mirror of b097/C001 alpha_surv=0.50 临界 + ic_oos sign 反 expected_sign + incr_ic=-0.006 库削减; reciprocal mirror 不可推广, close 上半 vs 下半 Barra basis 同构性显著不同 |
| [[batches/batch_098/candidates/C002\|b098 C002]] | `Mean(Lt(\|C-O\|/(H-L),0.3),20)` | CP01 hard_gate ic_oos_too_low (0.0021 < 0.008); small-body 信号在 csi1000 cross-section 几乎平坦, body 维度 binarize 失败 (body 与 vol_20d 共线) |
| [[batches/batch_098/candidates/C003\|b098 C003]] | `Mean(Gt((C-L)/(H-L),0.8),20)` | CP01 triple fail: sign_flip + ic_oos_min + oos_decay neg; 高阈 (0.8) close-position binarize regime instability, 涨停日 close==high 强制拉满引入 trend/vol regime sensitivity |
| [[batches/batch_098/candidates/C005\|b098 C005]] | `Mean(Gt($open/Ref($close,1)-1,0.015),60)` | CP04 poor: alpha_surv=**0.030** + vol_20d=**35.4** + style_r²=0.335; 提高阈值反而恶化 alpha_survival, gap-event family 跨阈值结构性 dead |
| [[batches/batch_098/candidates/C006\|b098 C006]] | `Mean(Gt((C-O)*(Ref(O,1)-Ref(C,1)),0),60)` | CP01 sign_flip + oos_decay neg; 跨日 candle-pattern regime-dependent, candle-pattern binarize 路径有效性仅限单日内 geometry |
| [[batches/batch_097/candidates/C006\|C006]] | `If(Gt(Corr(C,V,10),0),Sub(C/Ref(C,20),1),0)` | CP04 catastrophic: style_r²=**0.71** (本批最高) + str_1m_exp=7.77 + max_corr=0.55@F027; conditional observation gating 不破 momentum-basis 同构 |
| [[batches/batch_099/candidates/C001\|b099 C001]] | `Mean(Lt((C-L)/(H-L),0.2),60)` | CP01 hard_gate sign_flip + ic_oos≈0 + oos_decay_neg; F029 family **window 上限 < 60d**, 长窗 weak-close OOS 信号完全消失 |
| [[batches/batch_099/candidates/C002\|b099 C002]] | `Mean(Lt((C-L)/(H-L),0.15),20)` | CP05 high: max_corr=**0.82**@F029 + incremental_ic=**-0.0003** 负增量; F029 在 threshold 维度是 quasi-isolated point, 阈值微调即触发 near_dup |
| [[batches/batch_099/candidates/C003\|b099 C003]] | `Std(Lt((C-L)/(H-L),0.2),60)` | CP01 hard_gate sign_flip + ic_oos≈0; **Std-of-binarize ≡ Mean-of-binarize 60d 数学几乎等价** (Var(Bernoulli)=p(1-p) 低值区与 p 共线), aggregate wrap 轴 dead |
| [[batches/batch_099/candidates/C004\|b099 C004]] | `Mean(Lt((H-O)/(H-L),0.2),20)` | CP04 **poor**: alpha_survival=**0.15** catastrophic + str_1m=3.66 + incr_ic=**-0.0023**; **字段维度 mirror 不可推广** — open vs close 切换即跨入 str_1m basis 吸收区 |
| [[batches/batch_099/candidates/C005\|b099 C005]] | `Mean(Gt((C-L)/(H-L),0.8),10)` | CP01 hard_gate ic_oos_too_low (-0.0040<0.008); **b098 律 window-invariant**, Gt 0.8 强端 binarize 在 10d & 20d 都 fail, window 不能 rescue |
| [[batches/batch_099/candidates/C006\|b099 C006]] | `Mean(Mul(Lt((C-L)/(H-L),0.2),Gt((H-L)/C,0.02)),20)` | CP01 hard_gate sign_flip + oos_decay_neg, vol_20d_exp=**45.18** 史诗 catastrophic; **Gt(amplitude) ≡ vol_20d proxy**, AND 复合时 vol_20d-isomorphic condition 主导 Barra basis, F029 ⊥ basis 优势被覆盖 |

---

## Related

- 🥉 [[factors/F028|F028]] — `dmi_down_ratio_12` — 库内唯一条件算子 admit，本方向 anchor precheck 必看 max_corr
- 🥉 [[factors/F021|F021]] — `upper_shadow_disp_range_compress_rd_20` — T001 上影占比的 dispersion 对偶
- [[lessons#Path Selection]] (P004-deep path-integral) — T002/T004 离散事件 aggregate 必须自检
- [[lessons#Anti-Recapitulation]] — F028 anchor cluster precheck

---

## Narrative Log

> [!quote]+ 2026-05-16 · [[batches/batch_099/judge|batch_099]] judge
> **F029 family axis-wise extension 全 reject + status productive → saturated** · admit=**0** / reserve=0 / reject=**6** (C001-C006 全)
>
> - **6 候选沿 F029 family 三轴扩展全部 fail**: window (60d → OOS 信号归零, C001 + C003), threshold (0.2→0.15 → near_dup F029 corr=0.82 + incr_ic 负, C002), aggregate wrap (Std vs Mean 60d 数学几乎等价, C003), field mirror (open vs close → str_1m basis 吸收 alpha_surv=0.15, C004), short-window Gt 0.8 (window-invariant fail 验证 b098 律, C005), compound vol-filter (Gt(amplitude)≡vol_20d proxy, F029 ⊥ basis 优势被覆盖 vol_20d_exp=45.18 史诗, C006).
> - **核心 family-space 拓扑结论**: **F029 = close-position × Lt × 0.2 × 20d × Mean × 单 condition 的 6 维约束孤立 admissible point**, 周围邻域全 dead. F029 不是 family-cluster 中心点而是 quasi-isolated singularity.
> - **关键升格律 (b099 round 99, 4 条)**:
>   1. F029 family axis-wise 行为律: F029 是 6 维约束孤立 point, 任一维度扰动跨出 ⊥ basis 区
>   2. **Std-of-binarize ≡ Mean-of-binarize 60d 数学等价律** (跨 family 普适): Var(Bernoulli)=p(1-p) 低值区与 p 共线, second moment 不构成正交几何
>   3. **Compound vol-isomorphic condition 反弹律** (跨 family 普适): AND 复合两 condition 时 vol_20d-isomorphic condition 会主导 Barra basis 同构性
>   4. **binarize content 三要素 (字段+方向+阈值) 决定 ⊥ basis** (b098 round 10 律精化): 仅同 geometry framework 不足够, 字段切换即跨入 momentum basis
> - **Calibration trigger 状态**: zero_admit_streak 0 → **1** (本批 reset 后再起); rounds_since_consolidation 8 → **9**. 错杀侦测扫描: 无候选满足 4 件套 (C002/C004 incr_ic 都负, 不满足 incremental_ic>0.010).
> - **MT Budget**: cumulative 552 → **558** · direction **18** · bucket `high` (全 6 候选), search_adjusted 1 medium 多数 low — 同方向重复搜索回报递减信号明确.
>
> **Operations**　`status: productive → saturated` · priority `high → medium` · admits 保持 2 (F028+F029) · 本方向 9 batches/累积 30 candidates, admit rate=6.7% 低于 productive 阈值 (~15%).
> **下一步**:
> - (a) T008 family-space 已 systematically mapped exhausted, 后续探索需**跳出 F029 邻域**
> - (b) **F028 邻域 axis-wise 扩展** 尚未做 — DMI conditional 是库内另一 conditional anchor
> - (c) **跳出 candle-geometry binarize 子族**: 探索 turnover-binarize / fundamental-binarize / momentum-binarize 等其它 conditional content
> - (d) **b097/C001 reserve hold + Python residualize**: 等 daily_python 模板成熟
> - (e) **lessons-promotion 4 条 (上述律)**: orchestrator 下轮 consolidation (round 100, 距离 10 还有 1 轮触发) 应升格

> [!quote]- 2026-05-16 · [[batches/batch_098/judge|batch_098]] judge
> **T008 弱端 close-position binarize admit + T001 reciprocal mirror dead + T002 跨阈值 dead** · admit=**1** (C004→F{next} `weak_close_day_rate_20`) / reserve=0 / reject=5
>
> - **C004 admit** (弱收盘日 20d 占比, `Mean(Lt((C-L)/(H-L), 0.2), 20)`): alpha_survival=**1.10** Barra-clean + ls_tstat=**+3.28** strong + max_corr=0.32@F006 + 9 年 ic_by_year 全正. **库内第 2 个 conditional truncation rate 形式 alpha-clean** (与 b097/C001 上影主导日 1.07 同档级). **打破 9-batch zero_admit_streak** (9 → 0).
> - **C001 reject** (close 上半段 50% 阈, reciprocal mirror of b097/C001): alpha_survival=0.50 borderline + ic_oos sign 反 + incr_ic=-0.006 → mirror not portable. **关键洞察**: T001 reciprocal mirror 路径不可推广, close 上半 vs 下半 Barra basis 同构性显著不同.
> - **C003 reject** (强收盘日 80% 阈): CP01 sign_flip ×3. **高阈 binarize regime instability** — 80% 阈值在涨停日 (close==high) 强制拉满, 引入 trend/vol regime sensitivity.
> - **C005 reject** (gap-up 高阈 1.5% 60d, T002 跨阈值复测): alpha_survival=**0.030** + vol_20d=**35.4** **比 b097/C002 (0.5% 阈, 0.13) 更恶化** — **T002 family 跨阈值结构性 dead**, gap-event 内容自身 ≡ vol_20d basis 信号 source.
> - **C002 reject (T007)** (small-body 主导日): CP01 ic_oos_too_low (0.0021 平坦). body 维度 binarize 失败 — body 大小与 vol_20d 共线.
> - **C006 reject (T009)** (跨日反向 body pattern): CP01 sign_flip + oos_decay. **跨日 candle-pattern regime-dependent**, candle-pattern binarize 路径有效性**仅限单日内 geometry**.
> - **核心升格律 (round 9 → 进一步升级)**: 同 (C-L)/(H-L) 信号底层, 不同 binarize **方向 + 阈值** alpha_survival 显著不同 (Gt(.,0.5) 上半 0.50, Gt(.,0.8) 强端 fail, Lt(.,0.2) 弱端 1.10) — binarize 方向 + 阈值都 sign/threshold dependent. **left-tail thick (弱端) 是 robust escape, right-tail (强端) 是 vol_20d basis 共振更深**.
>
> **MT Budget**: cumulative 546 → **552** · direction 6 → **12** · bucket 全 high (search_adjusted 部分降至 medium/low).
>
> **Calibration trigger 状态**: zero_admit_streak 9 → **0 reset** (admit C004 验证 lessons round 91 升格律, 系统 calibration 正确, 没有错杀真 alpha). 错杀侦测扫描: 无候选满足 4 件套.
>
> **Operations**　`status: exploring` · rounds 1→2 · admits 0→**1** (C004) · reserves +0 (b097/C001 保留 reserve pool)
> **下一步**: (a) **T008 extension (下批)**: C004 base + extension wraps (Std/Skew of weak_close_day rate, 60d 窗口); 阈值变体 Lt(.,0.15)/Lt(.,0.25); 弱收盘日 + reversion gate 复合; lower-shadow 主导日 (Lt of (H-C)/(H-L)) 真镜像 T001; (b) **lessons-promotion 三条 (round 91 律进一步升格)**: binarize 方向 + 阈值 sign/threshold dependent / T002 family 跨阈值 dead / 跨日 candle-pattern dead 单日内 geometry productive; (c) orchestrator 检查 consolidation trigger (rounds_since 8 → 距离 10 还有 2 轮).

> [!quote]- 2026-05-16 · [[batches/batch_097/judge|batch_097]] judge
> **结构性 gap 假设部分验证 — Binarized event-rate 路径 admit 可行性严格依赖 binarized content ⊥ Barra style basis** · admit=0 / reserve=1 (C001) / reject=5
>
> - **C001 是唯一 productive candidate** (上影主导日 20d 占比): alpha_survival=**1.07** (Barra-clean, residual IC ≈ raw IC) + ls_t=2.85 moderate + mono_oos=+0.80 强 + max_corr=0.41@F022; P030 paradox guard 三条件仅满足 2/4 (alpha_surv + ls_t, 但 max_corr & incr_ic 临界) → reserve. **库内 0 个 conditional truncation event rate admit, C001 推进 conditional family 路径到 "borderline admit territory"**.
> - **C002/C004/C005 三个 full binarize event rate 全 reject**: alpha_survival ∈ [0.07, 0.22] catastrophic, vol_20d_exp ∈ [13.6, 46.8] 全 catastrophic. **机制揭示**: full binarize 不能保证 escape — 当 binarized 内容与 Barra style basis 同构 (gap-up rate ≈ vol_20d, return-sign rate ≈ str_1m, low-amp rate ≈ vol_20d 反向) 时, 100% basis 吸收.
> - **C003 mask × raw turnover reject**: alpha_survival=0.15 + vol_20d_exp=37.4 → **partial truncation 不构成 escape** (保留 raw magnitude → 与 raw turnover Mean 几乎等价).
> - **C006 conditional observation (If × continuous signal) reject**: style_r²=**0.71** catastrophic (本批最高) + str_1m_exp=7.77 + alpha_surv=0.83 paradox (P030 反例: alpha_surv 看似 OK 但 style_r² catastrophic) → **gating × continuous signal 不破 absorption**.
> - **核心 lesson**: conditional truncation 路径的 admit 充分条件不是"用了 Gt/Lt/If 就行", 而是 **binarized content ⊥ Barra style basis**. C001 (candle geometry 衍生 event rate) 是唯一满足该条件的几何, alpha_surv=1.07 验证. 其它 5 候选 binarized 内容都同构某 Barra style.
> - **P004-deep 律本质升格**: 不是"path-memory β-shift 消失", 而是 **"long-window aggregate 必然与 style basis 频谱共振 IF binarized content 同构 basis"**. binarize 只是 path-memory 消除的必要条件, 不是充分条件; 内容正交 basis 才是真充分条件.
>
> **MT Budget**: cumulative 540 → **546** · direction 0 → **6** · bucket `medium` (search_adjusted 0.32-0.59).
>
> **Calibration trigger 状态**: 已 true from b095/b096; 本批是结构性新方向探索 (NEW direction, NOT rank-diff dead-spiral 加深) — 验证了 conditional family 路径的 admit 可行性区间. zero_admit_streak 8→9. 错杀侦测扫描: 无候选满足 4 件套 (C001 max_corr=0.41 > 0.30, incremental_ic=0.0030 < 0.010).
>
> **Operations**　`status: exploring (NEW)` · rounds 0→1 · admits 0 · reserves +1 (C001)
> **下一步**: (a) **T001 几何扩展** (下批): C001 base + binarize content 变体 (下影主导日 / middle-body 占比 / range-position 离散化 / 多重 candle event rate); (b) C001 + Python residualize on vol_20d (b096 blocker — daily_python registry 待开发); (c) **lessons-promotion 三条**: conditional truncation admit 充分条件 / P004-deep 律本质升格 / conditional observation 不破 absorption; (d) orchestrator 下轮可考虑 calibration 流程对 reserve pool 整体重评估 (C001 加入 ranks-diff reserve 池, 共 8 候选).

> [!quote]- 2026-05-16 · batch_097 design
> **新方向创建** — 结构性缺口探索。库 28 admit / 27 线性算术 + 1 条件算子 (F028) → 显式 conditional
> operator family 存在 untapped territory。6 候选覆盖 6 子族 (T001-T006)：上影截断 / gap 事件率 /
> mask 条件流 / 上涨日占比 / 低振幅占比 / 条件动量。
>
> Self-check 5 hard rule:
> - **P030**: 全 6 候选 multi-CP rationale, 不依赖 alpha_surv 单边
> - **P004-deep borderline**: T002/T004 是 Sum/Mean of {0,1} 离散事件 truncate 后 aggregate —
>   理论上 path-memory 不存在 (β shift 在二值化后被丢弃)，但 path-integral form 边界需 case-by-case
>   Phase 3 实证 (manifest 候选 rationale 显式标注 borderline-discrete)
> - **F028 anchor precheck**: F028 是 IfElse-style ratio 形式，本批 6 候选不复制 DMI 上下行计数结构
>   (F028 用 Lt(H+L, prev_H+prev_L) × Greater(|ΔH|, |ΔL|) 复合, 本批 6 候选无此双 Lt×Greater 复合)
> - **Reciprocal duplicate**: `Greater(x,0)` 和 `Less(-x,0)` 是 sign-flip 镜像，本批避开
> - **Paper transferability**: 无外部 paper, 纯 structural 探索, 标 paper=none
>
> **Operations**　`status: exploring (NEW)` · priority `high`
