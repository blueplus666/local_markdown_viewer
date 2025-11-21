#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源管理器 v1.0.0
管理现有资源文件，支持资源发现、分类、监控和优化

作者: LAD Team
创建时间: 2025-08-16
最后更新: 2025-08-16
"""

import json
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import builtins

class ResourceType(Enum):
    """资源类型枚举"""
    CSS = "css"
    TEMPLATE = "template"
    ICON = "icon"
    IMAGE = "image"
    FONT = "font"
    SCRIPT = "script"
    CONFIG = "config"
    DATA = "data"
    LOG = "log"
    CACHE = "cache"
    TEMP = "temp"
    UNKNOWN = "unknown"


@dataclass
class ResourceInfo:
    """资源信息数据类"""
    path: str
    name: str
    resource_type: ResourceType
    size_bytes: int
    last_modified: str
    is_directory: bool
    children: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['resource_type'] = self.resource_type.value
        return data


class ResourceManager:
    """资源管理器"""
    
    def __init__(self, base_dir: Union[str, Path]):
        """
        初始化资源管理器
        
        Args:
            base_dir: 基础目录路径
        """
        self.base_dir = Path(base_dir)
        self.resources_dir = self.base_dir / "resources"
        self.cache_dir = self.base_dir / "cache"
        self.temp_dir = self.base_dir / "temp"
        
        # 确保目录存在
        self.resources_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 资源类型映射
        self.type_mappings = {
            '.css': ResourceType.CSS,
            '.scss': ResourceType.CSS,
            '.sass': ResourceType.CSS,
            '.html': ResourceType.TEMPLATE,
            '.htm': ResourceType.TEMPLATE,
            '.xml': ResourceType.TEMPLATE,
            '.json': ResourceType.TEMPLATE,
            '.png': ResourceType.ICON,
            '.jpg': ResourceType.ICON,
            '.jpeg': ResourceType.ICON,
            '.gif': ResourceType.ICON,
            '.svg': ResourceType.ICON,
            '.ico': ResourceType.ICON,
            '.bmp': ResourceType.IMAGE,
            '.tiff': ResourceType.IMAGE,
            '.webp': ResourceType.IMAGE,
            '.ttf': ResourceType.FONT,
            '.otf': ResourceType.FONT,
            '.woff': ResourceType.FONT,
            '.woff2': ResourceType.FONT,
            '.js': ResourceType.SCRIPT,
            '.ts': ResourceType.SCRIPT,
            '.py': ResourceType.SCRIPT,
            '.conf': ResourceType.CONFIG,
            '.ini': ResourceType.CONFIG,
            '.yaml': ResourceType.CONFIG,
            '.yml': ResourceType.CONFIG,
            '.md': ResourceType.DATA,
            '.txt': ResourceType.DATA,
            '.csv': ResourceType.DATA,
            '.log': ResourceType.LOG,
            '.tmp': ResourceType.TEMP,
            '.cache': ResourceType.CACHE
        }
        
        # 资源缓存
        self._resource_cache = {}
        self._last_scan_time = None
        
        # 扫描资源
        self.scan_resources()
    
    def scan_resources(self, force_rescan: bool = False) -> Dict[str, ResourceInfo]:
        """
        扫描资源目录
        
        Args:
            force_rescan: 是否强制重新扫描
            
        Returns:
            资源信息字典
        """
        current_time = datetime.now()
        
        # 检查是否需要重新扫描
        if (not force_rescan and 
            self._last_scan_time and 
            (current_time - self._last_scan_time).seconds < 300):  # 5分钟内不重复扫描
            return self._resource_cache
        
        self.logger.info("开始扫描资源目录")
        
        # 清空缓存
        self._resource_cache.clear()
        
        # 扫描各个目录
        self._scan_directory(self.resources_dir, "resources")
        self._scan_directory(self.cache_dir, "cache")
        self._scan_directory(self.temp_dir, "temp")
        
        # 更新扫描时间
        self._last_scan_time = current_time
        
        self.logger.info(f"资源扫描完成，共发现 {len(self._resource_cache)} 个资源")
        return self._resource_cache
    
    def _scan_directory(self, directory: Path, prefix: str):
        """扫描指定目录"""
        if not directory.exists():
            return
        
        for item in directory.rglob("*"):
            if item.is_file():
                resource_info = self._create_resource_info(item, prefix)
                if resource_info:
                    self._resource_cache[resource_info.path] = resource_info
            elif item.is_dir():
                # 为目录创建资源信息
                resource_info = self._create_resource_info(item, prefix, is_directory=True)
                if resource_info:
                    self._resource_cache[resource_info.path] = resource_info
    
    def _create_resource_info(self, path: Path, prefix: str, is_directory: bool = False) -> Optional[ResourceInfo]:
        """创建资源信息对象"""
        try:
            # 确定资源类型
            resource_type = self._determine_resource_type(path)
            
            # 获取文件大小
            size_bytes = 0
            if not is_directory:
                size_bytes = path.stat().st_size
            
            # 获取最后修改时间
            last_modified = datetime.fromtimestamp(path.stat().st_mtime).isoformat()
            
            # 构建相对路径
            relative_path = str(path.relative_to(self.base_dir))
            
            # 获取子项（如果是目录）
            children = None
            if is_directory:
                children = [str(child.relative_to(self.base_dir)) 
                          for child in path.iterdir() 
                          if child.is_file() or child.is_dir()]
            
            # 创建资源信息
            resource_info = ResourceInfo(
                path=relative_path,
                name=path.name,
                resource_type=resource_type,
                size_bytes=size_bytes,
                last_modified=last_modified,
                is_directory=is_directory,
                children=children,
                metadata=self._extract_metadata(path, resource_type)
            )
            
            return resource_info
            
        except Exception as e:
            self.logger.warning(f"创建资源信息失败 {path}: {e}")
            return None
    
    def _determine_resource_type(self, path: Path) -> ResourceType:
        """确定资源类型"""
        # 检查文件扩展名
        suffix = path.suffix.lower()
        if suffix in self.type_mappings:
            return self.type_mappings[suffix]
        
        # 检查目录名称
        if path.is_dir():
            dir_name = path.name.lower()
            if dir_name in ['css', 'styles']:
                return ResourceType.CSS
            elif dir_name in ['templates', 'views']:
                return ResourceType.TEMPLATE
            elif dir_name in ['icons', 'images', 'img']:
                return ResourceType.ICON
            elif dir_name in ['fonts']:
                return ResourceType.FONT
            elif dir_name in ['scripts', 'js']:
                return ResourceType.SCRIPT
            elif dir_name in ['config', 'conf']:
                return ResourceType.CONFIG
            elif dir_name in ['data', 'content']:
                return ResourceType.DATA
            elif dir_name in ['logs']:
                return ResourceType.LOG
            elif dir_name in ['cache']:
                return ResourceType.CACHE
            elif dir_name in ['temp', 'tmp']:
                return ResourceType.TEMP
        
        return ResourceType.UNKNOWN
    
    def _extract_metadata(self, path: Path, resource_type: ResourceType) -> Dict[str, Any]:
        """提取资源元数据"""
        metadata = {}
        
        try:
            if resource_type == ResourceType.CSS:
                metadata = self._extract_css_metadata(path)
            elif resource_type == ResourceType.TEMPLATE:
                metadata = self._extract_template_metadata(path)
            elif resource_type == ResourceType.IMAGE:
                metadata = self._extract_image_metadata(path)
            elif resource_type == ResourceType.SCRIPT:
                metadata = self._extract_script_metadata(path)
        except Exception as e:
            self.logger.debug(f"提取元数据失败 {path}: {e}")
        
        return metadata
    
    def _extract_css_metadata(self, path: Path) -> Dict[str, Any]:
        """提取CSS文件元数据"""
        metadata = {}
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
            metadata['line_count'] = len(content.splitlines())
            metadata['char_count'] = len(content)
            metadata['has_media_queries'] = '@media' in content
            metadata['has_animations'] = '@keyframes' in content or 'animation:' in content
        except Exception:
            pass
        return metadata
    
    def _extract_template_metadata(self, path: Path) -> Dict[str, Any]:
        """提取模板文件元数据"""
        metadata = {}
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
            metadata['line_count'] = len(content.splitlines())
            metadata['char_count'] = len(content)
            metadata['has_scripts'] = '<script' in content
            metadata['has_styles'] = '<style' in content
        except Exception:
            pass
        return metadata
    
    def _extract_image_metadata(self, path: Path) -> Dict[str, Any]:
        """提取图片文件元数据"""
        metadata = {}
        try:
            stat = path.stat()
            metadata['dimensions'] = "未知"  # 需要PIL库来获取实际尺寸
            metadata['format'] = path.suffix.lower()
        except Exception:
            pass
        return metadata
    
    def _extract_script_metadata(self, path: Path) -> Dict[str, Any]:
        """提取脚本文件元数据"""
        metadata = {}
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
            metadata['line_count'] = len(content.splitlines())
            metadata['char_count'] = len(content)
            metadata['has_functions'] = 'def ' in content or 'function ' in content
            metadata['has_classes'] = 'class ' in content
        except Exception:
            pass
        return metadata
    
    def get_resources_by_type(self, resource_type: ResourceType) -> List[ResourceInfo]:
        """
        按类型获取资源
        
        Args:
            resource_type: 资源类型
            
        Returns:
            资源信息列表
        """
        return [info for info in self._resource_cache.values() 
                if info.resource_type == resource_type]
    
    def get_resource_info(self, path: str) -> Optional[ResourceInfo]:
        """
        获取指定路径的资源信息
        
        Args:
            path: 资源路径
            
        Returns:
            资源信息对象
        """
        return self._resource_cache.get(path)
    
    def get_resources_summary(self) -> Dict[str, Any]:
        """获取资源摘要信息"""
        summary = {
            'total_resources': len(self._resource_cache),
            'total_size_bytes': 0,
            'type_distribution': {},
            'last_scan_time': self._last_scan_time.isoformat() if self._last_scan_time else None
        }
        
        # 统计各类型资源数量和大小
        for info in self._resource_cache.values():
            resource_type = info.resource_type.value
            if resource_type not in summary['type_distribution']:
                summary['type_distribution'][resource_type] = {
                    'count': 0,
                    'total_size_bytes': 0
                }
            
            summary['type_distribution'][resource_type]['count'] += 1
            summary['type_distribution'][resource_type]['total_size_bytes'] += info.size_bytes
            summary['total_size_bytes'] += info.size_bytes
        
        return summary
    
    def optimize_resources(self) -> Dict[str, Any]:
        """
        优化资源
        
        Returns:
            优化结果
        """
        optimization_result = {
            'timestamp': datetime.now().isoformat(),
            'actions_taken': [],
            'space_saved_bytes': 0,
            'warnings': []
        }
        
        try:
            # 1. 清理临时文件
            temp_files = self.get_resources_by_type(ResourceType.TEMP)
            for temp_file in temp_files:
                try:
                    file_path = self.base_dir / temp_file.path
                    if file_path.exists():
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        optimization_result['space_saved_bytes'] += file_size
                        optimization_result['actions_taken'].append(f"删除临时文件: {temp_file.path}")
                except Exception as e:
                    optimization_result['warnings'].append(f"删除临时文件失败 {temp_file.path}: {e}")
            
            # 2. 清理过期缓存
            cache_files = self.get_resources_by_type(ResourceType.CACHE)
            current_time = datetime.now()
            for cache_file in cache_files:
                try:
                    file_path = self.base_dir / cache_file.path
                    if file_path.exists():
                        # 检查文件年龄（超过7天）
                        file_age = current_time - datetime.fromisoformat(cache_file.last_modified)
                        if file_age.days > 7:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            optimization_result['space_saved_bytes'] += file_size
                            optimization_result['actions_taken'].append(f"删除过期缓存: {cache_file.path}")
                except Exception as e:
                    optimization_result['warnings'].append(f"删除过期缓存失败 {cache_file.path}: {e}")
            
            # 3. 重新扫描资源
            self.scan_resources(force_rescan=True)
            
            self.logger.info(f"资源优化完成，释放空间: {optimization_result['space_saved_bytes']} 字节")
            
        except Exception as e:
            error_msg = f"资源优化过程中发生异常: {e}"
            optimization_result['warnings'].append(error_msg)
            self.logger.error(error_msg)
        
        return optimization_result
    
    def backup_resources(self, backup_dir: Union[str, Path] = None) -> str:
        """
        备份资源
        
        Args:
            backup_dir: 备份目录，默认为base_dir下的backup目录
            
        Returns:
            备份目录路径
        """
        if backup_dir is None:
            backup_dir = self.base_dir / "backup"
        else:
            backup_dir = Path(backup_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"resources_backup_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # 备份resources目录
            if self.resources_dir.exists():
                shutil.copytree(self.resources_dir, backup_path / "resources", dirs_exist_ok=True)
            
            # 备份配置文件
            config_files = list(self.base_dir.glob("*.json"))
            for config_file in config_files:
                if config_file.is_file():
                    shutil.copy2(config_file, backup_path / config_file.name)
            
            # 创建备份信息文件
            backup_info = {
                'timestamp': timestamp,
                'backup_path': str(backup_path),
                'resources_count': len(self._resource_cache),
                'description': '资源管理器自动备份'
            }
            
            backup_info_file = backup_path / "backup_info.json"
            with builtins.open(backup_info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"资源备份完成: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            error_msg = f"资源备份失败: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def get_resource_usage_report(self) -> str:
        """生成资源使用报告"""
        summary = self.get_resources_summary()
        
        report = []
        report.append("# 资源使用报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("## 总体统计")
        report.append(f"- 总资源数量: {summary['total_resources']}")
        report.append(f"- 总占用空间: {summary['total_size_bytes'] / 1024 / 1024:.2f} MB")
        report.append(f"- 最后扫描时间: {summary['last_scan_time']}")
        report.append("")
        
        report.append("## 类型分布")
        for resource_type, stats in summary['type_distribution'].items():
            size_mb = stats['total_size_bytes'] / 1024 / 1024
            report.append(f"### {resource_type.upper()}")
            report.append(f"- 数量: {stats['count']}")
            report.append(f"- 占用空间: {size_mb:.2f} MB")
            report.append("")
        
        return "\n".join(report)


# 便捷函数
def create_resource_manager(base_dir: Union[str, Path]) -> ResourceManager:
    """创建资源管理器的便捷函数"""
    return ResourceManager(Path(base_dir))


def get_resources_summary(base_dir: Union[str, Path]) -> Dict[str, Any]:
    """快速获取资源摘要的便捷函数"""
    manager = create_resource_manager(base_dir)
    return manager.get_resources_summary() 