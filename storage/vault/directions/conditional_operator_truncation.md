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

库 28 admit 中 **F028** (DMI-down ratio) 与 **F029** (weak_close_day_rate_20) 是仅有的两个条件算子族 admit;
其余 26 个 **100% 线性算术形式** (Mul/Div/Sub/Add/Mean/Std/TsRank/Corr/Cov)。

**结构性 gap 假设**: 条件算子族 truncation（full binarize + Mean event-rate aggregation）构成 cross-section 上 distinct geometry,
可与库内线性算术因子保持低 max_corr 同时提供独立 incremental IC — **但 admit 充分条件极窄**。

**Admit 充分条件 (经 b097-b099 实证升格, 7 维约束)**:
1. **Full binarize** (非 partial mask × raw magnitude) — 必须丢弃连续 magnitude
2. **Event-rate aggregate** (Mean of {0,1}, 非 If × continuous signal gating)
3. **Binarized content ⊥ Barra style basis** — gap-rate ≡ vol_20d / return-sign ≡ str_1m / low-amp ≡ vol_20d 反向都 fail
4. **字段** — open vs close 切换即跨入 str_1m basis 吸收区 (T001 字段 mirror dead)
5. **方向** — Lt 弱端 left-tail thick 是 robust escape, Gt 强端 vol_20d basis 共振更深
6. **阈值** — 0.2 微调到 0.15 即触发 near_dup F029 (corr=0.82), Gt 0.8 涨停日 close==high 强制拉满引入 regime sensitivity
7. **窗口** — 20d 是 sweet spot, 60d 长窗 OOS 信号归零, 10d 短窗 Gt 强端 window-invariant fail

**F029 邻域 unsystematic mapping**: F029 = close-position × Lt × 0.2 × 20d × Mean × 单 condition 的 **7 维约束孤立 admissible point** (quasi-isolated singularity, 非 family-cluster 中心), 周围邻域全 dead.

## Threads

### T001: 上影占比 truncation [◉ ACTIVE — reserve hold, 等 daily_python residualize]

> [!warning]+ Thread 结论 (partial)
> b097/C001 `Mean(Gt((H-C)/(H-L), 0.5), 20)` alpha_surv=**1.07** Barra-clean, ls_t=+2.85, mono_oos=+0.80, max_corr=0.41@F022, incremental_ic=0.0030 临界 → **reserve hold**.
>
> reciprocal mirror (b098/C001 close 上半) + 字段 mirror (b099/C004 open-position) 两路径均不可推广 — 见 Hypothesis 7 维约束 (字段+方向+阈值 mirror 全 fail).
>
> **Next**: b097/C001 + Python residualize on vol_20d, 等 daily_python registry 模板.

### T008: range-position 弱端 truncation [✓ ANSWERED → F029, family-space exhausted]

> [!success]+ Thread 结论
> b098/C004 `Mean(Lt((C-L)/(H-L), 0.2), 20)` alpha_surv=**1.10** Barra-clean + ls_t=+3.28 + max_corr=0.32@F006 + 9 年 ic_by_year 全正 → **admit → [[factors/F029]]** (`weak_close_day_rate_20`). 库内第 2 个 conditional truncation rate alpha-clean.
>
> b099 沿 6 维轴 systematically map F029 邻域 (window/threshold/aggregate wrap/field/direction/compound) **全 reject** → F029 是 quasi-isolated singularity, family-space exhausted.

---

## Disproven Threads (compressed)

