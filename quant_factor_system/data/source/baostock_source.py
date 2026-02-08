"""
备用 A 股数据源 - BaoStock
BaoStock 是一家提供免费 A 股数据的公司
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 检查是否安装
try:
    import baostock as bs
    HAS_BAOSTOCK = True
except ImportError:
    HAS_BAOSTOCK = False


class BaoStockDataSource:
    """
    BaoStock 数据源
    官方网站: https://www.baostock.com
    """
    
    def __init__(self):
        if HAS_BAOSTOCK:
            # 登录
            lg = bs.login()
            print(f"BaoStock 登录: {lg.msg}")
        else:
            print("⚠️ BaoStock 未安装，请运行: pip install baostock")
    
    def logout(self):
        """登出"""
        if HAS_BAOSTOCK:
            bs.logout()
    
    def get_stock_list(self) -> pd.DataFrame:
        """获取股票列表"""
        if not HAS_BAOSTOCK:
            return pd.DataFrame()
        
        try:
            rs = bs.query_all_sh_code()
            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())
            
            df = pd.DataFrame(data_list, columns=rs.fields)
            return df
            
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_price(self, 
                  symbols: List[str],
                  start_date: str,
                  end_date: str,
                  adjust: str = "qfq") -> pd.DataFrame:
        """
        获取日线数据
        
        Args:
            symbols: 股票代码，如 'sh.600000', 'sz.000001'
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            adjust: 复权类型 ('qfq'=前复权, 'hfq'=后复权, 'None'=不复权)
        """
        if not HAS_BAOSTOCK:
            print("⚠️ BaoStock 未安装")
            return pd.DataFrame()
        
        all_data = []
        
        for symbol in symbols:
            try:
                # 转换代码格式
                if '.' not in symbol:
                    # 默认为上海
                    symbol = f"sh.{symbol}"
                
                # 获取数据
                rs = bs.query_history_k_data_plus(
                    symbol,
                    "date,code,open,high,low,close,volume,amount,pe,pb",
                    start_date=start_date,
                    end_date=end_date,
                    adjustflag=adjust
                )
                
                data_list = []
                while rs.error_code == '0' and rs.next():
                    data_list.append(rs.get_row_data())
                
                if data_list:
                    df = pd.DataFrame(data_list, columns=rs.fields)
                    df['symbol'] = symbol
                    all_data.append(df)
                    
            except Exception as e:
                print(f"获取 {symbol} 数据失败: {e}")
                continue
        
        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            result['date'] = pd.to_datetime(result['date'])
            result = result.set_index('date').sort_index()
            
            # 转换数值类型
            for col in ['open', 'high', 'low', 'close', 'volume', 'amount', 'pe', 'pb']:
                if col in result.columns:
                    result[col] = pd.to_numeric(result[col], errors='coerce')
            
            return result
        
        return pd.DataFrame()


def get_a_stock_data_baostock(symbol: str,
                               start_date: str = '2020-01-01',
                               end_date: str = None,
                               adjust: str = 'qfq') -> pd.DataFrame:
    """
    获取单只 A 股数据
    
    Args:
        symbol: 股票代码，如 '000001' (平安银行)
        start_date: 开始日期
        end_date: 结束日期
        adjust: 复权类型
        
    Returns:
        价格数据 DataFrame
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    # 转换代码格式
    if symbol.startswith('6'):
        symbol = f"sh.{symbol}"
    else:
        symbol = f"sz.{symbol}"
    
    data_source = BaoStockDataSource()
    data = data_source.get_price([symbol], start_date, end_date, adjust)
    data_source.logout()
    
    return data


# 测试函数
def test_baostock():
    """测试 BaoStock 数据源"""
    if not HAS_BAOSTOCK:
        print("⚠️ 请安装 BaoStock: pip install baostock")
        return
    
    print("🧪 测试 BaoStock...")
    
    data_source = BaoStockDataSource()
    
    # 获取股票列表
    print("获取股票列表...")
    stocks = data_source.get_stock_list()
    if not stocks.empty:
        print(f"  股票数量: {len(stocks)}")
    else:
        print("  获取失败")
    
    # 获取上证指数
    print("获取上证指数...")
    index_data = data_source.get_price(['sh.000001'], '2024-01-01', '2024-12-31')
    if not index_data.empty:
        print(f"  数据量: {len(index_data)}")
    else:
        print("  获取失败")
    
    data_source.logout()


if __name__ == "__main__":
    test_baostock()
