# 量化因子系统 - 需求与规划

## 📌 核心愿景

构建一个**端到端的量化因子研究平台**，支持：
1. 因子发现与研究（从论文、PDF 中复现）
2. 因子评估（IC、分组回测、多空收益）
3. 因子组合（选出表现好的因子，构建投资组合）
4. Dashboard 可视化与管理

---

## 🎯 核心功能需求

### 1. 因子评估引擎
- ✅ 已有基础框架
- 需要增强：
  - IC 序列分析（时间序列稳定性）
  - IC 衰减分析
  - 分组收益归因
  - 换手率分析
  - 因子相关性分析

### 2. 因子筛选与组合
- 因子有效性筛选（IC > 0.02, 胜率 > 50%）
- 因子相关性过滤（剔除高相关因子）
- 因子权重优化（等权、IC 权、优化器）
- 复合因子构建

### 3. 选股功能
- 基于因子值的股票筛选
- 多因子综合打分
- 持仓管理

### 4. Dashboard 可视化（Streamlit 原型）
- 因子表现总览
- 实时因子监控
- 组合绩效展示
- 交互式分析

### 5. 因子研究工作流
- PDF/论文因子复现模板
- 自定义因子开发框架
- 因子版本管理

---

## 🏗️ 架构设计

### 当前结构
```
quant_factor_system/
├── core/           # 核心类
├── factors/        # 因子模块
├── data/           # 数据模块
├── evaluation/     # 评估模块
├── trading/        # 交易模块
├── automation/     # 自动化模块
└── visualization/  # 可视化模块
```

### 完整结构
```
quant_factor_system/
├── core/              # 核心类（保持）
├── factors/           # 因子模块（保持）
│   ├── basic/        # 基础因子
│   ├── barra/        # Barra 因子
│   └── custom/       # 自定义因子模板
├── data/             # 数据模块（保持）
├── evaluation/       # 评估模块（增强）
├── trading/          # 交易模块（增强）
├── research/         # 研究工作流
│   └── templates/    # 因子复现模板
├── dashboard/        # Streamlit Dashboard
│   ├── pages/        # 页面
│   │   ├── 1_因子评估.py
│   │   ├── 2_因子筛选.py
│   │   ├── 3_选股.py
│   │   └── 4_历史回测.py
│   ├── components/   # 组件
│   ├── utils/        # 工具
│   └── config.py     # 配置
└── storage/          # 【核心】存储层
    ├── database/      # SQLite
    │   └── factors.db
    ├── data/          # CSV 文件
    │   ├── factors/   # 因子原始数据
    │   └── backtests/# 回测历史
    └── cache/         # 缓存
        └── cache.pkl
```

---

## 💾 存储层设计

### 技术选型

| 类型 | 方案 | 用途 |
|------|------|------|
| **数据库** | SQLite | 持久化存储（评估结果、因子配置）|
| **文件** | CSV | 因子原始数据、回测历史 |
| **缓存** | Pickle | 内存缓存（加速读取）|

### 数据目录结构

```
storage/
├── database/
│   └── factors.db          # SQLite 数据库
├── data/
│   ├── factors/            # 因子数据（CSV）
│   │   ├── momentum.csv
│   │   ├── value.csv
│   │   └── ...
│   ├── market/            # 市场数据
│   │   └── a_stock_2024.csv
│   └── backtests/         # 回测结果
│       ├── 2024_01_01_momentum.csv
│       └── ...
└── cache/
    └── cache.pkl          # Pickle 缓存
```

### SQLite 数据模型

```sql
-- 因子定义表
CREATE TABLE factors (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    category TEXT,              -- momentum, value, quality, etc.
    description TEXT,
    params TEXT,                -- JSON 参数字符串
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 评估结果表
CREATE TABLE evaluations (
    id INTEGER PRIMARY KEY,
    factor_id INTEGER NOT NULL,
    eval_date DATE NOT NULL,
    period_start DATE,
    period_end DATE,
    ic REAL,                   # 信息系数
    ic_ir REAL,                # IC IR
    ic_std REAL,               # IC 标准差
    win_rate REAL,             # 胜率
    long_short_return REAL,     # 多空收益
    group_returns TEXT,         # JSON 各组收益
    num_groups INTEGER,
    num_samples INTEGER,        # 样本数量
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (factor_id) REFERENCES factors(id),
    UNIQUE(factor_id, eval_date)
);

-- 选股结果表
CREATE TABLE stock_selections (
    id INTEGER PRIMARY KEY,
    factor_id INTEGER,
    selection_date DATE NOT NULL,
    stock_code TEXT NOT NULL,
    factor_value REAL,
    rank INTEGER,
    weight REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (factor_id) REFERENCES factors(id)
);

-- 回测记录表
CREATE TABLE backtests (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    config TEXT,               -- JSON 配置
    start_date DATE,
    end_date DATE,
    total_return REAL,
    sharpe_ratio REAL,
    max_drawdown REAL,
    results TEXT,               -- JSON 详细结果
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 存储接口

```python
# storage/database.py
import sqlite3
import pandas as pd
import json
from typing import Dict, List, Optional

