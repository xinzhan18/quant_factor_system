# QuantFactorSystem v4.0

完整的量化因子研究与交易平台。

## 🎯 项目概述

从数据获取到因子分析、回测、实盘交易的完整量化投资解决方案。

### 核心能力

- **数据层**: TimescaleDB 存储，米筐(RiceQuant) 唯一数据源
- **因子层**: 分钟到日级因子计算，多种计算方法
- **选股层**: 单因子/多因子选股，因子过滤与排名
- **仓位层**: 等权、因子里重、凯利公式
- **止损层**: 固定止损、ATR止损、追踪止损
- **回测层**: 完整模拟与绩效分析
- **Dashboard**: 策略配置、结果展示、任务监控

## 🚀 快速启动

### 环境配置

```bash
# 激活 conda 环境
conda activate quantfactor

# 进入项目目录
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system

# 安装项目包（首次或更新后）
pip install -e .
```

### 启动 Dashboard

```bash
# 方式1: 使用绝对路径
/Users/xinzhan/miniconda3/envs/quantfactor/bin/streamlit run quant_factor_system/dashboard/Home.py

# 方式2: 先 cd 再运行
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system/dashboard
streamlit run Home.py
```

**Dashboard 访问地址:** http://localhost:8501

### 运行因子计算

```bash
/Users/xinzhan/miniconda3/envs/quantfactor/bin/python recompute_factors.py
```

## 📦 模块结构

```
quant_factor_system/
├── core/                    # 核心基类
│
├── data/                   # 数据层 ⭐ 重构完成
│   ├── ricequant_source.py  # 米筐数据源
│   ├── data_manager.py      # 统一数据管理
│   ├── loaders.py          # 数据加载（从数据库加载因子/价格数据）
│   ├── clean/              # 数据清洗
│   │   └── validator.py    # 数据验证
│   ├── storage/            # 存储层
│   │   ├── timescale_storage.py  # TimescaleDB 主存储
│   │   ├── timescale_db.py      # TimescaleDB 操作
│   │   ├── factor_storage.py    # 因子存储
│   │   ├── factor_version.py   # 因子版本管理
│   │   ├── frequency.py        # 频率常量
│   │   └── db_utils.py         # 数据库工具
│   └── utils/              # 工具类
│       ├── postgres_db.py       # PostgreSQL 基础操作
│       ├── formatter.py         # 数据格式化
│       └── industry_source.py   # 行业数据
│
├── factors/                # 因子层
│   ├── registry.py           # 因子注册表
│   ├── factory.py           # 因子工厂
│   ├── basic/              # 基础因子
│   │   ├── factors.py      # 动量、均线、RSI等
│   │   └── return_factors.py
│   ├── aggregator.py       # 因子聚合
│   ├── processor.py        # 因子处理
│   └── visualization/      # IC分析、分组收益可视化
│       ├── ic_analyzer.py  # IC分析
│       └── group_returns.py # 分组收益
│
├── backtest/               # 回测层 ⭐ 重构完成
│   ├── engine.py           # 回测引擎
│   ├── analyzer.py         # 绩效分析
│   ├── selection/          # 选股模块
│   │   ├── single.py       # 单因子选股
│   │   ├── multi.py        # 多因子选股
│   │   ├── filter.py       # 因子过滤与排名
│   │   ├── factor_selector.py
│   │   ├── stock_filter.py
│   │   └── ranker.py
│   ├── position/           # 仓位模块
│   │   ├── equal.py        # 等权配置
│   │   ├── factor.py       # 因子里重
│   │   └── kelly.py        # 凯利公式
│   ├── stoploss/          # 止损模块
│   │   ├── fixed.py        # 固定止损
│   │   └── atr.py          # ATR动态止损
│   └── signal/            # 信号生成
│       └── generator.py
│
├── dashboard/             # Dashboard ⭐ 重构完成
│   ├── components/        # 可复用组件
│   │   ├── charts.py      # 图表组件
│   │   ├── forms/        # 表单组件
│   │   └── tables/        # 表格组件
│   └── pages/            # 页面
│       ├── Home.py        # 首页
│       ├── Factors.py     # 因子评估
│       ├── Pipeline.py    # Pipeline
│       ├── BacktestResult.py # 回测结果
│       └── Data.py       # 数据浏览
│
├── pipeline/              # Pipeline
├── examples/              # 示例
├── docs/                 # 文档
│   ├── PROJECT_OVERVIEW.md
│   ├── ARCHITECTURE.md   # 架构文档
│   └── plan/            # Plan 文档
└── scripts/              # 脚本
```

