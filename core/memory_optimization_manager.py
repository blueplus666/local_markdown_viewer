#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内存优化管理器 v1.0.0
优化内存使用，提供内存监控、垃圾回收、内存池等优化功能

作者: LAD Team
创建时间: 2025-08-16
最后更新: 2025-08-16
"""

import os
import gc
import psutil
import threading
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import weakref
import sys

# 导入统一缓存管理器
from .unified_cache_manager import UnifiedCacheManager, CacheStrategy
from .enhanced_error_handler import EnhancedErrorHandler, ErrorRecoveryStrategy


class MemoryStrategy(Enum):
    """内存策略枚举"""
    AGGRESSIVE = "aggressive"     # 激进内存回收
    BALANCED = "balanced"         # 平衡内存管理
    CONSERVATIVE = "conservative" # 保守内存管理
    ADAPTIVE = "adaptive"         # 自适应内存管理


class MemoryThreshold(Enum):
    """内存阈值枚举"""
    LOW = "low"           # 低内存阈值
    MEDIUM = "medium"     # 中等内存阈值
    HIGH = "high"         # 高内存阈值
    CRITICAL = "critical" # 临界内存阈值


@dataclass
class MemoryInfo:
    """内存信息数据类"""
    total_memory_mb: float
    available_memory_mb: float
    used_memory_mb: float
    memory_percent: float
    swap_total_mb: float
    swap_used_mb: float
    swap_percent: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


@dataclass
class MemoryMetrics:
    """内存性能指标数据类"""
    current_usage_mb: float
    peak_usage_mb: float
    gc_collections: int
    gc_time_ms: float
    memory_efficiency: float
    cache_memory_mb: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


class MemoryPool:
    """内存池类"""
    
    def __init__(self, pool_size: int = 1000):
        """
        初始化内存池
        
        Args:
            pool_size: 池大小
        """
        self.pool_size = pool_size
        self.available_objects = []
        self.used_objects = set()
        self.lock = threading.Lock()
    
    def get_object(self):
        """获取对象"""
        with self.lock:
            if self.available_objects:
                obj = self.available_objects.pop()
                self.used_objects.add(obj)
                return obj
            else:
                # 创建新对象
                obj = self._create_object()
                self.used_objects.add(obj)
                return obj
    
    def return_object(self, obj):
        """返回对象"""
        with self.lock:
            if obj in self.used_objects:
                self.used_objects.remove(obj)
                if len(self.available_objects) < self.pool_size:
                    self.available_objects.append(obj)
    
    def _create_object(self):
        """创建对象（子类重写）"""
        return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            return {
                'pool_size': self.pool_size,
                'available_count': len(self.available_objects),
                'used_count': len(self.used_objects),
                'utilization': len(self.used_objects) / self.pool_size if self.pool_size > 0 else 0
            }


class StringPool(MemoryPool):
    """字符串池"""
    
    def _create_object(self):
        """创建字符串对象"""
        return ""
    
    def get_string(self, content: str) -> str:
        """获取字符串（可能从池中获取）"""
        obj = self.get_object()
        if isinstance(obj, str):
            return obj
        else:
            return content


class MemoryOptimizationManager:
    """内存优化管理器"""
    
    def __init__(self, strategy: MemoryStrategy = MemoryStrategy.BALANCED, 
                 monitoring_interval: float = 5.0):
        """
        初始化内存优化管理器
        
        Args:
            strategy: 内存策略
            monitoring_interval: 监控间隔（秒）
        """
        self.logger = logging.getLogger(__name__)
        self._fast_mode = (os.environ.get("LAD_TEST_MODE") == "1" or os.environ.get("LAD_QA_FAST") == "1")
        self.strategy = strategy
        self.monitoring_interval = monitoring_interval
        
        # 统一缓存管理器
        self.cache_manager = UnifiedCacheManager(
            max_size=500,  # 较小的缓存大小
            default_ttl=1800,  # 30分钟过期
            strategy=CacheStrategy.LRU,
            cache_dir=(None if getattr(self, "_fast_mode", False) else Path(__file__).parent.parent / "cache" / "memory")
        )
        
        # 增强错误处理器
        self.error_handler = EnhancedErrorHandler(
            error_log_dir=(None if getattr(self, "_fast_mode", False) else Path(__file__).parent.parent / "logs" / "errors"),
            max_error_history=100
        )
        
        # 内存池
        self.string_pool = StringPool(1000)
        
        # 内存监控
        self.memory_monitor_thread = None
        self.monitoring_running = False
        
        # 内存统计
        self.memory_stats = {
            'total_allocations': 0,
            'total_deallocations': 0,
            'peak_memory_mb': 0.0,
            'gc_collections': 0,
            'gc_time_ms': 0.0,
            'memory_warnings': 0,
            'strategy_changes': 0
        }
        
        # 内存阈值配置
        self.memory_thresholds = {
            MemoryThreshold.LOW: 0.3,      # 30%
            MemoryThreshold.MEDIUM: 0.5,   # 50%
            MemoryThreshold.HIGH: 0.7,     # 70%
            MemoryThreshold.CRITICAL: 0.9  # 90%
        }
 
        self._manual_override_timestamp = 0.0

        # 启动内存监控
        self._start_memory_monitor()
        
        self.logger.info("内存优化管理器初始化完成")
    
    def _start_memory_monitor(self):
        """启动内存监控"""
        if getattr(self, "_fast_mode", False):
            return
        if self.memory_monitor_thread is None or not self.memory_monitor_thread.is_alive():
            self.monitoring_running = True
            self.memory_monitor_thread = threading.Thread(target=self._memory_monitor_worker, daemon=True)
            self.memory_monitor_thread.start()
            self.logger.info("内存监控线程已启动")
    
    def _memory_monitor_worker(self):
        """内存监控工作线程"""
        while self.monitoring_running:
            try:
                memory_info = self._get_memory_info()
                self._check_memory_thresholds(memory_info)

                if self.strategy == MemoryStrategy.ADAPTIVE:
                    if time.time() - self._manual_override_timestamp > max(self.monitoring_interval, 5.0):
                        self._adaptive_strategy_adjustment()

                self._update_memory_stats(memory_info)
                time.sleep(self.monitoring_interval)

            except Exception as e:
                self.logger.error(f"内存监控错误: {e}")
                time.sleep(self.monitoring_interval)
    
    def _get_memory_info(self) -> MemoryInfo:
        """获取内存信息"""
        try:
            process = psutil.Process(os.getpid())
            memory = process.memory_info()
            
            # 系统内存信息
            system_memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return MemoryInfo(
                total_memory_mb=system_memory.total / 1024 / 1024,
                available_memory_mb=system_memory.available / 1024 / 1024,
                used_memory_mb=system_memory.used / 1024 / 1024,
                memory_percent=system_memory.percent / 100,
                swap_total_mb=swap.total / 1024 / 1024,
                swap_used_mb=swap.used / 1024 / 1024,
                swap_percent=swap.percent / 100
            )
        except Exception as e:
            self.logger.error(f"获取内存信息失败: {e}")
            # 返回默认值
            return MemoryInfo(
                total_memory_mb=1024.0,
                available_memory_mb=512.0,
                used_memory_mb=512.0,
                memory_percent=0.5,
                swap_total_mb=1024.0,
                swap_used_mb=0.0,
                swap_percent=0.0
            )
    
    def _check_memory_thresholds(self, memory_info: MemoryInfo):
        """检查内存阈值"""
        try:
            current_usage = memory_info.memory_percent
            
            if current_usage >= self.memory_thresholds[MemoryThreshold.CRITICAL]:
                self.logger.warning(f"内存使用达到临界阈值: {current_usage:.1%}")
                self._handle_critical_memory()
            elif current_usage >= self.memory_thresholds[MemoryThreshold.HIGH]:
                self.logger.warning(f"内存使用达到高阈值: {current_usage:.1%}")
                self._handle_high_memory()
            elif current_usage >= self.memory_thresholds[MemoryThreshold.MEDIUM]:
                self.logger.info(f"内存使用达到中等阈值: {current_usage:.1%}")
                self._handle_medium_memory()
            elif current_usage >= self.memory_thresholds[MemoryThreshold.LOW]:
                self.logger.debug(f"内存使用达到低阈值: {current_usage:.1%}")
                self._handle_low_memory()
                
        except Exception as e:
            self.logger.error(f"检查内存阈值失败: {e}")
    
    def _handle_critical_memory(self):
        """处理临界内存情况"""
        try:
            # 强制垃圾回收
            self._force_garbage_collection()
            
            # 清空缓存
            self._clear_caches()
            
            # 调整内存策略
            self._adjust_memory_strategy(MemoryStrategy.AGGRESSIVE)
            
            self.memory_stats['memory_warnings'] += 1
            
        except Exception as e:
            self.logger.error(f"处理临界内存失败: {e}")
    
    def _handle_high_memory(self):
        """处理高内存情况"""
        try:
            # 执行垃圾回收
            self._garbage_collection()
            
            # 清理内存池
            self._cleanup_memory_pools()
            
            # 调整内存策略
            self._adjust_memory_strategy(MemoryStrategy.BALANCED)
            
        except Exception as e:
            self.logger.error(f"处理高内存失败: {e}")
    
    def _handle_medium_memory(self):
        """处理中等内存情况"""
        try:
            # 轻度垃圾回收
            self._light_garbage_collection()
            
            # 调整内存策略
            self._adjust_memory_strategy(MemoryStrategy.BALANCED)
            
        except Exception as e:
            self.logger.error(f"处理中等内存失败: {e}")
    
    def _handle_low_memory(self):
        """处理低内存情况"""
        try:
            # 调整内存策略
            self._adjust_memory_strategy(MemoryStrategy.CONSERVATIVE)
            
        except Exception as e:
            self.logger.error(f"处理低内存失败: {e}")
    
    def _force_garbage_collection(self):
        """强制垃圾回收"""
        try:
            start_time = time.time()
            
            # 收集所有代
            collected = gc.collect()
            
            # 手动触发完整回收
            gc.collect(2)
            
            end_time = time.time()
            gc_time = (end_time - start_time) * 1000
            
            self.memory_stats['gc_collections'] += 1
            self.memory_stats['gc_time_ms'] += gc_time
            
            self.logger.info(f"强制垃圾回收完成，回收对象: {collected}, 耗时: {gc_time:.2f}ms")
            
        except Exception as e:
            self.logger.error(f"强制垃圾回收失败: {e}")
    
    def _garbage_collection(self):
        """执行垃圾回收"""
        try:
            start_time = time.time()
            
            # 收集第1代和第2代
            collected = gc.collect(1)
            
            end_time = time.time()
            gc_time = (end_time - start_time) * 1000
            
            self.memory_stats['gc_collections'] += 1
            self.memory_stats['gc_time_ms'] += gc_time
            
            self.logger.debug(f"垃圾回收完成，回收对象: {collected}, 耗时: {gc_time:.2f}ms")
            
        except Exception as e:
            self.logger.error(f"垃圾回收失败: {e}")
    
    def _light_garbage_collection(self):
        """轻度垃圾回收"""
        try:
            start_time = time.time()
            
            # 只收集第0代
            collected = gc.collect(0)
            
            end_time = time.time()
            gc_time = (end_time - start_time) * 1000
            
            self.memory_stats['gc_collections'] += 1
            self.memory_stats['gc_time_ms'] += gc_time
            
            self.logger.debug(f"轻度垃圾回收完成，回收对象: {collected}, 耗时: {gc_time:.2f}ms")
            
        except Exception as e:
            self.logger.error(f"轻度垃圾回收失败: {e}")
    
    def _clear_caches(self):
        """清空缓存"""
        try:
            # 清空统一缓存管理器
            self.cache_manager.clear()
            
            # 清空字符串池
            self.string_pool.available_objects.clear()
            
            self.logger.info("缓存已清空")
            
        except Exception as e:
            self.logger.error(f"清空缓存失败: {e}")
    
    def _cleanup_memory_pools(self):
        """清理内存池"""
        try:
            # 清理字符串池
            self.string_pool.available_objects.clear()
            
            self.logger.debug("内存池已清理")
            
        except Exception as e:
            self.logger.error(f"清理内存池失败: {e}")
    
    def _adjust_memory_strategy(self, new_strategy: MemoryStrategy):
        """调整内存策略"""
        if new_strategy != self.strategy:
            old_strategy = self.strategy
            self.strategy = new_strategy
            
            self.memory_stats['strategy_changes'] += 1
            
            self.logger.info(f"内存策略已调整: {old_strategy.value} -> {new_strategy.value}")
            
            # 根据新策略调整参数
            self._apply_memory_strategy()
    
    def _apply_memory_strategy(self):
        """应用内存策略"""
        try:
            if self.strategy == MemoryStrategy.AGGRESSIVE:
                # 激进策略：频繁GC，小缓存
                self.monitoring_interval = 2.0
                self.cache_manager.max_size = 200
                gc.set_threshold(100, 5, 5)  # 降低GC阈值
                
            elif self.strategy == MemoryStrategy.BALANCED:
                # 平衡策略：中等GC，中等缓存
                self.monitoring_interval = 5.0
                self.cache_manager.max_size = 500
                gc.set_threshold(700, 10, 10)  # 默认GC阈值
                
            elif self.strategy == MemoryStrategy.CONSERVATIVE:
                # 保守策略：较少GC，大缓存
                self.monitoring_interval = 10.0
                self.cache_manager.max_size = 1000
                gc.set_threshold(1000, 15, 15)  # 提高GC阈值
                
            elif self.strategy == MemoryStrategy.ADAPTIVE:
                # 自适应策略：根据内存使用动态调整
                if time.time() - self._manual_override_timestamp > max(self.monitoring_interval, 5.0):
                    self._adaptive_strategy_adjustment()
 
            self.logger.info(
                f"内存策略应用: {self.strategy.value}, interval={self.monitoring_interval}s, cache_max={self.cache_manager.max_size}"
            )

        except Exception as e:
            self.logger.error(f"应用内存策略失败: {e}")
    
    def _adaptive_strategy_adjustment(self):
        """自适应策略调整"""
        try:
            memory_info = self._get_memory_info()
            current_usage = memory_info.memory_percent
            
            if current_usage > 0.8:
                # 高内存使用：激进策略
                self.monitoring_interval = 2.0
                self.cache_manager.max_size = 200
                gc.set_threshold(100, 5, 5)
            elif current_usage > 0.6:
                # 中等内存使用：平衡策略
                self.monitoring_interval = 5.0
                self.cache_manager.max_size = 500
                gc.set_threshold(700, 10, 10)
            else:
                # 低内存使用：保守策略
                self.monitoring_interval = 10.0
                self.cache_manager.max_size = 1000
                gc.set_threshold(1000, 15, 15)
                
        except Exception as e:
            self.logger.error(f"自适应策略调整失败: {e}")
    
    def _update_memory_stats(self, memory_info: MemoryInfo):
        """更新内存统计信息"""
        try:
            current_memory = memory_info.used_memory_mb
            
            if current_memory > self.memory_stats['peak_memory_mb']:
                self.memory_stats['peak_memory_mb'] = current_memory
            
        except Exception as e:
            self.logger.error(f"更新内存统计失败: {e}")
    
    def optimize_memory(self):
        """手动优化内存"""
        try:
            self.logger.info("开始手动内存优化")
            
            # 执行垃圾回收
            self._garbage_collection()
            
            # 清理内存池
            self._cleanup_memory_pools()
            
            # 获取优化后的内存信息
            memory_info = self._get_memory_info()
            
            self.logger.info(f"内存优化完成，当前使用: {memory_info.used_memory_mb:.1f}MB")
            
            return memory_info
            
        except Exception as e:
            self.logger.error(f"手动内存优化失败: {e}")
            return None
    
    def get_memory_info(self) -> MemoryInfo:
        """获取内存信息"""
        return self._get_memory_info()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取内存统计信息"""
        # 获取缓存统计信息
        cache_stats = self.cache_manager.get_stats()
        
        # 获取内存池统计信息
        string_pool_stats = self.string_pool.get_stats()
        
        return {
            'strategy': self.strategy.value,
            'monitoring_interval': self.monitoring_interval,
            'total_allocations': self.memory_stats['total_allocations'],
            'total_deallocations': self.memory_stats['total_deallocations'],
            'peak_memory_mb': self.memory_stats['peak_memory_mb'],
            'gc_collections': self.memory_stats['gc_collections'],
            'gc_time_ms': self.memory_stats['gc_time_ms'],
            'memory_warnings': self.memory_stats['memory_warnings'],
            'strategy_changes': self.memory_stats['strategy_changes'],
            'cache_stats': cache_stats.to_dict(),
            'string_pool_stats': string_pool_stats,
            'memory_thresholds': {k.value: v for k, v in self.memory_thresholds.items()}
        }
    
    def set_memory_strategy(self, strategy: MemoryStrategy):
        """设置内存策略"""
        try:
            if strategy != self.strategy:
                old = self.strategy
                self.strategy = strategy
                self.memory_stats['strategy_changes'] += 1
                self.logger.info(f"内存策略已设置为: {strategy.value}")
                self.logger.info(f"内存策略已调整: {old.value} -> {strategy.value}")
            else:
                self.logger.info(f"内存策略保持: {strategy.value}")
            self._apply_memory_strategy()
            self._manual_override_timestamp = time.time()
        except Exception as e:
            self.logger.error(f"设置内存策略失败: {e}")
    
    def set_memory_threshold(self, threshold: MemoryThreshold, value: float):
        """设置内存阈值"""
        try:
            if 0.0 <= value <= 1.0:
                self.memory_thresholds[threshold] = value
                self.logger.info(f"内存阈值 {threshold.value} 已设置为: {value:.1%}")
            else:
                self.logger.error(f"内存阈值必须在0.0到1.0之间: {value}")
        except Exception as e:
            self.logger.error(f"设置内存阈值失败: {e}")
    
    def clear_cache(self):
        """清空缓存"""
        self._clear_caches()
    
    def shutdown(self):
        """关闭内存优化管理器"""
        try:
            # 停止内存监控
            self.monitoring_running = False
            if self.memory_monitor_thread and self.memory_monitor_thread.is_alive():
                _t = 0.2 if getattr(self, "_fast_mode", False) else 5
                self.memory_monitor_thread.join(timeout=_t)
            
            # 关闭缓存管理器
            self.cache_manager.shutdown()
            
            # 关闭错误处理器
            self.error_handler.shutdown()
            
            self.logger.info("内存优化管理器已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭内存优化管理器时出现错误: {e}")
    
    def __del__(self):
        """析构函数"""
        try:
            self.shutdown()
        except:
            pass 