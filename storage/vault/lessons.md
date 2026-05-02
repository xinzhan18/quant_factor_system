---
version: 7
last_consolidated_at: 2026-05-02T07:00:00Z
source: Phase 5 consolidation round 74 — promoted from calibration/007-008 + library_gap/012-014 + pattern_analyst/016-021 + hypothesis_promoter/011-013. New lessons升格: P019 Qlib Corr/Cov cross-field start_index 数据契约硬阻断; P021 Cross-product Mul wrapper 系统性塌缩律; P008 escape 机制层验证 (alpha_surv≈1.0 in b081 / b072 frontier); Library-residualize 路径未启动 + 跨 family rhs_change 是仅生还路径; minor-path revival 系统证伪 (b078); Geometric absorbing-factor 律 + 高阶 composition 逃离路径; Cap-denominator 隐藏 vol_20d (microstructure 端实证); In-batch denominator family 等价性自检 (P024); Forward horizon h>1d 评估路径全库零兑现 (Cov/Corr long-window 真饱和).
---

# Research Lessons

系统级硬事实。每次挖掘循环开始前必读。
由 Phase 5 CONSOLIDATION 周期性重写。**不要**在这里追加单 batch 的教训 —— 那些写在 `directions/{direction}.md`。

固定四段结构：**Data Facts** / **Operator Registry** / **Path Selection** / **Structural Constraints**。其它段（Forbidden Patterns / Paper Transferability / Direction Lifecycle / Threshold Calibration / Metric Semantics / Language Policy / Promising Unexplored）按需附加，不引入新四段外的"常律"段。

## Data Facts

- **Data split (不可违反)**：
  - Train `[2015-01-01, 2021-12-31]` / Validation `[2022-01-01, 2023-12-31]` / Holdout `[2024-01-01, 2024-12-31]`（Phase 2/3 永远看不到，仅 `research holdout-review` 可读）/ 2025+ 永不触碰
- **Primary universe = `all_tradable`**：CP01–CP06 全套判定在「全市场可交易股票日」上跑（`base_tradable ∧ load_universe_mask(primary)`），csi300/csi500/csi1000 仅作 robustness label，不进 verdict
- **csi300 是 alpha 死区**：23 因子 retrofit 显示 7 个跨过 admission floor；大盘股被机构 arbitrage 压平 alpha 是常态
- **`$vwap` 全零**（数据源未填）—— precheck 禁用；**`$amount` 有数据**
- **A 股约束**：不做空头 alpha；因子必须从多头侧产生
- **市值代理红线**：`|corr| > 0.3` 对 `$market_cap` / `$circ_market_cap` 直接 reject（size factor 已占 Barra basis，放宽 = 双重计数）
- **A 股 ±10% 涨跌幅约束**：`$high / $low / Ref($close,1)` 三 reference point 同时被夹紧，使 `(H-L)/C` / `|gap|/range` / `gap/Std(ret,20)` 等 cross-section affine-like 共变 → 与 gap/VWAP 系列 (F003/F014) 80%+ cluster 是默认结局
- **Train→Validation regime 切换**：2015-2021 (低利率成长) → 2022-2023 (利率上行价值回归)；higher-moment LHS 在 raw fundamental / intraday signed / residual 字段上**系统性翻号**
- **Tradable mask + ST 过滤改写历史 mono**：persistence/mean/cumsum 系列 freeze 阶段必须看 ST-filtered probe IC，不能信 raw probe（F003/F010/F011 旧版无 ST mask mono=1.0，加 PIT ST + 停牌 mask 后跌到 0.40）
- **Qlib binary 数据契约（P019 升格 round 74）**：二进制格式 `[start_index:f32][data:f32×N]` 中，**PIT valuation / 全 TTM ratio / `$turnover_rate`** 与核心 OHLCV 字段 `start_index` 不一致（RiceQuant 同步起点不同）；`Corr(safe, unsafe, N)` 在多股票 universe 内部 rolling 操作 shape mismatch（实测 2620 vs 2674）→ `np.isclose` broadcast crash 整批 compute 终止
  - **Corr-safe 字段集**：`{$close, $open, $high, $low, $volume, $amount, $num_trades}`（仅 7 字段双端可用）
  - **Corr-unsafe 字段集**：全 PIT valuation (`$pe_ratio` / `$pb_ratio` / `$ps_ratio` / `$pcf_ratio` / `$market_cap` / `$circ_market_cap`) + 全 TTM ratio (`*_ttm`) + `$turnover_rate`
  - 修复路径：(a) data loader unify start_index；(b) Python 包装绕过 Qlib op；当前 fix 未到，**Phase 1 generator AST 层硬阻断 cross-field Corr/Cov 候选**

## Operator Registry

- **白名单唯一**：DSL 算子/字段必须出现在 `src/research/phases/phase1_start.py:DSL_FIELD_WHITELIST`
- **可用字段**（2026-05-01 扩展，22 个基本面/微观字段）：
  - 价量：`$open $high $low $close $volume $amount`
  - 微观：`$turnover_rate $num_trades`
  - 估值 PIT：`$pe_ratio $pb_ratio $ps_ratio $pcf_ratio $market_cap $circ_market_cap`
  - 盈利 TTM：`$return_on_{equity,asset,invested_capital}_ttm $gross_profit_margin_ttm $operating_profit_margin_ttm`
  - 偿债 TTM：`$debt_to_{asset,equity}_ratio_ttm $current_ratio_ttm`
  - 效率 TTM：`$total_asset_turnover_ttm $inventory_turnover_ttm $account_receivable_turnover_rate_ttm`
  - 成长 TTM：`$operating_revenue_growth_ratio_ttm $net_profit_growth_ratio_ttm $net_asset_growth_ratio_ttm`
  - 每股/收益率 TTM：`$eps_ttm $book_value_per_share_ttm $operating_cash_flow_per_share_ttm $dividend_yield_ttm`
  - 估值 TTM：`$pcf_ratio_total_ttm $peg_ratio_ttm`
  - 数据来源：`ref_financials` (TTM) / `ref_valuation` (PIT) / `ref_shares` (microstructure)
- **自定义算子**（需要 `C.kernels = 1`）：`TsRank, TsMax, TsMin, TsAutoCorr, TsDecay, TsMomentum, RealizedVol, CsRank, CsZscore, CsDemean, AmihudIlliq, HHI, SignedPower, Tanh, Exp, Sigmoid`
- **禁用算子**：`Neg`（用 `Mul($x,-1)`）；`SMA`（用 `EMA` 或 `Mean`）
- **横截面算子**（`CsRank/CsZscore/CsDemean`）始终在 `D.instruments("all")` 上计算，与挖掘 universe 无关
- **Rank-preserving 单算子变体零增量律**：DSL `{Linear, SignedPower(p>0), Sigmoid, Tanh, Exp, Softmax, CsZscore, Scale}` 包装单已 admit 因子 → cross-section rank 完全保留 → max_corr ≈ 1.000 必为 near_duplicate；Generator AST 层硬阻断 `f(F_admitted)`
- **DSL Div/Mul 不是真 orthogonalization**：`Div(factor, vol_proxy)` / `Div(factor, turnover_mean)` 要么保序，要么仅是 style exposure 搬家；真 orthogonalization 必走 Python OLS / Barra residual

