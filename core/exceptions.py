"""
量化因子系统异常
QuantFactor System Exceptions

功能:
- 统一异常类型
- 异常处理装饰器
- 错误码定义
"""

from typing import Callable, Any
from functools import wraps
import traceback


# ==================== 异常基类 ====================

class QuantFactorError(Exception):
    """量化因子系统异常基类"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "QFS_UNKNOWN",
        details: dict = None,
        original_error: Exception = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.original_error = original_error
        
        # 记录完整traceback
        if original_error:
            self.traceback = traceback.format_exc()
        else:
            self.traceback = traceback.format_exc()
    
    def __str__(self):
        return f"[{self.error_code}] {self.message}"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details,
            'traceback': self.traceback
        }


# ==================== 具体异常类型 ====================

class DataError(QuantFactorError):
    """数据相关异常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="QFS_DATA",
            **kwargs
        )


class DatabaseError(QuantFactorError):
    """数据库相关异常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="QFS_DB",
            **kwargs
        )


class PipelineError(QuantFactorError):
    """Pipeline相关异常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="QFS_PIPELINE",
            **kwargs
        )


class FactorError(QuantFactorError):
    """因子计算异常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="QFS_FACTOR",
            **kwargs
        )


class ConfigurationError(QuantFactorError):
    """配置相关异常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="QFS_CONFIG",
            **kwargs
        )


# ==================== 错误码定义 ====================

ERROR_CODES = {
    # 数据错误
    "QFS_DATA_001": "数据为空",
    "QFS_DATA_002": "数据格式错误",
    "QFS_DATA_003": "数据缺失列",
    "QFS_DATA_004": "数据超出范围",
    "QFS_DATA_005": "数据重复",
    
    # 数据库错误
    "QFS_DB_001": "连接失败",
    "QFS_DB_002": "查询失败",
    "QFS_DB_003": "写入失败",
    "QFS_DB_004": "表不存在",
    "QFS_DB_005": "事务失败",
    
    # Pipeline错误
    "QFS_PIPELINE_001": "因子不存在",
    "QFS_PIPELINE_002": "循环依赖",
    "QFS_PIPELINE_003": "计算超时",
    "QFS_PIPELINE_004": "内存不足",
    
    # 因子错误
    "QFS_FACTOR_001": "因子参数无效",
    "QFS_FACTOR_002": "因子计算失败",
    "QFS_FACTOR_003": "因子名称冲突",
    "QFS_FACTOR_004": "因子未注册",
}


# ==================== 异常处理装饰器 ====================

class ErrorHandler:
    """异常处理器"""
    
    @staticmethod
    def handle(
        default_return: Any = None,
        log_errors: bool = True,
        reraise: bool = False
    ) -> Callable:
        """
        异常处理装饰器
        
        Args:
            default_return: 异常时返回的默认值
            log_errors: 是否记录错误
            reraise: 是否重新抛出异常
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                try:
                    return func(*args, **kwargs)
                except QuantFactorError:
                    raise
                except Exception as e:
                    if log_errors:
                        # 记录错误
                        from .logger import get_logger
                        logger = get_logger()
                        logger.error(f"异常 in {func.__name__}: {e}")
                    
                    if reraise:
                        raise QuantFactorError(
                            message=str(e),
                            original_error=e
                        )
                    
                    return default_return
            
            return wrapper
        return decorator


def safe_call(func: Callable, default_return: Any = None) -> Any:
    """
    安全调用函数
    
    Args:
        func: 要调用的函数
        default_return: 异常时返回的值
        
    Returns:
        函数返回值或默认值
    """
    try:
        return func()
    except Exception:
        return default_return


# ==================== 全局异常钩子 ====================

_exception_handlers = []


def add_exception_handler(handler: Callable[[QuantFactorError], None]):
    """添加异常处理器"""
    _exception_handlers.append(handler)


def remove_exception_handler(handler: Callable[[QuantFactorError], None]):
    """移除异常处理器"""
    if handler in _exception_handlers:
        _exception_handlers.remove(handler)


def _notify_handlers(error: QuantFactorError):
    """通知所有处理器"""
    for handler in _exception_handlers:
        try:
            handler(error)
        except Exception:
            pass  # 避免处理器自身出错


def handle_error(error: QuantFactorError):
    """处理异常"""
    _notify_handlers(error)
    
    # 打印错误
    from .logger import get_logger
    logger = get_logger()
    logger.error(f"[{error.error_code}] {error.message}")


# ==================== 便捷函数 ====================

def raise_data_error(message: str, **kwargs):
    """抛出数据异常"""
    raise DataError(message, **kwargs)


def raise_database_error(message: str, **kwargs):
    """抛出数据库异常"""
    raise DatabaseError(message, **kwargs)


def raise_pipeline_error(message: str, **kwargs):
    """抛出Pipeline异常"""
    raise PipelineError(message, **kwargs)


def raise_factor_error(message: str, **kwargs):
    """抛出因子异常"""
    raise FactorError(message, **kwargs)


# ==================== 导出 ====================

__all__ = [
    # 异常类
    'QuantFactorError',
    'DataError',
    'DatabaseError',
    'PipelineError',
    'FactorError',
    'ConfigurationError',
    
    # 错误码
    'ERROR_CODES',
    
    # 处理
    'ErrorHandler',
    'safe_call',
    'add_exception_handler',
    'handle_error',
    
    # 便捷函数
    'raise_data_error',
    'raise_database_error',
    'raise_pipeline_error',
    'raise_factor_error',
]
