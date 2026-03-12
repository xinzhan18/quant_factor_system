# Quant Factor Trading Platform - 项目概览

## 📦 项目简介

完整的量化因子研究与交易平台，从数据获取到因子分析，回测、实盘交易。

## 🏗️ 架构

```
┌────────────────────────────────────────────────────────┐
│              Dashboard (Streamlit)                 │
└────────────────────────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│                  Backtest Engine                    │
└────────────────────────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│                    Factor Module                    │
└────────────────────────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│                     Data Module                     │
└────────────────────────────────────────────────────────┘
```

## 📁 目录结构

```
quant_factor_system/
├── data/              # 数据模块
├── factors/           # 因子模块
├── backtest/         # 回测模块
├── selector/          # 选股模块
├── position/         # 仓位模块
├── stoploss/         # 止损模块
├── dashboard/        # Web界面
└── docs/            # 文档
```

## 🚀 启动方式

```bash
conda activate quantfactor
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
pip install -e .
cd dashboard
streamlit run Home.py
```

## ⚙️ 环境配置

### 配置文件位置

项目使用 `.env` 文件存储敏感配置（数据库密码、API Key等），不提交到 Git。

```
quant_factor_system/
├── .env                    # 实际配置（不提交Git）
├── .env.example           # 配置模板（提交Git）
```

### 配置内容

```bash
# TimescaleDB 数据库
TIMESCALE_HOST=localhost
TIMESCALE_PORT=5432
TIMESCALE_DB=quant_data
TIMESCALE_USER=postgres
TIMESCALE_PASSWORD=postgres

# 米筐数据源 (从 ~/.zshenv 获取)
RQDATAC_CONF="tcp://license:xxx@rqdatad-pro.ricequant.com:16011"
```

### 获取米筐 License

1. 登录米筐官网 https://ricequant.com
2. 获取 License Key
3. 复制到 `.env` 文件

### 确保服务运行

**1. TimescaleDB (Docker)**
```bash
# 检查状态
docker ps | grep timescale

# 启动（如未运行）
docker run -d --name timescaledb \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=postgres \
  timescale/timescaledb:latest-pg14
```

**2. 运行脚本前加载环境变量**
```bash
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
export $(cat .env | grep -v "^#" | xargs)

# 然后运行脚本
python scripts/pull_1min_data.py
```

**3. Cron 任务已配置自动加载环境变量**

### 依赖安装

```bash
pip install python-dotenv  # 已添加到 requirements.txt
```

## 📞 支持

- 文档: `docs/`
- 任务: `docs/plan/OVERVIEW.md`

---

*最后更新: 2026-02-19*
