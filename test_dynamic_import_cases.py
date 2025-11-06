#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态导入与渲染链路案例测试

使用方式：
  python test_dynamic_import_cases.py

注意：此脚本仅打印结果，便于在控制台快速观察，不依赖UI。
"""

import sys
from pathlib import Path
import json

# 确保可以导入本项目模块
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.config_manager import ConfigManager
from core.dynamic_module_importer import DynamicModuleImporter
from core.markdown_renderer import HybridMarkdownRenderer


def print_section(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def case_import_status():
    print_section("CASE 1: 动态导入状态")
    cfg = ConfigManager()
    importer = DynamicModuleImporter(cfg)
    result = importer.import_module('markdown_processor', ['markdown'])
    print("import_result:", json.dumps({
        'success': result.get('success'),
        'module': result.get('module'),
        'path': result.get('path'),
        'used_fallback': result.get('used_fallback'),
        'error_code': result.get('error_code'),
        'message': result.get('message')
    }, ensure_ascii=False))


def case_render_priority():
    print_section("CASE 2: 渲染优先级")
    renderer = HybridMarkdownRenderer()
    content = "# Title\n\n**bold** text."
    result = renderer.render(content)
    print("renderer:", result.get('renderer'))
    print("success:", result.get('success'))


def case_disable_dynamic_import():
    print_section("CASE 3: 关闭动态导入")
    renderer = HybridMarkdownRenderer()
    renderer.default_options['use_dynamic_import'] = False
    result = renderer.render("# Disabled dynamic import")
    print("renderer:", result.get('renderer'))


def case_long_content_limit():
    print_section("CASE 4: 超出长度限制")
    renderer = HybridMarkdownRenderer()
    renderer.default_options['max_content_length'] = 10
    result = renderer.render("This content is definitely longer than 10 chars.")
    print("success:", result.get('success'))
    print("error_type:", result.get('error_type'))


def case_markdown_processor_missing_symbols():
    print_section("CASE 5: 缺少必要函数模拟（仅打印期望）")
    print("若markdown_processor缺失 render_markdown_with_zoom 或 render_markdown_to_html，应返回 MISSING_SYMBOLS 并回退。")


if __name__ == '__main__':
    case_import_status()
    case_render_priority()
    case_disable_dynamic_import()
    case_long_content_limit()
    case_markdown_processor_missing_symbols()
    print("\nDone.")