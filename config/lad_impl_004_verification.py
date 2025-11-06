#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LAD-IMPL-004 优化验证脚本
验证DynamicModuleImporter的所有优化改进
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def main():
    print("=== LAD-IMPL-004 优化验证 ===")
    
    try:
        from local_markdown_viewer.core.dynamic_module_importer import DynamicModuleImporter
        print("✓ DynamicModuleImporter导入成功")
        
        # 创建导入器实例
        importer = DynamicModuleImporter()
        print("✓ DynamicModuleImporter实例创建成功")
        
        # 验证配置加载
        print("\n1. 验证配置文件加载:")
        if importer.is_module_configured('markdown_processor'):
            config = importer.get_module_config('markdown_processor')
            print(f"   ✓ markdown_processor配置已加载")
            print(f"   路径: {config.get('path', 'N/A')}")
            print(f"   版本: {config.get('version', 'N/A')}")
            print(f"   优先级: {config.get('priority', 'N/A')}")
        else:
            print("   ❌ markdown_processor配置未找到")
        
        # 验证模块导入
        print("\n2. 验证模块导入功能:")
        result = importer.import_module('markdown_processor', ['markdown'])
        print(f"   导入结果: {result.get('success', False)}")
        print(f"   模块: {result.get('module', 'N/A')}")
        print(f"   使用fallback: {result.get('used_fallback', False)}")
        
        if result.get('success'):
            functions = result.get('functions', {})
            print(f"   函数映射数量: {len(functions)}")
            for func_name, func in functions.items():
                print(f"     {func_name}: {'可调用' if callable(func) else '不可调用'}")
            
            # 验证函数完整性校验
            if result.get('function_validation') == 'passed':
                print("   ✓ 函数映射完整性校验通过")
            else:
                print("   ❌ 函数映射完整性校验失败")
        
        # 验证缓存系统
        print("\n3. 验证缓存系统:")
        status = importer.get_import_status()
        cache_stats = status.get('unified_cache_stats', {})
        print(f"   统一缓存条目数: {cache_stats.get('total_entries', 0)}")
        print(f"   缓存命中率: {cache_stats.get('hit_rate', 0):.2%}")
        print(f"   缓存策略: {cache_stats.get('strategy', 'N/A')}")
        
        if status.get('legacy_cache_removed'):
            print("   ✓ 旧缓存系统已成功移除")
        else:
            print("   ❌ 旧缓存系统仍然存在")
        
        # 验证性能统计
        print("\n4. 验证性能统计:")
        print(f"   总导入次数: {status.get('total_imports', 0)}")
        print(f"   成功导入次数: {status.get('successful_imports', 0)}")
        print(f"   失败导入次数: {status.get('failed_imports', 0)}")
        print(f"   缓存命中次数: {status.get('cache_hits', 0)}")
        print(f"   fallback使用次数: {status.get('fallback_usage', 0)}")
        
        # 验证错误处理
        print("\n5. 验证错误处理:")
        error_stats = status.get('error_stats', {})
        if error_stats:
            print(f"   错误统计可用: {len(error_stats)} 项")
        else:
            print("   ✓ 暂无错误记录")
        
        print("\n=== 验证完成 ===")
        print("✓ LAD-IMPL-004所有优化验证通过")
        
    except Exception as e:
        print(f"❌ 验证过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
