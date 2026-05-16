---
paper_slug: george_hwang_52weekhigh_2004
source_pdf: raw/papers/George-Hwang-52WeekHigh-2004.pdf
source_kind: generic_pdf
arxiv_id: null
status: converted
primary_frequency: daily
direction_tag: anchor_proximity_momentum
reviewed_at: 2026-05-02
---

# The 52-Week High and Momentum Investing (George & Hwang, JF 2004)

## Core Claim

George & Hwang 在 CRSP 1963-2001 全样本上做出三件事：

1. 把 **PTA = `current_price / 52_week_high`**（"nearness to 52-week high"）当排名变量，做 (6,6) 长 top-30% 短 bottom-30% 的 self-financing strategy，月度收益 0.45%（含一月）/ 1.23%（除一月）/ 1.06%（FM 控 size + bid-ask）—— 与 JT 6 个月个股动量 (0.48% / 1.07% / 0.46%) 同量级，但 t-stat 在剔一月后 7.06 vs JT 6.97。
2. **嵌套排序**：在 JT winner / loser 子集内**再按 PTA 排序**仍能拿到 0.46-0.56% 的 winner-loser；反之**在 PTA winner / loser 子集内按 JT 排序**只能拿到 0.22-0.27% 且大多 t-stat<2。结论：**PTA 包住了 JT 的预测力**，反之不真。Fama-MacBeth 多策略联合回归同样把 JT 系数压到不显著、PTA 系数仍显著。
3. **长期反转**：PTA 形成的 (6,12) / (6,36) 不像 JT 那样 60 个月后大幅反转——PTA 的 winner 收益**没有**镜像 (12-60) 月负收益。作者把这解读为：anchoring bias 的修正不需要 overcorrection；short-term momentum 与 long-term reversal 是**两个独立现象**而非"news lifecycle"的两段。

机制叙事：传统 BSV / DHS / HS 模型把动量解释为"信息渗透太慢 + 后期 overreact"。George-Hwang 替换为：**52WH 是 trader 的锚点**，价格接近锚时 trader 因为"不想往新高送"而短期低估利好；远离锚时因为"不想以这么低价格卖"而短期低估利空。这是 Kahneman-Tversky anchoring + 类比 Grinblatt-Han disposition effect 的 anchor 替代版（GH 用 long-term high 而非 acquisition price）。

实验依赖：纯月频 CRSP 美股，all common stocks (CRSP share codes 10/11)，等权组合，跳一个月降 bid-ask 影响。**整个论文不用任何 intraday 信息，唯一时序量是 12 个月 daily/weekly close 的 max**。

## Aha Moment

**单边比率（price ÷ rolling max of price）和双边归一（stochastic %K）是不同的几何对象**——`stochastic_position` direction 已经把后者证伪并归因到 vol_20d 吞噬，但前者从未在本库测过，且其分母是单调非降的 anchor envelope 而非 vol-driven 范围，理论上不应该被 vol_20d 吸收。

## Candidate Ideas

### Idea 1 — Raw PTA (price-to-anchor ratio) at 250d window

- **Paper mechanism**: `Pi,t-1 / max(Pi, t-12m to t-1)` — 当前价与过去 12 月最高收盘价之比。月频 cross-section rank 形成 (6,6) 自融资组合，剔一月 t=7.06。
- **Target frequency**: daily（论文用月频，我们降到 1d/5d/20d horizon）
- **Current readiness**: dsl_ready
- **Required fields**: `$close`
- **Why it may survive daily downsampling**: PTA 是无量纲 [0, 1] 比率，分母 `Max($close, 250)` 是**单调非降 envelope**——一旦 close 创新高分母被钉住，否则 close 上行 PTA 上行；这与 `stochastic_position` 的 `(close - TsMin(low,N)) / (TsMax(high,N) - TsMin(low,N))` **几何不同**：%K 的分母在窗口内同时抓 low 和 high，是 rolling range（vol-driven）；PTA 分母只是 anchor，**不会随波动率上升而被动膨胀**。
- **Main distortion risk**: (a) PTA 在 long-bull 阶段对所有股票同时贴近 1，cross-section 区分度退化；(b) 与 csi1000 的 60d-momentum 相关（Corr(Mean($return, 60), PTA) > 0 ex ante），但 paper 已给出 PTA dominates JT 的直接证据，应在我们 6CP 的 incremental_ic 上验证；(c) 250d 在 csi1000 上的有效覆盖（IPO ≤1y 个股）需要 partial-window fallback，可能让 coverage<0.80 触发 P010。
- **Suggested direction tag**: `anchor_proximity_momentum`

