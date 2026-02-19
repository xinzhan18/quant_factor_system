"""
历史股票列表管理器
Historical Stock List Manager

功能:
- 记录每年年末的股票列表
- 处理退市股票
- 生成全市场股票列表

使用:
    python -m quant_factor_system.scripts.manage_stock_list --year 2015 --generate
"""

import json
from datetime import datetime
from typing import List
import logging
import os

logger = logging.getLogger(__name__)

# 股票列表缓存目录
STOCK_LIST_DIR = './.cache/stock_lists'


class StockListManager:
    """
    历史股票列表管理器
    """
    
    def __init__(self):
        os.makedirs(STOCK_LIST_DIR, exist_ok=True)
    
    def _get_stock_list_file(self, year: int) -> str:
        """获取股票列表文件路径"""
        return f'{STOCK_LIST_DIR}/stocks_{year}.json'
    
    def save_year_end_stocks(
        self,
        year: int,
        stocks: list = None,
        source: str = 'ricequant'
    ):
        """
        保存某年末股票列表
        
        Args:
            year: 年份
            stocks: 股票列表 (默认从米筐获取)
            source: 数据源
        """
        if stocks is None:
            from quant_factor_system.data import RiceQuantSource
            rq = RiceQuantSource()
            
            # 获取该年末最后一个交易日的股票列表
            end_date = f'{year}1231'
            stocks_df = rq.get_all_stocks(date=end_date)
            
            if stocks_df.empty:
                logger.warning(f"⚠️ 无法获取 {year} 年股票列表")
                return
            
            # 提取股票代码
            stocks = []
            for _, row in stocks_df.iterrows():
                order_book_id = row['order_book_id']
                if order_book_id.endswith('.SH'):
                    stocks.append(f'SH{order_book_id.split(".")[0]}')
                elif order_book_id.endswith('.XSHE'):
                    stocks.append(f'SZ{order_book_id.split(".")[0]}')
        
        # 保存
        file_path = self._get_stock_list_file(year)
        data = {
            'year': year,
            'count': len(stocks),
            'stocks': sorted(stocks),
            'source': source,
            'updated': datetime.now().isoformat()
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 保存 {year} 年股票列表: {len(stocks)} 只")
    
    def get_year_stocks(self, year: int) -> List[str]:
        """
        获取某年股票列表
        
        Args:
            year: 年份
            
        Returns:
            股票代码列表
        """
        file_path = self._get_stock_list_file(year)
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
            return data.get('stocks', [])
        
        # 如果不存在，尝试从米筐获取
        logger.info(f"📥 尝试获取 {year} 年股票列表...")
        self.save_year_end_stocks(year)
        
        # 重新加载
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
            return data.get('stocks', [])
        
        return []
    
    def get_historical_stocks(
        self,
        start_year: int,
        end_year: int
    ) -> List[str]:
        """
        获取历史股票列表（合并多年）
        
        功能:
        - 获取指定年份范围内的所有股票
        - 包括已退市股票
        - 去除重复
        
        Args:
            start_year: 起始年份
            end_year: 结束年份
            
        Returns:
            合并后的股票列表
        """
        all_stocks = set()
        
        for year in range(start_year, end_year + 1):
            stocks = self.get_year_stocks(year)
            all_stocks.update(stocks)
            logger.info(f"  {year}年: {len(stocks)} 只")
        
        result = sorted(list(all_stocks))
        logger.info(f"\n📊 历史股票总数: {len(result)}")
        
        return result
    
    def get_full_market_stocks(self, year: int) -> List[str]:
        """
        获取某年全市场股票列表
        
        优先使用:
        1. 预存的年末股票列表
        2. 实时API获取
        
        Args:
            year: 年份
            
        Returns:
            股票代码列表
        """
        # 尝试从缓存获取
        stocks = self.get_year_stocks(year)
        
        if stocks:
            return stocks
        
        # 实时获取
        from quant_factor_system.data import RiceQuantSource
        rq = RiceQuantSource()
        
        stocks_df = rq.get_all_stocks(date=f'{year}1231')
        
        if stocks_df.empty:
            return []
        
        stocks = []
        for _, row in stocks_df.iterrows():
            order_book_id = row['order_book_id']
            if order_book_id.endswith('.SH'):
                stocks.append(f'SH{order_book_id.split(".")[0]}')
            elif order_book_id.endswith('.XSHE'):
                stocks.append(f'SZ{order_book_id.split(".")[0]}')
        
        # 保存
        self.save_year_stocks(year, stocks)
        
        return stocks


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='历史股票列表管理工具')
    
    parser.add_argument(
        '--year',
        type=int,
        default=None,
        help='指定年份'
    )
    
    parser.add_argument(
        '--start-year',
        type=int,
        default=2015,
        help='起始年份'
    )
    
    parser.add_argument(
        '--end-year',
        type=int,
        default=2024,
        help='结束年份'
    )
    
    parser.add_argument(
        '--generate',
        action='store_true',
        default=False,
        help='生成历史股票列表'
    )
    
    parser.add_argument(
        '--count',
        action='store_true',
        default=False,
        help='显示股票数量'
    )
    
    args = parser.parse_args()
    
    manager = StockListManager()
    
    if args.count and args.year:
        stocks = manager.get_year_stocks(args.year)
        print(f"\n{args.year} 年股票数量: {len(stocks)}")
        return
    
    if args.generate:
        print(f"\n生成 {args.start_year}-{args.end_year} 年历史股票列表...")
        
        all_stocks = manager.get_historical_stocks(
            args.start_year,
            args.end_year
        )
        
        print(f"\n历史股票总数: {len(all_stocks)}")
        print(f"示例: {all_stocks[:20]}")
        return
    
    if args.year:
        stocks = manager.get_full_market_stocks(args.year)
        print(f"\n{args.year} 年股票数量: {len(stocks)}")
        print(f"示例: {stocks[:20]}")


if __name__ == '__main__':
    main()
