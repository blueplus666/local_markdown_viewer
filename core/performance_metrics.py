#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能指标收集器模块 v1.0.0
LAD-IMPL-006A: 架构修正方案实施
基于006B V2.1简化配置架构

作者: LAD Team
创建时间: 2025-10-11
"""

import logging
import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING

from utils.config_manager import ConfigManager


if TYPE_CHECKING:
    from core.enhanced_logger import EnhancedLogger


class PerformanceMetrics:
    """性能指标收集与快照支持"""

    def __init__(self, config_manager: Optional[ConfigManager] = None) -> None:
        self.config_manager = config_manager or ConfigManager()
        
        logging_config = self.config_manager.get_unified_config("features.logging", {})
        metrics_config = logging_config.get("metrics", {})

        self._timers: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
        self._thresholds: Dict[str, Dict[str, Any]] = metrics_config.get("thresholds", {})
        self._listeners: List[Callable[[str, float, Dict[str, Any]], None]] = []

        self._snapshot_timer_limit = metrics_config.get("max_snapshot_timers", 50)
        self._snapshot_counter_limit = metrics_config.get("max_snapshot_counters", 50)
        self._snapshot_histogram_limit = metrics_config.get("max_snapshot_histograms", 20)
        self._snapshot_trim_mode = metrics_config.get("snapshot_timer_trim", "drop_oldest")
        self._snapshot_timer_keep_recent = metrics_config.get("timer_keep_recent", 50)

        self.logger = logging.getLogger(__name__)

    def register_threshold_listener(
        self, callback: Callable[[str, float, Dict[str, Any]], None]
    ) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def _notify_threshold(self, metric_name: str, value: float, metadata: Dict[str, Any]) -> None:
        for listener in list(self._listeners):
            try:
                listener(metric_name, value, metadata)
            except Exception as exc:
                self.logger.warning("性能阈值回调失败 %s: %s", metric_name, exc)

    def _check_threshold(self, metric_name: str, value: float, metadata: Dict[str, Any]) -> None:
        config = self._thresholds.get(metric_name)
        if not config:
            return
        threshold = config.get("max")
        min_threshold = config.get("min")
        warn_only = config.get("warn_only", False)

        triggered = False
        severity = "warning"

        if threshold is not None and value > threshold:
            triggered = True
            severity = config.get("severity_over", "warning")
            metadata.setdefault("threshold", threshold)
        if min_threshold is not None and value < min_threshold:
            triggered = True
            severity = config.get("severity_under", "warning")
            metadata.setdefault("threshold_min", min_threshold)

        if triggered:
            metadata.setdefault("severity", severity)
            metadata.setdefault("warn_only", warn_only)
            self._notify_threshold(metric_name, value, metadata)

    @contextmanager
    def start_timer_ctx(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.record_timer(name, duration, metadata=metadata or {})

    def start_timer(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        start = time.perf_counter()
        key = f"{name}_{int(time.time() * 1000)}"
        with self._lock:
            self._timers[key] = {
                "name": name,
                "duration": None,
                "metadata": metadata or {},
                "_start": start,
            }
        return key

    def end_timer(self, timer_id: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[float]:
        with self._lock:
            entry = self._timers.get(timer_id)
            if not entry or entry.get("duration") is not None:
                return None
            start = entry.pop("_start", None)
        if start is None:
            return None
        duration = time.perf_counter() - start
        final_meta = entry.get("metadata", {}).copy()
        if metadata:
            final_meta.update(metadata)
        self.record_timer(entry["name"], duration, metadata=final_meta)
        with self._lock:
            self._timers.pop(timer_id, None)
        return duration

    def record_timer(self, name: str, duration: float, metadata: Optional[Dict[str, Any]] = None) -> None:
        metadata = metadata or {}
        metadata.setdefault("captured_at", datetime.now(timezone.utc).isoformat())

        with self._lock:
            timer_key = f"{name}_{int(time.time() * 1000)}"
            self._timers[timer_key] = {
                "name": name,
                "duration": duration,
                "metadata": metadata,
            }

            if len(self._timers) > self._snapshot_timer_limit:
                if self._snapshot_trim_mode == "keep_recent":
                    keys_to_keep = list(self._timers.keys())[-self._snapshot_timer_keep_recent :]
                    self._timers = OrderedDict((k, self._timers[k]) for k in keys_to_keep)
                elif self._snapshot_trim_mode == "ignore":
                    self._timers.pop(timer_key, None)
                else:
                    self._timers.popitem(last=False)

        self._check_threshold(name, duration, metadata)

    def increment_counter(self, name: str, value: int = 1, metadata: Optional[Dict[str, Any]] = None) -> None:
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + value
            self._trim_map(self._counters, self._snapshot_counter_limit)
            current = self._counters[name]
        self._check_threshold(name, float(current), metadata or {})

    def set_gauge(self, name: str, value: float, metadata: Optional[Dict[str, Any]] = None) -> None:
        with self._lock:
            self._gauges[name] = value
        self._check_threshold(name, value, metadata or {})

    def record_histogram(self, name: str, value: float, metadata: Optional[Dict[str, Any]] = None) -> None:
        with self._lock:
            self._histograms.setdefault(name, []).append(value)
            if len(self._histograms[name]) > self._snapshot_histogram_limit:
                self._histograms[name].pop(0)
        self._check_threshold(name, value, metadata or {})

    def record_module_update(self, module_name: str, status: Dict[str, Any]) -> None:
        self.increment_counter(f"module_updates.{module_name}")
        self.set_gauge("last_module_update_ts", time.time())

    def record_render_update(self, status: Dict[str, Any]) -> None:
        renderer_type = status.get("renderer_type", "unknown")
        self.increment_counter(f"render_updates.{renderer_type}")
        self.set_gauge("last_render_update_ts", time.time())

    def record_link_update(self, status: Dict[str, Any]) -> None:
        result = status.get("last_result", "unknown")
        self.increment_counter(f"link_updates.{result}")
        self.set_gauge("last_link_update_ts", time.time())

    def _trim_map(self, mapping: Dict[str, Any], limit: int) -> None:
        if len(mapping) > limit:
            for key in list(mapping.keys())[:-limit]:
                mapping.pop(key, None)

    def get_metrics_snapshot(
        self,
        include_timers: bool = True,
        include_counters: bool = True,
        include_gauges: bool = True,
        include_histograms: bool = False,
    ) -> Dict[str, Any]:
        with self._lock:
            snapshot: Dict[str, Any] = {}

            if include_timers:
                timers_items = list(self._timers.items())[-self._snapshot_timer_keep_recent :]
                snapshot["timers"] = OrderedDict(timers_items)

            if include_counters:
                snapshot["counters"] = dict(self._counters)

            if include_gauges:
                snapshot["gauges"] = dict(self._gauges)

            if include_histograms:
                snapshot["histograms"] = {k: list(v) for k, v in self._histograms.items()}

            return snapshot


class PerformanceThresholdMonitor:
    """将性能指标超限与日志器联动的辅助器。"""

    def __init__(self, metrics: PerformanceMetrics, logger: "EnhancedLogger") -> None:
        self.metrics = metrics
        self.logger = logger
        self.metrics.register_threshold_listener(self._on_threshold_triggered)

    def _on_threshold_triggered(self, metric_name: str, value: float, metadata: Dict[str, Any]) -> None:
        severity = metadata.get("severity", "warning").upper()
        threshold = metadata.get("threshold") or metadata.get("threshold_min")
        warn_only = metadata.get("warn_only", False)
        message = (
            f"性能阈值触发: {metric_name}={value:.4f}"
            + (f" 阈值={threshold}" if threshold is not None else "")
        )
        logger_level = "WARNING" if warn_only else severity
        self.logger.log_with_context(
            logger_level,
            message,
            operation="performance_check",
            component=metadata.get("component", "performance_monitor"),
            metric_name=metric_name,
            metric_value=value,
            threshold=threshold,
            severity=severity,
            threshold_direction="max" if "threshold" in metadata else "min",
            metadata=metadata,
        )












