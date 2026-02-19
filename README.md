# QuantFactorSystem v3.0

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
├── data/                   # 数据模块
│   ├── postgres_db.py      # PostgreSQL 通用管理
│   ├── timescale_db.py     # TimescaleDB (生产环境)
│   ├── data_manager.py     # 数据管理
│   ├── factor_storage.py   # 因子存储引擎
│   └── clean/              # 数据清洗/验证
│
├── factors/                # 因子模块
│   ├── registry.py         # 因子注册表
│   ├── factory.py          # 因子工厂
│   ├── basic/              # 基础因子
│   │   ├── factors.py      # 动量、均线、RSI等
│   │   └── return_factors.py
│   ├── aggregator.py       # 因子聚合
│   ├── processor.py        # 因子处理
│   └── visualization/      # IC分析、分组收益可视化
│
├── backtest/               # 回测模块
│   ├── engine.py           # 回测引擎
│   ├── analyzer.py         # 绩效分析
│   ├── selection/          # 因子选择
│   │   ├── single.py       # 单因子选股
│   │   ├── multi.py        # 多因子选股
│   │   └── filter.py       # 因子过滤与排名
│   └── signal/             # 信号生成
│
├── selector/                # 选股模块 (冗余，指向 backtest/selection)
│
├── position/               # 仓位模块
│   ├── equal.py            # 等权配置
│   ├── factor.py           # 因子里重
│   └── kelly.py            # 凯利公式
│
├── stoploss/               # 止损模块
│   ├── fixed.py            # 固定止损
│   ├── atr.py              # ATR止损
│   └── trailing.py         # 追踪止损
│
├── pipeline/               # Pipeline
│   └── pipeline.py         # Pipeline引擎
│
├── dashboard/              # Web界面
│   ├── Home.py             # 首页
│   ├── pages/
│   │   ├── Factors.py      # 因子评估
│   │   ├── Pipeline.py     # Pipeline组合
│   │   └── Backtest.py     # 回测结果
│   └── components/         # 通用组件
│
├── core/                   # 核心模块
│   └── base.py             # Factor基类
│
├── examples/               # 示例代码
├── scripts/                # 工具脚本
├── docs/                   # 文档
└── tests/                  # 测试
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

### 行业因子 (industry)

| 因子类型 | 更新频率 | 示例 |
|---------|---------|------|
| 行业归属 | 季度 | 中信一级行业 |
| 行业收益率 | 每日 | 行业日收益率 |
| 行业动量 | 每日 | 20日行业累计收益 |

## 🔧 使用示例

### 1. 初始化因子存储

```python
from quant_factor_system.data import init_factor_storage

storage = init_factor_storage()
print(storage.get_stats())
```

### 2. 注册和计算因子

```python
from quant_factor_system.factors import MomentumFactor

factor = MomentumFactor(lookback=20)
result = factor.compute(data)
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

4. **回测 (Backtest)**
   - 策略配置
   - 绩效分析
   - 结果展示

## 🛠️ 维护命令

```bash
# 数据库管理
./scripts/db.sh start      # 启动
./scripts/db.sh stop       # 停止
./scripts/db.sh shell       # 进入命令行

# 数据操作
./scripts/data.sh sample   # 生成示例数据
./scripts/data.sh import file.csv

# 系统维护
./run.sh info       # 系统信息
./run.sh init       # 初始化
./run.sh clean      # 清理
```

## 📋 开发规范

### Git 工作流程

1. **可以 commit**: 每次完成需求或阶段性任务
2. **不能 push**: 所有 push 必须经过用户同意
3. **询问后 push**: 完成用户要求的所有任务后，询问是否 push

```bash
# 1. 添加更改
git add -A

# 2. 提交
git commit -m "feat: 描述你的更改"

# 3. ⚠️ 不要直接push！先询问用户
# ...
# 用户同意后:
git push origin main
```

### 代码规范

- 保持代码清晰、可扩展
- 优先重构旧代码，不随意创建新文件
- 一次性脚本放 `scripts/` 目录
- 更新依赖时同步更新 `requirements.txt` 和文档

## 📚 文档

- **项目概览**: `docs/PROJECT_OVERVIEW.md`
- **架构文档**: `docs/ARCHITECTURE.md`
- **任务计划**: `docs/plan/OVERVIEW.md`

## 🧰 技术栈

- **Python**: 3.8+
- **Web**: Streamlit
- **数据处理**: Pandas, NumPy, SciPy
- **数据库**: TimescaleDB (生产), SQLite (已移除)
- **可视化**: Matplotlib, Plotly
- **数据源**: RiceQuant (米筐)

## 📝 更新日志

### v3.0 (2026-02-10) - 因子存储架构重构

- ✅ **FactorStorage** - 全新因子存储引擎
- ✅ **分区表** - 分钟因子按月分区
- ✅ **宽表设计** - 日级因子列式存储
- ✅ **因子配置表** - 统一管理因子元信息
- ✅ **自动分区创建** - 智能分区管理
- ✅ **持久化存储** - 所有数据永久保存

---

*最后更新: 2026-02-19*
