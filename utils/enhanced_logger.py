#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强日志器 v1.0.0
在现有日志格式基础上增加关键结构化信息，保持向后兼容

作者: LAD Team
创建时间: 2025-08-16
最后更新: 2025-08-16
"""

import logging
import time
import functools
from typing import Dict, Any, Optional, Callable, Union
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class OperationContext:
    """操作上下文数据类"""
    operation: str
    file_path: Optional[str] = None
    duration_ms: Optional[float] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


class EnhancedLogger:
    """增强日志器，在现有日志基础上增加结构化信息"""
    
    def __init__(self, logger: logging.Logger):
        """
        初始化增强日志器
        
        Args:
            logger: 现有的日志器实例
        """
        self.logger = logger
        self.operation_stack = []
        self.context_data = {}
        
        # 设置上下文处理器
        self._setup_context_processor()
    
    def _setup_context_processor(self):
        """设置上下文处理器"""
        # 为现有日志器添加上下文信息
        original_handlers = self.logger.handlers.copy()
        
        for handler in original_handlers:
            # 创建增强的格式化器
            enhanced_formatter = EnhancedLogFormatter()
            handler.setFormatter(enhanced_formatter)
    
    def log_operation(self, message: str, operation: str = None, **kwargs):
        """
        记录操作日志，在消息中嵌入关键信息
        
        Args:
            message: 日志消息
            operation: 操作类型
            **kwargs: 额外的上下文信息
        """
        # 构建增强消息
        enhanced_message = self._build_enhanced_message(message, operation, **kwargs)
        
        # 使用现有日志器记录
        self.logger.info(enhanced_message)
    
    def log_performance(self, message: str, duration_ms: float, **kwargs):
        """
        记录性能相关日志
        
        Args:
            message: 日志消息
            duration_ms: 执行时间（毫秒）
            **kwargs: 额外的上下文信息
        """
        kwargs['duration_ms'] = duration_ms
        self.log_operation(message, operation='performance', **kwargs)
    
    def log_file_operation(self, message: str, file_path: str, **kwargs):
        """
        记录文件操作日志
        
        Args:
            message: 日志消息
            file_path: 文件路径
            **kwargs: 额外的上下文信息
        """
        kwargs['file_path'] = file_path
        self.log_operation(message, operation='file_operation', **kwargs)
    
    def log_error(self, message: str, error: Exception = None, **kwargs):
        """
        记录错误日志
        
        Args:
            message: 日志消息
            error: 异常对象
            **kwargs: 额外的上下文信息
        """
        if error:
            kwargs['error_type'] = type(error).__name__
            kwargs['error_message'] = str(error)
        
        kwargs['operation'] = 'error'
        enhanced_message = self._build_enhanced_message(message, 'error', **kwargs)
        
        self.logger.error(enhanced_message)
    
    def log_warning(self, message: str, **kwargs):
        """
        记录警告日志
        
        Args:
            message: 日志消息
            **kwargs: 额外的上下文信息
        """
        enhanced_message = self._build_enhanced_message(message, 'warning', **kwargs)
        self.logger.warning(enhanced_message)
    
    def log_debug(self, message: str, **kwargs):
        """
        记录调试日志
        
        Args:
            message: 日志消息
            **kwargs: 额外的上下文信息
        """
        enhanced_message = self._build_enhanced_message(message, 'debug', **kwargs)
        self.logger.debug(enhanced_message)
    
    def _build_enhanced_message(self, message: str, operation: str = None, **kwargs) -> str:
        """
        构建增强的日志消息
        
        Args:
            message: 原始消息
            operation: 操作类型
            **kwargs: 额外的上下文信息
            
        Returns:
            增强后的消息
        """
        enhanced_parts = [message]
        
        # 添加操作类型
        if operation:
            enhanced_parts.append(f"[{operation}]")
        
        # 添加文件路径
        if kwargs.get('file_path'):
            enhanced_parts.append(f"file: {kwargs['file_path']}")
        
        # 添加执行时间
        if kwargs.get('duration_ms'):
            enhanced_parts.append(f"({kwargs['duration_ms']:.2f}ms)")
        
        # 添加用户ID
        if kwargs.get('user_id'):
            enhanced_parts.append(f"user: {kwargs['user_id']}")
        
        # 添加会话ID
        if kwargs.get('session_id'):
            enhanced_parts.append(f"session: {kwargs['session_id']}")
        
        # 添加其他额外数据
        extra_data = {k: v for k, v in kwargs.items() 
                     if k not in ['operation', 'file_path', 'duration_ms', 'user_id', 'session_id']}
        if extra_data:
            extra_str = " | ".join([f"{k}={v}" for k, v in extra_data.items()])
            enhanced_parts.append(extra_str)
        
        return " | ".join(enhanced_parts)
    
    def operation_context(self, operation: str, **context_kwargs):
        """
        操作上下文装饰器，自动记录操作开始和结束
        
        Args:
            operation: 操作名称
            **context_kwargs: 上下文参数
            
        Returns:
            装饰器函数
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 记录操作开始
                start_time = time.time()
                self.log_operation(f"开始执行操作: {operation}", operation, **context_kwargs)
                
                try:
                    # 执行原函数
                    result = func(*args, **kwargs)
                    
                    # 记录操作成功
                    duration_ms = (time.time() - start_time) * 1000
                    self.log_operation(f"操作执行成功: {operation}", operation, 
                                     duration_ms=duration_ms, **context_kwargs)
                    
                    return result
                    
                except Exception as e:
                    # 记录操作失败
                    duration_ms = (time.time() - start_time) * 1000
                    self.log_error(f"操作执行失败: {operation}", error=e, 
                                 duration_ms=duration_ms, **context_kwargs)
                    raise
            
            return wrapper
        return decorator
    
    def performance_monitor(self, threshold_ms: float = 1000):
        """
        性能监控装饰器，记录超过阈值的操作
        
        Args:
            threshold_ms: 性能阈值（毫秒）
            
        Returns:
            装饰器函数
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    
                    duration_ms = (time.time() - start_time) * 1000
                    
                    if duration_ms > threshold_ms:
                        self.log_warning(f"操作执行时间过长: {func.__name__}", 
                                       operation='performance_warning',
                                       duration_ms=duration_ms,
                                       threshold_ms=threshold_ms)
                    else:
                        self.log_debug(f"操作执行时间正常: {func.__name__}", 
                                     operation='performance_normal',
                                     duration_ms=duration_ms)
                    
                    return result
                    
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    self.log_error(f"操作执行异常: {func.__name__}", error=e,
                                 duration_ms=duration_ms)
                    raise
            
            return wrapper
        return decorator
    
    def set_context(self, **context_data):
        """
        设置全局上下文数据
        
        Args:
            **context_data: 上下文数据
        """
        self.context_data.update(context_data)
    
    def clear_context(self):
        """清除全局上下文数据"""
        self.context_data.clear()
    
    def get_context(self) -> Dict[str, Any]:
        """获取当前上下文数据"""
        return self.context_data.copy()
    
    def push_operation(self, operation: str, **context_data):
        """
        推入操作到操作栈
        
        Args:
            operation: 操作名称
            **context_data: 操作上下文
        """
        operation_context = OperationContext(
            operation=operation,
            **context_data
        )
        self.operation_stack.append(operation_context)
    
    def pop_operation(self) -> Optional[OperationContext]:
        """
        从操作栈弹出操作
        
        Returns:
            操作上下文对象，如果栈为空则返回None
        """
        if self.operation_stack:
            return self.operation_stack.pop()
        return None
    
    def get_current_operation(self) -> Optional[OperationContext]:
        """
        获取当前操作上下文
        
        Returns:
            当前操作上下文对象，如果没有则返回None
        """
        if self.operation_stack:
            return self.operation_stack[-1]
        return None
    
    def log_with_context(self, message: str, level: str = 'info', **kwargs):
        """
        使用当前上下文记录日志
        
        Args:
            message: 日志消息
            level: 日志级别
            **kwargs: 额外的上下文信息
        """
        # 合并全局上下文和当前操作上下文
        context = self.context_data.copy()
        
        current_op = self.get_current_operation()
        if current_op:
            context.update(current_op.to_dict())
        
        # 合并额外参数
        context.update(kwargs)
        
        # 根据级别记录日志
        if level.lower() == 'debug':
            self.log_debug(message, **context)
        elif level.lower() == 'info':
            self.log_operation(message, **context)
        elif level.lower() == 'warning':
            self.log_warning(message, **context)
        elif level.lower() == 'error':
            self.log_error(message, **context)
        else:
            self.log_operation(message, **context)


class EnhancedLogFormatter(logging.Formatter):
    """增强的日志格式化器"""
    
    def __init__(self, fmt=None, datefmt=None, style='%'):
        super().__init__(fmt, datefmt, style)
        self.default_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    def format(self, record):
        """格式化日志记录"""
        # 如果消息已经包含增强信息，直接使用
        if hasattr(record, 'enhanced_message'):
            record.msg = record.enhanced_message
        
        # 使用默认格式
        return super().format(record)


class LoggingContextManager:
    """日志上下文管理器"""
    
    def __init__(self, enhanced_logger: EnhancedLogger):
        self.enhanced_logger = enhanced_logger
        self.operation_name = None
        self.context_data = {}
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 记录操作结束
        if self.operation_name:
            if exc_type is None:
                self.enhanced_logger.log_operation(
                    f"操作完成: {self.operation_name}",
                    operation=self.operation_name,
                    **self.context_data
                )
            else:
                self.enhanced_logger.log_error(
                    f"操作失败: {self.operation_name}",
                    error=exc_val,
                    **self.context_data
                )
    
    def set_operation(self, operation: str):
        """设置操作名称"""
        self.operation_name = operation
        self.enhanced_logger.push_operation(operation, **self.context_data)
    
    def set_context(self, **context_data):
        """设置上下文数据"""
        self.context_data.update(context_data)
        if self.operation_name:
            self.enhanced_logger.push_operation(self.operation_name, **self.context_data)


# 便捷函数
def create_enhanced_logger(logger_name: str = None, 
                          logger: logging.Logger = None) -> EnhancedLogger:
    """
    创建增强日志器的便捷函数
    
    Args:
        logger_name: 日志器名称，如果提供则创建新的日志器
        logger: 现有的日志器实例
        
    Returns:
        增强日志器实例
    """
    if logger is None:
        if logger_name is None:
            logger_name = __name__
        logger = logging.getLogger(logger_name)
    
    return EnhancedLogger(logger)


def enhance_existing_logger(logger: logging.Logger) -> EnhancedLogger:
    """
    增强现有日志器的便捷函数
    
    Args:
        logger: 现有的日志器实例
        
    Returns:
        增强日志器实例
    """
    return EnhancedLogger(logger)


# 使用示例
if __name__ == "__main__":
    # 创建基础日志器
    logging.basicConfig(level=logging.INFO)
    base_logger = logging.getLogger("test_logger")
    
    # 创建增强日志器
    enhanced_logger = create_enhanced_logger(logger=base_logger)
    
    # 设置全局上下文
    enhanced_logger.set_context(module="test_module", version="1.0.0")
    
    # 记录各种日志
    enhanced_logger.log_operation("开始测试", operation="test_start")
    enhanced_logger.log_file_operation("读取配置文件", "config.json")
    enhanced_logger.log_performance("处理完成", 150.5)
    
    # 使用上下文管理器
    with LoggingContextManager(enhanced_logger) as ctx:
        ctx.set_operation("file_processing")
        ctx.set_context(file_path="test.md", file_size=1024)
        
        # 模拟文件处理
        enhanced_logger.log_with_context("开始处理文件", level="info")
        enhanced_logger.log_with_context("文件处理完成", level="info")
    
    # 使用装饰器
    @enhanced_logger.operation_context("data_analysis")
    def analyze_data():
        time.sleep(0.1)  # 模拟处理时间
        return "分析结果"
    
    @enhanced_logger.performance_monitor(threshold_ms=50)
    def slow_operation():
        time.sleep(0.2)  # 模拟慢操作
        return "慢操作结果"
    
    # 执行测试
    analyze_data()
    slow_operation() 