#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器模块 v1.0.0
负责加载和管理应用的所有配置文件
包括应用配置、界面配置、文件类型配置等

作者: LAD Team
创建时间: 2025-01-08
最后更新: 2025-01-08
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union


class ConfigManager:
    """
    配置管理器类
    统一管理应用的所有配置文件，提供配置的读取、写入和验证功能
    """
    
    def __init__(self, config_dir: str = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录路径，默认为当前目录下的config文件夹
        """
        # 设置配置文件目录
        if config_dir is None:
            # 获取当前文件所在目录的上级目录下的config文件夹
            current_dir = Path(__file__).parent
            self.config_dir = current_dir.parent / "config"
        else:
            self.config_dir = Path(config_dir)
        
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化配置字典
        self._app_config = {}
        self._ui_config = {}
        self._file_types_config = {}
        self._config_cache = {}  # V2.1: 统一配置缓存
        self._change_listeners = []  # 可选：配置热重载监听
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 加载所有配置文件
        self._load_all_configs()
    
    def _load_all_configs(self):
        """加载所有配置文件"""
        try:
            self._load_app_config()
            self._load_ui_config()
            self._load_file_types_config()
            # 额外加载 features/runtime 等扩展配置（存在则缓存）
            self._ensure_optional_config("features/logging.json")
            self._ensure_optional_config("runtime/performance.json")
            self.logger.info("所有配置文件加载成功")
        except Exception as e:
            self.logger.error(f"配置文件加载失败: {e}")
            # 如果配置文件不存在，创建默认配置
            self._create_default_configs()
    
    def _load_app_config(self):
        """加载应用配置文件"""
        config_file = self.config_dir / "app_config.json"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                self._app_config = json.load(f)
        else:
            self.logger.warning("应用配置文件不存在，将创建默认配置")
            self._create_default_app_config()
    
    def _load_ui_config(self):
        """加载界面配置文件"""
        config_file = self.config_dir / "ui_config.json"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                self._ui_config = json.load(f)
        else:
            self.logger.warning("界面配置文件不存在，将创建默认配置")
            self._create_default_ui_config()
    
    def _load_file_types_config(self):
        """加载文件类型配置文件"""
        config_file = self.config_dir / "file_types.json"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                self._file_types_config = json.load(f)
        else:
            self.logger.warning("文件类型配置文件不存在，将创建默认配置")
            self._create_default_file_types_config()
    
    def get_config(self, key: str, default: Any = None, config_type: str = "app") -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键，支持点号分隔的嵌套键，如 "app.name"
            default: 默认值
            config_type: 配置类型，可选值: "app", "ui", "file_types"
            
        Returns:
            配置值
        """
        try:
            # 向后兼容：直接返回完整配置对象
            if key in ("app_config", "app"):
                return self._app_config if self._app_config else default
            if key in ("ui_config", "ui"):
                return self._ui_config if self._ui_config else default
            if key in ("file_types_config", "file_types"):
                return self._file_types_config if self._file_types_config else default
            if key == "external_modules":
                data = self._load_config_file("external_modules")
                return data if data is not None else default

            config_dict = self._get_config_dict(config_type)
            if not config_dict:
                return default

            # 支持嵌套键访问
            keys = key.split('.')
            value = config_dict
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            self.logger.warning(f"配置项 {key} 不存在，返回默认值: {default}")
            return default
    
    def set_config(self, key: str, value: Any, config_type: str = "app") -> bool:
        """
        设置配置项
        
        Args:
            key: 配置键
            value: 配置值
            config_type: 配置类型
            
        Returns:
            是否设置成功
        """
        try:
            config_dict = self._get_config_dict(config_type)
            if not config_dict:
                return False
            
            # 支持嵌套键设置
            keys = key.split('.')
            target_dict = config_dict
            for k in keys[:-1]:
                if k not in target_dict:
                    target_dict[k] = {}
                target_dict = target_dict[k]
            
            target_dict[keys[-1]] = value
            
            # 保存配置
            self._save_config(config_type)
            self.logger.info(f"配置项 {key} 设置成功")
            return True
        except Exception as e:
            self.logger.error(f"设置配置项 {key} 失败: {e}")
            return False
    
    def _get_config_dict(self, config_type: str) -> Optional[Dict[str, Any]]:
        """获取指定类型的配置字典"""
        config_map = {
            "app": self._app_config,
            "ui": self._ui_config,
            "file_types": self._file_types_config
        }
        return config_map.get(config_type)

    def add_change_listener(self, callback):
        """注册配置变更回调（简化实现，未真正监听文件系统）。"""
        if callback not in self._change_listeners:
            self._change_listeners.append(callback)

    def _notify_change_listeners(self, config_name: str):
        """触发已注册的配置变更回调。"""
        for cb in list(self._change_listeners):
            try:
                cb(config_name)
            except Exception as exc:
                self.logger.warning(f"配置变更回调执行失败: {exc}")
    
    def load_ui_config(self) -> Dict[str, Any]:
        """加载界面配置"""
        return self._ui_config.copy()
    
    def load_file_types_config(self) -> Dict[str, Any]:
        """加载文件类型配置（实时刷新）。"""
        self._load_file_types_config()
        return json.loads(json.dumps(self._file_types_config))
    
    def update_config(self, key: str, value: Any, config_type: str = "app") -> bool:
        """
        更新配置项（配置文件内容修改）
        
        Args:
            key: 配置键
            value: 新值
            config_type: 配置类型
            
        Returns:
            是否更新成功
        """
        return self.set_config(key, value, config_type)
    
    def get_file_type_info(self, file_extension: str) -> Optional[Dict[str, Any]]:
        """
        根据文件扩展名获取文件类型信息
        
        Args:
            file_extension: 文件扩展名，如 ".md"
            
        Returns:
            文件类型信息字典，如果未找到返回None
        """
        for file_type, info in self._file_types_config.items():
            if file_extension.lower() in info.get("extensions", []):
                return info
        return None
    
    def get_markdown_config(self) -> Dict[str, Any]:
        """
        获取Markdown相关配置
        
        Returns:
            Markdown配置字典
        """
        return self._app_config.get("markdown", {})
    
    def get_markdown_module_path(self) -> str:
        """
        获取Markdown模块路径
        
        Returns:
            Markdown模块路径
        """
        # 优先从external_modules获取
        external_modules = self._app_config.get("external_modules", {})
        markdown_processor = external_modules.get("markdown_processor", {})
        
        if markdown_processor.get("enabled", False):
            return markdown_processor.get("module_path", "../../../lad_markdown_viewer")
        
        # 向后兼容：从markdown配置获取
        markdown_config = self.get_markdown_config()
        return markdown_config.get("module_path", "../../../lad_markdown_viewer")
    
    def get_external_module_config(self, module_name: str) -> Dict[str, Any]:
        """
        获取外部模块配置（V2.1更新：支持external_modules.json）
        
        Args:
            module_name: 模块名称，如 "markdown_processor"
            
        Returns:
            模块配置字典，如果不存在返回空字典
        """
        # V2.1: 优先从external_modules.json读取
        result = self.get_unified_config(
            f"external_modules.{module_name}",
            default={}
        )
        
        # 如果从external_modules.json读取失败，回退到app_config（向后兼容）
        if not result:
            external_modules = self._app_config.get("external_modules", {})
            result = external_modules.get(module_name, {})
        
        return result
    
    def is_external_module_enabled(self, module_name: str) -> bool:
        """
        检查外部模块是否启用
        
        Args:
            module_name: 模块名称
            
        Returns:
            是否启用
        """
        module_config = self.get_external_module_config(module_name)
        return module_config.get("enabled", False) if module_config else False
    
    def get_external_module_path(self, module_name: str) -> Optional[str]:
        """
        获取外部模块路径
        
        Args:
            module_name: 模块名称
            
        Returns:
            模块路径，如果未找到返回None
        """
        module_config = self.get_external_module_config(module_name)
        return module_config.get("module_path") if module_config else None
    
    def is_markdown_fallback_enabled(self) -> bool:
        """
        检查是否启用Markdown降级功能
        
        Returns:
            是否启用降级功能
        """
        markdown_config = self.get_markdown_config()
        return markdown_config.get("fallback_enabled", True)
    
    def is_markdown_cache_enabled(self) -> bool:
        """
        检查是否启用Markdown缓存功能
        
        Returns:
            是否启用缓存功能
        """
        markdown_config = self.get_markdown_config()
        return markdown_config.get("cache_enabled", True)
    
    def _create_default_configs(self):
        """创建默认配置文件"""
        self._create_default_app_config()
        self._create_default_ui_config()
        self._create_default_file_types_config()
    
    def _create_default_app_config(self):
        """创建默认应用配置"""
        self._app_config = {
            "app": {
                "name": "本地Markdown文件渲染器",
                "version": "1.0.0",
                "description": "基于PyQt5的本地Markdown文件渲染和文档管理工具",
                "author": "LAD Team",
                "default_root_path": str(Path.home()),
                "window": {
                    "width": 1200,
                    "height": 800,
                    "min_width": 800,
                    "min_height": 600,
                    "title": "本地Markdown文件渲染器 v1.0.0"
                }
            },
            "file_tree": {
                "show_hidden_files": False,
                "file_filters": ["*.md", "*.txt", "*.py", "*.json"],
                "exclude_patterns": ["*.log", "*.tmp", "__pycache__"],
                "max_file_size": 10485760
            },
            "markdown": {
                "enable_zoom": True,
                "enable_syntax_highlight": True,
                "theme": "default",
                "auto_reload": False,
                "max_content_length": 5242880
            },
            "logging": {
                "level": "INFO",
                "file": "app.log",
                "max_size": 10485760,
                "backup_count": 5
            }
        }
        self._save_app_config()
    
    def _create_default_ui_config(self):
        """创建默认界面配置"""
        self._ui_config = {
            "layout": {
                "left_panel_width": 300,
                "right_panel_width": "auto",
                "splitter_handle_width": 4
            },
            "colors": {
                "primary": "#2196f3",
                "secondary": "#f5f5f5",
                "text": "#333333",
                "background": "#ffffff"
            },
            "fonts": {
                "main": "微软雅黑",
                "code": "Consolas",
                "size": 14
            }
        }
        self._save_ui_config()
    
    def _create_default_file_types_config(self):
        """创建默认文件类型配置"""
        self._file_types_config = {
            "markdown_files": {
                "extensions": [".md", ".markdown", ".mdown"],
                "renderer": "markdown",
                "preview_mode": "rendered"
            },
            "text_files": {
                "extensions": [".txt", ".log", ".ini", ".cfg"],
                "renderer": "text",
                "preview_mode": "raw"
            },
            "code_files": {
                "extensions": [".py", ".js", ".html", ".css", ".json"],
                "renderer": "syntax_highlight",
                "preview_mode": "highlighted"
            }
        }
        self._save_file_types_config()
    
    def _save_app_config(self):
        """保存应用配置"""
        config_file = self.config_dir / "app_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self._app_config, f, indent=2, ensure_ascii=False)
        self._notify_change_listeners("app")
    
    def _save_ui_config(self):
        """保存界面配置"""
        config_file = self.config_dir / "ui_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self._ui_config, f, indent=2, ensure_ascii=False)
        self._notify_change_listeners("ui")
    
    def _save_file_types_config(self):
        """保存文件类型配置"""
        config_file = self.config_dir / "file_types.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self._file_types_config, f, indent=2, ensure_ascii=False)
        self._notify_change_listeners("file_types")

    def _ensure_optional_config(self, relative_path: str):
        """缓存存在的扩展配置文件，如 features/logging.json。"""
        config_file = self.config_dir / relative_path
        if config_file.exists():
            try:
                name = relative_path.replace('/', '_')
                with open(config_file, 'r', encoding='utf-8') as f:
                    self._config_cache[name] = json.load(f)
            except Exception as exc:
                self.logger.warning(f"读取扩展配置失败 {relative_path}: {exc}")
    
    def _save_config(self, config_type: str):
        """保存指定类型的配置"""
        save_map = {
            "app": self._save_app_config,
            "ui": self._save_ui_config,
            "file_types": self._save_file_types_config
        }
        save_func = save_map.get(config_type)
        if save_func:
            save_func()
    
    # ==================== V2.1增强方法 ====================
    
    def get_unified_config(self, key: str, default: Any = None) -> Any:
        """统一配置访问接口（V2.1新增）
        
        支持的key格式：
        - "app.name" -> app_config.json中的app.name
        - "external_modules.markdown_processor" -> external_modules.json中的数据
        - "ui.layout.left_panel_width" -> ui_config.json中的嵌套数据
        
        Args:
            key: 配置键路径，使用点号分隔
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        # 确定配置文件和路径
        if key.startswith('external_modules.'):
            # 特殊处理：external_modules配置
            return self._get_from_external_modules(key, default)
        else:
            # 通用处理：从对应的配置文件读取
            parts = key.split('.')
            if not parts:
                return default
            
            # 统一从_app_config中查找（因为所有配置都已加载到内部字典）
            # key="app.name" → 在_app_config中查找 app.name 路径
            # key="ui.layout" → 在_app_config中查找，但ui配置在_ui_config
            # 所以需要根据前缀路由
            
            first_part = parts[0]
            
            # 特殊路由：ui和file_types使用独立的配置字典
            if first_part == 'ui':
                if len(parts) == 1:
                    return self._ui_config if self._ui_config else default
                nested_key = '.'.join(parts[1:])
                return self._get_nested_value(self._ui_config, nested_key, default)
            elif first_part == 'file_types':
                if len(parts) == 1:
                    return self._file_types_config if self._file_types_config else default
                nested_key = '.'.join(parts[1:])
                return self._get_nested_value(self._file_types_config, nested_key, default)
            elif first_part == 'features':
                if len(parts) < 2:
                    return default
                feature_name = parts[1]
                config = self._load_config_file(f'features/{feature_name}')
                if not config:
                    return default
                if len(parts) == 2:
                    return config.get(feature_name, config) or default
                nested_key = '.'.join(parts[2:])
                base = config.get(feature_name, config)
                return self._get_nested_value(base or {}, nested_key, default)
            elif first_part == 'runtime':
                clean_key = '.'.join(parts[1:]) if len(parts) > 1 else ''
                config = self._load_config_file('runtime/performance')
                return self._get_nested_value(config or {}, clean_key, default)
            else:
                # 默认从_app_config查找完整路径（包括"app"前缀）
                return self._get_nested_value(self._app_config, key, default)
    
    def _get_from_external_modules(self, key: str, default: Any) -> Any:
        """从external_modules.json获取配置（V2.1新增）
        
        支持的key格式：
        - "external_modules.markdown_processor" -> 获取markdown_processor完整配置
        - "external_modules.markdown_processor.enabled" -> 获取enabled字段
        
        Args:
            key: 配置键路径
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        # 加载external_modules配置文件
        config_data = self._load_config_file("external_modules")
        if not config_data:
            return default
        
        # external_modules.json的实际结构是双层嵌套
        # {"external_modules": {"markdown_processor": {...}}}
        
        # 移除"external_modules."前缀，但保留后续路径
        if key.startswith('external_modules.'):
            clean_key = key.replace('external_modules.', '', 1)
            
            # 在external_modules层级下查找
            if 'external_modules' in config_data:
                return self._get_nested_value(
                    config_data['external_modules'],
                    clean_key,
                    default
                )
        
        return default
    
    def _load_config_file(self, config_name: str) -> Optional[Dict[str, Any]]:
        """加载指定的配置文件（V2.1新增）
        
        Args:
            config_name: 配置文件名（不含.json后缀）
            
        Returns:
            配置数据字典，如果加载失败返回None
        """
        if config_name in self._config_cache:
            return self._config_cache[config_name]
        
        parts = config_name.split('/')
        config_file = self.config_dir.joinpath(*parts).with_suffix('.json')
        if not config_file.exists():
            self.logger.warning(f"配置文件不存在: {config_file}")
            return None
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self._config_cache[config_name] = config
            return config
        except Exception as e:
            self.logger.error(f"读取配置文件失败: {config_file}, 错误: {e}")
            return None
    
    def _get_nested_value(self, data: Dict, key_path: str, default: Any) -> Any:
        """获取嵌套配置值（V2.1新增）
        
        Args:
            data: 配置数据字典
            key_path: 嵌套路径，如 "app.window.width"
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        try:
            keys = key_path.split('.')
            result = data
            
            for key in keys:
                if isinstance(result, dict) and key in result:
                    result = result[key]
                else:
                    return default
            
            return result
            
        except (KeyError, TypeError, AttributeError) as e:
            self.logger.debug(f"获取嵌套值失败: {key_path}, 错误: {e}")
            return default
    
    def reload_config(self, config_name: str = None):
        """重新加载配置（清除缓存）（V2.1新增）
        
        Args:
            config_name: 配置文件名，如果为None则清除所有缓存
        """
        if config_name:
            self._config_cache.pop(config_name, None)
            # 如果是已加载的配置，重新加载
            if config_name == "app" or config_name == "app_config":
                self._load_app_config()
            elif config_name == "ui" or config_name == "ui_config":
                self._load_ui_config()
            elif config_name == "file_types" or config_name == "file_types_config":
                self._load_file_types_config()
        else:
            self._config_cache.clear()
            self._load_all_configs()


# 全局配置管理器实例
_config_manager = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager 