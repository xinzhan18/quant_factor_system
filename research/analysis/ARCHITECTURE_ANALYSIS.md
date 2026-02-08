# 量化因子分析库 - 架构深度分析

## 摘要

本报告深入分析 Alphalens、QuantStats、Zipline 三个库的**核心架构设计**，提取可借鉴的工程模式。

---

## 1. Zipline Pipeline 架构分析

### 1.1 核心设计理念

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Zipline Pipeline 架构                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                  │
│  │   Factor   │───▶│   Filter    │───▶│ Classifier  │                  │
│  │   (因子)    │    │   (过滤)    │    │  (分类)     │                  │
│  └─────────────┘    └─────────────┘    └─────────────┘                  │
│         │                  │                  │                           │
│         └──────────────────┼──────────────────┘                           │
│                            ▼                                            │
│                   ┌─────────────────┐                                    │
│                   │     Term       │ ◀── 基类                           │
│                   │   (计算项)      │                                    │
│                   └─────────────────┘                                    │
│                            │                                            │
│         ┌───────────────────┼───────────────────┐                         │
│         ▼                   ▼                   ▼                         │
│  ┌───────────┐      ┌───────────┐      ┌───────────┐                  │
│  │ Computable│      │   Asset   │      │  Constant │                  │
│  │   Term    │      │  Exists   │      │           │                  │
│  └───────────┘      └───────────┘      └───────────┘                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Term 类核心设计 (term.py)

```python
class Term(metaclass=ABCMeta):
    """
    Pipeline 中所有计算项的基类
    
    核心特性:
    1. 记忆化 (Memoization): 相同参数返回相同实例
    2. 惰性计算 (Lazy): 按需计算
    3. 依赖追踪: 自动追踪计算依赖
    """
    
    # 子类必须定义
    dtype = NotSpecified           # 数据类型
    missing_value = NotSpecified    # 缺失值
    
    # 可选配置
    params = ()                     # 额外参数
    domain = GENERIC               # 领域
    window_safe = False            # 窗口安全
    
    # 缓存
    _term_cache = WeakValueDictionary()
    
    def __new__(cls, ...):
        # 记忆化: 相同参数返回相同实例
        identity = cls._static_identity(...)
        if identity in cls._term_cache:
            return cls._term_cache[identity]
        return super().__new__(cls)
```

### 1.3 Factor 因子基类设计 (factor.py)

```python
class Factor(Term):
    """
    因子基类
    
    支持的操作:
    - 算术运算: +, -, *, /
    - 比较运算: >, <, >=, <=, ==
    - 统计运算: mean(), sum(), std(), rank()
    """
    
    def __init__(self, 
                 inputs=None,           # 输入数据
                 window_length=None,    # 窗口长度
                 dtype=None,            # 数据类型
                 missing_value=None,    # 缺失值
                 window_safe=False):   # 窗口安全
        ...
    
    # 子类示例
    class RSI(Factor):
        """
        相对强弱指标
        """
        window_length = 14
        
        def compute(self, window):
            # 计算 RSI
            return rsi_values
```

### 1.4 Pipeline 引擎设计 (engine.py)

```python
class PipelineEngine:
    """
    Pipeline 执行引擎
    
    工作流程:
    1. 构建计算图 (DAG)
    2. 拓扑排序
    3. 批量执行
    """
    
    def run_pipeline(self, pipeline, start_date, end_date):
        """
        执行 Pipeline
        
        Returns:
            DataFrame: (date, asset) -> values
        """
        # 1. 初始化输出数组
        results = {}
        
        # 2. 按依赖顺序计算
        for term in self._get_compute_order(pipeline):
            if term in pipeline.outputs:
                results[term] = term.compute(
                    starts=dates,
                    **inputs
                )
        
        return results
```

### 1.5 可借鉴的设计模式

| 模式 | Zipline 实现 | 我们的借鉴 |
|------|-------------|----------|
| **记忆化** | `_term_cache` | 因子缓存，避免重复计算 |
| **惰性计算** | `compute()` 延迟 | 按需计算，节省资源 |
| **DAG 执行** | 拓扑排序 | 自动处理依赖 |
| **窗口安全** | `window_safe` flag | 处理边界条件 |
| **统一接口** | `Term` 基类 | 一致性 API |

---

## 2. Alphalens Tearsheet 架构

### 2.1 报告生成流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Alphalens Tearsheet 流程                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────┐                                                       │
│   │ factor_data │ ◀── 输入: MultiIndex DataFrame                        │
│   │             │    (date, asset) -> factor, returns, quantile         │
│   └──────┬──────┘                                                       │
│          │                                                               │
│          ▼                                                               │
│   ┌─────────────┐                                                       │
│   │ performance │ ◀── 计算层                                             │
│   │             │    - IC 计算                                            │
│   │             │    - 分组收益                                           │
│   │             │    - 换手率分析                                         │
│   └──────┬──────┘                                                       │
│          │                                                               │
│          ▼                                                               │
│   ┌─────────────┐                                                       │
│   │   plotting  │ ◀── 可视化层                                           │
│   │             │    - IC 热力图                                          │
│   │             │    - 分组收益图                                          │
│   │             │    - 换手率图                                           │
│   └──────┬──────┘                                                       │
│          │                                                               │
│          ▼                                                               │
│   ┌─────────────┐                                                       │
│   │    tears    │ ◀── 报告层                                             │
│   │             │    - GridFigure (网格布局)                              │
│   │             │    - 多图表组合                                         │
│   │             │    - HTML 输出                                         │
│   └─────────────┘                                                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 GridFigure 布局系统

