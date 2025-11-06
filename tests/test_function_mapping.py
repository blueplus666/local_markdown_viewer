#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
函数映射测试用例
LAD-IMPL-009: 基础功能验证 - P3级别改进要求
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.dynamic_module_importer import DynamicModuleImporter


def test_successful_function_mapping():
    """测试函数映射成功的情况"""
    importer = DynamicModuleImporter()
    result = importer.import_module('markdown_processor')
    
    # 验证基本字段
    assert result['success'] is True
    assert result['module'] == 'markdown_processor'
    assert result['used_fallback'] is False
    assert result['function_mapping_status'] == 'complete'
    
    # 验证函数映射
    assert 'functions' in result
    assert 'render_markdown_with_zoom' in result['functions']
    assert 'render_markdown_to_html' in result['functions']
    
    # 验证函数可调用
    assert callable(result['functions']['render_markdown_with_zoom'])
    assert callable(result['functions']['render_markdown_to_html'])
    
    # 验证必需函数列表
    assert 'required_functions' in result
    assert 'render_markdown_with_zoom' in result['required_functions']
    assert 'render_markdown_to_html' in result['required_functions']
    
    # 验证可用函数列表
    assert 'available_functions' in result
    assert 'render_markdown_with_zoom' in result['available_functions']
    assert 'render_markdown_to_html' in result['available_functions']


def test_missing_functions():
    """测试函数缺失的情况"""
    # 模拟缺失函数的情况（需要修改配置或使用mock）
    importer = DynamicModuleImporter()
    
    # 临时修改配置，要求一个不存在的函数
    original_paths = importer._module_paths.copy()
    
    # 修改配置以添加一个不存在的函数
    if 'markdown_processor' in importer._module_paths:
        importer._module_paths['markdown_processor']['required_functions'] = [
            'render_markdown_with_zoom', 
            'render_markdown_to_html',
            'non_existent_function'  # 不存在的函数
        ]
    
    try:
        result = importer.import_module('markdown_processor')
        
        # 验证失败状态
        assert result['success'] is False
        assert result['function_mapping_status'] == 'incomplete'
        assert 'missing_functions' in result
        assert 'non_existent_function' in result['missing_functions']
        assert 'error_code' in result
        assert 'message' in result
        
    finally:
        # 恢复原始配置
        importer._module_paths = original_paths


def test_non_callable_functions():
    """测试函数不可调用的情况"""
    # 模拟不可调用函数的情况（需要mock）
    importer = DynamicModuleImporter()
    
    # Mock _import_markdown_processor方法返回不可调用的函数
    with patch.object(importer, '_import_markdown_processor') as mock_import:
        mock_import.return_value = {
            'success': False,
            'module': 'markdown_processor',
            'path': '',
            'functions': {},
            'error_code': 'MISSING_SYMBOLS',
            'message': '函数映射验证失败: 函数不可调用: render_markdown_with_zoom',
            'attempted_paths': [],
            'used_fallback': False,
            'missing_functions': [],
            'non_callable_functions': ['render_markdown_with_zoom'],
            'validation_details': '函数不可调用: render_markdown_with_zoom',
            'function_mapping_status': 'incomplete'
        }
        
        result = importer.import_module('markdown_processor')
        
        # 验证失败状态
        assert result['success'] is False
        assert result['function_mapping_status'] == 'incomplete'
        assert 'non_callable_functions' in result
        assert 'render_markdown_with_zoom' in result['non_callable_functions']
        assert 'error_code' in result
        assert 'message' in result


def test_fallback_scenario():
    """测试fallback到markdown库的情况"""
    importer = DynamicModuleImporter()
    
    # 模拟目标模块不可用的情况
    with patch.object(importer, '_try_import_from_path') as mock_import:
        mock_import.return_value = {
            'success': False,
            'module': 'markdown_processor',
            'path': '',
            'functions': {},
            'error_code': 'PATH_NOT_FOUND',
            'message': '模块路径不存在',
            'attempted_paths': [],
            'used_fallback': False
        }
        
        result = importer.import_module('markdown_processor', ['markdown'])
        
        # 验证fallback状态
        assert result['success'] is True  # fallback成功
        assert result['module'] == 'markdown'
        assert result['used_fallback'] is True
        assert 'functions' not in result or not result['functions']  # 函数映射为空


def run_all_tests():
    """运行所有测试"""
    test_functions = [
        test_successful_function_mapping,
        test_missing_functions,
        test_non_callable_functions,
        test_fallback_scenario
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            print(f"✅ {test_func.__name__} 通过")
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} 失败: {e}")
            failed += 1
    
    print(f"\n测试结果: {passed} 通过, {failed} 失败")
    return failed == 0


def main():
    """主函数"""
    success = run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