### Idea 2 — PTA × past-winner gating (Hwang core finding + Chen-Stivers-Sun 2025 PTA × momentum interaction)

- **Paper mechanism**: 嵌套排序——PTA 在 JT winner subset 内仍 0.46% / 在 JT loser subset 内 0.56%（t≥3.13）。Chen-Stivers-Sun 2025 (paywalled, only abstract referenced here) 把这一交互 formalize 成 "high-PTA past-winner outperform low-PTA past-winner"，给 equity side 一个 ≈25% 增量年化超额（cf. JT alone）。
- **Target frequency**: daily
- **Current readiness**: dsl_ready
- **Required fields**: `$close`
- **Why it may survive daily downsampling**: gating 是**乘法**，不引入新数据依赖；本质是把 PTA 用作 momentum 信号的"质量过滤"——只在过去 60 日确实涨过的股票中找仍未触锚的、或已贴锚但仍能继续上行的。这个 gating 维度在 `up_fraction_regime_gating` 已经探测但用的是"上涨日比例 > 0.6"作 binary mask；PTA 是**连续 anchor distance**而非 binary，且锚的语义经济学解释不同（Singha 用 stock-specific drift；Hwang 用 reference-point anchoring）。
- **Main distortion risk**: 与 `up_fraction_regime_gating` 几何重叠概率约 30%——若 PTA 与 UpFraction 在 60d 窗口高 corr (>0.6) 则只是同律换包装；必须在首批做 `Corr(PTA, UpFraction_63d)` adjacency check。另一风险是与 `stochastic_position` C005 (`%K close-only 20d`) 的 long-window 复刻：如果换成 `(close - TsMin(close, 250)) / (TsMax(close, 250) - TsMin(close, 250))` 就**变成 stochastic_position 的 close-only 版本**——必须**只用 PTA 单边比率，不引入 TsMin floor**。
- **Suggested direction tag**: `anchor_proximity_momentum`

### Idea 3 — Distance from 52-week LOW (asymmetric anchor — A-share T+1 + retail anchoring potentially distinct from US)

- **Paper mechanism**: Hwang 论文未直接测 PTL = `current / 52w_low`（他只在嵌套表附录提到 "near 52w low" 的 trader 不愿低价卖），但 Grinblatt-Han 2002 disposition-effect 文献暗示 **acquisition-price-as-anchor** 在 underwater 情形下**更强**。在 A 股 T+1 + 散户高比例下，"低价不肯卖"的处置效应是出名 stronger than 美国 (Frazzini 2006 跨国对比)，PTL 可能携带 PTA 之外的独立 alpha。
- **Target frequency**: daily
- **Current readiness**: dsl_ready
- **Required fields**: `$close`
- **Why it may survive daily downsampling**: 与 PTA 完全对偶——`$close / Min($close, 250)` 也是单边比率，envelope 这次是单调非升。
- **Main distortion risk**: PTL 与 PTA 大概率 **负相关 0.3-0.6**（个股价格一阶趋势让两者反向），但**不可能完美负相关**（窗口内 high 和 low 可发生在不同时点）—— 应保留 PTL 作 ablation 而非 default 删除。次要风险：PTL 在小盘 csi1000 + IPO 多的环境下，分母 250d-min 可能被 IPO 后第一个跌停日永久锚定，让 PTL 长期偏离 1，丢 cross-section 区分度。
- **Suggested direction tag**: `anchor_proximity_momentum`

### Idea 4 — Shorter-anchor variants (60d / 120d) to test anchor-horizon decay

