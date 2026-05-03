---
version: 8
last_consolidated_at: 2026-05-03T00:00:00Z
source: Phase 5 consolidation round 75 — promoted from pattern_analyst/022-026 + library_gap/015-018 + calibration/009-011 + hypothesis_promoter/014-019. New升格: alpha_surv>1.0 + ic_by_year 翻号 paradox guard; Cov ≈ Mean(X*Y) DSL 等价定理; F001 first-moment 累积扩展律; P008 完整三条件 (TsRank≥60d + ratio + microstructure-only); paper transferability 三件套 (csi300→csi1000 衰减 / underlying drift / 同号校验); anchor cluster sufficient basis lock (admit-anchor pre-check 强制); P028 zero-mean rank-form anchor; directional signed magnitude 优先级; first-batch-dead 三要件 codify; rank-diff salvage 限定 (raw level 不得救 saturated); reserve revival pool 退潮; 2022-2023 regime 单独 split as ground-truth.
---

# Research Lessons

系统级硬事实。每次挖掘循环开始前必读。
由 Phase 5 CONSOLIDATION 周期性重写。**不要**在这里追加单 batch 的教训 —— 那些写在 `directions/{direction}.md`。

固定四段结构：**Data Facts** / **Operator Registry** / **Path Selection** / **Structural Constraints**。其它段（Forbidden Patterns / Paper Transferability / Direction Lifecycle / Threshold Calibration / Metric Semantics / Language Policy / Promising Unexplored）按需附加，不引入新四段外的"常律"段。

## Data Facts

- **Data split (不可违反)**：Train `[2015-01-01, 2021-12-31]` / Validation `[2022-01-01, 2023-12-31]` / Holdout `[2024-01-01, 2024-12-31]`（仅 `research holdout-review` 可读）/ 2025+ 永不触碰。**2022-2023 是 regime ground-truth**——不是噪声，而是利率上行→价值回归独立 regime；fundamental quality / signed cross-product 在此段系统翻号是 alpha 真饱和的核心证据
- **Primary universe = `all_tradable`**：CP01–CP06 在「全市场可交易股票日」上跑（`base_tradable ∧ load_universe_mask(primary)`）；csi300/csi500/csi1000 仅作 robustness label，不进 verdict
- **csi300 是 alpha 死区**：23 因子 retrofit 仅 7 个跨过 admission floor；大盘股被机构 arbitrage 压平 alpha 是常态
- **`$vwap` 全零**（数据源未填）—— precheck 禁用；**`$amount` 有数据**
- **A 股约束**：不做空头 alpha；因子必须从多头侧产生
- **市值代理红线**：`|corr| > 0.3` 对 `$market_cap` / `$circ_market_cap` 直接 reject（size 已占 Barra basis，放宽 = 双重计数）
- **A 股 ±10% 涨跌幅约束**：`$high / $low / Ref($close,1)` 三 reference point 同时被夹紧 → `(H-L)/C` / `|gap|/range` / `gap/Std(ret,20)` 等 cross-section affine-like 共变 → 与 gap/VWAP 系列 (F003/F014) 80%+ cluster 是默认结局
- **Train→Validation regime 切换**：2015-2021 (低利率成长) → 2022-2023 (利率上行价值回归)；higher-moment LHS 在 raw fundamental / intraday signed / residual 字段上**系统性翻号**
- **Tradable mask + ST 过滤改写历史 mono**：persistence/mean/cumsum 系列 freeze 阶段必须看 ST-filtered probe IC（F003/F010/F011 旧版无 ST mask mono=1.0，加 PIT ST + 停牌 mask 后跌到 0.40）
- **Qlib binary 数据契约**：格式 `[start_index:f32][data:f32×N]`，**PIT valuation / 全 TTM ratio / `$turnover_rate`** 与 OHLCV start_index 不一致（RiceQuant 同步起点不同）；`Corr(safe, unsafe, N)` rolling 操作 shape mismatch 整批 compute 终止
  - **Corr-safe 字段集**：`{$close, $open, $high, $low, $volume, $amount, $num_trades}`（仅 7 字段双端可用）
  - **Corr-unsafe 字段集**：全 PIT valuation + 全 TTM ratio + `$turnover_rate`
  - 修复路径：(a) data loader unify start_index；(b) Python 包装绕过 Qlib op；当前 fix 未到，**Phase 1 generator AST 层硬阻断 cross-field Corr/Cov**

## Operator Registry

- **白名单唯一**：DSL 算子/字段必须出现在 `src/research/phases/phase1_start.py:DSL_FIELD_WHITELIST`
- **可用字段**（22 基本面/微观字段，2026-05-01 扩展）：
  - 价量：`$open $high $low $close $volume $amount`
  - 微观：`$turnover_rate $num_trades`
  - 估值 PIT：`$pe_ratio $pb_ratio $ps_ratio $pcf_ratio $market_cap $circ_market_cap`
  - 盈利 TTM：`$return_on_{equity,asset,invested_capital}_ttm $gross_profit_margin_ttm $operating_profit_margin_ttm`
  - 偿债 TTM：`$debt_to_{asset,equity}_ratio_ttm $current_ratio_ttm`
  - 效率 TTM：`$total_asset_turnover_ttm $inventory_turnover_ttm $account_receivable_turnover_rate_ttm`
  - 成长 TTM：`$operating_revenue_growth_ratio_ttm $net_profit_growth_ratio_ttm $net_asset_growth_ratio_ttm`
  - 每股/收益率 TTM：`$eps_ttm $book_value_per_share_ttm $operating_cash_flow_per_share_ttm $dividend_yield_ttm`
  - 估值 TTM：`$pcf_ratio_total_ttm $peg_ratio_ttm`
  - 来源：`ref_financials` (TTM) / `ref_valuation` (PIT) / `ref_shares` (microstructure)
