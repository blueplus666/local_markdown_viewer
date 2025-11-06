# error_history/integration/__init__.py
"""
错误历史持久化子系统 - 集成模块
"""

from .main_integration import (
    ErrorHistoryIntegration,
    create_error_history_integration,
    open_error_history_ui,
    integrate_error_history_with_main_app,
    run_error_history_standalone
)

__all__ = [
    'ErrorHistoryIntegration',
    'create_error_history_integration',
    'open_error_history_ui',
    'integrate_error_history_with_main_app',
    'run_error_history_standalone'
]
