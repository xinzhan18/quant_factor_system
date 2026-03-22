"""
因子处理模块
Factor Processing Module

功能:
- 市值中心化 (Market Cap Neutralization)
- 涨跌停剔除 (Limit-up/limit-down filtering)
- 行业中性化 (Industry Neutralization)
- 因子正交化 (Factor Orthogonalization)

使用:
    from quant_factor_system.factors import FactorProcessor
    
    processor = FactorProcessor()
    
    # 市值中心化
    neutralized = processor.neutralize_market_cap(factor_df)
    
    # 剔除涨跌停
    filtered = processor.filter_limit_up_down(daily_data)
    
    # 完整处理
    processed = processor.process(
        factor_df,
        daily_data,
        industry_df
    )
"""

import pandas as pd
import numpy as np
from typing import List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class FactorProcessorConfig:
    """因子处理器配置"""
    # 市值中心化
    market_cap_method: str = 'regression'  # 'regression', 'demean', 'bucket'
    market_cap_buckets: int = 5  # 市值分桶数
    
    # 涨跌停剔除
    filter_limit_up: bool = True
    filter_limit_down: bool = True
    limit_up_days: int = 1  # 连续涨停天数
    limit_down_days: int = 1  # 连续跌停天数
    
    # 行业中性化
    industry_neutral: bool = True
    
    # 因子标准化
    standardize: bool = True
    outlier_clip: bool = True
    outlier_std: float = 3.0  # 异常值阈值


