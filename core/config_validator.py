#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置验证器模块 v1.0.0（简化版本）
LAD-IMPL-006A: 架构修正方案实施
基于006B V2.1简化配置架构

作者: LAD Team
创建时间: 2025-10-11
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from utils.config_manager import ConfigManager


class ConfigValidator:
    """
    简化版本的配置验证器
    专注于基本的重复检测和一致性验证
    无需JSON Schema，降低复杂度
    """
    
    def __init__(self, config_manager: ConfigManager = None):
        """
        初始化配置验证器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager or ConfigManager()
        
        # 从简化配置中读取验证规则
        app_config = self.config_manager._app_config
        validation_config = app_config.get("validation", {})
        self.strict_mode = validation_config.get("strict_mode", True)
        self.auto_fix = validation_config.get("auto_fix", False)
        
        # 日志
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"ConfigValidator initialized (strict_mode={self.strict_mode})")
    
    def validate_external_modules_config(self) -> Dict[str, Any]:
        """验证外部模块配置（简化版本）
        
        Returns:
            验证结果字典
        """
        try:
            # 获取统一的模块配置
            modules_config = self.config_manager._load_config_file("external_modules")
            
            # 基本格式验证
            if not isinstance(modules_config, dict):
                return {
                    "valid": False,
                    "error": "external_modules.json格式错误，应为JSON对象",
                    "validation_time": datetime.now().isoformat()
                }
            
            # 检查必需字段
            if "external_modules" not in modules_config:
                return {
                    "valid": False,
                    "error": "external_modules.json缺少'external_modules'字段",
                    "validation_time": datetime.now().isoformat()
                }
            
            # 验证每个模块的配置
            validated_modules = []
            external_modules = modules_config.get("external_modules", {})
            
            for module_name, module_config in external_modules.items():
                # 验证必需字段
                required_fields = ['enabled', 'module_path', 'required_functions']
                missing_fields = [f for f in required_fields if f not in module_config]
                
                if missing_fields:
                    return {
                        "valid": False,
                        "error": f"模块 {module_name} 缺少必需字段: {missing_fields}",
                        "validation_time": datetime.now().isoformat()
                    }
                
                validated_modules.append(module_name)
            
            return {
                "valid": True,
                "validated_modules": validated_modules,
                "module_count": len(validated_modules),
                "validation_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"配置验证失败: {str(e)}",
                "validation_time": datetime.now().isoformat()
            }
    
    def detect_config_conflicts(self) -> Dict[str, Any]:
        """检测配置冲突（简化版本）
        
        Returns:
            冲突检测结果
        """
        conflicts = []
        
        try:
            # 检查app_config.json和external_modules.json的一致性
            app_config = self.config_manager._app_config
            external_modules_file = self.config_manager._load_config_file("external_modules")
            
            # 检查是否还有重复的external_modules配置
            if "external_modules" in app_config and app_config["external_modules"]:
                conflicts.append({
                    "type": "duplicate_external_modules",
                    "message": "app_config.json中仍存在external_modules配置，应已移除",
                    "location": "app_config.json",
                    "severity": "warning"
                })
            
            # 检查模块配置完整性
            if external_modules_file and "external_modules" in external_modules_file:
                modules = external_modules_file.get("external_modules", {})
                for module_name, module_config in modules.items():
                    # 验证必需函数配置
                    required_functions = module_config.get("required_functions", [])
                    if not required_functions:
                        conflicts.append({
                            "type": "missing_required_functions",
                            "module": module_name,
                            "message": f"模块 {module_name} 缺少必需函数定义",
                            "severity": "error"
                        })
                    
                    # 验证模块路径
                    module_path = module_config.get("module_path", "")
                    if not module_path:
                        conflicts.append({
                            "type": "missing_module_path",
                            "module": module_name,
                            "message": f"模块 {module_name} 缺少module_path配置",
                            "severity": "error"
                        })
                    elif not Path(module_path).exists():
                        conflicts.append({
                            "type": "invalid_module_path",
                            "module": module_name,
                            "path": module_path,
                            "message": f"模块路径不存在: {module_path}",
                            "severity": "warning"
                        })
            
            return {
                "conflicts_found": len(conflicts) > 0,
                "conflict_count": len(conflicts),
                "conflicts": conflicts,
                "validation_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "conflicts_found": True,
                "conflict_count": 1,
                "conflicts": [{
                    "type": "validation_error",
                    "message": f"配置冲突检测失败: {str(e)}",
                    "severity": "error"
                }],
                "validation_time": datetime.now().isoformat()
            }
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要信息
        
        Returns:
            配置摘要字典
        """
        try:
            app_config = self.config_manager._app_config
            external_modules_file = self.config_manager._load_config_file("external_modules")
            ui_config = self.config_manager._ui_config
            
            return {
                "config_files": {
                    "app_config.json": {
                        "exists": bool(app_config),
                        "size": len(str(app_config)),
                        "main_sections": list(app_config.keys()) if app_config else []
                    },
                    "external_modules.json": {
                        "exists": bool(external_modules_file),
                        "module_count": len(external_modules_file.get("external_modules", {})) if external_modules_file else 0,
                        "modules": list(external_modules_file.get("external_modules", {}).keys()) if external_modules_file else []
                    },
                    "ui_config.json": {
                        "exists": bool(ui_config),
                        "size": len(str(ui_config))
                    }
                },
                "summary_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"配置摘要生成失败: {str(e)}",
                "summary_time": datetime.now().isoformat()
            }
































