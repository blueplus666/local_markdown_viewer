#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for log analysis utilities delivered by LAD-IMPL-008."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.performance_metrics import PerformanceMetrics
from tools.log_analyzer import LogAnalyzer, PerformanceAnalyzer
from tools.log_query_api import create_app
from tools.log_query_cli import LogQueryCLI


def _write_sample_log(tmp_path: Path) -> Path:
    entries = [
        {
            "timestamp": "2025-01-01T10:00:00Z",
            "level": "INFO",
            "logger": "core.dynamic_module_importer",
            "message": "Module import completed",
            "correlation_id": "cid-1",
            "operation": "import",
            "component": "importer",
            "details": {"duration_ms": 120, "severity": "INFO"},
        },
        {
            "timestamp": "2025-01-01T10:00:01Z",
            "level": "ERROR",
            "logger": "core.dynamic_module_importer",
            "message": "Module import failed",
            "correlation_id": "cid-2",
            "operation": "import",
            "component": "importer",
            "details": {"duration_ms": 350, "severity": "ERROR"},
        },
        {
            "timestamp": "2025-01-01T10:00:02Z",
            "level": "INFO",
            "logger": "core.markdown_renderer",
            "message": "Render completed",
            "correlation_id": "cid-1",
            "operation": "render",
            "component": "renderer",
            "renderer_type": "markdown_processor",
            "details": {"duration_ms": 45, "severity": "INFO"},
        },
        {
            "timestamp": "2025-01-01T10:00:03Z",
            "level": "INFO",
            "logger": "core.markdown_renderer",
            "message": "Render completed",
            "correlation_id": "cid-3",
            "operation": "render",
            "component": "renderer",
            "renderer_type": "fallback_renderer",
            "details": {"duration_ms": 120, "severity": "WARNING"},
        },
    ]

    log_path = tmp_path / "lad_markdown_viewer.log"
    with log_path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return log_path


def test_log_analyzer_queries(tmp_path: Path) -> None:
    log_path = _write_sample_log(tmp_path)
    analyzer = LogAnalyzer(log_path)
    analyzer.ensure_index(force=True)

    by_cid = analyzer.query(correlation_id="cid-1")
    assert len(by_cid) == 2

    time_filtered = analyzer.query(start="2025-01-01T10:00:00Z", end="2025-01-01T10:00:02Z")
    assert len(time_filtered) == 3

    with_filter = analyzer.query(filters={"details.severity": "WARNING"})
    assert len(with_filter) == 1
    assert with_filter[0]["correlation_id"] == "cid-3"

    recent = analyzer.get_recent(limit=2)
    assert len(recent) == 2
    assert recent[-1]["correlation_id"] == "cid-3"


def test_performance_analyzer_stats(tmp_path: Path) -> None:
    log_path = _write_sample_log(tmp_path)
    analyzer = LogAnalyzer(log_path)
    analyzer.ensure_index(force=True)

    perf = PerformanceAnalyzer(analyzer)
    import_stats = perf.analyze_import_performance()
    assert import_stats["total_imports"] == 2
    assert pytest.approx(import_stats["duration_statistics"]["avg_ms"], 0.1) == 235

    render_stats = perf.analyze_render_performance()
    assert set(render_stats.keys()) == {"markdown_processor", "fallback_renderer"}
    assert render_stats["markdown_processor"]["duration_statistics"]["max_ms"] == 45
    assert render_stats["fallback_renderer"]["alerts"]


def test_log_query_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    log_path = _write_sample_log(tmp_path)
    cli = LogQueryCLI()

    exit_code = cli.run(["--log-file", str(log_path), "correlation", "--id", "cid-1"])
    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["count"] == 2

    capsys.readouterr()
    exit_code = cli.run([
        "--log-file",
        str(log_path),
        "filter",
        "--start",
        "2025-01-01T10:00:02Z",
        "--filter",
        "renderer_type=fallback_renderer",
    ])
    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["count"] == 1


def test_log_query_api_endpoints(tmp_path: Path) -> None:
    log_path = _write_sample_log(tmp_path)
    app = create_app(str(log_path))

    client = app.test_client()

    response = client.get("/api/logs/correlation/cid-1")
    assert response.status_code == 200
    data = response.get_json()
    assert data["count"] == 2

    response = client.get("/api/analytics/render-performance")
    assert response.status_code == 200
    stats = response.get_json()
    assert "markdown_processor" in stats

    response = client.post("/api/config/log-level", json={"global_level": "DEBUG"})
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"

    response = client.post("/api/config/log-level/restore")
    assert response.status_code == 200


def test_performance_metrics_threshold_listener() -> None:
    metrics = PerformanceMetrics()
    metrics._thresholds = {
        "gauge.render_latency": {"max": 10, "severity_over": "ERROR"},
    }

    captured = []

    def _listener(name, value, metadata):
        captured.append((name, value, metadata))

    metrics.register_threshold_listener(_listener)
    metrics.set_gauge("gauge.render_latency", 15, {"component": "renderer"})

    assert captured
    name, value, metadata = captured[0]
    assert name == "gauge.render_latency"
    assert value == 15
    assert metadata["severity"] == "ERROR"
    assert metadata["component"] == "renderer"
