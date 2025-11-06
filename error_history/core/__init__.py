# error_history/core/__init__.py
"""
错误历史持久化子系统 - 核心模块
"""

from .manager import ErrorHistoryManager
from .models import ErrorRecord, DailyStatistics, ErrorHistoryConfig, ErrorSeverity, ErrorCategory

__all__ = [
    'ErrorHistoryManager',
    'ErrorRecord',
    'DailyStatistics',
    'ErrorHistoryConfig',
    'ErrorSeverity',
    'ErrorCategory'
]
