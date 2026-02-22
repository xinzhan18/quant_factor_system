# QuantFactorSystem - 架构文档

## 📐 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          QuantFactor System                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                        Dashboard Layer                          │   │
│   │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐   │   │
│   │   │  Home   │  │ Factors │  │ Pipeline│  │   Data      │   │   │
│   │   └─────────┘  └─────────┘  └─────────┘  └─────────────┘   │   │
│   │                        (Streamlit)                              │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                   │
│                                    ▼                                   │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      Backtest Engine Layer                       │   │
│   │   ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐ │   │
│   │   │ Selection │  │  Signal   │  │  Position │  │ Stop-Loss │ │   │
│   │   │   (选股)  │  │  (信号)   │  │  (仓位)   │  │  (止损)   │ │   │
│   │   └───────────┘  └───────────┘  └───────────┘  └───────────┘ │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                   │
│                                    ▼                                   │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                        Factor Layer                              │   │
│   │   ┌───────────┐  ┌───────────┐  ┌───────────────────────────┐ │   │
│   │   │  Registry │  │  Factory  │  │      Visualization        │ │   │
│   │   │ (因子注册) │  │ (因子工厂) │  │  - IC Analysis          │ │   │
│   │   │           │  │           │  │  - Group Returns         │ │   │
│   │   └───────────┘  └───────────┘  └───────────────────────────┘ │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                   │
│                                    ▼                                   │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                         Data Layer                               │   │
│   │   ┌─────────────────────────────────────────────────────────┐  │   │
│   │   │                     TimescaleDB                          │  │   │
│   │   └─────────────────────────────────────────────────────────┘  │   │
│   │                                    │                           │   │
│   │         ┌─────────────────────────┼─────────────────────────┐  │   │
│   │         ▼                         ▼                         ▼  │   │
│   │   ┌───────────┐           ┌───────────┐           ┌───────────┐│   │
│   │   │  Sources   │           │  Storage  │           │   Utils   ││   │
│   │   │ (数据源)   │           │  (存储)    │           │  (工具类)  ││   │
│   │   └───────────┘           └───────────┘           └───────────┘│   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      Data Source Layer                           │   │
│   │                    RiceQuant (米筐)                               │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 📁 模块详解

### 1. Data Layer (数据层)

#### 职责
- 原始数据获取、清洗、存储
- 因子数据持久化
- 数据库连接管理

#### 核心组件

```
data/
├── ricequant_source.py      # 米筐数据源
├── data_manager.py          # 统一数据管理
├── loaders.py              # ⭐ 数据加载（从数据库加载因子/价格数据）
│
├── clean/                  # 数据清洗
│   ├── validation.py       # 数据验证
│   └── __init__.py
│
├── storage/               # ⭐ 存储层（重构后）
│   ├── timescale_storage.py    # TimescaleDB 主存储
│   ├── timescale_db.py        # TimescaleDB 操作
│   ├── factor_storage.py      # 因子存储
│   ├── factor_version.py     # 因子版本管理
│   ├── frequency.py          # 频率常量
│   ├── db_utils.py         # 数据库工具函数
│   └── __init__.py
│
└── utils/                # ⭐ 工具类（重构后）
    ├── postgres_db.py         # PostgreSQL 基础操作
    ├── formatter.py           # 数据格式化
    ├── industry_source.py    # 行业数据
    └── __init__.py
```

#### 数据库架构

```
PostgreSQL 16 / TimescaleDB
├── quant (数据库)
│   ├── minute_factor_values (分钟因子 - 窄表分区)
│   │   ├── minute_factor_values_2026_01 (按月分区)
│   │   ├── minute_factor_values_2026_02
│   │   └── ...
│   │
│   ├── daily_factors_wide (日级因子 - 宽表)
│   │   ├── symbol, date, momentum_*, return_*, ma_*, etc.
│   │   └── 20+ 因子列
│   │
│   ├── weekly_factors_wide (周级因子 - 宽表)
│   │   └── 类似日级因子结构
│   │
│   └── factor_config (因子配置表)
│       ├── name, display_name, category
│       ├── frequency, storage_type, unit
│       └── description, created_at, updated_at
```

### 2. Factor Layer (因子层)

#### 职责
- 因子计算与注册
- 因子工厂模式
- IC分析、分组收益可视化

#### 核心组件

