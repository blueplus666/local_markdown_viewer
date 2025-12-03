"""Reporting utilities for integration QA.

This subpackage will host schema definitions, thresholds and writers
for QA reports. Only skeletons are provided at this stage.
"""

from .report_schema import (
    IntegrationTestReportSchema,
    ValidationReportSchema,
)
from .thresholds import (
    GateDecision,
    evaluate_integration_gate,
    evaluate_validation_gate,
)
from .writer import (
    QAReportPaths,
    get_default_paths,
    write_integration_report,
    write_validation_report,
)

__all__ = [
    "IntegrationTestReportSchema",
    "ValidationReportSchema",
    "GateDecision",
    "evaluate_integration_gate",
    "evaluate_validation_gate",
    "QAReportPaths",
    "get_default_paths",
    "write_integration_report",
    "write_validation_report",
]