class FactorDatabase:
    """SQLite 数据库封装"""
    
    def __init__(self, db_path: str = "storage/database/factors.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        # 创建表的 SQL
        pass
    
    # 因子 CRUD
    def add_factor(self, name: str, category: str, params: Dict):
        pass
    
    def get_factor(self, name: str) -> Optional[Dict]:
        pass
    
    def list_factors(self, category: str = None) -> pd.DataFrame:
        pass
    
    # 评估结果
    def save_evaluation(self, factor_name: str, results: Dict):
        pass
    
    def get_evaluations(self, factor_name: str, 
                        start_date: str = None,
                        end_date: str = None) -> pd.DataFrame:
        pass
    
    # 选股结果
    def save_stock_selection(self, factor_name: str, 
                             selection_date: str,
                             stocks: List[Dict]):
        pass
    
    def get_stock_selections(self, factor_name: str,
                             selection_date: str = None) -> pd.DataFrame:
        pass
```

---

## 📊 Dashboard 设计（Streamlit）

### 页面结构

```
Dashboard (Streamlit)
├── Sidebar（侧边栏）
│   ├── 页面导航
│   ├── 数据刷新
│   └── 设置
│
├── Pages（页面）
│   ├── 1_首页.py              # 总览
│   ├── 2_因子评估.py          # 因子表现
│   ├── 3_因子筛选.py          # 选股
│   ├── 4_组合管理.py          # 组合构建
│   └── 5_历史回测.py          # 回测记录
│
└── Components（组件）
    ├── ic_chart.py            # IC 曲线图
    ├── group_returns.py       # 分组收益图
    ├── factor_table.py        # 因子表格
    └── stock_picker.py        # 选股器
```

### 页面功能

#### 1. 首页（总览）
```python
# 页面元素
st.title("📊 量化因子 Dashboard")

# 统计卡片
col1, col2, col3, col4 = st.columns(4)
col1.metric("因子总数", 15)
col2.metric("今日评估", 5)
col3.metric("最佳因子", "Momentum")
col4.metric("平均 IC", "0.03")

# 最新评估表格
st.subheader("最新因子评估")
st.dataframe(get_latest_evaluations())

# 性能图表
st.subheader("因子 IC 走势")
st.linechart(get_ic_history())
```

#### 2. 因子评估（详情页）
```python
# 侧边栏选择因子
factor = st.selectbox("选择因子", get_factors())

# 评估指标
ic, ic_ir, win_rate = get_evaluation(factor)

# IC 序列图
st.subheader("IC 时间序列")
st.linechart(get_ic_series(factor))

# 分组收益
st.subheader("分组收益")
st.bar_chart(get_group_returns(factor))

# IC 衰减
st.subheader("IC 衰减")
st.linechart(get_ic_decay(factor))
```

#### 3. 因子筛选（选股）
```python
# 筛选条件
threshold = st.slider("IC 阈值", 0.0, 0.1, 0.02)
win_rate_threshold = st.slider("胜率阈值", 0.4, 0.6, 0.5)

# 获取达标因子
qualified_factors = get_qualified_factors(threshold, win_rate_threshold)

# 选股
selected_factor = st.selectbox("选择因子", qualified_factors)
num_stocks = st.slider("选股数量", 10, 100, 50)

# 选股结果
stocks = get_top_stocks(selected_factor, num_stocks)
st.dataframe(stocks)
```

#### 4. 组合管理
```python
# 选择因子组合
selected_factors = st.multiselect("选择因子", get_factors())

# 权重设置
weights = {}
for f in selected_factors:
    weights[f] = st.slider(f"{f} 权重", 0.0, 1.0, 1.0/len(selected_factors))

# 组合得分
composite_score = calculate_composite_score(selected_factors, weights)

# 持仓建议
holdings = generate_holdings(composite_score, top_n=50)
st.dataframe(holdings)
```

---

## 📋 实施计划

### Phase 1: 存储层 ✅ 已完成
**目标**：实现 SQLite 数据库和数据模型

- [x] 1.1 创建存储目录结构
  - [x] `storage/database/`
  - [x] `storage/data/factors/`
  - [x] `storage/data/backtests/`
  - [x] `storage/cache/`

- [x] 1.2 实现 SQLite 数据库封装
  - [x] `FactorDatabase` 类
  - [x] 因子 CRUD 接口
  - [x] 评估结果接口
  - [x] 选股结果接口

- [x] 1.3 实现 CSV 文件读写
  - [x] 因子数据读写
  - [x] 回测历史读写

- [x] 1.4 实现缓存层
  - [x] Pickle 缓存封装

**完成时间**: 2026-02-08

---

### Phase 2: Streamlit Dashboard 原型 ✅ 已完成
**目标**：构建可交互的 Dashboard

- [x] 2.1 项目初始化
  - [x] 创建 Streamlit 项目结构
  - [x] 配置 `config.py`
  - [x] 设置页面布局

- [x] 2.2 首页开发
  - [x] 统计卡片
  - [x] 最新评估表格
  - [x] IC 走势图

- [x] 2.3 因子评估页面
  - [x] 因子选择器
  - [x] IC 序列图
  - [x] 分组收益图
  - [x] IC 衰减曲线

- [x] 2.4 因子筛选页面
  - [x] IC/胜率阈值筛选
  - [x] 选股器
  - [x] 导出功能

- [x] 2.5 组合管理页面
  - [x] 因子多选
  - [x] 权重设置
  - [x] 复合因子计算

**完成时间**: 2026-02-08

---

### Phase 3: 因子评估增强 ⏳ 进行中
**目标**：增强评估功能

- [ ] 3.1 IC 序列分析
  - [ ] 时间序列图
  - [ ] 滚动 IC（rolling IC）
  - [ ] IC 分布直方图
  - [ ] IC 统计检验（t-test）

- [ ] 3.2 分组收益增强
  - [ ] 分组净值曲线
  - [ ] 换手率统计
  - [ ] 最大回撤
  - [ ] 分组夏普比率

- [ ] 3.3 因子相关性
  - [ ] 相关性热力图
  - [ ] 因子 IC 相关性
  - [ ] 因子冗余检测

- [ ] 3.4 IC 衰减分析
  - [ ] IC_decay 曲线
  - [ ] 预测期限分析

- [ ] 3.5 增强评估结果保存
  - [ ] 完整 IC 序列保存
  - [ ] 分组收益详情保存
  - [ ] 相关性矩阵保存

**计划完成时间**: 1 周

---

### Phase 4: 选股与组合（待开始）
**目标**：实现选股和组合功能

- [ ] 4.1 单因子选股
  - [ ] Top-N 选股
  - [ ] 分层选股

- [ ] 4.2 多因子选股
  - [ ] 因子标准化
  - [ ] 综合打分
  - [ ] 权重优化

- [ ] 4.3 持仓管理
  - [ ] 持仓生成
  - [ ] 权重分配
  - [ ] 信号输出

---

### Phase 5: 因子研究工作流（长期）
**目标**：支持因子复现与管理

- [ ] 5.1 因子模板
  - [ ] 因子开发模板
  - [ ] 论文复现指南

- [ ] 5.2 因子版本管理
  - [ ] 版本控制
  - [ ] 历史回测记录

---

## 🔧 技术栈

| 模块 | 技术选型 |
|------|---------|
| Dashboard | Streamlit |
| 数据库 | SQLite |
| 文件格式 | CSV, JSON |
| 缓存 | Pickle |
| 图表 | Altair/Plotly |
| 部署 | Docker（可选）|

---

## 📅 开发顺序

```
Week 1: 存储层（SQLite + 文件读写）
    ↓
Week 2-3: Streamlit Dashboard 原型
    ↓
Week 4: 评估增强 + 选股功能
    ↓
长期: 研究工作流
```

---

## 🚀 快速启动

```bash
# 1. 安装依赖
pip install streamlit pandas sqlalchemy

# 2. 启动 Dashboard
cd quant_factor_system/dashboard
streamlit run Home.py

# 3. 访问
# http://localhost:8501
```

---

*文档版本: 2.0*
*最后更新: 2026-02-08*