```
factors/
├── __init__.py           # 导出注册表和工厂
├── registry.py           # 因子注册表（单例模式）
│   ├── register()        # 注册因子
│   ├── get()           # 获取因子实例
│   └── list_factors()   # 列出所有因子
│
├── factory.py           # 因子工厂
│   └── create_factor()  # 创建因子实例
│
├── basic/
│   ├── factors.py        # 基础技术因子
│   │   ├── MomentumFactor      # 动量因子
│   │   ├── MovingAverage       # 移动平均线
│   │   ├── RSI                 # 相对强弱
│   │   ├── DistMAFactor        # 均线偏离度
│   │   └── VolatilityFactor    # 波动率
│   │
│   └── return_factors.py # 收益因子
│       ├── Return1dFactor
│       ├── Return5dFactor
│       └── Return20dFactor
│
├── aggregator.py        # 因子聚合（多因子合并）
├── processor.py         # 因子处理（标准化、去极值）
└── visualization/      # 可视化分析
    ├── ic_analyzer.py   # IC (Information Coefficient) 分析
    ├── group_returns.py # 分组收益分析
    └── report.py        # 报告生成
```

#### 因子基类 (core/base.py)

```python
class Factor(ABC):
    name: str           # 因子名称
    category: str       # 因子类别
    frequency: str      # 数据频率 (minute, daily, weekly)
    
    @abstractmethod
    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算因子值"""
        pass
    
    @abstractmethod
    def validate(self, data: pd.DataFrame) -> bool:
        """验证输入数据"""
        pass
```

### 3. Backtest Engine Layer (回测层)

#### 职责
- 策略回测模拟
- 绩效分析
- 信号生成与执行

#### 核心组件

```
backtest/
├── engine.py            # 回测引擎主程序
│   ├── load_data()      # 加载数据
│   ├── run()            # 执行回测
│   └── get_results()    # 获取结果
│
├── analyzer.py          # 绩效分析器
│   ├── calculate_returns()    # 计算收益
│   ├── calculate_metrics()    # 计算指标
│   └── generate_report()      # 生成报告
│
├── selection/          # ⭐ 选股模块（重构后移入）
│   ├── single.py         # 单因子选股
│   ├── multi.py          # 多因子选股
│   ├── filter.py         # 因子过滤
│   ├── factor_selector.py # 因子选择器
│   ├── stock_filter.py   # 股票过滤器
│   └── ranker.py         # 股票排名器
│
├── position/            # ⭐ 仓位模块（重构后移入）
│   ├── equal.py          # 等权配置
│   ├── factor.py         # 因子里重
│   └── kelly.py          # 凯利公式
│
├── stoploss/           # ⭐ 止损模块（重构后移入）
│   ├── fixed.py          # 固定止损
│   └── atr.py            # ATR动态止损
│
└── signal/             # 信号生成
    ├── generator.py       # 信号生成器
    └── __init__.py
```

#### 回测流程

```
1. 数据准备
   ├── 加载因子数据
   ├── 加载价格数据
   └── 数据对齐与清洗

2. 选股 (Selection)
   ├── 单因子选股: 按因子值排序，选择Top/Bottom N
   ├── 多因子选股: 因子标准化，合成综合因子
   └── 因子过滤: IC过滤、相关性过滤、分位数过滤

3. 仓位配置 (Position)
   ├── 等权: 每个标的等权重
   ├── 因子里重: 按因子绝对值分配权重
   └── 凯利公式: 根据胜率和盈亏比计算最优仓位

4. 止损 (Stop-Loss)
   ├── 固定止损: 设定固定百分比止损
   ├── ATR止损: 根据波动率动态止损
   └── 追踪止损: 跟踪价格最高点止损

5. 绩效分析
   ├── 收益指标: 年化收益、夏普比率、最大回撤
   ├── 风险指标: 波动率、VaR、CVaR
   └── 归因分析: 因子贡献、行业贡献
```

### 4. Dashboard Layer (Web界面)

#### 职责
- 纯 "Load + 展示" 模式
- 调用后端模块获取数据
- 渲染图表和表格

#### 页面结构

```
dashboard/
├── Home.py               # 首页
│   ├── 系统状态概览
│   ├── 数据库统计
│   └── 快速操作入口
│
├── pages/
│   ├── Factors.py        # 因子评估页面
│   │   ├── 因子选择器
│   │   ├── 参数配置
│   │   ├── IC分析图表
│   │   └── 分组收益图表
│   │
│   ├── Pipeline.py       # Pipeline组合页面
│   │   ├── 多因子配置
│   │   ├── 参数调优
│   │   └── 累计收益曲线
│   │
│   ├── BacktestResult.py # 回测结果页面
│   │   ├── 策略配置
│   │   ├── 绩效指标
│   │   └── 收益曲线
│   │
│   └── Data.py          # 数据浏览页面
│       └── 数据查询
│
└── components/          # 可复用组件
    ├── charts.py         # 图表组件
    │   ├── create_line_chart()
    │   ├── create_equity_curve()
    │   └── create_ic_chart()
    │
    ├── forms/           # 表单组件
    │   ├── factor_selector_form()
    │   ├── backtest_config_form()
    │   └── filter_form()
    │
    └── tables/          # 表格组件
        ├── render_dataframe()
        ├── render_metrics_row()
        └── render_performance_table()
```

