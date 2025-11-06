#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混合架构Markdown渲染器模块 v2.0.0
负责将Markdown内容渲染为HTML，支持动态模块导入和混合架构
支持文件渲染、内容渲染、自定义选项等功能
重构：集成DynamicModuleImporter，实现动态导入+统一路径解析的混合方案

作者: LAD Team
创建时间: 2025-08-02
最后更新: 2025-08-12
"""

import os
import sys
import logging
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Optional, Union, Tuple, List
from functools import lru_cache

# 导入统一缓存管理器
from .unified_cache_manager import UnifiedCacheManager, CacheStrategy
from .cache_invalidation_manager import CacheInvalidationManager, InvalidationTrigger
from .enhanced_error_handler import EnhancedErrorHandler, ErrorRecoveryStrategy



# 备用markdown库
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    logging.warning("无法导入markdown库，将使用基本文本渲染")

try:
    from utils.config_manager import ConfigManager
    from core.file_resolver import FileResolver
    from core.dynamic_module_importer import DynamicModuleImporter
except ImportError:
    # 如果导入失败，尝试相对导入
    try:
        from ..utils.config_manager import ConfigManager
        from ..core.file_resolver import FileResolver
        from ..core.dynamic_module_importer import DynamicModuleImporter
    except ImportError:
        # 最后尝试绝对路径导入
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from utils.config_manager import ConfigManager
        from core.file_resolver import FileResolver
        from core.dynamic_module_importer import DynamicModuleImporter


class HybridMarkdownRenderer:
    """
    混合架构Markdown渲染器类
    提供Markdown内容渲染功能，支持动态模块导入和多种渲染模式
    重构：集成DynamicModuleImporter，实现动态导入+统一路径解析的混合方案
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        初始化混合架构Markdown渲染器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager or ConfigManager()
        self.logger = logging.getLogger(__name__)
        
        # 初始化文件解析器
        self.file_resolver = FileResolver(config_manager)
        
        # 初始化动态模块导入器
        self.module_importer = DynamicModuleImporter(config_manager)
        
        # 统一缓存管理器
        self.cache_manager = UnifiedCacheManager(
            max_size=500,  # 增加缓存大小
            default_ttl=3600,  # 默认1小时过期
            strategy=CacheStrategy.LRU,
            cache_dir=Path(__file__).parent.parent / "cache" / "renderer"
        )
        
        # 缓存失效管理器
        self.invalidation_manager = CacheInvalidationManager(
            self.cache_manager,
            invalidation_dir=Path(__file__).parent.parent / "cache" / "invalidation"
        )
        
        # 增强错误处理器
        self.error_handler = EnhancedErrorHandler(
            error_log_dir=Path(__file__).parent.parent / "logs" / "errors",
            max_error_history=500
        )
        
        # 兼容性：保留旧缓存接口
        self._render_cache = {}
        self._cache_max_size = 100
        
        # 渲染选项
        self.default_options = {
            'enable_zoom': True,
            'enable_syntax_highlight': True,
            'theme': 'default',
            'max_content_length': 5 * 1024 * 1024,  # 5MB
            'cache_enabled': True,
            'fallback_to_text': True,
            'use_dynamic_import': True  # 新增：控制是否使用动态导入
        }
        
        # 根据配置更新选项
        self._update_options_from_config()
        
        # 检查可用性
        self._check_availability()
    
    def _update_options_from_config(self):
        """根据配置更新渲染选项"""
        markdown_config = self.config_manager.get_markdown_config()
        
        # 更新动态导入设置
        if 'use_dynamic_import' in markdown_config:
            self.default_options['use_dynamic_import'] = markdown_config['use_dynamic_import']
        
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
    
    def _check_availability(self):
        """检查渲染组件的可用性"""
        # 检查动态导入的模块
        if self.default_options.get('use_dynamic_import', True):
            markdown_processor_result = self.module_importer.import_module('markdown_processor', ['markdown'])
            self.markdown_processor_available = markdown_processor_result['success']
            
            if self.markdown_processor_available:
                self.logger.info("动态导入markdown_processor成功")
                self._markdown_processor_functions = markdown_processor_result['functions']
            else:
                self.logger.warning(f"动态导入markdown_processor失败: {markdown_processor_result.get('message')}")
        
        # 检查备用模块
        self.markdown_available = MARKDOWN_AVAILABLE
        
        self.logger.info(f"Markdown处理器可用: {getattr(self, 'markdown_processor_available', False)}")
        self.logger.info(f"备用Markdown库可用: {self.markdown_available}")
        
        if not self.markdown_processor_available and not self.markdown_available:
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
                
                # 使用统一缓存管理器
                cached_result = self.cache_manager.get(cache_key)
                if cached_result is not None:
                    cached_result = cached_result.copy()
                    cached_result['cached'] = True
                    cached_result['render_time'] = time.time() - start_time
                    cached_result['cache_hit'] = True
                    return cached_result
                
                # 兼容性：检查旧缓存
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
                # 使用统一缓存管理器
                self.cache_manager.set(cache_key, result, ttl=3600)  # 1小时过期
                
                # 兼容性：同时更新旧缓存
                self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            # 使用增强错误处理器，保留完整错误上下文，避免丢失定位信息
            error_info = self.error_handler.handle_error(
                e,
                context={'operation': 'render', 'content_length': len(markdown_content) if markdown_content else 0},
                recovery_strategy=ErrorRecoveryStrategy.FALLBACK
            )

            self.logger.error(f"渲染失败: {e}")
            error_result = self._render_error_result("渲染失败", str(e))
            # 追加结构化错误信息供上层透传/落盘
            try:
                error_result['error_info'] = error_info.to_dict()
            except Exception:
                pass

            # 调试落盘：记录 fail.json，便于定位“只能跳一次”问题
            try:
                import json
                debug_dir = Path(__file__).parent.parent / 'debug_render'
                debug_dir.mkdir(parents=True, exist_ok=True)
                debug_file = debug_dir / 'content_render.fail.json'
                with open(debug_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'stage': 'render(content)',
                        'error': error_result.get('error_info', {}),
                        'message': str(e)
                    }, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            return error_result
    
    def render_file(self, file_path: Union[str, Path], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        渲染Markdown文件（重构：使用file_resolver统一路径解析）
        
        Args:
            file_path: 文件路径
            options: 渲染选项
            
        Returns:
            渲染结果字典
        """
        start_time = time.time()
        
        try:
            # 使用file_resolver统一路径解析
            resolve_options = {
                'max_size': self.default_options.get('max_content_length', 5 * 1024 * 1024),
                'read_content': True,  # 渲染需要读取文件内容
                'detect_encoding': True
            }
            
            # 解析文件路径
            resolve_result = self.file_resolver.resolve_file_path(file_path, resolve_options)
            
            if not resolve_result['success']:
                return self._render_error_result(
                    resolve_result['error_type'],
                    resolve_result['error_message']
                )
            
            # 获取文件内容
            content = resolve_result.get('content')
            if content is None:
                return self._render_error_result(
                    "文件读取失败",
                    "无法读取文件内容"
                )
            
            # 监控文件变化，用于缓存失效
            file_path = resolve_result['file_path']
            self.invalidation_manager.watch_file(file_path)
            
            # 渲染内容
            render_result = self.render(content, options)
            
            # 合并结果
            result = {
                **render_result,
                'file_path': resolve_result['file_path'],
                'file_info': resolve_result.get('file_info', {}),
                'encoding': resolve_result.get('encoding', {}),
                'total_time': time.time() - start_time
            }
            
            return result
            
        except Exception as e:
            # 使用增强错误处理器，保留完整错误上下文
            error_info = self.error_handler.handle_error(
                e,
                context={'operation': 'render_file', 'file_path': str(file_path)},
                recovery_strategy=ErrorRecoveryStrategy.FALLBACK
            )

            self.logger.error(f"文件渲染失败: {e}")
            error_result = self._render_error_result("文件渲染失败", str(e))
            try:
                error_result['error_info'] = error_info.to_dict()
            except Exception:
                pass

            # 调试落盘：记录 fail.json（以文件名区分）
            try:
                import json
                debug_dir = Path(__file__).parent.parent / 'debug_render'
                debug_dir.mkdir(parents=True, exist_ok=True)
                name = Path(str(file_path)).name if file_path else 'unknown.md'
                debug_file = debug_dir / f'{name}.fail.json'
                with open(debug_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'stage': 'render_file',
                        'file_path': str(file_path),
                        'error': error_result.get('error_info', {}),
                        'message': str(e)
                    }, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            return error_result
    
    def _render_content(self, content: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行实际的渲染操作（混合架构优先级渲染链）
        
        Args:
            content: Markdown内容
            options: 渲染选项
            
        Returns:
            渲染结果
        """
        # 优先级1: 使用动态导入的markdown_processor
        if (getattr(self, 'markdown_processor_available', False) and 
            self.default_options.get('use_dynamic_import', True)):
            try:
                render_func = self._markdown_processor_functions['render_markdown_with_zoom']
                if options.get('enable_zoom', True):
                    html_content = render_func(content)
                else:
                    render_func = self._markdown_processor_functions['render_markdown_to_html']
                    html_content = render_func(content)
                
                return {
                    'success': True,
                    'html': html_content,
                    'renderer': 'markdown_processor',
                    'options_used': options
                }
            except Exception as e:
                self.logger.warning(f"markdown_processor渲染失败: {e}")
        
        # 优先级2: 使用备用markdown库
        if self.markdown_available:
            try:
                md = markdown.Markdown(extensions=[
                    'markdown.extensions.tables',
                    'markdown.extensions.fenced_code',
                    'markdown.extensions.codehilite',
                    'markdown.extensions.toc'
                ])
                html_content = md.convert(content)
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
        # 清空统一缓存管理器
        self.cache_manager.clear()
        
        # 清空失效历史
        self.invalidation_manager.invalidation_history.clear()
        
        # 兼容性：清空旧缓存
        self._render_cache.clear()
        self.logger.info("渲染缓存已清空")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息（统一接口）"""
        # 获取统一缓存管理器统计信息
        unified_stats = self.cache_manager.get_stats()
        
        # 获取失效管理器统计信息
        invalidation_stats = self.invalidation_manager.get_invalidation_stats()
        
        # 获取错误统计信息
        error_stats = self.error_handler.get_error_stats()
        
        return {
            'total': unified_stats.total_entries,
            'limit': unified_stats.max_size,
            'cache_size': unified_stats.total_size,  # 兼容旧字段
            'max_size': unified_stats.max_size,      # 兼容旧字段
            'cache_keys': self.cache_manager.get_keys(),
            'hit_rate': unified_stats.hit_rate,
            'hit_count': unified_stats.hit_count,
            'miss_count': unified_stats.miss_count,
            'eviction_count': unified_stats.eviction_count,
            'memory_usage_mb': unified_stats.memory_usage,
            'strategy': self.cache_manager.strategy.value,
            'legacy_cache_size': len(self._render_cache),  # 旧缓存大小
            'invalidation_stats': invalidation_stats,
            'watched_files': len(self.invalidation_manager.file_watchers),
            'error_stats': error_stats.to_dict()
        }
    
    def is_available(self) -> bool:
        """
        检查渲染器是否可用
        
        Returns:
            是否可用
        """
        return (getattr(self, 'markdown_processor_available', False) or 
                self.markdown_available)
    
    def get_supported_features(self) -> Dict[str, bool]:
        """
        获取支持的功能列表
        
        Returns:
            功能支持情况字典
        """
        return {
            'markdown_processor': getattr(self, 'markdown_processor_available', False),
            'markdown_library': self.markdown_available,
            'syntax_highlight': self.markdown_available,
            'text_fallback': True,
            'unified_path_resolution': True,
            'dynamic_module_import': getattr(self, 'markdown_processor_available', False),
            'zoom_support': getattr(self, 'markdown_processor_available', False),
            'enhanced_error_handling': True,
            'unified_caching': True,
            'cache_invalidation': True
        }
    
    def get_error_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取错误历史
        
        Args:
            limit: 返回数量限制
            
        Returns:
            错误历史列表
        """
        return self.error_handler.get_error_history(limit)
    
    def save_error_report(self, filename: Optional[str] = None) -> bool:
        """
        保存错误报告
        
        Args:
            filename: 文件名
            
        Returns:
            是否保存成功
        """
        return self.error_handler.save_error_report(filename)
    
    def shutdown(self):
        """关闭渲染器，释放所有资源"""
        try:
            # 关闭错误处理器
            if hasattr(self, 'error_handler'):
                self.error_handler.shutdown()
            
            # 关闭缓存失效管理器
            if hasattr(self, 'invalidation_manager'):
                self.invalidation_manager.shutdown()
            
            # 关闭统一缓存管理器
            if hasattr(self, 'cache_manager'):
                self.cache_manager.shutdown()
            
            # 关闭动态模块导入器
            if hasattr(self, 'module_importer'):
                self.module_importer.clear_cache()
            
            self.logger.info("Markdown渲染器已关闭，所有资源已释放")
            
        except Exception as e:
            self.logger.error(f"关闭渲染器时出现错误: {e}")
    
    def __del__(self):
        """析构函数，确保资源被释放"""
        try:
            self.shutdown()
        except:
            pass  # 析构函数中忽略异常
    
# 向后兼容性：保留原类名作为别名
MarkdownRenderer = HybridMarkdownRenderer

# --- 文档注释：引用示例（仅供参考，非运行代码） ---
# 统一异常与通配删除工具的示例用法：
# from core.errors import FileReadError, ServiceNotFoundError, ErrorSeverity
# from cache.delete_pattern_utils import delete_pattern
# 
# 示例：在渲染前读取文件，捕获统一文件读取异常
# try:
# 	content = file_resolver.read_file(markdown_path)
# except FileReadError as e:
# 	logger.error(f"Read failed: {e}")
# 
# 示例：当需要失效与渲染相关的解析缓存时（缓存实现无 delete_pattern）
# removed = delete_pattern(resolution_cache, "link_resolution:abc123:*")
# logger.info(f"Invalidated {removed} resolution keys")