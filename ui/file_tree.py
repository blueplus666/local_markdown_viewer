#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件树组件模块 v1.0.0
实现基于QFileSystemModel的文件树显示和管理功能
包含文件过滤、搜索、选择事件处理等功能

作者: LAD Team
创建时间: 2025-01-08
最后更新: 2025-01-08
"""

import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from PyQt5.QtWidgets import (
    QTreeView, QFileSystemModel, QVBoxLayout, 
    QHBoxLayout, QWidget, QLineEdit, QPushButton, QCheckBox, QLabel,
    QMenu, QAction, QMessageBox, QApplication, QHeaderView
)
from PyQt5.QtCore import Qt, QDir, pyqtSignal, QModelIndex, QTimer, QSortFilterProxyModel
from PyQt5.QtGui import QIcon, QFont, QPixmap

# 导入配置管理器
sys.path.append(str(Path(__file__).parent.parent))
from utils.config_manager import get_config_manager


class FileTree(QWidget):
    """
    文件树组件类
    基于QFileSystemModel实现文件系统浏览功能
    支持文件过滤、搜索、选择事件处理等
    """
    
    # 定义信号
    file_selected = pyqtSignal(str)  # 文件选择信号
    directory_changed = pyqtSignal(str)  # 目录变更信号
    file_double_clicked = pyqtSignal(str)  # 文件双击信号
    selection_changed = pyqtSignal(list)  # 选择变化信号
    
    def __init__(self, parent=None):
        """初始化文件树组件"""
        super().__init__(parent)
        
        # 获取配置管理器
        self.config_manager = get_config_manager()
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.file_model = None  # 文件系统模型
        self.proxy_model = None  # 代理模型
        self.tree_view = None  # 树视图
        self.search_box = None  # 搜索框
        self.filter_checkbox = None  # 过滤器复选框
        
        # 初始化UI
        self._init_ui()
        self._setup_models()
        self._setup_connections()
        self._load_config()
        
        self.logger.info("文件树组件初始化完成")
    
    def _init_ui(self):
        """初始化用户界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建工具栏
        self._create_toolbar()
        
        # 创建树视图
        self._create_tree_view()
        
        # 设置样式
        self._setup_styles()
    
    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        toolbar_layout.setSpacing(5)
        
        # 搜索框
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索文件...")
        self.search_box.setMaximumWidth(200)
        toolbar_layout.addWidget(self.search_box)
        
        # 过滤器复选框
        self.filter_checkbox = QCheckBox("显示隐藏文件")
        self.filter_checkbox.setChecked(False)
        toolbar_layout.addWidget(self.filter_checkbox)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.setMaximumWidth(60)
        refresh_btn.clicked.connect(self._refresh_tree)
        toolbar_layout.addWidget(refresh_btn)
        
        # 添加弹性空间
        toolbar_layout.addStretch()
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        toolbar_layout.addWidget(self.status_label)
        
        # 将工具栏添加到主布局
        self.layout().addWidget(toolbar)
    
    def _create_tree_view(self):
        """创建树视图"""
        self.tree_view = QTreeView()
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.setSelectionMode(QTreeView.SingleSelection)
        self.tree_view.setSortingEnabled(True)
        self.tree_view.setAnimated(True)
        self.tree_view.setExpandsOnDoubleClick(True)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # 设置列宽
        self.tree_view.setColumnWidth(0, 300)  # 名称列
        self.tree_view.setColumnWidth(1, 100)  # 大小列
        self.tree_view.setColumnWidth(2, 120)  # 类型列
        self.tree_view.setColumnWidth(3, 150)  # 修改日期列
        
        # 隐藏列标题
        self.tree_view.header().setVisible(False)
        
        # 将树视图添加到主布局
        self.layout().addWidget(self.tree_view)
    
    def _setup_models(self):
        """设置模型"""
        # 创建文件系统模型
        self.file_model = QFileSystemModel()
        self.file_model.setReadOnly(True)
        
        # 设置过滤器
        self._setup_filters()
        
        # 创建代理模型
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.file_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        
        # 设置树视图模型
        self.tree_view.setModel(self.proxy_model)
        
        # 设置根目录
        self._set_root_path()
    
    def _setup_filters(self):
        """设置文件过滤器"""
        # 获取支持的文件类型
        file_types_config = self.config_manager.load_file_types_config()
        supported_extensions = []
        
        for file_type, info in file_types_config.items():
            extensions = info.get("extensions", [])
            supported_extensions.extend(extensions)
        
        # 设置名称过滤器
        if supported_extensions:
            name_filters = [f"*{ext}" for ext in supported_extensions]
            self.file_model.setNameFilters(name_filters)
            self.file_model.setNameFilterDisables(False)
        
        # 设置隐藏文件过滤器
        self._update_hidden_files_filter()
    
    def _update_hidden_files_filter(self):
        """更新隐藏文件过滤器"""
        show_hidden = self.filter_checkbox.isChecked()
        if show_hidden:
            self.file_model.setFilter(QDir.AllEntries | QDir.Hidden)
        else:
            self.file_model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot)
    
    def _set_root_path(self):
        """设置根目录"""
        # 获取默认根路径
        default_root = self.config_manager.get_config("app.default_root_path", str(Path.home()))
        root_path = Path(default_root)
        
        if not root_path.exists():
            self.logger.warning(f"配置的根路径不存在: {root_path}，使用用户主目录")
            root_path = Path.home()
        
        # 设置根目录
        source_root_index = self.file_model.setRootPath(str(root_path))
        root_index = self.proxy_model.mapFromSource(source_root_index)
        if not root_index.isValid():
            self.logger.warning(f"代理根索引无效: {root_path}")
            fallback = Path.home()
            source_root_index = self.file_model.setRootPath(str(fallback))
            root_index = self.proxy_model.mapFromSource(source_root_index)
            if not root_index.isValid():
                self.logger.warning(f"回退根索引仍无效: {fallback}")
        self.tree_view.setRootIndex(root_index)
        
        # 展开根目录
        self.tree_view.expand(root_index)
        
        # 设置列宽
        self.tree_view.setColumnWidth(0, 300)  # 名称列
        self.tree_view.setColumnWidth(1, 100)  # 大小列
        self.tree_view.setColumnWidth(2, 120)  # 类型列
        self.tree_view.setColumnWidth(3, 150)  # 修改日期列
        
        # 显示列标题
        self.tree_view.header().setVisible(True)
        
        self._current_root = root_path
        self.logger.info(f"文件树根目录设置为: {root_path}")
        self.logger.info(f"根目录索引: {root_index}")
        self.logger.info(f"根目录是否有效: {root_index.isValid()}")
        
        # 更新状态标签
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"根目录: {root_path.name}")
    
    def _setup_connections(self):
        """设置信号连接"""
        # 搜索框连接
        self.search_box.textChanged.connect(self._on_search_text_changed)
        
        # 过滤器复选框连接
        self.filter_checkbox.toggled.connect(self._on_filter_changed)
        
        # 树视图连接
        self.tree_view.clicked.connect(self._on_item_clicked)
        self.tree_view.doubleClicked.connect(self._on_item_double_clicked)
        self.tree_view.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.tree_view.customContextMenuRequested.connect(self._on_context_menu)
        
        # 代理模型连接
        self.proxy_model.rowsInserted.connect(self._on_rows_inserted)
        self.proxy_model.rowsRemoved.connect(self._on_rows_removed)
    
    def _setup_styles(self):
        """设置样式"""
        self.setStyleSheet("""
            QTreeView {
                background-color: white;
                border: 1px solid #e0e0e0;
                outline: none;
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                font-size: 12px;
            }
            QTreeView::item {
                padding: 4px;
                border: none;
                min-height: 20px;
            }
            QTreeView::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QTreeView::item:hover {
                background-color: #f5f5f5;
            }
            QTreeView::branch {
                background-color: transparent;
            }
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQgNEw4IDZMNCA4VjRaIiBmaWxsPSIjNjY2Ii8+Cjwvc3ZnPgo=);
            }
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTYgNEw0IDZMNyA2TDYgNFoiIGZpbGw9IiM2NjYiLz4KPC9zdmc+Cg==);
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 6px;
                border: 1px solid #e0e0e0;
                font-weight: bold;
                color: #333;
            }
            QHeaderView::section:hover {
                background-color: #e9ecef;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 3px;
                background-color: white;
            }
            QPushButton {
                padding: 5px 10px;
                border: 1px solid #ddd;
                border-radius: 3px;
                background-color: #f8f9fa;
                color: #333;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QCheckBox {
                spacing: 5px;
                color: #333;
            }
            QLabel {
                color: #333;
            }
        """)
    
    def _load_config(self):
        """加载配置"""
        # 加载文件树配置
        show_hidden = self.config_manager.get_config("file_tree.show_hidden_files", False)
        self.filter_checkbox.setChecked(show_hidden)
        
        # 加载搜索配置
        search_text = self.config_manager.get_config("file_tree.last_search", "")
        if search_text:
            self.search_box.setText(search_text)
    
    def _on_search_text_changed(self, text: str):
        """搜索文本变化处理"""
        # 设置代理模型过滤器
        self.proxy_model.setFilterFixedString(text)
        
        # 保存搜索文本
        self.config_manager.set_config("file_tree.last_search", text, "app")
        
        # 更新状态
        self._update_status()
    
    def _on_filter_changed(self, checked: bool):
        """过滤器变化处理"""
        # 更新隐藏文件过滤器
        self._update_hidden_files_filter()
        
        # 保存配置
        self.config_manager.set_config("file_tree.show_hidden_files", checked, "app")
        
        # 更新状态
        self._update_status()
    
    def _on_item_clicked(self, index: QModelIndex):
        """项目点击处理"""
        # 获取文件路径
        source_index = self.proxy_model.mapToSource(index)
        file_path = self.file_model.filePath(source_index)
        
        # 检查是否为文件
        if self.file_model.isDir(source_index):
            self.directory_changed.emit(file_path)
        else:
            self.file_selected.emit(file_path)
    
    def _on_item_double_clicked(self, index: QModelIndex):
        """项目双击处理"""
        # 获取文件路径
        source_index = self.proxy_model.mapToSource(index)
        file_path = self.file_model.filePath(source_index)
        
        # 检查是否为文件
        if not self.file_model.isDir(source_index):
            self.file_double_clicked.emit(file_path)
    
    def _on_selection_changed(self):
        """选择变化处理"""
        # 获取选中的文件路径
        selected_files = self.get_selected_files()
        self.selection_changed.emit(selected_files)
    
    def _on_context_menu(self, position):
        """右键菜单处理"""
        # 获取点击的项目
        index = self.tree_view.indexAt(position)
        if not index.isValid():
            return
        
        # 获取文件路径
        source_index = self.proxy_model.mapToSource(index)
        file_path = self.file_model.filePath(source_index)
        
        # 创建右键菜单
        menu = QMenu(self)
        
        # 打开文件动作
        if not self.file_model.isDir(source_index):
            open_action = QAction("打开文件", self)
            open_action.triggered.connect(lambda: self.file_selected.emit(file_path))
            menu.addAction(open_action)
        
        # 在文件管理器中显示动作
        show_in_explorer_action = QAction("在文件管理器中显示", self)
        show_in_explorer_action.triggered.connect(lambda: self._show_in_explorer(file_path))
        menu.addAction(show_in_explorer_action)
        
        # 复制路径动作
        copy_path_action = QAction("复制路径", self)
        copy_path_action.triggered.connect(lambda: self._copy_path(file_path))
        menu.addAction(copy_path_action)
        
        # 显示菜单
        menu.exec_(self.tree_view.mapToGlobal(position))
    
    def _on_rows_inserted(self, parent, first, last):
        """行插入处理"""
        self._update_status()
    
    def _on_rows_removed(self, parent, first, last):
        """行删除处理"""
        self._update_status()
    
    def _update_status(self):
        """更新状态显示"""
        # 获取可见项目数量
        visible_count = self.proxy_model.rowCount(self.tree_view.rootIndex())
        
        # 获取搜索文本
        search_text = self.search_box.text()
        
        if search_text:
            self.status_label.setText(f"找到 {visible_count} 个项目")
        else:
            self.status_label.setText(f"共 {visible_count} 个项目")
    
    def _refresh_tree(self):
        """刷新文件树"""
        # 重新设置根目录
        self._set_root_path()
        
        # 更新状态
        self._update_status()
        
        self.logger.info("文件树已刷新")
    
    def _show_in_explorer(self, file_path: str):
        """在文件管理器中显示文件"""
        try:
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                subprocess.run(["explorer", "/select,", file_path])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", "-R", file_path])
            else:  # Linux
                subprocess.run(["xdg-open", str(Path(file_path).parent)])
                
        except Exception as e:
            self.logger.error(f"无法在文件管理器中显示文件: {e}")
            QMessageBox.warning(self, "错误", f"无法在文件管理器中显示文件: {e}")
    
    def _copy_path(self, file_path: str):
        """复制文件路径到剪贴板"""
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(file_path)
            self.status_label.setText("路径已复制到剪贴板")
        except Exception as e:
            self.logger.error(f"无法复制路径: {e}")
    
    def set_root_path(self, path: str):
        """设置根目录路径"""
        root_path = Path(path)
        if not root_path.exists():
            self.logger.warning(f"路径不存在: {path}")
            return False
        
        # 设置根目录
        source_root_index = self.file_model.setRootPath(str(root_path))
        root_index = self.proxy_model.mapFromSource(source_root_index)
        if not root_index.isValid():
            self.logger.warning(f"代理根索引无效: {root_path}")
            fallback = Path.home()
            source_root_index = self.file_model.setRootPath(str(fallback))
            root_index = self.proxy_model.mapFromSource(source_root_index)
            if root_index.isValid():
                root_path = fallback
        self.tree_view.setRootIndex(root_index)
        try:
            self.tree_view.expand(root_index)
        except Exception:
            pass
        try:
            for _ in range(100):
                if self.proxy_model.rowCount(self.tree_view.rootIndex()) > 0:
                    break
                from PyQt5.QtWidgets import QApplication
                QApplication.processEvents()
        except Exception:
            pass
        
        self._current_root = root_path
        self.logger.info(f"文件树根目录设置为: {root_path}")
        return True
    
    def get_selected_files(self) -> List[str]:
        """获取选中的文件列表"""
        selected_files = []
        selection_model = self.tree_view.selectionModel()
        
        for index in selection_model.selectedIndexes():
            source_index = self.proxy_model.mapToSource(index)
            file_path = self.file_model.filePath(source_index)
            
            # 只添加文件，不添加目录
            if not self.file_model.isDir(source_index):
                selected_files.append(file_path)
        
        return selected_files
    
    def get_current_directory(self) -> str:
        """获取当前目录"""
        root_index = self.tree_view.rootIndex()
        source_index = self.proxy_model.mapToSource(root_index)
        path = self.file_model.filePath(source_index)
        if not path:
            path = str(getattr(self, "_current_root", Path.home()))
        return path
    
    def expand_path(self, path: str):
        """展开指定路径"""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return False
            
            # 找到路径在模型中的索引
            source_index = self.file_model.index(str(path_obj))
            if not source_index.isValid():
                return False
            
            # 映射到代理模型
            proxy_index = self.proxy_model.mapFromSource(source_index)
            if not proxy_index.isValid():
                return False
            
            # 展开路径
            self.tree_view.expand(proxy_index)
            
            # 滚动到项目
            self.tree_view.scrollTo(proxy_index)
            
            self.logger.info(f"已展开路径: {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"展开路径失败: {e}")
            return False
    
    def select_file(self, file_path: str):
        """选择指定文件"""
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                return False
            
            # 找到文件在模型中的索引
            source_index = self.file_model.index(str(path_obj))
            if not source_index.isValid():
                parent_index = self.file_model.index(str(path_obj.parent))
                if parent_index.isValid():
                    parent_proxy = self.proxy_model.mapFromSource(parent_index)
                    if parent_proxy.isValid():
                        self.tree_view.expand(parent_proxy)
                source_index = self.file_model.index(str(path_obj))
                if not source_index.isValid():
                    self.logger.warning(f"无法定位文件: {file_path}")
                    return False

            proxy_index = self.proxy_model.mapFromSource(source_index)
            if not proxy_index.isValid():
                parent = source_index.parent()
                while parent.isValid() and not proxy_index.isValid():
                    self.tree_view.expand(self.proxy_model.mapFromSource(parent))
                    proxy_index = self.proxy_model.mapFromSource(source_index)
                    parent = parent.parent()
                if not proxy_index.isValid():
                    self.logger.warning(f"无法映射索引: {file_path}")
                    return False

            # 确保父目录展开
            parent = proxy_index.parent()
            while parent.isValid():
                self.tree_view.expand(parent)
                parent = parent.parent()

            # 选择文件
            selection_model = self.tree_view.selectionModel()
            selection_model.clearSelection()
            selection_model.select(proxy_index, selection_model.Select | selection_model.Rows)

            # 滚动到项目并设置当前索引
            self.tree_view.scrollTo(proxy_index)
            self.tree_view.setCurrentIndex(proxy_index)

            # 发射信号，保持行为与手动点击一致
            self.file_selected.emit(str(path_obj))

            self.logger.info(f"已选择文件: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"选择文件失败: {e}")
            return False
    
    def clear_selection(self):
        """清除选择"""
        selection_model = self.tree_view.selectionModel()
        selection_model.clearSelection()
    
    def get_file_count(self) -> int:
        """获取文件数量"""
        return self.proxy_model.rowCount(self.tree_view.rootIndex())

    def search_files(self, keyword: str) -> List[str]:
        """根据关键字搜索文件，返回匹配路径列表。"""
        if keyword is None:
            keyword = ""
        keyword = str(keyword)
        self.logger.info(f"执行文件搜索: {keyword}")
        self.search_box.setText(keyword)
        matches: List[str] = []
        if not keyword:
            return matches
        try:
            source_model = self.file_model
            keyword_lower = keyword.lower()
            root_index = self.proxy_model.mapToSource(self.tree_view.rootIndex())
            stack = [root_index]
            while stack:
                index = stack.pop()
                if not index.isValid():
                    continue
                path = Path(source_model.filePath(index))
                if keyword_lower in path.name.lower():
                    matches.append(str(path))
                if source_model.isDir(index):
                    for row in range(source_model.rowCount(index)):
                        stack.append(source_model.index(row, 0, index))
        except Exception as exc:
            self.logger.warning(f"文件搜索失败: {exc}")
        return matches

    def filter_files(self, patterns: Optional[List[str]] = None) -> None:
        """对文件树应用过滤模式。"""
        if not patterns:
            self.proxy_model.setFilterWildcard("")
            return
        # 使用简单的 OR 逻辑组合模式
        regex_parts = [pattern.replace('.', '\\.').replace('*', '.*') for pattern in patterns]
        combined = '|'.join(regex_parts)
        self.proxy_model.setFilterRegularExpression(combined)

    def get_filtered_files(self) -> List[str]:
        """返回当前过滤结果中的文件路径列表。"""
        results: List[str] = []
        for row in range(self.proxy_model.rowCount()):
            index = self.proxy_model.index(row, 0)
            source_index = self.proxy_model.mapToSource(index)
            path = self.file_model.filePath(source_index)
            if not self.file_model.isDir(source_index):
                results.append(path)
        return results
    
    def is_file_supported(self, file_path: str) -> bool:
        """检查文件是否被支持"""
        try:
            # 获取文件扩展名
            extension = Path(file_path).suffix.lower()
            
            # 获取支持的文件类型
            file_types_config = self.config_manager.load_file_types_config()
            
            for file_type, info in file_types_config.items():
                extensions = info.get("extensions", [])
                if extension in extensions:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查文件支持失败: {e}")
            return False


if __name__ == "__main__":
    # 测试文件树组件
    app = QApplication(sys.argv)
    
    # 创建文件树组件
    file_tree = FileTree()
    file_tree.show()
    
    # 运行应用程序
    sys.exit(app.exec_()) 