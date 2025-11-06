#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误处理测试脚本 v1.0.0
测试增强错误处理器的功能

作者: LAD Team
创建时间: 2025-08-16
最后更新: 2025-08-16
"""

import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.enhanced_error_handler import (
    EnhancedErrorHandler, 
    ErrorRecoveryStrategy, 
    ErrorSeverity, 
    ErrorCategory
)
from core.markdown_renderer import HybridMarkdownRenderer


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('error_handling_test.log', encoding='utf-8')
        ]
    )


def test_enhanced_error_handler():
    """测试增强错误处理器"""
    print("\n" + "="*50)
    print("测试增强错误处理器")
    print("="*50)
    
    # 创建错误处理器
    error_handler = EnhancedErrorHandler(
        error_log_dir=project_root / "logs" / "errors_test",
        max_error_history=100
    )
    
    # 测试基本错误处理
    print("1. 测试基本错误处理...")
    
    try:
        # 模拟文件不存在错误
        raise FileNotFoundError("测试文件不存在")
    except Exception as e:
        error_info = error_handler.handle_error(e)
        print(f"   错误ID: {error_info.error_id}")
        print(f"   错误类型: {error_info.error_type}")
        print(f"   错误分类: {error_info.category.value}")
        print(f"   严重程度: {error_info.severity.value}")
        print(f"   恢复策略: {error_info.recovery_strategy.value}")
    
    # 测试配置错误
    print("2. 测试配置错误处理...")
    
    try:
        # 模拟键错误
        config = {}
        value = config['missing_key']
    except Exception as e:
        error_info = error_handler.handle_error(
            e, 
            context={'operation': 'config_access', 'key': 'missing_key'},
            recovery_strategy=ErrorRecoveryStrategy.FALLBACK
        )
        print(f"   错误ID: {error_info.error_id}")
        print(f"   错误分类: {error_info.category.value}")
        print(f"   恢复策略: {error_info.recovery_strategy.value}")
    
    # 测试渲染错误
    print("3. 测试渲染错误处理...")
    
    try:
        # 模拟语法错误
        raise SyntaxError("测试语法错误")
    except Exception as e:
        error_info = error_handler.handle_error(
            e, 
            context={'operation': 'markdown_render', 'content': 'test'},
            recovery_strategy=ErrorRecoveryStrategy.FALLBACK
        )
        print(f"   错误ID: {error_info.error_id}")
        print(f"   错误分类: {error_info.category.value}")
        print(f"   严重程度: {error_info.severity.value}")
    
    # 测试统计信息
    print("4. 测试统计信息...")
    stats = error_handler.get_error_stats()
    print(f"   总错误数: {stats.total_errors}")
    print(f"   已解决错误数: {stats.resolved_errors}")
    print(f"   未解决错误数: {stats.unresolved_errors}")
    print(f"   错误分类分布: {stats.errors_by_category}")
    print(f"   严重程度分布: {stats.errors_by_severity}")
    
    # 测试错误历史
    print("5. 测试错误历史...")
    history = error_handler.get_error_history(10)
    print(f"   最近错误数: {len(history)}")
    
    # 测试错误报告
    print("6. 测试错误报告...")
    success = error_handler.save_error_report("test_error_report.json")
    print(f"   报告保存: {'成功' if success else '失败'}")
    
    # 清理
    error_handler.shutdown()
    print("✅ 增强错误处理器测试完成")


def test_markdown_renderer_error_handling():
    """测试Markdown渲染器错误处理"""
    print("\n" + "="*50)
    print("测试Markdown渲染器错误处理")
    print("="*50)
    
    # 创建渲染器
    renderer = HybridMarkdownRenderer()
    
    # 测试渲染错误处理
    print("1. 测试渲染错误处理...")
    
    # 测试无效内容渲染
    try:
        result = renderer.render(None)
        print(f"   渲染结果: {result['success']}")
    except Exception as e:
        print(f"   捕获异常: {e}")
    
    # 测试文件渲染错误处理
    print("2. 测试文件渲染错误处理...")
    
    # 测试不存在的文件
    result = renderer.render_file("nonexistent_file.md")
    print(f"   文件渲染结果: {result['success']}")
    print(f"   错误信息: {result.get('error', '无错误')}")
    
    # 测试错误统计
    print("3. 测试错误统计...")
    cache_info = renderer.get_cache_info()
    error_stats = cache_info.get('error_stats', {})
    print(f"   错误统计: {error_stats.get('total_errors', 0)} 个错误")
    
    # 测试错误历史
    print("4. 测试错误历史...")
    error_history = renderer.get_error_history(5)
    print(f"   错误历史: {len(error_history)} 条记录")
    
    print("✅ Markdown渲染器错误处理测试完成")


def test_error_recovery_strategies():
    """测试错误恢复策略"""
    print("\n" + "="*50)
    print("测试错误恢复策略")
    print("="*50)
    
    # 创建错误处理器
    error_handler = EnhancedErrorHandler(
        error_log_dir=project_root / "logs" / "recovery_test",
        max_error_history=50
    )
    
    # 测试重试策略
    print("1. 测试重试策略...")
    
    try:
        raise ConnectionError("测试连接错误")
    except Exception as e:
        error_info = error_handler.handle_error(
            e, 
            recovery_strategy=ErrorRecoveryStrategy.RETRY
        )
        print(f"   错误ID: {error_info.error_id}")
        print(f"   恢复策略: {error_info.recovery_strategy.value}")
        print(f"   重试次数: {error_info.retry_count}")
    
    # 测试降级策略
    print("2. 测试降级策略...")
    
    try:
        raise ValueError("测试配置值错误")
    except Exception as e:
        error_info = error_handler.handle_error(
            e, 
            recovery_strategy=ErrorRecoveryStrategy.FALLBACK
        )
        print(f"   错误ID: {error_info.error_id}")
        print(f"   恢复策略: {error_info.recovery_strategy.value}")
    
    # 测试忽略策略
    print("3. 测试忽略策略...")
    
    try:
        raise RuntimeWarning("测试运行时警告")
    except Exception as e:
        error_info = error_handler.handle_error(
            e, 
            recovery_strategy=ErrorRecoveryStrategy.IGNORE
        )
        print(f"   错误ID: {error_info.error_id}")
        print(f"   恢复策略: {error_info.recovery_strategy.value}")
    
    # 测试中止策略
    print("4. 测试中止策略...")
    
    try:
        raise SystemError("测试系统错误")
    except Exception as e:
        error_info = error_handler.handle_error(
            e, 
            recovery_strategy=ErrorRecoveryStrategy.ABORT
        )
        print(f"   错误ID: {error_info.error_id}")
        print(f"   恢复策略: {error_info.recovery_strategy.value}")
    
    # 清理
    error_handler.shutdown()
    print("✅ 错误恢复策略测试完成")


def main():
    """主测试函数"""
    print("🚀 开始错误处理测试")
    print("="*60)
    
    # 设置日志
    setup_logging()
    
    try:
        # 运行各项测试
        test_enhanced_error_handler()
        test_markdown_renderer_error_handling()
        test_error_recovery_strategies()
        
        print("\n" + "="*60)
        print("🎉 所有错误处理测试完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        logging.error(f"测试错误: {e}", exc_info=True)
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 