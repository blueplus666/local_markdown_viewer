#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用状态管理器模块 v1.0.0
LAD-IMPL-006A: 架构修正方案实施
基于006B V2.1简化配置架构

作者: LAD Team
创建时间: 2025-10-11
"""

import threading
import time
import logging
from contextlib import contextmanager
from typing import Dict, Any, Optional
from utils.config_manager import ConfigManager


class ApplicationStateManager:
    """
    应用状态管理器
    统一管理模块、渲染、链接三个域的状态
    基于006B V2.1简化配置架构，实施完整的线程安全机制
    """
    
    def __init__(self, config_manager: ConfigManager = None):
        """
        初始化应用状态管理器
        
        Args:
            config_manager: 配置管理器实例（来自006B V2.1）
        """
        # 使用006B V2.1的ConfigManager
        self.config_manager = config_manager or ConfigManager()
        
        # 从简化配置中读取参数
        app_config = self.config_manager._app_config
        perf_config = app_config.get('markdown', {})
        
        # 状态存储（三个域）
        self._module_states = {}  # 模块导入状态
        self._render_state = {}  # 渲染决策状态
        self._link_state = {}  # 链接处理状态
        
        # 简化配置驱动的组件初始化（延迟导入避免循环依赖）
        self._snapshot_manager = None
        self._performance_metrics = None
        
        # 简化配置的性能参数
        self._max_state_history = 100  # 默认值
        self._state_cache_ttl = 300  # 默认值，300秒
        
        # 线程安全控制（按照线程安全清单实现）
        self._state_lock = threading.RLock()  # 可重入锁（全局状态锁）
        self._module_locks = {}  # 模块级别的细粒度锁
        self._lock_manager_lock = threading.Lock()  # 锁管理器的锁
        
        # 日志记录器
        self.logger = logging.getLogger(__name__)
        self.logger.info("ApplicationStateManager initialized with simplified config")
    
    def set_snapshot_manager(self, snapshot_manager):
        """设置快照管理器（避免循环依赖）"""
        self._snapshot_manager = snapshot_manager
    
    def set_performance_metrics(self, performance_metrics):
        """设置性能指标收集器（避免循环依赖）"""
        self._performance_metrics = performance_metrics
    
    def _get_module_lock(self, module_name: str) -> threading.Lock:
        """获取模块专用锁（懒加载）
        
        Args:
            module_name: 模块名称
            
        Returns:
            模块专用的线程锁
        """
        with self._lock_manager_lock:
            if module_name not in self._module_locks:
                self._module_locks[module_name] = threading.Lock()
            return self._module_locks[module_name]
    
    @contextmanager
    def _state_transaction(self, module_name: Optional[str] = None):
        """状态事务上下文管理器
        
        Args:
            module_name: 如果指定，使用模块级别锁；否则使用全局锁
        """
        if module_name:
            # 模块级别锁
            module_lock = self._get_module_lock(module_name)
            with module_lock:
                yield
        else:
            # 全局状态锁
            with self._state_lock:
                yield
    
    def get_module_status(self, module_name: str) -> Dict[str, Any]:
        """线程安全获取模块状态（简化配置驱动）
        
        Args:
            module_name: 模块名称
            
        Returns:
            模块状态字典
        """
        with self._state_transaction(module_name):
            # 从简化配置中获取模块信息
            module_config = self.config_manager.get_external_module_config(module_name)
            
            # 合并运行时状态和配置信息
            state = self._module_states.get(module_name, {}).copy()
            state.update({
                "config_enabled": module_config.get("enabled", False),
                "config_version": module_config.get("version", "unknown"),
                "required_functions": module_config.get("required_functions", [])
            })
            
            # 添加线程信息
            state['_lock_info'] = {
                'thread_id': threading.current_thread().ident,
                'access_time': time.time()
            }
            
            return state
    
    def update_module_status(self, module_name: str, status_data: Dict[str, Any]) -> bool:
        """线程安全更新模块状态（简化配置感知）
        
        Args:
            module_name: 模块名称
            status_data: 状态数据
            
        Returns:
            是否更新成功
        """
        try:
            with self._state_transaction(module_name):
                # 验证模块是否在配置中启用
                module_config = self.config_manager.get_external_module_config(module_name) or {}
                if module_config and not module_config.get("enabled", False):
                    self.logger.warning(f"Module {module_name} is disabled in config")
                    return False
                
                # 深拷贝状态数据，避免外部修改影响
                safe_status_data = self._deep_copy_status_data(status_data)
                
                # 添加线程信息
                safe_status_data['_thread_info'] = {
                    'updated_by_thread': threading.current_thread().ident,
                    'update_time': time.time()
                }
                
                # 更新状态
                self._module_states[module_name] = safe_status_data
                
                # 更新快照（如果快照管理器已设置）
                if self._snapshot_manager:
                    snapshot_success = self._snapshot_manager.save_module_snapshot(
                        module_name, safe_status_data
                    )
                else:
                    snapshot_success = True
                
                # 记录性能指标（如果性能指标收集器已设置）
                if self._performance_metrics:
                    self._performance_metrics.record_module_update(module_name, safe_status_data)
                
                return snapshot_success
                
        except Exception as e:
            self._log_thread_safe_error(f"Failed to update module status for {module_name}: {e}")
            return False
    
    def get_render_status(self) -> Dict[str, Any]:
        """线程安全获取渲染状态
        
        Returns:
            渲染状态字典
        """
        with self._state_transaction():
            if self._snapshot_manager:
                snapshot = self._snapshot_manager.get_render_snapshot()
            else:
                snapshot = {}
            
            return {
                'renderer_type': snapshot.get('renderer_type', 'unknown'),
                'reason': snapshot.get('reason', 'unknown'),
                'details': snapshot.get('details', {}).copy(),
                'timestamp': snapshot.get('timestamp', ''),
                '_lock_info': {
                    'thread_id': threading.current_thread().ident,
                    'access_time': time.time()
                }
            }
    
    def update_render_status(self, status_data: Dict[str, Any]) -> bool:
        """线程安全更新渲染状态
        
        Args:
            status_data: 渲染状态数据
            
        Returns:
            是否更新成功
        """
        try:
            with self._state_transaction():
                safe_status_data = self._deep_copy_status_data(status_data)
                safe_status_data['_thread_info'] = {
                    'updated_by_thread': threading.current_thread().ident,
                    'update_time': time.time()
                }
                
                self._render_state = safe_status_data
                
                if self._snapshot_manager:
                    snapshot_success = self._snapshot_manager.save_render_snapshot(safe_status_data)
                else:
                    snapshot_success = True
                
                if self._performance_metrics:
                    self._performance_metrics.record_render_update(safe_status_data)
                
                return snapshot_success
                
        except Exception as e:
            self._log_thread_safe_error(f"Failed to update render status: {e}")
            return False
    
    def get_link_status(self) -> Dict[str, Any]:
        """线程安全获取链接状态
        
        Returns:
            链接状态字典
        """
        with self._state_transaction():
            if self._snapshot_manager:
                snapshot = self._snapshot_manager.get_link_snapshot()
            else:
                snapshot = {}
            
            return {
                'link_processor_loaded': snapshot.get('link_processor_loaded', False),
                'policy_profile': snapshot.get('policy_profile', 'default'),
                'last_action': snapshot.get('last_action', 'none'),
                'last_result': snapshot.get('last_result', 'unknown'),
                'details': snapshot.get('details', {}).copy(),
                'error_code': snapshot.get('error_code', ''),
                'message': snapshot.get('message', ''),
                'timestamp': snapshot.get('timestamp', ''),
                '_lock_info': {
                    'thread_id': threading.current_thread().ident,
                    'access_time': time.time()
                }
            }
    
    def update_link_status(self, status_data: Dict[str, Any]) -> bool:
        """线程安全更新链接状态
        
        Args:
            status_data: 链接状态数据
            
        Returns:
            是否更新成功
        """
        try:
            with self._state_transaction():
                safe_status_data = self._deep_copy_status_data(status_data)
                safe_status_data['_thread_info'] = {
                    'updated_by_thread': threading.current_thread().ident,
                    'update_time': time.time()
                }
                
                self._link_state = safe_status_data
                
                if self._snapshot_manager:
                    snapshot_success = self._snapshot_manager.save_link_snapshot(safe_status_data)
                else:
                    snapshot_success = True
                
                if self._performance_metrics:
                    self._performance_metrics.record_link_update(safe_status_data)
                
                return snapshot_success
                
        except Exception as e:
            self._log_thread_safe_error(f"Failed to update link status: {e}")
            return False
    
    # 辅助方法
    def _deep_copy_status_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """深拷贝状态数据，确保线程安全
        
        Args:
            data: 状态数据
            
        Returns:
            深拷贝后的数据
        """
        import copy
        return copy.deepcopy(data)
    
    def _log_thread_safe_error(self, message: str):
        """线程安全的错误日志记录
        
        Args:
            message: 错误消息
        """
        thread_id = threading.current_thread().ident
        self.logger.error(f"[Thread-{thread_id}] {message}")
    
    def get_all_states(self) -> Dict[str, Any]:
        """线程安全获取所有状态
        
        Returns:
            包含所有域状态的字典
        """
        with self._state_lock:
            return {
                'modules': self._module_states.copy(),
                'render': self._render_state.copy(),
                'link': self._link_state.copy(),
                '_access_info': {
                    'thread_id': threading.current_thread().ident,
                    'access_time': time.time()
                }
            }

    def get_snapshot_manager(self):
        return self._snapshot_manager

    def get_performance_metrics(self):
        return self._performance_metrics