```python
class GridFigure:
    """
    网格图表布局系统
    
    使用 gridspec 实现复杂布局:
    """
    
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.fig = plt.figure(figsize=(14, rows * 7))
        self.gs = gridspec.GridSpec(rows, cols, 
                                   wspace=0.4, hspace=0.3)
        self.curr_row = 0
        self.curr_col = 0
    
    def next_row(self):
        """跨整行"""
        subplt = plt.subplot(self.gs[self.curr_row, :])
        self.curr_row += 1
        return subplt
    
    def next_cell(self):
        """单个单元格"""
        subplt = plt.subplot(self.gs[self.curr_row, self.curr_col])
        self.curr_col += 1
        return subplt
```

### 2.3 标准 Tearsheet 结构

```python
def create_full_tear_sheet(factor_data):
    """
    标准 Tearsheet 结构:
    
    ┌────────────────────────────────────┐
    │ 1. 因子统计表                        │
    │    - IC均值/标准差                   │
    │    - 胜率                           │
    │    - 分组收益                        │
    ├────────────────────────────────────┤
    │ 2. IC 分析图                        │
    │    - IC 时序图                       │
    │    - IC 分布图                       │
    │    - IC decay                       │
    ├────────────────────────────────────┤
    │ 3. 分组收益图                        │
    │    - 分组柱状图                       │
    │    - 累计收益曲线                     │
    │    - 分组热力图                       │
    ├────────────────────────────────────┤
    │ 4. 换手率分析                        │
    │    - 分组换手率                       │
    │    - 自相关系数                       │
    └────────────────────────────────────┘
    """
```

---

## 3. QuantStats 简洁 API 设计

### 3.1 Pandas 扩展模式

```python
# QuantStats 通过 extend_pandas() 扩展 pandas

def extend_pandas():
    """
    为 pandas Series 添加便捷方法:
    
    returns.sharpe()      # 夏普比率
    returns.sortino()     # 索提诺比率
    returns.max_drawdown() # 最大回撤
    returns.cagr()        # 年化收益
    """
    
    @pd.api.extensions.register_dataframe_accessor("plot")
    class PlotAccessor:
        def snapshot(self, title, show): ...
        def drawdown(self, show): ...
        ...
    
    @pd.api.extensions.register_series_accessor("stats")
    class StatsAccessor:
        def sharpe(self): ...
        def sortino(self): ...
        def max_drawdown(self): ...
```

### 3.2 便捷函数设计

```python
# QuantStats 简洁 API

import quantstats as qs

# 方法1: 简洁函数
qs.sharpe(returns)
qs.sortino(returns)
qs.max_drawdown(returns)

# 方法2: 完整分析
qs.reports.full(returns, benchmark)

# 方法3: HTML 报告
qs.reports.html(returns, benchmark, output='report.html')
```

### 3.3 Monte Carlo 模拟

```python
class MonteCarlo:
    """
    Monte Carlo 模拟引擎
    """
    
    def __init__(self, returns, sims=1000):
        self.returns = returns
        self.sims = sims
    
    def run(self, seed=42):
        """运行模拟"""
        np.random.seed(seed)
        
        # 生成模拟路径
        self.paths = []
        for _ in range(self.sims):
            path = self.returns.sample(len(self.returns), replace=True)
            self.paths.append((1 + path).cumprod())
        
        return self
    
    def plot(self):
        """绘制模拟结果"""
        ...
```

---

## 4. 核心架构对比

### 4.1 架构复杂度对比

| 特性 | Alphalens | QuantStats | Zipline |
|------|-----------|------------|---------|
| **复杂度** | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ |
| **依赖** | 轻量 | 轻量 | 重量 |
| **实时性** | 离线 | 离线 | 实时 |
| **扩展性** | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ |
| **学习曲线** | 简单 | 最简单 | 陡峭 |

### 4.2 数据流对比

```
Alphalens:
因子 ──▶ 计算 ──▶ 可视化 ──▶ 报告
         │
         ▼
    performance.py
    ├── IC 系列
    ├── 分组收益
    └── 换手率

QuantStats:
收益 ──▶ 统计 ──▶ 可视化 ──▶ 报告
         │
         ▼
    stats.py
    ├── 收益指标
    ├── 风险指标
    └── Monte Carlo

Zipline:
因子 ──▶ Pipeline ──▶ DAG ──▶ 执行
              │
              ▼
         engine.py
         ├── 拓扑排序
         ├── 批量计算
         └── 实时更新
```

---

