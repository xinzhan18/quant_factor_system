# 📊 量化多因子评价系统

一个简单但功能完整的 Python 量化多因子评价系统。

## ✨ 功能特性

- **模块化设计**: 因子、系统、评估器解耦，易于扩展
- **常用因子**: 动量、价值、质量、波动率、成长等
- **全面评估**: IC分析、分组回测、换手率、夏普比率
- **简单易用**: 几行代码即可构建和评估因子

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行示例

```bash
python demo.py
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
import pandas as pd

# 创建系统
system = FactorSystem(name="My System")

# 添加因子
system.add_factor(MomentumFactor(period=6), weight=1.0)
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

## 📁 项目结构

```
quant_factor_system/
├── __init__.py          # 包入口
├── base.py              # 基础类 (Factor, FactorSystem)
├── factors.py           # 因子定义
│   ├── MomentumFactor   # 动量因子
│   ├── ValueFactor      # 价值因子
│   ├── QualityFactor    # 质量因子
│   ├── VolatilityFactor # 波动率因子
│   ├── GrowthFactor     # 成长因子
│   ├── SizeFactor       # 市值因子
│   └── LiquidityFactor  # 流动性因子
└── evaluator.py         # 评估器
    └── FactorEvaluator  # 因子评估
    └── BacktestEngine   # 回测引擎

demo.py                  # 使用示例
requirements.txt         # 依赖列表
README.md               # 说明文档
```

## 📊 评估指标

### 信息系数 (IC)
- IC: 因子与收益的相关系数
- IC_IR: 信息比率 (IC / IC标准差)
- IC胜率: IC为正的比例

### 分组回测
- Q1-Q5: 按因子值分5组
- 多空收益差: Q5 - Q1

### 绩效指标
- 夏普比率
- 最大回撤
- 换手率

## 🔧 自定义因子

创建自定义因子只需继承 `Factor` 类：

```python
from quant_factor_system import Factor

class MyCustomFactor(Factor):
    def __init__(self):
        super().__init__("MyFactor", "自定义因子")
        
    def calculate(self, data):
        # 实现你的因子逻辑
        return my_factor_values
```

## 📝 数据格式

系统接受 pandas DataFrame，需包含以下列：

- `close`: 收盘价
- `pe`: 市盈率 (用于ValueFactor)
- `roe`: 净资产收益率 (用于QualityFactor)
- `revenue`: 营收 (用于GrowthFactor)
- `market_cap`: 市值 (用于SizeFactor)
- `volume`: 成交量 (用于LiquidityFactor)

## 🤝 贡献

欢迎贡献代码！请提交 Pull Request。

## 📄 许可证

MIT License

## 👨‍💻 作者

Built with ❤️ by OpenClaw
