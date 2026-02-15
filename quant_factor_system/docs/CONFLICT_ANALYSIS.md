# 现有项目分析与冲突诊断报告

## 📊 项目现状分析

### 1. 现有核心模块

| 模块 | 位置 | 功能 | 状态 |
|------|------|------|------|
| **Pipeline** | `pipeline/pipeline.py` | 因子管道引擎 | ✅ 完整 |
| **FactorStorage** | `data/factor_storage.py` | PostgreSQL因子存储 | ⚠️ 有冲突 |
| **因子基类** | `core/base.py` | Factor基类 | ✅ 完整 |
| **因子工厂** | `factors/factory.py` | 动态因子创建 | ✅ 完整 |
| **Dashboard** | `dashboard/` | Streamlit界面 | ⚠️ 部分实现 |
| **DataManager** | `data/data_manager.py` | 统一数据接口 | ✅ 完整 |

---

## 🔴 关键冲突点诊断

### 冲突1: 存储策略冲突 ⚠️ 严重

#### 现状
```python
# factor_storage.py 第450行
def _upsert_daily_row(self, row: pd.Series):
    sql = f"""
    INSERT INTO daily_factors_wide ({cols})
    VALUES ({values})
    ON CONFLICT (symbol, date) DO UPDATE SET {set_clause}, updated_at = NOW();
    """
```

**问题**: 使用 `UPSERT` (INSERT ... ON CONFLICT DO UPDATE)

#### 需求
```
因子值落库后不能变，只能新增 (APPEND ONLY)
```

#### 冲突后果
```
├── 数据被覆盖 → 研究结果不可复现
├── 历史版本丢失 → 无法追踪因子演变
└── 数据一致性 → 无法保证
```

#### 解决方案
```
选项A: 改为纯INSERT，移除UPDATE逻辑
选项B: 添加历史版本表 (推荐)
选项C: 使用事件溯源 (Event Sourcing)
```

**推荐**: 选项B - 添加历史版本表 + 唯一约束

---

### 冲突2: 数据模型冲突 ⚠️ 中等

#### 现状
```python
# factor_storage.py 第76行
class DailyFactorWide(Base):
    __tablename__ = 'daily_factors_wide'
    
    symbol = Column(String(20), nullable=False, primary_key=True)
    date = Column(Date, nullable=False, primary_key=True)
    
    # 宽表: 多个因子作为列
    momentum_5d = Column(Float)
    momentum_10d = Column(Float)
    rsi_14 = Column(Float)
    # ... 20+ 列
```

**问题**: 宽表设计，固定列结构

#### 需求
```
├── 分钟因子: 需要窄表 (factor_name, symbol, timestamp, value)
├── 日频因子: 可能需要窄表或宽表
└── 扩展性: 动态添加新因子
```

#### 冲突后果
```
├── 新增因子 → 需要修改表结构
├── 分钟因子 → 无法用宽表存储
└── 灵活查询 → 宽表难以实现
```

#### 解决方案
```
方案A: 保留宽表日频 + 新建窄表分钟
方案B: 全部改为窄表
方案C: 混合模式 (推荐)

推荐: 方案C
├── 日频: 宽表 (性能好)
├── 分钟: 窄表 (灵活)
└── 聚合: 分钟→日频后写入宽表
```

---

### 冲突3: 数据库依赖冲突 ⚠️ 轻微

#### 现状
```
FactorStorage 依赖:
├── PostgreSQL (必需)
├── TimescaleDB (时间序列扩展)
└── SQLAlchemy ORM
```

#### 需求
```
需求文档建议: SQLite (轻量)
但也可以保留PostgreSQL
```

#### 分析
```
SQLite 优点:
├── 无需安装 (开箱即用)
├── 单文件存储
└── 足够小规模使用

PostgreSQL 优点:
├── 高性能
├── 分区表
└── 成熟稳定

结论: 可以保留PostgreSQL，但需要适配APPEND ONLY
```

---

### 冲突4: 频率处理冲突 ✅ 已解决

#### 现状
```python
# pipeline/pipeline.py 第40行
class Frequency(Enum):
    TICK = 'tick'
    MINUTE_1 = '1min'
    MINUTE_5 = '5min'
    MINUTE_15 = '15min'
    MINUTE_30 = '30min'
    HOUR_1 = '1hour'
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
```

**状态**: ✅ 已有频率枚举，良好

#### 需求
```
分钟数据聚合到日频因子
```

**状态**: ⚠️ 缺少聚合逻辑

---

## 📋 冲突总结表

| 序号 | 冲突点 | 严重程度 | 影响范围 | 解决方案 |
|------|--------|----------|----------|----------|
| 1 | 存储策略 (UPSERT) | 🔴 严重 | 所有因子数据 | 改为APPEND ONLY + 版本表 |
| 2 | 数据模型 (宽表) | ⚠️ 中等 | 分钟因子存储 | 宽表日频 + 窄表分钟 |
| 3 | 数据库依赖 | ⚠️ 轻微 | 部署复杂度 | 保留PostgreSQL |
| 4 | 分钟聚合 | ✅ 已解决 | 频率处理 | 已有Frequency枚举 |

---

## 🛠️ 建议修复方案

### 修复1: 改为APPEND ONLY存储

