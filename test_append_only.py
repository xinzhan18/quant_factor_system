#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试factor_storage.py的APPEND ONLY修改
"""

import sys
import os
import importlib.util

# 直接从工作目录加载模块
module_path = '/Users/xinzhan/.openclaw/workspace/quant_factor_system/data/factor_storage.py'
spec = importlib.util.spec_from_file_location('factor_storage', module_path)
factor_storage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factor_storage)

FactorStorage = factor_storage.FactorStorage
DailyFactorWide = factor_storage.DailyFactorWide
import pandas as pd
from datetime import date, datetime
import hashlib


def test_append_only():
    """测试APPEND ONLY模式"""
    
    print("=" * 60)
    print("测试 FactorStorage APPEND ONLY 修改")
    print("=" * 60)
    
    # 1. 检查方法是否存在
    print("\n1. 检查FactorStorage方法")
    
    import inspect
    from quant_factor_system.data.factor_storage import FactorStorage
    
    # 检查save_daily_factor方法签名
    sig = inspect.signature(FactorStorage.save_daily_factor)
    params = list(sig.parameters.keys())
    
    print(f"   save_daily_factor参数: {params}")
    
    if 'append_only' in params:
        print("   ✅ 包含append_only参数")
    else:
        print("   ❌ 缺少append_only参数")
        return False
    
    # 检查_exists_daily_factor方法
    if hasattr(FactorStorage, '_exists_daily_factor'):
        print("   ✅ 包含_exists_daily_factor方法")
    else:
        print("   ❌ 缺少_exists_daily_factor方法")
        return False
    
    # 检查_upsert_daily_row方法
    if hasattr(FactorStorage, '_upsert_daily_row'):
        print("   ✅ 包含_upsert_daily_row方法")
    else:
        print("   ❌ 缺少_upsert_daily_row方法")
        return False
    
    print("\n2. 检查_init方法中的unique constraint")
    init_sig = inspect.signature(FactorStorage.init)
    init_code = inspect.getsource(FactorStorage.init)
    
    if '_create_unique_constraints' in init_code:
        print("   ✅ 包含_create_unique_constraints调用")
    else:
        print("   ❌ 缺少_create_unique_constraints调用")
        return False
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过!")
    print("=" * 60)
    
    return True


def test_model_structure():
    """测试数据模型结构"""
    
    print("\n" + "=" * 60)
    print("测试 DailyFactorWide 模型结构")
    print("=" * 60)
    
    # 检查列定义
    columns = DailyFactorWide.__table__.columns
    
    print("\n表结构:")
    for col in columns:
        print(f"  - {col.name}: {col.type}")
    
    # 检查主键
    pk = DailyFactorWide.__table__.primary_key
    print(f"\n主键: {[c.name for c in pk.columns]}")
    
    # 检查是否包含我们需要的列
    required_cols = ['symbol', 'date', 'momentum_5d', 'return_1d', 'rsi_14']
    for col in required_cols:
        if col in columns:
            print(f"   ✅ {col}")
        else:
            print(f"   ⚠️ {col} (未找到)")
    
    print("\n" + "=" * 60)


def show_usage_example():
    """显示使用示例"""
    
    print("\n" + "=" * 60)
    print("使用示例")
    print("=" * 60)
    
    print("""
# 1. 初始化存储
from quant_factor_system.data import FactorStorage

storage = FactorStorage()
storage.init()

# 2. 保存因子 (APPEND ONLY - 默认)
df = pd.DataFrame({
    'symbol': ['SH600000', 'SH600001'],
    'date': [date(2024, 1, 2), date(2024, 1, 2)],
    'momentum_5d': [0.05, 0.03],
    'return_1d': [0.01, -0.02]
})

# 默认append_only=True，会报错如果数据已存在
storage.save_daily_factor(df, factor_columns=['momentum_5d', 'return_1d'])

# 3. 如果想强制更新 (不推荐)
storage.save_daily_factor(df, factor_columns=['momentum_5d', 'return_1d'], append_only=False)

# 4. 查询因子
result = storage.query_daily_factor(
    symbols=['SH600000'],
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 31)
)
print(result)
""")


if __name__ == '__main__':
    print("开始测试...")
    print()
    
    # 运行测试
    success = test_append_only()
    
    if success:
        test_model_structure()
        show_usage_example()
        
        print("\n🎉 所有测试完成!")
        sys.exit(0)
    else:
        print("\n💥 测试失败!")
        sys.exit(1)
