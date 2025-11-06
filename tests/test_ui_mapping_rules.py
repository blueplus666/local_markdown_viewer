#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LAD-IMPL-007 V4.2：UI映射规则测试
"""

import unittest
from PyQt5.QtWidgets import QLabel

from tests.test_session_setup import ensure_qapp

ensure_qapp()

from ui.main_window import MainWindow


class TestUIMappingRules(unittest.TestCase):
    def setUp(self):
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()

    def _get_label_color(self, status):
        label = QLabel()
        self.window._apply_status_color(label, status)
        return label.styleSheet().lower()

    def test_complete_status_color(self):
        self.assertIn("#2e7d32", self._get_label_color("complete"))

    def test_incomplete_status_color(self):
        self.assertIn("#f9a825", self._get_label_color("incomplete"))

    def test_import_failed_status_color(self):
        self.assertIn("#c62828", self._get_label_color("import_failed"))

    def test_unknown_status_color(self):
        self.assertIn("#666666", self._get_label_color("unknown"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

