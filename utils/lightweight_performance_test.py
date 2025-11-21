#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量级性能测试框架 v1.0.0
基于现有测试框架实现性能基准测试，提供性能指标收集和分析功能

作者: LAD Team
创建时间: 2025-08-16
最后更新: 2025-08-16
"""

import json
import time
import psutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import builtins

@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    execution_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success: bool
    error_message: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


class LightweightPerformanceTest:
    """轻量级性能测试框架"""
    
    def __init__(self, test_data_dir: Path, benchmark_dir: Path = None):
        """
        初始化性能测试框架
        
        Args:
            test_data_dir: 测试数据目录
            benchmark_dir: 基准结果目录，默认为test_data_dir下的benchmarks
        """
        self.test_data_dir = Path(test_data_dir)
        if benchmark_dir is None:
            self.benchmark_dir = self.test_data_dir / "benchmarks"
        else:
            self.benchmark_dir = Path(benchmark_dir)
        
        # 确保目录存在
        self.benchmark_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 性能基准文件
        self.baseline_file = self.benchmark_dir / "performance_baseline.json"
        self.results_file = self.benchmark_dir / "performance_results.json"
        
        # 测试结果缓存
        self.current_results = {}
        self.baseline_data = {}
        
        # 加载现有基准数据
        self._load_baseline_data()
    
    def create_test_files(self) -> Dict[str, Path]:
        """
        创建标准性能测试文件
        
        Returns:
            测试文件字典，包含小、中、大、超大文件
        """
        test_files = {}
        
        # 小文件：< 1KB
        small_file = self.test_data_dir / "small.md"
        if not small_file.exists():
            small_content = self._generate_markdown_content(0.5)  # 0.5KB
            small_file.write_text(small_content, encoding='utf-8')
        test_files['small'] = small_file
        
        # 中文件：1-10KB
        medium_file = self.test_data_dir / "medium.md"
        if not medium_file.exists():
            medium_content = self._generate_markdown_content(5)  # 5KB
            medium_file.write_text(medium_content, encoding='utf-8')
        test_files['medium'] = medium_file
        
        # 大文件：10-100KB
        large_file = self.test_data_dir / "large.md"
        if not large_file.exists():
            large_content = self._generate_markdown_content(50)  # 50KB
            large_file.write_text(large_content, encoding='utf-8')
        test_files['large'] = large_file
        
        # 超大文件：> 100KB
        huge_file = self.test_data_dir / "huge.md"
        if not huge_file.exists():
            huge_content = self._generate_markdown_content(200)  # 200KB
            huge_file.write_text(huge_content, encoding='utf-8')
        test_files['huge'] = huge_file
        
        self.logger.info(f"创建了 {len(test_files)} 个测试文件")
        return test_files
    
    def _generate_markdown_content(self, target_size_kb: float) -> str:
        """
        生成指定大小的Markdown测试内容
        
        Args:
            target_size_kb: 目标大小（KB）
            
        Returns:
            Markdown内容字符串
        """
        target_size = int(target_size_kb * 1024)
        
        # 基础Markdown模板
        base_content = """# 性能测试文档

## 概述
这是一个用于性能测试的Markdown文档，包含各种Markdown元素。

## 章节列表
"""
        
        # 计算需要添加的内容
        remaining_size = target_size - len(base_content.encode('utf-8'))
        if remaining_size <= 0:
            return base_content
        
        # 生成章节内容
        chapter_template = """
### 章节 {chapter_num}

这是一个测试章节，包含以下内容：

- **列表项1**: 这是第一个列表项的描述
- **列表项2**: 这是第二个列表项的描述
- **列表项3**: 这是第三个列表项的描述

#### 子章节 {chapter_num}.1

这里是一些示例文本，用于填充文档内容。Markdown渲染器需要处理这些内容，包括：

1. 标题层级
2. 列表格式
3. 粗体和斜体
4. 代码块
5. 链接和图片

```python
# 示例代码块
def example_function():
    print("这是一个示例函数")
    return True
```

> 这是一个引用块，用于测试引用格式的渲染性能。

---

