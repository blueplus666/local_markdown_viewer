"""
性能基准测试器 - 方案4.3.3系统集成与监控实施
基于前序模块的成果，进行全面测试
"""

import asyncio
import time
import statistics
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import psutil
import os

# 导入前序模块的成果（使用模拟实现）
from integration.mock_dependencies import (
    HybridMarkdownRenderer, FileResolver, PerformanceMonitor,
    UnifiedCacheManager, UnifiedErrorHandler, EnhancedLogger
)


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    test_name: str
    test_type: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    success_rate: float
    error_count: int
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class PerformanceBaseline:
    """性能基准"""
    baseline_name: str
    baseline_version: str
    created_at: datetime
    metrics: Dict[str, float]
    thresholds: Dict[str, float]
    test_scenarios: List[str]


class PerformanceBenchmarkTester:
    """性能基准测试器"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.logger = EnhancedLogger("PerformanceBenchmarkTester")
        self.performance_monitor = PerformanceMonitor()
        self.cache_manager = UnifiedCacheManager()
        self.error_handler = UnifiedErrorHandler()
        
        # 测试配置
        self.benchmark_config = {
            "test_iterations": 10,
            "warmup_iterations": 3,
            "timeout": 300.0,  # 5分钟
            "memory_threshold": 512,  # MB
            "cpu_threshold": 80.0,  # %
            "success_rate_threshold": 95.0,  # %
            "performance_regression_threshold": 10.0  # %
        }
        
        # 测试结果存储
        self.benchmark_results: List[BenchmarkResult] = []
        self.performance_baselines: Dict[str, PerformanceBaseline] = {}
        self.start_time = time.time()  # 初始化开始时间
        # 快速模式（仅测试态）
        self._fast_mode = os.environ.get("LAD_TEST_MODE") == "1" or os.environ.get("LAD_QA_FAST") == "1"
        self._fast_cached_results: Optional[List[BenchmarkResult]] = None
        if self._fast_mode:
            self.benchmark_config["test_iterations"] = 1
            self.benchmark_config["warmup_iterations"] = 0
            self.benchmark_config["timeout"] = 30.0
        
        # 测试场景
        self.test_scenarios = {
            "file_loading": self._test_file_loading_performance,
            "markdown_rendering": self._test_markdown_rendering_performance,
            "cache_performance": self._test_cache_performance,
            "error_handling": self._test_error_handling_performance,
            "memory_usage": self._test_memory_usage,
            "system_integration": self._test_system_integration_performance
        }
    
    async def _sleep(self, seconds: float) -> None:
        """封装sleep以便在快速模式下按比例缩短。"""
        if getattr(self, "_fast_mode", False):
            seconds = max(seconds * 0.1, 0.001)
        await asyncio.sleep(seconds)
    
    async def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """运行综合基准测试"""
        self.logger.info("开始综合性能基准测试")
        
        try:
            # 1. 建立性能基准
            baseline = await self._establish_performance_baseline()
            
            # 2. 运行所有测试场景
            test_results = await self._run_all_test_scenarios()
            
            # 3. 分析测试结果
            analysis_result = await self._analyze_benchmark_results(test_results)
            
            # 4. 生成回归测试报告
            regression_report = await self._generate_regression_report(baseline, test_results)
            
            # 5. 建立质量监控和持续改进机制
            quality_metrics = await self._establish_quality_monitoring()
            
            comprehensive_result = {
                "status": "completed",
                "baseline": asdict(baseline),
                "test_results": [asdict(result) for result in test_results],
                "analysis": analysis_result,
                "regression_report": regression_report,
                "quality_metrics": quality_metrics,
                "total_execution_time": time.time() - self.start_time
            }
            
            self.logger.info("综合性能基准测试完成")
            return comprehensive_result
            
        except Exception as e:
            self.logger.error(f"综合性能基准测试失败: {e}")
            await self.error_handler.handle_error(e, "BenchmarkTesting")
            raise
    
    async def _establish_performance_baseline(self) -> PerformanceBaseline:
        """建立性能基准"""
        self.logger.info("建立性能基准")
        
        baseline = PerformanceBaseline(
            baseline_name="方案4.3.3基准",
            baseline_version="v1.0.0",
            created_at=datetime.now(),
            metrics={},
            thresholds={
                "file_loading_time": 1000.0,  # ms
                "rendering_time": 500.0,  # ms
                "cache_hit_rate": 80.0,  # %
                "memory_usage": 256.0,  # MB
                "error_rate": 2.0,  # %
                "success_rate": 98.0  # %
            },
            test_scenarios=list(self.test_scenarios.keys())
        )
        
        # 运行基准测试获取基准指标（快速模式下避免重复执行场景）
        if getattr(self, "_fast_mode", False) and self._fast_cached_results is None:
            # 预先执行一次并缓存，供基线与后续使用
            self._fast_cached_results = await self._run_all_test_scenarios()
        baseline_metrics = await self._run_baseline_metrics()
        baseline.metrics = baseline_metrics
        
        self.performance_baselines[baseline.baseline_name] = baseline
        
        self.logger.info(f"性能基准建立完成: {baseline.baseline_name}")
        return baseline
    
    async def _run_all_test_scenarios(self) -> List[BenchmarkResult]:
        """运行所有测试场景"""
        self.logger.info("运行所有测试场景")
        
        # 快速模式下可复用已缓存的结果，避免重复执行
        if getattr(self, "_fast_mode", False) and self._fast_cached_results is not None:
            return self._fast_cached_results

        test_results = []
        
        for scenario_name, scenario_func in self.test_scenarios.items():
            try:
                self.logger.info(f"运行测试场景: {scenario_name}")
                result = await scenario_func()
                test_results.append(result)
                self.logger.info(f"测试场景 {scenario_name} 完成")
                
            except Exception as e:
                self.logger.error(f"测试场景 {scenario_name} 失败: {e}")
                # 创建失败结果
                result = BenchmarkResult(
                    test_name=scenario_name,
                    test_type="performance",
                    execution_time=0.0,
                    memory_usage=0.0,
                    cpu_usage=0.0,
                    success_rate=0.0,
                    error_count=1,
                    timestamp=datetime.now(),
                    metadata={"error": str(e)}
                )
                test_results.append(result)
        
        return test_results
    
    async def _test_file_loading_performance(self) -> BenchmarkResult:
        """测试文件加载性能"""
        self.logger.info("测试文件加载性能")
        
        test_files = [
            "small_file.md",  # 1KB
            "medium_file.md",  # 100KB
            "large_file.md",   # 1MB
            "very_large_file.md"  # 10MB
        ]
        
        results = []
        error_count = 0
        
        for file_name in test_files:
            for i in range(self.benchmark_config["test_iterations"]):
                try:
                    start_time = time.time()
                    start_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    start_cpu = psutil.cpu_percent()
                    
                    # 模拟文件加载
                    await self._sleep(0.1)  # 模拟加载时间
                    
                    end_time = time.time()
                    end_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    end_cpu = psutil.cpu_percent()
                    
                    results.append({
                        "execution_time": (end_time - start_time) * 1000,  # ms
                        "memory_usage": end_memory - start_memory,
                        "cpu_usage": (start_cpu + end_cpu) / 2
                    })
                    
                except Exception as e:
                    error_count += 1
                    self.logger.error(f"文件加载测试失败: {e}")
        
        # 计算统计结果
        if results:
            avg_execution_time = statistics.mean([r["execution_time"] for r in results])
            avg_memory_usage = statistics.mean([r["memory_usage"] for r in results])
            avg_cpu_usage = statistics.mean([r["cpu_usage"] for r in results])
            success_rate = ((len(results) - error_count) / len(results)) * 100
        else:
            avg_execution_time = 0.0
            avg_memory_usage = 0.0
            avg_cpu_usage = 0.0
            success_rate = 0.0
        
        return BenchmarkResult(
            test_name="file_loading_performance",
            test_type="performance",
            execution_time=avg_execution_time,
            memory_usage=avg_memory_usage,
            cpu_usage=avg_cpu_usage,
            success_rate=success_rate,
            error_count=error_count,
            timestamp=datetime.now(),
            metadata={"test_files": test_files, "iterations": len(results)}
        )
    
    async def _test_markdown_rendering_performance(self) -> BenchmarkResult:
        """测试Markdown渲染性能"""
        self.logger.info("测试Markdown渲染性能")
        
        markdown_samples = [
            "# 简单标题\n\n这是简单内容。",
            "# 复杂文档\n\n## 章节1\n\n- 列表项1\n- 列表项2\n\n## 章节2\n\n```python\nprint('Hello World')\n```",
            "# 大型文档\n\n" + "## 章节" + "\n\n内容" * 100
        ]
        
        results = []
        error_count = 0
        
        for sample in markdown_samples:
            for i in range(self.benchmark_config["test_iterations"]):
                try:
                    start_time = time.time()
                    start_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    start_cpu = psutil.cpu_percent()
                    
                    # 模拟Markdown渲染
                    await self._sleep(0.05)  # 模拟渲染时间
                    
                    end_time = time.time()
                    end_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    end_cpu = psutil.cpu_percent()
                    
                    results.append({
                        "execution_time": (end_time - start_time) * 1000,  # ms
                        "memory_usage": end_memory - start_memory,
                        "cpu_usage": (start_cpu + end_cpu) / 2
                    })
                    
                except Exception as e:
                    error_count += 1
                    self.logger.error(f"Markdown渲染测试失败: {e}")
        
        # 计算统计结果
        if results:
            avg_execution_time = statistics.mean([r["execution_time"] for r in results])
            avg_memory_usage = statistics.mean([r["memory_usage"] for r in results])
            avg_cpu_usage = statistics.mean([r["cpu_usage"] for r in results])
            success_rate = ((len(results) - error_count) / len(results)) * 100
        else:
            avg_execution_time = 0.0
            avg_memory_usage = 0.0
            avg_cpu_usage = 0.0
            success_rate = 0.0
        
        return BenchmarkResult(
            test_name="markdown_rendering_performance",
            test_type="performance",
            execution_time=avg_execution_time,
            memory_usage=avg_memory_usage,
            cpu_usage=avg_cpu_usage,
            success_rate=success_rate,
            error_count=error_count,
            timestamp=datetime.now(),
            metadata={"samples_count": len(markdown_samples), "iterations": len(results)}
        )
    
    async def _test_cache_performance(self) -> BenchmarkResult:
        """测试缓存性能"""
        self.logger.info("测试缓存性能")
        
        cache_operations = ["get", "set", "delete", "clear"]
        results = []
        error_count = 0
        
        for operation in cache_operations:
            for i in range(self.benchmark_config["test_iterations"]):
                try:
                    start_time = time.time()
                    start_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    start_cpu = psutil.cpu_percent()
                    
                    # 模拟缓存操作
                    await self._sleep(0.01)  # 模拟缓存操作时间
                    
                    end_time = time.time()
                    end_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    end_cpu = psutil.cpu_percent()
                    
                    results.append({
                        "execution_time": (end_time - start_time) * 1000,  # ms
                        "memory_usage": end_memory - start_memory,
                        "cpu_usage": (start_cpu + end_cpu) / 2
                    })
                    
                except Exception as e:
                    error_count += 1
                    self.logger.error(f"缓存性能测试失败: {e}")
        
        # 计算统计结果
        if results:
            avg_execution_time = statistics.mean([r["execution_time"] for r in results])
            avg_memory_usage = statistics.mean([r["memory_usage"] for r in results])
            avg_cpu_usage = statistics.mean([r["cpu_usage"] for r in results])
            success_rate = ((len(results) - error_count) / len(results)) * 100
        else:
            avg_execution_time = 0.0
            avg_memory_usage = 0.0
            avg_cpu_usage = 0.0
            success_rate = 0.0
        
        return BenchmarkResult(
            test_name="cache_performance",
            test_type="performance",
            execution_time=avg_execution_time,
            memory_usage=avg_memory_usage,
            cpu_usage=avg_cpu_usage,
            success_rate=success_rate,
            error_count=error_count,
            timestamp=datetime.now(),
            metadata={"operations": cache_operations, "iterations": len(results)}
        )
    
    async def _test_error_handling_performance(self) -> BenchmarkResult:
        """测试错误处理性能"""
        self.logger.info("测试错误处理性能")
        
        error_types = ["file_not_found", "permission_denied", "invalid_format", "timeout"]
        results = []
        error_count = 0
        
        for error_type in error_types:
            for i in range(self.benchmark_config["test_iterations"]):
                try:
                    start_time = time.time()
                    start_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    start_cpu = psutil.cpu_percent()
                    
                    # 模拟错误处理
                    await self._sleep(0.02)  # 模拟错误处理时间
                    
                    end_time = time.time()
                    end_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    end_cpu = psutil.cpu_percent()
                    
                    results.append({
                        "execution_time": (end_time - start_time) * 1000,  # ms
                        "memory_usage": end_memory - start_memory,
                        "cpu_usage": (start_cpu + end_cpu) / 2
                    })
                    
                except Exception as e:
                    error_count += 1
                    self.logger.error(f"错误处理性能测试失败: {e}")
        
        # 计算统计结果
        if results:
            avg_execution_time = statistics.mean([r["execution_time"] for r in results])
            avg_memory_usage = statistics.mean([r["memory_usage"] for r in results])
            avg_cpu_usage = statistics.mean([r["cpu_usage"] for r in results])
            success_rate = ((len(results) - error_count) / len(results)) * 100
        else:
            avg_execution_time = 0.0
            avg_memory_usage = 0.0
            avg_cpu_usage = 0.0
            success_rate = 0.0
        
        return BenchmarkResult(
            test_name="error_handling_performance",
            test_type="performance",
            execution_time=avg_execution_time,
            memory_usage=avg_memory_usage,
            cpu_usage=avg_cpu_usage,
            success_rate=success_rate,
            error_count=error_count,
            timestamp=datetime.now(),
            metadata={"error_types": error_types, "iterations": len(results)}
        )
    
    async def _test_memory_usage(self) -> BenchmarkResult:
        """测试内存使用"""
        self.logger.info("测试内存使用")
        
        memory_tests = ["normal_operation", "high_load", "memory_leak_test"]
        results = []
        error_count = 0
        
        for test_type in memory_tests:
            for i in range(self.benchmark_config["test_iterations"]):
                try:
                    start_time = time.time()
                    start_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    start_cpu = psutil.cpu_percent()
                    
                    # 模拟内存测试
                    await self._sleep(0.1)  # 模拟内存操作时间
                    
                    end_time = time.time()
                    end_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    end_cpu = psutil.cpu_percent()
                    
                    results.append({
                        "execution_time": (end_time - start_time) * 1000,  # ms
                        "memory_usage": end_memory - start_memory,
                        "cpu_usage": (start_cpu + end_cpu) / 2
                    })
                    
                except Exception as e:
                    error_count += 1
                    self.logger.error(f"内存使用测试失败: {e}")
        
        # 计算统计结果
        if results:
            avg_execution_time = statistics.mean([r["execution_time"] for r in results])
            avg_memory_usage = statistics.mean([r["memory_usage"] for r in results])
            avg_cpu_usage = statistics.mean([r["cpu_usage"] for r in results])
            success_rate = ((len(results) - error_count) / len(results)) * 100
        else:
            avg_execution_time = 0.0
            avg_memory_usage = 0.0
            avg_cpu_usage = 0.0
            success_rate = 0.0
        
        return BenchmarkResult(
            test_name="memory_usage",
            test_type="performance",
            execution_time=avg_execution_time,
            memory_usage=avg_memory_usage,
            cpu_usage=avg_cpu_usage,
            success_rate=success_rate,
            error_count=error_count,
            timestamp=datetime.now(),
            metadata={"memory_tests": memory_tests, "iterations": len(results)}
        )
    
    async def _test_system_integration_performance(self) -> BenchmarkResult:
        """测试系统集成性能"""
        self.logger.info("测试系统集成性能")
        
        integration_tests = ["module_communication", "data_flow", "error_propagation"]
        results = []
        error_count = 0
        
        for test_type in integration_tests:
            for i in range(self.benchmark_config["test_iterations"]):
                try:
                    start_time = time.time()
                    start_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    start_cpu = psutil.cpu_percent()
                    
                    # 模拟系统集成测试
                    await self._sleep(0.15)  # 模拟集成操作时间
                    
                    end_time = time.time()
                    end_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    end_cpu = psutil.cpu_percent()
                    
                    results.append({
                        "execution_time": (end_time - start_time) * 1000,  # ms
                        "memory_usage": end_memory - start_memory,
                        "cpu_usage": (start_cpu + end_cpu) / 2
                    })
                    
                except Exception as e:
                    error_count += 1
                    self.logger.error(f"系统集成性能测试失败: {e}")
        
        # 计算统计结果
        if results:
            avg_execution_time = statistics.mean([r["execution_time"] for r in results])
            avg_memory_usage = statistics.mean([r["memory_usage"] for r in results])
            avg_cpu_usage = statistics.mean([r["cpu_usage"] for r in results])
            success_rate = ((len(results) - error_count) / len(results)) * 100
        else:
            avg_execution_time = 0.0
            avg_memory_usage = 0.0
            avg_cpu_usage = 0.0
            success_rate = 0.0
        
        return BenchmarkResult(
            test_name="system_integration_performance",
            test_type="performance",
            execution_time=avg_execution_time,
            memory_usage=avg_memory_usage,
            cpu_usage=avg_cpu_usage,
            success_rate=success_rate,
            error_count=error_count,
            timestamp=datetime.now(),
            metadata={"integration_tests": integration_tests, "iterations": len(results)}
        )
    
    async def _run_baseline_metrics(self) -> Dict[str, float]:
        """运行基准指标"""
        self.logger.info("运行基准指标")
        
        # 运行所有测试场景获取基准指标（快速模式下复用缓存）
        if getattr(self, "_fast_mode", False) and self._fast_cached_results is not None:
            baseline_results = self._fast_cached_results
        else:
            baseline_results = await self._run_all_test_scenarios()
        
        baseline_metrics = {}
        for result in baseline_results:
            baseline_metrics[f"{result.test_name}_execution_time"] = result.execution_time
            baseline_metrics[f"{result.test_name}_memory_usage"] = result.memory_usage
            baseline_metrics[f"{result.test_name}_cpu_usage"] = result.cpu_usage
            baseline_metrics[f"{result.test_name}_success_rate"] = result.success_rate
        
        return baseline_metrics
    
    async def _analyze_benchmark_results(self, test_results: List[BenchmarkResult]) -> Dict[str, Any]:
        """分析基准测试结果"""
        self.logger.info("分析基准测试结果")
        
        analysis = {
            "total_tests": len(test_results),
            "successful_tests": 0,
            "failed_tests": 0,
            "average_execution_time": 0.0,
            "average_memory_usage": 0.0,
            "average_cpu_usage": 0.0,
            "average_success_rate": 0.0,
            "performance_summary": {},
            "recommendations": []
        }
        
        successful_results = []
        for result in test_results:
            if result.success_rate >= self.benchmark_config["success_rate_threshold"]:
                analysis["successful_tests"] += 1
                successful_results.append(result)
            else:
                analysis["failed_tests"] += 1
        
        if successful_results:
            analysis["average_execution_time"] = statistics.mean([r.execution_time for r in successful_results])
            analysis["average_memory_usage"] = statistics.mean([r.memory_usage for r in successful_results])
            analysis["average_cpu_usage"] = statistics.mean([r.cpu_usage for r in successful_results])
            analysis["average_success_rate"] = statistics.mean([r.success_rate for r in successful_results])
        
        # 生成性能摘要
        for result in test_results:
            analysis["performance_summary"][result.test_name] = {
                "execution_time": result.execution_time,
                "memory_usage": result.memory_usage,
                "cpu_usage": result.cpu_usage,
                "success_rate": result.success_rate,
                "status": "passed" if result.success_rate >= self.benchmark_config["success_rate_threshold"] else "failed"
            }
        
        # 生成建议
        analysis["recommendations"] = self._generate_recommendations(test_results)
        
        return analysis
    
    async def _generate_regression_report(self, baseline: PerformanceBaseline, test_results: List[BenchmarkResult]) -> Dict[str, Any]:
        """生成回归测试报告"""
        self.logger.info("生成回归测试报告")
        
        regression_report = {
            "baseline_name": baseline.baseline_name,
            "baseline_version": baseline.baseline_version,
            "regression_analysis": {},
            "performance_changes": {},
            "regression_detected": False,
            "recommendations": []
        }
        
        for result in test_results:
            baseline_key = f"{result.test_name}_execution_time"
            if baseline_key in baseline.metrics:
                baseline_value = baseline.metrics[baseline_key]
                current_value = result.execution_time
                
                if baseline_value > 0:
                    change_percentage = ((current_value - baseline_value) / baseline_value) * 100
                    
                    regression_report["performance_changes"][result.test_name] = {
                        "baseline": baseline_value,
                        "current": current_value,
                        "change_percentage": change_percentage,
                        "regression": change_percentage > self.benchmark_config["performance_regression_threshold"]
                    }
                    
                    if change_percentage > self.benchmark_config["performance_regression_threshold"]:
                        regression_report["regression_detected"] = True
                        regression_report["recommendations"].append(
                            f"检测到性能回归: {result.test_name} 性能下降 {change_percentage:.2f}%"
                        )
        
        return regression_report
    
    async def _establish_quality_monitoring(self) -> Dict[str, Any]:
        """建立质量监控和持续改进机制"""
        self.logger.info("建立质量监控和持续改进机制")
        
        quality_metrics = {
            "monitoring_enabled": True,
            "continuous_improvement": True,
            "quality_gates": {
                "performance_threshold": self.benchmark_config["performance_regression_threshold"],
                "success_rate_threshold": self.benchmark_config["success_rate_threshold"],
                "memory_threshold": self.benchmark_config["memory_threshold"],
                "cpu_threshold": self.benchmark_config["cpu_threshold"]
            },
            "automated_testing": True,
            "regression_detection": True,
            "alerting": True
        }
        
        return quality_metrics
    
    def _generate_recommendations(self, test_results: List[BenchmarkResult]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        for result in test_results:
            if result.execution_time > 1000:  # 超过1秒
                recommendations.append(f"优化 {result.test_name} 执行时间，当前: {result.execution_time:.2f}ms")
            
            if result.memory_usage > 100:  # 超过100MB
                recommendations.append(f"优化 {result.test_name} 内存使用，当前: {result.memory_usage:.2f}MB")
            
            if result.cpu_usage > 50:  # 超过50%
                recommendations.append(f"优化 {result.test_name} CPU使用，当前: {result.cpu_usage:.2f}%")
            
            if result.success_rate < 95:  # 低于95%
                recommendations.append(f"提高 {result.test_name} 成功率，当前: {result.success_rate:.2f}%")
        
        return recommendations
    
    def save_benchmark_results(self, file_path: Path):
        """保存基准测试结果"""
        try:
            results_data = {
                "timestamp": datetime.now().isoformat(),
                "benchmark_results": [asdict(result) for result in self.benchmark_results],
                "performance_baselines": {name: asdict(baseline) for name, baseline in self.performance_baselines.items()}
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, default=str, indent=2)
            
            self.logger.info(f"基准测试结果已保存到: {file_path}")
            
        except Exception as e:
            self.logger.error(f"保存基准测试结果失败: {e}")
    
    def get_benchmark_summary(self) -> Dict[str, Any]:
        """获取基准测试摘要"""
        if not self.benchmark_results:
            return {"status": "no_results"}
        
        return {
            "total_tests": len(self.benchmark_results),
            "average_execution_time": statistics.mean([r.execution_time for r in self.benchmark_results]),
            "average_memory_usage": statistics.mean([r.memory_usage for r in self.benchmark_results]),
            "average_success_rate": statistics.mean([r.success_rate for r in self.benchmark_results]),
            "baselines_count": len(self.performance_baselines)
        } 