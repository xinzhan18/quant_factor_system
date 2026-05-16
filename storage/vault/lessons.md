---
version: 10
last_consolidated_at: 2026-05-16T00:00:00Z
source: Phase 5 consolidation round 91 — promoted P030 (alpha_surv > 1.0 单边形式 ≠ library 充分条件, 5 batch × 5 方向) + P004-deep (path-integral / N-day 累积形式结构性失败, path-memory β-shift, 3 方向 dead) + Paper Transferability 4 层独立失效律 (从 round 75 3 件套扩展) + P030-cov (Cov ≈ Mean(X*Y) DSL 等价律, b087 实证 corr=0.927). 反复升格保留: P008 完整三条件 / Cov ≈ Mean(X·Y) 等价定理 / Anchor cluster pre-check / Rank-Diff 七律 / vol_20d 吸收律 / Rank-order ≠ Tradable Alpha. 压缩 ~18%.
---

# Research Lessons

系统级硬事实。每次挖掘循环开始前必读。
由 Phase 5 CONSOLIDATION 周期性重写。**不要**在这里追加单 batch 教训 —— 那些写在 `directions/{direction}.md`。

固定四段：**Data Facts** / **Operator Registry** / **Path Selection** / **Structural Constraints**。其它段（Forbidden Patterns / Paper Transferability / Direction Lifecycle / Threshold Calibration / Metric Semantics / Language Policy / Promising Unexplored）按需附加。

## Data Facts

- **Data split (不可违反)**：Train `[2015-01-01, 2021-12-31]` / Validation `[2022-01-01, 2023-12-31]` / Holdout `[2024-01-01, 2024-12-31]`（仅 `research holdout-review` 可读）/ 2025+ 永不触碰。**2022-2023 是 regime ground-truth**——不是噪声，而是利率上行→价值回归独立 regime；fundamental quality / signed cross-product 在此段系统翻号是 alpha 真饱和核心证据
- **Primary universe = `all_tradable`**：CP01–CP06 在「全市场可交易股票日」上跑（`base_tradable ∧ load_universe_mask(primary)`）；csi300/csi500/csi1000 仅作 robustness label
- **csi300 是 alpha 死区**：23 因子 retrofit 仅 7 个跨过 floor；大盘股被机构 arbitrage 压平
- **`$vwap` 全零** —— precheck 禁用；**`$amount` 有数据**
- **A 股约束**：不做空头 alpha；多头侧产生信号
- **市值代理红线**：`|corr| > 0.3` 对 `$market_cap` / `$circ_market_cap` 直接 reject
- **A 股 ±10% 涨跌幅约束**：`$high / $low / Ref($close,1)` 三 reference point 同时被夹紧 → `(H-L)/C` / `|gap|/range` / `gap/Std(ret,20)` cross-section affine-like 共变 → 与 gap/VWAP 系列 (F003/F014) 80%+ cluster 是默认结局
- **Train→Validation regime 切换**：higher-moment LHS 在 raw fundamental / intraday signed / residual 字段上**系统性翻号**
- **Tradable mask + ST 过滤改写历史 mono**：persistence/mean/cumsum 系列 freeze 阶段必须看 ST-filtered probe IC（F003/F010/F011 旧版 mono=1.0 → 加 PIT ST + 停牌 mask 后跌到 0.40）
- **Qlib binary 数据契约**：格式 `[start_index:f32][data:f32×N]`，**PIT valuation / 全 TTM ratio / `$turnover_rate`** 与 OHLCV start_index 不一致；`Corr(safe, unsafe, N)` rolling shape mismatch 整批 compute 终止
  - **Corr-safe 字段集**：`{$close, $open, $high, $low, $volume, $amount, $num_trades}`（仅 7 字段双端可用）
  - **Corr-unsafe**：全 PIT valuation + 全 TTM ratio + `$turnover_rate`
  - 当前 fix 未到，**Phase 1 generator AST 层硬阻断 cross-field Corr/Cov**

## Operator Registry

- **白名单唯一**：DSL 算子/字段必须出现在 `src/research/phases/phase1_start.py:DSL_FIELD_WHITELIST`
- **可用字段** (22 基本面/微观, 2026-05-01 扩展)：
  - 价量: `$open $high $low $close $volume $amount`
  - 微观: `$turnover_rate $num_trades`
  - 估值 PIT: `$pe_ratio $pb_ratio $ps_ratio $pcf_ratio $market_cap $circ_market_cap`
  - 盈利 TTM: `$return_on_{equity,asset,invested_capital}_ttm $gross_profit_margin_ttm $operating_profit_margin_ttm`
  - 偿债/效率/成长/每股/估值 TTM: 见 `DSL_FIELD_WHITELIST` (15+ 字段)
