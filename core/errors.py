"""
核心错误与严重性等级的最小定义。

用途：
- 在架构文档与示例代码中被引用（例如错误处理、文件读取、服务注册表）
- 作为统一的错误类型入口，避免到处定义零散异常

使用建议：
- 业务侧可在此文件上扩展更多领域异常，但保持最小依赖
"""
from enum import Enum


class ErrorSeverity(Enum):
    """错误严重性等级的统一枚举，用于日志与告警分级。"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ServiceNotFoundError(Exception):
    """服务注册表未找到目标服务时抛出。"""
    pass


class FileReadError(Exception):
    """文件读取失败（权限/编码/不存在等）时抛出。"""
    pass