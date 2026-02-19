"""
因子版本管理模块
Factor Version Management

功能:
- 记录因子计算的版本信息
- 追踪数据血缘
- 支持因子复现
"""

import pandas as pd
import json
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class VersionStatus(Enum):
    """版本状态"""
    DRAFT = 'draft'       # 草稿
    ACTIVE = 'active'     # 活跃
    DEPRECATED = 'deprecated'  # 已废弃
    ARCHIVED = 'archived'  # 归档


@dataclass
class FactorVersion:
    """因子版本"""
    id: int = None
    factor_name: str = ''
    version: str = ''
    description: str = ''
    computation_params: Dict[str, Any] = None
    source_data_hash: str = ''
    data_range: str = ''
    status: str = 'draft'
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.computation_params is None:
            self.computation_params = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        data = asdict(self)
        data['computation_params'] = json.dumps(self.computation_params)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FactorVersion':
        """从字典创建"""
        if isinstance(data.get('computation_params'), str):
            data['computation_params'] = json.loads(data['computation_params'])
        return cls(**data)


class FactorVersionManager:
    """
    因子版本管理器
    
    功能:
    - 创建新版本
    - 查询版本历史
    - 管理版本状态
    - 验证数据一致性
    """
    
    def __init__(self, storage=None):
        """
        初始化
        
        Args:
            storage: 数据库存储实例 (FactorStorage)
        """
        self.storage = storage
        self._versions: Dict[str, List[FactorVersion]] = {}
    
    def create_version(
        self,
        factor_name: str,
        version: str,
        params: Dict[str, Any],
        data_hash: str,
        data_range: str,
        description: str = ''
    ) -> FactorVersion:
        """
        创建新版本
        
        Args:
            factor_name: 因子名称
            version: 版本号 (如 'v1.0')
            params: 计算参数
            data_hash: 数据指纹 (用于验证)
            data_range: 数据范围
            description: 版本描述
            
        Returns:
            FactorVersion
        """
        version_obj = FactorVersion(
            factor_name=factor_name,
            version=version,
            description=description,
            computation_params=params,
            source_data_hash=data_hash,
            data_range=data_range,
            status=VersionStatus.ACTIVE.value
        )
        
        # 保存到存储
        if self.storage:
            self._save_version(version_obj)
        
        # 内存缓存
        if factor_name not in self._versions:
            self._versions[factor_name] = []
        self._versions[factor_name].append(version_obj)
        
        logger.info(f"✅ 创建因子版本: {factor_name} {version}")
        
        return version_obj
    
    def _save_version(self, version: FactorVersion):
        """保存版本到数据库"""
        # 如果有数据库存储，调用相应的save方法
        # 目前使用内存存储
    
    def get_versions(
        self,
        factor_name: str = None,
        status: str = None
    ) -> List[FactorVersion]:
        """
        获取版本列表
        
        Args:
            factor_name: 因子名称 (可选)
            status: 状态过滤
            
        Returns:
            版本列表
        """
        versions = []
        
        if factor_name:
            versions.extend(self._versions.get(factor_name, []))
        else:
            for v_list in self._versions.values():
                versions.extend(v_list)
        
        if status:
            versions = [v for v in versions if v.status == status]
        
        # 按创建时间排序
        versions.sort(key=lambda v: v.created_at, reverse=True)
        
        return versions
    
    def get_latest_version(self, factor_name: str) -> Optional[FactorVersion]:
        """获取最新版本"""
        versions = self.get_versions(factor_name)
        return versions[0] if versions else None
    
    def deprecate_version(
        self,
        factor_name: str,
        version: str
    ) -> bool:
        """
        废弃版本
        
        Args:
            factor_name: 因子名称
            version: 版本号
            
        Returns:
            是否成功
        """
        versions = self._versions.get(factor_name, [])
        
        for v in versions:
            if v.version == version:
                v.status = VersionStatus.DEPRECATED.value
                v.updated_at = datetime.now()
                logger.info(f"✅ 废弃版本: {factor_name} {version}")
                return True
        
        return False
    
    def archive_version(
        self,
        factor_name: str,
        version: str
    ) -> bool:
        """
        归档版本
        
        Args:
            factor_name: 因子名称
            version: 版本号
            
        Returns:
            是否成功
        """
        versions = self._versions.get(factor_name, [])
        
        for v in versions:
            if v.version == version:
                v.status = VersionStatus.ARCHIVED.value
                v.updated_at = datetime.now()
                logger.info(f"✅ 归档版本: {factor_name} {version}")
                return True
        
        return False
    
    def verify_data_hash(
        self,
        factor_name: str,
        version: str,
        data_hash: str
    ) -> bool:
        """
        验证数据一致性
        
        Args:
            factor_name: 因子名称
            version: 版本号
            data_hash: 当前数据指纹
            
        Returns:
            是否一致
        """
        versions = self._versions.get(factor_name, [])
        
        for v in versions:
            if v.version == version:
                if v.source_data_hash == data_hash:
                    return True
                else:
                    logger.warning(
                        f"⚠️ 数据不一致: {factor_name} {version}\n"
                        f"  预期: {v.source_data_hash}\n"
                        f"  实际: {data_hash}"
                    )
                    return False
        
        return False
    
    def generate_data_hash(
        self,
        data: pd.DataFrame,
        params: Dict[str, Any]
    ) -> str:
        """
        生成数据指纹
        
        Args:
            data: 因子数据
            params: 计算参数
            
        Returns:
            hash字符串
        """
        # 数据样本hash
        sample = data.head(100).to_json()
        params_str = json.dumps(params, sort_keys=True)
        
        combined = f"{sample}_{params_str}"
        return hashlib.md5(combined.encode()).hexdigest()


