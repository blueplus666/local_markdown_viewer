# error_history/ui/management_panel.py
"""
错误历史持久化子系统 - 管理面板
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QGroupBox, QPushButton, QTextEdit,
    QProgressBar, QFrame, QMessageBox, QCheckBox,
    QSpinBox, QLineEdit, QFileDialog, QComboBox,
    QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt

from ..core.manager import ErrorHistoryManager


class ManagementPanel(QWidget):
    """管理面板"""

    def __init__(self, manager: ErrorHistoryManager, parent=None):
        super().__init__(parent)
        self.manager = manager

        self._init_ui()
        self._setup_connections()
        self._load_current_config()

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
            content.setStyleSheet("QLabel, QLineEdit, QComboBox, QDateEdit, QPushButton, QTableWidget, QCheckBox, QSpinBox { font-size: 9pt; } QHeaderView::section { font-size: 8pt; }")
        except Exception:
            pass

        self._create_config_section(content_layout)
        self._create_database_section(content_layout)
        self._create_data_section(content_layout)
        self._create_status_section(content_layout)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _create_config_section(self, parent_layout):
        """创建配置管理区域"""
        config_group = QGroupBox("配置管理")
        config_layout = QGridLayout(config_group)
        config_layout.setContentsMargins(10, 10, 10, 10)
        config_layout.setHorizontalSpacing(10)
        config_layout.setVerticalSpacing(6)
        config_layout.setColumnStretch(1, 1)

        # 数据库路径
        config_layout.addWidget(QLabel("数据库路径:"), 0, 0)
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setMinimumHeight(26)
        self.db_path_edit.setMinimumWidth(260)
        self.db_path_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        config_layout.addWidget(self.db_path_edit, 0, 1)
        self.db_path_btn = QPushButton("浏览...")
        config_layout.addWidget(self.db_path_btn, 0, 2)

        # 保留天数
        config_layout.addWidget(QLabel("数据保留天数:"), 1, 0)
        self.retention_days_spin = QSpinBox()
        self.retention_days_spin.setRange(1, 3650)
        self.retention_days_spin.setValue(90)
        self.retention_days_spin.setMinimumHeight(26)
        self.retention_days_spin.setMaximumWidth(90)
        self.retention_days_spin.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        config_layout.addWidget(self.retention_days_spin, 1, 1)

        # 自动清理
        self.auto_cleanup_check = QCheckBox("启用自动清理")
        self.auto_cleanup_check.setChecked(True)
        config_layout.addWidget(self.auto_cleanup_check, 1, 2)

        # 最大连接数
        config_layout.addWidget(QLabel("最大连接数:"), 2, 0)
        self.max_connections_spin = QSpinBox()
        self.max_connections_spin.setRange(1, 20)
        self.max_connections_spin.setValue(5)
        self.max_connections_spin.setMinimumHeight(26)
        self.max_connections_spin.setMaximumWidth(90)
        self.max_connections_spin.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        config_layout.addWidget(self.max_connections_spin, 2, 1)

        # 配置操作按钮（与最大连接数同一行，右侧）
        actions_layout = QHBoxLayout()
        self.save_config_btn = QPushButton("保存配置")
        self.reset_config_btn = QPushButton("重置配置")
        actions_layout.addWidget(self.save_config_btn)
        actions_layout.addWidget(self.reset_config_btn)
        actions_layout.addStretch()

        config_layout.addLayout(actions_layout, 2, 2)

        parent_layout.addWidget(config_group)

    def _create_database_section(self, parent_layout):
        """创建数据库管理区域"""
        db_group = QGroupBox("数据库管理")
        db_layout = QVBoxLayout(db_group)
        db_layout.setContentsMargins(10, 10, 10, 10)
        db_layout.setSpacing(8)

        # 数据库操作按钮
        db_btn_layout = QHBoxLayout()

        self.optimize_db_btn = QPushButton("优化数据库")
        db_btn_layout.addWidget(self.optimize_db_btn)

        self.backup_db_btn = QPushButton("备份数据库")
        db_btn_layout.addWidget(self.backup_db_btn)

        self.cleanup_old_btn = QPushButton("清理过期数据")
        db_btn_layout.addWidget(self.cleanup_old_btn)

        db_btn_layout.addStretch()
        db_layout.addLayout(db_btn_layout)

        # 数据库信息显示
        info_layout = QHBoxLayout()

        self.db_info_text = QTextEdit()
        self.db_info_text.setReadOnly(True)
        self.db_info_text.setMaximumHeight(100)
        info_layout.addWidget(self.db_info_text)

        db_layout.addLayout(info_layout)

        # 刷新信息按钮
        refresh_info_btn = QPushButton("刷新信息")
        refresh_info_btn.clicked.connect(self._refresh_db_info)
        db_layout.addWidget(refresh_info_btn)

        parent_layout.addWidget(db_group)

    def _create_data_section(self, parent_layout):
        """创建数据管理区域"""
        data_group = QGroupBox("数据管理")
        data_layout = QVBoxLayout(data_group)
        data_layout.setContentsMargins(10, 10, 10, 10)
        data_layout.setSpacing(8)

        # 数据操作按钮
        data_btn_layout = QHBoxLayout()

        # 导出格式（移动到与导出按钮同一行，放在其左侧）
        data_btn_layout.addWidget(QLabel("导出格式:"))
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItem("JSON", "json")
        self.export_format_combo.addItem("CSV", "csv")
        self.export_format_combo.addItem("Excel", "xlsx")
        self.export_format_combo.setMinimumHeight(26)
        data_btn_layout.addWidget(self.export_format_combo)

        self.export_data_btn = QPushButton("导出数据")
        data_btn_layout.addWidget(self.export_data_btn)

        self.import_data_btn = QPushButton("导入数据")
        self.import_data_btn.setEnabled(False)  # 暂不支持
        data_btn_layout.addWidget(self.import_data_btn)

        self.clear_all_btn = QPushButton("清空所有数据")
        self.clear_all_btn.setStyleSheet("QPushButton { color: red; }")
        data_btn_layout.addWidget(self.clear_all_btn)

        data_btn_layout.addStretch()
        data_layout.addLayout(data_btn_layout)

        # 取消单独的导出格式行，已移至按钮行

        parent_layout.addWidget(data_group)

    def _create_status_section(self, parent_layout):
        """创建状态显示区域"""
        status_group = QGroupBox("系统状态")
        status_layout = QVBoxLayout(status_group)
        status_layout.setContentsMargins(10, 10, 10, 10)
        status_layout.setSpacing(8)

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMinimumHeight(110)
        status_layout.addWidget(self.status_text)

        # 调度控制按钮
        btn_row = QHBoxLayout()
        self.trigger_cleanup_btn = QPushButton("立即清理")
        self.restart_scheduler_btn = QPushButton("重启调度器")
        self.refresh_status_btn = QPushButton("刷新状态")
        btn_row.addWidget(self.trigger_cleanup_btn)
        btn_row.addWidget(self.restart_scheduler_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.refresh_status_btn)
        status_layout.addLayout(btn_row)

        parent_layout.addWidget(status_group)

    def _setup_connections(self):
        """设置信号连接"""
        # 配置管理
        self.db_path_btn.clicked.connect(self._browse_db_path)
        self.save_config_btn.clicked.connect(self._save_config)
        self.reset_config_btn.clicked.connect(self._reset_config)

        # 数据库管理
        self.optimize_db_btn.clicked.connect(self._optimize_database)
        self.backup_db_btn.clicked.connect(self._backup_database)
        self.cleanup_old_btn.clicked.connect(self._cleanup_old_data)

        # 数据管理
        self.export_data_btn.clicked.connect(self._export_data)
        self.clear_all_btn.clicked.connect(self._clear_all_data)
        # 状态/调度管理
        self.refresh_status_btn.clicked.connect(self._refresh_system_status)
        self.trigger_cleanup_btn.clicked.connect(self._trigger_cleanup_now)
        self.restart_scheduler_btn.clicked.connect(self._restart_scheduler)

    def _load_current_config(self):
        """加载当前配置"""
        try:
            if self.manager.config:
                config = self.manager.config
                self.db_path_edit.setText(str(config.database_path))
                self.retention_days_spin.setValue(config.retention_days)
                self.auto_cleanup_check.setChecked(config.auto_cleanup)
                self.max_connections_spin.setValue(config.max_connections)

            self._refresh_db_info()
            self._refresh_system_status()

        except Exception as e:
            QMessageBox.warning(self, "配置加载失败",
                              f"加载配置失败:\n{str(e)}")

    def _browse_db_path(self):
        """浏览数据库路径"""
        try:
            current_path = self.db_path_edit.text() or "data/error_history.db"
            filename, _ = QFileDialog.getSaveFileName(
                self, "选择数据库文件",
                current_path,
                "SQLite数据库 (*.db);;所有文件 (*)"
            )

            if filename:
                self.db_path_edit.setText(filename)

        except Exception as e:
            QMessageBox.warning(self, "路径选择失败",
                              f"选择数据库路径失败:\n{str(e)}")

    def _save_config(self):
        """保存配置"""
        try:
            if not self.manager or not hasattr(self.manager, 'config'):
                QMessageBox.warning(self, "配置保存失败", "管理器不可用，无法保存配置")
                return

            cfg = self.manager.config

            # 从UI读取并写回配置对象
            db_path = self.db_path_edit.text().strip() or "data/error_history.db"
            cfg.database_path = db_path
            cfg.retention_days = int(self.retention_days_spin.value())
            cfg.auto_cleanup = bool(self.auto_cleanup_check.isChecked())
            cfg.max_connections = int(self.max_connections_spin.value())

            # 尝试持久化到数据库，并应用运行期参数
            ok = False
            if hasattr(self.manager, 'save_config'):
                ok = self.manager.save_config()

            if ok:
                # 刷新信息展示
                self._refresh_db_info()
                self._refresh_system_status()
                QMessageBox.information(self, "配置保存", "配置已保存并应用。\n\n注意：数据库路径等部分配置可能需要重启子系统才能完全生效。")
            else:
                QMessageBox.warning(self, "配置保存失败", "无法写入持久化存储，请稍后重试。")

        except Exception as e:
            QMessageBox.critical(self, "配置保存失败",
                               f"保存配置失败:\n{str(e)}")

    def _reset_config(self):
        """重置配置"""
        reply = QMessageBox.question(
            self, "确认重置",
            "确定要重置所有配置为默认值吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # 重置为默认值
                self.db_path_edit.setText("data/error_history.db")
                self.retention_days_spin.setValue(90)
                self.auto_cleanup_check.setChecked(True)
                self.max_connections_spin.setValue(5)

                QMessageBox.information(self, "重置完成", "配置已重置为默认值")

                # 询问是否持久化保存
                persist = QMessageBox.question(
                    self, "保存配置",
                    "是否将当前默认值保存为永久配置？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if persist == QMessageBox.Yes:
                    try:
                        if self.manager and hasattr(self.manager, 'config'):
                            cfg = self.manager.config
                            cfg.database_path = self.db_path_edit.text().strip() or "data/error_history.db"
                            cfg.retention_days = int(self.retention_days_spin.value())
                            cfg.auto_cleanup = bool(self.auto_cleanup_check.isChecked())
                            cfg.max_connections = int(self.max_connections_spin.value())
                            if hasattr(self.manager, 'save_config') and self.manager.save_config():
                                self._refresh_db_info()
                                self._refresh_system_status()
                                QMessageBox.information(self, "保存成功", "默认配置已保存并应用")
                            else:
                                QMessageBox.warning(self, "保存失败", "无法将默认配置写入持久化存储")
                    except Exception as se:
                        QMessageBox.warning(self, "保存失败", f"保存默认配置失败:\n{str(se)}")

            except Exception as e:
                QMessageBox.critical(self, "重置失败",
                                   f"重置配置失败:\n{str(e)}")

    def _optimize_database(self):
        """优化数据库"""
        try:
            self.optimize_db_btn.setEnabled(False)
            self.optimize_db_btn.setText("优化中...")

            success = self.manager.optimize_database()

            if success:
                QMessageBox.information(self, "优化完成", "数据库优化完成")
                self._refresh_db_info()
            else:
                QMessageBox.warning(self, "优化失败", "数据库优化失败")

        except Exception as e:
            QMessageBox.critical(self, "优化失败",
                               f"数据库优化失败:\n{str(e)}")

        finally:
            self.optimize_db_btn.setEnabled(True)
            self.optimize_db_btn.setText("优化数据库")

    def _backup_database(self):
        """备份数据库"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "备份数据库",
                f"error_history_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
                "SQLite数据库 (*.db);;所有文件 (*)"
            )

            if filename:
                success = self.manager.backup_database(filename)

                if success:
                    QMessageBox.information(self, "备份完成",
                                          f"数据库已备份到:\n{filename}")
                else:
                    QMessageBox.warning(self, "备份失败", "数据库备份失败")

        except Exception as e:
            QMessageBox.critical(self, "备份失败",
                               f"数据库备份失败:\n{str(e)}")

    def _cleanup_old_data(self):
        """清理过期数据"""
        try:
            days = self.retention_days_spin.value()

            reply = QMessageBox.question(
                self, "确认清理",
                f"确定要清理 {days} 天前的错误数据吗？\n此操作不可撤销。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.cleanup_old_btn.setEnabled(False)
                self.cleanup_old_btn.setText("清理中...")

                deleted_count = self.manager.cleanup_old_errors(days)

                QMessageBox.information(self, "清理完成",
                                      f"已清理 {deleted_count} 条过期错误记录")

                self._refresh_db_info()
                self._refresh_system_status()

        except Exception as e:
            QMessageBox.critical(self, "清理失败",
                               f"清理过期数据失败:\n{str(e)}")

        finally:
            self.cleanup_old_btn.setEnabled(True)
            self.cleanup_old_btn.setText("清理过期数据")

    def _export_data(self):
        """导出数据"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "导出错误历史数据",
                f"error_history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "JSON (*.json);;CSV (*.csv);;Excel (*.xlsx);;所有文件 (*)"
            )

            if filename:
                format_type = self.export_format_combo.currentData()

                # 这里可以传递一些过滤条件
                filters = {}

                success = self.manager.export_data(filename, format_type, filters)

                if success:
                    QMessageBox.information(self, "导出完成",
                                          f"数据已导出到:\n{filename}")
                else:
                    QMessageBox.warning(self, "导出失败", "数据导出失败")

        except Exception as e:
            QMessageBox.critical(self, "导出失败",
                               f"数据导出失败:\n{str(e)}")

    def _clear_all_data(self):
        """清空所有数据"""
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有错误历史数据吗？\n此操作不可撤销！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 二次确认
            reply2 = QMessageBox.question(
                self, "再次确认",
                "这将永久删除所有错误历史数据！\n确定继续吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply2 == QMessageBox.Yes:
                try:
                    # 这里需要实现清空所有数据的功能
                    # 注意：这应该是一个非常谨慎的操作
                    QMessageBox.warning(self, "功能未实现",
                                      "清空所有数据的功能尚未实现，\n请手动删除数据库文件。")

                except Exception as e:
                    QMessageBox.critical(self, "清空失败",
                                       f"清空数据失败:\n{str(e)}")

    def _refresh_db_info(self):
        """刷新数据库信息"""
        try:
            db_info = self.manager.get_database_info()

            if db_info:
                info_lines = []
                info_lines.append("数据库信息:")
                info_lines.append(f"  路径: {db_info.get('database_path', '未知')}")
                info_lines.append(f"  大小: {db_info.get('database_size', 0)} 字节")

                tables = db_info.get('table_counts', {})
                if tables:
                    info_lines.append("  表记录数:")
                    for table, count in tables.items():
                        info_lines.append(f"    {table}: {count}")

                info_lines.append(f"  连接池大小: {db_info.get('connection_pool_size', 0)}")

                self.db_info_text.setPlainText("\n".join(info_lines))
            else:
                self.db_info_text.setPlainText("无法获取数据库信息")

        except Exception as e:
            self.db_info_text.setPlainText(f"获取数据库信息失败:\n{str(e)}")

    def _refresh_system_status(self):
        """刷新系统状态"""
        try:
            stats = self.manager.get_statistics()

            if stats:
                status_lines = []
                status_lines.append("系统状态:")
                status_lines.append(f"  总错误数: {stats.get('total_errors', 0)}")
                status_lines.append(f"  已解决: {stats.get('resolved_errors', 0)}")
                status_lines.append(f"  未解决: {stats.get('unresolved_errors', 0)}")
                status_lines.append(f"  错误率: {stats.get('error_rate_per_hour', 0):.2f}/小时")

                if stats.get('avg_resolution_time'):
                    status_lines.append(f"  平均解决时间: {stats.get('avg_resolution_time'):.1f}秒")

                # 严重程度分布
                severity_stats = stats.get('errors_by_severity', {})
                if severity_stats:
                    status_lines.append("  严重程度分布:")
                    for severity, count in sorted(severity_stats.items(), key=lambda x: x[1], reverse=True):
                        status_lines.append(f"    {severity}: {count}")

                # 自动清理调度状态
                try:
                    if hasattr(self.manager, 'get_cleanup_status'):
                        cs = self.manager.get_cleanup_status() or {}
                        status_lines.append("  自动清理:")
                        status_lines.append(f"    启用: {'是' if cs.get('enabled') else '否'}")
                        status_lines.append(f"    运行中: {'是' if cs.get('running') else '否'}")
                        status_lines.append(f"    计划: {cs.get('schedule') or '-'} ({cs.get('mode')})")
                        status_lines.append(f"    上次执行: {cs.get('last_run') or '-'}")
                        status_lines.append(f"    下次执行: {cs.get('next_run') or '-'}")
                except Exception:
                    pass

                self.status_text.setPlainText("\n".join(status_lines))
            else:
                self.status_text.setPlainText("无法获取系统状态信息")

        except Exception as e:
            self.status_text.setPlainText(f"获取系统状态失败:\n{str(e)}")

    def _trigger_cleanup_now(self):
        """立即执行清理任务"""
        try:
            self.trigger_cleanup_btn.setEnabled(False)
            self.trigger_cleanup_btn.setText("执行中...")
            deleted = 0
            if hasattr(self.manager, 'trigger_cleanup_now'):
                deleted = int(self.manager.trigger_cleanup_now())
            QMessageBox.information(self, "立即清理", f"已清理 {deleted} 条过期错误记录")
            self._refresh_db_info()
            self._refresh_system_status()
        except Exception as e:
            QMessageBox.critical(self, "立即清理失败", f"执行立即清理失败:\n{str(e)}")
        finally:
            self.trigger_cleanup_btn.setEnabled(True)
            self.trigger_cleanup_btn.setText("立即清理")

    def _restart_scheduler(self):
        """重启自动清理调度器"""
        try:
            self.restart_scheduler_btn.setEnabled(False)
            self.restart_scheduler_btn.setText("重启中...")
            ok = False
            if hasattr(self.manager, 'restart_scheduler'):
                ok = bool(self.manager.restart_scheduler())
            if ok:
                QMessageBox.information(self, "调度器", "自动清理调度器已重启")
            else:
                QMessageBox.warning(self, "调度器", "调度器未启动（可能未启用自动清理）")
            self._refresh_system_status()
        except Exception as e:
            QMessageBox.critical(self, "调度器失败", f"重启失败:\n{str(e)}")
        finally:
            self.restart_scheduler_btn.setEnabled(True)
            self.restart_scheduler_btn.setText("重启调度器")

    def refresh_data(self):
        """刷新数据"""
        self._refresh_db_info()
        self._refresh_system_status()

    def _apply_auto_heights(self):
        try:
            win = self.window()
            if not win:
                return
            h = max(win.height(), 1)
            target = max(110, min(130, int(h * 0.11)))
            if hasattr(self, 'status_text'):
                self.status_text.setMinimumHeight(target)
                self.status_text.setMaximumHeight(target)
        except Exception:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_auto_heights()

    def resizeEvent(self, event):
        self._apply_auto_heights()
        super().resizeEvent(event)
