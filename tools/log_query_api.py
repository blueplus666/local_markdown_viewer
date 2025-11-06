#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RESTFul 日志查询与分析 API (LAD-IMPL-008).

提供以下能力：
- 关联 ID 查询、时间区间查询、多字段筛选
- 导入/渲染性能统计
- 动态日志级别管理（查询、设置、恢复）
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from flask import Flask, jsonify, request

from core.dynamic_log_config import RuntimeLogLevelController
from tools.log_analyzer import LogAnalyzer, PerformanceAnalyzer


def _build_filters(query_args) -> Dict[str, str]:
    filters: Dict[str, str] = {}
    for key, value in query_args.items():
        if key.startswith("filter."):
            filters[key[7:]] = value
    return filters


def create_app(log_file_path: Optional[str] = None) -> Flask:
    analyzer = LogAnalyzer(log_file_path)
    performance_analyzer = PerformanceAnalyzer(analyzer)

    app = Flask(__name__)

    runtime_controller = RuntimeLogLevelController()
    root_logger = logging.getLogger()
    runtime_controller.register_logger(root_logger)
    for name, logger in logging.root.manager.loggerDict.items():
        if isinstance(logger, logging.Logger):
            runtime_controller.register_logger(logger)

    @app.before_request
    def _ensure_index():
        analyzer.ensure_index()

    @app.route("/api/logs/correlation/<string:correlation_id>")
    def get_logs_by_correlation(correlation_id: str):
        limit = request.args.get("limit", type=int)
        data = analyzer.query(correlation_id=correlation_id, limit=limit)
        return jsonify({"correlation_id": correlation_id, "count": len(data), "entries": data})

    @app.route("/api/logs/query")
    def query_logs():
        start = request.args.get("start")
        end = request.args.get("end")
        limit = request.args.get("limit", type=int)
        filters = _build_filters(request.args)
        data = analyzer.query(start=start, end=end, filters=filters or None, limit=limit)
        return jsonify({
            "count": len(data),
            "entries": data,
            "filters": filters,
            "start": start,
            "end": end,
        })

    @app.route("/api/logs/recent")
    def get_recent_logs():
        limit = request.args.get("limit", default=100, type=int)
        data = analyzer.get_recent(limit=limit)
        return jsonify({"count": len(data), "entries": data})

    @app.route("/api/analytics/import-performance")
    def import_performance():
        start = request.args.get("start")
        end = request.args.get("end")
        filters = _build_filters(request.args)
        stats = performance_analyzer.analyze_import_performance(time_range=(start, end) if start or end else None,
                                                                filters=filters or None)
        return jsonify(stats)

    @app.route("/api/analytics/render-performance")
    def render_performance():
        start = request.args.get("start")
        end = request.args.get("end")
        filters = _build_filters(request.args)
        stats = performance_analyzer.analyze_render_performance(time_range=(start, end) if start or end else None,
                                                                filters=filters or None)
        return jsonify(stats)

    @app.route("/api/config/log-level", methods=["GET"])
    def get_log_levels():
        return jsonify({"levels": runtime_controller.get_current_levels()})

    @app.route("/api/config/log-level", methods=["POST"])
    def set_log_levels():
        payload = request.get_json(silent=True) or {}
        responses = []

        global_level = payload.get("global_level")
        if global_level:
            runtime_controller.set_global_level(global_level)
            responses.append({"global_level": global_level})

        loggers = payload.get("loggers") or {}
        for name, level in loggers.items():
            runtime_controller.set_level(name, level)
            responses.append({name: level})

        return jsonify({"status": "ok", "changes": responses})

    @app.route("/api/config/log-level/restore", methods=["POST"])
    def restore_log_levels():
        runtime_controller.restore_original_levels()
        return jsonify({"status": "ok"})

    @app.route("/api/health")
    def health_check():
        return jsonify({"status": "healthy"})

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = create_app()
    app.run(host="0.0.0.0", port=5001)
