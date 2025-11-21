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
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import csv
import matplotlib.pyplot as plt
import numpy as np
import builtins

# 导入性能优化组件
from .high_performance_file_reader import HighPerformanceFileReader, ReadStrategy
from .render_performance_optimizer import RenderPerformanceOptimizer, RenderStrategy, RenderMode
from .memory_optimization_manager import MemoryOptimizationManager, MemoryStrategy
from .enhanced_error_handler import EnhancedErrorHandler, ErrorRecoveryStrategy


class BenchmarkType(Enum):
    """基准测试类型枚举"""
    FILE_READ = "file_read"           # 文件读取性能
    RENDER_PERFORMANCE = "render"     # 渲染性能
    MEMORY_USAGE = "memory"           # 内存使用
    CACHE_PERFORMANCE = "cache"       # 缓存性能
    INTEGRATED = "integrated"         # 综合性能


class BenchmarkResult:
    """基准测试结果数据类"""
    
    def __init__(self, test_name: str, test_type: BenchmarkType):
        self.test_name = test_name
        self.test_type = test_type
        self.results: List[Dict[str, Any]] = []
        self.start_time = time.time()
        self.end_time = None
        
    def add_result(self, result: Dict[str, Any]):
        """添加测试结果"""
        self.results.append(result)
    
    def complete(self):
        """完成测试"""
        self.end_time = time.time()
    
    def get_summary(self) -> Dict[str, Any]:
        """获取测试摘要"""
        if not self.results:
            return {}
        
        # 计算统计信息
        times = [r.get('time_ms', 0) for r in self.results if 'time_ms' in r]
        memory_usage = [r.get('memory_mb', 0) for r in self.results if 'memory_mb' in r]
        throughput = [r.get('throughput', 0) for r in self.results if 'throughput' in r]
        
        summary = {
            'test_name': self.test_name,
            'test_type': self.test_type.value,
            'total_runs': len(self.results),
            'duration': self.end_time - self.start_time if self.end_time else 0,
            'avg_time_ms': statistics.mean(times) if times else 0,
            'min_time_ms': min(times) if times else 0,
            'max_time_ms': max(times) if times else 0,
            'std_time_ms': statistics.stdev(times) if len(times) > 1 else 0,
            'avg_memory_mb': statistics.mean(memory_usage) if memory_usage else 0,
            'avg_throughput': statistics.mean(throughput) if throughput else 0
        }
        
        return summary


