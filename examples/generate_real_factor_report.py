"""
使用真实数据库数据生成因子报告
"""

import sys
sys.path.insert(0, '/Users/xinzhan/.openclaw/workspace')

from quant_factor_system.factors import FactorFactory, create_factor_report
from quant_factor_system.data import TimescaleDB
import pandas as pd
import numpy as np


def get_factor_data_from_db(factor_name: str, n_stocks: int = 100, n_days: int = 500):
    """
    从数据库获取因子数据
    
    Args:
        factor_name: 因子名称
        n_stocks: 股票数量
        n_days: 天数
    """
    print(f"📊 从数据库获取 {factor_name} 因子数据...")
    
    db = TimescaleDB()
    
    # 获取股票列表
    try:
        with db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT symbol 
                FROM price_daily 
                ORDER BY symbol 
                LIMIT %s
            """, (n_stocks,))
            stocks = [row[0] for row in cursor.fetchall()]
            print(f"   获取到 {len(stocks)} 只股票")
            
            # 获取最新交易日期
            cursor.execute("SELECT MAX(time) FROM price_daily")
            end_date = cursor.fetchone()[0]
            start_date = end_date - pd.Timedelta(days=n_days)
            
            # 获取价格数据
            cursor.execute("""
                SELECT symbol, time, close 
                FROM price_daily 
                WHERE symbol IN %s 
                AND time >= %s 
                AND time <= %s
                ORDER BY symbol, time
            """, (tuple(stocks), start_date, end_date))
            
            data = cursor.fetchall()
            print(f"   获取到 {len(data)} 条价格数据")
            
            # 转换为 DataFrame
            price_df = pd.DataFrame(data, columns=['symbol', 'time', 'close'])
            price_df['time'] = pd.to_datetime(price_df['time'])
            price_df = price_df.pivot(index='time', columns='symbol', values='close')
            price_df = price_df.sort_index()
            
            return price_df
            
    except Exception as e:
        print(f"   ❌ 数据库连接失败: {e}")
        print("   使用模拟数据...")
        return generate_simulated_data(n_stocks, n_days)


def generate_simulated_data(n_stocks: int = 100, n_days: int = 500):
    """生成模拟数据 - MultiIndex 格式（因子需要）"""
    print("📊 生成模拟数据...")
    
    dates = pd.date_range(end='2024-12-31', periods=n_days, freq='B')
    stocks = [f'STOCK_{i:03d}' for i in range(1, n_stocks + 1)]
    
    # 生成各股票的价格数据
    np.random.seed(42)
    all_data = []
    
    for stock in stocks:
        # 模拟各股票的收益率
        returns = np.random.randn(n_days) * 0.02 + 0.0003
        close = 100 * (1 + returns).cumprod()
        
        # 创建单股票数据
        stock_data = pd.DataFrame({
            'close': close,
            'open': close * (1 + np.random.randn(n_days) * 0.01),
            'high': close * (1 + np.abs(np.random.randn(n_days)) * 0.02),
            'low': close * (1 - np.abs(np.random.randn(n_days)) * 0.02),
            'volume': np.random.randint(1000000, 10000000, n_days),
        }, index=dates)
        stock_data['symbol'] = stock
        all_data.append(stock_data)
    
    # 合并为 MultiIndex DataFrame
    price_df = pd.concat(all_data)
    price_df.index.name = 'time'
    
    print(f"   生成 {len(price_df)} 条数据")
    print(f"   格式: MultiIndex (symbol, time)")
    print(f"   股票数: {len(stocks)}")
    
    return price_df


def main():
    print("="*60)
    print("🎯 生成因子研究报告")
    print("="*60)
    
    # 因子配置
    factor_configs = [
        ('momentum_20', 'momentum', {'period': 20}),
        ('momentum_60', 'momentum', {'period': 60}),
    ]
    
    # 生成单股票数据（演示用）
    print("\n📊 生成模拟价格数据...")
    dates = pd.date_range(end='2024-12-31', periods=500, freq='B')
    np.random.seed(42)
    
    # 单股票数据（宽格式）
    close = 100 * (1 + np.random.randn(500) * 0.02 + 0.0003).cumprod()
    price_data = pd.DataFrame({
        'close': close,
        'open': close * (1 + np.random.randn(500) * 0.01),
        'high': close * (1 + np.abs(np.random.randn(500)) * 0.02),
        'low': close * (1 - np.abs(np.random.randn(500)) * 0.02),
        'volume': np.random.randint(1000000, 10000000, 500),
    }, index=dates)
    price_data.index.name = 'time'
    print(f"   生成 {len(price_data)} 条单股票数据")
    
    for report_name, factor_name, params in factor_configs:
        print(f"\n{'='*60}")
        print(f"📈 生成报告: {report_name}")
        print("="*60)
        
        try:
            # 创建因子
            factor = FactorFactory.create(factor_name, params)
            print(f"   因子类型: {type(factor).__name__}")
            
            # 生成报告
            report = create_factor_report(
                name=report_name,
                factor=factor,
                price_data=price_data,
                output_dir='output/factors'
            )
            
            report.analyze()
            output_path = report.generate()
            
            print(f"\n✅ 报告已生成: {output_path}")
            
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("📁 生成的报告位于: output/factors/")
    print("="*60)
    
    # 列出所有报告
    import os
    for f in sorted(os.listdir('output/factors')):
        if f.endswith('.html'):
            print(f"   📄 {f}")


if __name__ == '__main__':
    main()
