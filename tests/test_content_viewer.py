#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容显示组件测试模块 v1.0.0
测试ContentViewer类的功能、性能和错误处理

作者: LAD Team
创建时间: 2025-01-08
最后更新: 2025-01-08
"""

import unittest
import sys
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from PyQt5.QtTest import QTest

from ui.content_viewer import ContentViewer


class TestContentViewer(unittest.TestCase):
    """内容显示组件测试类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """设置测试环境"""
        self.viewer = ContentViewer()
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试文件
        self.test_files = {}
        self._create_test_files()
    
    def tearDown(self):
        """清理测试环境"""
        # 清理临时文件
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        # 关闭组件
        self.viewer.close()
    
    def _create_test_files(self):
        """创建测试文件"""
        # Markdown文件
        md_content = """# 测试Markdown文件

这是一个测试文件。

## 代码示例
```python
def hello():
    print("Hello, World!")
```

## 列表
- 项目1
- 项目2
- 项目3
"""
        md_file = Path(self.temp_dir) / "test.md"
        md_file.write_text(md_content, encoding='utf-8')
        self.test_files['markdown'] = str(md_file)
        
        # Python文件
        py_content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"测试Python文件\"\"\"

def test_function():
    \"\"\"测试函数\"\"\"
    return "Hello, World!"

if __name__ == "__main__":
    print(test_function())
