#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第四阶段可观测性增强测试 v1.0.0
测试统一日志框架、性能监控指标和调试诊断功能

作者: LAD Team
创建时间: 2025-08-17
最后更新: 2025-08-17
"""

import sys
import os
import time
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入测试的组件
from core.unified_logging_framework import (
    UnifiedLoggingFramework, LogLevel, LogOutput, LogFormat, LogContext, LogMetrics,
    StructuredFormatter, setup_logging_framework,
    log_debug, log_info, log_warning, log_error, log_critical
)
from core.performance_metrics_manager import (
    PerformanceMetricsManager, MetricType, MetricUnit, MetricValue, MetricDefinition, MetricData,
    AlertRule, Alert
)
from core.debug_diagnostics_manager import (
    DebugDiagnosticsManager, DiagnosticLevel, DiagnosticType, DiagnosticResult,
    ComponentStatus, SystemHealth
)


class TestUnifiedLoggingFramework:
    """测试统一日志框架"""
    
    def setup_method(self):
        """测试前准备"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.logging_framework = UnifiedLoggingFramework(
            log_dir=self.test_dir / "logs",
            log_level=LogLevel.DEBUG,
            output_formats=[LogOutput.CONSOLE, LogOutput.FILE],
            log_format=LogFormat.STRUCTURED
        )
    
    def teardown_method(self):
        """测试后清理"""
        if hasattr(self, 'logging_framework'):
            self.logging_framework.shutdown()
        if hasattr(self, 'test_dir') and self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_logging_framework_initialization(self):
        """测试日志框架初始化"""
        assert self.logging_framework is not None
        assert self.logging_framework.log_level == LogLevel.DEBUG
        assert LogOutput.CONSOLE in self.logging_framework.output_formats
        assert LogOutput.FILE in self.logging_framework.output_formats
        assert self.logging_framework.log_format == LogFormat.STRUCTURED
    
    def test_log_with_context(self):
        """测试带上下文的日志记录"""
        # 记录测试日志
        self.logging_framework.log_with_context(
            level=LogLevel.INFO,
            message="测试日志消息",
            module="test_module",
            function="test_function",
            line_number=42,
            extra_data={"test_key": "test_value"}
        )
        
        # 检查日志指标
        metrics = self.logging_framework.get_log_metrics()
        assert metrics.total_logs > 0
        assert metrics.logs_by_level["INFO"] > 0
        assert "test_module" in metrics.logs_by_module
    
    def test_logger_creation(self):
        """测试日志记录器创建"""
        logger = self.logging_framework.get_logger("test_logger", LogLevel.DEBUG)
        assert logger is not None
        assert logger.name == "test_logger"
        assert logger.level == 10  # DEBUG level
    
    def test_log_export(self):
        """测试日志导出"""
        # 记录一些测试日志
        for i in range(5):
            self.logging_framework.log_with_context(
                level=LogLevel.INFO,
                message=f"测试日志 {i}",
                module="test_module",
                function="test_function",
                line_number=i
            )
        
        # 导出日志
        result = self.logging_framework.export_logs()
        assert "日志导出完成" in result
    
    def test_log_metrics(self):
        """测试日志指标"""
        # 记录不同级别的日志
        levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR]
        for level in levels:
            self.logging_framework.log_with_context(
                level=level,
                message=f"测试{level.value}日志",
                module="test_module",
                function="test_function",
                line_number=1
            )
        
        # 检查指标
        metrics = self.logging_framework.get_log_metrics()
        assert metrics.total_logs >= 4  # 可能有其他日志
        assert metrics.logs_by_level["DEBUG"] >= 1
        assert metrics.logs_by_level["INFO"] >= 1
        assert metrics.logs_by_level["WARNING"] >= 1
        assert metrics.logs_by_level["ERROR"] >= 1


