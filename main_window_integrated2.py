#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成主窗口模块 v1.0.0
集成所有核心组件：FileTree、ContentViewer、FileResolver、MarkdownRenderer、ContentPreview
实现完整的文件浏览和内容显示功能

作者: LAD Team
创建时间: 2025-01-08
最后更新: 2025-01-08
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import time

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QSplitter, QMenuBar, QStatusBar, QAction, QFileDialog,
    QMessageBox, QApplication, QProgressBar, QLabel
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont

# 导入配置管理器
sys.path.append(str(Path(__file__).parent))
from utils.config_manager import get_config_manager
from ui.file_tree import FileTree
from ui.content_viewer import ContentViewer
from core.file_resolver import FileResolver
from core.markdown_renderer import MarkdownRenderer
from core.content_preview import ContentPreview


class IntegratedMainWindow(QMainWindow):
    """
    集成主窗口类
    集成所有核心组件，实现完整的文件浏览和内容显示功能
    """
    
    # 定义信号
    file_selected = pyqtSignal(str)  # 文件选择信号
    content_loaded = pyqtSignal(str, bool)  # 内容加载完成信号
    error_occurred = pyqtSignal(str, str)  # 错误发生信号
    
    def __init__(self):
        """初始化集成主窗口"""
        super().__init__()
        
        # 获取配置管理器
        self.config_manager = get_config_manager()
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 初始化核心组件
        self._init_core_components()
        
        # 初始化UI组件
        self.file_tree = None
        self.content_viewer = None
        self.splitter = None
        
        # 性能监控
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self._monitor_performance)
        self.performance_timer.start(5000)  # 每5秒监控一次
        
        # 初始化窗口
        self._init_window()
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_status_bar()
        self._setup_connections()
        
        self.logger.info("集成主窗口初始化完成")
    
    def _init_core_components(self):
        """初始化核心组件"""
        try:
            # 初始化文件解析器
            self.file_resolver = FileResolver(self.config_manager)
            self.logger.info("FileResolver初始化成功")
            
            # 初始化Markdown渲染器
            self.markdown_renderer = MarkdownRenderer(self.config_manager)
            self.logger.info("MarkdownRenderer初始化成功")
            
            # 初始化内容预览器
            self.content_preview = ContentPreview(self.config_manager)
            self.logger.info("ContentPreview初始化成功")
            
        except Exception as e:
            self.logger.error(f"核心组件初始化失败: {e}")
            raise
    
    def _init_window(self):
        """初始化窗口基本属性"""
        # 设置窗口标题
        title = self.config_manager.get_config("app.window.title", "本地Markdown文件渲染器 - 集成版")
        self.setWindowTitle(title)
        
        # 设置窗口大小
        width = self.config_manager.get_config("app.window.width", 1400)
        height = self.config_manager.get_config("app.window.height", 900)
        self.resize(width, height)
        
        # 设置最小窗口大小
        min_width = self.config_manager.get_config("app.window.min_width", 1000)
        min_height = self.config_manager.get_config("app.window.min_height", 700)
        self.setMinimumSize(min_width, min_height)
        
        # 设置窗口居中显示
        self._center_window()
    
    def _center_window(self):
        """将窗口居中显示"""
        screen = QApplication.desktop().screenGeometry()
        window = self.geometry()
        x = (screen.width() - window.width()) // 2
        y = (screen.height() - window.height()) // 2
        self.move(x, y)
    
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
        main_layout.addWidget(self.splitter)
        
        # 创建左侧面板（文件树）
        self._create_left_panel()
        
        # 创建右侧面板（内容显示）
        self._create_right_panel()
        
        # 获取布局配置
        left_width = self.config_manager.get_config("layout.left_panel_width", 350, "ui")
        
        # 设置分割器
        self.splitter.setSizes([left_width, self.width() - left_width])
        
        # 设置分割器样式
        self._setup_splitter_style()
    
    def _create_left_panel(self):
        """创建左侧面板（文件树）"""
        # 创建左侧容器
        left_widget = QWidget()
        left_widget.setMinimumWidth(250)
        left_widget.setMaximumWidth(600)
        
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
        
        # 添加文件树组件
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
        """设置菜单栏"""
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
        
        # 刷新动作
        refresh_action = QAction("刷新(&R)", self)
        refresh_action.setShortcut("F5")
        refresh_action.setStatusTip("刷新当前文件")
        refresh_action.triggered.connect(self._refresh_current_file)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        # 退出动作
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("退出应用程序")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        
        # 缩放动作
        zoom_in_action = QAction("放大(&+)", self)
        zoom_in_action.setShortcut("Ctrl+=")
        zoom_in_action.setStatusTip("放大内容")
        zoom_in_action.triggered.connect(self._zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("缩小(&-)", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.setStatusTip("缩小内容")
        zoom_out_action.triggered.connect(self._zoom_out)
        view_menu.addAction(zoom_out_action)
        
        reset_zoom_action = QAction("重置缩放(&0)", self)
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.setStatusTip("重置缩放")
        reset_zoom_action.triggered.connect(self._reset_zoom)
        view_menu.addAction(reset_zoom_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")
        
        # 清除缓存动作
        clear_cache_action = QAction("清除缓存(&C)", self)
        clear_cache_action.setStatusTip("清除内容缓存")
        clear_cache_action.triggered.connect(self._clear_cache)
        tools_menu.addAction(clear_cache_action)
        
        # 性能信息动作
        performance_action = QAction("性能信息(&P)", self)
        performance_action.setStatusTip("显示性能信息")
        performance_action.triggered.connect(self._show_performance_info)
        tools_menu.addAction(performance_action)
        
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
        
        # 创建状态栏组件
        self.status_label = QLabel("就绪")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        
        # 添加到状态栏
        status_bar.addWidget(self.status_label)
        status_bar.addPermanentWidget(self.progress_bar)
        
        # 显示初始状态
        status_bar.showMessage("就绪")
        
        self.logger.info("状态栏设置完成")
    
    def _setup_connections(self):
        """设置信号连接"""
        # 连接分割器大小变化信号
        self.splitter.splitterMoved.connect(self._on_splitter_moved)
        
        # 连接文件树信号
        self.file_tree.file_selected.connect(self._handle_file_selected)
        self.file_tree.directory_changed.connect(self._handle_directory_changed)
        self.file_tree.file_double_clicked.connect(self._handle_file_double_clicked)
        
        # 连接内容显示组件信号
        self.content_viewer.content_loaded.connect(self._on_content_loaded)
        self.content_viewer.loading_progress.connect(self._on_loading_progress)
        self.content_viewer.error_occurred.connect(self._on_content_error)
        
        # 连接自定义信号
        self.file_selected.connect(self._on_file_selected)
        self.content_loaded.connect(self._on_content_loaded_signal)
        self.error_occurred.connect(self._on_error_occurred)
        
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
    
    def _refresh_current_file(self):
        """刷新当前文件"""
        current_file = self.content_viewer.get_current_file()
        if current_file:
            self._handle_file_selected(current_file, force_reload=True)
            self.statusBar().showMessage(f"已刷新文件: {Path(current_file).name}")
        else:
            self.statusBar().showMessage("没有当前文件")
    
    def _zoom_in(self):
        """放大内容"""
        if self.content_viewer.is_web_engine_available():
            current_zoom = self.content_viewer.get_zoom_factor()
            new_zoom = min(current_zoom * 1.2, 3.0)
            self.content_viewer.set_zoom_factor(new_zoom)
            self.statusBar().showMessage(f"缩放: {new_zoom:.1f}x")
    
    def _zoom_out(self):
        """缩小内容"""
        if self.content_viewer.is_web_engine_available():
            current_zoom = self.content_viewer.get_zoom_factor()
            new_zoom = max(current_zoom / 1.2, 0.3)
            self.content_viewer.set_zoom_factor(new_zoom)
            self.statusBar().showMessage(f"缩放: {new_zoom:.1f}x")
    
    def _reset_zoom(self):
        """重置缩放"""
        if self.content_viewer.is_web_engine_available():
            self.content_viewer.set_zoom_factor(1.0)
            self.statusBar().showMessage("缩放已重置")
    
    def _clear_cache(self):
        """清除缓存"""
        self.content_viewer.clear_cache()
        self.markdown_renderer.clear_cache()
        self.content_preview.clear_cache()
        self.statusBar().showMessage("缓存已清除")
    
    def _show_performance_info(self):
        """显示性能信息"""
        # 获取缓存信息
        content_cache_info = self.content_viewer.get_cache_info()
        markdown_cache_info = self.markdown_renderer.get_cache_info()
        preview_stats = self.content_preview.get_preview_stats()
        
        # 构建性能信息
        info_text = f"""
        <h3>性能信息</h3>
        <p><b>内容缓存:</b> {content_cache_info['total']}/{content_cache_info['limit']} 条目</p>
        <p><b>Markdown缓存:</b> {markdown_cache_info['total']}/{markdown_cache_info['limit']} 条目</p>
        <p><b>预览统计:</b> 总预览 {preview_stats['total_previews']} 次，成功 {preview_stats['successful_previews']} 次</p>
        <p><b>平均预览时间:</b> {preview_stats['average_time']:.3f} 秒</p>
        """
        
        QMessageBox.information(self, "性能信息", info_text)
    
    def _show_about(self):
        """显示关于对话框"""
        app_name = self.config_manager.get_config("app.name", "本地Markdown文件渲染器 - 集成版")
        app_version = self.config_manager.get_config("app.version", "1.0.0")
        app_description = self.config_manager.get_config("app.description", "集成所有核心组件的完整文件浏览和内容显示系统")
        app_author = self.config_manager.get_config("app.author", "LAD Team")
        
        about_text = f"""
        <h3>{app_name}</h3>
        <p>版本: {app_version}</p>
        <p>{app_description}</p>
        <p>作者: {app_author}</p>
        <p>基于PyQt5开发</p>
        <p><b>集成组件:</b></p>
        <ul>
            <li>FileResolver - 文件解析器</li>
            <li>MarkdownRenderer - Markdown渲染器</li>
            <li>ContentPreview - 内容预览器</li>
            <li>FileTree - 文件树组件</li>
            <li>ContentViewer - 内容显示组件</li>
        </ul>
        """
        
        QMessageBox.about(self, "关于", about_text)
    
    def _on_splitter_moved(self, pos, index):
        """分割器移动事件处理"""
        # 保存分割器位置到配置
        sizes = self.splitter.sizes()
        if sizes[0] > 0:
            self.config_manager.set_config("layout.left_panel_width", sizes[0], "ui")
    
    def _handle_file_selected(self, file_path: str, force_reload: bool = False):
        """处理文件选择事件"""
        self.logger.info(f"文件被选择: {file_path}")
        
        # 更新状态栏
        self.statusBar().showMessage(f"正在加载文件: {Path(file_path).name}")
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 发送文件选择信号
        self.file_selected.emit(file_path)
        
        # 使用内容显示组件显示文件
        if self.content_viewer:
            self.content_viewer.display_file(file_path, force_reload)
        
        # 更新窗口标题
        file_name = Path(file_path).name
        self.setWindowTitle(f"{file_name} - 本地Markdown文件渲染器 - 集成版")
    
    def _handle_directory_changed(self, directory_path: str):
        """处理目录变更事件"""
        self.logger.info(f"目录变更: {directory_path}")
        self.statusBar().showMessage(f"当前目录: {Path(directory_path).name}")
    
    def _handle_file_double_clicked(self, file_path: str):
        """处理文件双击事件"""
        self.logger.info(f"文件双击: {file_path}")
        self._handle_file_selected(file_path)
    
    def _handle_folder_selected(self, folder_path: str):
        """处理文件夹选择事件"""
        self.logger.info(f"文件夹被选择: {folder_path}")
        
        # 更新状态栏
        self.statusBar().showMessage(f"已选择文件夹: {folder_path}")
        
        # 设置文件树的根目录
        if self.file_tree:
            self.file_tree.set_root_path(folder_path)
    
    def _on_content_loaded(self, file_path: str, success: bool):
        """内容加载完成处理"""
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        
        if success:
            self.statusBar().showMessage(f"文件已加载: {Path(file_path).name}")
            self.logger.info(f"内容加载成功: {file_path}")
        else:
            self.statusBar().showMessage(f"文件加载失败: {Path(file_path).name}")
            self.logger.warning(f"内容加载失败: {file_path}")
    
    def _on_loading_progress(self, progress: int):
        """加载进度处理"""
        self.progress_bar.setValue(progress)
    
    def _on_content_error(self, error_type: str, error_message: str):
        """内容显示错误处理"""
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage(f"错误: {error_type}")
        self.logger.error(f"内容显示错误 - {error_type}: {error_message}")
    
    def _on_file_selected(self, file_path: str):
        """文件选择信号处理"""
        self.logger.info(f"文件选择信号: {file_path}")
    
    def _on_content_loaded_signal(self, file_path: str, success: bool):
        """内容加载完成信号处理"""
        self.logger.info(f"内容加载完成信号: {file_path}, 成功: {success}")
    
    def _on_error_occurred(self, error_type: str, error_message: str):
        """错误发生信号处理"""
        self.logger.error(f"错误发生信号 - {error_type}: {error_message}")
    
    def _monitor_performance(self):
        """性能监控"""
        try:
            # 获取缓存信息
            content_cache_info = self.content_viewer.get_cache_info()
            markdown_cache_info = self.markdown_renderer.get_cache_info()
            
            # 记录性能信息
            self.logger.debug(f"性能监控 - 内容缓存: {content_cache_info['total']}/{content_cache_info['limit']}, "
                            f"Markdown缓存: {markdown_cache_info['total']}/{markdown_cache_info['limit']}")
            
        except Exception as e:
            self.logger.error(f"性能监控失败: {e}")
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        self.logger.info("应用程序即将关闭")
        
        # 停止性能监控
        self.performance_timer.stop()
        
        # 保存窗口状态
        self._save_window_state()
        
        # 清理资源
        self._cleanup_resources()
        
        # 接受关闭事件
        event.accept()
    
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
    
    def _cleanup_resources(self):
        """清理资源"""
        try:
            # 清除缓存
            self.content_viewer.clear_cache()
            self.markdown_renderer.clear_cache()
            self.content_preview.clear_cache()
            
            self.logger.info("资源清理完成")
            
        except Exception as e:
            self.logger.error(f"资源清理失败: {e}")


if __name__ == "__main__":
    # 测试集成主窗口
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("本地Markdown文件渲染器 - 集成版")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("LAD Team")
    
    # 创建并显示集成主窗口
    window = IntegratedMainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_()) 