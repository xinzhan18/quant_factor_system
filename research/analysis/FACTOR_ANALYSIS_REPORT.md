# 量化因子分析库分析报告

## 1. 概述

本报告分析了市场上常见的量化因子分析库，重点关注其因子分析功能。

## 2. 分析的库

| 库名 | GitHub Stars | 定位 | 状态 |
|------|-------------|------|------|
| **Alphalens** | ~3k | 因子性能分析 | 活跃 |
| **QuantStats** | ~2k | 投资组合分析 | 活跃 |
| **Zipline** | ~13k | 完整量化交易框架 | 已停止维护 |

---

## 3. Alphalens 详细分析

### 3.1 核心功能

```
alphalens/
├── performance.py      # 因子性能计算
├── plotting.py         # 可视化
├── tears.py           # tearsheet 生成
├── utils.py           # 工具函数
└── tests/             # 测试
```

### 3.2 核心指标

| 函数 | 说明 |
|------|------|
| `factor_information_coefficient()` | IC (信息系数) 计算 |
| `mean_information_coefficient()` | 平均 IC |
| `factor_returns()` | 因子收益 |
| `factor_weights()` | 因子权重 |
| `factor_alpha_beta()` | Alpha/Beta 回归 |
| `mean_return_by_quantile()` | 分组收益 |
| `quantile_turnover()` | 分组换手率 |
| `factor_rank_autocorrelation()` | 因子自相关 |

### 3.3 数据格式

```python
# 输入: MultiIndex DataFrame
# Index: (date, asset)
# Columns: factor, factor_quantile, 1D, 5D, 10D forward returns

factor_data = pd.DataFrame({
    'factor': [0.5, 0.3, 0.8, ...],
    'factor_quantile': [2, 1, 3, ...],
    '1D': [0.01, -0.02, 0.03, ...],
    '5D': [0.05, -0.08, 0.12, ...],
}, index=pd.MultiIndex.from_tuples([
    ('2024-01-02', '000001.XSHE'),
    ('2024-01-02', '000002.XSHE'),
    ...
], names=['date', 'asset']))
```

### 3.4 优点

- ✅ 专注于因子分析，功能完整
- ✅ 支持 IC、分组回测、换手率分析
- ✅ 与 Zipline 集成良好
- ✅ 可生成 tearsheet

### 3.5 缺点

- ❌ 不维护更新
- ❌ 依赖 Zipline 数据格式
- ❌ 无机器学习因子支持

---

## 4. QuantStats 详细分析

### 4.1 核心功能

```
quantstats/
├── stats.py           # 统计指标
├── plots.py          # 可视化
├── reports.py        # 报告生成
├── utils.py          # 工具函数
└── __init__.py       # pandas 扩展
```

### 4.2 核心指标

| 函数 | 说明 |
|------|------|
| `sharpe()` | 夏普比率 |
| `sortino()` | 索提诺比率 |
| `calmar()` | 卡玛比率 |
| `max_drawdown()` | 最大回撤 |
| `volatility()` | 波动率 |
| `cagr()` | 复合年化增长率 |
| `win_rate()` | 胜率 |
| `profit_factor()` | 盈利因子 |
| `kelly_criterion()` | 凯利公式 |
| `value_at_risk()` | VaR |
| `conditional_value_at_risk()` | CVaR |

### 4.3 扩展的 pandas 方法

```python
qs.extend_pandas()

# 直接在 Series 上调用
returns.sharpe()      # 夏普比率
returns.sortino()     # 索提诺比率
returns.max_drawdown() # 最大回撤
returns.cagr()        # 年化收益
returns.win_rate()    # 胜率
```

### 4.4 优点

- ✅ 简单易用，API 友好
- ✅ 丰富的统计指标
- ✅ 支持 Monte Carlo 模拟
- ✅ 可生成 HTML 报告
- ✅ 支持 yfinance 数据源

### 4.5 缺点

- ❌ 侧重收益分析，非因子分析
- ❌ 无分组回测功能
- ❌ 无 IC 分析
- ❌ 无 Pipeline 支持

---

## 5. Zipline 详细分析

### 5.1 核心功能

