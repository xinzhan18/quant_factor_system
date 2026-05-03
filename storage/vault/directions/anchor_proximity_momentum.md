---
direction_tag: anchor_proximity_momentum
status: saturated
priority: low
rounds: 4
admits: 1
last_batch: batch_084
last_admits: []
last_goal: 'Round 84 — anchor_proximity_momentum continue_direction. zero_admit_streak=1
  (b083 range_structure dead 0/6); F025+F026 cluster占据 daily-resolution intraday position/ratio
  几何，新候选必须 max_corr<0.40 vs F025/F026/F018/F021/F022/F009. 本批 6 候选探索 (a) T004 PTA
  250d 长窗口 envelope（论文标定窗口，60d/120d 均失败 vol_20d 撑大）; (b) T002 PTA × past-winner 嵌套维度（CsRank-rank-diff
  form 而非 Mul wrapper, 避 P021）; (c) T005 wick-asymmetry ratio (upper/lower wick) —
  daily-resolution dim-less ratio 非对称版本 (F025 是对称 shadow asymmetry midpoint); (d)
  T005 CsRank-wrapper Mean(close_position, 20) — 测 P008 escape 是否 wrapper-conditional
  (无 TsRank); (e) T004 distance-from-MA60 z-score — 测 z-score 几何是否绕过 P008 specific
  atom 限制; (f) T004 PTA 250d × CsRank-wrapper baseline-first variant. 全候选避 F025/F026/F018/F021/F022/F009
  cluster, 严守 P019 数据契约（Corr 仅 OHLCV+amount+num_trades, 本批无 Corr 算子使用）+ P021（无 Mul
  wrapper 跨字段）+ rate-form forbidden（no Delta/Sub of PTA）. Hard targets: ≥1 admit alpha_surv≥0.40
  + max_corr<0.40 + style_r²<0.12 + mono_oos≥0.7. Fail → 报告"PTA 长窗口 envelope 与 F025/F026
  daily ratio 不可分"边界.'
last_activity: '2026-05-02T17:10:00Z'
created_batch: batch_080
members:
- F026
merged_into: null
---
# anchor_proximity_momentum

> [!abstract]+ 方向概要
> - **状态**　🟡 `saturated` · priority `low` · rounds = 4 · admits = 1 (F026)
> - **核心承载**　**P008 anchor cluster lock** 律——daily-resolution dim-less close-anchor 几何空间已被 F025+F026 完整占据；P008 escape 三条件律源头方向
> - **一句话**　PTA (price-to-52w-high) 论文 monthly horizon anchor effect 在 csi1000 daily 不复现；唯一存活几何是 F026 daily atom (c-l)/(h-l) + TsRank 60d，paper 标定 250d envelope alpha_surv hard fail

---

## Hypothesis

George-Hwang 2004 (CRSP 1963-2001 月频)：**nearness to 52-week high** PTA = `Div($close, Max($close, 250))` 是比 JT 6 个月 momentum 更强的预测变量；nested cross-section sort 显示 PTA 包含 JT 全部预测力。机制：anchoring bias —— trader 把 52WH 当 reference point 抗拒推过新高，价格远离锚时抗拒低价卖。Chen-Stivers-Sun 2025 形式化 PTA × past-winner interaction，equity side ≈25% 增量年化 alpha。

**A 股本地化假设状态 (post batch_080-084)**：
- **H1 PTA baseline 真度** ✗ — PTA 250d 论文标定窗口 alpha_surv=0.10 (b084 C001) 远低于 0.40 hard 阈；envelope 创新高频率低，大部分股票钉在 1 → cross-section 区分度差，vol_20d 反成 PTA 高低代理。短窗口 60d (b082 C004) 同样失败 (style_r²=0.327)。
- **H2 nested independence (PTA × past-winner)** ✗ — daily 频率上 LHS = (c-l)/(h-l) = F026 atom，CsRank-rank-diff form 不创造新维度 (b084 C002 max_corr=0.68@F026, incr_ic=-0.006)。论文 monthly 双独立维度在 csi1000 daily 不再成立。
- **H3 PTL mirror disposition asymmetry** ✗ (60d) — PTL 与 PTA 60d 同号同 style，是 sign-equivalent 投影非独立维度 (b082 C005)；250d 长窗口分支因 H1 disprove 不必再测。
- **存活通道**：daily-resolution single-bar dim-less ratio (单日 (h-l) 分母) + TsRank ≥60d wrapper —— 这是 F026 路径，也是 P008 escape 完整律的载体；但 anchor_proximity_momentum 内该几何空间已被 F025+F026 cluster 完整占据。

**A 股投资约束**：论文 0.45-1.06%/月 是 long-short self-financing 收益；A 股 T+1 + 单边做空管制 → 实盘只用 long 端 PTA-winner，库内 quintile mono 等价于 cross-section ranking。

