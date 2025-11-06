#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SnapshotManager v1.1.0
按照《第1份-架构修正方案》定义的schema统一管理模块导入、渲染与链接快照。

主要能力：
- 提供线程安全的快照读写接口
- 使用 UnifiedCacheManager 进行落盘缓存，支持进程重启恢复
- 维护 correlation_id 与时间戳，支持后续 008 任务的日志/性能关联
- 与 PerformanceMetrics 协同，记录快照写入次数
"""

from __future__ import annotations

import json
import threading
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from utils.config_manager import ConfigManager
from core.correlation_id_manager import CorrelationIdManager
from core.performance_metrics import PerformanceMetrics

try:
    from core.unified_cache_manager import (
        UnifiedCacheManager,
        CacheStrategy,
        CacheStats,
    )
except ImportError:  # pragma: no cover - 向后兼容
    from .unified_cache_manager import (  # type: ignore
        UnifiedCacheManager,
        CacheStrategy,
        CacheStats,
    )


MODULE_SNAPSHOT_FIELDS = {
    "snapshot_type": "module_import_snapshot",
    "module": "",
    "function_mapping_status": "unknown",
    "required_functions": [],
    "available_functions": [],
    "missing_functions": [],
    "non_callable_functions": [],
    "path": "",
    "used_fallback": False,
    "error_code": "",
    "message": "",
    "timestamp": "",
    "correlation_id": "",
}

RENDER_SNAPSHOT_FIELDS = {
    "snapshot_type": "render_snapshot",
    "renderer_type": "unknown",
    "reason": "unknown",
    "details": {},
    "timestamp": "",
    "correlation_id": "",
}

LINK_SNAPSHOT_FIELDS = {
    "snapshot_type": "link_snapshot",
    "link_processor_loaded": False,
    "policy_profile": "default",
    "last_action": "none",
    "last_result": "unknown",
    "details": {},
    "error_code": "",
    "message": "",
    "timestamp": "",
    "correlation_id": "",
}


class SnapshotManager:
    """线程安全的快照管理器。"""

    _MODULE_CACHE_PREFIX = "snapshot:module:"
    _RENDER_CACHE_KEY = "snapshot:render"
    _LINK_CACHE_KEY = "snapshot:link"

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        cache_manager: Optional[UnifiedCacheManager] = None,
        performance_metrics: Optional[PerformanceMetrics] = None,
        correlation_manager: Optional[CorrelationIdManager] = None,
    ) -> None:
        self.config_manager = config_manager or ConfigManager()
        self.correlation_manager = correlation_manager or CorrelationIdManager()
        self.performance_metrics = performance_metrics or PerformanceMetrics(self.config_manager)

        cache_dir = Path(__file__).parent.parent / "cache" / "snapshots"
        cache_dir.mkdir(parents=True, exist_ok=True)

        self.cache_manager = cache_manager or UnifiedCacheManager(
            max_size=512,
            default_ttl=None,
            strategy=CacheStrategy.LRU,
            cache_dir=cache_dir,
        )

        self._lock = threading.RLock()
        self._module_snapshots: Dict[str, Dict[str, Any]] = {}
        self._render_snapshot: Dict[str, Any] = {}
        self._link_snapshot: Dict[str, Any] = {}

        self._load_cached_snapshots()

    def set_cache_manager(self, cache_manager: UnifiedCacheManager) -> bool:
        with self._lock:
            self.cache_manager = cache_manager
        return True

    # ------------------------------------------------------------------
    # 公共 API：模块快照
    # ------------------------------------------------------------------
    def save_module_snapshot(self, module_name: str, data: Dict[str, Any]) -> bool:
        """保存模块导入快照。返回是否写入成功。"""
        normalized = self._normalize_module_snapshot(module_name, data)
        with self._lock:
            self._module_snapshots[module_name] = normalized
            self._persist_cache(self._module_cache_key(module_name), normalized)
            self._record_metric("snapshot.module_saved")
        return True

    def get_module_snapshot(self, module_name: str) -> Dict[str, Any]:
        """获取模块导入快照，若不存在则返回默认结构。"""
        with self._lock:
            snapshot = self._module_snapshots.get(module_name)
            if snapshot is None:
                snapshot = deepcopy(MODULE_SNAPSHOT_FIELDS)
                snapshot["module"] = module_name
            return deepcopy(snapshot)

    def delete_module_snapshot(self, module_name: str) -> None:
        with self._lock:
            self._module_snapshots.pop(module_name, None)
            self.cache_manager.delete(self._module_cache_key(module_name))

    def get_cache_stats(self) -> Optional[CacheStats]:
        """返回底层缓存统计信息（如不可用则None）。"""
        try:
            return self.cache_manager.get_stats()
        except Exception:
            return None

    def get_all_module_snapshots(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return deepcopy(self._module_snapshots)

    # ------------------------------------------------------------------
    # 公共 API：渲染快照
    # ------------------------------------------------------------------
    def save_render_snapshot(self, data: Dict[str, Any]) -> bool:
        normalized = self._normalize_render_snapshot(data)
        with self._lock:
            self._render_snapshot = normalized
            self._persist_cache(self._RENDER_CACHE_KEY, normalized)
            self._record_metric("snapshot.render_saved")
        return True

    def get_render_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            snapshot = self._render_snapshot or deepcopy(RENDER_SNAPSHOT_FIELDS)
            return deepcopy(snapshot)

    # ------------------------------------------------------------------
    # 公共 API：链接快照
    # ------------------------------------------------------------------
    def save_link_snapshot(self, data: Dict[str, Any]) -> bool:
        normalized = self._normalize_link_snapshot(data)
        with self._lock:
            self._link_snapshot = normalized
            self._persist_cache(self._LINK_CACHE_KEY, normalized)
            self._record_metric("snapshot.link_saved")
        return True

    def get_link_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            snapshot = self._link_snapshot or deepcopy(LINK_SNAPSHOT_FIELDS)
            return deepcopy(snapshot)

    # ------------------------------------------------------------------
    # 辅助能力
    # ------------------------------------------------------------------
    def get_snapshot_summary(self) -> Dict[str, Any]:
        """提供快照数量、最后更新时间等信息，便于调试。"""
        with self._lock:
            modules = {k: v.get("timestamp", "") for k, v in self._module_snapshots.items()}
            render_ts = self._render_snapshot.get("timestamp")
            link_ts = self._link_snapshot.get("timestamp")
            cache_stats: Optional[CacheStats] = None
            try:
                cache_stats = self.cache_manager.get_stats()
            except Exception:
                cache_stats = None
        return {
            "module_count": len(modules),
            "module_timestamps": modules,
            "render_timestamp": render_ts,
            "link_timestamp": link_ts,
            "cache": cache_stats.to_dict() if cache_stats else None,
        }

    def clear_all_snapshots(self) -> None:
        with self._lock:
            self._module_snapshots.clear()
            self._render_snapshot.clear()
            self._link_snapshot.clear()
            self.cache_manager.clear()

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------
    def _normalize_module_snapshot(self, module_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        snapshot = deepcopy(MODULE_SNAPSHOT_FIELDS)
        snapshot.update(deepcopy(data or {}))
        snapshot["snapshot_type"] = "module_import_snapshot"
        snapshot["module"] = module_name or snapshot.get("module") or "unknown"
        snapshot["timestamp"] = snapshot.get("timestamp") or self._utc_iso()
        snapshot["correlation_id"] = snapshot.get("correlation_id") or self._current_correlation("module")
        self._ensure_list_fields(snapshot, [
            "required_functions",
            "available_functions",
            "missing_functions",
            "non_callable_functions",
        ])
        return snapshot

    def _normalize_render_snapshot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        snapshot = deepcopy(RENDER_SNAPSHOT_FIELDS)
        snapshot.update(deepcopy(data or {}))
        snapshot["snapshot_type"] = "render_snapshot"
        snapshot["timestamp"] = snapshot.get("timestamp") or self._utc_iso()
        snapshot["details"] = deepcopy(snapshot.get("details") or {})
        snapshot["correlation_id"] = snapshot.get("correlation_id") or self._current_correlation("render")
        return snapshot

    def _normalize_link_snapshot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        snapshot = deepcopy(LINK_SNAPSHOT_FIELDS)
        snapshot.update(deepcopy(data or {}))
        snapshot["snapshot_type"] = "link_snapshot"
        snapshot["timestamp"] = snapshot.get("timestamp") or self._utc_iso()
        snapshot["details"] = deepcopy(snapshot.get("details") or {})
        snapshot["correlation_id"] = snapshot.get("correlation_id") or self._current_correlation("link")
        return snapshot

    def _load_cached_snapshots(self) -> None:
        with self._lock:
            keys = list(self.cache_manager.iter_keys()) if hasattr(self.cache_manager, "iter_keys") else []
            for key in keys:
                value = self.cache_manager.get(key)
                if key.startswith(self._MODULE_CACHE_PREFIX):
                    module_name = key[len(self._MODULE_CACHE_PREFIX) :]
                    if isinstance(value, dict):
                        self._module_snapshots[module_name] = value
                elif key == self._RENDER_CACHE_KEY and isinstance(value, dict):
                    self._render_snapshot = value
                elif key == self._LINK_CACHE_KEY and isinstance(value, dict):
                    self._link_snapshot = value

    def _persist_cache(self, key: str, snapshot: Dict[str, Any]) -> None:
        try:
            serializable = json.loads(json.dumps(snapshot, ensure_ascii=False))
            self.cache_manager.set(key, serializable)
        except Exception:
            # 持久化失败时忽略，但保持内存快照
            pass

    def _module_cache_key(self, module_name: str) -> str:
        return f"{self._MODULE_CACHE_PREFIX}{module_name}"

    def _record_metric(self, name: str) -> None:
        try:
            self.performance_metrics.increment_counter(name)
        except Exception:
            pass

    def _ensure_list_fields(self, snapshot: Dict[str, Any], fields: Any) -> None:
        for field in fields:
            value = snapshot.get(field)
            if not isinstance(value, list):
                snapshot[field] = list(value) if value else []

    def _utc_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _current_correlation(self, component: str) -> str:
        try:
            cid = self.correlation_manager.get_current_correlation_id(component)
            return cid or ""
        except Exception:
            return ""


__all__ = ["SnapshotManager"]














