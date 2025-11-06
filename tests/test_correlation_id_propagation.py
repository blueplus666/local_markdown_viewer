#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""correlation_id传播最小集成测试。"""

import unittest
from unittest.mock import patch

from tests._utils import get_qapp

get_qapp()

from ui.main_window import MainWindow


class TestCorrelationIdPropagation(unittest.TestCase):
    def setUp(self) -> None:
        self.window = MainWindow()

    def tearDown(self) -> None:
        self.window.close()

    @patch("ui.main_window.ContentViewer")
    def test_correlation_id_generated_on_file_select(self, mocked_viewer) -> None:
        mocked_instance = mocked_viewer.return_value
        mocked_instance.display_file.return_value = None

        self.window._handle_file_selected("/tmp/test.md")
        self.assertTrue(self.window.statusBar().currentMessage())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

