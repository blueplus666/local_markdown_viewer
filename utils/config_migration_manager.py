#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置迁移管理器 v1.0.0
实现现有配置的渐进式扩展、备份和恢复机制

作者: LAD Team
创建时间: 2025-08-16
最后更新: 2025-08-16
"""

import json
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class MigrationResult:
    """迁移结果数据类"""
    success: bool
    timestamp: str
    migrated_files: List[str]
    backup_location: str
    errors: List[str]
    warnings: List[str]
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


class ConfigMigrationManager:
    """配置迁移管理器"""
    
    def __init__(self, config_dir: Union[str, Path]):
        """
        初始化配置迁移管理器
        
        Args:
            config_dir: 配置文件目录路径
        """
        self.config_dir = Path(config_dir)
        self.backup_dir = self.config_dir / "backup"
        self.migration_log_file = self.config_dir / "migration.log"
        
        # 确保目录存在
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # 迁移配置模板
        self.migration_templates = {
            'app_config': {
                'cache': {
                    'enabled': True,
                    'max_size_mb': 100,
                    'ttl_seconds': 3600,
                    'cleanup_interval': 300
                },
                'error_handling': {
                    'log_errors': True,
                    'show_user_friendly_errors': True,
                    'retry_count': 3,
                    'error_notification': False
                },
                'performance': {
                    'enable_monitoring': False,
                    'collect_metrics': False,
                    'log_slow_operations': True,
                    'performance_threshold_ms': 1000
                },
                'logging': {
                    'enhanced_logging': True,
                    'structured_logging': False,
                    'log_operations': True,
                    'log_performance': False
                }
            },
            'ui_config': {
                'advanced_features': {
                    'enable_animations': True,
                    'enable_tooltips': True,
                    'enable_context_menus': True,
                    'enable_drag_drop': False
                },
                'accessibility': {
                    'high_contrast_mode': False,
                    'large_fonts': False,
                    'keyboard_navigation': True
                }
            },
            'file_types_config': {
                'advanced_file_types': {
                    'enable_binary_preview': False,
                    'enable_archive_preview': True,
                    'enable_image_preview': True,
                    'max_preview_size_mb': 10
                },
                'file_associations': {
                    'custom_extensions': {},
                    'default_applications': {}
                }
            }
        }
    
    def _setup_logging(self):
        """设置日志配置"""
        # 创建文件处理器
        file_handler = logging.FileHandler(self.migration_log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加到logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.INFO)
    
    def migrate_configs(self) -> MigrationResult:
        """
        渐进式迁移配置
        
        Returns:
            迁移结果对象
        """
        self.logger.info("开始配置迁移")
        
        result = MigrationResult(
            success=False,
            timestamp=datetime.now().isoformat(),
            migrated_files=[],
            backup_location="",
            errors=[],
            warnings=[]
        )
        
        try:
            # 1. 备份现有配置
            backup_path = self._backup_existing_configs()
            result.backup_location = str(backup_path)
            self.logger.info(f"配置备份完成: {backup_path}")
            
            # 2. 迁移app_config.json
            if self._migrate_app_config():
                result.migrated_files.append('app_config.json')
                self.logger.info("app_config.json 迁移成功")
            else:
                result.errors.append("app_config.json 迁移失败")
            
            # 3. 迁移ui_config.json
            if self._migrate_ui_config():
                result.migrated_files.append('ui_config.json')
                self.logger.info("ui_config.json 迁移成功")
            else:
                result.errors.append("ui_config.json 迁移失败")
            
            # 4. 迁移file_types.json
            if self._migrate_file_types_config():
                result.migrated_files.append('file_types.json')
                self.logger.info("file_types.json 迁移成功")
            else:
                result.errors.append("file_types.json 迁移失败")
            
            # 5. 创建新的配置文件
            new_configs = self._create_new_configs()
            for config_name in new_configs:
                result.migrated_files.append(config_name)
            
            # 6. 验证迁移结果
            validation_result = self._validate_migration()
            if validation_result['errors']:
                result.errors.extend(validation_result['errors'])
            if validation_result['warnings']:
                result.warnings.extend(validation_result['warnings'])
            
            # 判断迁移是否成功
            result.success = len(result.errors) == 0
            
            if result.success:
                self.logger.info("配置迁移完成")
            else:
                self.logger.error(f"配置迁移失败，错误数: {len(result.errors)}")
                # 尝试从备份恢复
                self._restore_from_backup(backup_path)
            
        except Exception as e:
            error_msg = f"配置迁移过程中发生异常: {e}"
            result.errors.append(error_msg)
            self.logger.error(error_msg)
            
            # 尝试从备份恢复
            if result.backup_location:
                self._restore_from_backup(Path(result.backup_location))
        
        # 记录迁移结果
        self._log_migration_result(result)
        
        return result
    
    def _backup_existing_configs(self) -> Path:
        """备份现有配置文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"config_backup_{timestamp}"
        backup_path.mkdir(exist_ok=True)
        
        # 备份所有JSON配置文件
        config_files = list(self.config_dir.glob("*.json"))
        for config_file in config_files:
            if config_file.is_file():
                shutil.copy2(config_file, backup_path / config_file.name)
                self.logger.info(f"已备份: {config_file.name}")
        
        # 创建备份信息文件
        backup_info = {
            'timestamp': timestamp,
            'backup_path': str(backup_path),
            'files_backed_up': [f.name for f in config_files if f.is_file()],
            'description': '配置迁移前的自动备份'
        }
        
        backup_info_file = backup_path / "backup_info.json"
        with open(backup_info_file, 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, indent=2, ensure_ascii=False)
        
        return backup_path
    
    def _migrate_app_config(self) -> bool:
        """迁移应用配置"""
        try:
            app_config_file = self.config_dir / "app_config.json"
            if not app_config_file.exists():
                self.logger.warning("app_config.json 不存在，跳过迁移")
                return True
            
            # 读取现有配置
            with open(app_config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 应用迁移模板
            template = self.migration_templates['app_config']
            config_data = self._apply_migration_template(config_data, template)
            
            # 保存迁移后的配置
            with open(app_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info("app_config.json 迁移完成")
            return True
            
        except Exception as e:
            self.logger.error(f"app_config.json 迁移失败: {e}")
            return False
    
    def _migrate_ui_config(self) -> bool:
        """迁移界面配置"""
        try:
            ui_config_file = self.config_dir / "ui_config.json"
            if not ui_config_file.exists():
                self.logger.warning("ui_config.json 不存在，跳过迁移")
                return True
            
            # 读取现有配置
            with open(ui_config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 应用迁移模板
            template = self.migration_templates['ui_config']
            config_data = self._apply_migration_template(config_data, template)
            
            # 保存迁移后的配置
            with open(ui_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info("ui_config.json 迁移完成")
            return True
            
        except Exception as e:
            self.logger.error(f"ui_config.json 迁移失败: {e}")
            return False
    
    def _migrate_file_types_config(self) -> bool:
        """迁移文件类型配置"""
        try:
            file_types_config_file = self.config_dir / "file_types.json"
            if not file_types_config_file.exists():
                self.logger.warning("file_types.json 不存在，跳过迁移")
                return True
            
            # 读取现有配置
            with open(file_types_config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 应用迁移模板
            template = self.migration_templates['file_types_config']
            config_data = self._apply_migration_template(config_data, template)
            
            # 保存迁移后的配置
            with open(file_types_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info("file_types.json 迁移完成")
            return True
            
        except Exception as e:
            self.logger.error(f"file_types.json 迁移失败: {e}")
            return False
    
    def _apply_migration_template(self, config_data: Dict[str, Any], 
                                 template: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用迁移模板到配置数据
        
        Args:
            config_data: 现有配置数据
            template: 迁移模板
            
        Returns:
            更新后的配置数据
        """
        for section, section_data in template.items():
            if section not in config_data:
                config_data[section] = section_data
                self.logger.info(f"添加新配置节: {section}")
            else:
                # 递归合并配置节
                config_data[section] = self._merge_config_sections(
                    config_data[section], section_data
                )
                self.logger.info(f"更新配置节: {section}")
        
        return config_data
    
    def _merge_config_sections(self, existing: Any, new: Any) -> Any:
        """递归合并配置节"""
        if isinstance(new, dict) and isinstance(existing, dict):
            result = existing.copy()
            for key, value in new.items():
                if key not in result:
                    result[key] = value
                else:
                    result[key] = self._merge_config_sections(result[key], value)
            return result
        else:
            # 如果现有值不是字典，或者新值不是字典，则使用新值
            return new
    
    def _create_new_configs(self) -> List[str]:
        """创建新的配置文件"""
        new_configs = []
        
        # 创建性能监控配置
        performance_config_file = self.config_dir / "performance_config.json"
        if not performance_config_file.exists():
            performance_config = {
                'monitoring': {
                    'enabled': False,
                    'interval_seconds': 60,
                    'metrics_retention_days': 7
                },
                'thresholds': {
                    'memory_warning_mb': 500,
                    'memory_critical_mb': 1000,
                    'cpu_warning_percent': 80,
                    'cpu_critical_percent': 95
                },
                'alerts': {
                    'enable_notifications': False,
                    'notification_methods': ['log', 'console']
                }
            }
            
            with open(performance_config_file, 'w', encoding='utf-8') as f:
                json.dump(performance_config, f, indent=2, ensure_ascii=False)
            
            new_configs.append('performance_config.json')
            self.logger.info("创建新配置文件: performance_config.json")
        
        # 创建缓存配置
        cache_config_file = self.config_dir / "cache_config.json"
        if not cache_config_file.exists():
            cache_config = {
                'general': {
                    'enabled': True,
                    'default_ttl_seconds': 3600
                },
                'memory_cache': {
                    'max_size_mb': 100,
                    'cleanup_interval_seconds': 300,
                    'eviction_policy': 'lru'
                },
                'file_cache': {
                    'enabled': True,
                    'max_size_mb': 500,
                    'cache_directory': 'cache'
                }
            }
            
            with open(cache_config_file, 'w', encoding='utf-8') as f:
                json.dump(cache_config, f, indent=2, ensure_ascii=False)
            
            new_configs.append('cache_config.json')
            self.logger.info("创建新配置文件: cache_config.json")
        
        return new_configs
    
    def _validate_migration(self) -> Dict[str, List[str]]:
        """验证迁移结果"""
        validation_result = {
            'errors': [],
            'warnings': []
        }
        
        # 检查必要的配置文件是否存在
        required_files = ['app_config.json', 'ui_config.json', 'file_types.json']
        for file_name in required_files:
            file_path = self.config_dir / file_name
            if not file_path.exists():
                validation_result['errors'].append(f"必需配置文件缺失: {file_name}")
            else:
                # 验证JSON格式
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    validation_result['errors'].append(f"配置文件格式错误 {file_name}: {e}")
        
        # 检查新配置文件
        new_files = ['performance_config.json', 'cache_config.json']
        for file_name in new_files:
            file_path = self.config_dir / file_name
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    validation_result['warnings'].append(f"新配置文件格式错误 {file_name}: {e}")
        
        return validation_result
    
    def _restore_from_backup(self, backup_path: Path):
        """从备份恢复配置"""
        try:
            self.logger.warning(f"从备份恢复配置: {backup_path}")
            
            # 恢复所有配置文件
            for config_file in backup_path.glob("*.json"):
                if config_file.name != "backup_info.json":
                    target_file = self.config_dir / config_file.name
                    shutil.copy2(config_file, target_file)
                    self.logger.info(f"已恢复: {config_file.name}")
            
            self.logger.info("配置恢复完成")
            
        except Exception as e:
            self.logger.error(f"配置恢复失败: {e}")
    
    def _log_migration_result(self, result: MigrationResult):
        """记录迁移结果"""
        if result.success:
            self.logger.info("配置迁移成功完成")
            self.logger.info(f"迁移的文件: {', '.join(result.migrated_files)}")
            self.logger.info(f"备份位置: {result.backup_location}")
        else:
            self.logger.error("配置迁移失败")
            self.logger.error(f"错误数量: {len(result.errors)}")
            for error in result.errors:
                self.logger.error(f"错误: {error}")
        
        if result.warnings:
            self.logger.warning(f"警告数量: {len(result.warnings)}")
            for warning in result.warnings:
                self.logger.warning(f"警告: {warning}")
    
    def get_migration_status(self) -> Dict[str, Any]:
        """获取迁移状态"""
        status = {
            'last_migration': None,
            'backup_count': 0,
            'config_files': [],
            'migration_log': []
        }
        
        # 检查最近的迁移日志
        if self.migration_log_file.exists():
            try:
                with open(self.migration_log_file, 'r', encoding='utf-8') as f:
                    log_lines = f.readlines()
                    # 查找最近的迁移记录
                    for line in reversed(log_lines):
                        if '开始配置迁移' in line:
                            status['last_migration'] = line.split(' - ')[0]
                            break
            except Exception as e:
                self.logger.warning(f"读取迁移日志失败: {e}")
        
        # 统计备份数量
        if self.backup_dir.exists():
            backup_dirs = [d for d in self.backup_dir.iterdir() if d.is_dir()]
            status['backup_count'] = len(backup_dirs)
        
        # 列出配置文件
        config_files = list(self.config_dir.glob("*.json"))
        status['config_files'] = [f.name for f in config_files if f.is_file()]
        
        return status
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        backups = []
        
        if self.backup_dir.exists():
            for backup_dir in self.backup_dir.iterdir():
                if backup_dir.is_dir():
                    backup_info_file = backup_dir / "backup_info.json"
                    backup_info = {}
                    
                    if backup_info_file.exists():
                        try:
                            with open(backup_info_file, 'r', encoding='utf-8') as f:
                                backup_info = json.load(f)
                        except Exception as e:
                            self.logger.warning(f"读取备份信息失败: {e}")
                    
                    backups.append({
                        'name': backup_dir.name,
                        'path': str(backup_dir),
                        'timestamp': backup_info.get('timestamp', ''),
                        'files': backup_info.get('files_backed_up', []),
                        'description': backup_info.get('description', '')
                    })
        
        # 按时间排序
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        return backups
    
    def restore_from_backup(self, backup_name: str) -> bool:
        """
        从指定备份恢复配置
        
        Args:
            backup_name: 备份目录名称
            
        Returns:
            是否恢复成功
        """
        try:
            backup_path = self.backup_dir / backup_name
            if not backup_path.exists():
                self.logger.error(f"备份不存在: {backup_name}")
                return False
            
            self.logger.info(f"从备份恢复: {backup_name}")
            self._restore_from_backup(backup_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"从备份恢复失败: {e}")
            return False


# 便捷函数
def create_config_migration_manager(config_dir: Union[str, Path]) -> ConfigMigrationManager:
    """创建配置迁移管理器的便捷函数"""
    return ConfigMigrationManager(Path(config_dir))


def migrate_configs(config_dir: Union[str, Path]) -> MigrationResult:
    """快速迁移配置的便捷函数"""
    manager = create_config_migration_manager(config_dir)
    return manager.migrate_configs() 