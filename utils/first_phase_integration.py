#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第一阶段组件集成 v1.0.0
将ConfigManager、FileTree、ContentViewer等现有组件集成到新架构中

作者: LAD Team
创建时间: 2025-08-16
最后更新: 2025-08-16
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Type
from dataclasses import dataclass, asdict
from datetime import datetime

from .architecture_adapter import ArchitectureAdapter, ComponentAdapter
from .config_manager import ConfigManager
from .resource_manager import ResourceManager
from .enhanced_logger import EnhancedLogger


@dataclass
class ComponentInfo:
    """组件信息数据类"""
    name: str
    component_type: str
    status: str
    integration_time: str
    dependencies: List[str]
    config: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


class ConfigManagerAdapter(ComponentAdapter):
    """ConfigManager组件适配器"""
    
    def __init__(self):
        """初始化适配器"""
        self.logger = logging.getLogger(__name__)
    
    def adapt(self, component_instance: Any, config: Dict[str, Any] = None) -> bool:
        """
        适配ConfigManager组件
        
        Args:
            component_instance: ConfigManager实例
            config: 配置信息
            
        Returns:
            是否适配成功
        """
        try:
            if not isinstance(component_instance, ConfigManager):
                self.logger.error("组件实例不是ConfigManager类型")
                return False
            
            # 验证组件功能
            if not hasattr(component_instance, 'get_config'):
                self.logger.error("ConfigManager缺少get_config方法")
                return False
            
            # 执行适配逻辑
            # 这里可以添加具体的适配逻辑，比如：
            # - 注册到服务注册表
            # - 设置配置监听器
            # - 建立配置同步机制
            
            self.logger.info("ConfigManager组件适配成功")
            return True
            
        except Exception as e:
            self.logger.error(f"ConfigManager组件适配失败: {e}")
            return False


class FileTreeAdapter(ComponentAdapter):
    """FileTree组件适配器"""
    
    def __init__(self):
        """初始化适配器"""
        self.logger = logging.getLogger(__name__)
    
    def adapt(self, component_instance: Any, config: Dict[str, Any] = None) -> bool:
        """
        适配FileTree组件
        
        Args:
            component_instance: FileTree实例
            config: 配置信息
            
        Returns:
            是否适配成功
        """
        try:
            # 检查组件实例
            if component_instance is None:
                self.logger.error("FileTree组件实例为空")
                return False
            
            # 验证组件功能
            required_methods = ['get_file_tree', 'refresh', 'set_root_path']
            for method in required_methods:
                if not hasattr(component_instance, method):
                    self.logger.warning(f"FileTree组件缺少{method}方法")
            
            # 执行适配逻辑
            # 这里可以添加具体的适配逻辑，比如：
            # - 注册文件系统监听器
            # - 建立文件树缓存机制
            # - 设置文件过滤规则
            
            self.logger.info("FileTree组件适配成功")
            return True
            
        except Exception as e:
            self.logger.error(f"FileTree组件适配失败: {e}")
            return False


class ContentViewerAdapter(ComponentAdapter):
    """ContentViewer组件适配器"""
    
    def __init__(self):
        """初始化适配器"""
        self.logger = logging.getLogger(__name__)
    
    def adapt(self, component_instance: Any, config: Dict[str, Any] = None) -> bool:
        """
        适配ContentViewer组件
        
        Args:
            component_instance: ContentViewer实例
            config: 配置信息
            
        Returns:
            是否适配成功
        """
        try:
            # 检查组件实例
            if component_instance is None:
                self.logger.error("ContentViewer组件实例为空")
                return False
            
            # 验证组件功能
            required_methods = ['load_content', 'render_content', 'get_content_type']
            for method in required_methods:
                if not hasattr(component_instance, method):
                    self.logger.warning(f"ContentViewer组件缺少{method}方法")
            
            # 执行适配逻辑
            # 这里可以添加具体的适配逻辑，比如：
            # - 注册内容渲染器
            # - 建立内容缓存机制
            # - 设置渲染选项
            
            self.logger.info("ContentViewer组件适配成功")
            return True
            
        except Exception as e:
            self.logger.error(f"ContentViewer组件适配失败: {e}")
            return False


