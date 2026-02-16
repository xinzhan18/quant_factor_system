"""
全市场日线数据批量拉取脚本
Full Market Daily Data Fetcher

功能:
- 从2015年开始拉取全市场日线数据
- 分批拉取，避免API限制
- 支持断点续传
- 增量更新

使用:
    # 拉取全部年份
    python -m quant_factor_system.scripts.fetch_full_market
    
    # 从指定年份开始
    python -m quant_factor_system.scripts.fetch_full_market --start-year 2015 --end-year 2024
    
    # 仅拉取单年
    python -m quant_factor_system.scripts.fetch_full_market --year 2020
"""

import sys
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FullMarketFetcher:
    """
    全市场数据批量拉取器
    """
    
    # 拉取配置
    BATCH_SIZE = 500          # 每批股票数量
    API_DELAY = 0.5           # API请求间隔（秒）
    MAX_RETRIES = 3           # 最大重试次数
    
    def __init__(self):
        from quant_factor_system.data import RiceQuantSource, TimescaleDB
        
        self.source = RiceQuantSource()
        self.db = TimescaleDB()
        
        # 拉取状态
        self.state_file = './.cache/fetch_state.json'
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """加载拉取状态"""
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except:
            return {'completed_years': [], 'last_date': None}
    
    def _save_state(self):
        """保存拉取状态"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f)
    
    def _get_all_symbols(self, year: int = None) -> List[str]:
        """
        获取全市场股票列表
        
        优先使用:
        1. 历史股票列表管理器（包含退市股票）
        2. 实时米筐API（仅当前股票）
        
        Args:
            year: 指定年份（使用该年末的股票列表）
        """
        if year:
            # 使用历史股票列表管理器
            from .stock_list_manager import StockListManager
            
            manager = StockListManager()
            symbols = manager.get_year_stocks(year)
            
            if symbols:
                logger.info(f"📋 使用 {year} 年历史股票列表: {len(symbols)} 只")
                return symbols
        
        # 默认：实时获取
        stocks = self.source.get_all_stocks()
        
        if stocks.empty:
            logger.warning("⚠️ 获取股票列表失败，使用模拟数据")
            return [f'SH{600000 + i:06d}' for i in range(3000)]
        
        # 转换股票代码
        symbols = []
        for _, row in stocks.iterrows():
            order_book_id = row['order_book_id']
            if order_book_id.endswith('.SH'):
                symbols.append(f'SH{order_book_id.split(".")[0]}')
            elif order_book_id.endswith('.XSHE'):
                symbols.append(f'SZ{order_book_id.split(".")[0]}')
        
        return symbols
    
    def _split_batches(self, symbols: List[str], batch_size: int = None) -> List[List[str]]:
        """分批"""
        batch_size = batch_size or self.BATCH_SIZE
        return [symbols[i:i+batch_size] for i in range(0, len(symbols), batch_size)]
    
    def _get_trading_days(self, year: int) -> List[str]:
        """获取某年交易日"""
        start = f'{year}0101'
        end = f'{year}1231'
        
        return self.source.get_trading_days(start_date=start, end_date=end)
    
    def fetch_year(
        self,
        year: int,
        force: bool = False
    ) -> Dict:
        """
        拉取某年全市场数据
        
        Args:
            year: 年份
            force: 强制重新拉取
            
        Returns:
            拉取统计
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"📅 开始拉取 {year} 年数据")
        logger.info(f"{'='*60}")
        
        # 检查是否已完成
        if not force and year in self.state['completed_years']:
            logger.info(f"ℹ️ {year} 年已拉取过，跳过")
            return {'status': 'skipped', 'year': year}
        
        # 获取全市场股票（使用该年末的股票列表，包含退市股票）
        all_symbols = self._get_all_symbols(year=year)
        batches = self._split_batches(all_symbols)
        
        logger.info(f"📊 总股票数: {len(all_symbols)}, 分为 {len(batches)} 批")
        
        # 获取交易日
        trading_days = self._get_trading_days(year)
        logger.info(f"📅 交易日数: {len(trading_days)}")
        
        # 拉取统计
        stats = {
            'year': year,
            'total_symbols': len(all_symbols),
            'total_batches': len(batches),
            'trading_days': len(trading_days),
            'success': 0,
            'failed': 0,
            'duplicates': 0
        }
        
        # 分批拉取
        for batch_idx, batch_symbols in enumerate(batches):
            if batch_idx % 10 == 0:
                logger.info(f"  进度: {batch_idx}/{len(batches)} 批")
            
            try:
                # 拉取该批次全年数据
                result = self._fetch_batch(
                    batch_symbols,
                    f'{year}0101',
                    f'{year}1231'
                )
                
                stats['success'] += result['success']
                stats['failed'] += result.get('failed', 0)
                stats['duplicates'] += result.get('duplicates', 0)
                
            except Exception as e:
                logger.error(f"  ❌ 批次 {batch_idx} 失败: {e}")
                stats['failed'] += len(batch_symbols)
            
            # API延迟
            import time
            time.sleep(self.API_DELAY)
        
        # 更新状态
        if stats['failed'] == 0:
            self.state['completed_years'].append(year)
            self.state['last_date'] = f'{year}-12-31'
            self._save_state()
        
        logger.info(f"\n✅ {year} 年拉取完成:")
        logger.info(f"   成功: {stats['success']} 条")
        logger.info(f"   跳过(已存在): {stats['duplicates']} 条")
        logger.info(f"   失败: {stats['failed']} 条")
        
        return stats
    
    def _fetch_batch(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str
    ) -> Dict:
        """拉取单批次数据"""
        # 获取数据
        df = self.source.get_daily_data(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date
        )
        
        if df.empty:
            return {'success': 0, 'duplicates': 0, 'failed': len(symbols)}
        
        # 检查已存在的数据
        existing_dates = self._get_existing_dates(symbols, start_date, end_date)
        
        # 过滤已存在
        if 'time' in df.columns:
            date_col = 'time'
        elif 'date' in df.columns:
            date_col = 'date'
        else:
            date_col = None
        
        if date_col:
            df['date_str'] = df[date_col].astype(str)
            df = df[~df['date_str'].isin(existing_dates)]
        
        if df.empty:
            return {'success': 0, 'duplicates': len(symbols)}
        
        # 保存到数据库
        count = self.db.insert_price(df, table='price_daily')
        
        return {
            'success': count,
            'duplicates': len(symbols) - len(df),
            'failed': 0
        }
    
    def _get_existing_dates(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str
    ) -> set:
        """获取已存在的日期"""
        existing = set()
        
        try:
            df = self.db.query_daily(
                symbols=symbols[:10],  # 只查几只作为参考
                start_date=start_date,
                end_date=end_date
            )
            
            if not df.empty:
                if isinstance(df.index, pd.MultiIndex):
                    existing = set(df.index.get_level_values('time').astype(str))
                elif 'time' in df.columns:
                    existing = set(df['time'].astype(str))
        except:
            pass
        
        return existing
    
    def fetch_range(
        self,
        start_year: int,
        end_year: int,
        force: bool = False
    ) -> List[Dict]:
        """
        拉取年份范围数据
        
        Args:
            start_year: 起始年份
            end_year: 结束年份
            force: 强制重新拉取
        """
        logger.info(f"\n🚀 开始批量拉取: {start_year} - {end_year}")
        logger.info(f"预计需要拉取 {end_year - start_year + 1} 年数据")
        logger.info(f"每批 {self.BATCH_SIZE} 只股票，间隔 {self.API_DELAY} 秒")
        
        results = []
        
        for year in range(start_year, end_year + 1):
            result = self.fetch_year(year, force=force)
            results.append(result)
        
        # 汇总
        total_success = sum(r.get('success', 0) for r in results)
        total_failed = sum(r.get('failed', 0) for r in results)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 批量拉取完成:")
        logger.info(f"   总成功: {total_success:,} 条")
        logger.info(f"   总失败: {total_failed:,} 条")
        logger.info(f"   完成年份: {len([r for r in results if r.get('status') == 'success'])}/{end_year - start_year + 1}")
        logger.info(f"{'='*60}")
        
        return results
    
    def get_status(self) -> Dict:
        """获取拉取状态"""
        return {
            'completed_years': self.state.get('completed_years', []),
            'last_date': self.state.get('last_date'),
            'pending_years': [y for y in range(2015, 2025) if y not in self.state.get('completed_years', [])]
        }


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description='全市场日线数据拉取工具')
    
    parser.add_argument(
        '--start-year',
        type=int,
        default=2015,
        help='起始年份 (默认: 2015)'
    )
    
    parser.add_argument(
        '--end-year',
        type=int,
        default=2024,
        help='结束年份 (默认: 2024)'
    )
    
    parser.add_argument(
        '--year',
        type=int,
        default=None,
        help='仅拉取指定年份'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        default=False,
        help='强制重新拉取'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        default=False,
        help='查看拉取状态'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=500,
        help='每批股票数量 (默认: 500)'
    )
    
    args = parser.parse_args()
    
    fetcher = FullMarketFetcher()
    fetcher.BATCH_SIZE = args.batch_size
    
    # 查看状态
    if args.status:
        status = fetcher.get_status()
        print(f"\n📊 拉取状态:")
        print(f"   已完成年份: {status['completed_years']}")
        print(f"   待拉取年份: {status['pending_years']}")
        print(f"   最后拉取: {status['last_date']}")
        return
    
    # 拉取单年
    if args.year:
        fetcher.fetch_year(args.year, force=args.force)
        return
    
    # 拉取年份范围
    fetcher.fetch_range(args.start_year, args.end_year, force=args.force)


if __name__ == '__main__':
    import pandas as pd
    main()
