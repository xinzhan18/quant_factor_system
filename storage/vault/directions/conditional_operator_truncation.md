---
direction_tag: conditional_operator_truncation
status: productive
priority: high
rounds: 4
admits: 2
last_batch: batch_098
last_admits:
- F029
last_goal: "Round 98 — data-driven extension of b097/C001 binarize-axis success.\n\
  b097/C001 上影主导日占比 alpha_surv=1.07 (Barra-clean reserve) — 全 6 中唯一 binarize\n内容 ⊥\
  \ Barra basis 的几何; 其余 5 子族 binarized content 同构 vol_20d / str_1m basis\n→ 100% absorption.\n\
  \n**核心律 (b097 实证)**: full binarize + Mean aggregate 仅在 binarized 内容\n⊥ Barra style\
  \ basis 时产生 distinct geometry; binarize 形式独特不够, 内容必须 distinct.\n\n**本批 hypothesis**:\
  \ candle-geometry content (上/下/中-body 占比, range-position 高/低位)\n都属于 candle-geometry\
  \ derivative, 应与 9-style Barra basis (size/vol_20d/momentum/value/\nquality/turnover/leverage/eps/str_1m)\
  \ 均不同构 → 期望多数 candidate 达到 alpha_surv ≥ 0.5\n+ ls_t ≥ 2.0 borderline, ≥1 admit (max_corr<0.40,\
  \ ls_t≥3.0, alpha_surv≥0.5, incr_ic≥0.005).\n\nQlib runtime op 实测可用: Gt/Lt (boolean),\
  \ Mean, Sub, Div, Abs, Mul, Ref. **不用 If/IfElse**\n(b097 C006 中 If × continuous\
  \ → str_1m 100% 吸收, 已 disprove). 全 6 候选走 full binarize\n+ Mean rate aggregate 路径.\n\
  \n**6 候选覆盖**:\n- C001 下影主导日占比 20d (T001 sign-flip镜像 / reciprocal duplicate 风险, 必精测)\n\
  - C002 small-body 主导日占比 20d (candle geometry 新维度, |close-open|/range < 0.3)\n- C003\
  \ range-position 高位主导日占比 20d ((close-low)/range > 0.8)\n- C004 range-position 低位主导日占比\
  \ 20d ((close-low)/range < 0.2)\n- C005 60d gap-up event rate (低阈 0.5%) — b097/C002\
  \ (阈 0.5%, 60d) sign-flip 不重测; 走\n  **强 gap-up 0.5% 60d 已 disprove**, 本批改 60d gap-up\
  \ event rate 复测但**更高阈 1.5%**\n  隔离 cross-day return 同构 vol_20d 风险\n- C006 60d engulfing\
  \ pattern rate (反向 candlestick reversal: 当日 body 与 前日 body 同号\n  + 当日 body 更大) —\
  \ 复合事件率, 新 geometry\n\n**Self-check 5 hard rule (P030 + P004-deep升格 + F028 + reciprocal\
  \ + Cov-equiv)**:\n- **P030**: 全 6 multi-CP rationale, 不依赖 alpha_surv 单边\n- **P004-deep\
  \ 升格 (b097 round 9 升格)**: long-window aggregate 必然与 style basis 频谱\n  共振 IF binarized\
  \ content 同构 basis. 本批 C001-C004 candle geometry, 已知与 9-style\n  不同构; C005 高阈 gap-up\
  \ 1.5% 走 60d aggregate, 风险**仍可能**与 vol_20d 频谱共振 — 显式\n  标注 borderline; C006 engulfing\
  \ 是 cross-day candlestick pattern, 不是 return 信号, 风险\n  较低. Phase 3 judge 若发现 vol_20d_exp\
  \ > 15 或 alpha_surv < 0.4 则该子族证伪.\n- **F028 anchor**: F028 用 Lt×Greater 双 condition\
  \ 比值, 本批 6 候选无双 condition 复合\n  → distinct\n- **b097/C001 anchor (round 9 新 reserve)**:\
  \ C001 (本批 下影主导日) 是 b097/C001 (上影主\n  导日) 的 sign-flip 镜像 — Gt((C-L)/(H-L), 0.5)\
  \ 等价于 Lt((H-C)/(H-L), 0.5), 二值化在\n  cross-section 上**可能产生互补但不严格 sign-flip** (因 close==(H+L)/2\
  \ 时两者同时 False\n  构成 \"middle-body day\"). 必跑 Phase 2 max_corr 实测; 预期 |corr|<0.7\
  \ 但 >0.3.\n- **Reciprocal duplicate**: C001 vs b097/C001 (sign-flip 风险); C003 vs\
  \ C004 (互补对偶高\n  位/低位, 中间 [0.2, 0.8] 是 \"middle-position day\" 共同 False, 非严格互补).\
  \ 本批不并列覆\n  盖 reciprocal 子族 (单边)\n- **Cov-equiv (P028)**: 无 Cov atom; 无 cross-section\
  \ OLS residualize (DSL only)\n\n**Anchor avoidance**:\n- F028 (DMI down-ratio):\
  \ 双 condition 复合, distinct\n- F021 (shadow_disp): F021 用 Std/dispersion 连续, 本批用\
  \ truncate+rate 离散, geometry 不同\n- b097/C001 (reserve, 上影主导日占比): 本批 C001 是 reciprocal\
  \ 镜像 — 必精测 max_corr\n- F022 (b097/C001 nearest@max_corr=0.41): 同样 candle-position\
  \ 路径相关, 注意\n- F019/F020 (gap rank-diff): C005 走 truncation+Mean 而非 rank-diff, geometry\
  \ 不同\n\n**Baseline-first 守则 explicit skip**: 15 untouched TTM 字段无法支撑 daily candle\
  \ geometry\nevent counting (TTM 季度更新). 显式 skip baseline-first, 本批纯 OHLCV structural\
  \ extension.\n\n**avoid-this-batch rank-diff axis**: 9 batches 累积零 admit, 本批不用 Sub(TsRank,\
  \ TsRank);\ncandle-geometry binarize 是正交几何.\n\nTarget: ≥1 admit (ls_t ≥ 3.0 + max_corr\
  \ < 0.40 + alpha_surv ≥ 0.5 + incr_ic ≥ 0.005)\nOR ≥2 candidates validated borderline\
  \ (alpha_surv ≥ 0.5 + ls_t > 2.0 confirming binarize\ncontent ⊥ Barra basis 律).\
  \ 若 0 admit + 多数 candle-geometry candidate 也被 basis 吸收\n→ T001 路径整体证伪, conditional\
  \ family 该路径 dead."