- **自定义算子** (需 `C.kernels = 1`)：`TsRank, TsMax, TsMin, TsAutoCorr, TsDecay, TsMomentum, RealizedVol, CsRank, CsZscore, CsDemean, AmihudIlliq, HHI, SignedPower, Tanh, Exp, Sigmoid`
- **禁用算子**：`Neg`（用 `Mul($x,-1)`）；`SMA`（用 `EMA` 或 `Mean`）
- **横截面算子** 始终在 `D.instruments("all")` 上计算
- **Rank-preserving 单算子变体零增量律**：DSL `{Linear, SignedPower(p>0), Sigmoid, Tanh, Exp, Softmax, CsZscore, Scale}` 包装单已 admit 因子 → max_corr ≈ 1.000 必为 near_duplicate；Generator AST 硬阻断 `f(F_admitted)`
- **DSL Div/Mul 不是真 orthogonalization**：要么保序，要么仅 style exposure 搬家；真 orthogonalization 必走 Python OLS / Barra residual
- **P028 Cov ≈ Mean(X·Y) − Mean(X)·Mean(Y) DSL 等价定理**：DSL 无原生 `Cov(X, Y, N)`；`Mean(Mul(X, Y), N)` 是其代理。两者 cross-section ranking 在 X/Y 中心化弱时 ≥0.95 同构 → **同批不得同时出现** raw `Mul(X,Y)` 与 `Cov(X,Y)` 候选
- **P030-cov 衍生律 (round 91 升格)**：csi1000 daily 个股 return / overnight gap / intraday body 等序列 cross-section 期望接近 0 (zero-mean stationary), 让 `Cov(X,Y,N) ≈ E[XY] = Mean(X*Y, N)` (二阶项消失). 实测 b087 C005 `Cov(o,i,20)` 与 F023 `Mean(Mul(o,i),20)` cross-section corr=**0.927**. Phase 1 generator AST 自检: candidate 含 `Cov(return_A, return_B, N)` + 库内含 `Mean(A*B, M∈[N/2, 2N])` → 必然 near_dup, design-time reject

## Path Selection

- **默认 DSL** (R8)。Python 逃生口仅在: DSL 无法向量化的非平凡循环 / DSL 表达不了的横截面操作 / 对发表 Python 参考实现的显式复刻
- **Python 因子契约**：`compute(df) -> pd.Series`, MultiIndex=`(time, symbol)`; `REQUIRED_FIELDS: list[str]` + `VECTORIZED: bool = True`; 纯函数; 白名单 `numpy/pandas/scipy`, 禁 `subprocess/os/sys/eval/open`
- **REQUIRED_FIELDS ⊆ loader 默认列**：`data_bridge.load_market_data` 默认 = `$amount, $market_cap, $close, $volume, $open, $high, $low`，**不含** `$turnover_rate / $pe_ratio / $pb_ratio / $ps_ratio`；Phase 1 freeze static validate
- **Python 因子源代码**：`storage/python_factors/F{id}_*.py` 是运行时入口
- **TTM × TTM 直接 DSL Sub/Mul/Div 数据契约失败**：TTM per-share 字段报表期外 NaN 10–30%；csi1000 daily 跨字段 NaN intersection 40%+；DSL `Sub/Mul/Div` 不容错。**Generator pre-check**：顶层 `Sub/Mul/Div` 且两端 atom 都 ⊆ TTM 字段集 → DSL 不可行硬阻断
- **Python residual + rolling 在 csi1000 系统性 coverage ≈ 0.71**：cross-sectional Barra residual ~1% NaN + rolling min_periods≥10 + csi1000 上市日异质性 → 复合 coverage 0.685–0.725，与 0.80 hard_gate 结构性不兼容。修复仅 (a) Cs 算子代 rolling；(b) loader ffill；(c) direction-aware 阈值放宽 (仅 barra_residual_alpha workaround)
- **alpha_survival > 1.0 paradox guard**：`alpha_survival` 仅捕"对线性 Barra basis 剥离"，**不预测 OOS sign alive**。b071 6/6 候选 alpha_surv ∈ [0.93, 7.23] 全 PASS 但 train +α / val -α 全部翻号。**判据**: alpha_survival 不可独立作 admission gate, 必须配 (a) `ic_by_year` 2022/2023 不翻号 + (b) `incr_ic ≥ 0` 不为 library reducer
- **Linear OLS residualize 不破 csi1000 vol_20d 非线性吸收**：`pinv + einsum` 工艺正确，但残差 dominant_style 仍 vol_20d。仅在 numerator 自身有 OOS-stable alpha 时该路径生效
- **P008 完整三条件 (TsRank≥60d + ratio + microstructure-only/OHLCV-only)**：vol_20d-escape 真路径**三条件并立**：
  1. **TsRank window ≥ 60d** — 60d 时序 rank 把 cross-section level 替换为"个股自身分位"
  2. **ratio 字段** — dim-less ratio (`$amount/$num_trades` / `$amount/$volume` / `H/L` / `(H-L)/(C+O)`)
  3. **两端 microstructure-only / OHLCV-only** — cap-denominator (`$market_cap` / `Mean($amount,N)` / `Mean($turnover_rate,N)`) cross-section 与 vol_20d 共线
  
  **库内现状**：F024 (TsRank(num_trades/volume,60)) + F025 (TsRank(shadow_asymmetry,60))。**安全反例**：F002 (PB 自带 value Barra basis 抗衡)；F012 (Amihud 特例)
