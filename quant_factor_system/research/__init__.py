"""
研究工作流模块
因子研究、版本管理、论文复现的完整工作流
"""

from .templates import (
    BaseFactorTemplate,
    FactorTemplate,
    FactorVersion,
    MomentumTemplate,
    MeanReversionTemplate,
    VolatilityTemplate,
    VolumeTemplate,
    QualityTemplate,
    ValueTemplate,
    CompositeFactorTemplate,
    FactorTemplateManager,
    register_builtin_templates,
    create_template,
)

from . import templates

__all__ = [
    # 模板
    "BaseFactorTemplate",
    "FactorTemplate",
    "FactorVersion",
    "MomentumTemplate",
    "MeanReversionTemplate",
    "VolatilityTemplate",
    "VolumeTemplate",
    "QualityTemplate",
    "ValueTemplate",
    "CompositeFactorTemplate",
    "FactorTemplateManager",
    "register_builtin_templates",
    "create_template",
    
    # 研究工作流
    "ResearchRecord",
    "ResearchWorkflow",
    "FactorVersionManager",
    "PaperReproducer",
    "create_research_workflow",
    "create_version_manager",
    
    # 子模块
    "templates",
]

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import hashlib
import copy
import warnings
warnings.filterwarnings('ignore')


@dataclass
class ResearchRecord:
    """
    研究记录
    记录一次完整的研究过程
    """
    id: str
    title: str
    factor_name: str
    created_at: str
    status: str  # draft, running, completed, archived
    hypothesis: str = ""
    methodology: str = ""
    data_source: str = ""
    period: str = ""
    
    # 研究结果
    ic: float = 0.0
    ic_ir: float = 0.0
    win_rate: float = 0.0
    long_short_return: float = 0.0
    
    # 元数据
    author: str = ""
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    
    # 关联
    version_id: str = ""
    backtest_id: str = ""


@dataclass
class FactorVersion:
    """
    因子版本
    """
    id: str
    factor_name: str
    version: str
    created_at: str
    code_hash: str
    config: Dict
    performance: Dict
    parent_version: str = ""
    notes: str = ""