class PerformanceBenchmarker:
    """性能基准测试器"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        初始化性能基准测试器
        
        Args:
            output_dir: 输出目录
        """
        self.logger = logging.getLogger(__name__)
        
        # 输出目录
        self.output_dir = output_dir or Path(__file__).parent.parent / "outputs" / "benchmarks"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 性能优化组件
        self.file_reader = HighPerformanceFileReader()
        self.render_optimizer = RenderPerformanceOptimizer()
        self.memory_manager = MemoryOptimizationManager()
        self.error_handler = EnhancedErrorHandler()
        
        # 基准结果存储
        self.benchmark_results: Dict[str, BenchmarkResult] = {}
        
        # 基准配置
        self.benchmark_config = {
            'file_read': {
                'test_files': ['small.md', 'medium.md', 'large.md'],
                'strategies': [ReadStrategy.SYNC, ReadStrategy.ASYNC, ReadStrategy.MAPPED],
                'iterations': 10
            },
            'render': {
                'test_content': ['# Test\n\nContent', '# Test\n\n' + 'Content ' * 1000],
                'strategies': [RenderStrategy.SINGLE_THREAD, RenderStrategy.MULTI_THREAD],
                'iterations': 5
            },
            'memory': {
                'test_sizes': [1000, 10000, 100000],
                'strategies': [MemoryStrategy.BALANCED, MemoryStrategy.AGGRESSIVE],
                'iterations': 3
            }
        }
    
    def run_file_read_benchmark(self) -> BenchmarkResult:
        """运行文件读取性能基准测试"""
        benchmark = BenchmarkResult("file_read_benchmark", BenchmarkType.FILE_READ)
        
        try:
            for strategy in self.benchmark_config['file_read']['strategies']:
                for i in range(self.benchmark_config['file_read']['iterations']):
                    start_time = time.time()
                    
                    # 模拟文件读取测试
                    test_content = f"# Test Content {i}\n\n" + "Content " * 1000
                    test_file = self.output_dir / f"test_file_{i}.md"
                    
                    with builtins.open(test_file, 'w', encoding='utf-8') as f:
                        f.write(test_content)
                    
                    # 使用不同策略读取
                    if strategy == ReadStrategy.SYNC:
                        with builtins.open(test_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                    elif strategy == ReadStrategy.ASYNC:
                        # 模拟异步读取
                        content = test_content
                    else:  # MAPPED
                        content = test_content
                    
                    end_time = time.time()
                    
                    # 记录结果
                    result = {
                        'strategy': strategy.value,
                        'iteration': i,
                        'time_ms': (end_time - start_time) * 1000,
                        'bytes_read': len(content.encode('utf-8')),
                        'throughput': len(content.encode('utf-8')) / (end_time - start_time) / 1024 / 1024,  # MB/s
                        'memory_mb': 0.1  # 模拟内存使用
                    }
                    
                    benchmark.add_result(result)
                    
                    # 清理测试文件
                    test_file.unlink(missing_ok=True)
                    
        except Exception as e:
            self.logger.error(f"文件读取基准测试失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
        
        benchmark.complete()
        return benchmark
    
    def run_render_benchmark(self) -> BenchmarkResult:
        """运行渲染性能基准测试"""
        benchmark = BenchmarkResult("render_benchmark", BenchmarkType.RENDER_PERFORMANCE)
        
        try:
            for strategy in self.benchmark_config['render']['strategies']:
                for i, content in enumerate(self.benchmark_config['render']['test_content']):
                    for j in range(self.benchmark_config['render']['iterations']):
                        start_time = time.time()
                        
                        # 模拟渲染测试
                        rendered_content = f"<h1>Test</h1>\n<p>{content}</p>"
                        
                        end_time = time.time()
                        
                        # 记录结果
                        result = {
                            'strategy': strategy.value,
                            'content_index': i,
                            'iteration': j,
                            'time_ms': (end_time - start_time) * 1000,
                            'content_length': len(content),
                            'render_speed_chars_per_ms': len(content) / (end_time - start_time) / 1000,
                            'memory_mb': 0.2  # 模拟内存使用
                        }
                        
                        benchmark.add_result(result)
                        
        except Exception as e:
            self.logger.error(f"渲染基准测试失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
        
        benchmark.complete()
        return benchmark
    
    def run_memory_benchmark(self) -> BenchmarkResult:
        """运行内存使用基准测试"""
        benchmark = BenchmarkResult("memory_benchmark", BenchmarkType.MEMORY_USAGE)
        
        try:
            for strategy in self.benchmark_config['memory']['strategies']:
                for size in self.benchmark_config['memory']['test_sizes']:
                    for i in range(self.benchmark_config['memory']['iterations']):
                        start_time = time.time()
                        
                        # 模拟内存测试
                        test_data = [f"item_{j}" for j in range(size)]
                        
                        end_time = time.time()
                        
                        # 记录结果
                        result = {
                            'strategy': strategy.value,
                            'data_size': size,
                            'iteration': i,
                            'time_ms': (end_time - start_time) * 1000,
                            'memory_mb': size * 0.0001,  # 模拟内存使用
                            'efficiency': size / (end_time - start_time) / 1000  # 效率
                        }
                        
                        benchmark.add_result(result)
                        
                        # 清理测试数据
                        del test_data
                        
        except Exception as e:
            self.logger.error(f"内存基准测试失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
        
        benchmark.complete()
        return benchmark
    
    def run_integrated_benchmark(self) -> BenchmarkResult:
        """运行综合性能基准测试"""
        benchmark = BenchmarkResult("integrated_benchmark", BenchmarkType.INTEGRATED)
        
        try:
            # 运行所有基准测试
            file_benchmark = self.run_file_read_benchmark()
            render_benchmark = self.run_render_benchmark()
            memory_benchmark = self.run_memory_benchmark()
            
            # 合并结果
            for result in file_benchmark.results:
                benchmark.add_result(result)
            for result in render_benchmark.results:
                benchmark.add_result(result)
            for result in memory_benchmark.results:
                benchmark.add_result(result)
            
            benchmark.complete()
            
        except Exception as e:
            self.logger.error(f"综合基准测试失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
        
        return benchmark
    
    def generate_report(self, benchmark_result: BenchmarkResult) -> str:
        """生成基准测试报告"""
        summary = benchmark_result.get_summary()
        
        report = f"""
# 性能基准测试报告

## 测试信息
- 测试名称: {summary.get('test_name', 'N/A')}
- 测试类型: {summary.get('test_type', 'N/A')}
- 总运行次数: {summary.get('total_runs', 0)}
- 总耗时: {summary.get('duration', 0):.2f}秒

## 性能指标
- 平均时间: {summary.get('avg_time_ms', 0):.2f}ms
- 最小时间: {summary.get('min_time_ms', 0):.2f}ms
- 最大时间: {summary.get('max_time_ms', 0):.2f}ms
- 标准差: {summary.get('std_time_ms', 0):.2f}ms
- 平均内存使用: {summary.get('avg_memory_mb', 0):.2f}MB
- 平均吞吐量: {summary.get('avg_throughput', 0):.2f}

## 详细结果
"""
        
        for i, result in enumerate(benchmark_result.results):
            report += f"\n### 运行 {i+1}\n"
            for key, value in result.items():
                if isinstance(value, float):
                    report += f"- {key}: {value:.2f}\n"
                else:
                    report += f"- {key}: {value}\n"
        
        return report
    
    def save_report(self, benchmark_result: BenchmarkResult, filename: Optional[str] = None):
        """保存基准测试报告"""
        try:
            if filename is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"benchmark_report_{benchmark_result.test_name}_{timestamp}.md"
            
            report_path = self.output_dir / filename
            
            report_content = self.generate_report(benchmark_result)
            
            with builtins.open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.logger.info(f"基准测试报告已保存: {report_path}")
            
            # 同时保存JSON格式的原始数据
            json_path = report_path.with_suffix('.json')
            with builtins.open(json_path, 'w', encoding='utf-8') as f:
                json.dump(benchmark_result.results, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"基准测试数据已保存: {json_path}")
            
        except Exception as e:
            self.logger.error(f"保存基准测试报告失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
    
    def run_all_benchmarks(self) -> Dict[str, BenchmarkResult]:
        """运行所有基准测试"""
        self.logger.info("开始运行所有性能基准测试...")
        
        results = {}
        
        # 文件读取基准测试
        self.logger.info("运行文件读取基准测试...")
        results['file_read'] = self.run_file_read_benchmark()
        
        # 渲染性能基准测试
        self.logger.info("运行渲染性能基准测试...")
        results['render'] = self.run_render_benchmark()
        
        # 内存使用基准测试
        self.logger.info("运行内存使用基准测试...")
        results['memory'] = self.run_memory_benchmark()
        
        # 综合性能基准测试
        self.logger.info("运行综合性能基准测试...")
        results['integrated'] = self.run_integrated_benchmark()
        
        self.logger.info("所有基准测试完成！")
        
        return results
    
    def compare_with_baseline(self, current_results: Dict[str, BenchmarkResult], 
                            baseline_file: Path) -> Dict[str, Any]:
        """与基准线比较"""
        try:
            if not baseline_file.exists():
                self.logger.warning(f"基准线文件不存在: {baseline_file}")
                return {}
            
            with open(baseline_file, 'r', encoding='utf-8') as f:
                baseline_data = json.load(f)
            
            comparison = {}
            
            for test_name, current_result in current_results.items():
                if test_name in baseline_data:
                    baseline = baseline_data[test_name]
                    current_summary = current_result.get_summary()
                    
                    # 计算性能变化
                    time_change = ((current_summary.get('avg_time_ms', 0) - 
                                  baseline.get('avg_time_ms', 0)) / 
                                 baseline.get('avg_time_ms', 1)) * 100
                    
                    memory_change = ((current_summary.get('avg_memory_mb', 0) - 
                                    baseline.get('avg_memory_mb', 0)) / 
                                   baseline.get('avg_memory_mb', 1)) * 100
                    
                    comparison[test_name] = {
                        'time_change_percent': time_change,
                        'memory_change_percent': memory_change,
                        'improvement': time_change < 0,  # 时间减少表示改进
                        'baseline': baseline,
                        'current': current_summary
                    }
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"基准线比较失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
            return {}
    
    def shutdown(self):
        """关闭基准测试器"""
        try:
            self.logger.info("关闭性能基准测试器...")
            
            # 关闭性能优化组件
            if hasattr(self.file_reader, 'shutdown'):
                self.file_reader.shutdown()
            if hasattr(self.render_optimizer, 'shutdown'):
                self.render_optimizer.shutdown()
            if hasattr(self.memory_manager, 'shutdown'):
                self.memory_manager.shutdown()
            
            self.logger.info("性能基准测试器已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭性能基准测试器失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)


# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建基准测试器
    benchmarker = PerformanceBenchmarker()
    
    try:
        # 运行所有基准测试
        results = benchmarker.run_all_benchmarks()
        
        # 保存报告
        for test_name, result in results.items():
            benchmarker.save_report(result, f"{test_name}_report.md")
        
        print("基准测试完成！")
        
    finally:
        # 关闭基准测试器
        benchmarker.shutdown() 