class FactorProcessor:
    """
    因子处理器
    
    功能:
    - 市值中心化
    - 涨跌停剔除
    - 行业中性化
    - 异常值处理
    """
    
    def __init__(self, config: FactorProcessorConfig = None):
        """
        初始化
        
        Args:
            config: 配置
        """
        self.config = config or FactorProcessorConfig()
    
    # ==================== 市值中心化 ====================
    
    def neutralize_market_cap(
        self,
        factor_df: pd.DataFrame,
        market_cap: pd.Series = None,
        date_col: str = 'date',
        symbol_col: str = 'symbol',
        factor_col: str = 'factor_value'
    ) -> pd.DataFrame:
        """
        市值中心化
        
        方法1: 回归法 (推荐)
            factor = alpha + beta * ln(mcap) + residual
            residual 即为市值中性化后的因子
        
        方法2: 去均值法
            factor_demeaned = factor - mean(factor)
        
        方法3: 分桶去均值
            在市值桶内去均值
        
        Args:
            factor_df: 因子数据
            market_cap: 市值数据 (symbol -> market_cap)
            date_col: 日期列
            symbol_col: 股票代码列
            factor_col: 因子值列
            
        Returns:
            中心化后的因子
        """
        if factor_df.empty:
            return factor_df.copy()
        
        df = factor_df.copy()
        
        if market_cap is None:
            logger.warning("未提供市值数据，跳过市值中心化")
            return df
        
        method = self.config.market_cap_method
        
        if method == 'regression':
            return self._neutralize_regression(
                df, market_cap, date_col, symbol_col, factor_col
            )
        elif method == 'demean':
            return self._neutralize_demean(
                df, market_cap, date_col, symbol_col, factor_col
            )
        elif method == 'bucket':
            return self._neutralize_bucket(
                df, market_cap, date_col, symbol_col, factor_col
            )
        else:
            logger.warning(f"未知方法: {method}")
            return df
    
    def _neutralize_regression(
        self,
        df: pd.DataFrame,
        market_cap: pd.Series,
        date_col: str,
        symbol_col: str,
        factor_col: str
    ) -> pd.DataFrame:
        """
        回归法市值中性化
        
        回归: factor = alpha + beta * ln(mcap) + residual
        """
        try:
            from scipy import stats
            
            results = []
            
            for date, group in df.groupby(date_col):
                # 获取该日数据
                group = group.copy()
                
                # 对齐市值
                group['mcap'] = group[symbol_col].map(market_cap)
                group = group.dropna(subset=['mcap', factor_col])
                
                if len(group) < 10:
                    # 数据太少，跳过
                    group['factor_neutralized'] = group[factor_col]
                    results.append(group)
                    continue
                
                # 对市值取对数
                group['ln_mcap'] = np.log(group['mcap'].clip(lower=1))
                
                # 回归
                x = group['ln_mcap'].values
                y = group[factor_col].values
                
                # 线性回归
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                
                # 计算残差
                predicted = intercept + slope * x
                residual = y - predicted
                
                group['factor_neutralized'] = residual
                results.append(group)
            
            result = pd.concat(results, ignore_index=True)
            return result
            
        except ImportError:
            logger.warning("scipy未安装，使用简单方法")
            return self._neutralize_bucket(df, market_cap, date_col, symbol_col, factor_col)
    
    def _neutralize_demean(
        self,
        df: pd.DataFrame,
        market_cap: pd.Series,
        date_col: str,
        symbol_col: str,
        factor_col: str
    ) -> pd.DataFrame:
        """
        去均值法市值中性化
        
        根据市值加权去均值
        """
        results = []
        
        for date, group in df.groupby(date_col):
            group = group.copy()
            
            # 获取该日市值
            group['mcap'] = group[symbol_col].map(market_cap)
            group = group.dropna(subset=['mcap', factor_col])
            
            if len(group) < 2:
                group['factor_neutralized'] = group[factor_col]
                results.append(group)
                continue
            
            # 市值加权均值
            total_cap = group['mcap'].sum()
            weighted_mean = (group[factor_col] * group['mcap']).sum() / total_cap
            
            # 去均值
            group['factor_neutralized'] = group[factor_col] - weighted_mean
            results.append(group)
        
        return pd.concat(results, ignore_index=True)
    
    def _neutralize_bucket(
        self,
        df: pd.DataFrame,
        market_cap: pd.Series,
        date_col: str,
        symbol_col: str,
        factor_col: str
    ) -> pd.DataFrame:
        """
        分桶去均值法市值中性化
        
        将股票按市值分桶，在桶内去均值
        """
        results = []
        
        for date, group in df.groupby(date_col):
            group = group.copy()
            
            # 获取该日市值
            group['mcap'] = group[symbol_col].map(market_cap)
            group = group.dropna(subset=['mcap', factor_col])
            
            if len(group) < 5:
                group['factor_neutralized'] = group[factor_col]
                results.append(group)
                continue
            
            # 分桶 (使用qcut)
            try:
                group['mcap_bucket'] = pd.qcut(
                    group['mcap'], 
                    q=self.config.market_cap_buckets, 
                    labels=False,
                    duplicates='drop'
                )
            except ValueError:
                group['mcap_bucket'] = 0
            
            # 桶内去均值
            bucket_mean = group.groupby('mcap_bucket')[factor_col].transform('mean')
            group['factor_neutralized'] = group[factor_col] - bucket_mean
            
            results.append(group)
        
        return pd.concat(results, ignore_index=True)
    
    # ==================== 涨跌停剔除 ====================
    
    def filter_limit_up_down(
        self,
        daily_data: pd.DataFrame,
        lookback: int = 5,
        date_col: str = 'date',
        symbol_col: str = 'symbol',
        price_col: str = 'close',
        high_col: str = 'high',
        low_col: str = 'low'
    ) -> pd.DataFrame:
        """
        涨跌停剔除
        
        使用米筐原生字段判断:
        - 涨停: close >= limit_up
        - 跌停: close <= limit_down
        
        如果数据中没有 limit_up/limit_down 字段,
        则使用涨跌幅判断:
        - 涨停: close == high 且 pct_chg > 9.5%
        - 跌停: close == low 且 pct_chg < -9.5%
        
        Args:
            daily_data: 日线数据
            lookback: 回溯天数
            date_col: 日期列
            symbol_col: 股票代码列
            price_col: 收盘价列
            high_col: 最高价列
            low_col: 最低价列
            
        Returns:
            包含limit_status的数据框
        """
        if daily_data.empty:
            return daily_data.copy()
        
        df = daily_data.copy()
        
        # 检查是否有米筐原生涨跌停字段
        has_limit_fields = 'limit_up' in df.columns and 'limit_down' in df.columns
        
        if has_limit_fields:
            # 使用米筐原生字段判断
            df['is_limit_up'] = df[price_col] >= df['limit_up']
            df['is_limit_down'] = df[price_col] <= df['limit_down']
        else:
            # 计算涨跌幅
            if 'pct_chg' not in df.columns:
                df = df.sort_values([symbol_col, date_col])
                df['pct_chg'] = df.groupby(symbol_col)[price_col].pct_change() * 100
            
            # 使用涨跌幅判断
            df['is_limit_up'] = (
                (df[price_col] == df[high_col]) &  # 收于最高价
                (df['pct_chg'] > 9.5)             # 涨幅>9.5%
            )
            
            df['is_limit_down'] = (
                (df[price_col] == df[low_col]) &   # 收于最低价
                (df['pct_chg'] < -9.5)             # 跌幅<-9.5%
            )
        
        # 综合涨跌停状态 (当天判断)
        df['is_excluded'] = (
            (df['is_limit_up'] & self.config.filter_limit_up) |
            (df['is_limit_down'] & self.config.filter_limit_down)
        )
        
        return df
    
    def get_excluded_symbols(
        self,
        daily_data: pd.DataFrame,
        date: str = None,
        date_col: str = 'date',
        symbol_col: str = 'symbol'
    ) -> List[str]:
        """
        获取指定日期被剔除的股票列表
        
        Args:
            daily_data: 日线数据 (已处理过)
            date: 指定日期
            date_col: 日期列
            symbol_col: 股票代码列
            
        Returns:
            被剔除的股票列表
        """
        if date:
            df = daily_data[daily_data[date_col] == date]
        else:
            df = daily_data
        
        if df.empty:
            return []
        
        excluded = df[df['is_excluded'] == True][symbol_col].unique()
        return list(excluded)
    
    def filter_stocks(
        self,
        factor_df: pd.DataFrame,
        daily_data: pd.DataFrame,
        date_col: str = 'date',
        symbol_col: str = 'symbol'
    ) -> pd.DataFrame:
        """
        过滤涨跌停股票
        
        Args:
            factor_df: 因子数据
            daily_data: 日线数据
            date_col: 日期列
            symbol_col: 股票代码列
            
        Returns:
            过滤后的因子数据
        """
        # 处理日线数据
        processed_daily = self.filter_limit_up_down(daily_data)
        
        # 获取每日的剔除列表
        excluded_map = {}
        for date in factor_df[date_col].unique():
            excluded = self.get_excluded_symbols(
                processed_daily, date, date_col, symbol_col
            )
            excluded_map[date] = set(excluded)
        
        # 过滤
        def check_excluded(row):
            date = row[date_col]
            symbol = row[symbol_col]
            return symbol not in excluded_map.get(date, set())
        
        mask = factor_df.apply(check_excluded, axis=1)
        filtered = factor_df[mask].copy()
        
        logger.info(f"过滤前: {len(factor_df)}, 过滤后: {len(filtered)}")
        
        return filtered
    
    # ==================== 行业中性化 ====================
    
    def neutralize_industry(
        self,
        factor_df: pd.DataFrame,
        industry: pd.Series = None,
        date_col: str = 'date',
        symbol_col: str = 'symbol',
        factor_col: str = 'factor_value'
    ) -> pd.DataFrame:
        """
        行业中性化
        
        在行业内去均值
        
        Args:
            factor_df: 因子数据
            industry: 行业数据 (symbol -> industry)
            date_col: 日期列
            symbol_col: 股票代码列
            factor_col: 因子值列
            
        Returns:
            中性化后的因子
        """
        if factor_df.empty:
            return factor_df.copy()
        
        if industry is None:
            logger.warning("未提供行业数据，跳过行业中性化")
            return factor_df.copy()
        
        df = factor_df.copy()
        
        # 对齐行业
        df['industry'] = df[symbol_col].map(industry)
        df = df.dropna(subset=['industry', factor_col])
        
        results = []
        
        for date, group in df.groupby(date_col):
            group = group.copy()
            
            if len(group) < 5:
                group['factor_industry_neutral'] = group[factor_col].values
                results.append(group)
                continue
            
            # 行业内去均值
            industry_mean = group.groupby('industry')[factor_col].transform('mean')
            group['factor_industry_neutral'] = (group[factor_col] - industry_mean).values
            
            results.append(group)
        
        return pd.concat(results, ignore_index=True)
    
    # ==================== 因子标准化 ====================
    
    def standardize(
        self,
        factor_df: pd.DataFrame,
        date_col: str = 'date',
        factor_col: str = 'factor_value',
        method: str = 'zscore'
    ) -> pd.DataFrame:
        """
        因子标准化
        
        Args:
            factor_df: 因子数据
            date_col: 日期列
            factor_col: 因子值列
            method: 方法 ('zscore', 'rank')
            
        Returns:
            标准化后的因子
        """
        if factor_df.empty:
            return factor_df.copy()
        
        df = factor_df.copy()
        
        if method == 'zscore':
            # Z-score标准化
            results = []
            
            for date, group in df.groupby(date_col):
                group = group.copy()
                
                mean = group[factor_col].mean()
                std = group[factor_col].std()
                
                if std > 0:
                    group['factor_standardized'] = (group[factor_col] - mean) / std
                else:
                    group['factor_standardized'] = 0
                
                results.append(group)
            
            df = pd.concat(results, ignore_index=True)
            
        elif method == 'rank':
            # 排名标准化
            df['factor_standardized'] = df.groupby(date_col)[factor_col].rank(pct=True) - 0.5
        
        return df
    
    def clip_outliers(
        self,
        factor_df: pd.DataFrame,
        date_col: str = 'date',
        factor_col: str = 'factor_value'
    ) -> pd.DataFrame:
        """
        异常值处理 (截尾法)
        
        Args:
            factor_df: 因子数据
            date_col: 日期列
            factor_col: 因子值列
            
        Returns:
            处理后的因子
        """
        if not self.config.outlier_clip:
            return factor_df.copy()
        
        df = factor_df.copy()
        n_std = self.config.outlier_std
        
        results = []
        
        for date, group in df.groupby(date_col):
            group = group.copy()
            
            mean = group[factor_col].mean()
            std = group[factor_col].std()
            
            if std > 0:
                lower = mean - n_std * std
                upper = mean + n_std * std
                
                group['factor_clipped'] = group[factor_col].clip(lower, upper)
            else:
                group['factor_clipped'] = group[factor_col]
            
            results.append(group)
        
        return pd.concat(results, ignore_index=True)
    
    # ==================== 完整处理流程 ====================
    
    def process(
        self,
        factor_df: pd.DataFrame,
        daily_data: pd.DataFrame = None,
        market_cap: pd.Series = None,
        industry: pd.Series = None,
        date_col: str = 'date',
        symbol_col: str = 'symbol',
        factor_col: str = 'factor_value'
    ) -> pd.DataFrame:
        """
        完整因子处理流程
        
        步骤:
        1. 涨跌停过滤
        2. 市值中心化
        3. 行业中性化
        4. 异常值处理
        5. 标准化
        
        Args:
            factor_df: 因子数据
            daily_data: 日线数据 (用于涨跌停判断)
            market_cap: 市值数据
            industry: 行业数据
            date_col: 日期列
            symbol_col: 股票代码列
            factor_col: 因子值列
            
        Returns:
            处理后的因子
        """
        result = factor_df.copy()
        
        # 确保因子值列存在
        if factor_col not in result.columns:
            # 找到因子值列
            value_cols = [c for c in result.columns if c not in [date_col, symbol_col]]
            if value_cols:
                result[factor_col] = result[value_cols[0]]
        
        # Step 1: 涨跌停过滤
        if daily_data is not None:
            result = self.filter_stocks(
                result, daily_data, date_col, symbol_col
            )
        
        # Step 2: 市值中心化
        if market_cap is not None:
            neutralized = self._neutralize_regression_simple(
                result, market_cap, date_col, symbol_col, factor_col
            )
            result[factor_col] = neutralized[factor_col].values
        
        # Step 3: 行业中性化
        if industry is not None and self.config.industry_neutral:
            neutralized = self._neutralize_industry_simple(
                result, industry, date_col, symbol_col, factor_col
            )
            result[factor_col] = neutralized[factor_col].values
        
        # Step 4: 异常值处理
        result = self._clip_outliers_simple(result, date_col, factor_col)
        
        # Step 5: 标准化
        if self.config.standardize:
            result = self._standardize_simple(result, date_col, factor_col)
        
        return result
    
    def _neutralize_regression_simple(
        self,
        df: pd.DataFrame,
        market_cap: pd.Series,
        date_col: str,
        symbol_col: str,
        factor_col: str
    ) -> pd.DataFrame:
        """简化版市值回归中性化"""
        df = df.copy()
        df['mcap'] = df[symbol_col].map(market_cap)
        df = df.dropna(subset=['mcap', factor_col])
        
        results = []
        for date, group in df.groupby(date_col):
            group = group.copy()
            group['ln_mcap'] = np.log(group['mcap'].clip(lower=1))
            
            if len(group) < 10:
                continue
            
            x = group['ln_mcap'].values
            y = group[factor_col].values
            
            # 简单线性回归
            x_mean = np.mean(x)
            y_mean = np.mean(y)
            
            numerator = np.sum((x - x_mean) * (y - y_mean))
            denominator = np.sum((x - x_mean) ** 2)
            
            if denominator != 0:
                slope = numerator / denominator
                intercept = y_mean - slope * x_mean
                predicted = intercept + slope * x
                group[factor_col] = y - predicted
            else:
                group[factor_col] = y - y_mean
            
            results.append(group)
        
        return pd.concat(results, ignore_index=True) if results else df
    
    def _neutralize_industry_simple(
        self,
        df: pd.DataFrame,
        industry: pd.Series,
        date_col: str,
        symbol_col: str,
        factor_col: str
    ) -> pd.DataFrame:
        """简化版行业中性化"""
        df = df.copy()
        df['industry'] = df[symbol_col].map(industry)
        df = df.dropna(subset=['industry', factor_col])
        
        results = []
        for date, group in df.groupby(date_col):
            group = group.copy()
            
            if len(group) < 5:
                continue
            
            # 行业内去均值
            industry_mean = group.groupby('industry')[factor_col].transform('mean')
            group[factor_col] = (group[factor_col] - industry_mean).values
            
            results.append(group)
        
        return pd.concat(results, ignore_index=True) if results else df
    
    def _clip_outliers_simple(
        self,
        df: pd.DataFrame,
        date_col: str,
        factor_col: str
    ) -> pd.DataFrame:
        """简化版异常值处理"""
        if not self.config.outlier_clip:
            return df
        
        df = df.copy()
        n_std = self.config.outlier_std
        
        results = []
        for date, group in df.groupby(date_col):
            group = group.copy()
            
            mean = group[factor_col].mean()
            std = group[factor_col].std()
            
            if std > 0:
                lower = mean - n_std * std
                upper = mean + n_std * std
                group[factor_col] = group[factor_col].clip(lower, upper)
            
            results.append(group)
        
        return pd.concat(results, ignore_index=True) if results else df
    
    def _standardize_simple(
        self,
        df: pd.DataFrame,
        date_col: str,
        factor_col: str
    ) -> pd.DataFrame:
        """简化版标准化"""
        df = df.copy()
        
        results = []
        for date, group in df.groupby(date_col):
            group = group.copy()
            
            mean = group[factor_col].mean()
            std = group[factor_col].std()
            
            if std > 0:
                group[factor_col] = (group[factor_col] - mean) / std
            else:
                group[factor_col] = 0
            
            results.append(group)
        
        return pd.concat(results, ignore_index=True) if results else df
    
    def build_daily_factor(
        self,
        daily_data: pd.DataFrame,
        factor_name: str,
        market_cap: pd.Series = None,
        industry: pd.Series = None,
        date_col: str = 'date',
        symbol_col: str = 'symbol'
    ) -> pd.DataFrame:
        """
        构建每日因子
        
        完整的因子构建流程:
        1. 计算原始因子
        2. 涨跌停过滤
        3. 市值中心化
        4. 行业中性化
        5. 标准化
        
        Args:
            daily_data: 日线数据
            factor_name: 因子名称
            market_cap: 市值数据
            industry: 行业数据
            date_col: 日期列
            symbol_col: 股票代码列
            
        Returns:
            处理后的因子数据
        """
        # Step 1: 计算原始因子 (由子类实现)
        raw_factor = self._calculate_raw_factor(
            daily_data, factor_name, date_col, symbol_col
        )
        
        # Step 2-5: 完整处理
        processed = self.process(
            raw_factor,
            daily_data,
            market_cap,
            industry,
            date_col,
            symbol_col,
            'factor_value'
        )
        
        return processed
    
    def _calculate_raw_factor(
        self,
        daily_data: pd.DataFrame,
        factor_name: str,
        date_col: str,
        symbol_col: str
    ) -> pd.DataFrame:
        """
        计算原始因子 (子类重写)
        
        Args:
            daily_data: 日线数据
            factor_name: 因子名称
            date_col: 日期列
            symbol_col: 股票代码列
            
        Returns:
            原始因子数据
        """
        # 默认返回收盘价
        df = daily_data[[date_col, symbol_col, 'close']].copy()
        df = df.rename(columns={'close': 'factor_value'})
        return df


# ==================== 便捷函数 ====================

def neutralize_market_cap(
    factor_df: pd.DataFrame,
    market_cap: pd.Series,
    method: str = 'regression'
) -> pd.DataFrame:
    """市值中心化"""
    config = FactorProcessorConfig(market_cap_method=method)
    processor = FactorProcessor(config)
    return processor.neutralize_market_cap(factor_df, market_cap)


def filter_limit_up_down(daily_data: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """涨跌停过滤"""
    processor = FactorProcessor()
    return processor.filter_limit_up_down(daily_data, **kwargs)


def process_factor(
    factor_df: pd.DataFrame,
    daily_data: pd.DataFrame = None,
    market_cap: pd.Series = None,
    industry: pd.Series = None
) -> pd.DataFrame:
    """完整因子处理"""
    processor = FactorProcessor()
    return processor.process(factor_df, daily_data, market_cap, industry)
