#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LAD-IMPL-007 V4.2：CorrelationIdManager架构对齐测试
架构依据：第2份-LAD-IMPL-008日志系统增强完整细化过程文档-续篇2.md 第274-333行
"""

import threading
import unittest
from core.correlation_id_manager import CorrelationIdManager


class TestCorrelationIdManager(unittest.TestCase):
    """关联ID管理器架构对齐测试"""

    def test_format_with_component(self):
        corr_id = CorrelationIdManager.generate_correlation_id("import", "markdown")
        parts = corr_id.split("_")
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[0], "import")
        self.assertEqual(parts[1], "markdown")
        self.assertTrue(parts[2].isdigit())
        self.assertEqual(len(parts[3]), 8)

    def test_format_without_component(self):
        corr_id = CorrelationIdManager.generate_correlation_id("render")
        parts = corr_id.split("_")
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], "render")
        self.assertTrue(parts[1].isdigit())

    def test_singleton_thread_safety(self):
        instances = []

        def get_instance():
            instances.append(CorrelationIdManager())

        threads = [threading.Thread(target=get_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertTrue(all(inst is instances[0] for inst in instances))

    def test_set_get_clear_cycle(self):
        manager = CorrelationIdManager()
        manager.set_current_correlation_id("ui", "test_id")
        self.assertEqual(manager.get_current_correlation_id("ui"), "test_id")
        manager.clear_current_correlation_id("ui")
        self.assertIsNone(manager.get_current_correlation_id("ui"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