class TestPerformanceMetricsManager:
    """测试性能监控指标管理器"""
    
    def setup_method(self):
        """测试前准备"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.metrics_manager = PerformanceMetricsManager(
            metrics_dir=self.test_dir / "metrics",
            collection_interval=1.0,  # 快速收集用于测试
            enable_alerts=True,
            max_history_size=100
        )
    
    def teardown_method(self):
        """测试后清理"""
        if hasattr(self, 'metrics_manager'):
            self.metrics_manager.shutdown()
        if hasattr(self, 'test_dir') and self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_metrics_manager_initialization(self):
        """测试指标管理器初始化"""
        assert self.metrics_manager is not None
        assert self.metrics_manager.collection_interval == 1.0
        assert self.metrics_manager.enable_alerts is True
        assert self.metrics_manager.max_history_size == 100
    
    def test_metric_definitions(self):
        """测试指标定义"""
        metrics = self.metrics_manager.get_all_metrics()
        assert len(metrics) > 0
        
        # 检查系统指标
        assert "cpu_usage" in metrics
        assert "memory_usage" in metrics
        assert "disk_usage" in metrics
        
        # 检查应用指标
        assert "application_memory" in metrics
        assert "application_threads" in metrics
        assert "application_uptime" in metrics
        
        # 检查性能指标
        assert "response_time" in metrics
        assert "throughput" in metrics
        assert "error_rate" in metrics
    
    def test_metrics_collection(self):
        """测试指标收集"""
        # 等待指标收集
        time.sleep(2)
        
        # 检查指标数据
        cpu_metric = self.metrics_manager.get_metric_data("cpu_usage")
        assert cpu_metric is not None
        assert cpu_metric.current_value is not None
        assert cpu_metric.current_value.value >= 0
    
    def test_alert_rules(self):
        """测试告警规则"""
        # 添加告警规则
        alert_rule = AlertRule(
            metric_name="cpu_usage",
            condition=">",
            threshold=50.0,
            severity="warning",
            message="CPU使用率超过{threshold}%，当前值：{value}%"
        )
        self.metrics_manager.add_alert_rule(alert_rule)
        
        # 检查告警规则
        active_alerts = self.metrics_manager.get_active_alerts()
        # 注意：这里可能没有告警，因为CPU使用率可能不会超过50%
        assert isinstance(active_alerts, list)
    
    def test_metrics_summary(self):
        """测试指标摘要"""
        summary = self.metrics_manager.get_metrics_summary()
        assert summary is not None
        assert "total_metrics" in summary
        assert "metrics_by_type" in summary
        assert "alerts_summary" in summary
        assert "collection_status" in summary
        
        assert summary["total_metrics"] > 0
        assert summary["collection_status"]["running"] is True
    
    def test_metrics_export(self):
        """测试指标导出"""
        # 等待一些指标数据收集
        time.sleep(2)
        
        # 导出指标
        result = self.metrics_manager.export_metrics()
        assert "指标导出完成" in result


class TestDebugDiagnosticsManager:
    """测试调试和诊断管理器"""
    
    def setup_method(self):
        """测试前准备"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.diagnostics_manager = DebugDiagnosticsManager(
            diagnostics_dir=self.test_dir / "diagnostics",
            enable_auto_diagnostics=True,
            auto_diagnostics_interval=1.0,  # 快速诊断用于测试
            max_diagnostic_history=50
        )
    
    def teardown_method(self):
        """测试后清理"""
        if hasattr(self, 'diagnostics_manager'):
            self.diagnostics_manager.shutdown()
        if hasattr(self, 'test_dir') and self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_diagnostics_manager_initialization(self):
        """测试诊断管理器初始化"""
        assert self.diagnostics_manager is not None
        assert self.diagnostics_manager.enable_auto_diagnostics is True
        assert self.diagnostics_manager.auto_diagnostics_interval == 1.0
        assert self.diagnostics_manager.max_diagnostic_history == 50
    
    def test_system_diagnostics(self):
        """测试系统诊断"""
        results = self.diagnostics_manager.run_system_diagnostics()
        assert isinstance(results, list)
        assert len(results) > 0
        
        # 检查诊断结果
        for result in results:
            assert isinstance(result, DiagnosticResult)
            assert result.type == DiagnosticType.SYSTEM
            assert result.timestamp > 0
            assert result.message is not None
    
    def test_application_diagnostics(self):
        """测试应用诊断"""
        results = self.diagnostics_manager.run_application_diagnostics()
        assert isinstance(results, list)
        assert len(results) > 0
        
        # 检查诊断结果
        for result in results:
            assert isinstance(result, DiagnosticResult)
            assert result.type == DiagnosticType.APPLICATION
            assert result.timestamp > 0
            assert result.message is not None
    
    def test_performance_diagnostics(self):
        """测试性能诊断"""
        results = self.diagnostics_manager.run_performance_diagnostics()
        assert isinstance(results, list)
        assert len(results) > 0
        
        # 检查诊断结果
        for result in results:
            assert isinstance(result, DiagnosticResult)
            assert result.type == DiagnosticType.PERFORMANCE
            assert result.timestamp > 0
            assert result.message is not None
    
    def test_memory_diagnostics(self):
        """测试内存诊断"""
        results = self.diagnostics_manager.run_memory_diagnostics()
        assert isinstance(results, list)
        assert len(results) > 0
        
        # 检查诊断结果
        for result in results:
            assert isinstance(result, DiagnosticResult)
            assert result.type == DiagnosticType.MEMORY
            assert result.timestamp > 0
            assert result.message is not None
    
    def test_cache_diagnostics(self):
        """测试缓存诊断"""
        results = self.diagnostics_manager.run_cache_diagnostics()
        assert isinstance(results, list)
        # 注意：缓存诊断可能返回空列表，因为缓存管理器可能没有初始化
    
    def test_system_health(self):
        """测试系统健康状态"""
        health = self.diagnostics_manager.get_system_health()
        assert isinstance(health, SystemHealth)
        assert health.overall_status in ["healthy", "warning", "error", "unknown"]
        assert health.component_count >= 0  # 可能为0
        assert health.last_check > 0
        
        # 测试运行时状态查询接口
        runtime_status = self.diagnostics_manager.get_runtime_status()
        assert isinstance(runtime_status, dict)
        assert 'system_health' in runtime_status
        assert 'component_statuses' in runtime_status
        assert 'diagnostic_summary' in runtime_status
        assert 'timestamp' in runtime_status
        
        # 测试组件状态查询
        component_status = self.diagnostics_manager.get_component_status("system")
        assert component_status is not None
        assert 'status' in component_status
        assert 'last_check' in component_status
        
        # 测试系统概览
        system_overview = self.diagnostics_manager.get_system_overview()
        assert isinstance(system_overview, dict)
        assert 'system_info' in system_overview
        assert 'python_info' in system_overview
        assert 'timestamp' in system_overview
        
        # 测试性能状态
        performance_status = self.diagnostics_manager.get_performance_status()
        assert isinstance(performance_status, dict)
        assert 'response_time' in performance_status
        assert 'throughput' in performance_status
        assert 'timestamp' in performance_status
    
    def test_diagnostic_history(self):
        """测试诊断历史"""
        # 运行一些诊断
        self.diagnostics_manager.run_system_diagnostics()
        self.diagnostics_manager.run_application_diagnostics()
        
        # 获取诊断历史
        history = self.diagnostics_manager.get_diagnostic_history()
        assert isinstance(history, list)
        assert len(history) > 0
        
        # 按类型过滤
        system_history = self.diagnostics_manager.get_diagnostic_history(
            diagnostic_type=DiagnosticType.SYSTEM
        )
        assert isinstance(system_history, list)
        for result in system_history:
            assert result.type == DiagnosticType.SYSTEM
    
    def test_diagnostics_export(self):
        """测试诊断数据导出"""
        # 运行一些诊断
        self.diagnostics_manager.run_system_diagnostics()
        self.diagnostics_manager.run_application_diagnostics()
        
        # 导出诊断数据
        result = self.diagnostics_manager.export_diagnostics()
        assert "诊断数据导出完成" in result


