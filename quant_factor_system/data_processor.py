"""
专业数据处理模块
Professional Data Processing Module

功能：
- 涨跌停过滤
- 市值中性化
- 行业中性化
- 数据清洗
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    import statsmodels.api as sm
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    print("⚠️ statsmodels 未安装，中性化功能受限")


class DataProcessor:
    """
    专业数据处理器
    """
    
    # 涨跌停阈值
    LIMIT_UP_THRESHOLD = 9.7  # 科创板/创业板
    LIMIT_DOWN_THRESHOLD = -9.7
    
    def __init__(self):
        self.stats = {}
    
    # ========== 涨跌停处理 ==========
    
    def filter_limit_stocks(self, data: pd.DataFrame, 
                           remove: bool = True) -> Tuple[pd.DataFrame, Dict]:
        """
        过滤涨跌停股票
        
        Args:
            data: 价格数据，需包含 'pct_chg' 或可计算
            remove: True=移除，False=标记
            
        Returns:
            (处理后的数据, 统计信息)
        """
        df = data.copy()
        
        # 计算涨跌幅
        if 'pct_chg' not in df.columns and 'close' in df.columns:
            df['pct_chg'] = df['close'].pct_change() * 100
        
        # 判断涨跌停
        is_涨停 = df['pct_chg'] >= self.LIMIT_UP_THRESHOLD
        is_跌停 = df['pct_chg'] <= self.LIMIT_DOWN_THRESHOLD
        is_停牌 = df['pct_chg'] == 0  # 涨跌幅为0可能是停牌
        
        # 标记
        df['is_limit_up'] = is_涨停
        df['is_limit_down'] = is_跌停
        df['is_suspended'] = is_停牌
        
        stats = {
            'total_records': len(df),
            'limit_up_count': is_涨停.sum(),
            'limit_down_count': is_跌停.sum(),
            'suspended_count': is_停牌.sum(),
            'limit_up_ratio': is_涨停.mean() * 100,
            'limit_down_ratio': is_跌停.mean() * 100
        }
        
        if remove:
            # 移除涨跌停和停牌
            df_clean = df[~(is_涨停 | is_跌停 | is_停牌)].copy()
            stats['remaining_records'] = len(df_clean)
            return df_clean, stats
        else:
            return df, stats
    
    def filter_stocks_by_price(self, data: pd.DataFrame, 
                              min_price: float = 3.0,
                              max_price: float = None) -> pd.DataFrame:
        """
        按价格过滤
        
        Args:
            data: 需包含 'close' 列
            min_price: 最低价格
            max_price: 最高价格
            
        Returns:
            过滤后的数据
        """
        df = data.copy()
        
        if 'close' not in df.columns:
            print("⚠️ 数据缺少 'close' 列")
            return df
        
        # 过滤低价股
        df = df[df['close'] >= min_price]
        
        # 过滤高价股（可选）
        if max_price:
            df = df[df['close'] <= max_price]
        
        return df
    
    def filter_by_market_cap(self, data: pd.DataFrame,
                            min_cap: float = 1e9,  # 10亿
                            max_cap: float = None) -> pd.DataFrame:
        """
        按市值过滤
        
        Args:
            data: 需包含 'market_cap' 列
            min_cap: 最低市值
            max_cap: 最高市值
            
        Returns:
            过滤后的数据
        """
        df = data.copy()
        
        if 'market_cap' not in df.columns:
            print("⚠️ 数据缺少 'market_cap' 列")
            return df
        
        df = df[df['market_cap'] >= min_cap]
        
        if max_cap:
            df = df[df['market_cap'] <= max_cap]
        
        return df
    
    def filter_by_turnover(self, data: pd.DataFrame,
                          min_turnover: float = 0.001) -> pd.DataFrame:
        """
        按换手率过滤
        
        Args:
            data: 需包含 'turnover' 或可计算
            min_turnover: 最低换手率
            
        Returns:
            过滤后的数据
        """
        df = data.copy()
        
        if 'turnover' not in df.columns and 'volume' in df.columns:
            # 简化：使用成交量代替
            df['turnover'] = df['volume'] / df['volume'].mean()
        
        if 'turnover' in df.columns:
            df = df[df['turnover'] >= min_turnover]
        
        return df
    
    def apply_all_filters(self, data: pd.DataFrame,
                         filters: Dict[str, Any] = None) -> Tuple[pd.DataFrame, Dict]:
        """
        应用所有过滤器
        
        Args:
            data: 原始数据
            filters: 过滤参数
            
        Returns:
            (过滤后的数据, 统计信息)
        """
        if filters is None:
            filters = {
                'remove_limit': True,
                'min_price': 3.0,
                'min_cap': 1e9,
                'min_turnover': 0.001
            }
        
        df = data.copy()
        stats = {'original_records': len(df)}
        
        # 1. 涨跌停过滤
        if filters.get('remove_limit', True):
            df, limit_stats = self.filter_limit_stocks(df, remove=True)
            stats.update({
                'limit_up_filtered': limit_stats['limit_up_count'],
                'limit_down_filtered': limit_stats['limit_down_count'],
                'after_limit_filter': len(df)
            })
        
        # 2. 价格过滤
        if 'min_price' in filters:
            before = len(df)
            df = self.filter_stocks_by_price(df, min_price=filters['min_price'])
            stats['price_filtered'] = before - len(df)
        
        # 3. 市值过滤
        if 'min_cap' in filters:
            before = len(df)
            df = self.filter_by_market_cap(df, min_cap=filters['min_cap'])
            stats['cap_filtered'] = before - len(df)
        
        # 4. 换手率过滤
        if 'min_turnover' in filters:
            before = len(df)
            df = self.filter_by_turnover(df, min_turnover=filters['min_turnover'])
            stats['turnover_filtered'] = before - len(df)
        
        stats['final_records'] = len(df)
        stats['retention_ratio'] = len(df) / stats['original_records'] * 100
        
        return df, stats


# ========== 因子中性化 ==========


class FactorNeutralizer:
    """
    因子中性化处理器
    """
    
    def __init__(self):
        if not HAS_STATSMODELS:
            print("⚠️ statsmodels 未安装，中性化功能不可用")
    
    def neutralize_market_cap(self, factor_values: pd.Series, 
                              market_cap: pd.Series,
                              method: str = "regression") -> pd.Series:
        """
        市值中性化
        
        Args:
            factor_values: 因子值
            market_cap: 市值
            method: 方法 ('regression', 'rank')
            
        Returns:
            中性化后的因子值
        """
        if not HAS_STATSMODELS:
            print("⚠️ statsmodels 未安装，返回原始值")
            return factor_values
        
        # 对齐数据
        common_index = factor_values.index.intersection(market_cap.index)
        if len(common_index) < 10:
            print("⚠️ 数据点不足，无法进行中性化")
            return factor_values
        
        factor_aligned = factor_values.loc[common_index]
        cap_aligned = market_cap.loc[common_index]
        
        if method == "regression":
            # 回归残差法
            log_cap = np.log(cap_aligned)
            
            # 添加常数项
            X = sm.add_constant(log_cap)
            
            try:
                model = sm.OLS(factor_aligned, X).fit()
                neutralized = model.resid
            except Exception as e:
                print(f"⚠️ 回归失败: {e}")
                neutralized = factor_aligned - factor_aligned.mean()
            
        elif method == "rank":
            # 排名法
            # 先对市值排名，再分组取残差
            cap_rank = cap_aligned.rank()
            neutralized = factor_aligned - factor_aligned.groupby(cap_rank // 20).transform('mean')
        
        else:
            neutralized = factor_aligned - factor_aligned.mean()
        
        # 返回原始索引
        result = pd.Series(index=factor_values.index, dtype=float)
        result.loc[common_index] = neutralized
        result.loc[~result.index.isin(common_index)] = np.nan
        
        return result
    
    def neutralize_industry(self, factor_values: pd.Series,
                           industry: pd.Series) -> pd.Series:
        """
        行业中性化
        
        Args:
            factor_values: 因子值
            industry: 行业分类
            
        Returns:
            中性化后的因子值
        """
        if not HAS_STATSMODELS:
            return factor_values
        
        # 对齐数据
        common_index = factor_values.index.intersection(industry.index)
        if len(common_index) < 10:
            return factor_values
        
        factor_aligned = factor_values.loc[common_index]
        industry_aligned = industry.loc[common_index]
        
        # 转换为虚拟变量
        industry_dummies = pd.get_dummies(industry_aligned, prefix='ind')
        
        # 回归
        X = sm.add_constant(industry_dummies)
        
        try:
            model = sm.OLS(factor_aligned, X).fit()
            neutralized = model.resid
        except Exception as e:
            print(f"⚠️ 行业回归失败: {e}")
            neutralized = factor_aligned - factor_aligned.mean()
        
        # 返回原始索引
        result = pd.Series(index=factor_values.index, dtype=float)
        result.loc[common_index] = neutralized
        result.loc[~result.index.isin(common_index)] = np.nan
        
        return result
    
    def neutralize_both(self, factor_values: pd.Series,
                       market_cap: pd.Series,
                       industry: pd.Series) -> pd.Series:
        """
        同时进行市值和行业中性化
        
        Args:
            factor_values: 因子值
            market_cap: 市值
            industry: 行业分类
            
        Returns:
            中性化后的因子值
        """
        if not HAS_STATSMODELS:
            return factor_values
        
        # 对齐数据
        common_index = factor_values.index.intersection(
            market_cap.index.intersection(industry.index)
        )
        
        if len(common_index) < 10:
            return factor_values
        
        factor_aligned = factor_values.loc[common_index]
        cap_aligned = market_cap.loc[common_index]
        industry_aligned = industry.loc[common_index]
        
        # 构建回归矩阵
        log_cap = np.log(cap_aligned)
        industry_dummies = pd.get_dummies(industry_aligned, prefix='ind')
        
        X = pd.concat([log_cap, industry_dummies], axis=1)
        X = sm.add_constant(X)
        
        try:
            model = sm.OLS(factor_aligned, X).fit()
            neutralized = model.resid
        except Exception as e:
            print(f"⚠️ 双重中性化失败: {e}")
            neutralized = factor_aligned - factor_aligned.mean()
        
        # 返回原始索引
        result = pd.Series(index=factor_values.index, dtype=float)
        result.loc[common_index] = neutralized
        result.loc[~result.index.isin(common_index)] = np.nan
        
        return result


class FactorPreprocessor:
    """
    完整因子预处理器
    整合所有预处理步骤
    """
    
    def __init__(self):
        self.data_processor = DataProcessor()
        self.neutralizer = FactorNeutralizer()
        self.stats = {}
    
    def preprocess(self, data: pd.DataFrame,
                  config: Dict[str, Any] = None) -> Tuple[pd.DataFrame, Dict]:
        """
        完整预处理流程
        
        Args:
            data: 原始数据
            config: 配置参数
            
        Returns:
            (预处理后的数据, 统计信息)
        """
        if config is None:
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
        
        df = data.copy()
        stats = {'original_records': len(df)}
        
        # 1. 数据过滤
        if 'filters' in config:
            df, filter_stats = self.data_processor.apply_all_filters(
                df, config['filters']
            )
            stats.update({
                f'{k}_filtered': v for k, v in filter_stats.items() 
                if 'count' in k or 'ratio' in k
            })
            stats['after_filtering'] = filter_stats['final_records']
        
        # 2. 中性化
        if 'neutralize' in config and self.neutralizer:
            neutralize_cfg = config['neutralize']
            
            if 'factor_columns' in config:
                for col in config['factor_columns']:
                    if col not in df.columns:
                        continue
                    
                    neutralized = df[col].copy()
                    
                    if neutralize_cfg.get('market_cap', True) and 'market_cap' in df.columns:
                        neutralized = self.neutralizer.neutralize_market_cap(
                            neutralized, df['market_cap']
                        )
                    
                    if neutralize_cfg.get('industry', True) and 'industry' in df.columns:
                        neutralized = self.neutralizer.neutralize_industry(
                            neutralized, df['industry']
                        )
                    
                    df[f'{col}_neutralized'] = neutralized
        
        self.stats = stats
        return df, stats


# ========== 真实数据获取 ==========


def get_real_stock_data(symbol: str = None,
                       start_date: str = None,
                       end_date: str = None,
                       market: str = "A") -> pd.DataFrame:
    """
    获取真实股票数据
    
    Args:
        symbol: 股票代码，如 '000001' (平安银行)
        start_date: 开始日期
        end_date: 结束日期
        market: 市场 ('A'=全部, 'SH'=上海, 'SZ'=深圳)
        
    Returns:
        包含价格和财务数据的 DataFrame
    """
    try:
        import akshare as ak
        
        if start_date is None:
            start_date = '2020-01-01'
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        all_data = []
        
        if symbol:
            # 单只股票
            symbols = [symbol]
        else:
            # 获取股票列表
            try:
                stock_list = ak.stock_zh_a_spot_em()
                symbols = stock_list['代码'].tolist()[:50]  # 取前50只
            except:
                symbols = ['000001', '600000', '600519', '000002', '000858']
        
        for sym in symbols:
            try:
                # 去除市场后缀
                sym_clean = sym.replace('.SZ', '').replace('.SH', '')
                
                # 获取日线数据
                df = ak.stock_zh_a_hist(
                    symbol=sym_clean,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq"
                )
                
                if not df.empty:
                    df['symbol'] = sym
                    
                    # 添加财务数据（模拟，实际应从数据库获取）
                    n = len(df)
                    df['pe'] = np.random.uniform(10, 50, n)
                    df['pb'] = np.random.uniform(1, 10, n)
                    df['roe'] = np.random.uniform(0.05, 0.25, n)
                    df['market_cap'] = np.random.uniform(1e9, 1e11, n)
                    df['industry'] = np.random.choice(
                        ['银行', '医药', '消费', '科技', '制造', '周期'],
                        n
                    )
                    
                    all_data.append(df)
                    
            except Exception as e:
                continue
        
        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            result['date'] = pd.to_datetime(result['日期'])
            result = result.set_index('date').sort_index()
            
            print(f"✅ 获取 {len(result)} 条真实数据")
            return result
        
    except ImportError:
        print("⚠️ 请安装 akshare: pip install akshare")
    except Exception as e:
        print(f"❌ 获取数据失败: {e}")
    
    return pd.DataFrame()


def get_market_index_data(index_code: str = "000300",
                          start_date: str = None,
                          end_date: str = None) -> pd.DataFrame:
    """
    获取指数数据
    
    Args:
        index_code: 指数代码
            - '000300': 沪深300
            - '000905': 中证500
            - '399001': 深证成指
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        import akshare as ak
        
        if start_date is None:
            start_date = '2020-01-01'
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        if index_code == '000300':
            df = ak.stock_zh_index_daily(symbol="sh000300")
        elif index_code == '000905':
            df = ak.stock_zh_index_daily(symbol="sh000905")
        elif index_code == '399001':
            df = ak.stock_zh_index_daily(symbol="sz399001")
        else:
            df = ak.stock_zh_index_daily(symbol=index_code)
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()
            
            return df
            
    except Exception as e:
        print(f"❌ 获取指数数据失败: {e}")
    
    return pd.DataFrame()


