#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地Markdown文件渲染器 - 主程序入口 v1.0.0
基于PyQt5的桌面应用程序，用于本地Markdown文件渲染和文档管理

作者: LAD Team
创建时间: 2025-01-08
最后更新: 2025-08-13
"""

import sys
import os
import logging
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, QCoreApplication

# 导入主窗口
from ui.main_window import MainWindow


def setup_logging():
    """设置日志系统"""
    # 创建logs目录
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(logs_dir / "app.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def check_import_status():
    """轻量探测渲染能力（不触发完整子系统初始化）。"""
    try:
        # 仅做符号可用性/可导入性检测，杜绝初始化/关闭的副作用
        status_info = {
            'markdown_processor_available': False,
            'markdown_available': False,
            'dynamic_import_enabled': True,
        }
        try:
            import importlib
            # 探测可选高阶处理器
            mp = importlib.util.find_spec('lad_markdown_viewer')
            status_info['markdown_processor_available'] = mp is not None
        except Exception:
            pass
        try:
            # 探测标准 markdown 库
            import importlib
            md = importlib.util.find_spec('markdown')
            status_info['markdown_available'] = md is not None
        except Exception:
            pass
        logger = logging.getLogger(__name__)
        logger.info(f"动态导入状态轻量探测完成: {status_info}")
        return status_info
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"轻量探测失败，按保守值返回: {e}")
        return {
            'markdown_processor_available': False,
            'markdown_available': False,
            'dynamic_import_enabled': True,
            'error': str(e)
        }


def main():
    """主函数"""
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("启动本地Markdown文件渲染器")
    
    try:
        # 在创建 QApplication 之前设置高 DPI 属性
        try:
            QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
            QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        except Exception:
            pass

        # 创建QApplication实例
        app = QApplication(sys.argv)
        
        # 设置应用程序信息
        app.setApplicationName("本地Markdown文件渲染器")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("LAD Team")
        app.setOrganizationDomain("lad.com")
        
        # 应用程序属性已在 QApplication 创建前设置
        
        # 统一初始化关键运行时配置（确保与调试入口一致的导航与历史策略）
        try:
            from utils.config_manager import get_config_manager
            cfgm = get_config_manager()
            # 历史栈上限（避免长时间导航导致内存增长），默认 200，可由 config/ui_config.json 覆盖
            if cfgm.get_config("content_viewer.history_max", None, "ui") is None:
                cfgm.set_config("content_viewer.history_max", 200, "ui")
            # 允许为调试器或其他工具读取统一上限（可选，不影响主界面）
            if cfgm.get_config("link_debugger.history_max", None, "ui") is None:
                cfgm.set_config("link_debugger.history_max", 200, "ui")
            logger.info(
                f"运行时配置: history_max(cv)={cfgm.get_config('content_viewer.history_max', 200, 'ui')}, "
                f"history_max(ld)={cfgm.get_config('link_debugger.history_max', 200, 'ui')}"
            )
        except Exception:
            # 配置非致命，失败时继续
            pass

        # 检查导入状态
        import_status = check_import_status()
        logger.info(f"导入状态: {import_status}")
        
        # 在创建主窗口前按配置运行集成与监控（不阻塞启动）
        try:
            cfg_path = project_root / "config" / "lad_integration.json"
            cfg = {"enabled": False, "monitoring": {"enabled": False}}
            if cfg_path.exists():
                try:
                    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
                except Exception:
                    cfg = {"enabled": False, "monitoring": {"enabled": False}}

            from integration.system_integration_coordinator import SystemIntegrationCoordinator
            from monitoring.monitoring_system_deployer import MonitoringSystemDeployer

            import asyncio
            loop = asyncio.get_event_loop()

            async def _run_optional():
                if cfg.get("enabled", False):
                    try:
                        coordinator = SystemIntegrationCoordinator()
                        await coordinator.integrate_all_modules()
                    except Exception:
                        pass
                if cfg.get("enabled", False) and cfg.get("monitoring", {}).get("enabled", False):
                    try:
                        deployer = MonitoringSystemDeployer()
                        await deployer.deploy_monitoring_system()
                    except Exception:
                        pass

            if loop.is_running():
                loop.create_task(_run_optional())
            else:
                try:
                    loop.run_until_complete(_run_optional())
                except Exception:
                    pass
        except Exception:
            pass

        # 创建并显示主窗口
        window = MainWindow()
        # 直接使用集成版相同的展示逻辑，避免几何差异
        window.show()
        # 记录几何信息
        try:
            from PyQt5.QtGui import QGuiApplication
            ag = (QGuiApplication.screenAt(window.pos()) or QGuiApplication.primaryScreen()).availableGeometry()
            fg = window.frameGeometry(); g = window.geometry()
            dpr = getattr(window.windowHandle(), 'devicePixelRatio', lambda: 1.0)()
            logger.info(
                f"GEOM|main.show|screen.available={ag.x()},{ag.y()},{ag.width()},{ag.height()} "
                f"win.geom.after={g.x()},{g.y()},{g.width()},{g.height()} win.frame={fg.x()},{fg.y()},{fg.width()},{fg.height()} "
                f"dpr={dpr}"
            )
        except Exception:
            pass
        
        # 在主窗口显示后更新状态栏显示导入状态
        if hasattr(window, 'statusBar'):
            status_message = ""
            if import_status.get('markdown_processor_available'):
                status_message = "✅ Markdown处理器已加载 (动态导入)"
            elif import_status.get('markdown_available'):
                status_message = "⚠️ Markdown处理器已加载 (备用库)"
            else:
                status_message = "❌ Markdown处理器不可用，将使用纯文本"
            
            # 更新状态栏
            window.statusBar().showMessage(status_message)
            logger.info(f"状态栏已更新: {status_message}")
        
        logger.info("主窗口已显示")
        
        # 运行应用程序
        exit_code = app.exec_()
        
        logger.info(f"应用程序退出，退出码: {exit_code}")
        return exit_code
        
    except Exception as e:
        logger.error(f"应用程序启动失败: {e}")
        return 1


if __name__ == "__main__":
    # 运行主函数
    sys.exit(main()) 