- **自定义算子**（需 `C.kernels = 1`）：`TsRank, TsMax, TsMin, TsAutoCorr, TsDecay, TsMomentum, RealizedVol, CsRank, CsZscore, CsDemean, AmihudIlliq, HHI, SignedPower, Tanh, Exp, Sigmoid`
- **禁用算子**：`Neg`（用 `Mul($x,-1)`）；`SMA`（用 `EMA` 或 `Mean`）
- **横截面算子** 始终在 `D.instruments("all")` 上计算
- **Rank-preserving 单算子变体零增量律**：DSL `{Linear, SignedPower(p>0), Sigmoid, Tanh, Exp, Softmax, CsZscore, Scale}` 包装单已 admit 因子 → cross-section rank 保留 → max_corr ≈ 1.000 必为 near_duplicate；Generator AST 硬阻断 `f(F_admitted)`
- **DSL Div/Mul 不是真 orthogonalization**：要么保序，要么仅 style exposure 搬家；真 orthogonalization 必走 Python OLS / Barra residual
- **Cov ≈ Mean(X·Y) − Mean(X)·Mean(Y) DSL 等价定理**（pattern_analyst/023 升格）：DSL 不存在原生 `Cov(X, Y, N)`；常态下 `Mean(Mul(X, Y), N)` 或显式 `Mean(X·Y,N) - Mean(X,N)·Mean(Y,N)` 是其代理。两者 cross-section ranking 在 X/Y 中心化弱时 ≥0.95 同构 → **同批不得同时出现** raw `Mul(X,Y)` 与 `Cov(X,Y)` 候选；F073/F074/F075 cov-form admit 已锁定该几何，后续只允许跨 family rhs_change

## Path Selection

- **默认 DSL**（R8）。Python 逃生口仅在：DSL 无法向量化的非平凡循环 / DSL 表达不了的横截面操作 / 对发表 Python 参考实现的显式复刻
- **Python 因子契约**：`compute(df: pd.DataFrame) -> pd.Series`，df MultiIndex=`(time, symbol)`；模块级 `REQUIRED_FIELDS: list[str]` + `VECTORIZED: bool = True`；纯函数；导入白名单 `numpy/pandas/scipy`，禁用 `subprocess/os/sys/eval/open`
- **REQUIRED_FIELDS ⊆ loader 默认列**：`data_bridge.load_market_data` 默认 = `$amount, $market_cap, $close, $volume, $open, $high, $low`，**不含** `$turnover_rate / $pe_ratio / $pb_ratio / $ps_ratio`；Phase 1 freeze 必须 static validate
- **Python 因子源代码走代码版本控制**：`storage/python_factors/F{id}_*.py` 是运行时入口（被 PR 跟踪），`vault/batches/.../python_candidates/` 副本仅作历史快照
- **TTM × TTM 直接 DSL Sub/Mul/Div 数据契约失败**：TTM per-share 字段报表期外 NaN ~10–30%；csi1000 daily 跨字段 NaN intersection ~40%+；DSL `Sub/Mul/Div` 不容错 → preprocessed factor empty hard_gate fail。修复路径：(a) Python cross-section ffill 后 Sub；(b) z-score 后 Sub；(c) 标准化 `(eps-ocf)/|eps+ocf|` + ffill。**Generator pre-check**：顶层 `Sub/Mul/Div` 且两端 atom 都 ⊆ TTM 字段集 → DSL 不可行硬阻断
- **Python residual + rolling 在 csi1000 系统性 coverage ≈ 0.71**：cross-sectional Barra residual ~1% NaN + rolling min_periods≥10 + csi1000 上市日异质性 → 三因子复合 coverage 0.685–0.725，与 0.80 hard_gate 结构性不兼容。修复：(a) 用 cross-sectional 算子代替 rolling（CsRank/CsZscore 不需 min_periods）；(b) loader 端 ffill / industry-mean fill；(c) direction-aware 阈值放宽到 0.70（仅 barra_residual_alpha workaround）
- **alpha_survival > 1.0 paradox guard**（calibration/009 + pattern_analyst/022 + hypothesis_promoter/017 升格）：`alpha_survival` 仅捕"对线性 Barra basis 的剥离"，**不预测 OOS sign alive**。b071 Python OLS-residualized TTM quality 6/6 候选 alpha_surv ∈ [0.93, 7.23] 全 PASS 但 train +α / val -α 全部翻号；b081 C006 alpha_surv≈1.0 + incr_ic=-0.035 reject。**判据 composition**：alpha_survival 不可独立作 admission gate，必须配 (a) `ic_by_year` 2022/2023 不翻号；(b) `incr_ic ≥ 0` 不为 library reducer；alpha_surv >> 1.0 但任一条件失败 → 默认 reject
- **Linear OLS residualize 不破 csi1000 vol_20d 非线性吸收**（b071 5/6 实证）：`pinv + einsum` 工艺正确（alpha_survival ≥ 0.93），但残差 dominant_style 仍 vol_20d，vol_20d_exp ∈ [11.6, 22.9]。机理：OLS 只 strip 线性 βvol_20d，残差仍载 vol_20d 非线性载荷。**vol_20d 逃离正路径 (a)** 限定语义：仅在 numerator 自身有 OOS-stable alpha 时该路径生效。不试 Polynomial/Kernel OLS（参数过多过拟合）
- **P008 完整三条件 (TsRank≥60d + ratio + microstructure-only/OHLCV-only)**（pattern_analyst/025 + hypothesis_promoter/019 升格）：vol_20d-escape 真路径**必须三条件并立**：
  1. **TsRank window ≥ 60d** —— 60d 时序 rank 把 cross-section level 替换为"个股自身分位"，绕过 cross-section vol_20d basis ranking 重叠（同字段 raw rank vol_20d_exp=30.9 → TsRank60=10.87 降 65%）
  2. **ratio 字段** —— 必须是 dim-less ratio（`$amount/$num_trades` / `$amount/$volume` / `H/L` / `(H-L)/(C+O)`），单 atom ratio 不破 vol_20d
  3. **两端 microstructure-only / OHLCV-only** —— cap-denominator (`$market_cap` / `$circ_market_cap` / `Mean($amount,N)` / `Mean($turnover_rate,N)`) cross-section 与 vol_20d 共线，把 numerator 拉进 size×vol_20d 联合 basis（b073 C005 vol_20d_exp=17.4 / b074 C004=19.1 / b068 C001=23.4）
  
  **库内现状**：51 admit 中 P008 兑现 = F024 (TsRank(num_trades/volume,60)) + F025 (TsRank(shadow_asymmetry,60))。**安全反例**：F002 (PB/Mean(amount,20)) PB 自带 value Barra basis 抗衡；F012 (Amihud) microstructure 端特例。**衍生律 (raw $num_trades 不构成新几何)**：cross-section raw level → F012 size 共线性已覆盖 (b072 C002 max_corr=0.75@F012)；复活路径仅 (a) Python OLS size-residualize on log_circ_cap；(b) 时序 form (TsRank ≥ 60d)；(c) cross-sectional rank-diff 配独立 RHS basis
