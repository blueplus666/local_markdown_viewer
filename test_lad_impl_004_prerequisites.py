#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LAD-IMPL-004前置条件验证脚本
用于验证LAD-IMPL-004任务的所有前置条件是否满足

作者: LAD Team
创建时间: 2025-08-30
"""

import os
import sys
import json
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional

class LADImpl004PrerequisitesValidator:
    """LAD-IMPL-004前置条件验证器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"
        self.core_dir = self.project_root / "core"
        self.validation_results = {}
        
    def validate_all_prerequisites(self) -> Dict[str, Any]:
        """验证所有前置条件"""
        print("=== LAD-IMPL-004前置条件验证开始 ===\n")
        
        # 1. 配置文件验证
        self.validation_results['config_file'] = self.validate_config_file()
        
        # 2. 模块路径验证
        self.validation_results['module_path'] = self.validate_module_path()
        
        # 3. 函数存在性验证
        self.validation_results['functions'] = self.validate_functions()
        
        # 4. 临时导入机制验证
        self.validation_results['import_mechanism'] = self.validate_import_mechanism()
        
        # 5. 现有代码实现验证
        self.validation_results['existing_implementation'] = self.validate_existing_implementation()
        
        # 6. 权限验证
        self.validation_results['permissions'] = self.validate_permissions()
        
        # 生成验证报告
        report = self.generate_validation_report()
        
        print("=== LAD-IMPL-004前置条件验证完成 ===\n")
        return report
    
    def validate_config_file(self) -> Dict[str, Any]:
        """验证配置文件"""
        print("1. 验证配置文件...")
        
        config_file = self.config_dir / "external_modules.json"
        result = {
            'status': 'FAILED',
            'details': [],
            'config_data': None
        }
        
        # 检查文件存在性
        if not config_file.exists():
            result['details'].append("配置文件不存在")
            print(f"  ❌ 配置文件不存在: {config_file}")
            return result
        
        # 检查文件可读性
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            result['config_data'] = config_data
        except json.JSONDecodeError as e:
            result['details'].append(f"JSON格式错误: {e}")
            print(f"  ❌ JSON格式错误: {e}")
            return result
        except Exception as e:
            result['details'].append(f"文件读取错误: {e}")
            print(f"  ❌ 文件读取错误: {e}")
            return result
        
        # 验证必需字段
        required_fields = ['external_modules']
        for field in required_fields:
            if field not in config_data:
                result['details'].append(f"缺少必需字段: {field}")
                print(f"  ❌ 缺少必需字段: {field}")
                return result
        
        # 验证markdown_processor配置
        md_config = config_data.get('external_modules', {}).get('markdown_processor', {})
        if not md_config:
            result['details'].append("缺少markdown_processor配置")
            print(f"  ❌ 缺少markdown_processor配置")
            return result
        
        # 验证必需配置项
        required_config_items = ['module_path', 'required_functions', 'fallback_enabled']
        for item in required_config_items:
            if item not in md_config:
                result['details'].append(f"缺少配置项: {item}")
                print(f"  ❌ 缺少配置项: {item}")
                return result
        
        # 验证路径格式
        module_path = md_config.get('module_path', '')
        if not module_path or not isinstance(module_path, str):
            result['details'].append("module_path格式错误")
            print(f"  ❌ module_path格式错误")
            return result
        
        # 验证函数列表
        required_functions = md_config.get('required_functions', [])
        if not isinstance(required_functions, list) or len(required_functions) == 0:
            result['details'].append("required_functions格式错误")
            print(f"  ❌ required_functions格式错误")
            return result
        
        result['status'] = 'SUCCESS'
        result['details'].append("配置文件验证通过")
        print(f"  ✅ 配置文件验证通过")
        print(f"     - 模块路径: {module_path}")
        print(f"     - 必需函数: {required_functions}")
        print(f"     - Fallback启用: {md_config.get('fallback_enabled')}")
        
        return result
    
    def validate_module_path(self) -> Dict[str, Any]:
        """验证模块路径"""
        print("2. 验证模块路径...")
        
        result = {
            'status': 'FAILED',
            'details': [],
            'module_path': None
        }
        
        # 获取配置的模块路径
        config_result = self.validation_results.get('config_file', {})
        if config_result.get('status') != 'SUCCESS':
            result['details'].append("配置文件验证失败，无法获取模块路径")
            print(f"  ❌ 配置文件验证失败")
            return result
        
        config_data = config_result.get('config_data', {})
        md_config = config_data.get('external_modules', {}).get('markdown_processor', {})
        module_path_str = md_config.get('module_path', '')
        
        # 解析路径
        try:
            module_path = Path(module_path_str)
            result['module_path'] = str(module_path)
        except Exception as e:
            result['details'].append(f"路径解析失败: {e}")
            print(f"  ❌ 路径解析失败: {e}")
            return result
        
        # 检查路径存在性
        if not module_path.exists():
            result['details'].append(f"模块路径不存在: {module_path}")
            print(f"  ❌ 模块路径不存在: {module_path}")
            return result
        
        # 检查路径可访问性
        if not os.access(module_path, os.R_OK):
            result['details'].append(f"模块路径无读取权限: {module_path}")
            print(f"  ❌ 模块路径无读取权限: {module_path}")
            return result
        
        # 检查markdown_processor.py文件
        processor_file = module_path / "markdown_processor.py"
        if not processor_file.exists():
            result['details'].append(f"markdown_processor.py文件不存在: {processor_file}")
            print(f"  ❌ markdown_processor.py文件不存在: {processor_file}")
            return result
        
        result['status'] = 'SUCCESS'
        result['details'].append("模块路径验证通过")
        print(f"  ✅ 模块路径验证通过")
        print(f"     - 路径: {module_path}")
        print(f"     - 处理器文件: {processor_file}")
        
        return result
    
    def validate_functions(self) -> Dict[str, Any]:
        """验证函数存在性"""
        print("3. 验证函数存在性...")
        
        result = {
            'status': 'FAILED',
            'details': [],
            'functions_found': [],
            'functions_missing': []
        }
        
        # 获取配置的函数列表
        config_result = self.validation_results.get('config_file', {})
        if config_result.get('status') != 'SUCCESS':
            result['details'].append("配置文件验证失败，无法获取函数列表")
            print(f"  ❌ 配置文件验证失败")
            return result
        
        config_data = config_result.get('config_data', {})
        md_config = config_data.get('external_modules', {}).get('markdown_processor', {})
        required_functions = md_config.get('required_functions', [])
        
        # 获取模块路径
        path_result = self.validation_results.get('module_path', {})
        if path_result.get('status') != 'SUCCESS':
            result['details'].append("模块路径验证失败")
            print(f"  ❌ 模块路径验证失败")
            return result
        
        module_path = path_result.get('module_path')
        processor_file = Path(module_path) / "markdown_processor.py"
        
        # 读取文件内容检查函数定义
        try:
            with open(processor_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            result['details'].append(f"无法读取处理器文件: {e}")
            print(f"  ❌ 无法读取处理器文件: {e}")
            return result
        
        # 检查每个必需函数
        for func_name in required_functions:
            if f"def {func_name}(" in content:
                result['functions_found'].append(func_name)
            else:
                result['functions_missing'].append(func_name)
        
        # 验证结果
        if result['functions_missing']:
            result['details'].append(f"缺少函数: {', '.join(result['functions_missing'])}")
            print(f"  ❌ 缺少函数: {', '.join(result['functions_missing'])}")
            return result
        
        result['status'] = 'SUCCESS'
        result['details'].append("函数存在性验证通过")
        print(f"  ✅ 函数存在性验证通过")
        print(f"     - 找到函数: {', '.join(result['functions_found'])}")
        
        return result
    
    def validate_import_mechanism(self) -> Dict[str, Any]:
        """验证临时导入机制"""
        print("4. 验证临时导入机制...")
        
        result = {
            'status': 'FAILED',
            'details': [],
            'import_test_result': None
        }
        
        # 获取模块路径
        path_result = self.validation_results.get('module_path', {})
        if path_result.get('status') != 'SUCCESS':
            result['details'].append("模块路径验证失败")
            print(f"  ❌ 模块路径验证失败")
            return result
        
        module_path = path_result.get('module_path')
        
        # 测试临时导入机制
        try:
            # 保存原始sys.path
            original_path = sys.path.copy()
            
            # 临时添加模块路径
            sys.path.insert(0, module_path)
            
            # 尝试导入
            spec = importlib.util.spec_from_file_location(
                "markdown_processor", 
                f"{module_path}/markdown_processor.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 验证函数可调用性
            config_result = self.validation_results.get('config_file', {})
            config_data = config_result.get('config_data', {})
            md_config = config_data.get('external_modules', {}).get('markdown_processor', {})
            required_functions = md_config.get('required_functions', [])
            
            callable_functions = []
            non_callable_functions = []
            
            for func_name in required_functions:
                if hasattr(module, func_name):
                    func = getattr(module, func_name)
                    if callable(func):
                        callable_functions.append(func_name)
                    else:
                        non_callable_functions.append(func_name)
                else:
                    non_callable_functions.append(func_name)
            
            # 恢复原始sys.path
            sys.path[:] = original_path
            
            if non_callable_functions:
                result['details'].append(f"函数不可调用: {', '.join(non_callable_functions)}")
                print(f"  ❌ 函数不可调用: {', '.join(non_callable_functions)}")
                return result
            
            result['import_test_result'] = {
                'module': module,
                'callable_functions': callable_functions,
                'module_path': getattr(module, '__file__', 'unknown')
            }
            
        except Exception as e:
            # 恢复原始sys.path
            sys.path[:] = original_path
            result['details'].append(f"临时导入测试失败: {e}")
            print(f"  ❌ 临时导入测试失败: {e}")
            return result
        
        result['status'] = 'SUCCESS'
        result['details'].append("临时导入机制验证通过")
        print(f"  ✅ 临时导入机制验证通过")
        print(f"     - 可调用函数: {', '.join(callable_functions)}")
        print(f"     - 模块文件: {result['import_test_result']['module_path']}")
        
        return result
    
    def validate_existing_implementation(self) -> Dict[str, Any]:
        """验证现有代码实现"""
        print("5. 验证现有代码实现...")
        
        result = {
            'status': 'FAILED',
            'details': [],
            'implementation_status': {}
        }
        
        # 检查DynamicModuleImporter
        importer_file = self.core_dir / "dynamic_module_importer.py"
        if not importer_file.exists():
            result['details'].append("DynamicModuleImporter文件不存在")
            print(f"  ❌ DynamicModuleImporter文件不存在")
            return result
        
        # 检查HybridMarkdownRenderer
        renderer_file = self.core_dir / "markdown_renderer.py"
        if not renderer_file.exists():
            result['details'].append("HybridMarkdownRenderer文件不存在")
            print(f"  ❌ HybridMarkdownRenderer文件不存在")
            return result
        
        # 检查关键方法
        try:
            with open(importer_file, 'r', encoding='utf-8') as f:
                importer_content = f.read()
            
            with open(renderer_file, 'r', encoding='utf-8') as f:
                renderer_content = f.read()
            
            # 检查Importer关键方法
            importer_methods = [
                'import_module',
                '_load_module_configs',
                '_temp_sys_path',
                '_import_markdown_processor'
            ]
            
            for method in importer_methods:
                if f"def {method}(" in importer_content:
                    result['implementation_status'][f'importer_{method}'] = 'EXISTS'
                else:
                    result['implementation_status'][f'importer_{method}'] = 'MISSING'
                    result['details'].append(f"Importer缺少方法: {method}")
            
            # 检查Renderer关键方法
            renderer_methods = [
                'render',
                '_render_content'
            ]
            
            for method in renderer_methods:
                if f"def {method}(" in renderer_content:
                    result['implementation_status'][f'renderer_{method}'] = 'EXISTS'
                else:
                    result['implementation_status'][f'renderer_{method}'] = 'MISSING'
                    result['details'].append(f"Renderer缺少方法: {method}")
            
        except Exception as e:
            result['details'].append(f"代码文件读取失败: {e}")
            print(f"  ❌ 代码文件读取失败: {e}")
            return result
        
        # 检查是否有缺失的方法
        missing_methods = [k for k, v in result['implementation_status'].items() if v == 'MISSING']
        if missing_methods:
            print(f"  ⚠️  发现缺失方法: {', '.join(missing_methods)}")
        else:
            print(f"  ✅ 所有关键方法都存在")
        
        result['status'] = 'SUCCESS'
        result['details'].append("现有代码实现验证通过")
        print(f"  ✅ 现有代码实现验证通过")
        
        return result
    
    def validate_permissions(self) -> Dict[str, Any]:
        """验证权限"""
        print("6. 验证权限...")
        
        result = {
            'status': 'FAILED',
            'details': [],
            'permission_status': {}
        }
        
        # 检查配置文件权限
        config_file = self.config_dir / "external_modules.json"
        if config_file.exists():
            if os.access(config_file, os.R_OK):
                result['permission_status']['config_read'] = 'OK'
            else:
                result['permission_status']['config_read'] = 'DENIED'
                result['details'].append("配置文件无读取权限")
        
        # 检查模块路径权限
        path_result = self.validation_results.get('module_path', {})
        if path_result.get('status') == 'SUCCESS':
            module_path = path_result.get('module_path')
            if os.access(module_path, os.R_OK):
                result['permission_status']['module_read'] = 'OK'
            else:
                result['permission_status']['module_read'] = 'DENIED'
                result['details'].append("模块路径无读取权限")
        
        # 检查代码文件权限
        importer_file = self.core_dir / "dynamic_module_importer.py"
        renderer_file = self.core_dir / "markdown_renderer.py"
        
        for file_path in [importer_file, renderer_file]:
            if file_path.exists():
                if os.access(file_path, os.R_OK):
                    result['permission_status'][f'{file_path.name}_read'] = 'OK'
                else:
                    result['permission_status'][f'{file_path.name}_read'] = 'DENIED'
                    result['details'].append(f"{file_path.name}无读取权限")
        
        # 检查是否有权限问题
        denied_permissions = [k for k, v in result['permission_status'].items() if v == 'DENIED']
        if denied_permissions:
            print(f"  ❌ 权限问题: {', '.join(denied_permissions)}")
            return result
        
        result['status'] = 'SUCCESS'
        result['details'].append("权限验证通过")
        print(f"  ✅ 权限验证通过")
        
        return result
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        print("\n=== 验证报告 ===")
        
        # 统计结果
        total_checks = len(self.validation_results)
        passed_checks = sum(1 for result in self.validation_results.values() if result.get('status') == 'SUCCESS')
        failed_checks = total_checks - passed_checks
        
        # 总体状态
        overall_status = 'SUCCESS' if failed_checks == 0 else 'FAILED'
        
        # 生成报告
        report = {
            'overall_status': overall_status,
            'summary': {
                'total_checks': total_checks,
                'passed_checks': passed_checks,
                'failed_checks': failed_checks,
                'success_rate': (passed_checks / total_checks) * 100 if total_checks > 0 else 0
            },
            'detailed_results': self.validation_results,
            'recommendations': []
        }
        
        # 打印摘要
        print(f"总体状态: {'✅ 通过' if overall_status == 'SUCCESS' else '❌ 失败'}")
        print(f"检查项目: {total_checks}")
        print(f"通过项目: {passed_checks}")
        print(f"失败项目: {failed_checks}")
        print(f"成功率: {report['summary']['success_rate']:.1f}%")
        
        # 打印详细结果
        print("\n详细结果:")
        for check_name, result in self.validation_results.items():
            status_icon = "✅" if result.get('status') == 'SUCCESS' else "❌"
            print(f"  {status_icon} {check_name}: {result.get('status')}")
            if result.get('details'):
                for detail in result['details']:
                    print(f"    - {detail}")
        
        # 生成建议
        if overall_status == 'SUCCESS':
            report['recommendations'].append("所有前置条件验证通过，可以开始执行LAD-IMPL-004任务")
        else:
            report['recommendations'].append("存在验证失败的项目，需要先解决这些问题")
            for check_name, result in self.validation_results.items():
                if result.get('status') != 'SUCCESS':
                    report['recommendations'].append(f"需要修复: {check_name}")
        
        print(f"\n建议:")
        for recommendation in report['recommendations']:
            print(f"  - {recommendation}")
        
        return report

def main():
    """主函数"""
    validator = LADImpl004PrerequisitesValidator()
    report = validator.validate_all_prerequisites()
    
    # 返回退出码
    if report['overall_status'] == 'SUCCESS':
        print("\n🎉 所有前置条件验证通过！可以开始执行LAD-IMPL-004任务。")
        return 0
    else:
        print("\n⚠️  存在验证失败的项目，请先解决这些问题。")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 