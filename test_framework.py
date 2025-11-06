#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础框架测试脚本 v1.0.0
测试第一阶段基础框架的各个组件是否正常工作

作者: LAD Team
创建时间: 2025-01-08
最后更新: 2025-01-08
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_config_manager():
    """测试配置管理器"""
    print("=== 测试配置管理器 ===")
    try:
        from utils.config_manager import get_config_manager
        
        # 获取配置管理器实例
        config_mgr = get_config_manager()
        print("✓ 配置管理器创建成功")
        
        # 测试配置读取
        app_name = config_mgr.get_config("app.name")
        print(f"✓ 应用名称: {app_name}")
        
        # 测试文件类型信息
        file_info = config_mgr.get_file_type_info(".md")
        print(f"✓ Markdown文件类型信息: {file_info}")
        
        print("✓ 配置管理器测试通过\n")
        
    except Exception as e:
        print(f"✗ 配置管理器测试失败: {e}\n")
        assert False

def test_project_structure():
    """测试项目结构"""
    print("=== 测试项目结构 ===")
    
    required_dirs = [
        "config",
        "ui",
        "core", 
        "utils",
        "resources",
        "tests"
    ]
    
    required_files = [
        "main.py",
        "README.md",
        "requirements.txt",
        "__init__.py",
        "config/app_config.json",
        "config/ui_config.json", 
        "config/file_types.json",
        "ui/main_window.py",
        "ui/__init__.py",
        "utils/config_manager.py",
        "utils/__init__.py",
        "core/__init__.py"
    ]
    
    all_passed = True
    
    # 检查目录
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"✓ 目录存在: {dir_name}")
        else:
            print(f"✗ 目录缺失: {dir_name}")
            all_passed = False
    
    # 检查文件
    for file_name in required_files:
        file_path = project_root / file_name
        if file_path.exists():
            print(f"✓ 文件存在: {file_name}")
        else:
            print(f"✗ 文件缺失: {file_name}")
            all_passed = False
    
    if all_passed:
        print("✓ 项目结构测试通过\n")
    else:
        print("✗ 项目结构测试失败\n")
    
    assert all_passed

def main():
    """主测试函数"""
    print("本地Markdown文件渲染器 - 基础框架测试")
    print("=" * 50)
    
    # 测试项目结构
    structure_ok = test_project_structure()
    
    # 测试配置管理器
    config_ok = test_config_manager()
    
    # 总结
    print("=" * 50)
    print("测试总结:")
    print(f"项目结构: {'✓ 通过' if structure_ok else '✗ 失败'}")
    print(f"配置管理器: {'✓ 通过' if config_ok else '✗ 失败'}")
    
    if all([structure_ok, config_ok]):
        print("\n🎉 所有测试通过！基础框架实现完整。")
        return 0
    else:
        print("\n❌ 部分测试失败，需要修复问题。")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 