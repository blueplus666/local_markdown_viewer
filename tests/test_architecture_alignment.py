#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""架构对齐自动验证（附录C批量检查）。"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from core.dynamic_module_importer import DynamicModuleImporter
from core.snapshot_manager import SnapshotManager
from core.correlation_id_manager import CorrelationIdManager
from utils.config_manager import ConfigManager
from ui.status_events import StatusEventEmitter, StatusChangeEvent
from ui.main_window import MainWindow

from tests._utils import get_qapp


ROOT = Path(__file__).resolve().parents[1]


class TestConfigurationAlignment(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with (ROOT / "config" / "app_config.json").open("r", encoding="utf-8") as f:
            cls.app_config = json.load(f)
        with (ROOT / "config" / "ui_config.json").open("r", encoding="utf-8") as f:
            cls.ui_config = json.load(f)

    def test_app_config_status_bar_messages(self) -> None:
        messages = self.app_config.get("ui", {}).get("status_bar_messages", {})
        self.assertTrue(messages, "ui.status_bar_messages 必须存在")
        for key in ("complete", "incomplete", "import_failed"):
            self.assertIn(key, messages)
            self.assertIn("text", messages[key])

    def test_app_config_logging_and_performance(self) -> None:
        logging_cfg = self.app_config.get("logging", {})
        perf_cfg = self.app_config.get("performance", {})
        self.assertTrue(logging_cfg.get("correlation_id_enabled"), "必须启用correlation_id")
        self.assertIn("monitoring", perf_cfg)
        thresholds = perf_cfg.get("thresholds", {})
        self.assertIn("status_bar_update_ms", thresholds)

    def test_ui_config_colors(self) -> None:
        colors = self.ui_config.get("colors", {})
        for key in ("success", "warning", "error", "critical", "disabled", "default"):
            self.assertIn(key, colors, f"ui_config.colors 缺少 {key}")


class TestSnapshotAlignment(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config_manager = ConfigManager()
        cls.importer = DynamicModuleImporter(cls.config_manager)
        cls.snapshot_manager = SnapshotManager(cls.config_manager)

    def test_module_snapshot_fields(self) -> None:
        result = self.importer.import_module("markdown_processor")
        status = result.get("function_mapping_status")
        if not status:
            status = "complete" if result.get("success") else "import_failed"
        self.assertIn(status, {"complete", "incomplete", "import_failed"})

        snapshot = self.importer.get_last_import_snapshot("markdown_processor")
        required = {
            "snapshot_type",
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
        self.assertTrue(required.issubset(snapshot.keys()))
        self.assertEqual(snapshot["snapshot_type"], "module_import_snapshot")

    def test_render_snapshot_fields(self) -> None:
        self.snapshot_manager.save_render_snapshot({"renderer_type": "markdown_processor"})
        render_snapshot = self.snapshot_manager.get_render_snapshot()
        self.assertEqual(render_snapshot.get("snapshot_type"), "render_snapshot")
        self.assertIn(render_snapshot.get("renderer_type"), {"markdown_processor", "markdown_library", "text_fallback", "unknown"})


class TestCorrelationAlignment(unittest.TestCase):
    def test_correlation_id_format(self) -> None:
        corr_id = CorrelationIdManager.generate_correlation_id("import", "markdown")
        parts = corr_id.split("_")
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[0], "import")
        self.assertEqual(parts[1], "markdown")
        self.assertTrue(parts[2].isdigit())

    def test_correlation_id_parse(self) -> None:
        corr_id = CorrelationIdManager.generate_correlation_id("ui_action", "status_bar")
        parsed = CorrelationIdManager.parse_correlation_id(corr_id)
        self.assertEqual(parsed["operation_type"], "ui_action")
        self.assertEqual(parsed["component"], "status_bar")


class TestStatusEventAlignment(unittest.TestCase):
    def test_event_emitter_max_history(self) -> None:
        emitter = StatusEventEmitter(max_history=2)
        emitter.emit(StatusChangeEvent("type1", "ui", "old", "new1"))
        emitter.emit(StatusChangeEvent("type2", "ui", "old", "new2"))
        emitter.emit(StatusChangeEvent("type3", "ui", "old", "new3"))
        history = emitter.get_history(10)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].new_status, "new2")
        self.assertEqual(history[1].new_status, "new3")


class TestUiMappingAlignment(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        get_qapp()
        cls.window = MainWindow()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.window.close()

    def test_function_mapping_color(self) -> None:
        status = {"module": "markdown_processor", "function_mapping_status": "complete", "error_code": ""}
        self.assertIn("#2e7d32", self.window._get_status_color(status))

        status["function_mapping_status"] = "incomplete"
        self.assertIn("#f9a825", self.window._get_status_color(status))

        status["function_mapping_status"] = "import_failed"
        status["error_code"] = "SYS_RES_MEMORY_EXHAUSTED"
        self.assertIn("#8b0000", self.window._get_status_color(status).lower())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

