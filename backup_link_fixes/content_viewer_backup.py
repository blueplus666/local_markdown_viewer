#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容显示组件模块 v1.0.0
=====================================

【模块定位】
- 位置：ui/content_viewer.py
- 职责：UI显示层，负责将文件内容渲染到用户界面
- 特点：基于PyQt5的QWebEngineView，有完整的用户界面

【核心功能】
实现基于QWebEngineView的文件内容显示功能，包括：
- 文件内容加载和显示
- 用户交互界面（进度条、状态栏、刷新按钮）
- 内容缓存管理
- 错误处理和用户提示
- 缩放和显示控制

【与ContentPreview的区别】
- ContentPreview：生成预览HTML内容（无UI，纯逻辑）
- ContentViewer：显示HTML内容到界面（有UI，用户交互）
- 关系：ContentViewer调用ContentPreview获取内容，然后显示

【架构层次】
- 底层：ContentPreview（内容生成）
- 中层：ContentViewer（内容显示）
- 上层：主窗口（整体布局）

【输入输出】
- 输入：文件路径 + 用户操作
- 输出：界面显示 + 用户交互反馈
- 有状态：维护当前文件、缓存、UI状态

作者: LAD Team
创建时间: 2025-01-08
最后更新: 2025-01-08
"""

import sys
import logging
import tempfile
import os
from pathlib import Path
from typing import Optional, Dict, Any, Union
from urllib.parse import urljoin
from urllib.request import pathname2url

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QPushButton, QMessageBox, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSlot, QUrl
from PyQt5.QtGui import QFont, QPixmap, QDesktopServices
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEnginePage

# 导入配置管理器
sys.path.append(str(Path(__file__).parent.parent))
from utils.config_manager import get_config_manager
from core.file_resolver import FileResolver
from core.markdown_renderer import MarkdownRenderer
from core.content_preview import ContentPreview
from core.link_processor import LinkProcessor, LinkContext, LinkType

# ============================================================================
# 重要说明：此模块与 content_preview.py 的区别
# ============================================================================
# 
# 【ContentViewer (content_viewer.py) - 当前文件】
# - 位置：ui/content_viewer.py
# - 职责：UI显示层，将文件内容渲染到用户界面
# - 特点：基于PyQt5，有完整UI，用户交互，状态管理
# - 输出：界面显示 + 用户反馈
# 
# 【ContentPreview (content_preview.py)】
# - 位置：core/content_preview.py
# - 职责：纯业务逻辑层，生成预览HTML内容
# - 特点：无UI，纯数据处理，可复用
# - 输出：HTML字符串 + 元数据
# 
# 【调用关系】
# 本类调用 ContentPreview.preview_file() 获取预览内容
# 然后使用 QWebEngineView 将内容显示到界面
# 这是标准的分层架构：逻辑层(ContentPreview) + 表现层(ContentViewer)
# ============================================================================


class _CVPage(QWebEnginePage):
    """Custom page to surface JS console messages and synthetic link clicks."""
    def __init__(self, owner, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._owner = owner

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # Forward to owner's handler for optional logging
        try:
            self._owner._on_js_console_message(level, message, lineNumber, sourceID)
        except Exception:
            pass
        # Detect synthetic link click signal
        try:
            if isinstance(message, str) and message.startswith("LPCLICK:"):
                href = message[len("LPCLICK:"):].strip()
                if href:
                    self._owner._handle_lpclick(href)
        except Exception:
            pass


class ContentViewer(QWidget):
    """
    内容显示组件类 - UI显示层
    
    【设计原则】
    - 单一职责：只负责文件内容的界面显示
    - UI驱动：基于PyQt5的QWebEngineView
    - 用户交互：提供进度显示、错误提示、刷新等功能
    
    【主要方法】
    - display_file(): 主入口，显示指定文件内容
    - _display_*(): 各种显示方式的专门方法
    - _init_ui(): 初始化用户界面组件
    
    【依赖关系】
    - 依赖ContentPreview：获取文件预览内容
    - 依赖MarkdownRenderer：处理Markdown文件
    - 依赖FileResolver：解析文件信息
    
    【使用场景】
    - 主窗口的内容显示区域
    - 文件预览窗口
    - 需要文件内容显示的对话框
    
    【注意】
    此类负责界面显示，不处理文件内容生成
    如需生成预览内容，请使用ContentPreview类
    """
    
    # 定义信号
    content_loaded = pyqtSignal(str, bool)  # 内容加载完成信号(文件路径, 是否成功)
    loading_progress = pyqtSignal(int)  # 加载进度信号
    error_occurred = pyqtSignal(str, str)  # 错误发生信号(错误类型, 错误消息)
    
    def __init__(self, parent=None):
        """初始化内容显示组件"""
        super().__init__(parent)
        
        # 获取配置管理器
        self.config_manager = get_config_manager()
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.web_engine_view = None  # Web引擎视图
        self.fallback_text_edit = None  # 备用文本显示
        self.progress_bar = None  # 进度条
        self.status_label = None  # 状态标签
        self.current_file_path = None  # 当前文件路径
        self._history_stack = []  # 简单历史栈（存放文件路径）
    # 注意：历史前进/后退应在主窗体统一管理，此处不再作为正式导航来源，仅保留以兼容右键菜单的最小化使用
        self.temp_files = []  # 临时文件列表
        # 导航与历史栈保护
        self._nav_in_progress = False
        try:
            self._history_max = int(self.config_manager.get_config("content_viewer.history_max", 200, "ui"))
        except Exception:
            self._history_max = 200
        
        # 初始化核心模块
        self.file_resolver = FileResolver(self.config_manager)
        self.markdown_renderer = MarkdownRenderer(self.config_manager)
        self.content_preview = ContentPreview(self.config_manager)
        
        # 初始化链接处理器
        self.link_processor = LinkProcessor(
            config_manager=self.config_manager,
            file_resolver=self.file_resolver,
            logger=self.logger
        )
        
        # 设置链接处理器
        from core.link_processor import (
            ExternalHandler, RelativeMarkdownHandler, DirectoryHandler,
            AnchorHandler, ImageHandler, MermaidHandler, TocHandler, FileProtocolHandler
        )
        
        self.link_processor.set_handlers({
            LinkType.EXTERNAL_HTTP: ExternalHandler(),
            LinkType.RELATIVE_MD: RelativeMarkdownHandler(),
            LinkType.DIRECTORY: DirectoryHandler(),
            LinkType.ANCHOR: AnchorHandler(),
            LinkType.IMAGE: ImageHandler(),
            LinkType.MERMAID: MermaidHandler(),
            LinkType.TOC: TocHandler(),
            LinkType.FILE_PROTOCOL: FileProtocolHandler(),
        })
        
        # 内容缓存
        self.content_cache = {}
        self.cache_limit = self.config_manager.get_config("content_viewer.cache_limit", 50, "ui")
        
        # 初始化UI
        self._init_ui()
        self._setup_web_engine()
        self._setup_connections()
        
        # 显示欢迎页面
        self._show_welcome_page()
        
        self.logger.info("内容显示组件初始化完成")
    
    def _init_ui(self):
        """初始化用户界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建状态栏
        self._create_status_bar(main_layout)
        
        # 创建Web引擎视图
        try:
            self.web_engine_view = QWebEngineView()
            # Attach custom page that can receive JS console messages
            try:
                # 每次构建或装载新内容前都替换 Page，避免旧页监听残留
                self._cv_page = _CVPage(self, self)
                self.web_engine_view.setPage(self._cv_page)
            except Exception as e:
                self.logger.warning(f"自定义页面设置失败，将继续使用默认页面: {e}")
            # 使用自定义右键菜单，接管 Back/Forward 行为，确保恢复 current_file_path
            try:
                self.web_engine_view.setContextMenuPolicy(Qt.CustomContextMenu)
                self.web_engine_view.customContextMenuRequested.connect(self._show_context_menu)
            except Exception as e:
                self.logger.warning(f"设置自定义菜单失败: {e}")
            main_layout.addWidget(self.web_engine_view, 1)
            self.logger.info("Web引擎视图创建成功")
        except Exception as e:
            self.logger.warning(f"Web引擎视图创建失败，使用备用文本显示: {e}")
            self._create_fallback_view(main_layout)
        
        # 设置样式
        self._apply_styles()
    
    def _create_status_bar(self, layout):
        """创建状态栏"""
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(5, 2, 5, 2)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setMaximumHeight(16)
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        # 重新加载按钮
        reload_btn = QPushButton("刷新")
        reload_btn.setMaximumWidth(60)
        reload_btn.setMaximumHeight(20)
        reload_btn.clicked.connect(self._reload_content)
        status_layout.addWidget(reload_btn)
        
        layout.addWidget(status_widget)
    
    def _create_fallback_view(self, layout):
        """创建备用文本显示视图"""
        self.fallback_text_edit = QTextEdit()
        self.fallback_text_edit.setReadOnly(True)
        self.fallback_text_edit.setFont(QFont("Consolas, Monaco, monospace", 10))
        layout.addWidget(self.fallback_text_edit, 1)
    
    def _setup_web_engine(self):
        """配置Web引擎"""
        if not self.web_engine_view:
            return
        
        # 获取Web引擎设置
        settings = self.web_engine_view.settings()
        
        # 基本设置
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        
        # 字体设置
        default_font_size = self.config_manager.get_config("content_viewer.default_font_size", 14, "ui")
        settings.setFontSize(QWebEngineSettings.DefaultFontSize, default_font_size)
        
        # 缩放设置
        default_zoom = self.config_manager.get_config("content_viewer.default_zoom", 1.0, "ui")
        self.web_engine_view.setZoomFactor(default_zoom)
        
        # 设置页面脚本注入，用于链接处理
        self._setup_link_handling()
        
        # 暂时禁用JavaScript控制台消息处理，使用更简单的方案
        # try:
        #     self.web_engine_view.page().javaScriptConsoleMessage.connect(self._on_js_console_message)
        # except AttributeError:
        #     # 如果信号不存在，使用备用方案
        #     self.logger.warning("JavaScript控制台消息信号不可用，使用备用链接处理方案")
        
        self.logger.info("Web引擎配置完成")
    
    def _setup_link_handling(self):
        """设置链接处理"""
        if not self.web_engine_view:
            return
        # 早期方案与当前方案重复，易相互干扰；此处不再注入静态脚本，全部交给 _setup_javascript_link_handling
        self.link_script = ""
        # 注入逻辑在页面加载完成后执行
    
    def _setup_connections(self):
        """设置信号连接"""
        # 连接Web引擎信号
        if self.web_engine_view:
            self.web_engine_view.loadFinished.connect(self._on_page_load_finished)
            self.web_engine_view.loadStarted.connect(self._on_load_started)
            self.web_engine_view.loadProgress.connect(self._on_load_progress)
            self.web_engine_view.loadFinished.connect(self._on_load_finished)
    
    def _show_welcome_page(self):
        """显示欢迎页面"""
        welcome_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>欢迎使用本地Markdown文件渲染器</title>
            <style>
                body {
                    font-family: 'Microsoft YaHei', Arial, sans-serif;
                    margin: 0;
                    padding: 40px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .welcome-container {
                    text-align: center;
                    max-width: 800px;
                    background: rgba(255, 255, 255, 0.1);
                    padding: 40px;
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                }
                h1 {
                    font-size: 2.5em;
                    margin-bottom: 20px;
                    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
                }
                .subtitle {
                    font-size: 1.2em;
                    margin-bottom: 30px;
                    opacity: 0.9;
                }
                .features {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin: 30px 0;
                }
                .feature {
                    background: rgba(255, 255, 255, 0.1);
                    padding: 20px;
                    border-radius: 15px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                .feature h3 {
                    margin: 0 0 10px 0;
                    color: #ffd700;
                }
                .feature p {
                    margin: 0;
                    opacity: 0.8;
                }
                .instructions {
                    margin-top: 30px;
                    padding: 20px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 15px;
                    border-left: 4px solid #ffd700;
                }
                .instructions h3 {
                    margin: 0 0 15px 0;
                    color: #ffd700;
                }
                .instructions ol {
                    text-align: left;
                    margin: 0;
                    padding-left: 20px;
                }
                .instructions li {
                    margin: 8px 0;
                    opacity: 0.9;
                }
            </style>
        </head>
        <body>
            <div class="welcome-container">
                <h1>🚀 本地Markdown文件渲染器</h1>
                <div class="subtitle">专业的本地文档查看和管理工具</div>
                
                <div class="features">
                    <div class="feature">
                        <h3>📖 Markdown渲染</h3>
                        <p>支持标准Markdown语法，实时预览渲染效果</p>
                    </div>
                    <div class="feature">
                        <h3>🔗 智能链接处理</h3>
                        <p>自动识别和处理各种类型的链接和引用</p>
                    </div>
                    <div class="feature">
                        <h3>📁 文件树浏览</h3>
                        <p>直观的文件系统浏览和快速导航</p>
                    </div>
                    <div class="feature">
                        <h3>⚡ 高性能</h3>
                        <p>基于Web引擎的快速渲染和流畅体验</p>
                    </div>
                </div>
                
                <div class="instructions">
                    <h3>📋 使用说明</h3>
                    <ol>
                        <li>在左侧文件树中选择要查看的Markdown文件</li>
                        <li>文件内容将在右侧显示，支持实时渲染</li>
                        <li>点击文件中的链接可以跳转到其他文档</li>
                        <li>使用右键菜单进行前进、后退等操作</li>
                        <li>支持文件搜索和过滤功能</li>
                    </ol>
                </div>
            </div>
        </body>
        </html>
        """
        
        if self.web_engine_view:
            self.web_engine_view.setHtml(welcome_html)
            self._set_status("欢迎页面已加载")
        elif hasattr(self, 'fallback_text_edit'):
            self.fallback_text_edit.setHtml(welcome_html)
            self._set_status("欢迎页面已加载（备用模式）")
    
    def _on_load_finished(self, success: bool):
        """统一入口：转发到 _on_page_load_finished（保持单次注入）"""
        try:
            self._on_page_load_finished(success)
        except Exception as e:
            self.logger.warning(f"_on_load_finished 处理异常: {e}")

    def _on_load_progress(self, progress: int):
        """更新进度条显示"""
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(progress)
            self.loading_progress.emit(progress)
            if progress >= 100:
                self.progress_bar.setVisible(False)
        except Exception:
            pass
    
    def _apply_styles(self):
        """应用样式"""
        # 设置主窗口样式
        self.setStyleSheet("""
            QWidget {
                background-color: white;
            }
            QLabel {
                color: #666;
                font-size: 12px;
            }
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """)
    
    def display_file(self, file_path: Union[str, Path], force_reload: bool = False):
        """
        显示文件内容
        
        Args:
            file_path: 文件路径
            force_reload: 是否强制重新加载
        """
        if not file_path:
            self._display_error("错误", "未提供文件路径")
            return
        
        file_path = str(file_path)
        self.current_file_path = file_path
        try:
            self.logger.info(f"NAV|current={self.current_file_path}")
        except Exception:
            pass
        # 为新文档替换 Page，确保无旧监听
        try:
            if self.web_engine_view:
                self._cv_page = _CVPage(self, self)
                self.web_engine_view.setPage(self._cv_page)
        except Exception:
            pass
        
        # 检查缓存
        if not force_reload and file_path in self.content_cache:
            self._display_cached_content(file_path)
            return
        
        # 更新状态
        self._set_status(f"正在加载: {Path(file_path).name}")
        self._show_progress(True)
        
        try:
            # 解析文件
            file_info = self.file_resolver.resolve_file_path(file_path)
            if not file_info['success']:
                self._display_error("文件解析失败", file_info.get('error', '未知错误'))
                return
            
            # 根据文件类型选择显示方式
            renderer_type = file_info['file_type']['extension_type']['renderer']
            self._display_content_by_type(file_path, file_info, renderer_type)
            
        except Exception as e:
            self.logger.error(f"文件显示失败: {e}")
            self._display_error("显示失败", str(e))
        finally:
            self._show_progress(False)
    
    def _display_content_by_type(self, file_path: str, file_info: Dict[str, Any], renderer_type: str):
        """根据文件类型显示内容"""
        try:
            if renderer_type == 'markdown':
                self._display_markdown(file_path, file_info)
            elif renderer_type in ['text', 'syntax_highlight', 'data_viewer', 'image_viewer', 'binary', 'archive']:
                self._display_preview(file_path, file_info)
            else:
                self._display_unsupported(file_path, file_info)
                
        except Exception as e:
            self.logger.error(f"内容显示失败 ({renderer_type}): {e}")
            self._display_error("内容显示失败", str(e))
    
    def _display_markdown(self, file_path: str, file_info: Dict[str, Any]):
        """显示Markdown文件"""
        try:
            # 使用Markdown渲染器
            render_options = self._get_markdown_options()
            result = self.markdown_renderer.render_file(file_path, render_options)
            
            if result['success']:
                html_content = result['html']
                # 调试：统计链接与落盘HTML
                # 统计<a>数量（优先BeautifulSoup，失败则用正则）
                try:
                    from bs4 import BeautifulSoup  # 可选依赖
                    soup = BeautifulSoup(html_content, 'html.parser')
                    a_count = len(soup.find_all('a'))
                except Exception:
                    import re
                    a_count = len(re.findall(r'<a\b', html_content, flags=re.IGNORECASE))
                try:
                    debug_dir = Path(__file__).resolve().parent.parent / 'debug_render'
                    debug_dir.mkdir(parents=True, exist_ok=True)
                    debug_file = debug_dir / f"{Path(file_path).name}.rendered.html"
                    debug_file.write_text(html_content, encoding='utf-8')
                    self.logger.info(f"已保存调试HTML: {debug_file} | 链接数: {a_count}")
                except Exception as e:
                    self.logger.warning(f"保存调试HTML失败: {e}")
                self._display_html(html_content)
                self._cache_content(file_path, html_content, 'markdown')
                self._set_status(f"Markdown文件已加载: {Path(file_path).name}")
                self.content_loaded.emit(file_path, True)
            else:
                self._display_error("Markdown渲染失败", result.get('error_message', '未知错误'))
                
        except Exception as e:
            self.logger.error(f"Markdown显示失败: {e}")
            self._display_error("Markdown显示失败", str(e))

    def _get_markdown_options(self) -> Dict[str, Any]:
        """提供 Markdown 渲染选项（从配置安全读取，含 base_url）。"""
        try:
            base_dir = None
            if self.current_file_path:
                try:
                    base_dir = Path(self.current_file_path).parent
                except Exception:
                    base_dir = None
            return {
                "base_url": (str(base_dir) if base_dir else None),
                "use_dynamic_import": self.config_manager.get_config("use_dynamic_import", True, "markdown"),
                "fallback_enabled": self.config_manager.get_config("fallback_enabled", True, "markdown"),
                "cache_enabled": self.config_manager.get_config("cache_enabled", True, "markdown"),
                "max_content_length": self.config_manager.get_config("max_content_length", 5*1024*1024, "markdown"),
            }
        except Exception:
            return {}
    
    def _display_preview(self, file_path: str, file_info: Dict[str, Any]):
        """显示预览内容"""
        try:
            # 使用内容预览器
            max_lines = self.config_manager.get_config("content_viewer.max_preview_lines", 1000, "ui")
            max_size = self.config_manager.get_config("content_viewer.max_preview_size", 5*1024*1024, "ui")
            
            result = self.content_preview.preview_file(file_path, max_lines, max_size)
            
            if result['success']:
                html_content = result['html']
                self._display_html(html_content)
                self._cache_content(file_path, html_content, result['preview_type'])
                self._set_status(f"文件已加载: {Path(file_path).name}")
                self.content_loaded.emit(file_path, True)
            else:
                # 若包含底层 error_info，则拼接到错误展示中，避免信息丢失
                err_msg = result.get('error_message', '未知错误')
                if result.get('error_info'):
                    try:
                        import json
                        err_msg = f"{err_msg}<pre style=\"text-align:left;white-space:pre-wrap;\">{json.dumps(result['error_info'], ensure_ascii=False)}</pre>"
                    except Exception:
                        pass
                self._display_error("文件预览失败", err_msg)
                
        except Exception as e:
            self.logger.error(f"预览显示失败: {e}")
            self._display_error("预览显示失败", str(e))
    
    def _display_unsupported(self, file_path: str, file_info: Dict[str, Any]):
        """显示不支持的文件类型"""
        file_name = Path(file_path).name
        file_size = file_info['file_info']['size_formatted']
        file_type = file_info['file_type']['final_type']
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>不支持的文件类型</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 20px;
                    text-align: center;
                    background-color: #f9f9f9;
                }}
                .info-box {{
                    background: white;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 30px;
                    margin: 20px auto;
                    max-width: 500px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .icon {{
                    font-size: 48px;
                    color: #999;
                    margin-bottom: 20px;
                }}
                .file-name {{
                    font-size: 18px;
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 10px;
                }}
                .file-info {{
                    color: #666;
                    margin: 5px 0;
                }}
            </style>
        </head>
        <body>
            <div class="info-box">
                <div class="icon">📄</div>
                <div class="file-name">{file_name}</div>
                <div class="file-info">文件大小: {file_size}</div>
                <div class="file-info">文件类型: {file_type}</div>
                <div class="file-info" style="margin-top: 20px; color: #999;">
                    此文件类型暂不支持预览
                </div>
            </div>
        </body>
        </html>
        """
        
        self._display_html(html_content)
        self._set_status(f"不支持的文件类型: {file_name}")
        self.content_loaded.emit(file_path, False)

    def _set_status(self, text: str):
        """更新状态栏文本（安全调用）。"""
        try:
            if self.status_label:
                self.status_label.setText(str(text))
            self.logger.info(str(text))
        except Exception:
            pass

    def _show_progress(self, visible: bool):
        """显示/隐藏进度条（安全调用）。"""
        try:
            if self.progress_bar:
                self.progress_bar.setVisible(bool(visible))
                if not visible:
                    try:
                        self.progress_bar.setValue(0)
                    except Exception:
                        pass
        except Exception:
            pass

    def _display_error(self, title: str, message: str):
        """统一错误展示，避免未实现导致崩溃。"""
        try:
            html = f"""
            <!DOCTYPE html>
            <html><head><meta charset='utf-8'><title>{title}</title></head>
            <body style='font-family:Arial, sans-serif; padding:16px;'>
                <h3 style='color:#d32f2f;'>{title}</h3>
                <pre style='white-space:pre-wrap;word-break:break-word;border:1px solid #eee;padding:12px;background:#fafafa;'>
{message}
                </pre>
            </body></html>
            """
            self._display_html(html)
            self._set_status(f"{title}: {message}")
            self._show_progress(False)
            try:
                self.error_occurred.emit(str(title), str(message))
            except Exception:
                pass
        except Exception:
            try:
                self.logger.error(f"错误展示失败: {title} | {message}")
            except Exception:
                pass
    
    def _display_html(self, html_content: str):
        """显示HTML内容"""
        if self.web_engine_view:
            # 调试：在日志中打印<a>标签数
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                a_count = len(soup.find_all('a'))
            except Exception:
                import re
                a_count = len(re.findall(r'<a\b', html_content, flags=re.IGNORECASE))
            self.logger.info(f"本次渲染HTML包含链接数: {a_count}")
            # 注入链接处理脚本
            if hasattr(self, 'link_script') and self.link_script:
                # 在</body>标签前插入脚本
                if '</body>' in html_content:
                    html_content = html_content.replace('</body>', f'{self.link_script}</body>')
                else:
                    html_content += self.link_script
            
            # 使用Web引擎显示（提供 baseUrl 以确保相对链接正确解析）
            try:
                base_dir = None
                if self.current_file_path:
                    try:
                        base_dir = Path(self.current_file_path).parent
                    except Exception:
                        base_dir = None
                if base_dir and str(base_dir).strip():
                    base_url = QUrl.fromLocalFile(str(base_dir) + os.sep)
                    self.web_engine_view.setHtml(html_content, base_url)
                else:
                    self.web_engine_view.setHtml(html_content)
            except Exception:
                # 退回不带 baseUrl 的方式
                self.web_engine_view.setHtml(html_content)
            # 不再二次注入或轮询，所有链接拦截统一在 _on_load_finished 注入的脚本中完成
        elif self.fallback_text_edit:
            # 使用备用文本显示（去除HTML标签）
            import re
            text_content = re.sub(r'<[^>]+>', '', html_content)
            self.fallback_text_edit.setPlainText(text_content)
        else:
            self.logger.error("没有可用的显示组件")
    
    def _on_page_load_finished(self, success: bool):
        """页面加载完成后的处理"""
        if success:
            # 页面加载成功后设置链接处理（一次性注入拦截脚本）
            try:
                js = r"""
                    (function() {
                        try {
                            // 清理旧监听
                            if (window.linkClickHandler) {
                                document.removeEventListener('click', window.linkClickHandler, true);
                            }
                            window.linkClickHandler = function(ev){
                                try{
                                    var a = ev.target && ev.target.closest ? ev.target.closest('a') : null;
                                    if (!a || !a.getAttribute) { return; }
                                    var href = a.getAttribute('href') || '';
                                    if (!href) { return; }
                                    ev.preventDefault();
                                    console.log('LPCLICK:' + href);
                                    return false;
                                }catch(e){ console.log('link-handler-error:' + e); }
                            };
                            document.addEventListener('click', window.linkClickHandler, true);
                            console.log('link-handlers-attached');
                        } catch (e) { console.log('link-handler-init-error:' + e); }
                    })();
                """
                self.web_engine_view.page().runJavaScript(js)
            except Exception as e:
                self.logger.warning(f"注入链接处理脚本失败: {e}")
            # 断开连接，避免重复调用
            try:
                self.web_engine_view.loadFinished.disconnect(self._on_page_load_finished)
            except Exception:
                pass
            self.logger.info("页面加载完成，链接处理已设置")
        else:
            self.logger.warning("页面加载失败")
    
    def _setup_simple_link_handling(self):
        """设置简单的链接处理（使用更直接的方法）"""
        if not self.web_engine_view:
            return
            
        # 直接使用JavaScript拦截方案，这是最可靠的方法
        try:
            self.logger.info("使用JavaScript拦截方案设置链接处理")
            self._setup_javascript_link_handling()
        except Exception as e:
            self.logger.error(f"设置链接处理失败: {e}")
    
    def _setup_javascript_link_handling(self):
        """使用JavaScript拦截链接点击（已废弃入口，兼容保留）"""
        # 旧方案已废弃：统一由 _on_page_load_finished/_on_load_finished 注入 LPCLICK 脚本
        try:
            self.logger.debug("_setup_javascript_link_handling 已禁用（使用LPCLICK统一方案）")
        except Exception:
            pass
    def _on_js_test_result(self, result):
        """JavaScript测试结果回调"""
        self.logger.info(f"JavaScript测试结果: {result}")
    
    def _setup_link_monitoring(self):
        """设置链接监控（已废弃，兼容保留）"""
        # 旧轮询方案移除：LPCLICK 通过 console 回传，无需定时器
        try:
            if hasattr(self, 'link_check_timer') and self.link_check_timer:
                self.link_check_timer.stop()
        except Exception:
            pass
        self.logger.debug("链接监控轮询已禁用（LPCLICK方案）")
    
    def _check_for_clicked_links(self):
        """检查是否有链接被点击（已废弃）"""
        # 废弃，无操作
        return
    
    def _on_link_clicked(self, result):
        """处理链接点击事件（已废弃）"""
        # 轮询通道已废弃，保持空实现以保兼容
        return
    
    def _on_navigation_requested(self, url):
        """处理导航请求（未使用，兼容保留）"""
        try:
            url_str = url.toString() if hasattr(url, 'toString') else str(url)
            self.logger.debug(f"_on_navigation_requested: {url_str}")
        except Exception:
            pass
        return
    
    def _handle_link_click(self, link_info):
        """处理链接点击（旧接口，转发到 _handle_lpclick）"""
        try:
            href = link_info.get('href', '') if isinstance(link_info, dict) else str(link_info)
            if href:
                self._handle_lpclick(href)
        except Exception:
            pass
        return

    def _handle_lpclick(self, href: str):
        """统一的 LPCLICK 入口：由 _CVPage.javaScriptConsoleMessage 调用"""
        try:
            current_path = Path(self.current_file_path) if self.current_file_path else None
            try:
                self.logger.info(f"NAV|click_href={href}|current={self.current_file_path}")
            except Exception:
                pass
            ctx = LinkContext(
                href=href,
                current_file=current_path,
                current_dir=(current_path.parent if current_path else None),
                source_component="content_viewer",
                extra={"session_id": f"viewer_{id(self)}"}
            )
            result = self.link_processor.process_link(ctx)
            try:
                # 预取目标，便于日志
                tgt = None
                if isinstance(result, dict):
                    pld = result.get('payload') or {}
                    tgt = pld.get('path') or pld.get('target') or pld.get('url')
                else:
                    pld = getattr(result, 'payload', {}) or {}
                    tgt = pld.get('path') or pld.get('target') or pld.get('url')
                self.logger.info(f"NAV|resolved_target={tgt}")
            except Exception:
                pass
            self._execute_link_action(result)
        except Exception as e:
            self.logger.error(f"处理链接失败: {e}")
            self._set_status("链接处理失败")

    def _execute_link_action(self, result: Any):
        """根据 LinkProcessor 返回执行动作（兼容 dict 与对象形式）。"""
        if getattr(self, '_nav_in_progress', False):
            try:
                self.logger.warning("NAV|skip|reentry_guard_active")
            except Exception:
                pass
            return
        self._nav_in_progress = True
        try:
            # 兼容两种返回结构
            if isinstance(result, dict):
                success = bool(result.get('success', True))
                action = result.get('action')
                payload = result.get('payload') or {}
                message = result.get('message', '')
            else:
                success = getattr(result, 'success', True)
                action = getattr(result, 'action', None)
                payload = getattr(result, 'payload', {}) or {}
                message = getattr(result, 'message', '')

            if not success:
                self._display_error("链接错误", message or "处理失败")
                return

            if not action:
                self.logger.warning("未指定动作，忽略")
                return

            # 统一历史入栈逻辑
            def _push_history():
                if self.current_file_path:
                    try:
                        self._history_stack.append(self.current_file_path)
                        if hasattr(self, '_history_max') and self._history_max > 0 and len(self._history_stack) > self._history_max:
                            self._history_stack = self._history_stack[-self._history_max:]
                    except Exception:
                        pass

            # 动作分发（兼容旧/新命名）
            if action in ('open_markdown_in_tree', 'open_file'):
                target = payload.get('path') or payload.get('target')
                if target:
                    try:
                        self.logger.info(f"NAV|open_file|from={self.current_file_path}|to={target}")
                    except Exception:
                        pass
                    _push_history()
                    self.display_file(target, force_reload=True)
                    try:
                        self._set_status(f"已打开文件: {Path(target).name}")
                    except Exception:
                        pass
                else:
                    self.logger.warning("打开文件缺少目标路径")

            elif action in ('open_browser', 'open_external'):
                url = payload.get('url') or payload.get('target')
                if url:
                    try:
                        QDesktopServices.openUrl(QUrl(str(url)))
                        self._set_status("已打开外部链接")
                    except Exception as e:
                        self.logger.warning(f"外部链接打开失败: {e}")
                else:
                    self.logger.warning("外部链接缺少 url/target")

            elif action in ('scroll_to_anchor',):
                anchor = payload.get('id') or payload.get('anchor') or payload.get('target')
                if anchor and self.web_engine_view:
                    js = (
                        "(function(a){var el=document.getElementById(a)||document.querySelector('[name=""+a+""]');"
                        "if(el){el.scrollIntoView({behavior:'smooth'});}})('" + str(anchor).replace("'","\\'") + "');"
                    )
                    self.web_engine_view.page().runJavaScript(js)
                    self._set_status(f"已跳转到锚点: {anchor}")
                else:
                    self.logger.warning("锚点跳转缺少 anchor 或 web 引擎不可用")
            elif action in ('open_directory',):
                # 优先尝试目录 README.md；不存在则渲染目录索引页，避免 fail.json
                try:
                    from pathlib import Path as _P
                    dir_path = _P(payload.get('path') or '')
                    if dir_path and dir_path.exists() and dir_path.is_dir():
                        candidate = dir_path / 'README.md'
                        if candidate.exists():
                            _push_history()
                            self.display_file(str(candidate), force_reload=True)
                            try:
                                self._set_status(f"已打开目录 README: {candidate.name}")
                            except Exception:
                                pass
                        else:
                            # 构造简易目录索引 HTML 并直接显示
                            items = []
                            try:
                                for p in sorted(dir_path.iterdir()):
                                    name = p.name
                                    href = name + ('/' if p.is_dir() else '')
                                    items.append(f"<li><a href='{href}'>{name}</a></li>")
                            except Exception:
                                pass
                            html = (
                                "<!DOCTYPE html><html><head><meta charset='utf-8'><title>目录索引</title></head><body>"
                                f"<h3>目录：{dir_path.as_posix()}</h3>"
                                "<p>未找到 README.md，已显示目录列表。</p>"
                                f"<ul>{''.join(items)}</ul>"
                                "</body></html>"
                            )
                            # 以目录为 baseUrl，保证相对链接可点击
                            try:
                                self.web_engine_view.setHtml(html, QUrl.fromLocalFile(str(dir_path)))
                            except Exception:
                                self.web_engine_view.setHtml(html)
                            self._set_status("目录链接（展示目录索引）")
                    else:
                        self._set_status("目录链接（路径无效）")
                except Exception:
                    self._set_status("目录链接（由主窗体处理）")
            else:
                self._set_status(f"未知动作: {action}")
        except Exception as e:
            self.logger.error(f"执行链接动作失败: {e}")
        finally:
            self._nav_in_progress = False
    
    def _handle_external_link(self, url):
        """处理外部链接"""
        try:
            self.logger.info(f"处理外部链接: {url}")
            if not url:
                return
            QDesktopServices.openUrl(QUrl(str(url)))
        except Exception as e:
            self.logger.warning(f"外部链接处理失败: {e}")
    
    def _on_js_console_message(self, level, message, line_number, source_id):
        """处理JavaScript控制台消息（仅记录日志；LPCLICK 由 _CVPage 处理）"""
        try:
            level_map = {
                QWebEnginePage.InfoMessageLevel: "INFO",
                QWebEnginePage.WarningMessageLevel: "WARN",
                QWebEnginePage.ErrorMessageLevel: "ERROR",
            }
            level_str = level_map.get(level, "UNKNOWN")
            self.logger.debug(f"JS [{level_str}] {source_id}:{line_number}: {message}")
        except Exception:
            pass
    
    def _reload_content(self):
        """重新加载当前文件内容"""
        try:
            if self.current_file_path:
                self.display_file(self.current_file_path, force_reload=True)
        except Exception as e:
            self.logger.warning(f"重新加载失败: {e}")

    def _show_context_menu(self, pos):
        """显示自定义右键菜单，接管Back/Forward并同步当前文件状态。"""
        try:
            from PyQt5.QtWidgets import QMenu, QAction
            menu = QMenu(self)
            try:
                self.logger.warning("NAV|context_menu_opened")
            except Exception:
                pass
            act_back = QAction("Back", self)
            act_forward = QAction("Forward", self)
            act_reload = QAction("Reload", self)

            def _on_back():
                # 强制重载，确保完全替换旧页与基准目录
                try:
                    if getattr(self, '_nav_in_progress', False):
                        try:
                            self.logger.warning("NAV|back_skip|reentry_guard_active")
                        except Exception:
                            pass
                        return
                    self._nav_in_progress = True
                    try:
                        self.logger.warning("NAV|back_menu_clicked")
                    except Exception:
                        pass
                    if self._history_stack:
                        prev = self._history_stack.pop()
                        try:
                            self.logger.warning(f"NAV|back_clicked|stack_size_after_pop={len(self._history_stack)}")
                            self.logger.warning(f"NAV|back|from={self.current_file_path}|to={prev}")
                        except Exception:
                            pass
                        self.display_file(prev, force_reload=True)
                        try:
                            self._set_status(f"已返回: {Path(prev).name}")
                        except Exception:
                            pass
                    else:
                        try:
                            self.logger.warning("NAV|back_clicked|stack_empty")
                        except Exception:
                            pass
                except Exception as e:
                    self.logger.warning(f"Back 操作失败: {e}")
                finally:
                    self._nav_in_progress = False

            def _on_forward():
                # 预留：如需实现自定义前进栈，可在此扩展
                self._set_status("Forward 暂未实现（由主窗体统一管理）")

            def _on_reload():
                self._reload_content()

            act_back.triggered.connect(_on_back)
            act_forward.triggered.connect(_on_forward)
            act_reload.triggered.connect(_on_reload)

            menu.addAction(act_back)
            menu.addAction(act_forward)
            menu.addSeparator()
            menu.addAction(act_reload)
            menu.exec_(self.web_engine_view.mapToGlobal(pos))
        except Exception as e:
            # 降级：若自定义菜单失败，忽略
            self.logger.warning(f"显示自定义菜单失败: {e}")
    
    def handle_image_click(self, image_data: dict):
        """处理图片点击事件"""
        try:
            src = image_data.get('href', '')
            if not src:
                return
            
            # 创建图片链接上下文
            ctx = LinkContext(
                href=src,
                current_file=Path(self.current_file_path) if self.current_file_path else None,
                current_dir=Path(self.current_file_path).parent if self.current_file_path else None,
                source_component="content_viewer",
                extra={
                    "session_id": f"viewer_{id(self)}",
                    "image_alt": image_data.get('text', ''),
                    "image_width": image_data.get('width', 0),
                    "image_height": image_data.get('height', 0),
                    "mermaid_container": src.endswith(('.mmd', '.mermaid'))
                }
            )
            
            # 使用LinkProcessor处理图片链接
            result = self.link_processor.process_link(ctx)
            
            # 执行相应操作
            self._execute_link_action(result)
            
        except Exception as e:
            self.logger.error(f"图片处理失败: {e}")
            self._display_error("图片处理错误", str(e))
    
    def clear_cache(self):
        """清空内容缓存"""
        self.content_cache.clear()
        self.logger.info("内容缓存已清空")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息（统一接口）"""
        return {
            'total': len(self.content_cache),
            'limit': self.cache_limit,
            'total_items': len(self.content_cache),  # 兼容旧字段
            'cache_limit': self.cache_limit,         # 兼容旧字段
            'cached_files': list(self.content_cache.keys())
        }

    def _cache_content(self, file_path: str, html_content: str, preview_type: str) -> None:
        """简单缓存：LRU 近似策略，超限时弹出最早项。"""
        try:
            if not isinstance(self.content_cache, dict):
                self.content_cache = {}
            self.content_cache[file_path] = {
                'html': html_content,
                'type': preview_type,
            }
            # 超限裁剪
            try:
                limit = int(self.cache_limit or 0)
            except Exception:
                limit = 0
            if limit and len(self.content_cache) > limit:
                # 移除第一个键（最早项）
                first_key = next(iter(self.content_cache.keys()))
                if first_key in self.content_cache:
                    self.content_cache.pop(first_key, None)
        except Exception:
            pass

    def _display_cached_content(self, file_path: str) -> None:
        """显示缓存内容（若存在）。"""
        try:
            item = self.content_cache.get(file_path)
            if not item:
                return
            html = item.get('html', '')
            if html:
                self._display_html(html)
                self._set_status(f"已从缓存加载: {Path(file_path).name}")
        except Exception:
            pass
    
    def get_current_file(self) -> Optional[str]:
        """获取当前显示的文件路径"""
        return self.current_file_path
    
    def is_web_engine_available(self) -> bool:
        """检查Web引擎是否可用"""
        return self.web_engine_view is not None
    
    def set_zoom_factor(self, factor: float):
        """设置缩放因子"""
        if self.web_engine_view:
            self.web_engine_view.setZoomFactor(factor)
            # 保存缩放设置
            self.config_manager.set_config("content_viewer.default_zoom", factor, "ui")
    
    def get_zoom_factor(self) -> float:
        """获取当前缩放因子"""
        if self.web_engine_view:
            return self.web_engine_view.zoomFactor()
        return 1.0
    
    def closeEvent(self, event):
        """组件关闭事件处理"""
        # 清理临时文件
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                self.logger.warning(f"删除临时文件失败: {temp_file}, 错误: {e}")
        
        # 清空缓存
        self.clear_cache()
        
        self.logger.info("内容显示组件已关闭")
        event.accept()


if __name__ == "__main__":
    # 测试内容显示组件
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    viewer = ContentViewer()
    viewer.resize(800, 600)
    viewer.show()
    
    # 如果有测试文件，可以显示
    test_file = Path(__file__).parent.parent / "README.md"
    if test_file.exists():
        viewer.display_file(str(test_file))
    
    sys.exit(app.exec_())