# ==================== 数据血缘追踪 ====================

@dataclass
class LineageNode:
    """血缘节点"""
    node_type: str  # 'source', 'factor', 'strategy'
    name: str
    version: str = ''
    parents: List[str] = None
    
    def __post_init__(self):
        if self.parents is None:
            self.parents = []


class DataLineageTracker:
    """
    数据血缘追踪器
    
    功能:
    - 记录数据流转
    - 追踪因子依赖
    - 支持回溯分析
    """
    
    def __init__(self):
        self._lineage: Dict[str, LineageNode] = {}
    
    def add_node(self, node: LineageNode):
        """添加节点"""
        key = f"{node.name}:{node.version}"
        self._lineage[key] = node
        logger.info(f"✅ 添加血缘节点: {key}")
    
    def add_edge(self, parent: str, child: str):
        """添加依赖边"""
        # parent -> child
        parent_key = f"{parent['name']}:{parent['version']}"
        child_key = f"{child['name']}:{child['version']}"
        
        if parent_key in self._lineage:
            self._lineage[parent_key].parents.append(child_key)
    
    def get_lineage(self, name: str, version: str = '') -> List[LineageNode]:
        """获取血缘链"""
        key = f"{name}:{version}" if version else name
        
        # 递归获取所有祖先
        nodes = []
        visited = set()
        
        def dfs(node_key):
            if node_key in visited:
                return
            visited.add(node_key)
            
            if node_key in self._lineage:
                node = self._lineage[node_key]
                nodes.append(node)
                for parent_key in node.parents:
                    dfs(parent_key)
        
        dfs(key)
        
        return nodes


# ==================== 便捷函数 ====================

_version_manager: Optional[FactorVersionManager] = None

def get_version_manager() -> FactorVersionManager:
    """获取版本管理器单例"""
    global _version_manager
    if _version_manager is None:
        _version_manager = FactorVersionManager()
    return _version_manager


def create_factor_version(
    factor_name: str,
    version: str,
    params: Dict[str, Any],
    data: pd.DataFrame,
    data_range: str,
    description: str = ''
) -> FactorVersion:
    """创建因子版本 (便捷函数)"""
    manager = get_version_manager()
    
    # 生成数据hash
    data_hash = manager.generate_data_hash(data, params)
    
    return manager.create_version(
        factor_name=factor_name,
        version=version,
        params=params,
        data_hash=data_hash,
        data_range=data_range,
        description=description
    )


# ==================== 导出 ====================

__all__ = [
    'FactorVersion',
    'FactorVersionManager',
    'VersionStatus',
    'DataLineageTracker',
    'LineageNode',
    'get_version_manager',
    'create_factor_version',
]
