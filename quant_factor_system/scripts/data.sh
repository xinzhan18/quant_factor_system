#!/bin/bash
# ============================================================
# QuantFactorSystem - 数据管理脚本
# ============================================================

PROJECT_DIR="/Users/xinzhan/.openclaw/workspace/quant_factor_system"
DATA_DIR="$PROJECT_DIR/data"

echo "============================================================"
echo "💾 数据管理"
echo "============================================================"
echo ""

# Conda环境
CONDA_BASE="/Users/xinzhan/miniconda3"
CONDA_ENV="quantfactor"

# 设置Python路径
export PYTHONPATH="/Users/xinzhan/.openclaw/workspace:$PYTHONPATH"

# 使用conda环境中的Python
PYTHON="$CONDA_BASE/envs/$CONDA_ENV/bin/python"

# 检查环境
if [ ! -d "$CONDA_BASE/envs/$CONDA_ENV" ]; then
    echo "❌ Conda环境 '$CONDA_ENV' 不存在"
    exit 1
fi

# 确保数据目录存在
mkdir -p "$DATA_DIR"

case "${1:-help}" in
    import)
        if [ -z "$2" ]; then
            echo "用法: $0 import <csv文件>"
            echo ""
            echo "示例:"
            echo "  $0 import ./data/price.csv"
            exit 1
        fi
        
        if [ ! -f "$2" ]; then
            echo "❌ 文件不存在: $2"
            exit 1
        fi
        
        echo "📥 导入数据: $2"
        echo ""
        cd $PROJECT_DIR
        $PYTHON -c "
from quant_factor_system.data import DataManager
dm = DataManager()
dm.import_csv('$2', symbol_col='symbol', date_col='date', price_col='close')
print('✅ 导入完成')
"
        ;;
    
    export)
        echo "📤 导出数据..."
        echo "TODO: 实现导出功能"
        ;;
    
    list)
        echo "📋 数据列表..."
        echo ""
        
        if [ -d "$DATA_DIR" ]; then
            echo "本地数据目录: $DATA_DIR"
            ls -la "$DATA_DIR" 2>/dev/null || echo "  空目录"
        else
            echo "  数据目录不存在"
        fi
        ;;
    
    sample)
        echo "📊 生成示例数据..."
        echo ""
        cd $PROJECT_DIR
        $PYTHON -c "
import pandas as pd
import numpy as np
from datetime import datetime

# 生成示例价格数据
symbols = ['SH600000', 'SH600001', 'SH600002', 'SH600003', 'SH600004']
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 12, 31)
dates = pd.date_range(start_date, end_date, freq='B')

data = []
for symbol in symbols:
    price = 10 + np.random.randn() * 2
    for date in dates:
        price = price * (1 + np.random.randn() * 0.02)
        data.append({
            'symbol': symbol,
            'date': date.strftime('%Y-%m-%d'),
            'close': round(price, 2),
            'volume': np.random.randint(100000, 10000000)
        })

df = pd.DataFrame(data)
df.to_csv('$DATA_DIR/sample_price.csv', index=False)
print(f'✅ 生成了 {len(df)} 条数据')
print(f'📁 保存到: $DATA_DIR/sample_price.csv')
print(f'📊 股票数: {df[\"symbol\"].nunique()}')
print(f'📅 日期范围: {df[\"date\"].min()} ~ {df[\"date\"].max()}')
"
        ;;
    
    help|*)
        echo "用法: $0 {import|export|list|sample}"
        echo ""
        echo "命令:"
        echo "  import <file>  - 导入CSV数据"
        echo "  export         - 导出数据"
        echo "  list           - 查看数据列表"
        echo "  sample         - 生成示例数据"
        echo ""
        echo "示例:"
        echo "  $0 sample              # 生成示例数据"
        echo "  $0 import ./data.csv   # 导入CSV"
        echo "  $0 list                # 查看数据"
        exit 0
        ;;
esac
