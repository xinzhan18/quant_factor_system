---
direction_tag: up_fraction_regime_gating
status: exploring
priority: medium
rounds: 0
admits: 0
last_batch: pending
last_admits: []
last_goal: null
last_activity: null
created_batch: batch_080
members: []
merged_into: null
---

# up_fraction_regime_gating

> [!abstract]+ 方向概要
> - **状态**　🔵 `exploring` · priority `medium` · rounds = 0 · admits = 0
> - **最近**　未运行 · seeded from [[../papers/arxiv_2511_12490v1|Singha 2025 (arXiv 2511.12490)]]
> - **一句话**　测试 paper 提出的"`Mean(I[ret>0], 63) > 0.6` 二元 gate × 弱 base signal"机制是否在 csi1000 携带独立 alpha；对照 `trend_quality_gated` (DEAD) 的 csi300→csi1000 翻号教训

---

## Hypothesis

Singha (2025) 在 S&P 500 上声称：把"value (`1/price` rank) + reversal (negated 10d return)"线性组合的弱 base signal，用 stock-specific drift regime gate（`Mean(I[ret>0], 63) > 0.6`）做二元开关相乘，OOS Sharpe 从 1.2 跃升到 13.2，53% 的收益归因于 gate × base 的"interaction effect"。在 csi1000 daily 上的本地化假设：

**核心假设（H1）**：UpFraction>0.6 这个 63d 累积上涨日比例阈值，作为 multiplicative mask 加到一个本身在 csi1000 上 weak / borderline 的弱信号上，能否把弱信号转化为 OOS-stable cross-section alpha？关键不是 base signal 本身（reversal 在 csi1000 已知有效；inverse-price 是已知 size proxy），关键是 **gate 本身是否在 csi1000 上独立携带 conditional information**。

**A 股本地化的关键修正**：
- `1/$close` 在 A 股是 size proxy（低价股 ≈ 小盘股，因为没有 split history），lessons.md 明确 `|corr|>0.3 to $market_cap` 红线必 reject。本地化用 `1/$pb_ratio` (F028 已 admit) 作 value 端
- csi1000 上 cumulative momentum 是 dead（return_momentum_acceleration / asymmetric_momentum 两条 dead direction），所以 UpFraction 自身（continuous 形式）大概率与已 dead 的 momentum 几何高度重叠 → 必须作为 control 候选先测，确认 gate 与 cumulative momentum 不是同一回事
- `trend_quality_gated` (DEAD batch_037) 把 paper QA Channel 3 的"momentum × clean trend gate"机制迁移到 csi1000，6/6 IC_OOS 全 reject 且符号翻转；该方向是 **gate-as-mechanism 在 csi1000 上的第一个独立证伪**。本方向的 base signal 是 reversal 而非 momentum（csi1000 反转本身有效），因此不构成同律证伪 —— 但是论文的 "gate alone is the alpha" 这一主张如果成立，应该在 ANY 弱 base signal 上都能复现；该律本身正是 trend_quality_gated 已经否定的

**核心假设（H2，falsification 设计）**：如果反转 gate（`Sub(1, REGIME)`）也产生同样的 OOS alpha 或者刚好反号，则 paper 的二元状态机制 transfer；如果 gated / anti-gated 形式都死，则 gate 是装饰，base signal 自身才是 alpha 来源（与 paper 矛盾）。这是 `trend_quality_gated` 当时**没有做** 的 ablation —— 它直接相信了 gate 机制。

**先验预期**：
- 概率 ~30% gate 携带独立信息（≥1 candidate admit），主要场景是 2020-2021 风格 regime + reversal base
- 概率 ~50% gate × reversal corr 到 F025/F044 > 0.7，CP05 redundancy 直接挂
- 概率 ~20% 6/6 全 reject + 符号翻转，方向直接 dead，作为 paper transfer 律的第二独立验证（继 trend_quality_gated 之后）

---

## Current Focus

首批 batch_080 设计 5-6 候选覆盖 paper 完整 ablation matrix：
- 1 个 paper 原配置（gated `1/$close` value）
- 1 个 paper 原配置（gated 10d reversal）
- 1 个 A 股本地化（gated `1/$pb_ratio`，避开 size proxy 红线）
- 1 个 control（pure UpFraction continuous，验证与 momentum 几何不重叠）
- 1 个 falsifier（anti-gated reversal，`Sub(1, REGIME)` × reversal）
- 可选 1 个 reserve pool 复活（gated borderline factor）

下一步若首批至少 1 admit → T001/T002 转 active，开 batch_081 探索 gate 窗口长度（44d / 63d / 80d）和阈值（0.5 / 0.6 / 0.7）的稳定性；若 6/6 reject + 符号翻转 → status `exploring → dead`，与 `trend_quality_gated` 并列升格"paper transfer + binary regime gate 在 csi1000 默认 dead"系统级 lesson。

---

## Threads

### T001: Gated value channel — paper exact 值通道在 csi1000 的可移植性 [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: `Mul(CsRank(Div(1, $close)), Gt(Mean(Gt(Sub($close, Ref($close,1)), 0), 63), 0.6))` 在 csi1000 上是否携带独立 OOS alpha，且能避开 `1/$close` size proxy 红线（`|corr| > 0.3` 对 `$market_cap`/`$circ_market_cap` 直接 reject）？若原配置触红线，A 股本地化版本（替换为 `1/$pb_ratio`）能否生还？
>
> **Evidence trail**:
> - (待 batch_080 注入)
>
> **Next probes**: batch_080 C001 paper 原配置 + C004 A 股本地化两个一同测，确认 gate 在 value 端 vs PB-rank 端表现一致性