class ResearchWorkflow:
    """
    研究工作流
    管理因子研究的完整生命周期
    """
    
    def __init__(self, storage_dir: str = "research"):
        """
        初始化
        
        Args:
            storage_dir: 存储目录
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.records: Dict[str, ResearchRecord] = {}
        self.versions: Dict[str, List[FactorVersion]] = {}
        
        self._load_records()
    
    def _load_records(self):
        """加载研究记录"""
        records_file = self.storage_dir / "records.json"
        
        if records_file.exists():
            with open(records_file, 'r') as f:
                data = json.load(f)
                for r in data:
                    self.records[r['id']] = ResearchRecord(**r)
    
    def _save_records(self):
        """保存研究记录"""
        records_file = self.storage_dir / "records.json"
        
        with open(records_file, 'w') as f:
            json.dump([r.__dict__ for r in self.records.values()], f, indent=2, default=str)
    
    def _generate_id(self) -> str:
        """生成唯一 ID"""
        return hashlib.md5(f"{datetime.now()}".encode()).hexdigest()[:8]
    
    def create_record(self, title: str, factor_name: str,
                     author: str = "", **kwargs) -> ResearchRecord:
        """
        创建研究记录
        
        Args:
            title: 研究标题
            factor_name: 因子名称
            author: 作者
            **kwargs: 其他参数
            
        Returns:
            ResearchRecord
        """
        record = ResearchRecord(
            id=self._generate_id(),
            title=title,
            factor_name=factor_name,
            created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            status="draft",
            author=author,
            **kwargs
        )
        
        self.records[record.id] = record
        self._save_records()
        
        return record
    
    def update_record(self, record_id: str, **kwargs) -> Optional[ResearchRecord]:
        """
        更新研究记录
        
        Args:
            record_id: 记录 ID
            **kwargs: 更新内容
            
        Returns:
            更新后的记录或 None
        """
        if record_id not in self.records:
            return None
        
        record = self.records[record_id]
        
        for key, value in kwargs.items():
            if hasattr(record, key):
                setattr(record, key, value)
        
        self._save_records()
        return record
    
    def get_record(self, record_id: str) -> Optional[ResearchRecord]:
        """
        获取研究记录
        
        Args:
            record_id: 记录 ID
            
        Returns:
            ResearchRecord 或 None
        """
        return self.records.get(record_id)
    
    def list_records(self, status: str = None, 
                    factor_name: str = None) -> List[ResearchRecord]:
        """
        列出研究记录
        
        Args:
            status: 筛选状态
            factor_name: 筛选因子名称
            
        Returns:
            ResearchRecord 列表
        """
        results = list(self.records.values())
        
        if status:
            results = [r for r in results if r.status == status]
        
        if factor_name:
            results = [r for r in results if r.factor_name == factor_name]
        
        return sorted(results, key=lambda x: x.created_at, reverse=True)
    
    def run_research(self, record_id: str,
                    research_func: Callable) -> ResearchRecord:
        """
        运行研究
        
        Args:
            record_id: 记录 ID
            research_func: 研究函数 (record, **kwargs) -> performance_dict
            
        Returns:
            更新后的记录
        """
        record = self.records.get(record_id)
        if not record:
            raise ValueError(f"记录 {record_id} 不存在")
        
        # 更新状态
        record.status = "running"
        self._save_records()
        
        try:
            # 运行研究
            performance = research_func(record)
            
            # 更新结果
            record.status = "completed"
            record.ic = performance.get('ic', 0)
            record.ic_ir = performance.get('ic_ir', 0)
            record.win_rate = performance.get('win_rate', 0)
            record.long_short_return = performance.get('long_short_return', 0)
            
        except Exception as e:
            record.status = "failed"
            record.notes = str(e)
        
        self._save_records()
        return record
    
    def archive_record(self, record_id: str) -> bool:
        """
        归档记录
        
        Args:
            record_id: 记录 ID
            
        Returns:
            是否成功
        """
        if record_id not in self.records:
            return False
        
        self.records[record_id].status = "archived"
        self._save_records()
        return True


class FactorVersionManager:
    """
    因子版本管理器
    管理因子的版本历史
    """
    
    def __init__(self, storage_dir: str = "research"):
        """
        初始化
        
        Args:
            storage_dir: 存储目录
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.versions: Dict[str, List[FactorVersion]] = {}
        self._load_versions()
    
    def _load_versions(self):
        """加载版本"""
        versions_file = self.storage_dir / "versions.json"
        
        if versions_file.exists():
            with open(versions_file, 'r') as f:
                data = json.load(f)
                for factor_name, vers in data.items():
                    self.versions[factor_name] = [FactorVersion(**v) for v in vers]
    
    def _save_versions(self):
        """保存版本"""
        versions_file = self.storage_dir / "versions.json"
        
        data = {
            name: [v.__dict__ for v in vers] 
            for name, vers in self.versions.items()
        }
        
        with open(versions_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _generate_id(self) -> str:
        """生成唯一 ID"""
        return hashlib.md5(f"{datetime.now()}".encode()).hexdigest()[:8]
    
    def create_version(self, factor_name: str, version: str,
                      code: str, config: Dict,
                      performance: Dict = None,
                      parent_version: str = "",
                      notes: str = "") -> FactorVersion:
        """
        创建版本
        
        Args:
            factor_name: 因子名称
            version: 版本号
            code: 代码
            config: 配置
            performance: 性能指标
            parent_version: 父版本
            notes: 备注
            
        Returns:
            FactorVersion
        """
        # 计算代码哈希
        code_hash = hashlib.md5(code.encode()).hexdigest()
        
        v = FactorVersion(
            id=self._generate_id(),
            factor_name=factor_name,
            version=version,
            created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            code_hash=code_hash,
            config=copy.deepcopy(config),
            performance=copy.deepcopy(performance) or {},
            parent_version=parent_version,
            notes=notes
        )
        
        if factor_name not in self.versions:
            self.versions[factor_name] = []
        
        self.versions[factor_name].append(v)
        self._save_versions()
        
        return v
    
    def get_versions(self, factor_name: str) -> List[FactorVersion]:
        """
        获取版本历史
        
        Args:
            factor_name: 因子名称
            
        Returns:
            版本列表
        """
        return self.versions.get(factor_name, [])
    
    def get_latest_version(self, factor_name: str) -> Optional[FactorVersion]:
        """
        获取最新版本
        
        Args:
            factor_name: 因子名称
            
        Returns:
            最新版本或 None
        """
        versions = self.versions.get(factor_name, [])
        if not versions:
            return None
        
        return versions[-1]
    
    def compare_versions(self, factor_name: str,
                       v1_id: str, v2_id: str) -> Dict[str, Any]:
        """
        对比两个版本
        
        Args:
            factor_name: 因子名称
            v1_id: 版本1 ID
            v2_id: 版本2 ID
            
        Returns:
            对比结果
        """
        versions = self.versions.get(factor_name, [])
        
        v1 = next((v for v in versions if v.id == v1_id), None)
        v2 = next((v for v in versions if v.id == v2_id), None)
        
        if not v1 or not v2:
            return {}
        
        # 对比性能
        perf_comparison = {}
        all_keys = set(v1.performance.keys()) | set(v2.performance.keys())
        
        for key in all_keys:
            val1 = v1.performance.get(key, 'N/A')
            val2 = v2.performance.get(key, 'N/A')
            perf_comparison[key] = {
                'version1': val1,
                'version2': val2,
                'change': val2 - val1 if isinstance(val1, (int, float)) and isinstance(val2, (int, float)) else 'N/A'
            }
        
        return {
            'version1': v1.__dict__,
            'version2': v2.__dict__,
            'performance_comparison': perf_comparison
        }
    
    def rollback(self, factor_name: str, version_id: str) -> bool:
        """
        回滚到指定版本
        
        Args:
            factor_name: 因子名称
            version_id: 版本 ID
            
        Returns:
            是否成功
        """
        versions = self.versions.get(factor_name, [])
        
        target = next((v for v in versions if v.id == version_id), None)
        if not target:
            return False
        
        # 创建新版本指向目标版本
        self.create_version(
            factor_name=factor_name,
            version=f"{target.version}.rollback",
            code=target.config.get('code', ''),
            config=target.config,
            performance={},
            parent_version=target.id,
            notes=f"回滚到版本 {target.version}"
        )
        
        return True


class PaperReproducer:
    """
    论文复现器
    辅助从论文中复现因子
    """
    
    def __init__(self):
        """初始化"""
        self.papers: Dict[str, Dict] = {}
    
    def add_paper(self, paper_id: str, title: str, 
                 authors: str, year: int, **kwargs):
        """
        添加论文
        
        Args:
            paper_id: 论文 ID
            title: 标题
            authors: 作者
            year: 年份
            **kwargs: 其他信息 (url, abstract, key_findings, etc.)
        """
        self.papers[paper_id] = {
            'id': paper_id,
            'title': title,
            'authors': authors,
            'year': year,
            'factors': [],  # 复现的因子列表
            'status': 'pending',  # pending, in_progress, completed
            **kwargs
        }
    
    def link_factor(self, paper_id: str, factor_name: str, 
                   config: Dict, notes: str = ""):
        """
        关联因子
        
        Args:
            paper_id: 论文 ID
            factor_name: 因子名称
            config: 因子配置
            notes: 备注
        """
        if paper_id not in self.papers:
            return False
        
        self.papers[paper_id]['factors'].append({
            'factor_name': factor_name,
            'config': config,
            'notes': notes,
            'status': 'pending'
        })
        
        return True
    
    def get_paper_factors(self, paper_id: str) -> List[Dict]:
        """
        获取论文关联的因子
        
        Args:
            paper_id: 论文 ID
            
        Returns:
            因子列表
        """
        return self.papers.get(paper_id, {}).get('factors', [])
    
    def mark_completed(self, paper_id: str, factor_name: str = None):
        """
        标记完成
        
        Args:
            paper_id: 论文 ID
            factor_name: 因子名称（可选）
        """
        if paper_id not in self.papers:
            return
        
        if factor_name:
            for f in self.papers[paper_id]['factors']:
                if f['factor_name'] == factor_name:
                    f['status'] = 'completed'
        else:
            self.papers[paper_id]['status'] = 'completed'
            for f in self.papers[paper_id]['factors']:
                f['status'] = 'completed'
    
    def list_papers(self, status: str = None) -> List[Dict]:
        """
        列出论文
        
        Args:
            status: 筛选状态
            
        Returns:
            论文列表
        """
        if status:
            return [p for p in self.papers.values() if p['status'] == status]
        return list(self.papers.values())


# ========== 便捷函数 ==========

def create_research_workflow(storage_dir: str = "research") -> ResearchWorkflow:
    """
    创建研究工作流
    """
    return ResearchWorkflow(storage_dir)


def create_version_manager(storage_dir: str = "research") -> FactorVersionManager:
    """
    创建版本管理器
    """
    return FactorVersionManager(storage_dir)


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 测试研究工作流模块")
    print("=" * 60)
    
    import shutil
    
    # 清理测试目录
    if Path("test_research").exists():
        shutil.rmtree("test_research")
    
    # 1. 测试研究记录
    print("\n1. 测试研究记录:")
    workflow = create_research_workflow("test_research")
    
    record = workflow.create_record(
        title="动量因子研究",
        factor_name="Momentum",
        author="researcher",
        hypothesis="动量因子具有正向预测能力",
        methodology="IC分析、分组回测"
    )
    print(f"   创建记录: {record.id}")
    print(f"   标题: {record.title}")
    print(f"   状态: {record.status}")
    
    # 2. 测试运行研究
    print("\n2. 测试运行研究:")
    
    def sample_research(record, **kwargs):
        # 模拟研究过程
        import time
        time.sleep(0.1)
        
        return {
            'ic': 0.05,
            'ic_ir': 0.8,
            'win_rate': 0.55,
            'long_short_return': 0.02
        }
    
    record = workflow.run_research(record.id, sample_research)
    print(f"   运行完成")
    print(f"   IC: {record.ic:.4f}")
    print(f"   胜率: {record.win_rate:.2%}")
    
    # 3. 测试版本管理
    print("\n3. 测试版本管理:")
    vm = create_version_manager("test_research")
    
    v1 = vm.create_version(
        factor_name="Momentum",
        version="1.0",
        code="class Momentum {...}",
        config={'period': 20},
        performance={'ic': 0.03}
    )
    print(f"   创建版本: {v1.id}")
    
    v2 = vm.create_version(
        factor_name="Momentum",
        version="1.1",
        code="class Momentum {...}",
        config={'period': 20, 'method': 'log'},
        performance={'ic': 0.05}
    )
    print(f"   创建版本: {v2.id}")
    
    versions = vm.get_versions("Momentum")
    print(f"   版本数: {len(versions)}")
    
    # 4. 测试论文复现
    print("\n4. 测试论文复现:")
    reproducer = PaperReproducer()
    
    reproducer.add_paper(
        paper_id="carhart_1997",
        title="On Persistence in Mutual Fund Performance",
        authors="Carhart",
        year=1997,
        url="https://...",
        abstract="研究共同基金的持续性..."
    )
    
    print(f"   添加论文: {len(reproducer.papers)} 篇")
    
    reproducer.link_factor(
        paper_id="carhart_1997",
        factor_name="Momentum_12m",
        config={'period': 12},
        notes="12个月动量"
    )
    
    factors = reproducer.get_paper_factors("carhart_1997")
    print(f"   关联因子: {len(factors)} 个")
    
    # 5. 列出记录
    print("\n5. 研究记录列表:")
    records = workflow.list_records(status="completed")
    print(f"   完成记录: {len(records)}")
    
    # 清理
    print("\n清理测试数据...")
    if Path("test_research").exists():
        shutil.rmtree("test_research")
    
    print("\n" + "=" * 60)
    print("✅ 研究工作流模块测试完成!")
    print("=" * 60)
