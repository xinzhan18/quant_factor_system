# 📊 量化多因子评价系统 (Quant Factor System)

一个简单但功能完整的 Python 量化多因子评价框架，基于 Barra 模型和行业最佳实践。

[![GitHub stars](https://img.shields.io/github/stars/xinzhan18/quant_factor_system)](https://github.com/xinzhan18/quant_factor_system/stargazers)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://python.org)

## ✨ 功能特性

- **🎯 多因子框架**: 支持 Barra 风格因子和自定义因子
- **📈 完整因子库**: 动量、价值、质量、成长、市值、波动率、流动性等
- **🔍 全面评估**: IC分析、分组回测、换手率、夏普比率
- **📊 多数据源**: 支持 AkShare (A股)、yfinance (美股)
- **🚀 简单易用**: 几行代码即可构建和评估因子
- **📦 模块化设计**: 易于扩展和二次开发

## 📁 项目结构

```
quant_factor_system/
├── __init__.py              # 包入口和导出
├── base.py                  # 基础类 (Factor, FactorSystem)
├── factors.py               # 基础因子实现
├── extended_factors.py      # Barra 风格因子
├── evaluator.py             # 评估器和回测引擎
├── data_source.py           # 数据获取模块
└── examples.py             # 完整示例代码

demo.py                      # 快速入门示例
requirements.txt             # 依赖列表
README.md                    # 说明文档
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt

# A股数据 (可选)
pip install akshare

# 美股数据 (可选)
pip install yfinance
```

### 2. 运行示例

```bash
# 快速示例
python demo.py

# 完整教程 (含图表)
python quant_factor_system/examples.py
```

### 3. 简单使用示例

```python
from quant_factor_system import (
    FactorSystem,
    MomentumFactor,
    ValueFactor,
    QualityFactor,
    FactorEvaluator
)

# 创建因子系统
system = FactorSystem(name="My Quant System")

# 添加因子
system.add_factor(MomentumFactor(period=120), weight=1.0)
system.add_factor(ValueFactor(metric='pe'), weight=1.0)
system.add_factor(QualityFactor(metric='roe'), weight=1.0)

# 计算因子值
factor_values = system.calculate_all(data)

# 获取综合得分
scores = system.get_composite_score()

# 评估因子
evaluator = FactorEvaluator(system)
evaluator.print_report(returns)
```

## 📊 因子列表

### 基础因子 (factors.py)

| 因子 | 描述 | 默认参数 |
|------|------|---------|
| `MomentumFactor` | 动量因子 | period=12 |
| `ValueFactor` | 价值因子 | metric='pe' |
| `QualityFactor` | 质量因子 | metric='roe' |
| `VolatilityFactor` | 波动率因子 | period=20 |
| `GrowthFactor` | 成长因子 | metric='revenue' |
| `SizeFactor` | 市值因子 | - |
| `LiquidityFactor` | 流动性因子 | - |

### Barra 风格因子 (extended_factors.py)

| 因子 | 描述 | 计算方法 |
|------|------|---------|
| `BarraSizeFactor` | 市值因子 | 对数市值 |
| `BarraMomentumFactor` | 动量因子 | 12个月累计收益 |
| `BarraValueFactor` | 价值因子 | PE/PB |
| `BarraVolatilityFactor` | 残差波动率 | 标准差 |
| `BarraLiquidityFactor` | 流动性因子 | 换手率 |
| `BetaFactor` | 市场敏感度 | CAPM Beta |
| `EarningsYieldFactor` | 盈利收益率 | 1/PE |
| `GrowthFactor` | 成长因子 | 营收增长 |
| `LeverageFactor` | 杠杆因子 | 资产负债率 |

## 📈 评估指标

### 信息系数 (IC)

```python
ic_results = evaluator.evaluate_ic(returns)

# 输出:
# Momentum: IC=0.05, IC_IR=0.32, IC胜率=58%
# Value: IC=0.08, IC_IR=0.45, IC胜率=62%
# Quality: IC=0.03, IC_IR=0.18, IC胜率=52%
```

### 分组回测

```python
group_returns = evaluator.evaluate_group_return(returns, groups=5)

# Q1-Q5 分组收益
# 高因子值组 vs 低因子值组
```

### 回测引擎

```python
backtest = BacktestEngine(system, rebalance_period=20, top_n=10)
portfolio_returns = backtest.run_backtest(data, returns)
performance = backtest.get_performance()

# 输出:
# total_return: 25.6%
# sharpe_ratio: 1.25
# max_drawdown: -12.3%
```

## 📊 数据获取

```python
from quant_factor_system import get_a_stock_data, MultiSourceDataManager

# 获取 A 股数据
data = get_a_stock_data('000001', '2020-01-01', '2024-12-31')

# 管理多个数据源
manager = MultiSourceDataManager()
```

## 🔧 自定义因子

创建自定义因子：

```python
from quant_factor_system import Factor

class MyCustomFactor(Factor):
    def __init__(self):
        super().__init__("MyFactor", "我的自定义因子")
    
    def calculate(self, data):
        # 实现你的因子逻辑
        my_factor = data['close'].pct_change(20)
        return my_factor

# 使用自定义因子
factor = MyCustomFactor()
values = factor.calculate(data)
```

## 📝 数据格式

### 输入数据格式

```python
DataFrame 需包含以下列:

价格数据:
- close: 收盘价
- open: 开盘价
- high: 最高价
- low: 最低价
- volume: 成交量

财务数据:
- pe: 市盈率
- pb: 市净率
- roe: 净资产收益率
- revenue: 营收
- profit: 利润
- market_cap: 市值
```

### 示例数据

```python
import pandas as pd

data = pd.DataFrame({
    'close': [10.5, 11.0, 10.8, ...],
    'pe': [15.2, 16.0, 14.8, ...],
    'roe': [0.12, 0.15, 0.11, ...],
    'market_cap': [1e9, 1.2e9, ...],
    'volume': [1e6, 1.5e6, ...],
}, index=date_index)
```

## 📦 扩展功能

### 使用 Jupyter Notebook

```bash
pip install jupyter notebook
jupyter notebook
```

```python
# 在 Jupyter 中
from quant_factor_system import *
%matplotlib inline
```

### 机器学习因子

```python
from sklearn.decomposition import PCA

# 使用 PCA 提取因子
pca = PCA(n_components=3)
pca_factors = pca.fit_transform(factor_values)
```

## 🤝 贡献

欢迎贡献代码！

1. Fork 本项目
2. 创建分支 (`git checkout -b feature/AmazingFeature`)
3. 提交改动 (`git commit -m 'Add AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

MIT License

## 🙏 参考

- [QuantConnect Lean](https://github.com/QuantConnect/Lean)
- [Zipline](https://github.com/stefan-jansen/zipline)
- [Backtrader](https://github.com/mementum/backtrader)
- [AkShare](https://github.com/akfamily/akshare)
- [QUANTAXIS](https://github.com/QUANTAXIS/QUANTAXIS)

## 👨‍💻 作者

**xinzhan18**

- GitHub: [@xinzhan18](https://github.com/xinzhan18)
- Email: xin.zhan18@outlook.com

---

⭐ 如果这个项目对你有帮助，请给个 Star！
