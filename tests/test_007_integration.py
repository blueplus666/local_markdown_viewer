#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""007任务集成测试：验证核心流程是否按架构标准协同工作。"""

import unittest

from tests._utils import get_qapp

get_qapp()

from ui.main_window import MainWindow


class Test007Integration(unittest.TestCase):
    """主窗口期望行为的最小集成测试。"""

    def setUp(self) -> None:
        self.window = MainWindow()

    def tearDown(self) -> None:
        self.window.close()

    def test_status_bar_update_flow(self) -> None:
        # 模拟一次状态栏更新流程，确保不会抛异常。
        self.window.update_status_bar_with_import_info()
        message = self.window.statusBar().currentMessage()
        self.assertIsInstance(message, str)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

