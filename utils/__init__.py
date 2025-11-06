#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具模块包
包含配置管理、文件工具等通用功能

作者: LAD Team
创建时间: 2025-01-08
最后更新: 2025-08-16
"""

# 导入基础工具模块
from .config_manager import ConfigManager

# 导入第一阶段：轻量级基础功能
from .lightweight_performance_test import (
    LightweightPerformanceTest, 
    PerformanceMetrics,
    create_performance_test,
    run_quick_benchmark
)

from .config_migration_manager import (
    ConfigMigrationManager,
    MigrationResult,
    create_config_migration_manager,
    migrate_configs
)

from .enhanced_logger import (
    EnhancedLogger,
    OperationContext,
    EnhancedLogFormatter,
    LoggingContextManager,
    create_enhanced_logger,
    enhance_existing_logger
)

# 导入第二阶段：资源与架构管理
from .resource_manager import (
    ResourceManager,
    ResourceType,
    ResourceInfo,
    create_resource_manager,
    get_resources_summary
)

from .architecture_adapter import (
    ArchitectureAdapter,
    ServiceRegistry,
    ServiceStatus,
    ServicePriority,
    ServiceInfo,
    ComponentAdapter,
    create_architecture_adapter,
    get_architecture_status
)

from .first_phase_integration import (
    FirstPhaseComponentIntegration,
    ComponentInfo,
    ConfigManagerAdapter,
    FileTreeAdapter,
    ContentViewerAdapter,
    create_first_phase_integration,
    integrate_all_components
)

# 导入第三阶段：接口一致性管理
from .interface_compatibility_manager import (
    InterfaceCompatibilityManager,
    InterfaceVersion,
    CompatibilityLevel,
    InterfaceInfo,
    CompatibilityResult,
    InterfaceSpecification,
    create_interface_compatibility_manager,
    analyze_interface,
    check_interface_compatibility
)

from .interface_validator import (
    InterfaceValidator,
    ValidationLevel,
    ValidationResult,
    ValidationIssue,
    ValidationReport,
    create_interface_validator,
    validate_interface
)

__all__ = [
    # 基础工具
    'ConfigManager',
    
    # 第一阶段：轻量级基础功能
    'LightweightPerformanceTest',
    'PerformanceMetrics', 
    'create_performance_test',
    'run_quick_benchmark',
    
    'ConfigMigrationManager',
    'MigrationResult',
    'create_config_migration_manager', 
    'migrate_configs',
    
    'EnhancedLogger',
    'OperationContext',
    'EnhancedLogFormatter',
    'LoggingContextManager',
    'create_enhanced_logger',
    'enhance_existing_logger',
    
    # 第二阶段：资源与架构管理
    'ResourceManager',
    'ResourceType',
    'ResourceInfo',
    'create_resource_manager',
    'get_resources_summary',
    
    'ArchitectureAdapter',
    'ServiceRegistry',
    'ServiceStatus',
    'ServicePriority',
    'ServiceInfo',
    'ComponentAdapter',
    'create_architecture_adapter',
    'get_architecture_status',
    
    'FirstPhaseComponentIntegration',
    'ComponentInfo',
    'ConfigManagerAdapter',
    'FileTreeAdapter',
    'ContentViewerAdapter',
    'create_first_phase_integration',
    'integrate_all_components',
    
    # 第三阶段：接口一致性管理
    'InterfaceCompatibilityManager',
    'InterfaceVersion',
    'CompatibilityLevel',
    'InterfaceInfo',
    'CompatibilityResult',
    'InterfaceSpecification',
    'create_interface_compatibility_manager',
    'analyze_interface',
    'check_interface_compatibility',
    
    'InterfaceValidator',
    'ValidationLevel',
    'ValidationResult',
    'ValidationIssue',
    'ValidationReport',
    'create_interface_validator',
    'validate_interface'
] 