## 🗄️ 数据库

| 配置 | 值 |
|------|-----|
| 类型 | TimescaleDB (PostgreSQL 16 超集) |
| 主机 | localhost |
| 端口 | 5432 |
| 数据库 | quant |
| 用户 | postgres |
| 密码 | postgres |

### 因子存储架构

#### 按频率分表设计

| 频率 | 存储类型 | 表名 | 数据量估算 |
|------|---------|------|-----------|
| 分钟 | 窄表分区 | `minute_factor_values` | ~7.5亿/年/因子 |
| 日级 | 宽表 | `daily_factors_wide` | ~3650万/年/20因子 |
| 周级 | 宽表 | `weekly_factors_wide` | ~260万/年 |

#### 因子配置表 `factor_config`

存储所有因子的元信息：名称、类别、频率、存储类型、描述、单位等。

## 📊 内置因子

### 技术因子 (tech)

| 因子名 | 类名 | 说明 |
|--------|------|------|
| momentum | MomentumFactor | 动量因子 (5/10/20/60日) |
| ma | MovingAverage | 移动平均线 |
| rsi | RSI | 相对强弱指数 |
| dist_ma | DistMAFactor | 均线偏离度 |
| volatility | VolatilityFactor | 波动率 |

### 收益因子 (return)

| 因子名 | 类名 | 说明 |
|--------|------|------|
| return_1d | Return1dFactor | 1日收益率 |
| return_5d | Return5dFactor | 5日收益率 |
| return_20d | Return20dFactor | 20日收益率 |

### 统计因子 (stats)

| 因子名 | 类名 | 说明 |
|--------|------|------|
| zscore | ZScoreFactor | Z分数标准化 |
| ic | ICFactor | 信息系数 |

## 🔧 使用示例

### 1. 数据加载

```python
from quant_factor_system.data.loaders import (
    get_factor_data,
    get_price_data,
)

# 获取因子数据
factor_df, error = get_factor_data('momentum_20', connection)

# 获取价格数据
price_df = get_price_data(['SH600000'], '20240101', '20240131', connection)
```

### 2. IC 分析

```python
from quant_factor_system.factors.visualization import ICAnalyzer

analyzer = ICAnalyzer()
result = analyzer.compute_ic(factor_df, price_df, split_date)
print(f"IC: {result['ic_all']:.3f}")
```

### 3. 运行回测

```python
from quant_factor_system.backtest import BacktestEngine

engine = BacktestEngine()
result = engine.run(strategy_config)
```

## 📈 Dashboard 页面

1. **首页 (Home)**
   - 系统状态概览
   - 数据库统计
   - 快速创建因子

2. **因子评估 (Factors)**
   - 选择已有因子
   - 参数配置
   - IC分析、分组收益可视化
   - 保存到数据库

3. **Pipeline (Pipeline)**
   - 多因子组合
   - 参数配置
   - 累计收益曲线

4. **回测 (BacktestResult)**
   - 策略配置
   - 绩效分析
   - 结果展示

## 🛠️ 维护命令

```bash
# 数据库
./scripts/db.sh start      # 启动
./scripts/db.sh stop       # 停止
./scripts/db.sh shell      # 进入命令行

# 数据操作
./scripts/data.sh sample   # 生成示例数据
./scripts/data.sh import file.csv

# 系统维护
./run.sh info       # 系统信息
./run.sh init       # 初始化
./run.sh clean      # 清理
```

## 📋 重构历史 (2026-02-19)

| 重构项 | 改动 |
|--------|------|
| selector/position/stoploss | 从顶层移入 backtest/ |
| Dashboard IC计算 | 调用 factors/visualization/ICAnalyzer |
| Dashboard 数据加载 | 抽取为 data/loaders.py |
| 删除模拟数据 | 删除 simulator.py, sample_price.csv |
| data/ 目录重构 | 拆分为 storage/ + utils/ |

## 📚 文档

- **项目概览**: `docs/PROJECT_OVERVIEW.md`
- **架构文档**: `docs/ARCHITECTURE.md`
- **Plan 列表**: `docs/plan/OVERVIEW.md`

## 🧰 技术栈

- **Python**: 3.8+
- **Web**: Streamlit
- **数据处理**: Pandas, NumPy, SciPy
- **数据库**: TimescaleDB (PostgreSQL 超集)
- **可视化**: Matplotlib, Plotly
- **数据源**: RiceQuant (米筐)

---

*最后更新: 2026-02-19*
