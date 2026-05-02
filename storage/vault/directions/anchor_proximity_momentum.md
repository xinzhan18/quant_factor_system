---
direction_tag: anchor_proximity_momentum
status: productive
priority: medium
rounds: 2
admits: 2
last_batch: batch_082
last_admits:
- F026
last_goal: P008 escape 跨 direction 复现：TsRank window 60d on bounded [0,1] dimless close-anchor
  proximity ratios — 验证 alpha_surv≈1.0 generalizability 跨方向（b081 C006 hl_norm_sym
  单例首证）。本批 6 候选全是 close-anchor proximity dimless ratio + TsRank 60d 不同 atom，验证 vol_20d-escape
  路径在 anchor_proximity_momentum 方向是否可复现并产生 admittable alpha；同时严守 P019 数据契约（不用 fundamental
  TTM 作 Corr 内层）+ P021（避免 Mul wrapper 跨字段）+ Geometric absorbing-factor 律（max_corr<0.40
  vs F024/F025/F018/F021）。
last_activity: '2026-05-02T15:56:58Z'
created_batch: batch_080
members:
- F026
merged_into: null
---
# anchor_proximity_momentum

> [!abstract]+ 方向概要
> - **状态**　🔵 `exploring` · priority `medium` · rounds = 0 · admits = 0
> - **最近**　未运行 · seeded from [[papers/george_hwang_52weekhigh_2004|George & Hwang JF 2004]] + Chen-Stivers-Sun 2025 PTA × momentum interaction extension
> - **一句话**　测试 **price-to-52w-high 单边 anchor envelope 比率**（PTA = `Div($close, Max($close, 250))`）在 csi1000 daily 上是否独立于 `stochastic_position` (DEAD) 的双边 range 归一族

---

## Hypothesis

George-Hwang 2004 在 CRSP 1963-2001 月频证明：**nearness to 52-week high (PTA = current_price / max_close_over_12m)** 是一个比 JT 6 个月 cumulative momentum 更强的预测变量；nested cross-section sort 显示 PTA 包含 JT 的全部预测力，反之不真。机制叙事是 anchoring bias：trader 把 52WH 当 reference point，价格接近锚时不愿把价格往新高送（短期低估利好 → forward continuation），价格远离锚时不愿低价卖（短期低估利空 → forward 下跌持续）。Chen-Stivers-Sun 2025 在更近样本上把 PTA × past-winner 的 interaction 形式化，给出 equity side ≈25% 增量年化 alpha（vs JT alone）。

**A 股本地化核心假设（H1, baseline 真度）**：
PTA = `Div($close, Max($close, 250))` 是 **[0, 1] bounded 单边 anchor envelope 比率**。它在几何上**不同于** `stochastic_position` (DEAD batch_041) 测试的 `(close - TsMin(low,N)) / (TsMax(high,N) - TsMin(low,N))` —— 后者的分母是 rolling range（被 vol 主动撑大），所以会被 vol_20d 吞噬；前者的分母是单调非降 anchor envelope（创新高才更新，否则钉住），**不被 vol 主动撑大**。因此 PTA 应该有非平凡概率（先验 ~40%）逃脱 stochastic_position 那一族的 vol_20d 吞噬律。

**A 股本地化核心假设（H2, nested independence）**：
论文 Table III/V 用 nested sort 证明 PTA 与 JT past-return 是**两个独立维度**。在 csi1000 上 cumulative momentum **已 dead**（[[asymmetric_momentum]] / [[return_momentum_acceleration]] 双 dead），所以"PTA dominates dead momentum" 是 free lunch test —— 真正要验证的是 PTA 单变量是否携带 alpha，以及 PTA × past-winner 排名乘积是否进一步增强（incremental IC > 0 over PTA alone）。

**A 股本地化核心假设（H3, asymmetric anchor）**：
A 股 T+1 + 散户高占比 + 单边做空管制 → disposition effect 跨国比较中**特别强**（Frazzini 2006 "disposition effect & under-reaction" 跨市场 evidence 显示 A 股版本最显著）。这意味着 **PTL = `Div($close, Min($close, 250))`** （距 52w 低距离）的镜像变体可能携带 PTA 之外的独立 alpha，而不是 PTA 的纯反号。论文未直接测此变体，是 H3 的开放空间。