- **Reserve revival 仅生还路径**（b078 6/6 reject + calibration/010 升格）：51 flip-candidate retro audit——5 minor 复活路径全部失败：
  - **P025 rank-form 仿射 no-op**：TsRank/CsRank 在 affine `a*x+b (a>0)` 下不变；减常数/减 rolling mean 是数学 no-op，Phase 1 reject
  - **P026 reserve alpha decay**：chronologically aged reserve（≥1 year / ≥20 batches）retest 时信号可消失（b053 → b078 ic_oos +0.0025 mono FLIP）
  - **P027 rhs_change 必须跨 family**：同 microstructure liquidity family 内换 RHS 不破共线性
  - **P028 rank-form zero-mean anchor (library_gap/016 升格)**：rank-form atom (TsRank/CsRank) 的 cross-section mean 恒等于常数，与 zero-mean baseline 在 Sub 下 anchor —— `Sub(CsRank(X), const)` 与 `CsRank(X)` rank 完全等价，generator 必须 dedup 同源 rank atom 减常数变体
  - **P029 Library saturation 单调累积**：reserve 推迟复活无收益；不存在"等阈值变松了再复活"的免费午餐
  - **仅生还路径 4 条**：(a) **Python residualize**（cross-section OLS residual against blocking factor，DSL 不可表达）；(b) **跨 family rhs_change**（microstructure → fundamental basis 或 temporal basis）；(c) **structural transform**（Mean→Std/Skew 量纲层升级）；(d) **跨 direction 机制复现**（P008 escape 在新 direction 复测，不是对原候选 revival）

## Structural Constraints

- **禁看 holdout**：Phase 2/3 代码永远不能读 2024 年数据；holdout 物理隔离在 `storage/_holdout_private/`
- **向量化（R5）**：禁止行/日期/标的 `for` 循环；禁用 `groupby.transform`（隐式按日期 for）
- **Barra residual 基线**：alpha 在剥离 Barra 风格后度量；`style_r²` + `alpha_survival` 是 CP04 核心。dominant_style=vol_20d 时优先看 alpha_survival
- **冗余红线（CP05）**：`max_lib_corr > 0.70` 直接 reject
- **Python 因子必须进 library 对比**：`data_bridge.load_library_signals` 同时覆盖 DSL + Python 两源（按 `sha256(源码)` 缓存）
- **Sample policy 版本**：`config.yaml.sample_policy_version`（v3→v4）会重置 §7.MT 多重检验预算的 `validation_exposure` 计数
- **Multi-universe schema**：`validation_metrics_by_universe` 写入三 universe + `universe_robustness` summary + `recompute_provenance`
- **Library recompute self 检测必须空 library_signals**：批量重算整库时手动 `inputs.library_signals = {}`
- **`revalidated_in_batch` ≠ `admitted_in_batch`**：report builder 读 `meta.get("revalidated_in_batch") or meta["admitted_in_batch"]`
- **DB `factor_values` 表已 DROP**：Phase 2 不读 DB（用 sha256-keyed parquet cache + 即算即用）

### vol_20d 结构性吸收律（≥12-direction 顶级失败律）

csi1000 daily-bar cross-section 几何被 Barra `vol_20d` 占据 2nd-moment 空间。任何 magnitude / ratio / power-mean / Std / Var / quantile / IQR 形态 cross-section rank 都 monotone-equivalent 到 vol_20d，alpha_survival 典型 0.08–0.30。

**机理**：A 股 ±10% 涨跌幅 + 小盘散户主导，使 `|daily_return|` / `(H-L)/C` / `$amount` 的 std/CV / Quantile 差 / Skew/Kurt 在 cross-section 上高度同构。Robust estimator (Quantile/Median) 的 outlier-robust 性 **不等于** Barra vol_20d orthogonality。**Daily-aggregate liquidity denominator 隐藏路径**：`Mean($amount, N)` / `Mean($turnover_rate, N)` 作 denominator 时本身 cross-section 嵌入 vol_20d；F002 (PB/Mean(amount,20)) admit 是特例（PB 自带 value Barra basis 抗衡）。

**判别规则（reject）**：`dominant_style=vol_20d` + `style_r² > 0.30` + `alpha_survival < 0.30` 三者同立 → 直接 reject。

