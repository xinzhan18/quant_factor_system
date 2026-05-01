---
version: 4
last_consolidated_at: 2026-04-27T00:00:00Z
source: Phase 5 consolidation — merged 13 specialist findings; codified rank-diff alpha_surv floor 0.30 / library-reducer hard-block / ls_t IS-OOS collapse hard_gate; introduced Direction Lifecycle (archived state + first-batch dead rule + saturated 双层证据律); promoted Rank-order ≠ Tradable Alpha 判别律
---

# Research Lessons

系统级硬事实。每次挖掘循环开始前必读。
由 Phase 5 CONSOLIDATION 周期性重写。**不要**在这里追加单 batch 的教训 —— 那些写在 `directions/{direction}.md`。

## Data Facts

- **Data split (不可违反)**:
  - Train: `[2015-01-01, 2021-12-31]`
  - Validation: `[2022-01-01, 2023-12-31]`
  - Holdout: `[2024-01-01, 2024-12-31]` —— Phase 2 / Phase 3 **永远看不到**，仅 `research holdout-review` 可读
  - 2025+：永不触碰
- **Primary universe = `all_tradable`**：CP01–CP06 全套判定在「全市场可交易股票日」上跑（`base_tradable ∧ load_universe_mask(primary)`，自 2026-04-25 mainline wiring 显式化），`csi300` / `csi1000` / `csi500` 仅作 robustness 参考，不进 verdict。`Phase2Inputs.universe` 作为 label 保留。
- **csi300 是 alpha 死区**：23 因子 retrofit 显示仅 7 个跨过 csi300 admission floor。大盘股被机构 arbitrage 压平 alpha 是常态 —— csi300_passes 仅作 robustness label，不否定因子在 all_tradable 的价值。
- **`$vwap` 全零**（当前数据源未填）—— precheck 禁用
- **`$amount` 有数据**，可用
- **`index_constituents` 表**：2.7M 行，含 `csi300` / `csi500` / `csi1000` 每日成分
- **A 股约束**：不做空头 alpha；因子必须从多头侧产生 alpha
- **市值代理红线**：`|corr|` > 0.3 对 `$market_cap` 或 `$circ_market_cap` 的因子直接 reject（size factor 已占 Barra basis，放宽 = 双重计数）
- **A 股 ±10% 涨跌幅约束**（影响因子设计）：`$high / $low / Ref($close,1)` 三个 reference point 同时被夹紧，使 `(H-L)/C` / `|gap|/range` / `gap/Std(ret,20)` 等"日内幅度归一"派生量 cross-section affine-like 共变 → 与已 admit 的 gap/VWAP 系列 (F003/F014) 80%+ cluster 是默认结局
- **Train→Validation regime 切换**：2015-2021 (低利率成长) → 2022-2023 (利率上行价值回归)。higher-moment LHS 在 raw fundamental / intraday signed / residual 字段上**系统性翻号**（见 Forbidden Patterns）
- **Tradable mask + ST 过滤改写历史 mono**：F003 / F010 / F011 旧版 (no ST mask) mono=1.0；加 PIT ST + 停牌 mask 后 mono 跌到 0.40 —— 原"持续性 carry"很大一块由 ST 股反向漂移撑起。**batch_010~025 整批 overnight persistence 候选系统性高估**。设计层硬约束：persistence / mean / cumsum 系列因子 freeze 阶段必须看 ST-filtered probe IC，不能信 raw probe。

## Operator Registry

- **白名单唯一**：DSL 算子 / 字段必须出现在 `src/research/phases/phase1_start.py:DSL_FIELD_WHITELIST`（single source of truth）
- **可用字段**（2026-05-01 扩展，新增 22 个基本面 / 微观字段）：
  - **价量**：`$open $high $low $close $volume $amount`
  - **微观**：`$turnover_rate $num_trades`（单日成交笔数）
  - **估值 PIT**：`$pe_ratio $pb_ratio $ps_ratio $pcf_ratio $market_cap $circ_market_cap`
  - **盈利 TTM**：`$return_on_equity_ttm $return_on_asset_ttm $return_on_invested_capital_ttm $gross_profit_margin_ttm $operating_profit_margin_ttm`
  - **偿债 TTM**：`$debt_to_asset_ratio_ttm $debt_to_equity_ratio_ttm $current_ratio_ttm`
  - **效率 TTM**：`$total_asset_turnover_ttm $inventory_turnover_ttm $account_receivable_turnover_rate_ttm`
  - **成长 TTM**：`$operating_revenue_growth_ratio_ttm $net_profit_growth_ratio_ttm $net_asset_growth_ratio_ttm`
  - **每股 / 收益率 TTM**：`$eps_ttm $book_value_per_share_ttm $operating_cash_flow_per_share_ttm $dividend_yield_ttm`
  - **估值 TTM**：`$pcf_ratio_total_ttm $peg_ratio_ttm`
  - **数据来源**：`ref_financials` (TTM, 米矿 get_factor 同步) / `ref_valuation` (PIT) / `ref_shares` (microstructure)；2026-05-01 同步全 11 年历史，~5500 股
  - **新方向提示**：基本面 TTM 因子与已饱和的 OHLCV 几何**完全独立**，不撞 vol_20d / F015/F017 anchor。优先尝试 quality (ROE/ROA/margins) × growth × leverage 类原子，与价量字段做 ratio / sub / interaction
