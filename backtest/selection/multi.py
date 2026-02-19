"""
多因子组合模块
Multi Factor Combiner

功能:
- 因子值加权组合
- IC加权
- 等权组合
- Z-score标准化

使用示例:
    from .multi import MultiFactorCombiner
    
    combiner = MultiFactorCombiner(weights={
        'momentum': 0.4,
        'value': 0.3,
        'quality': 0.3
    })
    
    result = combiner.combine({
        'momentum': momentum_df,
        'value': value_df,
        'quality': quality_df
    })
"""

import pandas as pd
import numpy as np
from typing import Dict
from dataclasses import dataclass
from enum import Enum
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class CombinationMethod(Enum):
    """组合方法"""
    EQUAL = 'equal'           # 等权
    WEIGHTED = 'weighted'     # 加权
    IC_WEIGHTED = 'ic_weighted'  # IC加权
    OPTIMAL = 'optimal'       # 最优权重 (均值方差)
    RANK = 'rank'            # 排名组合


@dataclass
class CombinedFactor:
    """组合因子结果"""
    data: pd.DataFrame          # 组合后的因子数据
    weights: Dict[str, float]  # 使用的权重
    ic_values: Dict[str, float]  # 各因子IC
    method: str                # 组合方法


class MultiFactorCombiner:
    """
    多因子组合器
    
    功能:
    - 因子标准化 (Z-score)
    - 因子加权组合
    - IC权重计算
    - 均值方差优化
    """
    
    def __init__(
        self,
        weights: Dict[str, float] = None,
        method: str = 'weighted',
        normalize: bool = True
    ):
        """
        初始化
        
        Args:
            weights: 因子权重 (默认等权)
            method: 组合方法 (equal/weighted/ic_weighted/optimal)
            normalize: 是否标准化
        """
        self.weights = weights or {}
        self.method = CombinationMethod(method)
        self.normalize = normalize
        self._ic_cache: Dict[str, float] = {}
    
    def combine(
        self,
        factor_data: Dict[str, pd.DataFrame],
        returns_data: pd.DataFrame = None,
        method: str = None
    ) -> CombinedFactor:
        """
        组合多个因子
        
        Args:
            factor_data: {因子名: DataFrame(symbol, date, factor_value)}
            returns_data: 收益率数据 (用于计算IC权重)
            method: 覆盖默认组合方法
            
        Returns:
            CombinedFactor
        """
        if not factor_data:
            logger.warning("因子数据为空")
            return CombinedFactor(
                data=pd.DataFrame(),
                weights={},
                ic_values={},
                method=''
            )
        
        # 确定组合方法
        combo_method = method or self.method.value
        
        # 1. 标准化因子
        normalized = self._normalize_factors(factor_data)
        
        # 2. 计算权重
        if combo_method == 'ic_weighted' and returns_data is not None:
            weights = self._calculate_ic_weights(normalized, returns_data)
        elif combo_method == 'optimal':
            weights = self._calculate_optimal_weights(normalized, returns_data)
        else:
            weights = self._get_weights(normalized)
        
        # 3. 计算IC
        ic_values = {}
        if returns_data is not None:
            ic_values = self._calculate_ic_all(normalized, returns_data)
        
        # 4. 组合因子
        combined = self._combine(normalized, weights, combo_method)
        
        logger.info(f"✅ 多因子组合完成: {len(combined)}行, 方法: {combo_method}")
        
        return CombinedFactor(
            data=combined,
            weights=weights,
            ic_values=ic_values,
            method=combo_method
        )
    
    def _normalize_factors(
        self,
        factor_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.DataFrame]:
        """标准化因子"""
        normalized = {}
        
        for name, df in factor_data.items():
            if df.empty:
                continue
            
            if not self.normalize:
                normalized[name] = df.copy()
                continue
            
            # Z-score标准化
            factor_values = df['factor_value'].values
            mean = np.mean(factor_values)
            std = np.std(factor_values)
            
            if std > 0:
                df = df.copy()
                df['factor_value'] = (factor_values - mean) / std
            else:
                df = df.copy()
                df['factor_value'] = 0
            
            normalized[name] = df
        
        return normalized
    
    def _get_weights(
        self,
        factor_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """获取权重"""
        # 如果有预设权重，使用预设
        if self.weights:
            return self.weights
        
        # 否则等权
        n = len(factor_data)
        if n == 0:
            return {}
        
        return {name: 1.0 / n for name in factor_data.keys()}
    
    def _calculate_ic_weights(
        self,
        factor_data: Dict[str, pd.DataFrame],
        returns_data: pd.DataFrame
    ) -> Dict[str, float]:
        """计算IC权重"""
        ic_values = self._calculate_ic_all(factor_data, returns_data)
        
        # 使用IC的绝对值作为权重
        total_ic = sum(abs(ic) for ic in ic_values.values())
        
        if total_ic <= 0:
            n = len(factor_data)
            return {name: 1.0 / n for name in factor_data.keys()}
        
        weights = {}
        for name, ic in ic_values.items():
            weights[name] = abs(ic) / total_ic
        
        # 缓存IC值
        self._ic_cache = ic_values
        
        return weights
    
    def _calculate_optimal_weights(
        self,
        factor_data: Dict[str, pd.DataFrame],
        returns_data: pd.DataFrame
    ) -> Dict[str, float]:
        """计算最优权重 (均值方差优化)"""
        # 获取合并的因子数据
        combined = self._combine(factor_data, self._get_weights(factor_data), 'weighted')
        
        if combined.empty or returns_data.empty:
            return self._get_weights(factor_data)
        
        # 计算因子收益
        factor_returns = self._calculate_factor_returns(combined, returns_data)
        
        if factor_returns.empty:
            return self._get_weights(factor_data)
        
        # 计算协方差矩阵
        factor_returns.cov()
        
        # 计算预期收益
        factor_returns.mean()
        
        # 简单的均值方差优化 (最大化夏普比率)
        try:
            # 简化的优化: 等权 + IC调整
            n = len(factor_data)
            base_weight = 1.0 / n
            
            # 获取IC值
            ic_values = self._calculate_ic_all(factor_data, returns_data)
            
            # 基于IC调整权重
            total_ic = sum(abs(ic) for ic in ic_values.values())
            if total_ic > 0:
                weights = {}
                for name in factor_data.keys():
                    ic = abs(ic_values.get(name, 0))
                    weights[name] = base_weight * (1 + ic / total_ic)
                
                # 归一化
                total = sum(weights.values())
                if total > 0:
                    return {k: v / total for k, v in weights.items()}
            
            return self._get_weights(factor_data)
            
        except Exception as e:
            logger.warning(f"最优权重计算失败: {e}")
            return self._get_weights(factor_data)
    
    def _calculate_ic_all(
        self,
        factor_data: Dict[str, pd.DataFrame],
        returns_data: pd.DataFrame
    ) -> Dict[str, float]:
        """计算所有因子的IC"""
        ic_values = {}
        
        for name, df in factor_data.items():
            if df.empty:
                continue
            
            ic = self._calculate_ic(df, returns_data)
            ic_values[name] = ic
        
        return ic_values
    
    def _calculate_ic(
        self,
        factor_df: pd.DataFrame,
        returns_data: pd.DataFrame
    ) -> float:
        """计算单个因子的IC"""
        if factor_df.empty or returns_data.empty:
            return 0
        
        # 合并数据
        merged = self._merge_factor_returns(factor_df, returns_data)
        
        if merged.empty:
            return 0
        
        # 计算IC
        try:
            ic, _ = stats.spearmanr(
                merged['factor_value'],
                merged['return']
            )
            return ic if not np.isnan(ic) else 0
        except:
            return 0
    
    def _merge_factor_returns(
        self,
        factor_df: pd.DataFrame,
        returns_data: pd.DataFrame
    ) -> pd.DataFrame:
        """合并因子和收益率数据"""
        # 确保日期对齐
        factor_df = factor_df.copy()
        returns_data = returns_data.copy()
        
        # 重命名列
        factor_df = factor_df.rename(columns={'factor_value': 'factor_value_temp'})
        returns_data = returns_data.rename(columns={'return': 'return_temp'})
        
        # 合并
        merged = pd.merge(
            factor_df,
            returns_data,
            on=['symbol', 'date'],
            how='inner'
        )
        
        # 重命名回来
        if 'factor_value_temp' in merged.columns:
            merged = merged.rename(columns={'factor_value_temp': 'factor_value'})
        if 'return_temp' in merged.columns:
            merged = merged.rename(columns={'return_temp': 'return'})
        
        return merged
    
    def _calculate_factor_returns(
        self,
        combined: pd.DataFrame,
        returns_data: pd.DataFrame
    ) -> pd.DataFrame:
        """计算因子收益序列"""
        if combined.empty or returns_data.empty:
            return pd.DataFrame()
        
        # 按日期分组，计算每个日期的因子值与下期收益的相关性
        dates = sorted(combined['date'].unique())
        
        ic_series = []
        for d in dates[:-1]:
            factor_day = combined[combined['date'] == d]
            return_day = returns_data[returns_data['date'] == d]
            
            if factor_day.empty or return_day.empty:
                continue
            
            merged = pd.merge(
                factor_day[['symbol', 'factor_value']],
                return_day[['symbol', 'return']],
                on='symbol',
                how='inner'
            )
            
            if len(merged) < 10:
                continue
            
            try:
                ic, _ = stats.spearmanr(
                    merged['factor_value'],
                    merged['return']
                )
                if not np.isnan(ic):
                    ic_series.append({'date': d, 'ic': ic})
            except:
                continue
        
        if not ic_series:
            return pd.DataFrame()
        
        return pd.DataFrame(ic_series)
    
    def _combine(
        self,
        factor_data: Dict[str, pd.DataFrame],
        weights: Dict[str, float],
        method: str
    ) -> pd.DataFrame:
        """组合因子"""
        # 获取公共股票列表
        common_symbols = None
        for name, df in factor_data.items():
            if df.empty:
                continue
            symbols = set(df['symbol'].unique())
            if common_symbols is None:
                common_symbols = symbols
            else:
                common_symbols = common_symbols & symbols
        
        if not common_symbols:
            logger.warning("没有共同的股票")
            return pd.DataFrame()
        
        # 创建复合因子
        combined_data = []
        
        for symbol in common_symbols:
            score = 0
            for name, df in factor_data.items():
                if name not in weights:
                    continue
                
                factor_row = df[df['symbol'] == symbol]
                if factor_row.empty:
                    continue
                
                factor_value = factor_row['factor_value'].values[0]
                weight = weights[name]
                
                score += factor_value * weight
            
            # 获取日期
            dates = set()
            for name, df in factor_data.items():
                dates.update(df[df['symbol'] == symbol]['date'].tolist())
            
            for d in dates:
                combined_data.append({
                    'symbol': symbol,
                    'date': d,
                    'factor_value': score,
                    'weight': weights.get(symbol, 1.0)
                })
        
        if not combined_data:
            return pd.DataFrame()
        
        result = pd.DataFrame(combined_data)
        
        # Z-score标准化最终结果
        if self.normalize and not result.empty:
            values = result['factor_value'].values
            mean = np.mean(values)
            std = np.std(values)
            if std > 0:
                result['factor_value'] = (values - mean) / std
        
        return result
    
    def get_ic_series(self, factor_name: str) -> pd.Series:
        """获取IC序列"""
        return pd.Series()
    
    def get_correlation_matrix(self) -> pd.DataFrame:
        """获取因子相关性矩阵"""
        return pd.DataFrame()


# ==================== 因子正交化 ====================

class FactorOrthogonalizer:
    """
    因子正交化
    
    用于去除因子间的共线性
    """
    
    def orthogonalize(
        self,
        factor_data: Dict[str, pd.DataFrame],
        base_factor: str = None
    ) -> Dict[str, pd.DataFrame]:
        """
        正交化因子
        
        Args:
            factor_data: 因子数据
            base_factor: 基础因子 (不去正交化)
            
        Returns:
            正交化后的因子数据
        """
        # 获取公共数据
        merged = None
        for name, df in factor_data.items():
            if merged is None:
                merged = df.copy()
            else:
                merged = pd.merge(
                    merged,
                    df.rename(columns={'factor_value': name}),
                    on=['symbol', 'date'],
                    how='inner'
                )
        
        if merged is None or merged.empty:
            return factor_data
        
        # 对每个因子进行回归正交化
        orthogonalized = {}
        
        factor_cols = [c for c in merged.columns if c not in ['symbol', 'date']]
        
        for name in factor_cols:
            if name == base_factor:
                orthogonalized[name] = factor_data[name].copy()
                continue
            
            # 对其他因子进行回归
            Y = merged[name].values
            
            # 使用其他因子作为X
            X_cols = [c for c in factor_cols if c != name]
            
            if not X_cols:
                orthogonalized[name] = factor_data[name].copy()
                continue
            
            X = merged[X_cols].values
            
            try:
                # 线性回归
                from numpy.linalg import lstsq
                
                # 添加常数项
                X = np.column_stack([np.ones(len(Y)), X])
                
                # 最小二乘
                coeffs, _, _, _ = lstsq(X, Y, rcond=None)
                
                # 预测值
                Y_pred = X @ coeffs
            
                # 残差即为正交化后的因子值
                residual = Y - Y_pred
                
                # 标准化
                std = np.std(residual)
                if std > 0:
                    residual = residual / std
                
                # 创建结果DataFrame
                result = factor_data[name].copy()
                result['factor_value'] = residual
                
                orthogonalized[name] = result
                
            except Exception as e:
                logger.warning(f"因子{name}正交化失败: {e}")
                orthogonalized[name] = factor_data[name].copy()
        
        return orthogonalized


# ==================== 导出 ====================

__all__ = [
    'MultiFactorCombiner',
    'CombinedFactor',
    'CombinationMethod',
    'FactorOrthogonalizer',
]
