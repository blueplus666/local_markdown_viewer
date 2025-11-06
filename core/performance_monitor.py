#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控器 v1.0.0
实时监控系统性能，提供性能指标收集、分析和预警功能

作者: LAD Team
创建时间: 2025-08-16
最后更新: 2025-08-16
"""

import os
import time
import json
import threading
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import psutil
import gc
from collections import deque, defaultdict

# 导入性能优化组件
from .high_performance_file_reader import HighPerformanceFileReader, ReadStrategy
from .render_performance_optimizer import RenderPerformanceOptimizer, RenderStrategy, RenderMode
from .memory_optimization_manager import MemoryOptimizationManager, MemoryStrategy
from .enhanced_error_handler import EnhancedErrorHandler, ErrorRecoveryStrategy


class MetricType(Enum):
    """指标类型枚举"""
    CPU_USAGE = "cpu_usage"           # CPU使用率
    MEMORY_USAGE = "memory_usage"     # 内存使用
    DISK_IO = "disk_io"               # 磁盘I/O
    NETWORK_IO = "network_io"         # 网络I/O
    CACHE_PERFORMANCE = "cache"       # 缓存性能
    RENDER_PERFORMANCE = "render"     # 渲染性能
    FILE_READ_PERFORMANCE = "file_read"  # 文件读取性能


class AlertLevel(Enum):
    """告警级别枚举"""
    INFO = "info"           # 信息
    WARNING = "warning"     # 警告
    ERROR = "error"         # 错误
    CRITICAL = "critical"   # 严重


@dataclass
class PerformanceMetric:
    """性能指标数据类"""
    metric_type: MetricType
    value: float
    unit: str
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['metric_type'] = self.metric_type.value
        return data


@dataclass
class Alert:
    """告警数据类"""
    level: AlertLevel
    message: str
    metric_type: MetricType
    value: float
    threshold: float
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['level'] = self.level.value
        data['metric_type'] = self.metric_type.value
        return data


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, monitoring_interval: float = 1.0, alert_thresholds: Optional[Dict] = None):
        """
        初始化性能监控器
        
        Args:
            monitoring_interval: 监控间隔（秒）
            alert_thresholds: 告警阈值配置
        """
        self.logger = logging.getLogger(__name__)
        
        # 监控配置
        self.monitoring_interval = monitoring_interval
        self.monitoring_active = False
        self.monitor_thread = None
        
        # 性能优化组件
        self.file_reader = HighPerformanceFileReader()
        self.render_optimizer = RenderPerformanceOptimizer()
        self.memory_manager = MemoryOptimizationManager()
        self.error_handler = EnhancedErrorHandler()
        
        # 指标存储
        self.metrics_history: Dict[MetricType, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.current_metrics: Dict[MetricType, PerformanceMetric] = {}
        
        # 告警配置和存储
        self.alert_thresholds = alert_thresholds or {
            MetricType.CPU_USAGE: {'warning': 70.0, 'error': 85.0, 'critical': 95.0},
            MetricType.MEMORY_USAGE: {'warning': 80.0, 'error': 90.0, 'critical': 95.0},
            MetricType.CACHE_PERFORMANCE: {'warning': 0.8, 'error': 0.6, 'critical': 0.4},
            MetricType.RENDER_PERFORMANCE: {'warning': 100.0, 'error': 50.0, 'critical': 25.0}
        }
        
        self.alerts: List[Alert] = []
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        
        # 性能统计
        self.performance_stats = {
            'total_metrics_collected': 0,
            'total_alerts_generated': 0,
            'monitoring_start_time': time.time(),
            'last_cleanup_time': time.time()
        }
    
    def start_monitoring(self):
        """开始性能监控"""
        if self.monitoring_active:
            self.logger.warning("性能监控已在运行中")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("性能监控已启动")
    
    def stop_monitoring(self):
        """停止性能监控"""
        if not self.monitoring_active:
            self.logger.warning("性能监控未在运行")
            return
        
        self.monitoring_active = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        
        self.logger.info("性能监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.monitoring_active:
            try:
                # 收集系统性能指标
                self._collect_system_metrics()
                
                # 收集应用性能指标
                self._collect_application_metrics()
                
                # 检查告警条件
                self._check_alerts()
                
                # 清理旧数据
                self._cleanup_old_data()
                
                # 等待下次监控
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"监控循环异常: {e}")
                self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
                time.sleep(self.monitoring_interval)
    
    def _collect_system_metrics(self):
        """收集系统性能指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_metric = PerformanceMetric(
                metric_type=MetricType.CPU_USAGE,
                value=cpu_percent,
                unit="%",
                timestamp=time.time()
            )
            self._store_metric(cpu_metric)
            
            # 内存使用
            memory = psutil.virtual_memory()
            memory_metric = PerformanceMetric(
                metric_type=MetricType.MEMORY_USAGE,
                value=memory.percent,
                unit="%",
                timestamp=time.time(),
                metadata={
                    'total_mb': memory.total / 1024 / 1024,
                    'available_mb': memory.available / 1024 / 1024,
                    'used_mb': memory.used / 1024 / 1024
                }
            )
            self._store_metric(memory_metric)
            
            # 磁盘I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                disk_metric = PerformanceMetric(
                    metric_type=MetricType.DISK_IO,
                    value=disk_io.read_bytes + disk_io.write_bytes,
                    unit="bytes",
                    timestamp=time.time(),
                    metadata={
                        'read_bytes': disk_io.read_bytes,
                        'write_bytes': disk_io.write_bytes,
                        'read_count': disk_io.read_count,
                        'write_count': disk_io.write_count
                    }
                )
                self._store_metric(disk_metric)
            
        except Exception as e:
            self.logger.error(f"收集系统指标失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
    
    def _collect_application_metrics(self):
        """收集应用性能指标"""
        try:
            # 缓存性能指标
            if hasattr(self.file_reader, 'cache_manager'):
                cache_stats = self.file_reader.cache_manager.get_stats()
                cache_hit_rate = cache_stats.get('hit_rate', 0.0)
                
                cache_metric = PerformanceMetric(
                    metric_type=MetricType.CACHE_PERFORMANCE,
                    value=cache_hit_rate,
                    unit="ratio",
                    timestamp=time.time(),
                    metadata=cache_stats
                )
                self._store_metric(cache_metric)
            
            # 渲染性能指标
            if hasattr(self.render_optimizer, 'get_performance_stats'):
                render_stats = self.render_optimizer.get_performance_stats()
                render_speed = render_stats.get('avg_render_speed', 0.0)
                
                render_metric = PerformanceMetric(
                    metric_type=MetricType.RENDER_PERFORMANCE,
                    value=render_speed,
                    unit="chars/ms",
                    timestamp=time.time(),
                    metadata=render_stats
                )
                self._store_metric(render_metric)
            
            # 文件读取性能指标
            if hasattr(self.file_reader, 'get_performance_stats'):
                file_stats = self.file_reader.get_performance_stats()
                read_speed = file_stats.get('avg_read_speed', 0.0)
                
                file_metric = PerformanceMetric(
                    metric_type=MetricType.FILE_READ_PERFORMANCE,
                    value=read_speed,
                    unit="MB/s",
                    timestamp=time.time(),
                    metadata=file_stats
                )
                self._store_metric(file_metric)
            
        except Exception as e:
            self.logger.error(f"收集应用指标失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
    
    def _store_metric(self, metric: PerformanceMetric):
        """存储性能指标"""
        try:
            # 更新当前指标
            self.current_metrics[metric.metric_type] = metric
            
            # 添加到历史记录
            self.metrics_history[metric.metric_type].append(metric)
            
            # 更新统计
            self.performance_stats['total_metrics_collected'] += 1
            
        except Exception as e:
            self.logger.error(f"存储指标失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
    
    def _check_alerts(self):
        """检查告警条件"""
        try:
            for metric_type, thresholds in self.alert_thresholds.items():
                if metric_type in self.current_metrics:
                    metric = self.current_metrics[metric_type]
                    value = metric.value
                    
                    # 检查各个告警级别
                    for level_name, threshold in thresholds.items():
                        level = AlertLevel(level_name.upper())
                        
                        # 根据指标类型确定告警条件
                        if self._should_alert(metric_type, value, threshold, level):
                            alert = Alert(
                                level=level,
                                message=f"{metric_type.value} 指标 {value}{metric.unit} 超过阈值 {threshold}",
                                metric_type=metric_type,
                                value=value,
                                threshold=threshold,
                                timestamp=time.time()
                            )
                            
                            self._generate_alert(alert)
            
        except Exception as e:
            self.logger.error(f"检查告警失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
    
    def _should_alert(self, metric_type: MetricType, value: float, threshold: float, level: AlertLevel) -> bool:
        """判断是否应该生成告警"""
        try:
            if metric_type in [MetricType.CPU_USAGE, MetricType.MEMORY_USAGE]:
                # CPU和内存使用率超过阈值时告警
                return value > threshold
            elif metric_type in [MetricType.CACHE_PERFORMANCE]:
                # 缓存命中率低于阈值时告警
                return value < threshold
            elif metric_type in [MetricType.RENDER_PERFORMANCE, MetricType.FILE_READ_PERFORMANCE]:
                # 性能指标低于阈值时告警
                return value < threshold
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"判断告警条件失败: {e}")
            return False
    
    def _generate_alert(self, alert: Alert):
        """生成告警"""
        try:
            # 添加到告警列表
            self.alerts.append(alert)
            
            # 更新统计
            self.performance_stats['total_alerts_generated'] += 1
            
            # 记录告警日志
            self.logger.warning(f"性能告警: {alert.message}")
            
            # 调用告警回调函数
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    self.logger.error(f"告警回调函数执行失败: {e}")
            
        except Exception as e:
            self.logger.error(f"生成告警失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
    
    def _cleanup_old_data(self):
        """清理旧数据"""
        try:
            current_time = time.time()
            
            # 每小时清理一次
            if current_time - self.performance_stats['last_cleanup_time'] > 3600:
                # 清理超过24小时的指标数据
                cutoff_time = current_time - 86400
                
                for metric_type in list(self.metrics_history.keys()):
                    # 移除过期的指标
                    while (self.metrics_history[metric_type] and 
                           self.metrics_history[metric_type][0].timestamp < cutoff_time):
                        self.metrics_history[metric_type].popleft()
                
                # 清理超过1000条的告警
                if len(self.alerts) > 1000:
                    self.alerts = self.alerts[-1000:]
                
                self.performance_stats['last_cleanup_time'] = current_time
                
        except Exception as e:
            self.logger.error(f"清理旧数据失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """添加告警回调函数"""
        self.alert_callbacks.append(callback)
    
    def get_current_metrics(self) -> Dict[MetricType, PerformanceMetric]:
        """获取当前性能指标"""
        return self.current_metrics.copy()
    
    def get_metric_history(self, metric_type: MetricType, limit: int = 100) -> List[PerformanceMetric]:
        """获取指标历史数据"""
        if metric_type in self.metrics_history:
            return list(self.metrics_history[metric_type])[-limit:]
        return []
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        try:
            summary = {
                'monitoring_active': self.monitoring_active,
                'monitoring_interval': self.monitoring_interval,
                'total_metrics_collected': self.performance_stats['total_metrics_collected'],
                'total_alerts_generated': self.performance_stats['total_alerts_generated'],
                'monitoring_duration': time.time() - self.performance_stats['monitoring_start_time'],
                'current_metrics': {k.value: v.to_dict() for k, v in self.current_metrics.items()},
                'recent_alerts': [alert.to_dict() for alert in self.alerts[-10:]]  # 最近10条告警
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"获取性能摘要失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
            return {}
    
    def export_metrics(self, output_file: Path, format: str = 'json'):
        """导出性能指标"""
        try:
            if format.lower() == 'json':
                data = {
                    'export_time': time.time(),
                    'performance_stats': self.performance_stats,
                    'current_metrics': {k.value: v.to_dict() for k, v in self.current_metrics.items()},
                    'metrics_history': {k.value: [m.to_dict() for m in v] for k, v in self.metrics_history.items()},
                    'alerts': [alert.to_dict() for alert in self.alerts]
                }
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"性能指标已导出到: {output_file}")
                
            else:
                self.logger.warning(f"不支持的导出格式: {format}")
                
        except Exception as e:
            self.logger.error(f"导出性能指标失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
    
    def shutdown(self):
        """关闭性能监控器"""
        try:
            self.logger.info("关闭性能监控器...")
            
            # 停止监控
            self.stop_monitoring()
            
            # 关闭性能优化组件
            if hasattr(self.file_reader, 'shutdown'):
                self.file_reader.shutdown()
            if hasattr(self.render_optimizer, 'shutdown'):
                self.render_optimizer.shutdown()
            if hasattr(self.memory_manager, 'shutdown'):
                self.memory_manager.shutdown()
            
            self.logger.info("性能监控器已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭性能监控器失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)


# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建性能监控器
    monitor = PerformanceMonitor(monitoring_interval=2.0)
    
    try:
        # 启动监控
        monitor.start_monitoring()
        
        # 运行一段时间
        time.sleep(10)
        
        # 获取性能摘要
        summary = monitor.get_performance_summary()
        print("性能摘要:", json.dumps(summary, indent=2, ensure_ascii=False))
        
        # 停止监控
        monitor.stop_monitoring()
        
    finally:
        # 关闭监控器
        monitor.shutdown()
