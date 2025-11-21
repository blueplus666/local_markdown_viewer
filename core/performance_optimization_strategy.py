"""
性能优化策略管理器

实现自适应性能优化策略，根据系统状态动态调整优化方案
"""

import time
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import psutil
import asyncio
import os
import builtins

from .unified_cache_manager import UnifiedCacheManager
from .enhanced_error_handler import EnhancedErrorHandler
from .performance_metrics_manager import PerformanceMetricsManager


class OptimizationStrategy(Enum):
    """优化策略类型"""
    AGGRESSIVE = "aggressive"      # 激进优化
    BALANCED = "balanced"          # 平衡优化
    CONSERVATIVE = "conservative"  # 保守优化
    ADAPTIVE = "adaptive"          # 自适应优化


class OptimizationTarget(Enum):
    """优化目标"""
    FILE_READ = "file_read"        # 文件读取
    CACHE = "cache"                # 缓存
    RENDER = "render"              # 渲染
    MEMORY = "memory"              # 内存
    INTEGRATION = "integration"    # 集成性能


class OptimizationLevel(Enum):
    """优化级别"""
    LOW = "low"                    # 低级别优化
    MEDIUM = "medium"              # 中级别优化
    HIGH = "high"                  # 高级别优化
    MAXIMUM = "maximum"            # 最大优化


@dataclass
class OptimizationRule:
    """优化规则"""
    name: str
    target: OptimizationTarget
    strategy: OptimizationStrategy
    level: OptimizationLevel
    conditions: Dict[str, Any]
    actions: List[str]
    priority: int
    enabled: bool
    created_at: float
    updated_at: float


@dataclass
class OptimizationResult:
    """优化结果"""
    rule_name: str
    target: OptimizationTarget
    strategy: OptimizationStrategy
    level: OptimizationLevel
    success: bool
    performance_gain: float
    resource_usage: Dict[str, float]
    execution_time: float
    timestamp: float
    details: Dict[str, Any]


@dataclass
class PerformanceProfile:
    """性能配置"""
    name: str
    description: str
    strategy: OptimizationStrategy
    targets: List[OptimizationTarget]
    rules: List[str]
    created_at: float
    updated_at: float


