#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统资源边界检查器 v1.0.0
检查系统资源边界、监控资源使用和设置资源限制

作者: LAD Team
创建时间: 2025-08-17
最后更新: 2025-08-17
"""

import os
import sys
import time
import json
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Callable, Type
from dataclasses import dataclass, asdict
from enum import Enum
import queue
import psutil
import builtins

# 导入现有组件
from .enhanced_error_handler import EnhancedErrorHandler, ErrorCategory, ErrorSeverity
from .unified_cache_manager import UnifiedCacheManager, CacheStrategy


class ResourceType(Enum):
    """资源类型枚举"""
    CPU = "cpu"                       # CPU资源
    MEMORY = "memory"                 # 内存资源
    DISK = "disk"                     # 磁盘资源
    NETWORK = "network"               # 网络资源
    PROCESS = "process"               # 进程资源
    THREAD = "thread"                 # 线程资源


class ResourceStatus(Enum):
    """资源状态枚举"""
    NORMAL = "normal"                 # 正常
    WARNING = "warning"               # 警告
    CRITICAL = "critical"             # 严重
    EXCEEDED = "exceeded"            # 超出限制


@dataclass
class ResourceLimit:
    """资源限制数据类"""
    resource_type: ResourceType
    parameter_name: str
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    warning_threshold: Optional[Union[int, float]] = None
    critical_threshold: Optional[Union[int, float]] = None
    enabled: bool = True
    description: str = ""


@dataclass
class ResourceUsage:
    """资源使用数据类"""
    resource_type: ResourceType
    parameter_name: str
    current_value: Union[int, float]
    unit: str
    limit: Optional[ResourceLimit] = None
    status: ResourceStatus = ResourceStatus.NORMAL
    timestamp: float = 0.0
    details: Dict[str, Any] = None


@dataclass
class ResourceAlert:
    """资源告警数据类"""
    resource_type: ResourceType
    parameter_name: str
    current_value: Union[int, float]
    threshold: Union[int, float]
    alert_type: ResourceStatus
    message: str
    timestamp: float
    acknowledged: bool = False


class SystemResourceBoundaryChecker:
    """系统资源边界检查器"""
    
    def __init__(self, 
                 config_dir: Optional[Path] = None,
                 enable_auto_checking: bool = True,
                 check_interval: float = 5.0,
                 max_alerts: int = 1000):
        """
        初始化系统资源边界检查器
        
        Args:
            config_dir: 配置目录
            enable_auto_checking: 是否启用自动检查
            check_interval: 检查间隔（秒）
            max_alerts: 最大告警数量
        """
        self.logger = None  # 将在setup_logging中设置
        self._is_shutdown = False
        
        # 配置参数
        self.enable_auto_checking = enable_auto_checking
        self.check_interval = check_interval
        self.max_alerts = max_alerts
        
        # 配置目录
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / "resource_config"
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 组件集成
        self.error_handler = EnhancedErrorHandler(
            error_log_dir=self.config_dir / "errors",
            max_error_history=100
        )
        
        self.cache_manager = UnifiedCacheManager(
            max_size=1000,
            strategy=CacheStrategy.LRU
        )
        
        # 资源限制和监控
        self.resource_limits: Dict[str, ResourceLimit] = {}
        self.resource_usage_history: List[ResourceUsage] = []
        self.active_alerts: List[ResourceAlert] = []
        
        # 线程安全
        self._lock = threading.Lock()
        self._limits_lock = threading.Lock()
        self._usage_lock = threading.Lock()
        self._alerts_lock = threading.Lock()
        
        # 控制标志
        self._stop_checking = False
        self._checking_thread = None
        
        # 初始化默认资源限制
        self._initialize_default_limits()
        
        # 加载配置
        self._load_configuration()
        
        # 启动自动检查
        if self.enable_auto_checking:
            self._start_resource_checking()
        
        print("系统资源边界检查器初始化完成")
    
    def _initialize_default_limits(self):
        """初始化默认资源限制"""
        try:
            # CPU使用率限制
            self.add_resource_limit(
                resource_type=ResourceType.CPU,
                parameter_name="cpu_usage_percent",
                min_value=0.0,
                max_value=100.0,
                warning_threshold=80.0,
                critical_threshold=95.0,
                description="CPU使用率限制"
            )
            
            # 内存使用率限制
            self.add_resource_limit(
                resource_type=ResourceType.MEMORY,
                parameter_name="memory_usage_percent",
                min_value=0.0,
                max_value=100.0,
                warning_threshold=80.0,
                critical_threshold=95.0,
                description="内存使用率限制"
            )
            
            # 磁盘使用率限制
            self.add_resource_limit(
                resource_type=ResourceType.DISK,
                parameter_name="disk_usage_percent",
                min_value=0.0,
                max_value=100.0,
                warning_threshold=85.0,
                critical_threshold=95.0,
                description="磁盘使用率限制"
            )
            
            # 进程数量限制
            self.add_resource_limit(
                resource_type=ResourceType.PROCESS,
                parameter_name="process_count",
                min_value=1,
                max_value=1000,
                warning_threshold=800,
                critical_threshold=950,
                description="进程数量限制"
            )
            
            # 线程数量限制
            self.add_resource_limit(
                resource_type=ResourceType.THREAD,
                parameter_name="thread_count",
                min_value=1,
                max_value=10000,
                warning_threshold=8000,
                critical_threshold=9500,
                description="线程数量限制"
            )
            
        except Exception as e:
            print(f"初始化默认资源限制失败: {e}")
    
    def add_resource_limit(self, 
                          resource_type: ResourceType,
                          parameter_name: str,
                          min_value: Optional[Union[int, float]] = None,
                          max_value: Optional[Union[int, float]] = None,
                          warning_threshold: Optional[Union[int, float]] = None,
                          critical_threshold: Optional[Union[int, float]] = None,
                          enabled: bool = True,
                          description: str = "") -> bool:
        """添加资源限制"""
        try:
            limit = ResourceLimit(
                resource_type=resource_type,
                parameter_name=parameter_name,
                min_value=min_value,
                max_value=max_value,
                warning_threshold=warning_threshold,
                critical_threshold=critical_threshold,
                enabled=enabled,
                description=description
            )
            
            with self._limits_lock:
                self.resource_limits[parameter_name] = limit
            
            # 缓存限制
            cache_key = f"resource_limit_{parameter_name}"
            self.cache_manager.set(cache_key, limit, ttl=3600)
            
            return True
            
        except Exception as e:
            print(f"添加资源限制失败: {e}")
            return False
    
    def remove_resource_limit(self, parameter_name: str) -> bool:
        """移除资源限制"""
        try:
            with self._limits_lock:
                if parameter_name in self.resource_limits:
                    del self.resource_limits[parameter_name]
                    
                    # 从缓存中移除
                    cache_key = f"resource_limit_{parameter_name}"
                    self.cache_manager.delete(cache_key)
                    
                    return True
            return False
            
        except Exception as e:
            print(f"移除资源限制失败: {e}")
            return False
    
    def _start_resource_checking(self):
        """启动资源检查"""
        def check_resources():
            while not self._stop_checking:
                try:
                    # 检查CPU使用率
                    self._check_cpu_usage()
                    
                    # 检查内存使用率
                    self._check_memory_usage()
                    
                    # 检查磁盘使用率
                    self._check_disk_usage()
                    
                    # 检查进程数量
                    self._check_process_count()
                    
                    # 检查线程数量
                    self._check_thread_count()
                    
                    # 检查网络使用情况
                    self._check_network_usage()
                    
                    # 清理旧数据
                    self._cleanup_old_data()
                    
                    time.sleep(self.check_interval)
                    
                except Exception as e:
                    print(f"资源检查失败: {e}")
                    time.sleep(1)
        
        self._checking_thread = threading.Thread(target=check_resources, daemon=True)
        self._checking_thread.start()
    
    def _check_cpu_usage(self):
        """检查CPU使用率"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            
            usage = ResourceUsage(
                resource_type=ResourceType.CPU,
                parameter_name="cpu_usage_percent",
                current_value=cpu_percent,
                unit="%",
                limit=self.resource_limits.get("cpu_usage_percent"),
                timestamp=time.time(),
                details={"cpu_count": psutil.cpu_count()}
            )
            
            # 检查状态
            usage.status = self._evaluate_resource_status(usage)
            
            # 保存使用情况
            self._save_resource_usage(usage)
            
            # 检查是否需要告警
            self._check_resource_alert(usage)
            
        except Exception as e:
            print(f"检查CPU使用率失败: {e}")
    
    def _check_memory_usage(self):
        """检查内存使用率"""
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            usage = ResourceUsage(
                resource_type=ResourceType.MEMORY,
                parameter_name="memory_usage_percent",
                current_value=memory_percent,
                unit="%",
                limit=self.resource_limits.get("memory_usage_percent"),
                timestamp=time.time(),
                details={
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "free": memory.free
                }
            )
            
            # 检查状态
            usage.status = self._evaluate_resource_status(usage)
            
            # 保存使用情况
            self._save_resource_usage(usage)
            
            # 检查是否需要告警
            self._check_resource_alert(usage)
            
        except Exception as e:
            print(f"检查内存使用率失败: {e}")
    
    def _check_disk_usage(self):
        """检查磁盘使用率"""
        try:
            # 检查当前目录所在磁盘
            try:
                disk = psutil.disk_usage('.')
                disk_percent = disk.percent
            except (FileNotFoundError, OSError):
                # Windows系统可能没有根目录，使用当前目录
                disk = psutil.disk_usage('.')
                disk_percent = disk.percent
            
            usage = ResourceUsage(
                resource_type=ResourceType.DISK,
                parameter_name="disk_usage_percent",
                current_value=disk_percent,
                unit="%",
                limit=self.resource_limits.get("disk_usage_percent"),
                timestamp=time.time(),
                details={
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free
                }
            )
            
            # 检查状态
            usage.status = self._evaluate_resource_status(usage)
            
            # 保存使用情况
            self._save_resource_usage(usage)
            
            # 检查是否需要告警
            self._check_resource_alert(usage)
            
        except Exception as e:
            print(f"检查磁盘使用率失败: {e}")
    
    def _check_process_count(self):
        """检查进程数量"""
        try:
            process_count = len(psutil.pids())
            
            usage = ResourceUsage(
                resource_type=ResourceType.PROCESS,
                parameter_name="process_count",
                current_value=process_count,
                unit="count",
                limit=self.resource_limits.get("process_count"),
                timestamp=time.time(),
                details={"current_process": psutil.Process().pid}
            )
            
            # 检查状态
            usage.status = self._evaluate_resource_status(usage)
            
            # 保存使用情况
            self._save_resource_usage(usage)
            
            # 检查是否需要告警
            self._check_resource_alert(usage)
            
        except Exception as e:
            print(f"检查进程数量失败: {e}")
    
    def _check_thread_count(self):
        """检查线程数量"""
        try:
            thread_count = threading.active_count()
            
            usage = ResourceUsage(
                resource_type=ResourceType.THREAD,
                parameter_name="thread_count",
                current_value=thread_count,
                unit="count",
                limit=self.resource_limits.get("thread_count"),
                timestamp=time.time(),
                details={"main_thread": threading.main_thread().name}
            )
            
            # 检查状态
            usage.status = self._evaluate_resource_status(usage)
            
            # 保存使用情况
            self._save_resource_usage(usage)
            
            # 检查是否需要告警
            self._check_resource_alert(usage)
            
        except Exception as e:
            print(f"检查线程数量失败: {e}")
    
    def _check_network_usage(self):
        """检查网络使用情况"""
        try:
            network = psutil.net_io_counters()
            total_bytes = network.bytes_sent + network.bytes_recv
            
            usage = ResourceUsage(
                resource_type=ResourceType.NETWORK,
                parameter_name="network_total_bytes",
                current_value=total_bytes,
                unit="bytes",
                limit=None,  # 网络使用暂时不设限制
                timestamp=time.time(),
                details={
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            )
            
            # 保存使用情况
            self._save_resource_usage(usage)
            
        except Exception as e:
            print(f"检查网络使用情况失败: {e}")
    
    def _evaluate_resource_status(self, usage: ResourceUsage) -> ResourceStatus:
        """评估资源状态"""
        try:
            if not usage.limit or not usage.limit.enabled:
                return ResourceStatus.NORMAL
            
            current_value = usage.current_value
            
            # 检查是否超出限制
            if usage.limit.max_value is not None and current_value > usage.limit.max_value:
                return ResourceStatus.EXCEEDED
            
            if usage.limit.min_value is not None and current_value < usage.limit.min_value:
                return ResourceStatus.EXCEEDED
            
            # 检查是否达到严重阈值
            if usage.limit.critical_threshold is not None and current_value >= usage.limit.critical_threshold:
                return ResourceStatus.CRITICAL
            
            # 检查是否达到警告阈值
            if usage.limit.warning_threshold is not None and current_value >= usage.limit.warning_threshold:
                return ResourceStatus.WARNING
            
            return ResourceStatus.NORMAL
            
        except Exception as e:
            print(f"评估资源状态失败: {e}")
            return ResourceStatus.NORMAL
    
    def _check_resource_alert(self, usage: ResourceUsage):
        """检查资源告警"""
        try:
            if not usage.limit or not usage.limit.enabled:
                return
            
            current_value = usage.current_value
            alert_type = None
            threshold = None
            message = ""
            
            # 确定告警类型
            if usage.status == ResourceStatus.EXCEEDED:
                if usage.limit.max_value is not None and current_value > usage.limit.max_value:
                    alert_type = ResourceStatus.EXCEEDED
                    threshold = usage.limit.max_value
                    message = f"{usage.resource_type.value}使用超出最大值限制: {current_value} > {threshold}"
                elif usage.limit.min_value is not None and current_value < usage.limit.min_value:
                    alert_type = ResourceStatus.EXCEEDED
                    threshold = usage.limit.min_value
                    message = f"{usage.resource_type.value}使用低于最小值限制: {current_value} < {threshold}"
            
            elif usage.status == ResourceStatus.CRITICAL:
                alert_type = ResourceStatus.CRITICAL
                threshold = usage.limit.critical_threshold
                message = f"{usage.resource_type.value}使用达到严重阈值: {current_value} >= {threshold}"
            
            elif usage.status == ResourceStatus.WARNING:
                alert_type = ResourceStatus.WARNING
                threshold = usage.limit.warning_threshold
                message = f"{usage.resource_type.value}使用达到警告阈值: {current_value} >= {threshold}"
            
            # 创建告警
            if alert_type:
                alert = ResourceAlert(
                    resource_type=usage.resource_type,
                    parameter_name=usage.parameter_name,
                    current_value=current_value,
                    threshold=threshold,
                    alert_type=alert_type,
                    message=message,
                    timestamp=time.time()
                )
                
                self._add_resource_alert(alert)
                
        except Exception as e:
            print(f"检查资源告警失败: {e}")
    
    def _add_resource_alert(self, alert: ResourceAlert):
        """添加资源告警"""
        try:
            with self._alerts_lock:
                # 检查是否已存在相同告警
                for existing_alert in self.active_alerts:
                    if (existing_alert.resource_type == alert.resource_type and
                        existing_alert.parameter_name == alert.parameter_name and
                        existing_alert.alert_type == alert.alert_type and
                        not existing_alert.acknowledged):
                        return  # 已存在相同告警
                
                # 添加新告警
                self.active_alerts.append(alert)
                
                # 限制告警数量
                if len(self.active_alerts) > self.max_alerts:
                    self.active_alerts = self.active_alerts[-self.max_alerts:]
                
                # 缓存告警
                cache_key = f"resource_alert_{alert.parameter_name}_{int(alert.timestamp)}"
                self.cache_manager.set(cache_key, alert, ttl=3600)
                
                print(f"资源告警: {alert.message}")
                
        except Exception as e:
            print(f"添加资源告警失败: {e}")
    
    def _save_resource_usage(self, usage: ResourceUsage):
        """保存资源使用情况"""
        try:
            with self._usage_lock:
                self.resource_usage_history.append(usage)
                
                # 限制历史记录大小
                if len(self.resource_usage_history) > 1000:
                    self.resource_usage_history = self.resource_usage_history[-1000:]
                
                # 缓存使用情况
                cache_key = f"resource_usage_{usage.parameter_name}_{int(usage.timestamp)}"
                self.cache_manager.set(cache_key, usage, ttl=3600)
                
        except Exception as e:
            print(f"保存资源使用情况失败: {e}")
    
    def _cleanup_old_data(self):
        """清理旧数据"""
        try:
            current_time = time.time()
            cutoff_time = current_time - (24 * 3600)  # 保留24小时
            
            with self._usage_lock:
                self.resource_usage_history = [
                    usage for usage in self.resource_usage_history
                    if usage.timestamp > cutoff_time
                ]
            
            with self._alerts_lock:
                self.active_alerts = [
                    alert for alert in self.active_alerts
                    if alert.timestamp > cutoff_time
                ]
                
        except Exception as e:
            print(f"清理旧数据失败: {e}")
    
    def get_resource_usage(self, 
                          resource_type: Optional[ResourceType] = None,
                          parameter_name: Optional[str] = None,
                          limit: Optional[int] = None) -> List[ResourceUsage]:
        """获取资源使用情况"""
        try:
            with self._usage_lock:
                usage_list = self.resource_usage_history.copy()
                
                if resource_type:
                    usage_list = [u for u in usage_list if u.resource_type == resource_type]
                
                if parameter_name:
                    usage_list = [u for u in usage_list if u.parameter_name == parameter_name]
                
                if limit:
                    usage_list = usage_list[-limit:]
                
                return usage_list
                
        except Exception as e:
            print(f"获取资源使用情况失败: {e}")
            return []
    
    def get_resource_limits(self, 
                           resource_type: Optional[ResourceType] = None) -> List[ResourceLimit]:
        """获取资源限制"""
        try:
            with self._limits_lock:
                limits = list(self.resource_limits.values())
                
                if resource_type:
                    limits = [l for l in limits if l.resource_type == resource_type]
                
                return limits
                
        except Exception as e:
            print(f"获取资源限制失败: {e}")
            return []
    
    def get_active_alerts(self, 
                         resource_type: Optional[ResourceType] = None,
                         alert_type: Optional[ResourceStatus] = None) -> List[ResourceAlert]:
        """获取活动告警"""
        try:
            with self._alerts_lock:
                alerts = [a for a in self.active_alerts if not a.acknowledged]
                
                if resource_type:
                    alerts = [a for a in alerts if a.resource_type == resource_type]
                
                if alert_type:
                    alerts = [a for a in alerts if a.alert_type == alert_type]
                
                return alerts
                
        except Exception as e:
            print(f"获取活动告警失败: {e}")
            return []
    
    def acknowledge_alert(self, 
                         resource_type: ResourceType,
                         parameter_name: str) -> bool:
        """确认告警"""
        try:
            with self._alerts_lock:
                for alert in self.active_alerts:
                    if (alert.resource_type == resource_type and
                        alert.parameter_name == parameter_name):
                        alert.acknowledged = True
                        return True
            return False
            
        except Exception as e:
            print(f"确认告警失败: {e}")
            return False
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """获取资源摘要"""
        try:
            summary = {
                'total_resources': len(self.resource_limits),
                'resources_by_type': {},
                'alerts_summary': {
                    'total_alerts': len(self.active_alerts),
                    'active_alerts': len(self.get_active_alerts()),
                    'acknowledged_alerts': len([a for a in self.active_alerts if a.acknowledged])
                },
                'checking_status': {
                    'enabled': self.enable_auto_checking,
                    'interval': self.check_interval,
                    'running': not self._stop_checking
                },
                'last_update': time.time()
            }
            
            # 按类型统计资源
            for limit in self.resource_limits.values():
                resource_type = limit.resource_type.value
                if resource_type not in summary['resources_by_type']:
                    summary['resources_by_type'][resource_type] = 0
                summary['resources_by_type'][resource_type] += 1
            
            return summary
            
        except Exception as e:
            print(f"获取资源摘要失败: {e}")
            return {}
    
    def _load_configuration(self):
        """加载配置"""
        try:
            config_file = self.config_dir / "resource_config.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 加载资源限制
                for limit_data in config_data.get('limits', []):
                    try:
                        limit = ResourceLimit(
                            resource_type=ResourceType(limit_data['resource_type']),
                            parameter_name=limit_data['parameter_name'],
                            min_value=limit_data.get('min_value'),
                            max_value=limit_data.get('max_value'),
                            warning_threshold=limit_data.get('warning_threshold'),
                            critical_threshold=limit_data.get('critical_threshold'),
                            enabled=limit_data.get('enabled', True),
                            description=limit_data.get('description', '')
                        )
                        self.resource_limits[limit.parameter_name] = limit
                    except Exception as e:
                        print(f"加载资源限制{limit_data.get('parameter_name', 'unknown')}失败: {e}")
                
        except Exception as e:
            print(f"加载配置失败: {e}")
    
    def save_configuration(self):
        """保存配置"""
        try:
            config_file = self.config_dir / "resource_config.json"
            
            config_data = {
                'limits': []
            }
            
            with self._limits_lock:
                for limit in self.resource_limits.values():
                    limit_dict = asdict(limit)
                    limit_dict['resource_type'] = limit.resource_type.value
                    config_data['limits'].append(limit_dict)
            
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with builtins.open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def setup_logging(self, logger):
        """设置日志记录器"""
        self.logger = logger
    
    def shutdown(self):
        """关闭资源边界检查器"""
        if getattr(self, '_is_shutdown', False):
            return
        try:
            # 停止资源检查
            self._stop_checking = True
            
            if self._checking_thread and self._checking_thread.is_alive():
                self._checking_thread.join(timeout=5)
            
            # 保存配置
            self.save_configuration()
            
            # 关闭组件
            if hasattr(self, 'error_handler'):
                self.error_handler.shutdown()
            
            if hasattr(self, 'cache_manager'):
                self.cache_manager.shutdown()
            
            print("系统资源边界检查器已关闭")
            
        except Exception as e:
            print(f"关闭资源边界检查器时出现错误: {e}")
        finally:
            self._is_shutdown = True
    
    def __del__(self):
        """析构函数"""
        try:
            self.shutdown()
        except:
            pass
            pass 