# 📊 量化多因子评价系统 (Quant Factor System) v2.0

一个简单但功能完整的 Python 量化多因子评价框架，基于 Barra 模型和行业最佳实践。

[![GitHub stars](https://img.shields.io/github/stars/xinzhan18/quant_factor_system)](https://github.com/xinzhan18/quant_factor_system/stargazers)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## ✨ 功能特性

### 🎯 完整因子框架
- **多因子系统**: 支持 Barra 风格因子和自定义因子
- **丰富因子库**: 动量、价值、质量、成长、市值、波动率、流动性等
- **因子评估**: IC分析、分组回测、换手率、夏普比率

### 📥 数据层
- **多数据源**: AkShare (A股)、yfinance (美股)
- **数据持久化**: SQLite 数据库存储
- **自动更新**: 每日增量更新市场数据

### ⚙️ 自动化
- **任务调度**: Cron 风格的定时任务
- **流水线**: 数据→因子→回测→报告全自动
- **监控告警**: 任务状态追踪和通知

### 📊 可视化
- **仪表盘**: 交互式因子分析看板
- **HTML 报告**: 自动生成专业报告
- **多格式导出**: HTML、JSON

## 📁 项目结构

```
quant_factor_system/
├── __init__.py              # 包入口，导出所有类和函数
├── base.py                  # Factor、FactorSystem 核心类
├── factors.py               # 7个基础因子
├── extended_factors.py       # 10个 Barra 风格因子
├── evaluator.py             # 评估器和回测引擎
├── data_source.py           # 数据获取模块
├── data_storage.py          # SQLite 数据持久化 ⭐ NEW
├── automation.py            # 任务调度和流水线 ⭐ NEW
├── visualization.py         # 可视化报告 ⭐ NEW
└── full_demo.py             # 完整自动化示例 ⭐ NEW

demo.py                      # 快速入门示例
requirements.txt             # 依赖列表
README.md                   # 说明文档
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt

# A股数据
pip install akshare

# 美股数据
pip install yfinance

# 可视化依赖
pip install matplotlib pandas numpy
```

### 2. 运行演示

```bash
# 快速示例
python demo.py

# 完整自动化示例（推荐）
python quant_factor_system/full_demo.py
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

## 📊 完整自动化示例

```python
from quant_factor_system import (
    # 数据持久化
    DataRepository,
    AutoDataUpdater,
    
    # 因子
    FactorSystem,
    MomentumFactor,
    ValueFactor,
    
    # 评估
    FactorEvaluator,
    
    # 自动化
    create_default_pipeline,
    
    # 可视化
    FactorDashboard,
)

# 1. 创建数据仓库（自动保存到 SQLite）
repo = DataRepository("./data/factor_data.db")

# 2. 自动更新数据
updater = AutoDataUpdater(repo)
updater.run_full_update()

# 3. 创建因子系统
system = FactorSystem(name="Daily Factor System")
system.add_factor(MomentumFactor(), weight=1.0)
system.add_factor(ValueFactor(), weight=1.0)

# 4. 计算和评估因子
factor_values = system.calculate_all(data)
evaluator = FactorEvaluator(system)
ic_results = evaluator.evaluate_ic(returns)

# 5. 生成可视化报告
dashboard = FactorDashboard("./data/reports")
for name, ic in ic_results.items():
    dashboard.add_factor_performance(name, ic)
report_path = dashboard.generate_html_report("每日因子分析")

# 6. 启动自动调度（每日定时执行）
pipeline = create_default_pipeline()
pipeline.start_scheduler()
```

## 📈 因子列表

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

## 📊 评估指标

### 信息系数 (IC)

```python
ic_results = evaluator.evaluate_ic(returns)
# 输出:
# Momentum: IC=0.05, IC_IR=0.32, IC胜率=58%
# Value: IC=0.08, IC_IR=0.45, IC胜率=62%
```

### 分组回测

```python
group_returns = evaluator.evaluate_group_return(returns, groups=5)
# Q1-Q5 分组收益
```

### 回测引擎

```python
backtest = BacktestEngine(system, rebalance_period=20, top_n=10)
portfolio_returns = backtest.run_backtest(data, returns)
performance = backtest.get_performance()
# total_return: 25.6%
# sharpe_ratio: 1.25
# max_drawdown: -12.3%
```

## ⚙️ 自动化调度

### 创建定时任务

```python
from quant_factor_system import TaskScheduler

scheduler = TaskScheduler()

# 注册每日任务
scheduler.register_task(
    name="daily_update",
    func=update_data,
    schedule_time="08:00",  # 每天早上8点
    description="每日更新市场数据",
    retry_times=3
)

# 启动调度器
scheduler.start()
```

### 流水线配置

```python
from quant_factor_system import create_default_pipeline

# 创建预配置流水线
pipeline = create_default_pipeline()

# 任务列表：
# 1. daily_data_update (08:00)  - 更新市场数据
# 2. factor_calculation (09:30)  - 计算因子值
# 3. factor_evaluation (10:00)  - 评估因子
# 4. backtest (15:00)           - 运行回测
# 5. generate_report (16:00)    - 生成报告

# 启动调度
pipeline.start_scheduler()

# 或手动运行完整流水线
results = pipeline.run_full_pipeline()
```

## 📄 报告示例

系统自动生成的 HTML 报告包含：

- 📊 系统状态概览
- 📈 因子绩效汇总表（IC、IC_IR、胜率、换手率）
- 📉 因子相关性热力图
- 📉 IC 时间序列图
- 💡 投资建议

## 📂 数据结构

### SQLite 数据库

```
./data/factor_data.db
├── price_data           # 价格数据
├── fundamental_data     # 财务数据
├── factor_data          # 因子数据
├── factor_performance   # 因子绩效
└── system_status        # 系统状态
```

### 报告输出

```
./data/reports/
├── factor_report_20240208_153000.html  # HTML 报告
└── export_20240208_153000.json         # JSON 数据
```

## 🔧 扩展开发

### 自定义因子

```python
from quant_factor_system import Factor

class MyCustomFactor(Factor):
    def __init__(self):
        super().__init__("MyFactor", "我的自定义因子")
    
    def calculate(self, data):
        my_factor = data['close'].pct_change(20)
        return my_factor

factor = MyCustomFactor()
values = factor.calculate(data)
```

### 自定义数据源

```python
from quant_factor_system import DataSource

class MyDataSource(DataSource):
    def get_price(self, symbols, start_date, end_date, adjust="qfq"):
        # 实现数据获取逻辑
        return price_data
    
    def get_fundamental(self, symbols, fields, start_date, end_date):
        # 实现财务数据获取
        return fundamental_data
```

### 自定义任务

```python
def my_task():
    print("执行自定义任务...")
    return {"status": "success"}

scheduler.register_task(
    name="my_task",
    func=my_task,
    schedule_time="10:30",
    description="我的自定义任务"
)
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
- [AkShare](https://github.com/akfamily/akshare)
- [QUANTAXIS](https://github.com/QUANTAXIS/QUANTAXIS)

## 👨‍💻 作者

**xinzhan18**

- GitHub: [@xinzhan18](https://github.com/xinzhan18)
- Email: xin.zhan18@outlook.com

---

⭐ 如果这个项目对你有帮助，请给个 Star！