- **Paper mechanism**: Hwang 用 12 个月固定窗口；他主要在脚注里说"试过 6 月 / 24 月，结果定性一致但 12 月最优"。在 csi1000 上散户记忆周期可能短得多——60d 或 120d 锚点更贴合"近期高点 anchoring"。
- **Target frequency**: daily
- **Current readiness**: dsl_ready
- **Required fields**: `$close`
- **Why it may survive daily downsampling**: 完全在 DSL 表达力内（`Max($close, 60)` / `Max($close, 120)`）。
- **Main distortion risk**: window 越短越接近"近期 momentum"——60d Max 在数学上接近 `$close > Mean($close, 60)` 这种 trend signal 的渐近形式，可能与 `return_momentum_acceleration` (DEAD) 的 5d-20d spread 同律收敛到 vol_20d。**60d 是危险窗口**；120d-250d 是论文意义上的"long-term anchor"，应作为窗口上下界 ablation。
- **Suggested direction tag**: `anchor_proximity_momentum`

### Idea 5 — PTA at signed-dispersion window (anchoring in fundamental space, blocked-by-uncertain-mapping)

- **Paper mechanism**: 类比延伸——把 anchor 从 price 换成 **PE / PB ratio 的 12 月最高值**（"valuation anchor"）。Hwang 论文未做此变体，但 Lakonishok-Shleifer-Vishny 1994 关于 value 的 reference-point 论文暗示存在 valuation anchoring。
- **Target frequency**: daily
- **Current readiness**: dsl_ready 但价值不明
- **Required fields**: `$pb_ratio` / `$pe_ratio`
- **Why it may survive daily downsampling**: PE/PB 都是日度 PIT；`Max($pe_ratio, 250)` 完全可表达。
- **Main distortion risk**: `pit_valuation_pure` 和 `value_liquidity_interaction` 已在估值空间 active；fundamental 化的 anchor 大概率被 F028 (1/PB) / F040 (PE×PB rank) 几何吃掉。**本轮不开**，挂 Blocked Ideas For Future。
- **Suggested direction tag**: null（不入主线）

## Data Requirements

**论文依赖**：
- 月频 CRSP daily close（用来算 12 个月 max）
- 等权组合 + skip-1-month + Fama-French 6 因子模型（risk adjustment）
- size 控制（market cap）— 我们有 `$market_cap`
- bid-ask bounce 控制（前月 return）— 我们有 `Ref($close, 1)` 自动控

**我们缺什么**：
- **无**——PTA 的所有数据依赖（close + 长窗口 max）都是日频价量白名单内
- 唯一可能的覆盖问题：250d window 对 IPO ≤1y 个股 partial coverage —— 必须 baseline 验证 `Max($close, 250)` 的 coverage ≥ 0.80（lessons P010 红线）
- 论文是月频信号 + 月频持有；我们是日频信号 + next-1d/5d/20d horizon —— 频率降阶差异需关注（PTA 在月频 0.45%/月，降到日频后单日 IC 量级很小，必须看 ICIR 而非 absolute IC）

**DSL 算子映射**（paper 侧 → 我们侧）：
- `max(close over t-12m to t-1)` → `Max($close, 250)` ✓（白名单含 `Max`）
- `current_price / max` → `Div($close, Max($close, 250))` ✓
- 等权组合 long-short → 我们 6CP 自动通过 quintile mono 评估
- size control → cross-section neutralization 在 Phase 2 vectorized_barra 自动做

## Mapping To Current System

**既有覆盖（防重造轮子）**：

- **`stochastic_position` (DEAD batch_041)** —— 测了 `(close - TsMin(low, N)) / (TsMax(high, N) - TsMin(low, N))` 与 `TsRank($close, N)` 两种**双边归一**形式，全 6 候选 mono_oos 崩塌 + dominant_style=vol_20d。**关键区分**：%K 分母是 `TsMax(high) - TsMin(low)` = rolling range（被 vol 撑大）；PTA 分母是 `Max($close, 250)` = 单调非降 anchor envelope（不被 vol 撑大）。同样是"close 在某个尺度内的位置"，但**尺度的几何含义不同**——一个是范围（vol-driven），另一个是包络（trend-driven）。这是同 family 但不同 sub-family。
- **`asymmetric_momentum` (DEAD)** + **`return_momentum_acceleration` (DEAD)** —— 都是 return-based momentum 拆分 / 加速度，与 PTA 这种 price-level-based 的 anchor 信号机制不同；论文 Table III/V 的 nested test 直接证明 price-level anchor 与 past-return momentum 是**两个独立维度**。
- **`up_fraction_regime_gating` (exploring batch_080)** —— 用 binary mask "上涨日比例 > 0.6" 做门控；PTA 是**连续 anchor distance**，且语义是 reference-point anchoring 而非 stock-specific drift regime。两者**可能**正交但需第一批做 corr 验证。