## Path Selection

- **默认 DSL**（R8）。Python 逃生口仅在：DSL 无法向量化的非平凡循环 / DSL 表达不了的横截面操作 / 对发表 Python 参考实现的显式复刻
- **Python 因子契约**：`compute(df: pd.DataFrame) -> pd.Series`，df MultiIndex=`(time, symbol)`；模块级 `REQUIRED_FIELDS: list[str]` + `VECTORIZED: bool = True`；纯函数；导入白名单 `numpy/pandas/scipy`，禁用 `subprocess/os/sys/eval/open`
- **REQUIRED_FIELDS 必须 ⊆ loader 默认列**：`data_bridge.load_market_data` 默认 = `$amount, $market_cap, $close, $volume, $open, $high, $low`，**不含** `$turnover_rate / $pe_ratio / $pb_ratio / $ps_ratio`；Phase 1 freeze 必须 static validate
- **Python 因子源代码必须走代码版本控制**：`storage/python_factors/F{id}_*.py` 是运行时入口（被 PR 跟踪），`vault/batches/.../python_candidates/` 副本仅作历史快照
- **TTM × TTM 直接 DSL Sub/Mul/Div 数据契约失败**：`ref_financials` TTM per-share 字段（`$eps_ttm` / `$operating_cash_flow_per_share_ttm` / `$book_value_per_share_ttm` / `$dividend_yield_ttm`）报表期外 NaN ~10–30%；csi1000 daily 跨字段 NaN intersection ~40%+；DSL `Sub/Mul/Div` 不容错（任一边 NaN→结果 NaN）→ preprocessed factor empty hard_gate fail。修复路径：(a) Python cross-section ffill 后 Sub；(b) z-score 后 Sub；(c) 标准化 `(eps-ocf)/|eps+ocf|` + ffill。**Generator pre-check**：顶层 `Sub/Mul/Div` 且两端 atom 都 ⊆ TTM 字段集 → DSL 不可行硬阻断
- **Python residual + rolling 在 csi1000 系统性 coverage ≈ 0.71**：cross-sectional Barra residual ~1% NaN + rolling min_periods≥10 + csi1000 上市日异质性 → 三因子复合后 coverage 0.685–0.725，与 0.80 hard_gate 结构性不兼容；信号常常 alive (b034/C005 alpha_surv=1.20 / b054/C005=1.57) 仅 coverage gate KO。修复路径：(a) cross-sectional 算子代替 rolling（CsRank/CsZscore 不需 min_periods）；(b) loader 端 ffill / industry-mean fill；(c) direction-aware 阈值放宽到 0.70（仅 barra_residual_alpha 临时 workaround）
- **alpha_survival ≥ 0.40 必须配 ic_by_year 后期同号 check**（round 73, b071 6/6 实证）：alpha_survival 衡量"残差对 Barra 已知 style 线性独立"，**不预测 OOS sign alive**；b071 Python OLS-residualized TTM quality 6/6 候选 alpha_surv ∈ [0.93, 7.23] 全 PASS 但 train +α / val -α 全部翻号。机理：alpha_survival 仅捕"对线性 Barra basis 的剥离"；csi1000 daily TTM quality 在 2022-2023 regime drift 独立失活，与 Barra style 暴露**无关**。**判据 composition**：alpha_survival 不可独立作 admission gate，必须配 cross-validation sign-stability（`ic_by_year` 2022/2023 不翻号）；alpha_surv >> 1.0 但 ic_by_year 后期翻号 → 默认 reject
- **Linear OLS residualize 不破 csi1000 vol_20d 非线性吸收**（round 73, b071 5/6 实证）：`numpy.linalg.pinv + einsum` vectorized OLS residualize on Barra basis 工艺正确（alpha_survival ≥ 0.93 PASS），但残差 dominant_style 仍 vol_20d，vol_20d_exp ∈ [11.6, 22.9]。机理：OLS 只 strip 线性 βvol_20d，残差仍载 vol_20d 二阶/非线性载荷——cross-section daily 上 vol_20d 是非线性 manifold。**vol_20d 结构性吸收律段"逃离正路径 (a) Python Barra residual orthogonalize"** 限定语义：仅在 numerator 自身有 OOS-stable alpha 时该路径生效。不试 Polynomial/Kernel OLS（参数过多过拟合）
- **TsRank window≥60d on ratio fields 是新 vol_20d-escape 路径**（round 73, b072 C006 + b068/b069 对照实证；round 74 b081 C006 机制层验证 alpha_surv≈1.0）：在 ratio 字段（`$amount/$num_trades` / `$amount/$volume` / `H/L` / `$close/Mean(...)`）上，TsRank 时序量纲化（≥60d）相比 cross-section level / Std rolling 大幅降低 vol_20d 暴露；同字段 raw rank vol_20d_exp=30.9 → TsRank60=10.87（**降 65%**）；style_r² 0.59 → 0.15（**降 75%**）。机理：60d 时序 rank 把 cross-section level 替换为"个股自身分位"，绕过 cross-section vol_20d basis ranking 重叠。**前提**：仅适用于 ratio 字段；alpha_surv ≥ 0.40 必须 PASS。**库内现状**：51 admit 中 TsRank 几何 admit = F024/F025 + b072 C006 reserve 火种；b081 C006 alpha_surv≈1.0 = Barra 空间独立载体首次机制层验证（但 incr_ic=-0.035 强 NEG 库 reducer 三件套 reject）
  - **衍生律 (raw $num_trades 不构成新几何)**：cross-section raw level 形式上不提供新独立几何（b072 C002 `CsRank($num_trades)` max_corr=0.75@F012 NEAR_DUPLICATE，F012 Amihud 通过 size 共线性已覆盖 retail attention/trading frequency）；raw $num_trades CsRank default-skip；复活路径 (a) Python OLS size-residualize on log_circ_cap；(b) 时序 form (TsRank ≥ 60d)；(c) cross-sectional rank-diff 配独立 RHS basis
