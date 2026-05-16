---
paper_slug: haitong_45_qualityfactor_2019
source_pdf: raw/papers/Haitong-45-QualityFactor-2019.pdf
source_kind: generic_pdf
arxiv_id: null
status: reviewed
primary_frequency: daily
direction_tag: null
reviewed_at: 2026-05-02
---

# 海通证券 选股因子系列研究（四十五）—— 质量因子 (2019-02-21)

## Core Claim

海通 2019 把"质量因子"拆成 6 个 sub-attribute（盈利能力 / 增长 / 盈利稳定性 / 投资 / 股份发行 / 资本结构），逐项用 2011-2018 A 股月频/季频 cross-section 回归测溢价。结论：

- **盈利能力（ROE/营业盈利能力）**：显著为正（月均 0.23-0.34%, T=4.1-4.84）；当年一季报数据显著优于上年年报数据
- **增长（ROE 变化 / EPS 变化 / "预期外"标准化变化）**：显著为正（预期外指标最强，T 高达 8.67）
- **盈利稳定性（ROE/EPS 变化波动率）**：单因子无显著选股效果（与 Jason Hsu 海外结论一致）
- **投资因子（股东权益增长率 / 总资产增长率）**：全 A 上效果弱（T≈-2 边缘），但**大盘小盘截然相反**——大盘负相关（T=-3.20），小盘正相关（T=1.78）
- **股份发行 NS（剔除送转后的总股本对数变化）**：显著负（月均 -0.36%, T=-3.01），但季频衰减不显著
- **资本结构 dDebt/Asset（资产负债率 YoY 变化）**：显著正（月均 0.14%, T=4.86），且**条件于未来 ROE 高的股票集中**：高 ROE 子集 dDebt/Asset 多空收益差 0.95% / T=3.90，低 ROE 子集仅 0.06% 不显著

paper 的核心信号实质是 **monthly cross-section regression 上的"质量子因子分别测试"** —— 不是真正的 multi-signal QMJ composite，而是 6 个 sub-attribute 各自的单因子证据。换仓频率月度/季度，标的为全 A（剔 ST / 停牌 / 上市不足 1 年），universe ≈ 2300-2400 只。

## Aha Moment

**单 atom "dDebt/Asset YoY × ROE 子集条件" 的非线性 conditional gating 结构** —— 其余 5 个 sub-attribute 在我们系统里已被 6 个独立方向（fundamental_quality_carry / python_ttm_residual_quality / fundamental_momentum / pit_valuation_pure / cov_ratio_long_window / cov_microstructure_valuation）系统性证伪，但 paper 明确 highlight 的"capital structure CHANGE × profitability quintile" 这条 conditional rail 在我们方向库里**从未单独探索过**。

这件事对我们仍有启发的逻辑：dDebt/Asset 本身在全 A 上溢价 0.14% 弱（其单调性对全 A 不一定可见），但 paper Table 12 给出 monotone gradient（低/中/高 ROE 子集 0.06% / 0.50% / 0.95%）—— 这不是 raw rate-form alpha，是 **dDebt/Asset 在某个"信用/盈利能力相位"内才有方向性**。机理：高 ROE 公司加杠杆 = signal of high-conviction ROE projection，市场赏；低 ROE 公司加杠杆 = signal of distress，市场惩。这种 conditional sign 翻转是我们 csi1000 daily 上没测过的 atom 几何。

但 —— 见 Direction Recommendation 段 —— 即便这个 angle 是新空间，它仍是 rate-form + 跨 family interaction，落在 lessons.md L1 + L2 (Forbidden Patterns "rate/delta/ratio default-skip" + "Higher-moment LHS / signed fundamental cross-product 四类 atom regime sign-flip") 的两条死区律的交集，预期 csi1000 OOS 不存活的概率极高。

## Candidate Ideas

### Idea 1 — ROE TTM baseline atom (untouched profitability axis)