**部分覆盖（可作为 thread 归入现有方向 — REJECTED）**：

- **可否归入 `stochastic_position`**？不可——该方向是 `saturated → archived` 候选，新增几何（哪怕真的不同）会让 saturated 状态混乱；且 stochastic_position 的核心结论"price position 跨日仍失效"是基于双边归一，**单边 anchor ratio 没有被它的实验否定**，需独立打开方向才能正确归因。

**未覆盖（NEW angle, 直接对应 Idea 1-4）**：

- 库内零因子使用 `Max($close, ≥120)` 作 anchor —— 完全空白
- nested PTA × past-return-rank 交互未被测过（Idea 2）
- 单边 anchor envelope 几何（vs 双边 range 几何）未被测过

**最优落点**：新开 `anchor_proximity_momentum`，主线 Idea 1（PTA baseline）+ Idea 2（PTA × past-winner 交互），Idea 3（PTL 镜像）+ Idea 4（窗口 ablation）作辅。

**DSL 还是 Python**：全部 DSL。`Max`, `Min`, `Div`, `Mul`, `CsRank`, `Mean`, `Sub`, `Sign` 全在白名单。

## Feasibility Assessment

### Idea 1 — Raw PTA at 250d
- **Original dependency**: 月频 CRSP close + 12m rolling max
- **Coverage in current system**: `$close` ✓；`Max($close, 250)` 在白名单，但需 Phase 1 baseline 验证 coverage ≥ 0.80（IPO ≤1y partial window 风险）
- **Can it be downgraded to daily?**: 是——anchor 本就是 daily 滚动量，月频是降频版而非升频版
- **Implementation path**: dsl
- **Missing piece**: 无；表达式 `Div($close, Max($close, 250))`

### Idea 2 — PTA × past-winner gating
- **Original dependency**: PTA + 6m past return rank
- **Coverage in current system**: 全 daily 白名单
- **Can it be downgraded to daily?**: 是
- **Implementation path**: dsl
- **Missing piece**: 无；表达式（举例）：`Mul(CsRank(Div($close, Max($close, 250))), CsRank(Sub($close, Ref($close, 120))))`

### Idea 3 — PTL (52-week low distance)
- **Original dependency**: 12m rolling min of close
- **Coverage in current system**: `Min($close, 250)` 白名单
- **Can it be downgraded to daily?**: 是
- **Implementation path**: dsl
- **Missing piece**: 无；表达式 `Div($close, Min($close, 250))`；A 股 IPO 后第一跌停日永久锚定 risk 应在 result 阶段看 cross-section dispersion

### Idea 4 — Window ablation 60d / 120d / 500d
- **Original dependency**: paper 锚定 250d 但脚注提及 6m/24m
- **Coverage in current system**: 全白名单
- **Can it be downgraded to daily?**: 是
- **Implementation path**: dsl
- **Missing piece**: 无；60d 危险（接近 momentum）；120d / 500d 是论文窗口上下界

### Idea 5 — Valuation anchor (PE/PB max)
- **Original dependency**: 论文未做；类比延伸
- **Coverage in current system**: `pit_valuation_pure` + `value_liquidity_interaction` 已饱和该空间
- **Can it be downgraded to daily?**: 是
- **Implementation path**: dsl 但路径覆盖
- **Missing piece**: 优先级低；本轮不开

## What The Paper Is Hiding

1. **CRSP 1963-2001 美股 ≠ csi1000 A 股 2015-2024（最大 hidden assumption）** —— 论文样本一半在 pre-decimalization 时期（1963-2001 中 1963-1996 都用 1/8 美元 tick），bid-ask bounce 结构与 A 股 T+1 + 0.01 元 tick 完全不同。论文的 anchoring bias 对象是 70 年代美股个人投资者 + 90 年代机构；csi1000 散户占比 80%+ 但散户**记忆周期更短**（A 股研究公认 30-60d 而非 12m），所以 250d anchor 在 A 股可能是**机构**的 anchor 而非散户——signal 本身可能存在但 magnitude 不应直接 0.45%/月外推。

