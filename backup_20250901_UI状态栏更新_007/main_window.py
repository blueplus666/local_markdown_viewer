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
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QSplitter, QMenuBar, QStatusBar, QAction, QFileDialog,
    QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtGui import QIcon, QFont

# 导入配置管理器
sys.path.append(str(Path(__file__).parent.parent))
from utils.config_manager import get_config_manager
from ui.file_tree import FileTree  # 导入FileTree组件
from ui.content_viewer import ContentViewer  # 导入ContentViewer组件


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
        super().__init__()
        
        # 获取配置管理器
        self.config_manager = get_config_manager()
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 初始化UI组件
        self.file_tree = None  # 文件树组件（后续实现）
        self.content_viewer = None  # 内容显示组件（后续实现）
        self.splitter = None  # 分割器
        
        # 初始化窗口
        self._init_window()
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_status_bar()
        self._setup_connections()
        
        self.logger.info("主窗口初始化完成")
    
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
        
        # 添加文件树组件（占位，后续实现）
        self.file_tree = FileTree() # 使用FileTree组件
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
        self.content_viewer = ContentViewer()
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
        
        # 显示初始状态
        status_bar.showMessage("就绪")
        
        self.logger.info("状态栏设置完成")
    
    def _setup_connections(self):
        """设置信号连接"""
        # 连接分割器大小变化信号
        self.splitter.splitterMoved.connect(self._on_splitter_moved)
        
        # 连接文件选择信号
        self.file_tree.file_selected.connect(self._handle_file_selected)
        
        # 连接内容显示组件信号
        if self.content_viewer:
            self.content_viewer.content_loaded.connect(self._on_content_loaded)
            self.content_viewer.error_occurred.connect(self._on_content_error)
        
        self.logger.info("信号连接设置完成")
    
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
        
        # 使用内容显示组件显示文件
        if self.content_viewer:
            self.content_viewer.display_file(file_path)
        
        # 更新窗口标题
        file_name = Path(file_path).name
        self.setWindowTitle(f"{file_name} - 本地Markdown文件渲染器")
    
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
        else:
            self.statusBar().showMessage(f"文件加载失败: {Path(file_path).name}")
            self.logger.warning(f"内容加载失败: {file_path}")
    
    def _on_content_error(self, error_type: str, error_message: str):
        """内容显示错误处理"""
        self.statusBar().showMessage(f"错误: {error_type}")
        self.logger.error(f"内容显示错误 - {error_type}: {error_message}")


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