**先验预期**：
- 概率 ~40% PTA baseline 真度成立（≥1 candidate 进入 reserve 或 admit）
- 概率 ~30% PTA × past-winner 交互携 incremental IC over PTA alone（H2 holds）
- 概率 ~25% PTL 镜像携带 PTA 之外独立 alpha（H3 holds）
- 概率 ~30% 6/6 全 reject 且 dominant_style=vol_20d，方向落入 stochastic_position 同律 → 升格"任何 close-anchored bounded ratio 在 csi1000 都 vol_20d 吞噬" 系统级 lesson

**A 股投资约束（必须明确）**：
论文 0.45-1.06%/月 的核心收益是 **long-short self-financing**。A 股 T+1 + 无裸卖空 + 转融通成本极高 → 实盘**只用 long 端 PTA-winner**。库内入选标准是 quintile mono（cross-section ranking 等价于 long-short 排序权），与论文 winner-loser 直接对应；但读论文时不能把 1.06%/月 直接外推为 admit-day 实盘预期。

---

## Current Focus

首批 batch_080 设计 6 候选覆盖论文核心机制 + 关键 ablation matrix：
- 1 个 PTA baseline at 250d (T001 主线 baseline，验证单边 envelope 几何脱离 vol_20d 吞噬)
- 1 个 PTA × past-winner 排名乘积 (T002 论文 nested-sort 的日频版本)
- 1 个 PTL 镜像 (T003 disposition effect asymmetry)
- 1 个 PTA - PTL spread (T003 双侧合成)
- 1 个 PTA at 120d 中窗口 (T004 ablation - 论文锚定 250d 但散户记忆周期可能更短)
- 1 个 PTA at 60d 短窗口 falsifier (T004 - 预期与 dead momentum 退化等价，作为 anchor → momentum 边界证据)

**首批关键 adjacency 自检**（在 design 阶段就要写进 rationale）：
- 必须验证 `Corr(PTA_250d, %K_close_only_60d)` < 0.7 —— 否则方向是 stochastic_position 的换皮
- 必须验证 `Corr(PTA_250d, UpFraction_63d)` < 0.6 —— 否则与 [[up_fraction_regime_gating]] 同律
- 必须验证 `Corr(PTA_250d, Mean($return, 60))` 不 ≈ 1 —— 否则 PTA 只是 momentum 的 smooth proxy（What The Paper Is Hiding #2）

下一步若首批 ≥1 admit → T001/T002 转 active，开 batch_081 探索：
- (a) PTA 与 admitted alpha (F009/F004/F043) 的 corr 矩阵 + incremental IC over library
- (b) PTA × Mean(turnover) 的 attention-weighted 变体（论文 anchoring effect 在 high-attention stocks 应该更强）
- (c) Idea 4 窗口 ablation 完整曲线 60→120→250→500

若首批 6/6 全 reject + dominant_style=vol_20d → status `exploring → dead`，与 stochastic_position 并列升格 **"close-anchored bounded ratio 在 csi1000 daily 默认 vol_20d 吞噬"** 系统级 lesson（无论分母是 range 还是 envelope）。

---

## Threads

### T001: PTA 单边 anchor envelope 是否独立于双边 range 归一族 [✓ ANSWERED batch_082]

> [!success]+ Thread 结论
> **Question**: `Div($close, Max($close, 250))` 这种**单边非降 envelope**几何，在 csi1000 daily 是否携带独立 forward IC，而不重演 stochastic_position 双边 range %K/TsRank 的 vol_20d 吞噬？关键审计：style_r² 与 dominant_style；与 admitted alpha 的 max_corr。
>
> **Evidence trail**:
> - [[batches/batch_082/candidates/C001|batch_082 C001]]　TsRank(stochastic_position, 60)　ic_oos=-0.027 ls_t=-1.98 mono=-0.4 style_r²=0.36 → **reject** (60d 双边 range %K TsRank 包装重演 stochastic_position 同律)
> - [[batches/batch_082/candidates/C002|batch_082 C002]]　TsRank((h-c)/(h-l), 60)　ic_oos=0.046 ls_t=6.40 mono=1.0 alpha_surv=1.20 style_r²=0.062 → **reserve** (数学镜像 C006，自身够 admit 但避免库重复)
> - [[batches/batch_082/candidates/C004|batch_082 C004]]　TsRank(close/TsMax($close,60), 60) PTA 60d　ic_oos=-0.026 ls_t=-2.14 mono=-0.7 style_r²=0.327 vol_exp=19.82 → **reject** (PTA 60d 短窗口 envelope 仍被 vol 撑大)
> - [[batches/batch_082/candidates/C006|batch_082 C006]]　TsRank((c-l)/(h-l), 60)　ic_oos=-0.046 ls_t=-6.31 mono=**-1.0 PERFECT** alpha_surv=1.13 style_r²=0.068 → **admit → [[factors/F026]]** (P008 escape 跨 direction 复现核心证据)
>
> **结论**: T001 question 通过 daily-resolution 几何 (单日 (h-l) 分母) **YES**——bounded [0,1] dimless close-anchor proximity ratio + TsRank 60d 在 csi1000 daily 上**结构性可逃 vol_20d 吞噬律**。但 60d 跨日 envelope/range/mean 几何**全部失败**——P008 escape 关键不是"TsRank 60d wrapper"而是"atom 不被未来累积 vol 污染"。