"""
        py_file = Path(self.temp_dir) / "test.py"
        py_file.write_text(py_content, encoding='utf-8')
        self.test_files['python'] = str(py_file)
        
        # 文本文件
        txt_content = "这是一个简单的文本文件。\n包含多行内容。\n用于测试文本显示功能。"
        txt_file = Path(self.temp_dir) / "test.txt"
        txt_file.write_text(txt_content, encoding='utf-8')
        self.test_files['text'] = str(txt_file)
        
        # JSON文件
        json_content = """{
    "name": "测试项目",
    "version": "1.0.0",
    "description": "这是一个测试JSON文件",
    "author": "LAD Team",
    "dependencies": {
        "PyQt5": "5.15.0",
        "markdown": "3.4.1"
    }
}"""
        json_file = Path(self.temp_dir) / "test.json"
        json_file.write_text(json_content, encoding='utf-8')
        self.test_files['json'] = str(json_file)
    
    def test_basic_display_markdown(self):
        """测试基本Markdown显示功能"""
        # 显示Markdown文件
        self.viewer.display_file(self.test_files['markdown'])
        
        # 等待加载完成
        QTest.qWait(1000)
        
        # 检查当前文件路径
        self.assertEqual(self.viewer.get_current_file(), self.test_files['markdown'])
        
        # 检查Web引擎是否可用
        if self.viewer.is_web_engine_available():
            self.assertIsNotNone(self.viewer.web_engine_view)
        else:
            self.assertIsNotNone(self.viewer.fallback_text_edit)
    
    def test_basic_display_code(self):
        """测试代码文件显示功能"""
        # 显示Python文件
        self.viewer.display_file(self.test_files['python'])
        
        # 等待加载完成
        QTest.qWait(800)
        
        # 检查当前文件路径
        self.assertEqual(self.viewer.get_current_file(), self.test_files['python'])
    
    def test_basic_display_text(self):
        """测试文本文件显示功能"""
        # 显示文本文件
        self.viewer.display_file(self.test_files['text'])
        
        # 等待加载完成
        QTest.qWait(500)
        
        # 检查当前文件路径
        self.assertEqual(self.viewer.get_current_file(), self.test_files['text'])
    
    def test_basic_display_json(self):
        """测试JSON文件显示功能"""
        # 显示JSON文件
        self.viewer.display_file(self.test_files['json'])
        
        # 等待加载完成
        QTest.qWait(500)
        
        # 检查当前文件路径
        self.assertEqual(self.viewer.get_current_file(), self.test_files['json'])
    
    def test_error_handling_nonexistent_file(self):
        """测试不存在文件的错误处理"""
        # 记录错误信号
        error_received = []
        self.viewer.error_occurred.connect(lambda t, m: error_received.append((t, m)))
        
        # 尝试显示不存在的文件
        non_existent_file = os.path.join(self.temp_dir, "nonexistent.md")
        self.viewer.display_file(non_existent_file)
        
        # 等待处理完成
        QTest.qWait(500)
        
        # 检查是否收到错误信号
        self.assertTrue(len(error_received) > 0)
    
    def test_error_handling_empty_path(self):
        """测试空文件路径的错误处理"""
        # 记录错误信号
        error_received = []
        self.viewer.error_occurred.connect(lambda t, m: error_received.append((t, m)))
        
        # 尝试显示空路径
        self.viewer.display_file("")
        
        # 等待处理完成
        QTest.qWait(200)
        
        # 检查是否收到错误信号
        self.assertTrue(len(error_received) > 0)
    
    def test_cache_functionality(self):
        """测试缓存功能"""
        # 显示文件（第一次）
        self.viewer.display_file(self.test_files['markdown'])
        QTest.qWait(500)
        
        # 获取缓存信息
        cache_info = self.viewer.get_cache_info()
        self.assertGreater(cache_info['total_items'], 0)
        self.assertIn(self.test_files['markdown'], cache_info['cached_files'])
        
        # 再次显示同一文件（应该使用缓存）
        start_time = time.time()
        self.viewer.display_file(self.test_files['markdown'])
        QTest.qWait(200)
        end_time = time.time()
        
        # 缓存显示应该更快
        self.assertLess(end_time - start_time, 1.0)
    
    def test_cache_clear(self):
        """测试缓存清理功能"""
        # 添加文件到缓存
        self.viewer.display_file(self.test_files['markdown'])
        QTest.qWait(300)
        
        # 检查缓存
        cache_info = self.viewer.get_cache_info()
        self.assertGreater(cache_info['total_items'], 0)
        
        # 清理缓存
        self.viewer.clear_cache()
        
        # 检查缓存已清空
        cache_info = self.viewer.get_cache_info()
        self.assertEqual(cache_info['total_items'], 0)
    
    def test_force_reload(self):
        """测试强制重新加载功能"""
        # 首次加载
        self.viewer.display_file(self.test_files['text'])
        QTest.qWait(300)
        
        # 强制重新加载
        self.viewer.display_file(self.test_files['text'], force_reload=True)
        QTest.qWait(300)
        
        # 应该成功加载
        self.assertEqual(self.viewer.get_current_file(), self.test_files['text'])
    
    def test_zoom_functionality(self):
        """测试缩放功能"""
        if not self.viewer.is_web_engine_available():
            self.skipTest("Web引擎不可用，跳过缩放测试")
        
        # 设置缩放因子
        self.viewer.set_zoom_factor(1.5)
        self.assertEqual(self.viewer.get_zoom_factor(), 1.5)
        
        # 恢复默认缩放
        self.viewer.set_zoom_factor(1.0)
        self.assertEqual(self.viewer.get_zoom_factor(), 1.0)
    
    def test_signal_emissions(self):
        """测试信号发送"""
        # 记录信号
        content_loaded_signals = []
        loading_progress_signals = []
        
        self.viewer.content_loaded.connect(
            lambda path, success: content_loaded_signals.append((path, success))
        )
        self.viewer.loading_progress.connect(
            lambda progress: loading_progress_signals.append(progress)
        )
        
        # 显示文件
        self.viewer.display_file(self.test_files['markdown'])
        QTest.qWait(1000)
        
        # 检查信号
        self.assertTrue(len(content_loaded_signals) > 0)
        last_signal = content_loaded_signals[-1]
        self.assertEqual(last_signal[0], self.test_files['markdown'])
        self.assertTrue(last_signal[1])  # 成功加载
    
    def test_performance_large_file(self):
        """测试大文件性能"""
        # 创建大文本文件
        large_content = "这是一行测试内容。\n" * 1000
        large_file = Path(self.temp_dir) / "large.txt"
        large_file.write_text(large_content, encoding='utf-8')
        
        # 测试加载时间
        start_time = time.time()
        self.viewer.display_file(str(large_file))
        QTest.qWait(2000)
        end_time = time.time()
        
        # 检查性能（应在2秒内完成）
        self.assertLess(end_time - start_time, 3.0)
        self.assertEqual(self.viewer.get_current_file(), str(large_file))
    
    def test_web_engine_availability(self):
        """测试Web引擎可用性检查"""
        # 检查Web引擎可用性
        is_available = self.viewer.is_web_engine_available()
        self.assertIsInstance(is_available, bool)
        
        if is_available:
            self.assertIsNotNone(self.viewer.web_engine_view)
        else:
            self.assertIsNotNone(self.viewer.fallback_text_edit)
    
    def test_file_type_detection(self):
        """测试文件类型检测"""
        # 检查文件解析器是否正常工作
        self.assertIsNotNone(self.viewer.file_resolver)
        self.assertIsNotNone(self.viewer.markdown_renderer)
        self.assertIsNotNone(self.viewer.content_preview)
    
    def test_get_current_file(self):
        """测试获取当前文件功能"""
        # 初始状态
        self.assertIsNone(self.viewer.get_current_file())
        
        # 加载文件后
        self.viewer.display_file(self.test_files['text'])
        QTest.qWait(300)
        self.assertEqual(self.viewer.get_current_file(), self.test_files['text'])
    
    def test_status_updates(self):
        """测试状态更新"""
        # 检查状态标签存在
        self.assertIsNotNone(self.viewer.status_label)
        
        # 显示文件时状态应该更新
        self.viewer.display_file(self.test_files['markdown'])
        QTest.qWait(500)
        
        # 状态文本应该包含文件名
        status_text = self.viewer.status_label.text()
        self.assertTrue("test.md" in status_text or "已加载" in status_text or "正在加载" in status_text)
    
    def test_progress_bar(self):
        """测试进度条功能"""
        # 检查进度条存在
        self.assertIsNotNone(self.viewer.progress_bar)
        
        # 初始状态应该隐藏
        self.assertFalse(self.viewer.progress_bar.isVisible())
    
    def test_configuration_integration(self):
        """测试配置集成"""
        # 检查配置管理器
        self.assertIsNotNone(self.viewer.config_manager)
        
        # 检查缓存限制配置
        cache_limit = self.viewer.cache_limit
        self.assertIsInstance(cache_limit, int)
        self.assertGreater(cache_limit, 0)


class TestContentViewerIntegration(unittest.TestCase):
    """内容显示组件集成测试类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """设置测试环境"""
        self.viewer = ContentViewer()
    
    def tearDown(self):
        """清理测试环境"""
        self.viewer.close()
    
    def test_component_initialization(self):
        """测试组件初始化"""
        # 检查基本组件
        self.assertIsNotNone(self.viewer.config_manager)
        self.assertIsNotNone(self.viewer.file_resolver)
        self.assertIsNotNone(self.viewer.markdown_renderer)
        self.assertIsNotNone(self.viewer.content_preview)
        
        # 检查UI组件
        self.assertIsNotNone(self.viewer.status_label)
        self.assertIsNotNone(self.viewer.progress_bar)
        
        # 检查缓存
        self.assertIsInstance(self.viewer.content_cache, dict)
        self.assertEqual(len(self.viewer.content_cache), 0)
    
    def test_error_recovery(self):
        """测试错误恢复机制"""
        # 模拟文件解析失败
        with patch.object(self.viewer.file_resolver, 'resolve_file_path') as mock_resolve:
            mock_resolve.return_value = {'success': False, 'error': '测试错误'}
            
            # 记录错误信号
            error_received = []
            self.viewer.error_occurred.connect(lambda t, m: error_received.append((t, m)))
            
            # 尝试显示文件
            self.viewer.display_file("test.md")
            QTest.qWait(300)
            
            # 应该收到错误信号
            self.assertTrue(len(error_received) > 0)


if __name__ == '__main__':
    # 运行测试
    unittest.main(argv=[''], exit=False, verbosity=2)