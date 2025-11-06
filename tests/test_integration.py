#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试模块 v1.0.0
测试所有组件的集成功能和端到端流程

作者: LAD Team
创建时间: 2025-01-08
最后更新: 2025-01-08
"""

import sys
import os
import tempfile
import shutil
import time
import unittest
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QEventLoop, QCoreApplication, Qt
from PyQt5.QtTest import QTest

from main_window_integrated import IntegratedMainWindow
from utils.config_manager import get_config_manager
from core.file_resolver import FileResolver
from core.markdown_renderer import MarkdownRenderer
from core.content_preview import ContentPreview
from ui.file_tree import FileTree
from ui.content_viewer import ContentViewer


class IntegrationTest(unittest.TestCase):
    """集成测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        _t0 = time.perf_counter()
        try:
            _existing_app = QApplication.instance()
        except Exception:
            _existing_app = None
        if _existing_app is None:
            QCoreApplication.setAttribute(Qt.AA_UseSoftwareOpenGL, True)
            QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
            cls.app = QApplication(sys.argv)
            cls._created_app = True
        else:
            cls.app = _existing_app
            cls._created_app = False
        _t1 = time.perf_counter()
        cls.test_dir = tempfile.mkdtemp(prefix="integration_test_")
        cls.test_files = {}
        cls._create_test_files()
        _t2 = time.perf_counter()
        cls.config_manager = get_config_manager()
        _t3 = time.perf_counter()
        try:
            print(f"[CLASS SETUP TIMERS] app={(_t1 - _t0):.3f}s, files={(_t2 - _t1):.3f}s, config={(_t3 - _t2):.3f}s, total={(_t3 - _t0):.3f}s")
        except Exception:
            pass
        print(f"测试目录: {cls.test_dir}")
    
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        _t0 = time.perf_counter()
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
        _t1 = time.perf_counter()
        try:
            for _ in range(50):
                QCoreApplication.processEvents()
                QTest.qWait(5)
        except Exception:
            pass
        try:
            if getattr(cls, "_created_app", False):
                cls.app.quit()
        except Exception:
            pass
        _t2 = time.perf_counter()
        try:
            print(f"[CLASS TEARDOWN TIMERS] rmtree={(_t1 - _t0):.3f}s, app.quit={(_t2 - _t1):.3f}s, total={(_t2 - _t0):.3f}s")
        except Exception:
            pass
    
    @classmethod
    def _create_test_files(cls):
        """创建测试文件"""
        # Markdown文件
        markdown_content = """# 测试Markdown文件

这是一个测试用的Markdown文件。

## 功能列表
- 文件解析
- Markdown渲染
- 内容预览
- 文件树显示

## 代码示例
```python
def test_function():
    print("Hello, World!")
    return True
```

## 表格示例
| 组件 | 状态 | 描述 |
|------|------|------|
| FileResolver | ✅ | 文件解析器 |
| MarkdownRenderer | ✅ | Markdown渲染器 |
| ContentPreview | ✅ | 内容预览器 |
| FileTree | ✅ | 文件树组件 |
| ContentViewer | ✅ | 内容显示组件 |
"""
        
        markdown_file = os.path.join(cls.test_dir, "test.md")
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        cls.test_files['markdown'] = markdown_file
        
        # Python文件
        python_content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
测试Python文件
\"\"\"

import sys
import os
from pathlib import Path