## 5. 推荐架构设计

### 5.1 混合架构

基于我们的需求，推荐采用**分层架构**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         推荐架构                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │                      API 层 (简洁)                              │     │
│  │                                                                 │     │
│  │   evaluate_factor(name, factor, returns)                       │     │
│  │   create_tearsheet(factor_data)                                │     │
│  │   calculate_risk_metrics(returns)                               │     │
│  │                                                                 │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │                      计算层 (参考 Zipline)                      │     │
│  │                                                                 │     │
│  │   PipelineEngine      ──▶ DAG 执行                              │     │
│  │   Term (记忆化)       ──▶ 因子缓存                              │     │
│  │   WindowedComputer   ──▶ 滚动计算                              │     │
│  │                                                                 │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │                     可视化层 (参考 Alphalens)                   │     │
│  │                                                                 │     │
│  │   GridFigure        ──▶ 网格布局                                │     │
│  │   TearsheetBuilder   ──▶ 报告生成                                │     │
│  │                                                                 │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 核心组件设计

```python
# 1. 因子基类 (参考 Zipline)
class Factor:
    """
    因子基类
    
    特性:
    - 记忆化: 相同参数返回相同实例
    - 窗口支持: 自动处理滚动窗口
    - 组合: 支持因子运算
    """
    
    def __init__(self, name, window_length=None):
        self.name = name
        self.window_length = window_length
        self._cache = {}
    
    def __call__(self, data):
        """计算因子值"""
        if self.name in self._cache:
            return self._cache[self.name]
        return self.compute(data)
    
    def compute(self, data):
        """子类重写"""
        raise NotImplementedError
    
    # 支持运算符重载
    def __add__(self, other):
        return CombinedFactor(self, other, '+')
    
    def __gt__(self, threshold):
        return FactorFilter(self, threshold, '>')


# 2. Pipeline 引擎
class PipelineEngine:
    """
    Pipeline 执行引擎
    
    支持:
    - DAG 执行
    - 增量计算
    - 并行执行
    """
    
    def __init__(self):
        self.graph = DAG()
    
    def add_factor(self, factor, name):
        """添加因子"""
        self.graph.add_node(name, factor)
    
    def run(self, start_date, end_date):
        """执行 Pipeline"""
        # 拓扑排序
        order = self.graph.topological_sort()
        
        # 顺序计算
        results = {}
        for name in order:
            factor = self.graph.nodes[name]['factor']
            results[name] = factor(results)
        
        return results


# 3. Tearsheet 构建器
class TearsheetBuilder:
    """
    Tearsheet 报告生成器
    """
    
    def __init__(self, title="Factor Analysis"):
        self.sections = []
    
    def add_ic_analysis(self, ic_series):
        """添加 IC 分析"""
        self.sections.append({
            'type': 'ic',
            'data': ic_series
        })
    
    def add_returns_analysis(self, returns):
        """添加收益分析"""
        self.sections.append({
            'type': 'returns',
            'data': returns
        })
    
    def render(self):
        """渲染报告"""
        for section in self.sections:
            if section['type'] == 'ic':
                self._plot_ic(section['data'])
            elif section['type'] == 'returns':
                self._plot_returns(section['data'])
    
    def save(self, path):
        """保存为 HTML"""
        ...
```

---

## 6. 实现优先级

### Phase 1: 核心计算层

| 优先级 | 任务 | 来源 |
|--------|------|------|
| P0 | Factor 基类 (记忆化) | Zipline |
| P0 | Pipeline 引擎 (DAG) | Zipline |
| P1 | 因子缓存机制 | Zipline |

### Phase 2: 可视化层

| 优先级 | 任务 | 来源 |
|--------|------|------|
| P0 | GridFigure 布局 | Alphalens |
| P1 | Tearsheet 构建器 | Alphalens |
| P2 | HTML 导出 | Alphalens |

### Phase 3: 便捷 API

| 优先级 | 任务 | 来源 |
|--------|------|------|
| P0 | pandas 扩展方法 | QuantStats |
| P1 | Monte Carlo 模拟 | QuantStats |
| P2 | 一键报告生成 | QuantStats |

---

## 7. 总结

### 7.1 关键洞察

1. **Zipline Pipeline**: 复杂但强大，适合生产环境
2. **Alphalens**: 简洁实用，适合因子分析
3. **QuantStats**: 极简 API，适合快速分析

### 7.2 核心原则

```
1. 记忆化优先
   → 避免重复计算相同因子

2. 惰性计算
   → 按需计算，节省资源

3. 统一接口
   → Factor/Filter/Classifier 一致性

4. 可视化驱动
   → Tearsheet 是标准输出

5. 简洁 API
   → 用户友好，一行代码
```

### 7.3 下一步

1. 实现 Factor 基类 (参考 Zipline)
2. 实现 Pipeline 引擎
3. 实现 Tearsheet 构建器
4. 添加 pandas 扩展方法

---

*报告生成时间: 2026-02-09*
*分析版本: Alphalens (latest), QuantStats (latest), Zipline (1.4.0)*
