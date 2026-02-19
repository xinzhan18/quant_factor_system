# Quant Factor Trading Platform - 项目概览

## 📦 项目简介

完整的**量化因子研究与交易平台**，从数据获取到因子分析、回测、实盘交易的一体化解决方案。

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    📊 Dashboard (Streamlit)                    │
│         因子评估 | 回测配置 | 结果展示 | 任务监控               │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      🔄 Backtest (回测引擎)                      │
│        因子选择 → 股票筛选 → 仓位管理 → 止盈止损 → 收益分析    │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                   📈 Factor (因子模块)                          │
│                  因子计算 → 可视化 → 存储                         │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                     💾 Data (数据模块)                          │
│                数据下载 → 存储 → 清洗 → 查询                     │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 目录结构

```
quant_factor_system/
├── data/                    # 数据模块
│   ├── clean/             # 数据清洗/验证
│   ├── ricequant_source.py
│   └── timescale_storage.py
│
├── factors/               # 因子模块
│   ├── basic/            # 基础因子
│   ├── visualization/   # 可视化 (IC/分组收益)
│   └── processor.py
│
├── backtest/              # 回测模块
│   ├── selection/        # 选股 (因子选择/过滤/排名)
│   ├── signal/           # 信号生成
│   ├── engine.py         # 回测引擎
│   └── analyzer.py       # 绩效分析
│
├── position/              # 仓位管理
├── stoploss/             # 止损策略
├── selector/              # 选股模块
│
├── dashboard/            # Web界面
│   ├── pages/           # 页面
│   └── components/     # 通用组件
│
└── docs/                 # 文档
    ├── ARCHITECTURE.md   # 架构文档
    ├── TASK_PLAN.md     # 任务计划
    └── plan/            # 需求文档
```

## 🚀 启动方式

### 1. 安装依赖
```bash
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
pip install -e .
```

### 2. 启动 Dashboard
```bash
cd /Users/xinzhan/.openclaw/workspace
/Users/xinzhan/miniconda3/envs/quantfactor/bin/streamlit run quant_factor_system/dashboard/Home.py
```

### 3. 运行因子计算
```bash
cd /Users/xinzhan/.openclaw/workspace
/Users/xinzhan/miniconda3/envs/quantfactor/bin/python recompute_factors.py
```

## 🔧 核心模块

### Data Module
```python
from quant_factor_system.data import DataManager

dm = DataManager()
# 下载数据
dm.download_and_save_daily(symbols, start_date, end_date)
# 查询数据
df = dm.query_daily(symbols, start_date, end_date)
```

### Factor Module
```python
from quant_factor_system.factors import ICAnalyzer, GroupReturnsAnalyzer

# IC分析
ic_analyzer = ICAnalyzer('return_1d')
result = ic_analyzer.compute_ic(factor_df, price_df)

# 分组收益
group_analyzer = GroupReturnsAnalyzer('return_1d')
result = group_analyzer.compute_group_returns(factor_df, price_df)
```

### Backtest Module
```python
from quant_factor_system.backtest import BacktestEngine

engine = BacktestEngine()
result = engine.run(config)
```

## 📊 核心指标

| 模块 | 功能 |
|-----|------|
| IC | 信息系数，预测能力 |
| ICIR | IC均值/IC标准差 |
| 分组收益 | Q1-Q5各组收益 |
| 多空收益 | Q5-Q1组合收益 |
| 夏普比率 | 风险调整收益 |

## 🔄 数据流转

```
米筐API → Data Module → Factor Module → Backtest Module → Dashboard
                ↓                    ↓
           TimescaleDB       可视化图表
```

## 📝 当前状态

- **因子数据**: 部分完成 (return_1d, return_5d完整，其他因子待计算)
- **Dashboard**: 运行中
- **回测框架**: 完成

## 📞 支持

- 文档: `docs/`
- 架构: `docs/ARCHITECTURE.md`
- 任务: `docs/TASK_PLAN.md`

---

*最后更新: 2026-02-19*