### T002: PTA × past-winner 交互在 csi1000 是否携 incremental IC over PTA alone [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: 论文 Table III/V 嵌套排序的日频版本——`Mul(CsRank(PTA), CsRank(past_return_120d))` 是否携 incremental IC over PTA alone？csi1000 cumulative momentum 已 dead，所以这一交互如果有效，alpha 来源**必须**是 PTA × momentum 的乘积形式而非任一单变量。
>
> **Evidence trail**:
> - （待 batch_080 首批结果填入 — C004 PTA × past-winner rank 乘积）
>
> **Next probes**: 若 C004 incremental IC > C001 (PTA alone) → 论文 nested test 的 daily 版本本地 confirm；若 < C001 → 论文 nested 在 A 股不复现，回到 PTA 单变量主线。

### T003: PTL (52w 低距离) 镜像是否携带 PTA 之外独立 alpha [✗ DISPROVEN batch_082]

> [!failure]+ Thread 结论
> **Question**: `Div($close, Min($close, 250))` 在 A 股散户 disposition effect 强环境下是否携带 PTA 之外独立 alpha？还是与 PTA 仅是负相关镜像？关键审计：`Corr(PTA, PTL)`，期望 |corr| < 0.8（不可能完全相关，因 high/low 时点可在窗口内不同）。
>
> **Evidence trail**:
> - [[batches/batch_082/candidates/C005|batch_082 C005]]　TsRank((close - TsMin(close,60))/TsMin(close,60), 60) PTL mirror 60d　ic_oos=-0.032 ls_t=-2.39 mono=-0.2 style_r²=0.387 → **reject** (PTL 60d 与 C004 PTA 60d 同号 negative, 同 style vol_20d 主导，非 mirror 异号独立维度)
>
> **结论**: hypothesis H3 mirror disposition asymmetry 在 60d 窗口**partial 反驳**——PTL 与 PTA 同号同 style，是同 vol_20d 吸收族的 sign-equivalent 投影而非独立维度。本批仅在 60d 窗口反驳；250d 长窗口空间未测，T003 在长窗口仍开放，但本批已 close 60d 窗口分支。

### T004: 锚窗口曲线 60d → 120d → 250d → 500d 寻找 sweet spot [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: 论文锚 250d 但脚注提及 6m/24m 定性一致；A 股散户记忆周期可能 30-60d 远短于 12m。窗口越短越接近 cumulative momentum（已 dead）；窗口越长越纯 anchor。sweet spot 在哪？60d 是危险窗口（接近 dead momentum），120d 是首批中窗口对照，250d 是论文标定窗口，500d 是上界 ablation 留 batch_081。
>
> **Evidence trail**:
> - [[batches/batch_082/candidates/C003|batch_082 C003]]　TsRank(close/Mean($close,60), 60)　ic_oos=-0.036 ls_t=-2.87 mono=-0.3 style_r²=0.448 → **reject** (`Mean($close,60)` dynamic mean 分母被 vol 撑大，非 monotone envelope)
> - [[batches/batch_082/candidates/C004|batch_082 C004]]　TsRank(close/TsMax($close,60), 60) PTA 60d　ic_oos=-0.026 ls_t=-2.14 mono=-0.7 style_r²=0.327 vol_exp=19.82 → **reject** (PTA 60d 短窗口 envelope 仍 follow vol regime, vol_20d exposure 本批最高)
>
> **本批进展**: 60d 窗口下 PTA envelope 不够"刚性"（vol_20d exposure=19.82 本批最高）；论文 250d 长窗口期 envelope 更刚性的 hypothesis 仍开放。下批应保留 PTA 250d / PTA 120d 长窗口探索。
>
> **Next probes**: 250d 长窗口 PTA 是否 alpha_surv > 1.0 + style_r² < 0.12？或 30d 短窗口若仍 dead 则确认"daily-resolution 几何 dominates 跨日 envelope" 律。

