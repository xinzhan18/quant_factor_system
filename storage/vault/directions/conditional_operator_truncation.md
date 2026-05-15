---
direction_tag: conditional_operator_truncation
status: exploring
priority: high
rounds: 2
admits: 0
last_batch: batch_097
last_admits: []
last_goal: "Round 97 — structural gap exploration: conditional operator family (Gt\
  \ / Lt / If)\nunder-utilized in library (28 admit: 1 conditional F028 + 27 linear-arithmetic).\n\
  6 候选覆盖 6 子族 (T001 上影主导日占比, T002 gap-up 事件率, T003 high-turnover-rank\nconditional\
  \ flow, T004 上涨日占比, T005 低振幅日占比, T006 PV-corr-gated momentum) —\n全部使用 Gt/Lt 把信号离散化为\
  \ {0,1} 事件 + Mean aggregate 成 Bernoulli rate,\n或用 If 做 conditional observation。\n\
  \nQlib op note: Qlib runtime 提供 Gt/Lt (返回 bool) 与 Greater/Less (返回 element-wise\n\
  max/min) 是不同语义算子; 本批用 Gt/Lt 做 boolean event count, 用 If(cond, left, right)\n做 conditional\
  \ select (Qlib 用 If 而非 IfElse 名).\n\n**核心 hypothesis**: conditional truncation 在\
  \ cross-section 上产生 geometric distinct\nordering — 与 27 个线性算术 admit max_corr 应 <\
  \ 0.40, 同时离散事件率 aggregate 不构成\npath-integral path-memory (因二值化丢弃了连续 ε 信号).\n\n**Self-check\
  \ 5 hard rule (round 73 + round 91 升格)**:\n- **P030** (alpha_surv>1.0 单边 ≠ admit\
  \ 充分): 全 6 候选 multi-CP rationale, 不依赖\n  alpha_surv 单边; 即使 truncation 几何独特, admit\
  \ 仍需 incr_ic + max_corr + ls_t 至少 2/3\n- **P004-deep path-integral borderline**\
  \ (round 91 升格): T002/T004/T005 是 Sum/Mean of\n  `Greater(.,.)` 或 `IfElse(.,1,0)`\
  \ 离散事件 — 在二值化 truncate 后, path-memory β-shift\n  机制理论上消失 (path-integral 危险源是 `Σ(ε_t-i)`\
  \ 内层连续 ε, 二值化把它降到 {0,1}\n  离散概率, 等价于 Bernoulli rate). **borderline 标注**: 本批显式 case-by-case\
  \ 进入,\n  Phase 3 judge 若发现 vol_20d_exp > 15 或 alpha_surv < 0.4 触发 P004-deep 类失败模式,\n\
  \  则该子族证伪\n- **F028 anchor precheck**: F028 = `Div(Sum(Lt × Greater, 12), ...)`\
  \ 是 DMI 双计数比值;\n  本批 6 候选无 Lt×Greater 双 condition 复合 (T001-T005 单 Greater/Lt, T006\
  \ IfElse 选择);\n  几何 distinct 概率高, 但 Phase 2 必跑 max_corr_F028 实测\n- **Reciprocal\
  \ monotonic-invariant**: `Greater(x, 0)` ≠ `Less(-x, 0)` 同 cross-section\n  rank\
  \ (sign-flip 但 cross-section 上 truncate 方向同, 不等价); 本批避免 Greater/Less\n  互补对偶 (无\
  \ `Greater(x,c) + Less(x,c)` 配对覆盖全空间)\n- **Cross-section OLS sign-flip / Cov-equiv\
  \ (P028)**: 无 Cov atom; 无 cross-section\n  OLS residualize (DSL only)\n\n**Anchor\
  \ avoidance**:\n- F028 (DMI down-ratio): 双 condition 复合 (Lt × Greater), 本批 6 候选无此结构\
  \ → distinct\n- F021 (upper_shadow_disp_range_compress_rd): T001 上影占比走 truncation+aggregate\
  \ 路径,\n  与 F021 走 dispersion+rank-diff 路径几何不同 (truncation 是离散二值, dispersion 是连续\
  \ Std)\n- F012 (Amihud 反转簇): T002/T004 是 cross-day return 事件率, 与 Amihud `Mean(|ret|/$amount)`\n\
  \  level 信号不同 (truncate 后 magnitude 信息丢失, 只剩计数)\n- F019/F020 (gap-related rank-diff):\
  \ T002 gap event rate 走 truncation+Mean 路径, 与 F020\n  `gap_vol_body_ratio_rank_diff_20`\
  \ 走 ratio+rank-diff 几何不同\n\n**Baseline-first 守则 explicit skip**: 15 untouched TTM\
  \ fields 与 conditional truncation\n几何 (cross-day return event / shadow ratio threshold\
  \ / turnover-rank gating) 完全不相关 —\nconditional truncation 依赖 daily price/volume\
  \ 频率离散事件, TTM 财务字段是季度更新无法支撑\ndaily event counting. 显式 skip baseline-first, 本批纯 OHLCV/microstructure\
  \ structural 探索.\n\n**avoid-this-batch rank-diff axis**: 8 batches 累积零 admit 进入\
  \ dead-spiral, 本批显式不\n用 Sub(TsRank, TsRank) 形式; conditional operator 是正交几何。\n\n\
  Target: ≥1 admit (ls_t ≥ 3.0 + max_corr < 0.40 + alpha_surv ≥ 0.5) OR ≥2 子族 validated\n\
  (P004-deep 离散事件 aggregate 不触发 vol_20d 吸收, alpha_surv ≥ 0.5 + ls_t > 2.0).\nCalibration\
  \ trigger 已 true from b095/b096; 本批是首个结构性新方向探索, 若 0 admit 不加深\ndead-spiral 因子, 而是检验\
  \ conditional family 路径可行性。"
