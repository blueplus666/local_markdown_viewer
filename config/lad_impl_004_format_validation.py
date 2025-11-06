#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LAD-IMPL-004补漏-C：标准化结果格式验证
验证DynamicModuleImporter返回结果的标准化格式完整性
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Set

class ResultFormatValidator:
    """结果格式验证器"""
    
    def __init__(self):
        self.validation_results = []
        
    def validate_success_result_format(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """验证成功结果的标准化格式"""
        print("=== 成功结果格式验证 ===")
        
        # 必需字段定义
        required_fields = {
            'success': bool,
            'module': str,
            'path': str,
            'functions': dict,
            'used_fallback': bool
        }
        
        # 可选字段定义
        optional_fields = {
            'cached': bool,
            'elapsed_ms': (int, float),
            'cache_hit': bool,
            'function_validation': str,
            'error_id': str,
            'error_category': str
        }
        
        validation_result = {
            'format_type': 'success_result',
            'required_fields_check': [],
            'optional_fields_check': [],
            'type_validation': [],
            'overall_valid': True
        }
        
        # 检查必需字段
        for field, expected_type in required_fields.items():
            if field in result:
                actual_type = type(result[field])
                type_match = actual_type == expected_type
                validation_result['required_fields_check'].append({
                    'field': field,
                    'present': True,
                    'expected_type': expected_type.__name__,
                    'actual_type': actual_type.__name__,
                    'type_valid': type_match
                })
                if not type_match:
                    validation_result['overall_valid'] = False
            else:
                validation_result['required_fields_check'].append({
                    'field': field,
                    'present': False,
                    'expected_type': expected_type.__name__,
                    'actual_type': 'missing',
                    'type_valid': False
                })
                validation_result['overall_valid'] = False
        
        # 检查可选字段
        for field, expected_type in optional_fields.items():
            if field in result:
                actual_type = type(result[field])
                if isinstance(expected_type, tuple):
                    type_match = actual_type in expected_type
                    expected_type_str = ' | '.join(t.__name__ for t in expected_type)
                else:
                    type_match = actual_type == expected_type
                    expected_type_str = expected_type.__name__
                    
                validation_result['optional_fields_check'].append({
                    'field': field,
                    'present': True,
                    'expected_type': expected_type_str,
                    'actual_type': actual_type.__name__,
                    'type_valid': type_match
                })
        
        # 特殊验证：functions字段内容
        if 'functions' in result and isinstance(result['functions'], dict):
            functions = result['functions']
            required_functions = ['render_markdown_with_zoom', 'render_markdown_to_html']
            
            for func_name in required_functions:
                if func_name in functions:
                    is_callable = callable(functions[func_name])
                    validation_result['type_validation'].append({
                        'check': f'function_{func_name}_callable',
                        'valid': is_callable,
                        'details': f"{func_name}可调用: {is_callable}"
                    })
                    if not is_callable:
                        validation_result['overall_valid'] = False
                else:
                    validation_result['type_validation'].append({
                        'check': f'function_{func_name}_present',
                        'valid': False,
                        'details': f"{func_name}不存在"
                    })
                    validation_result['overall_valid'] = False
        
        return validation_result
    
    def validate_error_result_format(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """验证错误结果的标准化格式"""
        print("=== 错误结果格式验证 ===")
        
        # 错误结果必需字段
        required_fields = {
            'success': bool,
            'error_code': str,
            'message': str,
            'attempted_paths': list,
            'used_fallback': bool
        }
        
        # 错误结果可选字段
        optional_fields = {
            'elapsed_ms': (int, float),
            'error_id': str,
            'error_category': str,
            'missing_functions': list
        }
        
        validation_result = {
            'format_type': 'error_result',
            'required_fields_check': [],
            'optional_fields_check': [],
            'semantic_validation': [],
            'overall_valid': True
        }
        
        # 检查必需字段
        for field, expected_type in required_fields.items():
            if field in result:
                actual_type = type(result[field])
                type_match = actual_type == expected_type
                validation_result['required_fields_check'].append({
                    'field': field,
                    'present': True,
                    'expected_type': expected_type.__name__,
                    'actual_type': actual_type.__name__,
                    'type_valid': type_match
                })
                if not type_match:
                    validation_result['overall_valid'] = False
            else:
                validation_result['required_fields_check'].append({
                    'field': field,
                    'present': False,
                    'expected_type': expected_type.__name__,
                    'actual_type': 'missing',
                    'type_valid': False
                })
                validation_result['overall_valid'] = False
        
        # 语义验证
        if 'success' in result:
            success_false = result['success'] == False
            validation_result['semantic_validation'].append({
                'check': 'success_field_false',
                'valid': success_false,
                'details': f"success字段为False: {success_false}"
            })
            if not success_false:
                validation_result['overall_valid'] = False
        
        if 'error_code' in result and 'message' in result:
            has_error_info = bool(result['error_code']) and bool(result['message'])
            validation_result['semantic_validation'].append({
                'check': 'error_info_present',
                'valid': has_error_info,
                'details': f"错误信息完整: {has_error_info}"
            })
            if not has_error_info:
                validation_result['overall_valid'] = False
        
        return validation_result
    
    def run_comprehensive_format_validation(self) -> Dict[str, Any]:
        """执行综合格式验证"""
        print("LAD-IMPL-004补漏-C：标准化结果格式验证\n")
        
        try:
            # 导入DynamicModuleImporter
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from local_markdown_viewer.core.dynamic_module_importer import DynamicModuleImporter
            
            importer = DynamicModuleImporter()
            
            # 测试1：成功导入结果格式
            success_result = importer.import_module('markdown_processor')
            print(f"成功导入测试结果: {success_result.get('success', False)}")
            
            if success_result.get('success'):
                success_validation = self.validate_success_result_format(success_result)
                self.validation_results.append(success_validation)
                
                print("成功结果格式检查:")
                for check in success_validation['required_fields_check']:
                    status = "✓" if check['present'] and check['type_valid'] else "❌"
                    print(f"  {status} {check['field']}: {check['expected_type']} -> {check['actual_type']}")
            
            # 测试2：失败导入结果格式
            error_result = importer.import_module('nonexistent_module_for_testing')
            print(f"\n失败导入测试结果: {error_result.get('success', True)}")
            
            if not error_result.get('success'):
                error_validation = self.validate_error_result_format(error_result)
                self.validation_results.append(error_validation)
                
                print("错误结果格式检查:")
                for check in error_validation['required_fields_check']:
                    status = "✓" if check['present'] and check['type_valid'] else "❌"
                    print(f"  {status} {check['field']}: {check['expected_type']} -> {check['actual_type']}")
            
            # 测试3：fallback结果格式
            fallback_result = importer.import_module('nonexistent_module', ['markdown'])
            print(f"\nFallback导入测试结果: {fallback_result.get('success', False)}")
            
            if fallback_result.get('success') and fallback_result.get('used_fallback'):
                fallback_validation = self.validate_success_result_format(fallback_result)
                self.validation_results.append(fallback_validation)
                
                print("Fallback结果格式检查:")
                print(f"  ✓ 使用fallback: {fallback_result.get('used_fallback')}")
                print(f"  ✓ 函数映射为空: {len(fallback_result.get('functions', {})) == 0}")
            
            # 生成综合报告
            return self.generate_validation_report()
            
        except Exception as e:
            print(f"❌ 格式验证异常: {e}")
            import traceback
            traceback.print_exc()
            return {'overall_valid': False, 'error': str(e)}
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        print("\n=== 标准化格式验证报告 ===")
        
        total_validations = len(self.validation_results)
        valid_formats = sum(1 for v in self.validation_results if v['overall_valid'])
        
        report = {
            'total_validations': total_validations,
            'valid_formats': valid_formats,
            'validation_rate': (valid_formats / total_validations * 100) if total_validations > 0 else 0,
            'detailed_results': self.validation_results,
            'compliance_status': 'COMPLIANT' if valid_formats == total_validations else 'NON_COMPLIANT'
        }
        
        print(f"验证总数: {total_validations}")
        print(f"通过验证: {valid_formats}")
        print(f"验证通过率: {report['validation_rate']:.1f}%")
        print(f"合规状态: {report['compliance_status']}")
        
        # 详细问题报告
        for i, validation in enumerate(self.validation_results, 1):
            if not validation['overall_valid']:
                print(f"\n问题 {i} ({validation['format_type']}):")
                for check in validation.get('required_fields_check', []):
                    if not check['present'] or not check['type_valid']:
                        print(f"  ❌ {check['field']}: {check.get('actual_type', 'missing')}")
        
        return report

def main():
    """主验证函数"""
    validator = ResultFormatValidator()
    report = validator.run_comprehensive_format_validation()
    return report

if __name__ == "__main__":
    report = main()
