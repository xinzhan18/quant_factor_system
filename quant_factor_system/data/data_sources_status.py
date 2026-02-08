"""
A股数据获取方案
数据来源说明和故障排除
"""

# ============================================================
# 当前数据源状态
# ============================================================

CURRENT_DATA_SOURCES = """
# A股数据获取状态

## 1. AkShare（主要数据源）✅ 安装完成
   - 状态: API 连接受限（东方财富服务器）
   - 原因: 网络延迟/服务器维护
   - 解决方案: 

## 2. 替代方案
   - baostock（证券宝）
   - tushare（需要 token）
   - akshare-okx（备用源）
"""

# ============================================================
# 故障排除
# ============================================================

TROUBLESHOOTING = """
# A股数据获取故障排除

## 问题：HTTPSConnectionPool 超时

## 解决方案：

### 1. 检查网络
```bash
curl -I https://push2.eastmoney.com
```

### 2. 安装 baostock（备用数据源）
```bash
pip install baostock
```

### 3. 使用 tushare（需要注册）
```bash
pip install tushare
# 注册获取 token: https://tushare.pro
```

### 4. 手动下载数据
   - 东方财富: http://push2.eastmoney.com
   - 同花顺: http://data.10jqka.com.cn
   - 通达信: http://quotes.money.163.com
"""

# ============================================================
# 备用数据源实现
# ============================================================

def get_data_from_baostock():
    """
    从 baostock 获取数据
    
    安装: pip install baostock
    """
    pass


def get_data_from_tushore():
    """
    从 tushare 获取数据
    
    安装: pip install tushare
    注册: https://tushare.pro
    """
    pass


# ============================================================
# 推荐的解决方案
# ============================================================

RECOMMENDED_SOLUTION = """
# 推荐解决方案

## 方案1：等待 API 恢复
AkShare 数据源有时会暂时不可用，可以稍后再试。

## 方案2：使用 baostock
```bash
pip install baostock
```

## 方案3：手动下载数据
从东方财富网站下载CSV数据，然后本地读取。

## 方案4：使用我们的模拟数据
先使用模拟数据测试整个流程，真实数据API恢复后再替换。
"""
