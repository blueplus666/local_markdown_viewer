"""Command-line entry points for integration QA.

This module provides a minimal CLI that will later be extended to run
integration and validation suites via the integration.qa.runners
package. For now it only parses arguments and raises a clear error to
signal that the implementation is pending.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Integration QA CLI (skeleton)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_all = subparsers.add_parser("run-all", help="Run integration and validation suites")
    run_all.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional output directory for QA reports (defaults to reports/qa)",
    )

    run_int = subparsers.add_parser("run-integration", help="Run integration suite only")
    run_int.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional output directory for the integration report",
    )

    run_val = subparsers.add_parser("run-validation", help="Run validation suite only")
    run_val.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional output directory for the validation report",
    )
    run_val.add_argument(
        "--fast",
        action="store_true",
        help="Run in fast mode if supported by the underlying runner",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for ``python -m integration.qa.cli``.

    The current implementation only validates arguments and indicates
    that the functionality is not yet wired. This avoids accidental use
    in CI before the implementation is complete.
    """

    if argv is None:
        argv = sys.argv[1:]

    parser = _build_parser()
    args = parser.parse_args(argv)

    # Skeleton behavior: refuse to run and guide the caller.
    parser.error(
        "integration.qa CLI is a skeleton only; "
        "wire runners and writers before using it in CI."
    )

    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
