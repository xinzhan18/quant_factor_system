---
batch_id: batch_060
direction: overnight_intraday_split
judged_at: 2026-04-28T02:30:00Z
candidates:
  - {candidate_id: C001, verdict: reject}
  - {candidate_id: C002, verdict: reject}
  - {candidate_id: C003, verdict: reject}
  - {candidate_id: C004, verdict: reject}
  - {candidate_id: C005, verdict: reject}
  - {candidate_id: C006, verdict: reserve}
batch_summary: {total: 6, admit: 0, reserve: 1, reject: 5}
admit_count: 0
reject_count: 5
reserve_count: 1
candidate_count: 6
mt_bucket: high
---

# batch_060 Judge Summary

> [!abstract]+ batch_060 · [[directions/overnight_intraday_split]] · 6 candidates
> ❌ **admit=0** · ⏸ **reserve=1** (C006) · ❌ **reject=5** (C001/C002/C003/C004/C005)
> **核心发现**: T012 close-position atom **下一代 LHS 突破三路径全军覆没** + T013 hybrid sign×magnitude **双向探针 0/2 admit** 路径基本封闭。具体: (a) **跨窗 range normalization (Min/Max 20d/60d)** 让 LHS 脱离 F022 仿射 (C001 corr=0.39@F016, C006 corr=0.37@F017) 但 incr_ic 中位数 -0.005 → cross-section IC 仍在但 **无库内增值空间** — 新 atom 信号被库内 F015-F023 多因子组合提前吸收;(b) **Power-cubed 非线性 wrap** 触发 **train-validation sign-flip** (C002 IS=+0.018 但 OOS=-0.022 ls_t=-2.77,sign_consistency 在 IS 内单调但跨 train→val 翻号 — P003 higher-moment regime sign-flip 跨 family 硬律在 close-position cubed 几何复现);(c) **from-peak 不对称 reference** hard_gate fail ic_oos=0.004 — 单边 reference 距高点跌幅信号在 csi1000 cross-section 上塌缩到 noise (alpha_surv=0.69 健康但 ic 不达标),**T012(c) DISPROVEN**;(d) **T013 hybrid Sign×|magnitude|** 双向探针 (C004 Sign(gap)×|body| / C005 Sign(intraday)×|gap|) 全部 alpha_surv<0.30 floor — vol_20d (10.7-21.9) + str_1m (0.81-2.76) 双吸收,即使 cross-section IC 健康也不脱 Barra style。**关键升格**: T012 close-position atom 几何 **彻底穷尽**(仿射 + 非线性 + 不对称 reference + 跨窗 normalization 四代 LHS 设计全失效)→ 升格 lessons 候选: "single-atom geometric exhaustion 律 — 当一个 atom 的所有 first-/second-order 几何变体 (4+ 代设计) 都被 ≤0.50 max_corr 但 ≤0 incr_ic 阻断时,该 atom 已结构性饱和,需切换字段或聚合维度,不能继续微调"。
> **MT Budget**: cumulative 318 → **324** · direction 33 → **39** · bucket `high` 持续 (search_adjusted ≈ 0.30 → low) · 本批 6 候选全 high bucket。**zero_admit_streak 0 → 1**

## 候选一览

