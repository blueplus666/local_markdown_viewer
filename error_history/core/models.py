# error_history/core/models.py
"""
错误历史持久化子系统 - 数据模型
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from enum import Enum


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ErrorCategory(Enum):
    """错误分类"""
    UNKNOWN = "UNKNOWN"
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    VALIDATION = "VALIDATION"
    DATABASE = "DATABASE"
    NETWORK = "NETWORK"
    FILE_IO = "FILE_IO"
    MODULE_IMPORT = "MODULE_IMPORT"
    RENDERING = "RENDERING"
    CONFIGURATION = "CONFIGURATION"
    SYSTEM = "SYSTEM"
    LOGGING = "LOGGING"


@dataclass
class ErrorRecord:
    """错误记录数据模型"""
    id: Optional[int] = None
    error_id: str = ""
    error_type: str = ""
    error_message: str = ""
    severity: ErrorSeverity = ErrorSeverity.LOW
    category: ErrorCategory = ErrorCategory.UNKNOWN
    module: Optional[str] = None
    function: Optional[str] = None
    line_number: Optional[int] = None
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    user_context: Optional[Dict[str, Any]] = None
    system_context: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_method: Optional[str] = None
    resolution_time: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            'id': self.id,
            'error_id': self.error_id,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'severity': self.severity.value,
            'category': self.category.value,
            'module': self.module,
            'function': self.function,
            'line_number': self.line_number,
            'stack_trace': self.stack_trace,
            'resolved': self.resolved,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }

        # 处理可选字段
        if self.context:
            result['context'] = json.dumps(self.context, ensure_ascii=False)
        if self.user_context:
            result['user_context'] = json.dumps(self.user_context, ensure_ascii=False)
        if self.system_context:
            result['system_context'] = json.dumps(self.system_context, ensure_ascii=False)
        if self.created_at:
            result['created_at'] = self.created_at.isoformat()
        if self.resolved_at:
            result['resolved_at'] = self.resolved_at.isoformat()
        if self.resolution_method:
            result['resolution_method'] = self.resolution_method
        if self.resolution_time is not None:
            result['resolution_time'] = self.resolution_time
        if self.tags:
            result['tags'] = json.dumps(self.tags, ensure_ascii=False)
        if self.metadata:
            result['metadata'] = json.dumps(self.metadata, ensure_ascii=False)

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorRecord':
        """从字典创建对象"""
        # 解析JSON字段
        context = json.loads(data.get('context', '{}')) if data.get('context') else None
        user_context = json.loads(data.get('user_context', '{}')) if data.get('user_context') else None
        system_context = json.loads(data.get('system_context', '{}')) if data.get('system_context') else None
        tags = json.loads(data.get('tags', '[]')) if data.get('tags') else None
        metadata = json.loads(data.get('metadata', '{}')) if data.get('metadata') else None

        # 解析日期时间
        created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        resolved_at = datetime.fromisoformat(data['resolved_at']) if data.get('resolved_at') else None

        return cls(
            id=data.get('id'),
            error_id=data['error_id'],
            error_type=data['error_type'],
            error_message=data['error_message'],
            severity=ErrorSeverity(data['severity']),
            category=ErrorCategory(data['category']),
            module=data.get('module'),
            function=data.get('function'),
            line_number=data.get('line_number'),
            stack_trace=data.get('stack_trace'),
            context=context,
            user_context=user_context,
            system_context=system_context,
            created_at=created_at,
            resolved=data.get('resolved', False),
            resolved_at=resolved_at,
            resolution_method=data.get('resolution_method'),
            resolution_time=data.get('resolution_time'),
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3),
            tags=tags,
            metadata=metadata
        )

    @classmethod
    def from_error_info(cls, error_info) -> 'ErrorRecord':
        """从ErrorInfo对象创建ErrorRecord"""
        return cls(
            error_id=getattr(error_info, 'error_id', ''),
            error_type=getattr(error_info, 'error_type', ''),
            error_message=getattr(error_info, 'error_message', ''),
            severity=getattr(error_info, 'severity', ErrorSeverity.LOW),
            category=getattr(error_info, 'category', ErrorCategory.UNKNOWN),
            context={
                'module': getattr(error_info.context, 'module', None) if hasattr(error_info, 'context') and error_info.context else None,
                'function': getattr(error_info.context, 'function', None) if hasattr(error_info, 'context') and error_info.context else None,
                'line_number': getattr(error_info.context, 'line_number', None) if hasattr(error_info, 'context') and error_info.context else None,
                'stack_trace': getattr(error_info.context, 'stack_trace', None) if hasattr(error_info, 'context') and error_info.context else None,
            } if hasattr(error_info, 'context') and error_info.context else None,
            user_context=getattr(error_info.context, 'user_context', None) if hasattr(error_info, 'context') and error_info.context else None,
            system_context=getattr(error_info.context, 'system_context', None) if hasattr(error_info, 'context') and error_info.context else None,
            resolved=getattr(error_info, 'resolved', False),
            resolution_method=getattr(error_info, 'resolution_method', None),
            retry_count=getattr(error_info, 'retry_count', 0),
            max_retries=getattr(error_info, 'max_retries', 3)
        )


@dataclass
class DailyStatistics:
    """日统计数据模型"""
    date: date
    total_errors: int = 0
    errors_by_severity: Optional[Dict[str, int]] = None
    errors_by_category: Optional[Dict[str, int]] = None
    errors_by_module: Optional[Dict[str, int]] = None
    resolved_errors: int = 0
    unresolved_errors: int = 0
    avg_resolution_time: Optional[float] = None
    error_rate_per_hour: Optional[float] = None

    def __post_init__(self):
        if self.errors_by_severity is None:
            self.errors_by_severity = {}
        if self.errors_by_category is None:
            self.errors_by_category = {}
        if self.errors_by_module is None:
            self.errors_by_module = {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'date': self.date.isoformat(),
            'total_errors': self.total_errors,
            'errors_by_severity': json.dumps(self.errors_by_severity, ensure_ascii=False),
            'errors_by_category': json.dumps(self.errors_by_category, ensure_ascii=False),
            'errors_by_module': json.dumps(self.errors_by_module, ensure_ascii=False),
            'resolved_errors': self.resolved_errors,
            'unresolved_errors': self.unresolved_errors,
            'avg_resolution_time': self.avg_resolution_time,
            'error_rate_per_hour': self.error_rate_per_hour
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DailyStatistics':
        """从字典创建对象"""
        return cls(
            date=date.fromisoformat(data['date']),
            total_errors=data['total_errors'],
            errors_by_severity=json.loads(data.get('errors_by_severity', '{}')),
            errors_by_category=json.loads(data.get('errors_by_category', '{}')),
            errors_by_module=json.loads(data.get('errors_by_module', '{}')),
            resolved_errors=data['resolved_errors'],
            unresolved_errors=data['unresolved_errors'],
            avg_resolution_time=data.get('avg_resolution_time'),
            error_rate_per_hour=data.get('error_rate_per_hour')
        )


@dataclass
class ErrorHistoryConfig:
    """错误历史配置"""
    version: str = "1.0"
    enabled: bool = True

    # 数据库配置
    database_path: str = "data/error_history.db"
    max_connections: int = 5
    timeout_seconds: int = 30
    backup_enabled: bool = True
    backup_interval_hours: int = 24

    # 保留策略
    retention_days: int = 90
    auto_cleanup: bool = True
    cleanup_schedule: str = "0 2 * * *"  # 每天凌晨2点
    compression_enabled: bool = False

    # UI配置
    theme: str = "system"
    language: str = "zh-CN"
    page_size: int = 50
    auto_refresh_seconds: int = 30
    chart_colors: List[str] = field(default_factory=lambda: ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0"])

    # 监控配置
    alerts_enabled: bool = True
    error_rate_threshold: int = 10
    unresolved_threshold: int = 50
    alert_channels: List[str] = field(default_factory=lambda: ["log", "notification"])

    # 导出配置
    default_format: str = "json"
    supported_formats: List[str] = field(default_factory=lambda: ["json", "csv", "xlsx", "pdf"])
    max_export_rows: int = 10000

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'version': self.version,
            'enabled': self.enabled,
            'database': {
                'path': self.database_path,
                'max_connections': self.max_connections,
                'timeout_seconds': self.timeout_seconds,
                'backup_enabled': self.backup_enabled,
                'backup_interval_hours': self.backup_interval_hours
            },
            'retention': {
                'days': self.retention_days,
                'auto_cleanup': self.auto_cleanup,
                'cleanup_schedule': self.cleanup_schedule,
                'compression_enabled': self.compression_enabled
            },
            'ui': {
                'theme': self.theme,
                'language': self.language,
                'page_size': self.page_size,
                'auto_refresh_seconds': self.auto_refresh_seconds,
                'chart_colors': self.chart_colors
            },
            'monitoring': {
                'alerts_enabled': self.alerts_enabled,
                'error_rate_threshold': self.error_rate_threshold,
                'unresolved_threshold': self.unresolved_threshold,
                'alert_channels': self.alert_channels
            },
            'export': {
                'default_format': self.default_format,
                'supported_formats': self.supported_formats,
                'max_export_rows': self.max_export_rows
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorHistoryConfig':
        """从字典创建配置对象"""
        database = data.get('database', {})
        retention = data.get('retention', {})
        ui = data.get('ui', {})
        monitoring = data.get('monitoring', {})
        export_data = data.get('export', {})

        return cls(
            version=data.get('version', '1.0'),
            enabled=data.get('enabled', True),
            database_path=database.get('path', 'data/error_history.db'),
            max_connections=database.get('max_connections', 5),
            timeout_seconds=database.get('timeout_seconds', 30),
            backup_enabled=database.get('backup_enabled', True),
            backup_interval_hours=database.get('backup_interval_hours', 24),
            retention_days=retention.get('days', 90),
            auto_cleanup=retention.get('auto_cleanup', True),
            cleanup_schedule=retention.get('cleanup_schedule', '0 2 * * *'),
            compression_enabled=retention.get('compression_enabled', False),
            theme=ui.get('theme', 'system'),
            language=ui.get('language', 'zh-CN'),
            page_size=ui.get('page_size', 50),
            auto_refresh_seconds=ui.get('auto_refresh_seconds', 30),
            chart_colors=ui.get('chart_colors', ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0"]),
            alerts_enabled=monitoring.get('alerts_enabled', True),
            error_rate_threshold=monitoring.get('error_rate_threshold', 10),
            unresolved_threshold=monitoring.get('unresolved_threshold', 50),
            alert_channels=monitoring.get('alert_channels', ["log", "notification"]),
            default_format=export_data.get('default_format', 'json'),
            supported_formats=export_data.get('supported_formats', ["json", "csv", "xlsx", "pdf"]),
            max_export_rows=export_data.get('max_export_rows', 10000)
        )