### T002: Gated reversal channel — gate × reversal 是否独立于 F025/F044 [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: `Mul(Mul(Mean(Sub($close, Ref($close,1)), 10), -1), Gt(Mean(Gt(Sub($close, Ref($close,1)), 0), 63), 0.6))` 在 csi1000 上是否相对于已 admit 的 F025 vol_confirmed_reversal_5 / F044 price_reversal_60 携带独立信息（max_lib_corr ≤ 0.7）？gate 的 ~35% 稀疏度是否足以把 base reversal 信号 decorrelate？
>
> **Evidence trail**:
> - (待 batch_080 注入)
>
> **Next probes**: batch_080 C002 测 paper 原配置；若 corr 到 F025/F044 ≥ 0.7 但 OOS 信号本身 healthy，则改测 5d / 20d 不同 reversal 窗口配 63d gate 是否能拉开几何独立性

### T003: Gate-itself ablation — anti-gate falsification [◉ ACTIVE]

> [!note]+ Thread 当前
> **Question**: 把 gate 反转（`Sub(1, REGIME)` × base）后，OOS alpha 符号反转、消失、还是不变？如果 gated / anti-gated 都死 → gate 不是 alpha 源；如果反号 → paper 二元状态机制在 csi1000 transfer；如果都活 → gate 不携独立信息，base signal 自己就在工作。这是 `trend_quality_gated` (DEAD) 当时缺失的关键 ablation
>
> **Evidence trail**:
> - (待 batch_080 注入)
>
> **Next probes**: batch_080 C005 设计 anti-gated reversal 与 C002 配对，3 路结果（C002 / C005 / 单纯 reversal baseline）三角对比定 gate 是否独立信号

---

## Known Failures

| Candidate | Expression | Reject Reason |
|---|---|---|
| _(none yet — direction not yet executed)_ | | |

---

## Related

- 📖 [[../papers/arxiv_2511_12490v1]] — paper intake 种子（Singha 2025, NASA 单作者 arXiv preprint，Sharpe 13.2 强主张但 survivorship + 多层 portfolio overlay 警告）
- 🔴 [[trend_quality_gated]] `dead` — gate-as-mechanism 在 csi1000 第一次证伪（paper QA Channel 3 trend × clean gate 6/6 IC_OOS 反号）；本方向是 binary multiplicative gate 的第二次独立测试，base signal 切换到 reversal/value 而非 momentum
- 🔴 [[return_momentum_acceleration]] `dead` — UpFraction continuous 形式预期与之高 corr；C003 control 候选用于确认 gate 不是变形 momentum
- 🔴 [[asymmetric_momentum]] `dead` — sign-conditional aggregation 同族；UpFraction 本质是 sign>0 的 63d count，需警惕同族失败
- 🟡 [[value_liquidity_interaction]] `saturated` — value × 其他 composite 已探索；本方向 gate 是 mask 不是 interaction，几何不同
- 🟡 [[overnight_intraday_split]] `saturated` — 时段拆分 vs 状态 gate，概念邻近但机制不同
- 🟡 [[reserve_revival_paths]] `exploring` — Idea 3 (gate over borderline factor) 的潜在 base signal 来源，可能在 batch_081+ 引入
- 📖 [[../lessons#Structural Constraints]] — `1/$close` size proxy 红线（`|corr|>0.3` 对 `$market_cap` 直接 reject）；csi1000 rate-form 系统失败律（UpFraction 继承部分风险）；paper transfer default 律（F302）
- 📖 [[arxiv_2602_07085v2]] — 前一篇 paper intake；QA Channel 3 = trend_quality_gated dead 的来源。两篇 paper 共同提示：S&P 500 / CSI 300 上的 regime gating 类工艺有 csi1000 transfer 默认失败律

---

## Narrative Log

> [!quote]+ 2026-05-02 · paper intake
> **方向由 Singha (2025) "Discovery of a 13-Sharpe OOS Factor" 推断得出** · rounds = 0 / admits = 0
>
> - 核心机制：`EDGE = BASE × REGIME`，BASE = `0.7 * value + 0.3 * reversal`，REGIME = `I[Mean(I[ret>0], 63) > 0.6]`
> - paper 自报 OOS Sharpe 13.2，但 NASA 单作者 / arXiv preprint / S&P 500 现成份生存偏 / 多层 portfolio overlay (vol scaling + kill-switch) — 默认 dampening 预期 1-3x 现有 Grade A 因子，不是 13x
> - 关键洞察：`gate alone may be the alpha` — paper Table 8 的 53% interaction contribution 暗示 base signal 可被替换；若成立，方向价值在于 gate 作为 meta-operator 复活 reserve pool 中的 borderline factor
> - 警示：`trend_quality_gated` (DEAD batch_037) 是 csi1000 上 gate-as-mechanism 第一次证伪 (paper QA Channel 3，6/6 IC_OOS 反号)。本方向 base signal 切换到 reversal/value (csi1000 已知有效)，不构成同律证伪 — 但若 6/6 仍 reject + 符号翻转，则升格 "paper-driven binary regime gate 在 csi1000 默认 dead" 系统级 lesson
> - 首批设计：5 候选覆盖 paper 完整 ablation matrix（2 paper 原配置 + 1 A 股本地化 + 1 continuous control + 1 anti-gate falsifier），不复刻 paper portfolio simulation 部分
>
> **Operations**　新建 `status: exploring` · `priority: medium`（second-paper-intake；prior trend_quality_gated transfer 失败将 priority 从 high 下调到 medium）
