# error_history/ui/main_window.py
"""
错误历史持久化子系统 - 主UI窗口
"""

import sys
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QComboBox, QLineEdit,
    QDateEdit, QGroupBox, QCheckBox, QTextEdit, QMessageBox,
    QProgressBar, QStatusBar, QMenuBar, QMenu, QAction,
    QFrame, QScrollArea, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QDate, QSettings, QByteArray, QSize
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon, QGuiApplication

from ..core.manager import ErrorHistoryManager
from ..core.models import ErrorSeverity, ErrorCategory
from .query_panel import QueryPanel
from .stats_panel import StatsPanel
from .analysis_panel import AnalysisPanel
from .management_panel import ManagementPanel

logger = logging.getLogger(__name__)


class ErrorHistoryMainWindow(QMainWindow):
    """错误历史主窗口"""

    def __init__(self, mode: str = "query", parent=None):
        super().__init__(parent)

        self.mode = mode
        self.manager = None
        self.current_errors = []
        self.auto_refresh_timer = QTimer()
        self._splitter_initialized = False

        # 初始化UI
        self._init_manager()
        self._init_ui()
        self._setup_connections()
        self._load_initial_data()

        # 设置窗口属性
        self.setWindowTitle("错误历史持久化子系统 v1.0.0")
        self._pending_initial_sizing = True

        self.setMinimumSize(600, 360)
        self.setWindowIcon(QIcon())  # 可以设置图标

        # 首次显示后再进行尺寸与居中，避免预显示几何调整


        # 自动刷新
        self.auto_refresh_timer.timeout.connect(self._auto_refresh)
        if self.manager and self.manager.config.auto_refresh_seconds > 0:
            self.auto_refresh_timer.start(self.manager.config.auto_refresh_seconds * 1000)

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

    def _clamp_to_work_area(self):
        """将窗口限制在当前屏幕可用工作区内，避免被任务栏覆盖。"""
        try:
            ag = self._get_available_geometry()
            fg = self.frameGeometry()  # 包含窗口边框的几何
            # 目标位置：夹在可用区域内
            target_x = max(ag.left(), min(fg.left(), ag.right() - fg.width()))
            target_y = max(ag.top(), min(fg.top(), ag.bottom() - fg.height()))
            if target_x != fg.left() or target_y != fg.top():
                self.move(target_x, target_y)
        except Exception:
            pass

    def _apply_screen_constraints(self):
        """依据屏幕可用区域约束窗口尺寸与细节区高度"""
        try:
            ag = self._get_available_geometry()

            # 动态最小尺寸：永不超过基线最小值，避免抬高 MINMAXINFO 的 mintrack
            base_min_w = max(1, self.minimumWidth())
            base_min_h = max(1, self.minimumHeight())
            dyn_min_w = min(base_min_w, max(320, ag.width() - 120))
            dyn_min_h = min(base_min_h, max(240, ag.height() - 120))
            self.setMinimumSize(dyn_min_w, dyn_min_h)

            # 不在此处调整窗口尺寸，仅对内部子控件进行限制，防止在用户调整大小时触发几何冲突

            # 限制底部详情区高度占比，避免上下挤压（按窗口高度的 ~28% 上限）
            try:
                self._cap_details_panel()
            except Exception:
                pass
        except Exception:
            pass

    def _cap_details_panel(self):
        try:
            if not hasattr(self, 'splitter'):
                return
            # 仅在垂直布局时进行高度上限约束；水平布局不做宽度上限，保留用户自由调整
            if self.splitter.orientation() == Qt.Vertical:
                h = max(self.height(), 1)
                bottom_cap = max(120, int(h * 0.22))

                # 面板整体上限（允许在上限内拖动扩大）
                if hasattr(self, 'details_widget'):
                    self.details_widget.setMaximumHeight(bottom_cap)

                # 调整分割器尺寸，收敛底部高度
                sizes = self.splitter.sizes()
                if len(sizes) >= 2:
                    total = max(sum(sizes), h)
                    bottom = sizes[-1]
                    if bottom > bottom_cap:
                        self.splitter.setSizes([max(total - bottom_cap, 100), bottom_cap])
        except Exception:
            pass

    def _init_manager(self):
        """初始化管理器"""
        try:
            # 这里可以从主系统获取配置管理器
            # 暂时使用默认配置
            self.manager = ErrorHistoryManager()

            if self.statusBar():
                self.statusBar().showMessage("错误历史管理器初始化成功", 3000)

        except Exception as e:
            logger.error(f"初始化错误历史管理器失败: {e}")
            # 不要在这里显示对话框，因为这可能导致递归问题
            # 让调用者处理这个异常
            raise RuntimeError(f"无法初始化错误历史管理器: {str(e)}")

    def _init_ui(self):
        """初始化用户界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QVBoxLayout(central_widget)

        # 创建工具栏
        self._create_toolbar()

        # 创建状态栏
        self._create_status_bar()

        # 创建主内容区域
        self._create_main_content(main_layout)

    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = self.addToolBar("主工具栏")
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        # 刷新按钮
        refresh_action = QAction("刷新(&R)", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._refresh_data)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        # 导出按钮
        export_action = QAction("导出(&E)", self)
        export_action.triggered.connect(self._export_data)
        toolbar.addAction(export_action)

        # 管理按钮
        manage_action = QAction("管理(&M)", self)
        manage_action.triggered.connect(self._show_management)
        toolbar.addAction(manage_action)

    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()

        # 数据库状态标签
        self.db_status_label = QLabel("数据库: 未连接")
        self.status_bar.addWidget(self.db_status_label)

        self.status_bar.addPermanentWidget(QLabel(" | "))

        # 统计信息标签
        self.stats_label = QLabel("总错误: 0 | 未解决: 0")
        self.status_bar.addPermanentWidget(self.stats_label)

        # 更新数据库状态
        self._update_db_status()

    def _create_main_content(self, parent_layout):
        """创建主内容区域"""
        parent_layout.setContentsMargins(12, 12, 12, 12)
        parent_layout.setSpacing(12)
        # 创建分割器（改为左右布局）
        self.splitter = QSplitter(Qt.Horizontal)

        # 创建标签页控件
        self.tab_widget = QTabWidget()

        # 创建各个面板
        self.query_panel = QueryPanel(self.manager)
        self.stats_panel = StatsPanel(self.manager)
        self.analysis_panel = AnalysisPanel(self.manager)
        self.management_panel = ManagementPanel(self.manager)

        # 添加到标签页
        self.tab_widget.addTab(self.query_panel, "查询")
        self.tab_widget.addTab(self.stats_panel, "统计")
        self.tab_widget.addTab(self.analysis_panel, "分析")
        self.tab_widget.addTab(self.management_panel, "管理")

        # 根据初始模式选择标签页
        mode_index = {
            "query": 0,
            "statistics": 1,
            "analysis": 2,
            "management": 3
        }.get(self.mode, 0)
        self.tab_widget.setCurrentIndex(mode_index)

        self.splitter.addWidget(self.tab_widget)

        # 创建详情面板
        self.details_widget = self._create_details_panel()
        self.splitter.addWidget(self.details_widget)

        # 设置分割器比例（左:右 = 3:1）
        try:
            # 允许右侧面板可折叠，降低最小跟踪宽度压力
            self.splitter.setCollapsible(1, True)
        except Exception:
            pass
        self.splitter.setSizes([600, 200])
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)

        try:
            settings = QSettings("LAD", "ErrorHistoryUI")
            # 仅从新键恢复，避免旧的垂直状态干扰
            state = settings.value("splitterState_h")
            if state:
                self.splitter.restoreState(state if isinstance(state, QByteArray) else QByteArray(state))
            # 强制水平
            self.splitter.setOrientation(Qt.Horizontal)
            self._cap_details_panel()
        except Exception:
            pass

        parent_layout.addWidget(self.splitter)

    def _create_details_panel(self) -> QWidget:
        """创建详情面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        widget.setMinimumWidth(160)

        # 标题
        title_label = QLabel("错误详情")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)

        # 详情文本框
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMinimumHeight(120)
        layout.addWidget(self.details_text)

        # 操作按钮
        buttons_layout = QHBoxLayout()

        self.mark_resolved_btn = QPushButton("标记已解决")
        self.mark_resolved_btn.clicked.connect(self._mark_error_resolved)
        self.mark_resolved_btn.setEnabled(False)
        buttons_layout.addWidget(self.mark_resolved_btn)

        self.delete_error_btn = QPushButton("删除错误")
        self.delete_error_btn.clicked.connect(self._delete_error)
        self.delete_error_btn.setEnabled(False)
        buttons_layout.addWidget(self.delete_error_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        return widget

    def _setup_connections(self):
        """设置信号连接"""
        # 查询面板信号
        if hasattr(self.query_panel, 'error_selected'):
            self.query_panel.error_selected.connect(self._on_error_selected)
        if hasattr(self.query_panel, 'data_changed'):
            self.query_panel.data_changed.connect(self._update_status)

        # 标签页切换
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

    def _load_initial_data(self):
        """加载初始数据"""
        try:
            # 更新状态信息
            self._update_status()
            self._update_db_status()

        except Exception as e:
            QMessageBox.warning(self, "数据加载失败",
                              f"加载初始数据失败:\n{str(e)}")

    def _on_error_selected(self, error_data: Dict[str, Any]):
        """错误选择处理"""
        try:
            if not error_data:
                self.details_text.clear()
                self.mark_resolved_btn.setEnabled(False)
                self.delete_error_btn.setEnabled(False)
                return

            # 格式化详情信息
            details = self._format_error_details(error_data)
            self.details_text.setPlainText(details)

            # 启用操作按钮
            is_resolved = error_data.get('resolved', False)
            self.mark_resolved_btn.setEnabled(not is_resolved)
            self.mark_resolved_btn.setText("标记未解决" if is_resolved else "标记已解决")
            self.delete_error_btn.setEnabled(True)

            # 存储当前错误ID
            self.current_error_id = error_data.get('error_id')

        except Exception as e:
            QMessageBox.warning(self, "详情显示失败",
                              f"显示错误详情失败:\n{str(e)}")

    def _format_error_details(self, error_data: Dict[str, Any]) -> str:
        """格式化错误详情"""
        lines = []

        lines.append(f"错误ID: {error_data.get('error_id', 'N/A')}")
        lines.append(f"错误类型: {error_data.get('error_type', 'N/A')}")
        lines.append(f"错误消息: {error_data.get('error_message', 'N/A')}")
        lines.append(f"严重程度: {error_data.get('severity', 'N/A')}")
        lines.append(f"分类: {error_data.get('category', 'N/A')}")
        lines.append(f"模块: {error_data.get('module', 'N/A')}")
        lines.append(f"函数: {error_data.get('function', 'N/A')}")
        lines.append(f"行号: {error_data.get('line_number', 'N/A')}")
        lines.append(f"创建时间: {error_data.get('created_at', 'N/A')}")
        lines.append(f"已解决: {'是' if error_data.get('resolved') else '否'}")

        if error_data.get('resolved_at'):
            lines.append(f"解决时间: {error_data.get('resolved_at')}")
        if error_data.get('resolution_method'):
            lines.append(f"解决方法: {error_data.get('resolution_method')}")
        if error_data.get('resolution_time'):
            lines.append(".2f")
        if error_data.get('retry_count'):
            lines.append(f"重试次数: {error_data.get('retry_count')}")

        # 堆栈跟踪
        if error_data.get('stack_trace'):
            lines.append("")
            lines.append("堆栈跟踪:")
            lines.append(error_data['stack_trace'])

        # 上下文信息
        if error_data.get('context'):
            lines.append("")
            lines.append("上下文信息:")
            context_str = str(error_data['context'])
            lines.append(context_str[:500] + "..." if len(context_str) > 500 else context_str)

        return "\n".join(lines)

    def _mark_error_resolved(self):
        """标记错误已解决/未解决"""
        if not hasattr(self, 'current_error_id'):
            return

        try:
            # 获取当前错误信息
            error = self.manager.get_error(self.current_error_id)
            if not error:
                QMessageBox.warning(self, "操作失败", "找不到指定的错误记录")
                return

            # 切换解决状态
            new_resolved_status = not error.resolved

            # 更新错误记录
            error.resolved = new_resolved_status
            if new_resolved_status:
                error.resolved_at = datetime.now()
                error.resolution_method = "手动标记"
            else:
                error.resolved_at = None
                error.resolution_method = None

            if self.manager.update_error(error):
                # 刷新数据
                self._refresh_data()

                status_text = "已解决" if new_resolved_status else "未解决"
                QMessageBox.information(self, "操作成功",
                                      f"错误已标记为{status_text}")
            else:
                QMessageBox.warning(self, "操作失败", "更新错误状态失败")

        except Exception as e:
            QMessageBox.critical(self, "操作失败",
                               f"标记错误状态失败:\n{str(e)}")

    def _delete_error(self):
        """删除错误"""
        if not hasattr(self, 'current_error_id'):
            return

        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这条错误记录吗？此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            if self.manager.delete_error(self.current_error_id):
                # 刷新数据
                self._refresh_data()

                # 清空详情
                self.details_text.clear()
                self.mark_resolved_btn.setEnabled(False)
                self.delete_error_btn.setEnabled(False)

                QMessageBox.information(self, "操作成功", "错误记录已删除")
            else:
                QMessageBox.warning(self, "操作失败", "删除错误记录失败")

        except Exception as e:
            QMessageBox.critical(self, "操作失败",
                               f"删除错误记录失败:\n{str(e)}")

    def refresh_data(self):
        """刷新数据（公共方法）"""
        self._refresh_data()

    def _refresh_data(self):
        """刷新数据"""
        try:
            # 刷新当前标签页
            current_index = self.tab_widget.currentIndex()
            current_widget = self.tab_widget.widget(current_index)

            if hasattr(current_widget, 'refresh_data'):
                current_widget.refresh_data()

            # 更新状态
            self._update_status()

        except Exception as e:
            QMessageBox.warning(self, "刷新失败",
                              f"刷新数据失败:\n{str(e)}")

    def _export_data(self):
        """导出数据"""
        try:
            from PyQt5.QtWidgets import QFileDialog

            # 获取导出格式
            formats = ["JSON (*.json)", "CSV (*.csv)", "Excel (*.xlsx)"]
            format_map = {
                "JSON (*.json)": "json",
                "CSV (*.csv)": "csv",
                "Excel (*.xlsx)": "xlsx"
            }

            filename, selected_filter = QFileDialog.getSaveFileName(
                self, "导出错误历史数据",
                f"error_history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                ";;".join(formats)
            )

            if filename:
                format_type = format_map.get(selected_filter, "json")

                # 获取当前查询条件
                current_widget = self.tab_widget.currentWidget()
                filters = {}
                if hasattr(current_widget, 'get_current_filters'):
                    filters = current_widget.get_current_filters()

                # 执行导出
                if self.manager.export_data(filename, format_type, filters):
                    QMessageBox.information(self, "导出成功",
                                          f"数据已导出到:\n{filename}")
                else:
                    QMessageBox.warning(self, "导出失败", "数据导出失败")

        except Exception as e:
            QMessageBox.critical(self, "导出失败",
                               f"导出数据失败:\n{str(e)}")

    def _show_management(self):
        """显示管理面板"""
        self.tab_widget.setCurrentIndex(3)  # 切换到管理标签页

    def _on_tab_changed(self, index: int):
        """标签页切换处理"""
        # 可以在这里添加标签页切换时的特殊处理
        pass

    def _update_status(self):
        """更新状态栏信息"""
        try:
            if not self.manager:
                return

            # 获取统计信息
            stats = self.manager.get_statistics()

            if stats:
                total = stats.get('total_errors', 0)
                unresolved = stats.get('unresolved_errors', 0)
                resolved = stats.get('resolved_errors', 0)

                status_text = f"总错误: {total} | 已解决: {resolved} | 未解决: {unresolved}"
                self.stats_label.setText(status_text)

        except Exception as e:
            self.stats_label.setText("统计信息获取失败")

    def _update_db_status(self):
        """更新数据库状态"""
        try:
            if not self.manager:
                self.db_status_label.setText("数据库: 未连接")
                return

            db_info = self.manager.get_database_info()
            if db_info:
                db_path = db_info.get('database_path', '未知')
                db_size = db_info.get('database_size', 0)
                size_mb = db_size / (1024 * 1024)

                status_text = f"数据库: {db_path} ({size_mb:.2f} MB)"
                self.db_status_label.setText(status_text)
            else:
                self.db_status_label.setText("数据库: 连接异常")

        except Exception as e:
            self.db_status_label.setText("数据库: 状态获取失败")

    def _auto_refresh(self):
        """自动刷新"""
        try:
            # 只在查询和统计标签页自动刷新
            current_index = self.tab_widget.currentIndex()
            if current_index in [0, 1]:  # 查询和统计标签页
                self._refresh_data()
        except Exception as e:
            # 自动刷新失败不显示错误对话框，只记录日志
            print(f"自动刷新失败: {e}")

    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            # 停止自动刷新
            self.auto_refresh_timer.stop()

            try:
                settings = QSettings("LAD", "ErrorHistoryUI")
                if hasattr(self, 'splitter'):
                    # 保存为新键（水平）并兼容旧键
                    state = self.splitter.saveState()
                    settings.setValue("splitterState_h", state)
                    settings.setValue("splitterState", state)
            except Exception:
                pass

            # 关闭管理器
            if self.manager:
                self.manager.shutdown()

            event.accept()

        except Exception as e:
            print(f"关闭窗口时发生错误: {e}")
            event.accept()

    def resizeEvent(self, event):
        # 首次显示或正在最大化/全屏时，或接近最大化尺寸时，不调整窗口几何，避免与系统行为冲突
        try:
            ag = self._get_available_geometry()
            near_max = False
            try:
                sz = event.size()
                near_max = (sz.width() >= ag.width() - 16) or (sz.height() >= ag.height() - 16)
            except Exception:
                pass
            if getattr(self, '_pending_initial_sizing', False) or self.isMaximized() or self.isFullScreen() or near_max:
                try:
                    self._cap_details_panel()
                except Exception:
                    pass
                super().resizeEvent(event)
                return
        except Exception:
            pass
        try:
            # 仅应用子部件的约束（不主动更改窗口尺寸）
            self._cap_details_panel()
        except Exception:
            pass
        super().resizeEvent(event)

    def moveEvent(self, event):
        # 首次显示或最大化/全屏状态下，不夹紧位置
        if getattr(self, '_pending_initial_sizing', False) or self.isMaximized() or self.isFullScreen():
            super().moveEvent(event)
            return
        try:
            ag = self._get_available_geometry()
            fg = self.frameGeometry()
            # 接近最大化时不干预
            near_max = (fg.width() >= ag.width() - 16) or (fg.height() >= ag.height() - 16)
            if near_max:
                super().moveEvent(event)
                return
            # 仅在明显越界时才夹紧（考虑装饰边距）
            out = fg.left() < ag.left() - 1 or fg.top() < ag.top() - 1 or fg.right() > ag.right() + 1 or fg.bottom() > ag.bottom() + 1
            if out:
                try:
                    self._clamp_to_work_area()
                except Exception:
                    pass
        except Exception:
            pass
        super().moveEvent(event)

    def showEvent(self, event):
        """窗口显示时，按屏幕可用区域做一次适配与居中"""
        super().showEvent(event)
        try:
            if getattr(self, '_pending_initial_sizing', False):
                QTimer.singleShot(0, self._initial_size_and_center)
            else:
                # 后续显示：仅应用子部件约束；非最大化时再夹紧位置
                try:
                    self._cap_details_panel()
                except Exception:
                    pass
                if not (self.isMaximized() or self.isFullScreen()):
                    try:
                        self._clamp_to_work_area()
                    except Exception:
                        pass
        except Exception:
            pass
        # 首次显示时，强制水平与默认比例（若没有保存值）
        try:
            if not getattr(self, "_splitter_initialized", False) and hasattr(self, 'splitter'):
                self.splitter.setOrientation(Qt.Horizontal)
                settings = QSettings("LAD", "ErrorHistoryUI")
                state = settings.value("splitterState_h")
                if state:
                    self.splitter.restoreState(state if isinstance(state, QByteArray) else QByteArray(state))
                else:
                    total = max(self.width(), 1)
                    left = max(300, int(total * 0.74))
                    right = max(260, total - left)
                    self.splitter.setSizes([left, right])
                self._splitter_initialized = True
        except Exception:
            pass

    def _initial_size_and_center(self):
        try:
            ag = self._get_available_geometry()
            hint = self.sizeHint()
            # 使用更保守的比例，并限制在可用区域之内
            tw = min(hint.width(), max(600, ag.width() - 96))
            th = min(hint.height(), max(360, ag.height() - 96))
            # 不低于当前 baseline 最小尺寸
            tw = max(self.minimumWidth(), tw)
            th = max(self.minimumHeight(), th)

            self.resize(tw, th)
            self._center_window()
            self._clamp_to_work_area()
        except Exception:
            pass
        self._pending_initial_sizing = False

    # 为避免Windows在初次展示时根据过大的sizeHint尝试放大窗口，提供保守的尺寸建议
    def sizeHint(self) -> QSize:
        try:
            return QSize(600, 360)
        except Exception:
            return QSize(600, 360)

    def minimumSizeHint(self) -> QSize:
        try:
            return QSize(600, 360)
        except Exception:
            return super().minimumSizeHint()

    @staticmethod
    def show_error_history_ui(mode: str = "query"):
        """静态方法显示错误历史UI"""
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        window = ErrorHistoryMainWindow(mode=mode)
        window.show()

        return app.exec_() if app else 0