class TestObservabilityIntegration:
    """测试可观测性组件集成"""
    
    def setup_method(self):
        """测试前准备"""
        self.test_dir = Path(tempfile.mkdtemp())
        
        # 创建日志框架
        self.logging_framework = UnifiedLoggingFramework(
            log_dir=self.test_dir / "logs",
            log_level=LogLevel.DEBUG
        )
        
        # 创建指标管理器
        self.metrics_manager = PerformanceMetricsManager(
            metrics_dir=self.test_dir / "metrics",
            collection_interval=1.0
        )
        
        # 创建诊断管理器
        self.diagnostics_manager = DebugDiagnosticsManager(
            diagnostics_dir=self.test_dir / "diagnostics",
            auto_diagnostics_interval=1.0
        )
        
        # 设置日志记录器
        self.metrics_manager.setup_logging(self.logging_framework.get_logger("metrics"))
        self.diagnostics_manager.setup_logging(self.logging_framework.get_logger("diagnostics"))
    
    def teardown_method(self):
        """测试后清理"""
        if hasattr(self, 'diagnostics_manager'):
            self.diagnostics_manager.shutdown()
        if hasattr(self, 'metrics_manager'):
            self.metrics_manager.shutdown()
        if hasattr(self, 'logging_framework'):
            self.logging_framework.shutdown()
        if hasattr(self, 'test_dir') and self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_integrated_observability(self):
        """测试集成可观测性功能"""
        # 记录日志
        self.logging_framework.log_with_context(
            level=LogLevel.INFO,
            message="集成测试日志",
            module="integration_test",
            function="test_function",
            line_number=1
        )
        
        # 等待指标收集
        time.sleep(2)
        
        # 运行诊断
        self.diagnostics_manager.run_system_diagnostics()
        self.diagnostics_manager.run_application_diagnostics()
        
        # 检查日志指标
        log_metrics = self.logging_framework.get_log_metrics()
        assert log_metrics.total_logs > 0
        
        # 检查性能指标
        metrics_summary = self.metrics_manager.get_metrics_summary()
        assert metrics_summary["total_metrics"] > 0
        
        # 检查系统健康
        system_health = self.diagnostics_manager.get_system_health()
        assert system_health.component_count > 0
        
        print("集成可观测性测试通过")
    
    def test_end_to_end_observability_workflow(self):
        """测试端到端可观测性工作流"""
        # 1. 设置日志框架
        setup_logging_framework(self.logging_framework)
        
        # 2. 使用便捷日志函数
        log_info("工作流测试开始", "test_workflow", "test_function", 1, test_param="test_value")
        log_warning("工作流警告", "test_workflow", "test_function", 2)
        log_error("工作流错误", "test_workflow", "test_function", 3)
        
        # 3. 添加告警规则
        alert_rule = AlertRule(
            metric_name="cpu_usage",
            condition=">",
            threshold=80.0,
            severity="warning",
            message="CPU使用率过高"
        )
        self.metrics_manager.add_alert_rule(alert_rule)
        
        # 4. 等待数据收集和诊断
        time.sleep(3)
        
        # 5. 检查所有组件状态
        log_metrics = self.logging_framework.get_log_metrics()
        metrics_summary = self.metrics_manager.get_metrics_summary()
        system_health = self.diagnostics_manager.get_system_health()
        
        # 6. 导出数据
        log_export_result = self.logging_framework.export_logs()
        metrics_export_result = self.metrics_manager.export_metrics()
        diagnostics_export_result = self.diagnostics_manager.export_diagnostics()
        
        # 验证结果
        assert log_metrics.total_logs >= 3  # 至少3条日志
        assert metrics_summary["total_metrics"] > 0
        assert system_health.component_count > 0
        assert "日志导出完成" in log_export_result
        assert "指标导出完成" in metrics_export_result
        assert "诊断数据导出完成" in diagnostics_export_result
        
        print("端到端可观测性工作流测试通过")


