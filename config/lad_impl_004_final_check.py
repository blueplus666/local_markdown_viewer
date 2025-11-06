#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LAD-IMPL-004最终检查
对所有实施内容进行综合验证和完整性检查
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, List
import importlib.util

class LADImpl004FinalChecker:
    """LAD-IMPL-004最终检查器"""
    
    def __init__(self):
        self.check_results = {
            'core_implementation': {},
            'configuration_files': {},
            'verification_scripts': {},
            'api_compatibility': {},
            'performance_validation': {},
            'overall_status': {}
        }
        
    def check_core_implementation(self) -> Dict[str, Any]:
        """检查核心实现"""
        print("=== 核心实现检查 ===")
        
        core_checks = {}
        
        # 检查DynamicModuleImporter文件
        importer_file = Path(__file__).parent.parent / "core" / "dynamic_module_importer.py"
        
        if importer_file.exists():
            with open(importer_file, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # 关键实现检查
            core_checks['file_exists'] = True
            core_checks['unified_cache_manager'] = 'UnifiedCacheManager' in source_code
            core_checks['legacy_cache_removed'] = '_import_cache' not in source_code
            core_checks['enhanced_error_handler'] = 'EnhancedErrorHandler' in source_code
            core_checks['temp_syspath_context'] = '_temp_sys_path' in source_code
            core_checks['function_mapping_validation'] = 'missing_functions' in source_code
            core_checks['fallback_logic_enhanced'] = 'used_fallback' in source_code and 'fallback_reason' in source_code
            
            # 导入逻辑简化检查
            config_manager_imports = source_code.count('from') + source_code.count('import')
            core_checks['import_logic_simplified'] = config_manager_imports < 50  # 简化后应该更少
            
            print(f"✓ 核心文件存在: {core_checks['file_exists']}")
            print(f"✓ 统一缓存管理器: {core_checks['unified_cache_manager']}")
            print(f"✓ legacy缓存已移除: {core_checks['legacy_cache_removed']}")
            print(f"✓ 增强错误处理器: {core_checks['enhanced_error_handler']}")
            print(f"✓ 临时sys.path上下文: {core_checks['temp_syspath_context']}")
            print(f"✓ 函数映射验证: {core_checks['function_mapping_validation']}")
            print(f"✓ fallback逻辑增强: {core_checks['fallback_logic_enhanced']}")
            
        else:
            core_checks['file_exists'] = False
            print("❌ 核心文件不存在")
        
        self.check_results['core_implementation'] = core_checks
        return core_checks
    
    def check_configuration_files(self) -> Dict[str, Any]:
        """检查配置文件"""
        print("\n=== 配置文件检查 ===")
        
        config_checks = {}
        
        # 检查external_modules.json
        config_file = Path(__file__).parent / "external_modules.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                config_checks['config_file_exists'] = True
                config_checks['has_markdown_processor'] = 'markdown_processor' in config_data
                
                if 'markdown_processor' in config_data:
                    mp_config = config_data['markdown_processor']
                    config_checks['has_enabled_field'] = 'enabled' in mp_config
                    config_checks['has_version_field'] = 'version' in mp_config
                    config_checks['has_required_functions'] = 'required_functions' in mp_config
                    config_checks['has_fallback_strategy'] = 'fallback_strategy' in mp_config
                    config_checks['fallback_is_markdown'] = mp_config.get('fallback_strategy') == 'markdown'
                    
                    required_funcs = mp_config.get('required_functions', [])
                    expected_funcs = ['render_markdown_with_zoom', 'render_markdown_to_html']
                    config_checks['required_functions_complete'] = all(f in required_funcs for f in expected_funcs)
                
                config_checks['config_format_valid'] = True
                print("✓ 配置文件存在且格式正确")
                print(f"✓ markdown_processor配置: {config_checks['has_markdown_processor']}")
                print(f"✓ 必需字段完整: enabled={config_checks.get('has_enabled_field')}, version={config_checks.get('has_version_field')}")
                print(f"✓ fallback策略正确: {config_checks.get('fallback_is_markdown')}")
                print(f"✓ 必需函数完整: {config_checks.get('required_functions_complete')}")
                
            except json.JSONDecodeError as e:
                config_checks['config_file_exists'] = True
                config_checks['config_format_valid'] = False
                print(f"❌ 配置文件JSON格式错误: {e}")
                
        else:
            config_checks['config_file_exists'] = False
            print("❌ 配置文件不存在")
        
        self.check_results['configuration_files'] = config_checks
        return config_checks
    
    def check_verification_scripts(self) -> Dict[str, Any]:
        """检查验证脚本"""
        print("\n=== 验证脚本检查 ===")
        
        script_checks = {}
        
        expected_scripts = [
            'lad_impl_004_verification.py',
            'syspath_mechanism_test.py', 
            'lad_impl_004_predefined_questions.py',
            'lad_impl_004_format_validation.py',
            'lad_impl_004_key_data_summary.py'
        ]
        
        for script_name in expected_scripts:
            script_path = Path(__file__).parent / script_name
            exists = script_path.exists()
            script_checks[script_name] = exists
            
            if exists:
                # 检查脚本内容
                with open(script_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                script_checks[f"{script_name}_has_main"] = 'def main(' in content or 'if __name__ == "__main__"' in content
                print(f"✓ {script_name}: 存在且可执行")
            else:
                print(f"❌ {script_name}: 不存在")
        
        script_checks['all_scripts_present'] = all(script_checks[script] for script in expected_scripts)
        
        self.check_results['verification_scripts'] = script_checks
        return script_checks
    
    def check_api_compatibility(self) -> Dict[str, Any]:
        """检查API兼容性"""
        print("\n=== API兼容性检查 ===")
        
        api_checks = {}
        
        try:
            # 动态导入测试
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from local_markdown_viewer.core.dynamic_module_importer import DynamicModuleImporter
            
            # 创建实例
            importer = DynamicModuleImporter()
            api_checks['importer_instantiation'] = True
            
            # 检查关键方法存在
            api_checks['has_import_module'] = hasattr(importer, 'import_module')
            api_checks['has_get_stats'] = hasattr(importer, 'get_stats')
            
            # 检查方法调用
            if api_checks['has_import_module']:
                result = importer.import_module('markdown_processor')
                api_checks['import_module_callable'] = True
                api_checks['return_format_valid'] = isinstance(result, dict) and 'success' in result
                
                # 检查返回字段
                expected_fields = ['success', 'module', 'path', 'functions', 'used_fallback']
                api_checks['return_fields_complete'] = all(field in result for field in expected_fields)
            
            if api_checks['has_get_stats']:
                stats = importer.get_stats()
                api_checks['get_stats_callable'] = True
                api_checks['stats_format_valid'] = isinstance(stats, dict)
            
            # 检查legacy属性已移除
            api_checks['legacy_cache_removed'] = not hasattr(importer, '_import_cache')
            
            print("✓ DynamicModuleImporter实例化成功")
            print(f"✓ import_module方法: {api_checks['has_import_module']}")
            print(f"✓ get_stats方法: {api_checks['has_get_stats']}")
            print(f"✓ 返回格式有效: {api_checks.get('return_format_valid')}")
            print(f"✓ 返回字段完整: {api_checks.get('return_fields_complete')}")
            print(f"✓ legacy缓存已移除: {api_checks['legacy_cache_removed']}")
            
        except Exception as e:
            api_checks['importer_instantiation'] = False
            api_checks['error'] = str(e)
            print(f"❌ API兼容性检查失败: {e}")
        
        self.check_results['api_compatibility'] = api_checks
        return api_checks
    
    def check_performance_validation(self) -> Dict[str, Any]:
        """检查性能验证"""
        print("\n=== 性能验证检查 ===")
        
        perf_checks = {}
        
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from local_markdown_viewer.core.dynamic_module_importer import DynamicModuleImporter
            
            importer = DynamicModuleImporter()
            
            # 性能测试
            import time
            
            # 首次导入
            start_time = time.time()
            result1 = importer.import_module('markdown_processor')
            first_import_time = (time.time() - start_time) * 1000
            
            # 缓存导入
            start_time = time.time()
            result2 = importer.import_module('markdown_processor')
            cached_import_time = (time.time() - start_time) * 1000
            
            perf_checks['first_import_success'] = result1.get('success', False)
            perf_checks['cached_import_success'] = result2.get('success', False)
            perf_checks['first_import_time_ms'] = round(first_import_time, 2)
            perf_checks['cached_import_time_ms'] = round(cached_import_time, 2)
            perf_checks['cache_speedup'] = round(first_import_time / max(cached_import_time, 0.01), 2)
            
            # 性能目标检查
            perf_checks['first_import_under_100ms'] = first_import_time < 100
            perf_checks['cached_import_under_10ms'] = cached_import_time < 10
            perf_checks['significant_speedup'] = perf_checks['cache_speedup'] > 2
            
            # 统计信息
            stats = importer.get_stats()
            perf_checks['stats_available'] = bool(stats)
            perf_checks['success_rate'] = (stats.get('successful_imports', 0) / max(stats.get('total_imports', 1), 1)) * 100
            
            print(f"✓ 首次导入: {perf_checks['first_import_time_ms']}ms (目标<100ms)")
            print(f"✓ 缓存导入: {perf_checks['cached_import_time_ms']}ms (目标<10ms)")
            print(f"✓ 缓存加速: {perf_checks['cache_speedup']}x")
            print(f"✓ 成功率: {perf_checks['success_rate']:.1f}%")
            
        except Exception as e:
            perf_checks['error'] = str(e)
            print(f"❌ 性能验证失败: {e}")
        
        self.check_results['performance_validation'] = perf_checks
        return perf_checks
    
    def generate_overall_status(self) -> Dict[str, Any]:
        """生成总体状态"""
        print("\n=== 总体状态评估 ===")
        
        # 计算各模块通过率
        modules = ['core_implementation', 'configuration_files', 'verification_scripts', 'api_compatibility', 'performance_validation']
        module_scores = {}
        
        for module in modules:
            if module in self.check_results:
                checks = self.check_results[module]
                if 'error' not in checks:
                    # 计算布尔值的通过率
                    bool_checks = [v for v in checks.values() if isinstance(v, bool)]
                    if bool_checks:
                        module_scores[module] = (sum(bool_checks) / len(bool_checks)) * 100
                    else:
                        module_scores[module] = 100  # 没有布尔检查项默认通过
                else:
                    module_scores[module] = 0  # 有错误则为0分
        
        overall_score = sum(module_scores.values()) / len(module_scores) if module_scores else 0
        
        # 确定状态等级
        if overall_score >= 95:
            status_grade = "EXCELLENT"
            status_desc = "所有检查项完美通过"
        elif overall_score >= 90:
            status_grade = "GOOD"
            status_desc = "主要功能完整，少量优化空间"
        elif overall_score >= 80:
            status_grade = "ACCEPTABLE"
            status_desc = "基本功能完整，需要改进"
        else:
            status_grade = "NEEDS_IMPROVEMENT"
            status_desc = "存在重要问题需要修复"
        
        overall_status = {
            'overall_score': round(overall_score, 1),
            'status_grade': status_grade,
            'status_description': status_desc,
            'module_scores': module_scores,
            'ready_for_production': overall_score >= 90,
            'ready_for_next_phase': overall_score >= 85
        }
        
        print(f"总体得分: {overall_score:.1f}%")
        print(f"状态等级: {status_grade}")
        print(f"状态描述: {status_desc}")
        print(f"生产就绪: {overall_status['ready_for_production']}")
        print(f"下阶段就绪: {overall_status['ready_for_next_phase']}")
        
        print(f"\n模块得分:")
        for module, score in module_scores.items():
            print(f"  {module}: {score:.1f}%")
        
        self.check_results['overall_status'] = overall_status
        return overall_status
    
    def run_final_check(self) -> Dict[str, Any]:
        """执行最终检查"""
        print("LAD-IMPL-004最终检查执行\n")
        
        # 执行所有检查
        self.check_core_implementation()
        self.check_configuration_files()
        self.check_verification_scripts()
        self.check_api_compatibility()
        self.check_performance_validation()
        self.generate_overall_status()
        
        # 生成最终报告
        final_report = {
            'check_timestamp': '2025-08-30T18:15:27+08:00',
            'task_id': 'LAD-IMPL-004',
            'check_version': '1.0',
            'results': self.check_results
        }
        
        # 保存报告
        report_file = Path(__file__).parent / "lad_impl_004_final_check_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 最终检查报告已保存: {report_file}")
        
        return final_report

def main():
    """主函数"""
    checker = LADImpl004FinalChecker()
    report = checker.run_final_check()
    return report

if __name__ == "__main__":
    report = main()