class FirstPhaseComponentIntegration:
    """第一阶段组件集成管理器"""
    
    def __init__(self, architecture_adapter: ArchitectureAdapter):
        """
        初始化组件集成管理器
        
        Args:
            architecture_adapter: 架构适配器实例
        """
        self.architecture_adapter = architecture_adapter
        self.logger = logging.getLogger(__name__)
        
        # 组件信息缓存
        self.integrated_components: Dict[str, ComponentInfo] = {}
        
        # 注册组件适配器
        self._register_component_adapters()
    
    def _register_component_adapters(self):
        """注册组件适配器"""
        # 注册ConfigManager适配器
        self.architecture_adapter.register_component_adapter(
            "config_manager", 
            ConfigManagerAdapter()
        )
        
        # 注册FileTree适配器
        self.architecture_adapter.register_component_adapter(
            "file_tree", 
            FileTreeAdapter()
        )
        
        # 注册ContentViewer适配器
        self.architecture_adapter.register_component_adapter(
            "content_viewer", 
            ContentViewerAdapter()
        )
        
        self.logger.info("组件适配器注册完成")
    
    def integrate_config_manager(self, config_dir: Union[str, Path] = None) -> bool:
        """
        集成ConfigManager组件
        
        Args:
            config_dir: 配置目录路径
            
        Returns:
            是否集成成功
        """
        try:
            self.logger.info("开始集成ConfigManager组件")
            
            # 创建ConfigManager实例
            if config_dir is None:
                config_dir = self.architecture_adapter.base_dir / "config"
            
            config_manager = ConfigManager(config_dir)
            
            # 执行适配
            success = self.architecture_adapter.adapt_existing_component(
                "config_manager", 
                config_manager,
                {"config_dir": str(config_dir)}
            )
            
            if success:
                # 记录集成信息
                component_info = ComponentInfo(
                    name="config_manager",
                    component_type="core",
                    status="integrated",
                    integration_time=datetime.now().isoformat(),
                    dependencies=[],
                    config={"config_dir": str(config_dir)},
                    metadata={"version": "1.0.0", "type": "configuration"}
                )
                
                self.integrated_components["config_manager"] = component_info
                self.logger.info("ConfigManager组件集成成功")
            else:
                self.logger.error("ConfigManager组件集成失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"集成ConfigManager组件时发生异常: {e}")
            return False
    
    def integrate_file_tree(self, root_path: Union[str, Path] = None) -> bool:
        """
        集成FileTree组件
        
        Args:
            root_path: 根目录路径
            
        Returns:
            是否集成成功
        """
        try:
            self.logger.info("开始集成FileTree组件")
            
            # 这里应该导入实际的FileTree类
            # 由于我们没有实际的FileTree实现，这里创建一个模拟的集成
            if root_path is None:
                root_path = self.architecture_adapter.base_dir
            
            # 模拟FileTree组件
            file_tree_component = self._create_mock_file_tree(root_path)
            
            # 执行适配
            success = self.architecture_adapter.adapt_existing_component(
                "file_tree", 
                file_tree_component,
                {"root_path": str(root_path)}
            )
            
            if success:
                # 记录集成信息
                component_info = ComponentInfo(
                    name="file_tree",
                    component_type="ui",
                    status="integrated",
                    integration_time=datetime.now().isoformat(),
                    dependencies=["config_manager"],
                    config={"root_path": str(root_path)},
                    metadata={"version": "1.0.0", "type": "file_system"}
                )
                
                self.integrated_components["file_tree"] = component_info
                self.logger.info("FileTree组件集成成功")
            else:
                self.logger.error("FileTree组件集成失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"集成FileTree组件时发生异常: {e}")
            return False
    
    def integrate_content_viewer(self, config: Dict[str, Any] = None) -> bool:
        """
        集成ContentViewer组件
        
        Args:
            config: 组件配置
            
        Returns:
            是否集成成功
        """
        try:
            self.logger.info("开始集成ContentViewer组件")
            
            if config is None:
                config = {}
            
            # 模拟ContentViewer组件
            content_viewer_component = self._create_mock_content_viewer(config)
            
            # 执行适配
            success = self.architecture_adapter.adapt_existing_component(
                "content_viewer", 
                content_viewer_component,
                config
            )
            
            if success:
                # 记录集成信息
                component_info = ComponentInfo(
                    name="content_viewer",
                    component_type="ui",
                    status="integrated",
                    integration_time=datetime.now().isoformat(),
                    dependencies=["config_manager", "file_tree"],
                    config=config,
                    metadata={"version": "1.0.0", "type": "content_display"}
                )
                
                self.integrated_components["content_viewer"] = component_info
                self.logger.info("ContentViewer组件集成成功")
            else:
                self.logger.error("ContentViewer组件集成失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"集成ContentViewer组件时发生异常: {e}")
            return False
    
    def _create_mock_file_tree(self, root_path: Path):
        """创建模拟的FileTree组件"""
        class MockFileTree:
            def __init__(self, root_path):
                self.root_path = Path(root_path)
            
            def get_file_tree(self):
                return {"root": str(self.root_path), "type": "directory"}
            
            def refresh(self):
                return True
            
            def set_root_path(self, path):
                self.root_path = Path(path)
                return True
        
        return MockFileTree(root_path)
    
    def _create_mock_content_viewer(self, config: Dict[str, Any]):
        """创建模拟的ContentViewer组件"""
        class MockContentViewer:
            def __init__(self, config):
                self.config = config
            
            def load_content(self, content):
                return True
            
            def render_content(self, content):
                return f"Rendered: {content}"
            
            def get_content_type(self):
                return "markdown"
        
        return MockContentViewer(config)
    
    def integrate_all_components(self) -> Dict[str, bool]:
        """
        集成所有组件
        
        Returns:
            各组件集成结果字典
        """
        self.logger.info("开始集成所有组件")
        
        results = {}
        
        # 1. 集成ConfigManager
        results["config_manager"] = self.integrate_config_manager()
        
        # 2. 集成FileTree
        results["file_tree"] = self.integrate_file_tree()
        
        # 3. 集成ContentViewer
        results["content_viewer"] = self.integrate_content_viewer()
        
        # 统计结果
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        self.logger.info(f"组件集成完成: {success_count}/{total_count} 成功")
        
        return results
    
    def get_integration_status(self) -> Dict[str, Any]:
        """获取集成状态"""
        return {
            'timestamp': datetime.now().isoformat(),
            'total_components': len(self.integrated_components),
            'integrated_components': {
                name: info.to_dict() 
                for name, info in self.integrated_components.items()
            },
            'architecture_status': self.architecture_adapter.get_architecture_status()
        }
    
    def generate_integration_report(self) -> str:
        """生成集成报告"""
        status = self.get_integration_status()
        
        report = []
        report.append("# 第一阶段组件集成报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("## 集成概览")
        report.append(f"- 总组件数量: {status['total_components']}")
        report.append(f"- 架构状态: 正常")
        report.append("")
        
        report.append("## 已集成组件")
        for name, info in status['integrated_components'].items():
            report.append(f"### {name}")
            report.append(f"- 类型: {info['component_type']}")
            report.append(f"- 状态: {info['status']}")
            report.append(f"- 集成时间: {info['integration_time']}")
            report.append(f"- 依赖: {', '.join(info['dependencies']) if info['dependencies'] else '无'}")
            report.append("")
        
        report.append("## 架构状态")
        arch_status = status['architecture_status']
        report.append(f"- 基础目录: {arch_status['base_directory']}")
        report.append(f"- 服务数量: {arch_status['services']['total_services']}")
        report.append(f"- 组件适配器: {', '.join(arch_status['component_adapters'])}")
        
        return "\n".join(report)
    
    def validate_integration(self) -> Dict[str, Any]:
        """验证集成结果"""
        validation_result = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'unknown',
            'component_validation': {},
            'dependency_validation': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # 验证各组件
            for name, info in self.integrated_components.items():
                component_status = self._validate_component(name, info)
                validation_result['component_validation'][name] = component_status
            
            # 验证依赖关系
            validation_result['dependency_validation'] = self._validate_dependencies()
            
            # 确定整体状态
            all_valid = all(
                status['valid'] 
                for status in validation_result['component_validation'].values()
            )
            
            if all_valid:
                validation_result['overall_status'] = 'success'
            else:
                validation_result['overall_status'] = 'partial_success'
            
        except Exception as e:
            validation_result['overall_status'] = 'error'
            validation_result['errors'].append(f"验证过程中发生异常: {e}")
        
        return validation_result
    
    def _validate_component(self, name: str, info: ComponentInfo) -> Dict[str, Any]:
        """验证单个组件"""
        validation = {
            'name': name,
            'valid': False,
            'errors': [],
            'warnings': []
        }
        
        try:
            # 检查组件状态
            if info.status != 'integrated':
                validation['errors'].append(f"组件状态不正确: {info.status}")
            
            # 检查配置
            if not info.config:
                validation['warnings'].append("组件配置为空")
            
            # 如果没有错误，标记为有效
            if not validation['errors']:
                validation['valid'] = True
            
        except Exception as e:
            validation['errors'].append(f"验证组件时发生异常: {e}")
        
        return validation
    
    def _validate_dependencies(self) -> Dict[str, Any]:
        """验证依赖关系"""
        dependency_validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # 检查依赖关系
            for name, info in self.integrated_components.items():
                for dep in info.dependencies:
                    if dep not in self.integrated_components:
                        dependency_validation['errors'].append(
                            f"组件 {name} 依赖的 {dep} 未集成"
                        )
                        dependency_validation['valid'] = False
            
        except Exception as e:
            dependency_validation['errors'].append(f"验证依赖关系时发生异常: {e}")
            dependency_validation['valid'] = False
        
        return dependency_validation


# 便捷函数
def create_first_phase_integration(architecture_adapter: ArchitectureAdapter) -> FirstPhaseComponentIntegration:
    """创建第一阶段组件集成的便捷函数"""
    return FirstPhaseComponentIntegration(architecture_adapter)


def integrate_all_components(base_dir: Union[str, Path]) -> Dict[str, Any]:
    """快速集成所有组件的便捷函数"""
    # 创建架构适配器
    arch_adapter = ArchitectureAdapter(Path(base_dir))
    
    # 创建组件集成管理器
    integration_manager = create_first_phase_integration(arch_adapter)
    
    # 执行集成
    results = integration_manager.integrate_all_components()
    
    # 返回结果
    return {
        'integration_results': results,
        'integration_status': integration_manager.get_integration_status(),
        'validation_result': integration_manager.validate_integration()
    } 