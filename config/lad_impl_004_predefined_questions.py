#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LAD-IMPL-004补漏-B：4个预设追问计划执行
根据原始任务要求执行完整性、鲁棒性、代码质量和向后兼容性验证
"""

import sys
import os
from pathlib import Path
import importlib
import traceback
from typing import Dict, Any, List

class LADImpl004QualityAssurance:
    """LAD-IMPL-004质量保证验证器"""
    
    def __init__(self):
        self.results = {
            'completeness': {'score': 0, 'details': []},
            'robustness': {'score': 0, 'details': []},
            'code_quality': {'score': 0, 'details': []},
            'backward_compatibility': {'score': 0, 'details': []}
        }
        
    def question_1_completeness_coverage(self) -> Dict[str, Any]:
        """预设追问1：导入场景覆盖完整性检查"""
        print("=== 追问1：导入场景覆盖完整性 ===")
        
        scenarios = [
            "正常模块导入",
            "配置文件驱动导入", 
            "fallback模块导入",
            "缓存命中场景",
            "临时sys.path导入",
            "函数映射验证",
            "错误恢复机制"
        ]
        
        coverage_results = []
        
        try:
            # 导入DynamicModuleImporter
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from local_markdown_viewer.core.dynamic_module_importer import DynamicModuleImporter
            
            importer = DynamicModuleImporter()
            
            # 场景1：正常模块导入
            result1 = importer.import_module('markdown_processor')
            coverage_results.append({
                'scenario': '正常模块导入',
                'covered': result1.get('success', False),
                'details': f"成功: {result1.get('success')}, 路径: {result1.get('path', 'N/A')}"
            })
            
            # 场景2：配置文件驱动导入
            config_driven = hasattr(importer, '_module_paths') and len(importer._module_paths) > 0
            coverage_results.append({
                'scenario': '配置文件驱动导入',
                'covered': config_driven,
                'details': f"配置模块数: {len(getattr(importer, '_module_paths', {}))}"
            })
            
            # 场景3：fallback导入
            result3 = importer.import_module('nonexistent_module', ['markdown'])
            coverage_results.append({
                'scenario': 'fallback模块导入',
                'covered': result3.get('used_fallback', False),
                'details': f"使用fallback: {result3.get('used_fallback')}"
            })
            
            # 场景4：缓存验证
            result4a = importer.import_module('markdown_processor')
            result4b = importer.import_module('markdown_processor')
            cache_hit = result4b.get('cache_hit', False)
            coverage_results.append({
                'scenario': '缓存命中场景',
                'covered': cache_hit,
                'details': f"缓存命中: {cache_hit}"
            })
            
            # 场景5：临时sys.path机制检查
            temp_syspath_method = hasattr(importer, '_temp_sys_path')
            coverage_results.append({
                'scenario': '临时sys.path导入',
                'covered': temp_syspath_method,
                'details': f"临时路径方法存在: {temp_syspath_method}"
            })
            
            # 场景6：函数映射验证
            functions = result1.get('functions', {})
            required_functions = ['render_markdown_with_zoom', 'render_markdown_to_html']
            function_coverage = all(func in functions for func in required_functions)
            coverage_results.append({
                'scenario': '函数映射验证',
                'covered': function_coverage,
                'details': f"必需函数覆盖: {len([f for f in required_functions if f in functions])}/{len(required_functions)}"
            })
            
            # 场景7：错误恢复机制
            error_handler_exists = hasattr(importer, 'error_handler')
            coverage_results.append({
                'scenario': '错误恢复机制',
                'covered': error_handler_exists,
                'details': f"错误处理器存在: {error_handler_exists}"
            })
            
        except Exception as e:
            coverage_results.append({
                'scenario': '导入器初始化',
                'covered': False,
                'details': f"异常: {str(e)}"
            })
        
        # 计算覆盖率
        covered_count = sum(1 for r in coverage_results if r['covered'])
        coverage_rate = covered_count / len(scenarios) * 100
        
        self.results['completeness'] = {
            'score': coverage_rate,
            'details': coverage_results,
            'summary': f"场景覆盖率: {coverage_rate:.1f}% ({covered_count}/{len(scenarios)})"
        }
        
        print(f"场景覆盖率: {coverage_rate:.1f}%")
        for result in coverage_results:
            status = "✓" if result['covered'] else "❌"
            print(f"  {status} {result['scenario']}: {result['details']}")
        
        return self.results['completeness']
    
    def question_2_robustness_check(self) -> Dict[str, Any]:
        """预设追问2：错误处理鲁棒性检查"""
        print("\n=== 追问2：错误处理鲁棒性 ===")
        
        robustness_tests = []
        
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from local_markdown_viewer.core.dynamic_module_importer import DynamicModuleImporter
            
            importer = DynamicModuleImporter()
            
            # 测试1：不存在的模块
            result1 = importer.import_module('completely_nonexistent_module')
            robustness_tests.append({
                'test': '不存在模块处理',
                'robust': not result1.get('success', True),
                'details': f"错误码: {result1.get('error_code', 'N/A')}"
            })
            
            # 测试2：空模块名
            result2 = importer.import_module('')
            robustness_tests.append({
                'test': '空模块名处理',
                'robust': not result2.get('success', True),
                'details': f"处理结果: {result2.get('message', 'N/A')}"
            })
            
            # 测试3：None参数
            try:
                result3 = importer.import_module(None)
                robustness_tests.append({
                    'test': 'None参数处理',
                    'robust': not result3.get('success', True),
                    'details': "异常被捕获"
                })
            except Exception as e:
                robustness_tests.append({
                    'test': 'None参数处理',
                    'robust': True,
                    'details': f"正确抛出异常: {type(e).__name__}"
                })
            
            # 测试4：错误统计
            stats = importer.get_stats()
            has_error_stats = 'failed_imports' in stats
            robustness_tests.append({
                'test': '错误统计记录',
                'robust': has_error_stats,
                'details': f"失败导入数: {stats.get('failed_imports', 'N/A')}"
            })
            
            # 测试5：错误恢复策略
            error_handler_exists = hasattr(importer, 'error_handler')
            robustness_tests.append({
                'test': '错误恢复策略',
                'robust': error_handler_exists,
                'details': f"错误处理器: {'存在' if error_handler_exists else '不存在'}"
            })
            
        except Exception as e:
            robustness_tests.append({
                'test': '鲁棒性测试初始化',
                'robust': False,
                'details': f"异常: {str(e)}"
            })
        
        # 计算鲁棒性分数
        robust_count = sum(1 for t in robustness_tests if t['robust'])
        robustness_score = robust_count / len(robustness_tests) * 100
        
        self.results['robustness'] = {
            'score': robustness_score,
            'details': robustness_tests,
            'summary': f"鲁棒性得分: {robustness_score:.1f}% ({robust_count}/{len(robustness_tests)})"
        }
        
        print(f"鲁棒性得分: {robustness_score:.1f}%")
        for test in robustness_tests:
            status = "✓" if test['robust'] else "❌"
            print(f"  {status} {test['test']}: {test['details']}")
        
        return self.results['robustness']
    
    def question_3_code_quality_check(self) -> Dict[str, Any]:
        """预设追问3：代码质量和最佳实践检查"""
        print("\n=== 追问3：代码质量和最佳实践 ===")
        
        quality_checks = []
        
        try:
            # 检查源码文件
            importer_file = Path(__file__).parent.parent / "core" / "dynamic_module_importer.py"
            
            if importer_file.exists():
                with open(importer_file, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                
                # 检查1：文档字符串
                has_docstrings = '"""' in source_code and 'Args:' in source_code
                quality_checks.append({
                    'check': '文档字符串完整性',
                    'passed': has_docstrings,
                    'details': f"包含文档字符串: {has_docstrings}"
                })
                
                # 检查2：类型注解
                has_type_hints = 'from typing import' in source_code and '->' in source_code
                quality_checks.append({
                    'check': '类型注解使用',
                    'passed': has_type_hints,
                    'details': f"使用类型注解: {has_type_hints}"
                })
                
                # 检查3：异常处理
                has_exception_handling = 'try:' in source_code and 'except' in source_code
                quality_checks.append({
                    'check': '异常处理机制',
                    'passed': has_exception_handling,
                    'details': f"包含异常处理: {has_exception_handling}"
                })
                
                # 检查4：日志记录
                has_logging = 'logging' in source_code and 'self.logger' in source_code
                quality_checks.append({
                    'check': '日志记录机制',
                    'passed': has_logging,
                    'details': f"使用日志记录: {has_logging}"
                })
                
                # 检查5：配置管理
                has_config_management = 'ConfigManager' in source_code
                quality_checks.append({
                    'check': '配置管理模式',
                    'passed': has_config_management,
                    'details': f"使用配置管理: {has_config_management}"
                })
                
                # 检查6：缓存机制
                has_caching = 'cache_manager' in source_code or 'UnifiedCacheManager' in source_code
                quality_checks.append({
                    'check': '缓存机制实现',
                    'passed': has_caching,
                    'details': f"实现缓存机制: {has_caching}"
                })
                
            else:
                quality_checks.append({
                    'check': '源码文件访问',
                    'passed': False,
                    'details': f"文件不存在: {importer_file}"
                })
                
        except Exception as e:
            quality_checks.append({
                'check': '代码质量检查初始化',
                'passed': False,
                'details': f"异常: {str(e)}"
            })
        
        # 计算质量分数
        passed_count = sum(1 for c in quality_checks if c['passed'])
        quality_score = passed_count / len(quality_checks) * 100 if quality_checks else 0
        
        self.results['code_quality'] = {
            'score': quality_score,
            'details': quality_checks,
            'summary': f"代码质量得分: {quality_score:.1f}% ({passed_count}/{len(quality_checks)})"
        }
        
        print(f"代码质量得分: {quality_score:.1f}%")
        for check in quality_checks:
            status = "✓" if check['passed'] else "❌"
            print(f"  {status} {check['check']}: {check['details']}")
        
        return self.results['code_quality']
    
    def question_4_backward_compatibility_check(self) -> Dict[str, Any]:
        """预设追问4：向后兼容性验证"""
        print("\n=== 追问4：向后兼容性验证 ===")
        
        compatibility_tests = []
        
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from local_markdown_viewer.core.dynamic_module_importer import DynamicModuleImporter
            
            importer = DynamicModuleImporter()
            
            # 测试1：原有API接口保持
            has_import_module = hasattr(importer, 'import_module')
            compatibility_tests.append({
                'test': 'import_module方法保持',
                'compatible': has_import_module,
                'details': f"方法存在: {has_import_module}"
            })
            
            # 测试2：返回格式兼容性
            result = importer.import_module('markdown_processor')
            required_fields = ['success', 'module', 'path']
            has_required_fields = all(field in result for field in required_fields)
            compatibility_tests.append({
                'test': '返回格式兼容性',
                'compatible': has_required_fields,
                'details': f"必需字段完整: {has_required_fields}"
            })
            
            # 测试3：统计接口保持
            has_get_stats = hasattr(importer, 'get_stats')
            compatibility_tests.append({
                'test': 'get_stats方法保持',
                'compatible': has_get_stats,
                'details': f"统计方法存在: {has_get_stats}"
            })
            
            # 测试4：配置初始化兼容
            try:
                importer_no_config = DynamicModuleImporter()
                init_compatible = True
            except Exception:
                init_compatible = False
            
            compatibility_tests.append({
                'test': '无参数初始化兼容',
                'compatible': init_compatible,
                'details': f"默认初始化: {'成功' if init_compatible else '失败'}"
            })
            
            # 测试5：legacy缓存移除不影响功能
            # 检查是否还有_import_cache属性（应该被移除）
            no_legacy_cache = not hasattr(importer, '_import_cache')
            compatibility_tests.append({
                'test': 'legacy缓存清理',
                'compatible': no_legacy_cache,
                'details': f"legacy缓存已移除: {no_legacy_cache}"
            })
            
        except Exception as e:
            compatibility_tests.append({
                'test': '兼容性测试初始化',
                'compatible': False,
                'details': f"异常: {str(e)}"
            })
        
        # 计算兼容性分数
        compatible_count = sum(1 for t in compatibility_tests if t['compatible'])
        compatibility_score = compatible_count / len(compatibility_tests) * 100
        
        self.results['backward_compatibility'] = {
            'score': compatibility_score,
            'details': compatibility_tests,
            'summary': f"向后兼容性得分: {compatibility_score:.1f}% ({compatible_count}/{len(compatibility_tests)})"
        }
        
        print(f"向后兼容性得分: {compatibility_score:.1f}%")
        for test in compatibility_tests:
            status = "✓" if test['compatible'] else "❌"
            print(f"  {status} {test['test']}: {test['details']}")
        
        return self.results['backward_compatibility']
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成综合质量报告"""
        print("\n=== LAD-IMPL-004 综合质量报告 ===")
        
        # 计算总体得分
        scores = [
            self.results['completeness']['score'],
            self.results['robustness']['score'], 
            self.results['code_quality']['score'],
            self.results['backward_compatibility']['score']
        ]
        
        overall_score = sum(scores) / len(scores)
        
        # 确定质量等级
        if overall_score >= 90:
            quality_grade = "优秀"
        elif overall_score >= 80:
            quality_grade = "良好"
        elif overall_score >= 70:
            quality_grade = "合格"
        else:
            quality_grade = "需改进"
        
        report = {
            'overall_score': overall_score,
            'quality_grade': quality_grade,
            'dimension_scores': {
                'completeness': self.results['completeness']['score'],
                'robustness': self.results['robustness']['score'],
                'code_quality': self.results['code_quality']['score'],
                'backward_compatibility': self.results['backward_compatibility']['score']
            },
            'detailed_results': self.results,
            'recommendations': []
        }
        
        # 生成改进建议
        if self.results['completeness']['score'] < 80:
            report['recommendations'].append("增加更多导入场景的测试覆盖")
        if self.results['robustness']['score'] < 80:
            report['recommendations'].append("加强异常处理和错误恢复机制")
        if self.results['code_quality']['score'] < 80:
            report['recommendations'].append("改进代码文档和类型注解")
        if self.results['backward_compatibility']['score'] < 80:
            report['recommendations'].append("确保API向后兼容性")
        
        print(f"总体得分: {overall_score:.1f}% - {quality_grade}")
        print(f"完整性: {self.results['completeness']['score']:.1f}%")
        print(f"鲁棒性: {self.results['robustness']['score']:.1f}%")
        print(f"代码质量: {self.results['code_quality']['score']:.1f}%")
        print(f"向后兼容性: {self.results['backward_compatibility']['score']:.1f}%")
        
        if report['recommendations']:
            print("\n改进建议:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        return report

def main():
    """执行4个预设追问计划"""
    print("LAD-IMPL-004补漏-B：4个预设追问计划执行\n")
    
    qa = LADImpl004QualityAssurance()
    
    # 执行4个预设追问
    qa.question_1_completeness_coverage()
    qa.question_2_robustness_check()
    qa.question_3_code_quality_check()
    qa.question_4_backward_compatibility_check()
    
    # 生成综合报告
    report = qa.generate_comprehensive_report()
    
    return report

if __name__ == "__main__":
    report = main()
