#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
架构适配器 v1.0.0
创建服务注册表适配层，支持现有组件与新架构的集成

作者: LAD Team
创建时间: 2025-08-16
最后更新: 2025-08-16
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable, Type
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod


class ServiceStatus(Enum):
    """服务状态枚举"""
    REGISTERED = "registered"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    UNKNOWN = "unknown"


class ServicePriority(Enum):
    """服务优先级枚举"""
    CRITICAL = 0      # 关键服务
    HIGH = 1          # 高优先级
    NORMAL = 2        # 普通优先级
    LOW = 3           # 低优先级
    BACKGROUND = 4    # 后台服务


@dataclass
class ServiceInfo:
    """服务信息数据类"""
    name: str
    service_type: str
    status: ServiceStatus
    priority: ServicePriority
    dependencies: List[str]
    instance: Optional[Any] = None
    config: Optional[Dict[str, Any]] = None
    start_time: Optional[str] = None
    last_heartbeat: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['status'] = self.status.value
        data['priority'] = self.priority.value
        return data


class ServiceRegistry:
    """服务注册表"""
    
    def __init__(self):
        """初始化服务注册表"""
        self.services: Dict[str, ServiceInfo] = {}
        self.service_types: Dict[str, List[str]] = {}
        self.dependency_graph: Dict[str, List[str]] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_service(self, name: str, service_type: str, 
                        priority: ServicePriority = ServicePriority.NORMAL,
                        dependencies: List[str] = None,
                        config: Dict[str, Any] = None) -> bool:
        """
        注册服务
        
        Args:
            name: 服务名称
            service_type: 服务类型
            priority: 服务优先级
            dependencies: 依赖服务列表
            config: 服务配置
            
        Returns:
            是否注册成功
        """
        try:
            if name in self.services:
                self.logger.warning(f"服务 {name} 已存在，将被覆盖")
            
            # 创建服务信息
            service_info = ServiceInfo(
                name=name,
                service_type=service_type,
                status=ServiceStatus.REGISTERED,
                priority=priority,
                dependencies=dependencies or [],
                config=config or {}
            )
            
            # 注册服务
            self.services[name] = service_info
            
            # 更新服务类型索引
            if service_type not in self.service_types:
                self.service_types[service_type] = []
            self.service_types[service_type].append(name)
            
            # 更新依赖图
            self.dependency_graph[name] = dependencies or []
            
            self.logger.info(f"服务 {name} 注册成功")
            return True
            
        except Exception as e:
            self.logger.error(f"服务 {name} 注册失败: {e}")
            return False
    
    def unregister_service(self, name: str) -> bool:
        """
        注销服务
        
        Args:
            name: 服务名称
            
        Returns:
            是否注销成功
        """
        try:
            if name not in self.services:
                self.logger.warning(f"服务 {name} 不存在")
                return False
            
            service_info = self.services[name]
            
            # 从服务类型索引中移除
            if service_info.service_type in self.service_types:
                if name in self.service_types[service_info.service_type]:
                    self.service_types[service_info.service_type].remove(name)
            
            # 从依赖图中移除
            if name in self.dependency_graph:
                del self.dependency_graph[name]
            
            # 从服务列表中移除
            del self.services[name]
            
            self.logger.info(f"服务 {name} 注销成功")
            return True
            
        except Exception as e:
            self.logger.error(f"服务 {name} 注销失败: {e}")
            return False
    
    def get_service(self, name: str) -> Optional[ServiceInfo]:
        """获取服务信息"""
        return self.services.get(name)
    
    def get_services_by_type(self, service_type: str) -> List[ServiceInfo]:
        """按类型获取服务列表"""
        service_names = self.service_types.get(service_type, [])
        return [self.services[name] for name in service_names if name in self.services]
    
    def update_service_status(self, name: str, status: ServiceStatus, 
                            error_message: str = None) -> bool:
        """更新服务状态"""
        if name not in self.services:
            return False
        
        service_info = self.services[name]
        service_info.status = status
        service_info.last_heartbeat = datetime.now().isoformat()
        
        if status == ServiceStatus.RUNNING and not service_info.start_time:
            service_info.start_time = datetime.now().isoformat()
        
        if error_message:
            service_info.error_message = error_message
        
        return True
    
    def get_service_dependencies(self, name: str) -> List[str]:
        """获取服务依赖"""
        return self.dependency_graph.get(name, [])
    
    def check_dependencies_ready(self, name: str) -> bool:
        """检查服务依赖是否就绪"""
        dependencies = self.get_service_dependencies(name)
        for dep_name in dependencies:
            dep_service = self.get_service(dep_name)
            if not dep_service or dep_service.status != ServiceStatus.RUNNING:
                return False
        return True
    
    def get_services_summary(self) -> Dict[str, Any]:
        """获取服务摘要信息"""
        summary = {
            'total_services': len(self.services),
            'service_types': {},
            'status_distribution': {},
            'priority_distribution': {}
        }
        
        # 统计服务类型分布
        for service_type, service_names in self.service_types.items():
            summary['service_types'][service_type] = len(service_names)
        
        # 统计状态分布
        for service in self.services.values():
            status = service.status.value
            if status not in summary['status_distribution']:
                summary['status_distribution'][status] = 0
            summary['status_distribution'][status] += 1
        
        # 统计优先级分布
        for service in self.services.values():
            priority = service.priority.value
            if priority not in summary['priority_distribution']:
                summary['priority_distribution'][priority] = 0
            summary['priority_distribution'][priority] += 1
        
        return summary


