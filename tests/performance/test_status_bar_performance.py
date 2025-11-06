#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""状态栏性能测试脚本（LAD-IMPL-007 V4.2）。"""

from __future__ import annotations

import statistics
import time
import unittest

from tests._utils import get_qapp

get_qapp()

from ui.main_window import MainWindow


class TestStatusBarPerformance(unittest.TestCase):
    ITERATIONS = 5

    def setUp(self) -> None:
        self.window = MainWindow()

    def tearDown(self) -> None:
        self.window.close()

    def test_status_bar_update_performance(self) -> None:
        durations_ms = []
        for _ in range(self.ITERATIONS):
            start = time.perf_counter()
            self.window.update_status_bar_with_import_info()
            duration = (time.perf_counter() - start) * 1000
            durations_ms.append(duration)

        avg = statistics.mean(durations_ms)
        self.assertLess(avg, 100.0, f"状态栏更新平均耗时过高: {avg:.2f}ms")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