## 🔄 数据流

### 因子计算与存储流程

```
1. 数据获取 (RiceQuant)
   └── ricequant_source.get_price(symbols, start_date, end_date)
   
2. 因子计算
   └── factor.compute(price_data)
   
3. IC计算
   └── ic_analyzer.compute_ic(factor_values, returns)
   
4. 数据验证
   └── validator.check(factor_data)
   
5. 因子存储
   ├── 窄表: storage.save_minute_factor(name, data, ic)
   └── 宽表: storage.save_daily_factor(data)
```

### 回测执行流程

```
1. 配置回测参数
   ├── 选股规则: 单因子/多因子
   ├── 仓位配置: 等权/因子里重/凯利
   ├── 止损规则: 固定/ATR/追踪
   └── 时间范围: start_date, end_date

2. 加载数据
   ├── 因子数据: loaders.get_factor_data(factor_name)
   └── 价格数据: loaders.get_price_data(symbols, date_range)

3. 按时间循环
   for each trading_day:
       ├── 选股: selection.select(day)
       ├── 仓位: position.allocate(day)
       ├── 交易: execute_trades()
       ├── 止损: stoploss.check()
       └── 记录: record_portfolio()
   
4. 绩效分析
   ├── 计算收益序列
   ├── 计算指标: 年化收益、夏普、最大回撤
   └── 生成报告
   
5. Dashboard 展示
   ├── loaders 获取数据
   ├── factors/visualization 计算 IC
   └── components/charts 渲染图表
```

## 🗄️ 数据库设计

### 表结构详细说明

#### 1. factor_config (因子配置表)

```sql
CREATE TABLE factor_config (
    name VARCHAR(100) PRIMARY KEY,
    display_name VARCHAR(200),
    category VARCHAR(50),
    frequency VARCHAR(20) NOT NULL,
    storage_type VARCHAR(20) NOT NULL,
    description TEXT,
    unit VARCHAR(50),
    params JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX idx_factor_config_category ON factor_config(category);
CREATE INDEX idx_factor_config_frequency ON factor_config(frequency);
```

#### 2. minute_factor_values (分钟因子 - 窄表)

```sql
CREATE TABLE minute_factor_values (
    time TIMESTAMP NOT NULL,
    factor_name VARCHAR(100),
    symbol VARCHAR(20),
    factor_value DOUBLE PRECISION,
    ic DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT NOW()
);

SELECT create_hypertable('minute_factor_values', 'time');

CREATE TABLE minute_factor_values_2026_01
    PARTITION OF minute_factor_values
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE INDEX idx_minute_factor_lookup 
ON minute_factor_values (factor_name, symbol, time DESC);
```

#### 3. daily_factors_wide (日级因子 - 宽表)

```sql
CREATE TABLE daily_factors_wide (
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    
    -- 动量因子
    momentum_5d DOUBLE PRECISION,
    momentum_10d DOUBLE PRECISION,
    momentum_20d DOUBLE PRECISION,
    momentum_60d DOUBLE PRECISION,
    
    -- 收益率因子
    return_1d DOUBLE PRECISION,
    return_5d DOUBLE PRECISION,
    return_10d DOUBLE PRECISION,
    return_20d DOUBLE PRECISION,
    return_60d DOUBLE PRECISION,
    
    -- 均线因子
    ma_5 DOUBLE PRECISION,
    ma_10 DOUBLE PRECISION,
    ma_20 DOUBLE PRECISION,
    ma_60 DOUBLE PRECISION,
    
    -- 均线偏离度
    dist_ma10 DOUBLE PRECISION,
    dist_ma20 DOUBLE PRECISION,
    
    -- 技术指标
    rsi_14 DOUBLE PRECISION,
    volatility_20d DOUBLE PRECISION,
    
    -- 统计因子
    zscore_60 DOUBLE PRECISION,
    
    updated_at TIMESTAMP DEFAULT NOW(),
    
    PRIMARY KEY (symbol, date)
);

CREATE INDEX idx_daily_factors_date ON daily_factors_wide(date DESC);
CREATE INDEX idx_daily_factors_symbol ON daily_factors_wide(symbol);
```

## 📈 性能考量

### 数据量

