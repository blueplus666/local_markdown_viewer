#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高性能文件读取器 v1.0.0
解决文件读取瓶颈，提供异步读取、预读取、缓存等优化功能

作者: LAD Team
创建时间: 2025-08-16
最后更新: 2025-08-16
"""

import os
import asyncio
import threading
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from enum import Enum
import mmap
import hashlib

# 导入统一缓存管理器
from .unified_cache_manager import UnifiedCacheManager, CacheStrategy
from .enhanced_error_handler import EnhancedErrorHandler, ErrorRecoveryStrategy


class ReadStrategy(Enum):
    """读取策略枚举"""
    SYNC = "sync"           # 同步读取
    ASYNC = "async"         # 异步读取
    MAPPED = "mapped"       # 内存映射读取
    STREAMING = "streaming" # 流式读取
    PRELOAD = "preload"     # 预加载读取


class FileType(Enum):
    """文件类型枚举"""
    MARKDOWN = "markdown"   # Markdown文件
    TEXT = "text"           # 文本文件
    BINARY = "binary"       # 二进制文件
    UNKNOWN = "unknown"     # 未知类型


@dataclass
class FileInfo:
    """文件信息数据类"""
    path: str
    size: int
    modified_time: float
    file_type: FileType
    encoding: str
    checksum: str
    last_access: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['file_type'] = self.file_type.value
        return data


@dataclass
class ReadMetrics:
    """读取性能指标数据类"""
    read_time_ms: float
    bytes_read: int
    throughput_mbps: float
    cache_hit: bool
    strategy_used: str
    memory_usage_mb: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


class HighPerformanceFileReader:
    """高性能文件读取器"""
    
    def __init__(self, max_workers: int = 4, cache_size: int = 1000):
        """
        初始化高性能文件读取器
        
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
            default_ttl=3600,  # 1小时过期
            strategy=CacheStrategy.LRU,
            cache_dir=(None if getattr(self, "_fast_mode", False) else Path(__file__).parent.parent / "cache" / "file_reader")
        )
        
        # 增强错误处理器
        self.error_handler = EnhancedErrorHandler(
            error_log_dir=(None if getattr(self, "_fast_mode", False) else Path(__file__).parent.parent / "logs" / "errors"),
            max_error_history=200
        )
        
        # 文件信息缓存
        self.file_info_cache: Dict[str, FileInfo] = {}
        
        # 性能统计
        self.read_stats = {
            'total_reads': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_bytes': 0,
            'total_time_ms': 0.0,
            'strategy_usage': {}
        }
        
        # 预读取队列
        self.preload_queue: List[str] = []
        self.preload_thread = None
        self.preload_running = False
        
        # 启动预读取线程
        self._start_preload_thread()
        
        self.logger.info("高性能文件读取器初始化完成")
    
    def _start_preload_thread(self):
        """启动预读取线程"""
        if getattr(self, "_fast_mode", False):
            return
        if self.preload_thread is None or not self.preload_thread.is_alive():
            self.preload_running = True
            self.preload_thread = threading.Thread(target=self._preload_worker, daemon=True)
            self.preload_thread.start()
            self.logger.info("预读取线程已启动")
    
    def _preload_worker(self):
        """预读取工作线程"""
        while self.preload_running:
            try:
                if self.preload_queue:
                    file_path = self.preload_queue.pop(0)
                    self._preload_file(file_path)
                else:
                    time.sleep(0.01 if getattr(self, "_fast_mode", False) else 0.1)  # 等待新文件
            except Exception as e:
                self.logger.error(f"预读取线程错误: {e}")
                time.sleep(1)
    
    def _preload_file(self, file_path: str):
        """预读取文件"""
        try:
            if os.path.exists(file_path):
                # 异步预读取文件内容
                future = self.executor.submit(self._read_file_content, file_path)
                future.add_done_callback(lambda f: self._on_preload_complete(file_path, f))
        except Exception as e:
            self.logger.error(f"预读取文件失败 {file_path}: {e}")
    
    def _on_preload_complete(self, file_path: str, future):
        """预读取完成回调"""
        try:
            result = future.result()
            if result['success']:
                self.logger.debug(f"文件预读取完成: {file_path}")
        except Exception as e:
            self.logger.error(f"预读取完成处理失败 {file_path}: {e}")
    
    def _detect_file_type(self, file_path: str) -> FileType:
        """检测文件类型"""
        try:
            ext = Path(file_path).suffix.lower()
            if ext in ['.md', '.markdown']:
                return FileType.MARKDOWN
            elif ext in ['.txt', '.text']:
                return FileType.TEXT
            else:
                # 尝试读取文件头来判断
                with open(file_path, 'rb') as f:
                    header = f.read(1024)
                    if b'\x00' in header:
                        return FileType.BINARY
                    else:
                        return FileType.TEXT
        except Exception:
            return FileType.UNKNOWN
    
    def _detect_encoding(self, file_path: str) -> str:
        """检测文件编码"""
        try:
            import chardet
            with open(file_path, 'rb') as f:
                raw_len = 1024 if getattr(self, "_fast_mode", False) else 10000
                raw_data = f.read(raw_len)
                result = chardet.detect(raw_data)
                return result['encoding'] or 'utf-8'
        except ImportError:
            # 如果没有chardet，使用默认编码
            return 'utf-8'
        except Exception:
            return 'utf-8'
    
    def _calculate_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        try:
            if getattr(self, "_fast_mode", False):
                return ""
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def _get_file_info(self, file_path: str) -> FileInfo:
        """获取文件信息"""
        try:
            stat = os.stat(file_path)
            file_type = self._detect_file_type(file_path)
            encoding = self._detect_encoding(file_path)
            checksum = self._calculate_checksum(file_path)
            
            return FileInfo(
                path=file_path,
                size=stat.st_size,
                modified_time=stat.st_mtime,
                file_type=file_type,
                encoding=encoding,
                checksum=checksum,
                last_access=time.time()
            )
        except Exception as e:
            self.logger.error(f"获取文件信息失败 {file_path}: {e}")
            return None
    
    def _read_file_content(self, file_path: str, strategy: ReadStrategy = ReadStrategy.SYNC) -> Dict[str, Any]:
        """读取文件内容"""
        start_time = time.time()
        
        try:
            file_info = self._get_file_info(file_path)
            if not file_info:
                return {'success': False, 'error': '无法获取文件信息'}
            
            # 根据策略选择读取方法
            if strategy == ReadStrategy.MAPPED and file_info.size > 0:
                content = self._read_mapped(file_path, file_info)
            elif strategy == ReadStrategy.STREAMING and file_info.size > 1024 * 1024:  # 1MB以上使用流式
                content = self._read_streaming(file_path, file_info)
            else:
                content = self._read_sync(file_path, file_info)
            
            if content['success']:
                read_time = (time.time() - start_time) * 1000
                bytes_read = len(content['content'].encode('utf-8'))
                throughput = (bytes_read / 1024 / 1024) / (read_time / 1000)  # MB/s
                
                # 更新统计信息
                self.read_stats['total_reads'] += 1
                self.read_stats['total_bytes'] += bytes_read
                self.read_stats['total_time_ms'] += read_time
                self.read_stats['strategy_usage'][strategy.value] = self.read_stats['strategy_usage'].get(strategy.value, 0) + 1
                
                # 创建性能指标
                metrics = ReadMetrics(
                    read_time_ms=read_time,
                    bytes_read=bytes_read,
                    throughput_mbps=throughput,
                    cache_hit=False,
                    strategy_used=strategy.value,
                    memory_usage_mb=bytes_read / 1024 / 1024
                )
                
                content['metrics'] = metrics.to_dict()
                content['file_info'] = file_info.to_dict()
                
                # 缓存文件内容
                cache_key = f"file_content_{file_path}"
                self.cache_manager.set(cache_key, content, ttl=1800)  # 30分钟过期
                
                return content
            else:
                return content
                
        except Exception as e:
            # 使用增强错误处理器
            error_info = self.error_handler.handle_error(
                e, 
                context={'operation': 'file_read', 'file_path': file_path, 'strategy': strategy.value},
                recovery_strategy=ErrorRecoveryStrategy.FALLBACK
            )
            
            self.logger.error(f"文件读取失败 {file_path}: {e}")
            return {
                'success': False, 
                'error': str(e),
                'error_id': error_info.error_id,
                'error_category': error_info.category.value
            }
    
    def _read_sync(self, file_path: str, file_info: FileInfo) -> Dict[str, Any]:
        """同步读取文件"""
        try:
            with open(file_path, 'r', encoding=file_info.encoding, errors='replace') as f:
                content = f.read()
                return {'success': True, 'content': content}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _read_mapped(self, file_path: str, file_info: FileInfo) -> Dict[str, Any]:
        """内存映射读取文件"""
        try:
            with open(file_path, 'rb') as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    content = mm.read().decode(file_info.encoding, errors='replace')
                    return {'success': True, 'content': content}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _read_streaming(self, file_path: str, file_info: FileInfo) -> Dict[str, Any]:
        """流式读取文件"""
        try:
            content = ""
            with open(file_path, 'r', encoding=file_info.encoding, errors='replace') as f:
                for chunk in iter(lambda: f.read(8192), ""):
                    content += chunk
            return {'success': True, 'content': content}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def read_file(self, file_path: str, strategy: ReadStrategy = ReadStrategy.SYNC) -> Dict[str, Any]:
        """
        读取文件
        
        Args:
            file_path: 文件路径
            strategy: 读取策略
            
        Returns:
            读取结果
        """
        # 检查缓存
        cache_key = f"file_content_{file_path}"
        cached_content = self.cache_manager.get(cache_key)
        
        if cached_content is not None:
            self.read_stats['cache_hits'] += 1
            cached_content['cache_hit'] = True
            cached_content['metrics']['cache_hit'] = True
            return cached_content
        
        self.read_stats['cache_misses'] += 1
        
        # 执行读取
        return self._read_file_content(file_path, strategy)
    
    def read_file_async(self, file_path: str, strategy: ReadStrategy = ReadStrategy.ASYNC) -> asyncio.Future:
        """
        异步读取文件
        
        Args:
            file_path: 文件路径
            strategy: 读取策略
            
        Returns:
            异步Future对象
        """
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(self.executor, self.read_file, file_path, strategy)
    
    def preload_file(self, file_path: str):
        """
        预加载文件
        
        Args:
            file_path: 文件路径
        """
        if file_path not in self.preload_queue:
            self.preload_queue.append(file_path)
            self.logger.debug(f"文件已加入预加载队列: {file_path}")
    
    def read_multiple_files(self, file_paths: List[str], strategy: ReadStrategy = ReadStrategy.SYNC) -> List[Dict[str, Any]]:
        """
        批量读取多个文件
        
        Args:
            file_paths: 文件路径列表
            strategy: 读取策略
            
        Returns:
            读取结果列表
        """
        results = []
        
        # 使用线程池并发读取
        futures = []
        for file_path in file_paths:
            future = self.executor.submit(self.read_file, file_path, strategy)
            futures.append((file_path, future))
        
        # 收集结果
        for file_path, future in futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                self.logger.error(f"批量读取失败 {file_path}: {e}")
                results.append({'success': False, 'error': str(e), 'file_path': file_path})
        
        return results
    
    def get_file_info(self, file_path: str) -> Optional[FileInfo]:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息
        """
        if file_path in self.file_info_cache:
            return self.file_info_cache[file_path]
        
        file_info = self._get_file_info(file_path)
        if file_info:
            self.file_info_cache[file_path] = file_info
        
        return file_info
    
    def get_read_stats(self) -> Dict[str, Any]:
        """
        获取读取统计信息
        
        Returns:
            统计信息字典
        """
        # 获取缓存统计信息
        cache_stats = self.cache_manager.get_stats()
        
        # 计算平均性能指标
        avg_read_time = (self.read_stats['total_time_ms'] / self.read_stats['total_reads'] 
                        if self.read_stats['total_reads'] > 0 else 0)
        avg_throughput = (self.read_stats['total_bytes'] / 1024 / 1024) / (self.read_stats['total_time_ms'] / 1000)
        
        return {
            'total_reads': self.read_stats['total_reads'],
            'cache_hits': self.read_stats['cache_hits'],
            'cache_misses': self.read_stats['cache_misses'],
            'cache_hit_rate': (self.read_stats['cache_hits'] / self.read_stats['total_reads'] 
                              if self.read_stats['total_reads'] > 0 else 0),
            'total_bytes': self.read_stats['total_bytes'],
            'total_time_ms': self.read_stats['total_time_ms'],
            'avg_read_time_ms': avg_read_time,
            'avg_throughput_mbps': avg_throughput,
            'strategy_usage': self.read_stats['strategy_usage'],
            'cache_stats': cache_stats.to_dict(),
            'preload_queue_size': len(self.preload_queue)
        }
    
    def clear_cache(self):
        """清空缓存"""
        self.cache_manager.clear()
        self.file_info_cache.clear()
        self.logger.info("文件读取器缓存已清空")
    
    def shutdown(self):
        """关闭文件读取器"""
        try:
            # 停止预读取线程
            self.preload_running = False
            if self.preload_thread and self.preload_thread.is_alive():
                self.preload_thread.join(timeout=5)
            
            # 关闭线程池
            self.executor.shutdown(wait=True)
            
            # 关闭缓存管理器
            self.cache_manager.shutdown()
            
            # 关闭错误处理器
            self.error_handler.shutdown()
            
            self.logger.info("高性能文件读取器已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭文件读取器时出现错误: {e}")
    
    def __del__(self):
        """析构函数"""
        try:
            self.shutdown()
        except:
            pass 