last_activity: '2026-05-16T00:34:43Z'
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
>
> **Next probes**: (a) b097/C001 + Python residualize on vol_20d (b096 blocker); (b) lower-shadow 主导日 `Mean(Gt((Min(O,C)-L)/(H-L), 0.5), 20)` 真 lower-shadow 而非 close-position mirror; (c) b097/C001 base form + extension wraps (Std/Skew of event rate).

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
> **Next probes**: (a) C004 base + extension wraps (Std/Skew of weak_close_day rate, 60d 窗口); (b) 阈值变体 Lt(.,0.15) / Lt(.,0.25) 敏感性; (c) 弱收盘日 + reversion gate (Mean(Lt × Sub(C, Ref(C,5))/Ref(C,5), 20)) 复合; (d) lower-shadow 主导日 sign 镜像于 T001.

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

---

## Related

- 🥉 [[factors/F028|F028]] — `dmi_down_ratio_12` — 库内唯一条件算子 admit，本方向 anchor precheck 必看 max_corr
- 🥉 [[factors/F021|F021]] — `upper_shadow_disp_range_compress_rd_20` — T001 上影占比的 dispersion 对偶
- [[lessons#Path Selection]] (P004-deep path-integral) — T002/T004 离散事件 aggregate 必须自检
- [[lessons#Anti-Recapitulation]] — F028 anchor cluster precheck

---

## Narrative Log

> [!quote]+ 2026-05-16 · [[batches/batch_098/judge|batch_098]] judge
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

> [!quote]+ 2026-05-16 · [[batches/batch_097/judge|batch_097]] judge
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

> [!quote]+ 2026-05-16 · batch_097 design
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