- **自定义算子**（需要 `C.kernels = 1`）：`TsRank`, `TsMax`, `TsMin`, `TsAutoCorr`, `TsDecay`, `TsMomentum`, `RealizedVol`, `CsRank`, `CsZscore`, `CsDemean`, `AmihudIlliq`, `HHI`, `SignedPower`, `Tanh`, `Exp`, `Sigmoid`
- **禁用算子**：`Neg`（用 `Mul($x, -1)`），`SMA`（用 `EMA` 或 `Mean`）
- **横截面算子**（`CsRank` / `CsZscore` / `CsDemean`）无论挖掘 universe 是什么，始终在 `D.instruments("all")` 上计算
- **Rank-preserving 单算子变体零增量律**：DSL `{Linear, SignedPower(p>0), Sigmoid, Tanh, Exp, Softmax, CsZscore, Scale}` 包装单已 admit 因子 → cross-section rank 完全保留 → max_corr ≈ 1.000 必为 near_duplicate（b031 C004 CsZscore(F012) / b046 C005 SignedPower(F012,0.5) 双独立 1.000 证伪）。Generator AST 层硬阻断 `f(F_admitted)`。
- **DSL Div / Mul 不是真 orthogonalization**：`Div(factor, vol_proxy)` / `Div(factor, turnover_mean)` 要么保序、要么仅是 style exposure 搬家（b031 C002/C003：vol exposure 5.9→32.6 或 alpha_survival 塌 69%）；`Div`-based cross-field 与 `Mul` 撞同样量纲吞噬。真 orthogonalization 必走 Python OLS / Barra residual。

## Path Selection

- **默认走 DSL**（R8）。Python 逃生口仅在下列情况触发：DSL 无法向量化的非平凡循环 / DSL 表达不了的横截面操作 / 对已发表 Python 参考实现的显式复刻
- **Python factor 契约**：
  - 签名：`def compute(df: pd.DataFrame) -> pd.Series`，df MultiIndex = `(time, symbol)`
  - 模块级 `REQUIRED_FIELDS: list[str]` 和 `VECTORIZED: bool = True`
  - 纯函数，不碰 I/O / DB / 网络
  - 导入白名单：`numpy`, `pandas`, `scipy`；禁用：`subprocess`, `os`, `sys`, `eval`, `open`
- **REQUIRED_FIELDS 必须 ⊆ loader 默认列**：`data_bridge.load_market_data` 默认列 = `$amount, $market_cap, $close, $volume, $open, $high, $low`。**不包含 `$turnover_rate` / `$pe_ratio` / `$pb_ratio` / `$ps_ratio`**。Phase 1 freeze 必须 static validate；否则 compute_error: market_df missing（b015 missing $high/$low → b054 missing $turnover_rate 9 批后跨 direction 二次复现，系统级修复 priority high）
- **Python residual + rolling 在 csi1000 系统性 coverage ≈ 0.71**（数据契约层结构性下界）：cross-sectional Barra residual ~1% NaN（style 缺失传播）+ rolling min_periods≥10 + csi1000 上市日异质性 → 三因子复合后 coverage 0.685–0.725，与 0.80 hard_gate 结构性不兼容。跨 amount_volatility (b033 5/5) / value_liquidity (b034 5/5) / barra_residual (b054 5/5) 三方向 15+ 候选独立确认。**信号常常健康** (b034 C005 alpha_surv=1.20 / b054 C005 alpha_surv=1.57 + style_r²=0.024 极清洁) 仅 coverage gate KO。修复路径：(a) cross-sectional 算子代替 rolling（CsRank/CsZscore 不需 min_periods）；(b) loader 端 forward-fill / industry-mean fill；(c) direction-aware coverage 阈值放宽到 0.70（仅限 barra_residual_alpha，临时 workaround）
- **Python 因子源代码必须走代码版本控制，不放 immutable archive**：admitted python 因子的"运行时入口"应在 `storage/python_factors/F{id}_*.py`（被代码 PR 流程跟踪），`vault/batches/.../python_candidates/` 副本仅作历史快照。F004/F005 第一轮失败因为 scipy `pinv` 的 `rcond=` API 在 1.7+ 已被 `rtol=` 替代，archive 拷贝没跟进。

## Structural Constraints

