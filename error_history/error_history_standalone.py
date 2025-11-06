#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误历史持久化子系统 - 独立启动脚本

此脚本用于独立运行错误历史持久化子系统，
主要用于测试和独立使用场景。
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    try:
        # 导入子系统
        from error_history.integration.main_integration import run_error_history_standalone

        logger.info("启动错误历史持久化子系统...")

        # 解析命令行参数
        mode = "query"  # 默认模式
        if len(sys.argv) > 1:
            mode = sys.argv[1]

        # 验证模式参数
        valid_modes = ["query", "statistics", "analysis", "management"]
        if mode not in valid_modes:
            print(f"无效的模式参数: {mode}")
            print(f"有效模式: {', '.join(valid_modes)}")
            return 1

        logger.info(f"启动模式: {mode}")

        # 运行子系统
        return run_error_history_standalone(mode)

    except ImportError as e:
        logger.error(f"导入错误: {e}")
        print("错误: 无法导入错误历史子系统")
        print("请确保已正确安装依赖:")
        print("  pip install PyQt5")
        return 1

    except KeyboardInterrupt:
        logger.info("用户中断")
        return 0

    except Exception as e:
        logger.error(f"启动失败: {e}")
        return 1


def check_dependencies():
    """检查依赖"""
    missing_deps = []

    try:
        import PyQt5
    except ImportError:
        missing_deps.append("PyQt5")

    try:
        import sqlite3
    except ImportError:
        missing_deps.append("sqlite3 (Python标准库)")

    if missing_deps:
        print("缺少必要的依赖:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\n请安装缺失的依赖:")
        print("  pip install PyQt5")
        return False

    return True


if __name__ == "__main__":
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)

    # 运行主函数
    sys.exit(main())
