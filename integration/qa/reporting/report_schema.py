"""Schema helpers for QA reports.

These are lightweight, typed views over the JSON structures used by
integration_test_report.json and validation_report.json.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class IntegrationTestReportSchema:
    """Typed view over the integration test report JSON structure."""

    test_summary: Dict[str, Any]
    test_results: List[Dict[str, Any]]
    timestamp: str


@dataclass
class ValidationReportSchema:
    """Typed view over the validation report JSON structure."""

    components: Dict[str, Dict[str, Any]]
