#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误历史持久化子系统 - 快速测试脚本

用于验证子系统各组件是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试导入"""
    print("=== 测试导入 ===")

    try:
        from error_history.core.manager import ErrorHistoryManager
        from error_history.core.models import ErrorRecord, ErrorSeverity, ErrorCategory
        from error_history.ui.main_window import ErrorHistoryMainWindow
        from error_history.integration.main_integration import ErrorHistoryIntegration

        print("✅ 所有核心组件导入成功")
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        assert False

def test_database_operations():
    """测试数据库操作"""
    print("\n=== 测试数据库操作 ===")

    try:
        from error_history.core.manager import ErrorHistoryManager
        from error_history.core.models import ErrorRecord, ErrorSeverity, ErrorCategory

        # 创建临时数据库进行测试
        test_db_path = ":memory:"  # 使用内存数据库进行测试
        manager = ErrorHistoryManager(db_path=test_db_path)

        # 创建测试错误记录
        error = ErrorRecord(
            error_id="TEST_001",
            error_type="ValueError",
            error_message="测试错误消息",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.VALIDATION,
            module="test_module",
            function="test_function"
        )

        # 测试保存
        success = manager.save_error(error)
        if success:
            print("✅ 错误保存成功")
        else:
            print("❌ 错误保存失败")
            assert False

        # 测试查询
        errors = manager.query_errors(limit=10)
        if len(errors) > 0:
            print(f"✅ 查询成功，返回 {len(errors)} 条记录")
        else:
            print("❌ 查询失败，无返回结果")
            assert False

        # 测试统计
        stats = manager.get_statistics()
        if stats and 'total_errors' in stats:
            print(f"✅ 统计成功，总错误数: {stats['total_errors']}")
        else:
            print("❌ 统计失败")
            assert False

        # 关闭管理器
        manager.shutdown()

        print("✅ 数据库操作测试通过")
        

    except Exception as e:
        print(f"❌ 数据库操作测试失败: {e}")
        assert False

def test_config_loading():
    """测试配置加载"""
    print("\n=== 测试配置加载 ===")

    try:
        from error_history.core.manager import ErrorHistoryManager

        # 创建管理器（应该自动加载配置）
        manager = ErrorHistoryManager()

        # 检查配置是否正确加载
        if hasattr(manager, 'config') and manager.config:
            print("✅ 配置加载成功")
            print(f"   数据库路径: {manager.config.database_path}")
            print(f"   保留天数: {manager.config.retention_days}")
            print(f"   自动清理: {manager.config.auto_cleanup}")
        else:
            print("❌ 配置对象不存在")
            assert False

        manager.shutdown()
        print("✅ 配置加载测试通过")
        

    except Exception as e:
        print(f"❌ 配置加载测试失败: {e}")
        assert False

def test_ui_components():
    """测试UI组件（不实际显示窗口）"""
    print("\n=== 测试UI组件 ===")

    try:
        # 只需要测试导入，不实际创建窗口
        from error_history.ui.main_window import ErrorHistoryMainWindow
        from error_history.ui.query_panel import QueryPanel
        from error_history.ui.stats_panel import StatsPanel
        from error_history.ui.analysis_panel import AnalysisPanel
        from error_history.ui.management_panel import ManagementPanel

        print("✅ UI组件导入成功")

        # 验证类定义完整性
        required_methods = ['__init__', 'refresh_data']
        for cls_name, cls in [
            ("ErrorHistoryMainWindow", ErrorHistoryMainWindow),
            ("QueryPanel", QueryPanel),
            ("StatsPanel", StatsPanel),
            ("AnalysisPanel", AnalysisPanel),
            ("ManagementPanel", ManagementPanel)
        ]:
            for method in required_methods:
                if not hasattr(cls, method):
                    print(f"❌ {cls_name} 缺少必要方法: {method}")
                    assert False

        print("✅ UI组件结构验证通过")
        

    except Exception as e:
        print(f"❌ UI组件测试失败: {e}")
        assert False

def test_integration():
    """测试集成组件"""
    print("\n=== 测试集成组件 ===")

    try:
        from error_history.integration.main_integration import (
            ErrorHistoryIntegration,
            create_error_history_integration,
            integrate_error_history_with_main_app
        )

        print("✅ 集成组件导入成功")

        # 测试创建集成管理器
        integration = create_error_history_integration()
        if integration:
            print("✅ 集成管理器创建成功")
            integration.shutdown()
        else:
            print("❌ 集成管理器创建失败")
            assert False

        print("✅ 集成组件测试通过")
        

    except Exception as e:
        print(f"❌ 集成组件测试失败: {e}")
        assert False

def main():
    """主测试函数"""
    print("错误历史持久化子系统 - 快速测试")
    print("=" * 50)

    # 检查Python版本
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    print()

    # 运行所有测试
    tests = [
        ("导入测试", test_imports),
        ("数据库操作测试", test_database_operations),
        ("配置加载测试", test_config_loading),
        ("UI组件测试", test_ui_components),
        ("集成组件测试", test_integration)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")

    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！子系统运行正常。")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查相关组件。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