```python
# 方案: 添加历史版本表

class FactorValueHistory(Base):
    """因子值历史表 - APPEND ONLY"""
    __tablename__ = 'factor_value_history'
    
    id = Column(BigInteger, autoincrement=True, primary_key=True)
    factor_name = Column(String(100), nullable=False)
    symbol = Column(String(20), nullable=False)
    date = Column(Date, nullable=False)
    frequency = Column(String(20), nullable=False)  # daily/minute/5min
    factor_value = Column(Float)
    
    # 血缘信息
    source_data = Column(String(200))  # 数据来源
    computation_time = Column(DateTime) # 计算时间
    
    # 审计字段
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    # 唯一约束 (防止重复插入)
    __table_args__ = (
        UniqueConstraint('factor_name', 'symbol', 'date', 'frequency', 
                       name='uq_factor_symbol_date_freq'),
    )
```

### 修复2: 添加分钟聚合器

```python
# 新文件: factors/aggregator.py

class MinuteAggregator:
    """
    分钟聚合器
    
    将分钟数据聚合到日频因子
    """
    
    AGG_METHODS = {
        'last': lambda x: x.iloc[-1],   # 最新值
        'mean': lambda x: x.mean(),      # 均值
        'max': lambda x: x.max(),        # 最大值
        'min': lambda x: x.min(),        # 最小值
        'std': lambda x: x.std(),        # 标准差
        'sum': lambda x: x.sum(),        # 求和
    }
    
    def __init__(self, method: str = 'last'):
        """
        Args:
            method: 聚合方法 (last/mean/max/min/std/sum)
        """
        if method not in self.AGG_METHODS:
            raise ValueError(f"不支持的聚合方法: {method}")
        self.method = method
    
    def aggregate(
        self,
        minute_df: pd.DataFrame,
        symbol_col: str = 'symbol',
        price_col: str = 'close',
        date_col: str = 'timestamp'
    ) -> pd.DataFrame:
        """
        将分钟数据聚合为日频因子
        
        Args:
            minute_df: 分钟级价格数据
            symbol_col: 股票代码列
            price_col: 价格列
            date_col: 时间戳列
            
        Returns:
            日频因子DataFrame
        """
        df = minute_df.copy()
        
        # 提取日期
        df['date'] = pd.to_datetime(df[date_col]).dt.date
        
        # 按股票和日期分组聚合
        agg_func = self.AGG_METHODS[self.method]
        
        result = df.groupby([symbol_col, 'date'])[price_col].apply(agg_func)
        result = result.reset_index()
        result.columns = [symbol_col, 'date', 'factor_value']
        
        return result
```

### 修复3: 统一数据接口

```python
# 新文件: data/unified_storage.py

class UnifiedFactorStorage:
    """
    统一因子存储
    
    支持:
    - APPEND ONLY (只增不改)
    - 宽表日频
    - 窄表分钟
    - SQLite/PostgreSQL双支持
    """
    
    def __init__(self, backend: str = 'sqlite'):
        """
        Args:
            backend: 'sqlite' | 'postgresql'
        """
        self.backend = backend
        self._init_storage()
    
    def save_factor(
        self,
        factor_name: str,
        df: pd.DataFrame,
        frequency: str = 'daily',
        **kwargs
    ) -> int:
        """
        保存因子 (APPEND ONLY)
        
        Returns:
            插入行数
        """
        if frequency == 'daily':
            return self._save_daily_wide(factor_name, df, **kwargs)
        else:
            return self._save_minute_narrow(factor_name, df, **kwargs)
    
    def _save_daily_wide(self, factor_name: str, df: pd.DataFrame, **kwargs):
        """保存日频因子 (宽表)"""
        # 宽表逻辑
        pass
    
    def _save_minute_narrow(self, factor_name: str, df: pd.DataFrame, **kwargs):
        """保存分钟因子 (窄表)"""
        # 窄表逻辑
        pass
```

---

## 📁 建议的代码修改

### 修改清单

| 文件 | 修改内容 | 优先级 |
|------|----------|--------|
| `data/factor_storage.py` | 改为APPEND ONLY + 添加历史表 | P0 |
| `factors/aggregator.py` | 新建分钟聚合器 | P0 |
| `data/unified_storage.py` | 新建统一存储接口 | P1 |
| `data/ricequant_source.py` | 新建米筐数据源 | P1 |
| `pipeline/pipeline.py` | 适配新的存储逻辑 | P1 |

### 不需要修改的模块

```
✅ core/base.py - 因子基类 (设计良好)
✅ factors/factory.py - 因子工厂 (设计良好)
✅ factors/registry.py - 因子注册表 (设计良好)
✅ data/data_manager.py - 数据管理器 (可扩展)
```

---

## 🎯 结论与建议

### 1. 总体评估

```
现有项目完成度: 70%

核心优势:
├── Pipeline设计 (借鉴Zipline) ✅
├── 因子工厂模式 ✅
├── 多频率支持 ✅
└── Dashboard原型 ✅

主要缺陷:
├── 存储策略 (UPSERT问题) 🔴
├── 分钟因子存储 ⚠️
└── 米筐数据源缺失 ⚠️
```

### 2. 推荐行动

```
Phase 1: 修复存储冲突 (1-2天)
├── 1.1 添加APPEND ONLY逻辑
├── 1.2 添加历史版本表
└── 1.3 添加唯一约束

Phase 2: 补充缺失模块 (3-5天)
├── 2.1 分钟聚合器
├── 2.2 米筐数据源
└── 2.3 统一存储接口

Phase 3: 完善功能 (1周)
├── 3.1 回测引擎
├── 3.2 仓位管理
└── 3.3 Dashboard完善
```

### 3. 是否需要重构?

```
问题: 是否需要大规模重构?

答案: 不需要

理由:
├── Pipeline设计良好，无需修改
├── 因子基类完整，无需修改
├── 只有存储层需要小规模修改
└── 整体架构稳定

建议: 增量式修改，而非推倒重来
```

---

*文档版本: 1.0*
*分析时间: 2026-02-15*
*作者: OpenClaw*
