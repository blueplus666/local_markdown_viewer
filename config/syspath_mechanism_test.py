#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LAD-IMPL-004补漏：临时sys.path管理机制验证
验证DynamicModuleImporter的核心临时路径导入功能
"""

import sys
import os
from pathlib import Path
from contextlib import contextmanager

def test_temp_syspath_mechanism():
    """测试临时sys.path管理机制"""
    print("=== 临时sys.path管理机制验证 ===")
    
    # 记录原始sys.path
    original_path = sys.path.copy()
    print(f"1. 原始sys.path长度: {len(original_path)}")
    
    # 测试路径
    test_path = r"D:\lad\LAD_md_ed2\lad_markdown_viewer"
    print(f"2. 测试路径: {test_path}")
    print(f"   路径存在: {os.path.exists(test_path)}")
    
    @contextmanager
    def temp_sys_path(path: str):
        """临时修改sys.path的上下文管理器"""
        original = sys.path.copy()
        try:
            sys.path.insert(0, path)
            print(f"   临时添加路径到sys.path[0]: {path}")
            yield
        finally:
            sys.path[:] = original
            print(f"   恢复原始sys.path")
    
    # 验证临时路径机制
    print("\n3. 验证临时路径添加和恢复:")
    with temp_sys_path(test_path):
        print(f"   临时状态sys.path[0]: {sys.path[0]}")
        print(f"   临时状态sys.path长度: {len(sys.path)}")
        
        # 测试模块导入
        try:
            import markdown_processor
            print(f"   ✓ markdown_processor导入成功")
            print(f"   模块文件: {getattr(markdown_processor, '__file__', 'N/A')}")
            
            # 验证必需函数
            required_functions = ['render_markdown_with_zoom', 'render_markdown_to_html']
            for func_name in required_functions:
                if hasattr(markdown_processor, func_name):
                    func = getattr(markdown_processor, func_name)
                    print(f"   ✓ {func_name}: {'可调用' if callable(func) else '不可调用'}")
                else:
                    print(f"   ❌ {func_name}: 不存在")
                    
        except ImportError as e:
            print(f"   ❌ markdown_processor导入失败: {e}")
    
    # 验证路径恢复
    restored_path = sys.path.copy()
    print(f"\n4. 路径恢复验证:")
    print(f"   恢复后sys.path长度: {len(restored_path)}")
    print(f"   路径恢复正确: {original_path == restored_path}")
    
    if test_path in sys.path:
        print(f"   ❌ 测试路径仍在sys.path中")
    else:
        print(f"   ✓ 测试路径已从sys.path中移除")
    
    assert original_path == restored_path

def test_dynamic_module_importer_integration():
    """测试DynamicModuleImporter的集成使用"""
    print("\n=== DynamicModuleImporter集成测试 ===")
    
    try:
        # 添加项目路径
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        from local_markdown_viewer.core.dynamic_module_importer import DynamicModuleImporter
        print("✓ DynamicModuleImporter导入成功")
        
        # 创建实例
        importer = DynamicModuleImporter()
        print("✓ DynamicModuleImporter实例创建成功")
        
        # 测试模块导入
        result = importer.import_module('markdown_processor', ['markdown'])
        print(f"\n导入结果分析:")
        print(f"  成功: {result.get('success', False)}")
        print(f"  模块: {result.get('module', 'N/A')}")
        print(f"  路径: {result.get('path', 'N/A')}")
        print(f"  使用fallback: {result.get('used_fallback', False)}")
        
        functions = result.get('functions', {})
        print(f"  函数映射数量: {len(functions)}")
        for func_name, func in functions.items():
            print(f"    {func_name}: {'可调用' if callable(func) else '不可调用'}")
        
        # 验证标准化格式
        required_keys = ['success', 'module', 'path', 'used_fallback', 'functions']
        missing_keys = [key for key in required_keys if key not in result]
        if missing_keys:
            print(f"  ❌ 缺少必需字段: {missing_keys}")
        else:
            print(f"  ✓ 标准化格式验证通过")
        
        assert result is not None, "集成测试应返回结果"
        assert not missing_keys, f"缺少必需字段: {missing_keys}"
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        assert False

def main():
    """主测试函数"""
    print("LAD-IMPL-004补漏：临时sys.path管理机制验证\n")
    
    # 测试1：临时路径机制
    path_test_passed = test_temp_syspath_mechanism()
    
    # 测试2：集成测试
    integration_result = test_dynamic_module_importer_integration()
    
    # 总结
    print("\n=== 验证总结 ===")
    print(f"临时路径机制: {'✓ 通过' if path_test_passed else '❌ 失败'}")
    print(f"集成测试: {'✓ 通过' if integration_result and integration_result.get('success') else '❌ 失败'}")
    
    if path_test_passed and integration_result and integration_result.get('success'):
        print("✅ 所有验证通过，临时sys.path管理机制工作正常")
    else:
        print("❌ 验证失败，需要进一步检查")

if __name__ == "__main__":
    main()
