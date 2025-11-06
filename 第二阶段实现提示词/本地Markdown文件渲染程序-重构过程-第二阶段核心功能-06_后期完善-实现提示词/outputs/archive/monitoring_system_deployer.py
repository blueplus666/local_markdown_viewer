"""
监控系统部署器 - 方案4.3.3系统集成与监控实施
部署性能监控、错误监控、日志监控系统
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import psutil
import json

# 导入前序模块的成果（使用模拟实现）
from mock_dependencies import (
    PerformanceMonitor, UnifiedErrorHandler, EnhancedLogger, UnifiedCacheManager
)


class MonitoringType(Enum):
    """监控类型枚举"""
    PERFORMANCE = "performance"
    ERROR = "error"
    LOG = "log"
    SYSTEM = "system"
    CACHE = "cache"


class AlertLevel(Enum):
    """告警级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MonitoringMetric:
    """监控指标"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str]
    alert_level: AlertLevel = AlertLevel.INFO


@dataclass
class AlertRule:
    """告警规则"""
    metric_name: str
    condition: str  # ">", "<", "==", ">=", "<="
    threshold: float
    alert_level: AlertLevel
    message: str
    enabled: bool = True


class MonitoringSystemDeployer:
    """监控系统部署器"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.logger = EnhancedLogger("MonitoringSystemDeployer")
        self.performance_monitor = PerformanceMonitor()
        self.error_handler = UnifiedErrorHandler()
        self.cache_manager = UnifiedCacheManager()
        
        # 监控配置
        self.monitoring_config = {
            "performance": {
                "enabled": True,
                "interval": 5.0,  # 秒
                "metrics": ["response_time", "memory_usage", "cpu_usage", "cache_hit_rate"]
            },
            "error": {
                "enabled": True,
                "interval": 1.0,  # 秒
                "metrics": ["error_rate", "error_count", "error_types"]
            },
            "log": {
                "enabled": True,
                "interval": 10.0,  # 秒
                "metrics": ["log_volume", "log_levels", "log_sources"]
            },
            "system": {
                "enabled": True,
                "interval": 30.0,  # 秒
                "metrics": ["disk_usage", "network_io", "process_count"]
            }
        }
        
        # 告警规则
        self.alert_rules: List[AlertRule] = []
        self._setup_default_alert_rules()
        
        # 监控数据存储
        self.metrics_storage: Dict[str, List[MonitoringMetric]] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self.data_storage: Dict[str, Path] = {}  # 初始化数据存储路径
        
        # 监控状态
        self.monitoring_active = False
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        
        # 通知渠道
        self.notification_channels: Dict[str, Callable] = {}
        self._setup_notification_channels()
    
    async def deploy_monitoring_system(self) -> Dict[str, Any]:
        """部署监控系统"""
        self.logger.info("开始部署监控系统")
        
        try:
            # 1. 部署性能监控系统
            await self._deploy_performance_monitoring()
            
            # 2. 部署错误监控系统
            await self._deploy_error_monitoring()
            
            # 3. 部署日志监控系统
            await self._deploy_log_monitoring()
            
            # 4. 部署系统监控
            await self._deploy_system_monitoring()
            
            # 5. 配置告警规则和通知渠道
            await self._configure_alerts_and_notifications()
            
            # 6. 建立监控数据存储和分析机制
            await self._setup_data_storage_and_analysis()
            
            # 7. 启动监控系统
            await self._start_monitoring_system()
            
            deployment_result = {
                "status": "success",
                "deployment_time": time.time(),
                "monitoring_types": list(self.monitoring_config.keys()),
                "alert_rules_count": len(self.alert_rules),
                "notification_channels": list(self.notification_channels.keys())
            }
            
            self.logger.info("监控系统部署完成")
            return deployment_result
            
        except Exception as e:
            self.logger.error(f"监控系统部署失败: {e}")
            await self.error_handler.handle_error(e, "MonitoringDeployment")
            raise
    
    def _setup_default_alert_rules(self):
        """设置默认告警规则"""
        self.alert_rules = [
            AlertRule("memory_usage", ">", 80, AlertLevel.WARNING, "内存使用率过高"),
            AlertRule("cpu_usage", ">", 80, AlertLevel.WARNING, "CPU使用率过高"),
            AlertRule("error_rate", ">", 5, AlertLevel.ERROR, "错误率过高"),
            AlertRule("disk_usage", ">", 90, AlertLevel.CRITICAL, "磁盘使用率过高"),
            AlertRule("cache_hit_rate", "<", 50, AlertLevel.WARNING, "缓存命中率过低")
        ]
    
    def _setup_notification_channels(self):
        """设置通知渠道"""
        self.notification_channels = {
            "logger": self._log_notification,
            "console": self._console_notification
        }
    
    async def _log_notification(self, message: str, level: AlertLevel):
        """日志通知"""
        if level == AlertLevel.CRITICAL:
            self.logger.critical(f"告警: {message}")
        elif level == AlertLevel.ERROR:
            self.logger.error(f"告警: {message}")
        elif level == AlertLevel.WARNING:
            self.logger.warning(f"告警: {message}")
        else:
            self.logger.info(f"告警: {message}")
    
    async def _console_notification(self, message: str, level: AlertLevel):
        """控制台通知"""
        print(f"[{level.value.upper()}] {message}")
    
    async def _deploy_performance_monitoring(self):
        """部署性能监控系统"""
        self.logger.info("部署性能监控系统")
        
        if not self.monitoring_config["performance"]["enabled"]:
            self.logger.info("性能监控已禁用")
            return
        
        # 创建性能监控任务
        self.monitoring_tasks["performance"] = asyncio.create_task(
            self._performance_monitoring_loop()
        )
        
        # 初始化性能指标存储
        self.metrics_storage["performance"] = []
        
        self.logger.info("性能监控系统部署完成")
    
    async def _deploy_error_monitoring(self):
        """部署错误监控系统"""
        self.logger.info("部署错误监控系统")
        
        if not self.monitoring_config["error"]["enabled"]:
            self.logger.info("错误监控已禁用")
            return
        
        # 创建错误监控任务
        self.monitoring_tasks["error"] = asyncio.create_task(
            self._error_monitoring_loop()
        )
        
        # 初始化错误指标存储
        self.metrics_storage["error"] = []
        
        self.logger.info("错误监控系统部署完成")
    
    async def _deploy_log_monitoring(self):
        """部署日志监控系统"""
        self.logger.info("部署日志监控系统")
        
        if not self.monitoring_config["log"]["enabled"]:
            self.logger.info("日志监控已禁用")
            return
        
        # 创建日志监控任务
        self.monitoring_tasks["log"] = asyncio.create_task(
            self._log_monitoring_loop()
        )
        
        # 初始化日志指标存储
        self.metrics_storage["log"] = []
        
        self.logger.info("日志监控系统部署完成")
    
    async def _deploy_system_monitoring(self):
        """部署系统监控"""
        self.logger.info("部署系统监控")
        
        if not self.monitoring_config["system"]["enabled"]:
            self.logger.info("系统监控已禁用")
            return
        
        # 创建系统监控任务
        self.monitoring_tasks["system"] = asyncio.create_task(
            self._system_monitoring_loop()
        )
        
        # 初始化系统指标存储
        self.metrics_storage["system"] = []
        
        self.logger.info("系统监控部署完成")
    
    async def _configure_alerts_and_notifications(self):
        """配置告警规则和通知渠道"""
        self.logger.info("配置告警规则和通知渠道")
        
        # 应用告警规则
        for rule in self.alert_rules:
            if rule.enabled:
                self.logger.info(f"启用告警规则: {rule.metric_name} {rule.condition} {rule.threshold}")
        
        # 测试通知渠道
        for channel_name, channel_func in self.notification_channels.items():
            try:
                await channel_func("监控系统部署完成", AlertLevel.INFO)
                self.logger.info(f"通知渠道 {channel_name} 测试成功")
            except Exception as e:
                self.logger.warning(f"通知渠道 {channel_name} 测试失败: {e}")
        
        self.logger.info("告警规则和通知渠道配置完成")
    
    async def _setup_data_storage_and_analysis(self):
        """建立监控数据存储和分析机制"""
        self.logger.info("建立监控数据存储和分析机制")
        
        # 创建数据存储目录
        storage_dir = Path("monitoring_data")
        storage_dir.mkdir(exist_ok=True)
        
        # 初始化数据存储
        self.data_storage = {
            "metrics_file": storage_dir / "metrics.json",
            "alerts_file": storage_dir / "alerts.json",
            "analysis_file": storage_dir / "analysis.json"
        }
        
        # 启动数据清理任务
        self.monitoring_tasks["data_cleanup"] = asyncio.create_task(
            self._data_cleanup_loop()
        )
        
        # 启动数据分析任务
        self.monitoring_tasks["data_analysis"] = asyncio.create_task(
            self._data_analysis_loop()
        )
        
        self.logger.info("监控数据存储和分析机制建立完成")
    
    async def _start_monitoring_system(self):
        """启动监控系统"""
        self.logger.info("启动监控系统")
        
        self.monitoring_active = True
        
        # 启动所有监控任务
        for task_name, task in self.monitoring_tasks.items():
            if not task.done():
                self.logger.info(f"监控任务 {task_name} 已启动")
        
        self.logger.info("监控系统启动完成")
    
    # 监控循环方法
    async def _performance_monitoring_loop(self):
        """性能监控循环"""
        interval = self.monitoring_config["performance"]["interval"]
        
        while self.monitoring_active:
            try:
                # 收集性能指标
                metrics = await self._collect_performance_metrics()
                
                # 存储指标
                self.metrics_storage["performance"].extend(metrics)
                
                # 检查告警
                await self._check_alerts(metrics)
                
                # 限制存储大小
                if len(self.metrics_storage["performance"]) > 1000:
                    self.metrics_storage["performance"] = self.metrics_storage["performance"][-500:]
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"性能监控循环错误: {e}")
                await asyncio.sleep(interval)
    
    async def _error_monitoring_loop(self):
        """错误监控循环"""
        interval = self.monitoring_config["error"]["interval"]
        
        while self.monitoring_active:
            try:
                # 收集错误指标
                metrics = await self._collect_error_metrics()
                
                # 存储指标
                self.metrics_storage["error"].extend(metrics)
                
                # 检查告警
                await self._check_alerts(metrics)
                
                # 限制存储大小
                if len(self.metrics_storage["error"]) > 1000:
                    self.metrics_storage["error"] = self.metrics_storage["error"][-500:]
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"错误监控循环错误: {e}")
                await asyncio.sleep(interval)
    
    async def _log_monitoring_loop(self):
        """日志监控循环"""
        interval = self.monitoring_config["log"]["interval"]
        
        while self.monitoring_active:
            try:
                # 收集日志指标
                metrics = await self._collect_log_metrics()
                
                # 存储指标
                self.metrics_storage["log"].extend(metrics)
                
                # 检查告警
                await self._check_alerts(metrics)
                
                # 限制存储大小
                if len(self.metrics_storage["log"]) > 1000:
                    self.metrics_storage["log"] = self.metrics_storage["log"][-500:]
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"日志监控循环错误: {e}")
                await asyncio.sleep(interval)
    
    async def _system_monitoring_loop(self):
        """系统监控循环"""
        interval = self.monitoring_config["system"]["interval"]
        
        while self.monitoring_active:
            try:
                # 收集系统指标
                metrics = await self._collect_system_metrics()
                
                # 存储指标
                self.metrics_storage["system"].extend(metrics)
                
                # 检查告警
                await self._check_alerts(metrics)
                
                # 限制存储大小
                if len(self.metrics_storage["system"]) > 1000:
                    self.metrics_storage["system"] = self.metrics_storage["system"][-500:]
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"系统监控循环错误: {e}")
                await asyncio.sleep(interval)
    
    async def _data_cleanup_loop(self):
        """数据清理循环"""
        while self.monitoring_active:
            try:
                # 清理旧数据（保留最近24小时）
                cutoff_time = datetime.now() - timedelta(hours=24)
                
                for storage_key, metrics_list in self.metrics_storage.items():
                    self.metrics_storage[storage_key] = [
                        metric for metric in metrics_list
                        if metric.timestamp > cutoff_time
                    ]
                
                # 保存数据到文件
                await self._save_metrics_to_file()
                
                await asyncio.sleep(3600)  # 每小时清理一次
                
            except Exception as e:
                self.logger.error(f"数据清理循环错误: {e}")
                await asyncio.sleep(3600)
    
    async def _data_analysis_loop(self):
        """数据分析循环"""
        while self.monitoring_active:
            try:
                # 分析监控数据
                analysis_result = await self._analyze_monitoring_data()
                
                # 保存分析结果
                await self._save_analysis_result(analysis_result)
                
                await asyncio.sleep(300)  # 每5分钟分析一次
                
            except Exception as e:
                self.logger.error(f"数据分析循环错误: {e}")
                await asyncio.sleep(300)
    
    # 指标收集方法
    async def _collect_performance_metrics(self) -> List[MonitoringMetric]:
        """收集性能指标"""
        metrics = []
        timestamp = datetime.now()
        
        # 响应时间
        response_time = await self.performance_monitor.get_average_response_time()
        metrics.append(MonitoringMetric(
            name="response_time",
            value=response_time,
            unit="ms",
            timestamp=timestamp,
            tags={"type": "performance"},
            alert_level=AlertLevel.INFO
        ))
        
        # 内存使用
        memory_usage = psutil.virtual_memory().percent
        metrics.append(MonitoringMetric(
            name="memory_usage",
            value=memory_usage,
            unit="%",
            timestamp=timestamp,
            tags={"type": "performance"},
            alert_level=AlertLevel.WARNING if memory_usage > 80 else AlertLevel.INFO
        ))
        
        # CPU使用
        cpu_usage = psutil.cpu_percent()
        metrics.append(MonitoringMetric(
            name="cpu_usage",
            value=cpu_usage,
            unit="%",
            timestamp=timestamp,
            tags={"type": "performance"},
            alert_level=AlertLevel.WARNING if cpu_usage > 80 else AlertLevel.INFO
        ))
        
        # 缓存命中率
        cache_hit_rate = await self.cache_manager.get_hit_rate()
        metrics.append(MonitoringMetric(
            name="cache_hit_rate",
            value=cache_hit_rate,
            unit="%",
            timestamp=timestamp,
            tags={"type": "performance"},
            alert_level=AlertLevel.WARNING if cache_hit_rate < 50 else AlertLevel.INFO
        ))
        
        return metrics
    
    async def _collect_error_metrics(self) -> List[MonitoringMetric]:
        """收集错误指标"""
        metrics = []
        timestamp = datetime.now()
        
        # 错误率
        error_rate = await self.error_handler.get_error_rate()
        metrics.append(MonitoringMetric(
            name="error_rate",
            value=error_rate,
            unit="%",
            timestamp=timestamp,
            tags={"type": "error"},
            alert_level=AlertLevel.ERROR if error_rate > 5 else AlertLevel.INFO
        ))
        
        # 错误计数
        error_count = await self.error_handler.get_error_count()
        metrics.append(MonitoringMetric(
            name="error_count",
            value=error_count,
            unit="count",
            timestamp=timestamp,
            tags={"type": "error"},
            alert_level=AlertLevel.WARNING if error_count > 100 else AlertLevel.INFO
        ))
        
        return metrics
    
    async def _collect_log_metrics(self) -> List[MonitoringMetric]:
        """收集日志指标"""
        metrics = []
        timestamp = datetime.now()
        
        # 日志量
        log_volume = await self._get_log_volume()
        metrics.append(MonitoringMetric(
            name="log_volume",
            value=log_volume,
            unit="lines/min",
            timestamp=timestamp,
            tags={"type": "log"},
            alert_level=AlertLevel.WARNING if log_volume > 1000 else AlertLevel.INFO
        ))
        
        return metrics
    
    async def _collect_system_metrics(self) -> List[MonitoringMetric]:
        """收集系统指标"""
        metrics = []
        timestamp = datetime.now()
        
        # 磁盘使用
        disk_usage = psutil.disk_usage('/').percent
        metrics.append(MonitoringMetric(
            name="disk_usage",
            value=disk_usage,
            unit="%",
            timestamp=timestamp,
            tags={"type": "system"},
            alert_level=AlertLevel.WARNING if disk_usage > 90 else AlertLevel.INFO
        ))
        
        # 网络IO
        net_io = psutil.net_io_counters()
        metrics.append(MonitoringMetric(
            name="network_io",
            value=net_io.bytes_sent + net_io.bytes_recv,
            unit="bytes",
            timestamp=timestamp,
            tags={"type": "system"},
            alert_level=AlertLevel.INFO
        ))
        
        return metrics
    
    # 告警检查方法
    async def _check_alerts(self, metrics: List[MonitoringMetric]):
        """检查告警"""
        for metric in metrics:
            for rule in self.alert_rules:
                if rule.metric_name == metric.name and rule.enabled:
                    if self._evaluate_alert_condition(metric.value, rule.condition, rule.threshold):
                        await self._trigger_alert(rule, metric)
    
    def _evaluate_alert_condition(self, value: float, condition: str, threshold: float) -> bool:
        """评估告警条件"""
        if condition == ">":
            return value > threshold
        elif condition == "<":
            return value < threshold
        elif condition == "==":
            return value == threshold
        elif condition == ">=":
            return value >= threshold
        elif condition == "<=":
            return value <= threshold
        return False
    
    async def _trigger_alert(self, rule: AlertRule, metric: MonitoringMetric):
        """触发告警"""
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "rule": asdict(rule),
            "metric": asdict(metric),
            "message": rule.message
        }
        
        self.alert_history.append(alert_data)
        
        # 发送通知
        for channel_name, channel_func in self.notification_channels.items():
            try:
                await channel_func(rule.message, rule.alert_level)
            except Exception as e:
                self.logger.error(f"发送告警通知失败 {channel_name}: {e}")
    
    # 辅助方法
    async def _get_log_volume(self) -> float:
        """获取日志量"""
        # 这里应该实现实际的日志量统计
        return 100.0  # 占位符
    
    async def _save_metrics_to_file(self):
        """保存指标到文件"""
        try:
            with open(self.data_storage["metrics_file"], 'w', encoding='utf-8') as f:
                json.dump(self.metrics_storage, f, default=str, indent=2)
        except Exception as e:
            self.logger.error(f"保存指标文件失败: {e}")
    
    async def _save_analysis_result(self, analysis_result: Dict[str, Any]):
        """保存分析结果"""
        try:
            with open(self.data_storage["analysis_file"], 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, default=str, indent=2)
        except Exception as e:
            self.logger.error(f"保存分析结果失败: {e}")
    
    async def _analyze_monitoring_data(self) -> Dict[str, Any]:
        """分析监控数据"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "trends": {},
            "recommendations": []
        }
        
        # 分析各类型指标
        for storage_key, metrics_list in self.metrics_storage.items():
            if metrics_list:
                recent_metrics = metrics_list[-100:]  # 最近100个指标
                
                # 计算平均值
                avg_values = {}
                for metric in recent_metrics:
                    if metric.name not in avg_values:
                        avg_values[metric.name] = []
                    avg_values[metric.name].append(metric.value)
                
                for name, values in avg_values.items():
                    avg_values[name] = sum(values) / len(values)
                
                analysis["summary"][storage_key] = avg_values
        
        return analysis 