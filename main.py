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
import atexit
import logging
import json
import threading
from pathlib import Path
from typing import Any, Dict, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, QCoreApplication

# 导入主窗口
from ui.main_window import MainWindow
from core.dynamic_log_config import DynamicLogConfigManager, RuntimeLogLevelController
from core.log_rotation import (
    DiskSpaceMonitor,
    IntelligentLogRotationManager,
    LogRotationScheduler,
)
from utils.config_manager import get_config_manager


_logging_initialized = False
_logging_config_lock = threading.RLock()
_dynamic_log_config_manager: Optional[DynamicLogConfigManager] = None
_runtime_log_level_controller: Optional[RuntimeLogLevelController] = None
_log_rotation_manager: Optional[IntelligentLogRotationManager] = None
_log_rotation_scheduler: Optional[LogRotationScheduler] = None
_disk_space_monitor: Optional[DiskSpaceMonitor] = None
_console_handler: Optional[logging.Handler] = None
_file_handler: Optional[logging.Handler] = None
_log_file_path: Optional[Path] = None
_current_logging_config: Dict[str, Any] = {}


def _resolve_log_file_path(path_value: str) -> Path:
    candidate = Path(path_value)
    if not candidate.is_absolute():
        candidate = project_root / candidate
    candidate.parent.mkdir(parents=True, exist_ok=True)
    return candidate.resolve()


def _reopen_file_handler() -> None:
    global _file_handler
    with _logging_config_lock:
        if _log_file_path is None or _current_logging_config is None:
            return
        root_logger = logging.getLogger()
        if _file_handler is not None:
            root_logger.removeHandler(_file_handler)
            try:
                _file_handler.close()
            except Exception:
                pass
        formatter = logging.Formatter(
            _current_logging_config.get(
                "format",
                "%(asctime)s %(levelname)s [%(name)s] %(message)s",
            )
        )
        file_level = (
            _current_logging_config.get("handlers", {})
            .get("file", {})
            .get("level", _current_logging_config.get("level", "INFO"))
        )
        _file_handler = logging.FileHandler(_log_file_path, encoding="utf-8")
        _file_handler.setLevel(getattr(logging, file_level.upper(), logging.INFO))
        _file_handler.setFormatter(formatter)
        root_logger.addHandler(_file_handler)


def _stop_rotation_components() -> None:
    global _log_rotation_scheduler, _log_rotation_manager, _disk_space_monitor
    if _log_rotation_scheduler is not None:
        _log_rotation_scheduler.stop()
        _log_rotation_scheduler = None
    _log_rotation_manager = None
    if _disk_space_monitor is not None:
        _disk_space_monitor.stop()
        _disk_space_monitor = None


def _ensure_rotation_components(logging_cfg: Dict[str, Any], log_file_path: Path) -> None:
    global _log_rotation_manager, _log_rotation_scheduler, _disk_space_monitor
    rotation_cfg = logging_cfg.get("rotation", {})
    scheduler_interval = rotation_cfg.get("scheduler_interval_seconds", 3600.0)
    if _log_rotation_manager is None:
        _log_rotation_manager = IntelligentLogRotationManager(str(log_file_path), logging_cfg)
        _log_rotation_manager.register_rotation_callback(_reopen_file_handler)
    else:
        _log_rotation_manager.update_config(str(log_file_path), logging_cfg)
    if _log_rotation_scheduler is None:
        _log_rotation_scheduler = LogRotationScheduler(_log_rotation_manager, scheduler_interval)
        _log_rotation_scheduler.start()
    else:
        _log_rotation_scheduler.set_check_interval(scheduler_interval)
    disk_cfg = logging_cfg.get("disk_monitor", {})
    if disk_cfg:
        monitor_path = disk_cfg.get("path", log_file_path.parent)
        if isinstance(monitor_path, str):
            monitor_path = _resolve_log_file_path(monitor_path)
        min_free_gb = disk_cfg.get("min_free_gb", 1.0)
        check_interval = disk_cfg.get("check_interval_seconds", 600.0)
        if _disk_space_monitor is None:
            _disk_space_monitor = DiskSpaceMonitor(str(monitor_path), min_free_gb, check_interval)
            _disk_space_monitor.start()
        else:
            _disk_space_monitor.path = Path(monitor_path)
            if _disk_space_monitor.path.is_file():
                _disk_space_monitor.path = _disk_space_monitor.path.parent
            _disk_space_monitor.path.mkdir(parents=True, exist_ok=True)
            _disk_space_monitor.update_settings(min_free_gb, check_interval)
    else:
        if _disk_space_monitor is not None:
            _disk_space_monitor.stop()
            _disk_space_monitor = None


