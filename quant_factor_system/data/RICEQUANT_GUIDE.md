# 米筐数据获取指南

## 1. 注册米筐账号

1. 访问 [米筐官网](https://www.ricequant.com)
2. 注册账号（推荐使用企业邮箱）
3. 获取 API Token

## 2. 安装依赖

```bash
pip install ricequant pandas numpy
```

## 3. 获取全市场数据

### 方式一：命令行

```bash
# 设置 token（替换 YOUR_TOKEN）
export RQ_TOKEN=your_token_here

# 测试连接
python quant_factor_system/data/ricequant_downloader.py --token YOUR_TOKEN --test

# 下载所有日线数据（2010年至今，前复权）
python quant_factor_system/data/ricequant_downloader.py --token YOUR_TOKEN

# 指定日期范围
python quant_factor_system/data/ricequant_downloader.py \
    --token YOUR_TOKEN \
    --start 2023-01-01 \
    --end 2024-01-01

# 全量下载（不增量）
python quant_factor_system/data/ricequant_downloader.py \
    --token YOUR_TOKEN \
    --full
```

### 方式二：Python 脚本

```python
from quant_factor_system.data.ricequant_downloader import RiceQuantDownloader

# 初始化
downloader = RiceQuantDownloader(
    token='YOUR_TOKEN',
    db_path='storage/database/market_data.db'
)

# 测试连接
if downloader.test_connection():
    print("✅ 连接成功")
else:
    print("❌ 连接失败")

# 下载全市场数据
downloader.download_all(
    start_date='2010-01-01',
    end_date='2024-02-09',
    adjust_type='pre'  # 前复权
)
```

## 4. 数据查询

```python
from quant_factor_system.data.ricequant_downloader import DataQuerier

# 初始化查询器
querier = DataQuerier('storage/database/market_data.db')

# 查看统计
stats = querier.get_data_stats()
print(f"股票数量: {stats['stocks']}")
print(f"日线记录: {stats['daily_records']}")
print(f"日期范围: {stats['start_date']} ~ {stats['end_date']}")

# 查询股票列表
stocks = querier.query_stocks(exchange='SSE')
print(stocks.head())

# 查询日线数据
daily = querier.query_daily(
    code='000001.XSHE',
    start_date='2024-01-01',
    end_date='2024-02-01'
)
print(daily.head())
```

## 5. 数据格式

### 股票列表 (stocks 表)

| 字段 | 类型 | 说明 |
|------|------|------|
| code | TEXT | 股票代码 (000001.XSHE) |
| name | TEXT | 股票名称 |
| exchange | TEXT | 交易所 (SSE, SZSE) |
| list_date | TEXT | 上市日期 |
| delist_date | TEXT | 退市日期 |
| status | TEXT | 状态 |

### 日线数据 (daily_data 表)

| 字段 | 类型 | 说明 |
|------|------|------|
| code | TEXT | 股票代码 |
| date | TEXT | 交易日期 |
| open | REAL | 开盘价 |
| high | REAL | 最高价 |
| low | REAL | 最低价 |
| close | REAL | 收盘价 |
| volume | REAL | 成交量 |
| amount | REAL | 成交额 |
| turn | REAL | 换手率 |
| pct_chg | REAL | 涨跌幅 |
| pre_close | REAL | 昨收价 |

## 6. 使用现有数据

如果你已经有米筐导出的 CSV 文件：

```python
from quant_factor_system.data.formatter import QuantDataFormatter

# 读取 CSV
df = pd.read_csv('your_data.csv')

# 格式化
formatter = QuantDataFormatter('ricequant')
formatted = formatter.format_daily_data(df, 
                                     symbol_col='code',
                                     date_col='date')

print(formatted.head())
```

## 7. 注意事项

1. **API 限制**: 免费账户有每日请求次数限制
2. **数据范围**: 建议先获取完整历史，再增量更新
3. **复权选择**: 
   - `pre`: 前复权（推荐）
   - `none`: 不复权
   - `post`: 后复权
4. **增量更新**: 默认只下载新数据

## 8. 故障排除

### 连接失败
```bash
# 检查 token
python ricequant_downloader.py --token YOUR_TOKEN --test
```

### 数据缺失
```bash
# 查看已下载的股票
python ricequant_downloader.py --query stocks

# 查看数据统计
python ricequant_downloader.py --query stats

# 全量重新下载
python ricequant_downloader.py --token YOUR_TOKEN --full
```

## 9. 费用说明

- **免费账户**: 有请求限制，适合个人研究
- **付费账户**: 无限制，可用于生产环境

如需商业使用，建议购买付费套餐。

---

*最后更新: 2026-02-09*