- **Cap-denominator 隐藏 vol_20d 嵌入路径，frontier 部分失效**（round 74 升格，b073/b074/b068 实证）：形态 `f(microstructure, $market_cap)` / `f(microstructure, $circ_market_cap)` / `f(quality, Mean($amount,N))` / `f(quality, Mean($turnover_rate,N))` 即使外层用 P008 frontier 路径（TsRank≥60d on ratio）仍 vol_20d_exp 显著高于 OHLCV-only 同形候选 50%+。证据：b073 C005 TsRank(`$turnover_rate/$market_cap`,60) vol_20d_exp=17.4 + incr_ic=-0.036；b074 C004 TsRank(`$num_trades/$circ_market_cap`,60) vol_20d_exp=19.1 + incr_ic=-0.038；b068 C001 ROE/Mean($amount,20) vol_20d_exp=23.4 整库顶级；对照 F024 (num_trades/volume) microstructure-only ratio vol_20d_exp=12.6 frontier 真生效。机理：cap-类字段 cross-section 与 vol_20d 共线（small-cap=high vol），用作分母把 numerator 拉入 size×vol_20d 联合 basis。**实操**：P008 frontier 仅适用于两端都是 microstructure-only/OHLCV-only；cap-denominator 形态默认 reject。**安全反例**：F002 (PB/Mean(amount,20)) PB 自带 value Barra basis 抗衡 vol_20d；F012 (Amihud Mean(|Δclose|/amount,N)) microstructure 端特例
- **Reserve revival 仅生还路径**（round 74 升格，b078 6/6 reject 实证）：51 flip-candidate retro audit 实测——5 minor 复活路径全部失败（`Δ max_corr` 全为正或大幅恶化）：
  - **P025 rank-form 仿射 no-op**：TsRank/CsRank 在 affine `a*x+b (a>0)` 下不变；减常数/减 rolling mean 是数学 no-op，Phase 1 设计 checklist 必须 reject
  - **P026 reserve alpha decay**：chronologically aged reserve（≥1 year / ≥20 batches）retest 时信号可完全消失（b053 ls_Sharpe=2.45 mono PERFECT → b078 ic_oos=+0.0025 mono FLIP）；retro_post_floor 路径**不假设原信号守恒**
  - **P027 rhs_change 必须跨 family**：同 microstructure liquidity family 内换 RHS（turnover→num_trades / amount→num_trades / H/L_60→num_trades）不破共线性——同 hypersurface 不同投影
  - **P028 Library saturation 单调累积**：reserve 推迟复活无收益，反而越来越难；不存在"等阈值变松了再复活"的免费午餐
  - **仅生还路径**：(a) **Python residualize**（cross-section OLS residual against blocking factor，DSL 表达不出，走 storage/python_factors/）；(b) **跨 family rhs_change**（microstructure → fundamental basis 或 temporal basis）；(c) **structural transform**（Mean→Std/Skew 量纲层升级）；(d) **跨 direction 机制复现**（P008 escape 在不同 direction 复测，不是对原候选 revival）

## Structural Constraints

- **禁看 holdout**：Phase 2/3 代码永远不能读 2024 年数据；holdout 物理隔离在 `storage/_holdout_private/`
- **向量化（R5）**：禁止行/日期/标的 `for` 循环；禁用 `groupby.transform`（隐式按日期 for）；标准套路 long→wide pivot→`(n_dates × n_symbols)` 矩阵 numpy→wide→long
- **Barra residual 基线**：alpha 是在剥离 Barra 风格暴露后度量；`style_r²` + `alpha_survival` 是 CP04 核心。当 dominant_style=vol_20d 时优先看 alpha_survival（b056 C006: style_r²=0.21 borderline 但 alpha_survival=0.0725 极端 poor）
- **冗余红线（CP05）**：对已 admitted 因子 `max_lib_corr > 0.70` 直接 reject
- **Python 因子必须进 library 对比**：`data_bridge.load_library_signals` 同时覆盖 DSL + Python 两源（按 `sha256(源码)` 缓存）
- **Sample policy 版本**：`config.yaml.sample_policy_version`（v3→v4）会重置 §7.MT 多重检验预算的 `validation_exposure` 计数
- **Multi-universe schema**：`validation_metrics_by_universe` 写入三 universe + `universe_robustness` summary + `recompute_provenance`
- **Library recompute self 检测必须空 library_signals**：批量重算整库时若仍走 `data_bridge.load_library_signals`，每个因子跟自己/同 family 做 redundancy → 全部 hard_gate fail；recompute 时手动 `inputs.library_signals = {}`
- **`revalidated_in_batch` ≠ `admitted_in_batch`**：report builder 必须读 `meta.get("revalidated_in_batch") or meta["admitted_in_batch"]`；admit 历史保留作 audit trail，不可覆盖
- **DB `factor_values` 表已 DROP**：`factor_001..factor_045` 是 mining_v1 时代命名，跟 F-命名不对应；Phase 2 不读 DB（用 sha256-keyed parquet cache + 即算即用）

### vol_20d 结构性吸收律（≥10-direction 顶级失败律）

csi1000 daily-bar cross-section 几何被 Barra `vol_20d` 占据 2nd-moment 空间。任何 magnitude / ratio / power-mean / Std / Var / quantile / IQR 形态——无论作用于 return / range / amount / turnover / OHLC ratio——cross-section rank 都 monotone-equivalent 到 vol_20d，alpha_survival 典型 0.08–0.30。

**机理**：A 股 ±10% 涨跌幅 + 小盘散户主导，使 `|daily_return|` / `(H-L)/C` / `$amount` 的 std/CV / Quantile 差 / Skew/Kurt 在 cross-section 上高度同构。Robust estimator (Quantile/Median) 的 outlier-robust 性 **不等于** Barra vol_20d orthogonality。**Daily-aggregate liquidity denominator 隐藏路径**（fundamental_quality_carry 跨字段族扩展）：`Mean($amount, N)` / `Mean($turnover_rate, N)` 作 denominator 时**本身 cross-section 嵌入 vol_20d**——把任意 numerator（即使 fundamental TTM 几何独立）拉进 vol_20d basis；F002 (PB/Mean(amount,20)) admit 是**特例**：PB 自带 cross-section value Barra basis 抗衡 vol_20d。

**判别规则（reject）**：`dominant_style=vol_20d` + `style_r² > 0.30` + `alpha_survival < 0.30` 三者同立 → 直接 reject，切换设计轴。

**逃离路径仅四条**：(a) Python Barra residual orthogonalize（受 coverage<0.80 + Linear OLS 不破非线性吸收双重限制；仅在 numerator 自身有 OOS-stable alpha 时生效）；(b) 非 daily-bar 数据（minute/tick）；(c) 非 magnitude 几何 —— sign 聚合 / rank-diff cross-family / 严格 mono_is≥0.6 + scale-free RHS 的 higher-moment 单层；(d) overnight 段独立分解；(e) **TsRank ≥60d on ratio fields**（round 73-74 升格新路径，仅适用于两端都是 microstructure-only / OHLCV-only ratio，cap-denominator 失效）。

**证据链**：≥12 方向独立确认 —— return_distribution_signals / vol_shock_signals / amount_volatility_signal / stochastic_position / range_structure / quantile_shape_signals / intraday_price_formation / turnover_structural_signal / vwap_proxy_signals / fundamental_quality_carry / python_ttm_residual_quality / institutional_flow_proxy / cov_microstructure_valuation / cov_ratio_long_window。

### Geometric absorbing-factor 律（admit 后同 family frontier 上限饱和）