---

## Threads

### T001+T004: PTA envelope 几何 [60d, 250d] 全窗口 vol_20d-escape sweet spot 不存在 [✗ DISPROVEN]

> [!failure]+ Thread 结论 (合并 T001 baseline + T004 窗口曲线)
> **Question**: `Div($close, Max($close, N))` 单边非降 envelope 是否独立于 stochastic_position 双边 range 归一族？哪个 N 形成 vol_20d-escape sweet spot？
>
> **Evidence (合并 b082+b084)**:
> - b082 C001 `TsRank((c-TsMin(low,60))/(TsMax(high,60)-TsMin(low,60)),60)` style_r²=0.36 vol_exp=12.04 → reject (双边 range %K TsRank 包装重演 stochastic_position)
> - b082 C003 `TsRank(close/Mean(close,60),60)` style_r²=0.448 → reject (Mean 分母被 vol 撑大)
> - b082 C004 `TsRank(close/TsMax(close,60),60)` PTA 60d style_r²=0.327 vol_exp=19.82 → reject (短窗口 envelope 不够刚性)
> - b084 C001 `TsRank(close/Max(close,250),250)` PTA 250d alpha_surv=**0.10** style_r²=0.244 → reject (envelope 创新高频率低 → 钉在 1)
> - b084 C006 `Sub(CsRank(close/Max(close,250)),CsRank(Std(close,60)))` rank-diff alpha_surv=0.15 ls_t=0.35 vol_20d_exp=30.3 → reject (减 Std60 不净化 vol_20d basis)
>
> **结论**: csi1000 daily 上 PTA 在 [60d, 250d] 全窗口空间 + 双形式 (TsRank wrap + CsRank-rank-diff) 全 fail；论文 monthly anchoring effect 在 daily 频率失活，500d 不必再测 (envelope 更钉)。

### T003: PTL 镜像 disposition asymmetry 独立性 [✗ DISPROVEN 60d 窗口]

> [!failure]+ Thread 结论
> **Evidence**: b082 C005 `TsRank((close-TsMin(close,60))/TsMin(close,60),60)` PTL 60d ic_oos=-0.032 mono=-0.2 style_r²=0.387 → reject (PTL 与 PTA 60d 同号同 style，sign-equivalent 投影)
>
> **结论**: H3 在 60d disprove；250d 因 T001+T004 全窗口 disprove 不必再测。

### T005: P008 anchor cluster lock — daily-resolution dim-less ratio + TsRank 60d 三条件律 [◉ CORE LAW]

> [!success]+ Thread 律核心 (P008 完整律 — 三条件演化源头)
> **Question**: "daily-resolution dim-less close-anchor ratio (单日 (h-l) 分母) + TsRank 60d" 是否是结构性 generalizable 律——可跨 direction 复现 alpha_surv > 1.0 + style_r² < 0.10 + mono_oos PERFECT？
>
> **Evidence trail**:
> - b082 C002 `TsRank((h-c)/(h-l),60)` ic_oos=0.046 ls_t=6.40 mono=1.0 alpha_surv=1.20 style_r²=0.062 → **reserve** (数学镜像 C006，corr ≈ -1)
> - b082 C006 `TsRank((c-l)/(h-l),60)` ic_oos=-0.046 ls_t=-6.31 mono_oos=**-1.0 PERFECT** alpha_surv=1.13 style_r²=0.068 → **admit → [[factors/F026]]** (P008 跨方向复现首证)
> - b084 C003 `TsRank(upper_wick/lower_wick,60)` mono=+1.0 ls_t=+6.63 style_r²=0.026 alpha_surv=1.14 max_corr=**0.89@F025** → reject (与 F025 midpoint colinear；anchor cluster 占据)
> - b084 C004 `CsRank(Mean((c-l)/(h-l),20))` style_r²=0.279 vol_20d_exp=17.87 incr_ic=-0.018 → reject (**wrapper-conditional 律证据**: CsRank ≠ TsRank as vol-escape)
> - b084 C005 `TsRank((close-Mean60)/Std60,60)` z-score style_r²=0.403 vol_20d HIGH → reject (cross-day Mean/Std atom 不属 P008 适用域)
>
> **P008 完整律 (三条件演化, consolidation candidate)**: vol_20d-escape via daily-resolution close-anchor 几何在 csi1000 daily 上**必须**同时满足:
> 1. **Atom 条件**: 单日 OHLC dim-less fraction-of-range ([0,1] bounded, 单日 (h-l) 分母, 不被未来累积 vol 污染)
> 2. **Wrapper 条件**: outer wrap 用 TsRank window ≥ 60d (time-series rank — CsRank/Mean/Std 替代均 fail)
> 3. **几何条件**: 脱 F025/F026 anchor cluster (max_corr<0.40 — 否则 colinear hard fail)
>
> 三条件之一缺失即 fail。三条件演化全部由本方向 batches b082+b084 候选证据支撑（成功对照: F026; 失败对照: b082 C001/C003/C004/C005, b083 C001/C004/C005, b084 C001/C002/C003/C004/C005/C006）。
>
> **本方向 anchor cluster lock**: F025+F026 完整占据 daily intraday position/ratio 几何 — b084 8 候选 max_corr 检验全部触及 (C002@F026=0.68, C003@F025=0.89, C004@F022=0.55)；继续探测必须跨方向 (intraday_price_formation/ohlc_temporal_aggregation/range_structure)，但 b083 0/6 + b081 0/6 显示其他方向 P008 schema 复现极难。

