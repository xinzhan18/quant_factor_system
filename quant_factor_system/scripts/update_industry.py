"""
行业因子更新脚本
Industry Factor Update Script

功能:
- 更新行业归属信息 (季度)
- 更新行业因子 (每日)

使用:
    # 更新行业归属 (季度执行)
    python -m quant_factor_system.scripts.update_industry_classification
    
    # 更新行业因子 (每日执行)
    python -m quant_factor_system.scripts.update_industry_factors --date 2024-01-01
"""

import sys
import argparse
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_industry_classification():
    """
    更新行业归属信息
    
    建议: 季度执行一次
    """
    from quant_factor_system.data import IndustrySource, IndustryStorage
    
    logger.info("🔄 开始更新行业归属信息...")
    
    # 获取最新行业分类
    source = IndustrySource()
    
    today = datetime.now().strftime('%Y%m%d')
    df = source.get_industry_classification(date=today)
    
    if df.empty:
        logger.warning("⚠️ 获取行业分类失败")
        return False
    
    # 添加日期列
    df['update_date'] = today
    
    # 保存
    storage = IndustryStorage()
    storage.create_tables()
    
    count = storage.save_industry_classification(df)
    
    logger.info(f"✅ 行业归属更新完成: {count} 条记录")
    return True


def update_industry_factors(date: str = None, force: bool = False):
    """
    更新行业因子
    
    建议: 每日收盘后执行
    
    Args:
        date: 更新日期
        force: 强制更新
    """
    from quant_factor_system.data import IndustrySource, IndustryStorage
    
    logger.info(f"🔄 开始更新行业因子... (日期: {date})")
    
    date = date or datetime.now().strftime('%Y%m%d')
    
    # 检查是否需要更新
    storage = IndustryStorage()
    
    if not force and not storage.need_daily_update(date):
        logger.info(f"ℹ️ {date} 行业因子已存在，跳过更新")
        return True
    
    # 获取行业因子
    source = IndustrySource()
    
    factors = [
        'industry_return',
        'industry_momentum',
        'industry_volatility',
        'industry_size',
        'industry_turnover'
    ]
    
    df = source.get_industry_factors(date=date, factors=factors)
    
    if df.empty:
        logger.warning("⚠️ 获取行业因子失败")
        return False
    
    # 保存
    storage.create_tables()
    
    count = storage.save_industry_factors(df, date=date)
    
    logger.info(f"✅ 行业因子更新完成: {count} 条记录")
    return True


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description='行业因子更新工具')
    
    parser.add_argument(
        '--type',
        choices=['classification', 'factors', 'all'],
        default='all',
        help='更新类型: classification(行业归属), factors(行业因子), all(全部)'
    )
    
    parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='更新日期 (YYYYMMDD格式)'
    )
    
    parser.add_argument(
        '--force',
        action='true',
        default=False,
        help='强制更新'
    )
    
    args = parser.parse_args()
    
    results = {}
    
    if args.type in ['classification', 'all']:
        results['classification'] = update_industry_classification()
    
    if args.type in ['factors', 'all']:
        results['factors'] = update_industry_factors(args.date, args.force)
    
    # 输出结果
    logger.info("\n📊 更新结果:")
    for key, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        logger.info(f"  {key}: {status}")
    
    return all(results.values())


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