一个 admit factor 在其几何家族内自动成为 absorbing prototype，同 family 后续 frontier 续探在 cross-section 上 max_corr ≥0.55 @ 该 factor。**4+ admit factor 跨 6+ direction 独立确认**：
- **F024** (TsRank(num_trades/volume,60), b073 admit) → b074 三轴 ablation (window/cross-atom/mirror-atom) 全 max_corr ≥0.91@F024
- **F025** (TsRank(shadow_asymmetry,60), b076 admit) → b077 三层 nested Div/Mul + cross-product Mul 三类续探全 max_corr 0.58–0.70@F025
- **F018** (overnight sign-aggregation) → b078 C006 rhs_change 0.576→0.790@F018 加深耦合
- **F021** (upper_shadow_disp_range_compress) → b081 C001 hl_norm_sym 60d Mean max_corr=0.68@F021 数学同构

**机理**：admit 因子在 cross-section 几何上"占领" family prototype 位置，后续同 family 候选（同 atom × 不同 window / nested composition / cross-product / 替换 form / 同字段跨窗）在 cross-section ranking 上仍 monotone-equivalent 到 prototype。

**判别要件**：family 内 admit ≥1 后，同 family 续探 max_corr ≥0.55 @ admit factor → 默认 reject 不再消耗 CP3-CP6 计算预算；续探必须 (a) cross-family（atom × directionally orthogonal RHS）；(b) Python residualize on prototype；(c) structural transform (Mean→Std/Skew 量纲层升级)。

**逃离路径**：**高阶 composition (ratio-of-derived-quantity)** —— F025 shadow_asymmetry 是 ratio of two derived shadow lengths（不是 single-atom ratio），cross-section 上分子分母同消 base scale + base volatility，与 single-atom Mean shadow (F008) 几何独立（max_corr 0.29 vs 0.45–0.47），vol_20d_exp=6.03 frontier 真生效顶级。与 TsRank≥60d ratio escape 配对：高阶 composition 是 dim-less ratio frontier 真红利第二阶。

### Cross-product Mul wrapper 系统性塌缩律（跨 4+ direction 5+ 次独立证伪）

形态：`Mul(F_admit_atom_A, F_admit_atom_B)` 或 `Mul(CsRank(A_admit), CsRank(B_admit))` **从不产生独立新维度**，仅出现两失败模式：
1. **塌缩到强势一端**（b077 C004 max_corr=0.6972@F025，F024×F025 = F025 复制）
2. **sign_flip catastrophic + alpha_surv collapse**（b074 C006 alpha_surv=0.068 + incr_ic=-0.023；b080 C001 decay=-5.16 + sign_flip）

机理：Mul 改变 cross-section moment structure → Barra style basis 重新捕捉；sign 由联合分布 quartile 决定 → regime drift 触发 sign 翻号；在 cross-section rank 上塌缩到几何 dominance 较强一端。**与 Sub 不对称**：Sub 抵消共有 basis（rank-diff 6 admit），Mul 放大共有 basis（系统性塌缩）。

**安全例外**：(a) F025 高阶 composition (ratio-of-derived-quantity 单 atom 内部)；(b) `Sub(CsRank(A), CsRank(B))` rank-diff 形式。

**Generator pre-block**：`Mul(F{id}_atom_A, F{id}_atom_B)` 或两端来自已 admit factor atom 形式默认 skip；需 cross-product 时改 Sub 或改 directionally orthogonal atoms（fundamental × 价量）。

### Rank-Diff Geometry 七律 + factor-anchored cluster

`Sub(CsRank(LHS), CsRank(RHS))` 是 csi1000 日频 cross-section 的**通用设计范式** —— 6 admit 跨 5 family 兑现（F015–F020），但 7 条硬约束：

1. **两端 scale-invariance**：LHS / RHS 必须都是 CV / ratio / correlation 等无量纲量；任一端 scale-dependent → 退化为主因子近重复
2. **raw field 独立**：两端不得共享 numerator 或 denominator raw field
3. **同字段跨窗口禁止**：`Sub(CsRank(X_20d), CsRank(X_5d))` rank 高度相关 cancellation
4. **Sub 方向对偶 dedup**：`Sub(A,B) = -Sub(B,A)` 数学完美反号，generator pre-dedup
5. **同批 LHS 共享 anchor rule**：同批 LHS 共享主信号端最多 admit 1
6. **RHS 共振饱和（动态）**：每 admit 一个 rank-diff 消耗一个 RHS 类目；**dead RHS endpoints**：`overnight_5 / turnover_5 / amount_20 / body_ratio_20 / price_vol_20 / circ_mktcap_60 / H_L_60_geo`
7. **factor-anchored cluster (LHS+RHS 双形态)**：4 已识别 anchor —— **F002**（value_liquidity，含 amount/turnover 分母 ±0.40–0.47 cluster）/ **F012**（microstructure 长窗 Amihud-numerator RHS ±0.69–0.73 negative cluster）/ **F020**（gap anti-anchor 同源 LHS 跨候选 -0.69 anti-cluster）/ **F022**（overnight close-position 仿射变体 / sign 离散化 0.82–0.93 cluster）；新候选起手 mandatory 4 anchor pre-check

**rank-diff 双阈值（direction-aware codified）**：`alpha_surv_min = 0.30`（rank-diff 通过 CsRank ordinal 映射损失 magnitude，Barra OLS residual 占比天然偏低）+ `incr_ic ≥ 0.015` 当 `max_corr ∈ [0.30, 0.70]` borderline。

**逃 cluster 启发**：higher-moment LHS independence axis（Std vs Mean of same atom）在 OHLC (F019) + gap (F020) 跨 family 复现；**单层** higher-moment 是 alpha 源头，**嵌套** compound moment 是 IS over-fit 源头（b052 C006 ls_t_is=12.18 → ls_t_oos=-0.13）。

**已证伪边界**：value_liquidity_interaction (b052 6/6) / intraday_price_formation (b053 5 reject) / barra_residual_alpha (b054 6/6) —— rank-diff 不能救 saturated 方向。

### OHLC Family Defaults（algebraic mirror trap）

A 股 daily-bar OHLC cross-section 几何上有两个**结构性共动约束**：
- **10% 涨跌幅约束** → `H / L / prev_close` 三 reference point 同时被夹紧 → `(VWAP-L)/(H-L)` / `gap/Std(ret,20)` / `range_norm × prev_close` 派生量与 F003/F014 cluster 79–96%
- **OHLC algebraic mirror**：`lower_shadow ≡ -upper_shadow`（corr=1.000@F006）；`signed_range` 与 `upper_shadow` corr=0.544；`(O+H+L+C)/4 ≈ close` → `(close - OHLC4_mean)/range ≈ 0 + noise`（hard_gate quad-fail）

