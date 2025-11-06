#!/usr/bin/env python3
"""
LAD-IMPL-006B 执行前环境检查脚本
用于验证执行006B任务前的环境和配置文件状态

使用时机：在开始执行006B任务之前运行此脚本
使用方法：python config/pre_execution_check.py
"""

import sys
import json
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    print("=" * 50)
    print("1. Python环境检查")
    print("=" * 50)
    
    version_info = sys.version_info
    if version_info >= (3, 8):
        print(f"✅ Python版本: {version_info.major}.{version_info.minor}.{version_info.micro}")
        return True
    else:
        print(f"❌ Python版本过低: {version_info.major}.{version_info.minor}.{version_info.micro}")
        print("   需要 Python >= 3.8")
        return False

def check_directories():
    """检查目录结构"""
    print("\n" + "=" * 50)
    print("2. 目录结构检查")
    print("=" * 50)
    
    required_dirs = [
        ("config", "配置目录"),
        ("utils", "工具类目录"),
        ("core", "核心模块目录")
    ]
    
    all_ok = True
    for dir_name, description in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"✅ {description}存在: {dir_path}")
        else:
            print(f"❌ {description}不存在: {dir_path}")
            all_ok = False
    
    return all_ok

def check_config_files():
    """检查配置文件完整性"""
    print("\n" + "=" * 50)
    print("3. 配置文件完整性检查")
    print("=" * 50)
    
    required_files = [
        ("config/app_config.json", "应用配置"),
        ("config/external_modules.json", "外部模块配置"),
        ("config/ui_config.json", "UI配置"),
        ("config/file_types.json", "文件类型配置"),
        ("config/lad_integration.json", "LAD集成配置")
    ]
    
    all_exist = True
    file_info = []
    
    for file_path, description in required_files:
        path = Path(file_path)
        if path.exists():
            size = path.stat().st_size
            print(f"✅ {description}: {file_path} ({size} bytes)")
            file_info.append((file_path, size, True))
        else:
            print(f"❌ {description}不存在: {file_path}")
            file_info.append((file_path, 0, False))
            all_exist = False
    
    return all_exist, file_info

