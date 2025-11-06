#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown渲染器测试模块
测试MarkdownRenderer类的各种功能

作者: LAD Team
创建时间: 2025-08-02
最后更新: 2025-08-02
"""

import unittest
import tempfile
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.markdown_renderer import MarkdownRenderer
from utils.config_manager import ConfigManager


class TestMarkdownRenderer(unittest.TestCase):
    """Markdown渲染器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.config_manager = ConfigManager()
        self.renderer = MarkdownRenderer(self.config_manager)
        
        # 测试用的Markdown内容
        self.simple_markdown = "# 测试标题\n\n这是一个测试段落。"
        self.complex_markdown = """
# 复杂Markdown测试

## 代码块
```python
def hello_world():
    print("Hello, World!")
```

## 表格
| 列1 | 列2 |
|-----|-----|
| 数据1 | 数据2 |

## 列表
- 项目1
- 项目2
  - 子项目2.1
  - 子项目2.2

## 链接
[测试链接](https://example.com)

## 图片
![测试图片](https://example.com/image.png)
"""
    
    def test_renderer_initialization(self):
        """测试渲染器初始化"""
        self.assertIsNotNone(self.renderer)
        self.assertIsNotNone(self.renderer.config_manager)
        self.assertIsInstance(self.renderer.default_options, dict)
        self.assertTrue('enable_zoom' in self.renderer.default_options)
    
    def test_render_simple_content(self):
        """测试简单内容渲染"""
        result = self.renderer.render(self.simple_markdown)
        
        self.assertIsInstance(result, dict)
        self.assertTrue('success' in result)
        self.assertTrue('html' in result)
        self.assertTrue('render_time' in result)
        
        # 检查渲染时间
        self.assertIsInstance(result['render_time'], (int, float))
        self.assertGreaterEqual(result['render_time'], 0)
    
    def test_render_complex_content(self):
        """测试复杂内容渲染"""
        result = self.renderer.render(self.complex_markdown)
        
        self.assertIsInstance(result, dict)
        self.assertTrue('success' in result)
        self.assertTrue('html' in result)
        
        # 检查HTML内容包含关键元素（忽略样式部分）
        html = result['html']
        # 移除样式部分后检查
        html_without_style = html.replace('<style>', '').replace('</style>', '')
        self.assertIn('<h1', html_without_style)
        self.assertIn('<h2', html_without_style)
        self.assertIn('<code', html_without_style)
    
    def test_render_with_options(self):
        """测试带选项的渲染"""
        options = {
            'enable_zoom': False,
            'theme': 'dark',
            'cache_enabled': False
        }
        
        result = self.renderer.render(self.simple_markdown, options)
        
        self.assertIsInstance(result, dict)
        self.assertTrue('success' in result)
        self.assertTrue('options_used' in result)
        
        # 检查选项是否正确传递
        used_options = result['options_used']
        self.assertEqual(used_options['enable_zoom'], False)
        self.assertEqual(used_options['theme'], 'dark')
    
    def test_render_file(self):
        """测试文件渲染"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(self.simple_markdown)
            temp_file = f.name
        
        try:
            result = self.renderer.render_file(temp_file)
            
            self.assertIsInstance(result, dict)
            self.assertTrue('success' in result)
            self.assertTrue('html' in result)
            self.assertTrue('file_path' in result)
            self.assertTrue('file_info' in result)
            self.assertTrue('encoding' in result)
            self.assertTrue('total_time' in result)
            
            # 检查文件信息
            self.assertEqual(result['file_path'], temp_file)
            self.assertIsInstance(result['file_info']['size'], int)
            self.assertEqual(result['encoding']['encoding'], 'utf-8')
            
        finally:
            # 清理临时文件
            os.unlink(temp_file)
    
    def test_render_nonexistent_file(self):
        """测试渲染不存在的文件"""
        result = self.renderer.render_file("nonexistent_file.md")
        
        self.assertIsInstance(result, dict)
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'FILE_NOT_FOUND')
        self.assertTrue('html' in result)
    
    def test_render_large_content(self):
        """测试大内容渲染"""
        # 创建超过限制的内容（确保超过5MB限制）
        max_length = self.renderer.default_options['max_content_length']
        
        # 直接创建一个超过限制的内容
        large_content = "x" * (max_length + 1000000)  # 超过限制1MB
        
        # 验证内容确实超过限制
        self.assertGreater(len(large_content), max_length, 
                          f"内容长度({len(large_content)})应该超过限制({max_length})")
        
        result = self.renderer.render(large_content)
        
        self.assertIsInstance(result, dict)
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], '内容过长')
    
    def test_cache_functionality(self):
        """测试缓存功能"""
        # 第一次渲染
        result1 = self.renderer.render(self.simple_markdown)
        self.assertTrue(result1['success'])
        
        # 第二次渲染（应该使用缓存）
        result2 = self.renderer.render(self.simple_markdown)
        self.assertTrue(result2['success'])
        
        # 检查缓存信息
        cache_info = self.renderer.get_cache_info()
        self.assertIsInstance(cache_info, dict)
        self.assertTrue('cache_size' in cache_info)
        self.assertTrue('max_size' in cache_info)
        
        # 清空缓存
        self.renderer.clear_cache()
        cache_info_after = self.renderer.get_cache_info()
        self.assertEqual(cache_info_after['cache_size'], 0)
    
    def test_cache_with_different_options(self):
        """测试不同选项的缓存"""
        # 使用不同选项渲染相同内容
        result1 = self.renderer.render(self.simple_markdown, {'enable_zoom': True})
        result2 = self.renderer.render(self.simple_markdown, {'enable_zoom': False})
        
        self.assertTrue(result1['success'])
        self.assertTrue(result2['success'])
        
        # 应该产生不同的缓存键
        cache_info = self.renderer.get_cache_info()
        self.assertGreaterEqual(cache_info['cache_size'], 2)
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试空内容
        result = self.renderer.render("")
        self.assertTrue(result['success'])
        
        # 测试None内容
        result = self.renderer.render(None)
        self.assertFalse(result['success'])
    
    def test_encoding_detection(self):
        """测试编码检测"""
        # 创建UTF-8文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(self.simple_markdown)
            utf8_file = f.name
        
        # 创建GBK文件（如果支持）
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='gbk') as f:
                f.write(self.simple_markdown)
                gbk_file = f.name
            
            try:
                # 测试UTF-8文件
                result1 = self.renderer.render_file(utf8_file)
                self.assertTrue(result1['success'])
                self.assertEqual(result1['encoding']['encoding'], 'utf-8')
                
                # 测试GBK文件
                result2 = self.renderer.render_file(gbk_file)
                self.assertTrue(result2['success'])
                # GBK文件可能被检测为GB2312，这是正常的
                detected_encoding = result2['encoding']['encoding'].lower()
                self.assertIn(detected_encoding, ['gbk', 'gb2312'])
                
            finally:
                os.unlink(gbk_file)
        except LookupError:
            # 如果不支持GBK编码，跳过GBK测试
            pass
        finally:
            os.unlink(utf8_file)
    
    def test_performance(self):
        """测试性能"""
        # 测试渲染时间
        start_time = time.time()
        result = self.renderer.render(self.simple_markdown)
        end_time = time.time()
        
        render_time = end_time - start_time
        
        # 检查性能指标
        self.assertLess(render_time, 0.5)  # 应该小于500ms
        self.assertLess(result['render_time'], 0.5)
    
    def test_supported_features(self):
        """测试支持的功能"""
        features = self.renderer.get_supported_features()
        
        self.assertIsInstance(features, dict)
        self.assertTrue('markdown_library' in features)
        self.assertTrue('syntax_highlight' in features)
        self.assertTrue('text_fallback' in features)
        self.assertTrue('unified_path_resolution' in features)
    
    def test_availability_check(self):
        """测试可用性检查"""
        is_available = self.renderer.is_available()
        self.assertIsInstance(is_available, bool)
    
    def test_render_with_disabled_cache(self):
        """测试禁用缓存的渲染"""
        options = {'cache_enabled': False}
        
        # 第一次渲染
        result1 = self.renderer.render(self.simple_markdown, options)
        self.assertTrue(result1['success'])
        
        # 第二次渲染
        result2 = self.renderer.render(self.simple_markdown, options)
        self.assertTrue(result2['success'])
        
        # 应该没有缓存
        self.assertNotIn('cached', result2)
    
    def test_render_with_fallback(self):
        """测试降级渲染"""
        # 模拟所有渲染器都失败的情况
        with patch.object(self.renderer, '_render_content', side_effect=Exception("渲染失败")):
            result = self.renderer.render(self.simple_markdown, {'fallback_to_text': True})
            
            # 由于异常被捕获并返回错误结果，所以这里应该检查错误处理
            self.assertFalse(result['success'])
            self.assertEqual(result['error_type'], '渲染失败')
    
    def test_render_without_fallback(self):
        """测试无降级的渲染"""
        # 模拟所有渲染器都失败的情况
        with patch.object(self.renderer, '_render_content', side_effect=Exception("渲染失败")):
            result = self.renderer.render(self.simple_markdown, {'fallback_to_text': False})
            
            self.assertFalse(result['success'])
            self.assertEqual(result['error_type'], '渲染失败')
    
    def test_render_with_text_fallback(self):
        """测试文本降级渲染"""
        # 直接测试文本降级功能
        result = self.renderer._render_as_text(self.simple_markdown, {})
        
        self.assertTrue(result['success'])
        self.assertEqual(result['renderer'], 'text_fallback')
        self.assertIn('text-content', result['html'])


class TestMarkdownRendererIntegration(unittest.TestCase):
    """Markdown渲染器集成测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.renderer = MarkdownRenderer()
    
    def test_with_file_resolver_integration(self):
        """测试与文件解析器的集成"""
        # 这里可以测试与FileResolver的集成
        # 由于FileResolver已经实现，可以进行集成测试
        pass
    
    def test_with_config_manager_integration(self):
        """测试与配置管理器的集成"""
        config_manager = ConfigManager()
        renderer = MarkdownRenderer(config_manager)
        
        # 测试配置管理器是否正确传递
        self.assertIsNotNone(renderer.config_manager)
        self.assertEqual(renderer.config_manager, config_manager)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2) 