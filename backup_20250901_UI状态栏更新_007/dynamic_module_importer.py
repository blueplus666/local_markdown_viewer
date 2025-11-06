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
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from contextlib import contextmanager

# 导入统一缓存管理器
from .unified_cache_manager import UnifiedCacheManager, CacheStrategy
from .enhanced_error_handler import EnhancedErrorHandler, ErrorRecoveryStrategy

# 统一导入策略：优先相对导入，失败时使用绝对路径
try:
	from ..utils.config_manager import ConfigManager
except ImportError:
	# 备用：添加父目录到路径并导入
	sys.path.insert(0, str(Path(__file__).parent.parent))
	from utils.config_manager import ConfigManager


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
	
	def __init__(self, config_manager: Optional[ConfigManager] = None):
		"""
		初始化动态模块导入器
		
		Args:
			config_manager: 配置管理器实例
		"""
		self.config_manager = config_manager or ConfigManager()
		self.logger = logging.getLogger(__name__)
		
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
	
	def _load_module_configs(self):
		"""加载模块配置 - 优化版本：增强与external_modules.json的兼容性"""
		try:
			# 清空后重新加载，避免旧配置残留
			self._module_paths.clear()
			
			# 优化1: 优先尝试直接读取external_modules.json
			config_file_path = Path(__file__).parent.parent / "config" / "external_modules.json"
			if config_file_path.exists():
				try:
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
							
							# 优化2: 增强日志记录
							self.logger.info(f"从external_modules.json加载配置成功: {module_path}")
							self.logger.info(f"必需函数: {md_config.get('required_functions', [])}")
							self.logger.info(f"Fallback启用: {md_config.get('fallback_enabled', True)}")
							
							return  # 成功加载，直接返回
							
				except Exception as e:
					self.logger.warning(f"直接读取external_modules.json失败: {e}")
			
			# 优化3: 降级到ConfigManager（向后兼容）
			self.logger.info("尝试通过ConfigManager加载配置...")
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
					self.logger.info(f"通过ConfigManager加载配置成功: {module_path}")
			
			# 优化4: 配置验证和统计
			if self._module_paths:
				self.logger.info(f"成功加载了 {len(self._module_paths)} 个模块配置")
				for name, config in self._module_paths.items():
					self.logger.info(f"  - {name}: {config['path']} (优先级: {config['priority']})")
			else:
				self.logger.warning("未加载到任何模块配置")
			
		except Exception as e:
			self.logger.error(f"加载模块配置失败: {e}")
			# 优化5: 记录详细错误信息
			self.error_handler.handle_error(
				e, 
				context={'operation': 'load_module_configs'},
				recovery_strategy=ErrorRecoveryStrategy.FALLBACK
			)
	
	def import_module(self, module_name: str, fallback_modules: Optional[List[str]] = None) -> Dict[str, Any]:
		"""
		智能导入模块 - 优化版本：增强日志记录和错误处理
		
		Args:
			module_name: 模块名称
			fallback_modules: 备用模块列表
			
		Returns:
			导入结果字典
		"""
		start_time = time.time()
		
		try:
			self._stats['total_imports'] += 1
			
			# 优化6: 增强日志记录
			self.logger.info(f"开始导入模块: {module_name}")
			if fallback_modules:
				self.logger.info(f"备用模块: {fallback_modules}")
			
			# 检查缓存
			cache_key = f"module_import_{module_name}"
			
			# 使用统一缓存管理器
			cached_result = self.cache_manager.get(cache_key)
			if cached_result is not None:
				self._stats['cache_hits'] += 1
				self.logger.info(f"模块 {module_name} 从缓存加载成功")
				cached_result = cached_result.copy()
				cached_result['cached'] = True
				cached_result['elapsed_ms'] = 0
				cached_result['cache_hit'] = True
				return cached_result
			
			# 旧缓存逻辑已移除，统一使用UnifiedCacheManager
			
			# 尝试配置的路径
			if module_name in self._module_paths:
				module_config = self._module_paths[module_name]
				self.logger.info(f"尝试从配置路径导入: {module_config['path']}")
				
				result = self._try_import_from_path(module_name, module_config['path'])
				
				# 优化7: 增强结果日志记录
				self._log_import_result(result, module_name, "配置路径导入")
				
				if result['success']:
					self._stats['successful_imports'] += 1
					self.logger.info(f"模块 {module_name} 导入成功")
					
					# 使用统一缓存管理器
					self.cache_manager.set(cache_key, result, ttl=7200)  # 2小时过期
					
					# 旧缓存逻辑已移除
					result['elapsed_ms'] = (time.time() - start_time) * 1000
					return result
				else:
					self.logger.warning(f"模块 {module_name} 从配置路径导入失败: {result.get('message', '未知错误')}")
			
			# 尝试fallback模块
			if fallback_modules:
				self.logger.info(f"开始尝试fallback模块: {fallback_modules}")
				for fallback in fallback_modules:
					self.logger.info(f"尝试fallback模块: {fallback}")
					result = self._try_import_fallback(module_name, fallback)
					
					# 优化8: 增强fallback结果日志记录
					self._log_import_result(result, module_name, f"fallback导入({fallback})")
					
					if result['success']:
						self._stats['successful_imports'] += 1
						self._stats['fallback_usage'] += 1
						self.logger.info(f"模块 {module_name} 通过fallback {fallback} 导入成功")
						
						# 使用统一缓存管理器
						self.cache_manager.set(cache_key, result, ttl=7200)  # 2小时过期
						
						# 旧缓存逻辑已移除
						result['elapsed_ms'] = (time.time() - start_time) * 1000
						return result
			
			# 完全失败
			self._stats['failed_imports'] += 1
			failure_result = {
				'success': False,
				'error_code': self.ERROR_CODES['UNKNOWN_ERROR'],
				'message': '所有导入方式都失败',
				'attempted_paths': [info['path'] for info in self._module_paths.values()],
				'used_fallback': False,
				'elapsed_ms': (time.time() - start_time) * 1000
			}
			
			# 优化9: 记录失败详情
			self.logger.error(f"模块 {module_name} 所有导入方式都失败")
			self.logger.error(f"尝试的路径: {failure_result['attempted_paths']}")
			self.logger.error(f"尝试的fallback: {fallback_modules or []}")
			
			return failure_result
			
		except Exception as e:
			self._stats['failed_imports'] += 1
			
			# 使用增强错误处理器
			error_info = self.error_handler.handle_error(
				e, 
				context={'operation': 'module_import', 'module_name': module_name, 'fallback_modules': fallback_modules},
				recovery_strategy=ErrorRecoveryStrategy.FALLBACK
			)
			
			self.logger.error(f"模块导入异常: {e}")
			return {
				'success': False,
				'error_code': self.ERROR_CODES['UNKNOWN_ERROR'],
				'message': str(e),
				'attempted_paths': [],
				'used_fallback': False,
				'elapsed_ms': (time.time() - start_time) * 1000,
				'error_id': error_info.error_id,
				'error_category': error_info.category.value
			}
	
	def _try_import_from_path(self, module_name: str, module_path: str) -> Dict[str, Any]:
		"""
		尝试从指定路径导入模块 - 优化版本：增强错误处理和日志记录
		
		Args:
			module_name: 模块名称
			module_path: 模块路径
			
		Returns:
			导入结果
		"""
		try:
			# 解析路径
			resolved_path = self._resolve_module_path(module_path)
			if not resolved_path or not resolved_path.exists():
				error_result = {
					'success': False,
					'error_code': self.ERROR_CODES['PATH_NOT_FOUND'],
					'message': f'模块路径不存在: {module_path}',
					'attempted_paths': [module_path],
					'used_fallback': False
				}
				self.logger.error(f"路径解析失败: {module_path}")
				return error_result
			
			# 使用上下文管理器临时修改sys.path
			with self._temp_sys_path(str(resolved_path)):
				# 尝试导入
				if module_name == 'markdown_processor':
					result = self._import_markdown_processor()
					# 如果导入成功，添加路径信息
					if result['success']:
						result['path'] = str(resolved_path)
					return result
				else:
					# 通用导入
					module = __import__(module_name)
					return {
						'success': True,
						'module': module,
						'path': str(resolved_path),
						'used_fallback': False
					}
					
		except ImportError as e:
			error_result = {
				'success': False,
				'error_code': self.ERROR_CODES['IMPORT_ERROR'],
				'message': f'导入失败: {e}',
				'attempted_paths': [module_path],
				'used_fallback': False
			}
			self.logger.error(f"导入失败: {e}")
			return error_result
		except Exception as e:
			error_result = {
				'success': False,
				'error_code': self.ERROR_CODES['UNKNOWN_ERROR'],
				'message': f'导入异常: {e}',
				'attempted_paths': [module_path],
				'used_fallback': False
			}
			self.logger.error(f"导入异常: {e}")
			return error_result
	
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
			self.logger.info(f"验证必需函数: {required_functions}")
			
			# 验证函数存在性和可调用性
			validation_result = self._validate_function_mapping(
				required_functions, 
				render_markdown_with_zoom, 
				render_markdown_to_html
			)
			
			if not validation_result['is_valid']:
				# 函数映射不完整，返回失败
				self.logger.error(f"函数映射验证失败: {validation_result['details']}")
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
			self.logger.info(f"markdown_processor导入成功")
			self.logger.info(f"  - 模块文件: {import_path}")
			self.logger.info(f"  - 可用函数: {list(function_map.keys())}")
			self.logger.info(f"  - 函数验证: 通过")
			self.logger.info(f"  - 函数映射状态: 完整")
			
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
			self.logger.error(f"无法导入markdown_processor: {e}")
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
				self.logger.info(f"fallback命中: 使用内置markdown库")
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
			self.logger.error(f"fallback模块导入失败: {fallback_name} - {e}")
			return {
				'success': False,
				'module': fallback_name,  # 修复：添加module字段
				'path': '',  # 修复：添加path字段
				'functions': {},  # 修复：添加functions字段
				'error_code': self.ERROR_CODES['IMPORT_ERROR'],
				'message': f'fallback模块导入失败: {fallback_name} - {e}',
				'used_fallback': True
			}
	
	# 优化13: 新增结构化日志记录方法
	def _log_import_result(self, result: Dict[str, Any], module_name: str, import_method: str):
		"""
		记录导入结果的详细信息并保存到缓存
		
		Args:
			result: 导入结果
			module_name: 模块名称
			import_method: 导入方法
		"""
		from datetime import datetime
		
		# 创建可序列化的缓存数据
		cache_data = {
			'module': result.get('module', ''),
			'path': result.get('path', ''),
			'used_fallback': result.get('used_fallback', False),
			'function_mapping_status': result.get('function_mapping_status', ''),
			'required_functions': result.get('required_functions', []),
			'available_functions': result.get('available_functions', []),
			'error_code': result.get('error_code', ''),
			'message': result.get('message', ''),
			'import_method': import_method,
			'timestamp': datetime.now().isoformat()
		}
		
		# 如果functions存在，只保存函数名列表
		if 'functions' in result and result['functions']:
			cache_data['function_names'] = list(result['functions'].keys())
		else:
			cache_data['function_names'] = []
		
		# 保存到缓存
		cache_key = f"import_result_{result.get('module', 'unknown')}"
		try:
			self.cache_manager.set(cache_key, cache_data)
			self.logger.debug(f"缓存导入结果: {cache_key}")
		except Exception as e:
			self.logger.warning(f"缓存保存失败: {e}")
		
		# 记录导入结果日志
		self.logger.info(f"导入结果记录 - 模块: {module_name}, 方法: {import_method}")
		self.logger.info(f"  - 成功状态: {result.get('success', False)}")
		self.logger.info(f"  - 模块路径: {result.get('path', 'unknown')}")
		self.logger.info(f"  - 是否fallback: {result.get('used_fallback', False)}")
		
		if result.get('success'):
			self.logger.info(f"  - 可用函数: {list(result.get('functions', {}).keys())}")
			if 'function_mapping_status' in result:
				self.logger.info(f"  - 函数映射状态: {result['function_mapping_status']}")
		else:
			self.logger.info(f"  - 错误码: {result.get('error_code', 'unknown')}")
			self.logger.info(f"  - 错误消息: {result.get('message', 'unknown')}")
			if 'missing_functions' in result and result['missing_functions']:
				self.logger.info(f"  - 缺失函数: {result['missing_functions']}")
			if 'non_callable_functions' in result and result['non_callable_functions']:
				self.logger.info(f"  - 不可调用函数: {result['non_callable_functions']}")
		
		# 记录导入结果到INFO级别日志
		self.logger.info(f"导入结果: module={result.get('module')}, "
		                f"status={result.get('function_mapping_status')}, "
		                f"fallback={result.get('used_fallback')}")
	
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