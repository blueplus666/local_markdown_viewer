#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口模块 v1.0.0
实现PyQt5主窗口的二栏布局管理
包含文件树和内容显示区域

作者: LAD Team
创建时间: 2025-01-08
最后更新: 2025-01-08
"""

import sys
import logging
import copy
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QSplitter, QMenuBar, QStatusBar, QAction, QFileDialog,
    QMessageBox, QApplication, QLabel
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtGui import QIcon, QFont

# 导入配置管理器
sys.path.append(str(Path(__file__).parent.parent))
from utils.config_manager import get_config_manager
from ui.file_tree import FileTree
from ui.content_viewer import ContentViewer
from ui.status_events import StatusEventEmitter, StatusChangeEvent
from core.correlation_id_manager import CorrelationIdManager
from core.unified_cache_manager import UnifiedCacheManager
from core.performance_metrics import PerformanceMetrics
from core.enhanced_logger import TemplatedLogger
from core.performance_metrics import PerformanceThresholdMonitor
from core.snapshot_manager import SnapshotManager
from core.snapshot_logger import SnapshotLogger
from core.state_change_listener import StateChangeListener
from core.snapshot_manager import SnapshotManager
from core.application_state_manager import ApplicationStateManager
from core.config_validator import ConfigValidator
from core.error_code_manager import ErrorCodeManager
from core.dynamic_module_importer import DynamicModuleImporter
from core.markdown_renderer import HybridMarkdownRenderer


class MainWindow(QMainWindow):
    """
    主窗口类
    实现二栏布局：左侧文件树，右侧文档内容显示
    支持菜单栏、状态栏和基本的窗口管理功能
    """
    
    # 定义信号
    file_selected = pyqtSignal(str)  # 文件选择信号
    
    def __init__(self):
        """初始化主窗口"""
        # 确保存在 QApplication 实例（测试环境可能未先构造）
        try:
            from PyQt5.QtWidgets import QApplication as _QApp
            if _QApp.instance() is None:
                _QApp([])
        except Exception:
            pass
        super().__init__()
        
        # 设置日志
        self.logger = TemplatedLogger(__name__)
        
        # 架构核心组件将在initialize_architecture_components中按顺序构建
        self.config_manager = get_config_manager()
        self.correlation_manager = CorrelationIdManager()
        self.status_event_emitter = StatusEventEmitter()
        self._importer = None
        self.performance_metrics = None
        self.state_manager = None
        self.snapshot_manager = None
        self.snapshot_logger = None
        self.error_manager = None
        self.dynamic_importer = None
        self.markdown_renderer = None
        self.config_validator = None
        self._status_poll_timer: Optional[QTimer] = None
        self._last_module_status: Optional[Dict[str, Any]] = None
        self._last_render_status: Optional[Dict[str, Any]] = None
        self._status_color_rules: Dict[str, str] = {}
        self._status_messages: Dict[str, Dict[str, Any]] = {}
        
        # 初始化UI组件
        self.file_tree = None  # 文件树组件
        self.content_viewer = None  # 内容显示组件
        self.splitter = None  # 分割器
        self._last_selected_file: Optional[str] = None
        
        # 初始化窗口
        self._init_window()
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_status_bar()

        # 初始化架构组件（严格按架构要求的顺序）
        self.initialize_architecture_components()

        # 初始状态栏刷新
        try:
            self.update_status_bar()
        except Exception as init_err:
            self.logger.warning(f"初始状态栏刷新失败: {init_err}")

        # 设置信号连接与状态轮询
        self._setup_connections()
        self.setup_status_update_triggers()
        
        # 安装默认的状态监听器，确保事件能写入日志
        try:
            default_listener = StateChangeListener(self.logger)
            self.register_status_event_listener(default_listener)
        except Exception as e:
            self.logger.warning(f"注册默认状态监听器失败: {e}")

        self.logger.info("主窗口初始化完成")

    # ------------------------------------------------------------------
    # 供008任务注册/注销状态事件监听器
    # ------------------------------------------------------------------
    def register_status_event_listener(self, listener: Callable[[StatusChangeEvent], None]) -> None:
        """注册状态事件监听器（供008 StateChangeListener 使用）。"""
        if not callable(listener):
            raise TypeError("listener 必须可调用")
        self.status_event_emitter.add_listener(listener)

    def unregister_status_event_listener(self, listener: Callable[[StatusChangeEvent], None]) -> None:
        """注销状态事件监听器。"""
        self.status_event_emitter.remove_listener(listener)
    
    def _init_window(self):
        """初始化窗口基本属性"""
        # 设置窗口标题
        title = self.config_manager.get_config("app.window.title", "本地Markdown文件渲染器")
        self.setWindowTitle(title)
        # 确保标准窗口按钮可见
        try:
            self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        except Exception:
            pass
        
        # 设置窗口大小（与集成版对齐：按可用屏幕的比例设置初始大小）
        width = self.config_manager.get_config("app.window.width", 1200)
        height = self.config_manager.get_config("app.window.height", 800)
        try:
            screen = self._get_available_geometry()
            # 使用80%的可用区域作为初始大小，行为与 main_window_integrated 类一致
            init_w = int(screen.width() * 0.8)
            init_h = int(screen.height() * 0.8)
            width = int(min(max(width, 800), screen.width())) if width else init_w
            height = int(min(max(height, 600), screen.height())) if height else init_h
            self.setMinimumSize(800, 600)
            # 不设置最大尺寸，改为在事件中夹紧，保留纵向自由调整
        except Exception:
            self.setMinimumSize(600, 400)
        self.resize(width, height)
        
        # 设置最小窗口大小
        min_width = self.config_manager.get_config("app.window.min_width", 800)
        min_height = self.config_manager.get_config("app.window.min_height", 600)
        self.setMinimumSize(min_width, min_height)
        
        # 设置窗口图标（如果有的话）
        # self.setWindowIcon(QIcon("path/to/icon.png"))
        
        # 设置窗口居中显示
        self._center_window()
        # 采用系统窗口管理，避免过度约束导致异常
        try:
            ag = self._get_available_geometry()
            fg = self.frameGeometry()
            g = self.geometry()
            dpr = getattr(self.windowHandle(), 'devicePixelRatio', lambda: 1.0)()
            self.logger.info(
                f"GEOM|init|screen.available={ag.x()},{ag.y()},{ag.width()},{ag.height()} "
                f"screen.full={QApplication.desktop().screenGeometry().x()},{QApplication.desktop().screenGeometry().y()},"
                f"{QApplication.desktop().screenGeometry().width()},{QApplication.desktop().screenGeometry().height()} "
                f"win.geom.before={g.x()},{g.y()},{g.width()},{g.height()} win.frame={fg.x()},{fg.y()},{fg.width()},{fg.height()} "
                f"dpr={dpr}"
            )
        except Exception:
            pass
    
    def _center_window(self):
        """将窗口居中显示，并确保不超出可用屏幕区域"""
        ag = self._get_available_geometry()
        # 先夹紧尺寸到可用区域
        new_w = min(self.width(), max(100, ag.width() - 8))
        new_h = min(self.height(), max(100, ag.height() - 8))
        if new_w != self.width() or new_h != self.height():
            self.resize(new_w, new_h)
        # 计算位于可用区域的中心点
        x = ag.left() + (ag.width() - self.width()) // 2
        y = ag.top() + (ag.height() - self.height()) // 2
        # 再次夹紧位置，防止标题栏被顶出屏幕
        x = max(ag.left(), min(x, ag.right() - self.width()))
        y = max(ag.top(), min(y, ag.bottom() - self.height()))
        self.move(x, y)

    def _get_available_geometry(self):
        """获取当前窗口所在屏幕的可用区域（考虑任务栏）。"""
        try:
            wh = self.windowHandle()
            if wh and wh.screen():
                return wh.screen().availableGeometry()
            scr = QGuiApplication.screenAt(self.pos()) or QGuiApplication.primaryScreen()
            if scr:
                return scr.availableGeometry()
        except Exception:
            pass
        return QApplication.desktop().availableGeometry(self)

    # 删除强制夹紧逻辑，完全交由系统窗口管理器处理，避免干扰用户拖拽
    
    def _setup_ui(self):
        """设置用户界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建分割器
        self.splitter = QSplitter(Qt.Horizontal)
        # 非不透明拖拽：仅在释放时重绘，避免拖动时卡顿
        try:
            self.splitter.setOpaqueResize(False)
        except Exception:
            pass
        main_layout.addWidget(self.splitter)
        
        # 创建左侧面板（文件树）
        self._create_left_panel()
        
        # 创建右侧面板（内容显示）
        self._create_right_panel()
        
        # 获取布局配置
        left_width = self.config_manager.get_config("layout.left_panel_width", 300, "ui")
        
        # 设置分割器
        self.splitter.setSizes([left_width, self.width() - left_width])
        
        # 设置分割器样式
        self._setup_splitter_style()
    
    def _create_left_panel(self):
        """创建左侧面板（文件树）"""
        # 创建左侧容器
        left_widget = QWidget()
        left_widget.setMinimumWidth(200)
        left_widget.setMaximumWidth(500)
        
        # 设置左侧面板样式
        left_widget.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-right: 1px solid #e0e0e0;
            }
        """)
        
        # 创建左侧布局
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        self.file_tree = FileTree()
        left_layout.addWidget(self.file_tree)
        
        # 将左侧面板添加到分割器
        self.splitter.addWidget(left_widget)
        
        self.logger.info("左侧面板创建完成")
    
    def _create_right_panel(self):
        """创建右侧面板（内容显示）"""
        # 创建右侧容器
        right_widget = QWidget()
        
        # 设置右侧面板样式
        right_widget.setStyleSheet("""
            QWidget {
                background-color: white;
            }
        """)
        
        # 创建右侧布局
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # 添加内容显示组件
        self.content_viewer = ContentViewer(parent=self)
        right_layout.addWidget(self.content_viewer)
        
        # 将右侧面板添加到分割器
        self.splitter.addWidget(right_widget)
        
        self.logger.info("右侧面板创建完成")
    
    def _setup_splitter_style(self):
        """设置分割器样式"""
        # 获取分割器配置
        splitter_width = self.config_manager.get_config("layout.splitter_handle_width", 4, "ui")
        splitter_color = self.config_manager.get_config("layout.splitter_handle_color", "#cccccc", "ui")
        
        # 设置分割器样式
        style = f"""
        QSplitter::handle {{
            background-color: {splitter_color};
            width: {splitter_width}px;
        }}
        """
        self.splitter.setStyleSheet(style)
    
    def _setup_menu_bar(self):
        """设置菜单栏（支持下拉式菜单，预留扩展）"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        # 打开文件动作
        open_action = QAction("打开文件(&O)", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("打开文件")
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)
        
        # 打开文件夹动作
        open_folder_action = QAction("打开文件夹(&F)", self)
        open_folder_action.setShortcut("Ctrl+Shift+O")
        open_folder_action.setStatusTip("打开文件夹")
        open_folder_action.triggered.connect(self._open_folder)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        # 退出动作
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("退出应用程序")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单（预留）
        edit_menu = menubar.addMenu("编辑(&E)")
        
        # 视图菜单（预留）
        view_menu = menubar.addMenu("视图(&V)")
        
        # 工具菜单（预留）
        tools_menu = menubar.addMenu("工具(&T)")
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        # 关于动作
        about_action = QAction("关于(&A)", self)
        about_action.setStatusTip("关于应用程序")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        self.logger.info("菜单栏设置完成")
    
    def _setup_status_bar(self):
        """设置状态栏"""
        status_bar = self.statusBar()
        
        # 设置状态栏样式
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #f0f0f0;
                border-top: 1px solid #e0e0e0;
            }
        """)
        
        # 指示器：模块状态 / 渲染状态 / 函数状态
        try:
            self._init_status_indicators()
        except Exception as e:
            self.logger.warning(f"初始化状态指示器失败: {e}")
        # 显示初始状态
        status_bar.showMessage("就绪")
        
        self.logger.info("状态栏设置完成")
    
    def initialize_architecture_components(self):
        """按架构标准顺序初始化核心组件。"""
        self.logger.info("初始化架构核心组件")
        try:
            # 基础层
            self.cache_manager = UnifiedCacheManager()
            # 监控层
            self.performance_metrics = PerformanceMetrics(self.config_manager)
            self.logger.performance_metrics = self.performance_metrics
            self.performance_monitor = PerformanceThresholdMonitor(self.performance_metrics, self.logger)
            self.error_manager = ErrorCodeManager(self.config_manager)
            # 快照层
            self.snapshot_manager = SnapshotManager(
                config_manager=self.config_manager,
                cache_manager=self.cache_manager,
                performance_metrics=self.performance_metrics,
                correlation_manager=self.correlation_manager,
            )
            self.snapshot_logger = SnapshotLogger(self.logger)
            if hasattr(self.dynamic_importer, "set_snapshot_manager"):
                try:
                    self.dynamic_importer.set_snapshot_manager(self.snapshot_manager)
                except Exception:
                    pass
            if hasattr(self.dynamic_importer, "set_performance_metrics"):
                try:
                    self.dynamic_importer.set_performance_metrics(self.performance_metrics)
                except Exception:
                    pass
                # 状态层
                self.state_manager = ApplicationStateManager(self.config_manager)
                self.state_manager.set_snapshot_manager(self.snapshot_manager)
                self.state_manager.set_performance_metrics(self.performance_metrics)
                # 验证层
                self.config_validator = ConfigValidator(self.config_manager)

                # 任务007要求的扩展组件
                self.dynamic_importer = DynamicModuleImporter(self.config_manager)
                self._importer = self.dynamic_importer
                self.markdown_renderer = HybridMarkdownRenderer(self.config_manager)

                # 预载配置
                self._load_status_bar_config()
        except Exception as exc:
            self.logger.error(f"架构组件初始化失败: {exc}")
            raise

    def _load_status_bar_config(self):
        """载入状态栏颜色与消息配置。"""
        default_colors = {
            "success": "#2e7d32",
            "warning": "#f9a825",
            "error": "#c62828",
            "critical": "#8B0000",
            "disabled": "#D3D3D3",
            "default": "#F0F0F0"
        }
        ui_colors = self.config_manager.get_config("colors", {}, "ui") or {}
        self._status_color_rules = {
            key: ui_colors.get(key, default)
            for key, default in default_colors.items()
        }

        status_messages = self.config_manager.get_config("ui.status_bar_messages", {}, "app") or {}
        self._status_messages = status_messages
        try:
            self._status_update_interval = int(self.config_manager.get_config(
                "ui.status_bar_update_interval_ms", 5000, "app"
            ) or 5000)
        except Exception:
            self._status_update_interval = 5000
    
    def _setup_connections(self):
        """设置信号连接"""
        # 架构组件若尚未初始化则先初始化（防御式处理）
        if self.state_manager is None:
            self.initialize_architecture_components()

        # 连接分割器大小变化信号
        self.splitter.splitterMoved.connect(self._on_splitter_moved)
        
        # 连接文件选择信号
        self.file_tree.file_selected.connect(self._handle_file_selected)
        
        # 连接内容显示组件信号
        if self.content_viewer:
            self.content_viewer.content_loaded.connect(self._on_content_loaded)
            self.content_viewer.error_occurred.connect(self._on_content_error)
        
        self.logger.info("信号连接设置完成")

    def setup_status_update_triggers(self):
        """设置状态栏轮询与初始刷新。"""
        self.logger.info("设置状态栏更新触发器")
        self.update_status_bar()

        if self._status_poll_timer:
            try:
                self._status_poll_timer.stop()
                self._status_poll_timer.deleteLater()
            except Exception:
                pass

        self._status_poll_timer = QTimer(self)
        self._status_poll_timer.setInterval(getattr(self, "_status_update_interval", 5000))
        self._status_poll_timer.timeout.connect(self.update_status_bar)
        self._status_poll_timer.start()

    def update_status_bar(self):
        """按照架构规范刷新状态栏并发射事件。"""
        correlation_id = self._generate_and_propagate_correlation_id("ui", "status_bar")
        timer_id = None
        try:
            if self.performance_metrics:
                timer_id = self.performance_metrics.start_timer(
                    "status_bar_update",
                    {"correlation_id": correlation_id},
                )

            module_status = self._get_module_status_safe()
            render_status = self._get_render_status_safe()

            if self.performance_metrics:
                self.performance_metrics.record_module_update(
                    module_status.get("module", "markdown_processor"),
                    module_status,
                )

            self._check_and_emit_status_changes(module_status, render_status, correlation_id)

            status_message = self._build_status_message(module_status, render_status)
            status_color = self._get_status_color(module_status)

            self.statusBar().showMessage(status_message)
            self.statusBar().setStyleSheet(
                f"background-color: {status_color}; border-top: 1px solid #e0e0e0;"
            )

            self._render_module_indicator(module_status)
            self._render_function_indicator(module_status)
            self._render_render_indicator(render_status)

        except Exception as exc:
            error_color = self._status_color_rules.get("error", "#FF6B6B")
            self.statusBar().showMessage(f"❌ 状态更新错误: {exc}")
            self.statusBar().setStyleSheet(
                f"background-color: {error_color}; border-top: 1px solid #e0e0e0;"
            )
            self.logger.log("ERROR", "状态栏刷新失败", operation="status_bar_update", component="ui", error=str(exc))
        finally:
            if self.performance_metrics and timer_id:
                duration_seconds = self.performance_metrics.end_timer(timer_id)
                if duration_seconds is not None:
                    duration_ms = duration_seconds * 1000
                    threshold = self.config_manager.get_config(
                        "performance.thresholds.status_bar_update_ms", 100, "app"
                    )
                    try:
                        threshold = float(threshold)
                    except Exception:
                        threshold = 100
                    if duration_ms > threshold:
                        self.logger.log(
                            "WARNING",
                            "状态栏更新耗时超过阈值",
                            operation="status_bar_update",
                            component="ui",
                            duration_ms=duration_ms,
                            threshold_ms=threshold
                        )

            self.correlation_manager.clear_current_correlation_id("ui")

    def _generate_and_propagate_correlation_id(self, component: str, operation: str) -> str:
        correlation_id = CorrelationIdManager.generate_correlation_id(operation, component)
        self.correlation_manager.set_current_correlation_id(component, correlation_id)

        if self.dynamic_importer and hasattr(self.dynamic_importer, "set_correlation_id"):
            try:
                self.dynamic_importer.set_correlation_id(correlation_id)
            except Exception:
                pass

        if self.markdown_renderer and hasattr(self.markdown_renderer, "module_importer"):
            try:
                self.markdown_renderer.module_importer.set_correlation_id(correlation_id)
            except Exception:
                pass

        return correlation_id

    def _get_module_status_safe(self) -> Dict[str, Any]:
        snapshot: Dict[str, Any] = {}
        try:
            if self.dynamic_importer:
                snapshot = self.dynamic_importer.get_last_import_snapshot("markdown_processor") or {}
                if not snapshot:
                    self.dynamic_importer.import_module("markdown_processor", ["markdown"])
                    snapshot = self.dynamic_importer.get_last_import_snapshot("markdown_processor") or {}

            if not snapshot and self.state_manager:
                snapshot = self.state_manager.get_module_status("markdown_processor")
        except Exception as exc:
            self.logger.warning(f"获取模块快照失败: {exc}")
            snapshot = {}

        if not snapshot:
            snapshot = {
                "snapshot_type": "module_import_snapshot",
                "module": "markdown_processor",
                "function_mapping_status": "unknown",
                "required_functions": [],
                "available_functions": [],
                "missing_functions": [],
                "non_callable_functions": [],
                "path": "",
                "used_fallback": False,
                "error_code": "",
                "message": "暂无快照",
                "timestamp": datetime.now().isoformat()
            }
        return snapshot

    def _get_render_status_safe(self) -> Dict[str, Any]:
        try:
            if self.state_manager:
                return self.state_manager.get_render_status()
        except Exception as exc:
            self.logger.warning(f"获取渲染状态失败: {exc}")

        return {
            "snapshot_type": "render_snapshot",
            "renderer_type": "unknown",
            "reason": "unavailable",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }

    def _check_and_emit_status_changes(
        self,
        module_status: Dict[str, Any],
        render_status: Dict[str, Any],
        correlation_id: str
    ) -> None:
        prev_module = self._last_module_status or {}
        prev_render = self._last_render_status or {}

        module_changed = prev_module.get("function_mapping_status") != module_status.get("function_mapping_status")
        render_changed = prev_render.get("renderer_type") != render_status.get("renderer_type")

        if module_changed:
            self.status_event_emitter.emit(StatusChangeEvent(
                event_type="module_status",
                component="ui",
                old_status=prev_module.get("function_mapping_status", "unknown"),
                new_status=module_status.get("function_mapping_status", "unknown"),
                correlation_id=correlation_id,
                metadata={"module": module_status.get("module", "markdown_processor")}
            ))

        if render_changed:
            self.status_event_emitter.emit(StatusChangeEvent(
                event_type="render_status",
                component="ui",
                old_status=prev_render.get("renderer_type", "unknown"),
                new_status=render_status.get("renderer_type", "unknown"),
                correlation_id=correlation_id,
                metadata={"details": render_status.get("details", {})}
            ))

        self._last_module_status = copy.deepcopy(module_status)
        self._last_render_status = copy.deepcopy(render_status)

    def _build_status_message(self, module_status: Dict[str, Any], render_status: Dict[str, Any]) -> str:
        mapping_status = module_status.get("function_mapping_status", "unknown")
        render_type = render_status.get("renderer_type", "unknown")

        message_cfg = self._status_messages.get(mapping_status, {}) if self._status_messages else {}
        base_text = message_cfg.get("text") or {
            "complete": "✅ Markdown处理器已准备就绪",
            "incomplete": "⚠️ Markdown处理器存在缺失或警告",
            "import_failed": "❌ Markdown处理器不可用",
        }.get(mapping_status, "ℹ️ Markdown处理器状态未知")

        details = []
        if mapping_status == "incomplete":
            missing = module_status.get("missing_functions") or []
            if missing:
                details.append(f"缺失函数: {', '.join(missing)}")
        if mapping_status == "import_failed":
            err = module_status.get("message") or module_status.get("error_code")
            if err:
                details.append(str(err))

        render_text = {
            "markdown_processor": "动态渲染",
            "markdown": "备用库",
            "text_fallback": "纯文本",
            "unknown": "未知渲染器"
        }.get(render_type, render_type)
        details.append(f"渲染器: {render_text}")

        if details:
            return f"{base_text} ｜ {'；'.join(details)}"
        return base_text

    def _get_status_color(self, module_status: Dict[str, Any]) -> str:
        module = module_status.get("module")
        mapping_status = module_status.get("function_mapping_status")
        color_map = {
            "complete": "#2e7d32",
            "incomplete": "#f9a825",
            "import_failed": "#8b0000",
        }
        if mapping_status in color_map:
            return color_map[mapping_status]
        return self._status_color_rules.get(mapping_status, self._status_color_rules.get("default", "#f0f0f0"))

    def _render_module_indicator(self, module_status: Dict[str, Any]) -> None:
        module = module_status.get("module", "unknown")
        status = module_status.get("function_mapping_status", "unknown")
        msg_map = {
            "complete": "✅ Markdown处理器已加载",
            "incomplete": "⚠️ Markdown处理器部分可用",
            "import_failed": "❌ Markdown处理器不可用"
        }
        self._lbl_module.setText(f"模块: {module}")
        self._lbl_module.setToolTip(msg_map.get(status, f"状态: {status}"))
        self._apply_status_color(self._lbl_module, status)

    def _render_function_indicator(self, module_status: Dict[str, Any]) -> None:
        status = module_status.get("function_mapping_status", "unknown")
        avail = module_status.get("available_functions", []) or module_status.get("function_names", [])
        missing = module_status.get("missing_functions", [])

        if status == "complete":
            self._lbl_functions.setText("函数: 完整")
            self._lbl_functions.setToolTip(f"可用: {', '.join(avail)}")
            self._apply_status_color(self._lbl_functions, "complete")
        elif status == "incomplete":
            tip = f"缺失: {', '.join(missing)}" if missing else "函数映射不完整"
            self._lbl_functions.setText("函数: 不完整")
            self._lbl_functions.setToolTip(tip)
            self._apply_status_color(self._lbl_functions, "incomplete")
        elif status == "import_failed":
            err = module_status.get("message", "未知错误")
            self._lbl_functions.setText("函数: 不可用")
            self._lbl_functions.setToolTip(err)
            self._apply_status_color(self._lbl_functions, "import_failed")
        else:
            self._lbl_functions.setText("函数: 未知")
            self._lbl_functions.setToolTip(f"状态: {status}")
            self._apply_status_color(self._lbl_functions, "warn")

    def _render_render_indicator(self, render_status: Dict[str, Any]) -> None:
        renderer = render_status.get("renderer_type", "unknown")
        mapping = {
            "markdown_processor": "渲染: markdown_processor | 就绪",
            "markdown": "渲染: markdown_library | 备用",
            "markdown_library": "渲染: markdown_library | 备用",
            "text_fallback": "渲染: text_fallback | 纯文本",
            "unknown": "渲染: 未知"
        }
        self._lbl_render.setText(mapping.get(renderer, f"渲染: {renderer}"))
        if renderer == "markdown_processor":
            self._apply_status_color(self._lbl_render, "ok")
        elif renderer in {"markdown", "markdown_library"}:
            self._apply_status_color(self._lbl_render, "warn")
        elif renderer == "text_fallback":
            self._apply_status_color(self._lbl_render, "warn")
        else:
            self._apply_status_color(self._lbl_render, "warn")

    
    def _open_file(self):
        """打开文件"""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("所有文件 (*.*)")
        
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            self._handle_file_selected(file_path)
    
    def _open_folder(self):
        """打开文件夹"""
        folder_dialog = QFileDialog(self)
        folder_dialog.setFileMode(QFileDialog.Directory)
        folder_dialog.setOption(QFileDialog.ShowDirsOnly, True)
        
        if folder_dialog.exec_():
            folder_path = folder_dialog.selectedFiles()[0]
            self._handle_folder_selected(folder_path)
    
    def _show_about(self):
        """显示关于对话框"""
        app_name = self.config_manager.get_config("app.name", "本地Markdown文件渲染器")
        app_version = self.config_manager.get_config("app.version", "1.0.0")
        app_description = self.config_manager.get_config("app.description", "")
        app_author = self.config_manager.get_config("app.author", "LAD Team")
        
        about_text = f"""
        <h3>{app_name}</h3>
        <p>版本: {app_version}</p>
        <p>{app_description}</p>
        <p>作者: {app_author}</p>
        <p>基于PyQt5开发</p>
        """
        
        QMessageBox.about(self, "关于", about_text)
    
    def _on_splitter_moved(self, pos, index):
        """分割器移动事件处理"""
        # 保存分割器位置到配置
        sizes = self.splitter.sizes()
        if sizes[0] > 0:
            self.config_manager.set_config("layout.left_panel_width", sizes[0], "ui")
    
    def _handle_file_selected(self, file_path: str):
        """处理文件选择事件"""
        self.logger.info(f"文件被选择: {file_path}")
        
        # 更新状态栏
        self.statusBar().showMessage(f"已选择文件: {file_path}")
        
        # 发送文件选择信号
        self.file_selected.emit(file_path)
        
        correlation_id = self._generate_and_propagate_correlation_id("ui", "file_open")

        # 使用内容显示组件显示文件
        if self.content_viewer:
            self.content_viewer.display_file(file_path)
            self._last_selected_file = file_path
        
        # 更新窗口标题
        file_name = Path(file_path).name
        self.setWindowTitle(f"{file_name} - 本地Markdown文件渲染器")

        # 发射状态事件（供008监听）
        try:
            self.status_event_emitter.emit(StatusChangeEvent(
                event_type="file_selected",
                component="ui",
                old_status="idle",
                new_status="file_selected",
                correlation_id=correlation_id,
                metadata={"path": file_path}
            ))
        except Exception:
            pass
    
    def _handle_folder_selected(self, folder_path: str):
        """处理文件夹选择事件"""
        self.logger.info(f"文件夹被选择: {folder_path}")
        
        # 更新状态栏
        self.statusBar().showMessage(f"已选择文件夹: {folder_path}")
        
        # 设置文件树的根目录
        if self.file_tree:
            self.file_tree.set_root_path(folder_path)
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        self.logger.info("应用程序即将关闭")
        try:
            # 清理ContentViewer资源
            if self.content_viewer:
                try:
                    self.content_viewer.closeEvent(event)
                except Exception as e:
                    self.logger.warning(f"ContentViewer清理失败: {e}")
            
            # 非阻塞地保存窗口状态，避免卡在关闭流程
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, self._save_window_state)
        except Exception:
            pass
        try:
            # 断开主要信号，减少后续事件风暴
            if self.splitter:
                try:
                    self.splitter.splitterMoved.disconnect()
                except Exception:
                    pass
            if self.content_viewer:
                try:
                    self.content_viewer.content_loaded.disconnect()
                except Exception:
                    pass
                try:
                    self.content_viewer.error_occurred.disconnect()
                except Exception:
                    pass
        except Exception:
            pass
        # 接受关闭事件并请求应用退出（不阻塞）
        event.accept()
        try:
            QApplication.instance().quit()
        except Exception:
            pass
        # 清理导入器（安全关闭线程与持久化）
        try:
            if getattr(self, '_importer', None):
                self._importer.shutdown()
                self._importer = None
        except Exception:
            pass
    
    def _save_window_state(self):
        """保存窗口状态"""
        # 保存窗口大小
        size = self.size()
        self.config_manager.set_config("app.window.width", size.width(), "app")
        self.config_manager.set_config("app.window.height", size.height(), "app")
        
        # 保存分割器位置
        sizes = self.splitter.sizes()
        if sizes[0] > 0:
            self.config_manager.set_config("layout.left_panel_width", sizes[0], "ui")
        
        self.logger.info("窗口状态已保存")
    
    def _on_content_loaded(self, file_path: str, success: bool):
        """内容加载完成处理"""
        if success:
            self.statusBar().showMessage(f"文件已加载: {Path(file_path).name}")
            self.logger.info(f"内容加载成功: {file_path}")
            # 内容加载后刷新导入状态到状态栏
            try:
                # 先以扩展名即时设置渲染块（不等待任何异步状态）
                ext = Path(file_path).suffix.lower()
                if ext in {'.md', '.markdown', '.mdx'}:
                    self._lbl_render.setText("渲染: 就绪")
                    self._apply_status_color(self._lbl_render, 'ok')
                else:
                    self._lbl_render.setText("渲染: 备用/纯文本")
                    self._apply_status_color(self._lbl_render, 'warn')

                # 再刷新模块/函数快照（不覆盖上面渲染块的颜色）
                self.update_status_bar_with_import_info()
            except Exception as e:
                self.logger.warning(f"更新状态栏失败: {e}")
        else:
            self.statusBar().showMessage(f"文件加载失败: {Path(file_path).name}")
            self.logger.warning(f"内容加载失败: {file_path}")
    
    def _on_content_error(self, error_type: str, error_message: str):
        """内容显示错误处理"""
        self.statusBar().showMessage(f"错误: {error_type}")
        self.logger.error(f"内容显示错误 - {error_type}: {error_message}")

    # === 状态栏指示器实现 ===
    def _init_status_indicators(self):
        """创建状态栏三种指示器: 模块/渲染/函数映射"""
        sb = self.statusBar()
        # 标签创建
        self._lbl_module = QLabel("模块: 未知")
        self._lbl_render = QLabel("渲染: 未知")
        self._lbl_functions = QLabel("函数: 未知")
        # 基础样式
        for w in (self._lbl_module, self._lbl_render, self._lbl_functions):
            w.setStyleSheet("padding: 0 8px;")
        # 添加到状态栏（持久小部件）
        sb.addPermanentWidget(self._lbl_module)
        sb.addPermanentWidget(self._lbl_render)
        sb.addPermanentWidget(self._lbl_functions)
        # 初次刷新模块导入状态
        try:
            self.update_status_bar_with_import_info()
        except Exception:
            pass

    def _apply_status_color(self, widget: QLabel, status: str):
        """根据状态设置颜色编码: green/yellow/red/gray"""
        color = {
            'complete': '#2e7d32',       # 绿
            'incomplete': '#f9a825',     # 黄
            'import_failed': '#c62828',  # 红
            'ok': '#2e7d32',
            'warn': '#f9a825',
            'error': '#c62828',
        }.get(status, '#666666')         # 灰
        widget.setStyleSheet(f"padding: 0 8px; color: {color};")

    def update_status_bar_with_import_info(self):
        """根据导入信息更新状态栏（模块/函数状态），渲染状态占位待接入Renderer信号"""
        try:
            importer = getattr(self, '_importer', None)
            snapshot = importer.get_last_import_snapshot('markdown_processor') if importer else {}
            # 若无快照，尝试轻量触发一次导入以生成快照
            if (not snapshot) and importer:
                try:
                    importer.import_module('markdown_processor')
                    snapshot = importer.get_last_import_snapshot('markdown_processor') or {}
                except Exception:
                    pass
        except Exception as e:
            self._lbl_module.setText("模块: 未知")
            self._lbl_module.setToolTip(str(e))
            self._apply_status_color(self._lbl_module, 'error')
            return

        if not snapshot:
            self._lbl_module.setText("模块: 未知")
            self._lbl_module.setToolTip("暂无导入记录")
            self._apply_status_color(self._lbl_module, 'warn')
            return

        status = snapshot.get('function_mapping_status', 'unknown')
        module = snapshot.get('module', 'unknown')
        msg_map = {
            'complete': "✅ Markdown处理器已加载（动态导入）",
            'incomplete': "⚠️ Markdown处理器部分可用（函数缺失）",
            'import_failed': "❌ Markdown处理器不可用（导入失败）"
        }
        # 模块指示器
        self._lbl_module.setText(f"模块: {module}")
        self._lbl_module.setToolTip(msg_map.get(status, f"状态: {status}"))
        self._apply_status_color(self._lbl_module, status)

        # 发射状态变更事件
        try:
            from core.correlation_id_manager import CorrelationIdManager
            cid = CorrelationIdManager().get_current_correlation_id("ui") or snapshot.get("correlation_id", "")
            self.status_event_emitter.emit(StatusChangeEvent(
                event_type="module_status",
                component="ui",
                old_status="unknown",
                new_status=status,
                correlation_id=cid,
                metadata={"module": module}
            ))
        except Exception:
            pass

        # 函数映射指示器
        avail = snapshot.get('available_functions', []) or snapshot.get('function_names', [])
        req = snapshot.get('required_functions', [])
        missing = snapshot.get('missing_functions', []) or [f for f in (req or []) if f not in (avail or [])]
        if status == 'complete':
            self._lbl_functions.setText("函数: 完整")
            self._lbl_functions.setToolTip(f"可用: {', '.join(avail)}")
            self._apply_status_color(self._lbl_functions, 'complete')
        elif status == 'incomplete':
            tip = []
            if missing:
                tip.append(f"缺失: {', '.join(missing)}")
            self._lbl_functions.setText("函数: 不完整")
            self._lbl_functions.setToolTip("; ".join(tip) if tip else "函数映射不完整")
            self._apply_status_color(self._lbl_functions, 'incomplete')
        elif status == 'import_failed':
            err = snapshot.get('message', '未知错误')
            self._lbl_functions.setText("函数: 不可用")
            self._lbl_functions.setToolTip(err)
            self._apply_status_color(self._lbl_functions, 'import_failed')
        else:
            self._lbl_functions.setText("函数: 未知")
            self._lbl_functions.setToolTip(f"状态: {status}")
            self._apply_status_color(self._lbl_functions, 'warn')

        # 渲染指示器：读取渲染器快照以显示来源标识
        try:
            rs = (self.markdown_renderer.get_last_render_snapshot() if self.markdown_renderer
                  else {})
            rtype = rs.get('renderer_type')
            if rtype == 'markdown_processor':
                self._lbl_render.setText("渲染: markdown_processor | 就绪")
                # 保持之前由扩展名决定的颜色为绿
            elif rtype == 'markdown_library':
                self._lbl_render.setText("渲染: markdown_library | 备用")
            elif rtype == 'text_fallback':
                self._lbl_render.setText("渲染: text_fallback | 纯文本")
            # 颜色策略：不覆盖_on_content_loaded中已设定的颜色
        except Exception:
            pass


if __name__ == "__main__":
    # 测试主窗口
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("本地Markdown文件渲染器")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("LAD Team")
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())
