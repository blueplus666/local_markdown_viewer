#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能基准测试器 v1.0.0
建立性能基准，提供性能测试、基准比较、性能报告等功能

作者: LAD Team
创建时间: 2025-08-16
最后更新: 2025-08-16
"""

import os
import time
import json
import statistics
import logging
import builtins
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue

# 导入性能优化组件
from .high_performance_file_reader import HighPerformanceFileReader, ReadStrategy
from .render_performance_optimizer import RenderPerformanceOptimizer, RenderStrategy, RenderMode
from .memory_optimization_manager import MemoryOptimizationManager, MemoryStrategy
from .enhanced_error_handler import EnhancedErrorHandler, ErrorRecoveryStrategy


class BenchmarkType(Enum):
    """基准测试类型枚举"""
    FILE_READ = "file_read"           # 文件读取性能
    RENDER = "render"                  # 渲染性能
    MEMORY = "memory"                  # 内存使用性能
    INTEGRATION = "integration"        # 集成性能
    STRESS = "stress"                  # 压力测试


class BenchmarkResultEnum(Enum):
    """基准测试结果枚举"""
    PASS = "pass"                      # 通过
    FAIL = "fail"                      # 失败
    WARNING = "warning"                # 警告
    UNKNOWN = "unknown"                # 未知


@dataclass
class BenchmarkMetrics:
    """基准测试指标数据类"""
    test_name: str
    test_type: str
    execution_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    throughput: float
    latency_ms: float
    success_rate: float
    error_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


@dataclass
class BenchmarkResult:
    """基准测试结果数据类"""
    test_name: str
    test_type: str
    result: BenchmarkResultEnum
    metrics: BenchmarkMetrics
    baseline_comparison: Dict[str, Any]
    recommendations: List[str]
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['result'] = self.result.value
        return data


class PerformanceBenchmark:
    """性能基准测试器"""
    
    def __init__(self, baseline_dir: Optional[Path] = None):
        """
        初始化性能基准测试器
        
        Args:
            baseline_dir: 基准数据目录
        """
        self.logger = logging.getLogger(__name__)
        
        # 基准数据目录
        if baseline_dir is None:
            baseline_dir = Path(__file__).parent.parent / "benchmarks"
        self.baseline_dir = baseline_dir
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        
        # 增强错误处理器
        self.error_handler = EnhancedErrorHandler(
            error_log_dir=Path(__file__).parent.parent / "logs" / "errors",
            max_error_history=100
        )
        
        # 性能组件
        self.file_reader = HighPerformanceFileReader()
        self.render_optimizer = RenderPerformanceOptimizer()
        self.memory_manager = MemoryOptimizationManager()
        
        # 测试结果队列
        self.test_results: queue.Queue = queue.Queue()
        
        # 基准数据
        self.baselines: Dict[str, Dict[str, Any]] = {}
        self.load_baselines()
        
        # 测试配置
        self.test_configs = {
            BenchmarkType.FILE_READ: {
                'iterations': 10,
                'file_sizes': ['small', 'medium', 'large'],
                'strategies': [ReadStrategy.SYNC, ReadStrategy.MAPPED, ReadStrategy.STREAMING]
            },
            BenchmarkType.RENDER: {
                'iterations': 10,
                'content_sizes': ['small', 'medium', 'large'],
                'strategies': [RenderStrategy.SINGLE_THREAD, RenderStrategy.MULTI_THREAD, RenderStrategy.INCREMENTAL]
            },
            BenchmarkType.MEMORY: {
                'iterations': 5,
                'memory_loads': ['light', 'medium', 'heavy'],
                'strategies': [MemoryStrategy.BALANCED, MemoryStrategy.AGGRESSIVE, MemoryStrategy.CONSERVATIVE]
            },
            BenchmarkType.INTEGRATION: {
                'iterations': 3,
                'scenarios': ['normal', 'high_load', 'low_memory']
            },
            BenchmarkType.STRESS: {
                'iterations': 1,
                'concurrent_users': [1, 5, 10, 20],
                'duration_seconds': 60
            }
        }
        # 测试态快速模式
        self._fast_mode = os.environ.get("LAD_TEST_MODE") == "1" or os.environ.get("LAD_QA_FAST") == "1"
        if self._fast_mode:
            self.test_configs[BenchmarkType.FILE_READ]['iterations'] = 1
            self.test_configs[BenchmarkType.RENDER]['iterations'] = 1
            self.test_configs[BenchmarkType.MEMORY]['iterations'] = 1
            self.test_configs[BenchmarkType.INTEGRATION]['iterations'] = 1
            self.test_configs[BenchmarkType.STRESS]['duration_seconds'] = 5
        
        self.logger.info("性能基准测试器初始化完成")

    def _sleep(self, seconds: float) -> None:
        """封装sleep，快速模式下按比例缩短。"""
        if getattr(self, "_fast_mode", False):
            seconds = max(seconds * 0.1, 0.001)
        time.sleep(seconds)
    
    def load_baselines(self):
        """加载基准数据"""
        try:
            baseline_file = self.baseline_dir / "performance_baselines.json"
            if baseline_file.exists():
                with open(baseline_file, 'r', encoding='utf-8') as f:
                    self.baselines = json.load(f)
                self.logger.info(f"已加载 {len(self.baselines)} 个基准数据")
            else:
                self.logger.info("未找到基准数据文件，将创建新的基准")
        except Exception as e:
            self.logger.error(f"加载基准数据失败: {e}")
            self.baselines = {}
    
    def save_baselines(self):
        """保存基准数据"""
        try:
            baseline_file = self.baseline_dir / "performance_baselines.json"
            with builtins.open(baseline_file, 'w', encoding='utf-8') as f:
                json.dump(self.baselines, f, indent=2, ensure_ascii=False)
            self.logger.info("基准数据已保存")
        except Exception as e:
            self.logger.error(f"保存基准数据失败: {e}")
    
    def create_test_files(self, test_dir: Path):
        """创建测试文件"""
        try:
            test_dir.mkdir(parents=True, exist_ok=True)
            
            # 小文件 (约1KB，快速模式下更小)
            _small_mult = 50
            _medium_mult = 2000
            _large_mult = 20000
            if getattr(self, "_fast_mode", False):
                _small_mult = 10
                _medium_mult = 200
                _large_mult = 2000
            small_content = "# 小文件测试\n\n这是一个小的Markdown文件，用于测试基本性能。\n" * _small_mult
            small_file = test_dir / "small_test.md"
            with builtins.open(small_file, 'w', encoding='utf-8') as f:
                f.write(small_content)
            
            # 中等文件 (约100KB，快速模式下更小)
            medium_content = "# 中等文件测试\n\n" + ("这是一个中等大小的Markdown文件，包含更多内容用于测试。\n" * _medium_mult)
            medium_file = test_dir / "medium_test.md"
            with builtins.open(medium_file, 'w', encoding='utf-8') as f:
                f.write(medium_content)
            
            # 大文件 (约1MB，快速模式下更小)
            large_content = "# 大文件测试\n\n" + ("这是一个大文件，用于测试大文件处理性能。包含大量内容。\n" * _large_mult)
            large_file = test_dir / "large_test.md"
            with builtins.open(large_file, 'w', encoding='utf-8') as f:
                f.write(large_content)
            
            self.logger.info("测试文件创建完成")
            return [small_file, medium_file, large_file]
            
        except Exception as e:
            self.logger.error(f"创建测试文件失败: {e}")
            return []
    
    def benchmark_file_read(self, test_files: List[Path]) -> List[BenchmarkResult]:
        """基准测试文件读取性能"""
        results = []
        
        try:
            config = self.test_configs[BenchmarkType.FILE_READ]
            
            for strategy in config['strategies']:
                for test_file in test_files:
                    test_name = f"file_read_{strategy.value}_{test_file.stem}"
                    
                    # 执行多次测试
                    execution_times = []
                    memory_usages = []
                    success_count = 0
                    error_count = 0
                    
                    for i in range(config['iterations']):
                        try:
                            start_time = time.time()
                            start_memory = self.memory_manager.get_memory_info()
                            
                            # 执行文件读取
                            result = self.file_reader.read_file(str(test_file), strategy)
                            
                            end_time = time.time()
                            end_memory = self.memory_manager.get_memory_info()
                            
                            if result['success']:
                                execution_time = (end_time - start_time) * 1000
                                memory_usage = end_memory.used_memory_mb - start_memory.used_memory_mb
                                
                                execution_times.append(execution_time)
                                memory_usages.append(memory_usage)
                                success_count += 1
                            else:
                                error_count += 1
                                
                        except Exception as e:
                            error_count += 1
                            self.logger.error(f"文件读取测试失败 {test_name}: {e}")
                    
                    # 计算指标
                    if execution_times:
                        avg_execution_time = statistics.mean(execution_times)
                        avg_memory_usage = statistics.mean(memory_usages)
                        success_rate = success_count / config['iterations']
                        
                        # 计算吞吐量 (MB/s)
                        file_size_mb = test_file.stat().st_size / 1024 / 1024
                        throughput = file_size_mb / (avg_execution_time / 1000) if avg_execution_time > 0 else 0
                        
                        metrics = BenchmarkMetrics(
                            test_name=test_name,
                            test_type=BenchmarkType.FILE_READ.value,
                            execution_time_ms=avg_execution_time,
                            memory_usage_mb=avg_memory_usage,
                            cpu_usage_percent=0.0,  # 简化实现
                            throughput=throughput,
                            latency_ms=avg_execution_time,
                            success_rate=success_rate,
                            error_count=error_count
                        )
                        
                        # 与基准比较
                        baseline_comparison = self._compare_with_baseline(test_name, metrics)
                        
                        # 生成建议
                        recommendations = self._generate_recommendations(metrics, baseline_comparison)
                        
                        # 确定结果
                        result_status = self._determine_result(metrics, baseline_comparison)
                        
                        benchmark_result = BenchmarkResult(
                            test_name=test_name,
                            test_type=BenchmarkType.FILE_READ.value,
                            result=result_status,
                            metrics=metrics,
                            baseline_comparison=baseline_comparison,
                            recommendations=recommendations,
                            timestamp=time.time()
                        )
                        
                        results.append(benchmark_result)
                        
                        # 保存到队列
                        self.test_results.put(benchmark_result)
            
            self.logger.info(f"文件读取基准测试完成，共 {len(results)} 个测试")
            
        except Exception as e:
            self.logger.error(f"文件读取基准测试失败: {e}")
        
        return results
    
    def benchmark_render(self, test_files: List[Path]) -> List[BenchmarkResult]:
        """基准测试渲染性能"""
        results = []
        
        try:
            config = self.test_configs[BenchmarkType.RENDER]
            
            for strategy in config['strategies']:
                for test_file in test_files:
                    test_name = f"render_{strategy.value}_{test_file.stem}"
                    
                    # 读取文件内容
                    with open(test_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 执行多次测试
                    execution_times = []
                    memory_usages = []
                    success_count = 0
                    error_count = 0
                    
                    for i in range(config['iterations']):
                        try:
                            start_time = time.time()
                            start_memory = self.memory_manager.get_memory_info()
                            
                            # 执行渲染
                            result = self.render_optimizer.render_content(content, strategy)
                            
                            end_time = time.time()
                            end_memory = self.memory_manager.get_memory_info()
                            
                            if result['success']:
                                execution_time = (end_time - start_time) * 1000
                                memory_usage = end_memory.used_memory_mb - start_memory.used_memory_mb
                                
                                execution_times.append(execution_time)
                                memory_usages.append(memory_usage)
                                success_count += 1
                            else:
                                error_count += 1
                                
                        except Exception as e:
                            error_count += 1
                            self.logger.error(f"渲染测试失败 {test_name}: {e}")
                    
                    # 计算指标
                    if execution_times:
                        avg_execution_time = statistics.mean(execution_times)
                        avg_memory_usage = statistics.mean(memory_usages)
                        success_rate = success_count / config['iterations']
                        
                        # 计算渲染速度 (字符/毫秒)
                        content_length = len(content)
                        render_speed = content_length / avg_execution_time if avg_execution_time > 0 else 0
                        
                        metrics = BenchmarkMetrics(
                            test_name=test_name,
                            test_type=BenchmarkType.RENDER.value,
                            execution_time_ms=avg_execution_time,
                            memory_usage_mb=avg_memory_usage,
                            cpu_usage_percent=0.0,  # 简化实现
                            throughput=render_speed,
                            latency_ms=avg_execution_time,
                            success_rate=success_rate,
                            error_count=error_count
                        )
                        
                        # 与基准比较
                        baseline_comparison = self._compare_with_baseline(test_name, metrics)
                        
                        # 生成建议
                        recommendations = self._generate_recommendations(metrics, baseline_comparison)
                        
                        # 确定结果
                        result_status = self._determine_result(metrics, baseline_comparison)
                        
                        benchmark_result = BenchmarkResult(
                            test_name=test_name,
                            test_type=BenchmarkType.RENDER.value,
                            result=result_status,
                            metrics=metrics,
                            baseline_comparison=baseline_comparison,
                            recommendations=recommendations,
                            timestamp=time.time()
                        )
                        
                        results.append(benchmark_result)
                        
                        # 保存到队列
                        self.test_results.put(benchmark_result)
            
            self.logger.info(f"渲染基准测试完成，共 {len(results)} 个测试")
            
        except Exception as e:
            self.logger.error(f"渲染基准测试失败: {e}")
        
        return results
    
    def benchmark_memory(self) -> List[BenchmarkResult]:
        """基准测试内存使用性能"""
        results = []
        
        try:
            config = self.test_configs[BenchmarkType.MEMORY]
            
            for strategy in config['strategies']:
                test_name = f"memory_{strategy.value}"
                
                # 设置内存策略
                self.memory_manager.set_memory_strategy(strategy)
                
                # 执行多次测试
                execution_times = []
                memory_usages = []
                success_count = 0
                error_count = 0
                
                for i in range(config['iterations']):
                    try:
                        start_time = time.time()
                        start_memory = self.memory_manager.get_memory_info()
                        
                        # 执行内存优化
                        result = self.memory_manager.optimize_memory()
                        
                        end_time = time.time()
                        end_memory = self.memory_manager.get_memory_info()
                        
                        if result:
                            execution_time = (end_time - start_time) * 1000
                            memory_usage = end_memory.used_memory_mb
                            
                            execution_times.append(execution_time)
                            memory_usages.append(memory_usage)
                            success_count += 1
                        else:
                            error_count += 1
                            
                    except Exception as e:
                        error_count += 1
                        self.logger.error(f"内存测试失败 {test_name}: {e}")
                
                # 计算指标
                if execution_times:
                    avg_execution_time = statistics.mean(execution_times)
                    avg_memory_usage = statistics.mean(memory_usages)
                    success_rate = success_count / config['iterations']
                    
                    # 计算内存效率
                    memory_efficiency = 1.0 - (avg_memory_usage / 1024)  # 假设1GB为基准
                    
                    metrics = BenchmarkMetrics(
                        test_name=test_name,
                        test_type=BenchmarkType.MEMORY.value,
                        execution_time_ms=avg_execution_time,
                        memory_usage_mb=avg_memory_usage,
                        cpu_usage_percent=0.0,  # 简化实现
                        throughput=memory_efficiency,
                        latency_ms=avg_execution_time,
                        success_rate=success_rate,
                        error_count=error_count
                    )
                    
                    # 与基准比较
                    baseline_comparison = self._compare_with_baseline(test_name, metrics)
                    
                    # 生成建议
                    recommendations = self._generate_recommendations(metrics, baseline_comparison)
                    
                    # 确定结果
                    result_status = self._determine_result(metrics, baseline_comparison)
                    
                    benchmark_result = BenchmarkResult(
                        test_name=test_name,
                        test_type=BenchmarkType.MEMORY.value,
                        result=result_status,
                        metrics=metrics,
                        baseline_comparison=baseline_comparison,
                        recommendations=recommendations,
                        timestamp=time.time()
                    )
                    
                    results.append(benchmark_result)
                    
                    # 保存到队列
                    self.test_results.put(benchmark_result)
            
            self.logger.info(f"内存基准测试完成，共 {len(results)} 个测试")
            
        except Exception as e:
            self.logger.error(f"内存基准测试失败: {e}")
        
        return results
    
    def benchmark_integration(self) -> List[BenchmarkResult]:
        """基准测试集成性能"""
        results = []
        
        try:
            config = self.test_configs[BenchmarkType.INTEGRATION]
            
            for scenario in config['scenarios']:
                test_name = f"integration_{scenario}"
                
                # 执行多次测试
                execution_times = []
                memory_usages = []
                success_count = 0
                error_count = 0
                
                for i in range(config['iterations']):
                    try:
                        start_time = time.time()
                        start_memory = self.memory_manager.get_memory_info()
                        
                        # 模拟集成场景
                        if scenario == 'normal':
                            # 正常负载
                            self._simulate_normal_load()
                        elif scenario == 'high_load':
                            # 高负载
                            self._simulate_high_load()
                        elif scenario == 'low_memory':
                            # 低内存
                            self._simulate_low_memory()
                        
                        end_time = time.time()
                        end_memory = self.memory_manager.get_memory_info()
                        
                        execution_time = (end_time - start_time) * 1000
                        memory_usage = end_memory.used_memory_mb - start_memory.used_memory_mb
                        
                        execution_times.append(execution_time)
                        memory_usages.append(memory_usage)
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        self.logger.error(f"集成测试失败 {test_name}: {e}")
                
                # 计算指标
                if execution_times:
                    avg_execution_time = statistics.mean(execution_times)
                    avg_memory_usage = statistics.mean(memory_usages)
                    success_rate = success_count / config['iterations']
                    
                    metrics = BenchmarkMetrics(
                        test_name=test_name,
                        test_type=BenchmarkType.INTEGRATION.value,
                        execution_time_ms=avg_execution_time,
                        memory_usage_mb=avg_memory_usage,
                        cpu_usage_percent=0.0,  # 简化实现
                        throughput=1.0 / avg_execution_time if avg_execution_time > 0 else 0,
                        latency_ms=avg_execution_time,
                        success_rate=success_rate,
                        error_count=error_count
                    )
                    
                    # 与基准比较
                    baseline_comparison = self._compare_with_baseline(test_name, metrics)
                    
                    # 生成建议
                    recommendations = self._generate_recommendations(metrics, baseline_comparison)
                    
                    # 确定结果
                    result_status = self._determine_result(metrics, baseline_comparison)
                    
                    benchmark_result = BenchmarkResult(
                        test_name=test_name,
                        test_type=BenchmarkType.INTEGRATION.value,
                        result=result_status,
                        metrics=metrics,
                        baseline_comparison=baseline_comparison,
                        recommendations=recommendations,
                        timestamp=time.time()
                    )
                    
                    results.append(benchmark_result)
                    
                    # 保存到队列
                    self.test_results.put(benchmark_result)
            
            self.logger.info(f"集成基准测试完成，共 {len(results)} 个测试")
            
        except Exception as e:
            self.logger.error(f"集成基准测试失败: {e}")
        
        return results
    
    def _simulate_normal_load(self):
        """模拟正常负载"""
        self._sleep(0.1)  # 模拟100ms的处理时间
    
    def _simulate_high_load(self):
        """模拟高负载"""
        self._sleep(0.5)  # 模拟500ms的处理时间
    
    def _simulate_low_memory(self):
        """模拟低内存情况"""
        self._sleep(0.2)  # 模拟200ms的处理时间
    
    def _compare_with_baseline(self, test_name: str, metrics: BenchmarkMetrics) -> Dict[str, Any]:
        """与基准比较"""
        if test_name not in self.baselines:
            return {
                'has_baseline': False,
                'message': '无基准数据'
            }
        
        baseline = self.baselines[test_name]
        comparison = {
            'has_baseline': True,
            'execution_time_diff': metrics.execution_time_ms - baseline.get('execution_time_ms', 0),
            'execution_time_ratio': metrics.execution_time_ms / baseline.get('execution_time_ms', 1) if baseline.get('execution_time_ms', 0) > 0 else 0,
            'memory_usage_diff': metrics.memory_usage_mb - baseline.get('memory_usage_mb', 0),
            'memory_usage_ratio': metrics.memory_usage_mb / baseline.get('memory_usage_mb', 1) if baseline.get('memory_usage_mb', 0) > 0 else 0,
            'throughput_diff': metrics.throughput - baseline.get('throughput', 0),
            'throughput_ratio': metrics.throughput / baseline.get('throughput', 1) if baseline.get('throughput', 0) > 0 else 0
        }
        
        return comparison
    
    def _generate_recommendations(self, metrics: BenchmarkMetrics, baseline_comparison: Dict[str, Any]) -> List[str]:
        """生成性能建议"""
        recommendations = []
        
        if baseline_comparison.get('has_baseline', False):
            # 执行时间建议
            if baseline_comparison.get('execution_time_ratio', 1) > 1.2:
                recommendations.append("执行时间增加超过20%，建议检查性能瓶颈")
            elif baseline_comparison.get('execution_time_ratio', 1) < 0.8:
                recommendations.append("执行时间减少超过20%，性能有所改善")
            
            # 内存使用建议
            if baseline_comparison.get('memory_usage_ratio', 1) > 1.3:
                recommendations.append("内存使用增加超过30%，建议优化内存管理")
            elif baseline_comparison.get('memory_usage_ratio', 1) < 0.7:
                recommendations.append("内存使用减少超过30%，内存效率显著提升")
            
            # 吞吐量建议
            if baseline_comparison.get('throughput_ratio', 1) < 0.8:
                recommendations.append("吞吐量下降超过20%，建议优化处理流程")
            elif baseline_comparison.get('throughput_ratio', 1) > 1.2:
                recommendations.append("吞吐量提升超过20%，性能表现优秀")
        
        # 通用建议
        if metrics.success_rate < 0.9:
            recommendations.append("成功率低于90%，建议检查错误处理机制")
        
        if metrics.error_count > 0:
            recommendations.append("存在错误，建议分析错误原因并优化")
        
        if not recommendations:
            recommendations.append("性能表现良好，继续保持")
        
        return recommendations
    
    def _determine_result(self, metrics: BenchmarkMetrics, baseline_comparison: Dict[str, Any]) -> BenchmarkResultEnum:
        """确定测试结果"""
        if not baseline_comparison.get('has_baseline', False):
            return BenchmarkResultEnum.UNKNOWN
        
        # 检查关键指标
        execution_time_ratio = baseline_comparison.get('execution_time_ratio', 1)
        memory_usage_ratio = baseline_comparison.get('memory_usage_ratio', 1)
        success_rate = metrics.success_rate
        
        if success_rate < 0.8:
            return BenchmarkResultEnum.FAIL
        elif execution_time_ratio > 1.5 or memory_usage_ratio > 1.5:
            return BenchmarkResultEnum.WARNING
        elif execution_time_ratio < 1.2 and memory_usage_ratio < 1.2:
            return BenchmarkResultEnum.PASS
        else:
            return BenchmarkResultEnum.WARNING
    
    def run_all_benchmarks(self) -> Dict[str, List[BenchmarkResult]]:
        """运行所有基准测试"""
        try:
            self.logger.info("开始运行所有基准测试")
            
            # 创建测试文件
            test_dir = self.baseline_dir / "test_files"
            test_files = self.create_test_files(test_dir)
            
            if not test_files:
                raise Exception("无法创建测试文件")
            
            # 运行各项测试
            results = {
                BenchmarkType.FILE_READ.value: self.benchmark_file_read(test_files),
                BenchmarkType.RENDER.value: self.benchmark_render(test_files),
                BenchmarkType.MEMORY.value: self.benchmark_memory(),
                BenchmarkType.INTEGRATION.value: self.benchmark_integration()
            }
            
            # 更新基准数据
            self._update_baselines(results)
            
            # 保存基准数据
            self.save_baselines()
            
            self.logger.info("所有基准测试完成")
            return results
            
        except Exception as e:
            self.logger.error(f"运行基准测试失败: {e}")
            return {}
    
    def _update_baselines(self, results: Dict[str, List[BenchmarkResult]]):
        """更新基准数据"""
        try:
            for test_type, test_results in results.items():
                for result in test_results:
                    baseline_key = result.test_name
                    self.baselines[baseline_key] = {
                        'execution_time_ms': result.metrics.execution_time_ms,
                        'memory_usage_mb': result.metrics.memory_usage_mb,
                        'throughput': result.metrics.throughput,
                        'success_rate': result.metrics.success_rate,
                        'timestamp': result.timestamp,
                        'test_type': result.test_type
                    }
            
            self.logger.info(f"已更新 {len(self.baselines)} 个基准数据")
            
        except Exception as e:
            self.logger.error(f"更新基准数据失败: {e}")
    
    def generate_report(self, results: Dict[str, List[BenchmarkResult]]) -> str:
        """生成性能报告"""
        try:
            report_lines = []
            report_lines.append("# 性能基准测试报告")
            report_lines.append(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append("")
            
            total_tests = 0
            passed_tests = 0
            failed_tests = 0
            warning_tests = 0
            
            for test_type, test_results in results.items():
                report_lines.append(f"## {test_type} 测试结果")
                report_lines.append("")
                
                for result in test_results:
                    total_tests += 1
                    
                    if result.result == BenchmarkResultEnum.PASS:
                        passed_tests += 1
                        status = "✅ 通过"
                    elif result.result == BenchmarkResultEnum.FAIL:
                        failed_tests += 1
                        status = "❌ 失败"
                    elif result.result == BenchmarkResultEnum.WARNING:
                        warning_tests += 1
                        status = "⚠️ 警告"
                    else:
                        status = "❓ 未知"
                    
                    report_lines.append(f"### {result.test_name} - {status}")
                    report_lines.append(f"- 执行时间: {result.metrics.execution_time_ms:.2f}ms")
                    report_lines.append(f"- 内存使用: {result.metrics.memory_usage_mb:.2f}MB")
                    report_lines.append(f"- 吞吐量: {result.metrics.throughput:.2f}")
                    report_lines.append(f"- 成功率: {result.metrics.success_rate:.1%}")
                    
                    if result.recommendations:
                        report_lines.append("- 建议:")
                        for rec in result.recommendations:
                            report_lines.append(f"  - {rec}")
                    
                    report_lines.append("")
            
            # 总结
            report_lines.append("## 测试总结")
            report_lines.append(f"- 总测试数: {total_tests}")
            report_lines.append(f"- 通过: {passed_tests}")
            report_lines.append(f"- 失败: {failed_tests}")
            report_lines.append(f"- 警告: {warning_tests}")
            report_lines.append(f"- 通过率: {passed_tests/total_tests:.1%}" if total_tests > 0 else "- 通过率: N/A")
            
            report = "\n".join(report_lines)
            
            # 保存报告
            report_file = self.baseline_dir / f"performance_report_{int(time.time())}.md"
            with builtins.open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            self.logger.info(f"性能报告已保存到: {report_file}")
            
            return report
            
        except Exception as e:
            self.logger.error(f"生成性能报告失败: {e}")
            return f"生成报告失败: {e}"
    
    def get_test_results(self) -> List[BenchmarkResult]:
        """获取测试结果"""
        results = []
        while not self.test_results.empty():
            try:
                result = self.test_results.get_nowait()
                results.append(result)
            except queue.Empty:
                break
        return results
    
    def shutdown(self):
        """关闭基准测试器"""
        try:
            # 关闭性能组件
            self.file_reader.shutdown()
            self.render_optimizer.shutdown()
            self.memory_manager.shutdown()
            
            # 关闭错误处理器
            self.error_handler.shutdown()
            
            self.logger.info("性能基准测试器已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭基准测试器时出现错误: {e}")
    
    def __del__(self):
        """析构函数"""
        try:
            self.shutdown()
        except:
            pass 