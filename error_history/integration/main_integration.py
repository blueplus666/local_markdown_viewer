# error_history/integration/main_integration.py
"""
错误历史持久化子系统 - 主系统集成
"""

import logging
from typing import Optional, Any
from PyQt5.QtWidgets import QMessageBox

from ..core.manager import ErrorHistoryManager
from ..core.models import ErrorRecord
from ..ui.main_window import ErrorHistoryMainWindow

logger = logging.getLogger(__name__)


class ErrorHistoryIntegration:
    """错误历史与主系统的集成管理器"""

    def __init__(self, main_app=None, config_manager=None):
        """
        初始化集成管理器

        Args:
            main_app: 主应用程序实例
            config_manager: 配置管理器实例
        """
        self.main_app = main_app
        self.config_manager = config_manager
        self.manager = None
        self.ui_window = None

        # 初始化
        self._init_manager()
        self._setup_integration()

        logger.info("错误历史子系统集成初始化完成")

    def _init_manager(self):
        """初始化错误历史管理器"""
        try:
            self.manager = ErrorHistoryManager(config_manager=self.config_manager)
            logger.info("错误历史管理器初始化成功")
        except Exception as e:
            logger.error(f"错误历史管理器初始化失败: {e}")
            QMessageBox.warning(None, "初始化警告",
                              f"错误历史子系统初始化失败:\n{str(e)}\n\n系统将以降级模式运行。")

    def _setup_integration(self):
        """设置与主系统的集成"""
        if not self.main_app or not self.manager:
            return

        try:
            # 1. 添加菜单项
            self._add_menu_items()

            # 集成错误处理器
            self._integrate_error_handler()

            # 集成日志处理器（处理logging模块的错误级别日志）
            self._integrate_logging_handler()

            # 3. 添加状态栏信息
            self._add_status_bar_info()

            logger.info("错误历史子系统集成设置完成")

        except Exception as e:
            logger.error(f"设置集成失败: {e}")

    def _add_menu_items(self):
        """添加菜单项"""
        try:
            if not hasattr(self.main_app, 'menuBar'):
                return

            menubar = self.main_app.menuBar()
            tools_menu = None

            # 查找现有的工具菜单
            for action in menubar.actions():
                menu = action.menu()
                if menu and menu.title() in ["工具(&T)", "工具", "&T"]:
                    tools_menu = menu
                    break

            # 如果找不到工具菜单，则创建错误历史顶级菜单作为后备
            if not tools_menu:
                logger.warning("未找到工具菜单，使用错误历史顶级菜单作为后备")
                error_history_menu = menubar.addMenu("错误历史(&E)")
            else:
                # 在工具菜单中添加错误历史子菜单
                error_history_menu = tools_menu.addMenu("错误历史(&E)")

            # 查询错误历史
            query_action = error_history_menu.addAction("查询错误历史(&Q)")
            query_action.triggered.connect(lambda: self.open_ui("query"))

            # 错误统计
            stats_action = error_history_menu.addAction("错误统计(&S)")
            stats_action.triggered.connect(lambda: self.open_ui("statistics"))

            # 错误分析
            analysis_action = error_history_menu.addAction("错误分析(&A)")
            analysis_action.triggered.connect(lambda: self.open_ui("analysis"))

            error_history_menu.addSeparator()

            # 系统管理
            manage_action = error_history_menu.addAction("系统管理(&M)")
            manage_action.triggered.connect(lambda: self.open_ui("management"))

            logger.info("错误历史菜单项添加完成")

        except Exception as e:
            logger.error(f"添加菜单项失败: {e}")

    def _integrate_error_handler(self):
        """集成错误处理器"""
        try:
            if hasattr(self.main_app, 'error_handler') and self.main_app.error_handler:
                original_handle_error = self.main_app.error_handler.handle_error

                def enhanced_handle_error(exception, context=None):
                    # 先调用原始错误处理
                    error_info = original_handle_error(exception, context)

                    # 保存到错误历史数据库（处理所有级别的信息，包括INFO、WARNING等）
                    if error_info and self.manager:
                        try:
                            error_record = self._convert_to_error_record(error_info)
                            self.manager.save_error(error_record)
                            logger.debug(f"错误已保存到历史数据库: {error_record.error_id}")
                        except Exception as e:
                            logger.warning(f"保存错误到历史数据库失败: {e}")

                    return error_info

                # 替换错误处理方法
                self.main_app.error_handler.handle_error = enhanced_handle_error

                logger.info("错误处理器集成完成")

        except Exception as e:
            logger.error(f"集成错误处理器失败: {e}")

    def _integrate_logging_handler(self):
        """集成日志处理器，将logging的ERROR和CRITICAL级别日志发送到错误历史"""
        try:
            # 创建自定义日志处理器
            class ErrorHistoryLogHandler(logging.Handler):
                def __init__(self, error_history_integration):
                    super().__init__()
                    self.integration = error_history_integration
                    self.setLevel(logging.ERROR)  # 只处理ERROR和CRITICAL级别

                def emit(self, record):
                    try:
                        # 只处理ERROR和CRITICAL级别的日志
                        if record.levelno >= logging.ERROR:
                            # 创建模拟的错误信息对象
                            from ..core.models import ErrorSeverity, ErrorCategory
                            from datetime import datetime

                            # 根据日志级别映射到错误严重程度
                            severity_map = {
                                logging.ERROR: ErrorSeverity.CRITICAL,  # ERROR级别日志映射为CRITICAL严重程度
                                logging.CRITICAL: ErrorSeverity.CRITICAL,
                            }

                            error_info = type('MockErrorInfo', (), {
                                'error_id': f"LOG_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{record.levelno}",
                                'error_type': record.getMessage(),
                                'error_message': record.getMessage(),
                                'severity': severity_map.get(record.levelno, ErrorSeverity.CRITICAL),
                                'category': ErrorCategory.LOGGING,
                                'context': type('MockContext', (), {
                                    'module': record.name,
                                    'function': record.funcName if hasattr(record, 'funcName') else None,
                                    'line_number': record.lineno if hasattr(record, 'lineno') else None,
                                    'stack_trace': None,
                                    'user_context': None,
                                    'system_context': None,
                                })(),
                                'resolved': False,
                                'resolution_method': None,
                                'retry_count': 0,
                                'max_retries': 3
                            })()

                            # 保存到错误历史（避免使用logger.debug防止递归）
                            if self.integration.manager:
                                error_record = self.integration._convert_to_error_record(error_info)
                                self.integration.manager.save_error(error_record)
                                # 不使用logger.debug，避免递归调用

                    except Exception as e:
                        # 避免日志处理器本身的错误导致递归
                        print(f"错误历史日志处理器异常: {e}")

            # 添加到根日志器
            root_logger = logging.getLogger()
            error_history_handler = ErrorHistoryLogHandler(self)
            root_logger.addHandler(error_history_handler)

            logger.info("日志处理器集成完成")

        except Exception as e:
            logger.error(f"集成日志处理器失败: {e}")

    def _add_status_bar_info(self):
        """添加状态栏信息"""
        try:
            if hasattr(self.main_app, 'status_bar') and self.main_app.status_bar:
                # 这里可以添加错误历史的状态显示
                # 例如：显示未解决错误数量等
                pass

        except Exception as e:
            logger.error(f"添加状态栏信息失败: {e}")

    def _convert_to_error_record(self, error_info) -> ErrorRecord:
        """将ErrorInfo转换为ErrorRecord"""
        return ErrorRecord(
            error_id=getattr(error_info, 'error_id', ''),
            error_type=getattr(error_info, 'error_type', ''),
            error_message=getattr(error_info, 'error_message', ''),
            severity=getattr(error_info, 'severity', 'LOW'),
            category=getattr(error_info, 'category', 'UNKNOWN'),
            context={
                'module': getattr(error_info.context, 'module', None) if hasattr(error_info, 'context') and error_info.context else None,
                'function': getattr(error_info.context, 'function', None) if hasattr(error_info, 'context') and error_info.context else None,
                'line_number': getattr(error_info.context, 'line_number', None) if hasattr(error_info, 'context') and error_info.context else None,
                'stack_trace': getattr(error_info.context, 'stack_trace', None) if hasattr(error_info, 'context') and error_info.context else None,
            } if hasattr(error_info, 'context') and error_info.context else None,
            user_context=getattr(error_info.context, 'user_context', None) if hasattr(error_info, 'context') and error_info.context else None,
            system_context=getattr(error_info.context, 'system_context', None) if hasattr(error_info, 'context') and error_info.context else None,
            resolved=getattr(error_info, 'resolved', False),
            resolution_method=getattr(error_info, 'resolution_method', None),
            retry_count=getattr(error_info, 'retry_count', 0),
            max_retries=getattr(error_info, 'max_retries', 3)
        )

    def open_ui(self, mode: str = "query"):
        """
        打开错误历史UI

        Args:
            mode: UI模式 (query, statistics, analysis, management)
        """
        try:
            logger.debug(f"尝试打开错误历史UI，模式: {mode}, 当前窗口: {self.ui_window}")

            if self.ui_window and not self.ui_window.isHidden() and self.ui_window.isVisible():
                # 如果窗口已存在且可见，切换到指定模式
                logger.debug("窗口已存在且可见，切换模式")
                self.ui_window.tab_widget.setCurrentIndex({
                    "query": 0,
                    "statistics": 1,
                    "analysis": 2,
                    "management": 3
                }.get(mode, 0))
                self.ui_window.activateWindow()
                self.ui_window.raise_()
            else:
                # 创建新窗口
                logger.debug("创建新窗口")
                window = None
                try:
                    window = ErrorHistoryMainWindow(mode=mode)
                    logger.debug(f"窗口创建成功: {window}")
                except Exception as e:
                    logger.error(f"创建错误历史窗口失败: {e}")
                    QMessageBox.critical(None, "初始化失败",
                                       f"无法创建错误历史窗口:\n{str(e)}")
                    return

                # 多重安全检查
                if window is None:
                    logger.error("窗口创建后为None")
                    QMessageBox.critical(None, "初始化失败", "窗口创建失败")
                    return

                # 立即验证窗口对象状态
                if not hasattr(window, 'setWindowModality'):
                    logger.error("窗口对象缺少必要方法")
                    QMessageBox.critical(None, "初始化失败", "窗口对象无效")
                    return

                self.ui_window = window

                # 立即验证窗口对象状态（关键修复点）
                logger.debug(f"窗口对象赋值后状态检查: {self.ui_window}")
                logger.debug(f"窗口对象类型: {type(self.ui_window)}")
                logger.debug(f"窗口对象ID: {id(self.ui_window)}")
                logger.debug(f"窗口对象方法检查: {hasattr(self.ui_window, 'setWindowModality')}")

                # 设置为独立窗口 - 使用多重保护
                try:
                    from PyQt5.QtCore import Qt
                    # 再次检查窗口对象状态（防止赋值后立即失效）
                    current_window = self.ui_window
                    logger.debug(f"模态设置前的窗口状态: {current_window}")
                    logger.debug(f"模态设置前的窗口类型: {type(current_window)}")

                    if current_window is not None and hasattr(current_window, 'setWindowModality'):
                        current_window.setWindowModality(Qt.NonModal)
                        logger.debug("窗口模态设置成功")

                        # 验证模态设置是否生效
                        try:
                            current_modality = current_window.windowModality()
                            logger.debug(f"窗口模态验证成功: {current_modality}")
                        except Exception as e:
                            logger.warning(f"无法验证窗口模态: {e}")

                    else:
                        logger.error(f"窗口对象无效，无法设置模态 - window: {current_window}, has_method: {hasattr(current_window, 'setWindowModality') if current_window else 'N/A'}")
                        # 清理无效对象
                        if current_window:
                            try:
                                current_window.close()
                                logger.debug("无效窗口已关闭")
                            except Exception as e:
                                logger.warning(f"关闭无效窗口失败: {e}")
                        self.ui_window = None
                        return
                except Exception as e:
                    logger.error(f"设置窗口模态失败: {e}")
                    # 清理无效对象
                    if self.ui_window:
                        try:
                            self.ui_window.close()
                            logger.debug("异常后清理窗口")
                        except Exception as e:
                            logger.warning(f"异常清理失败: {e}")
                    self.ui_window = None
                    return

                # 确保窗口显示并激活 - 最终检查
                final_window = self.ui_window
                logger.debug(f"显示前的最终窗口检查: {final_window}")
                if final_window is not None:
                    try:
                        final_window.show()
                        final_window.raise_()
                        final_window.activateWindow()
                        logger.debug("窗口显示成功")

                        # 最终验证窗口是否真的可见
                        if final_window.isVisible():
                            logger.debug("窗口可见性验证成功")
                        else:
                            logger.warning("窗口显示后不可见")

                    except Exception as e:
                        logger.error(f"显示窗口失败: {e}")
                        # 清理无效对象
                        try:
                            final_window.close()
                            logger.debug("显示失败后清理窗口")
                        except Exception as e:
                            logger.warning(f"显示失败清理异常: {e}")
                        self.ui_window = None
                        return
                else:
                    logger.error("最终窗口对象为None，无法显示窗口")
                    return

                # 连接信号（在显示窗口后连接，避免关闭时的信号问题）
                try:
                    if self.ui_window:
                        window_ref = self.ui_window
                        window_ref.destroyed.connect(lambda obj=None, w_ref=window_ref: self._on_ui_closed(w_ref))
                        logger.debug("信号连接成功")
                except Exception as e:
                    logger.warning(f"连接窗口关闭信号失败: {e}")

            logger.info(f"错误历史UI已打开 (模式: {mode})")

        except Exception as e:
            logger.error(f"打开错误历史UI失败: {e}")
            QMessageBox.critical(None, "打开失败",
                               f"无法打开错误历史界面:\n{str(e)}")

    def _on_ui_closed(self, closed_window=None):
        """UI 窗口关闭处理"""
        try:
            logger.debug("开始处理 UI 窗口关闭")

            # 只在收到当前窗口的关闭信号时才进行清理
            if closed_window is not None and closed_window is not self.ui_window:
                logger.debug("收到非当前窗口的关闭信号，忽略")
                return

            # 若窗口仍然存在，断开信号并清理引用
            if hasattr(self, "ui_window") and self.ui_window is not None:
                logger.debug("发现有效的窗口对象，开始清理")
                try:
                    if hasattr(self.ui_window, "destroyed"):
                        self.ui_window.destroyed.disconnect(self._on_ui_closed)
                        logger.debug("信号已断开")
                except Exception as e:
                    logger.debug(f"断开信号异常: {e}")

                # 清理窗口引用，防止后续使用到已销毁的对象
                self.ui_window = None
                logger.debug("窗口引用已清理")
            else:
                logger.debug("窗口对象已为空或不存在，无需清理")

            logger.info("错误历史 UI 窗口已关闭")
        except Exception as e:
            logger.warning(f"处理 UI 窗口关闭时发生错误: {e}")
            # 确保在异常情况下也能把引用置空，避免悬挂对象
            try:
                self.ui_window = None
            except Exception:
                pass
            
    def shutdown(self):
        """关闭集成管理器"""
        try:
            # 关闭UI窗口
            if self.ui_window:
                self.ui_window.close()
                self.ui_window = None

            # 关闭管理器
            if self.manager:
                self.manager.shutdown()
                self.manager = None

            logger.info("错误历史子系统集成已关闭")

        except Exception as e:
            logger.error(f"关闭错误历史子系统集成失败: {e}")


