"""Gate and threshold helpers for QA reports.

Current implementations intentionally mirror the existing minimal QA
gate behavior from tests/test_qa_minimal.py. They can be extended with
richer performance and regression checks in later steps.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Mapping, Any


@dataclass
class GateDecision:
    """Result of evaluating a QA gate."""

    passed: bool
    reasons: List[str]


def evaluate_integration_gate(summary: Mapping[str, Any]) -> GateDecision:
    """Evaluate the integration report gate based on test_summary only.

    This matches the current assertions in tests/test_qa_minimal.py,
    requiring success_rate == 100.0 and failed_tests == 0.
    """

    reasons: List[str] = []
    success_rate = float(summary.get("success_rate", 0.0))
    failed_tests = int(summary.get("failed_tests", 1))

    if success_rate != 100.0:
        reasons.append(f"success_rate != 100.0 (actual={success_rate})")
    if failed_tests != 0:
        reasons.append(f"failed_tests != 0 (actual={failed_tests})")

    return GateDecision(passed=not reasons, reasons=reasons)


_CRITICAL_COMPONENT_KEYS = [
    "system_integration_coordinator",
    "monitoring_system_deployer",
    "performance_benchmark_tester",
    "link_processor_integration_preparer",
    "comparison_analysis_tool",
    "integration_test_suite",
]


def evaluate_validation_gate(components: Mapping[str, Mapping[str, Any]]) -> GateDecision:
    """Evaluate the validation report gate based on component status.

    This mirrors the current behavior that requires each critical
    component to exist and have status == "passed".
    """

    reasons: List[str] = []

    for key in _CRITICAL_COMPONENT_KEYS:
        data = components.get(key)
        if data is None:
            reasons.append(f"missing component: {key}")
            continue
        status = data.get("status")
        if status != "passed":
            reasons.append(f"component {key} not passed (status={status})")

    return GateDecision(passed=not reasons, reasons=reasons)
