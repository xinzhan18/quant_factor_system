# QuantFactorSystem v3.0

量化因子分析系统

## 🚀 启动方式

### 必需步骤（重要！）

```bash
# 1. 激活 conda 环境
conda activate quantfactor

# 2. 进入项目目录
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system

# 3. 安装项目包（首次或更新后）
pip install -e .

# 4. 启动 Dashboard
cd dashboard
streamlit run Home.py
```

**Dashboard 访问地址:** http://localhost:8501

---

## 📊 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    QuantFactor System                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Dashboard  │    │   Pipeline    │    │   CLI/Term   │  │
│  │  (Streamlit) │    │   (Engine)    │    │   (Python)   │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │           │
│         └───────────────────┼───────────────────┘           │
│                             │                               │
│                    ┌────────▼────────┐                     │
│                    │  FactorStorage   │                     │
│                    │  (因子存储引擎)   │                     │
│                    └────────┬────────┘                     │
│                             │                               │
│         ┌───────────────────┼───────────────────┐          │
│         │                   │                   │          │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐    │
│  │  分钟因子    │    │   日级因子   │    │   周级因子   │    │
│  │  (窄表分区)  │    │   (宽表)     │    │   (宽表)     │    │
│  │ ~7.5亿/年   │    │ ~365万/年    │    │ ~26万/年     │    │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    │
│         │                   │                   │          │
│  ┌──────▼──────────────────────────────────────────────┐    │
│  │                  PostgreSQL 16                      │    │
│  │              (localhost:5432/quant)                 │    │
│  └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗄️ 数据库连接信息

| 配置 | 值 |
|------|-----|
| 主机 | localhost |
| 端口 | 5432 |
| 数据库 | quant |
| 用户 | postgres |
| 密码 | postgres |

---

## 📁 目录结构

```
quant_factor_system/
├── run.sh              # 主启动脚本
├── cli.py              # CLI工具
├── setup.py            # 包配置
│
├── core/               # 核心模块
│   └── base.py         # Factor基类
│
├── data/               # 数据模块
│   ├── postgres_db.py   # PostgreSQL 通用管理
│   ├── timescale_db.py   # TimescaleDB (兼容)
│   ├── data_manager.py   # 数据管理
│   └── factor_storage.py  # ⭐ 因子存储引擎
│
├── factors/            # 因子模块
│   ├── __init__.py     # 导出注册表和工厂
│   ├── registry.py      # 因子注册表
│   ├── factory.py       # 因子工厂
│   ├── basic/          # 基础因子
│   │   ├── factors.py
│   │   └── return_factors.py
│   └── ...
│
├── pipeline/           # Pipeline
│   └── pipeline.py     # Pipeline引擎
│
└── dashboard/          # Web界面
    ├── Home.py         # 首页
    ├── pages/
    │   ├── Factors.py  # 因子评估
    │   └── Pipeline.py # Pipeline组合
    └── start_dashboard.sh
```

---

## 🗄️ 因子存储架构

### 设计原则

1. **按频率分表** - 不同频率的因子分开存储
2. **宽表 + 窄表** - 平衡存储空间和查询效率
3. **时间分区** - 分钟级因子按月分区，便于管理
4. **持久化存储** - 所有数据永久保存

### 表结构

#### 1. 因子配置表 `factor_config`

```sql
CREATE TABLE factor_config (
    name VARCHAR(100) PRIMARY KEY,      -- 因子名称
    display_name VARCHAR(200),           -- 显示名称
    category VARCHAR(50),               -- 类别 (tech, return, etc.)
    frequency VARCHAR(20) NOT NULL,     -- 频率 (minute, daily, weekly)
    storage_type VARCHAR(20) NOT NULL,  -- 存储类型 (wide, narrow)
    description TEXT,
    unit VARCHAR(50),                   -- 单位
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### 2. 分钟因子 `minute_factor_values` (窄表分区)

| 字段 | 类型 | 说明 |
|------|------|------|
| factor_name | VARCHAR(100) | 因子名称 |
| symbol | VARCHAR(20) | 股票代码 |
| timestamp | TIMESTAMP | 时间戳 |
| factor_value | FLOAT | 因子值 |
| ic | FLOAT | 信息系数 |
| created_at | TIMESTAMP | 创建时间 |

**数据量**: 5000股票 × 每分钟 × 252天 ≈ **7.5亿/年**

**分区**: 按月自动分区 (`minute_factor_values_2026_01`, etc.)

#### 3. 日级因子 `daily_factors_wide` (宽表)

| 字段 | 类型 | 说明 |
|------|------|------|
| symbol | VARCHAR(20) | 股票代码 |
| date | DATE | 日期 |
| momentum_5d/10d/20d/60d | FLOAT | 动量因子 |
| return_1d/5d/10d/20d/60d | FLOAT | 收益率因子 |
| ma_5/10/20/60 | FLOAT | 均线因子 |
| dist_ma10/20 | FLOAT | 均线偏离度 |
| rsi_14 | FLOAT | RSI |
| zscore_60 | FLOAT | Z分数 |
| volatility_20d | FLOAT | 波动率 |
| updated_at | TIMESTAMP | 更新时间 |

**数据量**: 5000股票 × 每天 × 20因子 ≈ **3650万/年**

---

## 📈 数据量估算

| 场景 | 股票数 | 频率 | 因子数 | 年数据量 | 存储方案 |
|------|--------|------|--------|----------|----------|
| 高频 | 5000 | 分钟 | 1 | 7.5亿 | 窄表 + 分区 |
| 中频 | 5000 | 分钟 | 10 | 75亿 | 窄表 + 分区 |
| 低频 | 5000 | 日 | 20 | 3650万 | 宽表 |
| 低频 | 5000 | 日 | 100 | 1.8亿 | 窄表 |
| 超低频 | 5000 | 周 | 10 | 260万 | 宽表 |

**存储空间估算**:
- 分钟因子: ~100GB/年 (1因子) / ~1TB/年 (10因子)
- 日级因子: ~3GB/年 (20因子宽表) / ~15GB/年 (100因子窄表)

---

## 🔧 使用示例

### 1. 初始化因子存储

```python
from quant_factor_system.data import init_factor_storage

