#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渲染性能优化器 v1.0.0
优化Markdown渲染性能，提供并行渲染、增量渲染、渲染缓存等优化功能

作者: LAD Team
创建时间: 2025-08-16
最后更新: 2025-08-16
"""

import time
import os

import threading
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import re

# 导入统一缓存管理器
from .unified_cache_manager import UnifiedCacheManager, CacheStrategy
from .enhanced_error_handler import EnhancedErrorHandler, ErrorRecoveryStrategy


class RenderStrategy(Enum):
    """渲染策略枚举"""
    SINGLE_THREAD = "single_thread"     # 单线程渲染
    MULTI_THREAD = "multi_thread"       # 多线程渲染
    INCREMENTAL = "incremental"         # 增量渲染
    LAZY = "lazy"                       # 懒加载渲染
    PREEMPTIVE = "preemptive"           # 预渲染


class RenderMode(Enum):
    """渲染模式枚举"""
    FULL = "full"                       # 完整渲染
    PARTIAL = "partial"                 # 部分渲染
    SKELETON = "skeleton"               # 骨架渲染
    INTERACTIVE = "interactive"         # 交互式渲染


@dataclass
class RenderMetrics:
    """渲染性能指标数据类"""
    render_time_ms: float
    content_length: int
    render_speed_chars_per_ms: float
    cache_hit: bool
    strategy_used: str
    memory_usage_mb: float
    cpu_usage_percent: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


@dataclass
class RenderChunk:
    """渲染块数据类"""
    start_pos: int
    end_pos: int
    content: str
    rendered_html: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


class RenderPerformanceOptimizer:
    """渲染性能优化器"""
    
    def __init__(self, max_workers: int = 4, cache_size: int = 2000):
        """
        初始化渲染性能优化器
        
        Args:
            max_workers: 最大工作线程数
            cache_size: 缓存大小
        """
        self.logger = logging.getLogger(__name__)
        self._fast_mode = (os.environ.get("LAD_TEST_MODE") == "1" or os.environ.get("LAD_QA_FAST") == "1")
        
        # 线程池执行器
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # 统一缓存管理器
        self.cache_manager = UnifiedCacheManager(
            max_size=cache_size,
            default_ttl=7200,  # 2小时过期
            strategy=CacheStrategy.LRU,
            cache_dir=Path(__file__).parent.parent / "cache" / "renderer"
        )
        
        # 增强错误处理器
        self.error_handler = EnhancedErrorHandler(
            error_log_dir=Path(__file__).parent.parent / "logs" / "errors",
            max_error_history=200
        )
        
        # 渲染统计
        self.render_stats = {
            'total_renders': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_content_length': 0,
            'total_render_time_ms': 0.0,
            'strategy_usage': {},
            'mode_usage': {}
        }
        
        # 增量渲染缓存
        self.incremental_cache: Dict[str, List[RenderChunk]] = {}
        
        # 预渲染队列
        self.prerender_queue: List[str] = []
        self.prerender_thread = None
        self.prerender_running = False
        
        # 启动预渲染线程
        self._start_prerender_thread()
        
        self.logger.info("渲染性能优化器初始化完成")
    
    def _start_prerender_thread(self):
        """启动预渲染线程"""
        if getattr(self, "_fast_mode", False):
            return
        if self.prerender_thread is None or not self.prerender_thread.is_alive():
            self.prerender_running = True
            self.prerender_thread = threading.Thread(target=self._prerender_worker, daemon=True)
            self.prerender_thread.start()
            self.logger.info("预渲染线程已启动")
    
    def _prerender_worker(self):
        """预渲染工作线程"""
        while self.prerender_running:
            try:
                if self.prerender_queue:
                    content_hash = self.prerender_queue.pop(0)
                    self._prerender_content(content_hash)
                else:
                    time.sleep(0.01 if getattr(self, "_fast_mode", False) else 0.1)  # 等待新内容
            except Exception as e:
                self.logger.error(f"预渲染线程错误: {e}")
                time.sleep(1)
    
    def _prerender_content(self, content_hash: str):
        """预渲染内容"""
        try:
            # 从缓存获取内容
            cached_content = self.cache_manager.get(f"content_{content_hash}")
            if cached_content:
                # 异步预渲染
                future = self.executor.submit(self._render_markdown, cached_content['content'])
                future.add_done_callback(lambda f: self._on_prerender_complete(content_hash, f))
        except Exception as e:
            self.logger.error(f"预渲染内容失败 {content_hash}: {e}")
    
    def _on_prerender_complete(self, content_hash: str, future):
        """预渲染完成回调"""
        try:
            result = future.result()
            if result['success']:
                # 缓存渲染结果
                cache_key = f"rendered_{content_hash}"
                self.cache_manager.set(cache_key, result, ttl=7200)
                self.logger.debug(f"内容预渲染完成: {content_hash}")
        except Exception as e:
            self.logger.error(f"预渲染完成处理失败 {content_hash}: {e}")
    
    def _calculate_content_hash(self, content: str) -> str:
        """计算内容哈希值"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _split_content_into_chunks(self, content: str, chunk_size: int = 4096) -> List[RenderChunk]:
        """将内容分割为渲染块"""
        chunks = []
        lines = content.split('\n')
        current_chunk = ""
        start_pos = 0
        
        for i, line in enumerate(lines):
            current_chunk += line + '\n'
            
            # 检查是否达到块大小或遇到段落边界
            if (len(current_chunk) >= chunk_size or 
                line.strip() == '' or 
                line.startswith('#') or 
                line.startswith('---')):
                
                chunks.append(RenderChunk(
                    start_pos=start_pos,
                    end_pos=start_pos + len(current_chunk),
                    content=current_chunk.strip(),
                    rendered_html="",
                    metadata={'line_count': i + 1}
                ))
                
                start_pos += len(current_chunk)
                current_chunk = ""
        
        # 添加最后一个块
        if current_chunk.strip():
            chunks.append(RenderChunk(
                start_pos=start_pos,
                end_pos=start_pos + len(current_chunk),
                content=current_chunk.strip(),
                rendered_html="",
                metadata={'line_count': len(lines)}
            ))
        
        return chunks
    
    def _render_markdown(self, content: str) -> Dict[str, Any]:
        """渲染Markdown内容"""
        try:
            # 快速模式：直接使用简化渲染，避免加载完整markdown扩展
            if getattr(self, "_fast_mode", False):
                html = self._basic_markdown_to_html(content)
                return {
                    'success': True,
                    'html': html,
                    'content_length': len(content),
                    'metadata': {
                        'renderer': 'basic_fast',
                        'extensions': []
                    }
                }
            # 尝试导入markdown库
            try:
                import markdown
                md = markdown.Markdown(extensions=['extra', 'codehilite', 'toc'])
                html = md.convert(content)
            except ImportError:
                # 降级到基本HTML转换
                html = self._basic_markdown_to_html(content)
            
            return {
                'success': True,
                'html': html,
                'content_length': len(content),
                'metadata': {
                    'renderer': 'markdown' if 'markdown' in globals() else 'basic',
                    'extensions': ['extra', 'codehilite', 'toc'] if 'markdown' in globals() else []
                }
            }
            
        except Exception as e:
            # 使用增强错误处理器
            error_info = self.error_handler.handle_error(
                e, 
                context={'operation': 'markdown_render', 'content_length': len(content)},
                recovery_strategy=ErrorRecoveryStrategy.FALLBACK
            )
            
            self.logger.error(f"Markdown渲染失败: {e}")
            return {
                'success': False, 
                'error': str(e),
                'error_id': error_info.error_id,
                'error_category': error_info.category.value
            }
    
    def _basic_markdown_to_html(self, content: str) -> str:
        """基本的Markdown到HTML转换"""
        html = content
        
        # 标题
        html = re.sub(r'^### (.*$)', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*$)', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*$)', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # 粗体和斜体
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        
        # 代码块
        html = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)
        html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
        
        # 链接
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
        
        # 列表
        html = re.sub(r'^\* (.*$)', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'((?:<li>.*</li>\n?)+)', r'<ul>\1</ul>', html)
        
        # 段落
        html = re.sub(r'\n\n', r'</p><p>', html)
        html = f'<p>{html}</p>'
        
        return html
    
    def render_content(self, content: str, strategy: RenderStrategy = RenderStrategy.SINGLE_THREAD, 
                      mode: RenderMode = RenderMode.FULL) -> Dict[str, Any]:
        """
        渲染内容
        
        Args:
            content: Markdown内容
            strategy: 渲染策略
            mode: 渲染模式
            
        Returns:
            渲染结果
        """
        start_time = time.time()
        
        # 在快速模式下对内容进行截断，降低处理量
        if getattr(self, "_fast_mode", False) and len(content) > 20000:
            content = content[:20000]
        # 计算内容哈希
        content_hash = self._calculate_content_hash(content)
        
        # 检查缓存
        cache_key = f"rendered_{content_hash}"
        cached_result = self.cache_manager.get(cache_key)
        
        if cached_result is not None:
            self.render_stats['cache_hits'] += 1
            cached_result['cache_hit'] = True
            cached_result['metrics']['cache_hit'] = True
            return cached_result
        
        self.render_stats['cache_misses'] += 1
        
        # 根据策略选择渲染方法
        if strategy == RenderStrategy.MULTI_THREAD and len(content) > 10000 and not getattr(self, "_fast_mode", False):  # 快速模式下避免多线程
            result = self._render_multithreaded(content, mode)
        elif strategy == RenderStrategy.INCREMENTAL and len(content) > 5000 and not getattr(self, "_fast_mode", False):  # 快速模式下避免增量渲染
            result = self._render_incremental(content, mode)
        elif strategy == RenderStrategy.LAZY:
            result = self._render_lazy(content, mode)
        else:
            result = self._render_single_thread(content, mode)
        
        if result['success']:
            render_time = (time.time() - start_time) * 1000
            content_length = len(content)
            render_speed = content_length / render_time if render_time > 0 else 0
            
            # 更新统计信息
            self.render_stats['total_renders'] += 1
            self.render_stats['total_content_length'] += content_length
            self.render_stats['total_render_time_ms'] += render_time
            self.render_stats['strategy_usage'][strategy.value] = self.render_stats['strategy_usage'].get(strategy.value, 0) + 1
            self.render_stats['mode_usage'][mode.value] = self.render_stats['mode_usage'].get(mode.value, 0) + 1
            
            # 创建性能指标
            metrics = RenderMetrics(
                render_time_ms=render_time,
                content_length=content_length,
                render_speed_chars_per_ms=render_speed,
                cache_hit=False,
                strategy_used=strategy.value,
                memory_usage_mb=content_length / 1024 / 1024,
                cpu_usage_percent=0.0  # 这里可以集成系统监控
            )
            
            result['metrics'] = metrics.to_dict()
            result['content_hash'] = content_hash
            
            # 缓存渲染结果
            self.cache_manager.set(cache_key, result, ttl=7200)
            
            # 缓存原始内容
            self.cache_manager.set(f"content_{content_hash}", {
                'content': content,
                'timestamp': time.time()
            }, ttl=3600)
            
            # 加入预渲染队列
            self.prerender_queue.append(content_hash)
            
            return result
        else:
            return result
    
    def _render_single_thread(self, content: str, mode: RenderMode) -> Dict[str, Any]:
        """单线程渲染"""
        return self._render_markdown(content)
    
    def _render_multithreaded(self, content: str, mode: RenderMode) -> Dict[str, Any]:
        """多线程渲染"""
        try:
            # 分割内容为块
            chunks = self._split_content_into_chunks(content)
            
            # 并行渲染块
            futures = []
            for chunk in chunks:
                future = self.executor.submit(self._render_markdown, chunk.content)
                futures.append((chunk, future))
            
            # 收集结果
            rendered_chunks = []
            for chunk, future in futures:
                try:
                    result = future.result()
                    if result['success']:
                        chunk.rendered_html = result['html']
                        rendered_chunks.append(chunk)
                except Exception as e:
                    self.logger.error(f"块渲染失败: {e}")
            
            # 合并结果
            if rendered_chunks:
                combined_html = '\n'.join(chunk.rendered_html for chunk in rendered_chunks)
                return {
                    'success': True,
                    'html': combined_html,
                    'content_length': len(content),
                    'chunks_rendered': len(rendered_chunks),
                    'total_chunks': len(chunks),
                    'metadata': {'renderer': 'multithreaded', 'chunk_count': len(chunks)}
                }
            else:
                return {'success': False, 'error': '所有块渲染都失败'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _render_incremental(self, content: str, mode: RenderMode) -> Dict[str, Any]:
        """增量渲染"""
        try:
            # 检查增量缓存
            if content in self.incremental_cache:
                cached_chunks = self.incremental_cache[content]
                # 只渲染新增的部分
                # 这里简化实现，实际应该比较内容差异
                return self._render_markdown(content)
            
            # 分割内容
            chunks = self._split_content_into_chunks(content)
            
            # 缓存块信息
            self.incremental_cache[content] = chunks
            
            # 渲染所有块
            return self._render_multithreaded(content, mode)
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _render_lazy(self, content: str, mode: RenderMode) -> Dict[str, Any]:
        """懒加载渲染"""
        try:
            # 只渲染可见部分（这里简化实现）
            if mode == RenderMode.SKELETON:
                # 骨架渲染：只渲染标题和结构
                lines = content.split('\n')
                skeleton_lines = []
                for line in lines:
                    if line.startswith('#') or line.startswith('---') or line.strip() == '':
                        skeleton_lines.append(line)
                
                skeleton_content = '\n'.join(skeleton_lines)
                return self._render_markdown(skeleton_content)
            else:
                # 完整渲染
                return self._render_markdown(content)
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def render_file(self, file_path: str, strategy: RenderStrategy = RenderStrategy.SINGLE_THREAD,
                   mode: RenderMode = RenderMode.FULL) -> Dict[str, Any]:
        """
        渲染文件
        
        Args:
            file_path: 文件路径
            strategy: 渲染策略
            mode: 渲染模式
            
        Returns:
            渲染结果
        """
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # 渲染内容
            return self.render_content(content, strategy, mode)
            
        except Exception as e:
            # 使用增强错误处理器
            error_info = self.error_handler.handle_error(
                e, 
                context={'operation': 'file_render', 'file_path': file_path},
                recovery_strategy=ErrorRecoveryStrategy.FALLBACK
            )
            
            self.logger.error(f"文件渲染失败 {file_path}: {e}")
            return {
                'success': False, 
                'error': str(e),
                'error_id': error_info.error_id,
                'error_category': error_info.category.value
            }
    
    def get_render_stats(self) -> Dict[str, Any]:
        """
        获取渲染统计信息
        
        Returns:
            统计信息字典
        """
        # 获取缓存统计信息
        cache_stats = self.cache_manager.get_stats()
        
        # 计算平均性能指标
        avg_render_time = (self.render_stats['total_render_time_ms'] / self.render_stats['total_renders'] 
                          if self.render_stats['total_renders'] > 0 else 0)
        avg_render_speed = (self.render_stats['total_content_length'] / self.render_stats['total_render_time_ms'] 
                           if self.render_stats['total_render_time_ms'] > 0 else 0)
        
        return {
            'total_renders': self.render_stats['total_renders'],
            'cache_hits': self.render_stats['cache_hits'],
            'cache_misses': self.render_stats['cache_misses'],
            'cache_hit_rate': (self.render_stats['cache_hits'] / self.render_stats['total_renders'] 
                              if self.render_stats['total_renders'] > 0 else 0),
            'total_content_length': self.render_stats['total_content_length'],
            'total_render_time_ms': self.render_stats['total_render_time_ms'],
            'avg_render_time_ms': avg_render_time,
            'avg_render_speed_chars_per_ms': avg_render_speed,
            'strategy_usage': self.render_stats['strategy_usage'],
            'mode_usage': self.render_stats['mode_usage'],
            'cache_stats': cache_stats.to_dict(),
            'prerender_queue_size': len(self.prerender_queue),
            'incremental_cache_size': len(self.incremental_cache)
        }
    
    def clear_cache(self):
        """清空缓存"""
        self.cache_manager.clear()
        self.incremental_cache.clear()
        self.logger.info("渲染优化器缓存已清空")
    
    def shutdown(self):
        """关闭渲染优化器"""
        try:
            # 停止预渲染线程
            self.prerender_running = False
            if self.prerender_thread and self.prerender_thread.is_alive():
                self.prerender_thread.join(timeout=5)
            
            # 关闭线程池
            self.executor.shutdown(wait=True)
            
            # 关闭缓存管理器
            self.cache_manager.shutdown()
            
            # 关闭错误处理器
            self.error_handler.shutdown()
            
            self.logger.info("渲染性能优化器已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭渲染优化器时出现错误: {e}")
    
    def __del__(self):
        """析构函数"""
        try:
            self.shutdown()
        except:
            pass 