- **禁看 holdout**：Phase 2 / Phase 3 代码永远不能读 2024 年数据。Holdout 物理隔离在 `storage/_holdout_private/`
- **向量化（R5）**：禁止行 / 日期 / 标的 `for` 循环。用 `groupby` / broadcasting / `einsum` / `np.linalg.pinv`；同样禁用 `groupby.transform`（隐式按日期 for 循环）。标准套路：long → wide pivot → 在 `(n_dates × n_symbols)` 矩阵上做 row-level numpy 运算 → wide → long
- **Barra residual 基线**：因子 alpha 是在**剥离 Barra 风格暴露之后**度量的。`style_r²` 和 `alpha_survival` 是 CP04 Risk Cleanness 的核心指标。**alpha_survival 比 style_r² 更敏感** —— 当 dominant_style=vol_20d 时优先看 alpha_survival（b056 C006 案例：style_r²=0.21 仅 borderline 但 alpha_survival=0.0725 极端 poor）
- **冗余红线（CP05）**：对已 admitted 因子的 `max_lib_corr > 0.70` 直接 reject
- **Python 因子必须进 library 对比**：`data_bridge.load_library_signals` 同时覆盖 DSL + Python 两种源类型（按 `sha256(源码)` 缓存）。任何护栏新增源类型时，redundancy / incremental_ic / 指标计算三路径必须同步覆盖
- **Sample policy 版本**：`config.yaml` 升级 `sample_policy_version`（`v3 → v4`）会重置 §7.MT 多重检验预算的 `validation_exposure` 计数 —— 不要轻易升
- **Multi-universe schema 是新基线**：`validation_metrics_by_universe` 自动写入三 universe (`all_tradable` primary + `csi300/csi1000` secondary basic) + `universe_robustness` summary + `recompute_provenance`（仅 retrofit 因子）
- **Library recompute self 检测必须空 library_signals**：批量重算整库时若仍走 `data_bridge.load_library_signals`，每个因子跟自己 / 同 family 因子做 redundancy 检测，结果 `is_near_duplicate=True` 全部触发 hard_gate fail。recompute 时手动 `inputs.library_signals = {}`。
- **`revalidated_in_batch` ≠ `admitted_in_batch`**：report builder (`render_factor`) 必须读 `meta.get("revalidated_in_batch") or meta["admitted_in_batch"]`。admit 历史保留在 `admitted_in_batch` 作 audit trail，不可覆盖。
- **DB `factor_values` 表已 DROP**：`factor_001..factor_045` 是 mining_v1 时代命名，跟当前 F-命名不对应。当前 Phase 2 不读 DB（用 sha256-keyed parquet cache + 即算即用）。

### vol_20d 结构性吸收律（≥9-direction 顶级失败律）

csi1000 daily-bar cross-section 几何被 Barra `vol_20d` 占据 2nd-moment 空间。任何 magnitude / ratio / power-mean / Std / Var / quantile / IQR 形态——无论作用于 return / range / amount / turnover / OHLC ratio——cross-section rank 都 monotone-equivalent 到 vol_20d，alpha_survival 典型 0.08–0.30。

**机理**：A 股 ±10% 涨跌幅 + 小盘散户主导，使 `|daily_return|` / `(H-L)/C` / `$amount` 的 std/CV / Quantile 差 / Skew/Kurt 在 cross-section 上高度同构。Robust estimator (Quantile/Median) 的 outlier-robust 性 **不等于** Barra vol_20d orthogonality。

**判别规则（reject）**：`dominant_style=vol_20d` + `style_r² > 0.30` + `alpha_survival < 0.30` 三者同立 → 直接 reject，切换设计轴。

**逃离路径仅四条**：(a) Python Barra residual orthogonalize（受 coverage<0.80 限制）；(b) 非 daily-bar 数据（minute/tick）；(c) 非 magnitude 几何 —— sign 聚合 (F018) / rank-diff cross-family (F015–F020) / higher-moment 单层（F019/F020 仅当 `mono_is≥0.6` + scale-free RHS）；(d) overnight 段独立分解 (F009–F011)。

**证据链**：≥9 方向独立确认 —— return_distribution_signals (b016) / vol_shock_signals (b024) / amount_volatility_signal (b033 19/19 dom=vol_20d) / stochastic_position (b041 6/6 exposure 8.7–16.5) / range_structure (b043+b045+b055+b056) / quantile_shape_signals (b044 4/6 exp 27–42) / intraday_price_formation (b053 style_r²=0.66) / turnover_structural_signal (b004 5/5) / vwap_proxy_signals (b057 C003 vol_20d=48.04 整库新高)。

### Rank-Diff Geometry 七律 + factor-anchored cluster

`Sub(CsRank(LHS), CsRank(RHS))` 是 csi1000 日频 cross-section 的**通用设计范式** —— 6 admit 跨 5 family 兑现（F015 microstructure × amount_CV / F016 microstructure × turnover_CV / F017 overnight × turnover / F018 overnight_sign × amount / F019 OHLC body higher-moment × price_vol / F020 gap higher-moment × body_ratio），但**不是万能钥匙**。新候选必须通过 7 条硬约束：

1. **两端 scale-invariance**：LHS / RHS 必须都是 CV / ratio / correlation 等**无量纲量**；任一端 scale-dependent (Std/Mean/绝对 level) → 退化为主因子近重复（b046 C004 corr=0.935@F012）
2. **raw field 独立**：两端不得共享 numerator 或 denominator raw field；`$amount` 共分母让 Sub 抵消 → noise（b047 C002 / b048 C002）
3. **同字段跨窗口禁止**：`Sub(CsRank(X_20d), CsRank(X_5d))` rank 高度相关 cancellation（b048 C005 ic=-0.0014）
4. **Sub 方向对偶 dedup**：`Sub(A,B) = -Sub(B,A)` 数学完美反号，generator pre-dedup（b047 C001/C004）
5. **同批 LHS 共享 anchor rule**：同批候选若 LHS 共享主信号端，最多 admit 1
6. **RHS 共振饱和（动态）**：每 admit 一个 rank-diff 因子消耗一个 RHS 类目 —— **dead RHS endpoints（持续累积）**：`overnight_5 / turnover_5 / amount_20 / body_ratio_20 / price_vol_20 / circ_mktcap_60 / H_L_60_geo`（b049/b055/b059 升格）；新候选必须验证 RHS 不在死亡名单
7. **factor-anchored cluster (LHS+RHS 双形态)**：saturated 方向 anchor factor 在 cross-section 上结构性占据中心。**4 已识别 anchor**：F002（value_liquidity，含 amount/turnover 分母 ±0.40–0.47 cluster）/ F012（microstructure 长窗 Amihud-numerator RHS ±0.69–0.73 negative cluster）/ F020（gap anti-anchor 同源 LHS 跨候选 -0.69 anti-cluster）/ F022（overnight close-position 仿射变体 / sign 离散化 0.82–0.93 cluster）。新候选起手 mandatory 4 anchor pre-check。

