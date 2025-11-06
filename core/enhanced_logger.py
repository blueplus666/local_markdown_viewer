"""
增强日志记录器（LAD-IMPL-008 起步实现）
结构化日志输出、模板化日志、关联ID传递、性能数据聚合。
"""

import json
import logging
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from core.performance_metrics import PerformanceMetrics
from utils.config_manager import ConfigManager


LOG_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "status_update": {
        "level": "INFO",
        "operation": "status_bar_update",
        "component": "ui",
        "message_template": "状态栏更新成功: {status_message}",
        "required_fields": ["status_message"]
    },
    "status_update_slow": {
        "level": "WARNING",
        "operation": "status_bar_update",
        "component": "ui",
        "message_template": "状态栏刷新耗时 {duration_ms}ms 超过阈值 {threshold_ms}ms",
        "required_fields": ["duration_ms", "threshold_ms"]
    },
    "module_import_start": {
        "level": "INFO",
        "operation": "module_import",
        "component": "dynamic_module_importer",
        "message_template": "开始导入模块 {module_name}",
        "required_fields": ["module_name"]
    },
    "module_import_cache_hit": {
        "level": "INFO",
        "operation": "module_import",
        "component": "dynamic_module_importer",
        "message_template": "模块 {module_name} 从缓存命中，跳过重新导入",
        "required_fields": ["module_name"]
    },
    "module_import_success": {
        "level": "INFO",
        "operation": "module_import",
        "component": "dynamic_module_importer",
        "message_template": "模块 {module_name} 通过 {import_method} 导入成功，耗时 {duration_ms}ms",
        "required_fields": ["module_name", "import_method", "duration_ms"]
    },
    "module_import_failure": {
        "level": "ERROR",
        "operation": "module_import",
        "component": "dynamic_module_importer",
        "message_template": "模块 {module_name} 通过 {import_method} 导入失败，错误码 {error_code}: {error_message}",
        "required_fields": ["module_name", "import_method", "error_code", "error_message"]
    },
    "module_import_fallback": {
        "level": "WARNING",
        "operation": "module_import",
        "component": "dynamic_module_importer",
        "message_template": "模块 {module_name} 使用 fallback {fallback_name}，结果 {fallback_status}",
        "required_fields": ["module_name", "fallback_name", "fallback_status"]
    },
    "module_config_source_attempt": {
        "level": "INFO",
        "operation": "module_import",
        "component": "dynamic_module_importer",
        "message_template": "模块配置尝试从 {source} 加载",
        "required_fields": ["source"]
    },
    "module_config_loaded": {
        "level": "INFO",
        "operation": "module_import",
        "component": "dynamic_module_importer",
        "message_template": "模块 {module_name} （来源 {source}） 配置加载成功，路径 {module_path}",
        "required_fields": ["module_name", "source", "module_path"]
    },
    "module_config_summary": {
        "level": "INFO",
        "operation": "module_import",
        "component": "dynamic_module_importer",
        "message_template": "已加载 {module_count} 个模块配置",
        "required_fields": ["module_count"]
    },
    "module_config_summary_item": {
        "level": "INFO",
        "operation": "module_import",
        "component": "dynamic_module_importer",
        "message_template": "配置模块 {module_name} 路径 {module_path} 优先级 {priority}",
        "required_fields": ["module_name", "module_path", "priority"]
    },
    "module_config_missing": {
        "level": "WARNING",
        "operation": "module_import",
        "component": "dynamic_module_importer",
        "message_template": "未加载到模块配置",
        "required_fields": []
    },
    "module_config_error": {
        "level": "ERROR",
        "operation": "module_import",
        "component": "dynamic_module_importer",
        "message_template": "模块配置加载异常: {error}",
        "required_fields": ["error"]
    },
    "module_import_path_attempt": {
        "level": "INFO",
        "operation": "module_import",
        "component": "dynamic_module_importer",
        "message_template": "模块 {module_name} 尝试通过路径 {module_path} 导入",
        "required_fields": ["module_name", "module_path"]
    },
    "module_import_path_missing": {
        "level": "ERROR",
        "operation": "module_import",
        "component": "dynamic_module_importer",
        "message_template": "模块 {module_name} 路径不存在: {module_path}",
        "required_fields": ["module_name", "module_path"]
    },
    "module_import_path_failure": {
        "level": "WARNING",
        "operation": "module_import",
        "component": "dynamic_module_importer",
        "message_template": "模块 {module_name} 从路径 {module_path} 导入失败，错误码 {error_code}: {error_message}",
        "required_fields": ["module_name", "module_path", "error_code", "error_message"]
    },
    "module_import_fallback_start": {
        "level": "INFO",
        "operation": "module_import",
        "component": "dynamic_module_importer",
        "message_template": "模块 {module_name} 启动 fallback 序列: {fallbacks}",
        "required_fields": ["module_name", "fallbacks"]
    },
    "module_import_fallback_attempt": {
        "level": "INFO",
        "operation": "module_import",
        "component": "dynamic_module_importer",
        "message_template": "模块 {module_name} 尝试 fallback {fallback_name}",
        "required_fields": ["module_name", "fallback_name"]
    },
    "module_import_fallback_failure": {
        "level": "ERROR",
        "operation": "module_import",
        "component": "dynamic_module_importer",
        "message_template": "模块 {module_name} fallback {fallback_name} 导入失败: {error_message}",
        "required_fields": ["module_name", "fallback_name", "error_message"]
    },
    "module_import_validation": {
        "level": "INFO",
        "operation": "module_import",
        "component": "dynamic_module_importer",
        "message_template": "模块 {module_name} 验证必需函数: {required_functions}",
        "required_fields": ["module_name", "required_functions"]
    },
    "module_import_validation_failed": {
        "level": "ERROR",
        "operation": "module_import",
        "component": "dynamic_module_importer",
        "message_template": "模块 {module_name} 函数映射验证失败: {details}",
        "required_fields": ["module_name", "details"]
    },
    "module_import_validation_success": {
        "level": "INFO",
        "operation": "module_import",
        "component": "dynamic_module_importer",
        "message_template": "模块 {module_name} 验证通过，路径 {module_path}，可用函数 {available_functions}",
        "required_fields": ["module_name", "module_path", "available_functions"]
    }
}


