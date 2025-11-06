#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
State change listener (LAD-IMPL-008 基础实现)
负责接收 StatusChangeEvent，并将事件转换为结构化日志。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.enhanced_logger import EnhancedLogger
from core.error_code_manager import ErrorCodeManager
from core.performance_metrics import PerformanceMetrics


class StateChangeListener:
    """状态变更监听器（供 008 任务结构化日志使用）。"""

    def __init__(
        self,
        logger: EnhancedLogger,
        error_code_manager: Optional[ErrorCodeManager] = None,
        performance_metrics: Optional[PerformanceMetrics] = None,
    ) -> None:
        self.logger = logger
        self.error_code_manager = error_code_manager or ErrorCodeManager()
        self.performance_metrics = performance_metrics or PerformanceMetrics()
        self._last_events: Dict[str, Dict[str, Any]] = {}

    def __call__(self, event: Any) -> None:
        # 兼容 dataclass 与 dict
        if hasattr(event, "to_dict"):
            payload = event.to_dict()  # type: ignore[arg-type]
        elif isinstance(event, dict):
            payload = dict(event)
        else:
            payload = {"event": str(event)}

        event_type = payload.get("event_type", "unknown")
        correlation_id = payload.get("correlation_id")
        tracking_id = payload.get("tracking_id")
        change_reason = payload.get("change_reason")
        severity = payload.get("severity")
        metrics = payload.get("metrics", {})
        snapshot_key = payload.get("snapshot_key")
        session_id = payload.get("session_id")

        if correlation_id:
            self.logger.set_correlation_id(correlation_id, operation="state_change", component="ui")

        # 记录事件并缓存最近状态
        self.logger.log(
            "INFO",
            f"状态事件: {event_type}",
            operation="state_change",
            component="ui",
            tracking_id=tracking_id,
            change_reason=change_reason,
            severity=severity,
            event_payload=payload,
            snapshot_key=snapshot_key,
            session_id=session_id,
            metrics=metrics,
        )

        self._last_events[event_type] = payload

    def get_last_event(self, event_type: str) -> Optional[Dict[str, Any]]:
        return self._last_events.get(event_type)


__all__ = ["StateChangeListener"]

