#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""日志查询命令行工具 (LAD-IMPL-008).

用法示例：
    python tools/log_query_cli.py correlation --id 123
    python tools/log_query_cli.py filter --start 2025-01-01T00:00:00 --filter level=ERROR
    python tools/log_query_cli.py performance --type render --start 2025-01-01T00:00:00
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional

from tools.log_analyzer import LogAnalyzer, PerformanceAnalyzer


class LogQueryCLI:
    def __init__(self, log_file: Optional[str] = None) -> None:
        self.analyzer = LogAnalyzer(Path(log_file) if log_file else None)
        self.performance_analyzer = PerformanceAnalyzer(self.analyzer)

    def run(self, argv: Optional[list[str]] = None) -> int:
        parser = self._build_parser()
        args = parser.parse_args(argv)

        if args.log_file:
            self.analyzer = LogAnalyzer(Path(args.log_file))
            self.performance_analyzer = PerformanceAnalyzer(self.analyzer)

        self.analyzer.ensure_index(force=args.force_reindex)

        if args.command == "correlation":
            return self._handle_correlation(args)
        if args.command == "filter":
            return self._handle_filter(args)
        if args.command == "performance":
            return self._handle_performance(args)
        if args.command == "recent":
            return self._handle_recent(args)

        parser.print_help()
        return 1

    def _build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="结构化日志查询工具")
        parser.add_argument("--log-file", help="日志文件路径，默认读取配置文件中定义的路径")
        parser.add_argument("--force-reindex", action="store_true", help="强制重建索引")

        subparsers = parser.add_subparsers(dest="command")

        # correlation
        correlation = subparsers.add_parser("correlation", help="按关联ID查询日志")
        correlation.add_argument("--id", required=True, help="关联 ID")
        correlation.add_argument("--limit", type=int, help="返回条数限制")

        # filter
        filter_parser = subparsers.add_parser("filter", help="按时间/条件筛选日志")
        filter_parser.add_argument("--start", help="起始时间 (ISO8601)")
        filter_parser.add_argument("--end", help="结束时间 (ISO8601)")
        filter_parser.add_argument("--limit", type=int, help="返回条数限制")
        filter_parser.add_argument(
            "--filter",
            action="append",
            help="按字段过滤，格式 key=value，支持嵌套，如 details.duration_ms=100",
        )

        # performance
        perf = subparsers.add_parser("performance", help="性能统计")
        perf.add_argument("--type", choices=["import", "render"], required=True, help="统计类型")
        perf.add_argument("--start", help="起始时间 (ISO8601)")
        perf.add_argument("--end", help="结束时间 (ISO8601)")
        perf.add_argument(
            "--filter",
            action="append",
            help="附加过滤字段，如 renderer_type=markdown_processor",
        )

        # recent
        recent = subparsers.add_parser("recent", help="查看最近日志")
        recent.add_argument("--limit", type=int, default=50, help="返回条数，默认50")

        return parser

    def _parse_filters(self, filter_args: Optional[list[str]]) -> Dict[str, Any]:
        filters: Dict[str, Any] = {}
        if not filter_args:
            return filters
        for item in filter_args:
            if "=" not in item:
                continue
            key, value = item.split("=", 1)
            filters[key] = value
        return filters

    def _handle_correlation(self, args: argparse.Namespace) -> int:
        data = self.analyzer.query(correlation_id=args.id, limit=args.limit)
        print(json.dumps({"count": len(data), "entries": data}, ensure_ascii=False, indent=2))
        return 0

    def _handle_filter(self, args: argparse.Namespace) -> int:
        filters = self._parse_filters(args.filter)
        data = self.analyzer.query(start=args.start, end=args.end, filters=filters or None, limit=args.limit)
        payload = {
            "count": len(data),
            "entries": data,
            "filters": filters,
            "start": args.start,
            "end": args.end,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    def _handle_recent(self, args: argparse.Namespace) -> int:
        data = self.analyzer.get_recent(limit=args.limit)
        print(json.dumps({"count": len(data), "entries": data}, ensure_ascii=False, indent=2))
        return 0

    def _handle_performance(self, args: argparse.Namespace) -> int:
        filters = self._parse_filters(args.filter)
        time_range = (args.start, args.end) if args.start or args.end else None
        if args.type == "import":
            stats = self.performance_analyzer.analyze_import_performance(time_range=time_range, filters=filters or None)
        else:
            stats = self.performance_analyzer.analyze_render_performance(time_range=time_range, filters=filters or None)
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return 0


def main(argv: Optional[list[str]] = None) -> int:
    cli = LogQueryCLI()
    return cli.run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
