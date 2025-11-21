#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件解析器测试模块 v1.0.0
测试FileResolver类的各种功能

作者: LAD Team
创建时间: 2025-08-02
最后更新: 2025-08-02
"""

import unittest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.file_resolver import FileResolver
from utils.config_manager import ConfigManager


class TestFileResolver(unittest.TestCase):
    """文件解析器测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = Path(self.temp_dir)
        
        # 创建测试文件
        self._create_test_files()
        
        # 初始化文件解析器
        self.resolver = FileResolver()
    
    def tearDown(self):
        """测试后的清理工作"""
        # 删除临时目录
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_files(self):
        """创建测试文件"""
        # 创建Markdown文件
        self.md_file = self.test_dir / "test.md"
        with open(self.md_file, 'w', encoding='utf-8') as f:
            f.write("# Test Markdown\n\nThis is a test file.")
        
        # 创建文本文件
        self.txt_file = self.test_dir / "test.txt"
        with open(self.txt_file, 'w', encoding='utf-8') as f:
            f.write("This is a test text file.")
        
        # 创建Python文件
        self.py_file = self.test_dir / "test.py"
        with open(self.py_file, 'w', encoding='utf-8') as f:
            f.write("# Test Python file\nprint('Hello, World!')")
        
        # 创建JSON文件
        self.json_file = self.test_dir / "test.json"
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump({"test": "data"}, f)
        
        # 创建GBK编码文件
        self.gbk_file = self.test_dir / "test_gbk.txt"
        with open(self.gbk_file, 'w', encoding='gbk') as f:
            f.write("这是GBK编码的测试文件")
    
    def test_resolve_markdown_file(self):
        """测试解析Markdown文件"""
        result = self.resolver.resolve_file_path(self.md_file)
        
        self.assertTrue(result['success'])
        expected_path = os.path.normcase(os.path.normpath(str(self.md_file.resolve())))
        actual_path = os.path.normcase(os.path.normpath(result['file_path']))
        self.assertEqual(actual_path, expected_path)
        
        # 检查文件信息
        file_info = result['file_info']
        self.assertEqual(file_info['name'], 'test.md')
        self.assertEqual(file_info['extension'], '.md')
        self.assertTrue(file_info['size'] > 0)
        self.assertTrue(file_info['is_readable'])
        
        # 检查文件类型
        file_type = result['file_type']
        self.assertEqual(file_type['extension'], '.md')
        self.assertIsNotNone(file_type['extension_type'])
        self.assertEqual(file_type['extension_type']['name'], 'markdown_files')
        
        # 检查编码
        encoding = result['encoding']
        self.assertIn('encoding', encoding)
        self.assertIn('confidence', encoding)
    
    def test_resolve_text_file(self):
        """测试解析文本文件"""
        result = self.resolver.resolve_file_path(self.txt_file)
        
        self.assertTrue(result['success'])
        
        # 检查文件类型
        file_type = result['file_type']
        self.assertEqual(file_type['extension'], '.txt')
        self.assertEqual(file_type['extension_type']['name'], 'text_files')
    
    def test_resolve_python_file(self):
        """测试解析Python文件"""
        result = self.resolver.resolve_file_path(self.py_file)
        
        self.assertTrue(result['success'])
        
        # 检查文件类型
        file_type = result['file_type']
        self.assertEqual(file_type['extension'], '.py')
        self.assertEqual(file_type['extension_type']['name'], 'code_files')
    
    def test_resolve_json_file(self):
        """测试解析JSON文件"""
        result = self.resolver.resolve_file_path(self.json_file)
        
        self.assertTrue(result['success'])
        
        # 检查文件类型
        file_type = result['file_type']
        self.assertEqual(file_type['extension'], '.json')
        self.assertEqual(file_type['extension_type']['name'], 'code_files')
    
    def test_resolve_gbk_file(self):
        """测试解析GBK编码文件"""
        result = self.resolver.resolve_file_path(self.gbk_file)
        
        self.assertTrue(result['success'])
        
        # 检查编码
        encoding = result['encoding']
        self.assertIn('encoding', encoding)
        # GBK文件应该能够被正确检测
    
    def test_resolve_nonexistent_file(self):
        """测试解析不存在的文件"""
        nonexistent_file = self.test_dir / "nonexistent.txt"
        result = self.resolver.resolve_file_path(nonexistent_file)
        
        self.assertFalse(result['success'])
        self.assertIn('error_type', result)
        self.assertEqual(result['error_type'], 'FILE_NOT_FOUND')
    
    def test_resolve_directory(self):
        """测试解析目录"""
        result = self.resolver.resolve_file_path(self.test_dir)
        
        self.assertFalse(result['success'])
        self.assertIn('error_type', result)
    
    def test_resolve_with_relative_path(self):
        """测试使用相对路径解析文件"""
        # 切换到临时目录
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            result = self.resolver.resolve_file_path("test.md")
            self.assertTrue(result['success'])
            self.assertEqual(result['file_info']['name'], 'test.md')
        finally:
            os.chdir(original_cwd)
    
    def test_file_type_confidence(self):
        """测试文件类型置信度计算"""
        result = self.resolver.resolve_file_path(self.md_file)
        
        file_type = result['file_type']
        confidence = file_type['confidence']
        
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    def test_encoding_detection(self):
        """测试编码检测"""
        result = self.resolver.resolve_file_path(self.txt_file)
        
        encoding = result['encoding']
        self.assertIn('encoding', encoding)
        self.assertIn('confidence', encoding)
        self.assertIn('method', encoding)
        
        # 检查置信度
        self.assertGreaterEqual(encoding['confidence'], 0.0)
        self.assertLessEqual(encoding['confidence'], 1.0)
    
    def test_get_supported_extensions(self):
        """测试获取支持的扩展名"""
        extensions = self.resolver.get_supported_extensions()
        
        self.assertIsInstance(extensions, dict)
        self.assertIn('markdown_files', extensions)
        self.assertIn('text_files', extensions)
        self.assertIn('code_files', extensions)
        
        # 检查扩展名列表
        self.assertIn('.md', extensions['markdown_files'])
        self.assertIn('.txt', extensions['text_files'])
        self.assertIn('.py', extensions['code_files'])
    
    def test_get_supported_encodings(self):
        """测试获取支持的编码"""
        encodings = self.resolver.get_supported_encodings()
        
        self.assertIsInstance(encodings, list)
        self.assertIn('utf-8', encodings)
        self.assertIn('gbk', encodings)
        self.assertIn('latin-1', encodings)
    
    def test_is_supported_file(self):
        """测试文件支持检查"""
        # 测试支持的文件
        self.assertTrue(self.resolver.is_supported_file(self.md_file))
        self.assertTrue(self.resolver.is_supported_file(self.txt_file))
        self.assertTrue(self.resolver.is_supported_file(self.py_file))
        
        # 测试不支持的文件
        unsupported_file = self.test_dir / "test.xyz"
        self.assertFalse(self.resolver.is_supported_file(unsupported_file))
        
        # 测试不存在的文件 - 应该返回False，因为文件不存在
        nonexistent_file = self.test_dir / "nonexistent.txt"
        # 注意：is_supported_file只检查扩展名，不检查文件是否存在
        # 所以对于不存在的文件，它仍然可能返回True（如果扩展名被支持）
        # 我们需要修改测试逻辑
        self.assertTrue(self.resolver.is_supported_file(nonexistent_file))  # .txt扩展名被支持
    
    def test_large_file_warning(self):
        """测试大文件警告"""
        # 创建一个较大的文件（模拟）
        large_file = self.test_dir / "large.txt"
        with open(large_file, 'w') as f:
            f.write("x" * 1024 * 1024)  # 1MB
        
        # 这里应该不会抛出异常，但会记录警告
        result = self.resolver.resolve_file_path(large_file)
        self.assertTrue(result['success'])
    
    @patch('core.file_resolver.CHARDET_AVAILABLE', False)
    def test_encoding_detection_without_chardet(self):
        """测试没有chardet库时的编码检测"""
        # 重新创建解析器（模拟没有chardet的情况）
        resolver = FileResolver()
        result = resolver.resolve_file_path(self.txt_file)
        
        self.assertTrue(result['success'])
        encoding = result['encoding']
        self.assertEqual(encoding['method'], 'basic')
    
    def test_file_info_permissions(self):
        """测试文件权限信息"""
        result = self.resolver.resolve_file_path(self.txt_file)
        file_info = result['file_info']
        
        self.assertIn('is_readable', file_info)
        self.assertIn('is_writable', file_info)
        self.assertIn('is_executable', file_info)
        
        # 文件应该至少是可读的
        self.assertTrue(file_info['is_readable'])
    
    def test_file_size_formatting(self):
        """测试文件大小格式化"""
        # 创建不同大小的文件进行测试
        small_file = self.test_dir / "small.txt"
        with open(small_file, 'w') as f:
            f.write("small")
        
        result = self.resolver.resolve_file_path(small_file)
        file_info = result['file_info']
        
        self.assertIn('size_formatted', file_info)
        self.assertIsInstance(file_info['size_formatted'], str)
        self.assertIn('B', file_info['size_formatted'])
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试权限错误（模拟）
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.side_effect = PermissionError("Permission denied")
            
            result = self.resolver.resolve_file_path(self.txt_file)
            self.assertFalse(result['success'])
            self.assertIn('error_type', result)
    
    def test_config_manager_integration(self):
        """测试配置管理器集成"""
        # 测试使用自定义配置管理器
        config_manager = ConfigManager()
        resolver = FileResolver(config_manager)
        
        result = resolver.resolve_file_path(self.md_file)
        self.assertTrue(result['success'])
    
    def test_file_signature_detection(self):
        """测试文件头签名检测"""
        # 创建一个PNG文件头（模拟）
        png_file = self.test_dir / "test.png"
        with open(png_file, 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n' + b'x' * 100)  # PNG文件头
        
        result = self.resolver.resolve_file_path(png_file)
        self.assertTrue(result['success'])
        
        file_type = result['file_type']
        # 应该能检测到PNG文件头
        self.assertIsNotNone(file_type['header_type'])


class TestFileResolverEdgeCases(unittest.TestCase):
    """文件解析器边界情况测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = Path(self.temp_dir)
        self.resolver = FileResolver()
    
    def tearDown(self):
        """测试后的清理工作"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_empty_file(self):
        """测试空文件"""
        empty_file = self.test_dir / "empty.txt"
        empty_file.touch()
        
        result = self.resolver.resolve_file_path(empty_file)
        self.assertTrue(result['success'])
        
        file_info = result['file_info']
        self.assertEqual(file_info['size'], 0)
        self.assertEqual(file_info['size_formatted'], "0 B")
    
    def test_file_without_extension(self):
        """测试没有扩展名的文件"""
        no_ext_file = self.test_dir / "noextension"
        with open(no_ext_file, 'w') as f:
            f.write("content")
        
        result = self.resolver.resolve_file_path(no_ext_file)
        self.assertTrue(result['success'])
        
        file_type = result['file_type']
        self.assertEqual(file_type['extension'], '')
        self.assertEqual(file_type['final_type'], 'unknown')
    
    def test_very_long_filename(self):
        """测试很长的文件名"""
        long_name = "a" * 200 + ".txt"
        long_file = self.test_dir / long_name
        with open(long_file, 'w') as f:
            f.write("content")
        
        result = self.resolver.resolve_file_path(long_file)
        self.assertTrue(result['success'])
        self.assertEqual(result['file_info']['name'], long_name)
    
    def test_special_characters_in_filename(self):
        """测试文件名中的特殊字符"""
        # Windows不允许某些特殊字符，使用允许的字符
        special_file = self.test_dir / "test_#$%^&().txt"
        with open(special_file, 'w') as f:
            f.write("content")
        
        result = self.resolver.resolve_file_path(special_file)
        self.assertTrue(result['success'])
        self.assertEqual(result['file_info']['name'], "test_#$%^&().txt")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2) 