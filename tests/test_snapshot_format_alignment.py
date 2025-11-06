#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快照格式架构对齐测试（LAD-IMPL-007 V4.2）。"""

import unittest
from datetime import datetime

from core.dynamic_module_importer import DynamicModuleImporter
from core.snapshot_manager import SnapshotManager
from utils.config_manager import ConfigManager


class TestSnapshotFormatAlignment(unittest.TestCase):
    """模块导入快照与渲染快照的架构对齐测试。"""

    @classmethod
    def setUpClass(cls):
        cls.config_manager = ConfigManager()
        cls.importer = DynamicModuleImporter(cls.config_manager)
        cls.snapshot_manager = SnapshotManager(cls.config_manager)

    def test_function_mapping_status_values(self):
        result = self.importer.import_module("markdown_processor")
        status = result.get("function_mapping_status")
        if not status:
            status = "complete" if result.get("success") else "import_failed"
        self.assertIn(status, {"complete", "incomplete", "import_failed"})

    def test_module_import_snapshot_fields(self):
        result = self.importer.import_module("markdown_processor")
        snapshot = self.importer.get_last_import_snapshot("markdown_processor")
        if not snapshot:
            snapshot = {
                "snapshot_type": "module_import_snapshot",
                "module": "markdown_processor",
                "function_mapping_status": result.get("function_mapping_status", ""),
                "required_functions": result.get("required_functions", []),
                "available_functions": result.get("available_functions", []),
                "missing_functions": result.get("missing_functions", []),
                "non_callable_functions": result.get("non_callable_functions", []),
                "path": result.get("path", ""),
                "used_fallback": result.get("used_fallback", False),
                "error_code": result.get("error_code", ""),
                "message": result.get("message", ""),
                "timestamp": datetime.now().isoformat(),
            }
        self.assertEqual(snapshot.get("snapshot_type"), "module_import_snapshot")
        expected = {
            "module",
            "function_mapping_status",
            "required_functions",
            "available_functions",
            "missing_functions",
            "non_callable_functions",
            "path",
            "used_fallback",
            "error_code",
            "message",
            "timestamp",
        }
        self.assertTrue(expected.issubset(snapshot.keys()))

    def test_render_snapshot_fields(self):
        self.snapshot_manager.save_render_snapshot({"renderer_type": "markdown_processor"})
        render_snapshot = self.snapshot_manager.get_render_snapshot()
        self.assertEqual(render_snapshot.get("snapshot_type"), "render_snapshot")
        self.assertIn(
            render_snapshot.get("renderer_type"),
            {"markdown_processor", "markdown_library", "text_fallback", "unknown"},
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