- **Paper mechanism**: ROE 月度 cross-section 回归溢价 0.23-0.34% (T=4.11-4.84)。paper 强调"当年一季报数据 > 上年年报数据"，但我们的 `$return_on_equity_ttm` 是滚动 TTM，没有 paper 的 PIT 时间分辨率
- **Target frequency**: daily
- **Current readiness**: dsl_ready
- **Required fields**: `$return_on_equity_ttm`
- **Why it may survive daily downsampling**: 论文是月频，我们用日频 cross-section rank（CsRank）做基线 atom 探索；ROE 跨字段独立性已知（与 OHLCV 几何独立）
- **Main distortion risk**: **已被 b068 C001 (ROE/Mean(amount,20)) + b071 C001 (Python residualize ROE) 共同证伪** —— b068 vol_20d_exp=23.4 + b071 alpha_surv=0.93 PASS 但 6/6 OOS sign_flip，机理是 csi1000 daily 上 TTM quality 类 alpha 在 2022-2023 全 regime sign-flip。**但 raw `CsRank($return_on_equity_ttm)` baseline atom（不带 daily liquidity denominator + 不做 OLS residualize）从未单独 freeze 过** —— 是真正的 baseline-first untouched 形式
- **Suggested direction tag**: 不新开方向（最多作为 fundamental_quality_carry archived 状态的 baseline 对照补丁，但 archived 方向不再分配预算）

### Idea 2 — Gross profit margin TTM baseline atom

- **Paper mechanism**: 营业盈利能力（OP/Asset 类） paper 也是 T=4.36 显著正
- **Target frequency**: daily
- **Current readiness**: dsl_ready
- **Required fields**: `$gross_profit_margin_ttm` 或 `$operating_profit_margin_ttm`
- **Why it may survive daily downsampling**: GPM 跨字段独立于 OHLCV；与 ROE 不同 numerator 类
- **Main distortion risk**: **b068 C005 (gross_margin/Mean(turnover,20)) vol_20d_exp=31.1 整库历史最高** + b071 C003 (Python residualize gross_margin) IS IC=0.0012 极弱（10x 弱于 ROE）。raw baseline 形式未单独测过，但弱信号可能性极高
- **Suggested direction tag**: 不新开

### Idea 3 — Earnings stability (Std of TTM growth) baseline

- **Paper mechanism**: paper 测 EPS / ROE 变化波动率 → cross-section 单因子无显著选股效果（T 全 < 1.5）。Jason Hsu 海外结论一致
- **Target frequency**: daily
- **Current readiness**: dsl_ready
- **Required fields**: `$net_profit_growth_ratio_ttm` （rolling Std on TTM growth, e.g. `Std($net_profit_growth_ratio_ttm, 60)`）
- **Why it may survive daily downsampling**: 时序 Std 是 standard 操作；TTM growth 有 11 年历史可滚 Std
- **Main distortion risk**: **paper 自己已说不显著**；同时落在 lessons.md L2 "Higher-moment LHS regime sign-flip 四类 atom" 第 1 类 (raw fundamental Std/Var) 的死区，预期 csi1000 上同样无效或翻号
- **Suggested direction tag**: blocked-by-paper-self-disproof

### Idea 4 — Accruals proxy via NetIncomeGrowth − OCFGrowth

