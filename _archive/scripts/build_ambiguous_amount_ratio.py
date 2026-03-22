#!/usr/bin/env python
"""
模糊金额比因子构建脚本

因子逻辑:
1. 对股票i计算n日内的1分钟收益率
2. 计算第t分钟的波动率: [t-4, t]区间内分钟收益率的标准差
3. 计算第t分钟的模糊性: [t-4, t]区间内上述分钟波动率的标准差
4. 日内模糊性 > 日内模糊性均值 → "起雾时刻"
5. 总体金额 = 所有时刻的分钟成交额均值
6. 模糊金额比 = 起雾时刻成交额 / 总体金额
7. 月度处理: 每月末对最近20天求均值和标准差，等权合并

参数:
- n: 计算窗口天数 (默认20)
- monthly_window: 月度窗口 (默认20)
- ambiguity_window: 模糊性窗口 (默认5，即[t-4, t])
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
import warnings
warnings.filterwarnings('ignore')

# 设置环境变量
os.environ['RQDATAC_CONF'] = os.environ.get(
    'RQDATAC_CONF',
    'tcp://license:HZ9KQ7fUrGDbo_F2vppomXjs3-VpXzGY5anDDKDL5Te49kbTtDLmsTneaTvNNkDMMnQ9uUVeTHWkfwSMPaTt8CVZGZkaywfraeEUVOMXz1W6bGnuXoOTJ1qHVm5sfOGzMG-3drD1uYKCGNWfAAyIJbF0lnfJlzl9l0YElhWdUUk=DG_OVcg3wFeBRyuAjywrddEqJomlNjGY3EmKFLp-2KYeKg6hY7qwf4jxFxy_36gZSsvaAhhClwjLCZEJCW3RRGGFLoID28nZq4xkVjBF7p0-u-GyOqcnuxnio7eWJ5HklkwpInBUIY2x7sgIVvf-jgw3OlUZMKcv5KBilmi0DKE=@rqdatad-pro.ricequant.com:16011'
)

# 添加项目路径
sys.path.insert(0, '/Users/xinzhan/.openclaw/workspace/quant_factor_system')

# 直接导入，避免从包导入
import importlib.util
spec = importlib.util.spec_from_file_location(
    "ricequant_source", 
    "/Users/xinzhan/.openclaw/workspace/quant_factor_system/data/ricequant_source.py"
)
RiceQuantSource = importlib.util.module_from_spec(spec)
spec.loader.exec_module(RiceQuantSource)
RiceQuantSource = RiceQuantSource.RiceQuantSource


class AmbiguousAmountRatioFactor:
    """模糊金额比因子"""
    
    def __init__(
        self,
        n: int = 20,
        monthly_window: int = 20,
        ambiguity_window: int = 5
    ):
        """
        初始化
        
        Args:
            n: 计算窗口天数
            monthly_window: 月度窗口天数
            ambiguity_window: 模糊性窗口大小
        """
        self.n = n
        self.monthly_window = monthly_window
        self.ambiguity_window = ambiguity_window
        self.source = RiceQuantSource()
        
    def calculate_for_symbol(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        计算单个股票的模糊金额比因子
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            包含因子值的DataFrame
        """
        print(f"  处理股票: {symbol}")
        
        # 获取分钟数据
        df = self.source.get_minute_data(
            symbols=[symbol],
            start_date=start_date,
            end_date=end_date,
            frequency='1min'
        )
        
        if df.empty:
            print(f"    无数据: {symbol}")
            return pd.DataFrame()
        
        # 处理列名（兼容不同数据源）
        if 'datetime' in df.columns:
            df['time'] = df['datetime']
        if 'total_turnover' in df.columns:
            df['amount'] = df['total_turnover']
        elif 'amount' not in df.columns:
            df['amount'] = df['volume'] * df['close']
        
        # 统一symbol格式
        if 'order_book_id' in df.columns:
            df['symbol'] = df['order_book_id']
        
        # 解析时间
        df['time'] = pd.to_datetime(df['time'])
        df['date'] = df['time'].dt.date
        
        # 按日期分组计算
        results = []
        
        # 获取所有交易日
        trading_dates = sorted(df['date'].unique())
        
        # 计算每一天的模糊金额比
        for i, current_date in enumerate(trading_dates):
            # 获取最近n天的数据
            start_idx = max(0, i - self.n + 1)
            window_dates = trading_dates[start_idx:i+1]
            
            # 合并窗口内所有数据
            window_data = df[df['date'].isin(window_dates)].copy()
            
            if window_data.empty:
                continue
            
            # 计算分钟收益率
            window_data = window_data.sort_values('time')
            window_data['return'] = window_data['close'].pct_change()
            
            # 剔除开盘前9分钟的数据（根据因子描述）
            # 开盘 9:30，前9分钟是 09:30-09:38
            window_data['minute'] = window_data['time'].dt.time
            from datetime import time
            market_open = time(9, 30)
            market_close = time(15, 00)
            
            # 剔除开盘后9分钟和收盘前若干分钟
            window_data = window_data[
                (window_data['minute'] > time(9, 38)) & 
                (window_data['minute'] < market_close)
            ]
            
            if window_data.empty or len(window_data) < 10:
                continue
            
            # 计算波动率 (5分钟窗口)
            window_data['volatility'] = window_data['return'].rolling(
                window=self.ambiguity_window, 
                min_periods=self.ambiguity_window
            ).std()
            
            # 计算模糊性 (5分钟窗口的波动率的标准差)
            window_data['ambiguity'] = window_data['volatility'].rolling(
                window=self.ambiguity_window,
                min_periods=self.ambiguity_window
            ).std()
            
            # 获取当天的数据
            today_data = window_data[window_data['date'] == current_date].copy()
            
            if today_data.empty or today_data['ambiguity'].isna().all():
                continue
            
            # 计算当天的模糊性均值
            today_ambiguity_mean = today_data['ambiguity'].mean()
            
            if pd.isna(today_ambiguity_mean):
                continue
            
            # 识别"起雾时刻"（模糊性 > 均值）
            today_data['is_foggy'] = today_data['ambiguity'] > today_ambiguity_mean
            
            # 计算总体金额（所有时刻的分钟成交额均值）
            total_amount = today_data['amount'].mean()
            
            # 计算起雾时刻的成交额均值
            foggy_amount = today_data[today_data['is_foggy']]['amount'].mean()
            
            if pd.isna(foggy_amount) or total_amount == 0:
                continue
            
            # 模糊金额比
            ambiguous_ratio = foggy_amount / total_amount
            
            results.append({
                'symbol': symbol,
                'date': current_date,
                'ambiguous_ratio': ambiguous_ratio,
                'foggy_amount': foggy_amount,
                'total_amount': total_amount,
                'ambiguity_mean': today_ambiguity_mean
            })
        
        return pd.DataFrame(results)
    
    def calculate_monthly(
        self,
        daily_results: pd.DataFrame
    ) -> pd.DataFrame:
        """
        月度处理: 每月末对最近20天求均值和标准差，等权合并
        
        Args:
            daily_results: 日度因子结果
            
        Returns:
            月度因子结果
        """
        if daily_results.empty:
            return pd.DataFrame()
        
        daily_results['date'] = pd.to_datetime(daily_results['date'])
        daily_results['month'] = daily_results['date'].dt.to_period('M')
        
        monthly_results = []
        
        for (symbol, month), group in daily_results.groupby(['symbol', 'month']):
            if len(group) < 5:  # 至少5天数据
                continue
            
            # 最近20天（或当月所有天）
            recent = group.tail(self.monthly_window)
            
            # 均值
            mean_value = recent['ambiguous_ratio'].mean()
            # 标准差
            std_value = recent['ambiguous_ratio'].std()
            
            # 等权合并
            final_value = (mean_value + std_value) / 2
            
            monthly_results.append({
                'symbol': symbol,
                'month': str(month),
                'ambiguous_ratio_monthly': final_value,
                'ambiguous_ratio_mean': mean_value,
                'ambiguous_ratio_std': std_value,
                'days_count': len(recent)
            })
        
        return pd.DataFrame(monthly_results)
    
    def run(
        self,
        symbols: list,
        start_date: str,
        end_date: str,
        output_path: str = None
    ) -> pd.DataFrame:
        """
        运行因子计算
        
        Args:
            symbols: 股票列表
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            output_path: 输出路径
            
        Returns:
            因子数据
        """
        print("=" * 70)
        print("模糊金额比因子计算")
        print("=" * 70)
        print(f"参数: n={self.n}, monthly_window={self.monthly_window}, ambiguity_window={self.ambiguity_window}")
        print(f"股票数: {len(symbols)}")
        print(f"时间范围: {start_date} ~ {end_date}")
        print("=" * 70)
        
        all_results = []
        
        for i, symbol in enumerate(symbols):
            print(f"\n[{i+1}/{len(symbols)}]", end=" ")
            
            result = self.calculate_for_symbol(symbol, start_date, end_date)
            
            if not result.empty:
                all_results.append(result)
            
            # 进度
            progress = (i + 1) / len(symbols) * 100
            print(f"进度: {progress:.1f}%")
        
        if not all_results:
            print("\n无数据！")
            return pd.DataFrame()
        
        # 合并所有结果
        daily_df = pd.concat(all_results, ignore_index=True)
        print(f"\n日度因子计算完成: {len(daily_df)} 条记录")
        
        # 月度处理
        monthly_df = self.calculate_monthly(daily_df)
        print(f"月度因子计算完成: {len(monthly_df)} 条记录")
        
        # 保存结果
        if output_path:
            daily_df.to_csv(output_path.replace('.csv', '_daily.csv'), index=False)
            monthly_df.to_csv(output_path, index=False)
            print(f"\n结果已保存:")
            print(f"  日度: {output_path.replace('.csv', '_daily.csv')}")
            print(f"  月度: {output_path}")
        
        return monthly_df


