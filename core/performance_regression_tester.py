#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能回归测试器 v1.0.0
检测性能回归，提供性能趋势分析和回归预警功能

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
import numpy as np
from collections import deque, defaultdict
import builtins

# 导入性能优化组件
from .performance_benchmarker import PerformanceBenchmarker, BenchmarkResult, BenchmarkType
from .performance_monitor import PerformanceMonitor, PerformanceMetric, MetricType
from .enhanced_error_handler import EnhancedErrorHandler, ErrorRecoveryStrategy


class RegressionType(Enum):
    """回归类型枚举"""
    PERFORMANCE_DEGRADATION = "performance_degradation"  # 性能下降
    MEMORY_LEAK = "memory_leak"                         # 内存泄漏
    CACHE_EFFICIENCY_DROP = "cache_efficiency_drop"     # 缓存效率下降
    RENDER_SPEED_DROP = "render_speed_drop"             # 渲染速度下降
    FILE_READ_SLOWDOWN = "file_read_slowdown"           # 文件读取变慢


class TrendDirection(Enum):
    """趋势方向枚举"""
    IMPROVING = "improving"      # 改善
    STABLE = "stable"            # 稳定
    DEGRADING = "degrading"      # 下降
    FLUCTUATING = "fluctuating"  # 波动


@dataclass
class RegressionAlert:
    """回归告警数据类"""
    regression_type: RegressionType
    severity: str
    message: str
    current_value: float
    baseline_value: float
    degradation_percent: float
    trend_data: List[float]
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['regression_type'] = self.regression_type.value
        return data


@dataclass
class TrendAnalysis:
    """趋势分析数据类"""
    metric_type: MetricType
    direction: TrendDirection
    slope: float
    r_squared: float
    confidence: float
    data_points: int
    trend_data: List[float]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['metric_type'] = self.metric_type.value
        data['direction'] = self.direction.value
        return data