---

## Anti-Recap

- **避免 stochastic_position 双边 range 几何** — 不重 `(close-TsMin(low,N))/(TsMax(high,N)-TsMin(low,N))`；不重 `TsRank($close,N)`；本方向单边 envelope，禁止加 TsMin floor。
- **避免 return-rate 维度** — 不重 sign-conditional return / 5d20d return rate / delta / spread；本方向是 price-level anchor ratio。
- **avoid up_fraction binary mask** — `Mean(I[ret>0],N)>threshold` 几何不同。
- **红线 1**: 候选必须在 design 写明 stochastic_position adjacency check (`Max($close,N)` envelope vs range 区分)。
- **红线 2**: 禁用 `$volume`/`$amount`/`$turnover_rate` 作 PTA 分母 (退化 microstructure_illiquidity)。
- **红线 3**: rate-form (Delta/Sub of PTA) forbidden (lessons F300)。
- **新增 (post b084)**: max_corr<0.40 vs F025/F026/F018/F021/F022/F009 cluster；任何 daily [0,1] bounded fraction-of-range 几何默认触及 anchor cluster。

---

## Related

- 🔴 [[stochastic_position]] `saturated` — 双边 range %K 全 DEAD 归 vol_20d；本方向单边 envelope 同样 disprove
- 🔴 [[asymmetric_momentum]] `dead` · 🔴 [[return_momentum_acceleration]] `dead` — return-rate 族 DEAD；T002 nested independence 在 daily 同样不复现
- 🟡 [[intraday_price_formation]] `saturated` — F003/F022 close-position；P008 daily atom 同源，cluster 相邻
- 🟡 [[ohlc_temporal_aggregation]] `saturated` — b081 0/6 P008 schema 跨方向复现失败证据
- 🟡 [[range_structure]] `dead` — b083 0/6 P008 schema 跨方向复现失败证据
- 📖 [[lessons#Structural Constraints]] — vol_20d 吞噬律 (F301)；P008 三条件律候选源头
- 📖 [[lessons#Forbidden Patterns]] — rate-form (F300)

---

## Narrative Log

### 2026-05-02 [[batches/batch_084/judge|batch_084]] · admit=0 reject=6
**核心**: T002 (CsRank-rank-diff PTA × past-winner) + T004 (PTA 250d 双形式) 双 DISPROVEN；**P008 wrapper-conditional 律确认** (C004 CsRank≠TsRank vol-escape)；z-score cross-day form 不属 P008 适用域 (C005)；F025/F026 cluster 占据 daily intraday geometry (max_corr 检验全触及)。
**Operations**: `status: productive→saturated`; `priority: medium→low`; `rounds: 2→3`; P008 完整律候选送 Phase 5 hypothesis_promoter.

### 2026-05-02 [[batches/batch_082/judge|batch_082]] · admit=1 (F026) reserve=1 (C002 mirror) reject=4
**核心**: P008 escape 跨方向复现成功首证 — TsRank((c-l)/(h-l),60) alpha_surv=1.13 mono_oos=-1.0 PERFECT style_r²=0.068；distillation: 关键不是 "TsRank 60d wrapper" 而是 "atom 不被未来累积 vol 污染"；C002/C006 数学镜像 corr≈-1 → admit C006 canonical, C002 reserve.
**Operations**: `status: exploring→productive`; `rounds: 0→1`; `admits: 0→1`.

> [!quote]+ 2026-05-02 · seeded from [[papers/george_hwang_52weekhigh_2004|George & Hwang JF 2004]]
> Direction created from foundational US-equity paper. PTA = `Div($close, Max($close, 250))` 库内零因子使用 `Max($close, ≥120)` 作 anchor — 完全空白。区分: 单边 envelope vs 双边 range / price-level anchor vs return-rate / continuous distance vs binary mask.
> **Operations** `status: exploring (new)` · `priority: medium` · `created_batch: batch_080`
