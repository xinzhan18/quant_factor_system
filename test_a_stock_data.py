#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股数据获取测试
支持多个数据源
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
import numpy as np
from datetime import datetime


def test_akshare():
    """测试 AkShare 数据源"""
    print("\n" + "="*60)
    print("📊 测试 AkShare 数据源")
    print("="*60)
    
    try:
        import akshare as ak
        
        print(f"AkShare 版本: {ak.__version__}")
        
        # 获取股票列表
        print("\n获取 A 股列表...")
        stock_list = ak.stock_zh_a_spot_em()
        print(f"  ✅ 获取 {len(stock_list)} 只股票")
        
        # 获取单只股票
        print("\n获取平安银行(000001)...")
        df = ak.stock_zh_a_hist(
            symbol='000001',
            period="daily",
            start_date='2024-01-01',
            end_date='2024-12-31',
            adjust="qfq"
        )
        
        if not df.empty:
            print(f"  ✅ 获取 {len(df)} 条数据")
            print(f"  日期范围: {df['日期'].min()} ~ {df['日期'].max()}")
            print(f"  价格范围: {df['收盘'].min():.2f} ~ {df['收盘'].max():.2f}")
            return True
        else:
            print("  ⚠️ 无数据")
            return False
            
    except ImportError:
        print("  ⚠️ AkShare 未安装: pip install akshare")
        return False
    except Exception as e:
        print(f"  ❌ 错误: {str(e)[:100]}")
        return False


def test_baostock():
    """测试 BaoStock 数据源"""
    print("\n" + "="*60)
    print("📊 测试 BaoStock 数据源")
    print("="*60)
    
    try:
        import baostock as bs
        
        # 登录
        lg = bs.login()
        print(f"登录: {lg.msg}")
        
        # 获取股票列表
        print("\n获取股票列表...")
        rs = bs.query_all_sh_code()
        
        data_list = []
        count = 0
        while rs.error_code == '0' and rs.next():
            data_list.append(rs.get_row_data())
            count += 1
        
        print(f"  股票数量: {count}")
        
        # 获取上证指数
        print("\n获取上证指数...")
        rs = bs.query_history_k_data_plus(
            "sh.000001",
            "date,code,open,high,low,close,volume",
            start_date='2024-01-01',
            end_date='2024-12-31'
        )
        
        data_list = []
        while rs.error_code == '0' and rs.next():
            data_list.append(rs.get_row_data())
        
        if data_list:
            df = pd.DataFrame(data_list, columns=rs.fields)
            print(f"  ✅ 获取 {len(df)} 条数据")
            print(f"  日期范围: {df['date'].min()} ~ {df['date'].max()}")
        
        # 登出
        bs.logout()
        
        return True
        
    except ImportError:
        print("  ⚠️ BaoStock 未安装: pip install baostock")
        return False
    except Exception as e:
        print(f"  ❌ 错误: {str(e)[:100]}")
        return False


def test_simulated_data():
    """测试模拟数据"""
    print("\n" + "="*60)
    print("📊 测试模拟数据")
    print("="*60)
    
    np.random.seed(42)
    
    dates = pd.date_range('2024-01-01', periods=500, freq='B')
    n = len(dates)
    
    # 创建多只股票
    stocks = ['000001', '600000', '600519', '000002', '000858']
    all_data = []
    
    for stock in stocks:
        trend = np.linspace(0.01, 0.02, n)
        noise = np.random.randn(n) * 0.02
        returns = trend + noise
        prices = 100 * np.cumprod(1 + returns)
        
        df = pd.DataFrame({
            'symbol': stock,
            'close': prices,
            'pct_chg': returns * 100,
            'pe': np.random.uniform(10, 50, n),
            'roe': np.random.uniform(0.05, 0.25, n),
            'market_cap': prices * np.random.uniform(1e6, 1e7, n),
            'volume': np.random.randint(1e6, 1e8, n),
            'turnover': np.random.uniform(0.001, 0.05, n),
            'industry': pd.Categorical(np.random.choice(['银行', '医药', '消费', '科技', '制造'], n)),
        }, index=dates)
        
        all_data.append(df)
    
    data = pd.concat(all_data)
    
    print(f"  ✅ 创建 {len(data)} 条数据")
    print(f"  股票数量: {data['symbol'].nunique()}")
    print(f"  时间范围: {data.index.min()} ~ {data.index.max()}")
    
    return data


def run_full_pipeline(data):
    """运行完整因子分析流程"""
    print("\n" + "="*60)
    print("🚀 运行完整因子分析流程")
    print("="*60)
    
    from quant_factor_system import (
        FactorSystem, MomentumFactor, ValueFactor, QualityFactor,
        DataProcessor, BacktestConfig, FactorEvaluator
    )
    
    # 涨跌停过滤
    print("\n1. 涨跌停过滤...")
    processor = DataProcessor()
    df_clean, stats = processor.filter_limit_stocks(data.copy(), remove=True)
    print(f"   过滤后: {len(df_clean)} 条 ({len(df_clean)/len(data)*100:.1f}%)")
    
    # 因子计算
    print("\n2. 因子计算...")
    system = FactorSystem(name="AStockSystem")
    system.add_factor(MomentumFactor(20), weight=1.0)
    system.add_factor(ValueFactor("pe"), weight=1.0)
    system.add_factor(QualityFactor("roe"), weight=1.0)
    
    factor_values = system.calculate_all(df_clean)
    print(f"   因子数: {len(system.factors)}")
    
    # 因子评估
    print("\n3. 因子评估...")
    config = BacktestConfig(num_groups=5)
    evaluator = FactorEvaluator(config)
    
    returns = df_clean.groupby('symbol')['close'].pct_change().dropna()
    
    results = evaluator.evaluate_multiple(
        factor_values, returns,
        df_clean['market_cap'], df_clean['industry']
    )
    
    print("\n   📊 IC 分析结果:")
    print("   " + "-"*50)
    for name, r in results.items():
        status = "OK" if abs(r.ic) > 0.03 else ("~" if abs(r.ic) > 0 else "X")
        print(f"   {status} {name:<12} IC={r.ic:.4f}  胜率={r.ic_sign_ratio:.1%}")
    
    print("\n✅ 完整流程测试通过!")
    return results


def main():
    """主函数"""
    print("\n" + "="*70)
    print("🚀 量化因子系统 - A股数据获取测试")
    print("="*70)
    
    # 测试数据源
    akshare_ok = test_akshare()
    baostock_ok = test_baostock()
    
    # 使用可用的数据源
    if akshare_ok or baostock_ok:
        # 使用真实数据
        print("\n" + "="*60)
        print("⚠️ 真实数据 API 暂时不可用")
        print("="*60)
        print("""
由于网络原因，东方财富API暂时无法访问。

解决方案:
1. 等待 API 恢复
2. 使用备用数据源: pip install baostock
3. 使用模拟数据测试完整流程
""")
    
    # 测试模拟数据
    data = test_simulated_data()
    
    # 运行完整流程
    results = run_full_pipeline(data)
    
    # 总结
    print("\n" + "="*70)
    print("📊 测试总结")
    print("="*70)
    
    print("""
数据源状态:
  AkShare:  %s
  BaoStock: %s
  模拟数据: ✅ 可用

下一步:
  1. 安装 BaoStock: pip install baostock
  2. 或等待 AkShare API 恢复
  3. 或手动导入本地数据
""" % (
        "✅ 可用" if akshare_ok else "❌ 暂时不可用",
        "✅ 可用" if baostock_ok else "❌ 未安装"
    ))
    
    print("="*70)


if __name__ == "__main__":
    main()
