# error_history/ui/query_panel.py
"""
错误历史持久化子系统 - 查询面板
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QLabel, QComboBox, QLineEdit,
    QDateEdit, QGroupBox, QCheckBox, QProgressBar,
    QSplitter, QFrame, QScrollArea, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDate
from PyQt5.QtGui import QFont, QColor

from ..core.manager import ErrorHistoryManager
from ..core.models import ErrorSeverity, ErrorCategory


class QueryWorker(QThread):
    """查询工作线程"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, manager: ErrorHistoryManager, filters: Dict[str, Any]):
        super().__init__()
        self.manager = manager
        self.filters = filters

    def run(self):
        try:
            errors = self.manager.query_errors(filters=self.filters, limit=1000)
            self.finished.emit(errors)
        except Exception as e:
            self.error.emit(str(e))


class QueryPanel(QWidget):
    """查询面板"""

    # 信号
    error_selected = pyqtSignal(dict)  # 错误选择信号
    data_changed = pyqtSignal()        # 数据变更信号

    def __init__(self, manager: ErrorHistoryManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.current_errors = []
        self.query_worker = None

        self._init_ui()
        self._setup_connections()
        self._load_initial_data()

    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(8)
        try:
            content.setStyleSheet(
                "QLabel, QLineEdit, QComboBox, QDateEdit, QPushButton, QCheckBox { font-size: 9pt; }"
                " QTableWidget, QHeaderView::section { font-size: 8pt; }"
            )
        except Exception:
            pass

        # 创建过滤条件面板
        self._create_filter_panel(content_layout)

        # 创建结果表格
        self._create_results_table(content_layout)

        # 创建分页控件
        self._create_pagination(content_layout)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _create_filter_panel(self, parent_layout):
        """创建过滤条件面板"""
        filter_group = QGroupBox("查询条件")
        filter_layout = QGridLayout(filter_group)
        filter_layout.setContentsMargins(8, 8, 8, 8)
        filter_layout.setHorizontalSpacing(8)
        filter_layout.setVerticalSpacing(5)
        filter_layout.setColumnStretch(1, 1)
        filter_layout.setColumnStretch(3, 1)

        # 日期范围
        filter_layout.addWidget(QLabel("开始日期:"), 0, 0)
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setMinimumHeight(26)
        filter_layout.addWidget(self.start_date_edit, 0, 1)

        filter_layout.addWidget(QLabel("结束日期:"), 0, 2)
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setMinimumHeight(26)
        filter_layout.addWidget(self.end_date_edit, 0, 3)

        # 严重程度
        filter_layout.addWidget(QLabel("严重程度:"), 1, 0)
        self.severity_combo = QComboBox()
        self.severity_combo.addItem("全部", None)
        for severity in ErrorSeverity:
            self.severity_combo.addItem(severity.value, severity)
        self.severity_combo.setMinimumHeight(26)
        filter_layout.addWidget(self.severity_combo, 1, 1)

        # 错误分类
        filter_layout.addWidget(QLabel("错误分类:"), 1, 2)
        self.category_combo = QComboBox()
        self.category_combo.addItem("全部", None)
        for category in ErrorCategory:
            self.category_combo.addItem(category.value, category)
        self.category_combo.setMinimumHeight(26)
        filter_layout.addWidget(self.category_combo, 1, 3)

        # 模块名称
        filter_layout.addWidget(QLabel("模块名称:"), 2, 0)
        self.module_edit = QLineEdit()
        self.module_edit.setPlaceholderText("输入模块名进行过滤")
        self.module_edit.setMinimumHeight(26)
        filter_layout.addWidget(self.module_edit, 2, 1, 1, 3)

        # 错误类型
        filter_layout.addWidget(QLabel("错误类型:"), 3, 0)
        self.error_type_edit = QLineEdit()
        self.error_type_edit.setPlaceholderText("输入错误类型关键字")
        self.error_type_edit.setMinimumHeight(26)
        filter_layout.addWidget(self.error_type_edit, 3, 1, 1, 3)

        # 解决状态
        filter_layout.addWidget(QLabel("解决状态:"), 4, 0)
        self.resolved_combo = QComboBox()
        self.resolved_combo.addItem("全部", None)
        self.resolved_combo.addItem("已解决", True)
        self.resolved_combo.addItem("未解决", False)
        self.resolved_combo.setMinimumHeight(26)
        filter_layout.addWidget(self.resolved_combo, 4, 1)

        # 操作按钮
        buttons_layout = QHBoxLayout()

        self.query_btn = QPushButton("查询(&Q)")
        self.query_btn.setDefault(True)
        buttons_layout.addWidget(self.query_btn)

        self.clear_btn = QPushButton("清空(&C)")
        buttons_layout.addWidget(self.clear_btn)

        self.refresh_btn = QPushButton("刷新(&R)")
        buttons_layout.addWidget(self.refresh_btn)

        buttons_layout.addStretch()

        filter_layout.addLayout(buttons_layout, 4, 2, 1, 2)

        parent_layout.addWidget(filter_group)

    def _create_results_table(self, parent_layout):
        """创建结果表格"""
        # 表格容器
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(8, 8, 8, 8)
        table_layout.setSpacing(6)

        # 表格标题和统计
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("查询结果"))

        self.results_count_label = QLabel("共 0 条记录")
        header_layout.addWidget(self.results_count_label)

        header_layout.addStretch()

        # 显示列选择
        header_layout.addWidget(QLabel("显示列:"))
        self.columns_combo = QComboBox()
        self.columns_combo.addItem("标准视图", "standard")
        self.columns_combo.addItem("详细视图", "detailed")
        self.columns_combo.addItem("最小视图", "minimal")
        header_layout.addWidget(self.columns_combo)

        table_layout.addLayout(header_layout)

        # 创建表格
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setMinimumHeight(110)
        self.results_table.setMaximumHeight(130)
        self.results_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 设置表格样式
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.verticalHeader().setVisible(False)

        table_layout.addWidget(self.results_table)

        parent_layout.addWidget(table_container)

        # 设置表格列（标准视图）
        self._setup_table_columns()

    def _setup_table_columns(self, view_type: Optional[str] = None):
        """根据当前选择设置表头与列数"""
        try:
            # 优先使用传入的类型，否则取当前下拉框的 data
            vt = view_type
            if not vt:
                vt = self.columns_combo.currentData() or "standard"

            try:
                header = self.results_table.horizontalHeader()
                header.setSectionResizeMode(QHeaderView.Stretch)
                header.setMinimumSectionSize(30)
                header.setDefaultSectionSize(80)
            except Exception:
                pass

            if vt == "standard":
                headers = [
                    "错误ID", "错误类型", "错误消息", "严重程度",
                    "分类", "模块", "创建时间", "解决状态"
                ]
                self.results_table.setColumnCount(len(headers))
                self.results_table.setHorizontalHeaderLabels(headers)
            elif vt == "detailed":
                headers = [
                    "错误ID", "错误类型", "错误消息", "严重程度", "分类",
                    "模块", "函数", "行号", "创建时间", "解决状态",
                    "解决时间", "重试次数"
                ]
                self.results_table.setColumnCount(len(headers))
                self.results_table.setHorizontalHeaderLabels(headers)
            elif vt == "minimal":
                headers = ["错误ID", "错误消息", "严重程度", "创建时间", "解决状态"]
                self.results_table.setColumnCount(len(headers))
                self.results_table.setHorizontalHeaderLabels(headers)
            else:
                # fallback
                headers = ["错误ID", "错误消息", "严重程度", "创建时间", "解决状态"]
                self.results_table.setColumnCount(len(headers))
                self.results_table.setHorizontalHeaderLabels(headers)
        except Exception:
            pass

    def _apply_auto_heights(self):
        try:
            win = self.window()
            if not win:
                return
            h = max(win.height(), 1)
            target = max(110, min(130, int(h * 0.11)))
            if hasattr(self, 'results_table'):
                self.results_table.setMinimumHeight(target)
                self.results_table.setMaximumHeight(target)
        except Exception:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_auto_heights()

    def _create_pagination(self, parent_layout):
        """创建分页控件"""
        pagination_layout = QHBoxLayout()

        self.prev_btn = QPushButton("上一页")
        self.prev_btn.setEnabled(False)
        pagination_layout.addWidget(self.prev_btn)

        self.page_info_label = QLabel("第 1 页 / 共 1 页")
        pagination_layout.addWidget(self.page_info_label)

        self.next_btn = QPushButton("下一页")
        self.next_btn.setEnabled(False)
        pagination_layout.addWidget(self.next_btn)

        pagination_layout.addStretch()

        # 页面大小选择
        pagination_layout.addWidget(QLabel("每页显示:"))
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItem("50", 50)
        self.page_size_combo.addItem("100", 100)
        self.page_size_combo.addItem("200", 200)
        self.page_size_combo.setCurrentText("100")
        pagination_layout.addWidget(self.page_size_combo)

        parent_layout.addLayout(pagination_layout)

    def _setup_connections(self):
        """设置信号连接"""
        # 查询按钮
        self.query_btn.clicked.connect(self._perform_query)

        # 清空按钮
        self.clear_btn.clicked.connect(self._clear_filters)

        # 刷新按钮
        self.refresh_btn.clicked.connect(self.refresh_data)

        # 表格选择变化
        self.results_table.itemSelectionChanged.connect(self._on_table_selection_changed)

        # 视图切换
        self.columns_combo.currentTextChanged.connect(self._on_view_changed)

        # 分页
        self.prev_btn.clicked.connect(self._prev_page)
        self.next_btn.clicked.connect(self._next_page)
        self.page_size_combo.currentTextChanged.connect(self._on_page_size_changed)

    def _load_initial_data(self):
        """加载初始数据"""
        # 执行默认查询（最近7天）
        self._perform_query()

    def _perform_query(self):
        """执行查询"""
        try:
            # 收集查询条件
            filters = self._collect_filters()

            # 显示进度
            self.query_btn.setEnabled(False)
            self.query_btn.setText("查询中...")

            # 启动查询线程
            self.query_worker = QueryWorker(self.manager, filters)
            self.query_worker.finished.connect(self._on_query_finished)
            self.query_worker.error.connect(self._on_query_error)
            self.query_worker.start()

        except Exception as e:
            QMessageBox.warning(self, "查询失败", f"执行查询失败:\n{str(e)}")
            self._reset_query_button()

    def _collect_filters(self) -> Dict[str, Any]:
        """收集查询过滤条件"""
        filters = {}

        # 日期范围
        start_date = self.start_date_edit.date().toPyDate()
        end_date = self.end_date_edit.date().toPyDate()
        filters['start_date'] = start_date
        filters['end_date'] = end_date

        # 严重程度
        severity_data = self.severity_combo.currentData()
        if severity_data is not None:
            filters['severity'] = severity_data

        # 错误分类
        category_data = self.category_combo.currentData()
        if category_data is not None:
            filters['category'] = category_data

        # 模块名称
        module = self.module_edit.text().strip()
        if module:
            filters['module'] = module

        # 错误类型
        error_type = self.error_type_edit.text().strip()
        if error_type:
            filters['error_type'] = error_type

        # 解决状态
        resolved_data = self.resolved_combo.currentData()
        if resolved_data is not None:
            filters['resolved'] = resolved_data

        return filters

    def _on_query_finished(self, errors: List):
        """查询完成处理"""
        try:
            self.current_errors = errors
            self._display_results(errors)
            self._update_pagination()
            self._reset_query_button()

            # 发送数据变更信号
            self.data_changed.emit()

        except Exception as e:
            QMessageBox.warning(self, "显示结果失败", f"显示查询结果失败:\n{str(e)}")

    def _on_query_error(self, error_msg: str):
        """查询错误处理"""
        QMessageBox.critical(self, "查询失败", f"查询执行失败:\n{error_msg}")
        self._reset_query_button()

    def _reset_query_button(self):
        """重置查询按钮状态"""
        self.query_btn.setEnabled(True)
        self.query_btn.setText("查询(&Q)")

    def _display_results(self, errors: List):
        """显示查询结果"""
        view_type = self.columns_combo.currentData() or "standard"

        self.results_table.setRowCount(len(errors))

        for row, error in enumerate(errors):
            if view_type == "standard":
                self._display_standard_row(row, error)
            elif view_type == "detailed":
                self._display_detailed_row(row, error)
            elif view_type == "minimal":
                self._display_minimal_row(row, error)

        # 更新记录数显示
        self.results_count_label.setText(f"共 {len(errors)} 条记录")

    def _display_standard_row(self, row: int, error):
        """显示标准视图行"""
        items = [
            error.error_id,
            error.error_type,
            error.error_message[:100] + "..." if len(error.error_message) > 100 else error.error_message,
            error.severity.value,
            error.category.value,
            error.module or "",
            error.created_at.strftime("%Y-%m-%d %H:%M:%S") if error.created_at else "",
            "已解决" if error.resolved else "未解决"
        ]

        for col, item_text in enumerate(items):
            table_item = QTableWidgetItem(str(item_text))
            table_item.setData(Qt.UserRole, error)  # 存储完整错误对象
            self.results_table.setItem(row, col, table_item)

    def _display_detailed_row(self, row: int, error):
        """显示详细视图行"""
        items = [
            error.error_id,
            error.error_type,
            error.error_message[:100] + "..." if len(error.error_message) > 100 else error.error_message,
            error.severity.value,
            error.category.value,
            error.module or "",
            error.function or "",
            str(error.line_number) if error.line_number else "",
            error.created_at.strftime("%Y-%m-%d %H:%M:%S") if error.created_at else "",
            "已解决" if error.resolved else "未解决",
            error.resolved_at.strftime("%Y-%m-%d %H:%M:%S") if error.resolved_at else "",
            str(error.retry_count)
        ]

        for col, item_text in enumerate(items):
            table_item = QTableWidgetItem(str(item_text))
            table_item.setData(Qt.UserRole, error)
            self.results_table.setItem(row, col, table_item)

    def _display_minimal_row(self, row: int, error):
        """显示最小视图行"""
        items = [
            error.error_id,
            error.error_message[:150] + "..." if len(error.error_message) > 150 else error.error_message,
            error.severity.value,
            error.created_at.strftime("%Y-%m-%d %H:%M:%S") if error.created_at else "",
            "已解决" if error.resolved else "未解决"
        ]

        for col, item_text in enumerate(items):
            table_item = QTableWidgetItem(str(item_text))
            table_item.setData(Qt.UserRole, error)
            self.results_table.setItem(row, col, table_item)

    def _update_pagination(self):
        """更新分页信息"""
        # 简单的分页实现
        total_records = len(self.current_errors)
        page_size = int(self.page_size_combo.currentText())

        if total_records == 0:
            self.page_info_label.setText("第 0 页 / 共 0 页")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return

        total_pages = (total_records + page_size - 1) // page_size
        current_page = 1  # 简化实现，始终显示第一页

        self.page_info_label.setText(f"第 {current_page} 页 / 共 {total_pages} 页")
        self.prev_btn.setEnabled(current_page > 1)
        self.next_btn.setEnabled(current_page < total_pages)

    def _on_table_selection_changed(self):
        """表格选择变化处理"""
        selected_rows = set()
        for item in self.results_table.selectedItems():
            selected_rows.add(item.row())

        if len(selected_rows) == 1:
            row = list(selected_rows)[0]
            error = self.results_table.item(row, 0).data(Qt.UserRole)

            # 转换为字典格式发送信号
            error_dict = {
                'error_id': error.error_id,
                'error_type': error.error_type,
                'error_message': error.error_message,
                'severity': error.severity.value,
                'category': error.category.value,
                'module': error.module,
                'function': error.function,
                'line_number': error.line_number,
                'stack_trace': error.stack_trace,
                'created_at': error.created_at.isoformat() if error.created_at else None,
                'resolved': error.resolved,
                'resolved_at': error.resolved_at.isoformat() if error.resolved_at else None,
                'resolution_method': error.resolution_method,
                'resolution_time': error.resolution_time,
                'retry_count': error.retry_count,
                'context': error.context,
                'user_context': error.user_context,
                'system_context': error.system_context
            }

            self.error_selected.emit(error_dict)
        else:
            self.error_selected.emit({})

    def _on_view_changed(self, _text: str):
        """视图切换处理"""
        self._setup_table_columns()
        if self.current_errors:
            self._display_results(self.current_errors)

    def _clear_filters(self):
        """清空过滤条件"""
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        self.end_date_edit.setDate(QDate.currentDate())
        self.severity_combo.setCurrentIndex(0)
        self.category_combo.setCurrentIndex(0)
        self.module_edit.clear()
        self.error_type_edit.clear()
        self.resolved_combo.setCurrentIndex(0)

    def _prev_page(self):
        """上一页"""
        # 简化实现
        pass

    def _next_page(self):
        """下一页"""
        # 简化实现
        pass

    def _on_page_size_changed(self):
        """页面大小变化处理"""
        # 重新执行查询以应用新的页面大小
        if self.current_errors:
            self._perform_query()

    def refresh_data(self):
        """刷新数据"""
        self._perform_query()

    def get_current_filters(self) -> Dict[str, Any]:
        """获取当前过滤条件（用于导出）"""
        return self._collect_filters()
