#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Status events for UI status bar updates (thread-safe emitter)
"""

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, Dict, Any, List


@dataclass
class StatusChangeEvent:
    event_type: str
    component: str
    old_status: str
    new_status: str
    correlation_id: str = ""
    timestamp_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    metadata: Dict[str, Any] = field(default_factory=dict)
    tracking_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    snapshot_id: str = ""
    event_source: str = "ui"
    change_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """以dict形式返回事件，方便结构化日志或跨线程传递。"""
        return {
            "event_type": self.event_type,
            "component": self.component,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "correlation_id": self.correlation_id,
            "timestamp_ms": self.timestamp_ms,
            "metadata": self.metadata,
            "tracking_id": self.tracking_id,
            "snapshot_id": self.snapshot_id,
            "event_source": self.event_source,
            "change_reason": self.change_reason,
        }


class StatusEventEmitter:
    """Thread-safe event emitter with lock-out callbacks."""

    def __init__(self, max_history: int = 100) -> None:
        self._lock = threading.RLock()
        self._listeners: List[Callable[[StatusChangeEvent], None]] = []
        self._history: List[StatusChangeEvent] = []
        self._max_history = max_history

    def add_listener(self, fn: Callable[[StatusChangeEvent], None]) -> None:
        with self._lock:
            if fn not in self._listeners:
                self._listeners.append(fn)

    def remove_listener(self, fn: Callable[[StatusChangeEvent], None]) -> None:
        with self._lock:
            if fn in self._listeners:
                self._listeners.remove(fn)

    def clear_listeners(self) -> None:
        with self._lock:
            self._listeners.clear()

    def emit(self, event: StatusChangeEvent) -> None:
        with self._lock:
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history.pop(0)
            listeners = list(self._listeners)
        # 在锁外回调，避免死锁
        for fn in listeners:
            try:
                fn(event)
            except Exception:
                continue

    def get_history(self, limit: int = 50) -> List[StatusChangeEvent]:
        with self._lock:
            return list(self._history[-limit:])

    def get_listener_count(self) -> int:
        with self._lock:
            return len(self._listeners)

    def get_event_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return [event.to_dict() for event in self._history[-limit:]]


