#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
米筐数据加载测试
Test RiceQuant Data Loading

使用:
    python examples/test_ricequant.py
"""

import sys
sys.path.insert(0, '/Users/xinzhan/.openclaw/workspace/quant_factor_system')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 导入模块
from quant_factor_system.data import QuantDataManager


def test_ricequant_connection():
    """测试米筐连接"""
    print("=" * 60)
    print("测试1: 米筐连接")
    print("=" * 60)
    
    try:
        from quant_factor_system.data import RiceQuantSource
        
        source = RiceQuantSource()
        
        # 测试获取交易日历
        dates = source.get_trading_days('2024-01-01', '2024-01-31')
        print(f"✅ 交易日历获取成功: {len(dates)} 个交易日")
        print(f"   示例: {dates[:5]}")
        
        # 测试获取股票列表
        stocks = source.get_all_stocks('2024-01-15')
        print(f"\n✅ 股票列表获取成功: {len(stocks)} 只")
        print(f"   示例: {stocks.head()}")
        
        return True
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_daily_data():
    """测试获取日线数据"""
    print("\n" + "=" * 60)
    print("测试2: 获取日线数据")
    print("=" * 60)
    
    try:
        from quant_factor_system.data import RiceQuantSource
        
        source = RiceQuantSource()
        
        # 获取日线数据
        data = source.get_daily_data(
            symbols=['SH600000', 'SH600001'],
            start_date='20240101',
            end_date='20240131',
            fields=['open', 'high', 'low', 'close', 'volume']
        )
        
        print(f"✅ 日线数据获取成功")
        print(f"   记录数: {len(data)}")
        print(f"   股票数: {data['symbol'].nunique() if 'symbol' in data.columns else 'N/A'}")
        
        if not data.empty:
            print(f"\n   前5条:")
            print(data.head())
        
        return data
        
    except Exception as e:
        print(f"❌ 获取失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_get_minute_data():
    """测试获取分钟数据"""
    print("\n" + "=" * 60)
    print("测试3: 获取分钟数据")
    print("=" * 60)
    
    try:
        from quant_factor_system.data import RiceQuantSource
        
        source = RiceQuantSource()
        
        # 获取分钟数据
        data = source.get_minute_data(
            symbols=['SH600000'],
            start_date='20240102',
            end_date='20240102',
            frequency='1min'
        )
        
        print(f"✅ 分钟数据获取成功")
        print(f"   记录数: {len(data)}")
        
        if not data.empty:
            print(f"\n   前5条:")
            print(data.head())
        
        return data
        
    except Exception as e:
        print(f"❌ 获取失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_save_to_timescaledb():
    """测试保存到 TimescaleDB"""
    print("\n" + "=" * 60)
    print("测试4: 保存到 TimescaleDB")
    print("=" * 60)
    
    try:
        from quant_factor_system.data import RiceQuantSource, QuantDataManager
        
        # 获取数据
        source = RiceQuantSource()
        data = source.get_daily_data(
            symbols=['SH600000', 'SH600001'],
            start_date='20240101',
            end_date='20240131'
        )
        
        if data is None or data.empty:
            print("❌ 无数据可保存")
            return
        
        # 保存到数据库
        manager = QuantDataManager()
        count = manager.db.insert_price(data, table='price_daily')
        
        print(f"✅ 数据保存成功: {count} 条")
        
        # 查询验证
        df = manager.get_price(
            symbols=['SH600000', 'SH600001'],
            start_date='2024-01-01',
            end_date='2024-01-31',
            frequency='daily'
        )
        
        print(f"✅ 查询验证: {len(df)} 条")
        
        return df
        
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_calculate_factor():
    """测试计算因子"""
    print("\n" + "=" * 60)
    print("测试5: 计算因子 (ret20)")
    print("=" * 60)
    
    try:
        from quant_factor_system.data import QuantDataManager
        
        manager = QuantDataManager()
        
        # 获取价格数据
        df = manager.get_price(
            symbols=['SH600000'],
            start_date='2024-01-01',
            end_date='2024-01-31',
            frequency='daily'
        )
        
        if df is None or df.empty:
            print("❌ 无数据")
            return
        
        # 计算 ret20 (20日收益率)
        if isinstance(df.index, pd.MultiIndex):
            df = df.reset_index()
        
        stock_data = df.set_index('symbol').loc['SH600000']
        stock_data = stock_data.sort_index()
        
        lookback = min(20, len(stock_data))
        
        factors = []
        for i in range(lookback - 1, len(stock_data)):
            current_close = stock_data['close'].iloc[i]
            past_close = stock_data['close'].iloc[i - lookback + 1]
            ret = (current_close - past_close) / past_close
            
            date = stock_data.index[i]
            factors.append({
                'symbol': 'SH600000',
                'time': date,
                'factor_name': 'ret20',
                'value': ret
            })
        
        factor_df = pd.DataFrame(factors)
        
        print(f"✅ 因子计算成功: {len(factor_df)} 条")
        print(f"\n   最新因子值:")
        print(factor_df.tail())
        
        # 保存到数据库
        manager.db.create_factor_table('ret20')
        manager.db.insert_factor(factor_df, 'ret20', value_col='value')
        print(f"\n✅ 因子已保存到数据库")
        
        return factor_df
        
    except Exception as e:
        print(f"❌ 计算失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """
    主测试函数
    """
    print("\n" + "🚀" * 20)
    print("米筐数据加载测试")
    print("🚀" * 20 + "\n")
    
    # 测试1: 连接
    if not test_ricequant_connection():
        print("\n❌ 米筐连接失败，请检查账号配置")
        return
    
    # 测试2: 日线数据
    daily_data = test_get_daily_data()
    
    # 测试3: 分钟数据
    minute_data = test_get_minute_data()
    
    # 测试4: 保存到数据库
    saved_data = test_save_to_timescaledb()
    
    # 测试5: 计算因子
    factor_data = test_calculate_factor()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"日线数据: {'✅' if daily_data is not None else '❌'}")
    print(f"分钟数据: {'✅' if minute_data is not None else '❌'}")
    print(f"数据库保存: {'✅' if saved_data is not None else '❌'}")
    print(f"因子计算: {'✅' if factor_data is not None else '❌'}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
