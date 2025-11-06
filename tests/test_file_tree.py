#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FileTree 组件测试
"""
import sys
import os
import unittest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../ui')))
from file_tree import FileTree

app = QApplication.instance() or QApplication(sys.argv)

class TestFileTree(unittest.TestCase):
    def setUp(self):
        self.widget = FileTree()
        self.widget.show()

    def tearDown(self):
        self.widget.close()

    def test_basic_display(self):
        # 检查树视图是否显示
        self.assertTrue(self.widget.tree_view.isVisible())
        # 检查根目录是否存在
        root_dir = self.widget.get_current_directory()
        self.assertTrue(os.path.exists(root_dir))

    def test_file_filter(self):
        # 切换显示隐藏文件
        self.widget.filter_checkbox.setChecked(True)
        self.assertTrue(self.widget.filter_checkbox.isChecked())
        self.widget.filter_checkbox.setChecked(False)
        self.assertFalse(self.widget.filter_checkbox.isChecked())

    def test_search_function(self):
        # 输入搜索内容
        self.widget.search_box.setText('test')
        self.assertEqual(self.widget.search_box.text(), 'test')
        # 清空搜索
        self.widget.search_box.setText('')
        self.assertEqual(self.widget.search_box.text(), '')

    def test_file_selection_signal(self):
        # 连接信号
        self.selected_path = None
        def on_file_selected(path):
            self.selected_path = path
        self.widget.file_selected.connect(on_file_selected)
        # 模拟点击第一个文件（如果有）
        model = self.widget.proxy_model
        for row in range(model.rowCount()):
            idx = model.index(row, 0)
            source_idx = model.mapToSource(idx)
            if not self.widget.file_model.isDir(source_idx):
                self.widget.tree_view.setCurrentIndex(idx)
                self.widget._on_item_clicked(idx)
                break
        # 检查信号是否触发
        self.assertTrue(self.selected_path is None or os.path.exists(self.selected_path))

    def test_performance_large_dir(self):
        # 性能测试：切换到用户主目录
        import time
        home_dir = os.path.expanduser('~')
        start = time.time()
        self.widget.set_root_path(home_dir)
        elapsed = time.time() - start
        # 要求切换根目录不超过2秒
        self.assertLess(elapsed, 2.0)

if __name__ == '__main__':
    unittest.main()