| Thread | Mechanism | Evidence |
|---|---|---|
| T002 gap event rate | 跨阈值 family-wide dead: gap content ≡ vol_20d basis source-level 同构 (overnight gap 自身是 daily vol marker), threshold tuning 不解决 | b097/C002 (0.5% 阈, alpha_surv=0.13) + b098/C005 (1.5% 阈, alpha_surv=**0.030**, 提高阈值反而恶化) |
| T003 mask × raw turnover | partial truncation ≠ full binarize: 保留 raw magnitude → 100% vol_20d basis 吸收 | b097/C003 alpha_surv=0.15, vol_20d=37.4 |
| T004 上涨日占比 | return-sign ≡ str_1m basis direct proxy | b097/C004 alpha_surv=**0.07** (本批最低), str_1m=5.45 |
| T005 低振幅日占比 | 低振幅 ≡ vol_20d 反向 direct proxy | b097/C005 ic_oos=0.057 (强!) 但 alpha_surv=0.22, vol_20d=**46.8** |
| T006 PV-corr gated momentum | If × continuous signal 不破 absorption (P030 反例: alpha_surv=0.83 OK 但 style_r²=0.71 catastrophic) | b097/C006 style_r²=0.71, str_1m=7.77 |
| T007 small-body 主导日 | body 维度 binarize 失败: body 大小与 vol_20d 共线, 信号几乎平坦 | b098/C002 ic_oos=0.0021, mono_oos=0.0 |
| T009 跨日 candle-pattern | candle-pattern binarize 仅限单日内 geometry, 跨日 regime-dependent | b098/C006 sign_flip + oos_decay |

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| [[batches/batch_097/candidates/C002\|b097 C002]] | `Mean(Gt($open/Ref($close,1),1.005),60)` | CP04: alpha_surv=0.13, vol_20d=27.6; gap rate // vol_20d basis |
| [[batches/batch_097/candidates/C003\|b097 C003]] | `Mean(Mul(Gt(TsRank($turn,60),0.8),$turn),20)` | CP04: alpha_surv=0.15, vol_20d=37.4; partial truncation 保留 raw magnitude |
| [[batches/batch_097/candidates/C004\|b097 C004]] | `Mean(Gt($close/Ref($close,1),1.0),20)` | CP04: alpha_surv=**0.07**, str_1m=5.45; return-sign ≡ str_1m |
| [[batches/batch_097/candidates/C005\|b097 C005]] | `Mean(Lt(($high-$low)/$close,0.03),60)` | CP04+CP05: alpha_surv=0.22, vol_20d=**46.8**, max_corr=0.66@F021 |
| [[batches/batch_097/candidates/C006\|b097 C006]] | `If(Gt(Corr(C,V,10),0),Sub(C/Ref(C,20),1),0)` | CP04: style_r²=**0.71**, str_1m=7.77; gating 不破 absorption |
| [[batches/batch_098/candidates/C001\|b098 C001]] | `Mean(Gt((C-L)/(H-L),0.5),20)` | reciprocal mirror not portable: alpha_surv=0.50, ic_oos sign 反, incr_ic=-0.006 |
| [[batches/batch_098/candidates/C002\|b098 C002]] | `Mean(Lt(\|C-O\|/(H-L),0.3),20)` | CP01 hard_gate: ic_oos=0.0021 平坦; body 维度 binarize 失败 |
| [[batches/batch_098/candidates/C003\|b098 C003]] | `Mean(Gt((C-L)/(H-L),0.8),20)` | CP01 triple fail; 高阈 (0.8) 涨停日 close==high 强制拉满, regime instability |
| [[batches/batch_098/candidates/C005\|b098 C005]] | `Mean(Gt($open/Ref($close,1)-1,0.015),60)` | CP04: alpha_surv=**0.030**, vol_20d=**35.4**; gap family 跨阈值 dead |
| [[batches/batch_098/candidates/C006\|b098 C006]] | `Mean(Gt((C-O)*(Ref(O,1)-Ref(C,1)),0),60)` | CP01 sign_flip + oos_decay; 跨日 candle-pattern regime-dependent |
| [[batches/batch_099/candidates/C001\|b099 C001]] | `Mean(Lt((C-L)/(H-L),0.2),60)` | CP01 hard_gate; F029 family window 上限 < 60d |
| [[batches/batch_099/candidates/C002\|b099 C002]] | `Mean(Lt((C-L)/(H-L),0.15),20)` | CP05 high: max_corr=**0.82**@F029, incr_ic=**-0.0003**; threshold quasi-isolated |
| [[batches/batch_099/candidates/C003\|b099 C003]] | `Std(Lt((C-L)/(H-L),0.2),60)` | CP01 hard_gate; Std-of-binarize ≡ Mean-of-binarize 60d 数学等价 (Var(Bernoulli)=p(1-p) 低值区) |
| [[batches/batch_099/candidates/C004\|b099 C004]] | `Mean(Lt((H-O)/(H-L),0.2),20)` | CP04 poor: alpha_surv=**0.15**, str_1m=3.66; 字段 mirror open vs close 跨入 str_1m basis |
| [[batches/batch_099/candidates/C005\|b099 C005]] | `Mean(Gt((C-L)/(H-L),0.8),10)` | CP01 hard_gate; b098 律 window-invariant, Gt 0.8 短窗仍 fail |
| [[batches/batch_099/candidates/C006\|b099 C006]] | `Mean(Mul(Lt((C-L)/(H-L),0.2),Gt((H-L)/C,0.02)),20)` | CP01 hard_gate, vol_20d_exp=**45.18** 史诗; Gt(amplitude) ≡ vol_20d proxy 主导复合 basis |