- **Reserve revival 仅 4 条生还路径**：51 flip-candidate retro audit, 5 minor 复活路径全部失败:
  - **P025 rank-form 仿射 no-op**：TsRank/CsRank 在 `a*x+b (a>0)` 下不变
  - **P026 reserve alpha decay**：chronologically aged reserve retest 信号消失
  - **P027 rhs_change 必须跨 family**：同 family 内换 RHS 不破共线性
  - **P028 rank-form zero-mean anchor**：`Sub(CsRank(X), const)` 与 `CsRank(X)` rank 完全等价
  - **P029 Library saturation 单调累积**：不存在"等阈值松了再复活"的免费午餐
  - **仅生还路径 4 条**：(a) **Python residualize** (cross-section OLS on blocking factor)；(b) **跨 family rhs_change**；(c) **structural transform** (Mean→Std/Skew 量纲层升级)；(d) **跨 direction 机制复现** (P008 escape 在新 direction 复测)

## Structural Constraints

- **禁看 holdout**：Phase 2/3 永远不能读 2024 数据；物理隔离 `storage/_holdout_private/`
- **向量化 (R5)**：禁 for 循环；禁 `groupby.transform` (隐式按日期 for)
- **Barra residual 基线**：`style_r²` + `alpha_survival` 是 CP04 核心。dominant_style=vol_20d 时优先看 alpha_survival
- **冗余红线 (CP05)**：`max_lib_corr > 0.70` 直接 reject
- **Python 因子必须进 library 对比**：`data_bridge.load_library_signals` 同时覆盖 DSL + Python 两源 (按 sha256 缓存)
- **Sample policy 版本**：`config.yaml.sample_policy_version` 变更重置 §7.MT validation_exposure 计数
- **Multi-universe schema**：`validation_metrics_by_universe` + `universe_robustness` + `recompute_provenance`
- **Library recompute self 检测必须空 library_signals**：批量重算手动 `inputs.library_signals = {}`
- **`revalidated_in_batch` ≠ `admitted_in_batch`**：report builder 读 `meta.get("revalidated_in_batch") or meta["admitted_in_batch"]`
- **DB `factor_values` 表已 DROP**：Phase 2 不读 DB

### vol_20d 结构性吸收律 (≥12-direction 顶级失败律)

csi1000 daily-bar cross-section 2nd-moment 空间被 Barra `vol_20d` 占据。任何 magnitude / ratio / power-mean / Std / Var / quantile / IQR 形态 rank monotone-equivalent 到 vol_20d，alpha_survival 典型 0.08–0.30。

**机理**：A 股 ±10% 涨跌幅 + 小盘散户主导，使 `|daily_return|` / `(H-L)/C` / `$amount` 的 std/CV / Quantile 差 / Skew/Kurt 高度同构。Robust estimator **不等于** Barra vol_20d orthogonality。`Mean($amount, N)` / `Mean($turnover_rate, N)` 作 denominator 本身嵌入 vol_20d；F002 (PB/Mean(amount,20)) admit 是特例（PB 自带 value Barra basis 抗衡）。

**判别规则**：`dominant_style=vol_20d` + `style_r² > 0.30` + `alpha_survival < 0.30` 三立 → 直接 reject。

**逃离路径 5 条**：(a) Python Barra residual orthogonalize（受 coverage<0.80 + Linear OLS 不破非线性双重限制）；(b) 非 daily-bar 数据；(c) sign 聚合 / rank-diff cross-family / 严格 mono_is≥0.6 higher-moment 单层；(d) overnight 段独立分解；(e) **P008 完整三条件**。

**P004-deep — path-integral / N-day 累积形式结构性失败 (round 91 升格)**: Barra cross-sectional residualization 是 **single-step 线性算子** — 对 single-day ε admit-able (F004 alpha_surv=1.41 反例); **任何 N-day path-integral / 累积 / EMA-差 / rank-diff / IVOL-gated 累积形式默认 reject**. 3 batch × 3 方向 13 候选实证: signed_money_flow_oscillator b088 PVT(20)/(60) alpha_surv=0.11/0.16; idiosyncratic_momentum_residual b089 60d/120d/250d cumulative residual alpha_surv 单调衰减 0.42→0.37→0.36; price_conditional_amplitude b090 6/6 rank-conditional aggregation 残差吞噬 63-75%. **机理**: path-integral `Σ(ε_t-i)` 让内层 β(t-i) 不是 t 时刻常数, **path-memory β-shift 让累积形式 vol_20d basis 重新涌现** — 比 "non-linear absorption" 更深一层. **实操律**: (a) stay at single-step (F004 模式); (b) 用 multi-day evaluation horizon 替代 multi-day LHS aggregation; (c) Phase 1 hard precheck: 顶层 `Sum(residual_X, N)` / `Mean(Cumulative_signed_flow, N)` / `Sum(signed_return × Vol, N)` (N>1) 自动 reject. **三方向已 dead**: signed_money_flow_oscillator / idiosyncratic_momentum_residual / price_conditional_amplitude.

### Geometric absorbing-factor 律 (admit-anchor cluster lock)