def check_config_manager():
    """检查ConfigManager文件状态"""
    print("\n" + "=" * 50)
    print("4. ConfigManager状态检查")
    print("=" * 50)
    
    config_manager_path = Path("utils/config_manager.py")
    
    if config_manager_path.exists():
        size = config_manager_path.stat().st_size
        print(f"✅ ConfigManager存在: {config_manager_path} ({size} bytes)")
        
        # 检查是否已有get_unified_config方法
        try:
            with open(config_manager_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'get_unified_config' in content:
                print("ℹ️  已存在get_unified_config方法，可能已执行过006B任务")
                return True, True
            else:
                print("ℹ️  未发现get_unified_config方法，需要执行006B任务")
                return True, False
        except Exception as e:
            print(f"⚠️  读取ConfigManager文件失败: {e}")
            return True, False
    else:
        print(f"❌ ConfigManager不存在: {config_manager_path}")
        print("   需要先创建ConfigManager基础实现")
        return False, False

def check_app_config_detail():
    """详细检查app_config.json的external_modules字段"""
    print("\n" + "=" * 50)
    print("5. app_config.json详细检查")
    print("=" * 50)
    
    app_config_path = Path("config/app_config.json")
    
    if not app_config_path.exists():
        print("❌ app_config.json不存在")
        return False
    
    try:
        with open(app_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if "external_modules" in config:
            external_modules = config["external_modules"]
            if external_modules == {}:
                print("⚠️  发现空的external_modules字段: {}")
                print("   这是006B任务需要清理的残留字段")
                return "needs_cleanup"
            elif isinstance(external_modules, dict) and len(external_modules) > 0:
                print(f"⚠️  external_modules字段不为空，包含: {list(external_modules.keys())}")
                print("   可能存在配置重复问题，需要人工确认")
                return "needs_review"
            else:
                print(f"⚠️  external_modules字段类型异常: {type(external_modules)}")
                return "abnormal"
        else:
            print("✅ external_modules字段不存在（已清理或从未存在）")
            return "clean"
    except json.JSONDecodeError as e:
        print(f"❌ app_config.json格式错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 读取app_config.json失败: {e}")
        return False

def check_external_modules_structure():
    """检查external_modules.json的结构"""
    print("\n" + "=" * 50)
    print("6. external_modules.json结构检查")
    print("=" * 50)
    
    external_modules_path = Path("config/external_modules.json")
    
    if not external_modules_path.exists():
        print("❌ external_modules.json不存在")
        return False
    
    try:
        with open(external_modules_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 检查双层嵌套结构
        if "external_modules" in config:
            print("✅ 发现external_modules顶层字段（双层嵌套结构）")
            external_modules = config["external_modules"]
            
            if isinstance(external_modules, dict):
                module_count = len(external_modules)
                print(f"✅ 包含 {module_count} 个模块配置:")
                for module_name in external_modules.keys():
                    print(f"   - {module_name}")
                
                return True
            else:
                print(f"⚠️  external_modules字段类型异常: {type(external_modules)}")
                return False
        else:
            print("⚠️  未发现external_modules顶层字段")
            print("   配置结构可能需要调整")
            return False
            
    except json.JSONDecodeError as e:
        print(f"❌ external_modules.json格式错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 读取external_modules.json失败: {e}")
        return False

def print_summary(results):
    """打印检查结果摘要"""
    print("\n" + "=" * 70)
    print("执行前检查结果摘要")
    print("=" * 70)
    
    # 统计结果
    python_ok = results['python_version']
    dirs_ok = results['directories']
    configs_ok = results['config_files'][0]
    config_manager_exists = results['config_manager'][0]
    has_unified_config = results['config_manager'][1]
    app_config_status = results['app_config_detail']
    external_modules_ok = results['external_modules_structure']
    
    total_checks = 6
    passed_checks = sum([
        python_ok,
        dirs_ok,
        configs_ok,
        config_manager_exists,
        app_config_status in ['clean', 'needs_cleanup'],
        external_modules_ok
    ])
    
    print(f"\n通过检查: {passed_checks}/{total_checks}")
    
    # 详细建议
    print("\n📋 执行建议:")
    
    if has_unified_config:
        print("⚠️  ConfigManager已包含get_unified_config方法")
        print("   可能已执行过006B任务，建议检查是否需要重复执行")
    
    if app_config_status == "needs_cleanup":
        print("✅ 发现需要清理的空external_modules字段")
        print("   可以执行006B任务进行清理")
    elif app_config_status == "needs_review":
        print("⚠️  external_modules字段不为空")
        print("   建议先手动检查配置内容，确认后再执行006B任务")
    elif app_config_status == "clean":
        print("ℹ️  app_config.json中无external_modules字段")
        print("   006B任务的清理部分可以跳过")
    
    if external_modules_ok:
        print("✅ external_modules.json结构正确（双层嵌套）")
        print("   ConfigManager增强需要支持这种结构")
    
    # 最终判断
    print("\n" + "=" * 70)
    
    if passed_checks == total_checks:
        print("🎉 环境检查完全通过！可以开始执行006B任务")
        return True
    elif passed_checks >= 4:
        print("⚠️  环境基本满足要求，但存在一些问题")
        print("   建议解决上述问题后再执行006B任务")
        return False
    else:
        print("❌ 环境检查未通过，请先解决上述问题")
        return False

def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("LAD-IMPL-006B 执行前环境检查")
    print("=" * 70)
    print("\n此脚本将检查执行006B任务前的环境和配置文件状态")
    print("请确保在项目根目录（包含config/和utils/目录）执行此脚本\n")
    
    # 执行所有检查
    results = {
        'python_version': check_python_version(),
        'directories': check_directories(),
        'config_files': check_config_files(),
        'config_manager': check_config_manager(),
        'app_config_detail': check_app_config_detail(),
        'external_modules_structure': check_external_modules_structure()
    }
    
    # 打印摘要
    success = print_summary(results)
    
    # 返回适当的退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

