"""
因子选择器 - 根据IC和其他指标选择因子
Factor Selector

功能:
1. 基于IC选择因子
2. 多因子组合优化
3. 因子相关性分析
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FactorScore:
    """因子评分"""
    name: str
    ic: float
    icir: float
    win_rate: float
    momentum: float  # IC自相关性
    score: float  # 综合评分


class FactorSelector:
    """
    因子选择器
    
    根据多种指标选择优质因子
    """
    
    def __init__(self, min_ic: float = 0.02, min_samples: int = 1000):
        """
        初始化
        
        Args:
            min_ic: 最小IC阈值
            min_samples: 最小样本数
        """
        self.min_ic = min_ic
        self.min_samples = min_samples
        self.factor_scores: Dict[str, FactorScore] = {}
    
    def evaluate_factor(
        self,
        factor_name: str,
        ic: float,
        ic_std: float,
        win_rate: float,
        samples: int,
        ic_series: pd.Series = None
    ) -> Optional[FactorScore]:
        """
        评估单个因子
        
        Args:
            factor_name: 因子名称
            ic: 信息系数
            ic_std: IC标准差
            win_rate: IC胜率
            samples: 样本数
            ic_series: IC时间序列（用于计算动量）
            
        Returns:
            FactorScore 或 None（如果不符合要求）
        """
        if samples < self.min_samples:
            return None
        
        if abs(ic) < self.min_ic:
            return None
        
        # 计算ICIR
        icir = abs(ic) / ic_std if ic_std > 0 else 0
        
        # 计算IC动量（近期IC均值/历史IC均值）
        if ic_series is not None and len(ic_series) > 60:
            recent_ic = ic_series.tail(30).mean()
            historical_ic = ic_series.head(len(ic_series)-30).mean()
            momentum = recent_ic / historical_ic if historical_ic != 0 else 1.0
        else:
            momentum = 1.0
        
        # 计算综合评分
        score = self._calculate_score(ic, icir, win_rate, momentum)
        
        factor_score = FactorScore(
            name=factor_name,
            ic=ic,
            icir=icir,
            win_rate=win_rate,
            momentum=momentum,
            score=score
        )
        
        self.factor_scores[factor_name] = factor_score
        return factor_score
    
    def _calculate_score(
        self,
        ic: float,
        icir: float,
        win_rate: float,
        momentum: float
    ) -> float:
        """
        计算综合评分
        
        权重:
        - IC绝对值: 40%
        - ICIR: 30%
        - 胜率: 20%
        - IC动量: 10%
        """
        ic_weight = 0.4
        icir_weight = 0.3
        win_weight = 0.2
        mom_weight = 0.1
        
        # 归一化
        ic_score = min(abs(ic) / 0.05, 1.0)  # 假设0.05是很好的IC
        icir_score = min(icir / 0.5, 1.0)  # 假设0.5是很好的ICIR
        win_score = win_rate
        mom_score = min(max(momentum, 0), 2) / 2  # 0-2范围归一化到0-1
        
        total_score = (
            ic_weight * ic_score +
            icir_weight * icir_score +
            win_weight * win_score +
            mom_weight * mom_score
        )
        
        return round(total_score, 4)
    
    def select_top_k(
        self,
        k: int = 5,
        sort_by: str = 'score'
    ) -> List[FactorScore]:
        """
        选择前K个因子
        
        Args:
            k: 选择数量
            sort_by: 排序依据 (score/ic/icir/win_rate)
            
        Returns:
            FactorScore列表
        """
        if not self.factor_scores:
            return []
        
        scores = list(self.factor_scores.values())
        
        # 按指定字段排序
        reverse = True  # 降序
        if sort_by == 'momentum':
            reverse = False  # IC动量越小越好
        
        scores = sorted(scores, key=lambda x: getattr(x, sort_by), reverse=reverse)
        
        return scores[:k]
    
    def select_by_correlation(
        self,
        factor_ic_matrix: pd.DataFrame,
        threshold: float = 0.7
    ) -> List[str]:
        """
        基于相关性选择因子（去相关）
        
        Args:
            factor_ic_matrix: 因子IC矩阵（行=因子，列=日期）
            threshold: 相关性阈值
            
        Returns:
            选中的因子名称列表
        """
        selected = []
        remaining = list(factor_ic_matrix.index)
        
        while remaining:
            # 选择与已选因子相关性最低的因子
            best_factor = None
            best_avg_corr = float('inf')
            
            for factor in remaining:
                if not selected:
                    avg_corr = 0
                else:
                    # 计算与所有已选因子的平均相关性
                    corrs = []
                    for sel in selected:
                        if factor in factor_ic_matrix.index and sel in factor_ic_matrix.columns:
                            corr = factor_ic_matrix.loc[factor, sel]
                            corrs.append(abs(corr))
                    avg_corr = np.mean(corrs) if corrs else 0
                
                if avg_corr < best_avg_corr:
                    best_avg_corr = avg_corr
                    best_factor = factor
            
            # 如果相关性低于阈值，添加
            if best_avg_corr < threshold:
                selected.append(best_factor)
                remaining.remove(best_factor)
            else:
                # 相关性太高，停止
                break
        
        return selected
    
    def optimize_weights(
        self,
        factor_scores: List[FactorScore],
        returns_df: pd.DataFrame,
        method: str = 'icir'
    ) -> Dict[str, float]:
        """
        优化因子权重
        
        Args:
            factor_scores: 因子评分列表
            returns_df: 因子收益DataFrame
            method: 优化方法 (icir/sharpe/equal)
            
        Returns:
            权重字典
        """
        if method == 'equal':
            # 等权
            n = len(factor_scores)
            return {s.name: 1.0/n for s in factor_scores}
        
        elif method == 'icir':
            # 基于ICIR加权
            total_icir = sum(s.icir for s in factor_scores)
            if total_icir == 0:
                return {s.name: 1.0/len(factor_scores) for s in factor_scores}
            return {s.name: s.icir/total_icir for s in factor_scores}
        
        elif method == 'score':
            # 基于综合评分加权
            total_score = sum(s.score for s in factor_scores)
            if total_score == 0:
                return {s.name: 1.0/len(factor_scores) for s in factor_scores}
            return {s.name: s.score/total_score for s in factor_scores}
        
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def get_summary(self) -> pd.DataFrame:
        """
        获取因子评分汇总
        
        Returns:
            汇总DataFrame
        """
        if not self.factor_scores:
            return pd.DataFrame()
        
        data = []
        for score in self.factor_scores.values():
            data.append({
                '因子名称': score.name,
                'IC': score.ic,
                'ICIR': score.icir,
                '胜率': score.win_rate,
                'IC动量': score.momentum,
                '综合评分': score.score
            })
        
        return pd.DataFrame(data).sort_values('综合评分', ascending=False)


def create_factor_selector(
    min_ic: float = 0.02,
    min_samples: int = 1000
) -> FactorSelector:
    """创建因子选择器"""
    return FactorSelector(min_ic, min_samples)


# ==================== 导出 ====================

__all__ = [
    'FactorSelector',
    'FactorScore',
    'create_factor_selector',
]