- **Paper mechanism**: paper 提到"会计质量（Accounting Quality）"是 Jason Hsu 7 attributes 之一海外显著，但**paper 自己声明本文不测会计质量**（Page 6 "本文主要对除会计质量以外的 6 种质量因子属性"）。所以这是 paper 留白的点
- **Target frequency**: daily
- **Current readiness**: blocked_by_data （部分）
- **Required fields**: `$eps_ttm`, `$operating_cash_flow_per_share_ttm`, `$net_profit_growth_ratio_ttm`
- **Why it may survive daily downsampling**: Sloan accruals 在中国市场公开文献部分有效
- **Main distortion risk**: **b068 C003 已实证**: `Sub($eps_ttm, $operating_cash_flow_per_share_ttm)` DSL 直接做 → 全 NaN compute_error hard_gate fail (lessons.md "TTM × TTM 直接 DSL Sub/Mul/Div 数据契约失败")。复活需 Python ffill 包装；但**`$accruals_ttm` 不在白名单**，必须代理。代理 = `Sub($net_profit_growth_ratio_ttm, $operating_cash_flow_per_share_ttm × const)` 这种形式同样落在 TTM × TTM 数据契约失败死区，且引入"复合 cross-product"再触 lessons.md L2 第 4 类 atom (signed fundamental cross-product)
- **Suggested direction tag**: blocked_by_data + blocked_by_architecture (need Python ffill wrapper + need a true accruals field)

### Idea 5 — Investment factor (asset growth) cross-cap conditional

- **Paper mechanism**: 总资产增长率 / 股东权益增长率 在大盘小盘上方向相反（大盘 T=-3.20 / 小盘 T=+1.78）。全 A 净抵消故全市场上 weak
- **Target frequency**: daily
- **Current readiness**: blocked_by_architecture
- **Required fields**: `$net_asset_growth_ratio_ttm` + universe split by `$market_cap`
- **Why it may survive daily downsampling**: 经济机制清晰 (paper §5 股息贴现模型推导)
- **Main distortion risk**: 我们的 primary universe 是 `all_tradable`（约等于 A 股全市场，含大量小盘），跟 paper 全 A 一致 → **预期同样净抵消 weak signal**。要复刻 paper 结论必须 size-conditional split → 落在"market cap proxy 红线"上 (`|corr($market_cap)| > 0.3` reject)，且我们没有"按 size 子集分别评估 IC"的 evaluation machinery。Phase 2 默认 cross-section IC = 全 universe，不做 size sub-bucket
- **Suggested direction tag**: blocked_by_architecture（需要 size-bucket evaluation pipeline + 与 size 红线冲突）

### Idea 6 — Net stock issuance (NS factor)

- **Paper mechanism**: 月频总股本对数变化（剔送转）→ T=-3.01 显著负
- **Target frequency**: monthly (paper 自己说季频衰减不显著)
- **Current readiness**: blocked_by_data
- **Required fields**: 月度总股本数据 + 送股/转增事件标记 → **均不在当前白名单** (`ref_shares` 表只有 `$turnover_rate` / `$num_trades` 微观字段，没有 share count delta + 没有送转事件标记)
- **Why it may survive daily downsampling**: 不行 —— paper 自己证明季频已衰减，daily 频率下管理层 timing 信号噪声会更大
- **Main distortion risk**: 频率不匹配 + 数据缺
- **Suggested direction tag**: blocked_by_data（需要月度 total_shares 字段 + 送转事件标记数据接入）

### Idea 7 — dDebt/Asset YoY change × ROE conditional gating (paper 最强发现)

- **Paper mechanism**: 资产负债率 YoY 变化 cross-section 溢价 T=4.86 显著正，**且 monotone 强化于高 ROE 子集** (低/中/高 ROE 多空 0.06% / 0.50% / 0.95%)。paper 自己 highlight 这是"资本结构变化与未来盈利预期的 interaction signal"
- **Target frequency**: monthly (paper)；尝试 daily aggregate
- **Current readiness**: dsl_ready (DSL 表达 OK, 但 hits multiple forbidden patterns)
- **Required fields**: `$debt_to_asset_ratio_ttm`, `$return_on_equity_ttm`
- **Why it may survive daily downsampling**: paper conditional gating 的非线性 ROE-quintile 结构 csi1000 daily 完全没测过；与 b068/b071 测过的 raw quality LEVEL × liquidity / Python residualize 几何不同
- **Main distortion risk**: **同时落在 3 条死区律**：
  1. lessons.md "rate/delta/ratio default-skip" L1（dDebt/Asset 是 YoY rate of change form）
  2. lessons.md "Higher-moment LHS / signed fundamental cross-product 四类 atom" L2 第 4 类（`Mul($debt_to_asset_change, $return_on_equity_ttm)` = 两 signed fundamental signal 相乘）
  3. lessons.md macro lesson "csi1000 daily fundamental + institutional flow 真饱和" 路径 d（TTM aggregate signed signal regime drift）