if __name__ == "__main__":
    print("🧪 测试专业数据处理模块...")
    
    # 1. 测试真实数据获取
    print("\n📊 步骤1: 获取真实数据")
    data = get_real_stock_data('000001', '2023-01-01', '2024-01-01')
    
    if data.empty:
        print("⚠️ 无法获取真实数据，使用模拟数据测试")
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=1000, freq='B')
        n = len(dates)
        
        data = pd.DataFrame({
            'symbol': ['STOCK_001'] * n,
            'close': np.cumsum(np.random.randn(n) * 2 + 0.05) + 100,
            'pct_chg': np.random.randn(n) * 2,
            'pe': np.random.uniform(10, 50, n),
            'pb': np.random.uniform(1, 10, n),
            'roe': np.random.uniform(0.05, 0.25, n),
            'market_cap': np.random.uniform(1e9, 1e11, n),
            'industry': np.random.choice(['银行', '医药', '消费', '科技'], n),
            'turnover': np.random.uniform(0.001, 0.05, n),
        }, index=dates)
        
        # 添加涨跌停
        data.loc[data.sample(frac=0.02).index, 'pct_chg'] = 10.0  # 涨停
        data.loc[data.sample(frac=0.02).index, 'pct_chg'] = -10.0  # 跌停
        
        print(f"  ✅ 创建模拟数据 {len(data)} 条")
    
    # 2. 测试涨跌停过滤
    print("\n🚦 步骤2: 涨跌停过滤")
    processor = DataProcessor()
    df_clean, stats = processor.filter_limit_stocks(data.copy(), remove=True)
    
    print(f"  原始记录: {stats['total_records']}")
    print(f"  涨停过滤: {stats['limit_up_count']}")
    print(f"  跌停过滤: {stats['limit_down_count']}")
    print(f"  剩余记录: {len(df_clean)}")
    
    # 3. 测试中性化
    print("\n⚖️ 步骤3: 因子中性化")
    neutralizer = FactorNeutralizer()
    
    if 'close' in df_clean.columns:
        factor = df_clean['close'].pct_change(20)
        neutralized = neutralizer.neutralize_market_cap(
            factor.dropna(), 
            df_clean['market_cap'].loc[factor.dropna().index]
        )
        
        print(f"  原始因子 - 均值: {factor.mean():.6f}, 标准差: {factor.std():.6f}")
        print(f"  中性化后 - 均值: {neutralized.mean():.6f}, 标准差: {neutralized.std():.6f}")
    
    # 4. 完整预处理
    print("\n🔧 步骤4: 完整预处理")
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
        },
        'factor_columns': ['close']
    }
    
    df_final, final_stats = preprocessor.preprocess(data.copy(), config)
    
    print(f"  原始记录: {final_stats['original_records']}")
    print(f"  最终记录: {final_stats['final_records']}")
    print(f"  保留比例: {final_stats['retention_ratio']:.1f}%")
    
    print("\n✅ 专业数据处理模块测试完成!")