```
zipline/
├── algorithm.py       # 交易算法
├── pipeline/         # ⭐ 因子管道
│   ├── engine.py      # 管道引擎
│   ├── factors/      # ⭐ 因子实现
│   │   ├── factor.py      # 因子基类
│   │   ├── basic.py       # 基础因子
│   │   ├── technical.py    # 技术因子
│   │   └── statistical.py  # 统计因子
│   ├── data/         # 数据源
│   └── loaders/      # 数据加载器
└── finance/          # 金融计算
```

### 5.2 Pipeline 因子系统

```python
from zipline.pipeline import Pipeline
from zipline.pipeline.factors import RSI, BollingerBands

# 定义因子管道
def make_pipeline():
    return Pipeline(
        columns={
            'rsi': RSI(window_length=14),
            'bb': BollingerBands(window_length=20, k=2),
            'momentum': Returns(window_length=252),
        },
        screen='universe_filter'
    )
```

### 5.3 内置因子

| 类别 | 因子 |
|------|------|
| **技术因子** | RSI, MACD, BollingerBands, ExponentialWeightedMovingAverage |
| **统计因子** | RollingPearsonCorrelation, RollingSpearmanCorrelation |
| **基础因子** | Latest, Returns, AverageDollarVolume |

### 5.4 优点

- ✅ 完整的量化框架
- ✅ Pipeline 因子系统优雅
- ✅ 支持实时交易
- ✅ 回测功能完整

### 5.5 缺点

- ❌ **已停止维护** (2023)
- ❌ Python 3.9+ 兼容问题
- ❌ 安装复杂
- ❌ 数据源依赖官方

---

## 6. 功能对比矩阵

| 功能 | Alphalens | QuantStats | Zipline |
|------|-----------|------------|---------|
| **IC 分析** | ✅ | ❌ | ❌ |
| **分组回测** | ✅ | ❌ | ✅ |
| **因子收益** | ✅ | ❌ | ✅ |
| **换手率分析** | ✅ | ❌ | ❌ |
| **自相关分析** | ✅ | ❌ | ❌ |
| **夏普比率** | ❌ | ✅ | ✅ |
| **最大回撤** | ❌ | ✅ | ✅ |
| **Pipeline** | ❌ | ❌ | ✅ |
| **Tearsheet** | ✅ | ✅ | ❌ |
| **Monte Carlo** | ❌ | ✅ | ❌ |
| **ML 因子** | ❌ | ❌ | ❌ |

---

## 7. 集成建议

### 7.1 推荐方案

基于分析，我们推荐以下集成策略：

| 优先级 | 库 | 集成方式 | 用途 |
|--------|-----|---------|------|
| **P0** | Alphalens | 部分引用 | IC、分组回测 |
| **P1** | QuantStats | 部分引用 | 收益统计 |
| **P2** | Zipline | 参考设计 | Pipeline 架构 |

### 7.2 集成原则

1. **Alphalens**: 引用 `performance.py` 的核心函数
   - `factor_information_coefficient()`
   - `mean_return_by_quantile()`
   - `quantile_turnover()`

2. **QuantStats**: 引用 `stats.py` 的指标
   - `sharpe()`, `sortino()`, `calmar()`
   - `max_drawdown()`, `volatility()`

3. **Zipline**: 参考 Pipeline 设计
   - 因子管道架构
   - 因子组合方式

---

## 8. 实现计划

### Phase 1: 核心指标 (本周)

- [ ] 实现 IC 系列 (IC, ICIR, IC decay)
- [ ] 实现分组回测 (5组/10组)
- [ ] 实现因子换手率分析

### Phase 2: 收益统计 (下周)

- [ ] 实现夏普比率 (滚动/历史)
- [ ] 实现最大回撤序列
- [ ] 实现风险指标 (VaR, CVaR)

### Phase 3: Pipeline 架构 (下月)

- [ ] 设计因子管道 API
- [ ] 实现因子组合
- [ ] 支持因子过滤

---

## 9. 结论

1. **Alphalens** 仍然是因子分析的最佳参考，其 IC 分析和分组回测是行业标准
2. **QuantStats** 的统计指标可以丰富我们的收益分析
3. **Zipline** 的 Pipeline 架构值得借鉴，但不应直接引用（已停止维护）
4. 建议**选择性集成**，而非全盘复制

---

*报告生成时间: 2026-02-09*
*分析的库版本: Alphalens (latest), QuantStats (latest), Zipline (1.4.0)*
