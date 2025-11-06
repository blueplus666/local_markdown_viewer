#!/usr/bin/env python3
"""
LAD完整验证脚本 - 补充LAD-IMPL-001和LAD-IMPL-002缺失的验证
"""

import json
import os
import sys
import importlib.util
import stat
from pathlib import Path

def validate_file_permissions(file_path):
    """验证文件权限"""
    try:
        # 检查文件是否可读
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1)  # 尝试读取一个字符
        
        # 获取文件权限信息
        file_stat = os.stat(file_path)
        permissions = {
            "readable": os.access(file_path, os.R_OK),
            "writable": os.access(file_path, os.W_OK),
            "executable": os.access(file_path, os.X_OK),
            "size": file_stat.st_size,
            "mode": oct(file_stat.st_mode)
        }
        return True, permissions
    except Exception as e:
        return False, str(e)

def test_function_callability(module_path, required_functions):
    """测试函数可调用性"""
    results = {}
    original_path = sys.path.copy()
    
    try:
        # 临时添加模块路径
        if module_path not in sys.path:
            sys.path.insert(0, module_path)
        
        # 导入模块
        spec = importlib.util.spec_from_file_location(
            "markdown_processor", 
            os.path.join(module_path, "markdown_processor.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 测试每个函数
        for func_name in required_functions:
            try:
                if hasattr(module, func_name):
                    func = getattr(module, func_name)
                    if callable(func):
                        # 尝试简单调用测试
                        if func_name == "render_markdown_to_html":
                            test_result = func("# 测试")
                            results[func_name] = {
                                "exists": True,
                                "callable": True,
                                "test_passed": bool(test_result and "<h1" in test_result),
                                "error": None
                            }
                        elif func_name == "render_markdown_with_zoom":
                            test_result = func("# 测试")
                            results[func_name] = {
                                "exists": True,
                                "callable": True,
                                "test_passed": bool(test_result and len(test_result) > 0),
                                "error": None
                            }
                        else:
                            results[func_name] = {
                                "exists": True,
                                "callable": True,
                                "test_passed": None,  # 未知函数不测试
                                "error": None
                            }
                    else:
                        results[func_name] = {
                            "exists": True,
                            "callable": False,
                            "test_passed": False,
                            "error": "函数不可调用"
                        }
                else:
                    results[func_name] = {
                        "exists": False,
                        "callable": False,
                        "test_passed": False,
                        "error": "函数不存在"
                    }
            except Exception as e:
                results[func_name] = {
                    "exists": hasattr(module, func_name),
                    "callable": callable(getattr(module, func_name, None)),
                    "test_passed": False,
                    "error": str(e)
                }
    
    except Exception as e:
        for func_name in required_functions:
            results[func_name] = {
                "exists": False,
                "callable": False,
                "test_passed": False,
                "error": f"模块导入失败: {e}"
            }
    
    finally:
        # 恢复sys.path
        sys.path = original_path
    
    return results

def test_temporary_import_mechanism(module_path):
    """测试临时导入机制"""
    test_results = {
        "path_addition": False,
        "import_success": False,
        "path_cleanup": False,
        "import_cleanup": False,
        "errors": []
    }
    
    original_path = sys.path.copy()
    original_modules = set(sys.modules.keys())
    
    try:
        # 1. 测试路径添加
        if module_path not in sys.path:
            sys.path.insert(0, module_path)
            test_results["path_addition"] = module_path in sys.path
        else:
            test_results["path_addition"] = True
        
        # 2. 测试导入
        try:
            import markdown_processor
            test_results["import_success"] = True
        except ImportError as e:
            test_results["errors"].append(f"导入失败: {e}")
        
        # 3. 测试路径清理
        sys.path = original_path
        test_results["path_cleanup"] = module_path not in sys.path
        
        # 4. 测试模块清理
        modules_to_remove = [name for name in sys.modules.keys() 
                           if name not in original_modules and 'markdown_processor' in name]
        for module_name in modules_to_remove:
            del sys.modules[module_name]
        
        test_results["import_cleanup"] = not any('markdown_processor' in name 
                                               for name in sys.modules.keys() 
                                               if name not in original_modules)
        
    except Exception as e:
        test_results["errors"].append(f"临时导入机制测试失败: {e}")
        # 确保清理
        sys.path = original_path
    
    return test_results

def run_complete_validation():
    """运行完整验证"""
    print("=" * 60)
    print("LAD完整验证报告")
    print("=" * 60)
    
    # 加载配置
    config_path = Path(__file__).parent / "external_modules.json"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("✓ 配置文件加载成功")
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        return False
    
    module_config = config['external_modules']['markdown_processor']
    module_path = module_config['module_path']
    required_functions = module_config['required_functions']
    
    # 1. 权限验证
    print("\n1. 权限验证")
    print("-" * 30)
    perm_ok, perm_info = validate_file_permissions(config_path)
    if perm_ok:
        print(f"✓ 配置文件权限正常")
        print(f"  - 可读: {perm_info['readable']}")
        print(f"  - 文件大小: {perm_info['size']} 字节")
    else:
        print(f"❌ 配置文件权限问题: {perm_info}")
    
    # 2. 函数可调用性测试
    print("\n2. 函数可调用性测试")
    print("-" * 30)
    func_results = test_function_callability(module_path, required_functions)
    
    all_functions_ok = True
    for func_name, result in func_results.items():
        status = "✓" if result['test_passed'] else "❌"
        print(f"{status} {func_name}")
        print(f"  - 存在: {result['exists']}")
        print(f"  - 可调用: {result['callable']}")
        print(f"  - 测试通过: {result['test_passed']}")
        if result['error']:
            print(f"  - 错误: {result['error']}")
        
        if not result['test_passed']:
            all_functions_ok = False
    
    # 3. 临时导入机制测试
    print("\n3. 临时导入机制测试")
    print("-" * 30)
    import_results = test_temporary_import_mechanism(module_path)
    
    import_tests = [
        ("路径添加", import_results['path_addition']),
        ("导入成功", import_results['import_success']),
        ("路径清理", import_results['path_cleanup']),
        ("导入清理", import_results['import_cleanup'])
    ]
    
    all_import_ok = True
    for test_name, result in import_tests:
        status = "✓" if result else "❌"
        print(f"{status} {test_name}: {result}")
        if not result:
            all_import_ok = False
    
    if import_results['errors']:
        print("错误详情:")
        for error in import_results['errors']:
            print(f"  - {error}")
    
    # 4. 总体结果
    print("\n4. 总体验证结果")
    print("-" * 30)
    overall_success = perm_ok and all_functions_ok and all_import_ok
    
    print(f"权限验证: {'通过' if perm_ok else '失败'}")
    print(f"函数测试: {'通过' if all_functions_ok else '失败'}")
    print(f"导入机制: {'通过' if all_import_ok else '失败'}")
    print(f"总体结果: {'✓ 完全通过' if overall_success else '❌ 存在问题'}")
    
    return overall_success

if __name__ == "__main__":
    success = run_complete_validation()
    sys.exit(0 if success else 1)
