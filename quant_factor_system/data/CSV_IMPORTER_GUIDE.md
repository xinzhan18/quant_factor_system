# 本地 CSV 导入指南

## 使用方法

### 1. 初始化数据库

```bash
python quant_factor_system/data/csv_importer.py --init
```

### 2. 导入日线数据

```bash
# 方式一: 直接指定文件
python csv_importer.py --daily your_daily.csv

# 方式二: 指定数据库路径
python csv_importer.py --daily daily.csv --db storage/database/market_data.db
```

**日线 CSV 格式要求:**
```csv
code,date,open,high,low,close,volume
000001.XSHE,2024-01-02,10.50,10.80,10.30,10.60,5000000
000001.XSHE,2024-01-03,10.60,10.90,10.40,10.80,6000000
600519.SH,2024-01-02,1700,1750,1690,1720,800000
```

### 3. 导入股票列表

```bash
python csv_importer.py --stocks stocks.csv
```

**股票列表 CSV 格式:**
```csv
code,name,exchange,list_date,status
000001.XSHE,平安银行,SZSE,1991-04-03,Listed
600519.SH,贵州茅台,SSE,2001-08-27,Listed
```

### 4. 导入因子数据

```bash
# 宽格式 (每个因子一列)
python csv_importer.py --factors factors.csv

# 长格式 (factor_name, value 列)
python csv_importer.py --factors factors_long.csv
```

**因子 CSV 格式 (宽格式):**
```csv
code,date,momentum_20d,momentum_60d,pe,roe
000001.XSHE,2024-01-02,0.05,0.08,8.5,0.15
000001.XSHE,2024-01-03,0.06,0.09,8.6,0.16
```

**因子 CSV 格式 (长格式):**
```csv
code,date,factor_name,value
000001.XSHE,2024-01-02,momentum_20d,0.05
000001.XSHE,2024-01-02,pe,8.5
000001.XSHE,2024-01-02,roe,0.15
```

### 5. 查看统计

```bash
python csv_importer.py --stats
```

输出:
```
📊 数据库统计: storage/database/market_data.db
   股票数量: 5000
   日线记录: 12,500,000
   因子记录: 25,000,000
   日期范围: 2010-01-04 ~ 2024-02-08
```

### 6. 查询样本数据

```bash
# 查询日线样本
python csv_importer.py --query --table daily_data

# 查询股票样本
python csv_importer.py --query --table stocks
```

## 字段映射

如果你的 CSV 列名不同，脚本会自动映射：

| 原始列名 | 映射为 |
|---------|--------|
| symbol, ticker | code |
| market | exchange |
| listed_date, list_date | list_date |
| turnover | turn |
| pct_change, pct_chg | pct_chg |

## 示例流程

```bash
# 1. 初始化
python csv_importer.py --init

# 2. 导入股票列表
python csv_importer.py --stocks stocks.csv

# 3. 导入日线数据
python csv_importer.py --daily daily_data.csv

# 4. 导入因子数据
python csv_importer.py --factors momentum.csv

# 5. 查看统计
python csv_importer.py --stats
```

## 数据库结构

```
market_data.db
├── stocks          # 股票列表
│   ├── code (PK)
│   ├── name
│   ├── exchange
│   └── list_date
│
├── daily_data     # 日线数据
│   ├── code
│   ├── date
│   ├── open, high, low, close
│   ├── volume, amount
│   └── turn, pct_chg
│
└── factor_data   # 因子数据
    ├── code
    ├── date
    ├── factor_name
    └── value
```

---

*最后更新: 2026-02-09*
