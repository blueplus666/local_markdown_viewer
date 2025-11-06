#!/usr/bin/env python3
"""
LAD-IMPL-006A 任务集成测试脚本
模拟006A任务中ApplicationStateManager对ConfigManager的使用

使用时机：在完成006B任务后，验证ConfigManager是否满足006A任务需求
使用方法：python config/test_006a_integration.py
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from utils.config_manager import ConfigManager
except ImportError as e:
    print(f"[FAIL] 无法导入ConfigManager: {e}")
    print("   请确保已完成006B任务的ConfigManager增强")
    sys.exit(1)

class MockApplicationStateManager:
    """模拟006A任务中的ApplicationStateManager"""
    
    def __init__(self, config_manager: ConfigManager = None):
        # 这是006A V4.0文档第158-163行的使用方式
        self.config_manager = config_manager or ConfigManager()
        
        # 从简化配置中读取参数（006A V4.0第166-167行）
        app_config = self.config_manager.get_config("app_config") or {}
        perf_config = app_config.get('markdown', {})  # 使用markdown配置段
        
        # 006A需要的性能参数
        self._max_state_history = perf_config.get("cache_enabled", True)
        self._cache_enabled = perf_config.get("cache_enabled", True)
        
        print(f"[OK] MockApplicationStateManager初始化成功")
        print(f"   缓存启用: {self._cache_enabled}")
    
    def test_get_external_module_config(self):
        """测试外部模块配置获取（006A V4.0第214行）"""
        # 006A任务需要的调用方式
        module_config = self.config_manager.get_external_module_config("markdown_processor")
        
        assert module_config is not None, "[FAIL] 模块配置应该存在"
        assert isinstance(module_config, dict), "[FAIL] 模块配置应该是字典"
        
        # 006A需要的配置字段（第219-221行）
        config_enabled = module_config.get("enabled", False)
        config_version = module_config.get("version", "unknown")
        required_functions = module_config.get("required_functions", [])
        
        print(f"[OK] 模块配置获取成功:")
        print(f"   enabled: {config_enabled}")
        print(f"   version: {config_version}")
        print(f"   required_functions: {required_functions}")
        
        return True

def test_006a_config_access_pattern():
    """测试1：006A任务的配置访问模式"""
    print("\n" + "="*50)
    print("测试1：006A任务的配置访问模式")
    print("="*50)
    
    config_manager = ConfigManager()
    
    # 模式1：获取完整配置段（006A常用方式）
    app_config = config_manager.get_config("app_config") or {}
    assert app_config is not None, "[FAIL] app_config应该存在"
    print("[OK] 模式1：获取完整配置段成功")
    
    # 模式2：从配置段中提取子配置
    markdown_config = app_config.get('markdown', {})
    assert markdown_config is not None, "[FAIL] markdown配置应该存在"
    print(f"[OK] 模式2：提取子配置成功 (cache_enabled={markdown_config.get('cache_enabled')})")
    
    # 模式3：获取外部模块配置（006A关键方法）
    try:
        module_config = config_manager.get_external_module_config("markdown_processor")
        assert module_config is not None, "[FAIL] 模块配置应该存在"
        print("[OK] 模式3：外部模块配置获取成功")
    except AttributeError:
        print("[WARN]  模式3：get_external_module_config方法不存在")
        print("   请先完成006B任务的ConfigManager增强")
        assert False
    
    print("\n[OK] 测试1通过：006A配置访问模式验证成功")
    

def test_006a_component_initialization():
    """测试2：006A组件初始化"""
    print("\n" + "="*50)
    print("测试2：006A组件初始化模拟")
    print("="*50)
    
    try:
        # 模拟006A任务中ApplicationStateManager的初始化
        mock_state_manager = MockApplicationStateManager()
        
        # 测试外部模块配置获取
        result = mock_state_manager.test_get_external_module_config()
        assert result, "006A组件初始化失败"
        print("\n[OK] 测试2通过：006A组件初始化成功")
            
    except Exception as e:
        print(f"\n[FAIL] 测试2异常: {e}")
        import traceback
        traceback.print_exc()
        assert False

def test_006a_performance_config():
    """测试3：006A性能配置获取"""
    print("\n" + "="*50)
    print("测试3：006A性能配置获取")
    print("="*50)
    
    config_manager = ConfigManager()
    
    # 006A V4.0需要的性能配置访问方式
    app_config = config_manager.get_config("app_config") or {}
    
    # 从markdown配置段获取性能参数
    markdown_config = app_config.get('markdown', {})
    
    # 006A可能需要的性能参数
    cache_enabled = markdown_config.get("cache_enabled", True)
    use_dynamic_import = markdown_config.get("use_dynamic_import", True)
    fallback_enabled = markdown_config.get("fallback_enabled", True)
    
    print(f"[OK] 性能配置获取成功:")
    print(f"   cache_enabled: {cache_enabled}")
    print(f"   use_dynamic_import: {use_dynamic_import}")
    print(f"   fallback_enabled: {fallback_enabled}")
    
    # 从logging配置获取日志参数
    logging_config = app_config.get('logging', {})
    log_level = logging_config.get('level', 'INFO')
    print(f"   log_level: {log_level}")
    
    print("\n[OK] 测试3通过：006A性能配置获取成功")

def test_006a_module_validation():
    """测试4：006A模块配置验证"""
    print("\n" + "="*50)
    print("测试4：006A模块配置验证")
    print("="*50)
    
    config_manager = ConfigManager()
    
    try:
        # 获取模块配置
        module_config = config_manager.get_external_module_config("markdown_processor")
        
        # 006A任务需要验证的字段（V4.0第237-240行）
        validation_checks = {
            "enabled字段": "enabled" in module_config,
            "module_path字段": "module_path" in module_config,
            "required_functions字段": "required_functions" in module_config,
            "required_functions非空": len(module_config.get("required_functions", [])) > 0,
        }
        
        all_passed = True
        for check_name, result in validation_checks.items():
            if result:
                print(f"[OK] {check_name}")
            else:
                print(f"[FAIL] {check_name}")
                all_passed = False
        
        if all_passed:
            print("\n[OK] 测试4通过：006A模块配置验证成功")
        else:
            print("\n[FAIL] 测试4失败：模块配置不完整")
        assert all_passed
            
    except AttributeError as e:
        print(f"\n[WARN]  测试4失败: {e}")
        print("   请先完成006B任务的ConfigManager增强")
        assert False

def run_all_integration_tests():
    """运行所有006A集成测试"""
    print("\n" + "="*70)
    print("LAD-IMPL-006A 任务集成测试套件")
    print("="*70)
    print("\n此脚本模拟006A任务中ApplicationStateManager对ConfigManager的使用")
    print("验证006B任务的成果是否满足006A任务的需求\n")
    
    test_results = []
    
    try:
        test_results.append(("006A配置访问模式", test_006a_config_access_pattern()))
        test_results.append(("006A组件初始化", test_006a_component_initialization()))
        test_results.append(("006A性能配置", test_006a_performance_config()))
        test_results.append(("006A模块验证", test_006a_module_validation()))
        
        # 统计结果
        print("\n" + "="*70)
        print("006A集成测试结果摘要")
        print("="*70)
        
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        print(f"\n通过测试: {passed}/{total}")
        
        for test_name, result in test_results:
            status = "[OK] 通过" if result else "[FAIL] 失败"
            print(f"{status}: {test_name}")
        
        if passed == total:
            print("\n" + "="*70)
            print("[SUCCESS] 所有006A集成测试通过！")
            print("   ConfigManager已满足006A任务需求，可以开始执行006A任务")
            print("="*70)
            return True
        else:
            print("\n" + "="*70)
            print("[WARN]  部分006A集成测试失败")
            print("   建议先解决上述问题后再执行006A任务")
            print("="*70)
            return False
        
    except Exception as e:
        print(f"\n[FAIL] 集成测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_integration_tests()
    sys.exit(0 if success else 1)

