"""
全市场数据拉取示例
Full Market Fetch Example

运行:
    python examples/fetch_full_market_example.py
"""

import sys
sys.path.insert(0, '.')

from quant_factor_system.scripts.fetch_full_market import FullMarketFetcher


def example_check_status():
    """示例: 查看拉取状态"""
    print("\n" + "="*60)
    print("示例1: 查看拉取状态")
    print("="*60)
    
    fetcher = FullMarketFetcher()
    status = fetcher.get_status()
    
    print(f"\n已完成年份: {status['completed_years']}")
    print(f"待拉取年份: {status['pending_years']}")
    print(f"最后拉取: {status['last_date']}")


def example_fetch_single_year():
    """示例: 拉取单年数据"""
    print("\n" + "="*60)
    print("示例2: 拉取 2020 年数据")
    print("="*60)
    
    fetcher = FullMarketFetcher()
    
    # 拉取 2020 年
    result = fetcher.fetch_year(2020, force=False)
    
    print(f"\n结果: {result}")


def example_fetch_range():
    """示例: 拉取年份范围"""
    print("\n" + "="*60)
    print("示例3: 拉取 2015-2016 年数据")
    print("="*60)
    
    fetcher = FullMarketFetcher()
    
    # 拉取 2015-2016 年
    results = fetcher.fetch_range(2015, 2016, force=False)
    
    for r in results:
        print(f"  {r['year']}: {r.get('status', 'unknown')}")


def main():
    """运行所有示例"""
    print("\n" + "="*60)
    print("🚀 全市场数据拉取示例")
    print("="*60)
    
    try:
        # 示例1: 查看状态
        example_check_status()
        
        # 示例2: 拉取单年
        # example_fetch_single_year()
        
        # 示例3: 拉取范围
        # example_fetch_range()
        
        print("\n" + "="*60)
        print("✅ 示例运行完成")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