2. **Anchoring 还是 mechanically slow-moving bounded ratio？** —— PTA = `close / max(close, 250)` 是一个 [0, 1] bounded、慢速变化的比率。任何"接近某个上界的比率"在 bull market 都自动贴近 1（与 bull 同方向），在 bear 自动远离 1。论文的 cross-section 排名测试**部分**控制了 market beta，但**没有**做 PTA 与 trailing return correlation 的彻底分离——0.65%/月的 PTA 自融资收益里有多少是"PTA 是 momentum 的 smooth proxy"？Chen-Stivers-Sun 2025 的 PTA × past-return interaction 可能正是为了**部分**回答这一点（"PTA-residual conditional on past-return rank"），但他们也只是部分隔离。我们做 Phase 2 时**必须**看 incremental IC over a baseline momentum factor，而不是 raw IC。

3. **Long-short 利润不可在 A 股做空** —— 论文核心 0.45%/月 / 1.06%/月（剔一月）是 winner-loser 自融资。A 股 T+1 + 无裸卖空 + 转融通成本极高的环境下，**只有 long-only PTA-winner 那一侧投资得了**。论文 Table I 显示 winner 月 1.51% / loser 月 1.06% —— 长侧自身 1.51% 已是 month CSI1000 平均水平的 1.5x，但**不是论文核心 claim**；论文真正的"alpha"全在 long-short spread。我们入库后用作 long-only 的 cross-section ranking 信号是合规的（quintile mono 评估等价于 long-short 排序权），但读论文时不能把 0.45%/月 直接外推为我们的 admit-day 预期。

4. **JT (6,6) baseline 偏弱** —— 论文用 1963-2001 的 (6,6) JT 作 benchmark；JT 在 1990s 后已经**部分死亡** (Asness-Frazzini-Pedersen 2014)，2010+ 几乎完全 dead in cross-section。所以"PTA dominates JT" 这个 dominance 可能本来就是因为 baseline 在样本后段崩塌而不是 PTA 真的更强。我们 csi1000 上 cumulative momentum **已 dead** (`return_momentum_acceleration` / `asymmetric_momentum`)，所以"PTA dominates dead momentum" 不算 free win——必须看 PTA 是否能 dominate 库内仍 alive 的 reversal / vol cluster (F009 / F004 / F043) 才有意义。

5. **Long-term reversal "doesn't reverse" 是 35-year average**, single-regime 看可能完全不同 —— Table VI/VII 的 (12, 60) 反转测试是 1963-2001 平均；A 股 2015-2024 是单 regime（10 年）+ 2 次大风格切换 (2017 大白马 / 2021 小盘高 vol)，single-regime PTA 是否真不反转**不能复刻**论文级 evidence。退一步说，我们也不预测 60 月 horizon —— 我们最长 horizon 是 next-20d，所以这一点的 binding 主要是机制信念问题（"PTA 是不是真的非反转 mechanism"），不影响 implementation。

6. **PTA 与 size 的天然纠缠** —— 在论文 Fama-MacBeth 回归里 PTA dummy 的系数是控 size 后的 incremental，但**只是控当期 log size**。PTA 本身在小盘高 vol 个股上分布更宽（小盘股更容易远离 anchor），在大盘股上更集中——这是个**conditional cross-section dispersion**问题，单变量 size 控不住。我们 csi1000 只取小盘 1000 只 universe 已经部分缓解（universe 内 size dispersion 比 CRSP all-stocks 小一个量级），但仍需在 6CP 的 Barra alpha_survival 上看是否 size_exposure > 红线。

**最重要的 3 条**：#1 (universe / regime mismatch)、#2 (PTA 是不是 momentum smooth proxy)、#3 (long-only 投资性约束)。

## Blocked Ideas For Future

- **Industry-relative PTA**（个股 PTA - 行业均值 PTA）—— 论文 Section II.D 隐含此变体（控行业效应可能放大 individual anchoring effect）。**Unblock 条件**：接入 SW / 中信行业归属表（`industry_id` 字段），或用 K-means cluster on returns 自构 group。
- **Earnings-announcement-anchor variant** —— 论文未做但 Frankel-Lee 1998 暗示"EPS surprise + 锚点"组合更强。**Unblock 条件**：接入 EPS announcement event date + post-announcement window 标记字段。
- **Intraday "test 52WH" event signal** —— 当 `$high == Max($high, 250)` 当日是 "tested 52WH"，往后 N 日的 follow-through 是 Hwang 论文的隐藏 sub-claim（"信息最终 prevail"）。**Unblock 条件**：接入 minute bars 看 intraday max-test 时点；日频版可用 `Eq($high, Max($high, 250))` 但 boolean 信号 cross-section 区分度过低。
- **Valuation anchor (PE / PB max)** —— Idea 5；**Unblock 条件**：`pit_valuation_pure` 与 `value_liquidity_interaction` 双双饱和后再考虑，预期吸收路径过深。

