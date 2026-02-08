"""
专业因子分析示例
Professional Factor Analysis Example

展示：
1. 真实数据获取
2. 涨跌停过滤
3. 市值中性化
4. 行业中性化
"""

import pandas as pd
import numpy as np
from datetime import datetime

from quant_factor_system import (
    # 数据处理（专业版）
    get_real_stock_data,
    get_market_index_data,
    DataProcessor,
    FactorNeutralizer,
    FactorPreprocessor,
    
    # 因子
    MomentumFactor,
    ValueFactor,
    QualityFactor,
    
    # 评估
    FactorEvaluator,
)


def create_sample_data_with_limit():
    """
    创建带有涨跌停的示例数据
    """
    np.random.seed(42)
    
    dates = pd.date_range(start='2023-01-01', periods=1000, freq='B')
    n = len(dates)
    
    # 创建多只股票
    stocks = ['STOCK_00%d' % i for i in range(1, 51)]
    all_data = []
    
    for stock in stocks:
        # 价格走势
        trend = np.linspace(0.01, 0.02, n)
        noise = np.random.randn(n) * 0.02
        returns = trend + noise
        
        # 添加涨停/跌停
        returns[np.random.choice(n, n//50)] = 0.10  # 涨停
        returns[np.random.choice(n, n//50)] = -0.10  # 跌停
        
        prices = 100 * np.cumprod(1 + returns)
        
        df = pd.DataFrame({
            'symbol': stock,
            'close': prices,
            'pct_chg': returns * 100,
            'pe': np.random.uniform(10, 50, n),
            'pb': np.random.uniform(1, 10, n),
            'roe': np.random.uniform(0.05, 0.25, n),
            'revenue': np.cumsum(np.random.randn(n) * 1e7 + 1e7),
            'market_cap': prices * np.random.uniform(1e6, 1e7, n),
            'volume': np.random.randint(1e6, 1e8, n),
            'turnover': np.random.uniform(0.001, 0.05, n),
            'industry': np.random.choice(['银行', '医药', '消费', '科技', '制造'], n),
        }, index=dates)
        
        all_data.append(df)
    
    data = pd.concat(all_data)
    return data


def demo_data_processing():
    """
    演示专业数据处理
    """
    print("\n" + "="*60)
    print("🔧 专业数据处理演示")
    print("="*60)
    
    # 1. 创建示例数据（含涨跌停）
    print("\n📊 步骤1: 创建示例数据")
    data = create_sample_data_with_limit()
    print(f"  原始数据: {len(data)} 条, {data['symbol'].nunique()} 只股票")
    
    # 2. 涨跌停过滤
    print("\n🚦 步骤2: 涨跌停过滤")
    processor = DataProcessor()
    
    df_clean, stats = processor.filter_limit_stocks(data.copy(), remove=True)
    
    print(f"  原始记录: {stats['total_records']}")
    print(f"  涨停数量: {stats['limit_up_count']} ({stats['limit_up_ratio']:.2f}%)")
    print(f"  跌停数量: {stats['limit_down_count']} ({stats['limit_down_ratio']:.2f}%)")
    print(f"  过滤后: {len(df_clean)} 条 ({len(df_clean)/len(data)*100:.1f}%)")
    
    # 3. 完整预处理
    print("\n⚙️ 步骤3: 完整预处理")
    preprocessor = FactorPreprocessor()
    
    config = {
        'filters': {
            'remove_limit': True,
            'min_price': 3.0,
            'min_cap': 1e9,
            'min_turnover': 0.001
        },
        'neutralize': {
            'market_cap': True,
            'industry': True
        }
    }
    
    df_final, final_stats = preprocessor.preprocess(data.copy(), config)
    
    # 获取最终记录数
    final_records = final_stats.get('final_records', 
                    final_stats.get('after_filtering', 
                    len(df_final)))
    retention = final_stats.get('retention_ratio',
                    final_records / final_stats['original_records'] * 100 if 'original_records' in final_stats else 0)
    
    print(f"  原始记录: {final_stats['original_records']}")
    print(f"  最终记录: {final_records}")
    print(f"  保留比例: {retention:.1f}%")
    
    return df_final


def demo_factor_neutralization(data):
    """
    演示因子中性化
    """
    print("\n" + "="*60)
    print("⚖️ 因子中性化演示")
    print("="*60)
    
    neutralizer = FactorNeutralizer()
    
    # 计算动量因子
    momentum = data.groupby('symbol')['close'].pct_change(20)
    
    # 市值中性化
    print("\n📈 市值中性化:")
    neutralized_mcap = neutralizer.neutralize_market_cap(
        momentum.dropna(),
        data['market_cap'].loc[momentum.dropna().index]
    )
    
    print(f"  原始动量 - 均值: {momentum.mean():.6f}, 标准差: {momentum.std():.6f}")
    print(f"  中性化后 - 均值: {neutralized_mcap.mean():.6f}, 标准差: {neutralized_mcap.std():.6f}")
    
    # 行业中性化
    print("\n🏭 行业中性化:")
    neutralized_industry = neutralizer.neutralize_industry(
        momentum.dropna(),
        data['industry'].loc[momentum.dropna().index]
    )
    
    print(f"  原始动量 - 均值: {momentum.mean():.6f}")
    print(f"  中性化后 - 均值: {neutralized_industry.mean():.6f}")
    
    # 双重中性化
    print("\n🔄 双重中性化 (市值 + 行业):")
    neutralized_both = neutralizer.neutralize_both(
        momentum.dropna(),
        data['market_cap'].loc[momentum.dropna().index],
        data['industry'].loc[momentum.dropna().index]
    )
    
    print(f"  原始 - 均值: {momentum.mean():.6f}, 标准差: {momentum.std():.6f}")
    print(f"  双重中性化 - 均值: {neutralized_both.mean():.6f}, 标准差: {neutralized_both.std():.6f}")
    
    return neutralized_both


def demo_factor_evaluation(data, neutralized_momentum):
    """
    演示因子评估
    """
    print("\n" + "="*60)
    print("📊 因子评估演示")
    print("="*60)
    
    # 创建因子系统
    from quant_factor_system import FactorSystem
    
    system = FactorSystem(name="Professional Factor System")
    system.add_factor(MomentumFactor(period=20), weight=1.0)
    system.add_factor(ValueFactor(metric='pe'), weight=1.0)
    system.add_factor(QualityFactor(metric='roe'), weight=1.0)
    
    # 计算因子
    print("\n🔢 计算因子...")
    factor_values = system.calculate_all(data)
    print(f"  因子数量: {len(system.factors)}")
    print(f"  数据形状: {factor_values.shape}")
    
    # 计算收益率
    returns = data.groupby('symbol')['close'].pct_change().dropna()
    
    # 评估
    evaluator = FactorEvaluator(system)
    
    print("\n📈 IC 分析:")
    ic_results = evaluator.evaluate_ic(returns)
    
    for name, ic in ic_results.items():
        status = "✅" if ic['ic'] > 0.03 else ("⚠️" if ic['ic'] > 0 else "❌")
        print(f"  {status} {name}: IC={ic['ic']:.4f}, IR={ic['ic_ir']:.4f}, 胜率={ic['ic_sign_ratio']:.2%}")
    
    return ic_results


def demo_real_data():
    """
    演示真实数据获取
    """
    print("\n" + "="*60)
    print("🌐 真实数据获取演示")
    print("="*60)
    
    print("\n📊 尝试获取真实 A 股数据...")
    
    try:
        # 获取单只股票数据
        data = get_real_stock_data('000001', '2023-01-01', '2024-01-01')
        
        if not data.empty:
            print(f"  ✅ 成功获取 {len(data)} 条数据")
            print(f"  股票: {data['symbol'].iloc[0]}")
            print(f"  时间范围: {data.index.min()} ~ {data.index.max()}")
            print(f"  价格范围: {data['close'].min():.2f} ~ {data['close'].max():.2f}")
            return data
        else:
            print("  ⚠️ 无法获取真实数据，使用模拟数据")
            return None
            
    except ImportError:
        print("  ⚠️ 请安装 akshare: pip install akshare")
        return None
    except Exception as e:
        print(f"  ❌ 获取数据失败: {e}")
        return None


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🚀 专业因子分析系统演示")
    print("="*60)
    
    # 1. 真实数据获取
    real_data = demo_real_data()
    
    # 2. 数据处理
    data = demo_data_processing()
    
    # 3. 因子中性化
    neutralized = demo_factor_neutralization(data)
    
    # 4. 因子评估
    ic_results = demo_factor_evaluation(data, neutralized)
    
    # 总结
    print("\n" + "="*60)
    print("📋 演示总结")
    print("="*60)
    
    print("""
✅ 已实现的专业功能:
    
1. 📥 真实数据获取
   - 支持 AkShare A股数据
   - 支持指数数据 (沪深300, 中证500等)
   
2. 🚦 涨跌停过滤
   - 自动检测涨停/跌停/停牌
   - 可选择移除或标记
   
3. ⚖️ 因子中性化
   - 市值中性化 (回归残差法)
   - 行业中性化 (行业虚拟变量)
   - 双重中性化 (同时处理)
   
4. 📊 完整预处理流程
   - 涨跌停过滤
   - 价格过滤
   - 市值过滤
   - 换手率过滤

📝 使用方法:
    
    from quant_factor_system import (
        get_real_stock_data,
        DataProcessor,
        FactorNeutralizer,
    )
    
    # 获取数据
    data = get_real_stock_data('000001', '2023-01-01', '2024-01-01')
    
    # 过滤涨跌停
    processor = DataProcessor()
    df_clean, stats = processor.filter_limit_stocks(data, remove=True)
    
    # 中性化
    neutralizer = FactorNeutralizer()
    neutralized = neutralizer.neutralize_market_cap(factor, df_clean['market_cap'])

💡 提示:
   - 安装依赖: pip install akshare statsmodels
   - 中性化可消除市值和行业偏差
   - 涨跌停过滤避免极端值影响
""")
    
    print("="*60)
    print("✅ 专业因子分析演示完成!")
    print("="*60)


if __name__ == "__main__":
    main()
