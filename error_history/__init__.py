# error_history/__init__.py
"""
错误历史持久化子系统

这是一个独立的子系统，用于管理本地Markdown文件渲染器的错误历史数据，
提供持久化存储、查询分析和可视化展示功能。
"""

__version__ = "1.0.0"
__author__ = "LAD AI Assistant"
__description__ = "错误历史持久化子系统"

# 导入主要组件
from .core.manager import ErrorHistoryManager
from .core.models import ErrorRecord, ErrorHistoryConfig, ErrorSeverity, ErrorCategory
from .ui.main_window import ErrorHistoryMainWindow
from .integration.main_integration import (
    ErrorHistoryIntegration,
    create_error_history_integration,
    open_error_history_ui,
    integrate_error_history_with_main_app,
    run_error_history_standalone
)

# 便捷访问
__all__ = [
    # 核心组件
    'ErrorHistoryManager',
    'ErrorRecord',
    'ErrorHistoryConfig',
    'ErrorSeverity',
    'ErrorCategory',

    # UI组件
    'ErrorHistoryMainWindow',

    # 集成组件
    'ErrorHistoryIntegration',
    'create_error_history_integration',
    'open_error_history_ui',
    'integrate_error_history_with_main_app',
    'run_error_history_standalone',
]