**rank-diff 双阈值（direction-aware，已 codify）**：`alpha_surv_min = 0.30`（rank-diff 通过 CsRank ordinal 映射损失 magnitude，Barra OLS residual 占比天然偏低；F015–F020 admit 实际 alpha_surv 历史范围 0.30–0.55，default=0.40 系统性错杀）+ `incr_ic ≥ 0.015` 当 `max_corr ∈ [0.30, 0.70]` borderline（cluster co-resonance 死区）。证据：b047 C001 (max_corr=0.734, incr=0.023) admit ✓ / b049 C004 (max_corr=0.725, incr=0.004) reject ✓ / b056 C001/C004 retroactive 候选。

**逃 cluster 启发**：**higher-moment LHS independence axis**（Std vs Mean of same atom）在 OHLC (F019) + gap (F020) 跨 family 复现。**单层** higher-moment 是 alpha 源头，**嵌套** compound moment（smooth-then-std, b052 C006）是 IS over-fit 源头（ls_t_is=12.18 → ls_t_oos=-0.13 戏剧崩塌）。

**已证伪边界**：value_liquidity_interaction (b052 6/6) / intraday_price_formation (b053 5 reject) / barra_residual_alpha (b054 6/6) —— rank-diff 不能救 saturated 方向。

### OHLC Family Defaults（algebraic mirror trap）

A 股 daily-bar OHLC 字段 cross-section 几何上有两个**结构性共动约束**：

- **10% 涨跌幅约束** → `H / L / prev_close` 三 reference point 同时被夹紧 → `(VWAP-L)/(H-L)` / `gap/Std(ret,20)` / `range_norm × prev_close 派生量` 与 F003 / F014 cluster 79–96%（b035 C005 corr=0.964 / b042 C001-C006 max_corr 0.79–0.89 / b051 C005 max_corr=0.696）
- **OHLC algebraic mirror**：
  - `lower_shadow ≡ -upper_shadow`（b018 C001 corr=1.000@F006）
  - `signed_range` 与 `upper_shadow` corr=0.544
  - `(O+H+L+C)/4 ≈ close`（csi1000 上四字段集中度高），任何 `(close - OHLC4_mean)/range ≈ 0 + noise`（b053 C002 hard_gate quad-fail）

**OHLC 派生 candidate 起手前必做 3 步 algebraic 检查**：
(a) 是否与已 admit OHLC factor (F003/F006/F007/F008/F014/F019/F020) 在 `H-L` / `prev_close` / `OHLC4` 维度存在 affine 等价 → max_corr ≥ 0.85 必为 cluster；
(b) 是否两字段反相关镜像（lower vs upper / O-C vs C-O / signed vs abs）；
(c) 是否 multi-field arithmetic mean 退化形态（4-field mean ≈ close / 5-field mean ≈ vwap）。

**单日对称抵消默认律**：单日 intraday OHLC 价格比率类（K线身体比 / 收盘位置 / close-open Corr）`mono_sign_flip` 是**默认失效模式**（日内多空力量在中长期持有中对称抵消）。**逃脱路径**：
- 多日 smoothed/aggregated 版本（5d sweet spot；upper-shadow [3d,7d] 稳，open-position **严格 5d-only**，≥10d 跨 phase 反转）
- sign aggregation 配 underlying field persistent drift（overnight 有 institutional accumulation drift → F018 admit；intraday body 是 random walk → b035/b037/b050 C006 三次证伪）
- higher-moment（Std/Skew/Kurt of OHLC ratios）与 Mean-base 库因子构成独立轴

**canonical de-dup**：generator 层应识别 affine-equivalent expression（C002 = C001 - 0.5 in b042 导致 metrics 六位小数恒等）—— pre-pack 阶段就该拦截。

### Rank-order ≠ Tradable Alpha 判别律（CP01–CP05 联合判读）

跨 ≥6 方向独立确认（return_distribution / vol_shock / value_liquidity / quantile_shape / intraday_price_formation / turnover_structural）：候选若同时满足
- **(1)** `|ls_t| ≥ 2 + mono ≥ 0.7`（CP3 强）
- **(2)** `alpha_survival < 0.30` **或** `incremental_ic < 0` **或** `style_r² > 0.30` 中任一（CP4/CP5 弱）

→ 默认是 vol_20d / 反转簇 / library anchor 的 monotone derivative，**reject 而非 reserve**——除非该候选含可证明独立的新几何（跨家族 rank-diff RHS / Python residual）。**机理**：rank-order 仅检验序结构，不检验 risk-adjusted PnL 的"独立性"——伪信号通常是已知风格因子的 monotone 变换，序结构传递但 risk-adjusted 价值已被库吞噬。判别律每方向首批 judge 节省 ~30% reserve 占位。

**Library-reducer 复合 hard-block（第六要件，跨 ≥5 批独立确认）**：候选若同时满足
- `mono_oos ≥ 0.85` + `|ls_t_oos| ≥ 2.5` + `incr_ic ≤ -0.005` + `alpha_surv ≤ 0.30`