- **Suggested direction tag**: 不新开（落在 3 条死区律交集）

## Data Requirements

**论文依赖**：
- 月度 / 季度财务数据 (PIT，按公告披露日)
- 月频 cross-section 回归 framework（不是 daily）
- Total shares outstanding（月度变化），含送股/转增事件标识
- 全 A universe（剔 ST、停牌、上市 < 1 年）
- ROE 计算可选"上年年报"或"当年一季报"两种 PIT 切换

**我们缺什么**：
- **PIT 季报字段**：我们只有 `*_ttm`（12-month rolling）字段，**无法**像 paper 那样比较"上年年报 vs 当年一季报"两种 ROE 计算
- **月度回归 framework**：我们 Phase 2 默认 daily cross-section IC，没有月频 cross-section 回归 framework；季频/月频聚合可在 Python 包装但属架构层补丁
- **Total shares 月度变化 + 送转事件**：完全无字段
- **size-bucket evaluation**：paper 投资因子需在大盘/中盘/小盘子集分别评估 IC，我们 Phase 2 是 single-universe IC

**DSL 算子对照**：
- `Std`/`Mean` over TTM fields → DSL 可表达，但落在 TTM × TTM 数据契约失败死区
- `Delta($debt_to_asset_ratio_ttm, 252)` (一年 YoY 变化) → DSL 可表达，落在 rate-form 死区
- `Mul($debt_to_asset_change, $return_on_equity_ttm)` → DSL 可表达，落在 signed cross-product 死区

## Mapping To Current System

**已被覆盖（不需要新开方向）**：

- **Idea 1 (ROE baseline)** + **Idea 2 (GPM baseline)** → fundamental_quality_carry (archived) / python_ttm_residual_quality (dead) 已在两条独立路径上 (DSL Div + Python Barra residualize) 共同证伪。**严格意义上"raw `CsRank($ROE_ttm)` baseline atom"未单独 freeze 过**，但前置 baseline-first 的 retest 在 archived 方向重启 archived → exploring 状态机不被允许（Direction Lifecycle "复活前置：lessons.md 升格条目本身被推翻"），且 lessons.md "csi1000 daily fundamental 真饱和"宏观 lesson 已 5 路径独立证伪
- **Idea 3 (Earnings stability)** → **paper 自己证明无显著效果** + 我们 lessons.md L2 死区律双重指向不存活
- **Idea 4 (Accruals)** → b068 C003 全 NaN 数据契约失败已实证；`$accruals_ttm` 不在白名单
- **Idea 5 (Investment cross-cap)** → blocked by size 红线 + size-bucket evaluation 架构缺失
- **Idea 6 (NS factor)** → blocked by data (无月度 total shares + 无送转事件标识)
- **Idea 7 (dDebt/Asset × ROE conditional)** → 落在 3 条死区律交集

**部分覆盖**：无 idea 落在"部分覆盖"区间。

**未覆盖（NEW angle）**：严格意义没有 idea 在 (a) 数据可表达 + (b) 不落入已升格 lessons.md 死区律 + (c) 与已 archived/dead 方向几何不同 三层同时为 true。

**最优落点**：**no new direction**。

**DSL 还是 Python**：N/A（无可行 idea）。

## Feasibility Assessment

### Idea 1 — ROE TTM baseline

