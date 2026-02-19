"""
因子工厂
根据注册信息动态创建因子实例
"""

import importlib
from typing import Dict, List, Optional, Type, Any
from ..core import get_registry, FactorRegistry


class FactorFactory:
    """
    因子工厂
    
    功能:
    - 从注册表动态加载因子类
    - 创建因子实例
    - 因子类自动发现
    """
    
    # 已知因子类映射 (从 factors.basic)
    KNOWN_FACTORS = {
        # 技术因子
        'MomentumFactor': 'quant_factor_system.factors.basic',
        'VolatilityFactor': 'quant_factor_system.factors.basic',
        
        # 收益率因子
        'Return1dFactor': 'quant_factor_system.factors.basic',
        'Return5dFactor': 'quant_factor_system.factors.basic',
        'Return20dFactor': 'quant_factor_system.factors.basic',
        'Return60dFactor': 'quant_factor_system.factors.basic',
        
        # 均值回归因子
        'DistMA10Factor': 'quant_factor_system.factors.basic',
        'DistMA20Factor': 'quant_factor_system.factors.basic',
        'DistMA60Factor': 'quant_factor_system.factors.basic',
        'ZScore60Factor': 'quant_factor_system.factors.basic',
        
        # 价值因子
        'ValueFactor': 'quant_factor_system.factors.basic',
        'QualityFactor': 'quant_factor_system.factors.basic',
        'GrowthFactor': 'quant_factor_system.factors.basic',
        'SizeFactor': 'quant_factor_system.factors.basic',
        'LiquidityFactor': 'quant_factor_system.factors.basic',
        'EarningsYieldFactor': 'quant_factor_system.factors.basic',
    }
    
    @classmethod
    def create(cls, name: str, params: dict = None) -> Any:
        """
        创建因子实例
        
        Args:
            name: 注册的因子名称
            params: 参数字典
        
        Returns:
            因子实例
        """
        # 1. 从注册表获取因子信息
        reg = get_registry()
        info = reg.get(name)
        
        if not info:
            raise ValueError(f"因子未注册: {name}")
        
        # 2. 获取因子类
        class_name = info['class_name']
        factor_class = cls._load_class(class_name)
        
        # 3. 合并参数
        factor_params = {**(info.get('params', {})), **(params or {})}
        
        # 4. 创建实例
        return factor_class(**factor_params)
    
    @classmethod
    def create_from_info(cls, info: Dict) -> Any:
        """从因子信息字典创建实例"""
        class_name = info['class_name']
        factor_class = cls._load_class(class_name)
        return factor_class(**info.get('params', {}))
    
    @classmethod
    def _load_class(cls, class_name: str) -> Type:
        """动态加载因子类"""
        # 1. 检查已知因子
        if class_name in cls.KNOWN_FACTORS:
            module_path = cls.KNOWN_FACTORS[class_name]
            module = importlib.import_module(module_path)
            return getattr(module, class_name)
        
        # 2. 尝试从 factors.basic 加载
        try:
            module = importlib.import_module('quant_factor_system.factors.basic')
            return getattr(module, class_name)
        except (ImportError, AttributeError):
            pass
        
        raise ValueError(f"无法加载因子类: {class_name}")
    
    @classmethod
    def get_available_factors(cls) -> List[Dict]:
        """获取所有可用因子 (从注册表)"""
        return get_registry().list_all()
    
    @classmethod
    def get_builtin_factors(cls) -> List[Dict]:
        """获取内置因子列表"""
        return [
            {'name': 'momentum', 'class_name': 'MomentumFactor', 'category': 'tech', 'description': '动量因子'},
            {'name': 'return_1d', 'class_name': 'Return1dFactor', 'category': 'return', 'description': '1日收益率'},
            {'name': 'return_5d', 'class_name': 'Return5dFactor', 'category': 'return', 'description': '5日收益率'},
            {'name': 'return_20d', 'class_name': 'Return20dFactor', 'category': 'return', 'description': '20日收益率'},
            {'name': 'dist_ma10', 'class_name': 'DistMA10Factor', 'category': 'tech', 'description': '10日均线偏离'},
            {'name': 'zscore_60', 'class_name': 'ZScore60Factor', 'category': 'tech', 'description': '60日Z分数'},
        ]
    
    @classmethod
    def discover_and_register(cls, auto_save: bool = True):
        """自动发现并注册所有内置因子"""
        reg = get_registry()
        
        for factor_info in cls.get_builtin_factors():
            name = factor_info['name']
            
            # 检查是否已注册
            if reg.get(name):
                continue
            
            # 注册因子
            reg.register(
                name=name,
                class_name=factor_info['class_name'],
                category=factor_info['category'],
                params={'period': 20} if 'period' not in factor_info and 'window' not in factor_info else {'period': 20},
                description=factor_info['description']
            )
        
        if auto_save:
            reg.save()


# ==================== 便捷函数 ====================

def create_factor(name: str, params: dict = None):
    """创建因子实例"""
    return FactorFactory.create(name, params)


def list_available_factors() -> List[Dict]:
    """列出所有可用因子"""
    return FactorFactory.get_available_factors()


def register_all_builtins():
    """注册所有内置因子"""
    FactorFactory.discover_and_register()


__all__ = [
    'FactorFactory',
    'create_factor',
    'list_available_factors',
    'register_all_builtins',
]