class PerformanceRegressionTester:
    """性能回归测试器"""
    
    def __init__(self, baseline_file: Optional[Path] = None, 
                 regression_thresholds: Optional[Dict] = None):
        """
        初始化性能回归测试器
        
        Args:
            baseline_file: 基准线文件路径
            regression_thresholds: 回归检测阈值
        """
        self.logger = logging.getLogger(__name__)
        
        # 基准线配置
        self.baseline_file = baseline_file
        self.baseline_data: Dict[str, Any] = {}
        
        # 回归检测阈值
        self.regression_thresholds = regression_thresholds or {
            'performance_degradation': 0.15,      # 15%性能下降
            'memory_leak': 0.20,                  # 20%内存增长
            'cache_efficiency_drop': 0.10,        # 10%缓存效率下降
            'render_speed_drop': 0.15,            # 15%渲染速度下降
            'file_read_slowdown': 0.20            # 20%文件读取变慢
        }
        
        # 性能组件
        self.benchmarker = PerformanceBenchmarker()
        self.monitor = PerformanceMonitor()
        self.error_handler = EnhancedErrorHandler()
        
        # 回归检测结果
        self.regression_alerts: List[RegressionAlert] = []
        self.trend_analyses: Dict[MetricType, TrendAnalysis] = {}
        
        # 历史数据存储
        self.performance_history: Dict[MetricType, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # 统计信息
        self.regression_stats = {
            'total_regressions_detected': 0,
            'last_regression_check': 0,
            'regression_check_count': 0,
            'baseline_established': False
        }
        
        # 加载基准线数据
        if self.baseline_file and self.baseline_file.exists():
            self._load_baseline()
    
    def _load_baseline(self):
        """加载基准线数据"""
        try:
            with open(self.baseline_file, 'r', encoding='utf-8') as f:
                self.baseline_data = json.load(f)
            
            self.regression_stats['baseline_established'] = True
            self.logger.info(f"基准线数据已加载: {self.baseline_file}")
            
        except Exception as e:
            self.logger.error(f"加载基准线数据失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
    
    def establish_baseline(self, output_file: Optional[Path] = None):
        """建立性能基准线"""
        try:
            self.logger.info("开始建立性能基准线...")
            
            # 运行基准测试
            benchmark_results = self.benchmarker.run_all_benchmarks()
            
            # 收集性能监控数据
            self.monitor.start_monitoring()
            time.sleep(10)  # 收集10秒的数据
            self.monitor.stop_monitoring()
            
            # 获取性能摘要
            performance_summary = self.monitor.get_performance_summary()
            
            # 构建基准线数据
            baseline_data = {
                'establishment_time': time.time(),
                'benchmark_results': {
                    name: result.get_summary() for name, result in benchmark_results.items()
                },
                'performance_metrics': performance_summary,
                'system_info': self._collect_system_info()
            }
            
            # 保存基准线数据
            if output_file is None:
                output_file = Path(__file__).parent.parent / "outputs" / "baseline" / "performance_baseline.json"
                output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with builtins.open(output_file, 'w', encoding='utf-8') as f:
                json.dump(baseline_data, f, indent=2, ensure_ascii=False)
            
            # 更新基准线文件路径和数据
            self.baseline_file = output_file
            self.baseline_data = baseline_data
            self.regression_stats['baseline_established'] = True
            
            self.logger.info(f"性能基准线已建立: {output_file}")
            
            return baseline_data
            
        except Exception as e:
            self.logger.error(f"建立性能基准线失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
            return None
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """收集系统信息"""
        try:
            import psutil
            
            system_info = {
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / 1024 / 1024 / 1024,
                'platform': os.name,
                'python_version': os.sys.version,
                'timestamp': time.time()
            }
            
            return system_info
            
        except Exception as e:
            self.logger.error(f"收集系统信息失败: {e}")
            return {}
    
    def detect_regressions(self) -> List[RegressionAlert]:
        """检测性能回归"""
        try:
            self.logger.info("开始检测性能回归...")
            
            if not self.regression_stats['baseline_established']:
                self.logger.warning("基准线未建立，无法检测回归")
                return []
            
            # 运行基准测试
            current_benchmark_results = self.benchmarker.run_all_benchmarks()
            
            # 收集当前性能指标
            self.monitor.start_monitoring()
            time.sleep(5)  # 收集5秒的数据
            self.monitor.stop_monitoring()
            
            current_metrics = self.monitor.get_current_metrics()
            
            # 检测各种类型的回归
            regressions = []
            
            # 检测性能下降
            performance_regression = self._detect_performance_degradation(
                current_benchmark_results, current_metrics
            )
            if performance_regression:
                regressions.extend(performance_regression)
            
            # 检测内存泄漏
            memory_regression = self._detect_memory_leak(current_metrics)
            if memory_regression:
                regressions.append(memory_regression)
            
            # 检测缓存效率下降
            cache_regression = self._detect_cache_efficiency_drop(current_metrics)
            if cache_regression:
                regressions.append(cache_regression)
            
            # 检测渲染速度下降
            render_regression = self._detect_render_speed_drop(current_metrics)
            if render_regression:
                regressions.append(render_regression)
            
            # 检测文件读取变慢
            file_read_regression = self._detect_file_read_slowdown(current_metrics)
            if file_read_regression:
                regressions.append(file_read_regression)
            
            # 更新回归统计
            self.regression_stats['total_regressions_detected'] += len(regressions)
            self.regression_stats['last_regression_check'] = time.time()
            self.regression_stats['regression_check_count'] += 1
            
            # 存储回归告警
            self.regression_alerts.extend(regressions)
            
            self.logger.info(f"回归检测完成，发现 {len(regressions)} 个回归问题")
            
            return regressions
            
        except Exception as e:
            self.logger.error(f"检测性能回归失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
            return []
    
    def _detect_performance_degradation(self, current_benchmarks: Dict[str, BenchmarkResult], 
                                      current_metrics: Dict) -> List[RegressionAlert]:
        """检测性能下降"""
        regressions = []
        
        try:
            baseline_benchmarks = self.baseline_data.get('benchmark_results', {})
            
            for test_name, current_result in current_benchmarks.items():
                if test_name in baseline_benchmarks:
                    baseline = baseline_benchmarks[test_name]
                    current_summary = current_result.get_summary()
                    
                    # 比较平均时间
                    baseline_time = baseline.get('avg_time_ms', 0)
                    current_time = current_summary.get('avg_time_ms', 0)
                    
                    if baseline_time > 0 and current_time > 0:
                        degradation = (current_time - baseline_time) / baseline_time
                        
                        if degradation > self.regression_thresholds['performance_degradation']:
                            alert = RegressionAlert(
                                regression_type=RegressionType.PERFORMANCE_DEGRADATION,
                                severity='warning' if degradation < 0.3 else 'error',
                                message=f"{test_name} 性能下降 {degradation*100:.1f}%",
                                current_value=current_time,
                                baseline_value=baseline_time,
                                degradation_percent=degradation * 100,
                                trend_data=[baseline_time, current_time],
                                timestamp=time.time()
                            )
                            regressions.append(alert)
            
        except Exception as e:
            self.logger.error(f"检测性能下降失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
        
        return regressions
    
    def _detect_memory_leak(self, current_metrics: Dict) -> Optional[RegressionAlert]:
        """检测内存泄漏"""
        try:
            # 这里需要实现内存泄漏检测逻辑
            # 可以通过监控内存使用趋势来判断
            return None
            
        except Exception as e:
            self.logger.error(f"检测内存泄漏失败: {e}")
            return None
    
    def _detect_cache_efficiency_drop(self, current_metrics: Dict) -> Optional[RegressionAlert]:
        """检测缓存效率下降"""
        try:
            baseline_metrics = self.baseline_data.get('performance_metrics', {})
            baseline_cache = baseline_metrics.get('current_metrics', {}).get('cache', {})
            current_cache = current_metrics.get('cache', {})
            
            if baseline_cache and current_cache:
                baseline_hit_rate = baseline_cache.get('value', 1.0)
                current_hit_rate = current_cache.get('value', 1.0)
                
                if baseline_hit_rate > 0 and current_hit_rate > 0:
                    drop = (baseline_hit_rate - current_hit_rate) / baseline_hit_rate
                    
                    if drop > self.regression_thresholds['cache_efficiency_drop']:
                        return RegressionAlert(
                            regression_type=RegressionType.CACHE_EFFICIENCY_DROP,
                            severity='warning',
                            message=f"缓存效率下降 {drop*100:.1f}%",
                            current_value=current_hit_rate,
                            baseline_value=baseline_hit_rate,
                            degradation_percent=drop * 100,
                            trend_data=[baseline_hit_rate, current_hit_rate],
                            timestamp=time.time()
                        )
            
            return None
            
        except Exception as e:
            self.logger.error(f"检测缓存效率下降失败: {e}")
            return None
    
    def _detect_render_speed_drop(self, current_metrics: Dict) -> Optional[RegressionAlert]:
        """检测渲染速度下降"""
        try:
            baseline_metrics = self.baseline_data.get('performance_metrics', {})
            baseline_render = baseline_metrics.get('current_metrics', {}).get('render', {})
            current_render = current_metrics.get('render', {})
            
            if baseline_render and current_render:
                baseline_speed = baseline_render.get('value', 100.0)
                current_speed = current_render.get('value', 100.0)
                
                if baseline_speed > 0 and current_speed > 0:
                    drop = (baseline_speed - current_speed) / baseline_speed
                    
                    if drop > self.regression_thresholds['render_speed_drop']:
                        return RegressionAlert(
                            regression_type=RegressionType.RENDER_SPEED_DROP,
                            severity='warning',
                            message=f"渲染速度下降 {drop*100:.1f}%",
                            current_value=current_speed,
                            baseline_value=baseline_speed,
                            degradation_percent=drop * 100,
                            trend_data=[baseline_speed, current_speed],
                            timestamp=time.time()
                        )
            
            return None
            
        except Exception as e:
            self.logger.error(f"检测渲染速度下降失败: {e}")
            return None
    
    def _detect_file_read_slowdown(self, current_metrics: Dict) -> Optional[RegressionAlert]:
        """检测文件读取变慢"""
        try:
            baseline_metrics = self.baseline_data.get('performance_metrics', {})
            baseline_file_read = baseline_metrics.get('current_metrics', {}).get('file_read', {})
            current_file_read = current_metrics.get('file_read', {})
            
            if baseline_file_read and current_file_read:
                baseline_speed = baseline_file_read.get('value', 100.0)
                current_speed = current_file_read.get('value', 100.0)
                
                if baseline_speed > 0 and current_speed > 0:
                    slowdown = (baseline_speed - current_speed) / baseline_speed
                    
                    if slowdown > self.regression_thresholds['file_read_slowdown']:
                        return RegressionAlert(
                            regression_type=RegressionType.FILE_READ_SLOWDOWN,
                            severity='warning',
                            message=f"文件读取速度下降 {slowdown*100:.1f}%",
                            current_value=current_speed,
                            baseline_value=baseline_speed,
                            degradation_percent=slowdown * 100,
                            trend_data=[baseline_speed, current_speed],
                            timestamp=time.time()
                        )
            
            return None
            
        except Exception as e:
            self.logger.error(f"检测文件读取变慢失败: {e}")
            return None
    
    def analyze_trends(self, metric_type: MetricType, data_points: int = 50) -> TrendAnalysis:
        """分析性能趋势"""
        try:
            # 获取历史数据
            history = self.monitor.get_metric_history(metric_type, data_points)
            
            if len(history) < 3:
                return None
            
            # 提取数值和时间
            values = [m.value for m in history]
            timestamps = [m.timestamp for m in history]
            
            # 计算趋势斜率
            x = np.array(timestamps)
            y = np.array(values)
            
            # 线性回归
            slope, intercept = np.polyfit(x, y, 1)
            
            # 计算R²值
            y_pred = slope * x + intercept
            r_squared = 1 - np.sum((y - y_pred) ** 2) / np.sum((y - np.mean(y)) ** 2)
            
            # 确定趋势方向
            if abs(slope) < 0.001:
                direction = TrendDirection.STABLE
            elif slope > 0:
                direction = TrendDirection.DEGRADING
            else:
                direction = TrendDirection.IMPROVING
            
            # 计算置信度
            confidence = min(abs(r_squared), 1.0)
            
            # 创建趋势分析结果
            trend_analysis = TrendAnalysis(
                metric_type=metric_type,
                direction=direction,
                slope=slope,
                r_squared=r_squared,
                confidence=confidence,
                data_points=len(history),
                trend_data=values
            )
            
            # 存储趋势分析结果
            self.trend_analyses[metric_type] = trend_analysis
            
            return trend_analysis
            
        except Exception as e:
            self.logger.error(f"分析性能趋势失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
            return None
    
    def generate_regression_report(self) -> str:
        """生成回归检测报告"""
        try:
            report = f"""
# 性能回归检测报告

## 检测信息
- 检测时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
- 基准线状态: {'已建立' if self.regression_stats['baseline_established'] else '未建立'}
- 总检测次数: {self.regression_stats['regression_check_count']}
- 总回归数量: {self.regression_stats['total_regressions_detected']}

## 回归检测结果
"""
            
            if self.regression_alerts:
                for i, alert in enumerate(self.regression_alerts[-10:], 1):  # 最近10个
                    report += f"""
### 回归 {i}
- 类型: {alert.regression_type.value}
- 严重程度: {alert.severity}
- 消息: {alert.message}
- 当前值: {alert.current_value:.2f}
- 基准值: {alert.baseline_value:.2f}
- 下降百分比: {alert.degradation_percent:.1f}%
- 检测时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert.timestamp))}
"""
            else:
                report += "\n**未检测到性能回归**\n"
            
            # 添加趋势分析
            if self.trend_analyses:
                report += "\n## 性能趋势分析\n"
                for metric_type, analysis in self.trend_analyses.items():
                    report += f"""
### {metric_type.value}
- 趋势方向: {analysis.direction.value}
- 斜率: {analysis.slope:.6f}
- R²值: {analysis.r_squared:.4f}
- 置信度: {analysis.confidence:.2f}
- 数据点数量: {analysis.data_points}
"""
            
            return report
            
        except Exception as e:
            self.logger.error(f"生成回归检测报告失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
            return "报告生成失败"
    
    def save_regression_report(self, filename: Optional[str] = None):
        """保存回归检测报告"""
        try:
            if filename is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"regression_report_{timestamp}.md"
            
            report_path = Path(__file__).parent.parent / "outputs" / "regression" / filename
            report_path.parent.mkdir(parents=True, exist_ok=True)
            
            report_content = self.generate_regression_report()
            
            with builtins.open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.logger.info(f"回归检测报告已保存: {report_path}")
            
        except Exception as e:
            self.logger.error(f"保存回归检测报告失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
    
    def get_regression_summary(self) -> Dict[str, Any]:
        """获取回归检测摘要"""
        try:
            summary = {
                'baseline_established': self.regression_stats['baseline_established'],
                'total_regressions_detected': self.regression_stats['total_regressions_detected'],
                'last_regression_check': self.regression_stats['last_regression_check'],
                'regression_check_count': self.regression_stats['regression_check_count'],
                'recent_regressions': [alert.to_dict() for alert in self.regression_alerts[-5:]],  # 最近5个
                'trend_analyses': {k.value: v.to_dict() for k, v in self.trend_analyses.items()}
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"获取回归检测摘要失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)
            return {}
    
    def shutdown(self):
        """关闭回归测试器"""
        try:
            self.logger.info("关闭性能回归测试器...")
            
            # 关闭性能组件
            if hasattr(self.benchmarker, 'shutdown'):
                self.benchmarker.shutdown()
            if hasattr(self.monitor, 'shutdown'):
                self.monitor.shutdown()
            
            self.logger.info("性能回归测试器已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭性能回归测试器失败: {e}")
            self.error_handler.handle_error(e, ErrorRecoveryStrategy.CONTINUE)


# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建回归测试器
    regression_tester = PerformanceRegressionTester()
    
    try:
        # 建立基准线
        baseline = regression_tester.establish_baseline()
        
        if baseline:
            # 检测回归
            regressions = regression_tester.detect_regressions()
            
            # 生成报告
            regression_tester.save_regression_report()
            
            print(f"回归检测完成，发现 {len(regressions)} 个回归问题")
        
    finally:
        # 关闭回归测试器
        regression_tester.shutdown()
