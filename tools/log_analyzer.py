#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""日志索引与性能分析工具 (LAD-IMPL-008).

- :class:`LogAnalyzer` 提供关联 ID、时间区间与多条件筛选查询。
- :class:`PerformanceAnalyzer` 针对导入/渲染流程输出统计与性能告警。
"""

from __future__ import annotations

import json
import logging
import statistics
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from utils.config_manager import ConfigManager

LOGGER = logging.getLogger(__name__)


def _parse_iso_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        val = value.rstrip()
        if val.endswith("Z"):
            val = val[:-1] + "+00:00"
        return datetime.fromisoformat(val)
    except Exception:
        return None


def _flatten_path(entry: Dict[str, Any], path: str) -> Any:
    parts = path.split(".")
    current: Any = entry
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


@dataclass
class IndexedLogRecord:
    line: int
    timestamp: Optional[datetime]
    entry: Dict[str, Any]


class LogAnalyzer:
    """针对结构化日志文件的索引与查询引擎。"""

    DEFAULT_LOG_PATH = Path("logs/lad_markdown_viewer.log")

    def __init__(self, log_file_path: Optional[Path | str] = None) -> None:
        config = ConfigManager()
        config_path = config.get_unified_config("features.logging.handlers.file.path", None)
        resolved = Path(log_file_path or config_path or self.DEFAULT_LOG_PATH)
        if not resolved.is_absolute():
            resolved = Path.cwd() / resolved
        self.log_file_path = resolved

        self._entries: List[IndexedLogRecord] = []
        self._correlation_map: Dict[str, List[IndexedLogRecord]] = {}
        self._last_index_mtime: Optional[float] = None

    # ------------------------------------------------------------------
    # 索引管理
    # ------------------------------------------------------------------
    def ensure_index(self, force: bool = False) -> None:
        path = self.log_file_path
        if force or not self._entries:
            self.build_index()
            return
        try:
            mtime = path.stat().st_mtime
        except FileNotFoundError:
            return
        if self._last_index_mtime is None or mtime > self._last_index_mtime:
            self.build_index()

    def build_index(self) -> None:
        self._entries.clear()
        self._correlation_map.clear()

        path = self.log_file_path
        try:
            handle = path.open("r", encoding="utf-8")
        except FileNotFoundError:
            LOGGER.info("日志文件不存在: %s", path)
            return

        with handle as fh:
            for line_num, line in enumerate(fh, 1):
                try:
                    raw = json.loads(line)
                except json.JSONDecodeError:
                    LOGGER.debug("忽略无法解析的日志行 %s", line_num)
                    continue

                record = IndexedLogRecord(
                    line=line_num,
                    timestamp=_parse_iso_timestamp(raw.get("timestamp")),
                    entry=raw,
                )
                self._entries.append(record)

                cid = raw.get("correlation_id")
                if cid:
                    self._correlation_map.setdefault(cid, []).append(record)

        self._entries.sort(key=lambda rec: (rec.timestamp or datetime.min, rec.line))

        try:
            self._last_index_mtime = path.stat().st_mtime
        except FileNotFoundError:
            self._last_index_mtime = None

    # ------------------------------------------------------------------
    # 查询接口
    # ------------------------------------------------------------------
    def query_by_correlation_id(self, correlation_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        self.ensure_index()
        records = self._correlation_map.get(correlation_id, [])
        sliced = records[:limit] if limit else records
        return [rec.entry for rec in sliced]

    def query_by_time_range(self, start: Optional[str] = None, end: Optional[str] = None) -> List[Dict[str, Any]]:
        self.ensure_index()
        start_dt = _parse_iso_timestamp(start) if isinstance(start, str) else start
        end_dt = _parse_iso_timestamp(end) if isinstance(end, str) else end

        results: List[Dict[str, Any]] = []
        for record in self._entries:
            ts = record.timestamp
            if start_dt and (ts is None or ts < start_dt):
                continue
            if end_dt and (ts is None or ts > end_dt):
                continue
            results.append(record.entry)
        return results

    def query(
        self,
        *,
        correlation_id: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        if correlation_id:
            return self.query_by_correlation_id(correlation_id, limit=limit)

        entries = self.query_by_time_range(start, end)
        if filters:
            entries = [entry for entry in entries if self._matches(entry, filters)]
        if limit is not None:
            entries = entries[:limit]
        return entries

    def get_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        self.ensure_index()
        return [rec.entry for rec in self._entries[-limit:]]

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------
    def _matches(self, entry: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        for key, expected in filters.items():
            actual = _flatten_path(entry, key) if "." in key else entry.get(key)
            if expected is None:
                if actual is not None:
                    return False
                continue

            if isinstance(expected, str) and "*" in expected:
                pattern = expected.replace("*", "")
                if pattern not in str(actual):
                    return False
            elif actual != expected:
                return False
        return True


class PerformanceAnalyzer:
    """基于结构化日志的数据分析器。"""

    def __init__(self, analyzer: LogAnalyzer) -> None:
        self.analyzer = analyzer

    def analyze_import_performance(
        self,
        time_range: Optional[Tuple[str, str]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        base_filters = {"operation": "import", "component": "importer"}
        if filters:
            base_filters.update(filters)
        logs = self.analyzer.query(start=time_range[0] if time_range else None,
                                   end=time_range[1] if time_range else None,
                                   filters=base_filters)
        return self._build_import_stats(logs)

    def analyze_render_performance(
        self,
        time_range: Optional[Tuple[str, str]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        base_filters = {"operation": "render", "component": "renderer"}
        if filters:
            base_filters.update(filters)
        logs = self.analyzer.query(start=time_range[0] if time_range else None,
                                   end=time_range[1] if time_range else None,
                                   filters=base_filters)
        return self._build_render_stats(logs)

    # ------------------------------------------------------------------
    # 内部统计实现
    # ------------------------------------------------------------------
    def _build_import_stats(self, logs: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        entries = list(logs)
        total = len(entries)
        success = sum(1 for entry in entries if entry.get("level", "").upper() == "INFO")

        durations = self._extract_durations(entries)

        return {
            "total_imports": total,
            "successful_imports": success,
            "failed_imports": total - success,
            "success_rate": (success / total) if total else 0,
            "duration_statistics": self._summarise_durations(durations),
            "alerts": self._collect_alerts(entries),
        }

    def _build_render_stats(self, logs: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for entry in logs:
            renderer = entry.get("renderer_type") or entry.get("details", {}).get("renderer_type", "unknown")
            grouped.setdefault(renderer, []).append(entry)

        result: Dict[str, Any] = {}
        for renderer, entries in grouped.items():
            durations = self._extract_durations(entries)
            result[renderer] = {
                "count": len(entries),
                "success_rate": self._compute_success_rate(entries),
                "duration_statistics": self._summarise_durations(durations),
                "alerts": self._collect_alerts(entries),
            }
        return result

    def _extract_durations(self, entries: Iterable[Dict[str, Any]]) -> List[float]:
        durations: List[float] = []
        for entry in entries:
            detail_duration = entry.get("details", {}).get("duration_ms")
            if detail_duration is not None:
                durations.append(float(detail_duration))
                continue

            metrics_duration = entry.get("metrics", {}).get("timers", {})
            if isinstance(metrics_duration, dict):
                duration_values = [float(v.get("duration", 0)) for v in metrics_duration.values() if isinstance(v, dict)]
                durations.extend([v * 1000 for v in duration_values if v])
        return [d for d in durations if d]

    def _summarise_durations(self, durations: List[float]) -> Dict[str, Any]:
        if not durations:
            return {
                "count": 0,
                "avg_ms": 0,
                "max_ms": 0,
                "min_ms": 0,
                "p95_ms": 0,
                "p99_ms": 0,
            }

        durations_sorted = sorted(durations)
        return {
            "count": len(durations_sorted),
            "avg_ms": sum(durations_sorted) / len(durations_sorted),
            "max_ms": durations_sorted[-1],
            "min_ms": durations_sorted[0],
            "p95_ms": self._percentile(durations_sorted, 95),
            "p99_ms": self._percentile(durations_sorted, 99),
        }

    def _collect_alerts(self, entries: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        alerts: List[Dict[str, Any]] = []
        for entry in entries:
            severity = entry.get("severity") or entry.get("details", {}).get("severity")
            if severity and severity.upper() in {"WARNING", "ERROR", "CRITICAL"}:
                alerts.append({
                    "timestamp": entry.get("timestamp"),
                    "message": entry.get("message"),
                    "severity": severity,
                    "correlation_id": entry.get("correlation_id"),
                })
        return alerts

    def _compute_success_rate(self, entries: Iterable[Dict[str, Any]]) -> float:
        data = list(entries)
        total = len(data)
        if not total:
            return 0.0
        success = sum(1 for entry in data if entry.get("level", "").upper() == "INFO")
        return success / total

    @staticmethod
    def _percentile(values: List[float], percentile: int) -> float:
        if not values:
            return 0.0
        if len(values) == 1:
            return values[0]
        try:
            return statistics.quantiles(values, n=100, method="inclusive")[percentile - 1]
        except Exception:
            rank = max(0, min(len(values) - 1, int(round((percentile / 100) * (len(values) - 1)))))
            return values[rank]


__all__ = ["LogAnalyzer", "PerformanceAnalyzer"]