→ direct hard-block reject 标 `library_reducer`，不进 reserve。机理：rank-diff factor 即使 max_corr 看似独立，多个 RHS 通过 vol_20d common cause 仍构成"组合层冗余"。证据：b042 C005 / b043 C005-C006 / b045 C006 / b055 C002 / b056 C004 六次独立复现。

## Forbidden Patterns

generator 层 / Phase 1 freeze 应 pre-block 的设计反模式。

- **Rate / delta / ratio / sign-conditional / Cov 形式 default-skip**：一阶 / 二阶变化率 / Cov 协动 / sign-conditional 拆分跨 ≥6 方向独立证伪 —— `fundamental_momentum` (b022 PE/PB/PS rate ls_t=-1.22~-1.81) / `return_momentum_acceleration` (b029 spread/ratio/delta 全 weak) / `asymmetric_momentum` (b028 3/3 hard_gate sign_flip) / `liquidity_acceleration` (b023+b032 9 候选全 reserve, 被 F001 吸收) / `pv_covariance` (b039 6/6 reject) / `return_distribution` Q90-Q10 (b016)。归簇 F001 amount_cv / F009 overnight_spread / F012 amihud 三反转载体。**Level 形式优越对照**：F010 hhi_vol_20 ls_t=**7.50** 整库记录 / F002 PB/amount level / F013 log(abnormal amount) 非线性压缩。**例外**：(a) rank-diff Sub 对偶（不是 rate 而是对称 ordinal 差）；(b) `Div(Delta(X), X)` 仅做 rank-order sanity 检查时可放行。
- **Higher-moment LHS 在 raw fundamental / intraday signed / residual 三类 atom 上 regime sign-flip**：`Std($pe_ratio,20)` / `Var($pb_ratio*$turnover_rate,60)` / `Std((C-O)/close,20)` / `Std(residual_ret,20)` / `Sum(residual_ret,5)` 在 csi1000 train→validation regime 切换中**几何反向**。跨 b052 (fundamental) / b053 (intraday) / b054 (residual) 三 family 5 候选独立验证。**触发条件**：LHS 含 `Std/Var/Sum($X,N)` 且 `N≥20d`，X ∈ {raw fundamental PE/PB/PS, raw intraday signed ratio, residual_returns}。**安全反例**：F019 `Std(body_ratio,20)` + F020 `Std(gap_ret,20)` —— 满足 (a) scale-free ratio 字段 + (b) 窗口 ≤20d + (c) 单层 moment（非嵌套 compound moment）。**衍生律（compound moment IS over-fit）**：嵌套 smooth-then-std (b052 C006 `Std(Mean(PB,5),20)`) ls_t_is=12.18 → ls_t_oos=-0.13 戏剧崩塌 —— 已升格 hard_gate（见下）。
- **Meta-pattern 跨方向机械迁移**：同一非线性变换在两个底层信号空间上效果完全相反。F013 log-compression 在 `gap_acceptance_structure` 把 sign×body mono_OOS 0.30→0.60 admit；同款 log 套到 value × liquidity (b038 6/6 IC_OOS 全负) / momentum gate (b037 6/6 reversal) / Cov 形态 (b039 6/6 reject)。**机制**：log 修复 sign×body 因 sign 已规整二值；log 救不了 value × liquidity 因 value 通道在 csi1000 已独立失效。**结构相同 ≠ 语义相同** —— 复用上一批成功 trick 必须先验底层 raw signal 在 csi1000 alive + trick 在新方向 underlying drift 同号；否则 hedge bet hypothesis 直接 dead（见 Direction Lifecycle）。
- **Rank-preserving 单算子包装**：见 Operator Registry 段。Generator AST hard_gate 预拦截 `f(F_admitted)`。

**绝对不放宽的硬闸**（Forbidden Patterns 不能跨过）：
- `hard_gate` 全局阈值（coverage / sign_flip / ic_oos_min / mono_flip / near_duplicate）—— CP01 硬闸是数据质量 + 结构完整性的物理边界，放宽 = 让垃圾入库。**例外**：barra_residual_alpha 方向 coverage direction-aware 放宽到 0.70（数据契约层结构性下界，临时 workaround）
- 市值代理红线 `|corr($market_cap)| > 0.3`
- holdout 保护

**新增 hard_gate（已升格）**：
- **`is_oos_lst_collapse`** —— `|ls_t_oos|/|ls_t_is| < 0.10 且 sign(is) ≠ sign(oos) 且 |ls_t_is| > 5.0` → hard_gate reject，标 `compound_moment_collapse`。仅 b052 C006 历史命中，但律已 3-family 确认（fundamental/intraday/residual），路径精准定向不误伤其他候选。
- **`library_reducer`** —— 见 Rank-order ≠ Tradable Alpha 段四要件。

## Paper Transferability

`/factor-paper` skill 的 paper intake → direction 转化阶段必读。

- **Paper CSI 300 大盘 → csi1000 小盘 transfer 默认失败**：量级 8x+ 衰减是常态，方向翻号是常见结局。两次独立确认 ——
  - **gap_acceptance T001 paper Channel 1**（sign×sign acceptance, CSI 300 Rank IC 0.0744）→ csi1000 三窗口同步 sign_flip + 2015-2020 全正 / 2021-2023 全负完全反转；唯一存活 F013 log(abnormal amount) 加权且 IC_OOS=0.0094（**~8x 衰减**）
  - **trend_quality_gated paper Channel 3**（CleanTrend / OrderlyTrend, CSI 300 Rank IC 0.0590 + 0.0465）→ csi1000 6/6 IC_OOS 全负 (-0.025 ~ -0.033)，signal **完全翻转方向为 reversal**；无任何 gate 变体可救