**逃离路径仅五条**：(a) Python Barra residual orthogonalize（受 coverage<0.80 + Linear OLS 不破非线性吸收双重限制）；(b) 非 daily-bar 数据（minute/tick）；(c) 非 magnitude 几何 —— sign 聚合 / rank-diff cross-family / 严格 mono_is≥0.6 + scale-free RHS 的 higher-moment 单层；(d) overnight 段独立分解；(e) **P008 完整三条件**（见 Path Selection）。

**证据链**：≥12 方向独立确认 —— return_distribution_signals / vol_shock_signals / amount_volatility_signal / stochastic_position / range_structure / quantile_shape_signals / intraday_price_formation / turnover_structural_signal / vwap_proxy_signals / fundamental_quality_carry / python_ttm_residual_quality / institutional_flow_proxy / cov_microstructure_valuation / cov_ratio_long_window。

### Geometric absorbing-factor 律（admit-anchor cluster lock）

一个 admit factor 在其几何家族内自动成为 absorbing prototype，同 family 后续 frontier 续探 max_corr ≥0.55 @ 该 factor。**5+ admit factor 跨 6+ direction 独立确认**：
- **F001 amount_cv_20** → first-moment Mean / Sum / EMA 累积变体在同字段族内 cross-section rank 同构（pattern_analyst/024 升格 — F001 first-moment 累积扩展律：连续 N 日累积/平滑 first moment 不脱离原 anchor）
- **F024** (TsRank(num_trades/volume,60), b073 admit) → b074 三轴 ablation 全 max_corr ≥0.91@F024
- **F025** (TsRank(shadow_asymmetry,60), b076 admit) → b077 三层 nested Div/Mul + cross-product Mul 全 max_corr 0.58–0.70@F025
- **F018** (overnight sign-aggregation) → b078 C006 rhs_change 0.576→0.790@F018
- **F021** (upper_shadow_disp_range_compress) → b081 C001 hl_norm_sym 60d Mean max_corr=0.68@F021

**机理**：admit 因子在 cross-section 几何上"占领" family prototype，后续同 atom × 不同 window / nested composition / cross-product / 替换 form / 同字段跨窗 cross-section ranking 仍 monotone-equivalent 到 prototype。

**Anchor cluster sufficient basis lock (admit-anchor pre-check 强制, library_gap/015 + hypothesis_promoter/016 升格)**：family 内 admit ≥1 后，新候选起手 mandatory 跑 anchor pre-check（IC daily corr / cross-section rank corr against admit anchor）；max_corr ≥0.55 @ admit factor → 默认 reject 不消耗 CP3-CP6 计算预算。续探必须 (a) cross-family（atom × directionally orthogonal RHS）；(b) Python residualize on prototype；(c) structural transform (Mean→Std/Skew 量纲层升级)；(d) 高阶 composition (ratio-of-derived-quantity)。

**逃离路径**：**高阶 composition (ratio-of-derived-quantity)** —— F025 是 ratio of two derived shadow lengths（不是 single-atom ratio），cross-section 上分子分母同消 base scale + base volatility，与 single-atom Mean shadow 几何独立 (max_corr 0.29 vs 0.45–0.47)，vol_20d_exp=6.03。与 P008 配对：高阶 composition 是 dim-less ratio frontier 真红利第二阶。

### Cross-product Mul wrapper 系统性塌缩律（5+ 跨方向证伪）

形态：`Mul(F_admit_atom_A, F_admit_atom_B)` 或 `Mul(CsRank(A_admit), CsRank(B_admit))` **从不产生独立新维度**，仅两失败模式：
1. **塌缩到强势一端**（b077 C004 max_corr=0.6972@F025，F024×F025 = F025 复制）
2. **sign_flip catastrophic + alpha_surv collapse**（b074 C006 alpha_surv=0.068 + incr_ic=-0.023；b080 C001 decay=-5.16）

机理：Mul 改变 cross-section moment structure → Barra style basis 重新捕捉；sign 由联合分布 quartile 决定 → regime drift 触发翻号。**与 Sub 不对称**：Sub 抵消共有 basis（rank-diff 6 admit），Mul 放大共有 basis。

**安全例外**：(a) F025 高阶 composition (单 atom 内部 ratio-of-derived-quantity)；(b) `Sub(CsRank(A), CsRank(B))` rank-diff 形式。

**Generator pre-block**：两端来自已 admit factor atom 的 Mul 形式默认 skip；需 cross-product 时改 Sub 或改 directionally orthogonal atoms（fundamental × 价量）。

### Rank-Diff Geometry 七律 + factor-anchored cluster

`Sub(CsRank(LHS), CsRank(RHS))` 是 csi1000 日频 cross-section 的**通用设计范式** —— 6 admit 跨 5 family 兑现（F015–F020），但 7 条硬约束：

1. **两端 scale-invariance**：LHS / RHS 必须都是 CV / ratio / correlation 等无量纲量
2. **raw field 独立**：两端不得共享 numerator 或 denominator raw field
3. **同字段跨窗口禁止**：`Sub(CsRank(X_20d), CsRank(X_5d))` rank 高度相关 cancellation
4. **Sub 方向对偶 dedup**：`Sub(A,B) = -Sub(B,A)` 数学完美反号
5. **同批 LHS 共享 anchor rule**：同批 LHS 共享主信号端最多 admit 1
6. **RHS 共振饱和（动态）**：dead RHS endpoints — `overnight_5 / turnover_5 / amount_20 / body_ratio_20 / price_vol_20 / circ_mktcap_60 / H_L_60_geo`
7. **factor-anchored cluster (LHS+RHS 双形态)**：4 anchor — **F002**（value_liquidity ±0.40–0.47 cluster）/ **F012**（microstructure 长窗 Amihud-numerator RHS ±0.69–0.73）/ **F020**（gap anti-anchor -0.69）/ **F022**（overnight close-position 0.82–0.93）；起手 mandatory 4-anchor pre-check