**OHLC 派生 candidate 起手 3 步 algebraic 检查**：
(a) 是否与已 admit OHLC factor 在 `H-L` / `prev_close` / `OHLC4` 维度存在 affine 等价 → max_corr ≥ 0.85 必为 cluster；
(b) 是否两字段反相关镜像（lower vs upper / O-C vs C-O / signed vs abs）；
(c) 是否 multi-field arithmetic mean 退化形态（4-field mean ≈ close / 5-field mean ≈ vwap）

**单日对称抵消默认律**：单日 intraday OHLC 价格比率类（K线身体比 / 收盘位置 / close-open Corr）`mono_sign_flip` 是默认失效模式。**逃脱路径**：(a) 多日 smoothed/aggregated（5d sweet spot；upper-shadow [3d,7d] 稳，open-position 严格 5d-only）；(b) sign aggregation 配 underlying field persistent drift；(c) higher-moment（Std/Skew/Kurt）与 Mean-base 库因子构成独立轴

**In-batch denominator family 等价性自检（P024 升格 round 74，b077 首例铁证）**：仅分母不同的候选在常态下数学等价是 in-batch near-duplicate 浪费 Phase 2 计算预算。b077 C003 `TsRank((H-L)/(C+O),60)` 与 C006 `TsRank((H-L)/midprice,60)` IC daily corr=**0.9996**——`(C+O)≈(H+L)≈midprice×2≈OHLC4_mean×4` 在常态下数学近似（差异由日内 trend strength 决定，被 |Δclose|<10% 约束限幅）。**Phase 1 自检规则**：candidate atom 仅分母不同时检查分母在常态下数学等价性；同批 candidate 顶层 atom 仅分母不同 → 必计算两候选 IC daily corr，≥0.90 reject 一保留另一，≥0.99 in-batch duplicate 浪费。**等价类**：(C+O) ≈ (H+L) ≈ midprice×2 ≈ OHLC4_mean×4 ≈ close；Mean(close,N) ≈ EMA(close,M)；Mean($amount,N)/Mean($turnover_rate,N) cap-denominator 类。

### Rank-order ≠ Tradable Alpha 判别律（CP01–CP05 联合判读）

跨 ≥6 方向独立确认：候选若同时满足
- **(1)** `|ls_t| ≥ 2 + mono ≥ 0.7`（CP3 强）
- **(2)** `alpha_survival < 0.30` **或** `incremental_ic < 0` **或** `style_r² > 0.30` 中任一（CP4/CP5 弱）

→ 默认是 vol_20d / 反转簇 / library anchor 的 monotone derivative，**reject 而非 reserve**——除非含可证明独立的新几何（跨家族 rank-diff RHS / Python residual）。机理：rank-order 仅检验序结构，不检验 risk-adjusted PnL 的"独立性"——伪信号通常是已知风格因子的 monotone 变换。

**Library-reducer 复合 hard-block（第六要件，跨 ≥5 批独立确认）**：候选若同时满足 `mono_oos ≥ 0.85 + |ls_t_oos| ≥ 2.5 + incr_ic ≤ -0.005 + alpha_surv ≤ 0.30` → direct hard-block reject 标 `library_reducer`，不进 reserve。

**P008 软判定区 reject vs reserve 边界**（round 73-74 codified，b072 C005 vs C006 干净对照）：当 alpha_surv > 0.30 不触发 P006 hard_block 进入软判定：
- **默认 reject**：`incr_ic < 0 + max_corr ∈ [0.40, 0.50] borderline + 设计层无独立新几何`（b072 C005: Mul cross-product 已被 F009 pv_corr 同源 → reject）
- **reserve 火种**：`incr_ic < 0 但 max_corr < 0.30 LOW + 设计层含独立新几何（TsRank 时序量纲化 / 库内极少先例）+ style_r² 极清洁`（b072 C006: TsRank avg_trade_size 60d → reserve）

## Forbidden Patterns

generator 层 / Phase 1 freeze 应 pre-block 的设计反模式。

- **Rate / delta / ratio / sign-conditional / Cov 形式 default-skip**：跨 ≥6 方向独立证伪 —— `fundamental_momentum` (b022) / `return_momentum_acceleration` (b029) / `asymmetric_momentum` (b028) / `liquidity_acceleration` (b023+b032) / `pv_covariance` (b039 6/6 reject) / `return_distribution` Q90-Q10 (b016)。归簇 F001 amount_cv / F009 overnight_spread / F012 amihud 三反转载体。**Level 形式优越对照**：F010 hhi_vol_20 ls_t=7.50 整库记录 / F002 PB/amount level / F013 log(abnormal amount)。**例外**：(a) rank-diff Sub 对偶；(b) `Div(Delta(X), X)` 仅 sanity 检查可放行
- **TTM-quality / daily-aggregate-liquidity ratio default-skip**（round 69 升格，b068 实证）：`Div(TTM_quality, Mean($amount, N))` / `Div(TTM_quality, Mean($turnover_rate, N))` 形式（quality ∈ TTM ratio）默认被 vol_20d 吸收。证据：b068 C001 (ROE/Mean(amount,20)) vol_20d_exp=23.4 + C005 (gross_margin/Mean(turnover,20)) vol_20d_exp=31.1 整库历史最高。**Generator pre-check**：candidate 顶层 `Div`/`Mul` + numerator ∈ TTM quality 字段集 + denominator/operand ∈ daily liquidity aggregates → default-skip。**逃离正路径**：(a) numerator ∈ {pe/pb/ps/dividend_yield 已 Barra value basis 字段}；(b) Python OLS residualize TTM quality on (size, vol_20d) 后再 ratio；(c) TTM × TTM 内部交互（注意需 Python 包装规避 DSL Sub/Mul/Div 数据契约失败）
- **Higher-moment LHS / signed fundamental cross-product 四类 atom regime sign-flip**：跨 b052/b053/b054/b068 四 family 独立验证。**四类 atom**：
  1. **raw fundamental Std/Var**：`Std($pe_ratio,20)` / `Var($pb_ratio*$turnover_rate,60)`
  2. **raw intraday signed ratio higher-moment**：`Std((C-O)/close,20)`
  3. **residual higher-moment**：`Std(residual_ret,20)` / `Sum(residual_ret,5)`
  4. **signed fundamental cross-product**：`Mul($growth_TTM, Div(1, $value_PIT))` / GARP / growth × value_reciprocal blend；机理：growth_ttm 与 1/pe 在 2015-2021 同向 / 2022-2023 反向，乘积放大相位失配（b068 C004 train +0.0019 → val -0.004 sign_flip + decay -2.145）

  **触发条件**：(a) LHS 含 `Std/Var/Sum($X,N)` 且 `N≥20d`，X ∈ {raw fundamental, raw intraday signed ratio, residual_returns}；**或** (b) 顶层 `Mul`/`Div` + 两端 signed fundamental signal。**安全反例**：F019 `Std(body_ratio,20)` + F020 `Std(gap_ret,20)`（满足 scale-free ratio + N≤20d + 单层 moment）；F002 PB/amount level + F048 size × inverse_pe（单边 level + Barra basis-anchored）。**衍生律 (compound moment IS over-fit)**：嵌套 smooth-then-std (b052 C006 `Std(Mean(PB,5),20)`) ls_t_is=12.18 → ls_t_oos=-0.13 戏剧崩塌 —— hard_gate 已升格（见下）

