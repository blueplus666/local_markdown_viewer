#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件解析器模块 v1.0.0
负责文件类型识别、路径解析和编码检测

作者: LAD Team
创建时间: 2025-08-02
最后更新: 2025-08-02
"""

import os
import mimetypes
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union
import json

try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False
    logging.warning("chardet库未安装，将使用基本编码检测方法")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.config_manager import ConfigManager


class FileResolver:
    """
    文件解析器类
    提供文件类型分析、路径解析和编码检测功能
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        初始化文件解析器
        
        Args:
            config_manager: 配置管理器实例，如果为None则创建新实例
        """
        self.config_manager = config_manager or ConfigManager()
        self.logger = logging.getLogger(__name__)
        
        # 加载文件类型配置
        self.file_types_config = self.config_manager.load_file_types_config()
        
        # 初始化MIME类型映射
        mimetypes.init()
        
        # 文件头签名映射
        self.file_signatures = {
            b'\x89PNG\r\n\x1a\n': 'image/png',
            b'\xff\xd8\xff': 'image/jpeg',
            b'GIF87a': 'image/gif',
            b'GIF89a': 'image/gif',
            b'BM': 'image/bmp',
            b'PK\x03\x04': 'application/zip',
            b'PK\x05\x06': 'application/zip',
            b'PK\x07\x08': 'application/zip',
            b'\x1f\x8b\x08': 'application/gzip',
            b'BZh': 'application/bzip2',
            b'\x37\x7A\xBC\xAF': 'application/x-7z-compressed',
            b'%PDF': 'application/pdf',
            b'<!DOCTYPE': 'text/html',
            b'<?xml': 'application/xml',
            b'{\n': 'application/json',
            b'{\r\n': 'application/json',
            b'#!': 'text/script',
        }
    
    def resolve_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        解析文件的完整信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            包含文件解析结果的字典
        """
        try:
            file_path = Path(file_path)
            
            # 验证文件路径
            if not self._validate_path(file_path):
                return {
                    'success': False,
                    'error': '文件路径无效或文件不存在',
                    'file_path': str(file_path)
                }
            
            # 获取文件基本信息
            file_info = self._get_file_info(file_path)
            
            # 分析文件类型
            file_type = self._analyze_file_type(file_path)
            
            # 检测文件编码
            encoding_info = self._detect_encoding(file_path)
            
            # 构建结果
            result = {
                'success': True,
                'file_path': str(file_path.absolute()),
                'file_info': file_info,
                'file_type': file_type,
                'encoding': encoding_info,
                'resolved_at': self._get_timestamp()
            }
            
            self.logger.info(f"文件解析成功: {file_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"文件解析失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': str(file_path) if 'file_path' in locals() else str(file_path)
            }
    
    def _validate_path(self, file_path: Path) -> bool:
        """
        验证文件路径的有效性
        
        Args:
            file_path: 文件路径
            
        Returns:
            路径是否有效
        """
        try:
            # 检查路径是否存在
            if not file_path.exists():
                return False
            
            # 检查是否为文件
            if not file_path.is_file():
                return False
            
            # 检查文件大小（避免处理过大的文件）
            if file_path.stat().st_size > 100 * 1024 * 1024:  # 100MB
                self.logger.warning(f"文件过大，可能影响性能: {file_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"路径验证失败: {e}")
            return False
    
    def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """
        获取文件基本信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息字典
        """
        try:
            stat = file_path.stat()
            
            return {
                'name': file_path.name,
                'extension': file_path.suffix.lower(),
                'size': stat.st_size,
                'size_formatted': self._format_file_size(stat.st_size),
                'modified_time': stat.st_mtime,
                'created_time': stat.st_ctime,
                'is_readable': os.access(file_path, os.R_OK),
                'is_writable': os.access(file_path, os.W_OK),
                'is_executable': os.access(file_path, os.X_OK)
            }
            
        except Exception as e:
            self.logger.error(f"获取文件信息失败: {e}")
            return {'error': str(e)}
    
    def _analyze_file_type(self, file_path: Path) -> Dict[str, Any]:
        """
        分析文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件类型信息字典
        """
        try:
            extension = file_path.suffix.lower()
            
            # 1. 基于扩展名的类型识别
            extension_type = self._get_type_by_extension(extension)
            
            # 2. 基于MIME类型的识别
            mime_type = mimetypes.guess_type(str(file_path))[0]
            
            # 3. 基于文件头的识别
            header_type = self._get_type_by_header(file_path)
            
            # 4. 确定最终类型
            final_type = self._determine_final_type(extension_type, mime_type, header_type)
            
            return {
                'extension': extension,
                'extension_type': extension_type,
                'mime_type': mime_type,
                'header_type': header_type,
                'final_type': final_type,
                'confidence': self._calculate_confidence(extension_type, mime_type, header_type)
            }
            
        except Exception as e:
            self.logger.error(f"文件类型分析失败: {e}")
            return {'error': str(e)}
    
    def _get_type_by_extension(self, extension: str) -> Optional[Dict[str, Any]]:
        """
        基于扩展名获取文件类型信息
        
        Args:
            extension: 文件扩展名
            
        Returns:
            文件类型信息字典
        """
        for type_name, type_info in self.file_types_config.items():
            if extension in type_info.get('extensions', []):
                return {
                    'name': type_name,
                    'renderer': type_info.get('renderer'),
                    'preview_mode': type_info.get('preview_mode'),
                    'icon': type_info.get('icon'),
                    'description': type_info.get('description')
                }
        return None
    
    def _get_type_by_header(self, file_path: Path) -> Optional[str]:
        """
        基于文件头获取文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            MIME类型字符串
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(16)  # 读取前16字节
                
                for signature, mime_type in self.file_signatures.items():
                    if header.startswith(signature):
                        return mime_type
                        
        except Exception as e:
            self.logger.debug(f"文件头分析失败: {e}")
            
        return None
    
    def _determine_final_type(self, extension_type: Optional[Dict], 
                            mime_type: Optional[str], 
                            header_type: Optional[str]) -> str:
        """
        确定最终的文件类型
        
        Args:
            extension_type: 扩展名类型信息
            mime_type: MIME类型
            header_type: 文件头类型
            
        Returns:
            最终确定的类型
        """
        # 优先级：扩展名 > 文件头 > MIME类型
        if extension_type:
            return extension_type['name']
        elif header_type:
            return header_type
        elif mime_type:
            return mime_type
        else:
            return 'unknown'
    
    def _calculate_confidence(self, extension_type: Optional[Dict], 
                            mime_type: Optional[str], 
                            header_type: Optional[str]) -> float:
        """
        计算类型识别的置信度
        
        Args:
            extension_type: 扩展名类型信息
            mime_type: MIME类型
            header_type: 文件头类型
            
        Returns:
            置信度（0.0-1.0）
        """
        confidence = 0.0
        
        if extension_type:
            confidence += 0.5
        if mime_type:
            confidence += 0.3
        if header_type:
            confidence += 0.2
            
        return min(confidence, 1.0)
    
    def _detect_encoding(self, file_path: Path) -> Dict[str, Any]:
        """
        检测文件编码
        
        Args:
            file_path: 文件路径
            
        Returns:
            编码信息字典
        """
        try:
            # 尝试使用chardet检测编码
            if CHARDET_AVAILABLE:
                return self._detect_encoding_with_chardet(file_path)
            else:
                return self._detect_encoding_basic(file_path)
                
        except Exception as e:
            self.logger.error(f"编码检测失败: {e}")
            return {
                'encoding': 'unknown',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _detect_encoding_with_chardet(self, file_path: Path) -> Dict[str, Any]:
        """
        使用chardet库检测编码
        
        Args:
            file_path: 文件路径
            
        Returns:
            编码信息字典
        """
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(1024 * 1024)  # 读取1MB用于检测
                
            result = chardet.detect(raw_data)
            
            return {
                'encoding': result['encoding'],
                'confidence': result['confidence'],
                'method': 'chardet'
            }
            
        except Exception as e:
            self.logger.error(f"chardet编码检测失败: {e}")
            return self._detect_encoding_basic(file_path)
    
    def _detect_encoding_basic(self, file_path: Path) -> Dict[str, Any]:
        """
        基本编码检测方法
        
        Args:
            file_path: 文件路径
            
        Returns:
            编码信息字典
        """
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(1024)  # 尝试读取一小部分
                return {
                    'encoding': encoding,
                    'confidence': 0.8,
                    'method': 'basic'
                }
            except UnicodeDecodeError:
                continue
            except Exception as e:
                self.logger.debug(f"编码{encoding}检测失败: {e}")
                continue
        
        return {
            'encoding': 'unknown',
            'confidence': 0.0,
            'method': 'basic'
        }
    
    def _format_file_size(self, size_bytes: int) -> str:
        """
        格式化文件大小
        
        Args:
            size_bytes: 文件大小（字节）
            
        Returns:
            格式化的文件大小字符串
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def _get_timestamp(self) -> str:
        """
        获取当前时间戳
        
        Returns:
            时间戳字符串
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_supported_extensions(self) -> Dict[str, list]:
        """
        获取支持的文件扩展名列表
        
        Returns:
            文件类型到扩展名的映射
        """
        result = {}
        for type_name, type_info in self.file_types_config.items():
            result[type_name] = type_info.get('extensions', [])
        return result
    
    def get_supported_encodings(self) -> list:
        """
        获取支持的编码列表
        
        Returns:
            支持的编码列表
        """
        return ['utf-8', 'gbk', 'gb2312', 'latin-1', 'cp1252', 'ascii']
    
    def is_supported_file(self, file_path: Union[str, Path]) -> bool:
        """
        检查文件是否被支持
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否支持该文件
        """
        try:
            file_path = Path(file_path)
            extension = file_path.suffix.lower()
            
            for type_info in self.file_types_config.values():
                if extension in type_info.get('extensions', []):
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"文件支持检查失败: {e}")
            return False 