admit factor 在其几何家族内自动成为 absorbing prototype，同 family 续探 max_corr ≥0.55 @ 该 factor。5+ admit 跨 6+ direction 独立确认：
- **F001 amount_cv_20** → first-moment Mean / Sum / EMA 累积变体同构（连续 N 日累积/平滑 first moment 不脱原 anchor）
- **F024** (TsRank(num_trades/volume,60)) → b074 三轴 ablation 全 max_corr ≥0.91
- **F025** (TsRank(shadow_asymmetry,60)) → b077 三层 nested + cross-product 全 0.58–0.70
- **F018** (overnight sign-aggregation) → b078 C006 rhs_change 0.576→0.790
- **F021** (upper_shadow_disp_range_compress) → b081 C001 0.68

**Anchor cluster sufficient basis lock (强制 pre-check)**：family 内 admit ≥1 后, 新候选起手 mandatory 跑 anchor pre-check; max_corr ≥0.55 @ admit factor → 默认 reject 不消耗 CP3-CP6 预算. 续探必须 (a) cross-family; (b) Python residualize on prototype; (c) structural transform; (d) **高阶 composition (ratio-of-derived-quantity)** — F025 是 ratio of two derived shadow lengths, cross-section 分子分母同消 base scale + base volatility, vol_20d_exp=6.03

### Cross-product Mul wrapper 系统性塌缩律 (5+ 跨方向证伪)

`Mul(F_admit_atom_A, F_admit_atom_B)` 或 `Mul(CsRank(A_admit), CsRank(B_admit))` **从不产生独立新维度**，两失败模式：
1. **塌缩到强势一端**（b077 C004 max_corr=0.6972@F025）
2. **sign_flip catastrophic + alpha_surv collapse**（b074 C006 alpha_surv=0.068）

**与 Sub 不对称**：Sub 抵消共有 basis (rank-diff 6 admit), Mul 放大共有 basis。**安全例外**：(a) F025 高阶 composition (单 atom 内部 ratio)；(b) `Sub(CsRank(A), CsRank(B))` rank-diff 形式。

**Generator pre-block**：两端来自已 admit factor atom 的 Mul 默认 skip。

### Rank-Diff Geometry 七律 + factor-anchored cluster

`Sub(CsRank(LHS), CsRank(RHS))` 是 csi1000 日频 cross-section 的**通用设计范式** — 6 admit 跨 5 family 兑现 (F015–F020), 但 7 条硬约束：

1. **两端 scale-invariance**：LHS / RHS 必须都是 CV / ratio / correlation 等无量纲量
2. **raw field 独立**：两端不得共享 numerator 或 denominator raw field
3. **同字段跨窗口禁止**：`Sub(CsRank(X_20d), CsRank(X_5d))` rank 高度相关 cancellation
4. **Sub 方向对偶 dedup**：`Sub(A,B) = -Sub(B,A)` 数学完美反号
5. **同批 LHS 共享 anchor rule**：同批 LHS 共享主信号端最多 admit 1
6. **RHS 共振饱和 (动态)**：dead RHS — `overnight_5 / turnover_5 / amount_20 / body_ratio_20 / price_vol_20 / circ_mktcap_60 / H_L_60_geo`
7. **factor-anchored cluster (LHS+RHS 双形态)**：4 anchor — **F002** (value_liquidity ±0.40–0.47) / **F012** (microstructure 长窗 Amihud-numerator RHS ±0.69–0.73) / **F020** (gap anti-anchor -0.69) / **F022** (overnight close-position 0.82–0.93); 起手 mandatory 4-anchor pre-check

**rank-diff 双阈值**：`alpha_surv_min = 0.30` + `incr_ic ≥ 0.015` 当 `max_corr ∈ [0.30, 0.70]` borderline。

**Rank-diff salvage 限定**：rank-diff 不能救 saturated 方向。已证伪边界: value_liquidity_interaction (b052 6/6) / intraday_price_formation (b053 5 reject) / barra_residual_alpha (b054 6/6)。

### OHLC Family Defaults (algebraic mirror trap)

A 股 daily-bar OHLC 两个结构性共动约束：
- **10% 涨跌幅约束** → `H / L / prev_close` 同时夹紧 → 派生量与 F003/F014 cluster 79–96%
- **OHLC algebraic mirror**：`lower_shadow ≡ -upper_shadow` (corr=1.000@F006); `signed_range` 与 `upper_shadow` corr=0.544; `(O+H+L+C)/4 ≈ close`

**OHLC 派生 candidate 起手 3 步 algebraic 检查**：(a) 与已 admit OHLC factor 在 `H-L` / `prev_close` / `OHLC4` 维度 affine 等价 (max_corr ≥ 0.85 必 cluster); (b) 两字段反相关镜像; (c) multi-field arithmetic mean 退化形态。

**单日对称抵消默认律**：单日 intraday OHLC 价格比率类 `mono_sign_flip` 默认失效。**逃脱**：(a) 多日 smoothed/aggregated (5d sweet spot); (b) sign aggregation 配 underlying persistent drift; (c) higher-moment 与 Mean-base 库因子构成独立轴。