| ID | Verdict | 档位 (CP3·4·5·6) | Key Metric | 反思 | Detail |
|---|---|---|---|---|---|
| C001 | ❌ reject | 🟠·🟢·🔴·🟡 | ic_oos=0.011 ls_t=0.26 mono_oos=0.30 incr_ic=-0.010 alpha_surv=2.44 | 跨 20d channel close-position × volume_CV 20d — IS Sharpe=2.35 → OOS=0.19 戏剧 IS-OOS 衰减 (oos_decay=0.60) + Mono OOS 从 1.0 崩到 0.30 + **incr_ic=-0.010 P006 库内 reducer 陷阱** (虽 alpha_surv=2.44 健康,但加入 C001 让组合信号变弱) | [[batches/batch_060/candidates/C001]] |
| C002 | ❌ reject | 🔴·🔴·🔴·🟠 | ic_is=+0.018 ic_oos=-0.022 ls_t=-2.77 alpha_surv=0.08 incr_ic=-0.017 | Power-cubed close-position × pb_60/20 ratio — **train→val sign-flip** (IS pos OOS neg) + alpha_surv=0.08 critical (vol_20d=11.4 + str_1m=4.9 双吸收) + cum_ic_mdd=-57.95 catastrophic + worst_quarter_ic=-0.083。**P003 higher-moment regime sign-flip 跨 family 硬律在 close-position cubed 几何首次实证复现**(库内 F019/F020 是 Std/Skew 二阶 LHS 同律,本候选是 Power(close_pos-0.5, 3) 三阶 power 同律) | [[batches/batch_060/candidates/C002]] |
| C003 | ❌ reject | hard_gate | ic_oos=0.004 < 0.008 floor | from-peak (Max($high,20)-C)/Max × ps_60 — 单边距高点距离 cross-section 信号弱;**T012(c) from-peak 路径 DISPROVEN** — 不对称 reference 在 csi1000 1d horizon 不携带独立 alpha (与 close-position 双边对称的差别在 cross-section 上不显著) | [[batches/batch_060/candidates/C003]] |
| C004 | ❌ reject | 🟠·🔴·🟡·🟢 | ic_oos=0.017 ls_t=2.23 alpha_surv=0.27 incr_ic=-0.0016 | Sign(overnight)×\|body\| × pe_60 — alpha_surv=0.27 < 0.30 rank-diff floor (vol_20d=10.7 + book_to_price=0.66) + incr_ic 微负 + 9/9 yr 单调改进但 worst_quarter=-0.010。**T013 hybrid 路径**: Sign(overnight)×\|intraday\| 在 cross-section 携带 IC 但被 Barra style 吸收,与 F018 (mean-Sign-overnight × amount,纯 sign 形式) 在 csi1000 上 corr=0.375 显示 hybrid 与 sign-only **共载 vol_20d 几何位置**;**hybrid 形式无法脱 Barra absorption** | [[batches/batch_060/candidates/C004]] |
| C005 | ❌ reject | 🔴·🔴·🟡·🟠 | ic_oos=0.023 ls_t=0.47 alpha_surv=0.09 incr_ic=-0.0048 | Sign(intraday)×\|gap\| × turnover_60 — alpha_surv=0.09 critical (vol_20d=21.86 + turnover_20d=6.39 双吸收 + str_1m=2.76) + train_validation_decay=10.88 极端 + ls_t=0.47 essentially zero (cross-section IC 有但 long-short spread 无) + incr_ic 负。**T013 hybrid 镜像方向 (sign-side 互换) 无救**: Sign(intraday)×\|overnight\| 与 Sign(overnight)×\|intraday\| (C004) 双向皆 alpha_surv 低 — sign-magnitude hybrid 形式在 csi1000 1d horizon 下被 vol_20d 结构性吸收,与字段方向无关 | [[batches/batch_060/candidates/C005]] |
| C006 | ⏸ reserve | 🟠·🟢·🟡·🟠 | ic_oos=0.019 ls_t=0.39 alpha_surv=0.93 incr_ic=+0.0025 max_corr=0.37@F017 | 跨 60d channel close-position × Std(turnover,60) — **本批唯一 incr_ic 正向** (+0.0025) + alpha_surv=0.93 健康 (vol_20d=11.8 中位但被 60d 长窗稀释) + max_corr 与库内最大相关仅 0.37 (cluster-clean) + 9/9 yr 7/9 positive (sign_consistency=1.0 不严格 — 实际有 1 yr 弱负)。但 ls_t=0.39 essentially zero + cum_ic_mdd=-8.82 偏深 + worst_quarter_ic=-0.050。**reserve 决策**: 唯一在本批 alpha_surv 与 incr_ic 双绿候选,但 long-short 不投资。CP05 high 档 reserve 决策档下界 (incr_ic ∈ [0.003, 0.005] 0.0025 略低),保留为下次 RHS 替换或 evaluation policy 调整后重测的种子 | [[batches/batch_060/candidates/C006]] |