## Direction Recommendation

- **Decision**: `create_direction`
- **Selected idea**: Idea 1（Raw PTA baseline）为 baseline + Idea 2（PTA × past-winner 交互）为论文核心机制 main thread + Idea 3（PTL）和 Idea 4（窗口 ablation）作辅
- **direction_tag**: `anchor_proximity_momentum`
- **Initial threads**:
  - T001: `Div($close, Max($close, 250))` 单边 anchor ratio 在 csi1000 daily 是否独立于 stochastic_position 的双边归一族（即不被 vol_20d 吞噬）？baseline-first 验证。
  - T002: PTA × past-return-rank 交互（Hwang 嵌套排序的 daily 版本）是否携带 incremental IC over PTA alone & over momentum alone？csi1000 cumulative momentum 已 dead，关键是看 PTA 单变量是否仍有效 + 交互是否进一步放大。
  - T003: PTL = `Div($close, Min($close, 250))` 镜像变体在 A 股散户 disposition effect 强环境下是否携带 PTA 之外的独立 alpha？
  - T004: 窗口 ablation 60d / 120d / 250d / 500d 寻找 sweet spot；防止 60d 退化为已 dead 的 cumulative momentum。
- **First candidate families**（DSL 草图，留给 `/factor-idea` 细化）:
  1. `Div($close, Max($close, 250))` — T001 PTA baseline 250d
  2. `Div($close, Max($close, 120))` — T004 中窗口对照
  3. `Div($close, Min($close, 250))` — T003 PTL 镜像
  4. `Mul(CsRank(Div($close, Max($close, 250))), CsRank(Sub($close, Ref($close, 120))))` — T002 PTA × past-winner 排名乘积
  5. `Sub(CsRank(Div($close, Max($close, 250))), CsRank(Div($close, Min($close, 250))))` — T003 spread 形式（PTA - PTL）
  6. `Div($close, Max($close, 60))` — T004 短窗口 sentinel（**预期失败**，作为 anchor → momentum 退化的 falsification 证据）
- **Minimum unblock condition**: 不涉及（所有字段与算子均在白名单内；唯一 baseline 风险是 250d window 对 IPO ≤1y 个股 coverage ≥ 0.80）

---

## Related

- 🔴 [[../directions/stochastic_position]] `saturated` — 双边 range-normalized %K 与 TsRank 全 DEAD；本方向是单边 anchor envelope 几何，**几何不同但 family 相邻** —— 第一道审计就是验证 PTA 与 %K 在 csi1000 上 corr<0.7
- 🔴 [[../directions/asymmetric_momentum]] `dead` · 🔴 [[../directions/return_momentum_acceleration]] `dead` — 收益率拆分 / 变化率族全 DEAD；论文直接证明 anchor (price-level) 与 past-return (return-level) 是**两个独立维度**，本方向 thread T002 nested test 用来在 csi1000 复现这一独立性
- 🔵 [[../directions/up_fraction_regime_gating]] `exploring` — paper-derived 二元 regime gate × 弱 base signal；本方向 T002 的 PTA × past-winner 是**连续 anchor distance × continuous past-return rank**，与 binary-mask gating 几何不同，但首批必做 `Corr(PTA_250, UpFraction_63)` ≥0.6 的 adjacency check
- 🟡 [[../directions/intraday_price_formation]] `saturated` —— F003 / F022 等 close-position intraday 形式；与 cross-day anchor 不在同一个 horizon 但同 "close 在某尺度内的位置" 大类
- 📖 [[../lessons#Structural Constraints]] — vol_20d 吞噬律 (F301)；PTA 单边比率是潜在 escape 路径（与 P012 dim-less count ratio 同 spirit 的 dim-less anchor ratio）
- 📖 [[../lessons#Forbidden Patterns]] — rate-form failure (F300)；PTA 是 level/ratio 形式而非 rate/delta，**不撞**该律