**In-batch denominator family 等价性自检 (P024)**：仅分母不同的候选数学等价为 in-batch near-duplicate。b077 C003/C006 IC daily corr=**0.9996**。**等价类**：(C+O) ≈ (H+L) ≈ midprice×2 ≈ OHLC4_mean×4 ≈ close；Mean(close,N) ≈ EMA(close,M)；Mean($amount,N)/Mean($turnover_rate,N) cap-denominator 类。

### Rank-order ≠ Tradable Alpha 判别律

跨 ≥6 方向独立确认: 候选若同时满足
- **(1)** `|ls_t| ≥ 2 + mono ≥ 0.7` (CP3 强)
- **(2)** `alpha_survival < 0.30` **或** `incremental_ic < 0` **或** `style_r² > 0.30` (CP4/CP5 弱)

→ 默认是 vol_20d / 反转簇 / library anchor 的 monotone derivative，**reject 而非 reserve**。

**Library-reducer 复合 hard-block (六要件)**：`mono_oos ≥ 0.85 + |ls_t_oos| ≥ 2.5 + incr_ic ≤ -0.005 + alpha_surv ≤ 0.30` → direct hard-block reject。

**P008 软判定区 reject vs reserve 边界**：alpha_surv > 0.30:
- **默认 reject**：`incr_ic < 0 + max_corr ∈ [0.40, 0.50] borderline + 设计层无独立新几何`
- **reserve 火种**：`incr_ic < 0 但 max_corr < 0.30 LOW + 设计层独立新几何 + style_r² 极清洁`

**Directional signed magnitude 优先级**：signed magnitude (sign × magnitude) 与 unsigned 在 cross-section 上是不同几何——unsigned 落入 vol_20d 簇；signed (F018 `Mean(Sign(overnight),N) × amount`) 是仅有 sign-aggregation admit 通道。前提是 underlying field 含 persistent drift（见 Paper Transferability）。

**P030 alpha_survival > 1.0 单边形式独立 ≠ library 充分条件 (round 91 升格)**: 跨 5 batch (b086-b090) × 5 方向 × 7+ candidates 独立复现同一悖论 — **Barra-residual IC ≥ raw IC (alpha_surv 1.05-1.59) + max_corr<0.30 LOW + sign_consistency=1.0 三立完美 form 独立, 但 incr_ic NEG (-0.005 ~ -0.023)**. 机理: alpha_surv 衡量 vs Barra 9-style basis 残差强度, **不衡量 vs admitted library 残差强度**. 库内 close-position cluster (F006-F008-F026) + multi_ma_reversion (F027) + amount_cv (F001) 都是 non-Barra 几何 — **Barra-clean 与 library-clean 是两个独立 gate**. 实操律: `alpha_surv > 1.0` 必须配 (a) `incr_ic ≥ +0.005` + (b) `max_corr < 0.40` + (c) `ls_t ≥ 1.5` 至少 2/3 才可 reserve, 单 alpha_surv 不足以 fire → 默认 reject. Phase 3 judge.md 跨候选反思段必须新增 "alpha_surv > 1.0 candidates 三项检查" 自检条目.

## Forbidden Patterns

generator 层 / Phase 1 freeze 应 pre-block 的设计反模式。

- **Rate / delta / ratio / sign-conditional / Cov 形式 default-skip**：跨 ≥6 方向独立证伪 — `fundamental_momentum` (b022) / `return_momentum_acceleration` (b029) / `asymmetric_momentum` (b028) / `liquidity_acceleration` (b023+b032) / `pv_covariance` (b039) / `return_distribution` Q90-Q10 (b016)。归簇 F001 / F009 / F012 三反转载体。**例外**：(a) rank-diff Sub 对偶；(b) `Div(Delta(X), X)` 仅 sanity check
- **TTM-quality / daily-aggregate-liquidity ratio default-skip** (b068)：`Div(TTM_quality, Mean($amount, N))` / `Div(TTM_quality, Mean($turnover_rate, N))` 默认被 vol_20d 吸收 (vol_20d_exp=23.4 / 31.1)。**逃离正路径**：(a) numerator ∈ Barra value basis 字段；(b) Python OLS residualize TTM quality on (size, vol_20d) 后再 ratio；(c) TTM × TTM 内部交互 (Python 包装)
- **Higher-moment LHS / signed fundamental cross-product 四类 atom regime sign-flip** (b052/b053/b054/b068)：
  1. **raw fundamental Std/Var**：`Std($pe_ratio,20)` / `Var($pb_ratio*$turnover_rate,60)`
  2. **raw intraday signed ratio higher-moment**：`Std((C-O)/close,20)`
  3. **residual higher-moment**：`Std(residual_ret,20)` / `Sum(residual_ret,5)`
  4. **signed fundamental cross-product**：`Mul($growth_TTM, Div(1, $value_PIT))` / GARP
  
  **触发**：(a) LHS 含 `Std/Var/Sum($X,N)` 且 `N≥20d`, X ∈ {raw fundamental, raw intraday signed ratio, residual_returns}；或 (b) 顶层 `Mul`/`Div` + 两端 signed fundamental signal。**安全反例**：F019 / F020 (scale-free ratio + N≤20d + 单层 moment)。**衍生**: 嵌套 smooth-then-std (b052 C006) ls_t_is=12.18 → ls_t_oos=-0.13 — hard_gate `is_oos_lst_collapse`