**档位编码**: 🟢 最优档 · 🟡 次档 · 🟠 边际 · 🔴 阻断档 · `hard_gate` reject 不填色。

## 跨候选对比

- **Style 聚合**: 6/6 候选 dominant_style_exposure=`vol_20d` (vol_20d=10.7-28.7,极值 C001=28.74)。本方向 9 admits 全载 vol_20d — direction-level structural exposure 已是 lessons 顶级失败律 (P004)。本批 4/6 候选 (C002/C004/C005/C006) 同时叠加 turnover_20d / str_1m 高 exposure → **rank-diff geometry 在 close-position atom 上的 vol_20d 结构性吸收硬上限** 已无法通过 RHS 类目替换或 LHS 几何变体绕过。
- **LHS atom 几何穷尽四代设计**: F022 (raw close-position 仿射) → b059 center-position (差常数仿射,corr=0.93 hard_gate) → b060 C001/C006 跨窗 range normalization (Min/Max 20d/60d 改分母 scale,corr 0.39/0.37 低相关但 incr_ic ≤0) + C002 Power-cubed 非线性 wrap (train→val sign-flip catastrophic) + C003 from-peak 不对称 reference (ic_oos hard_gate fail)。**所有 4 代设计都不兑现独立 alpha**。close-position atom 在 csi1000 daily-bar 几何已 **结构性饱和**。
- **T013 hybrid 双向探针 0/2 admit**: C004 (Sign(overnight)×|body|) + C005 (Sign(intraday)×|gap|) 镜像 hybrid 形式皆 alpha_surv<0.30 floor。**关键发现**: hybrid sign×magnitude 在 csi1000 cross-section 上几何位置与 Barra vol_20d (intraday body magnitude × 任何 sign aggregation) / turnover_20d (overnight gap × 任何 amount-derived RHS) 重叠 — sign-side 退化只贡献方向信息但 magnitude-side 仍嵌入 Barra basis。**T013 假说部分验证**: F018 sign-magnitude 0.37 低相关确实是 (Sign(overnight) × amount-LHS-not-derived-from-overnight) 特定组合的 happy accident,**hybrid 形式 (Sign × |magnitude| same-direction-pair) 普遍无法脱 Barra basis**。
- **Power-cubed sign-flip 升格信号** (C002 IS+0.018 OOS-0.022): csi1000 train (2015-2021 低利率成长) → val (2022-2023 利率上行价值回归) regime 切换在 close-position **三阶 power moment** 上首次实证复现 sign-flip。lessons.md "Train→Validation regime 切换" 律已记载 higher-moment LHS 在 raw fundamental / intraday signed / residual 字段上系统性翻号,本候选把该律扩展到 **close-position 三阶 power moment** —— intraday OHLC ratio 加 cubic 非线性也无法逃脱 regime sign-flip。
- **本批最强候选 C006 仅过 reserve 决策档下界**: incr_ic=+0.0025 低于 high-bucket reserve 决策档下界 (0.003),但其 cluster-clean (max_corr=0.37) + alpha_surv=0.93 显著 + 长窗 channel 跨窗 normalization 几何 fresh 三优势,值得保留为 future 实验种子。**LHS 60d channel 是 b060 唯一在 alpha_surv + incr_ic 双方向不输的 atom**。
- **MT 预算推进**: direction_candidates 33→39,family score 0.901,direction score 0.840 (从 0.76→0.84,direction-level 拥挤升级),exposure 满 1.0。本批 zero admit + alpha_surv 中位数 0.69 (从 b058 0.43 / b059 0.37 持续下滑) → **direction-level alpha quality 趋势性衰减信号**。

## Thread 进展