---

## Related

- 🥉 [[factors/F028|F028]] — `dmi_down_ratio_12` — 库内首个 conditional 算子 admit, **F028 邻域 axis-wise 扩展尚未做** (next-priority direction extension, DMI-up mirror / window sweep / threshold sweep)
- 🥉 [[factors/F029|F029]] — `weak_close_day_rate_20` — 本方向 admit, 7 维约束孤立 admissible point
- 🥉 [[factors/F021|F021]] — `upper_shadow_disp_range_compress_rd_20` — T001 上影占比的 dispersion 对偶
- [[lessons#Path Selection]] (P004-deep) — T002/T004 离散事件 aggregate 与 style basis 频谱共振自检
- [[lessons#Anti-Recapitulation]] — F028+F029 双 anchor cluster precheck

---

## Narrative Log

> [!quote]+ 2026-05-16 · [[batches/batch_099/judge|batch_099]] judge
> **F029 family axis-wise extension 全 reject + status productive → saturated** · admit=0 / reserve=0 / reject=6
>
> - 6 候选沿 F029 family 三轴扩展全部 fail: window (60d → OOS 归零), threshold (0.2→0.15 → near_dup corr=0.82 + incr_ic 负), aggregate wrap (Std ≡ Mean 60d 数学等价), field mirror (open vs close → str_1m basis 吸收), short-window Gt 0.8 (window-invariant fail), compound vol-filter (Gt(amplitude)≡vol_20d 主导 basis vol_20d_exp=45.18 史诗).
> - **核心**: F029 = 7 维约束孤立 admissible point (close-position × Lt × 0.2 × 20d × Mean × 单 condition), 周围邻域全 dead, quasi-isolated singularity 非 family-cluster 中心.
> - **4 条升格律**: (1) F029 family axis-wise 行为律; (2) Std-of-binarize ≡ Mean-of-binarize 60d 数学等价律 (跨 family 普适); (3) Compound vol-isomorphic condition 反弹律 (跨 family 普适); (4) binarize content 三要素 (字段+方向+阈值) 决定 ⊥ basis.
> - **MT Budget**: cumulative 552 → **558** · direction **18** · bucket `high`. 同方向重复搜索回报递减.
>
> **Operations**　`status: productive → saturated` · priority `high → medium` · admits 2 (F028+F029) · 9 batches/30 candidates, admit_rate=6.7%.
> **下一步**: (a) T008 exhausted, 跳出 F029 邻域; (b) **F028 邻域 axis-wise 扩展** 尚未做 (DMI conditional 是库内另一 conditional anchor); (c) 探索 turnover-binarize / fundamental-binarize / momentum-binarize 其它 conditional content; (d) b097/C001 reserve hold + Python residualize 等 daily_python 模板; (e) lessons-promotion 4 条.

> [!quote]- 2026-05-16 · [[batches/batch_098/judge|batch_098]] judge
> **T008 弱端 admit + T001 reciprocal mirror dead + T002 跨阈值 dead** · admit=1 (C004→F029) / reserve=0 / reject=5
>
> - C004 admit (`Mean(Lt((C-L)/(H-L), 0.2), 20)`): alpha_surv=**1.10** Barra-clean + ls_t=**+3.28** + max_corr=0.32@F006 + 9 年 ic_by_year 全正. 库内第 2 个 conditional truncation rate alpha-clean. 打破 9-batch zero_admit_streak.
> - C001 reject (reciprocal mirror 50% 阈): alpha_surv=0.50, ic_oos sign 反, incr_ic=-0.006 → reciprocal mirror not portable.
> - C003 reject (高阈 80%): CP01 sign_flip ×3, 涨停日 close==high 强制拉满 regime sensitivity.
> - C005 reject (gap-up 1.5% 60d): alpha_surv=**0.030** **比 b097/C002 更恶化**, T002 family 跨阈值 dead.
> - C002/C006 reject (T007/T009): body 维度 binarize 失败 + 跨日 candle-pattern dead.
> - **核心律 (round 9 升格)**: 同 (C-L)/(H-L) 信号底层, 不同 binarize 方向 + 阈值 alpha_survival 显著不同 (Gt(.,0.5)=0.50, Gt(.,0.8)=fail, Lt(.,0.2)=1.10) — left-tail thick (弱端) robust escape, right-tail (强端) vol_20d basis 共振更深.
>
> **MT Budget**: 546 → **552** · direction 6→12 · bucket 全 high.
> **Operations**　`status: exploring` · rounds 1→2 · admits 0→**1** (C004) · zero_admit_streak 9→0 reset.

> [!quote]- 2026-05-16 · [[batches/batch_097/judge|batch_097]] judge
> **Binarized event-rate 路径 admit 严格依赖 binarized content ⊥ Barra style basis** · admit=0 / reserve=1 (C001) / reject=5
>
> - C001 reserve (上影主导日 20d): alpha_surv=**1.07** Barra-clean + ls_t=2.85 + mono_oos=+0.80 + max_corr=0.41@F022 + incr_ic=0.0030 临界 → P030 2/4 reserve. 库内 0 个 conditional truncation event rate admit, C001 推进到 borderline admit territory.
> - C002/C004/C005 全 reject: alpha_surv ∈ [0.07, 0.22] catastrophic, vol_20d_exp ∈ [13.6, 46.8]. **机制**: full binarize 不能保证 escape — 当 binarized 内容与 Barra style basis 同构 (gap≡vol_20d / return-sign≡str_1m / low-amp≡vol_20d 反向) 时 100% basis 吸收.
> - C003 partial truncation reject + C006 If × continuous reject.
> - **核心 lesson**: conditional truncation admit 充分条件 = **binarized content ⊥ Barra style basis** (不是"用了 Gt/Lt/If 就行").
> - **P004-deep 律本质升格**: "long-window aggregate 必然与 style basis 频谱共振 IF binarized content 同构 basis" — binarize 是必要非充分条件, 内容正交 basis 才充分.
>
> **MT Budget**: 540 → **546** · direction 0→6 · bucket `medium`.
> **Operations**　`status: exploring (NEW)` · rounds 0→1 · reserves +1 (C001).

> [!quote]- 2026-05-16 · batch_097 design
> 新方向创建 — 结构性缺口探索: 库 28 admit / 27 线性算术 + 1 条件算子 (F028) → conditional operator family untapped territory. 6 候选覆盖 6 子族 (T001-T006). Self-check 5 hard rule 全过: P030 multi-CP / P004-deep borderline-discrete / F028 anchor precheck (本批无 Lt×Greater 双复合) / reciprocal duplicate avoid / paper=none.
>
> **Operations**　`status: exploring (NEW)` · priority `high`
