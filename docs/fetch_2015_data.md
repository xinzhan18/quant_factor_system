# 拉取 2015 年历史数据

## 环境准备

### 1. 安装依赖

```bash
# 进入项目目录
cd /Users/xinzhan/.openclaw/workspace

# 创建 conda 环境（推荐）
conda create -n quant python=3.9
conda activate quant

# 安装依赖
pip install -r requirements.txt

# 安装米筐
pip install rqdatac

# 安装数据库驱动
pip install psycopg2-binary
```

### 2. 配置米筐

```bash
# 创建配置文件
cat > ~/.rqdatac << EOF
[User]
username = 你的米筐账号
password = 你的米筐密码
EOF

# 设置权限
chmod 600 ~/.rqdatac
```

### 3. 启动数据库

```bash
# 检查 Docker
docker ps | grep timescaledb

# 如果没有运行，启动
docker run -d --name timescaledb \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=quant123 \
  timescale/timescaledb:latest-pg14
```

## 拉取数据

### 步骤 1: 获取 2015 年股票列表

```bash
conda activate quant
cd /Users/xinzhan/.openclaw/workspace

python -m quant_factor_system.scripts.stock_list_manager --year 2015 --count
```

### 步骤 2: 拉取 2015 年日线数据

```bash
# 仅拉取 2015 年
python -m quant_factor_system.scripts.fetch_full_market --year 2015

# 或者强制重新拉取
python -m quant_factor_system.scripts.fetch_full_market --year 2015 --force
```

### 步骤 3: 验证数据

```bash
# 查看数据库中的数据量
psql -h localhost -U postgres -d quant_data -c "SELECT COUNT(*) FROM price_daily WHERE time >= '2015-01-01' AND time < '2016-01-01';"
```

## 预期结果

| 指标 | 值 |
|-----|-----|
| 股票数量 | ~2800 只 |
| 交易日 | 244 天 |
| 总数据量 | ~680,000 条 |

## 查看拉取进度

```bash
# 查看状态
python -m quant_factor_system.scripts.fetch_full_market --status
```

## 常见问题

### Q: 报错 "rqdatac not found"
```bash
# 检查是否安装
pip list | grep rqdatac

# 重新安装
pip install rqdatac
```

### Q: 报错 "connection refused"
```bash
# 检查数据库
docker ps | grep timescaledb

# 重启数据库
docker restart timescaledb
```

### Q: 拉取很慢
- 这是正常的，米筐API有速率限制
- 建议设置 `--batch-size` 减小批次
- 或者在晚间运行
