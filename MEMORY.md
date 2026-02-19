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

## 工作流程

1. 接收需求 → 创建需求文档
2. 执行任务 → 更新文档
3. commit → 询问push

---

*Last updated: 2026-02-19*
