#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心模块包
包含文件解析、Markdown渲染等核心功能

作者: LAD Team
创建时间: 2025-01-08
最后更新: 2025-01-08
"""

# 导入第三阶段：性能优化组件
from .high_performance_file_reader import (
    HighPerformanceFileReader, ReadStrategy, FileType, FileInfo, ReadMetrics
)
from .render_performance_optimizer import (
    RenderPerformanceOptimizer, RenderStrategy, RenderMode, RenderMetrics, RenderChunk
)
from .memory_optimization_manager import (
    MemoryOptimizationManager, MemoryStrategy, MemoryThreshold, MemoryInfo, MemoryMetrics, MemoryPool, StringPool
)
from .performance_benchmark import (
    PerformanceBenchmark, BenchmarkType, BenchmarkResultEnum, BenchmarkResult, BenchmarkMetrics
)

# 导入第四阶段：可观测性增强组件
from .unified_logging_framework import (
    UnifiedLoggingFramework, LogLevel, LogOutput, LogFormat, LogContext, LogMetrics,
    StructuredFormatter, setup_logging_framework,
    log_debug, log_info, log_warning, log_error, log_critical
)
from .performance_metrics_manager import (
    PerformanceMetricsManager, MetricType, MetricUnit, MetricValue, MetricDefinition, MetricData,
    AlertRule, Alert
)
from .debug_diagnostics_manager import (
    DebugDiagnosticsManager, DiagnosticLevel, DiagnosticType, DiagnosticResult,
    ComponentStatus, SystemHealth
)

# 导入第五阶段：边界条件处理与系统健壮性组件
from .boundary_condition_handler import (
    BoundaryConditionHandler, BoundaryType, ValidationLevel, BoundaryRule, ValidationResult, ParameterSuggestion
)
from .system_resource_boundary_checker import (
    SystemResourceBoundaryChecker, ResourceType, ResourceStatus, ResourceLimit, ResourceUsage, ResourceAlert
)

# 导入第六阶段：性能优化策略组件
from .performance_optimization_strategy import (
    PerformanceOptimizationStrategy, OptimizationStrategy, OptimizationTarget, OptimizationLevel,
    OptimizationRule, OptimizationResult, PerformanceProfile
)

# 导出第三阶段性能优化组件
__all__ = [
    # 现有组件
    'UnifiedCacheManager', 'CacheStrategy', 'CacheStatus', 'CacheEntry', 'CacheStats',
    'CacheInvalidationManager', 'InvalidationStrategy', 'InvalidationTrigger', 'InvalidationRule', 'InvalidationEvent',
    'EnhancedErrorHandler', 'ErrorSeverity', 'ErrorCategory', 'ErrorRecoveryStrategy', 'ErrorContext', 'ErrorInfo',
    'HybridMarkdownRenderer', 'DynamicModuleImporter',
    
    # 第三阶段：性能优化组件
    'HighPerformanceFileReader', 'ReadStrategy', 'FileType', 'FileInfo', 'ReadMetrics',
    'RenderPerformanceOptimizer', 'RenderStrategy', 'RenderMode', 'RenderMetrics', 'RenderChunk',
    'MemoryOptimizationManager', 'MemoryStrategy', 'MemoryThreshold', 'MemoryInfo', 'MemoryMetrics', 'MemoryPool', 'StringPool',
    'PerformanceBenchmark', 'BenchmarkType', 'BenchmarkResultEnum', 'BenchmarkResult', 'BenchmarkMetrics',
    
    # 第四阶段：可观测性增强组件
    'UnifiedLoggingFramework', 'LogLevel', 'LogOutput', 'LogFormat', 'LogContext', 'LogMetrics',
    'StructuredFormatter', 'setup_logging_framework',
    'log_debug', 'log_info', 'log_warning', 'log_error', 'log_critical',
    'PerformanceMetricsManager', 'MetricType', 'MetricUnit', 'MetricValue', 'MetricDefinition', 'MetricData',
    'AlertRule', 'Alert',
    'DebugDiagnosticsManager', 'DiagnosticLevel', 'DiagnosticType', 'DiagnosticResult',
    'ComponentStatus', 'SystemHealth',
    
    # 第五阶段：边界条件处理与系统健壮性组件
    'BoundaryConditionHandler', 'BoundaryType', 'ValidationLevel', 'BoundaryRule', 'ValidationResult', 'ParameterSuggestion',
    'SystemResourceBoundaryChecker', 'ResourceType', 'ResourceStatus', 'ResourceLimit', 'ResourceUsage', 'ResourceAlert',
    
    # 第六阶段：性能优化策略组件
    'PerformanceOptimizationStrategy', 'OptimizationStrategy', 'OptimizationTarget', 'OptimizationLevel',
    'OptimizationRule', 'OptimizationResult', 'PerformanceProfile'
] 