# error_history/ui/stats_panel.py
"""
错误历史持久化子系统 - 统计面板
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QGroupBox, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QFrame, QMessageBox, QDateEdit, QSplitter, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

from ..core.manager import ErrorHistoryManager


class StatsPanel(QWidget):
    """统计面板"""

    def __init__(self, manager: ErrorHistoryManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.current_stats = {}

        self._init_ui()
        self._setup_connections()
        self.refresh_data()

    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(10)
        try:
            content.setStyleSheet(
                "QLabel, QLineEdit, QComboBox, QDateEdit, QPushButton { font-size: 9pt; }"
                " QTableWidget, QHeaderView::section { font-size: 8pt; }"
            )
        except Exception:
            pass

        # 创建控制面板
        self._create_control_panel(content_layout)

        # 创建统计卡片
        self._create_stats_cards(content_layout)

        # 创建详细统计表格
        self._create_stats_table(content_layout)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _create_control_panel(self, parent_layout):
        """创建控制面板"""
        control_group = QGroupBox("统计控制")
        control_layout = QHBoxLayout(control_group)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(8)

        # 时间范围选择
        control_layout.addWidget(QLabel("时间范围:"))
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItem("今天", "today")
        self.time_range_combo.addItem("昨天", "yesterday")
        self.time_range_combo.addItem("最近7天", "7days")
        self.time_range_combo.addItem("最近30天", "30days")
        self.time_range_combo.addItem("全部", "all")
        self.time_range_combo.setCurrentText("最近7天")
        self.time_range_combo.setMinimumHeight(26)
        control_layout.addWidget(self.time_range_combo)

        # 自定义日期范围
        control_layout.addWidget(QLabel("或选择日期范围:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setMinimumHeight(26)
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setMinimumHeight(26)

        # 设置默认日期范围（最近7天）
        today = date.today()
        self.start_date_edit.setDate(today - timedelta(days=7))
        self.end_date_edit.setDate(today)

        control_layout.addWidget(self.start_date_edit)
        control_layout.addWidget(QLabel("至"))
        control_layout.addWidget(self.end_date_edit)

        # 刷新按钮
        self.refresh_btn = QPushButton("刷新统计(&R)")
        self.refresh_btn.setMinimumHeight(26)
        control_layout.addWidget(self.refresh_btn)

        control_layout.addStretch()

        parent_layout.addWidget(control_group)

    def _create_stats_cards(self, parent_layout):
        """创建统计卡片"""
        cards_group = QGroupBox("统计概览")
        cards_layout = QGridLayout(cards_group)
        cards_layout.setContentsMargins(6, 6, 6, 6)
        cards_layout.setHorizontalSpacing(6)
        cards_layout.setVerticalSpacing(4)

        # 创建统计卡片
        self.total_errors_card = self._create_stat_card("总错误数", "0", "#FF6384")
        self.resolved_errors_card = self._create_stat_card("已解决", "0", "#36A2EB")
        self.unresolved_errors_card = self._create_stat_card("未解决", "0", "#FFCE56")
        self.avg_resolution_time_card = self._create_stat_card("平均解决时间", "0分钟", "#4BC0C0")

        cards_layout.addWidget(self.total_errors_card, 0, 0)
        cards_layout.addWidget(self.resolved_errors_card, 0, 1)
        cards_layout.addWidget(self.unresolved_errors_card, 1, 0)
        cards_layout.addWidget(self.avg_resolution_time_card, 1, 1)

        parent_layout.addWidget(cards_group)

    def _create_stat_card(self, title: str, value: str, color: str) -> QGroupBox:
        """创建统计卡片"""
        card = QGroupBox()
        card.setFixedHeight(56)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(8, 4, 8, 4)

        # 单行：标题 + 值
        title_label = QLabel(f"{title}：")
        title_label.setFont(QFont("Arial", 8))
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 11, QFont.Bold))
        value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(value_label)

        # 存储数值标签引用
        card.value_label = value_label

        return card

    def _create_stats_table(self, parent_layout):
        """创建详细统计表格"""
        table_group = QGroupBox("详细统计")
        table_layout = QVBoxLayout(table_group)
        table_layout.setContentsMargins(10, 10, 10, 10)
        table_layout.setSpacing(8)

        # 创建表格
        self.stats_table = QTableWidget()
        self.stats_table.setAlternatingRowColors(True)
        self.stats_table.setColumnCount(4)
        self.stats_table.setHorizontalHeaderLabels([
            "统计项目", "数量", "百分比", "趋势"
        ])

        # 设置表格样式
        try:
            header = self.stats_table.horizontalHeader()
            header.setStretchLastSection(True)
            header.setSectionResizeMode(QHeaderView.Stretch)
            header.setMinimumSectionSize(30)
            header.setDefaultSectionSize(80)
        except Exception:
            pass
        self.stats_table.verticalHeader().setVisible(False)
        self.stats_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.stats_table.setMinimumHeight(110)
        self.stats_table.setMaximumHeight(130)
        self.stats_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        table_layout.addWidget(self.stats_table)

        parent_layout.addWidget(table_group)

    def _apply_auto_heights(self):
        try:
            win = self.window()
            if not win:
                return
            h = max(win.height(), 1)
            target = max(110, min(130, int(h * 0.11)))
            if hasattr(self, 'stats_table'):
                self.stats_table.setMinimumHeight(target)
                self.stats_table.setMaximumHeight(target)
        except Exception:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_auto_heights()

    def resizeEvent(self, event):
        self._apply_auto_heights()
        super().resizeEvent(event)
    def _setup_connections(self):
        """设置信号连接"""
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.time_range_combo.currentTextChanged.connect(self._on_time_range_changed)

    def _on_time_range_changed(self):
        """时间范围变化处理"""
        range_type = self.time_range_combo.currentData()

        if range_type == "custom":
            self.start_date_edit.setEnabled(True)
            self.end_date_edit.setEnabled(True)
        else:
            self.start_date_edit.setEnabled(False)
            self.end_date_edit.setEnabled(False)

        self.refresh_data()

    def refresh_data(self):
        """刷新统计数据"""
        try:
            # 获取时间范围
            date_range = self._get_date_range()

            # 获取统计数据
            stats = self.manager.get_statistics(date_range)

            if stats:
                self.current_stats = stats
                self._update_stats_display(stats)
                self._update_stats_table(stats)
            else:
                self._clear_stats_display()

        except Exception as e:
            QMessageBox.warning(self, "刷新失败",
                              f"刷新统计数据失败:\n{str(e)}")

    def _get_date_range(self) -> Optional[Tuple[date, date]]:
        """获取日期范围"""
        range_type = self.time_range_combo.currentData()
        today = date.today()

        if range_type == "today":
            return (today, today)
        elif range_type == "yesterday":
            yesterday = today - timedelta(days=1)
            return (yesterday, yesterday)
        elif range_type == "7days":
            return (today - timedelta(days=7), today)
        elif range_type == "30days":
            return (today - timedelta(days=30), today)
        elif range_type == "all":
            return None  # 全部数据
        else:
            # 自定义日期范围
            start_date = self.start_date_edit.date().toPyDate()
            end_date = self.end_date_edit.date().toPyDate()
            return (start_date, end_date)

    def _update_stats_display(self, stats: Dict[str, Any]):
        """更新统计卡片显示"""
        total_errors = stats.get('total_errors', 0)
        resolved_errors = stats.get('resolved_errors', 0)
        unresolved_errors = stats.get('unresolved_errors', 0)
        avg_resolution_time = stats.get('avg_resolution_time', 0)

        # 更新卡片数值
        self.total_errors_card.value_label.setText(str(total_errors))
        self.resolved_errors_card.value_label.setText(str(resolved_errors))
        self.unresolved_errors_card.value_label.setText(str(unresolved_errors))

        # 平均解决时间（转换为分钟）
        if avg_resolution_time:
            avg_minutes = avg_resolution_time / 60
            self.avg_resolution_time_card.value_label.setText(f"{avg_minutes:.1f}分钟")
        else:
            self.avg_resolution_time_card.value_label.setText("0分钟")

    def _update_stats_table(self, stats: Dict[str, Any]):
        """更新统计表格"""
        self.stats_table.setRowCount(0)  # 清空表格

        total_errors = stats.get('total_errors', 0)

        # 按严重程度统计
        severity_stats = stats.get('errors_by_severity', {})
        row = 0
        for severity, count in severity_stats.items():
            percentage = (count / total_errors * 100) if total_errors > 0 else 0
            self._add_stats_table_row(row, f"严重程度-{severity}", count, f"{percentage:.1f}%", "")
            row += 1

        # 按分类统计
        category_stats = stats.get('errors_by_category', {})
        for category, count in category_stats.items():
            percentage = (count / total_errors * 100) if total_errors > 0 else 0
            self._add_stats_table_row(row, f"分类-{category}", count, f"{percentage:.1f}%", "")
            row += 1

        # 按模块统计（前10个）
        module_stats = stats.get('errors_by_module', {})
        sorted_modules = sorted(module_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        for module, count in sorted_modules:
            percentage = (count / total_errors * 100) if total_errors > 0 else 0
            self._add_stats_table_row(row, f"模块-{module}", count, f"{percentage:.1f}%", "")
            row += 1

    def _add_stats_table_row(self, row: int, item: str, count: int, percentage: str, trend: str):
        """添加统计表格行"""
        self.stats_table.insertRow(row)

        # 项目名称
        item_item = QTableWidgetItem(item)
        self.stats_table.setItem(row, 0, item_item)

        # 数量
        count_item = QTableWidgetItem(str(count))
        count_item.setData(Qt.DisplayRole, count)  # 用于排序
        self.stats_table.setItem(row, 1, count_item)

        # 百分比
        percentage_item = QTableWidgetItem(percentage)
        self.stats_table.setItem(row, 2, percentage_item)

        # 趋势
        trend_item = QTableWidgetItem(trend)
        self.stats_table.setItem(row, 3, trend_item)

    def _clear_stats_display(self):
        """清空统计显示"""
        self.total_errors_card.value_label.setText("0")
        self.resolved_errors_card.value_label.setText("0")
        self.unresolved_errors_card.value_label.setText("0")
        self.avg_resolution_time_card.value_label.setText("0分钟")

        self.stats_table.setRowCount(0)

    def get_current_filters(self) -> Dict[str, Any]:
        """获取当前过滤条件（用于导出）"""
        date_range = self._get_date_range()
        return {
            'date_range': date_range,
            'time_range_type': self.time_range_combo.currentData()
        }
