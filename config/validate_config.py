#!/usr/bin/env python3
"""
LAD配置文件验证脚本
用于验证external_modules.json的格式和完整性
"""

import json
import os
import sys
from pathlib import Path

def validate_external_modules_config():
    """验证external_modules.json配置文件"""
    config_path = Path(__file__).parent / "external_modules.json"
    
    validation_result = {
        "file_exists": False,
        "json_valid": False,
        "required_fields_present": False,
        "module_path_exists": False,
        "permissions_ok": False,
        "errors": [],
        "warnings": []
    }
    
    try:
        # 1. 检查文件存在性
        if not config_path.exists():
            validation_result["errors"].append(f"配置文件不存在: {config_path}")
            return validation_result
        
        validation_result["file_exists"] = True
        print(f"✓ 配置文件存在: {config_path}")
        
        # 2. 验证JSON格式
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            validation_result["json_valid"] = True
            print("✓ JSON格式验证通过")
        except json.JSONDecodeError as e:
            validation_result["errors"].append(f"JSON格式错误: {e}")
            return validation_result
        
        # 3. 验证必需字段
        required_top_fields = ['external_modules', 'import_settings', 'fallback_settings']
        missing_fields = []
        
        for field in required_top_fields:
            if field not in config:
                missing_fields.append(field)
        
        if missing_fields:
            validation_result["errors"].append(f"缺少必需字段: {missing_fields}")
        else:
            validation_result["required_fields_present"] = True
            print("✓ 必需字段检查通过")
        
        # 4. 验证markdown_processor模块配置
        if 'external_modules' in config and 'markdown_processor' in config['external_modules']:
            module_config = config['external_modules']['markdown_processor']
            
            # 检查模块配置必需字段
            required_module_fields = ['module_path', 'module_name', 'required_functions']
            missing_module_fields = []
            
            for field in required_module_fields:
                if field not in module_config:
                    missing_module_fields.append(field)
            
            if missing_module_fields:
                validation_result["errors"].append(f"模块配置缺少字段: {missing_module_fields}")
            else:
                print("✓ 模块配置字段完整")
                
                # 验证模块路径
                module_path = Path(module_config['module_path'])
                if module_path.exists():
                    validation_result["module_path_exists"] = True
                    print(f"✓ 模块路径存在: {module_path}")
                    
                    # 检查markdown_processor.py文件
                    processor_file = module_path / "markdown_processor.py"
                    if processor_file.exists():
                        print(f"✓ markdown_processor.py文件存在")
                    else:
                        validation_result["warnings"].append(f"markdown_processor.py文件不存在: {processor_file}")
                else:
                    validation_result["errors"].append(f"模块路径不存在: {module_path}")
        
        # 5. 验证文件权限
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                f.read()
            validation_result["permissions_ok"] = True
            print("✓ 文件权限检查通过")
        except PermissionError:
            validation_result["errors"].append("文件权限不足，无法读取配置文件")
        
        # 6. 验证配置内容合理性
        if 'external_modules' in config:
            for module_name, module_config in config['external_modules'].items():
                if 'required_functions' in module_config:
                    functions = module_config['required_functions']
                    if not isinstance(functions, list) or len(functions) == 0:
                        validation_result["warnings"].append(f"模块 {module_name} 的required_functions应为非空列表")
                    else:
                        print(f"✓ 模块 {module_name} 配置了 {len(functions)} 个必需函数")
        
    except Exception as e:
        validation_result["errors"].append(f"验证过程发生异常: {e}")
    
    return validation_result

def print_validation_summary(result):
    """打印验证结果摘要"""
    print("\n" + "="*50)
    print("配置文件验证结果摘要")
    print("="*50)
    
    total_checks = 5
    passed_checks = sum([
        result["file_exists"],
        result["json_valid"], 
        result["required_fields_present"],
        result["module_path_exists"],
        result["permissions_ok"]
    ])
    
    print(f"通过检查: {passed_checks}/{total_checks}")
    
    if result["errors"]:
        print(f"\n❌ 错误 ({len(result['errors'])}):")
        for error in result["errors"]:
            print(f"  - {error}")
    
    if result["warnings"]:
        print(f"\n⚠️  警告 ({len(result['warnings'])}):")
        for warning in result["warnings"]:
            print(f"  - {warning}")
    
    if passed_checks == total_checks and not result["errors"]:
        print("\n🎉 配置文件验证完全通过！")
        return True
    else:
        print("\n❌ 配置文件验证未完全通过，请检查上述问题")
        return False

if __name__ == "__main__":
    print("LAD外部模块配置文件验证")
    print("-" * 30)
    
    result = validate_external_modules_config()
    success = print_validation_summary(result)
    
    # 返回适当的退出码
    sys.exit(0 if success else 1)
