"""
因子注册表
存储和管理所有已注册的因子
"""

import pandas as pd
import json
from typing import Dict, List, Optional
from datetime import datetime


class FactorRegistry:
    """
    因子注册表
    
    功能:
    - 注册新因子
    - 获取已注册因子
    - 列出所有因子
    - 持久化存储
    """
    
    def __init__(self, storage_file: str = "factors_registry.csv"):
        self.storage_file = storage_file
        self._registry: Dict[str, Dict] = {}
        self._load()
    
    def _load(self):
        """从 CSV 加载"""
        try:
            df = pd.read_csv(self.storage_file)
            for _, row in df.iterrows():
                self._registry[row['name']] = {
                    'name': row['name'],
                    'class_name': row['class_name'],
                    'category': row.get('category', 'custom'),
                    'params': json.loads(row.get('params', '{}')),
                    'description': row.get('description', ''),
                    'created_at': row.get('created_at', datetime.now().isoformat()),
                }
        except FileNotFoundError:
            pass
    
    def save(self):
        """保存到 CSV"""
        data = []
        for name, info in self._registry.items():
            data.append({
                'name': name,
                'class_name': info['class_name'],
                'category': info.get('category', 'custom'),
                'params': json.dumps(info.get('params', {})),
                'description': info.get('description', ''),
                'created_at': info.get('created_at', datetime.now().isoformat()),
            })
        
        if data:
            df = pd.DataFrame(data)
            df.to_csv(self.storage_file, index=False)
    
    def register(
        self,
        name: str,
        class_name: str,
        category: str = "custom",
        params: dict = None,
        description: str = ""
    ):
        """
        注册因子
        
        Args:
            name: 因子名称 (唯一标识)
            class_name: 因子类名 (Python 类名)
            category: 因子类别 (tech, fundamental, custom)
            params: 默认参数
            description: 描述
        """
        self._registry[name] = {
            'name': name,
            'class_name': class_name,
            'category': category,
            'params': params or {},
            'description': description,
            'created_at': datetime.now().isoformat(),
        }
        self.save()
        print(f"✅ 因子已注册: {name} ({class_name})")
    
    def get(self, name: str) -> Optional[Dict]:
        """获取因子信息"""
        return self._registry.get(name)
    
    def list_all(self) -> List[Dict]:
        """列出所有因子"""
        return list(self._registry.values())
    
    def list_by_category(self, category: str) -> List[Dict]:
        """按类别列出因子"""
        return [f for f in self._registry.values() if f.get('category') == category]
    
    def delete(self, name: str):
        """删除因子"""
        if name in self._registry:
            del self._registry[name]
            self.save()
    
    def clear(self):
        """清空注册表"""
        self._registry.clear()
        self.save()


# ==================== 便捷函数 ====================

_registry = None

def get_registry(storage_file: str = "factors_registry.csv") -> FactorRegistry:
    """获取注册表单例"""
    global _registry
    if _registry is None:
        _registry = FactorRegistry(storage_file)
    return _registry


def register_factor(
    name: str,
    class_name: str,
    category: str = "custom",
    params: dict = None,
    description: str = ""
):
    """便捷注册函数"""
    reg = get_registry()
    reg.register(name, class_name, category, params, description)


def list_factors() -> List[Dict]:
    """列出所有因子"""
    return get_registry().list_all()


def get_factor_info(name: str) -> Optional[Dict]:
    """获取因子信息"""
    return get_registry().get(name)


__all__ = [
    'FactorRegistry',
    'get_registry',
    'register_factor',
    'list_factors',
    'get_factor_info',
]
