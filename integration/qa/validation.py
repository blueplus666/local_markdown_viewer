"""集成QA验证工具

提供与legacy集成测试报告的对比能力，用于验证新的 run_integration_suite()
是否在整体结果上与既有输出保持一致。

注意：本模块不会修改legacy脚本，只是读取其生成的JSON报告文件。
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Union

from integration.qa.runners import IntegrationTestReport, run_integration_suite


PathLike = Union[str, Path]


def _serialise_report(report: IntegrationTestReport) -> Dict[str, Any]:
    """将 IntegrationTestReport 转换为可与 JSON 比较的字典结构。"""

    return {
        "test_summary": report.test_summary,
        "test_results": [asdict(r) for r in report.test_results],
        "timestamp": report.timestamp,
    }


def load_legacy_report(path: PathLike) -> Dict[str, Any]:
    """加载 legacy 集成测试报告 JSON。

    参数
    ------
    path:
        legacy 报告 JSON 文件路径，一般由 legacy 集成脚本写出。
    """

    p = Path(path)
    if not p.is_file():  # pragma: no cover - 防御性检查
        raise FileNotFoundError(f"Legacy report file not found: {p}")

    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):  # pragma: no cover - 防御性
        raise ValueError("Legacy report must be a JSON object at top level.")

    return data


def compare_with_legacy(legacy_report_path: PathLike) -> Dict[str, Any]:
    """运行新的集成测试并与 legacy 报告进行对比。

    设计目标：
    - 不依赖 legacy 代码，只依赖其生成的 JSON 文件；
    - 主要对比 test_summary 级别的关键指标；
    - 报告所有字段的差异，便于逐项审查。

    返回值示例::

        {
            "status": "ok" | "mismatch",
            "legacy_summary": {...},
            "current_summary": {...},
            "summary_diff": {
                "total_tests": {"legacy": 6, "current": 6},
                ...
            },
        }
    """

    legacy_data = load_legacy_report(legacy_report_path)

    # 兼容两种形态：
    # 1) 顶层就有 test_summary 字段（推荐，也是我们现在的新结构）；
    # 2) 整个对象本身就是 summary（更宽松的老格式）。
    if "test_summary" in legacy_data and isinstance(legacy_data["test_summary"], dict):
        legacy_summary = legacy_data["test_summary"]
    else:
        legacy_summary = legacy_data

    # 运行新的集成测试
    current_report = run_integration_suite()
    current_payload = _serialise_report(current_report)
    current_summary = current_payload["test_summary"]

    # 对比 summary 中的所有字段
    summary_diff: Dict[str, Dict[str, Any]] = {}
    keys = set(legacy_summary.keys()) | set(current_summary.keys())

    for key in sorted(keys):
        legacy_value = legacy_summary.get(key)
        current_value = current_summary.get(key)
        if legacy_value != current_value:
            summary_diff[key] = {
                "legacy": legacy_value,
                "current": current_value,
            }

    status = "ok" if not summary_diff else "mismatch"

    return {
        "status": status,
        "legacy_summary": legacy_summary,
        "current_summary": current_summary,
        "summary_diff": summary_diff,
    }
