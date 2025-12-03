"""integration.qa CLI 入口

提供在命令行运行集成 QA 测试套件的能力。

用法示例::

    # 文本摘要（默认）
    python -m integration.qa

    # JSON 摘要输出到 stdout
    python -m integration.qa --format json

    # 文本模式 + 显示详细用例结果
    python -m integration.qa --details

    # 与 legacy 报告对比（同时运行新的集成套件）
    python -m integration.qa --compare outputs/integration_test_report.json

"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from integration.qa.runners import IntegrationTestReport, run_integration_suite
from integration.qa.validation import compare_with_legacy


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m integration.qa",
        description="运行 integration QA 集成测试套件，并可选与 legacy 报告对比。",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="输出格式：text 或 json，默认为 text。",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="在文本模式下输出每个用例的详情，或在 JSON 模式下包含 test_results。",
    )
    parser.add_argument(
        "--compare",
        metavar="LEGACY_JSON",
        help=(
            "可选：指定 legacy 集成测试 JSON 报告路径，将新的结果与其进行 summary 级别对比。"
        ),
    )
    parser.add_argument(
        "--write-report",
        metavar="PATH",
        help=(
            "可选：将本次集成测试报告写入指定的 JSON 文件路径；路径由调用方显式指定。"
        ),
    )
    parser.add_argument(
        "--fail-on-failed-tests",
        action="store_true",
        help="当存在失败用例时返回退出码 1（默认关闭）。",
    )
    parser.add_argument(
        "--fail-on-success-rate-below",
        type=float,
        metavar="PERCENT",
        help="当通过率低于给定百分比时返回退出码 2（默认关闭）。",
    )
    parser.add_argument(
        "--fail-on-compare-diff",
        action="store_true",
        help="与 legacy 报告对比不一致或对比失败时返回退出码 3（需配合 --compare，默认关闭）。",
    )
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="当检测到性能回归(regression_detected=true)时返回退出码 4（默认关闭）。",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="等价于同时启用 --fail-on-failed-tests, --fail-on-compare-diff, --fail-on-regression。",
    )
    return parser


def _print_text_summary(report: IntegrationTestReport, show_details: bool = False) -> None:
    """以人类可读的文本形式打印测试结果。"""

    summary = report.test_summary
    print("集成测试套件执行完成")
    print(f"  总用例数: {summary.get('total_tests')}")
    print(f"  通过用例: {summary.get('passed_tests')}")
    print(f"  失败用例: {summary.get('failed_tests')}")
    print(f"  跳过用例: {summary.get('skipped_tests')}")
    print(f"  通过率: {summary.get('success_rate')}%")
    print(f"  总耗时: {summary.get('total_execution_time')} 秒")

    if not show_details:
        return

    print("\n详细用例结果:")
    for result in report.test_results:
        line = f"- [{result.status}] {result.test_name} ({result.test_type}) - {result.execution_time:.3f}s"
        print(line)
        if result.error_message:
            print(f"    error: {result.error_message}")


def _build_json_payload(report: IntegrationTestReport, include_details: bool) -> Dict[str, Any]:
    """构造 JSON 输出 payload。"""

    payload: Dict[str, Any] = {
        "test_summary": report.test_summary,
        "timestamp": report.timestamp,
    }

    if include_details:
        payload["test_results"] = [asdict(r) for r in report.test_results]

    return payload


def _has_regression(report: IntegrationTestReport) -> bool:
    """检查报告中是否存在性能回归标记。"""

    for result in report.test_results:
        details = getattr(result, "details", None)
        if not isinstance(details, dict):
            continue
        regression_report = details.get("regression_report")
        if not isinstance(regression_report, dict):
            continue
        if regression_report.get("regression_detected") is True:
            return True
    return False


def _main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # 运行新的集成套件
    report = run_integration_suite()
    compare_result: Dict[str, Any] | None = None
    compare_error: Exception | None = None

    # 可选：与 legacy 报告对比（注意：compare_with_legacy 内部会再次运行一次套件）
    if args.compare:
        try:
            compare_result = compare_with_legacy(args.compare)
        except Exception as exc:  # pragma: no cover - 防御性日志
            compare_error = exc
            print(f"与 legacy 报告对比失败: {exc}")
        else:
            print()  # 与上方结果留一行空行
            status = compare_result.get("status")
            if status == "ok":
                print("与 legacy 报告对比结果: 一致 (summary 无差异)")
            else:
                print("与 legacy 报告对比结果: 存在差异")
                diff = compare_result.get("summary_diff", {})
                if diff:
                    print("summary 差异:")
                    print(json.dumps(diff, ensure_ascii=False, indent=2))

    # 可选：将报告写入指定路径（独立于 stdout 输出格式）
    if args.write_report:
        report_path = Path(args.write_report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        file_payload = _build_json_payload(report, include_details=args.details)
        with report_path.open("w", encoding="utf-8") as f:
            json.dump(file_payload, f, ensure_ascii=False, indent=2, default=str)

    # 根据格式输出
    if args.format == "json":
        payload = _build_json_payload(report, include_details=args.details)
        # 使用 default=str 以兼容 datetime 等不可直接序列化的类型
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    else:
        _print_text_summary(report, show_details=args.details)

    # 计算退出码（默认兼容：不开启任何失败开关则始终返回 0）
    exit_code = 0

    # strict 宏开关：启用部分失败规则
    fail_on_failed_tests = args.fail_on_failed_tests or args.strict
    fail_on_compare_diff = args.fail_on_compare_diff or args.strict
    fail_on_regression = args.fail_on_regression or args.strict

    summary = report.test_summary

    # 1 = 有 failed_tests
    if fail_on_failed_tests and summary.get("failed_tests", 0) > 0:
        exit_code = 1

    # 2 = success_rate 低于阈值（仅当未命中 1 时生效）
    if exit_code == 0 and args.fail_on_success_rate_below is not None:
        try:
            success_rate = float(summary.get("success_rate", 0.0))
        except (TypeError, ValueError):
            success_rate = 0.0
        if success_rate < args.fail_on_success_rate_below:
            exit_code = 2

    # 3 = legacy 对比不一致或失败（仅当未命中 1/2，且显式要求时）
    if exit_code == 0 and args.compare and fail_on_compare_diff:
        if compare_error is not None:
            exit_code = 3
        elif compare_result is not None and compare_result.get("status") != "ok":
            exit_code = 3

    # 4 = 性能回归（仅当未命中前面条件，且显式要求时）
    if exit_code == 0 and fail_on_regression:
        if _has_regression(report):
            exit_code = 4

    return exit_code


if __name__ == "__main__":  # pragma: no cover - CLI 入口
    raise SystemExit(_main())
