"""
基础因子类
Base Factor Classes
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
import pandas as pd


class Factor(ABC):
    """
    因子基类
    所有因子都需要继承这个类
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        初始化因子
        
        Args:
            name: 因子名称
            description: 因子描述
        """
        self.name = name
        self.description = description
        self.data: Optional[pd.DataFrame] = None
        self.values: Optional[pd.Series] = None
        
    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算因子值（子类必须实现）
        
        Args:
            data: 输入数据（包含价格、财务等数据）
            
        Returns:
            因子值序列
        """
    
    def normalize(self, method: str = "zscore") -> pd.Series:
        """
        标准化因子值
        
        Args:
            method: 标准化方法 ('zscore', 'rank', 'minmax')
            
        Returns:
            标准化后的因子值
        """
        if self.values is None:
            raise ValueError("请先计算因子值")
            
        if method == "zscore":
            return (self.values - self.values.mean()) / self.values.std()
        elif method == "rank":
            return self.values.rank(pct=True)
        elif method == "minmax":
            return (self.values - self.values.min()) / (self.values.max() - self.values.min())
        else:
            raise ValueError(f"不支持的标准化方法: {method}")
    
    def ic_analysis(self, returns: pd.Series) -> Dict[str, float]:
        """
        计算信息系数 (Information Coefficient)
        
        Args:
            returns: 收益率序列
            
        Returns:
            IC统计信息
        """
        if self.values is None:
            raise ValueError("请先计算因子值")
        
        # 对齐数据
        common_index = self.values.index.intersection(returns.index)
        if len(common_index) == 0:
            return {"ic": 0, "ic_ir": 0, "ic_sign_ratio": 0}
        
        factor_aligned = self.values.loc[common_index]
        returns_aligned = returns.loc[common_index]
        
        # 计算IC
        ic = factor_aligned.corr(returns_aligned)
        ic_ir = ic / factor_aligned.std() if factor_aligned.std() > 0 else 0
        ic_sign_ratio = (factor_aligned * returns_aligned > 0).mean()
        
        return {
            "ic": ic,
            "ic_ir": ic_ir,
            "ic_sign_ratio": ic_sign_ratio
        }
    
    def __repr__(self):
        return f"Factor(name='{self.name}')"


class FactorSystem:
    """
    多因子系统
    管理多个因子的组合和评估
    """
    
    def __init__(self, name: str = "Multi-Factor System"):
        """
        初始化因子系统
        
        Args:
            name: 系统名称
        """
        self.name = name
        self.factors: Dict[str, Factor] = {}
        self.factor_values: pd.DataFrame = pd.DataFrame()
        
    def add_factor(self, factor: Factor, weight: float = 1.0) -> None:
        """
        添加因子
        
        Args:
            factor: 因子实例
            weight: 因子权重
        """
        factor.weight = weight
        self.factors[factor.name] = factor
        
    def remove_factor(self, factor_name: str) -> None:
        """
        移除因子
        
        Args:
            factor_name: 要移除的因子名称
        """
        if factor_name in self.factors:
            del self.factors[factor_name]
    
    def calculate_all(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有因子值
        
        Args:
            data: 输入数据
            
        Returns:
            包含所有因子值的数据框
        """
        factor_data = {}
        
        for name, factor in self.factors.items():
            factor_values = factor.calculate(data)
            factor_data[name] = factor_values
            
        self.factor_values = pd.DataFrame(factor_data)
        return self.factor_values
    
    def get_composite_score(self, weights: Optional[Dict[str, float]] = None, 
                             normalize: bool = True) -> pd.Series:
        """
        计算综合得分
        
        Args:
            weights: 因子权重字典，如果为None则使用添加时的权重
            normalize: 是否标准化
            
        Returns:
            综合得分
        """
        if self.factor_values.empty:
            raise ValueError("请先计算因子值")
        
        # 获取权重
        if weights is None:
            weights = {name: getattr(factor, 'weight', 1.0) 
                      for name, factor in self.factors.items()}
        
        # 计算加权得分
        weighted_scores = pd.Series(0.0, index=self.factor_values.index)
        
        for name, weight in weights.items():
            if name in self.factor_values.columns:
                factor_values = self.factor_values[name]
                if normalize:
                    factor_values = (factor_values - factor_values.mean()) / factor_values.std()
                weighted_scores += factor_values * weight
        
        return weighted_scores
    
    def get_correlation_matrix(self) -> pd.DataFrame:
        """
        获取因子相关性矩阵
        """
        if self.factor_values.empty:
            raise ValueError("请先计算因子值")
        
        return self.factor_values.corr()
    
    def summary(self) -> Dict[str, Any]:
        """
        获取系统摘要信息
        """
        return {
            "name": self.name,
            "num_factors": len(self.factors),
            "factor_names": list(self.factors.keys()),
            "correlation_matrix": self.get_correlation_matrix().to_dict(),
            "data_points": len(self.factor_values)
        }
    
    def __repr__(self):
        return f"FactorSystem(name='{self.name}', factors={len(self.factors)})"
