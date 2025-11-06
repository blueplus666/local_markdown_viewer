#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CorrelationIdManager v1.0.0
线程安全的Correlation ID管理器（单例）
ID格式：operation_component_timestamp_random
"""

import threading
import time
import secrets
from typing import Optional, Dict


class CorrelationIdManager:
    """
    生成、传播与管理Correlation ID的单例类。
    - generate_correlation_id: 生成符合规范的ID
    - set_current_correlation_id/get_current_correlation_id/clear_current_correlation_id: 按组件存取
    - parse_correlation_id: 解析ID为结构化字段
    """

    _instance = None
    _instance_lock = threading.Lock()
    _id_metadata: Dict[str, Dict[str, str]] = {}

    def __new__(cls):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    # 内部初始化仅执行一次
                    cls._instance._init_singleton()
        return cls._instance

    def _init_singleton(self) -> None:
        self._lock = threading.RLock()
        self._component_to_correlation_id: Dict[str, str] = {}

    # === 生成/设置/获取/清理 ===
    @classmethod
    def generate_correlation_id(cls, operation: str, component: str = "") -> str:
        """生成形如 operation_component_timestamp_random 的ID。"""
        ts = int(time.time() * 1000)
        rnd = secrets.token_hex(4)
        op = (operation or "op").replace(" ", "_")
        if component:
            comp = component.replace(" ", "_")
            cid = f"{op}_{comp}_{ts}_{rnd}"
        else:
            cid = f"{op}_{ts}_{rnd}"
        with cls._instance_lock:
            cls._id_metadata[cid] = {
                "operation_type": operation,
                "component": component,
                "timestamp": str(ts),
                "random_suffix": rnd,
            }
        return cid

    @classmethod
    def parse_correlation_id(cls, correlation_id: str) -> Dict[str, str]:
        """允许通过类调用解析ID。"""
        if cls._instance is None:
            cls()
        return cls._instance._parse_correlation_id_internal(correlation_id)

    def set_current_correlation_id(self, component: str, correlation_id: str) -> None:
        with self._lock:
            if component:
                self._component_to_correlation_id[component] = correlation_id

    def get_current_correlation_id(self, component: str) -> Optional[str]:
        with self._lock:
            return self._component_to_correlation_id.get(component)

    def clear_current_correlation_id(self, component: str) -> None:
        with self._lock:
            if component in self._component_to_correlation_id:
                del self._component_to_correlation_id[component]

    # === 解析 ===
    def _parse_correlation_id_internal(self, correlation_id: str) -> Dict[str, str]:
        """解析ID为结构化字段，不严格校验长度。"""
        try:
            correlation_id = correlation_id or ""
            op = ""
            comp = ""
            ts = ""
            rnd = ""
            meta = self.__class__._id_metadata.get(correlation_id)
            if meta:
                op = meta.get("operation_type", "")
                comp = meta.get("component", "")
                ts = meta.get("timestamp", "")
                rnd = meta.get("random_suffix", "")
            elif correlation_id:
                try:
                    main, ts, rnd = correlation_id.rsplit("_", 2)
                    try:
                        op, comp = main.rsplit("_", 1)
                    except ValueError:
                        op = main
                        comp = ""
                except ValueError:
                    segments = correlation_id.split("_")
                    if len(segments) >= 2:
                        ts = segments[-2]
                        rnd = segments[-1]
                        op = "_".join(segments[:-2])
                        comp = ""
                    elif len(segments) == 1:
                        rnd = segments[0]
            return {
                "operation_type": op,
                "component": comp,
                "timestamp": ts,
                "random_suffix": rnd,
            }
        except Exception:
            return {"operation": "", "component": "", "timestamp": "", "random": ""}