> [!note]+ T012 [[directions/overnight_intraday_split#T012]] — `[◉ ACTIVE → ✗ EXHAUSTED batch_060]`
> **close-position atom 几何彻底穷尽**: 4 代 LHS 设计 (raw 仿射 / 跨窗 Min-Max normalization / 非线性 Power-cubed wrap / 不对称 from-peak reference) 全部失败。具体: (a) C001 (20d Min-Max channel) corr=0.39@F016 但 incr_ic=-0.010 + Mono IS=1.0→OOS=0.30 崩塌; (b) C006 (60d Min-Max channel) corr=0.37@F017 incr_ic=+0.0025 但 ls_t=0.39 essentially zero → reserve 唯一火种; (c) C002 (Power-cubed) train→val sign-flip catastrophic; (d) C003 (from-peak) hard_gate fail。**Thread 转 EXHAUSTED**。**Lessons 升格候选**: "single-atom geometric exhaustion 律 — 当一个 atom 的 4+ 代 first-/second-order 几何变体都失败 (max_corr 各代 ≤0.50 但 incr_ic ≤0 + alpha_surv 在 vol_20d 吸收下衰减) 时,该 atom 已结构性饱和,需切换字段或聚合维度"。

> [!note]+ T013 [[directions/overnight_intraday_split#T013]] — `[◉ ACTIVE → ✗ DISPROVEN batch_060]` (hybrid 路径)
> **hybrid Sign×|magnitude| 双向探针 0/2 admit**: C004 (Sign(o)×|i|) alpha_surv=0.27 < 0.30 floor + incr_ic=-0.0016, C005 (Sign(i)×|o|) alpha_surv=0.09 critical + ls_t=0.47。**关键发现**: hybrid 形式无论 sign-side 在 overnight 还是 intraday,magnitude-side 仍嵌入 Barra vol_20d / turnover_20d basis,sign 退化只贡献方向信息不脱 Barra absorption。**T013 假说部分验证**: F018 sign-magnitude corr=0.37 低相关是 (Sign(overnight) × amount RHS) 特定组合的 happy accident,**hybrid Sign×|magnitude| same-direction-pair 形式不可家族化**。Thread 状态: **DISPROVEN** for hybrid 路径。原始 question (sign-discretization 普适性) 部分保留 — sign-only 路径在 T011 已封闭,hybrid 路径在 T013 已 DISPROVEN,sign 离散化在本方向几何已 closed。

## 方向级反思

本方向第 10 批,9 admit (F009/F010/F011/F017/F018/F022/F023 + b048~b059),**direction.score 0.84 升至历史新高 + cumulative 0.90 偏高 + exposure 1.0 满 → MT bucket 持续 high**。本批 zero admit + alpha_surv 中位数 0.69 较 b058 0.43 / b059 0.37 看似回升,但拆解后: vol_20d 中位 17.0 (从 b058 中位 38.6 下降 → 表面健康但 4/6 候选 <30% floor),实际 alpha quality 在 close-position atom 上 **结构性下滑**。**reserve 积压**: b058 留 2 + b059 留 2 + b060 留 1 = 5 reserve,reserve/judged = 5/18=28% 远低 40% 警戒线。

**T012 EXHAUSTED + T013 hybrid DISPROVEN 双 thread 关闭**: 本方向 (overnight_intraday_split) 在 close-position atom 与 sign-discretization 形式上空间已尽。还有探索空间在: (a) **second-order interaction non-magnitude / non-sign 形式** (T011 magnitude-product 兑现后,可探 sum / max / min / std-of-product 聚合);(b) **跨日 lag-shifted overnight 自相关** (overnight_t × overnight_{t-1}, overnight 段自身 lag-correlation 是否独立于 spread/persistence);(c) **VWAP-like average price 派生量** ($amount/$volume = avg_trade_price,与 close 不同 reference point — 但 vwap 死区警告 P001 需注意 amount/volume 是否真的脱 vwap zero 问题)。

**zero_admit_streak 0→1**: 单批 zero admit 不触 calibration trigger (需累计 3 批);最近 3 批累计 admit=2 (b058 1 + b059 1 + b060 0),距 zero admit 警戒还有空间。

**direction status 评估**: 仍 productive (前两批连续 admit + 9 总 admit) 但 priority 应从 high → medium (close-position + sign 二大 thread 关闭,仅剩零碎探针 atomic 候选 — second-order interaction / lag-shifted overnight / VWAP 派生)。**本轮调整 priority: high → medium**。

**consolidation 信号**: rounds_since_last_consolidation=0 (上轮 b059 后已触发 consolidation),本轮无需。