- **Cov / Corr 长窗口协动 family csi1000 daily 真饱和**（round 74 升格，b075/b079/b039 三方向 dead 实证）：时间序列协动算子（Cov / Corr）在 csi1000 daily-bar 上无论 raw form 还是 TsRank-wrap 都被 vol_20d Barra basis 吸收——**形态独立性 ≠ alpha 独立性**。3 路径独立证伪：(a) **raw Cov(.,.,N) microstructure × valuation level**（b075 6/6 reject, alpha_surv 0.06–0.30 << 0.40, dom=vol_20d 全立）；(b) **TsRank-Corr 双重包裹**（b079 6/6 reject, 60d alpha_surv PASS 但 ic_oos sub-threshold <0.008, 120d sign_flip + ic≈0）；(c) **raw Cov(return-side)**（b039 6/6 reject, 撞 F001/F009/F012 反转簇）。机理：60d 协动 daily 1d primary horizon 信噪比天花板 ~0.006-0.007；120d 长周期信号反映 ≥半年级 macro/sector regime，daily 短期 alpha 时间尺度不符。**实操**：任何 Cov / Corr / TsRank-wrap-Corr 候选 N≥60d default-skip；复活路径仅 (a) 短窗 ≤20d（已被 b039 反转簇撞死）；(b) 非 daily-bar；(c) self-normalized ratio atom + N≤45d（F024/F025 已实证 ratio-form 是 Cov/Corr 替代）。**唯一火种**：b075 C006 `Cov($dividend_yield_ttm × $num_trades, 60)` risk-clean (alpha_surv=1.94) 但 ic 不足，不重测

- **Meta-pattern 跨方向机械迁移**：同一非线性变换在两个底层信号空间上效果完全相反。F013 log-compression 在 `gap_acceptance_structure` 把 sign×body mono_OOS 0.30→0.60 admit；同款 log 套到 value × liquidity (b038 6/6 IC_OOS 全负) / momentum gate (b037 6/6 reversal) / Cov 形态 (b039 6/6 reject)。**机制**：log 修复 sign×body 因 sign 已规整二值；log 救不了 value × liquidity 因 value 通道在 csi1000 已独立失效。**结构相同 ≠ 语义相同** —— 复用上一批成功 trick 必须先验底层 raw signal 在 csi1000 alive + trick 在新方向 underlying drift 同号；否则 hedge bet hypothesis 直接 dead

- **Rank-preserving 单算子包装**：见 Operator Registry 段。Generator AST hard_gate 预拦截 `f(F_admitted)`

**绝对不放宽的硬闸**：
- `hard_gate` 全局阈值（coverage / sign_flip / ic_oos_min / mono_flip / near_duplicate）—— **例外**：barra_residual_alpha coverage direction-aware 放宽到 0.70（数据契约层结构性下界，临时 workaround）
- 市值代理红线 `|corr($market_cap)| > 0.3`
- holdout 保护

**已升格 hard_gate**：
- **`is_oos_lst_collapse`**：`|ls_t_oos|/|ls_t_is| < 0.10 且 sign(is) ≠ sign(oos) 且 |ls_t_is| > 5.0` → reject 标 `compound_moment_collapse`
- **`library_reducer`**：见 Rank-order ≠ Tradable Alpha 段四要件
- **`corr_cov_field_safety`**（round 74 升格 candidate）：phase1 generator AST 检测 `Corr/Cov(A,B,N)` 节点，A/B 不双方在 Corr-safe 字段集 → 提前 reject 候选，error message `"Corr/Cov requires both fields in safe set"`；safe set = `{$close, $open, $high, $low, $volume, $amount, $num_trades}`

## csi1000 daily fundamental + institutional flow 真饱和（顶层 macro lesson）

**alpha 真饱和不是阈值过严**（round 73, b068-b072 5 路径独立证伪）：连续 5 批跨 4 直接 fundamental/institutional flow 方向（fundamental_quality_carry / pit_valuation_pure ×2 / python_ttm_residual_quality / institutional_flow_proxy）全部 0-admit。**5 独立失败路径**：

1. **路径 a — daily-aggregate liquidity ratio**（b068）：6/6 reject，4 thread DISPROVEN
2. **路径 b — PIT valuation rank composite**（b069/b070）：rank × rank Mul 仅当 RHS 含 1/PB 时 book basis 显化（b069 C006 reserve 火种 b/p=2.21）；PB → PE/PCF 替换 6/6 reject
3. **路径 c — Python OLS residualize TTM quality**（b071）：6/6 alpha_surv ∈ [0.93, 7.23] 全 PASS 但 6/6 OOS sign_flip
4. **路径 d — TTM aggregate signed signal**（b069 C003/C005）：`1/peg_ratio_ttm` + `1/pcf_total_ttm` 全 sign_flip
5. **路径 e — institutional flow microstructure**（b072）：raw level → F012 Amihud anchor (max_corr=0.75)；TsRank 60d (C006) 几何独立但 forward reversal + incr_ic NEG (-0.018) 仅 reserve

**Cov/Corr 长窗口协动扩展**（round 74，b075/b079）：cov_microstructure_valuation + cov_ratio_long_window 两方向 dead 加入同律——**Forward horizon h>1d 评估路径全库零兑现**：60d Cov daily 1d primary horizon 信噪比天花板 ~0.006-0.007，120d 信号 collapse。

**结论**：TTM quality / TTM valuation / institutional flow / long-window Cov/Corr 在 **csi1000 daily-bar 频率上不存在 OOS-stable cross-section alpha**——不是阈值过严，是 alpha 真饱和。**唯一未探路径**：minute/tick 数据 + 其它 universe (csi300/csi500)。当前 daily csi1000 不再分配预算到此族 frontier；direction allocation 转向 OHLC microstructure / intraday signals / Cov(liquidity, valuation_ratio) long-window family（F073/F074/F075 已 admit）+ 高阶 composition (F025) 第二阶 frontier。

### Composition Selection（rank × rank Mul 需 book yield basis）

**rank × rank Mul 复合需两端 atom 几何独立 + 至少一端 book yield basis 显化（b/p≥2）**（round 73, b069 C006 reserve + b070 RHS 替换 6/6 reject）：
- **book_to_price (1/PB)** 是 csi1000 cross-section **唯一同时具备** (a) cross-section dispersion 强 + (b) value Barra basis 抗 vol_20d 显化能力的 atom
- **PE/PCF/PEG** 在 ep_ratio basis 上有 dispersion 但缺 b/p basis 抗 vol_20d
- **充分但不必要**：`b/p ≥ 2 → ls_t ≥ 2`（b069 C006 b/p=2.21 ls_t=2.17）；`b/p<1.0 → ls_t<1.1`
- **Mul vs Sub 不对称律**：Mul 放大共有 basis（style_r²=0.578），Sub 抵消共有 basis（style_r²=0.23）

