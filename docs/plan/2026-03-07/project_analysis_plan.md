# 项目全面分析计划

## 📌 目前的状况

本项目 (quant_factor_system) 是一个完整的量化因子研究与交易平台，包含以下核心模块：

- **core/** - 核心配置与基础类
- **data/** - 数据层 (获取、清洗、存储)
- **factors/** - 因子层 (定义、计算、可视化)
- **backtest/** - 回测层 (选股、仓位、止损)
- **dashboard/** - Web 界面 (Streamlit)
- **scripts/** - 运维脚本
- **docs/** - 文档
- **examples/** - 示例代码

## ✅ 需要完成的需求

1. 分析 core/ 文件夹问题与解决方案
2. 分析 data/ 文件夹问题与解决方案
3. 分析 factors/ 文件夹问题与解决方案
4. 分析 backtest/ 文件夹问题与解决方案
5. 分析 dashboard/ 文件夹问题与解决方案
6. 分析 scripts/ 文件夹问题与解决方案
7. 整理根目录文件 (README, requirements.txt 等)
8. 总结整体架构问题与优化方向

## 📋 需求列表及状态

| 需求 | 状态 | 优先级 |
|------|------|--------|
| 分析 core/ 文件夹 | todo | high |
| 分析 data/ 文件夹 | todo | high |
| 分析 factors/ 文件夹 | todo | high |
| 分析 backtest/ 文件夹 | todo | high |
| 分析 dashboard/ 文件夹 | todo | medium |
| 分析 scripts/ 文件夹 | todo | medium |
| 整理根目录文件 | todo | low |
| 总结整体架构 | todo | high |

## 🎯 每个需求的独立任务

### 需求1: 分析 core/ 文件夹

**文件列表:**
- `__init__.py`
- `base.py` - 基础类定义
- `config.py` - 系统配置
- `exceptions.py` - 异常定义
- `logger.py` - 日志工具

**分析维度:**
- [ ] 代码结构与职责划分
- [ ] 配置管理是否合理
- [ ] 是否有代码重复
- [ ] 异常处理是否完善

---

### 需求2: 分析 data/ 文件夹

**文件列表:**
- `__init__.py`
_manager.py` - 数据管理入口- `data
- `loaders.py` - 数据加载器
- `ricequant_source.py` - 米筐数据源
- `storage/` - 存储层
  - `timescale_db.py`
  - `timescale_storage.py`
  - `factor_storage.py`
  - `factor_version.py`
  - `frequency.py`
  - `db_utils.py`
- `utils/` - 工具类
  - `postgres_db.py`
  - `formatter.py`
  - `industry_source.py`
- `clean/` - 数据清洗
  - `validator.py`

**分析维度:**
- [ ] 数据源依赖是否单一
- [ ] 存储层设计是否合理
- [ ] 是否有代码重复
- [ ] 数据验证是否完善

---

### 需求3: 分析 factors/ 文件夹

**文件列表:**
- `__init__.py`
- `core/` - 因子核心
- `processing/` - 因子处理
- `basic/` - 基础因子
- `visualization/` - 可视化
- `report/` - 报告生成

**分析维度:**
- [ ] 因子注册机制是否完善
- [ ] 因子计算性能
- [ ] 可视化模块是否完整

---

### 需求4: 分析 backtest/ 文件夹

**文件列表:**
- `__init__.py`
- `engine.py` - 回测引擎
- `analyzer.py` - 绩效分析
- `selection/` - 选股模块
- `position/` - 仓位管理
- `stoploss/` - 止损策略
- `signal/` - 信号生成

**分析维度:**
- [ ] 回测引擎性能
- [ ] 选股逻辑是否灵活
- [ ] 仓位管理是否完善

---

### 需求5: 分析 dashboard/ 文件夹

**文件列表:**
- `Home.py`
- `components/` - 通用组件
- `pages/` - 页面
- `start_dashboard.sh`

**分析维度:**
- [ ] 页面组织是否合理
- [ ] 组件复用情况

---

### 需求6: 分析 scripts/ 文件夹

**文件列表:**
- `cli.py` - 命令行入口
- `recompute_factors.py` - 因子重算
- `pull_1min_data.py` - 1分钟数据拉取
- `fetch_full_market.py` - 全市场数据
- `stock_list_manager.py` - 股票列表管理
- `update_industry.py` - 行业更新
- `db.sh`, `data.sh` - Shell 脚本

**分析维度:**
- [ ] 脚本职责是否清晰
- [ ] 是否有重复功能
- [ ] 是否可以整合

---

### 需求7: 整理根目录文件

**文件列表:**
- `README.md`
- `requirements.txt`
- `setup.py`
- `__init__.py`
- `MEMORY.md`
- `Dockerfile`
- `.gitignore`

---

### 需求8: 总结整体架构

- [ ] 模块间依赖关系是否清晰
- [ ] 是否有循环依赖
- [ ] 整体优化方向建议
