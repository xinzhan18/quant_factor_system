# Research Lessons — 研究经验与禁忌

> 每轮 /idea 和 /judge 前**必读**此文件。
> 新发现的经验教训直接追加到对应 section。

## Forbidden Patterns（禁止模式）

以下模式经过实验验证为无效或有害，**不要再尝试**。对应的正则已编码在 `research_config.yaml` 的 `forbidden_patterns` 中。

### FP001: TsAutoCorr($turnover_rate) 零信号
- **发现时间**: batch_003 (ST002)
- **现象**: ls_tstat=-0.20，quintile spread 完全平坦
- **原因**: 换手率自相关对预测未来收益无效
- **规则**: 禁止 `TsAutoCorr($turnover_rate, *)` 形式
- **状态**: active

### FP002-FP003: upper_shadow_ratio 极端 regime 不稳定
- **发现时间**: batch_003 (ST005)
- **现象**: validation IC=-0.024 (看似强), holdout IC=-0.0006 (完全消失), decay=0.025
- **原因**: 近年市场 regime 变化使影线信号增强但不可持续
- **规则**: 禁止上影线比例的均值和波动率形式
- **状态**: active

### FP004-FP005: IdxMax 跨量维度不能 decorrelate
- **发现时间**: batch_004
- **现象**: IdxMax($amount) vs IdxMax($volume) corr=0.92, IdxMax($turnover_rate) corr=0.99
- **原因**: timing encoding 在 volume/amount/turnover 间高度相关
- **规则**: 禁止 IdxMax($amount) 和 IdxMax($turnover_rate)
- **状态**: active

### FP006: Corr($amount, $turnover_rate) 零信号
- **发现时间**: batch_004
- **现象**: IC_val=0.0, ICIR=0.0, gate_fail_technical
- **原因**: amount ≈ price × volume, turnover_rate ≈ volume / shares, 两者近乎恒定线性关系
- **规则**: 禁止 Corr($amount, $turnover_rate, *)
- **状态**: active

## Near-Miss Lessons（差一点但没过的教训）

### NM001: ret_vol_cov_20 — 统计最强但 alpha_survival 最低
- **发现时间**: batch_002 (C002_02)
- **现象**: ICIR=0.50(batch最高), decay=0.99, 但 alpha_survival=10.6%
- **原因**: 收益-量协方差本质捕捉短期反转(str_1m)风格
- **教训**: 统计表现好 ≠ 独立 alpha；holdout 确认无残差 alpha (residual_ic=-0.004)

### NM002: range_x_turnover_vol — IC 最强但 alpha_survival 极低
- **发现时间**: batch_002 (C002_06)
- **现象**: IC=-0.085(batch最强), ls_t=-5.36, 但 alpha_survival=5.2%
- **原因**: crossover 因子放大了 vol_20d 风格暴露而非独立信号
- **教训**: 两个风格因子交叉不产生 orthogonal alpha

### NM003: amount_cv_20_60 — 加长窗口 barra_residual 翻转
- **发现时间**: batch_004 (C004_03)
- **现象**: alpha_surv=0.20(borderline), barra_residual_ic=-0.010(负翻转)
- **原因**: 更长 amount CV 窗口放大了 vol/turnover style 暴露
- **教训**: 加长窗口 ≠ 更稳定，反而加大风格依赖

## Operator/Expression Gotchas（表达式陷阱）

- `Max($open, $close)` — `Max` 是 rolling max 不是 element-wise max，对两个字段取 max 应该用 `If(Gt($open,$close),$open,$close)`
- `Rank(expr)` — `Rank` 需要窗口参数 N，截面 rank 应该用 `CsRank(expr)`
- `Neg(x)` — 未注册，用 `Mul(x, -1)` 替代
- `SMA(x, N)` — 未注册，用 `Mean(x, N)` 替代
- `AmihudIlliq($close, $volume, 20)` — 参数签名错误，应该只传 feature 和 N，内部计算 |return|/$volume

## Style Trap Warnings（风格陷阱）

### ST001: CsRank decorrelation 不降低 alpha_survival
- **发现时间**: batch_003
- **现象**: `Corr(CsRank($close), CsRank($volume), 20)` 的 alpha_survival=13.5%，与原始 Corr 形式相当
- **原因**: CsRank 只去除幅度差异，不去除风格结构（str_1m=0.317 仍占主导）
- **标志**: barra_residual_ic 符号翻转（+0.004）是最强信号
- **规则**: Rank 变换不能替代真正的因子正交化（Barra 残差化）
- **状态**: active