**实操**：rank × rank Mul 设计候选时，RHS 至少一端需为 1/PB 或带 book basis 衍生 atom。**衍生律**：跨族 (value × quality) Mul OOS regime drift 翻号是同律失败模式。

## Paper Transferability

`/factor-paper` skill 的 paper intake → direction 转化阶段必读。

- **Paper CSI 300 大盘 → csi1000 小盘 transfer 默认失败**：量级 8x+ 衰减是常态，方向翻号是常见结局
  - **gap_acceptance T001 paper Channel 1**（CSI 300 Rank IC 0.0744）→ csi1000 三窗口同步 sign_flip + 2015-2020 全正 / 2021-2023 全负完全反转；唯一存活 F013 IC_OOS=0.0094（**~8x 衰减**）
  - **trend_quality_gated paper Channel 3**（CSI 300 Rank IC 0.0590 + 0.0465）→ csi1000 6/6 IC_OOS 全负 (-0.025 ~ -0.033)，signal 完全翻转方向为 reversal
- **复刻 paper alpha 时硬约束**：(1) 必须先在 csi1000 上重测原始 raw signal 是否同号；(2) 若同号衰减 ≥ 5x 再考虑非线性压缩（log）；(3) 若翻号或单调性破坏，方向直接 dead
- **Sign aggregation underlying drift dependency**（三次对照确认）：sign-based aggregation 候选必须先验证 underlying field 的 drift 性质（rolling mean 显著非零）
  - F018 admit (b049 C006)：`Mean(Sign(overnight),20) × amount` ic_oos=+0.051 ls_t=+5.98 —— overnight 有 institutional accumulation drift
  - b050 C006 reject：`Mean(Sign(close-open),5) × pb_20` —— intraday body 是 random walk
  - b035 C001-C003 reject：pure `sign(gap) × sign(body)` 三窗口全 sign_flip
- **paper-driven candidate freeze 前必须 explicit 标注** `expected_decay_factor ≥ 5x for csi1000 transfer`

## Direction Lifecycle

方向状态机：`exploring → productive ↔ saturated → dead → archived`。

- **首批反向证伪 → 当批 dead（hedge-bet 方向尤其）**：复用上一批 admit 的 meta-pattern + 在新底层信号上重新包装 = hedge-bet 方向。**判别规则**：首批 (1) reject_rate ≥ 80% **且** (2) ≥2 候选独立命中 hard_gate (sign_flip / mono_sign_flip / IC_OOS 全反向) **且** (3) 失败机制非"窗口/算子细节"而是"信号方向与 hypothesis 反向" → 方向**当批 dead，priority 降到 low**。**例外**：方向若已成功 admit ≥ 1 因子，只是后续探索遇阻 → 转 saturated，不 dead
- **Saturated 双层证据律**：方向标 saturated 必须在 narrative 显式标注 (a) 信号设计层证据（≥2 路径 cluster / ≥3 candidate 几何不变量）+ (b) 数据契约层证据（Python residual coverage 实测 < 0.80 **或** Python 工具链未实现）。**(a)+(b) 同立** 才允许 saturated。**反向推论**：方向 reopen 前置条件必须显式列出"两层各自的解决路径"
- **`archived` 状态**：触发条件 = 元教训已被 ≥1 条 distillation finding 显式升格至 lessons.md + 方向 dead/saturated ≥30 天 + 无活跃 active thread。行为 = 方向 md 文件保留（历史可查），但 INDEX 不再列出，Phase 1 direction-selection 不再考虑。复活仅当 lessons.md 升格条目本身被推翻
- **当前批量 archive 提案（round 74 累积）**：return_distribution_signals / vol_shock_signals / quantile_shape_signals / trend_quality_gated / log_value_liquidity / pv_covariance / asymmetric_momentum / fundamental_momentum / return_momentum_acceleration / fundamental_quality_carry / **cov_microstructure_valuation**（round 74 加入，dead → archived）/ **cov_ratio_long_window**（round 74 加入，dead → archived）/ stochastic_position（saturated → archived）
- **2026-05-02 round 74 状态变更**：(a) **cov_microstructure_valuation** dead → archived（b075 6/6 reject 首批反向证伪；唯一火种 C006 已升格）；(b) **cov_ratio_long_window** dead → archived（b079 6/6 reject + P019 数据契约 + P018 边界扩展双律升格）；(c) **tsrank_candlestick_ratio** active → saturated（b077 三层续探全 reject，F025 absorbing prototype 已 cement）；(d) **reserve_revival_paths** 维持 active（audit-driven 工具方向，经验升格后 minor-path 可被 generator 预阻断）

## Metric Semantics

- **`ic.half_life_days`** —— **IC 衰减**半衰期。从多 horizon 的 train IC 曲线拟合，单位 = 持仓 horizon 天数。回答：alpha 随持仓期拉长衰减多快？
- **`feasibility.signal_half_life`** —— **signal 自相关**半衰期。每只标的信号 ACF 首阶跌到 0.5 的滞后，单位 = 交易日。回答：信号本身有多粘？
- **二者不可互换**。遗留的单名 `half_life` 字段已 deprecated

## Language Policy

- **叙事主体：中文**。Hypothesis / Current Focus / Narrative Log / 反思 / verdict 理由 / 跨候选对比 / Thread 推理全部中文
- **术语保留英文**：IC / ICIR / Sharpe / Barra / monotonicity / style_r² / alpha_survival / long_short / hard_gate / mt_bucket / admit / reserve / reject / exploring / productive / saturated / archived 等不翻译
- **YAML / frontmatter 值**：英文 snake_case
- **Markdown H2 标题**：英文（`## Hypothesis` / `## Threads` / `## CP01`…保持稳定便于 audit grep）
- **例外**：`INDEX.md` 上半段段落标题用中文

## Threshold Calibration

Thresholds 不是公理，是**可证伪的经验值**。

### 触发条件

任一满足即应审视当前阈值是否过严：
1. **连续零 admit**：同方向 ≥ 3 批次 0 admit 且每批有 reserve
2. **Reserve 积压**：累计 reserve / 累计 judged > 40% 且零 admit
3. **库规模停滞**：累计 batches ≥ 5 但 library size 未增 —— 检查 reject 理由是否都指向同一硬规则
4. **悖论复现**：同一"反直觉指标组合"在 ≥ 2 候选独立出现
5. **rank-diff paradigm 系统性错杀**：rank-diff 候选因 structural vol_20d exposure 在 alpha_surv ∈ [0.30, 0.40] 区间被默认 0.40 刷掉（已 codify 0.30 floor）

### 放宽的依据