- **复刻 paper alpha 时硬约束**：
  1. 必须先在 csi1000 上重测原始 raw signal 是否同号；
  2. 若同号衰减 ≥ 5x，再考虑非线性压缩（如 log，参考 F013）抢救；
  3. 若翻号或单调性破坏，方向直接 dead，不要再用 gate / 加权抢救。
- **Sign aggregation underlying drift dependency**（三次对照确认）：sign-based aggregation 候选必须先验证 underlying field 的 drift 性质（rolling mean 显著非零）。
  - F018 admit (b049 C006)：`Mean(Sign(overnight),20) × amount` ic_oos=+0.051 ls_t=+5.98 —— overnight 有 **institutional accumulation drift**
  - b050 C006 reject：`Mean(Sign(close-open),5) × pb_20` —— intraday body 是 **random walk**
  - b035 C001-C003 reject：pure `sign(gap) × sign(body)` 三窗口全 sign_flip —— gap sign 在 csi1000 也 noise 主导，需 amount weighting drift proxy 才能复活（F013）
- **paper-driven candidate freeze 前必须 explicit 标注** `expected_decay_factor ≥ 5x for csi1000 transfer`。

## Direction Lifecycle

方向状态机：`exploring → productive ↔ saturated → dead → archived`。

- **首批反向证伪 → 当批 dead（hedge-bet 方向尤其）**：复用上一批 admit 的 meta-pattern + 在新底层信号上重新包装 = hedge-bet 方向。**判别规则**：首批 (1) reject_rate ≥ 80% **且** (2) ≥2 候选独立命中 hard_gate (sign_flip / mono_sign_flip / IC_OOS 全反向) **且** (3) 失败机制非"窗口/算子细节"而是"信号方向与 hypothesis 反向" → 方向**当批 dead，priority 降到 low**，不允许同 hypothesis 第二批微调。**例外**：方向若已成功 admit ≥ 1 因子，只是后续探索遇阻 → 转 saturated，不 dead。证据：log_value_liquidity (b038) / trend_quality_gated (b037) / pv_covariance (b039) / asymmetric_momentum (b028) 4 方向独立得出。
- **Saturated 双层证据律**：方向标 saturated 必须在 narrative 显式标注 (a) 信号设计层证据（≥2 路径 cluster / ≥3 candidate 几何不变量）+ (b) 数据契约层证据（Python residual coverage 实测 < 0.80 **或** Python 工具链未实现）。**只有 (a) 而未触 (b)** → 标 productive (rounds≤2) 或 exploring，不进 saturated。**(a)+(b) 同立** 才允许 saturated。**反向推论**：方向 reopen 前置条件必须显式列出"两层各自的解决路径"（如：信号设计层换 frequency / 跨 family rank-diff；数据契约层 cross-sectional 算子代替 rolling / loader 端预填充 NaN）。证据：barra_residual_alpha / amount_volatility_signal / value_liquidity_interaction / turnover_structural_signal 4 方向。
- **`archived` 状态（新增）**：触发条件 = 元教训已被 ≥1 条 distillation finding 显式升格至 lessons.md + 方向 dead/saturated ≥30 天 + 无活跃 active thread。行为 = 方向 md 文件保留（历史可查），但 INDEX 不再列出，Phase 1 direction-selection 不再考虑，snapshot 不再 enumerate。复活仅当 lessons.md 升格条目本身被推翻（如 minute-bar 数据接入推翻 vol_20d 吸收律）。**当前批量 archive 提案（10 方向，由 orchestrator 审定）**：return_distribution_signals / vol_shock_signals / quantile_shape_signals / trend_quality_gated / log_value_liquidity / pv_covariance / asymmetric_momentum / fundamental_momentum / return_momentum_acceleration（dead → archived）+ stochastic_position（saturated → archived）。

## Metric Semantics

- **`ic.half_life_days`** —— **IC 衰减**半衰期。从多 horizon 的 train IC 曲线拟合，单位 = 持仓 horizon 天数。回答：alpha 随持仓期拉长衰减多快？
- **`feasibility.signal_half_life`** —— **signal 自相关**半衰期。每只标的信号 ACF 首阶跌到 0.5 的滞后，单位 = 交易日。回答：信号本身有多粘？
- **二者不可互换**。遗留的单名 `half_life` 字段已 deprecated

## Language Policy

vault 文档（INDEX / directions / judge / candidates / factor reports / narrative log）写作规则：

- **叙事主体：中文**。Hypothesis / Current Focus / Narrative Log / 反思 / verdict 理由 / 跨候选对比 / Thread 推理全部中文
- **术语保留英文**：IC / ICIR / Sharpe / Barra / monotonicity / style_r² / alpha_survival / long_short / hard_gate / mt_bucket / admit / reserve / reject / exploring / productive / saturated / archived 等技术词不翻译
- **YAML / frontmatter 值**：英文 snake_case（机器优先）
- **Markdown H2 标题**：英文（`## Hypothesis` / `## Threads` / `## CP01`…保持稳定便于 audit grep）
- **例外**：`INDEX.md` 上半段段落标题（`## 活跃方向` / `## 最近 Batch` / `## 因子库`）用中文，这是人看的总览页