# 初始化（创建表和分区）
storage = init_factor_storage()

# 查看统计
print(storage.get_stats())
```

### 2. 注册新因子

```python
from quant_factor_system.data import get_factor_storage

storage = get_factor_storage()

# 注册分钟级因子（窄表存储）
storage.register_factor(
    name="momentum_1min",
    frequency="minute",
    storage_type="narrow",
    category="tech",
    display_name="1分钟动量因子",
    unit="ratio"
)

# 注册日级因子（宽表存储）
storage.register_factor(
    name="momentum_20d",
    frequency="daily",
    storage_type="wide",
    category="tech",
    display_name="20日动量因子",
    unit="percent"
)
```

### 3. 保存分钟因子数据

```python
import pandas as pd
from quant_factor_system.data import get_factor_storage

storage = get_factor_storage()

# 模拟分钟数据
df = pd.DataFrame({
    'symbol': ['AAPL'] * 100,
    'timestamp': pd.date_range('2026-01-01', periods=100, freq='1min'),
    'factor_value': [0.01 * i for i in range(100)]
})

# 保存到窄表
storage.save_minute_factor("momentum_1min", df, ic=0.05)
```

### 4. 保存日级因子数据

```python
import pandas as pd
from quant_factor_system.data import get_factor_storage

storage = get_factor_storage()

# 日级数据（宽表格式）
df = pd.DataFrame({
    'symbol': ['AAPL', 'GOOGL', 'MSFT'],
    'date': pd.to_datetime(['2026-01-01'] * 3),
    'momentum_20d': [0.05, 0.03, 0.07],
    'rsi_14': [55, 60, 45],
    'return_1d': [0.01, -0.02, 0.015]
})

# 保存到宽表
storage.save_daily_factor(df)
```

### 5. 查询数据

```python
# 查询分钟因子
minute_data = storage.query_minute_factor(
    factor_name="momentum_1min",
    symbols=["AAPL", "GOOGL"],
    start=datetime(2026, 1, 1),
    end=datetime(2026, 1, 2),
    limit=10000
)

# 查询日级因子
daily_data = storage.query_daily_factor(
    symbols=["AAPL", "GOOGL"],
    start_date=datetime(2026, 1, 1),
    end_date=datetime(2026, 1, 31),
    factor_columns=["momentum_20d", "rsi_14"]
)
```

---

## 📦 内置因子

| 因子名 | 类名 | 类别 | 说明 |
|--------|------|------|------|
| momentum | MomentumFactor | tech | 动量因子 |
| ma | MovingAverage | tech | 移动平均 |
| rsi | RSI | tech | 相对强弱 |
| return_1d | Return1dFactor | return | 1日收益 |
| return_5d | Return5dFactor | return | 5日收益 |
| return_20d | Return20dFactor | return | 20日收益 |
| dist_ma10 | DistMA10Factor | tech | 均线偏离 |
| zscore_60 | ZScore60Factor | tech | Z分数 |

---

## 📈 Dashboard 页面

1. **首页 (Home.py)**
   - 系统状态概览
   - 数据库统计
   - 快速创建因子

2. **因子评估 (Factors.py)**
   - 选择已有因子
   - 设置参数
   - 查看 IC、收益分析
   - 保存到数据库

3. **Pipeline (Pipeline.py)**
   - 多因子组合
   - 参数配置
   - 累计收益曲线

---

## 🛠️ 维护命令

```bash
# 数据库
./scripts/db.sh start      # 启动
./scripts/db.sh stop       # 停止
./scripts/db.sh shell      # 进入命令行

# 数据
./scripts/data.sh sample   # 生成示例数据
./scripts/data.sh import file.csv

# 系统
./run.sh info       # 系统信息
./run.sh init       # 初始化
./run.sh clean      # 清理
```

---

## 📋 更新日志 (2026-02-10)

### v3.0 - 因子存储架构重构

#### 新增功能
- ✅ **FactorStorage** - 全新因子存储引擎
- ✅ **分区表** - 分钟因子按月分区
- ✅ **宽表设计** - 日级因子列式存储
- ✅ **因子配置表** - 统一管理因子元信息
- ✅ **自动分区创建** - 智能分区管理
- ✅ **持久化存储** - 所有数据永久保存

#### 架构优势
- 1. **高性能** - 宽表查询快，分区管理易
- 2. **可扩展** - 支持任意频率和因子数量
- 3. **易维护** - 分区表便于备份和清理
- 4. **成本可控** - 按需选择宽表/窄表