"""
        
        chapters_needed = max(1, remaining_size // len(chapter_template.encode('utf-8')))
        content = base_content
        
        for i in range(chapters_needed):
            chapter_content = chapter_template.format(
                chapter_num=i + 1
            )
            content += chapter_content
        
        # 如果内容仍然不够，添加更多文本
        while len(content.encode('utf-8')) < target_size:
            content += "这是额外的填充文本，用于达到目标文件大小。"
        
        return content
    
    def run_benchmark(self, test_func: Callable, test_file: Path, 
                      test_name: str = None) -> PerformanceMetrics:
        """
        运行性能基准测试
        
        Args:
            test_func: 要测试的函数
            test_file: 测试文件路径
            test_name: 测试名称，默认为文件名
            
        Returns:
            性能指标对象
        """
        if test_name is None:
            test_name = test_file.name
        
        self.logger.info(f"开始性能测试: {test_name}")
        
        # 获取进程信息
        process = psutil.Process()
        
        # 记录初始状态
        start_memory = process.memory_info().rss
        start_cpu = process.cpu_percent()
        start_time = time.time()
        
        try:
            # 执行测试函数
            result = test_func(test_file)
            success = result is not None
            error_message = None if success else "函数返回None"
            
        except Exception as e:
            success = False
            error_message = str(e)
            self.logger.error(f"测试执行失败: {e}")
        
        # 记录结束状态
        end_time = time.time()
        end_memory = process.memory_info().rss
        end_cpu = process.cpu_percent()
        
        # 计算性能指标
        execution_time_ms = (end_time - start_time) * 1000
        memory_usage_mb = (end_memory - start_memory) / 1024 / 1024
        cpu_usage_percent = (start_cpu + end_cpu) / 2  # 平均CPU使用率
        
        # 创建性能指标对象
        metrics = PerformanceMetrics(
            execution_time_ms=execution_time_ms,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent,
            success=success,
            error_message=error_message
        )
        
        # 保存结果
        self.current_results[test_name] = metrics
        
        self.logger.info(f"测试完成: {test_name}, 耗时: {execution_time_ms:.2f}ms, "
                        f"内存: {memory_usage_mb:.2f}MB")
        
        return metrics
    
    def run_comprehensive_benchmark(self, test_func: Callable) -> Dict[str, PerformanceMetrics]:
        """
        运行全面的性能基准测试
        
        Args:
            test_func: 要测试的函数
            
        Returns:
            所有测试结果字典
        """
        self.logger.info("开始全面性能基准测试")
        
        # 创建测试文件
        test_files = self.create_test_files()
        
        # 运行所有测试
        for test_type, test_file in test_files.items():
            self.run_benchmark(test_func, test_file, test_type)
        
        # 保存当前结果
        self._save_current_results()
        
        self.logger.info(f"全面性能测试完成，共测试 {len(self.current_results)} 个场景")
        return self.current_results
    
    def save_baseline(self, results: Dict[str, PerformanceMetrics] = None):
        """
        保存性能基准数据
        
        Args:
            results: 要保存的结果，默认为当前结果
        """
        if results is None:
            results = self.current_results
        
        baseline_data = {
            'timestamp': datetime.now().isoformat(),
            'description': '性能基准数据',
            'results': {}
        }
        
        for test_name, metrics in results.items():
            baseline_data['results'][test_name] = metrics.to_dict()
        
        # 保存到文件
        with builtins.open(self.baseline_file, 'w', encoding='utf-8') as f:
            json.dump(baseline_data, f, indent=2, ensure_ascii=False)
        
        # 更新内存中的基准数据
        self.baseline_data = baseline_data
        
        self.logger.info(f"性能基准数据已保存到: {self.baseline_file}")
    
    def compare_with_baseline(self, current_results: Dict[str, PerformanceMetrics] = None) -> Dict[str, Any]:
        """
        与基准数据比较
        
        Args:
            current_results: 当前测试结果，默认为当前结果
            
        Returns:
            比较结果字典
        """
        if current_results is None:
            current_results = self.current_results
        
        if not self.baseline_data:
            return {
                'status': 'no_baseline',
                'message': '没有可用的基准数据',
                'suggestions': ['运行save_baseline()创建基准数据']
            }
        
        comparison = {
            'status': 'comparison_complete',
            'timestamp': datetime.now().isoformat(),
            'baseline_timestamp': self.baseline_data.get('timestamp'),
            'results': {}
        }
        
        baseline_results = self.baseline_data.get('results', {})
        
        for test_name, current_metrics in current_results.items():
            if test_name in baseline_results:
                baseline_metrics = baseline_results[test_name]
                
                # 计算变化百分比
                time_change = self._calculate_change_percent(
                    baseline_metrics['execution_time_ms'],
                    current_metrics.execution_time_ms
                )
                
                memory_change = self._calculate_change_percent(
                    baseline_metrics['memory_usage_mb'],
                    current_metrics.memory_usage_mb
                )
                
                comparison['results'][test_name] = {
                    'execution_time': {
                        'baseline': baseline_metrics['execution_time_ms'],
                        'current': current_metrics.execution_time_ms,
                        'change_percent': time_change,
                        'status': self._get_change_status(time_change)
                    },
                    'memory_usage': {
                        'baseline': baseline_metrics['memory_usage_mb'],
                        'current': current_metrics.memory_usage_mb,
                        'change_percent': memory_change,
                        'status': self._get_change_status(memory_change)
                    },
                    'success': current_metrics.success
                }
            else:
                comparison['results'][test_name] = {
                    'status': 'no_baseline',
                    'message': f'测试 {test_name} 没有对应的基准数据'
                }
        
        return comparison
    
    def _calculate_change_percent(self, baseline: float, current: float) -> float:
        """计算变化百分比"""
        if baseline == 0:
            return 0.0
        return ((current - baseline) / baseline) * 100
    
    def _get_change_status(self, change_percent: float) -> str:
        """获取变化状态"""
        if change_percent <= -10:
            return 'improved'  # 性能改善
        elif change_percent <= 10:
            return 'stable'    # 性能稳定
        elif change_percent <= 50:
            return 'degraded'  # 性能下降
        else:
            return 'critical'  # 性能严重下降
    
    def generate_performance_report(self, comparison: Dict[str, Any] = None) -> str:
        """
        生成性能报告
        
        Args:
            comparison: 比较结果，默认为当前结果与基准的比较
            
        Returns:
            格式化的性能报告
        """
        if comparison is None:
            comparison = self.compare_with_baseline()
        
        report = []
        report.append("# 性能测试报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        if comparison['status'] == 'no_baseline':
            report.append("## 状态")
            report.append(comparison['message'])
            report.append("")
            report.append("## 建议")
            for suggestion in comparison.get('suggestions', []):
                report.append(f"- {suggestion}")
            return "\n".join(report)
        
        report.append("## 测试概览")
        report.append(f"- 基准时间: {comparison['baseline_timestamp']}")
        report.append(f"- 测试时间: {comparison['timestamp']}")
        report.append("")
        
        report.append("## 详细结果")
        for test_name, result in comparison['results'].items():
            if result.get('status') == 'no_baseline':
                report.append(f"### {test_name}")
                report.append(f"- 状态: {result['message']}")
                report.append("")
                continue
            
            report.append(f"### {test_name}")
            
            # 执行时间
            time_info = result['execution_time']
            report.append(f"- **执行时间**:")
            report.append(f"  - 基准: {time_info['baseline']:.2f}ms")
            report.append(f"  - 当前: {time_info['current']:.2f}ms")
            report.append(f"  - 变化: {time_info['change_percent']:+.2f}% ({time_info['status']})")
            
            # 内存使用
            memory_info = result['memory_usage']
            report.append(f"- **内存使用**:")
            report.append(f"  - 基准: {memory_info['baseline']:.2f}MB")
            report.append(f"  - 当前: {memory_info['current']:.2f}MB")
            report.append(f"  - 变化: {memory_info['change_percent']:+.2f}% ({memory_info['status']})")
            
            # 成功状态
            report.append(f"- **测试状态**: {'✅ 成功' if result['success'] else '❌ 失败'}")
            report.append("")
        
        return "\n".join(report)
    
    def _load_baseline_data(self):
        """加载现有基准数据"""
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, 'r', encoding='utf-8') as f:
                    self.baseline_data = json.load(f)
                self.logger.info(f"已加载基准数据: {self.baseline_file}")
            except Exception as e:
                self.logger.warning(f"加载基准数据失败: {e}")
                self.baseline_data = {}
        else:
            self.logger.info("未找到基准数据文件，将创建新的基准")
    
    def _save_current_results(self):
        """保存当前测试结果"""
        results_data = {
            'timestamp': datetime.now().isoformat(),
            'description': '当前性能测试结果',
            'results': {}
        }
        
        for test_name, metrics in self.current_results.items():
            results_data['results'][test_name] = metrics.to_dict()
        
        with builtins.open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"测试结果已保存到: {self.results_file}")
    
    def get_test_summary(self) -> Dict[str, Any]:
        """获取测试摘要"""
        return {
            'total_tests': len(self.current_results),
            'successful_tests': sum(1 for m in self.current_results.values() if m.success),
            'failed_tests': sum(1 for m in self.current_results.values() if not m.success),
            'total_execution_time': sum(m.execution_time_ms for m in self.current_results.values()),
            'total_memory_usage': sum(m.memory_usage_mb for m in self.current_results.values()),
            'has_baseline': bool(self.baseline_data),
            'baseline_file': str(self.baseline_file),
            'results_file': str(self.results_file)
        }


# 便捷函数
def create_performance_test(test_data_dir: Union[str, Path]) -> LightweightPerformanceTest:
    """创建性能测试实例的便捷函数"""
    return LightweightPerformanceTest(Path(test_data_dir))


def run_quick_benchmark(test_func: Callable, test_data_dir: Union[str, Path]) -> Dict[str, Any]:
    """快速运行性能基准测试的便捷函数"""
    perf_test = create_performance_test(test_data_dir)
    results = perf_test.run_comprehensive_benchmark(test_func)
    comparison = perf_test.compare_with_baseline(results)
    report = perf_test.generate_performance_report(comparison)
    
    return {
        'results': results,
        'comparison': comparison,
        'report': report,
        'summary': perf_test.get_test_summary()
    } 