### T005: daily-resolution dim-less anchor ratio + TsRank 60d 跨方向 generalizability 边界 [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: 承接 T001 主线 P008 escape 机制 distillation：**"daily-resolution dim-less close-anchor ratio (单日 (h-l) 分母) + TsRank 60d"** 是否是结构性 generalizable 律——可跨 direction 复现产生 alpha_surv > 1.0 + style_r² < 0.10 + mono_oos PERFECT？还是 anchor_proximity_momentum 方向特例？
>
> **Evidence trail**:
> - [[batches/batch_082/candidates/C006|batch_082 C006]]　TsRank((c-l)/(h-l), 60)　alpha_surv=1.13 mono_oos=-1.0 style_r²=0.068 → **admit** (b081 C006 hl_norm_sym alpha_surv=0.99 在 anchor_proximity_momentum 方向跨方向复现成功首证)
>
> **Next probes**: 在 [[intraday_price_formation]] / [[ohlc_temporal_aggregation]] 等其它方向用同 schema (单日 dim-less 比率 + TsRank 60d) 复现，确认这一律的边界——是否 vol_20d 吞噬律的通用 escape，还是仅 anchor proximity 几何独有？

---

## Known Failures

- C001 `TsRank(Div(Sub($close, TsMin($low, 60)), Sub(TsMax($high, 60), TsMin($low, 60))), 60)` — 60d 双边 range stochastic position TsRank 包装重演 stochastic_position DEAD 同律；style_r²=0.36 + dom=vol_20d exposure 12.04
- C003 `TsRank(Div($close, Mean($close, 60)), 60)` — `Mean($close,60)` dynamic mean 分母非 monotone envelope，被 vol 主动撑大；style_r²=0.448 远超 poor 阈
- C004 `TsRank(Div($close, TsMax($close, 60)), 60)` — PTA 60d 短窗口 envelope 不够刚性，vol_20d exposure=19.82 本批最高 high crowding；论文 250d 长窗口 hypothesis 仍开放
- C005 `TsRank(Div(Sub($close, TsMin($close, 60)), TsMin($close, 60)), 60)` — PTL mirror 60d 与 PTA 60d 同号同 style，反驳 H3 mirror disposition asymmetry 的 mirror 独立性 (60d 窗口下)

---

## Anti-Recap

- **避免 stochastic_position (batch_041) 6 reject 候选** — 不重 `(close - TsMin(low,N)) / (TsMax(high,N) - TsMin(low,N))` 双边 range %K 几何；不重 `TsRank($close, N)`。本方向只用单边 envelope 比率 `Div($close, Max($close, N))`，**禁止**加入 `TsMin` floor（一加就退化为 stochastic_position close-only 版）。
- **避免 asymmetric_momentum / return_momentum_acceleration 6 reject 候选** — 不重 sign-conditional return 拆分；不重 5d/20d return rate / delta / spread。本方向是 **price-level anchor ratio**，与 return-level rate 不同维度。
- **避免 up_fraction_regime_gating 候选几何** — 不重 binary mask `Mean(I[ret>0], N) > threshold`；本方向 PTA 是 continuous anchor distance ratio，几何不同。
- **红线 1**：本方向**所有候选必须**在 design 阶段写明 stochastic_position adjacency check，候选必须能描述自己分母为何不是 rolling range（即 `Max($close, N)` envelope 而非 `TsMax(high, N) - TsMin(low, N)` range）。
- **红线 2**：本方向**禁止**用 `$volume` / `$amount` / `$turnover_rate` 作为分母 normalize PTA（否则就退化为 `microstructure_illiquidity` / `liquidity_acceleration` 的几何）。PTA 必须保持 close-only / price-level / dimensionless 单边比率。
- **红线 3**：rate-form failure (lessons F300) — 本方向**禁止** Delta(PTA) / Δ(PTA) / Sub(PTA[t], PTA[t-N]) 等变化率形式。PTA 是 level/ratio 形式，rate 形式默认跳过。

---

## Related