**rank-diff 双阈值**：`alpha_surv_min = 0.30`（CsRank ordinal 映射损失 magnitude）+ `incr_ic ≥ 0.015` 当 `max_corr ∈ [0.30, 0.70]` borderline。

**逃 cluster 启发**：higher-moment LHS independence axis（Std vs Mean of same atom）跨 OHLC (F019) + gap (F020) 复现；**单层** higher-moment 是 alpha 源头，**嵌套** compound moment 是 IS over-fit 源头。

**Rank-diff salvage 限定 (hypothesis_promoter/018 升格)**：rank-diff 不能救 saturated 方向。**已证伪边界**：value_liquidity_interaction (b052 6/6) / intraday_price_formation (b053 5 reject) / barra_residual_alpha (b054 6/6)。raw level 形式不得作为已 saturated direction 的 rank-diff salvage RHS。

### OHLC Family Defaults（algebraic mirror trap）

A 股 daily-bar OHLC 两个**结构性共动约束**：
- **10% 涨跌幅约束** → `H / L / prev_close` 同时夹紧 → `(VWAP-L)/(H-L)` / `gap/Std(ret,20)` 派生量与 F003/F014 cluster 79–96%
- **OHLC algebraic mirror**：`lower_shadow ≡ -upper_shadow`（corr=1.000@F006）；`signed_range` 与 `upper_shadow` corr=0.544；`(O+H+L+C)/4 ≈ close` → `(close - OHLC4_mean)/range ≈ 0 + noise`

**OHLC 派生 candidate 起手 3 步 algebraic 检查**：(a) 是否与已 admit OHLC factor 在 `H-L` / `prev_close` / `OHLC4` 维度 affine 等价（max_corr ≥ 0.85 必为 cluster）；(b) 是否两字段反相关镜像；(c) 是否 multi-field arithmetic mean 退化形态。

**单日对称抵消默认律**：单日 intraday OHLC 价格比率类 `mono_sign_flip` 是默认失效。**逃脱**：(a) 多日 smoothed/aggregated（5d sweet spot；upper-shadow [3d,7d] 稳）；(b) sign aggregation 配 underlying field persistent drift；(c) higher-moment 与 Mean-base 库因子构成独立轴。

**In-batch denominator family 等价性自检（P024）**：仅分母不同的候选在常态下数学等价是 in-batch near-duplicate。b077 C003 `TsRank((H-L)/(C+O),60)` 与 C006 `TsRank((H-L)/midprice,60)` IC daily corr=**0.9996**。**Phase 1 自检**：同批 candidate 顶层 atom 仅分母不同 → 必计算两候选 IC daily corr，≥0.90 reject 一保留另一。**等价类**：(C+O) ≈ (H+L) ≈ midprice×2 ≈ OHLC4_mean×4 ≈ close；Mean(close,N) ≈ EMA(close,M)；Mean($amount,N)/Mean($turnover_rate,N) cap-denominator 类。

### Rank-order ≠ Tradable Alpha 判别律

跨 ≥6 方向独立确认：候选若同时满足
- **(1)** `|ls_t| ≥ 2 + mono ≥ 0.7`（CP3 强）
- **(2)** `alpha_survival < 0.30` **或** `incremental_ic < 0` **或** `style_r² > 0.30` 中任一（CP4/CP5 弱）

→ 默认是 vol_20d / 反转簇 / library anchor 的 monotone derivative，**reject 而非 reserve**——除非含可证明独立的新几何。

**Library-reducer 复合 hard-block (六要件)**：`mono_oos ≥ 0.85 + |ls_t_oos| ≥ 2.5 + incr_ic ≤ -0.005 + alpha_surv ≤ 0.30` → direct hard-block reject 标 `library_reducer`，不进 reserve。

**P008 软判定区 reject vs reserve 边界**：alpha_surv > 0.30 不触发 P006 进入软判定：
- **默认 reject**：`incr_ic < 0 + max_corr ∈ [0.40, 0.50] borderline + 设计层无独立新几何`（b072 C005）
- **reserve 火种**：`incr_ic < 0 但 max_corr < 0.30 LOW + 设计层含独立新几何 + style_r² 极清洁`（b072 C006）

**Directional signed magnitude 优先级 (library_gap/017 升格)**：signed magnitude (sign × magnitude) 与 unsigned magnitude 在 csi1000 cross-section 上是不同几何——unsigned 落入 vol_20d 吸收簇；signed 形式 (F018 `Mean(Sign(overnight),N) × amount`) 是仅有的 sign-aggregation admit 通道。设计候选时优先尝试 directional signed 形式 over unsigned magnitude，前提是 underlying field 含 persistent drift（见 Paper Transferability）。

## Forbidden Patterns

generator 层 / Phase 1 freeze 应 pre-block 的设计反模式。

