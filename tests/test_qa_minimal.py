#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4.3.4 QA 最小用例
断言 4.3.3 的关键产物存在且通过，监控通路可用。
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "第二阶段实现提示词" / "本地Markdown文件渲染程序-重构过程-第二阶段核心功能-06_后期完善-实现提示词" / "outputs"


def _read_json(path: Path):
    assert path.exists(), f"缺少文件: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def test_integration_report_ok():
    data = _read_json(OUT / "integration_test_report.json")
    summary = data.get("test_summary", {})
    assert summary.get("success_rate", 0) == 100.0, "集成测试成功率不足 100%"
    assert summary.get("failed_tests", 1) == 0, "存在失败用例"


def test_validation_report_ok():
    data = _read_json(OUT / "validation_report.json")
    # 简要检查几个关键模块通过
    keys = [
        "system_integration_coordinator",
        "monitoring_system_deployer",
        "performance_benchmark_tester",
        "link_processor_integration_preparer",
        "comparison_analysis_tool",
        "integration_test_suite",
    ]
    for k in keys:
        assert data.get(k, {}).get("status") == "passed", f"{k} 未通过"


def test_metrics_path_exists():
    metrics = ROOT / "metrics"
    assert metrics.exists(), "监控指标目录不存在"

