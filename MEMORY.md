# Long-Term Memory

## Project: Quant Factor Trading Platform

### Overview
Complete quantitative factor research and trading platform with:
- **Data Layer**: TimescaleDB (production)
- **Factor Layer**: Minute-to-daily aggregation, multiple methods
- **Selection Layer**: Single/multi-factor selection, filtering
- **Position Layer**: Equal weight, factor weighted, Kelly formula
- **Stop-Loss Layer**: Fixed, ATR-based, trailing stops
- **Backtest Engine**: Full simulation and performance analysis
- **Dashboard**: Strategy config, results display, task monitoring

### Technical Stack
- Python 3.8+
- Streamlit for Dashboard
- Pandas/NumPy/SciPy for data processing
- TimescaleDB (production only, SQLite removed)

---

## 📋 新工作流程 (2026-02-19)

### 需求处理流程

1. **接收需求** → 用户描述需求
2. **创建需求文档** → `docs/plan/YYYY-MM-DD/需求名称_plan.md`
   - 目前的状况
   - 需要完成的需求
   - 需求list及状态
   - 每个需求的独立任务
3. **执行任务** → 查看需求文档，判断下一步
4. **更新文档** → 执行完后更新文档状态
5. **自动执行** → 继续下一个任务
6. **推送代码** → 完成所有任务后push到GitHub

### 文档位置

```
docs/
├── PROJECT_OVERVIEW.md    # 项目概览 (架构、启动方式等)
├── ARCHITECTURE.md       # 详细架构文档
├── TASK_PLAN.md          # 任务计划
└── plan/
    └── OVERVIEW.md       # 总览 (所有需求和状态)
```

### 关键规则

1. **需求文档格式**: `docs/plan/YYYY-MM-DD/xxx_plan.md`
2. **总览文档**: `docs/plan/OVERVIEW.md`
3. **项目概览**: `docs/PROJECT_OVERVIEW.md`
4. **避免一次性脚本**: 放 scripts/ 目录方便管理
5. **更新依赖**: 同时更新 requirements.txt 和文档
6. **优先重构**: 在现有文档上修改，不随意创建新文档
7. **代码质量**: 保证清晰、可扩展，直接重构旧代码

### 启动命令

```bash
# 启动 Dashboard
cd /Users/xinzhan/.openclaw/workspace
/Users/xinzhan/miniconda3/envs/quantfactor/bin/streamlit run quant_factor_system/dashboard/Home.py

# 运行因子计算
/Users/xinzhan/miniconda3/envs/quantfactor/bin/python recompute_factors.py
```

---

## 📦 模块结构

```
quant_factor_system/
├── data/                    # 数据模块
│   ├── clean/             # 数据清洗/验证
│   └── ...
├── factors/                # 因子模块
│   ├── visualization/     # IC分析、分组收益
│   └── ...
├── backtest/              # 回测模块
│   ├── selection/         # 因子选择、过滤、排名
│   ├── signal/           # 信号生成
│   └── ...
├── dashboard/             # Web界面
│   ├── components/       # 通用组件
│   └── pages/            # 页面
└── docs/                 # 文档
    ├── PROJECT_OVERVIEW.md
    ├── ARCHITECTURE.md
    └── plan/
        └── OVERVIEW.md
```

---

## 🚀 Repository Rules

**每次代码更新后必须push到云端**

```bash
git add -A
git commit -m "feat: 描述你的更改"
git push origin main
```

---

## 📊 Data Source

- **Primary**: RiceQuant (米筐) - 唯一数据源
- 所有数据通过 `ricequant_source.py` 获取

### 正确的执行模式

```python
# 使用项目模块
cd /Users/xinzhan/.openclaw/workspace
/Users/xinzhan/miniconda3/envs/quantfactor/bin/python -c "
import os
os.environ['RQDATAC_CONF'] = 'xxx'

from quant_factor_system.data import TimescaleDB
db = TimescaleDB()
# ...
"
```

**环境配置**：
- Conda 环境: `quantfactor`
- Python 路径: `/Users/xinzhan/miniconda3/envs/quantfactor/bin/python`

---

## 📈 Industry Factor Management

| 因子类型 | 更新频率 | 示例 |
|---------|---------|------|
| 行业归属 | 季度 | 中信一级行业 |
| 行业收益率 | 每日 | 行业日收益率 |
| 行业动量 | 每日 | 20日行业累计收益 |

---

*Last updated: 2026-02-19*
