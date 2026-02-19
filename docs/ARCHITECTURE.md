# QuantFactorSystem - 架构文档

## 📐 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          QuantFactor System                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                        Dashboard Layer                          │   │
│   │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐   │   │
│   │   │  Home   │  │ Factors │  │ Pipeline│  │    Backtest     │   │   │
│   │   └─────────┘  └─────────┘  └─────────┘  └─────────────────┘   │   │
│   │                        (Streamlit)                               │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      Backtest Engine Layer                      │   │
│   │   ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────────┐  │   │
│   │   │ Selection │  │  Signal   │  │  Position │  │  Stop-Loss  │  │   │
│   │   │   Layer   │  │  Generation│  │  Layer    │  │   Layer     │  │   │
│   │   └───────────┘  └───────────┘  └───────────┘  └─────────────┘  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                        Factor Layer                             │   │
│   │   ┌───────────┐  ┌───────────┐  ┌─────────────────────────────┐  │   │
│   │   │  Registry │  │  Factory  │  │     Visualization           │  │   │
│   │   │           │  │           │  │  - IC Analysis              │  │   │
│   │   │           │  │           │  │  - Group Returns            │  │   │
│   │   └───────────┘  └───────────┘  └─────────────────────────────┘  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                         Data Layer                               │   │
│   │   ┌─────────────────────────────────────────────────────────────┐  │   │
│   │   │                   TimescaleDB                               │  │   │
│   │   │  ┌─────────────────┐  ┌─────────────────┐                 │  │   │
│   │   │  │  Minute Factors │  │  Daily Factors  │                 │  │   │
│   │   │  │  (Narrow/Partition)│ │  (Wide Table)   │                 │  │   │
│   │   │  └─────────────────┘  └─────────────────┘                 │  │   │
│   │   │  ┌─────────────────┐  ┌─────────────────┐                 │  │   │
│   │   │  │  Weekly Factors │  │  Factor Config  │                 │  │   │
│   │   │  │  (Wide Table)   │  │  (Metadata)     │                 │  │   │
│   │   │  └─────────────────┘  └─────────────────┘                 │  │   │
│   │   └─────────────────────────────────────────────────────────────┘  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      Data Source Layer                           │   │
│   │                    RiceQuant (米筐)                              │   │
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
├── postgres_db.py         # PostgreSQL 通用数据库操作
├── timescale_db.py        # TimescaleDB 时序数据库扩展
├── data_manager.py        # 数据管理（获取、清洗、验证）
├── factor_storage.py      # ⭐ 因子存储引擎
│   ├── register_factor() # 注册因子元信息
│   ├── save_minute_factor() # 保存分钟级因子（窄表）
│   ├── save_daily_factor()  # 保存日级因子（宽表）
│   ├── query_minute_factor() # 查询分钟因子
│   └── query_daily_factor()  # 查询日级因子
└── clean/
    ├── validation.py     # 数据验证
    └── normalization.py  # 数据标准化
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
│   ├── get()             # 获取因子实例
│   └── list_factors()    # 列出所有因子
│
├── factory.py            # 因子工厂
│   └── create_factor()   # 创建因子实例
│
├── basic/
│   ├── factors.py        # 基础技术因子
│   │   ├── MomentumFactor      # 动量因子
│   │   ├── MovingAverage       # 移动平均线
│   │   ├── RSI                  # 相对强弱
│   │   ├── DistMAFactor        # 均线偏离度
│   │   └── VolatilityFactor    # 波动率
│   │
│   └── return_factors.py # 收益因子
│       ├── Return1dFactor
│       ├── Return5dFactor
│       └── Return20dFactor
│
├── aggregator.py         # 因子聚合（多因子合并）
├── processor.py          # 因子处理（标准化、去极值）
└── visualization/       # 可视化分析
    ├── ic_analyzer.py    # IC (Information Coefficient) 分析
    ├── group_returns.py  # 分组收益分析
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
│   └── generate_report()       # 生成报告
│
├── selection/           # ⭐ 选股模块
│   ├── single.py        # 单因子选股
│   │   ├── select()    # 按因子值选股
│   │   └── rank()      # 因子排名
│   │
│   ├── multi.py         # 多因子选股
│   │   ├── combine()   # 因子合成
│   │   └── optimize()  # 因子权重优化
│   │
│   └── filter.py        # 因子过滤
│       ├── ic_filter()  # IC过滤
│       ├── quantile_filter() # 分位数过滤
│       └── corr_filter()  # 相关性过滤
│
└── signal/             # 信号生成
    ├── generator.py    # 信号生成器
    └── combiner.py     # 信号合并
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

### 4. Position Layer (仓位层)

#### 策略实现

```
position/
├── equal.py            # 等权配置
│   └── EqualWeightPosition
│       └── allocate(symbols, weights=None)
│
├── factor.py           # 因子里重
│   └── FactorWeightedPosition
│       └── allocate(symbols, factor_values)
│
└── kelly.py            # 凯利公式
    └── KellyPosition
        └── allocate(symbols, win_rate, avg_win, avg_loss)
```

### 5. Stop-Loss Layer (止损层)

#### 策略实现