- **Original dependency**: PIT ROE（季报 / 年报切换可选）+ 月频 cross-section 回归
- **Coverage in current system**: TTM 字段 `$return_on_equity_ttm` 有 11 年历史，但**无 PIT 季度切换**；无月频回归 framework
- **Can it be downgraded to daily?**: 是（CsRank 日频可做）
- **Implementation path**: dsl，但落在 archived 方向死区
- **Missing piece**: archived/dead 方向不再分配预算；raw baseline form 未单独 freeze 但 fundamental_quality_carry archived 状态前置条件 = lessons.md "vol_20d 吸收律 daily liquidity denominator 隐藏路径" 被推翻

### Idea 2 — GPM baseline

- **Original dependency**: 同 ROE
- **Coverage in current system**: b068 C005 / b071 C003 已实证 GPM 在 csi1000 daily 弱（IS IC=0.0012）
- **Can it be downgraded to daily?**: 是
- **Implementation path**: dsl，但 paper 信号 csi1000 上极弱
- **Missing piece**: 同 Idea 1 + 信号本身在 csi1000 上弱

### Idea 3 — Earnings stability

- **Original dependency**: 5 年 EPS / ROE 变化波动率
- **Coverage in current system**: TTM growth 有 11 年历史，可滚 60d Std；落 lessons.md L2 第 1 类死区
- **Can it be downgraded to daily?**: 是
- **Implementation path**: dsl 但预期 sign_flip
- **Missing piece**: paper 自证不显著 + lessons.md L2 死区律双重否

### Idea 4 — Accruals proxy

- **Original dependency**: net income − operating cash flow（标准化）
- **Coverage in current system**: b068 C003 数据契约失败实证；`$accruals_ttm` 缺
- **Can it be downgraded to daily?**: 否 (TTM × TTM Sub 全 NaN)
- **Implementation path**: blocked
- **Missing piece**: Python cross-section ffill 工具链 + accruals 字段接入

### Idea 5 — Investment × size conditional

- **Original dependency**: net asset growth + size-bucket split
- **Coverage in current system**: 字段有 `$net_asset_growth_ratio_ttm`；size split 缺
- **Can it be downgraded to daily?**: 是
- **Implementation path**: blocked
- **Missing piece**: size-bucket evaluation pipeline + 不能单独触市值代理红线

### Idea 6 — NS factor

- **Original dependency**: 月度 total shares + 送转事件标识
- **Coverage in current system**: 完全缺
- **Can it be downgraded to daily?**: 否（频率 mismatch + 数据缺）
- **Implementation path**: blocked
- **Missing piece**: total_shares 月度字段 + 送转事件 metadata

### Idea 7 — dDebt/Asset × ROE conditional gating

- **Original dependency**: 资产负债率 YoY 变化 + ROE 子集 quintile gating
- **Coverage in current system**: 字段都有（`$debt_to_asset_ratio_ttm` + `$return_on_equity_ttm`）；YoY Delta 可 DSL；conditional × 表达可用 Mul
- **Can it be downgraded to daily?**: 是
- **Implementation path**: dsl 但落 3 条死区律交集
- **Missing piece**: lessons.md L1+L2+macro lesson 三律之一被推翻；或 cross-section quintile-conditional 评估 framework 接入（DSL 不能表达 quintile gating，需 Python ffill + bucketize）

## What The Paper Is Hiding

1. **2011-2018 sample 2019 后 OOS 完全失活的 regime drift 没测**（最大假设）—— paper 截止 2018 数据 + 中国市场 2019-2024 经历 (a) 注册制改革 (b) 利率上行价值回归 (c) 小盘风格主导切换 (d) 中美脱钩贸易战 / 疫情冲击 → fundamental quality 系统在我们已知 2022-2023 csi1000 daily 上**全部 sign_flip** (b071 6/6 实证 + macro lesson "csi1000 daily fundamental 真饱和" 5 路径独立证伪)。paper 信号在 OOS 不存活的概率根据现有证据估算 > 90%

