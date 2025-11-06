#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LAD本地Markdown渲染器 - 动态模块导入器
增强版本：支持配置驱动的模块导入、函数映射完整性校验和fallback机制

版本: v1.2.0
更新: 增强函数映射完整性验证，添加状态报告机制
"""

import os
import sys
import logging
import time
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING
from contextlib import contextmanager

# 导入统一缓存管理器
from .unified_cache_manager import UnifiedCacheManager, CacheStrategy
from .enhanced_error_handler import EnhancedErrorHandler, ErrorRecoveryStrategy
from core.enhanced_logger import TemplatedLogger

# 统一导入策略：优先相对导入，失败时使用绝对路径
try:
	from ..utils.config_manager import ConfigManager
except ImportError:
	# 备用：添加父目录到路径并导入
	sys.path.insert(0, str(Path(__file__).parent.parent))
	from utils.config_manager import ConfigManager

try:
    from core.snapshot_manager import SnapshotManager
except ImportError:
    SnapshotManager = None

if TYPE_CHECKING:
    from core.performance_metrics import PerformanceMetrics
    from core.snapshot_manager import SnapshotManager as SnapshotManagerType


class DynamicModuleImporter:
	"""
	动态模块导入器类
	提供基于配置的动态模块导入功能，支持缓存、fallback和错误处理
	优化版本：增强配置文件兼容性、日志记录和错误处理
	"""
	
	# 错误码常量
	ERROR_CODES = {
		'PATH_NOT_FOUND': 'PATH_NOT_FOUND',
		'IMPORT_ERROR': 'IMPORT_ERROR', 
		'MISSING_SYMBOLS': 'MISSING_SYMBOLS',
		'CONFIG_ERROR': 'CONFIG_ERROR',
		'UNKNOWN_ERROR': 'UNKNOWN_ERROR'
	}
	
	def __init__(
		self,
		config_manager: Optional[ConfigManager] = None,
		logger: Optional[TemplatedLogger] = None,
		performance_metrics: Optional["PerformanceMetrics"] = None,
		snapshot_manager: Optional["SnapshotManagerType"] = None,
	) -> None:
		"""
		初始化动态模块导入器
		
		Args:
			config_manager: 配置管理器实例
		"""
		self.config_manager = config_manager or ConfigManager()
		self.performance_metrics = performance_metrics
		self.logger = logger or TemplatedLogger(
			__name__,
			templates=None,
			config_manager=self.config_manager,
			performance_metrics=performance_metrics,
		)
		
		# 统一缓存管理器
		self.cache_manager = UnifiedCacheManager(
			max_size=200,  # 模块导入缓存较小
			default_ttl=7200,  # 默认2小时过期（模块导入结果相对稳定）
			strategy=CacheStrategy.LRU,
			cache_dir=Path(__file__).parent.parent / "cache" / "modules"
		)
		
		# 增强错误处理器
		self.error_handler = EnhancedErrorHandler(
			error_log_dir=Path(__file__).parent.parent / "logs" / "errors",
			max_error_history=200
		)
		
		# 旧缓存系统已移除，统一使用UnifiedCacheManager
		
		# 模块路径配置
		self._module_paths = {}
		
		# 加载模块配置
		self._load_module_configs()
		
		# 性能统计
		self._stats = {
			'total_imports': 0,
			'successful_imports': 0,
			'failed_imports': 0,
			'cache_hits': 0,
			'fallback_usage': 0
		}

		# 关联的当前correlation_id（由UI或调用方注入）
		self._correlation_id: Optional[str] = None
		self.snapshot_manager: Optional["SnapshotManagerType"] = snapshot_manager
		if self.performance_metrics is None:
			try:
				from core.performance_metrics import PerformanceMetrics as _PM  # 延迟导入避免循环
				self.performance_metrics = _PM(self.config_manager)
			except Exception:
				self.performance_metrics = None
		else:
			self.logger.performance_metrics = self.performance_metrics
		
		if self.snapshot_manager is None and SnapshotManager is not None:
			try:
				self.snapshot_manager = SnapshotManager(self.config_manager)
			except Exception:
				self.snapshot_manager = None

	
	def _load_module_configs(self):
		"""加载模块配置 - 优化版本：增强与external_modules.json的兼容性"""
		try:
			# 清空后重新加载，避免旧配置残留
			self._module_paths.clear()
			
			# 优化1: 优先尝试直接读取external_modules.json
			config_file_path = Path(__file__).parent.parent / "config" / "external_modules.json"
			if config_file_path.exists():
				try:
					self.logger.log_from_template(
						"module_config_source_attempt",
						source="external_modules.json",
					)
					with open(config_file_path, 'r', encoding='utf-8') as f:
						external_config = json.load(f)
					
					# 解析external_modules.json配置
					md_config = external_config.get('external_modules', {}).get('markdown_processor', {})
					if md_config and md_config.get('enabled', True):  # 默认启用
						module_path = md_config.get('module_path', '')
						if module_path:
							self._module_paths['markdown_processor'] = {
								'path': module_path,
								'version': md_config.get('version', '1.0.0'),
								'description': md_config.get('description', ''),
								'priority': md_config.get('priority', 1),
								'required_functions': md_config.get('required_functions', []),
								'fallback_enabled': md_config.get('fallback_enabled', True)
							}
							self.logger.log_from_template(
								"module_config_loaded",
								module_name="markdown_processor",
								source="external_modules.json",
								module_path=module_path,
							)
							return  # 成功加载，直接返回
							
				except Exception as e:
					self.logger.log_from_template(
						"module_config_error",
						error=str(e),
					)
			
			# 优化3: 降级到ConfigManager（向后兼容）
			self.logger.log_from_template(
				"module_config_source_attempt",
				source="ConfigManager",
			)
			md_cfg = self.config_manager.get_external_module_config('markdown_processor')
			if md_cfg and md_cfg.get('enabled', False):
				module_path = md_cfg.get('module_path', '')
				if module_path:
					self._module_paths['markdown_processor'] = {
						'path': module_path,
						'version': md_cfg.get('version', '1.0.0'),
						'description': md_cfg.get('description', ''),
						'priority': md_cfg.get('priority', 1),
						'required_functions': md_cfg.get('required_functions', []),
						'fallback_enabled': md_cfg.get('fallback_enabled', True)
					}
					self.logger.log_from_template(
						"module_config_loaded",
						module_name="markdown_processor",
						source="ConfigManager",
						module_path=module_path,
					)
			
			# 优化4: 配置验证和统计
			if self._module_paths:
				self.logger.log_from_template(
					"module_config_summary",
					module_count=len(self._module_paths),
				)
				for name, config in self._module_paths.items():
					self.logger.log_from_template(
						"module_config_summary_item",
						module_name=name,
						module_path=config['path'],
						priority=config.get('priority', 1),
					)
			else:
				self.logger.log_from_template("module_config_missing")
			
		except Exception as e:
			self.logger.log_from_template(
				"module_config_error",
				error=str(e),
			)
			# 优化5: 记录详细错误信息
			self.error_handler.handle_error(
				e, 
				context={'operation': 'load_module_configs'},
				recovery_strategy=ErrorRecoveryStrategy.FALLBACK
			)
	
	def set_performance_metrics(self, metrics: Any) -> None:
		self.performance_metrics = metrics
		self.logger.performance_metrics = metrics

	def import_module(self, module_name: str, fallback_modules: Optional[List[str]] = None) -> Dict[str, Any]:
		"""
		智能导入模块 - 优化版本：增强日志记录和错误处理
		
		Args:
			module_name: 模块名称
			fallback_modules: 备用模块列表
			
		Returns:
			导入结果字典
		"""
		start_time = time.perf_counter()
		
		try:
			self._stats['total_imports'] += 1
			
			self.logger.log_from_template(
				"module_import_start",
				module_name=module_name,
				fallbacks=fallback_modules or [],
			)
			
			cache_key = f"module_import_{module_name}"
			cached_result = self.cache_manager.get(cache_key)
			if cached_result is not None:
				self._stats['cache_hits'] += 1
				self.logger.log_from_template(
					"module_import_cache_hit",
					module_name=module_name,
				)
				cached_result = cached_result.copy()
				cached_result['cached'] = True
				cached_result['elapsed_ms'] = 0
				cached_result['cache_hit'] = True
				return cached_result
			
			# 旧缓存逻辑已移除，统一使用UnifiedCacheManager
			
			# 尝试配置的路径
			if module_name in self._module_paths:
				module_config = self._module_paths[module_name]
				self.logger.log_from_template(
					"module_import_path_attempt",
					module_name=module_name,
					module_path=module_config['path'],
				)
				
				path_result = self._try_import_from_path(module_name, module_config['path'])
				result = self._finalize_import_result(
					path_result,
					module_name,
					import_method="configured_path",
					start_time=start_time,
				)
				
				if result['success']:
					self._stats['successful_imports'] += 1
					self.cache_manager.set(cache_key, result, ttl=7200)  # 2小时过期
					return result
				else:
					self.logger.log_from_template(
						"module_import_path_failure",
						module_name=module_name,
						module_path=module_config['path'],
						error_code=result.get('error_code', self.ERROR_CODES['UNKNOWN_ERROR']),
						error_message=result.get('message', ''),
					)
					
		except ImportError as e:
			try:
				result = {
					'success': False,
					'error_code': self.ERROR_CODES['IMPORT_ERROR'],
					'message': f'导入失败: {e}',
					'attempted_paths': [module_path],
					'used_fallback': False
				}
				self.logger.log_from_template(
					"module_import_failure",
					module_name=module_name,
					import_method="configured_path",
					error_code=self.ERROR_CODES['IMPORT_ERROR'],
					error_message=str(e),
					duration_ms=0,
				)
				return result
			except Exception as e:
				self.logger.log_from_template(
					"module_import_failure",
					module_name=module_name,
					import_method="configured_path",
					error_code=self.ERROR_CODES['UNKNOWN_ERROR'],
					error_message=str(e),
					duration_ms=0,
				)
				return {
					'success': False,
					'module': module_name,
					'path': '',  # 修复：添加path字段
					'functions': {},  # 修复：添加functions字段
					'error_code': self.ERROR_CODES['UNKNOWN_ERROR'],
					'message': f'导入异常: {e}',
					'attempted_paths': [module_path],
					'used_fallback': False
				}
	
	def _import_markdown_processor(self) -> Dict[str, Any]:
		"""
		导入markdown_processor模块并进行完整性校验 - 优化版本：增强验证和错误处理
		
		Returns:
			导入结果
		"""
		try:
			from markdown_processor import render_markdown_with_zoom, render_markdown_to_html
			
			# 优化10: 增强的函数映射完整性校验 - 修复：与要求完全一致
			# 按照《增强修复方案.md》要求：仅当"拿到完整函数映射"才标记 success=True
			
			# 新增：从配置文件读取required_functions进行验证
			required_functions = self._get_required_functions('markdown_processor')
			self.logger.log_from_template(
				"module_import_validation",
				module_name="markdown_processor",
				required_functions=",".join(required_functions) or "(none)",
			)
			
			# 验证函数存在性和可调用性
			validation_result = self._validate_function_mapping(
				required_functions, 
				render_markdown_with_zoom, 
				render_markdown_to_html
			)
			
			if not validation_result['is_valid']:
				# 函数映射不完整，返回失败
				self.logger.log_from_template(
					"module_import_validation_failed",
					module_name="markdown_processor",
					details=validation_result['details'],
				)
				return {
					'success': False,
					'module': 'markdown_processor',
					'path': '',  # 修复：添加path字段
					'functions': {},  # 修复：添加functions字段
					'error_code': self.ERROR_CODES['MISSING_SYMBOLS'],
					'message': f'函数映射验证失败: {validation_result["details"]}',
					'attempted_paths': [],
					'used_fallback': False,
					'missing_functions': validation_result.get('missing_functions', []),
					'non_callable_functions': validation_result.get('non_callable_functions', []),
					'validation_details': validation_result['details'],
					'function_mapping_status': 'incomplete'
				}
			
			# 函数映射完整，创建函数映射
			function_map = {
				'render_markdown_with_zoom': render_markdown_with_zoom,
				'render_markdown_to_html': render_markdown_to_html
				}
			
			# 获取模块路径信息
			import_path = ""
			try:
				import markdown_processor
				import_path = getattr(markdown_processor, '__file__', 'unknown')
			except:
				import_path = "dynamic_import"
			
			# 优化12: 记录成功导入的详细信息
			self.logger.log_from_template(
				"module_import_validation_success",
				module_name="markdown_processor",
				module_path=import_path,
				available_functions=",".join(function_map.keys()),
			)
			# 仅当函数映射完整时才返回成功
			return {
				'success': True,
				'module': 'markdown_processor',
				'path': import_path,
				'functions': function_map,
				'used_fallback': False,
				'function_validation': 'passed',
				'validation_details': '所有必需函数都存在且可调用',
				'function_mapping_status': 'complete',
				'required_functions': required_functions,
				'available_functions': list(function_map.keys())
			}
			
		except ImportError as e:
			self.logger.log_from_template(
				"module_import_failure",
				module_name="markdown_processor",
				import_method="configured_path",
				error_code=self.ERROR_CODES['IMPORT_ERROR'],
				error_message=str(e),
				duration_ms=0,
			)
			return {
				'success': False,
				'module': 'markdown_processor',
				'path': '',  # 修复：添加path字段
				'functions': {},  # 修复：添加functions字段
				'error_code': self.ERROR_CODES['IMPORT_ERROR'],
				'message': f'无法导入markdown_processor: {e}',
				'attempted_paths': [],
				'used_fallback': False,
				'function_mapping_status': 'import_failed'
			}
	
	def _try_import_fallback(self, module_name: str, fallback_name: str) -> Dict[str, Any]:
		"""
		尝试导入fallback模块，明确标记fallback语义 - 优化版本：增强日志记录
		
		Args:
			module_name: 原始模块名称
			fallback_name: 备用模块名称
			
		Returns:
			导入结果
		"""
		try:
			if fallback_name == 'markdown':
				import markdown
				# 明确fallback语义：成功但不提供functions映射
				self.logger.log_from_template(
					"module_import_fallback",
					module_name=module_name,
					fallback_name=fallback_name,
					fallback_status="success",
					duration_ms=0,
				)
				return {
					'success': True,
					'module': 'markdown',
					'path': 'builtin',  # 修复：添加path字段
					'used_fallback': True,
					'fallback_reason': f'原始模块 {module_name} 导入失败，使用备用库',
					'functions': {},  # fallback不提供函数映射
					'fallback_details': '内置markdown库'
				}
			# 可以添加更多fallback模块
		except ImportError as e:
			self.logger.log_from_template(
				"module_import_fallback_failure",
				module_name=module_name,
				fallback_name=fallback_name,
				error_message=str(e),
			)
			return {
				'success': False,
				'module': fallback_name,  # 修复：添加module字段
				'path': '',  # 修复：添加path字段
				'functions': {},  # 修复：添加functions字段
				'error_code': self.ERROR_CODES['IMPORT_ERROR'],
				'message': f'fallback模块导入失败: {fallback_name} - {e}',
				'used_fallback': True
			}
	
	def _finalize_import_result(
		self,
		result: Dict[str, Any],
		module_name: str,
		import_method: str,
		start_time: float,
	) -> Dict[str, Any]:
		"""统一收敛导入结果，输出结构化日志并记录性能指标。"""
		elapsed_ms = result.get('elapsed_ms')
		if elapsed_ms is None:
			elapsed_ms = max(0.0, (time.perf_counter() - start_time) * 1000)
		result['elapsed_ms'] = elapsed_ms
		result['import_method'] = import_method
		
		if self.performance_metrics:
			try:
				self.performance_metrics.record_histogram(
					"module_import.duration_ms",
					elapsed_ms,
					{
						"module": module_name,
						"method": import_method,
						"success": result.get('success', False),
						"used_fallback": result.get('used_fallback', False),
					},
				)
			except Exception:
				pass
		
		context_duration = round(elapsed_ms, 2)
		if result.get('success'):
			self.logger.log_from_template(
				"module_import_success",
				module_name=module_name,
				import_method=import_method,
				duration_ms=context_duration,
				used_fallback=result.get('used_fallback', False),
			)
			if result.get('used_fallback'):
				fallback_name = import_method.split(":", 1)[1] if ":" in import_method else import_method
				self.logger.log_from_template(
					"module_import_fallback",
					module_name=module_name,
					fallback_name=fallback_name,
					fallback_status="success",
					duration_ms=context_duration,
				)
		else:
			error_code = result.get('error_code') or self.ERROR_CODES['UNKNOWN_ERROR']
			error_message = result.get('message', 'unknown')
			self.logger.log_from_template(
				"module_import_failure",
				module_name=module_name,
				import_method=import_method,
				error_code=error_code,
				error_message=error_message,
				duration_ms=context_duration,
			)
			if result.get('used_fallback'):
				fallback_name = import_method.split(":", 1)[1] if ":" in import_method else import_method
				self.logger.log_from_template(
					"module_import_fallback",
					module_name=module_name,
					fallback_name=fallback_name,
					fallback_status="failure",
					duration_ms=context_duration,
				)
		self._save_module_snapshot(module_name, result, import_method, elapsed_ms)
		return result
	# 新增：获取模块的必需函数列表
	def _get_required_functions(self, module_name: str) -> List[str]:
		"""
		从配置文件获取模块的必需函数列表
		
		Args:
			module_name: 模块名称
			
		Returns:
			必需函数列表
		"""
		try:
			if module_name in self._module_paths:
				module_config = self._module_paths[module_name]
				return module_config.get('required_functions', [])
			return []
		except Exception as e:
			self.logger.warning(f"获取必需函数列表失败: {e}")
			return []
	
	# 新增：验证函数映射完整性
	def _validate_function_mapping(self, required_functions: List[str], 
								 render_markdown_with_zoom, 
								 render_markdown_to_html) -> Dict[str, Any]:
		"""
		验证函数映射的完整性
		
		Args:
			required_functions: 必需函数列表
			render_markdown_with_zoom: 缩放渲染函数
			render_markdown_to_html: HTML渲染函数
			
		Returns:
			验证结果
		"""
		validation_result = {
			'is_valid': True,
			'details': '验证通过',
			'missing_functions': [],
			'non_callable_functions': [],
			'validation_summary': {}
		}
		
		# 验证render_markdown_with_zoom
		if 'render_markdown_with_zoom' in required_functions:
			if render_markdown_with_zoom is None:
				validation_result['missing_functions'].append('render_markdown_with_zoom')
				validation_result['validation_summary']['render_markdown_with_zoom'] = 'missing'
			elif not callable(render_markdown_with_zoom):
				validation_result['non_callable_functions'].append('render_markdown_with_zoom')
				validation_result['validation_summary']['render_markdown_with_zoom'] = 'not_callable'
			else:
				validation_result['validation_summary']['render_markdown_with_zoom'] = 'valid'
		
		# 验证render_markdown_to_html
		if 'render_markdown_to_html' in required_functions:
			if render_markdown_to_html is None:
				validation_result['missing_functions'].append('render_markdown_to_html')
				validation_result['validation_summary']['render_markdown_to_html'] = 'missing'
			elif not callable(render_markdown_to_html):
				validation_result['non_callable_functions'].append('render_markdown_to_html')
				validation_result['validation_summary']['render_markdown_to_html'] = 'not_callable'
			else:
				validation_result['validation_summary']['render_markdown_to_html'] = 'valid'
		
		# 检查是否有验证失败的情况
		if validation_result['missing_functions'] or validation_result['non_callable_functions']:
			validation_result['is_valid'] = False
			
			if validation_result['missing_functions']:
				validation_result['details'] = f"缺少函数: {', '.join(validation_result['missing_functions'])}"
			elif validation_result['non_callable_functions']:
				validation_result['details'] = f"函数不可调用: {', '.join(validation_result['non_callable_functions'])}"
		
		return validation_result
	
	def _resolve_module_path(self, module_path: str) -> Optional[Path]:
		"""
		解析模块路径
		
		Args:
			module_path: 模块路径字符串
			
		Returns:
			解析后的Path对象
		"""
		try:
			if module_path.startswith('.'):
				# 相对路径
				base_path = Path(__file__).parent.parent.parent
				return base_path / module_path.lstrip('./')
			else:
				# 绝对路径
				return Path(module_path)
		except Exception as e:
			self.logger.error(f"路径解析失败: {e}")
			return None
	
	@contextmanager
	def _temp_sys_path(self, path: str):
		"""
		临时修改sys.path的上下文管理器
		
		Args:
			path: 要添加的路径
		"""
		original_path = sys.path.copy()
		try:
			sys.path.insert(0, path)
			yield
		finally:
			sys.path[:] = original_path
	
	def clear_cache(self):
		"""清空导入缓存"""
		# 清空统一缓存管理器
		self.cache_manager.clear()
		self.logger.info("动态模块导入缓存已清空")
	
	def get_import_status(self) -> Dict[str, Any]:
		"""
		获取导入状态
		
		Returns:
			状态信息字典
		"""
		# 获取统一缓存管理器统计信息
		unified_stats = self.cache_manager.get_stats()
		
		# 获取错误统计信息
		error_stats = self.error_handler.get_error_stats()
		
		return {
			'cached_modules': self.cache_manager.get_keys(),
			'configured_paths': self._module_paths,
			'total_imports': self._stats['total_imports'],
			'successful_imports': self._stats['successful_imports'],
			'failed_imports': self._stats['failed_imports'],
			'cache_hits': self._stats['cache_hits'],
			'fallback_usage': self._stats['fallback_usage'],
			'unified_cache_stats': {
				'total_entries': unified_stats.total_entries,
				'hit_rate': unified_stats.hit_rate,
				'hit_count': unified_stats.hit_count,
				'miss_count': unified_stats.miss_count,
				'eviction_count': unified_stats.eviction_count,
				'memory_usage_mb': unified_stats.memory_usage,
				'strategy': self.cache_manager.strategy.value
			},
			'legacy_cache_removed': True,  # 旧缓存系统已移除
			'error_stats': error_stats.to_dict()  # 错误统计信息
		}
	
	def get_module_config(self, module_name: str) -> Optional[Dict[str, Any]]:
		"""
		获取模块配置
		
		Args:
			module_name: 模块名称
			
		Returns:
			模块配置字典
		"""
		return self._module_paths.get(module_name)

	# === V4.2 扩展：correlation_id注入/读取 ===
	def set_correlation_id(self, correlation_id: str) -> None:
		"""
		设置当前操作的correlation_id，供快照与日志关联。
		"""
		self._correlation_id = correlation_id
		self.logger.set_correlation_id(correlation_id, operation="module_import", component="dynamic_module_importer")

	def get_correlation_id(self) -> Optional[str]:
		"""获取当前关联的correlation_id。"""
		return getattr(self, "_correlation_id", None)

	# === V4.2 扩展：获取不可调用的函数名列表 ===
	def _get_non_callable_functions(self, module_obj) -> List[str]:
		import inspect
		names: List[str] = []
		for name in dir(module_obj):
			try:
				attr = getattr(module_obj, name, None)
				if not callable(attr) and not name.startswith("__"):
					names.append(name)
			except Exception:
				continue
		return names

	# === V4.2 扩展：返回最后一次导入的标准化快照（11字段） ===
	def get_last_import_snapshot(self, module_name: str = "markdown_processor") -> Dict[str, Any]:
		"""返回标准module_import_snapshot（若无记录则返回空）。"""
		snapshot_manager = getattr(self, "snapshot_manager", None)
		if snapshot_manager:
			return snapshot_manager.get_module_snapshot(module_name)
		cache_key = f"import_result_{module_name}"
		data = self.cache_manager.get(cache_key)
		if not data:
			return {}
		return {
            "snapshot_type": "module_import_snapshot",
            "module": data.get("module", module_name),
            "function_mapping_status": data.get("function_mapping_status", ""),
            "required_functions": data.get("required_functions", []),
            "available_functions": data.get("available_functions", data.get("function_names", [])),
            "missing_functions": data.get("missing_functions", []),
            "non_callable_functions": data.get("non_callable_functions", []),
            "path": data.get("path", ""),
            "used_fallback": data.get("used_fallback", False),
            "error_code": data.get("error_code", ""),
            "message": data.get("message", ""),
            "timestamp": data.get("timestamp", __import__("datetime").datetime.now().isoformat()),
            "correlation_id": self.get_correlation_id() or data.get("correlation_id", ""),
        }
	
	def is_module_configured(self, module_name: str) -> bool:
		"""
		检查模块是否已配置
		
		Args:
			module_name: 模块名称
			
		Returns:
			是否已配置
		"""
		return module_name in self._module_paths
	
	def reload_config(self):
		"""重新加载配置"""
		self._module_paths.clear()
		self._load_module_configs()
		self.logger.info("模块配置已重新加载")
	
	def get_error_history(self, limit: int = 50) -> List[Dict[str, Any]]:
		"""
		获取错误历史
		
		Args:
			limit: 返回数量限制
			
		Returns:
			错误历史列表
		"""
		return self.error_handler.get_error_history(limit)
	
	def save_error_report(self, filename: Optional[str] = None) -> bool:
		"""
		保存错误报告
		
		Args:
			filename: 文件名
			
		Returns:
			是否保存成功
		"""
		return self.error_handler.save_error_report(filename)
	
	def generate_function_mapping_report(self) -> Dict[str, Any]:
		"""
		生成函数映射完整性报告
		
		Returns:
			报告字典
		"""
		report = {
			'total_modules_configured': len(self._module_paths),
			'module_reports': {}
		}
		
		for module_name, module_config in self._module_paths.items():
			report['module_reports'][module_name] = {
				'path': module_config['path'],
				'required_functions': module_config['required_functions'],
				'validation_status': 'Not checked'
			}
			
			if module_name == 'markdown_processor':
				try:
					from markdown_processor import render_markdown_with_zoom, render_markdown_to_html
					required_functions = module_config['required_functions']
					validation_result = self._validate_function_mapping(
						required_functions, 
						render_markdown_with_zoom, 
						render_markdown_to_html
					)
					report['module_reports'][module_name]['validation_status'] = {
						'is_valid': validation_result['is_valid'],
						'details': validation_result['details'],
						'missing_functions': validation_result['missing_functions'],
						'non_callable_functions': validation_result['non_callable_functions'],
						'validation_summary': validation_result['validation_summary']
					}
				except ImportError:
					report['module_reports'][module_name]['validation_status'] = {
						'is_valid': False,
						'details': 'markdown_processor模块未导入，无法验证',
						'missing_functions': [],
						'non_callable_functions': [],
						'validation_summary': {}
					}
				except Exception as e:
					report['module_reports'][module_name]['validation_status'] = {
						'is_valid': False,
						'details': f'验证失败: {e}',
						'missing_functions': [],
						'non_callable_functions': [],
						'validation_summary': {}
					}
		
		return report
	
	def shutdown(self):
		"""关闭导入器，释放所有资源"""
		try:
			# 关闭错误处理器
			if hasattr(self, 'error_handler'):
				self.error_handler.shutdown()
			
			# 关闭统一缓存管理器
			if hasattr(self, 'cache_manager'):
				self.cache_manager.shutdown()
			
			self.logger.info("动态模块导入器已关闭，所有资源已释放")
			
		except Exception as e:
			self.logger.error(f"关闭导入器时出现错误: {e}")
	
	def __del__(self):
		"""析构函数，确保资源被释放"""
		try:
			self.shutdown()
		except:
			pass  # 析构函数中忽略异常 

	def set_snapshot_manager(self, snapshot_manager: Any) -> None:
		self.snapshot_manager = snapshot_manager

	def _save_module_snapshot(self, module_name: str, result: Dict[str, Any], import_method: str, elapsed_ms: float) -> None:
		if not self.snapshot_manager:
			return
		try:
			required_functions = result.get('required_functions')
			if required_functions is None:
				required_functions = self._module_paths.get(module_name, {}).get('required_functions', [])
			available_functions = result.get('available_functions')
			if available_functions is None and isinstance(result.get('functions'), dict):
				available_functions = list(result['functions'].keys())
			missing_functions = result.get('missing_functions') or []
			non_callable = result.get('non_callable_functions') or []
			status = result.get('function_mapping_status') or ('complete' if result.get('success') else 'import_failed')
			snapshot_payload = {
				"module": module_name,
				"function_mapping_status": status,
				"required_functions": list(required_functions or []),
				"available_functions": list(available_functions or []),
				"missing_functions": list(missing_functions),
				"non_callable_functions": list(non_callable),
				"path": result.get('path', ''),
				"used_fallback": result.get('used_fallback', False),
				"error_code": result.get('error_code', ''),
				"message": result.get('message', ''),
				"timestamp": result.get('timestamp') or datetime.now(timezone.utc).isoformat(),
				"correlation_id": self.get_correlation_id() or result.get('correlation_id', ''),
				"import_method": import_method,
				"elapsed_ms": elapsed_ms,
			}
			self.snapshot_manager.save_module_snapshot(module_name, snapshot_payload)
		except Exception:
			pass

	def set_performance_metrics(self, metrics: Any) -> None:
		self.performance_metrics = metrics