class ArchitectureAdapter:
    """架构适配器"""
    
    def __init__(self, base_dir: Union[str, Path]):
        """
        初始化架构适配器
        
        Args:
            base_dir: 基础目录路径
        """
        self.base_dir = Path(base_dir)
        self.service_registry = ServiceRegistry()
        self.logger = logging.getLogger(__name__)
        
        # 组件适配器映射
        self.component_adapters: Dict[str, 'ComponentAdapter'] = {}
        
        # 初始化基础服务
        self._initialize_base_services()
    
    def _initialize_base_services(self):
        """初始化基础服务"""
        # 注册配置管理服务
        self.service_registry.register_service(
            name="config_manager",
            service_type="core",
            priority=ServicePriority.CRITICAL,
            dependencies=[],
            config={"config_dir": str(self.base_dir / "config")}
        )
        
        # 注册日志服务
        self.service_registry.register_service(
            name="logger",
            service_type="core",
            priority=ServicePriority.CRITICAL,
            dependencies=[],
            config={"log_level": "INFO"}
        )
        
        # 注册资源管理服务
        self.service_registry.register_service(
            name="resource_manager",
            service_type="core",
            priority=ServicePriority.HIGH,
            dependencies=["config_manager"],
            config={"base_dir": str(self.base_dir)}
        )
        
        self.logger.info("基础服务初始化完成")
    
    def register_component_adapter(self, component_type: str, adapter: 'ComponentAdapter'):
        """
        注册组件适配器
        
        Args:
            component_type: 组件类型
            adapter: 组件适配器实例
        """
        self.component_adapters[component_type] = adapter
        self.logger.info(f"组件适配器 {component_type} 注册成功")
    
    def get_component_adapter(self, component_type: str) -> Optional['ComponentAdapter']:
        """获取组件适配器"""
        return self.component_adapters.get(component_type)
    
    def adapt_existing_component(self, component_type: str, component_instance: Any,
                                config: Dict[str, Any] = None) -> bool:
        """
        适配现有组件
        
        Args:
            component_type: 组件类型
            component_instance: 组件实例
            config: 组件配置
            
        Returns:
            是否适配成功
        """
        try:
            adapter = self.get_component_adapter(component_type)
            if not adapter:
                self.logger.warning(f"未找到组件类型 {component_type} 的适配器")
                return False
            
            # 执行适配
            success = adapter.adapt(component_instance, config)
            if success:
                self.logger.info(f"组件 {component_type} 适配成功")
            else:
                self.logger.error(f"组件 {component_type} 适配失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"组件 {component_type} 适配过程中发生异常: {e}")
            return False
    
    def start_service(self, service_name: str) -> bool:
        """
        启动服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            是否启动成功
        """
        try:
            service_info = self.service_registry.get_service(service_name)
            if not service_info:
                self.logger.error(f"服务 {service_name} 不存在")
                return False
            
            # 检查依赖
            if not self.service_registry.check_dependencies_ready(service_name):
                self.logger.warning(f"服务 {service_name} 的依赖未就绪")
                return False
            
            # 更新状态为启动中
            self.service_registry.update_service_status(service_name, ServiceStatus.STARTING)
            
            # 执行启动逻辑
            if service_name == "config_manager":
                success = self._start_config_manager()
            elif service_name == "logger":
                success = self._start_logger()
            elif service_name == "resource_manager":
                success = self._start_resource_manager()
            else:
                success = self._start_custom_service(service_name)
            
            if success:
                self.service_registry.update_service_status(service_name, ServiceStatus.RUNNING)
                self.logger.info(f"服务 {service_name} 启动成功")
            else:
                self.service_registry.update_service_status(service_name, ServiceStatus.ERROR, "启动失败")
                self.logger.error(f"服务 {service_name} 启动失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"启动服务 {service_name} 时发生异常: {e}")
            self.service_registry.update_service_status(service_name, ServiceStatus.ERROR, str(e))
            return False
    
    def _start_config_manager(self) -> bool:
        """启动配置管理器"""
        try:
            # 这里可以添加配置管理器的启动逻辑
            return True
        except Exception as e:
            self.logger.error(f"启动配置管理器失败: {e}")
            return False
    
    def _start_logger(self) -> bool:
        """启动日志服务"""
        try:
            # 这里可以添加日志服务的启动逻辑
            return True
        except Exception as e:
            self.logger.error(f"启动日志服务失败: {e}")
            return False
    
    def _start_resource_manager(self) -> bool:
        """启动资源管理器"""
        try:
            # 这里可以添加资源管理器的启动逻辑
            return True
        except Exception as e:
            self.logger.error(f"启动资源管理器失败: {e}")
            return False
    
    def _start_custom_service(self, service_name: str) -> bool:
        """启动自定义服务"""
        try:
            # 这里可以添加自定义服务的启动逻辑
            return True
        except Exception as e:
            self.logger.error(f"启动自定义服务 {service_name} 失败: {e}")
            return False
    
    def stop_service(self, service_name: str) -> bool:
        """
        停止服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            是否停止成功
        """
        try:
            service_info = self.service_registry.get_service(service_name)
            if not service_info:
                return False
            
            # 更新状态为停止中
            self.service_registry.update_service_status(service_name, ServiceStatus.STOPPING)
            
            # 执行停止逻辑
            # 这里可以添加具体的停止逻辑
            
            # 更新状态为已停止
            self.service_registry.update_service_status(service_name, ServiceStatus.STOPPED)
            self.logger.info(f"服务 {service_name} 停止成功")
            return True
            
        except Exception as e:
            self.logger.error(f"停止服务 {service_name} 时发生异常: {e}")
            self.service_registry.update_service_status(service_name, ServiceStatus.ERROR, str(e))
            return False
    
    def get_architecture_status(self) -> Dict[str, Any]:
        """获取架构状态"""
        return {
            'timestamp': datetime.now().isoformat(),
            'services': self.service_registry.get_services_summary(),
            'component_adapters': list(self.component_adapters.keys()),
            'base_directory': str(self.base_dir)
        }
    
    def generate_architecture_report(self) -> str:
        """生成架构报告"""
        status = self.get_architecture_status()
        
        report = []
        report.append("# 架构适配器状态报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("## 基础信息")
        report.append(f"- 基础目录: {status['base_directory']}")
        report.append(f"- 组件适配器数量: {len(status['component_adapters'])}")
        report.append("")
        
        report.append("## 服务状态")
        services_summary = status['services']
        report.append(f"- 总服务数量: {services_summary['total_services']}")
        report.append("")
        
        # 服务类型分布
        report.append("### 服务类型分布")
        for service_type, count in services_summary['service_types'].items():
            report.append(f"- {service_type}: {count}")
        report.append("")
        
        # 状态分布
        report.append("### 服务状态分布")
        for status_name, count in services_summary['status_distribution'].items():
            report.append(f"- {status_name}: {count}")
        report.append("")
        
        # 优先级分布
        report.append("### 服务优先级分布")
        for priority, count in services_summary['priority_distribution'].items():
            report.append(f"- {priority}: {count}")
        report.append("")
        
        report.append("## 组件适配器")
        for adapter_name in status['component_adapters']:
            report.append(f"- {adapter_name}")
        
        return "\n".join(report)


class ComponentAdapter(ABC):
    """组件适配器抽象基类"""
    
    @abstractmethod
    def adapt(self, component_instance: Any, config: Dict[str, Any] = None) -> bool:
        """
        适配组件
        
        Args:
            component_instance: 组件实例
            config: 配置信息
            
        Returns:
            是否适配成功
        """
        pass


# 便捷函数
def create_architecture_adapter(base_dir: Union[str, Path]) -> ArchitectureAdapter:
    """创建架构适配器的便捷函数"""
    return ArchitectureAdapter(Path(base_dir))


def get_architecture_status(base_dir: Union[str, Path]) -> Dict[str, Any]:
    """快速获取架构状态的便捷函数"""
    adapter = create_architecture_adapter(base_dir)
    return adapter.get_architecture_status() 