段落内部可自然夹英文术语，但不要整段英文 prose 夹杂整段中文。

## Threshold Calibration

Thresholds 不是公理，是**可证伪的经验值**。系统运行中若发现自己**系统性错杀**某一类候选，必须主动触发校准 —— 避免"本地最优陷入局部搜索死循环"的关键机制。

### 触发条件

任一满足即应审视当前阈值是否过严：

1. **连续零 admit**：同方向 ≥ 3 批次 0 admit 且每批有 reserve，检查 reserve 中是否存在"rank-order 完美 + 库空间独立"但被**单指标 dealbreaker** 杀掉的
2. **Reserve 积压**：累计 reserve / 累计 judged > 40% 且零 admit
3. **库规模停滞**：累计 batches ≥ 5 但 library size 未增 —— 检查 reject 理由是否都指向同一个硬规则（direction-level 自设规则嫌疑最大）
4. **悖论复现**：同一"反直觉指标组合"在 ≥ 2 个候选独立出现（如"低 style_r² + 低 alpha_survival"），说明单指标阈值不能表达问题全貌
5. **rank-diff paradigm 系统性错杀**：rank-diff 候选因 structural vol_20d exposure 在 alpha_surv ∈ [0.30, 0.40] 区间被默认阈值 0.40 刷掉 —— 是真实 alpha + 必然 style coupling，不是信号弱（已 codify 0.30 floor）

### 放宽的依据

- **Barra-clean ≠ library-clean**（跨 ≥4 方向独立确认）：CP04 测与 **Barra 7-basis 的几何关系**；CP05 测与**已 admitted 因子的几何关系**。两个正交维度 —— alpha_survival 高 (>0.7) **不蕴含** library independence。错杀侦测必须**同时**满足 (a) max_corr<0.30 + (b) incr_ic>0.010 + (c) mono>0.8 + (d) sign_consistency=1.0 才 flag —— 单维度强不触发 retroactive admit
- **Portfolio-level orthogonalization**：多因子组合构建时 Barra 暴露可在 portfolio 层中和；单因子 Barra 脏 ≠ 不可用
- **"Static vs dynamic orthogonal" 悖论**：低 `style_r²` 说明因子值横截面 ⊥ Barra basis；低 `alpha_survival` 说明 IC 生成的 L/S weights ∈ span(Barra)。二者可共存 —— 对 library 增值判断的优先依据是**符号互补性 + 相关正交性**，不是 Barra residual 纯度
- **硬规则 auto-reject 粒度过粗**：`alpha_survival < X 一律 reject` 把"rank 完美 + 9 年同号 + 符号唯一"的真实 alpha 与"regime-dep 跨期翻号"同等处理，失去判断分辨率

### Direction-aware 阈值（已生效）

```yaml
# storage/config.yaml
thresholds:
  alpha_surv_min:
    default: 0.40
    barra_residual_alpha: 1.00       # residual IS the alpha
    amount_volatility_signal: 0.25
    value_liquidity_interaction: 0.30
    rank_diff_geometry: 0.30          # rank-diff structural vol_20d exposure 不可避（codified from b057 informal floor）
  hard_gates:
    min_coverage: 0.80
    min_coverage_by_direction:
      barra_residual_alpha: 0.70      # 数据契约层结构性下界, 临时 workaround
    is_oos_lst_collapse:               # NEW (compound moment IS over-fit catcher)
      max_ratio_with_sign_flip: 0.10
      min_lst_is_abs: 5.0
    library_reducer_hard_block:        # NEW (跨 5 批独立确认 signature)
      enabled: true
      mono_oos_min_abs: 0.85
      ls_t_oos_min_abs: 2.5
      incr_ic_max: -0.005
      alpha_surv_max: 0.30
  incremental_ic:
    min_global: 0.003
    min_when_corr_borderline: 0.015   # max_lib_corr ∈ [0.30, 0.70] borderline 区间必备
    corr_borderline_lower: 0.30
    corr_borderline_upper: 0.70
```

**rank-diff trigger**：candidate 若 LHS/RHS 都包含 `CsRank(...)` 且顶层算子是 `Sub` → 走 `rank_diff_geometry` 档；其余走 default。

**incr_ic borderline 律**：max_corr ∈ [0.30, 0.70] borderline 时，incr_ic ≥ 0.015 是 admission 必要条件（低于此值入库即近似复制 + 噪声）。设计阶段若预估 max_corr 会落入 borderline，须设计能产生 ≥0.015 incr_ic 的独立 alpha 维度 —— 通常是 (a) 跨 family LHS+RHS 全新组合 (b) higher-moment LHS (Std vs Mean) 切换 (c) sign 聚合 vs magnitude 聚合切换。证据：b047 C001 admit ✓ / b049 C004 reject ✓ / b050 C001 reserve ✓。

### 执行流程

**Step 1 — 诊断**：扫 reserve + reject 中触 single-dealbreaker 的候选。识别真实被错杀的标志：
- `max_corr@admitted < 0.30` 且 `incremental_ic > 0.010`（库空间独立）
- `|monotonicity_oos|` ≥ 0.8（rank-order 真实）
- `sign_consistency = 1.0` + `cum_ic_mdd` 相对 library 中位数更浅（时序稳健）
- reject_reason 只指向单一指标（如仅 `alpha_survival<threshold`）