- **Cov / Corr 长窗口协动 family csi1000 daily 真饱和** (b075/b079/b039 三方向 dead)：3 路径独立证伪 — raw `Cov` microstructure × valuation (alpha_surv 0.06–0.30); TsRank-Corr 双重包裹 (60d ic_oos<0.008, 120d sign_flip); raw Cov return-side (撞 F001/F009/F012 簇)。**实操**：任何 Cov / Corr / TsRank-wrap-Corr N≥60d default-skip

- **Meta-pattern 跨方向机械迁移**：F013 log-compression 在 gap_acceptance admit; 同款 log 套到 value × liquidity (b038 6/6 全负) / momentum gate (b037 6/6 reversal) / Cov (b039 6/6) 全 reject。**结构相同 ≠ 语义相同**

- **Rank-preserving 单算子包装**：见 Operator Registry。Generator AST 预拦截 `f(F_admitted)`

**绝对不放宽的硬闸**：`hard_gate` 全局阈值；市值代理红线；holdout 保护。例外仅 barra_residual_alpha coverage→0.70。

**已升格 hard_gate**：
- **`is_oos_lst_collapse`**：`|ls_t_oos|/|ls_t_is| < 0.10 且 sign(is) ≠ sign(oos) 且 |ls_t_is| > 5.0` → reject 标 `compound_moment_collapse`
- **`library_reducer`**：见 Rank-order ≠ Tradable Alpha 段四要件
- **`corr_cov_field_safety`**：phase1 generator AST 检测 `Corr/Cov(A,B,N)`, A/B 不双方在 Corr-safe 字段集 → reject

## csi1000 daily fundamental + institutional flow 真饱和 (顶层 macro lesson)

**alpha 真饱和不是阈值过严** (b068-b072 + b075/b079 7 路径独立证伪)：连续跨 7 方向全 0-admit。**7 独立失败路径**：

1. **daily-aggregate liquidity ratio** (b068)：6/6 reject
2. **PIT valuation rank composite** (b069/b070)：仅当 RHS 含 1/PB 时 book basis 显化
3. **Python OLS residualize TTM quality** (b071)：alpha_surv ∈ [0.93, 7.23] 全 PASS 但 6/6 OOS sign_flip
4. **TTM aggregate signed signal** (b069)：1/peg / 1/pcf_total 全 sign_flip
5. **institutional flow microstructure** (b072)：raw → F012 anchor; TsRank 60d 几何独立但 forward reversal
6. **Cov microstructure × valuation 长窗** (b075)：alpha_surv 0.06–0.30
7. **TsRank-Corr 双重包裹长窗** (b079)：60d ic_oos<0.008, 120d sign_flip

**Forward horizon h>1d 评估路径全库零兑现**：60d Cov daily 1d primary horizon 信噪比天花板 ~0.006-0.007。

**结论**：TTM quality / TTM valuation / institutional flow / long-window Cov/Corr 在 **csi1000 daily-bar 频率上不存在 OOS-stable cross-section alpha**。**唯一未探路径**：minute/tick + 其它 universe (csi300/csi500)。

### Composition Selection (rank × rank Mul 需 book yield basis)

**rank × rank Mul 复合需两端 atom 几何独立 + 至少一端 book yield basis 显化 (b/p≥2)** (b069 C006 + b070 6/6)：
- **book_to_price (1/PB)** 是 csi1000 cross-section **唯一同时具备** (a) cross-section dispersion 强 + (b) value Barra basis 抗 vol_20d 显化能力的 atom
- **PE/PCF/PEG** 在 ep_ratio basis 上有 dispersion 但缺 b/p basis 抗 vol_20d
- **充分但不必要**：`b/p ≥ 2 → ls_t ≥ 2`; `b/p<1.0 → ls_t<1.1`

## Paper Transferability

**Paper transferability 4 层独立失效律 (round 91 升格 — 从原 3 件套扩展)**: paper monthly/weekly + 大盘 (csi300/csi500/SPX) → csi1000 daily 默认 4 层独立失效, **任一 1 条立则 paper 信号默认低优先级 / 进 round 1 前需 LLM 额外 risk-review**:

1. **方向反号**: paper momentum 在 csi1000 daily 上反向有效 mean-reversion (海通-37 IMom b089 6/6 reject + 广发金工-42 Chaikin-AD b086 C001 9/9 negative + b088 9/9 negative + price_conditional_amplitude b090 paper raw V_high-V_low ic_oos=-0.053 反号)
2. **frequency mismatch**: paper monthly Barra residualization 跨月累加, csi1000 daily cross-day path memory β-shift 让累积失效 (b089 C004 vol-normalized 120d paper strict alpha_surv=0.332 vs raw 0.373 反而恶化)
3. **universe weakness**: paper 自承大盘 IC 在中证 800 外 (csi1000) 衰减 2.4x (海通-37 沪深 300 IC=4.56% → 中证 800 外 1.67%)
4. **library overlap**: csi1000 admitted 27 因子非-Barra 几何 (F006-F008-F026 close-position cluster / F027 multi_ma_reversion / F001 amount_cv) 已 capture paper signal 同质 alpha — paper alpha_surv 即使 ≥1.0 也是 Barra-clean 但 library-redundant (b086 C001/C005 + b088 C001/C005 实证)