# ================ 便捷函数 ================

def create_error_history_integration(main_app=None, config_manager=None) -> ErrorHistoryIntegration:
    """
    创建错误历史集成管理器的便捷函数

    Args:
        main_app: 主应用程序实例
        config_manager: 配置管理器实例

    Returns:
        ErrorHistoryIntegration实例
    """
    return ErrorHistoryIntegration(main_app, config_manager)


def open_error_history_ui(mode: str = "query"):
    """
    打开错误历史UI的便捷函数

    Args:
        mode: UI模式
    """
    try:
        integration = ErrorHistoryIntegration()
        integration.open_ui(mode)
    except Exception as e:
        logger.error(f"打开错误历史UI失败: {e}")


# ================ 主系统集成辅助函数 ================

def integrate_error_history_with_main_app(main_app) -> Optional[ErrorHistoryIntegration]:
    """
    将错误历史子系统集成到主应用程序

    Args:
        main_app: 主应用程序实例

    Returns:
        ErrorHistoryIntegration实例或None
    """
    try:
        # 获取配置管理器
        config_manager = getattr(main_app, 'config_manager', None)

        # 创建集成管理器
        integration = create_error_history_integration(main_app, config_manager)

        # 将集成管理器添加到主应用
        main_app.error_history_integration = integration

        logger.info("错误历史子系统已集成到主应用程序")
        return integration

    except Exception as e:
        logger.error(f"集成错误历史子系统到主应用失败: {e}")
        return None


def add_error_history_menu_to_main_app(main_app):
    """
    为主应用程序添加错误历史菜单

    Args:
        main_app: 主应用程序实例
    """
    try:
        # 检查是否已有集成
        if hasattr(main_app, 'error_history_integration') and main_app.error_history_integration:
            # 集成已存在，菜单应该已经添加
            return

        # 创建新的集成
        integration = integrate_error_history_with_main_app(main_app)

        if integration:
            logger.info("错误历史菜单已添加到主应用程序")

    except Exception as e:
        logger.error(f"为主应用添加错误历史菜单失败: {e}")


# ================ 独立运行支持 ================

def run_error_history_standalone(mode: str = "query"):
    """
    独立运行错误历史子系统

    Args:
        mode: 启动模式
    """
    import sys
    from PyQt5.QtWidgets import QApplication

    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # 创建集成管理器（无主应用）
        integration = create_error_history_integration()

        # 打开UI
        integration.open_ui(mode)

        return app.exec_()

    except Exception as e:
        logger.error(f"独立运行错误历史子系统失败: {e}")
        return 1


if __name__ == "__main__":
    # 独立运行测试
    import sys
    sys.exit(run_error_history_standalone())
