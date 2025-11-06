#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
接口规范验证器 v1.0.0
提供接口实现验证、规范检查、一致性验证等功能

作者: LAD Team
创建时间: 2025-08-16
最后更新: 2025-08-16
"""

import json
import logging
import inspect
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Type, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from .interface_compatibility_manager import (
    InterfaceCompatibilityManager, 
    InterfaceSpecification,
    InterfaceInfo,
    CompatibilityResult
)


class ValidationLevel(Enum):
    """验证级别枚举"""
    STRICT = "strict"       # 严格验证
    NORMAL = "normal"       # 正常验证
    RELAXED = "relaxed"     # 宽松验证


class ValidationResult(Enum):
    """验证结果枚举"""
    PASS = "pass"           # 通过
    WARNING = "warning"     # 警告
    ERROR = "error"         # 错误
    FAIL = "fail"           # 失败


@dataclass
class ValidationIssue:
    """验证问题数据类"""
    level: ValidationResult
    category: str
    message: str
    location: str
    suggestion: Optional[str] = None
    code: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['level'] = self.level.value
        return data


@dataclass
class ValidationReport:
    """验证报告数据类"""
    interface_name: str
    validation_time: str
    overall_result: ValidationResult
    total_issues: int
    error_count: int
    warning_count: int
    issues: List[ValidationIssue]
    summary: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['overall_result'] = self.overall_result.value
        data['issues'] = [issue.to_dict() for issue in self.issues]
        return data


class InterfaceValidator:
    """接口规范验证器"""
    
    def __init__(self, compatibility_manager: InterfaceCompatibilityManager):
        """
        初始化接口验证器
        
        Args:
            compatibility_manager: 接口一致性管理器
        """
        self.compatibility_manager = compatibility_manager
        self.logger = logging.getLogger(__name__)
        
        # 验证规则
        self.validation_rules = self._load_validation_rules()
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """加载验证规则"""
        return {
            'method_signature': {
                'enabled': True,
                'strict_typing': False,
                'check_docstrings': True
            },
            'property_validation': {
                'enabled': True,
                'check_types': True,
                'check_readonly': True
            },
            'dependency_check': {
                'enabled': True,
                'strict_dependencies': False
            },
            'naming_convention': {
                'enabled': True,
                'check_pep8': True,
                'allow_legacy': True
            }
        }
    
    def validate_interface_implementation(self, interface_class: Type, 
                                       spec: InterfaceSpecification,
                                       validation_level: ValidationLevel = ValidationLevel.NORMAL) -> ValidationReport:
        """
        验证接口实现
        
        Args:
            interface_class: 接口实现类
            spec: 接口规范
            validation_level: 验证级别
            
        Returns:
            验证报告
        """
        self.logger.info(f"开始验证接口实现: {spec.name} v{spec.version}")
        
        issues = []
        
        # 1. 验证方法实现
        method_issues = self._validate_methods(interface_class, spec, validation_level)
        issues.extend(method_issues)
        
        # 2. 验证属性实现
        property_issues = self._validate_properties(interface_class, spec, validation_level)
        issues.extend(property_issues)
        
        # 3. 验证依赖关系
        dependency_issues = self._validate_dependencies(interface_class, spec, validation_level)
        issues.extend(dependency_issues)
        
        # 4. 验证命名规范
        naming_issues = self._validate_naming_conventions(interface_class, validation_level)
        issues.extend(naming_issues)
        
        # 5. 验证整体一致性
        consistency_issues = self._validate_consistency(interface_class, spec, validation_level)
        issues.extend(consistency_issues)
        
        # 生成报告
        report = self._generate_validation_report(spec.name, issues)
        
        self.logger.info(f"接口验证完成: {spec.name} v{spec.version}, 结果: {report.overall_result.value}")
        return report
    
    def _validate_methods(self, interface_class: Type, spec: InterfaceSpecification, 
                         validation_level: ValidationLevel) -> List[ValidationIssue]:
        """验证方法实现"""
        issues = []
        
        try:
            # 检查必需方法
            for method_name in spec.methods:
                if not hasattr(interface_class, method_name):
                    issues.append(ValidationIssue(
                        level=ValidationResult.ERROR,
                        category="missing_method",
                        message=f"缺少必需方法: {method_name}",
                        location=f"class {interface_class.__name__}",
                        suggestion=f"实现方法 {method_name}",
                        code=f"def {method_name}(self): pass"
                    ))
                    continue
                
                # 获取方法对象
                method = getattr(interface_class, method_name)
                
                # 检查方法签名
                signature_issues = self._validate_method_signature(method, method_name, spec, validation_level)
                issues.extend(signature_issues)
                
                # 检查文档字符串
                if self.validation_rules['method_signature']['check_docstrings']:
                    docstring_issues = self._validate_method_docstring(method, method_name, validation_level)
                    issues.extend(docstring_issues)
            
            # 检查额外方法
            class_methods = set()
            for name, method in inspect.getmembers(interface_class, inspect.isfunction):
                if not name.startswith('_'):
                    class_methods.add(name)
            
            spec_methods = set(spec.methods.keys())
            extra_methods = class_methods - spec_methods
            
            if extra_methods and validation_level == ValidationLevel.STRICT:
                for method_name in extra_methods:
                    issues.append(ValidationIssue(
                        level=ValidationResult.WARNING,
                        category="extra_method",
                        message=f"实现包含规范外的方法: {method_name}",
                        location=f"class {interface_class.__name__}",
                        suggestion="考虑是否应该添加到接口规范中"
                    ))
            
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationResult.ERROR,
                category="validation_error",
                message=f"验证方法时发生异常: {e}",
                location=f"class {interface_class.__name__}",
                suggestion="检查类定义是否正确"
            ))
        
        return issues
    
    def _validate_method_signature(self, method: Callable, method_name: str, 
                                 spec: InterfaceSpecification, validation_level: ValidationLevel) -> List[ValidationIssue]:
        """验证方法签名"""
        issues = []
        
        try:
            # 获取方法签名
            sig = inspect.signature(method)
            
            # 检查参数数量（至少应该有self参数）
            if len(sig.parameters) < 1:
                issues.append(ValidationIssue(
                    level=ValidationResult.ERROR,
                    category="method_signature",
                    message=f"方法 {method_name} 缺少self参数",
                    location=f"method {method_name}",
                    suggestion="添加self参数作为第一个参数"
                ))
            
            # 检查类型注解（如果启用严格类型检查）
            if self.validation_rules['method_signature']['strict_typing']:
                for param_name, param in sig.parameters.items():
                    if param.annotation == inspect.Parameter.empty:
                        issues.append(ValidationIssue(
                            level=ValidationResult.WARNING,
                            category="type_annotation",
                            message=f"参数 {param_name} 缺少类型注解",
                            location=f"method {method_name}",
                            suggestion="添加类型注解以提高代码质量"
                        ))
            
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationResult.ERROR,
                category="signature_analysis",
                message=f"分析方法签名失败: {e}",
                location=f"method {method_name}",
                suggestion="检查方法定义是否正确"
            ))
        
        return issues
    
    def _validate_method_docstring(self, method: Callable, method_name: str, 
                                 validation_level: ValidationLevel) -> List[ValidationIssue]:
        """验证方法文档字符串"""
        issues = []
        
        try:
            docstring = method.__doc__
            
            if not docstring:
                if validation_level == ValidationLevel.STRICT:
                    issues.append(ValidationIssue(
                        level=ValidationResult.WARNING,
                        category="documentation",
                        message=f"方法 {method_name} 缺少文档字符串",
                        location=f"method {method_name}",
                        suggestion="添加文档字符串说明方法功能"
                    ))
            else:
                # 检查文档字符串质量
                docstring_quality_issues = self._validate_docstring_quality(docstring, method_name)
                issues.extend(docstring_quality_issues)
                
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationResult.WARNING,
                category="docstring_validation",
                message=f"验证文档字符串失败: {e}",
                location=f"method {method_name}",
                suggestion="检查文档字符串格式"
            ))
        
        return issues
    
    def _validate_docstring_quality(self, docstring: str, method_name: str) -> List[ValidationIssue]:
        """验证文档字符串质量"""
        issues = []
        
        # 检查文档字符串长度
        if len(docstring.strip()) < 10:
            issues.append(ValidationIssue(
                level=ValidationResult.WARNING,
                category="docstring_quality",
                message=f"方法 {method_name} 的文档字符串过短",
                location=f"method {method_name}",
                suggestion="提供更详细的方法说明"
            ))
        
        # 检查是否包含参数说明
        if 'param' not in docstring.lower() and 'arg' not in docstring.lower():
            issues.append(ValidationIssue(
                level=ValidationResult.WARNING,
                category="docstring_quality",
                message=f"方法 {method_name} 的文档字符串缺少参数说明",
                location=f"method {method_name}",
                suggestion="添加参数说明和返回值说明"
            ))
        
        return issues
    
    def _validate_properties(self, interface_class: Type, spec: InterfaceSpecification, 
                           validation_level: ValidationLevel) -> List[ValidationIssue]:
        """验证属性实现"""
        issues = []
        
        try:
            # 检查必需属性
            for prop_name in spec.properties:
                if not hasattr(interface_class, prop_name):
                    issues.append(ValidationIssue(
                        level=ValidationResult.ERROR,
                        category="missing_property",
                        message=f"缺少必需属性: {prop_name}",
                        location=f"class {interface_class.__name__}",
                        suggestion=f"添加属性 {prop_name}",
                        code=f"{prop_name} = None"
                    ))
                    continue
                
                # 获取属性对象
                prop = getattr(interface_class, prop_name)
                
                # 检查属性类型
                if self.validation_rules['property_validation']['check_types']:
                    type_issues = self._validate_property_type(prop, prop_name, spec, validation_level)
                    issues.extend(type_issues)
                
                # 检查只读属性
                if self.validation_rules['property_validation']['check_readonly']:
                    readonly_issues = self._validate_property_readonly(prop, prop_name, spec, validation_level)
                    issues.extend(readonly_issues)
            
            # 检查额外属性
            class_props = set()
            for name, prop in inspect.getmembers(interface_class, lambda x: not inspect.isfunction(x)):
                if not name.startswith('_'):
                    class_props.add(name)
            
            spec_props = set(spec.properties.keys())
            extra_props = class_props - spec_props
            
            if extra_props and validation_level == ValidationLevel.STRICT:
                for prop_name in extra_props:
                    issues.append(ValidationIssue(
                        level=ValidationResult.WARNING,
                        category="extra_property",
                        message=f"实现包含规范外的属性: {prop_name}",
                        location=f"class {interface_class.__name__}",
                        suggestion="考虑是否应该添加到接口规范中"
                    ))
            
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationResult.ERROR,
                category="property_validation",
                message=f"验证属性时发生异常: {e}",
                location=f"class {interface_class.__name__}",
                suggestion="检查类定义是否正确"
            ))
        
        return issues
    
    def _validate_property_type(self, prop: Any, prop_name: str, spec: InterfaceSpecification, 
                              validation_level: ValidationLevel) -> List[ValidationIssue]:
        """验证属性类型"""
        issues = []
        
        try:
            # 获取规范中定义的属性类型
            spec_prop = spec.properties.get(prop_name, {})
            expected_type = spec_prop.get('type', 'Any')
            
            # 如果规范中定义了具体类型，进行检查
            if expected_type != 'Any' and validation_level == ValidationLevel.STRICT:
                actual_type = type(prop).__name__
                if actual_type != expected_type:
                    issues.append(ValidationIssue(
                        level=ValidationResult.WARNING,
                        category="property_type",
                        message=f"属性 {prop_name} 类型不匹配: 期望 {expected_type}, 实际 {actual_type}",
                        location=f"property {prop_name}",
                        suggestion=f"确保属性类型为 {expected_type}"
                    ))
            
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationResult.WARNING,
                category="type_validation",
                message=f"验证属性类型失败: {e}",
                location=f"property {prop_name}",
                suggestion="检查属性定义"
            ))
        
        return issues
    
    def _validate_property_readonly(self, prop: Any, prop_name: str, spec: InterfaceSpecification, 
                                  validation_level: ValidationLevel) -> List[ValidationIssue]:
        """验证属性只读性"""
        issues = []
        
        try:
            # 获取规范中定义的只读属性
            spec_prop = spec.properties.get(prop_name, {})
            expected_readonly = spec_prop.get('read_only', False)
            
            # 检查属性是否可写
            if expected_readonly:
                # 这里可以添加更复杂的只读检查逻辑
                pass
            
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationResult.WARNING,
                category="readonly_validation",
                message=f"验证属性只读性失败: {e}",
                location=f"property {prop_name}",
                suggestion="检查属性定义"
            ))
        
        return issues
    
    def _validate_dependencies(self, interface_class: Type, spec: InterfaceSpecification, 
                             validation_level: ValidationLevel) -> List[ValidationIssue]:
        """验证依赖关系"""
        issues = []
        
        if not self.validation_rules['dependency_check']['enabled']:
            return issues
        
        try:
            # 分析类的依赖关系
            dependencies = self.compatibility_manager._extract_dependencies(interface_class)
            
            # 检查依赖是否满足
            for dep in dependencies:
                # 这里可以添加更复杂的依赖检查逻辑
                pass
            
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationResult.WARNING,
                category="dependency_validation",
                message=f"验证依赖关系失败: {e}",
                location=f"class {interface_class.__name__}",
                suggestion="检查类的导入和依赖"
            ))
        
        return issues
    
    def _validate_naming_conventions(self, interface_class: Type, 
                                   validation_level: ValidationLevel) -> List[ValidationIssue]:
        """验证命名规范"""
        issues = []
        
        if not self.validation_rules['naming_convention']['enabled']:
            return issues
        
        try:
            # 检查类名
            class_name = interface_class.__name__
            if not class_name[0].isupper():
                issues.append(ValidationIssue(
                    level=ValidationResult.WARNING,
                    category="naming_convention",
                    message=f"类名 {class_name} 不符合PascalCase命名规范",
                    location=f"class {class_name}",
                    suggestion="使用PascalCase命名类"
                ))
            
            # 检查方法名
            for name, method in inspect.getmembers(interface_class, inspect.isfunction):
                if not name.startswith('_'):
                    if not name[0].islower():
                        issues.append(ValidationIssue(
                            level=ValidationResult.WARNING,
                            category="naming_convention",
                            message=f"方法名 {name} 不符合snake_case命名规范",
                            location=f"method {name}",
                            suggestion="使用snake_case命名方法"
                        ))
            
            # 检查属性名
            for name, prop in inspect.getmembers(interface_class, lambda x: not inspect.isfunction(x)):
                if not name.startswith('_'):
                    if not name[0].islower():
                        issues.append(ValidationIssue(
                            level=ValidationResult.WARNING,
                            category="naming_convention",
                            message=f"属性名 {name} 不符合snake_case命名规范",
                            location=f"property {name}",
                            suggestion="使用snake_case命名属性"
                        ))
            
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationResult.WARNING,
                category="naming_validation",
                message=f"验证命名规范失败: {e}",
                location=f"class {interface_class.__name__}",
                suggestion="检查命名规范"
            ))
        
        return issues
    
    def _validate_consistency(self, interface_class: Type, spec: InterfaceSpecification, 
                            validation_level: ValidationLevel) -> List[ValidationIssue]:
        """验证整体一致性"""
        issues = []
        
        try:
            # 检查接口实现的一致性
            # 这里可以添加更复杂的逻辑检查
            
            # 检查是否有未使用的导入
            # 检查是否有死代码
            # 检查是否有循环依赖
            
            # 暂时跳过一致性检查，避免空try块
            pass
            
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationResult.WARNING,
                category="consistency_validation",
                message=f"验证一致性失败: {e}",
                location=f"class {interface_class.__name__}",
                suggestion="检查代码结构"
            ))
        
        return issues
    
    def _generate_validation_report(self, interface_name: str, issues: List[ValidationIssue]) -> ValidationReport:
        """生成验证报告"""
        # 统计问题数量
        error_count = sum(1 for issue in issues if issue.level == ValidationResult.ERROR)
        warning_count = sum(1 for issue in issues if issue.level == ValidationResult.WARNING)
        total_issues = len(issues)
        
        # 确定整体结果
        if error_count > 0:
            overall_result = ValidationResult.FAIL
        elif warning_count > 0:
            overall_result = ValidationResult.WARNING
        else:
            overall_result = ValidationResult.PASS
        
        # 生成摘要
        if overall_result == ValidationResult.PASS:
            summary = f"接口 {interface_name} 验证通过，无问题"
        elif overall_result == ValidationResult.WARNING:
            summary = f"接口 {interface_name} 验证通过，但有 {warning_count} 个警告"
        elif overall_result == ValidationResult.FAIL:
            summary = f"接口 {interface_name} 验证失败，有 {error_count} 个错误"
        else:
            summary = f"接口 {interface_name} 验证结果未知"
        
        return ValidationReport(
            interface_name=interface_name,
            validation_time=datetime.now().isoformat(),
            overall_result=overall_result,
            total_issues=total_issues,
            error_count=error_count,
            warning_count=warning_count,
            issues=issues,
            summary=summary
        )
    
    def generate_validation_summary(self, reports: List[ValidationReport]) -> str:
        """生成验证摘要报告"""
        summary = []
        summary.append("# 接口验证摘要报告")
        summary.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append("")
        
        # 总体统计
        total_interfaces = len(reports)
        passed_interfaces = sum(1 for r in reports if r.overall_result == ValidationResult.PASS)
        warning_interfaces = sum(1 for r in reports if r.overall_result == ValidationResult.WARNING)
        failed_interfaces = sum(1 for r in reports if r.overall_result == ValidationResult.FAIL)
        
        summary.append("## 总体统计")
        summary.append(f"- 总接口数量: {total_interfaces}")
        summary.append(f"- 验证通过: {passed_interfaces}")
        summary.append(f"- 有警告: {warning_interfaces}")
        summary.append(f"- 验证失败: {failed_interfaces}")
        summary.append("")
        
        # 详细结果
        summary.append("## 详细结果")
        for report in reports:
            status_emoji = {
                ValidationResult.PASS: "✅",
                ValidationResult.WARNING: "⚠️",
                ValidationResult.ERROR: "❌",
                ValidationResult.FAIL: "💥"
            }
            
            summary.append(f"### {status_emoji[report.overall_result]} {report.interface_name}")
            summary.append(f"- 结果: {report.overall_result.value}")
            summary.append(f"- 问题数量: {report.total_issues}")
            summary.append(f"- 错误: {report.error_count}, 警告: {report.warning_count}")
            summary.append(f"- 摘要: {report.summary}")
            summary.append("")
        
        return "\n".join(summary)


# 便捷函数
def create_interface_validator(compatibility_manager: InterfaceCompatibilityManager) -> InterfaceValidator:
    """创建接口验证器的便捷函数"""
    return InterfaceValidator(compatibility_manager)


def validate_interface(interface_class: Type, spec: InterfaceSpecification, 
                      compatibility_manager: InterfaceCompatibilityManager,
                      validation_level: ValidationLevel = ValidationLevel.NORMAL) -> ValidationReport:
    """快速验证接口的便捷函数"""
    validator = create_interface_validator(compatibility_manager)
    return validator.validate_interface_implementation(interface_class, spec, validation_level) 