**Step 2 — 阈值调整**（影响范围由小到大，只调必须调的一层）：

```
direction-level 自设硬规则 → rubric 档位阈值 → 全局 config 阈值
     (通常最先删)            (其次调)          (最后兜底)
```

每次调整同步更新三处：`storage/config.yaml` / `.claude/skills/factor-judge/candidate-rubric.md` CP04 表 / `storage/vault/directions/{direction}.md` 结构性约束。

**Step 3 — 追溯 admit**（retroactive admission）：

```bash
# 1. batches/batch_{N}/judge.md frontmatter: verdict reject → admit + factor_name
# 2. batches/batch_{N}/candidates/C{id}.md frontmatter 同步
# 3. batch md 顶部加 [!warning] Retroactive revision callout 说明放宽依据
# 4. 重置 state 到该 batch 重跑 archive:
PYTHONPATH=src python3 -m research state set current_batch batch_{N}
PYTHONPATH=src python3 -m research state set current_batch_phase judged
PYTHONPATH=src python3 -m research archive batch_{N}
# 5. archive 后 state.last_batch 会覆盖为 batch_{N}；手动复原到原 last_batch
# 6. dispatch /factor-report F{new_id} 生成深度报告
# 7. 验证 vault/factors/F{new_id}.md > 0 且含 '# F{new_id}' H1
```

**Step 4 — 审计 + 防回归**：更新本节历史记录 + `direction.md` Narrative Log 说明追溯依据。下次 Phase 5 若新阈值稳定运行 N 轮可升格为 Data Facts；若再次系统性错杀，循环触发校准。

### 绝对不做的事

- **不放宽 hard_gate**（coverage / sign_flip / ic_oos_min / mono_flip / near_duplicate / library_reducer / is_oos_lst_collapse）—— 例外仅 barra_residual_alpha coverage→0.70（数据契约层 narrowly 放宽）
- **不放宽市值代理红线** `|corr($market_cap)| > 0.3`
- **不放宽 holdout 保护** —— 任何阈值调整不能让 Phase 3 代码读 2024 数据
- **不机械地在"连续零 admit"就放宽** —— 必须先诊断是否真的是"错杀"而非"信号确实都不够好"；混淆这两种情况 = 库质量稀释

### 历史校准记录

- **2026-04-19** (R1 → R1-relaxed)：`alpha_surv_min` 0.60 → 0.40；rubric CP04 poor 阈值 0.60 → 0.30；删除 `value_liquidity_interaction` direction.md 自设硬规则。触发：batch_005–007 连续 3 批 0 admit + reserve 积压率 60% + 诊断到 C005_b5 单指标 alpha_survival=0.30 dealbreaker 错杀。追溯 admit 为 F002 `pb_amount_ratio_20`。
- **2026-04-25** (Phase 5 consolidation)：引入 3 条 direction-aware 阈值 —— `alpha_surv_min.rank_diff=0.30` / `min_coverage_by_direction.barra_residual_alpha=0.70` / `incr_ic.min_when_corr_borderline=0.015` + `corr_borderline=[0.30, 0.70]`。同时升格 5 顶级律。
- **2026-04-27** (Phase 5 consolidation)：(a) rename key `alpha_surv_min.rank_diff` → `alpha_surv_min.rank_diff_geometry` 并 codify b057 informal floor；(b) 新增 hard_gate `is_oos_lst_collapse` (compound moment IS over-fit, b052 C006 case)；(c) 新增 hard_gate `library_reducer_hard_block` (跨 5 批 signature: mono≥0.85 + |ls_t|≥2.5 + incr_ic≤-0.005 + alpha_surv≤0.30)；(d) 升格 Rank-order ≠ Tradable Alpha 判别律 (CP01–CP05 联合判读)；(e) 引入 Direction Lifecycle：archived 状态 + 首批反向证伪 dead 律 + saturated 双层证据律；(f) Rank-Diff Geometry 段加 4 anchor pre-check (F002/F012/F020/F022) + dead RHS endpoints 动态名单。

## Promising Unexplored

> Phase 1 新开方向时参考。LLM 首轮启动时若 `INDEX.md` 里没有 `active/exploring` 方向，读这一段挑一个切入。Phase 5 consolidation 可补充或剪裁。

- **Higher-moment LHS independence axis on scale-free OHLC ratios**：F019 (Std body_ratio,20) + F020 (Std gap_ret,20) 跨 OHLC×gap 两 family 独立兑现，是 family-agnostic 律。可优先在 microstructure / overnight 两 productive 方向尝试同构 axis（注意 N≤20d + 单层 moment + scale-free 三条件）
- **Sign × persistent drift × non-linear weighting**：F018 (overnight sign × amount) + F013 (gap sign × log amount) 是仅有的 sign-aggregation admit。其它有 persistent drift 的 underlying field（fundamental momentum 已 dead；分红 / 公告事件 ?；index inclusion ?）尚未尝试 —— 需先验证 underlying drift 显著非零
- **Cross-section 算子 (CsRank/CsZscore/CsDemean) 替代 rolling**：解决 Python residual+rolling coverage=0.71 死路。residual 字段上做 cross-section 而非 time-series 二阶聚合，可能绕开 coverage 硬闸
- **非 daily-bar 数据**（minute / tick）：vol_20d 吸收律的根本逃离路径之一。当前数据基础设施未就绪 —— 一旦支持，magnitude / quantile / power-mean 一整片 dead 方向可能复活