| 场景 | 股票数 | 频率 | 因子数 | 年数据量 | 存储方案 |
|------|--------|------|--------|----------|----------|
| 高频 | 5000 | 分钟 | 1 | 7.5亿 | 窄表 + 分区 |
| 中频 | 5000 | 分钟 | 10 | 75亿 | 窄表 + 分区 |
| 低频 | 5000 | 日 | 20 | 3650万 | 宽表 |
| 低频 | 5000 | 日 | 100 | 1.8亿 | 窄表 |
| 超低频 | 5000 | 周 | 10 | 260万 | 宽表 |

### 优化策略

1. **分区管理**: 分钟因子按月分区，便于数据清理和备份
2. **宽表设计**: 日级因子使用宽表，减少JOIN操作
3. **索引优化**: 按因子名、时间、股票代码复合索引
4. **批量写入**: 使用COPY进行批量数据导入
5. **缓存策略**: 热点数据缓存到内存

## 🔧 重构历史

### 2026-02-19 重构

| 重构项 | 改动 |
|--------|------|
| selector/position/stoploss | 从顶层移入 backtest/ |
| Dashboard IC计算 | 调用 factors/visualization/ICAnalyzer |
| Dashboard 数据加载 | 抽取为 data/loaders.py |
| 删除模拟数据 | 删除 simulator.py, sample_price.csv |
| data/ 目录重构 | 拆分为 storage/ + utils/ |

## 🚀 扩展指南

### 添加新因子

```python
from quant_factor_system.core.base import Factor

class MyFactor(Factor):
    name = 'my_factor'
    category = 'tech'
    frequency = 'daily'
    
    def __init__(self, param1=10):
        self.param1 = param1
    
    def compute(self, data):
        # 因子计算逻辑
        return result
    
    def validate(self, data):
        return True
```

### Dashboard 职责划分

```
Dashboard = Load + 展示

Load (数据加载)
├── data/loaders.py          # 从数据库加载
└── factors/visualization/   # 计算 IC、分组收益

展示 (UI 渲染)
├── dashboard/components/charts/  # 图表
├── dashboard/components/forms/    # 表单
└── dashboard/components/tables/  # 表格
```

---

## 📊 因子评估规范 (重要!)

### 训练集/测试集划分

| 数据集 | 时间范围 | 用途 |
|--------|----------|------|
| **训练集** | 2015-01-01 ~ 2022-12-31 | 因子筛选、参数优化 |
| **测试集** | 2023-01-01 ~ 至今 | 最终策略验证 |

### 因子收益计算 (关键!)

**所有因子评估必须使用 T+1 收益，计算方式:**

```python
# ❌ 错误: 当天收益 (用当天收盘价计算)
df['return_1d'] = df.groupby(level='symbol')['close'].pct_change(1)

# ✅ 正确: T+1 收益 (用明天收盘价计算)
# 方法1: shift(-1) 后计算
df['future_close'] = df.groupby(level='symbol')['close'].shift(-1)
df['return_1d'] = (df['future_close'] - df['close']) / df['close']

# 方法2: pct_change + shift
df['return_1d'] = df.groupby(level='symbol')['close'].pct_change(1).shift(-1)
```

**为什么重要:**
- 因子是用当天数据计算的
- 收益应该是明天的收益 (T+1)
- 如果不shift，会导致"未来函数"问题，IC虚高

### IC 计算

```python
from scipy import stats

# 每日 IC = 因子值与 T+1 收益的 Spearman 相关系数
daily_ic = df.groupby('time').apply(
    lambda x: stats.spearmanr(x['factor'], x['return_1d'])[0]
)

# IC 均值 = 因子预测能力的核心指标
ic_mean = daily_ic.mean()
ic_ir = daily_ic.mean() / daily_ic.std()  # IR > 0.5 为优秀
```

### 分组回测

```python
# 1. 每日按因子值分成5组 (Q1~Q5)
df['group'] = df.groupby('time')['factor'].transform(
    lambda x: pd.qcut(x, 5, labels=['Q1','Q2','Q3','Q4','Q5'], duplicates='drop')
)

# 2. 计算每组平均收益 (T+1)
group_returns = df.groupby('group')['return_1d'].mean() * 252  # 年化

# 3. 多空组合 (根据 IC 方向决定)
# IC > 0: Long Q5, Short Q1
# IC < 0: Long Q1, Short Q5
long_short_return = group_returns['Q5'] - group_returns['Q1']  # 根据方向调整
```

### 评估指标

| 指标 | 优秀 | 合格 | 较差 |
|------|------|------|------|
| IC 均值 | > 0.05 | 0.02~0.05 | < 0.02 |
| IC IR | > 0.5 | 0.3~0.5 | < 0.3 |
| IC > 0 占比 | > 60% | 50%~60% | < 50% |
| 多空年化 | > 15% | 5%~15% | < 5% |

---

*最后更新: 2026-02-22*