last_activity: '2026-05-15T23:57:31Z'
created_batch: batch_097
members: []
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

### T001: 上影占比 truncation [◉ ACTIVE]

> [!warning]+ Thread 结论 (partial)
> **Question**: 上影长度占当日 range 的比例离散化为事件率后的 20d 平均是否构成独立 alpha？
>
> **Answer (partial)**: **borderline reserve**. C001 实测 alpha_survival=**1.07** (Barra-clean), ls_t=+2.85 moderate, mono_oos=+0.80 强, max_lib_corr=0.41@F022 但 incremental_ic=0.0030 临界. **唯一未被 Barra basis 吸收的 binarize aggregate 路径** — 几何 distinct from 27 linear-arithmetic admits + Barra residual IC 接近 raw IC. P030 paradox guard 三条件: alpha_surv✓ + ls_t≥1.5✓ but max_corr<0.40✗ + incr_ic≥0.005✗ 仅满足 2/4 → reserve. 受 admit floor (ls_t<3.0) 与 incr_ic 临界制约.
>
> **Evidence trail**:
> - [[batches/batch_097/candidates/C001|batch_097 C001]]　`Mean(Gt((H-C)/(H-L), 0.5), 20)`　alpha_surv=1.07, ls_t=2.85, ic_oos=0.0088, max_corr=0.41@F022 → **reserve** (借 P030 paradox guard 2/4 缺 admit 充分条件)
>
> **Next probes**: (a) C001 + Python residualize on vol_20d (b096 blocker); (b) 下影主导日占比 / middle-body 主导日占比 / range-position 离散化变体; (c) C001 base form + extension wraps (Std/Skew of event rate).

### T002: gap event rate (cross-day) [✗ DISPROVEN batch_097]

> [!failure]+ Thread 结论
> **Question**: 60d gap-up 事件率是否构成独立 alpha？
>
> **Answer**: **disproven**. C002 alpha_survival=0.13 catastrophic + vol_20d_exp=27.6 catastrophic + ls_t=-0.61 弱 → 60d binarized event rate 仍被 vol_20d basis 吸收. P004-deep 律在 binarized aggregate 上**部分适用** (path-memory β 消失但 long-window event rate 与 vol style basis 频谱共振).
>
> **Evidence trail**:
> - [[batches/batch_097/candidates/C002|batch_097 C002]]　`Mean(Gt($open/Ref($close,1), 1.005), 60)`　alpha_surv=0.13, vol_20d=27.6, ls_t=-0.61 → **reject (CP04 catastrophic)**

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
| [[batches/batch_097/candidates/C006\|C006]] | `If(Gt(Corr(C,V,10),0),Sub(C/Ref(C,20),1),0)` | CP04 catastrophic: style_r²=**0.71** (本批最高) + str_1m_exp=7.77 + max_corr=0.55@F027; conditional observation gating 不破 momentum-basis 同构 |

---

## Related

- 🥉 [[factors/F028|F028]] — `dmi_down_ratio_12` — 库内唯一条件算子 admit，本方向 anchor precheck 必看 max_corr
- 🥉 [[factors/F021|F021]] — `upper_shadow_disp_range_compress_rd_20` — T001 上影占比的 dispersion 对偶
- [[lessons#Path Selection]] (P004-deep path-integral) — T002/T004 离散事件 aggregate 必须自检
- [[lessons#Anti-Recapitulation]] — F028 anchor cluster precheck

---

## Narrative Log

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
