import logging
from typing import Any, Dict, Optional

from core.enhanced_logger import EnhancedLogger


class SnapshotLogger:
    """为快照操作提供统一结构化日志接口。"""

    def __init__(self, logger: EnhancedLogger) -> None:
        self.logger = logger
        self._internal_logger = logging.getLogger(__name__)

    def log_operation(
        self,
        operation: str,
        snapshot_type: str,
        snapshot_key: str,
        correlation_id: Optional[str],
        **context: Any,
    ) -> None:
        try:
            self.logger.set_correlation_id(correlation_id, operation="snapshot_operation", component="snapshot_manager")
            self.logger.log_with_context(
                "DEBUG",
                f"快照操作: {operation} {snapshot_type}",
                operation="snapshot_operation",
                component="snapshot_manager",
                snapshot_operation=operation,
                snapshot_type=snapshot_type,
                snapshot_key=snapshot_key,
                **context,
            )
        except Exception as exc:
            self._internal_logger.warning("snapshot log failed: %s", exc)

    def log_consistency(
        self,
        snapshot_type: str,
        consistent: bool,
        correlation_id: Optional[str],
        **context: Any,
    ) -> None:
        try:
            self.logger.set_correlation_id(correlation_id, operation="consistency_check", component="snapshot_manager")
            level = "INFO" if consistent else "WARNING"
            self.logger.log_with_context(
                level,
                f"快照一致性检查: {snapshot_type} - {'通过' if consistent else '失败'}",
                operation="consistency_check",
                component="snapshot_manager",
                snapshot_type=snapshot_type,
                consistent=consistent,
                **context,
            )
        except Exception as exc:
            self._internal_logger.warning("snapshot consistency log failed: %s", exc)


__all__ = ["SnapshotLogger"]
