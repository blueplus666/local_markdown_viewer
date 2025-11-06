#!/usr/bin/env python3
"""
LAD路径配置验证脚本
验证external_modules.json中配置的路径和模块函数
"""

import json
import os
import sys
import importlib.util
from pathlib import Path

def verify_module_path_and_functions():
    """验证模块路径和函数完整性"""
    verification_result = {
        "config_loaded": False,
        "module_path_exists": False,
        "processor_file_exists": False,
        "functions_verified": {},
        "import_test_passed": False,
        "errors": [],
        "warnings": []
    }
    
    try:
        # 1. 加载配置文件
        config_path = Path(__file__).parent / "external_modules.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        verification_result["config_loaded"] = True
        print("✓ 配置文件加载成功")
        
        # 2. 获取模块配置
        module_config = config['external_modules']['markdown_processor']
        module_path = module_config['module_path']
        required_functions = module_config['required_functions']
        
        print(f"目标模块路径: {module_path}")
        print(f"必需函数: {required_functions}")
        
        # 3. 验证模块路径存在
        if os.path.exists(module_path):
            verification_result["module_path_exists"] = True
            print(f"✓ 模块路径存在: {module_path}")
        else:
            verification_result["errors"].append(f"模块路径不存在: {module_path}")
            return verification_result
        
        # 4. 验证markdown_processor.py文件存在
        processor_file = os.path.join(module_path, "markdown_processor.py")
        if os.path.exists(processor_file):
            verification_result["processor_file_exists"] = True
            print(f"✓ markdown_processor.py文件存在")
        else:
            verification_result["errors"].append(f"markdown_processor.py文件不存在: {processor_file}")
            return verification_result
        
        # 5. 测试模块导入和函数验证
        try:
            # 临时添加到sys.path
            original_path = sys.path.copy()
            if module_path not in sys.path:
                sys.path.insert(0, module_path)
            
            # 导入模块
            spec = importlib.util.spec_from_file_location(
                "markdown_processor", 
                processor_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            print("✓ 模块导入成功")
            
            # 验证每个必需函数
            for func_name in required_functions:
                if hasattr(module, func_name):
                    func = getattr(module, func_name)
                    if callable(func):
                        verification_result["functions_verified"][func_name] = True
                        print(f"✓ 函数存在且可调用: {func_name}")
                    else:
                        verification_result["functions_verified"][func_name] = False
                        verification_result["warnings"].append(f"函数存在但不可调用: {func_name}")
                else:
                    verification_result["functions_verified"][func_name] = False
                    verification_result["errors"].append(f"函数不存在: {func_name}")
            
            # 测试函数调用（简单测试）
            if all(verification_result["functions_verified"].values()):
                try:
                    # 测试render_markdown_to_html
                    test_md = "# 测试标题\n\n这是一个测试。"
                    result = module.render_markdown_to_html(test_md)
                    if result and "<h1" in result:
                        print("✓ render_markdown_to_html函数测试通过")
                    else:
                        verification_result["warnings"].append("render_markdown_to_html函数返回结果异常")
                    
                    # 测试render_markdown_with_zoom
                    result_zoom = module.render_markdown_with_zoom(test_md)
                    if result_zoom and "zoom" in result_zoom.lower():
                        print("✓ render_markdown_with_zoom函数测试通过")
                    else:
                        verification_result["warnings"].append("render_markdown_with_zoom函数返回结果可能异常")
                    
                    verification_result["import_test_passed"] = True
                    
                except Exception as e:
                    verification_result["warnings"].append(f"函数调用测试失败: {e}")
            
        except Exception as e:
            verification_result["errors"].append(f"模块导入失败: {e}")
        finally:
            # 恢复sys.path
            sys.path = original_path
        
    except Exception as e:
        verification_result["errors"].append(f"验证过程发生异常: {e}")
    
    return verification_result

def test_temporary_import_mechanism():
    """测试临时sys.path导入机制"""
    print("\n" + "="*50)
    print("测试临时导入机制")
    print("="*50)
    
    try:
        # 保存原始sys.path
        original_path = sys.path.copy()
        test_path = "D:\\lad\\LAD_md_ed2\\lad_markdown_viewer"
        
        # 添加测试路径
        if test_path not in sys.path:
            sys.path.insert(0, test_path)
            print(f"✓ 临时添加路径到sys.path: {test_path}")
        
        # 尝试导入
        import markdown_processor
        print("✓ 临时导入成功")
        
        # 验证函数存在
        functions = ["render_markdown_to_html", "render_markdown_with_zoom"]
        for func_name in functions:
            if hasattr(markdown_processor, func_name):
                print(f"✓ 函数可访问: {func_name}")
            else:
                print(f"❌ 函数不可访问: {func_name}")
        
        # 清理sys.path
        sys.path = original_path
        print("✓ sys.path已恢复")
        
        # 验证清理效果
        try:
            import markdown_processor
            print("⚠️  模块仍可导入（可能已缓存）")
        except ImportError:
            print("✓ 模块导入已清理")
        
        return True
        
    except Exception as e:
        print(f"❌ 临时导入机制测试失败: {e}")
        # 确保恢复sys.path
        sys.path = original_path
        return False

def print_verification_summary(result):
    """打印验证结果摘要"""
    print("\n" + "="*50)
    print("路径配置验证结果摘要")
    print("="*50)
    
    total_checks = 5
    passed_checks = sum([
        result["config_loaded"],
        result["module_path_exists"],
        result["processor_file_exists"],
        all(result["functions_verified"].values()) if result["functions_verified"] else False,
        result["import_test_passed"]
    ])
    
    print(f"通过检查: {passed_checks}/{total_checks}")
    
    # 函数验证详情
    if result["functions_verified"]:
        print(f"\n函数验证详情:")
        for func_name, status in result["functions_verified"].items():
            status_text = "✓ 通过" if status else "❌ 失败"
            print(f"  {func_name}: {status_text}")
    
    if result["errors"]:
        print(f"\n❌ 错误 ({len(result['errors'])}):")
        for error in result["errors"]:
            print(f"  - {error}")
    
    if result["warnings"]:
        print(f"\n⚠️  警告 ({len(result['warnings'])}):")
        for warning in result["warnings"]:
            print(f"  - {warning}")
    
    if passed_checks == total_checks and not result["errors"]:
        print("\n🎉 路径配置验证完全通过！")
        return True
    else:
        print("\n❌ 路径配置验证未完全通过，请检查上述问题")
        return False

if __name__ == "__main__":
    print("LAD路径配置验证")
    print("-" * 30)
    
    # 主验证流程
    result = verify_module_path_and_functions()
    success = print_verification_summary(result)
    
    # 测试临时导入机制
    import_test_success = test_temporary_import_mechanism()
    
    # 综合结果
    overall_success = success and import_test_success
    
    print(f"\n总体验证结果: {'通过' if overall_success else '失败'}")
    sys.exit(0 if overall_success else 1)