**实操律**: `/factor-paper` workflow 必须在 frontmatter 写 `transferability_risk: {layer1_reverse_sign, layer2_freq_mismatch, layer3_universe_weak, layer4_lib_overlap}` 4 项 yes/no. 任 1 yes 进 round 1 前需额外 risk-review。

**csi300 → csi1000 transfer 操作清单**:
- **8x+ 衰减是常态**：gap_acceptance T001 csi300 Rank IC 0.0744 → csi1000 三窗口同步 sign_flip; F013 IC_OOS=0.0094 (~8x 衰减)
- **复刻硬约束**：(a) csi1000 重测原始 raw signal 是否同号; (b) 若同号衰减 ≥ 5x 再考虑非线性压缩 (log); (c) 若翻号或单调性破坏, 方向直接 dead
- **Sign aggregation underlying drift dependency** (三次对照): sign-based aggregation 必须先验证 underlying field rolling mean 显著非零 — F018 admit (overnight institutional drift) vs b050 C006 reject (intraday body random walk) vs b035 reject (pure sign × sign)
- **paper-driven freeze 前 explicit 标注** `expected_decay_factor ≥ 5x for csi1000 transfer`

## Direction Lifecycle

方向状态机：`exploring → productive ↔ saturated → dead → archived`。

- **首批反向证伪 → 当批 dead (三要件)**：复用上批 admit 的 meta-pattern + 新底层信号包装 = hedge-bet 方向。**判别**：首批 (1) reject_rate ≥ 80% **且** (2) ≥2 候选独立命中 hard_gate **且** (3) 失败机制非"窗口/算子细节"而是"信号方向与 hypothesis 反向" → 方向**当批 dead**。例外：方向若已 admit ≥ 1 → 转 saturated
- **Saturated 双层证据律**：(a) 信号设计层 (≥2 路径 cluster / ≥3 candidate 几何不变量) + (b) 数据契约层 (Python residual coverage 实测 < 0.80 或 Python 工具链未实现)
- **`archived` 状态**：元教训已升格至 lessons.md + dead/saturated ≥30 天 + 无活跃 active thread。复活仅当 lessons.md 升格条目本身被推翻
- **批量 archive (round 75)**：return_distribution_signals / vol_shock_signals / quantile_shape_signals / trend_quality_gated / log_value_liquidity / pv_covariance / asymmetric_momentum / fundamental_momentum / return_momentum_acceleration / fundamental_quality_carry / cov_microstructure_valuation / cov_ratio_long_window / stochastic_position / tsrank_candlestick_ratio (saturated)
- **新增 dead (round 91)**: signed_money_flow_oscillator (b088 Chaikin/AD/PVT 4/4 子路径全证伪) / idiosyncratic_momentum_residual (b089 path-integral/vol-normalize/rank-diff/IVOL-gating 4/4 全证伪) / price_conditional_amplitude (b090 paper-original/DSL-soft/P008-stack/RHS-swap 4 路径全证伪). 三方向元教训已升格 P004-deep, 下次 consolidation 转 archived

## Metric Semantics

- **`ic.half_life_days`** — IC 衰减半衰期, 持仓 horizon 天数
- **`feasibility.signal_half_life`** — signal 自相关半衰期, 交易日
- **二者不可互换**

## Language Policy

- **叙事主体：中文**。Hypothesis / Current Focus / Narrative Log / 反思 / verdict 理由 全部中文
- **术语保留英文**：IC / ICIR / Sharpe / Barra / monotonicity / style_r² / alpha_survival / long_short / hard_gate / mt_bucket / admit / reserve / reject / exploring / productive / saturated / archived
- **YAML / frontmatter 值**：英文 snake_case
- **Markdown H2**：英文（`## Hypothesis` / `## Threads` / `## CP01`）
- **例外**：`INDEX.md` 上半段段落标题用中文

## Threshold Calibration

Thresholds 是**可证伪的经验值**。

### 触发条件

任一满足即审视当前阈值是否过严：
1. **连续零 admit**：同方向 ≥ 3 批次 0 admit 且每批有 reserve
2. **Reserve 积压**：累计 reserve / 累计 judged > 40% 且零 admit
3. **库规模停滞**：累计 batches ≥ 5 但 library size 未增
4. **悖论复现**：同一"反直觉指标组合"在 ≥ 2 候选独立出现
5. **rank-diff paradigm 系统性错杀**：rank-diff 候选因 structural vol_20d exposure 在 alpha_surv ∈ [0.30, 0.40] 区间被默认 0.40 刷掉

### 放宽的依据