2. **行业中性化默认假设但未明写** —— paper Table 13 "多因子截面回归"含 Barra-style 风格控制（市值 / 非线性市值 / 估值 / 波动率 / 换手率 / 反转 / 流动性），但**没有显式行业中性化**。我们的 Phase 2 也没做行业中性化，但 paper 的 ROE 0.27% 月均溢价是在 Barra-style 控制后的"residual cross-section regression coefficient"，**不是 raw long-short return**。我们的 IC 评估更接近 raw（部分 Barra residual）—— 量级不可直接对比

3. **A 股会计数据可信度（含粉饰）** —— paper 默认 ROE / 资产负债率等会计数据 PIT 真实，但 A 股普遍存在 (a) 季报粉饰（净利润操纵）(b) 资产负债表披露质量参差（小盘尤甚）(c) 一季报/年报数据修正律（"业绩变脸"）。我们的 `_ttm` 字段是 rqdatac 同步，可能含一定 look-ahead bias（同步时间对齐 vs 实际披露日的差异）—— 这个数据契约风险 paper 完全没提

4. **paper 分析的是月频/季频 PnL，不是 daily IC** —— paper 的 T 值都是月度 cross-section 回归 coefficient 的 T，对应"月持仓周期 + 月底 rebalance"。我们 Phase 2 是 daily cross-section forward IC（持仓 1d / 5d / 20d），频率 mismatch 6-20x。daily 频率下 fundamental 信号衰减更快（公告事件 cluster 在 4/8/10 月底数日，daily IC 大部分日子是 zero noise + 少量 announcement-day spike）—— **量级 8x+ 衰减是常态**，参考我们 lessons.md "Paper Transferability" 段两次独立确认

5. **"投资因子大盘小盘相反"未在 size-neutral 因子上验证** —— paper Page 9-10 给的 size-bucket split 没控住其它 Barra style，可能是 size × value / size × vol 残余 interaction 而非 pure investment effect。我们的 size 红线设计就是为了避免这种 "size-conditional alpha = size factor 重计数" 的陷阱

**选出 3 最大的**：#1 (regime drift OOS 失活)、#4 (月频→日频 8x+ 衰减常态)、#3 (A 股会计数据 PIT 可信度)。

## Blocked Ideas For Future

- **Idea 4 Accruals via Python ffill wrapper** — Unblock 条件：(a) 接入真 `$accruals_ttm` 字段 (rqdatac 提供 `accruals` 财务字段); 或 (b) cross-section ffill Python 工具链就绪 + 单独验证 `Sub_with_ffill($eps_ttm, $ocf_per_share_ttm)` 在 csi1000 daily 上信号存在
- **Idea 5 Investment × size conditional** — Unblock 条件：(a) Phase 2 evaluation pipeline 增加 `metrics_by_size_bucket` schema; (b) 同时确保候选不触 size 红线 (size-bucket 内的 IC 计算 ≠ size proxy factor)
- **Idea 6 NS factor** — Unblock 条件：(a) 接入 monthly total_shares + 送转事件 metadata（需扩 ref_shares 表 schema）；(b) 月频 cross-section IC framework 就绪
- **Idea 7 dDebt/Asset × ROE conditional gating via Python quintile bucketization** — Unblock 条件：(a) Python factor 支持 cross-section quintile gating + bucket-conditional return 评估；(b) lessons.md "rate/delta default-skip" 或 "signed fundamental cross-product 死区" 至少其一被推翻；(c) cross-section ffill TTM 工具链就绪
- **整体方向 reopen** — Unblock 条件：(a) minute-bar 数据接入推翻 vol_20d 几何形态 + csi1000 daily fundamental 真饱和宏观 lesson；或 (b) cross-universe (csi300/csi500) 验证 quality 类信号在其它 universe 仍 alive 后跨 universe 转移到 csi1000

## Direction Recommendation

