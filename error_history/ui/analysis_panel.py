# error_history/ui/analysis_panel.py
"""
错误历史持久化子系统 - 分析面板
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QGroupBox, QComboBox, QPushButton,
    QTextEdit, QProgressBar, QSplitter, QFrame,
    QMessageBox, QTableWidget, QTableWidgetItem, QScrollArea, QHeaderView
)
from PyQt5.QtCore import Qt, QSettings, QByteArray
from PyQt5.QtGui import QFont, QColor
import builtins

from ..core.manager import ErrorHistoryManager


class AnalysisPanel(QWidget):
    """分析面板"""

    def __init__(self, manager: ErrorHistoryManager, parent=None):
        super().__init__(parent)
        self.manager = manager

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
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(8)
        try:
            content.setStyleSheet(
                "QLabel, QLineEdit, QComboBox, QDateEdit, QPushButton { font-size: 9pt; }"
                " QTableWidget, QHeaderView::section { font-size: 8pt; }"
            )
        except Exception:
            pass

        self._create_control_panel(content_layout)
        self._create_analysis_display(content_layout)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _create_control_panel(self, parent_layout):
        """创建控制面板"""
        control_group = QGroupBox("分析控制")
        control_layout = QHBoxLayout(control_group)
        control_layout.setContentsMargins(12, 12, 12, 12)
        control_layout.setSpacing(10)

        # 分析类型选择
        control_layout.addWidget(QLabel("分析类型:"))
        self.analysis_type_combo = QComboBox()
        self.analysis_type_combo.addItem("错误模式识别", "pattern")
        self.analysis_type_combo.addItem("根本原因分析", "root_cause")
        self.analysis_type_combo.addItem("趋势分析", "trend")
        self.analysis_type_combo.addItem("影响评估", "impact")
        self.analysis_type_combo.setMinimumHeight(26)
        control_layout.addWidget(self.analysis_type_combo)

        # 时间范围选择
        control_layout.addWidget(QLabel("时间范围:"))
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItem("最近7天", "7days")
        self.time_range_combo.addItem("最近30天", "30days")
        self.time_range_combo.addItem("最近90天", "90days")
        self.time_range_combo.setCurrentText("最近30天")
        self.time_range_combo.setMinimumHeight(26)
        control_layout.addWidget(self.time_range_combo)

        # 分析按钮
        self.analyze_btn = QPushButton("开始分析(&A)")
        self.analyze_btn.setMinimumHeight(26)
        control_layout.addWidget(self.analyze_btn)

        # 导出按钮
        self.export_btn = QPushButton("导出报告(&E)")
        self.export_btn.setMinimumHeight(26)
        control_layout.addWidget(self.export_btn)

        control_layout.addStretch()

        parent_layout.addWidget(control_group)

    def _create_analysis_display(self, parent_layout):
        """创建分析结果显示区域"""
        splitter = QSplitter(Qt.Vertical)

        # 分析结果文本显示
        results_group = QGroupBox("分析结果")
        results_layout = QVBoxLayout(results_group)
        results_layout.setContentsMargins(10, 10, 10, 10)
        results_layout.setSpacing(8)

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Consolas", 9))
        self.results_text.setMinimumHeight(110)
        self.results_text.setMaximumHeight(130)
        results_layout.addWidget(self.results_text)

        splitter.addWidget(results_group)

        # 详细数据表格
        details_group = QGroupBox("详细数据")
        details_layout = QVBoxLayout(details_group)
        details_layout.setContentsMargins(10, 10, 10, 10)
        details_layout.setSpacing(8)

        self.details_table = QTableWidget()
        self.details_table.setAlternatingRowColors(True)
        self.details_table.setColumnCount(3)
        self.details_table.setHorizontalHeaderLabels([
            "项目", "数值", "说明"
        ])
        self.details_table.setMinimumHeight(110)
        self.details_table.setMaximumHeight(130)

        # 设置表格样式
        try:
            header = self.details_table.horizontalHeader()
            header.setStretchLastSection(True)
            header.setSectionResizeMode(QHeaderView.Stretch)
            header.setMinimumSectionSize(30)
            header.setDefaultSectionSize(80)
        except Exception:
            pass
        self.details_table.verticalHeader().setVisible(False)
        self.details_table.setEditTriggers(QTableWidget.NoEditTriggers)

        details_layout.addWidget(self.details_table)

        splitter.addWidget(details_group)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(6)

        # 设置分割器默认比例（若无历史状态，将在 showEvent 中应用）
        splitter.setSizes([200, 200])

        # 记录并接入持久化
        self.analysis_splitter = splitter
        try:
            self._in_splitter_adjust = False
            self._split_min = 110
            self._split_max = 130
            self._last_valid_sizes = None
            self.analysis_splitter.splitterMoved.connect(self._on_splitter_moved)
        except Exception:
            pass

        parent_layout.addWidget(splitter)

    def _apply_auto_heights(self):
        # 为支持用户拖动分割器，这里不再强制设置子部件高度
        pass

    def showEvent(self, event):
        super().showEvent(event)
        # 恢复分割器状态（仅一次）
        try:
            if not getattr(self, "_analysis_splitter_initialized", False) and hasattr(self, 'analysis_splitter'):
                settings = QSettings("LAD", "ErrorHistoryUI")
                state = settings.value("analysis_splitter_v")
                if state:
                    self.analysis_splitter.restoreState(state if isinstance(state, QByteArray) else QByteArray(state))
                else:
                    # 无历史状态时，按窗口高度 11%（夹 110–130）设定默认上下区域高度
                    try:
                        win = self.window()
                        h = max(win.height(), 1) if win else 0
                        target = max(110, min(130, int(h * 0.11)))
                        if target <= 0:
                            target = 120
                        self.analysis_splitter.setSizes([target, target])
                    except Exception:
                        self.analysis_splitter.setSizes([120, 120])
                self._analysis_splitter_initialized = True
        except Exception:
            pass
        # 记录初始有效尺寸
        try:
            if hasattr(self, 'analysis_splitter'):
                self._last_valid_sizes = list(self.analysis_splitter.sizes())
        except Exception:
            pass
        self._apply_auto_heights()

    def _save_analysis_splitter_state(self):
        try:
            if hasattr(self, 'analysis_splitter'):
                settings = QSettings("LAD", "ErrorHistoryUI")
                settings.setValue("analysis_splitter_v", self.analysis_splitter.saveState())
        except Exception:
            pass

    def _on_splitter_moved(self, pos, index):
        if getattr(self, '_in_splitter_adjust', False):
            return
        try:
            sizes = self.analysis_splitter.sizes()
            if len(sizes) < 2:
                return
            top, bottom = sizes[0], sizes[1]
            # 检查是否超界
            if not (self._split_min <= top <= self._split_max) or not (self._split_min <= bottom <= self._split_max):
                # 回退到上一次有效尺寸
                self._in_splitter_adjust = True
                if self._last_valid_sizes:
                    self.analysis_splitter.setSizes(self._last_valid_sizes)
                else:
                    self.analysis_splitter.setSizes([self._split_min, self._split_min])
                return
            # 合法则记录并持久化
            self._last_valid_sizes = list(sizes)
            self._save_analysis_splitter_state()
        finally:
            self._in_splitter_adjust = False

    def _enforce_splitter_bounds(self):
        try:
            if not hasattr(self, 'analysis_splitter'):
                return
            sizes = self.analysis_splitter.sizes()
            if len(sizes) < 2:
                return
            top, bottom = sizes[0], sizes[1]
            if not (self._split_min <= top <= self._split_max) or not (self._split_min <= bottom <= self._split_max):
                self._in_splitter_adjust = True
                if self._last_valid_sizes:
                    self.analysis_splitter.setSizes(self._last_valid_sizes)
                else:
                    self.analysis_splitter.setSizes([self._split_min, self._split_min])
            else:
                self._last_valid_sizes = list(sizes)
        finally:
            self._in_splitter_adjust = False

    def resizeEvent(self, event):
        self._enforce_splitter_bounds()
        self._apply_auto_heights()
        super().resizeEvent(event)

    def _setup_connections(self):
        """设置信号连接"""
        self.analyze_btn.clicked.connect(self._perform_analysis)
        self.export_btn.clicked.connect(self._export_analysis)

    def refresh_data(self):
        """刷新数据"""
        # 执行默认分析
        self._perform_analysis()

    def _perform_analysis(self):
        """执行分析"""
        try:
            analysis_type = self.analysis_type_combo.currentData()
            time_range = self.time_range_combo.currentData()

            # 获取日期范围
            date_range = self._get_date_range(time_range)

            # 执行相应分析
            if analysis_type == "pattern":
                self._analyze_patterns(date_range)
            elif analysis_type == "root_cause":
                self._analyze_root_causes(date_range)
            elif analysis_type == "trend":
                self._analyze_trends(date_range)
            elif analysis_type == "impact":
                self._analyze_impact(date_range)

        except Exception as e:
            QMessageBox.warning(self, "分析失败",
                              f"执行分析失败:\n{str(e)}")

    def _get_date_range(self, time_range: str) -> Tuple[date, date]:
        """获取日期范围"""
        today = date.today()

        if time_range == "7days":
            return (today - timedelta(days=7), today)
        elif time_range == "30days":
            return (today - timedelta(days=30), today)
        elif time_range == "90days":
            return (today - timedelta(days=90), today)
        else:
            return (today - timedelta(days=30), today)

    def _analyze_patterns(self, date_range: Tuple[date, date]):
        """分析错误模式"""
        try:
            # 获取统计数据
            stats = self.manager.get_statistics(date_range)

            if not stats:
                self.results_text.setPlainText("暂无数据进行模式分析")
                return

            # 生成分析报告
            report_lines = []
            report_lines.append("=== 错误模式识别分析报告 ===")
            report_lines.append(f"分析时间范围: {date_range[0]} 至 {date_range[1]}")
            report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append("")

            # 总错误数
            total_errors = stats.get('total_errors', 0)
            report_lines.append(f"📊 总错误数: {total_errors}")

            # 解决率分析
            resolved = stats.get('resolved_errors', 0)
            unresolved = stats.get('unresolved_errors', 0)
            if total_errors > 0:
                resolve_rate = resolved / total_errors * 100
                report_lines.append(f"✅ 解决率: {resolve_rate:.1f}% ({resolved}/{total_errors})")
                report_lines.append(f"❌ 未解决数: {unresolved}")
            report_lines.append("")

            # 严重程度分布
            severity_stats = stats.get('errors_by_severity', {})
            if severity_stats:
                report_lines.append("🔥 严重程度分布:")
                sorted_severity = sorted(severity_stats.items(), key=lambda x: x[1], reverse=True)
                for severity, count in sorted_severity:
                    percentage = count / total_errors * 100 if total_errors > 0 else 0
                    report_lines.append(f"  • {severity}: {count} ({percentage:.1f}%)")
                report_lines.append("")

            # 分类分布
            category_stats = stats.get('errors_by_category', {})
            if category_stats:
                report_lines.append("📂 错误分类分布:")
                sorted_category = sorted(category_stats.items(), key=lambda x: x[1], reverse=True)
                for category, count in sorted_category[:10]:  # 前10个
                    percentage = count / total_errors * 100 if total_errors > 0 else 0
                    report_lines.append(f"  • {category}: {count} ({percentage:.1f}%)")
                report_lines.append("")

            # 模块分析
            module_stats = stats.get('errors_by_module', {})
            if module_stats:
                report_lines.append("🏗️ 高频错误模块:")
                sorted_modules = sorted(module_stats.items(), key=lambda x: x[1], reverse=True)
                for module, count in sorted_modules[:10]:  # 前10个
                    percentage = count / total_errors * 100 if total_errors > 0 else 0
                    report_lines.append(f"  • {module}: {count} ({percentage:.1f}%)")
                report_lines.append("")

            # 模式识别
            report_lines.append("🎯 识别的错误模式:")
            if total_errors == 0:
                report_lines.append("  • 暂无错误数据")
            else:
                # 简单模式识别逻辑
                patterns = self._identify_patterns(stats)
                for pattern in patterns:
                    report_lines.append(f"  • {pattern}")

            # 显示结果
            self.results_text.setPlainText("\n".join(report_lines))

            # 更新详细表格
            self._update_details_table(stats)

        except Exception as e:
            self.results_text.setPlainText(f"分析过程中发生错误:\n{str(e)}")

    def _identify_patterns(self, stats: Dict[str, Any]) -> List[str]:
        """识别错误模式"""
        patterns = []

        total_errors = stats.get('total_errors', 0)
        if total_errors == 0:
            return ["暂无错误数据"]

        # 检查是否有某个严重程度占比过高
        severity_stats = stats.get('errors_by_severity', {})
        for severity, count in severity_stats.items():
            percentage = count / total_errors * 100
            if percentage > 50:
                patterns.append(f"错误主要集中在{severity}级别 ({percentage:.1f}%)")

        # 检查是否有某个分类占比过高
        category_stats = stats.get('errors_by_category', {})
        for category, count in category_stats.items():
            percentage = count / total_errors * 100
            if percentage > 30:
                patterns.append(f"{category}类错误占比较高 ({percentage:.1f}%)")

        # 检查未解决错误比例
        unresolved = stats.get('unresolved_errors', 0)
        if total_errors > 0:
            unresolved_rate = unresolved / total_errors * 100
            if unresolved_rate > 50:
                patterns.append(f"未解决错误比例较高 ({unresolved_rate:.1f}%)")

        if not patterns:
            patterns.append("错误分布相对均衡，无明显集中模式")

        return patterns

    def _analyze_root_causes(self, date_range: Tuple[date, date]):
        """根本原因分析"""
        report_lines = []
        report_lines.append("=== 根本原因分析报告 ===")
        report_lines.append(f"分析时间范围: {date_range[0]} 至 {date_range[1]}")
        report_lines.append("")

        # 这里可以实现更复杂的根本原因分析逻辑
        report_lines.append("🔍 根本原因分析:")
        report_lines.append("  • 基于堆栈跟踪分析")
        report_lines.append("  • 基于错误消息模式识别")
        report_lines.append("  • 基于时间分布分析")
        report_lines.append("")
        report_lines.append("⚠️ 此功能正在开发中")

        self.results_text.setPlainText("\n".join(report_lines))

    def _analyze_trends(self, date_range: Tuple[date, date]):
        """趋势分析"""
        report_lines = []
        report_lines.append("=== 错误趋势分析报告 ===")
        report_lines.append(f"分析时间范围: {date_range[0]} 至 {date_range[1]}")
        report_lines.append("")

        # 这里可以实现趋势分析逻辑
        report_lines.append("📈 趋势分析:")
        report_lines.append("  • 每日错误数量趋势")
        report_lines.append("  • 错误类型变化趋势")
        report_lines.append("  • 解决效率趋势")
        report_lines.append("")
        report_lines.append("⚠️ 此功能正在开发中")

        self.results_text.setPlainText("\n".join(report_lines))

    def _analyze_impact(self, date_range: Tuple[date, date]):
        """影响评估"""
        report_lines = []
        report_lines.append("=== 错误影响评估报告 ===")
        report_lines.append(f"分析时间范围: {date_range[0]} 至 {date_range[1]}")
        report_lines.append("")

        # 这里可以实现影响评估逻辑
        report_lines.append("⚡ 影响评估:")
        report_lines.append("  • 系统稳定性影响")
        report_lines.append("  • 用户体验影响")
        report_lines.append("  • 业务连续性影响")
        report_lines.append("")
        report_lines.append("⚠️ 此功能正在开发中")

        self.results_text.setPlainText("\n".join(report_lines))

    def _update_details_table(self, stats: Dict[str, Any]):
        """更新详细数据表格"""
        self.details_table.setRowCount(0)  # 清空表格

        # 添加统计数据
        data_items = [
            ("总错误数", stats.get('total_errors', 0), "时间范围内的错误总数"),
            ("已解决错误", stats.get('resolved_errors', 0), "已标记为解决的错误数"),
            ("未解决错误", stats.get('unresolved_errors', 0), "尚未解决的错误数"),
            ("平均解决时间", f"{stats.get('avg_resolution_time') or 0:.1f}秒", "平均错误解决耗时"),
            ("每小时错误率", f"{stats.get('error_rate_per_hour', 0):.2f}", "平均每小时错误发生率")
        ]

        for item, value, description in data_items:
            row = self.details_table.rowCount()
            self.details_table.insertRow(row)

            self.details_table.setItem(row, 0, QTableWidgetItem(item))
            self.details_table.setItem(row, 1, QTableWidgetItem(str(value)))
            self.details_table.setItem(row, 2, QTableWidgetItem(description))

    def _export_analysis(self):
        """导出分析报告"""
        try:
            from PyQt5.QtWidgets import QFileDialog

            filename, _ = QFileDialog.getSaveFileName(
                self, "导出分析报告",
                f"error_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "文本文件 (*.txt);;所有文件 (*)"
            )

            if filename:
                with builtins.open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.results_text.toPlainText())

                QMessageBox.information(self, "导出成功",
                                      f"分析报告已保存到:\n{filename}")

        except Exception as e:
            QMessageBox.critical(self, "导出失败",
                               f"导出分析报告失败:\n{str(e)}")

    def get_current_filters(self) -> Dict[str, Any]:
        """获取当前过滤条件（用于导出）"""
        return {
            'analysis_type': self.analysis_type_combo.currentData(),
            'time_range': self.time_range_combo.currentData()
        }