def get_stock_list() -> list:
    """获取股票列表"""
    source = RiceQuantSource()
    stocks = source.get_stock_list()
    
    if stocks is None or stocks.empty:
        # 使用默认测试股票列表
        return ['000001.XSHE', '000002.XSHE', '600000.SH', '600016.SH', '000858.XSHE']
    
    # 过滤A股
    stocks = stocks[stocks['board'].isin(['MAIN_BOARD', 'SME', 'ChiNext'])]
    return stocks['symbol'].tolist()[:100]  # 限制数量


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='模糊金额比因子构建')
    parser.add_argument('--start', type=str, default='20240101', help='开始日期')
    parser.add_argument('--end', type=str, default='20241231', help='结束日期')
    parser.add_argument('--n', type=int, default=20, help='计算窗口天数')
    parser.add_argument('--symbols', type=str, default=None, help='股票列表(逗号分隔)')
    parser.add_argument('--output', type=str, default='data/ambiguous_amount_ratio.csv', help='输出路径')
    
    args = parser.parse_args()
    
    # 获取股票列表
    if args.symbols:
        symbols = args.symbols.split(',')
    else:
        symbols = get_stock_list()
    
    # 限制测试股票数量
    symbols = symbols[:20]  # 先测试20只
    
    # 创建因子实例
    factor = AmbiguousAmountRatioFactor(n=args.n)
    
    # 运行
    result = factor.run(
        symbols=symbols,
        start_date=args.start,
        end_date=args.end,
        output_path=args.output
    )
    
    print("\n" + "=" * 70)
    print("计算完成!")
    print("=" * 70)
    
    if not result.empty:
        print("\n因子统计:")
        print(result.describe())


if __name__ == "__main__":
    main()