- **Rate / delta / ratio / sign-conditional / Cov 形式 default-skip**：跨 ≥6 方向独立证伪 — `fundamental_momentum` (b022) / `return_momentum_acceleration` (b029) / `asymmetric_momentum` (b028) / `liquidity_acceleration` (b023+b032) / `pv_covariance` (b039) / `return_distribution` Q90-Q10 (b016)。归簇 F001 amount_cv / F009 overnight_spread / F012 amihud 三反转载体。**例外**：(a) rank-diff Sub 对偶；(b) `Div(Delta(X), X)` 仅 sanity check
- **TTM-quality / daily-aggregate-liquidity ratio default-skip**（b068 实证）：`Div(TTM_quality, Mean($amount, N))` / `Div(TTM_quality, Mean($turnover_rate, N))` 默认被 vol_20d 吸收（b068 C001 vol_20d_exp=23.4 / C005=31.1 整库历史最高）。**Generator pre-check**：candidate 顶层 `Div`/`Mul` + numerator ∈ TTM quality + denominator ∈ daily liquidity aggregates → default-skip。**逃离正路径**：(a) numerator ∈ {pe/pb/ps/dividend_yield Barra value basis 字段}；(b) Python OLS residualize TTM quality on (size, vol_20d) 后再 ratio；(c) TTM × TTM 内部交互（需 Python 包装）
- **Higher-moment LHS / signed fundamental cross-product 四类 atom regime sign-flip**（b052/b053/b054/b068 验证）：
  1. **raw fundamental Std/Var**：`Std($pe_ratio,20)` / `Var($pb_ratio*$turnover_rate,60)`
  2. **raw intraday signed ratio higher-moment**：`Std((C-O)/close,20)`
  3. **residual higher-moment**：`Std(residual_ret,20)` / `Sum(residual_ret,5)`
  4. **signed fundamental cross-product**：`Mul($growth_TTM, Div(1, $value_PIT))` / GARP；growth_ttm 与 1/pe 在 2015-2021 同向 / 2022-2023 反向
  
  **触发条件**：(a) LHS 含 `Std/Var/Sum($X,N)` 且 `N≥20d`，X ∈ {raw fundamental, raw intraday signed ratio, residual_returns}；**或** (b) 顶层 `Mul`/`Div` + 两端 signed fundamental signal。**安全反例**：F019 `Std(body_ratio,20)` + F020 `Std(gap_ret,20)`（scale-free ratio + N≤20d + 单层 moment）。**衍生律 (compound moment IS over-fit)**：嵌套 smooth-then-std (b052 C006) ls_t_is=12.18 → ls_t_oos=-0.13 — hard_gate `is_oos_lst_collapse` 已升格

- **Cov / Corr 长窗口协动 family csi1000 daily 真饱和**（b075/b079/b039 三方向 dead）：3 路径独立证伪：(a) raw `Cov(.,.,N)` microstructure × valuation level（b075 6/6 reject, alpha_surv 0.06–0.30）；(b) TsRank-Corr 双重包裹（b079 6/6 reject, 60d alpha_surv PASS 但 ic_oos<0.008，120d sign_flip）；(c) raw Cov(return-side)（b039 6/6, 撞 F001/F009/F012 反转簇）。**实操**：任何 Cov / Corr / TsRank-wrap-Corr 候选 N≥60d default-skip；复活路径仅 (a) 短窗 ≤20d（已被 b039 撞死）；(b) 非 daily-bar；(c) self-normalized ratio atom + N≤45d（F024/F025 替代）

- **Meta-pattern 跨方向机械迁移**：F013 log-compression 在 `gap_acceptance_structure` admit；同款 log 套到 value × liquidity (b038 6/6 IC_OOS 全负) / momentum gate (b037 6/6 reversal) / Cov 形态 (b039 6/6) 全 reject。**结构相同 ≠ 语义相同** — 复用上批成功 trick 必须先验底层 raw signal 在 csi1000 alive + trick 在新方向 underlying drift 同号

- **Rank-preserving 单算子包装**：见 Operator Registry 段。Generator AST 预拦截 `f(F_admitted)`

**绝对不放宽的硬闸**：`hard_gate` 全局阈值（coverage / sign_flip / ic_oos_min / mono_flip / near_duplicate）；市值代理红线；holdout 保护。例外仅 barra_residual_alpha coverage→0.70。

**已升格 hard_gate**：
- **`is_oos_lst_collapse`**：`|ls_t_oos|/|ls_t_is| < 0.10 且 sign(is) ≠ sign(oos) 且 |ls_t_is| > 5.0` → reject 标 `compound_moment_collapse`
- **`library_reducer`**：见 Rank-order ≠ Tradable Alpha 段四要件
- **`corr_cov_field_safety`**：phase1 generator AST 检测 `Corr/Cov(A,B,N)` 节点，A/B 不双方在 Corr-safe 字段集 → reject；safe set = `{$close, $open, $high, $low, $volume, $amount, $num_trades}`

## csi1000 daily fundamental + institutional flow 真饱和（顶层 macro lesson）

**alpha 真饱和不是阈值过严**（b068-b072 + b075/b079 7 路径独立证伪）：连续跨 fundamental_quality_carry / pit_valuation_pure ×2 / python_ttm_residual_quality / institutional_flow_proxy / cov_microstructure_valuation / cov_ratio_long_window 全部 0-admit。**7 独立失败路径**：

1. **daily-aggregate liquidity ratio**（b068）：6/6 reject
2. **PIT valuation rank composite**（b069/b070）：rank × rank Mul 仅当 RHS 含 1/PB 时 book basis 显化（b069 C006 b/p=2.21 reserve）；PE/PCF 替换 6/6 reject
3. **Python OLS residualize TTM quality**（b071）：alpha_surv ∈ [0.93, 7.23] 全 PASS 但 6/6 OOS sign_flip
4. **TTM aggregate signed signal**（b069 C003/C005）：1/peg / 1/pcf_total 全 sign_flip
5. **institutional flow microstructure**（b072）：raw level → F012 anchor；TsRank 60d 几何独立但 forward reversal
6. **Cov microstructure × valuation 长窗**（b075）：alpha_surv 0.06–0.30, dom=vol_20d
7. **TsRank-Corr 双重包裹长窗**（b079）：60d ic_oos<0.008，120d sign_flip

