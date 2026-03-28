# 因子挖掘 — 问题与经验教训

## 1. 工程问题

### 1.1 Qlib 算子系统
- **问题**：使用 `Operators.register()` 内部映射 `cls.__name__` → 当类名与表达式名不一致时失败
- **解决**：直接注入 `Operators._ops[name] = cls`
- **问题**：`Neg`, `TsRank`, `TsMax`, `TsMin`, `SMA`, `Correlation` 在 pyqlib 0.9.7 中未注册
- **解决**：使用替代方案：`Mul(x,-1)` 替代 Neg，`Rank(x,N)` 替代 TsRank，`Max(x,N)` 替代 TsMax，`Corr` 替代 Correlation

### 1.2 自定义算子实现
- 滚动算子必须重写 `_load_internal()` 并调用 `super().__init__(feature, N, func_name)`
- 逐元素算子使用 NpElemOperator（如 `Tanh`）
- PairOperator/SignedPower 必须处理数值参数 — 在调用 `.load()` 前检查 `isinstance(feature, Expression)`
- **C.kernels = 1 是强制的** — 多进程 worker 不会继承 `_ops` 注册表

### 1.3 数据管道
- `D.instruments('all')` 返回 `{'market': 'all'}` 字典，不是股票代码 — 需要传给 `D.features()` 然后从 index 中提取
- `$amount` 和 `$vwap` 字段为零 — 数据源未填充这些字段
- `evaluate_batch` 返回 `BatchResult`（dataclass，有 `.admitted`, `.rejected`, `.replacements` 属性）— 不能直接遍历
- `evaluate_batch` 不会自动持久化到 library.yaml — 必须单独调用 `lib.admit()`

### 1.4 YAML 序列化
- 结果 YAML 文件可能包含 `_factor_values` 下的 pandas DataFrame 对象
- `yaml.safe_load` 会失败 → 使用 `yaml.unsafe_load` 或避免序列化 DataFrame
- 通过 `lib.replace()` 替换因子时，如果 metrics 字典的 key 是 `ic_mean_is` 而不是 `ic_mean`，会存储 `ic_mean: null` — 需要手动修复
- **已修复**：`BatchResult.to_dict()` 现在使用白名单方式，只保留必要字段，自动过滤 DataFrame 等大对象

## 2. 挖掘策略问题

### 2.1 盲目探索 vs 系统性引入（代价最大的错误）
- **浪费**：批次 002-006 没有充分上下文就运行，使用了错误的算子名（`Correlation` → `Corr`，`TsMax` → `Max`）
- **浪费**：批次 010-017（78个候选，0个录取）在经典 Alpha101 因子尚未尝试时就探索随机构造
- **教训**：必须先从已知好因子开始（Alpha101、Barra、技术指标），再探索新构造
- **教训**：先系统翻译已发表的因子库；创造性挖掘放后面

### 2.2 阈值管理
- 原始 corr_max=0.5 太严格 — rank_ret_times_rank_vol 在 corr=0.501 被拒
- 放宽到 0.7 后，Alpha101 批次额外录取了 12 个因子
- **教训**：初期用宽阈值（0.7），因子库大了再收紧
- **教训**：始终检查临界值附近的因子（corr 0.45-0.55）— 微小的阈值变化影响巨大

### 2.3 第1阶段 IC 膨胀
- 50只股票、约14天的第1阶段筛选会显示膨胀的 IC 值
- `consecutive_up_score` 在14天上 IC=0.104，但完整1092天 IC=0.009
- **教训**：永远不要信任第1阶段 IC 的绝对值 — 只用于相对排序/过滤
- **教训**：第1阶段应该过滤明显的垃圾，而不是识别赢家

## 3. A股市场洞察

### 3.1 波动率主导效应（"黑洞"效应）
- Factor 001（std_returns_20，IC=-0.058）与所有强信号的相关性在 0.6-0.9
- 低波动率异象是A股日频 OHLCV 数据中最根本的 Alpha
- 所有波动率度量（Std、MAD、RealizedVol、AmihudIlliq、IQR、Q90）本质上是同一个信号
- **除以波动率会摧毁信号** — `range_over_vol` IC=-0.008，`resi_over_vol` IC=-0.004

### 3.2 OHLCV 信号空间边界
- 从 260+ 个候选中录取24个因子后，边际递减效应严重
- 日频 OHLCV 只有约 3-4 个独立信号维度：波动率、成交量模式、K线形态、短期反转
- 长动量（>20天）在A股基本无效：return_60d IC=-0.009
- 自相关、熵、峰度（单独使用）全是噪声：|IC| < 0.01

### 3.3 什么有效
- **K线形态**：Williams %R 变体（IC=+0.070）、上影线比率（IC=+0.035）
- **波动率**：std_returns_20（IC=-0.058）、ATR（IC=-0.044）
- **成交量**：pv_corr_times_vol（IC=-0.052）、rank_ret*rank_vol（IC=-0.041）
- **状态切换**：vol_regime_reversal（IC=-0.044）— 必须使用非对称载荷
- **Alpha101 组合**：alpha024（IC=+0.049）、alpha038（IC=+0.035）、alpha023（IC=+0.030）
- **带符号非线性**：SignedPower(ret, 0.5)（IC=-0.032）

### 3.4 对称 IfElse 陷阱
- `If(cond, x, Mul(x, -1))` 无论条件如何都会产生相同的值 → corr=1.0
- 必须使用非对称载荷：两个分支使用不同的信号

## 4. Alpha101 翻译笔记

### 4.1 可翻译的（101个中约45个）
- 截面 `rank()` → 时序 `Rank(x, 60)`（60天滚动百分位）
- `ts_rank(x, d)` → `Rank(x, d)`
- `delay(x, d)` → `Ref(x, d)`
- `ts_argmax/ts_argmin` → `IdxMax/IdxMin`
- `sum(x, d)` → `Sum(x, d)`，`mean(x, d)` → `Mean(x, d)`
- `sign(x)` → `Sign(x)`，`abs(x)` → `Abs(x)`

### 4.2 不可翻译的（101个中约55个）
- 约35个需要 `$vwap`（adv20 * vwap 组合）
- 约18个需要行业中性化或 `IndNeutralize()`
- 约2个需要市值加权
- 在添加额外数据源之前无法实现

### 4.3 Alpha101 录取率
- 60个候选 → 12个录取 + 1个替换 = 21.7% 录取率（盲挖仅5.9%）
- 最强：williams_r_variant（IC=+0.070）、alpha024（IC=+0.049）
- 经典公式显著优于随机构造

## 5. 流程经验总结

1. **基线优先**：先筛选已知好因子，再进行创造性探索
2. **经典库是金矿**：Alpha101 录取率（21.7%）远高于盲挖（5.9%）
3. **初期宽阈值**：corr_max=0.7 可以全面覆盖；因子库大了再收紧
4. **立即持久化**：evaluate_batch 不会自动保存 — 录取后立刻调用 lib.admit()
5. **检查临界因子**：corr 在 0.45-0.55 的因子，微调阈值就可能录取
6. **验证算子可用性**：用简单表达式测试算子是否存在，然后再构建复杂公式
7. **第1阶段 IC 有噪声**：50只股票/14天的 IC 可能比全量膨胀10倍
8. **波动率就是一切**：在A股，几乎所有强日频信号都是波动率的代理
9. **不要除以波动率**：用 Std(ret) 做分母会摧毁预测力
10. **显式跟踪**：维护 library.yaml、state.yaml 和 patterns.yaml — evaluate_batch 的结果是临时的
