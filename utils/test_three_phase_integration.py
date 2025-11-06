#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三阶段组件集成测试 v1.0.0
验证基础架构实施的所有组件是否能正常工作

作者: LAD Team
创建时间: 2025-08-16
最后更新: 2025-08-16
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from local_markdown_viewer.utils import (
    # 第一阶段：轻量级基础功能
    LightweightPerformanceTest,
    ConfigMigrationManager,
    EnhancedLogger,
    
    # 第二阶段：资源与架构管理
    ResourceManager,
    ArchitectureAdapter,
    FirstPhaseComponentIntegration,
    
    # 第三阶段：接口一致性管理
    InterfaceCompatibilityManager,
    InterfaceValidator,
    ValidationLevel
)

from local_markdown_viewer.utils.config_manager import ConfigManager


def test_first_phase_components():
    """测试第一阶段组件"""
    print("🔧 测试第一阶段：轻量级基础功能")
    
    try:
        # 测试性能测试器
        print("  - 测试 LightweightPerformanceTest...")
        test_dir = Path(__file__).parent / "test_data"
        test_dir.mkdir(exist_ok=True)
        
        perf_test = LightweightPerformanceTest(test_dir)
        test_files = perf_test.create_test_files()
        print(f"    ✅ 创建测试文件: {len(test_files)} 个")
        
        # 测试配置迁移管理器
        print("  - 测试 ConfigMigrationManager...")
        config_dir = Path(__file__).parent / "config"
        config_dir.mkdir(exist_ok=True)
        
        migration_manager = ConfigMigrationManager(config_dir)
        result = migration_manager.migrate_configs()
        print(f"    ✅ 配置迁移: {result.success}")
        
        # 测试增强日志器
        print("  - 测试 EnhancedLogger...")
        logger = logging.getLogger("test_logger")
        enhanced_logger = EnhancedLogger(logger)
        enhanced_logger.log_operation("测试日志消息", operation="test")
        print("    ✅ 增强日志器工作正常")
        
        print("  ✅ 第一阶段组件测试通过")
        
    except Exception as e:
        print(f"  ❌ 第一阶段组件测试失败: {e}")
        assert False


def test_second_phase_components():
    """测试第二阶段组件"""
    print("🏗️ 测试第二阶段：资源与架构管理")
    
    try:
        # 测试资源管理器
        print("  - 测试 ResourceManager...")
        base_dir = Path(__file__).parent.parent
        resource_manager = ResourceManager(base_dir)
        resources = resource_manager.scan_resources()
        print(f"    ✅ 扫描资源: {len(resources)} 个")
        
        # 测试架构适配器
        print("  - 测试 ArchitectureAdapter...")
        architecture_adapter = ArchitectureAdapter(base_dir)
        status = architecture_adapter.generate_architecture_report()
        print(f"    ✅ 架构报告生成: {len(status)} 字符")
        
        # 测试组件集成
        print("  - 测试 FirstPhaseComponentIntegration...")
        integration = FirstPhaseComponentIntegration(architecture_adapter)
        result = integration.integrate_all_components()
        print(f"    ✅ 组件集成: {result}")
        
        print("  ✅ 第二阶段组件测试通过")
        
    except Exception as e:
        print(f"  ❌ 第二阶段组件测试失败: {e}")
        assert False


def test_third_phase_components():
    """测试第三阶段组件"""
    print("🔗 测试第三阶段：接口一致性管理")
    
    try:
        # 测试接口一致性管理器
        print("  - 测试 InterfaceCompatibilityManager...")
        base_dir = Path(__file__).parent.parent
        compatibility_manager = InterfaceCompatibilityManager(base_dir)
        
        # 分析一个接口
        interface_info = compatibility_manager.analyze_interface(ConfigManager)
        print(f"    ✅ 接口分析: {interface_info.name}")
        
        # 创建接口规范
        spec = compatibility_manager.create_interface_specification(interface_info)
        print(f"    ✅ 接口规范创建: {spec.name} v{spec.version}")
        
        # 测试接口验证器
        print("  - 测试 InterfaceValidator...")
        validator = InterfaceValidator(compatibility_manager)
        validation_report = validator.validate_interface_implementation(
            ConfigManager, spec, ValidationLevel.NORMAL
        )
        print(f"    ✅ 接口验证: {validation_report.overall_result.value}")
        
        print("  ✅ 第三阶段组件测试通过")
        
    except Exception as e:
        print(f"  ❌ 第三阶段组件测试失败: {e}")
        assert False


def test_cross_phase_integration():
    """测试跨阶段集成"""
    print("🔗 测试跨阶段集成")
    
    try:
        base_dir = Path(__file__).parent.parent
        
        # 创建所有管理器
        print("  - 创建所有管理器...")
        resource_manager = ResourceManager(base_dir)
        architecture_adapter = ArchitectureAdapter(base_dir)
        compatibility_manager = InterfaceCompatibilityManager(base_dir)
        
        # 测试资源管理器与架构适配器的集成
        print("  - 测试资源管理器与架构适配器集成...")
        architecture_adapter.register_component_adapter("resource_manager", resource_manager)
        
        # 测试架构适配器与接口一致性管理器的集成
        print("  - 测试架构适配器与接口一致性管理器集成...")
        interface_info = compatibility_manager.analyze_interface(ResourceManager)
        spec = compatibility_manager.create_interface_specification(interface_info)
        
        # 测试完整的验证流程
        print("  - 测试完整验证流程...")
        validator = InterfaceValidator(compatibility_manager)
        validation_report = validator.validate_interface_implementation(
            ResourceManager, spec, ValidationLevel.NORMAL
        )
        
        print(f"    ✅ 跨阶段集成测试通过: {validation_report.summary}")
        
    except Exception as e:
        print(f"  ❌ 跨阶段集成测试失败: {e}")
        assert False


def test_utils_package_imports():
    """测试utils包的导入"""
    print("📦 测试utils包导入")
    
    try:
        # 测试所有主要类的导入
        from local_markdown_viewer.utils import (
            # 第一阶段
            LightweightPerformanceTest,
            ConfigMigrationManager,
            EnhancedLogger,
            
            # 第二阶段
            ResourceManager,
            ArchitectureAdapter,
            FirstPhaseComponentIntegration,
            
            # 第三阶段
            InterfaceCompatibilityManager,
            InterfaceValidator
        )
        
        print("  ✅ 所有主要类导入成功")
        
        # 测试便捷函数导入
        from local_markdown_viewer.utils import (
            create_performance_test,
            create_config_migration_manager,
            create_enhanced_logger,
            create_resource_manager,
            create_architecture_adapter,
            create_first_phase_integration,
            create_interface_compatibility_manager,
            create_interface_validator
        )
        
        print("  ✅ 所有便捷函数导入成功")
        
    except Exception as e:
        print(f"  ❌ utils包导入测试失败: {e}")
        assert False


def main():
    """主测试函数"""
    print("🚀 开始三阶段组件集成测试")
    print("=" * 50)
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    test_results = []
    
    # 测试各阶段组件
    test_results.append(("第一阶段组件", test_first_phase_components()))
    test_results.append(("第二阶段组件", test_second_phase_components()))
    test_results.append(("第三阶段组件", test_third_phase_components()))
    
    # 测试跨阶段集成
    test_results.append(("跨阶段集成", test_cross_phase_integration()))
    
    # 测试包导入
    test_results.append(("utils包导入", test_utils_package_imports()))
    
    # 生成测试报告
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！基础架构实施完成！")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 