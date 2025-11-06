#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown渲染器模块 v1.0.0
负责将Markdown内容渲染为HTML，集成markdown_processor组件
支持文件渲染、内容渲染、自定义选项等功能

作者: LAD Team
创建时间: 2025-08-02
最后更新: 2025-08-02
"""

import os
import sys
import logging
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Optional, Union, Tuple
from functools import lru_cache

# 尝试导入markdown_processor模块
def _import_markdown_processor(config_manager):
    """根据配置导入markdown_processor模块"""
    try:
        # 从配置获取模块路径
        module_path = config_manager.get_markdown_module_path()
        
        # 解析相对路径
        if module_path.startswith('.'):
            # 相对路径，基于当前文件位置解析
            base_path = Path(__file__).parent.parent.parent
            resolved_path = base_path / module_path.lstrip('./')
        else:
            # 绝对路径
            resolved_path = Path(module_path)
        
        # 检查路径是否存在
        if resolved_path.exists():
            sys.path.insert(0, str(resolved_path))
            try:
                from markdown_processor import render_markdown_with_zoom, render_markdown_to_html
                return True, render_markdown_with_zoom, render_markdown_to_html
            except ImportError:
                # 如果导入失败，静默处理，不记录警告
                return False, None, None
        else:
            # 路径不存在时静默处理，不记录警告
            return False, None, None
            
    except Exception:
        # 任何异常都静默处理，不记录警告
        return False, None, None

# 初始化时先设置为False，在__init__中重新检查
MARKDOWN_PROCESSOR_AVAILABLE = False
render_markdown_with_zoom = None
render_markdown_to_html = None

# 备用markdown库
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    logging.warning("无法导入markdown库，将使用基本文本渲染")

try:
    from utils.config_manager import ConfigManager
except ImportError:
    # 如果导入失败，尝试相对导入
    try:
        from ..utils.config_manager import ConfigManager
    except ImportError:
        # 最后尝试绝对路径导入
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from utils.config_manager import ConfigManager


class MarkdownRenderer:
    """
    Markdown渲染器类
    提供Markdown内容渲染功能，支持多种渲染模式和错误处理
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        初始化Markdown渲染器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager or ConfigManager()
        self.logger = logging.getLogger(__name__)
        
        # 渲染缓存
        self._render_cache = {}
        self._cache_max_size = 100
        
        # 渲染选项
        self.default_options = {
            'enable_zoom': True,
            'enable_syntax_highlight': True,
            'theme': 'default',
            'max_content_length': 5 * 1024 * 1024,  # 5MB
            'cache_enabled': True,
            'fallback_to_text': True
        }
        
        # 根据配置更新选项
        self._update_options_from_config()
        
        # 导入markdown_processor模块
        self._import_markdown_processor()
        
        # 检查可用性
        self._check_availability()
    
    def _update_options_from_config(self):
        """根据配置更新渲染选项"""
        markdown_config = self.config_manager.get_markdown_config()
        
        # 更新缓存设置
        if 'cache_enabled' in markdown_config:
            self.default_options['cache_enabled'] = markdown_config['cache_enabled']
        
        # 更新降级设置
        if 'fallback_enabled' in markdown_config:
            self.default_options['fallback_to_text'] = markdown_config['fallback_enabled']
        
        # 更新其他设置
        for key in ['enable_zoom', 'enable_syntax_highlight', 'theme', 'max_content_length']:
            if key in markdown_config:
                self.default_options[key] = markdown_config[key]
    
    def _import_markdown_processor(self):
        """导入markdown_processor模块"""
        global MARKDOWN_PROCESSOR_AVAILABLE, render_markdown_with_zoom, render_markdown_to_html
        
        MARKDOWN_PROCESSOR_AVAILABLE, render_markdown_with_zoom, render_markdown_to_html = _import_markdown_processor(self.config_manager)
    
    def _check_availability(self):
        """检查渲染组件的可用性"""
        self.logger.info(f"Markdown处理器可用: {MARKDOWN_PROCESSOR_AVAILABLE}")
        self.logger.info(f"备用Markdown库可用: {MARKDOWN_AVAILABLE}")
        
        if not MARKDOWN_PROCESSOR_AVAILABLE and not MARKDOWN_AVAILABLE:
            self.logger.warning("所有Markdown渲染组件都不可用，将使用纯文本渲染")
    
    def render(self, markdown_content: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        渲染Markdown内容为HTML
        
        Args:
            markdown_content: Markdown内容字符串
            options: 渲染选项
            
        Returns:
            渲染结果字典
        """
        start_time = time.time()
        
        try:
            # 检查输入内容
            if markdown_content is None:
                return self._render_error_result("内容为空", "输入内容不能为None")
            
            # 合并选项
            render_options = {**self.default_options, **(options or {})}
            
            # 检查内容长度
            if len(markdown_content) > render_options['max_content_length']:
                return self._render_error_result(
                    "内容过长",
                    f"内容长度({len(markdown_content)})超过限制({render_options['max_content_length']})"
                )
            
            # 检查缓存
            if render_options['cache_enabled']:
                cache_key = self._generate_cache_key(markdown_content, render_options)
                if cache_key in self._render_cache:
                    cached_result = self._render_cache[cache_key].copy()
                    cached_result['cached'] = True
                    cached_result['render_time'] = time.time() - start_time
                    return cached_result
            
            # 执行渲染
            result = self._render_content(markdown_content, render_options)
            result['render_time'] = time.time() - start_time
            
            # 缓存结果
            if render_options['cache_enabled']:
                self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"渲染失败: {e}")
            return self._render_error_result("渲染失败", str(e))
    
    def render_file(self, file_path: Union[str, Path], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        渲染Markdown文件
        
        Args:
            file_path: 文件路径
            options: 渲染选项
            
        Returns:
            渲染结果字典
        """
        start_time = time.time()
        
        try:
            file_path = Path(file_path)
            
            # 检查文件是否存在
            if not file_path.exists():
                return self._render_error_result("文件不存在", f"文件路径: {file_path}")
            
            # 检查文件大小
            file_size = file_path.stat().st_size
            render_options = {**self.default_options, **(options or {})}
            
            if file_size > render_options['max_content_length']:
                return self._render_error_result(
                    "文件过大",
                    f"文件大小({file_size})超过限制({render_options['max_content_length']})"
                )
            
            # 读取文件内容
            content, encoding = self._read_file_content(file_path)
            if content is None:
                return self._render_error_result("文件读取失败", f"无法读取文件: {file_path}")
            
            # 渲染内容
            result = self.render(content, options)
            result['file_path'] = str(file_path)
            result['file_size'] = file_size
            result['encoding'] = encoding
            result['total_time'] = time.time() - start_time
            
            return result
            
        except Exception as e:
            self.logger.error(f"文件渲染失败: {e}")
            return self._render_error_result("文件渲染失败", str(e))
    
    def _render_content(self, content: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行实际的渲染操作
        
        Args:
            content: Markdown内容
            options: 渲染选项
            
        Returns:
            渲染结果
        """
        # 优先级1: 使用markdown_processor
        if MARKDOWN_PROCESSOR_AVAILABLE and render_markdown_with_zoom:
            try:
                if options.get('enable_zoom', True):
                    html_content = render_markdown_with_zoom(content)
                else:
                    html_content = render_markdown_to_html(content)
                
                return {
                    'success': True,
                    'html': html_content,
                    'renderer': 'markdown_processor',
                    'options_used': options
                }
            except Exception as e:
                self.logger.warning(f"markdown_processor渲染失败: {e}")
        
        # 优先级2: 使用备用markdown库
        if MARKDOWN_AVAILABLE:
            try:
                md = markdown.Markdown(extensions=[
                    'markdown.extensions.tables',
                    'markdown.extensions.fenced_code',
                    'markdown.extensions.codehilite',
                    'markdown.extensions.toc'
                ])
                html_content = md.convert(content)
                
                # 添加基本样式
                styled_html = self._add_basic_styles(html_content)
                
                return {
                    'success': True,
                    'html': styled_html,
                    'renderer': 'markdown_library',
                    'options_used': options
                }
            except Exception as e:
                self.logger.warning(f"备用markdown库渲染失败: {e}")
        
        # 优先级3: 降级到纯文本
        if options.get('fallback_to_text', True):
            return self._render_as_text(content, options)
        
        # 完全失败
        raise Exception("所有渲染方法都失败")
    
    def _render_as_text(self, content: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        将内容渲染为纯文本HTML
        
        Args:
            content: 原始内容
            options: 渲染选项
            
        Returns:
            渲染结果
        """
        # 转义HTML字符
        import html
        escaped_content = html.escape(content)
        
        # 将换行符转换为<br>标签
        formatted_content = escaped_content.replace('\n', '<br>')
        
        html_content = f"""
        <div class="text-content">
            <style>
                .text-content {{
                    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                    line-height: 1.6;
                    padding: 16px;
                    background: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 4px;
                }}
            </style>
            {formatted_content}
        </div>
        """
        
        return {
            'success': True,
            'html': html_content,
            'renderer': 'text_fallback',
            'options_used': options
        }
    
    def _add_basic_styles(self, html_content: str) -> str:
        """
        为HTML内容添加基本样式
        
        Args:
            html_content: 原始HTML内容
            
        Returns:
            带样式的HTML内容
        """
        styles = """
        <style>
            body { font-family: '微软雅黑', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }
            h1, h2, h3, h4, h5, h6 { margin-top: 24px; margin-bottom: 16px; font-weight: 600; line-height: 1.25; }
            p { margin-bottom: 16px; }
            code { background: #f6f8fa; padding: 2px 4px; border-radius: 3px; font-family: 'Consolas', 'Monaco', 'Courier New', monospace; }
            pre { background: #f6f8fa; padding: 16px; border-radius: 6px; overflow: auto; margin-bottom: 16px; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 16px; }
            th, td { border: 1px solid #d0d7de; padding: 8px 12px; text-align: left; }
            th { background: #f6f8fa; font-weight: 600; }
            blockquote { border-left: 4px solid #d0d7de; padding-left: 16px; margin: 16px 0; color: #656d76; }
        </style>
        """
        
        return f"{styles}\n{html_content}"
    
    def _read_file_content(self, file_path: Path) -> Tuple[Optional[str], Optional[str]]:
        """
        读取文件内容并检测编码
        
        Args:
            file_path: 文件路径
            
        Returns:
            (内容, 编码) 元组
        """
        try:
            # 尝试UTF-8
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return content, 'utf-8'
        except UnicodeDecodeError:
            try:
                # 尝试GBK
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
                    return content, 'gbk'
            except UnicodeDecodeError:
                try:
                    # 尝试Latin-1
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read()
                        return content, 'latin-1'
                except Exception as e:
                    self.logger.error(f"文件编码检测失败: {e}")
                    return None, None
    
    def _generate_cache_key(self, content: str, options: Dict[str, Any]) -> str:
        """
        生成缓存键
        
        Args:
            content: 内容
            options: 选项
            
        Returns:
            缓存键
        """
        # 创建包含内容和选项的字符串
        cache_string = f"{content}:{str(sorted(options.items()))}"
        return hashlib.md5(cache_string.encode('utf-8')).hexdigest()
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """
        缓存渲染结果
        
        Args:
            cache_key: 缓存键
            result: 渲染结果
        """
        if len(self._render_cache) >= self._cache_max_size:
            # 移除最旧的缓存项
            oldest_key = next(iter(self._render_cache))
            del self._render_cache[oldest_key]
        
        self._render_cache[cache_key] = result.copy()
    
    def _render_error_result(self, error_type: str, error_message: str) -> Dict[str, Any]:
        """
        生成错误结果
        
        Args:
            error_type: 错误类型
            error_message: 错误消息
            
        Returns:
            错误结果字典
        """
        return {
            'success': False,
            'error_type': error_type,
            'error_message': error_message,
            'html': f"""
            <div class="error-content">
                <style>
                    .error-content {{
                        padding: 20px;
                        background: #fff3cd;
                        border: 1px solid #ffeaa7;
                        border-radius: 4px;
                        color: #856404;
                    }}
                    .error-title {{
                        font-weight: bold;
                        margin-bottom: 10px;
                    }}
                </style>
                <div class="error-title">渲染错误: {error_type}</div>
                <div>{error_message}</div>
            </div>
            """,
            'renderer': 'error_handler'
        }
    
    def clear_cache(self):
        """清空渲染缓存"""
        self._render_cache.clear()
        self.logger.info("渲染缓存已清空")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息（统一接口）"""
        return {
            'total': len(self._render_cache),
            'limit': self._cache_max_size,
            'cache_size': len(self._render_cache),  # 兼容旧字段
            'max_size': self._cache_max_size,        # 兼容旧字段
            'cache_keys': list(self._render_cache.keys())
        }
    
    def is_available(self) -> bool:
        """
        检查渲染器是否可用
        
        Returns:
            是否可用
        """
        return MARKDOWN_PROCESSOR_AVAILABLE or MARKDOWN_AVAILABLE
    
    def get_supported_features(self) -> Dict[str, bool]:
        """
        获取支持的功能列表
        
        Returns:
            功能支持情况字典
        """
        return {
            'markdown_processor': MARKDOWN_PROCESSOR_AVAILABLE,
            'markdown_library': MARKDOWN_AVAILABLE,
            'zoom_support': MARKDOWN_PROCESSOR_AVAILABLE,
            'syntax_highlight': MARKDOWN_AVAILABLE,
            'text_fallback': True
        } 