class EnhancedLogger:
    """基础结构化日志器，支持配置驱动、性能数据及错误码扩展。"""

    _SESSION_PREFIX = "LAD"
    _DEFAULT_LEVEL = "INFO"

    def __init__(
        self,
        name: str,
        config_manager: Optional[ConfigManager] = None,
        performance_metrics: Optional[PerformanceMetrics] = None,
        error_code_manager: Optional["ErrorCodeManager"] = None,
    ) -> None:
        try:
            from core.error_code_manager import ErrorCodeManager
        except ImportError:  # 延迟导入失败时的兜底，避免循环依赖崩溃
            ErrorCodeManager = None  # type: ignore

        self.logger = logging.getLogger(name)
        self.config_manager = config_manager or ConfigManager()
        try:
            self.performance_metrics = performance_metrics or PerformanceMetrics(self.config_manager)
        except Exception:
            self.performance_metrics = None
        if error_code_manager is not None:
            self.error_code_manager = error_code_manager
        else:
            self.error_code_manager = None

        self.correlation_id: Optional[str] = None
        self.operation: Optional[str] = None
        self.component: Optional[str] = None
        self.session_id: str = self._generate_session_id()
        self._lock = threading.RLock()

        logging_cfg = self.config_manager.get_unified_config("features.logging", {})
        level = logging_cfg.get("level", self._DEFAULT_LEVEL).upper()
        self.logger.setLevel(getattr(logging, level, logging.INFO))

        self.config_manager.add_change_listener(self._on_config_changed)

    def _generate_session_id(self) -> str:
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y%m%d%H%M%S")
        suffix = uuid.uuid4().hex[:8]
        return f"{self._SESSION_PREFIX}_{timestamp}_{suffix}"

    def _on_config_changed(self, key: str, value: Any) -> None:
        if key.startswith("features.logging"):
            log_config = self.config_manager.get_unified_config("features.logging", {})
            level = log_config.get("level", self._DEFAULT_LEVEL).upper()
            self.logger.setLevel(getattr(logging, level, logging.INFO))

    def set_correlation_id(
        self,
        correlation_id: Optional[str],
        operation: Optional[str] = None,
        component: Optional[str] = None,
    ) -> None:
        with self._lock:
            self.correlation_id = correlation_id
            if operation:
                self.operation = operation
            if component:
                self.component = component

    def _build_log_record(
        self,
        level: str,
        message: str,
        operation: Optional[str],
        component: Optional[str],
        context: Dict[str, Any],
        error_code: Optional[str],
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        record_operation = operation or self.operation
        record_component = component or self.component

        record: Dict[str, Any] = {
            "timestamp": now.isoformat(),
            "level": level.upper(),
            "logger": self.logger.name,
            "message": message,
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "operation": record_operation,
            "component": record_component,
            "details": context or {},
        }

        if self.performance_metrics:
            record["metrics"] = self.performance_metrics.get_metrics_snapshot(
                include_timers=False,
                include_counters=True,
                include_gauges=True,
                include_histograms=False,
            )

        if error_code:
            try:
                if getattr(self, "error_code_manager", None) is not None:
                    error_payload = self.error_code_manager.format_error(
                        context.get("error_category", "system"),
                        error_code,
                        context.get("error_details"),
                    )
                    record.update({
                        "error_code": error_payload.get("code"),
                        "error_message": error_payload.get("message"),
                        "error_category": error_payload.get("category"),
                        "error_details": error_payload.get("details"),
                    })
                else:
                    record.update({
                        "error_code": str(error_code),
                        "error_message": context.get("error_message", ""),
                        "error_category": context.get("error_category", "system"),
                        "error_details": context.get("error_details"),
                    })
            except Exception:
                record.update({
                    "error_code": str(error_code),
                    "error_message": context.get("error_message", ""),
                    "error_category": context.get("error_category", "system"),
                    "error_details": context.get("error_details"),
                })

        record.setdefault("tracking_id", context.get("tracking_id") or uuid.uuid4().hex)
        record.setdefault("event_source", context.get("event_source", "system"))
        record.setdefault("timestamp_ms", context.get("timestamp_ms", int(time.time() * 1000)))
        return record

    def log(
        self,
        level: str,
        message: str,
        operation: Optional[str] = None,
        component: Optional[str] = None,
        error_code: Optional[str] = None,
        **context: Any,
    ) -> None:
        with self._lock:
            normalized_context = dict(context)
            record = self._build_log_record(level, message, operation, component, normalized_context, error_code)
            level_value = getattr(logging, level.upper(), logging.INFO)
            self.logger.log(level_value, json.dumps(record, ensure_ascii=False))

    def log_with_context(
        self,
        level: str,
        message: str,
        operation: Optional[str] = None,
        component: Optional[str] = None,
        error_code: Optional[str] = None,
        **context: Any,
    ) -> None:
        self.log(level, message, operation, component, error_code, **context)

    # --- 兼容标准logging接口 ---
    def debug(self, message: str, **context: Any) -> None:
        self.log("DEBUG", message, **context)

    def info(self, message: str, **context: Any) -> None:
        self.log("INFO", message, **context)

    def warning(self, message: str, **context: Any) -> None:
        self.log("WARNING", message, **context)

    def error(self, message: str, **context: Any) -> None:
        self.log("ERROR", message, **context)

    def critical(self, message: str, **context: Any) -> None:
        self.log("CRITICAL", message, **context)

    def exception(self, message: str, **context: Any) -> None:
        context.setdefault("exc_info", True)
        self.log("ERROR", message, **context)


class TemplatedLogger(EnhancedLogger):
    """提供模板化日志能力。"""

    def __init__(self, name: str, templates: Optional[Dict[str, Dict[str, Any]]] = None,
                 **kwargs):
        super().__init__(name, **kwargs)
        self.templates = templates or LOG_TEMPLATES

    def log_from_template(self, template_name: str, **context: Any) -> None:
        template = self.templates.get(template_name)
        if not template:
            self.log("WARNING", f"未知日志模板: {template_name}")
            return
        missing = [field for field in template.get("required_fields", []) if field not in context]
        if missing:
            self.log("ERROR", f"日志模板 {template_name} 缺少字段: {missing}")
            return
        message = template.get("message_template", "").format(**context)
        level = template.get("level", "INFO")
        operation = template.get("operation", context.get("operation"))
        component = template.get("component", context.get("component"))
        context.setdefault("template_name", template_name)
        # 兼容：避免同时以位置参数与关键字参数传递 error_code 导致 TypeError
        error_code = context.pop("error_code", template.get("error_code"))
        self.log(level, message, operation, component, error_code, **context)