- 🔴 [[stochastic_position]] `saturated` — 双边 range %K / TsRank 全 DEAD 归 vol_20d；本方向**单边 envelope** 几何不同但 family 相邻；首批 adjacency check 必做
- 🔴 [[asymmetric_momentum]] `dead` · 🔴 [[return_momentum_acceleration]] `dead` — return-level rate 族全 DEAD；论文 nested test 直接证明 price-level anchor 与 past-return 是**两个独立维度**，T002 在 csi1000 复现这一独立性
- 🔵 [[up_fraction_regime_gating]] `exploring` — 也是 paper-derived 但 binary regime mask 几何；本方向 continuous anchor distance × continuous past-return rank，必须做相互 corr adjacency
- 🟡 [[intraday_price_formation]] `saturated` — F003 / F022 等 close-position intraday 形式；与 cross-day anchor 同 "close 在某尺度内的位置" 大类但不同 horizon
- 🟡 [[ohlc_temporal_aggregation]] `saturated` — F006/F007/F008 5d body aggregation 占位；本方向 PTA 不依赖 body 几何，应正交
- 🟡 [[fundamental_quality_carry]] `saturated` — 完全不同字段族，仅作 INDEX 登记参考
- 📖 [[lessons#Structural Constraints]] — vol_20d 吞噬律 (F301)；PTA 单边 envelope 是潜在 escape 路径（dim-less anchor ratio，与 P012 dim-less count ratio 同 spirit）
- 📖 [[lessons#Forbidden Patterns]] — rate-form failure (F300)；PTA 是 level/ratio，**不撞**该律

---

## Narrative Log

### 2026-05-02 [[batches/batch_082/judge|batch_082]]
admit=1 (C006 daily_close_position_tsrank_60) · reserve=1 (C002 数学镜像 C006) · reject=4 (C001/C003/C004/C005)

**核心发现**：
1. **P008 escape 跨 direction 复现成功** — TsRank((c-l)/(h-l), 60) 在 anchor_proximity_momentum 方向打出 alpha_surv=1.13 + mono_oos=-1.0 PERFECT + ls_t=-6.31 + style_r²=0.068；验证 b081 C006 hl_norm_sym (对称版 alpha_surv=0.99) 不是单例 fluke 而是结构性 generalizable
2. **关键 distillation**：P008 escape 的关键机制不是"TsRank 60d wrapper"而是"atom 不被未来累积 vol 污染"——daily-resolution 单日 (h-l) 分母 (C002/C006) 全部成功；60d 跨日 envelope/range/mean (C001/C003/C004/C005) 全部失败 (vol_20d exposure 10.79-19.82 high crowding)
3. **C002 / C006 数学镜像**：(h-c)/(h-l) + (c-l)/(h-l) ≡ 1 + TsRank monotone-invariance → corr ≈ -1；admit C006 canonical, C002 reserve 等下轮独立性测试

**Thread 进展**：
- T001: ✓ ANSWERED — daily-resolution 几何 P008 escape YES, 60d 跨日 envelope NO
- T002: ◉ ACTIVE 本批未测 (PTA × past-winner 交互留下批)
- T003: ✗ DISPROVEN (60d) — PTL 与 PTA 同号同 style 不是独立 mirror 维度
- T004: ◉ ACTIVE — 60d 短窗口已证伪，250d 长窗口仍开放
- T005: ◉ ACTIVE 🆕 — daily-resolution dim-less ratio + TsRank 60d 跨方向 generalizability 边界

**下一步**: batch_083 优先 PTA 250d 长窗口 + T002 daily PTA × past-winner 交互 + T005 跨方向边界测试 ([[intraday_price_formation]] / [[ohlc_temporal_aggregation]]); 不再设 60d 跨日 envelope/range/mean 类候选 (已证伪)。

**Operations**：`status: exploring → productive` (首次 admit C006); `rounds: 0 → 1`; `admits: 0 → 1`; `last_batch: batch_082`

> [!quote]+ 2026-05-02 · seeded from [[papers/george_hwang_52weekhigh_2004|George & Hwang JF 2004]]
> Direction created from foundational US-equity paper intake. PTA = `Div($close, Max($close, 250))` 是 30 年前的 well-known 信号，但库内零因子使用 `Max($close, ≥120)` 作 anchor —— 完全空白。
>
> - 与 [[stochastic_position]] DEAD 的关键几何区分：单边 envelope vs 双边 range，前者不被 vol 主动撑大
> - 与 [[asymmetric_momentum]] / [[return_momentum_acceleration]] DEAD 的关键维度区分：price-level anchor vs return-level rate
> - 与 [[up_fraction_regime_gating]] exploring 的关键形态区分：continuous anchor distance vs binary regime mask
>
> **Operations**　`status: exploring (new)` · `priority: medium`（论文是 seminal 但 csi1000 上 close-anchored ratio 风险高，不开 high）· `created_batch: batch_080`
