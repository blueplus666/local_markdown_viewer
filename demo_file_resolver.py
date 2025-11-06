#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件解析器演示脚本
展示FileResolver的各种功能

作者: LAD Team
创建时间: 2025-08-02
"""

import sys
from pathlib import Path
import json

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from core.file_resolver import FileResolver


def demo_file_resolver():
    """演示文件解析器功能"""
    print("=" * 60)
    print("文件解析器功能演示")
    print("=" * 60)
    
    # 初始化文件解析器
    resolver = FileResolver()
    
    # 1. 显示支持的文件类型
    print("\n1. 支持的文件类型:")
    print("-" * 30)
    extensions = resolver.get_supported_extensions()
    for type_name, ext_list in extensions.items():
        print(f"{type_name}: {', '.join(ext_list)}")
    
    # 2. 显示支持的编码
    print("\n2. 支持的编码:")
    print("-" * 30)
    encodings = resolver.get_supported_encodings()
    print(f"编码列表: {', '.join(encodings)}")
    
    # 3. 解析当前目录下的文件
    print("\n3. 解析当前目录下的文件:")
    print("-" * 30)
    
    current_dir = Path(__file__).parent
    test_files = [
        "README.md",
        "main.py",
        "requirements.txt",
        "config/file_types.json"
    ]
    
    for file_name in test_files:
        file_path = current_dir / file_name
        if file_path.exists():
            print(f"\n解析文件: {file_name}")
            result = resolver.resolve_file_path(file_path)
            
            if result['success']:
                print(f"  ✅ 成功")
                print(f"  文件类型: {result['file_type']['final_type']}")
                print(f"  文件大小: {result['file_info']['size_formatted']}")
                print(f"  编码: {result['encoding']['encoding']} (置信度: {result['encoding']['confidence']:.2f})")
                print(f"  类型置信度: {result['file_type']['confidence']:.2f}")
            else:
                print(f"  ❌ 失败: {result['error']}")
        else:
            print(f"\n文件不存在: {file_name}")
    
    # 4. 测试文件支持检查
    print("\n4. 文件支持检查:")
    print("-" * 30)
    
    test_extensions = ['.md', '.txt', '.py', '.json', '.xyz', '.exe']
    for ext in test_extensions:
        test_file = f"test{ext}"
        is_supported = resolver.is_supported_file(test_file)
        status = "✅ 支持" if is_supported else "❌ 不支持"
        print(f"{ext}: {status}")
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    demo_file_resolver() 