"""Helpers for writing QA reports to disk.

These helpers centralize how integration and validation reports are
serialized into JSON files under reports/qa/ or a caller-provided
output directory. Implementations are intentionally minimal for now.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
import json


@dataclass
class QAReportPaths:
    """Collection of paths for QA reports under a given base directory."""

    base_dir: Path
    integration_report: Path
    validation_report: Path


def get_default_paths(root: Path | None = None) -> QAReportPaths:
    """Return default QA report paths under the given project root.

    If root is None, the caller is expected to pass fully qualified
    paths instead. This helper is intentionally conservative and only
    uses relative structure that mirrors the current layout.
    """

    if root is None:
        root = Path(__file__).resolve().parents[3]

    base_dir = root / "reports" / "qa"
    return QAReportPaths(
        base_dir=base_dir,
        integration_report=base_dir / "integration_test_report.json",
        validation_report=base_dir / "validation_report.json",
    )


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_integration_report(data: Dict[str, Any], paths: QAReportPaths) -> None:
    """Write an integration report JSON file.

    The data structure is expected to be compatible with the existing
    integration_test_report.json format.
    """

    _ensure_parent(paths.integration_report)
    with paths.integration_report.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def write_validation_report(data: Dict[str, Any], paths: QAReportPaths) -> None:
    """Write a validation report JSON file.

    The data structure is expected to be compatible with the existing
    validation_report.json format.
    """

    _ensure_parent(paths.validation_report)
    with paths.validation_report.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