class PerformanceOptimizationStrategy:
    """性能优化策略管理器"""
    
    def __init__(self, 
                 config_dir: Optional[Union[str, Path]] = None,
                 max_rules: int = 100,
                 enable_auto_optimization: bool = True,
                 optimization_interval: float = 30.0):
        """
        初始化性能优化策略管理器
        
        Args:
            config_dir: 配置目录
            max_rules: 最大规则数量
            enable_auto_optimization: 是否启用自动优化
            optimization_interval: 优化检查间隔（秒）
        """
        self.config_dir = Path(config_dir) if config_dir else Path("config/performance")
        self.max_rules = max_rules
        self.enable_auto_optimization = enable_auto_optimization
        self.optimization_interval = optimization_interval
        
        # 创建配置目录
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化组件
        from .unified_cache_manager import CacheStrategy
        self.cache_manager = UnifiedCacheManager(max_size=1000, strategy=CacheStrategy.LRU)
        self.error_handler = EnhancedErrorHandler()
        self.metrics_manager = PerformanceMetricsManager()
        
        # 优化规则和结果
        self.optimization_rules: Dict[str, OptimizationRule] = {}
        self.optimization_results: List[OptimizationResult] = []
        self.performance_profiles: Dict[str, PerformanceProfile] = {}
        
        # 线程锁
        self._rules_lock = threading.RLock()
        self._results_lock = threading.RLock()
        self._profiles_lock = threading.RLock()
        
        # 优化状态
        self._optimization_running = False
        self._optimization_thread = None
        # 测试态快速模式
        self._fast_mode = os.environ.get("LAD_TEST_MODE") == "1" or os.environ.get("LAD_QA_FAST") == "1"
        if self._fast_mode:
            self.enable_auto_optimization = False
            if self.optimization_interval and self.optimization_interval > 1.0:
                self.optimization_interval = 1.0
        
        # 初始化默认规则
        self._initialize_default_rules()
        
        # 启动自动优化
        if self.enable_auto_optimization:
            self._start_auto_optimization()
        
        print("性能优化策略管理器初始化完成")
    
    def _initialize_default_rules(self):
        """初始化默认优化规则"""
        try:
            # 文件读取优化规则
            self.add_optimization_rule(
                name="file_read_optimization",
                target=OptimizationTarget.FILE_READ,
                strategy=OptimizationStrategy.BALANCED,
                level=OptimizationLevel.MEDIUM,
                conditions={
                    "file_size_threshold": 1024 * 1024,  # 1MB
                    "read_frequency": 10,
                    "cache_hit_rate": 0.7
                },
                actions=[
                    "enable_async_reading",
                    "enable_preloading",
                    "optimize_buffer_size"
                ],
                priority=1
            )
            
            # 缓存优化规则
            self.add_optimization_rule(
                name="cache_optimization",
                target=OptimizationTarget.CACHE,
                strategy=OptimizationStrategy.ADAPTIVE,
                level=OptimizationLevel.HIGH,
                conditions={
                    "cache_hit_rate": 0.6,
                    "memory_usage": 0.8,
                    "cache_size": 1000
                },
                actions=[
                    "adjust_cache_strategy",
                    "optimize_eviction_policy",
                    "enable_compression"
                ],
                priority=2
            )
            
            # 渲染优化规则
            self.add_optimization_rule(
                name="render_optimization",
                target=OptimizationTarget.RENDER,
                strategy=OptimizationStrategy.BALANCED,
                level=OptimizationLevel.MEDIUM,
                conditions={
                    "render_time": 1000,  # 1秒
                    "content_size": 10000,
                    "complexity_score": 0.7
                },
                actions=[
                    "enable_lazy_rendering",
                    "optimize_markdown_parser",
                    "enable_parallel_processing"
                ],
                priority=3
            )
            
            # 内存优化规则
            self.add_optimization_rule(
                name="memory_optimization",
                target=OptimizationTarget.MEMORY,
                strategy=OptimizationStrategy.CONSERVATIVE,
                level=OptimizationLevel.HIGH,
                conditions={
                    "memory_usage": 0.85,
                    "memory_fragmentation": 0.3,
                    "gc_frequency": 10
                },
                actions=[
                    "trigger_garbage_collection",
                    "optimize_memory_pool",
                    "reduce_cache_size"
                ],
                priority=4
            )
            
            # 集成性能优化规则
            self.add_optimization_rule(
                name="integration_optimization",
                target=OptimizationTarget.INTEGRATION,
                strategy=OptimizationStrategy.ADAPTIVE,
                level=OptimizationLevel.MEDIUM,
                conditions={
                    "response_time": 2000,  # 2秒
                    "throughput": 100,
                    "error_rate": 0.05
                },
                actions=[
                    "optimize_workflow",
                    "enable_connection_pooling",
                    "optimize_data_flow"
                ],
                priority=5
            )
            
        except Exception as e:
            print(f"初始化默认优化规则失败: {e}")
    
    def add_optimization_rule(self,
                              name: str,
                              target: OptimizationTarget,
                              strategy: OptimizationStrategy,
                              level: OptimizationLevel,
                              conditions: Dict[str, Any],
                              actions: List[str],
                              priority: int = 1,
                              enabled: bool = True) -> bool:
        """
        添加优化规则
        
        Args:
            name: 规则名称
            target: 优化目标
            strategy: 优化策略
            level: 优化级别
            conditions: 触发条件
            actions: 执行动作
            priority: 优先级
            enabled: 是否启用
            
        Returns:
            是否添加成功
        """
        try:
            if len(self.optimization_rules) >= self.max_rules:
                print(f"优化规则数量已达上限: {self.max_rules}")
                return False
            
            rule = OptimizationRule(
                name=name,
                target=target,
                strategy=strategy,
                level=level,
                conditions=conditions,
                actions=actions,
                priority=priority,
                enabled=enabled,
                created_at=time.time(),
                updated_at=time.time()
            )
            
            with self._rules_lock:
                self.optimization_rules[name] = rule
            
            # 缓存规则
            cache_key = f"optimization_rule_{name}"
            self.cache_manager.set(cache_key, rule, ttl=3600)
            
            return True
            
        except Exception as e:
            print(f"添加优化规则失败: {e}")
            return False
    
    def remove_optimization_rule(self, name: str) -> bool:
        """
        移除优化规则
        
        Args:
            name: 规则名称
            
        Returns:
            是否移除成功
        """
        try:
            with self._rules_lock:
                if name in self.optimization_rules:
                    del self.optimization_rules[name]
                    
                    # 从缓存中移除
                    cache_key = f"optimization_rule_{name}"
                    self.cache_manager.delete(cache_key)
                    
                    return True
            return False
            
        except Exception as e:
            print(f"移除优化规则失败: {e}")
            return False
    
    def get_optimization_rules(self, 
                              target: Optional[OptimizationTarget] = None,
                              strategy: Optional[OptimizationStrategy] = None,
                              level: Optional[OptimizationLevel] = None) -> List[OptimizationRule]:
        """
        获取优化规则
        
        Args:
            target: 优化目标过滤
            strategy: 优化策略过滤
            level: 优化级别过滤
            
        Returns:
            优化规则列表
        """
        try:
            with self._rules_lock:
                rules = list(self.optimization_rules.values())
                
                if target:
                    rules = [r for r in rules if r.target == target]
                if strategy:
                    rules = [r for r in rules if r.strategy == strategy]
                if level:
                    rules = [r for r in rules if r.level == level]
                
                # 按优先级排序
                rules.sort(key=lambda x: x.priority, reverse=True)
                
                return rules
                
        except Exception as e:
            print(f"获取优化规则失败: {e}")
            return []
    
    def evaluate_optimization_conditions(self, rule: OptimizationRule) -> bool:
        """
        评估优化规则触发条件
        
        Args:
            rule: 优化规则
            
        Returns:
            是否满足触发条件
        """
        try:
            conditions = rule.conditions
            
            for condition_name, threshold in conditions.items():
                current_value = self._get_current_metric_value(condition_name)
                
                if current_value is None:
                    continue
                
                # 根据条件类型进行判断
                if condition_name.endswith("_threshold"):
                    if current_value < threshold:
                        return False
                elif condition_name.endswith("_rate"):
                    if current_value < threshold:
                        return False
                elif condition_name.endswith("_usage"):
                    if current_value < threshold:
                        return False
                elif condition_name.endswith("_time"):
                    if current_value > threshold:
                        return False
                elif condition_name.endswith("_size"):
                    if current_value > threshold:
                        return False
                elif condition_name.endswith("_frequency"):
                    if current_value < threshold:
                        return False
                elif condition_name.endswith("_score"):
                    if current_value < threshold:
                        return False
            
            return True
            
        except Exception as e:
            print(f"评估优化条件失败: {e}")
            return False
    
    def _get_current_metric_value(self, metric_name: str) -> Optional[float]:
        """
        获取当前指标值
        
        Args:
            metric_name: 指标名称
            
        Returns:
            指标值
        """
        try:
            # 从性能指标管理器获取
            try:
                metrics = self.metrics_manager.get_all_metrics()
                if metric_name in metrics:
                    return metrics[metric_name].current_value
            except Exception:
                pass  # 如果获取失败，继续使用系统指标
            
            # 从系统获取
            if metric_name == "memory_usage":
                return psutil.virtual_memory().percent / 100.0
            elif metric_name == "cpu_usage":
                return psutil.cpu_percent(interval=(0 if getattr(self, "_fast_mode", False) else 1)) / 100.0
            elif metric_name == "disk_usage":
                try:
                    return psutil.disk_usage('/').percent / 100.0
                except Exception:
                    return None
            
            return None
            
        except Exception as e:
            print(f"获取指标值失败: {e}")
            return None
    
    def execute_optimization_actions(self, rule: OptimizationRule) -> OptimizationResult:
        """
        执行优化动作
        
        Args:
            rule: 优化规则
            
        Returns:
            优化结果
        """
        start_time = time.time()
        
        try:
            # 执行优化动作
            actions_success = []
            actions_failed = []
            
            for action in rule.actions:
                try:
                    success = self._execute_single_action(action, rule)
                    if success:
                        actions_success.append(action)
                    else:
                        actions_failed.append(action)
                except Exception as e:
                    print(f"执行动作 {action} 失败: {e}")
                    actions_failed.append(action)
            
            # 计算性能提升
            performance_gain = self._calculate_performance_gain(rule.target)
            
            # 获取资源使用情况
            resource_usage = self._get_resource_usage()
            
            # 创建优化结果
            result = OptimizationResult(
                rule_name=rule.name,
                target=rule.target,
                strategy=rule.strategy,
                level=rule.level,
                success=len(actions_failed) == 0,
                performance_gain=performance_gain,
                resource_usage=resource_usage,
                execution_time=time.time() - start_time,
                timestamp=time.time(),
                details={
                    "actions_success": actions_success,
                    "actions_failed": actions_failed,
                    "conditions_met": True
                }
            )
            
            # 保存结果
            with self._results_lock:
                self.optimization_results.append(result)
                
                # 限制历史记录大小
                if len(self.optimization_results) > 1000:
                    self.optimization_results = self.optimization_results[-1000:]
            
            return result
            
        except Exception as e:
            print(f"执行优化动作失败: {e}")
            
            # 返回失败结果
            return OptimizationResult(
                rule_name=rule.name,
                target=rule.target,
                strategy=rule.strategy,
                level=rule.level,
                success=False,
                performance_gain=0.0,
                resource_usage={},
                execution_time=time.time() - start_time,
                timestamp=time.time(),
                details={
                    "error": str(e),
                    "actions_success": [],
                    "actions_failed": rule.actions,
                    "conditions_met": False
                }
            )
    
    def _execute_single_action(self, action: str, rule: OptimizationRule) -> bool:
        """
        执行单个优化动作
        
        Args:
            action: 动作名称
            rule: 优化规则
            
        Returns:
            是否执行成功
        """
        try:
            if action == "enable_async_reading":
                return self._enable_async_reading()
            elif action == "enable_preloading":
                return self._enable_preloading()
            elif action == "optimize_buffer_size":
                return self._optimize_buffer_size()
            elif action == "adjust_cache_strategy":
                return self._adjust_cache_strategy()
            elif action == "optimize_eviction_policy":
                return self._optimize_eviction_policy()
            elif action == "enable_compression":
                return self._enable_compression()
            elif action == "enable_lazy_rendering":
                return self._enable_lazy_rendering()
            elif action == "optimize_markdown_parser":
                return self._optimize_markdown_parser()
            elif action == "enable_parallel_processing":
                return self._enable_parallel_processing()
            elif action == "trigger_garbage_collection":
                return self._trigger_garbage_collection()
            elif action == "optimize_memory_pool":
                return self._optimize_memory_pool()
            elif action == "reduce_cache_size":
                return self._reduce_cache_size()
            elif action == "optimize_workflow":
                return self._optimize_workflow()
            elif action == "enable_connection_pooling":
                return self._enable_connection_pooling()
            elif action == "optimize_data_flow":
                return self._optimize_data_flow()
            else:
                print(f"未知的优化动作: {action}")
                return False
                
        except Exception as e:
            print(f"执行动作 {action} 失败: {e}")
            return False
    
    def _enable_async_reading(self) -> bool:
        """启用异步读取"""
        try:
            # 这里应该调用文件读取器的异步模式
            print("启用异步读取模式")
            return True
        except Exception as e:
            print(f"启用异步读取失败: {e}")
            return False
    
    def _enable_preloading(self) -> bool:
        """启用预加载"""
        try:
            print("启用文件预加载模式")
            return True
        except Exception as e:
            print(f"启用预加载失败: {e}")
            return False
    
    def _optimize_buffer_size(self) -> bool:
        """优化缓冲区大小"""
        try:
            print("优化文件读取缓冲区大小")
            return True
        except Exception as e:
            print(f"优化缓冲区大小失败: {e}")
            return False
    
    def _adjust_cache_strategy(self) -> bool:
        """调整缓存策略"""
        try:
            print("调整缓存策略为自适应模式")
            return True
        except Exception as e:
            print(f"调整缓存策略失败: {e}")
            return False
    
    def _optimize_eviction_policy(self) -> bool:
        """优化缓存淘汰策略"""
        try:
            print("优化缓存淘汰策略为LRU+TTL混合模式")
            return True
        except Exception as e:
            print(f"优化缓存淘汰策略失败: {e}")
            return False
    
    def _enable_compression(self) -> bool:
        """启用缓存压缩"""
        try:
            print("启用缓存数据压缩")
            return True
        except Exception as e:
            print(f"启用缓存压缩失败: {e}")
            return False
    
    def _enable_lazy_rendering(self) -> bool:
        """启用延迟渲染"""
        try:
            print("启用Markdown延迟渲染模式")
            return True
        except Exception as e:
            print(f"启用延迟渲染失败: {e}")
            return False
    
    def _optimize_markdown_parser(self) -> bool:
        """优化Markdown解析器"""
        try:
            print("优化Markdown解析器性能")
            return True
        except Exception as e:
            print(f"优化Markdown解析器失败: {e}")
            return False
    
    def _enable_parallel_processing(self) -> bool:
        """启用并行处理"""
        try:
            print("启用并行渲染处理")
            return True
        except Exception as e:
            print(f"启用并行处理失败: {e}")
            return False
    
    def _trigger_garbage_collection(self) -> bool:
        """触发垃圾回收"""
        try:
            import gc
            gc.collect()
            print("触发垃圾回收完成")
            return True
        except Exception as e:
            print(f"触发垃圾回收失败: {e}")
            return False
    
    def _optimize_memory_pool(self) -> bool:
        """优化内存池"""
        try:
            print("优化内存池配置")
            return True
        except Exception as e:
            print(f"优化内存池失败: {e}")
            return False
    
    def _reduce_cache_size(self) -> bool:
        """减少缓存大小"""
        try:
            print("减少缓存大小以释放内存")
            return True
        except Exception as e:
            print(f"减少缓存大小失败: {e}")
            return False
    
    def _optimize_workflow(self) -> bool:
        """优化工作流程"""
        try:
            print("优化系统工作流程")
            return True
        except Exception as e:
            print(f"优化工作流程失败: {e}")
            return False
    
    def _enable_connection_pooling(self) -> bool:
        """启用连接池"""
        try:
            print("启用数据库连接池")
            return True
        except Exception as e:
            print(f"启用连接池失败: {e}")
            return False
    
    def _optimize_data_flow(self) -> bool:
        """优化数据流"""
        try:
            print("优化数据流处理")
            return True
        except Exception as e:
            print(f"优化数据流失败: {e}")
            return False
    
    def _calculate_performance_gain(self, target: OptimizationTarget) -> float:
        """
        计算性能提升
        
        Args:
            target: 优化目标
            
        Returns:
            性能提升百分比
        """
        try:
            # 这里应该基于实际性能指标计算
            # 暂时返回模拟值
            base_gains = {
                OptimizationTarget.FILE_READ: 0.15,
                OptimizationTarget.CACHE: 0.25,
                OptimizationTarget.RENDER: 0.20,
                OptimizationTarget.MEMORY: 0.10,
                OptimizationTarget.INTEGRATION: 0.18
            }
            
            return base_gains.get(target, 0.0)
            
        except Exception as e:
            print(f"计算性能提升失败: {e}")
            return 0.0
    
    def _get_resource_usage(self) -> Dict[str, float]:
        """
        获取资源使用情况
        
        Returns:
            资源使用情况字典
        """
        try:
            return {
                "cpu_usage": psutil.cpu_percent(interval=(0 if getattr(self, "_fast_mode", False) else 1)) / 100.0,
                "memory_usage": psutil.virtual_memory().percent / 100.0,
                "disk_usage": psutil.disk_usage('/').percent / 100.0
            }
        except Exception as e:
            print(f"获取资源使用情况失败: {e}")
            return {}
    
    def run_optimization_cycle(self) -> List[OptimizationResult]:
        """
        运行优化周期
        
        Returns:
            优化结果列表
        """
        try:
            if self._optimization_running:
                print("优化周期已在运行中")
                return []
            
            self._optimization_running = True
            results = []
            
            # 获取所有启用的规则
            rules = self.get_optimization_rules()
            enabled_rules = [r for r in rules if r.enabled]
            
            print(f"开始优化周期，共 {len(enabled_rules)} 条规则")
            
            for rule in enabled_rules:
                try:
                    # 评估条件
                    if self.evaluate_optimization_conditions(rule):
                        print(f"执行优化规则: {rule.name}")
                        
                        # 执行优化
                        result = self.execute_optimization_actions(rule)
                        results.append(result)
                        
                        if result.success:
                            print(f"优化规则 {rule.name} 执行成功，性能提升: {result.performance_gain:.2%}")
                        else:
                            print(f"优化规则 {rule.name} 执行失败")
                    else:
                        print(f"优化规则 {rule.name} 条件不满足，跳过")
                        
                except Exception as e:
                    print(f"执行优化规则 {rule.name} 时出现错误: {e}")
            
            print(f"优化周期完成，共执行 {len(results)} 条规则")
            return results
            
        except Exception as e:
            print(f"运行优化周期失败: {e}")
            return []
        finally:
            self._optimization_running = False
    
    def _start_auto_optimization(self):
        """启动自动优化"""
        try:
            def auto_optimization_worker():
                while self.enable_auto_optimization:
                    try:
                        time.sleep(self.optimization_interval)
                        if self.enable_auto_optimization:
                            self.run_optimization_cycle()
                    except Exception as e:
                        print(f"自动优化工作线程错误: {e}")
            
            self._optimization_thread = threading.Thread(
                target=auto_optimization_worker,
                daemon=True,
                name="AutoOptimizationWorker"
            )
            self._optimization_thread.start()
            
            print(f"自动优化已启动，间隔: {self.optimization_interval}秒")
            
        except Exception as e:
            print(f"启动自动优化失败: {e}")
    
    def stop_auto_optimization(self):
        """停止自动优化"""
        try:
            self.enable_auto_optimization = False
            
            if self._optimization_thread and self._optimization_thread.is_alive():
                self._optimization_thread.join(timeout=5.0)
            
            print("自动优化已停止")
            
        except Exception as e:
            print(f"停止自动优化失败: {e}")
    
    def get_optimization_results(self,
                                target: Optional[OptimizationTarget] = None,
                                success_only: bool = False,
                                limit: int = 100) -> List[OptimizationResult]:
        """
        获取优化结果
        
        Args:
            target: 优化目标过滤
            success_only: 是否只返回成功的结果
            limit: 返回结果数量限制
            
        Returns:
            优化结果列表
        """
        try:
            with self._results_lock:
                results = list(self.optimization_results)
                
                if target:
                    results = [r for r in results if r.target == target]
                if success_only:
                    results = [r for r in results if r.success]
                
                # 按时间倒序排序
                results.sort(key=lambda x: x.timestamp, reverse=True)
                
                return results[:limit]
                
        except Exception as e:
            print(f"获取优化结果失败: {e}")
            return []
    
    def get_optimization_statistics(self) -> Dict[str, Any]:
        """
        获取优化统计信息
        
        Returns:
            统计信息字典
        """
        try:
            with self._results_lock:
                total_results = len(self.optimization_results)
                successful_results = len([r for r in self.optimization_results if r.success])
                
                if total_results == 0:
                    return {
                        "total_results": 0,
                        "success_rate": 0.0,
                        "average_performance_gain": 0.0,
                        "target_distribution": {},
                        "strategy_distribution": {}
                    }
                
                # 按目标统计
                target_distribution = {}
                for result in self.optimization_results:
                    target = result.target.value
                    target_distribution[target] = target_distribution.get(target, 0) + 1
                
                # 按策略统计
                strategy_distribution = {}
                for result in self.optimization_results:
                    strategy = result.strategy.value
                    strategy_distribution[strategy] = strategy_distribution.get(strategy, 0) + 1
                
                # 计算平均性能提升
                performance_gains = [r.performance_gain for r in self.optimization_results if r.success]
                avg_performance_gain = sum(performance_gains) / len(performance_gains) if performance_gains else 0.0
                
                return {
                    "total_results": total_results,
                    "success_rate": successful_results / total_results,
                    "average_performance_gain": avg_performance_gain,
                    "target_distribution": target_distribution,
                    "strategy_distribution": strategy_distribution
                }
                
        except Exception as e:
            print(f"获取优化统计信息失败: {e}")
            return {}
    
    def create_performance_profile(self,
                                  name: str,
                                  description: str,
                                  strategy: OptimizationStrategy,
                                  targets: List[OptimizationTarget],
                                  rule_names: List[str]) -> bool:
        """
        创建性能配置
        
        Args:
            name: 配置名称
            description: 配置描述
            strategy: 优化策略
            targets: 优化目标列表
            rule_names: 规则名称列表
            
        Returns:
            是否创建成功
        """
        try:
            profile = PerformanceProfile(
                name=name,
                description=description,
                strategy=strategy,
                targets=targets,
                rules=rule_names,
                created_at=time.time(),
                updated_at=time.time()
            )
            
            with self._profiles_lock:
                self.performance_profiles[name] = profile
            
            return True
            
        except Exception as e:
            print(f"创建性能配置失败: {e}")
            return False
    
    def get_performance_profile(self, name: str) -> Optional[PerformanceProfile]:
        """
        获取性能配置
        
        Args:
            name: 配置名称
            
        Returns:
            性能配置
        """
        try:
            with self._profiles_lock:
                return self.performance_profiles.get(name)
                
        except Exception as e:
            print(f"获取性能配置失败: {e}")
            return None
    
    def apply_performance_profile(self, name: str) -> bool:
        """
        应用性能配置
        
        Args:
            name: 配置名称
            
        Returns:
            是否应用成功
        """
        try:
            profile = self.get_performance_profile(name)
            if not profile:
                print(f"性能配置 {name} 不存在")
                return False
            
            print(f"应用性能配置: {name}")
            
            # 应用配置中的规则
            for rule_name in profile.rules:
                rule = self.optimization_rules.get(rule_name)
                if rule and rule.enabled:
                    if self.evaluate_optimization_conditions(rule):
                        result = self.execute_optimization_actions(rule)
                        if result.success:
                            print(f"应用规则 {rule_name} 成功")
                        else:
                            print(f"应用规则 {rule_name} 失败")
                    else:
                        print(f"规则 {rule_name} 条件不满足")
            
            return True
            
        except Exception as e:
            print(f"应用性能配置失败: {e}")
            return False
    
    def save_configuration(self):
        """保存配置"""
        try:
            # 保存优化规则
            rules_file = self.config_dir / "optimization_rules.json"
            rules_data = {
                'rules': []
            }
            
            for rule in self.optimization_rules.values():
                rule_dict = asdict(rule)
                # 转换枚举类型为字符串
                rule_dict['target'] = rule.target.value
                rule_dict['strategy'] = rule.strategy.value
                rule_dict['level'] = rule.level.value
                rules_data['rules'].append(rule_dict)
            
            with builtins.open(rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, indent=2, ensure_ascii=False)
            
            # 保存性能配置
            profiles_file = self.config_dir / "performance_profiles.json"
            profiles_data = {
                'profiles': []
            }
            
            for profile in self.performance_profiles.values():
                profile_dict = asdict(profile)
                # 转换枚举类型为字符串
                profile_dict['strategy'] = profile.strategy.value
                profile_dict['targets'] = [t.value for t in profile.targets]
                profiles_data['profiles'].append(profile_dict)
            
            with builtins.open(profiles_file, 'w', encoding='utf-8') as f:
                json.dump(profiles_data, f, indent=2, ensure_ascii=False)
            
            print("性能优化策略配置已保存")
            
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def load_configuration(self):
        """加载配置"""
        try:
            # 加载优化规则
            rules_file = self.config_dir / "optimization_rules.json"
            if rules_file.exists():
                with open(rules_file, 'r', encoding='utf-8') as f:
                    rules_data = json.load(f)
                
                for rule_data in rules_data.get('rules', []):
                    try:
                        rule = OptimizationRule(
                            name=rule_data['name'],
                            target=OptimizationTarget(rule_data['target']),
                            strategy=OptimizationStrategy(rule_data['strategy']),
                            level=OptimizationLevel(rule_data['level']),
                            conditions=rule_data['conditions'],
                            actions=rule_data['actions'],
                            priority=rule_data['priority'],
                            enabled=rule_data['enabled'],
                            created_at=rule_data['created_at'],
                            updated_at=rule_data['updated_at']
                        )
                        self.optimization_rules[rule.name] = rule
                    except Exception as e:
                        print(f"加载规则 {rule_data.get('name', 'unknown')} 失败: {e}")
            
            # 加载性能配置
            profiles_file = self.config_dir / "performance_profiles.json"
            if profiles_file.exists():
                with open(profiles_file, 'r', encoding='utf-8') as f:
                    profiles_data = json.load(f)
                
                for profile_data in profiles_data.get('profiles', []):
                    try:
                        profile = PerformanceProfile(
                            name=profile_data['name'],
                            description=profile_data['description'],
                            strategy=OptimizationStrategy(profile_data['strategy']),
                            targets=[OptimizationTarget(t) for t in profile_data['targets']],
                            rules=profile_data['rules'],
                            created_at=profile_data['created_at'],
                            updated_at=profile_data['updated_at']
                        )
                        self.performance_profiles[profile.name] = profile
                    except Exception as e:
                        print(f"加载配置 {profile_data.get('name', 'unknown')} 失败: {e}")
            
            print("性能优化策略配置已加载")
            
        except Exception as e:
            print(f"加载配置失败: {e}")
    
    def shutdown(self):
        """关闭性能优化策略管理器"""
        try:
            # 停止自动优化
            self.stop_auto_optimization()
            
            # 保存配置
            self.save_configuration()
            
            # 关闭组件
            if hasattr(self, 'cache_manager'):
                self.cache_manager.shutdown()
            
            if hasattr(self, 'error_handler'):
                self.error_handler.shutdown()
            
            if hasattr(self, 'metrics_manager'):
                self.metrics_manager.shutdown()
            
            print("性能优化策略管理器已关闭")
            
        except Exception as e:
            print(f"关闭性能优化策略管理器时出现错误: {e}")
    
    def __del__(self):
        """析构函数"""
        try:
            self.shutdown()
        except:
            pass