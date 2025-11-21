#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
接口一致性管理器 v1.0.0
管理接口版本、兼容性验证、接口规范等

作者: LAD Team
创建时间: 2025-08-16
最后更新: 2025-08-16
"""

import json
import logging
import inspect
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable, Type, Set
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod
import builtins

class InterfaceVersion(Enum):
    """接口版本枚举"""
    V1_0 = "1.0"
    V1_1 = "1.1"
    V1_2 = "1.2"
    V2_0 = "2.0"
    LATEST = "2.0"


class CompatibilityLevel(Enum):
    """兼容性级别枚举"""
    FULL = "full"           # 完全兼容
    PARTIAL = "partial"     # 部分兼容
    BREAKING = "breaking"   # 破坏性变更
    UNKNOWN = "unknown"     # 未知


@dataclass
class InterfaceInfo:
    """接口信息数据类"""
    name: str
    version: str
    module: str
    class_name: str
    methods: List[str]
    properties: List[str]
    dependencies: List[str]
    deprecated: bool = False
    replacement: Optional[str] = None
    documentation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


@dataclass
class CompatibilityResult:
    """兼容性检查结果数据类"""
    interface_name: str
    source_version: str
    target_version: str
    compatibility_level: CompatibilityLevel
    breaking_changes: List[str]
    new_features: List[str]
    deprecated_features: List[str]
    migration_guide: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['compatibility_level'] = self.compatibility_level.value
        return data


class InterfaceSpecification:
    """接口规范定义"""
    
    def __init__(self, name: str, version: str):
        """
        初始化接口规范
        
        Args:
            name: 接口名称
            version: 接口版本
        """
        self.name = name
        self.version = version
        self.methods: Dict[str, Dict[str, Any]] = {}
        self.properties: Dict[str, Dict[str, Any]] = {}
        self.constraints: Dict[str, Any] = {}
        self.examples: List[str] = []
    
    def add_method(self, name: str, signature: str, description: str, 
                   parameters: List[Dict[str, Any]] = None, 
                   return_type: str = None, 
                   exceptions: List[str] = None):
        """
        添加方法定义
        
        Args:
            name: 方法名称
            signature: 方法签名
            description: 方法描述
            parameters: 参数列表
            return_type: 返回类型
            exceptions: 异常列表
        """
        self.methods[name] = {
            'signature': signature,
            'description': description,
            'parameters': parameters or [],
            'return_type': return_type,
            'exceptions': exceptions or []
        }
    
    def add_property(self, name: str, type: str, description: str, 
                     read_only: bool = False, default_value: Any = None):
        """
        添加属性定义
        
        Args:
            name: 属性名称
            type: 属性类型
            description: 属性描述
            read_only: 是否只读
            default_value: 默认值
        """
        self.properties[name] = {
            'type': type,
            'description': description,
            'read_only': read_only,
            'default_value': default_value
        }
    
    def add_constraint(self, name: str, constraint_type: str, value: Any, description: str):
        """
        添加约束条件
        
        Args:
            name: 约束名称
            constraint_type: 约束类型
            value: 约束值
            description: 约束描述
        """
        self.constraints[name] = {
            'type': constraint_type,
            'value': value,
            'description': description
        }
    
    def add_example(self, example: str):
        """添加使用示例"""
        self.examples.append(example)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'name': self.name,
            'version': self.version,
            'methods': self.methods,
            'properties': self.properties,
            'constraints': self.constraints,
            'examples': self.examples
        }


class InterfaceCompatibilityManager:
    """接口一致性管理器"""
    
    def __init__(self, base_dir: Union[str, Path]):
        """
        初始化接口一致性管理器
        
        Args:
            base_dir: 基础目录路径
        """
        self.base_dir = Path(base_dir)
        self.specifications_dir = self.base_dir / "interface_specs"
        self.compatibility_dir = self.base_dir / "compatibility"
        
        # 确保目录存在
        self.specifications_dir.mkdir(parents=True, exist_ok=True)
        self.compatibility_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 接口规范缓存
        self.interface_specs: Dict[str, Dict[str, InterfaceSpecification]] = {}
        
        # 兼容性规则
        self.compatibility_rules: Dict[str, Dict[str, Any]] = {}
        
        # 加载现有规范
        self._load_interface_specifications()
        self._load_compatibility_rules()
    
    def _load_interface_specifications(self):
        """加载接口规范"""
        try:
            spec_files = list(self.specifications_dir.glob("*.json"))
            for spec_file in spec_files:
                try:
                    with builtins.open(spec_file, 'r', encoding='utf-8') as f:
                        spec_data = json.load(f)
                    
                    interface_name = spec_data.get('name')
                    version = spec_data.get('version')
                    
                    if interface_name and version:
                        if interface_name not in self.interface_specs:
                            self.interface_specs[interface_name] = {}
                        
                        # 创建规范对象
                        spec = InterfaceSpecification(interface_name, version)
                        spec.methods = spec_data.get('methods', {})
                        spec.properties = spec_data.get('properties', {})
                        spec.constraints = spec_data.get('constraints', {})
                        spec.examples = spec_data.get('examples', [])
                        
                        self.interface_specs[interface_name][version] = spec
                        
                except Exception as e:
                    self.logger.warning(f"加载接口规范失败 {spec_file}: {e}")
            
            self.logger.info(f"加载了 {len(self.interface_specs)} 个接口的规范")
            
        except Exception as e:
            self.logger.error(f"加载接口规范时发生异常: {e}")
    
    def _load_compatibility_rules(self):
        """加载兼容性规则"""
        try:
            rules_file = self.compatibility_dir / "compatibility_rules.json"
            if rules_file.exists():
                with builtins.open(rules_file, 'r', encoding='utf-8') as f:
                    self.compatibility_rules = json.load(f)
                self.logger.info("兼容性规则加载完成")
            else:
                self._create_default_compatibility_rules()
                
        except Exception as e:
            self.logger.error(f"加载兼容性规则时发生异常: {e}")
            self._create_default_compatibility_rules()
    
    def _create_default_compatibility_rules(self):
        """创建默认兼容性规则"""
        self.compatibility_rules = {
            'version_compatibility': {
                '1.0': ['1.1', '1.2'],
                '1.1': ['1.2'],
                '1.2': ['2.0'],
                '2.0': []
            },
            'breaking_changes': {
                '2.0': ['1.0', '1.1', '1.2']
            },
            'deprecation_policy': {
                'grace_period_versions': 2,
                'deprecation_notice_versions': 1
            }
        }
        
        # 保存默认规则
        self._save_compatibility_rules()
    
    def _save_compatibility_rules(self):
        """保存兼容性规则"""
        try:
            rules_file = self.compatibility_dir / "compatibility_rules.json"
            with builtins.open(rules_file, 'w', encoding='utf-8') as f:
                json.dump(self.compatibility_rules, f, indent=2, ensure_ascii=False)
            
            self.logger.info("兼容性规则保存完成")
            
        except Exception as e:
            self.logger.error(f"保存兼容性规则失败: {e}")
    
    def analyze_interface(self, interface_class: Type, interface_name: str = None) -> InterfaceInfo:
        """
        分析接口类
        
        Args:
            interface_class: 接口类
            interface_name: 接口名称，默认为类名
            
        Returns:
            接口信息对象
        """
        if interface_name is None:
            interface_name = interface_class.__name__
        
        try:
            # 获取类信息
            module_name = interface_class.__module__
            class_name = interface_class.__name__
            
            # 获取方法列表
            methods = []
            for name, method in inspect.getmembers(interface_class, inspect.isfunction):
                if not name.startswith('_'):
                    methods.append(name)
            
            # 获取属性列表
            properties = []
            for name, prop in inspect.getmembers(interface_class, lambda x: not inspect.isfunction(x)):
                if not name.startswith('_'):
                    properties.append(name)
            
            # 获取依赖关系
            dependencies = self._extract_dependencies(interface_class)
            
            # 创建接口信息
            interface_info = InterfaceInfo(
                name=interface_name,
                version=InterfaceVersion.LATEST.value,
                module=module_name,
                class_name=class_name,
                methods=methods,
                properties=properties,
                dependencies=dependencies
            )
            
            self.logger.info(f"接口 {interface_name} 分析完成")
            return interface_info
            
        except Exception as e:
            self.logger.error(f"分析接口 {interface_name} 时发生异常: {e}")
            raise
    
    def _extract_dependencies(self, interface_class: Type) -> List[str]:
        """提取接口依赖关系"""
        dependencies = []
        
        try:
            # 检查基类
            for base in interface_class.__bases__:
                if base != object:
                    dependencies.append(base.__name__)
            
            # 检查类型注解
            annotations = getattr(interface_class, '__annotations__', {})
            for name, annotation in annotations.items():
                if hasattr(annotation, '__name__'):
                    dependencies.append(annotation.__name__)
            
            # 检查方法参数
            for name, method in inspect.getmembers(interface_class, inspect.isfunction):
                if not name.startswith('_'):
                    sig = inspect.signature(method)
                    for param_name, param in sig.parameters.items():
                        if param.annotation != inspect.Parameter.empty:
                            if hasattr(param.annotation, '__name__'):
                                dependencies.append(param.annotation.__name__)
            
        except Exception as e:
            self.logger.debug(f"提取依赖关系时发生异常: {e}")
        
        return list(set(dependencies))
    
    def create_interface_specification(self, interface_info: InterfaceInfo, 
                                     version: str = None) -> InterfaceSpecification:
        """
        创建接口规范
        
        Args:
            interface_info: 接口信息
            version: 版本号，默认为接口信息中的版本
            
        Returns:
            接口规范对象
        """
        if version is None:
            version = interface_info.version
        
        # 创建规范
        spec = InterfaceSpecification(interface_info.name, version)
        
        # 添加方法定义
        for method_name in interface_info.methods:
            # 这里可以根据需要添加更详细的方法信息
            spec.add_method(
                name=method_name,
                signature=f"{method_name}()",
                description=f"方法 {method_name}",
                parameters=[],
                return_type="Any"
            )
        
        # 添加属性定义
        for prop_name in interface_info.properties:
            spec.add_property(
                name=prop_name,
                type="Any",
                description=f"属性 {prop_name}",
                read_only=False
            )
        
        # 添加约束条件
        spec.add_constraint(
            name="version_compatibility",
            constraint_type="version_range",
            value=f">={version}",
            description=f"要求版本 {version} 或更高"
        )
        
        # 添加使用示例
        spec.add_example(f"# 使用 {interface_info.name} 接口\n"
                        f"from {interface_info.module} import {interface_info.class_name}\n"
                        f"instance = {interface_info.class_name}()")
        
        return spec
    
    def save_interface_specification(self, spec: InterfaceSpecification):
        """
        保存接口规范
        
        Args:
            spec: 接口规范对象
        """
        try:
            # 确保接口目录存在
            interface_dir = self.specifications_dir / spec.name
            interface_dir.mkdir(exist_ok=True)
            
            # 保存规范文件
            spec_file = interface_dir / f"{spec.version}.json"
            with builtins.open(spec_file, 'w', encoding='utf-8') as f:
                json.dump(spec.to_dict(), f, indent=2, ensure_ascii=False)
            
            # 更新缓存
            if spec.name not in self.interface_specs:
                self.interface_specs[spec.name] = {}
            self.interface_specs[spec.name][spec.version] = spec
            
            self.logger.info(f"接口规范 {spec.name} v{spec.version} 保存成功")
            
        except Exception as e:
            self.logger.error(f"保存接口规范失败: {e}")
            raise
    
    def check_compatibility(self, source_version: str, target_version: str, 
                          interface_name: str) -> CompatibilityResult:
        """
        检查接口兼容性
        
        Args:
            source_version: 源版本
            target_version: 目标版本
            interface_name: 接口名称
            
        Returns:
            兼容性检查结果
        """
        try:
            # 获取版本规范
            source_spec = self.interface_specs.get(interface_name, {}).get(source_version)
            target_spec = self.interface_specs.get(interface_name, {}).get(target_version)
            
            if not source_spec or not target_spec:
                return CompatibilityResult(
                    interface_name=interface_name,
                    source_version=source_version,
                    target_version=target_version,
                    compatibility_level=CompatibilityLevel.UNKNOWN,
                    breaking_changes=["无法获取版本规范"],
                    new_features=[],
                    deprecated_features=[]
                )
            
            # 分析兼容性
            breaking_changes = []
            new_features = []
            deprecated_features = []
            
            # 检查方法变更
            source_methods = set(source_spec.methods.keys())
            target_methods = set(target_spec.methods.keys())
            
            # 移除的方法
            removed_methods = source_methods - target_methods
            for method in removed_methods:
                breaking_changes.append(f"方法 {method} 已被移除")
            
            # 新增的方法
            added_methods = target_methods - source_methods
            for method in added_methods:
                new_features.append(f"新增方法 {method}")
            
            # 检查属性变更
            source_props = set(source_spec.properties.keys())
            target_props = set(target_spec.properties.keys())
            
            # 移除的属性
            removed_props = source_props - target_props
            for prop in removed_props:
                breaking_changes.append(f"属性 {prop} 已被移除")
            
            # 新增的属性
            added_props = target_props - source_props
            for prop in added_props:
                new_features.append(f"新增属性 {prop}")
            
            # 确定兼容性级别
            if breaking_changes:
                compatibility_level = CompatibilityLevel.BREAKING
            elif new_features:
                compatibility_level = CompatibilityLevel.PARTIAL
            else:
                compatibility_level = CompatibilityLevel.FULL
            
            # 创建迁移指南
            migration_guide = self._create_migration_guide(
                interface_name, source_version, target_version,
                breaking_changes, new_features, deprecated_features
            )
            
            result = CompatibilityResult(
                interface_name=interface_name,
                source_version=source_version,
                target_version=target_version,
                compatibility_level=compatibility_level,
                breaking_changes=breaking_changes,
                new_features=new_features,
                deprecated_features=deprecated_features,
                migration_guide=migration_guide
            )
            
            self.logger.info(f"兼容性检查完成: {interface_name} {source_version} -> {target_version}")
            return result
            
        except Exception as e:
            self.logger.error(f"检查兼容性时发生异常: {e}")
            raise
    
    def _create_migration_guide(self, interface_name: str, source_version: str, 
                               target_version: str, breaking_changes: List[str],
                               new_features: List[str], deprecated_features: List[str]) -> str:
        """创建迁移指南"""
        guide = []
        guide.append(f"# {interface_name} 接口迁移指南")
        guide.append(f"## 版本变更: {source_version} -> {target_version}")
        guide.append("")
        
        if breaking_changes:
            guide.append("## 破坏性变更")
            for change in breaking_changes:
                guide.append(f"- {change}")
            guide.append("")
        
        if new_features:
            guide.append("## 新功能")
            for feature in new_features:
                guide.append(f"- {feature}")
            guide.append("")
        
        if deprecated_features:
            guide.append("## 已弃用功能")
            for feature in deprecated_features:
                guide.append(f"- {feature}")
            guide.append("")
        
        guide.append("## 迁移步骤")
        guide.append("1. 备份现有代码")
        guide.append("2. 处理破坏性变更")
        guide.append("3. 测试新功能")
        guide.append("4. 更新文档")
        
        return "\n".join(guide)
    
    def validate_interface_implementation(self, interface_class: Type, 
                                       spec: InterfaceSpecification) -> Dict[str, Any]:
        """
        验证接口实现
        
        Args:
            interface_class: 接口实现类
            spec: 接口规范
            
        Returns:
            验证结果
        """
        validation_result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'missing_methods': [],
            'missing_properties': [],
            'extra_methods': [],
            'extra_properties': []
        }
        
        try:
            # 检查必需方法
            for method_name in spec.methods:
                if not hasattr(interface_class, method_name):
                    validation_result['missing_methods'].append(method_name)
                    validation_result['errors'].append(f"缺少必需方法: {method_name}")
            
            # 检查必需属性
            for prop_name in spec.properties:
                if not hasattr(interface_class, prop_name):
                    validation_result['missing_properties'].append(prop_name)
                    validation_result['errors'].append(f"缺少必需属性: {prop_name}")
            
            # 检查额外方法
            class_methods = set()
            for name, method in inspect.getmembers(interface_class, inspect.isfunction):
                if not name.startswith('_'):
                    class_methods.add(name)
            
            spec_methods = set(spec.methods.keys())
            extra_methods = class_methods - spec_methods
            validation_result['extra_methods'] = list(extra_methods)
            
            # 检查额外属性
            class_props = set()
            for name, prop in inspect.getmembers(interface_class, lambda x: not inspect.isfunction(x)):
                if not name.startswith('_'):
                    class_props.add(name)
            
            spec_props = set(spec.properties.keys())
            extra_props = class_props - spec_props
            validation_result['extra_properties'] = list(extra_props)
            
            # 确定验证结果
            if not validation_result['errors']:
                validation_result['valid'] = True
                if validation_result['extra_methods'] or validation_result['extra_properties']:
                    validation_result['warnings'].append("实现包含规范外的额外功能")
            
            self.logger.info(f"接口实现验证完成: {spec.name} v{spec.version}")
            
        except Exception as e:
            validation_result['errors'].append(f"验证过程中发生异常: {e}")
            self.logger.error(f"验证接口实现时发生异常: {e}")
        
        return validation_result
    
    def generate_interface_report(self, interface_name: str = None) -> str:
        """生成接口报告"""
        if interface_name:
            # 生成单个接口报告
            return self._generate_single_interface_report(interface_name)
        else:
            # 生成总体报告
            return self._generate_overall_interface_report()
    
    def _generate_single_interface_report(self, interface_name: str) -> str:
        """生成单个接口报告"""
        if interface_name not in self.interface_specs:
            return f"# 接口报告\n\n接口 {interface_name} 不存在"
        
        specs = self.interface_specs[interface_name]
        
        report = []
        report.append(f"# {interface_name} 接口报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("## 版本概览")
        for version in sorted(specs.keys()):
            spec = specs[version]
            report.append(f"### 版本 {version}")
            report.append(f"- 方法数量: {len(spec.methods)}")
            report.append(f"- 属性数量: {len(spec.properties)}")
            report.append(f"- 约束条件: {len(spec.constraints)}")
            report.append("")
        
        return "\n".join(report)
    
    def _generate_overall_interface_report(self) -> str:
        """生成总体接口报告"""
        report = []
        report.append("# 接口一致性管理总体报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("## 接口统计")
        report.append(f"- 总接口数量: {len(self.interface_specs)}")
        
        total_versions = sum(len(specs) for specs in self.interface_specs.values())
        report.append(f"- 总版本数量: {total_versions}")
        report.append("")
        
        report.append("## 接口列表")
        for interface_name, specs in self.interface_specs.items():
            versions = sorted(specs.keys())
            report.append(f"### {interface_name}")
            report.append(f"- 版本: {', '.join(versions)}")
            report.append(f"- 最新版本: {versions[-1] if versions else '无'}")
            report.append("")
        
        return "\n".join(report)


# 便捷函数
def create_interface_compatibility_manager(base_dir: Union[str, Path]) -> InterfaceCompatibilityManager:
    """创建接口一致性管理器的便捷函数"""
    return InterfaceCompatibilityManager(Path(base_dir))


def analyze_interface(interface_class: Type, base_dir: Union[str, Path], 
                     interface_name: str = None) -> InterfaceInfo:
    """快速分析接口的便捷函数"""
    manager = create_interface_compatibility_manager(base_dir)
    return manager.analyze_interface(interface_class, interface_name)


def check_interface_compatibility(source_version: str, target_version: str, 
                                interface_name: str, base_dir: Union[str, Path]) -> CompatibilityResult:
    """快速检查接口兼容性的便捷函数"""
    manager = create_interface_compatibility_manager(base_dir)
    return manager.check_compatibility(source_version, target_version, interface_name) 