- **Barra-clean ≠ library-clean**：错杀侦测必须**同时**满足 (a) max_corr<0.30 + (b) incr_ic>0.010 + (c) mono>0.8 + (d) sign_consistency=1.0
- **Portfolio-level orthogonalization**：单因子 Barra 脏 ≠ 不可用
- **"Static vs dynamic orthogonal" 悖论**：低 `style_r²` ⊥ Barra basis；低 `alpha_survival` IC L/S weights ∈ span(Barra)

### Direction-aware 阈值 (已生效)

```yaml
thresholds:
  alpha_surv_min:
    default: 0.40
    barra_residual_alpha: 1.00
    amount_volatility_signal: 0.25
    value_liquidity_interaction: 0.30
    rank_diff_geometry: 0.30
  hard_gates:
    min_coverage: 0.80
    min_coverage_by_direction:
      barra_residual_alpha: 0.70
    is_oos_lst_collapse:
      max_ratio_with_sign_flip: 0.10
      min_lst_is_abs: 5.0
    library_reducer_hard_block:
      enabled: true
      mono_oos_min_abs: 0.85
      ls_t_oos_min_abs: 2.5
      incr_ic_max: -0.005
      alpha_surv_max: 0.30
    corr_cov_field_safety:
      enforce: true
      safe_fields: [$close, $open, $high, $low, $volume, $amount, $num_trades]
  incremental_ic:
    min_global: 0.003
    min_when_corr_borderline: 0.015
    corr_borderline_lower: 0.30
    corr_borderline_upper: 0.70
```

**rank-diff trigger**：candidate LHS/RHS 都包含 `CsRank(...)` 且顶层 `Sub` → 走 `rank_diff_geometry` 档。

**incr_ic borderline 律**：max_corr ∈ [0.30, 0.70] 时, incr_ic ≥ 0.015 是 admission 必要条件。

### 绝对不做

- **不放宽 hard_gate** — 例外仅 barra_residual_alpha coverage→0.70
- **不放宽市值代理红线** `|corr($market_cap)| > 0.3`
- **不放宽 holdout 保护**
- **不机械地在"连续零 admit"就放宽** — 必须先诊断是否真"错杀"

### 历史校准记录

- **2026-04-19**：`alpha_surv_min` 0.60 → 0.40；rubric CP04 poor 0.60 → 0.30；追溯 admit F002
- **2026-04-25**：引入 3 条 direction-aware 阈值
- **2026-04-27**：rename rank_diff → rank_diff_geometry；新增 `is_oos_lst_collapse` + `library_reducer_hard_block`；引入 archived 状态 + 首批反向证伪 dead 律
- **2026-05-02 round 69**：3 lesson 升格 (TTM-quality default-skip / TTM × TTM DSL 失败 / signed fundamental cross-product)
- **2026-05-02 round 73**：5 lesson 升格 (alpha_surv + ic_by_year / Linear OLS 不破非线性 / TsRank≥60d ratio escape / csi1000 daily fundamental 真饱和 / Composition Selection)
- **2026-05-02 round 74**：新增 hard_gate `corr_cov_field_safety`；9 lesson 升格
- **2026-05-03 round 75**：7 lesson 升格 (Cov 等价定理 / P008 三条件 / P028 zero-mean anchor / F001 累积扩展 / Anchor cluster pre-check / Directional signed magnitude / Paper 3 件套)
- **2026-05-16 round 91**：无阈值数字调整. 4 lesson 升格: (a) **P030 alpha_surv > 1.0 单边形式独立 ≠ library 充分条件** (5 batch × 5 方向, alpha_surv 必须配 incr_ic / max_corr / ls_t 三项至少 2/3); (b) **P004-deep path-integral / N-day 累积形式结构性失败** (path-memory β-shift, 3 方向 dead); (c) **Paper Transferability 从 3 件套扩展为 4 层独立失效律** (新增 frequency mismatch + library overlap 层); (d) **P030-cov Cov ≈ Mean(X*Y) 等价律** (b087 实证 corr=0.927)

## Promising Unexplored

> Phase 1 新开方向时参考。

- **高阶 composition (ratio-of-derived-quantity)**：F025 shadow_asymmetry vol_20d_exp=6.03 frontier 顶级；可在 OHLC body / range / shadow / overnight / gap family 复现
- **TsRank ≥60d on microstructure-only ratio fields**：F024 escape 首例；cross-section dim-less ratio + microstructure-only 两端 + TsRank ≥60d 是新 frontier
- **Higher-moment LHS independence axis on scale-free OHLC ratios**：F019 + F020 跨 OHLC×gap 两 family 兑现
- **Sign × persistent drift × non-linear weighting**：F018 + F013 是仅有 sign-aggregation admit；分红 / 公告事件 / index inclusion 等 persistent drift underlying 未尝试
- **Cross-section 算子 (CsRank/CsZscore/CsDemean) 替代 rolling**：解决 Python residual+rolling coverage=0.71 死路
- **非 daily-bar 数据** (minute / tick)：vol_20d 吸收律根本逃离；当前数据基础设施未就绪 — 一旦支持, magnitude / quantile / power-mean dead 方向可能复活；同时是 csi1000 daily fundamental 真饱和的唯一脱钩路径
