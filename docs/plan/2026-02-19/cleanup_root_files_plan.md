# 根目录文件整理计划

## 📌 目前的状况

当前根目录有很多散落的文件：

```
quant_factor_system/
├── core/                    # 核心基类
├── data/                   # 数据层
├── factors/                # 因子层
├── backtest/              # 回测层
├── dashboard/             # Dashboard
│
├── scripts/               # ⭐ 脚本目录
├── examples/              # ⭐ 示例目录
│
├── cli.py                 # ⚠️ 在根目录
├── config.py              # ⚠️ 在根目录
├── exceptions.py          # ⚠️ 在根目录
├── logger.py              # ⚠️ 在根目录
├── deps.py                # ⚠️ 在根目录
├── run.sh                 # ⚠️ 在根目录
└── requirements.txt       # ✅ 在根目录（合理）
```

## 🔍 问题分析

| 文件 | 当前目录 | 建议目录 | 问题 |
|------|---------|---------|------|
| `cli.py` | 根目录 | `scripts/` | 命令行工具 |
| `config.py` | 根目录 | `core/` | 配置相关 |
| `exceptions.py` | 根目录 | `core/` | 异常定义 |
| `logger.py` | 根目录 | `core/` | 日志相关 |
| `deps.py` | 根目录 | `scripts/` | 依赖检查脚本 |
| `run.sh` | 根目录 | `scripts/` | 启动脚本 |

## ✅ 重构方案

```
scripts/
├── cli.py              # 命令行工具
├── deps.py             # 依赖检查
├── run.sh              # 启动脚本
└── __init__.py

core/
├── base.py             # 因子基类（已有）
├── config.py           # 配置（从根目录移入）
├── exceptions.py       # 异常（从根目录移入）
├── logger.py           # 日志（从根目录移入）
└── __init__.py
```

## 📋 需求列表及状态

| 需求 | 状态 | 优先级 |
|------|------|--------|
| 复制 cli.py → scripts/ | done | medium |
| 复制 config.py → core/ | done | medium |
| 复制 exceptions.py → core/ | done | medium |
| 复制 logger.py → core/ | done | medium |
| 复制 deps.py → scripts/ | done | medium |
| 删除原始根目录文件 | done | medium |
| 创建 __init__.py 文件 | done | low |
| 测试验证 | done | low |

## 🎯 执行步骤

### Step 1: 复制文件

- [x] 复制 `cli.py` → `scripts/`
- [x] 复制 `config.py` → `core/`
- [x] 复制 `exceptions.py` → `core/`
- [x] 复制 `logger.py` → `core/`
- [x] 复制 `deps.py` → `scripts/`

### Step 2: 创建 __init__.py

- [x] 创建 `scripts/__init__.py`
- [x] 创建 `core/__init__.py`

### Step 3: 删除原始文件

- [x] 删除根目录 `cli.py`
- [x] 删除根目录 `config.py`
- [x] 删除根目录 `exceptions.py`
- [x] 删除根目录 `logger.py`
- [x] 删除根目录 `deps.py`

### Step 4: 测试验证

- [x] 测试核心模块导入
- [x] 测试 Dashboard 页面导入
- [x] 测试 factors 导入
- [x] 测试 backtest 导入

## 📁 新结构

```
quant_factor_system/
├── core/                  # 核心工具
│   ├── base.py          # 因子基类
│   ├── config.py        # 配置
│   ├── exceptions.py    # 异常
│   ├── logger.py        # 日志
│   └── __init__.py
│
├── scripts/            # 脚本
│   ├── cli.py          # 命令行工具
│   ├── deps.py         # 依赖检查
│   └── __init__.py
│
├── data/               # 数据层
├── factors/            # 因子层
├── backtest/          # 回测层
└── dashboard/         # Dashboard
```

---

*创建时间: 2026-02-19*
*更新时间: 2026-02-19*