**Forward horizon h>1d 评估路径全库零兑现**：60d Cov daily 1d primary horizon 信噪比天花板 ~0.006-0.007；120d 信号反映 ≥半年级 macro/sector regime，daily 短期 alpha 时间尺度不符。

**结论**：TTM quality / TTM valuation / institutional flow / long-window Cov/Corr 在 **csi1000 daily-bar 频率上不存在 OOS-stable cross-section alpha**。**唯一未探路径**：minute/tick 数据 + 其它 universe (csi300/csi500)。

### Composition Selection（rank × rank Mul 需 book yield basis）

**rank × rank Mul 复合需两端 atom 几何独立 + 至少一端 book yield basis 显化（b/p≥2）**（b069 C006 reserve + b070 6/6 reject）：
- **book_to_price (1/PB)** 是 csi1000 cross-section **唯一同时具备** (a) cross-section dispersion 强 + (b) value Barra basis 抗 vol_20d 显化能力的 atom
- **PE/PCF/PEG** 在 ep_ratio basis 上有 dispersion 但缺 b/p basis 抗 vol_20d
- **充分但不必要**：`b/p ≥ 2 → ls_t ≥ 2`；`b/p<1.0 → ls_t<1.1`
- **Mul vs Sub 不对称律**：Mul 放大共有 basis（style_r²=0.578），Sub 抵消共有 basis（style_r²=0.23）

## Paper Transferability

`/factor-paper` skill 的 paper intake → direction 转化阶段必读。

**Paper csi300 → csi1000 transfer 三件套** (pattern_analyst/026 升格)：
1. **8x+ 衰减是常态**：gap_acceptance T001 paper Channel 1 (CSI 300 Rank IC 0.0744) → csi1000 三窗口同步 sign_flip + 2015-2020 全正 / 2021-2023 全负完全反转；唯一存活 F013 IC_OOS=0.0094 (~8x 衰减)。trend_quality_gated paper Channel 3 (CSI 300 Rank IC 0.0590 + 0.0465) → csi1000 6/6 IC_OOS 全负
2. **复刻硬约束**：(a) 必须先在 csi1000 上重测原始 raw signal 是否同号；(b) 若同号衰减 ≥ 5x 再考虑非线性压缩（log）；(c) 若翻号或单调性破坏，方向直接 dead
3. **Sign aggregation underlying drift dependency**（三次对照确认）：sign-based aggregation 候选必须先验证 underlying field rolling mean 显著非零
   - F018 admit (b049 C006)：`Mean(Sign(overnight),20) × amount` ic_oos=+0.051 ls_t=+5.98 — overnight 有 institutional accumulation drift
   - b050 C006 reject：`Mean(Sign(close-open),5) × pb_20` — intraday body 是 random walk
   - b035 C001-C003 reject：pure `sign(gap) × sign(body)` 三窗口全 sign_flip

**paper-driven candidate freeze 前必须 explicit 标注** `expected_decay_factor ≥ 5x for csi1000 transfer`。

## Direction Lifecycle

方向状态机：`exploring → productive ↔ saturated → dead → archived`。

- **首批反向证伪 → 当批 dead (三要件 codify, hypothesis_promoter/014 升格)**：复用上一批 admit 的 meta-pattern + 在新底层信号上重新包装 = hedge-bet 方向。**判别**：首批 (1) reject_rate ≥ 80% **且** (2) ≥2 候选独立命中 hard_gate (sign_flip / mono_sign_flip / IC_OOS 全反向) **且** (3) 失败机制非"窗口/算子细节"而是"信号方向与 hypothesis 反向" → 方向**当批 dead，priority 降到 low**。**例外**：方向若已 admit ≥ 1 因子 → 转 saturated，不 dead
- **Saturated 双层证据律**：方向标 saturated 必须 (a) 信号设计层证据（≥2 路径 cluster / ≥3 candidate 几何不变量）+ (b) 数据契约层证据（Python residual coverage 实测 < 0.80 **或** Python 工具链未实现）。**(a)+(b) 同立** 才允许 saturated
- **`archived` 状态**：触发 = 元教训已升格至 lessons.md + 方向 dead/saturated ≥30 天 + 无活跃 active thread。行为 = 方向 md 保留但 INDEX 不再列出，Phase 1 不再考虑。复活仅当 lessons.md 升格条目本身被推翻
- **当前批量 archive 状态 (round 75)**：return_distribution_signals / vol_shock_signals / quantile_shape_signals / trend_quality_gated / log_value_liquidity / pv_covariance / asymmetric_momentum / fundamental_momentum / return_momentum_acceleration / fundamental_quality_carry / cov_microstructure_valuation / cov_ratio_long_window / stochastic_position / tsrank_candlestick_ratio (saturated)

## Metric Semantics

- **`ic.half_life_days`** — **IC 衰减**半衰期。从多 horizon 的 train IC 曲线拟合，单位 = 持仓 horizon 天数
- **`feasibility.signal_half_life`** — **signal 自相关**半衰期。每只标的信号 ACF 首阶跌到 0.5 的滞后，单位 = 交易日
- **二者不可互换**。遗留单名 `half_life` 字段已 deprecated

## Language Policy

- **叙事主体：中文**。Hypothesis / Current Focus / Narrative Log / 反思 / verdict 理由 / Thread 推理全部中文
- **术语保留英文**：IC / ICIR / Sharpe / Barra / monotonicity / style_r² / alpha_survival / long_short / hard_gate / mt_bucket / admit / reserve / reject / exploring / productive / saturated / archived 等不翻译
- **YAML / frontmatter 值**：英文 snake_case
- **Markdown H2 标题**：英文（`## Hypothesis` / `## Threads` / `## CP01` 保持稳定便于 audit grep）
- **例外**：`INDEX.md` 上半段段落标题用中文

## Threshold Calibration