- **Decision**: `do_not_create_direction`
- **Selected idea**: 无
- **direction_tag**: 不申请
- **Initial threads**: 不申请
- **First candidate families**: 不申请
- **Minimum unblock condition**:
  1. lessons.md macro lesson "csi1000 daily fundamental + institutional flow 真饱和"被推翻（minute-bar / cross-universe 反例）；**或**
  2. lessons.md Forbidden Patterns "rate/delta/ratio default-skip" + "signed fundamental cross-product regime sign-flip 第 4 类 atom" 至少其一被推翻；**或**
  3. 接入新数据：(a) PIT 季度财务字段（不仅 TTM）以复现 paper "上年年报 vs 当年一季报"切换；(b) monthly total_shares + 送转事件 metadata 以复现 NS 因子；(c) `$accruals_ttm` 字段接入；**且**
  4. cross-section ffill Python 工具链 + size-bucket evaluation pipeline 至少其一就绪以支持 quintile-conditional gating

**理由 (单段总结)**：海通 45 论文的 6 个 quality sub-attribute 在我们系统已被 6 个独立方向 (`fundamental_quality_carry` archived / `python_ttm_residual_quality` dead / `fundamental_momentum` dead / `pit_valuation_pure` saturated / `cov_ratio_long_window` dead / `cov_microstructure_valuation` dead) 系统性证伪——这是 5 路径独立 5/5 0-admit 升格的 macro lesson 而非阈值过严的局部失败。paper 唯一从未被我们方向库专门探索过的 angle 是"dDebt/Asset YoY × ROE quintile conditional gating"（paper Table 12 强 monotone），但该 atom 同时落在三条已升格 Forbidden Patterns 死区律的交集（rate-form / signed fundamental cross-product / TTM aggregate regime drift），csi1000 daily OOS 不存活的概率 > 90%。paper 的另两个新角度（NS factor + size-conditional investment factor）blocked by data / blocked by architecture。开新 direction 等于跨过 5 条独立证据 + 3 条已 codify 死区律强行投预算，违反 baseline-first mandate 的反向（"已知饱和族不投预算"，参见 user MEMORY 中"5 个新 fundamental 方向 30 候选全死，attribution 丢失"教训）。**正确动作 = 把 paper 注释为 reviewed，等数据/架构 unblock 条件满足后重跑本 skill** —— 这正是 `/factor-paper` 动态复评 protocol 的设计意图。

---

## Related

- ⚪ [[../directions/fundamental_quality_carry]] `archived` — 直接对照：ROE/ROA/margin × liquidity ratio 6/6 reject 实证；本 paper Idea 1+2 落入此死区
- 🔴 [[../directions/python_ttm_residual_quality]] `dead` — 直接对照：Python OLS residualize TTM quality 6/6 OOS sign_flip 实证；本 paper Idea 1+2+7 落入此死区
- 🔴 [[../directions/fundamental_momentum]] `dead` — 直接对照：PE/PB/PS rate-form 4/4 reject；本 paper Idea 7 dDebt/Asset YoY rate-form 落入此死区
- 🟠 [[../directions/pit_valuation_pure]] `saturated` — 邻近：valuation rank composite 仅 PB book yield basis 显化；本 paper 不涉及 PB-anchored composite
- 🔴 [[../directions/cov_ratio_long_window]] `dead` — 邻近：TsRank-Corr long-window 救 fundamental 协动 family 也 dead；进一步确认 fundamental family 真饱和
- 📜 [[../lessons#csi1000 daily fundamental + institutional flow 真饱和]] — macro lesson 5 路径独立证伪
- 📜 [[../lessons#Forbidden Patterns]] — rate/delta/ratio + signed fundamental cross-product + TTM-quality / daily-aggregate-liquidity 三死区律
- 📜 [[../lessons#Paper Transferability]] — Paper CSI 300 大盘 → csi1000 小盘 transfer 默认失败 + 量级 8x+ 衰减常态