```
stoploss/
├── fixed.py            # 固定止损
│   └── FixedStopLoss
│       └── check(entry_price, current_price)
│
├── atr.py              # ATR动态止损
│   └── ATRStopLoss
│       └── check(entry_price, current_price, atr)
│
└── trailing.py         # 追踪止损
    └── TrailingStopLoss
        └── check(entry_price, current_price, highest_price)
```

### 6. Dashboard Layer (Web界面)

#### 页面结构

```
dashboard/
├── Home.py             # 首页
│   ├── 系统状态概览
│   ├── 数据库统计
│   └── 快速操作入口
│
├── pages/
│   ├── Factors.py      # 因子评估页面
│   │   ├── 因子选择器
│   │   ├── 参数配置
│   │   ├── IC分析图表
│   │   └── 分组收益图表
│   │
│   ├── Pipeline.py    # Pipeline组合页面
│   │   ├── 多因子配置
│   │   ├── 参数调优
│   │   └── 累计收益曲线
│   │
│   └── Backtest.py    # 回测结果页面
│       ├── 策略配置
│       ├── 绩效指标
│       └── 收益曲线
│
└── components/
    ├── charts.py       # 图表组件
    ├── forms.py        # 表单组件
    └── tables.py       # 表格组件
```

## 🔄 数据流

### 因子计算与存储流程

```
1. 数据获取 (RiceQuant)
   └── get_price_data(symbols, start_date, end_date)
   
2. 因子计算
   └── factor.compute(price_data)
   
3. IC计算
   └── factor.compute_ic(factor_values, returns)
   
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
   ├── 因子数据: storage.query_daily_factor(...)
   └── 价格数据: ricequant.get_price(...)
   
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

5. 可视化
   ├── 累计收益曲线
   ├── 回撤曲线
   └── 分组收益对比
```

## 🗄️ 数据库设计

### 表结构详细说明

#### 1. factor_config (因子配置表)

```sql
CREATE TABLE factor_config (
    name VARCHAR(100) PRIMARY KEY,      -- 因子唯一标识
    display_name VARCHAR(200),           -- 显示名称
    category VARCHAR(50),               -- 类别 (tech, return, stats, industry)
    frequency VARCHAR(20) NOT NULL,     -- 频率 (minute, daily, weekly)
    storage_type VARCHAR(20) NOT NULL,  -- 存储类型 (wide, narrow)
    description TEXT,                   -- 因子描述
    unit VARCHAR(50),                   -- 单位 (percent, ratio, etc.)
    params JSONB,                      -- 参数配置
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 索引
CREATE INDEX idx_factor_config_category ON factor_config(category);
CREATE INDEX idx_factor_config_frequency ON factor_config(frequency);
```

#### 2. minute_factor_values (分钟因子 - 窄表)

```sql
-- Hypertable (TimescaleDB)
CREATE TABLE minute_factor_values (
    time TIMESTAMP NOT NULL,
    factor_name VARCHAR(100),
    symbol VARCHAR(20),
    factor_value DOUBLE PRECISION,
    ic DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT NOW()
);

SELECT create_hypertable('minute_factor_values', 'time');

-- 分区按月
CREATE TABLE minute_factor_values_2026_01
    PARTITION OF minute_factor_values
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- 索引
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
    
    -- 元数据
    updated_at TIMESTAMP DEFAULT NOW(),
    
    PRIMARY KEY (symbol, date)
);

-- 索引
CREATE INDEX idx_daily_factors_date ON daily_factors_wide(date DESC);
CREATE INDEX idx_daily_factors_symbol ON daily_factors_wide(symbol);
```

## 🔧 配置说明

### config.py 核心配置

```python
# 数据库配置
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'quant',
    'user': 'postgres',
    'password': 'postgres'
}

# 数据源配置
DATA_SOURCE = 'ricequant'  # 唯一数据源

# 回测配置
BACKTEST_CONFIG = {
    'initial_capital': 1000000,      # 初始资金
    'transaction_cost': 0.001,       # 交易成本
    'slippage': 0.0005,              # 滑点
    'min_position': 0.01,            # 最小仓位
    'max_position': 0.95             # 最大仓位
}
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

## 🚀 扩展指南

### 添加新因子

1. **创建因子类** (factors/basic/my_factor.py):

```python
from quant_factor_system.core.base import Factor

class MyFactor(Factor):
    name = 'my_factor'
    category = 'tech'
    frequency = 'daily'
    
    def __init__(self, param1=10, param2=20):
        self.param1 = param1
        self.param2 = param2
    
    def compute(self, data):
        # 因子计算逻辑
        return result
    
    def validate(self, data):
        # 数据验证
        return True
```

2. **注册因子** (factors/__init__.py):

```python
from quant_factor_system.factors.registry import register

register(MyFactor)
```

3. **使用因子**:

```python
from quant_factor_system.factors import get_factor

factor = get_factor('my_factor', param1=15)
result = factor.compute(data)
```

### 添加新止损策略

1. **创建止损类** (stoploss/my_stoploss.py):

```python
from quant_factor_system.core.base import StopLossStrategy

class MyStopLoss(StopLossStrategy):
    name = 'my_stoploss'
    
    def check(self, entry_price, current_price, **kwargs):
        # 止损逻辑
        return should_stop
```

2. **注册并使用** (同因子注册方式)

---

*最后更新: 2026-02-19*