Thresholds 不是公理，是**可证伪的经验值**。

### 触发条件

任一满足即应审视当前阈值是否过严：
1. **连续零 admit**：同方向 ≥ 3 批次 0 admit 且每批有 reserve
2. **Reserve 积压**：累计 reserve / 累计 judged > 40% 且零 admit
3. **库规模停滞**：累计 batches ≥ 5 但 library size 未增
4. **悖论复现**：同一"反直觉指标组合"在 ≥ 2 候选独立出现
5. **rank-diff paradigm 系统性错杀**：rank-diff 候选因 structural vol_20d exposure 在 alpha_surv ∈ [0.30, 0.40] 区间被默认 0.40 刷掉（已 codify 0.30 floor）

### 放宽的依据

- **Barra-clean ≠ library-clean**：CP04 测与 Barra 7-basis 几何关系；CP05 测与已 admitted 因子。错杀侦测必须**同时**满足 (a) max_corr<0.30 + (b) incr_ic>0.010 + (c) mono>0.8 + (d) sign_consistency=1.0
- **Portfolio-level orthogonalization**：单因子 Barra 脏 ≠ 不可用
- **"Static vs dynamic orthogonal" 悖论**：低 `style_r²` ⊥ Barra basis；低 `alpha_survival` IC L/S weights ∈ span(Barra)。二者可共存

### Direction-aware 阈值（已生效）

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

**rank-diff trigger**：candidate LHS/RHS 都包含 `CsRank(...)` 且顶层 `Sub` → 走 `rank_diff_geometry` 档；其余走 default。

**incr_ic borderline 律**：max_corr ∈ [0.30, 0.70] borderline 时，incr_ic ≥ 0.015 是 admission 必要条件。

### 绝对不做的事

- **不放宽 hard_gate**（coverage / sign_flip / ic_oos_min / mono_flip / near_duplicate / library_reducer / is_oos_lst_collapse / corr_cov_field_safety）— 例外仅 barra_residual_alpha coverage→0.70
- **不放宽市值代理红线** `|corr($market_cap)| > 0.3`
- **不放宽 holdout 保护**
- **不机械地在"连续零 admit"就放宽** — 必须先诊断是否真"错杀"

### 历史校准记录

- **2026-04-19**：`alpha_surv_min` 0.60 → 0.40；rubric CP04 poor 阈值 0.60 → 0.30；追溯 admit F002
- **2026-04-25**：引入 3 条 direction-aware 阈值 — `alpha_surv_min.rank_diff=0.30` / `min_coverage_by_direction.barra_residual_alpha=0.70` / `incr_ic.min_when_corr_borderline=0.015`
- **2026-04-27**：rename rank_diff → rank_diff_geometry；新增 hard_gate `is_oos_lst_collapse` + `library_reducer_hard_block`；升格 Rank-order ≠ Tradable Alpha；引入 archived 状态 + 首批反向证伪 dead 律
- **2026-05-02 round 69**：无阈值调整。3 lesson 升格（TTM-quality default-skip / TTM × TTM DSL 失败 / signed fundamental cross-product）
- **2026-05-02 round 73**：无阈值调整。5 lesson 升格（alpha_surv + ic_by_year / Linear OLS 不破非线性 / TsRank≥60d ratio escape / csi1000 daily fundamental 真饱和 / Composition Selection book yield）
- **2026-05-02 round 74**：新增 hard_gate candidate `corr_cov_field_safety`。9 lesson 升格（Qlib binary 数据契约 / Cap-denominator vol_20d / Reserve revival 4 路径 / Geometric absorbing-factor / Cross-product Mul 塌缩 / In-batch denominator P024 / Cov/Corr 长窗 saturation / P008 软判定 / Forward horizon h>1d 零兑现）
- **2026-05-03 round 75**：无阈值调整。本轮升格新 lesson：(a) Operator Registry 加 "Cov ≈ Mean(X·Y) DSL 等价定理"；(b) Path Selection 加 "P008 完整三条件" + "P028 rank-form zero-mean anchor"；(c) Structural Constraints 加 "F001 first-moment 累积扩展 anchor" + "Anchor cluster sufficient basis lock 强制 pre-check" + "Directional signed magnitude 优先级"；(d) Rank-Diff 段加 "Rank-diff salvage 限定不救 saturated"；(e) Paper Transferability 重组为三件套；(f) Direction Lifecycle 首批反向证伪三要件 codify；(g) Data Facts 加 "2022-2023 regime ground-truth"

## Promising Unexplored

> Phase 1 新开方向时参考。

- **高阶 composition (ratio-of-derived-quantity)**：F025 shadow_asymmetry vol_20d_exp=6.03 frontier 真生效顶级；可在 OHLC body / range / shadow / overnight / gap family 复现
- **TsRank ≥60d on microstructure-only ratio fields**：F024 是 escape 首例；cross-section dim-less ratio + microstructure-only 两端 + TsRank ≥60d 是新 frontier
- **Higher-moment LHS independence axis on scale-free OHLC ratios**：F019 + F020 跨 OHLC×gap 两 family 兑现；可优先在 microstructure / overnight 同构尝试
- **Sign × persistent drift × non-linear weighting**：F018 + F013 是仅有 sign-aggregation admit；分红 / 公告事件 / index inclusion 等 persistent drift underlying 未尝试
- **Cross-section 算子 (CsRank/CsZscore/CsDemean) 替代 rolling**：解决 Python residual+rolling coverage=0.71 死路
- **非 daily-bar 数据**（minute / tick）：vol_20d 吸收律根本逃离；当前数据基础设施未就绪 — 一旦支持，magnitude / quantile / power-mean 一片 dead 方向可能复活；同时是 csi1000 daily fundamental 真饱和的唯一脱钩路径
