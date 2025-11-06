#!/usr/bin/env python3
"""
ConfigManager功能测试脚本
测试V2.1增强版ConfigManager的所有功能

使用时机：在完成ConfigManager增强后，验证所有功能是否正常
使用方法：python config/test_config_manager.py
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from utils.config_manager import ConfigManager
except ImportError as e:
    print(f"❌ 无法导入ConfigManager: {e}")
    print("   请确保utils/config_manager.py文件存在")
    sys.exit(1)

def test_basic_config_access():
    """测试1：基本配置访问（向后兼容）"""
    print("\n" + "="*50)
    print("测试1: 基本配置访问(向后兼容)")
    print("="*50)
    
    config_manager = ConfigManager()
    
    # 测试1.1：访问app_config
    app_config = config_manager.get_config("app_config")
    assert app_config is not None, "❌ app_config应该存在"
    assert "app" in app_config, "❌ app_config应包含app字段"
    print("[OK] app_config访问成功")
    print(f"   应用名称: {app_config.get('app', {}).get('name', 'N/A')}")
    
    # 测试1.2：访问external_modules
    external_modules = config_manager.get_config("external_modules")
    assert external_modules is not None, "❌ external_modules应该存在"
    assert "external_modules" in external_modules, "❌ 应包含external_modules字段"
    print("[OK] external_modules访问成功")
    
    # 测试1.3：访问ui_config
    ui_config = config_manager.get_config("ui_config")
    assert ui_config is not None, "❌ ui_config应该存在"
    print("[OK] ui_config访问成功")
    
    # 测试1.4：访问不存在的配置
    nonexistent = config_manager.get_config("nonexistent_config", default=None)
    assert nonexistent is None, "❌ 不存在的配置应返回None"
    print("[OK] 不存在的配置返回默认值")
    
    print("\n[OK] 测试1通过: 基本配置访问正常")
    

def test_unified_config_access():
    """测试2：统一配置访问（新功能）"""
    print("\n" + "="*50)
    print("测试2：统一配置访问（新功能）")
    print("="*50)
    
    config_manager = ConfigManager()
    
    try:
        # 测试2.1：访问app配置
        app_name = config_manager.get_unified_config("app.name")
        assert app_name is not None, "❌ 应用名称应该存在"
        print(f"✅ 应用名称: {app_name}")
        
        # 测试2.2：访问嵌套配置
        window_width = config_manager.get_unified_config("app.window.width")
        assert window_width is not None, f"❌ 窗口宽度应该存在"
        print(f"✅ 窗口宽度: {window_width}")
        
        # 测试2.3：访问外部模块配置
        module_config = config_manager.get_unified_config("external_modules.markdown_processor")
        assert module_config is not None, "❌ markdown_processor配置应该存在"
        assert isinstance(module_config, dict), "❌ 模块配置应该是字典"
        print(f"✅ 模块配置: enabled={module_config.get('enabled', 'N/A')}")
        
        # 测试2.4：访问更深层的配置
        module_version = config_manager.get_unified_config("external_modules.markdown_processor.version")
        assert module_version is not None, f"❌ 模块版本应该存在"
        print(f"✅ 模块版本: {module_version}")
        
        # 测试2.5：访问required_functions
        required_functions = config_manager.get_unified_config("external_modules.markdown_processor.required_functions")
        assert required_functions is not None, "❌ 必需函数列表应该存在"
        assert isinstance(required_functions, list), "❌ 必需函数应该是列表"
        print(f"✅ 必需函数: {required_functions}")
        
        # 测试2.6：默认值测试
        nonexistent = config_manager.get_unified_config("nonexistent.config", default="default_value")
        assert nonexistent == "default_value", "❌ 应返回默认值"
        print("✅ 默认值返回正常")
        
        print("\n✅ 测试2通过：统一配置访问正常")
        
    except AttributeError as e:
        print(f"\n⚠️  测试2失败：get_unified_config方法可能不存在")
        print(f"   错误信息: {e}")
        print("   请确保已执行006B任务的ConfigManager增强")
        assert False

def test_external_module_config():
    """测试3：外部模块配置便捷方法"""
    print("\n" + "="*50)
    print("测试3：外部模块配置便捷方法")
    print("="*50)
    
    config_manager = ConfigManager()
    
    try:
        # 测试3.1：获取markdown_processor配置
        module_config = config_manager.get_external_module_config("markdown_processor")
        assert module_config is not None, "❌ markdown_processor配置应该存在"
        assert isinstance(module_config, dict), "❌ 模块配置应该是字典"
        print("✅ markdown_processor配置获取成功")
        
        # 测试3.2：验证必需字段
        required_fields = ["enabled", "module_path", "required_functions"]
        for field in required_fields:
            assert field in module_config, f"❌ 应包含{field}字段"
            print(f"✅ {field}: {module_config[field]}")
        
        # 测试3.3：验证必需函数
        required_functions = module_config.get("required_functions", [])
        assert len(required_functions) > 0, "❌ 应至少有一个必需函数"
        print(f"✅ 必需函数列表: {required_functions}")
        
        # 测试3.4：获取不存在的模块
        nonexistent_module = config_manager.get_external_module_config("nonexistent_module")
        assert nonexistent_module == {}, "❌ 不存在的模块应返回空字典"
        print("✅ 不存在的模块返回空字典")
        
        print("\n✅ 测试3通过：外部模块配置方法正常")
        
    except AttributeError as e:
        print(f"\n⚠️  测试3失败：get_external_module_config方法可能不存在")
        print(f"   错误信息: {e}")
        print("   请确保已执行006B任务的ConfigManager增强")
        assert False

def test_config_cache():
    """测试4：配置缓存机制"""
    print("\n" + "="*50)
    print("测试4：配置缓存机制")
    print("="*50)
    
    config_manager = ConfigManager()
    
    # 测试4.1：首次访问
    config1 = config_manager.get_config("app_config")
    assert config1 is not None, "❌ 首次访问应成功"
    print("✅ 首次访问成功")
    
    # 测试4.2：二次访问（应使用缓存）
    config2 = config_manager.get_config("app_config")
    assert config2 is config1, "❌ 二次访问应返回缓存对象"
    print("✅ 缓存机制正常")
    
    # 测试4.3：重新加载配置
    try:
        config_manager.reload_config("app_config")
        config3 = config_manager.get_config("app_config")
        assert config3 is not config1, "❌ 重新加载后应返回新对象"
        print("✅ 重新加载配置正常")
    except AttributeError:
        print("ℹ️  reload_config方法不存在（可选功能）")
    
    print("\n✅ 测试4通过：配置缓存机制正常")

def test_error_handling():
    """测试5：错误处理"""
    print("\n" + "="*50)
    print("测试5：错误处理")
    print("="*50)
    
    config_manager = ConfigManager()
    
    # 测试5.1：访问不存在的配置文件
    nonexistent_config = config_manager.get_config("nonexistent_config", default=None)
    assert nonexistent_config is None, "❌ 不存在的配置应返回None"
    print("✅ 不存在的配置返回None")
    
    # 测试5.2：访问不存在的嵌套路径
    try:
        nonexistent_path = config_manager.get_unified_config("app.nonexistent.path", default="default")
        assert nonexistent_path == "default", "❌ 不存在的路径应返回默认值"
        print("✅ 不存在的路径返回默认值")
    except AttributeError:
        print("ℹ️  get_unified_config方法不存在，跳过测试")
    
    # 测试5.3：访问外部模块的不存在字段
    try:
        nonexistent_field = config_manager.get_unified_config(
            "external_modules.markdown_processor.nonexistent_field",
            default=None
        )
        assert nonexistent_field is None, "❌ 不存在的字段应返回None"
        print("✅ 不存在的字段返回None")
    except AttributeError:
        print("ℹ️  get_unified_config方法不存在，跳过测试")
    
    print("\n✅ 测试5通过：错误处理正常")

def test_ui_config_access():
    """测试6：UI配置访问（额外测试）"""
    print("\n" + "="*50)
    print("测试6：UI配置访问（额外测试）")
    print("="*50)
    
    config_manager = ConfigManager()
    
    try:
        # 测试访问UI配置的嵌套字段
        left_panel_width = config_manager.get_unified_config("ui.layout.left_panel_width")
        print(f"✅ 左侧面板宽度: {left_panel_width}")
        
        primary_color = config_manager.get_unified_config("ui.colors.primary")
        print(f"✅ 主题色: {primary_color}")
        
        print("\n✅ 测试6通过：UI配置访问正常")
        
    except AttributeError:
        print("ℹ️  get_unified_config方法不存在，跳过测试")
        

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("ConfigManager V2.1 功能测试套件")
    print("="*70)
    print("\n此脚本将测试ConfigManager的所有功能")
    print("包括向后兼容性、新增功能和错误处理\n")
    
    test_results = []
    
    try:
        test_results.append(("基本配置访问", test_basic_config_access()))
        test_results.append(("统一配置访问", test_unified_config_access()))
        test_results.append(("外部模块配置", test_external_module_config()))
        test_results.append(("配置缓存机制", test_config_cache()))
        test_results.append(("错误处理", test_error_handling()))
        test_results.append(("UI配置访问", test_ui_config_access()))
        
        # 统计结果
        print("\n" + "="*70)
        print("测试结果摘要")
        print("="*70)
        
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        print(f"\n通过测试: {passed}/{total}")
        
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{status}: {test_name}")
        
        if passed == total:
            print("\n" + "="*70)
            print("🎉 所有测试通过！ConfigManager V2.1功能正常")
            print("="*70)
            return True
        else:
            print("\n" + "="*70)
            print("⚠️  部分测试失败，请检查ConfigManager实现")
            print("="*70)
            return False
        
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

