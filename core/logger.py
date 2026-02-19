"""
量化因子系统日志
QuantFactor System Logging

功能:
- 统一日志配置
- 多处理器支持
- 日志级别管理
- 格式化输出
"""

import logging
import sys
from typing import Optional
from pathlib import Path


class QuantLogger:
    """
    量化系统日志器
    
    特点:
    - 统一配置
    - 控制台 + 文件输出
    - 模块级别日志
    """
    
    _instances: dict = {}
    _default_handler: Optional[logging.Handler] = None
    
    def __init__(self, name: str = "QuantFactorSystem"):
        """
        初始化日志器
        
        Args:
            name: 日志器名称
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self._setup_default()
    
    def _setup_default(self):
        """设置默认配置"""
        self.logger.setLevel(logging.INFO)
        
        # 避免重复添加handler
        if not self.logger.handlers:
            # 控制台处理器
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            formatter = logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def set_level(self, level: str):
        """
        设置日志级别
        
        Args:
            level: DEBUG, INFO, WARNING, ERROR, CRITICAL
        """
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL,
        }
        
        level = level_map.get(level.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        for handler in self.logger.handlers:
            handler.setLevel(level)
    
    def add_file_handler(
        self,
        filepath: str,
        level: str = "INFO",
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        """
        添加文件处理器
        
        Args:
            filepath: 日志文件路径
            level: 日志级别
            max_bytes: 最大文件大小
            backup_count: 备份文件数量
        """
        # 确保目录存在
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # 创建处理器
        from logging.handlers import RotatingFileHandler
        handler = RotatingFileHandler(
            filepath,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        # 设置级别
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
        }
        handler.setLevel(level_map.get(level.upper(), logging.INFO))
        
        # 格式化
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
    
    def debug(self, msg: str, **kwargs):
        """DEBUG级别日志"""
        self.logger.debug(msg)
    
    def info(self, msg: str, **kwargs):
        """INFO级别日志"""
        self.logger.info(msg)
    
    def warning(self, msg: str, **kwargs):
        """WARNING级别日志"""
        self.logger.warning(msg)
    
    def error(self, msg: str, **kwargs):
        """ERROR级别日志"""
        self.logger.error(msg)
    
    def critical(self, msg: str, **kwargs):
        """CRITICAL级别日志"""
        self.logger.critical(msg)
    
    def log_performance(self, operation: str, duration: float, **kwargs):
        """记录性能日志"""
        self.logger.info(
            f"⏱️  {operation} | 耗时: {duration:.3f}s"
        )
    
    def log_data(self, operation: str, rows: int, **kwargs):
        """记录数据操作日志"""
        self.logger.info(
            f"📊 {operation} | 行数: {rows:,}"
        )
    
    def log_factor(self, name: str, status: str, **kwargs):
        """记录因子计算日志"""
        symbol = "✅" if status == "success" else "❌"
        self.logger.info(
            f"{symbol} 因子: {name} | 状态: {status}"
        )


# 全局日志器
_system_logger: Optional[QuantLogger] = None


def get_logger(name: str = "QuantFactorSystem") -> QuantLogger:
    """获取日志器"""
    global _system_logger
    
    if _system_logger is None:
        _system_logger = QuantLogger(name)
    
    return _system_logger


def setup_logger(
    level: str = "INFO",
    log_file: Optional[str] = None
) -> QuantLogger:
    """
    设置全局日志器
    
    Args:
        level: 日志级别
        log_file: 日志文件路径
    """
    global _system_logger
    
    _system_logger = QuantLogger("QuantFactorSystem")
    _system_logger.set_level(level)
    
    if log_file:
        _system_logger.add_file_handler(log_file, level)
    
    return _system_logger


# 便捷函数
def log_info(msg: str):
    """记录INFO日志"""
    get_logger().info(msg)


def log_error(msg: str):
    """记录ERROR日志"""
    get_logger().error(msg)


def log_performance(operation: str, duration: float):
    """记录性能日志"""
    get_logger().log_performance(operation, duration)


def log_data(operation: str, rows: int):
    """记录数据日志"""
    get_logger().log_data(operation, rows)
