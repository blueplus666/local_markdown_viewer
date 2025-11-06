#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误码管理器模块 v1.0.0
LAD-IMPL-006A: 架构修正方案实施
标准化错误码体系，统一错误处理

作者: LAD Team
创建时间: 2025-10-11
"""

from enum import Enum
from typing import Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass
import logging

if TYPE_CHECKING:  # 仅用于类型检查，避免运行时循环依赖
    from core.enhanced_logger import TemplatedLogger


class ModuleImportErrorCodes(Enum):
    """模块导入错误码"""
    MODULE_NOT_FOUND = ("M001", "模块文件不存在")
    MODULE_IMPORT_FAILED = ("M002", "模块导入失败")
    MODULE_INVALID_FORMAT = ("M003", "模块格式无效")
    FUNCTION_NOT_FOUND = ("M004", "必需函数不存在")
    FUNCTION_SIGNATURE_MISMATCH = ("M005", "函数签名不匹配")
    MODULE_DISABLED = ("M006", "模块已禁用")
    MODULE_DEPENDENCY_MISSING = ("M007", "模块依赖项缺失")
    MODULE_VERSION_MISMATCH = ("M008", "模块版本不匹配")
    MODULE_INIT_FAILED = ("M009", "模块初始化失败")


class RenderProcessingErrorCodes(Enum):
    """渲染处理错误码"""
    RENDER_FAILED = ("R001", "渲染失败")
    MARKDOWN_PARSE_ERROR = ("R002", "Markdown解析错误")
    HTML_GENERATION_ERROR = ("R003", "HTML生成错误")
    FALLBACK_TRIGGERED = ("R004", "触发降级渲染")
    RENDER_TIMEOUT = ("R005", "渲染超时")
    ZOOM_NOT_SUPPORTED = ("R006", "不支持缩放功能")


class LinkProcessingErrorCodes(Enum):
    """链接处理错误码"""
    LINK_INVALID_FORMAT = ("L001", "链接格式无效")
    LINK_SECURITY_VIOLATION = ("L002", "链接安全违规")
    LINK_NOT_FOUND = ("L003", "链接目标不存在")
    LINK_PERMISSION_DENIED = ("L004", "链接访问权限不足")
    POLICY_VIOLATION = ("L005", "违反安全策略")
    LINK_UNKNOWN_ERROR = ("L006", "未知链接错误")
    LINK_ACCESS_DENIED = ("L007", "链接访问被拒绝")
    LINK_TIMEOUT = ("L008", "链接超时")


class SystemErrorCodes(Enum):
    """系统错误码"""
    CONFIG_ERROR = ("S001", "配置错误")
    CACHE_ERROR = ("S002", "缓存错误")
    STATE_ERROR = ("S003", "状态错误")
    SNAPSHOT_ERROR = ("S004", "快照错误")
    THREAD_SAFETY_ERROR = ("S005", "线程安全错误")
    RESOURCE_EXHAUSTED = ("S006", "资源耗尽")
    NETWORK_ERROR = ("S007", "网络错误")
    DATABASE_ERROR = ("S008", "数据库错误")
    AUTHENTICATION_ERROR = ("S009", "认证错误")
    AUTHORIZATION_ERROR = ("S010", "授权错误")


@dataclass
class ErrorInfo:
    """错误信息数据类"""
    code: str
    message: str
    category: str
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "code": self.code,
            "message": self.message,
            "category": self.category,
            "details": self.details or {}
        }


class ErrorCodeManager:
    """
    错误码管理器
    提供统一的错误码查询和错误信息生成接口
    基于006B V2.1简化配置架构
    """
    
    def __init__(self, config_manager=None):
        """
        初始化错误码管理器
        
        Args:
            config_manager: 配置管理器实例（可选）
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # 错误码映射表
        self.error_codes = {
            'module': ModuleImportErrorCodes,
            'render': RenderProcessingErrorCodes,
            'link': LinkProcessingErrorCodes,
            'system': SystemErrorCodes
        }
        
        # 应用配置
        self._validate_and_apply_config()
    
    def _validate_and_apply_config(self):
        """验证并应用配置"""
        # 首先应用默认配置
        self._apply_default_config()
        
        if not self.config_manager:
            return
            
        try:
            # 尝试从配置管理器中获取配置
            if hasattr(self.config_manager, 'get_unified_config'):
                config = self.config_manager.get_unified_config('error_handling', {})
            else:
                config = getattr(self.config_manager, '_app_config', {}).get('error_handling', {})
            
            if not self._is_valid_config(config):
                self.logger.warning("配置验证失败，使用默认配置")
                return
                
            # 应用验证通过的配置
            self.error_strategy = config.get('strategy', self.error_strategy)
            self.auto_recovery = config.get('auto_recovery', self.auto_recovery)
            self.log_errors = config.get('log_errors', self.log_errors)
            self.max_error_history = config.get('max_error_history', self.max_error_history)
            
            # 延迟初始化TemplatedLogger，避免循环依赖
            self.templated_logger = None  # 延迟到首次使用时创建
            
        except Exception as e:
            self.logger.error(f"配置加载异常: {str(e)}", exc_info=True)
            
    def _get_templated_logger(self):
        """延迟获取TemplatedLogger，避免循环依赖"""
        if self.templated_logger is None:
            try:
                from core.enhanced_logger import TemplatedLogger
                self.templated_logger = TemplatedLogger(
                    __name__,
                    config_manager=self.config_manager
                )
            except Exception as e:
                self.logger.warning(f"无法创建TemplatedLogger，使用标准日志: {str(e)}")
                self.templated_logger = None
        return self.templated_logger
            
    def _is_valid_config(self, config: dict) -> bool:
        """验证配置有效性"""
        if not isinstance(config, dict):
            self.logger.warning("配置必须是一个字典")
            return False
            
        # 验证strategy
        strategy = config.get('strategy')
        if strategy is not None and strategy not in ('graceful', 'strict'):
            self.logger.warning(f"无效的错误处理策略: {strategy}，必须为 'graceful' 或 'strict'")
            return False
            
        # 验证布尔值配置
        bool_fields = ['auto_recovery', 'log_errors']
        for field in bool_fields:
            if field in config and not isinstance(config[field], bool):
                self.logger.warning(f"配置项 {field} 必须为布尔值")
                return False
                
        # 验证max_error_history
        max_history = config.get('max_error_history')
        if max_history is not None and (not isinstance(max_history, int) or max_history < 100):
            self.logger.warning("max_error_history必须为≥100的整数")
            return False
            
        return True
        
    def _apply_default_config(self):
        """应用默认配置"""
        self.error_strategy = 'graceful'
        self.auto_recovery = True
        self.log_errors = True
        self.max_error_history = 1000
        self.templated_logger = None
    
    def get_error_info(self, category: str, error_code_enum) -> ErrorInfo:
        """
        获取错误信息
        
        Args:
            category: 错误类别 (module/render/link/system)
            error_code_enum: 错误码枚举值
        
        Returns:
            ErrorInfo对象
        """
        # 兼容：既支持枚举也支持字符串/其他类型传入
        try:
            val = getattr(error_code_enum, "value")
            if isinstance(val, tuple) and len(val) >= 2:
                code, message = val[0], val[1]
            else:
                code = str(val)
                message = self.get_error_message(error_code_enum) or code
        except Exception:
            # 字符串或未知类型：尝试按名称/编号解析到已知枚举，否则回退为通用信息
            raw = str(error_code_enum)
            code, message = raw, self.get_error_message(raw) or raw
            # 优先按当前类别解析名称
            enum_cls = self.error_codes.get(category)
            resolved = None
            try:
                if enum_cls is not None:
                    # 按名称匹配
                    for e in enum_cls:
                        if e.name == raw or (isinstance(e.value, tuple) and e.value and e.value[0] == raw):
                            resolved = e
                            break
                # 跨类别兜底匹配
                if resolved is None:
                    for ec in (ModuleImportErrorCodes, RenderProcessingErrorCodes, LinkProcessingErrorCodes, SystemErrorCodes):
                        for e in ec:
                            if e.name == raw or (isinstance(e.value, tuple) and e.value and e.value[0] == raw):
                                resolved = e
                                break
                        if resolved is not None:
                            break
                if resolved is not None:
                    v = resolved.value
                    code = v[0] if isinstance(v, tuple) and v else str(v)
                    message = v[1] if isinstance(v, tuple) and len(v) >= 2 else (self.get_error_message(code) or code)
            except Exception:
                pass

        return ErrorInfo(code=code, message=message, category=category)
    
    def format_error(self, category: str, error_code_enum, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        格式化错误信息
        
        Args:
            category: 错误类别
            error_code_enum: 错误码枚举值
            details: 额外的错误详情
            
        Returns:
            格式化的错误字典
        """
        error_info = self.get_error_info(category, error_code_enum)
        error_info.details = details
        
        formatted_error = error_info.to_dict()
        
        # 记录日志：为避免与 EnhancedLogger 相互递归，这里统一使用标准日志
        if self.log_errors:
            try:
                self.logger.error(
                    f"[{error_info.code}] {error_info.message} | Category: {category} | Details: {details}"
                )
            except Exception:
                pass
        
        return formatted_error
    
    def get_all_error_codes(self) -> Dict[str, Dict[str, str]]:
        """
        获取所有错误码
        
        Returns:
            按类别组织的错误码字典
        """
        all_codes = {}
        
        for category, error_enum in self.error_codes.items():
            all_codes[category] = {
                code.name: code.value 
                for code in error_enum
            }
        
        return all_codes
    
    def validate_error_code(self, category: str, code: str) -> bool:
        """
        验证错误码是否有效
        
        Args:
            category: 错误类别
            code: 错误码
            
        Returns:
            是否有效
        """
        if category not in self.error_codes:
            return False
        
        error_enum = self.error_codes[category]
        valid_codes = [e.value[0] for e in error_enum]
        
        return code in valid_codes

    # === V4.2 扩展：提供严重度与消息查询，支持UI颜色映射 ===
    def get_error_severity(self, error_code_enum) -> str:
        """
        返回严重度：critical/error/warning/none
        要求：支持枚举或字符串代码
        """
        try:
            code = getattr(error_code_enum, "value", None)
            # 若是元组("M001","msg")取第一项
            if isinstance(code, tuple) and code:
                code = code[0]
            if code is None:
                code = str(error_code_enum)
        except Exception:
            code = str(error_code_enum)

        severity_map = {
            "MI_CRITICAL": "critical",
            "MI_ERROR": "error",
            "MI_WARN": "warning",
            # 兼容现有编号系：模块/渲染/系统等前缀
            "M001": "error",
            "M002": "error",
            "M003": "error",
            "M004": "warning",
            "M005": "warning",
            "M006": "warning",
            "R001": "error",
            "R002": "error",
            "R003": "error",
            "R004": "warning",
            "R005": "critical",
            "R006": "warning",
            "S001": "error",
            "S002": "error",
            "S003": "error",
            "S004": "error",
            "S005": "critical",
            "S006": "critical",
            "L001": "warning",
            "L002": "critical",
            "L003": "warning",
            "L004": "error",
            "L005": "error",
        }
        return severity_map.get(code, "none")

    def get_error_message(self, error_code_enum) -> str:
        """返回统一中文消息（支持字符串或枚举）。"""
        try:
            code = getattr(error_code_enum, "value", None)
            if isinstance(code, tuple) and code:
                # 若元组，第二项即为消息
                return code[1]
            if code is None:
                code = str(error_code_enum)
        except Exception:
            code = str(error_code_enum)

        message_map = {
            "MI_CRITICAL": "模块导入发生致命错误",
            "MI_ERROR": "模块导入失败",
            "MI_WARN": "模块导入存在缺陷（部分功能缺失）",
        }
        # 回退到各错误枚举定义内置消息
        for enum_cls in (ModuleImportErrorCodes, RenderProcessingErrorCodes, LinkProcessingErrorCodes, SystemErrorCodes):
            try:
                for e in enum_cls:
                    if e.value[0] == code:
                        return e.value[1]
            except Exception:
                continue
        return message_map.get(code, "")