def run_all_tests():
    """运行所有测试"""
    print("开始第四阶段可观测性增强测试...")
    
    # 测试统一日志框架
    print("\n=== 测试统一日志框架 ===")
    test_logging = TestUnifiedLoggingFramework()
    test_logging.setup_method()
    test_logging.test_logging_framework_initialization()
    test_logging.test_log_with_context()
    test_logging.test_logger_creation()
    test_logging.test_log_export()
    test_logging.test_log_metrics()
    test_logging.teardown_method()
    print("统一日志框架测试通过")
    
    # 测试性能监控指标管理器
    print("\n=== 测试性能监控指标管理器 ===")
    test_metrics = TestPerformanceMetricsManager()
    test_metrics.setup_method()
    test_metrics.test_metrics_manager_initialization()
    test_metrics.test_metric_definitions()
    test_metrics.test_metrics_collection()
    test_metrics.test_alert_rules()
    test_metrics.test_metrics_summary()
    test_metrics.test_metrics_export()
    test_metrics.teardown_method()
    print("性能监控指标管理器测试通过")
    
    # 测试调试和诊断管理器
    print("\n=== 测试调试和诊断管理器 ===")
    test_diagnostics = TestDebugDiagnosticsManager()
    test_diagnostics.setup_method()
    test_diagnostics.test_diagnostics_manager_initialization()
    test_diagnostics.test_system_diagnostics()
    test_diagnostics.test_application_diagnostics()
    test_diagnostics.test_performance_diagnostics()
    test_diagnostics.test_memory_diagnostics()
    test_diagnostics.test_cache_diagnostics()
    test_diagnostics.test_system_health()
    test_diagnostics.test_diagnostic_history()
    test_diagnostics.test_diagnostics_export()
    test_diagnostics.teardown_method()
    print("调试和诊断管理器测试通过")
    
    # 测试集成功能
    print("\n=== 测试可观测性集成 ===")
    test_integration = TestObservabilityIntegration()
    test_integration.setup_method()
    test_integration.test_integrated_observability()
    test_integration.test_end_to_end_observability_workflow()
    test_integration.teardown_method()
    print("可观测性集成测试通过")
    
    print("\n🎉 第四阶段可观测性增强测试全部通过！")


if __name__ == "__main__":
    run_all_tests() 