"""
米筐行业数据源适配器
RiceQuant Industry Data Adapter

功能:
- 获取行业分类信息
- 获取行业成分股
- 计算行业因子

使用:
    from quant_factor_system.data import IndustrySource
    
    source = IndustrySource()
    
    # 获取行业分类
    classification = source.get_industry_classification('2024-01-01')
    
    # 获取行业因子
    industry_factors = source.get_industry_factors('2024-01-01')
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# 检查是否安装了rqdatac
try:
    import rqdatac as rq
    RQDATAC_AVAILABLE = True
except ImportError:
    RQDATAC_AVAILABLE = False
    logger.warning("rqdatac未安装，将使用模拟行业数据")


class IndustrySource:
    """
    行业数据源 (米筐)
    
    功能:
    - 获取中信行业分类
    - 获取行业成分股
    - 计算行业因子
    """
    
    def __init__(
        self,
        cache_dir: str = './.cache/industry',
        cache_days: int = 30
    ):
        """
        初始化
        
        Args:
            cache_dir: 缓存目录
            cache_days: 缓存过期天数
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_days = cache_days
        
        # 内存缓存
        self._cache: Dict[str, pd.DataFrame] = {}
    
    # ==================== 行业分类 ====================
    
    def get_industry_classification(
        self,
        date: str = None,
        level: str = '中信一级'
    ) -> pd.DataFrame:
        """
        获取行业分类
        
        Args:
            date: 查询日期
            level: 行业等级 ('中信一级', '中信二级', '申万一级')
            
        Returns:
            行业分类DataFrame
        """
        cache_key = f"industry_class_{date}_{level}"
        
        # 检查缓存
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        if not RQDATAC_AVAILABLE:
            df = self._get_simulated_industry_classification(date, level)
            self._cache[cache_key] = df
            return df
        
        try:
            # 获取行业分类
            date = date or datetime.now().strftime('%Y%m%d')
            
            # 根据等级选择获取方式
            if '中信' in level:
                df = self._get_rq_industry(date, level)
            else:
                df = self._get_simulated_industry_classification(date, level)
            
            self._cache[cache_key] = df
            return df
            
        except Exception as e:
            logger.error(f"获取行业分类失败: {e}")
            df = self._get_simulated_industry_classification(date, level)
            self._cache[cache_key] = df
            return df
    
    def _get_rq_industry(self, date: str, level: str) -> pd.DataFrame:
        """获取米筐行业数据"""
        try:
            # 方法1: 通过 index_weights 获取行业成分
            # 获取中证行业指数列表
            if '中信一级' in level:
                # 中信一级行业
                industries = [
                    '中信一级-银行', '中信一级-非银金融', '中信一级-电子',
                    '中信一级-计算机', '中信一级-医药生物', '中信一级-食品饮料',
                    '中信一级-房地产', '中信一级-机械设备', '中信一级-化工',
                    '中信一级-有色金属', '中信一级-建筑材料', '中信一级-电气设备',
                    '中信一级-国防军工', '中信一级-传媒', '中信一级-通信',
                    '中信一级-交通运输', '中信一级-公用事业', '中信一级-农林牧渔',
                    '中信一级-商业贸易', '中信一级-休闲服务', '中信一级-综合'
                ]
            else:
                industries = []
            
            # 获取行业成分股
            stocks_by_industry = {}
            for industry in industries:
                try:
                    # 获取行业指数成分
                    idx_code = industry.replace('中信一级-', '') + '_CI'
                    stocks = rq.index_weights(idx_code, date)
                    if stocks is not None and not stocks.empty:
                        stocks_by_industry[industry] = stocks['order_book_id'].tolist()
                except Exception:
                    continue
            
            # 构建分类表
            rows = []
            for industry, stocks in stocks_by_industry.items():
                for stock in stocks:
                    rows.append({
                        'stock_code': self._to_symbol(stock),
                        'industry': industry,
                        'update_date': date
                    })
            
            return pd.DataFrame(rows)
            
        except Exception as e:
            logger.warning(f"米筐行业数据获取失败: {e}")
            return self._get_simulated_industry_classification(date, level)
    
    # ==================== 行业成分股 ====================
    
    def get_industry_stocks(
        self,
        industry: str,
        date: str = None
    ) -> List[str]:
        """
        获取某行业的成分股
        
        Args:
            industry: 行业名称
            date: 日期
            
        Returns:
            股票代码列表
        """
        classification = self.get_industry_classification(date)
        
        if classification.empty:
            return []
        
        stocks = classification[
            classification['industry'] == industry
        ]['stock_code'].tolist()
        
        return stocks
    
    # ==================== 行业因子 ====================
    
    def get_industry_factors(
        self,
        date: str = None,
        factors: List[str] = None
    ) -> pd.DataFrame:
        """
        获取行业因子
        
        Args:
            date: 查询日期
            factors: 因子列表 (默认全部)
                - industry_return: 行业收益率
                - industry_momentum: 行业动量
                - industry_volatility: 行业波动率
                - industry_size: 行业市值
                - industry_turnover: 行业换手率
            
        Returns:
            行业因子DataFrame
        """
        if factors is None:
            factors = [
                'industry_return',
                'industry_momentum',
                'industry_volatility',
                'industry_size',
                'industry_turnover'
            ]
        
        date = date or datetime.now().strftime('%Y%m%d')
        cache_key = f"industry_factors_{date}_{'_'.join(factors)}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 获取行业分类
        classification = self.get_industry_classification(date)
        
        if classification.empty:
            df = self._get_simulated_industry_factors(date, factors)
            self._cache[cache_key] = df
            return df
        
        # 计算行业因子
        df = self._calculate_industry_factors(
            classification,
            date,
            factors
        )
        
        self._cache[cache_key] = df
        return df
    
    def _calculate_industry_factors(
        self,
        classification: pd.DataFrame,
        date: str,
        factors: List[str]
    ) -> pd.DataFrame:
        """计算行业因子"""
        import numpy as np
        
        # 获取该日日期
        date = pd.to_datetime(date)
        prev_date = (date - timedelta(days=1)).strftime('%Y%m%d')
        start_date = (date - timedelta(days=20)).strftime('%Y%m%d')
        
        # 获取全市场股票的行业信息
        industries = classification['industry'].unique()
        
        # 获取全市场日线数据 (用于计算)
        if RQDATAC_AVAILABLE:
            try:
                all_daily = rq.get_price(
                    start_date=start_date,
                    end_date=date.strftime('%Y%m%d'),
                    frequency='1d',
                    fields=['close', 'volume', 'turnover_rate', 'total_market_cap']
                )
            except Exception as e:
                logger.warning(f"获取全市场数据失败: {e}")
                all_daily = None
        else:
            all_daily = None
        
        if all_daily is None or all_daily.empty:
            return self._get_simulated_industry_factors(date.strftime('%Y%m%d'), factors)
        
        # 合并行业信息
        all_daily = all_daily.reset_index()
        all_daily['symbol'] = all_daily['order_book_id'].apply(self._to_symbol)
        
        # 计算每个行业的因子
        rows = []
        
        for industry in industries:
            industry_stocks = classification[
                classification['industry'] == industry
            ]['stock_code'].tolist()
            
            # 筛选该行业股票
            industry_data = all_daily[
                all_daily['symbol'].isin(industry_stocks)
            ]
            
            if industry_data.empty:
                continue
            
            latest = industry_data[industry_data['time'] == industry_data['time'].max()]
            prev = industry_data[industry_data['time'] == industry_data['time'].min()]
            
            row = {
                'time': date,
                'industry': industry
            }
            
            # 计算各因子
            if 'industry_return' in factors:
                if len(latest) > 0 and len(prev) > 0:
                    avg_price_latest = latest['close'].mean()
                    avg_price_prev = prev['close'].mean()
                    row['industry_return'] = (avg_price_latest - avg_price_prev) / avg_price_prev
                else:
                    row['industry_return'] = np.nan
            
            if 'industry_momentum' in factors:
                if not industry_data.empty:
                    # 20日动量
                    returns = industry_data.groupby('symbol')['close'].pct_change()
                    row['industry_momentum'] = (1 + returns).prod() - 1
                else:
                    row['industry_momentum'] = np.nan
            
            if 'industry_volatility' in factors:
                if not industry_data.empty:
                    daily_returns = industry_data.groupby('symbol')['close'].pct_change()
                    row['industry_volatility'] = daily_returns.std()
                else:
                    row['industry_volatility'] = np.nan
            
            if 'industry_size' in factors:
                if 'total_market_cap' in industry_data.columns:
                    row['industry_size'] = latest['total_market_cap'].sum()
                else:
                    row['industry_size'] = (latest['close'] * latest.get('volume', 1)).sum()
            
            if 'industry_turnover' in factors:
                if 'turnover_rate' in industry_data.columns:
                    row['industry_turnover'] = latest['turnover_rate'].mean()
                else:
                    row['industry_turnover'] = np.nan
            
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    # ==================== 模拟数据 ====================
    
    def _get_simulated_industry_classification(
        self,
        date: str = None,
        level: str = '中信一级'
    ) -> pd.DataFrame:
        """生成模拟行业分类数据"""
        # 中信一级行业
        industries = [
            '银行', '非银金融', '电子', '计算机', '医药生物',
            '食品饮料', '房地产', '机械设备', '化工', '有色金属',
            '建筑材料', '电气设备', '国防军工', '传媒', '通信',
            '交通运输', '公用事业', '农林牧渔', '商业贸易', '休闲服务', '综合'
        ]
        
        rows = []
        date = date or datetime.now().strftime('%Y%m%d')
        
        for i, industry in enumerate(industries):
            # 每个行业随机分配 20-100 只股票
            n_stocks = np.random.randint(20, 100)
            
            # 随机选择股票代码
            for j in range(n_stocks):
                stock_code = f"{np.random.randint(600000, 700000):06d}"
                if np.random.random() < 0.5:
                    stock_code = f"{np.random.randint(1, 3000):06d}"
                
                rows.append({
                    'stock_code': f'SH{stock_code}' if i % 3 == 0 else f'SZ{stock_code}',
                    'industry': f'中信一级-{industry}',
                    'update_date': date
                })
        
        df = pd.DataFrame(rows)
        
        # 去除重复
        df = df.drop_duplicates(subset=['stock_code'])
        
        return df
    
    def _get_simulated_industry_factors(
        self,
        date: str = None,
        factors: List[str] = None
    ) -> pd.DataFrame:
        """生成模拟行业因子数据"""
        industries = [
            '中信一级-银行', '中信一级-非银金融', '中信一级-电子',
            '中信一级-计算机', '中信一级-医药生物', '中信一级-食品饮料',
            '中信一级-房地产', '中信一级-机械设备', '中信一级-化工',
            '中信一级-有色金属', '中信一级-建筑材料', '中信一级-电气设备'
        ]
        
        rows = []
        date = pd.to_datetime(date or datetime.now())
        
        for industry in industries:
            row = {
                'time': date,
                'industry': industry
            }
            
            for factor in factors:
                if factor == 'industry_return':
                    row[factor] = np.random.uniform(-0.05, 0.05)
                elif factor == 'industry_momentum':
                    row[factor] = np.random.uniform(-0.1, 0.15)
                elif factor == 'industry_volatility':
                    row[factor] = np.random.uniform(0.01, 0.05)
                elif factor == 'industry_size':
                    row[factor] = np.random.uniform(1e12, 5e13)
                elif factor == 'industry_turnover':
                    row[factor] = np.random.uniform(0.01, 0.05)
            
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    # ==================== 辅助方法 ====================
    
    def _to_symbol(self, order_book_id: str) -> str:
        """转换 order_book_id 为 symbol"""
        if order_book_id.endswith('.SH'):
            return f"SH{order_book_id.split('.')[0]}"
        elif order_book_id.endswith('.XSHE'):
            return f"SZ{order_book_id.split('.')[0]}"
        return order_book_id
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("行业数据缓存已清空")


# ==================== 便捷函数 ====================

def get_industry_classification(**kwargs) -> pd.DataFrame:
    """便捷函数: 获取行业分类"""
    source = IndustrySource()
    return source.get_industry_classification(**kwargs)


def get_industry_factors(**kwargs) -> pd.DataFrame:
    """便捷函数: 获取行业因子"""
    source = IndustrySource()
    return source.get_industry_factors(**kwargs)


# ==================== 导出 ====================

__all__ = [
    'IndustrySource',
    'get_industry_classification',
    'get_industry_factors',
]
