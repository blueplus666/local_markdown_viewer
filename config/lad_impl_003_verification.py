#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LAD-IMPL-003 补救验证脚本
验证PYTHONPATH环境变量设置和模块导入功能
"""

import sys
import os
import subprocess

def main():
    print("=== LAD-IMPL-003 补救验证 ===")
    
    # 1. 检查环境变量
    print("\n1. 检查PYTHONPATH环境变量:")
    pythonpath = os.environ.get('PYTHONPATH', '')
    if pythonpath:
        print(f"   PYTHONPATH = {pythonpath}")
        if 'LAD_md_ed2' in pythonpath:
            print("   ✓ LAD路径已包含在PYTHONPATH中")
        else:
            print("   ❌ LAD路径未包含在PYTHONPATH中")
    else:
        print("   ❌ PYTHONPATH环境变量为空")
    
    # 2. 检查sys.path
    print("\n2. 检查Python sys.path:")
    lad_paths = [p for p in sys.path if 'lad' in p.lower()]
    if lad_paths:
        print("   找到LAD相关路径:")
        for path in lad_paths:
            print(f"     {path}")
    else:
        print("   ❌ sys.path中未找到LAD相关路径")
    
    # 3. 测试模块导入
    print("\n3. 测试lad_markdown_viewer模块导入:")
    try:
        import lad_markdown_viewer
        print("   ✓ lad_markdown_viewer模块导入成功")
        print(f"   模块文件路径: {lad_markdown_viewer.__file__}")
        
        # 4. 测试关键函数
        print("\n4. 测试关键函数存在性:")
        try:
            from lad_markdown_viewer.markdown_processor import render_markdown_to_html, render_markdown_with_zoom
            print("   ✓ render_markdown_to_html 函数导入成功")
            print("   ✓ render_markdown_with_zoom 函数导入成功")
            
            # 5. 简单功能测试
            print("\n5. 简单功能测试:")
            test_md = "# 测试标题\n\n这是一个测试。"
            try:
                result1 = render_markdown_to_html(test_md)
                print("   ✓ render_markdown_to_html 函数调用成功")
                print(f"   输出长度: {len(result1)} 字符")
                
                result2 = render_markdown_with_zoom(test_md)
                print("   ✓ render_markdown_with_zoom 函数调用成功")
                print(f"   输出长度: {len(result2)} 字符")
                
            except Exception as e:
                print(f"   ❌ 函数调用失败: {e}")
                
        except ImportError as e:
            print(f"   ❌ 关键函数导入失败: {e}")
            
    except ImportError as e:
        print(f"   ❌ 模块导入失败: {e}")
        
        # 尝试手动添加路径
        print("\n   尝试手动添加路径后重新导入:")
        lad_path = r'D:\lad\LAD_md_ed2'
        if lad_path not in sys.path:
            sys.path.insert(0, lad_path)
            print(f"   已添加路径: {lad_path}")
            
        try:
            import lad_markdown_viewer
            print("   ✓ 手动添加路径后导入成功")
            print(f"   模块文件路径: {lad_markdown_viewer.__file__}")
        except Exception as e2:
            print(f"   ❌ 手动添加路径后仍然失败: {e2}")
    
    # 6. 环境变量持久性测试
    print("\n6. 环境变量持久性测试:")
    try:
        # 使用PowerShell检查用户级环境变量
        result = subprocess.run([
            'powershell', '-Command', 
            '[Environment]::GetEnvironmentVariable("PYTHONPATH", "User")'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            user_pythonpath = result.stdout.strip()
            if user_pythonpath:
                print(f"   用户级PYTHONPATH: {user_pythonpath}")
                if 'LAD_md_ed2' in user_pythonpath:
                    print("   ✓ 用户级环境变量设置正确")
                else:
                    print("   ❌ 用户级环境变量不包含LAD路径")
            else:
                print("   ❌ 用户级PYTHONPATH为空")
        else:
            print(f"   ❌ 无法检查用户级环境变量: {result.stderr}")
            
    except Exception as e:
        print(f"   ❌ 环境变量检查失败: {e}")
    
    print("\n=== 验证完成 ===")

if __name__ == "__main__":
    main()