def _apply_logging_config(logging_cfg: Dict[str, Any]) -> None:
    global _console_handler, _file_handler, _log_file_path, _current_logging_config
    with _logging_config_lock:
        _current_logging_config = logging_cfg or {}
        root_logger = logging.getLogger()
        level_name = (_current_logging_config.get("level") or "INFO").upper()
        root_logger.setLevel(getattr(logging, level_name, logging.INFO))
        formatter = logging.Formatter(
            _current_logging_config.get(
                "format",
                "%(asctime)s %(levelname)s [%(name)s] %(message)s",
            )
        )
        handlers_cfg = _current_logging_config.get("handlers", {})

        # Console handler
        console_cfg = handlers_cfg.get("console", {})
        console_enabled = console_cfg.get("enabled", True)
        if console_enabled:
            if _console_handler is None:
                _console_handler = logging.StreamHandler(sys.stdout)
                root_logger.addHandler(_console_handler)
            console_level = (
                console_cfg.get("level") or _current_logging_config.get("level", "INFO")
            ).upper()
            _console_handler.setLevel(getattr(logging, console_level, logging.INFO))
            _console_handler.setFormatter(formatter)
        else:
            if _console_handler is not None:
                root_logger.removeHandler(_console_handler)
                try:
                    _console_handler.close()
                except Exception:
                    pass
                _console_handler = None

        # File handler
        file_cfg = handlers_cfg.get("file", {})
        file_enabled = file_cfg.get("enabled", True)
        if file_enabled:
            file_path_value = file_cfg.get("path", "logs/lad_markdown_viewer.log")
            new_log_file_path = _resolve_log_file_path(file_path_value)
            file_level = (
                file_cfg.get("level") or _current_logging_config.get("level", "INFO")
            ).upper()
            if _file_handler is None or _log_file_path != new_log_file_path:
                if _file_handler is not None:
                    root_logger.removeHandler(_file_handler)
                    try:
                        _file_handler.close()
                    except Exception:
                        pass
                _file_handler = logging.FileHandler(new_log_file_path, encoding="utf-8")
                root_logger.addHandler(_file_handler)
                _log_file_path = new_log_file_path
                if _log_rotation_manager is not None:
                    _log_rotation_manager.update_config(str(new_log_file_path), _current_logging_config)
            _file_handler.setLevel(getattr(logging, file_level, logging.INFO))
            _file_handler.setFormatter(formatter)
            _ensure_rotation_components(_current_logging_config, new_log_file_path)
        else:
            if _file_handler is not None:
                root_logger.removeHandler(_file_handler)
                try:
                    _file_handler.close()
                except Exception:
                    pass
                _file_handler = None
                _log_file_path = None
            _stop_rotation_components()

        if _runtime_log_level_controller is not None:
            _runtime_log_level_controller.register_logger(root_logger)


def _on_dynamic_logging_config(old_config: Dict[str, Any], new_config: Dict[str, Any]) -> None:
    logging_cfg = (new_config or {}).get("logging", {})
    if logging_cfg:
        _apply_logging_config(logging_cfg)


def _teardown_logging_components() -> None:
    global _dynamic_log_config_manager
    with _logging_config_lock:
        if _dynamic_log_config_manager is not None:
            _dynamic_log_config_manager.stop()
            _dynamic_log_config_manager = None
        _stop_rotation_components()


atexit.register(_teardown_logging_components)


def setup_logging():
    """设置日志系统并启用动态配置、轮转及磁盘监控"""
    global _logging_initialized, _dynamic_log_config_manager, _runtime_log_level_controller
    if _logging_initialized:
        return

    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    cfg_manager = get_config_manager()
    initial_logging_cfg = cfg_manager.get_unified_config("features.logging", {}) or {}

    _runtime_log_level_controller = RuntimeLogLevelController()
    _apply_logging_config(initial_logging_cfg)

    logging_config_path = project_root / "config" / "features" / "logging.json"
    _dynamic_log_config_manager = DynamicLogConfigManager(str(logging_config_path))
    _dynamic_log_config_manager.register_reload_callback(_on_dynamic_logging_config)
    _dynamic_log_config_manager.start()

    _logging_initialized = True


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

        # ===== 集成错误历史持久化子系统 =====
        try:
            logger.info("正在集成错误历史持久化子系统...")

            # 获取配置管理器
            config_manager = get_config_manager()

            # 导入并创建错误历史集成管理器
            from error_history.integration.main_integration import integrate_error_history_with_main_app

            # 集成到主应用程序
            error_history_integration = integrate_error_history_with_main_app(window)

            if error_history_integration:
                logger.info("错误历史持久化子系统集成成功")

                # 将集成管理器保存到主窗口，便于后续访问
                window.error_history_integration = error_history_integration
            else:
                logger.warning("错误历史持久化子系统集成失败，将以降级模式运行")

        except Exception as e:
            logger.error(f"错误历史子系统集成异常: {e}")
            logger.info("将继续运行主应用程序（错误历史功能将不可用）")

        # 在主窗口显示后，按推荐方案刷新一次导入快照到状态栏
        try:
            if hasattr(window, 'update_status_bar_with_import_info'):
                window.update_status_bar_with_import_info()
                logger.info("状态栏已刷新导入快照")
        except Exception as e:
            logger.warning(f"状态栏导入快照刷新失败: {e}")

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