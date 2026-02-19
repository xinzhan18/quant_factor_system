# Quant Factor Trading Platform - Project Memory

## 项目定位

完整的量化因子研究与交易平台，从数据获取到因子分析、回测、实盘交易。

## 架构

```
quant_factor_system/
├── data/              # 数据模块
├── factors/           # 因子模块
├── backtest/          # 回测模块
├── selector/          # 选股模块
├── position/          # 仓位模块
├── stoploss/          # 止损模块
└── dashboard/         # Web界面
```

## 启动方式

```bash
conda activate quantfactor
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
pip install -e .
cd dashboard
streamlit run Home.py
```

---

## 🚀 Git 自动化规则

**自动 commit，push 需确认（重要！）**

- ✅ **自动 commit**: 每次完成需求、阶段性任务、文档更新后，自动执行
- ❌ **禁止自动 push**: 任何情况下都不执行 `git push`
- 📝 **询问 push**: 当用户说"可以push了"或"push吧"时，确认后执行
- 📁 **从项目目录执行**: 所有 git 操作必须在 `quant_factor_system/` 目录下执行

```bash
# 自动执行（每次完成任务后）
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
git add -A && git commit -m "feat: 描述你的更改"

# 手动执行（用户明确要求后）
git push origin main
```

**重要**: 禁止在 workspace 根目录执行 git 操作，所有操作必须在 quant_factor_system 项目内执行！

---

## 👤 称呼规则

- **称呼用户**: "xin"（如：xin，这个需求...）
- **保持友好简洁**: 不要过度使用敬语，直接沟通

---

## 📋 Plan 模式规则

**当用户说"plan模式"或类似表达时，自动执行以下流程：**

1. **识别 plan 意图**: 检测到用户想要制定计划/需求文档
2. **创建计划文档**: 在 `docs/plan/YYYY-MM-DD/xxx_plan.md` 创建需求文档
3. **确认需求**: 询问用户需求细节，补充文档
4. **执行任务**: 根据文档逐步执行
5. **更新文档**: 每完成一步，更新文档状态
6. **自动 commit**: 每次更新后自动 commit

---

*Last updated: 2026-02-19*