def main():
    \"\"\"主函数\"\"\"
    print("Hello, World!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""
        
        python_file = os.path.join(cls.test_dir, "test.py")
        with open(python_file, 'w', encoding='utf-8') as f:
            f.write(python_content)
        cls.test_files['python'] = python_file
        
        # 文本文件
        text_content = """这是一个测试文本文件。

包含以下内容：
1. 中文文本
2. English text
3. 数字: 123456
4. 特殊字符: !@#$%^&*()

文件用于测试文本文件的显示功能。
"""
        
        text_file = os.path.join(cls.test_dir, "test.txt")
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text_content)
        cls.test_files['text'] = text_file
        
        # JSON文件
        json_content = """{
    "name": "测试JSON文件",
    "version": "1.0.0",
    "description": "用于测试JSON文件显示",
    "components": [
        {
            "name": "FileResolver",
            "status": "working",
            "description": "文件解析器"
        },
        {
            "name": "MarkdownRenderer", 
            "status": "working",
            "description": "Markdown渲染器"
        },
        {
            "name": "ContentPreview",
            "status": "working", 
            "description": "内容预览器"
        }
    ],
    "settings": {
        "cache_enabled": true,
        "max_file_size": 5242880,
        "supported_formats": ["md", "py", "txt", "json"]
    }
}
"""
        
        json_file = os.path.join(cls.test_dir, "test.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            f.write(json_content)
        cls.test_files['json'] = json_file
        
        # 大文件（用于性能测试）
        large_content = "# 大文件测试\n\n" + "这是第{}行内容。\n".format(1) * 1000
        
        large_file = os.path.join(cls.test_dir, "large.md")
        with open(large_file, 'w', encoding='utf-8') as f:
            f.write(large_content)
        cls.test_files['large'] = large_file
    
    def setUp(self):
        """每个测试用例初始化"""
        self._t_setup_start = time.perf_counter()
        self.window = IntegratedMainWindow()
        _t_after_create = time.perf_counter()
        self.window.show()
        _t_after_show = time.perf_counter()
        QTest.qWait(100)
        _t_after_wait = time.perf_counter()
        try:
            print(f"[SETUP TIMERS] create={(_t_after_create - self._t_setup_start):.3f}s, show={(_t_after_show - _t_after_create):.3f}s, wait={(_t_after_wait - _t_after_show):.3f}s, total={(_t_after_wait - self._t_setup_start):.3f}s")
        except Exception:
            pass
    
    def tearDown(self):
        """每个测试用例清理"""
        _t0 = time.perf_counter()
        self.window.close()
        _t1 = time.perf_counter()
        QTest.qWait(100)
        _t2 = time.perf_counter()
        try:
            if hasattr(self.window, 'file_tree'):
                try:
                    ft = self.window.file_tree
                    try:
                        if getattr(ft, 'tree_view', None):
                            ft.tree_view.setModel(None)
                    except Exception:
                        pass
                    try:
                        if getattr(ft, 'proxy_model', None):
                            ft.proxy_model.deleteLater()
                            ft.proxy_model = None
                    except Exception:
                        pass
                    try:
                        if getattr(ft, 'file_model', None):
                            ft.file_model.deleteLater()
                            ft.file_model = None
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            pass
        try:
            self.window.deleteLater()
        except Exception:
            pass
        try:
            for _ in range(50):
                QCoreApplication.processEvents()
                QTest.qWait(5)
        except Exception:
            pass
        try:
            import gc
            gc.collect()
        except Exception:
            pass
        _t3 = time.perf_counter()
        try:
            print(f"[TEARDOWN TIMERS] close={(_t1 - _t0):.3f}s, wait={(_t2 - _t1):.3f}s, processEvents={(_t3 - _t2):.3f}s, total={(_t3 - _t0):.3f}s")
        except Exception:
            pass
    
    def test_01_component_initialization(self):
        """测试组件初始化"""
        print("\n=== 测试组件初始化 ===")
        
        # 检查核心组件是否正确初始化
        self.assertIsNotNone(self.window.file_resolver)
        self.assertIsNotNone(self.window.markdown_renderer)
        self.assertIsNotNone(self.window.content_preview)
        
        # 检查UI组件是否正确初始化
        self.assertIsNotNone(self.window.file_tree)
        self.assertIsNotNone(self.window.content_viewer)
        
        # 检查组件可用性
        self.assertTrue(self.window.file_resolver.is_available())
        self.assertTrue(self.window.markdown_renderer.is_available())
        self.assertTrue(self.window.content_preview.is_supported_file(self.test_files['markdown']))
        
        print("✅ 所有组件初始化成功")
    
    def test_02_file_tree_functionality(self):
        """测试文件树功能"""
        print("\n=== 测试文件树功能 ===")
        
        # 设置根目录
        self.window.file_tree.set_root_path(self.test_dir)
        QTest.qWait(500)  # 等待文件树加载
        
        # 检查文件数量
        file_count = self.window.file_tree.get_file_count()
        self.assertGreater(file_count, 0)
        print(f"✅ 文件树加载成功，文件数量: {file_count}")
        
        # 测试文件过滤
        self.window.file_tree.filter_files(["*.md"])
        QTest.qWait(100)
        
        # 测试搜索功能
        self.window.file_tree.search_files("test")
        QTest.qWait(100)
        
        print("✅ 文件树功能测试通过")
    
    def test_03_file_selection_flow(self):
        """测试文件选择流程"""
        print("\n=== 测试文件选择流程 ===")
        
        # 设置根目录
        self.window.file_tree.set_root_path(self.test_dir)
        QTest.qWait(500)
        
        # 选择Markdown文件
        markdown_file = self.test_files['markdown']
        self.window.file_tree.select_file(markdown_file)
        QTest.qWait(1000)  # 等待内容加载
        
        # 检查当前文件
        current_file = self.window.content_viewer.get_current_file()
        self.assertEqual(current_file, markdown_file)
        
        # 检查状态栏
        status_text = self.window.statusBar().currentMessage()
        self.assertIn("已加载", status_text)
        
        print("✅ 文件选择流程测试通过")
    
    def test_04_content_display_flow(self):
        """测试内容显示流程"""
        print("\n=== 测试内容显示流程 ===")
        
        # 测试Markdown文件显示
        markdown_file = self.test_files['markdown']
        self.window.content_viewer.display_file(markdown_file)
        QTest.qWait(1000)
        
        # 检查内容是否加载
        current_file = self.window.content_viewer.get_current_file()
        self.assertEqual(current_file, markdown_file)
        
        # 测试Python文件显示
        python_file = self.test_files['python']
        self.window.content_viewer.display_file(python_file)
        QTest.qWait(1000)
        
        # 测试文本文件显示
        text_file = self.test_files['text']
        self.window.content_viewer.display_file(text_file)
        QTest.qWait(1000)
        
        # 测试JSON文件显示
        json_file = self.test_files['json']
        self.window.content_viewer.display_file(json_file)
        QTest.qWait(1000)
        
        print("✅ 内容显示流程测试通过")
    
    def test_05_error_handling(self):
        """测试错误处理"""
        print("\n=== 测试错误处理 ===")
        
        # 测试不存在文件
        non_existent_file = os.path.join(self.test_dir, "non_existent.md")
        self.window.content_viewer.display_file(non_existent_file)
        QTest.qWait(500)
        
        # 测试不支持的文件类型
        unsupported_file = os.path.join(self.test_dir, "test.exe")
        with open(unsupported_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03')
        
        self.window.content_viewer.display_file(unsupported_file)
        QTest.qWait(500)
        
        print("✅ 错误处理测试通过")
    
    def test_06_performance_test(self):
        """测试性能"""
        print("\n=== 测试性能 ===")
        
        # 测试大文件加载性能
        large_file = self.test_files['large']
        
        start_time = time.time()
        self.window.content_viewer.display_file(large_file)
        QTest.qWait(2000)  # 等待加载完成
        end_time = time.time()
        
        load_time = end_time - start_time
        print(f"大文件加载时间: {load_time:.3f}秒")
        
        # 性能要求：大文件加载时间 < 3秒
        self.assertLess(load_time, 3.0)
        
        # 测试缓存功能
        cache_info = self.window.content_viewer.get_cache_info()
        self.assertIsInstance(cache_info, dict)
        self.assertIn('total', cache_info)
        self.assertIn('limit', cache_info)
        
        print("✅ 性能测试通过")
    
    def test_07_cache_functionality(self):
        """测试缓存功能"""
        print("\n=== 测试缓存功能 ===")
        
        # 获取初始缓存信息
        initial_cache = self.window.content_viewer.get_cache_info()
        
        # 加载文件
        markdown_file = self.test_files['markdown']
        self.window.content_viewer.display_file(markdown_file)
        QTest.qWait(500)
        
        # 再次加载相同文件（应该使用缓存）
        self.window.content_viewer.display_file(markdown_file)
        QTest.qWait(500)
        
        # 检查缓存是否工作
        final_cache = self.window.content_viewer.get_cache_info()
        self.assertGreaterEqual(final_cache['total'], initial_cache['total'])
        
        # 测试清除缓存
        self.window.content_viewer.clear_cache()
        cleared_cache = self.window.content_viewer.get_cache_info()
        self.assertEqual(cleared_cache['total'], 0)
        
        print("✅ 缓存功能测试通过")
    
    def test_08_signal_connections(self):
        """测试信号连接"""
        print("\n=== 测试信号连接 ===")
        
        # 测试文件选择信号
        signal_received = False
        file_path_received = ""
        
        def on_file_selected(file_path):
            nonlocal signal_received, file_path_received
            signal_received = True
            file_path_received = file_path
        
        self.window.file_selected.connect(on_file_selected)
        
        # 触发文件选择
        markdown_file = self.test_files['markdown']
        self.window.file_tree.select_file(markdown_file)
        QTest.qWait(500)
        
        # 检查信号是否被触发
        self.assertTrue(signal_received)
        self.assertEqual(file_path_received, markdown_file)
        
        print("✅ 信号连接测试通过")
    
    def test_09_menu_functionality(self):
        """测试菜单功能"""
        print("\n=== 测试菜单功能 ===")
        
        # 测试打开文件菜单
        # 注意：这里只是测试菜单项是否存在，实际文件对话框需要用户交互
        
        # 测试刷新功能
        markdown_file = self.test_files['markdown']
        self.window.content_viewer.display_file(markdown_file)
        QTest.qWait(500)
        
        # 模拟刷新操作
        self.window._refresh_current_file()
        QTest.qWait(500)
        
        # 测试缩放功能
        if self.window.content_viewer.is_web_engine_available():
            self.window._zoom_in()
            QTest.qWait(100)
            self.window._zoom_out()
            QTest.qWait(100)
            self.window._reset_zoom()
            QTest.qWait(100)
        
        print("✅ 菜单功能测试通过")
    
    def test_10_end_to_end_workflow(self):
        """测试端到端工作流程"""
        print("\n=== 测试端到端工作流程 ===")
        
        # 1. 设置根目录
        self.window.file_tree.set_root_path(self.test_dir)
        QTest.qWait(500)
        
        # 2. 选择文件
        markdown_file = self.test_files['markdown']
        self.window.file_tree.select_file(markdown_file)
        QTest.qWait(1000)
        
        # 3. 验证内容显示
        current_file = self.window.content_viewer.get_current_file()
        self.assertEqual(current_file, markdown_file)
        
        # 4. 切换到其他文件
        python_file = self.test_files['python']
        self.window.file_tree.select_file(python_file)
        QTest.qWait(1000)
        
        # 5. 验证内容更新
        current_file = self.window.content_viewer.get_current_file()
        self.assertEqual(current_file, python_file)
        
        # 6. 测试文件过滤
        self.window.file_tree.filter_files(["*.md"])
        QTest.qWait(100)
        
        # 7. 测试搜索
        self.window.file_tree.search_files("test")
        QTest.qWait(100)
        
        print("✅ 端到端工作流程测试通过")
    
    def test_11_memory_usage(self):
        """测试内存使用"""
        print("\n=== 测试内存使用 ===")
        
        # 加载多个文件
        for file_type, file_path in self.test_files.items():
            self.window.content_viewer.display_file(file_path)
            QTest.qWait(500)
        
        # 检查缓存信息
        cache_info = self.window.content_viewer.get_cache_info()
        self.assertLessEqual(cache_info['total'], cache_info['limit'])
        
        # 清除缓存
        self.window.content_viewer.clear_cache()
        cleared_cache = self.window.content_viewer.get_cache_info()
        self.assertEqual(cleared_cache['total'], 0)
        
        print("✅ 内存使用测试通过")
    
    def test_12_configuration_integration(self):
        """测试配置集成"""
        print("\n=== 测试配置集成 ===")
        
        # 检查配置管理器
        self.assertIsNotNone(self.window.config_manager)
        
        # 检查配置项
        window_title = self.window.config_manager.get_config("app.window.title")
        self.assertIsNotNone(window_title)
        
        # 检查文件类型配置
        file_types = self.window.config_manager.load_file_types_config()
        self.assertIsInstance(file_types, dict)
        self.assertIn('markdown_files', file_types)
        
        print("✅ 配置集成测试通过")


def run_integration_tests():
    """运行集成测试"""
    print("开始集成测试...")
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(IntegrationTest)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果
    print(f"\n测试结果:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # 运行集成测试
    success = run_integration_tests()
    
    if success:
        print("\n🎉 所有集成测试通过！")
        sys.exit(0)
    else:
        print("\n❌ 部分集成测试失败！")
        sys.exit(1) 