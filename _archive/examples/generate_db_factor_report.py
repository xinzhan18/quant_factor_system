"""
使用数据库因子结构生成报告 - 模拟真实因子分析
"""

import sys
sys.path.insert(0, '/Users/xinzhan/.openclaw/workspace')

from quant_factor_system.factors.report import FactorReportGenerator
from quant_factor_system.data import TimescaleDB
import pandas as pd
import numpy as np
from datetime import datetime


def main():
    print("="*60)
    print("🎯 生成因子研究报告")
    print("="*60)
    
    # 从数据库获取因子结构信息
    db = TimescaleDB()
    factor_info = []
    
    try:
        with db.connection() as conn:
            cursor = conn.cursor()
            
            # 获取因子表信息
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'factor_%'
                ORDER BY table_name
            """)
            
            for row in cursor.fetchall():
                table_name = row[0]
                factor_name = table_name.replace('factor_', '')
                
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                
                factor_info.append({
                    'name': factor_name,
                    'table': table_name,
                    'count': count
                })
    
    except Exception as e:
        print(f"数据库连接失败: {e}")
        print("使用内置因子生成报告...")
    
    # 生成报告的因子
    report_configs = [
        ('momentum_20', '动量因子 (20日)', 'momentum', {'period': 20}),
        ('dist_ma10', '均线偏离 (10日)', 'dist_ma10', {}),
        ('volatility_20', '波动率因子 (20日)', 'volatility', {'window': 20}),
    ]
    
    from quant_factor_system.factors import FactorFactory
    
    # 生成模拟价格数据（长周期）
    print("\n📊 生成模拟价格数据...")
    dates = pd.date_range('2023-01-01', periods=500, freq='B')
    np.random.seed(42)
    
    # 模拟价格走势
    returns = np.random.randn(500) * 0.02 + 0.0003
    close = 100 * (1 + returns).cumprod()
    
    price_data = pd.DataFrame({
        'close': close,
        'open': close * (1 + np.random.randn(500) * 0.01),
        'high': close * (1 + np.abs(np.random.randn(500)) * 0.02),
        'low': close * (1 - np.abs(np.random.randn(500)) * 0.02),
    }, index=dates)
    price_data.index.name = 'time'
    
    print(f"   ✅ 生成 {len(price_data)} 条数据")
    print(f"   📅 日期范围: {dates[0].date()} ~ {dates[-1].date()}")
    
    # 为每个因子生成报告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for report_name, display_name, factor_type, params in report_configs:
        print(f"\n{'='*60}")
        print(f"📊 生成报告: {display_name}")
        print("="*60)
        
        try:
            # 创建因子
            factor = FactorFactory.create(factor_type, params)
            print(f"   因子类型: {type(factor).__name__}")
            
            # 生成报告
            output_file = f'{report_name}_{timestamp}.html'
            
            report = FactorReportGenerator(
                name=report_name,
                factor=factor,
                price_data=price_data,
                output_dir='output/factors'
            )
            
            report.analyze()
            report.generate(output_file)
            
            print(f"   ✅ 报告已生成: output/factors/{output_file}")
            
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            import traceback
            traceback.print_exc()
    
    # 打印数据库中的因子信息
    if factor_info:
        print("\n" + "="*60)
        print("📋 数据库中的因子表:")
        print("="*60)
        for info in factor_info:
            print(f"   📊 {info['table']:25s} | {info['count']:>10,} 条记录")
    
    print("\n" + "="*60)
    print("📁 生成的报告:")
    print("="*60)
    
    import os
    for f in sorted(os.listdir('output/factors')):
        if f.endswith('.html') and '_' + timestamp + '.html' in f:
            print(f"   📄 {f}")


if __name__ == '__main__':
    main()
