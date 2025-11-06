# error_history/ui/__init__.py
"""
错误历史持久化子系统 - UI模块
"""

from .main_window import ErrorHistoryMainWindow
from .query_panel import QueryPanel
from .stats_panel import StatsPanel
from .analysis_panel import AnalysisPanel
from .management_panel import ManagementPanel

__all__ = [
    'ErrorHistoryMainWindow',
    'QueryPanel',
    'StatsPanel',
    'AnalysisPanel',
    'ManagementPanel'
]