- **Barra-clean ≠ library-clean**（跨 ≥4 方向独立确认）：CP04 测与 Barra 7-basis 几何关系；CP05 测与已 admitted 因子几何关系。错杀侦测必须**同时**满足 (a) max_corr<0.30 + (b) incr_ic>0.010 + (c) mono>0.8 + (d) sign_consistency=1.0
- **Portfolio-level orthogonalization**：多因子组合时 Barra 暴露可在 portfolio 层中和；单因子 Barra 脏 ≠ 不可用
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
    corr_cov_field_safety:           # round 74 升格 candidate
      enforce: true
      safe_fields: [$close, $open, $high, $low, $volume, $amount, $num_trades]
  incremental_ic:
    min_global: 0.003
    min_when_corr_borderline: 0.015
    corr_borderline_lower: 0.30
    corr_borderline_upper: 0.70
```

**rank-diff trigger**：candidate 若 LHS/RHS 都包含 `CsRank(...)` 且顶层算子是 `Sub` → 走 `rank_diff_geometry` 档；其余走 default。

**incr_ic borderline 律**：max_corr ∈ [0.30, 0.70] borderline 时，incr_ic ≥ 0.015 是 admission 必要条件。设计阶段若预估 max_corr 会落入 borderline，须设计能产生 ≥0.015 incr_ic 的独立 alpha 维度。

### 绝对不做的事

- **不放宽 hard_gate**（coverage / sign_flip / ic_oos_min / mono_flip / near_duplicate / library_reducer / is_oos_lst_collapse / corr_cov_field_safety）—— 例外仅 barra_residual_alpha coverage→0.70
- **不放宽市值代理红线** `|corr($market_cap)| > 0.3`
- **不放宽 holdout 保护**
- **不机械地在"连续零 admit"就放宽** —— 必须先诊断是否真的是"错杀"而非"信号确实都不够好"

### 历史校准记录

- **2026-04-19** (R1 → R1-relaxed)：`alpha_surv_min` 0.60 → 0.40；rubric CP04 poor 阈值 0.60 → 0.30；删除 `value_liquidity_interaction` direction.md 自设硬规则。追溯 admit F002 `pb_amount_ratio_20`
- **2026-04-25**：引入 3 条 direction-aware 阈值 —— `alpha_surv_min.rank_diff=0.30` / `min_coverage_by_direction.barra_residual_alpha=0.70` / `incr_ic.min_when_corr_borderline=0.015` + `corr_borderline=[0.30, 0.70]`
- **2026-04-27**：(a) rename `alpha_surv_min.rank_diff` → `rank_diff_geometry`；(b) 新增 hard_gate `is_oos_lst_collapse`；(c) 新增 hard_gate `library_reducer_hard_block`；(d) 升格 Rank-order ≠ Tradable Alpha；(e) 引入 Direction Lifecycle archived 状态 + 首批反向证伪 dead 律
- **2026-05-02 round 69**：**无阈值调整**。三条 lesson 升格非阈值类：(a) Forbidden Patterns 新增 "TTM-quality / daily-aggregate-liquidity ratio default-skip"；(b) Path Selection 新增 "TTM × TTM 直接 DSL Sub/Mul/Div 数据契约失败"；(c) Higher-moment regime sign-flip 段扩展第 4 类 atom "signed fundamental cross-product"
- **2026-05-02 round 73**：**无阈值调整**。5 条 lesson 升格：(a) Path Selection 新增 "alpha_survival ≥ 0.40 必须配 ic_by_year 后期同号 check"；(b) Path Selection "Linear OLS residualize 不破 vol_20d 非线性吸收"；(c) Path Selection "TsRank window≥60d on ratio fields 是新 vol_20d-escape 路径" + raw $num_trades 衍生律；(d) 新顶层 macro lesson "csi1000 daily fundamental + institutional flow 真饱和"；(e) "Composition Selection (rank × rank Mul 需 book yield basis)"
- **2026-05-02 round 74**：**新增 1 条 hard_gate candidate `corr_cov_field_safety`**（Generator AST 阶段阻断 cross-field Corr/Cov，safe set = OHLCV+num_trades 7 字段）。9 条 lesson 升格：(a) Data Facts 新增 "Qlib binary 数据契约 + Corr-safe/unsafe 字段集"（P019）；(b) Path Selection 新增 "Cap-denominator 隐藏 vol_20d 嵌入路径"（P016, b073/b074/b068 实证）；(c) Path Selection 新增 "Reserve revival 仅生还路径"（P025-P028, b078 6/6 reject 实证）；(d) Structural Constraints 新增 "Geometric absorbing-factor 律 + 高阶 composition 逃离路径"（F024/F025/F018/F021 实证）；(e) Structural Constraints 新增 "Cross-product Mul wrapper 系统性塌缩律"（b074/b077/b080 5+ 次跨方向）；(f) OHLC Family 段新增 "In-batch denominator family 等价性自检"（P024, b077 IC daily corr=0.9996 实证）；(g) Forbidden Patterns 新增 "Cov / Corr 长窗口协动 family 真饱和"（b075/b079/b039）；(h) "Rank-order ≠ Tradable Alpha" 段新增 "P008 软判定区 reject vs reserve 边界"（b072 C005/C006 干净对照）；(i) macro lesson 段加入 "Forward horizon h>1d 评估路径全库零兑现" + Cov/Corr 长窗口扩展。同步状态变更：cov_microstructure_valuation + cov_ratio_long_window dead→archived；tsrank_candlestick_ratio active→saturated。

## Promising Unexplored

> Phase 1 新开方向时参考。

- **高阶 composition (ratio-of-derived-quantity)**（round 74 新红利）：F025 shadow_asymmetry 是首例 vol_20d_exp=6.03 frontier 真生效顶级（ratio of two derived shadow lengths，分子分母同消 base scale + base volatility）；可在 OHLC body / range / shadow / overnight / gap family 复现
- **TsRank ≥60d on microstructure-only ratio fields**：F024 (num_trades/volume) admit 是 escape 路径首例；continuing on `Div(volume, $num_trades)`（mirror）已 disproven，但 cross-section dim-less ratio + microstructure-only 两端 + TsRank ≥60d 是新 frontier
- **Higher-moment LHS independence axis on scale-free OHLC ratios**：F019 (Std body_ratio,20) + F020 (Std gap_ret,20) 跨 OHLC×gap 两 family 独立兑现；可优先在 microstructure / overnight 两 productive 方向尝试同构 axis
- **Sign × persistent drift × non-linear weighting**：F018 + F013 是仅有的 sign-aggregation admit；分红 / 公告事件 / index inclusion 等具 persistent drift 的 underlying field 尚未尝试
- **Cross-section 算子 (CsRank/CsZscore/CsDemean) 替代 rolling**：解决 Python residual+rolling coverage=0.71 死路；residual 字段做 cross-section 二阶聚合可能绕开 coverage 硬闸
- **非 daily-bar 数据**（minute / tick）：vol_20d 吸收律的根本逃离路径；当前数据基础设施未就绪 —— 一旦支持，magnitude / quantile / power-mean 一整片 dead 方向可能复活；同时是 csi1000 daily fundamental 真饱和的唯一脱钩路径