### ST002: TsAutoCorr on turnover 零信号
- **发现时间**: batch_003
- **现象**: `TsAutoCorr($turnover_rate, 10)` 的 ls_tstat=-0.20（≈零），decay=0.43
- **原因**: 换手率自相关对预测未来收益无效
- **规则**: 自相关类因子在流动性度量上无独立信号
- **状态**: active

### ST003: str_1m 极端暴露 = 反转代理，不是独立 alpha
- **发现时间**: batch_003
- **现象**: `upday_turnover_ratio_20` 的 str_1m=0.877，残差 IC 符号翻转
- **原因**: 高 up-day turnover ratio 本质上是短期反转信号，而非流动性不对称
- **标志**: residual_ic 符号翻转（+0.016）比 alpha_survival 数字更重要
- **规则**: 当 dominant style 是 str_1m 且 residual IC 翻转，该因子不是独立 alpha
- **状态**: active

### ST004: IdxMax 是最有效的 decorrelation 工具
- **发现时间**: batch_003
- **现象**: `IdxMax($volume, 20)` alpha_survival=50%，style_r²=8.3%（两批次最佳）
- **原因**: 时序位置编码（"第几天最大量"）捕捉注意力耗竭模式，与波动率量级正交
- **启示**: 探索更多 IdxMax/IdxMin 变体（如 IdxMax of volume/amount over 10/20/60 窗口）
- **状态**: active

### ST006: Barra_residual_ic 符号翻转是最可靠的风格陷阱指标
- **发现时间**: batch_003
- **现象**: C003_01 Barra_residual_ic=-0.0087（负翻转），alpha_surv=0.50 但 reject；C003_04 Barra_residual_ic=+0.0157（正），admit
- **原因**: Barra 残差化后方向与原始 IC 相反 = 无独立 alpha；残差正向 = 风格掩盖了真实 alpha
- **规则**: alpha_surv < 0.2 + Barra_residual_ic 翻转 = definite reject； Barra_residual_ic > +0.01 即使 style dominant 也可能是真 alpha
- **状态**: active

### ST007: dominant_style=str_1m 不必然 reject
- **发现时间**: batch_003
- **现象**: C003_04 str_1m=0.877（极高），但 Barra_residual_ic=+0.0157，holdout 确认信号
- **原因**: 风格暴露和真实 alpha 可以共存于同一因子
- **规则**: Barra_residual_ic > +0.01 是独立 alpha 的确认信号，即使 dominant_style 极高
- **状态**: active

### ST009: Pure price/volatility signals without fundamental interaction are systematically style-absorbed
- **发现时间**: batch_005
- **现象**: batch_005 的 5 个候选全部 reject。price_volume correlation、price_to_MA、ATR变体全部有 Barra_residual flip。即使 holdout IC 强（-0.05到-0.07）也被 reject。
- **原因**: A股市场中价格/波动率信号几乎完全被 Barra 风格因子解释（str_1m, vol_20d, size）
- **规则**: 纯价格/波动率信号（无基本面字段交互）基本无独立 alpha。必须与基本面字段（$pe_ratio, $pb_ratio, $amount）交互才能 decorrelate from style
- **状态**: active

### ST008: Lower shadow ratio shows different regime behavior from upper shadow
- **发现时间**: batch_004
- **现象**: C004_06 lower_shadow_ratio_20 holdout IC=-0.030（强），C004_05 price_position holdout IC=-0.007（弱）
- **原因**: 下影线反映下方支撑，上影线反映上方抛压。不同市场 regime 下两者表现不同
- **规则**: Lower shadow 和 upper shadow 不可互换，需要单独验证
- **状态**: active

### ST005: 影线类因子有极强 regime 依赖性
- **发现时间**: batch_003
- **现象**: `upper_shadow_ratio_10` decay=4.52（OOS IC 是 train 的 4.5 倍），holdout IC=-0.0006（完全消失）
- **原因**: 近年市场 regime 变化（如量化/融券限制）使影线信号增强但不可持续
- **规则**: decay > 2.0 的因子需要 holdout 确认； ST005 confirmed — 2024 holdout IC 归零
- **状态**: active
