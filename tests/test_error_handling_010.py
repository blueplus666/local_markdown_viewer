#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
010任务错误处理标准化测试用例
测试错误码体系、配置驱动错误处理和graceful/strict模式
"""

import sys
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.error_code_manager import (
    ErrorCodeManager, ModuleImportErrorCodes, RenderProcessingErrorCodes,
    LinkProcessingErrorCodes, SystemErrorCodes
)
from core.enhanced_error_handler import EnhancedErrorHandler, ErrorSeverity, ErrorCategory
from utils.config_manager import ConfigManager


class TestErrorCodeManager:
    """测试错误码管理器"""

    def test_error_codes_definition(self):
        """测试错误码定义完整性"""
        ecm = ErrorCodeManager()

        # 验证所有错误码类别都存在
        assert 'module' in ecm.error_codes
        assert 'render' in ecm.error_codes
        assert 'link' in ecm.error_codes
        assert 'system' in ecm.error_codes

        # 验证错误码数量
        assert len(ecm.error_codes['module']) >= 6  # M001-M006 及扩展
        assert len(ecm.error_codes['render']) >= 6  # R001-R006
        assert len(ecm.error_codes['link']) >= 5    # L001-L005 及扩展
        assert len(ecm.error_codes['system']) >= 6   # S001-S006 及扩展

    def test_get_error_info(self):
        """测试获取错误信息"""
        ecm = ErrorCodeManager()

        error_info = ecm.get_error_info('module', ModuleImportErrorCodes.MODULE_NOT_FOUND)

        assert error_info.code == 'M001'
        assert error_info.message == '模块文件不存在'
        assert error_info.category == 'module'

    def test_format_error(self):
        """测试格式化错误信息"""
        ecm = ErrorCodeManager()

        formatted = ecm.format_error(
            'module',
            ModuleImportErrorCodes.MODULE_NOT_FOUND,
            {'path': '/test/path'}
        )

        assert formatted['code'] == 'M001'
        assert formatted['message'] == '模块文件不存在'
        assert formatted['category'] == 'module'
        assert formatted['details']['path'] == '/test/path'

    def test_validate_error_code(self):
        """测试错误码验证"""
        ecm = ErrorCodeManager()

        assert ecm.validate_error_code('module', 'M001') == True
        assert ecm.validate_error_code('module', 'INVALID') == False
        assert ecm.validate_error_code('invalid_category', 'M001') == False

    def test_get_all_error_codes(self):
        """测试获取所有错误码"""
        ecm = ErrorCodeManager()

        all_codes = ecm.get_all_error_codes()

        assert 'module' in all_codes
        assert 'render' in all_codes
        assert 'link' in all_codes
        assert 'system' in all_codes

        # 验证模块错误码
        assert 'MODULE_NOT_FOUND' in all_codes['module']
        assert all_codes['module']['MODULE_NOT_FOUND'] == ('M001', '模块文件不存在')


class TestErrorHandlingStrategy:
    """测试错误处理策略"""

    @patch('utils.config_manager.ConfigManager')
    def test_graceful_mode_config(self, mock_config_class):
        """测试graceful模式配置加载"""
        mock_config = Mock()
        mock_config.get_unified_config.return_value = {
            'strategy': 'graceful',
            'log_errors': True,
            'max_error_history': 200
        }
        mock_config_class.return_value = mock_config
        
        ecm = ErrorCodeManager(mock_config)
        
        assert ecm.error_strategy == 'graceful'
        assert ecm.log_errors == True

    @patch('utils.config_manager.ConfigManager')
    def test_strict_mode_config(self, mock_config_class):
        """测试strict模式配置加载"""
        mock_config = Mock()
        mock_config.get_unified_config.return_value = {
            'strategy': 'strict',
            'log_errors': False,
            'max_error_history': 100
        }
        mock_config_class.return_value = mock_config
        
        ecm = ErrorCodeManager(mock_config)
        
        assert ecm.error_strategy == 'strict'
        assert ecm.log_errors == False

    def test_default_config(self):
        """测试默认配置"""
        ecm = ErrorCodeManager()

        assert ecm.error_strategy == 'graceful'
        assert ecm.log_errors == True
        assert ecm.auto_recovery == True


class TestEnhancedErrorHandler:
    """测试增强错误处理器"""

    def test_graceful_mode_handling(self):
        """测试graceful模式错误处理"""
        config_manager = Mock()
        config_manager._app_config = {
            'error_handling': {'strategy': 'graceful'}
        }
        config_manager.get_unified_config.return_value = {'strategy': 'graceful'}

        handler = EnhancedErrorHandler(config_manager=config_manager)

        # 模拟一个可恢复的错误
        try:
            raise ValueError("test error")
        except ValueError as e:
            error_info = handler.handle_error(e, {"test": "context"})

            # graceful模式应该返回错误信息而不是抛出异常
            assert error_info is not None
            assert error_info.error_type == "ValueError"
            assert error_info.severity == ErrorSeverity.MEDIUM

    def test_strict_mode_handling(self):
        """测试strict模式错误处理"""
        config_manager = Mock()
        config_manager._app_config = {
            'error_handling': {'strategy': 'strict'}
        }
        config_manager.get_unified_config.return_value = {'strategy': 'strict'}

        handler = EnhancedErrorHandler(config_manager=config_manager)

        # 模拟一个错误
        with pytest.raises(ValueError):
            try:
                raise ValueError("test error")
            except ValueError as e:
                handler.handle_error(e, {"test": "context"})

    def test_error_categorization(self):
        """测试错误分类"""
        handler = EnhancedErrorHandler()

        # 测试文件I/O错误分类
        assert handler._categorize_exception(FileNotFoundError("test")) == ErrorCategory.FILE_IO
        assert handler._categorize_exception(PermissionError("test")) == ErrorCategory.FILE_IO

        # 测试网络错误分类
        assert handler._categorize_exception(ConnectionError("test")) == ErrorCategory.NETWORK
        assert handler._categorize_exception(TimeoutError("test")) == ErrorCategory.NETWORK

        # 测试配置错误分类
        assert handler._categorize_exception(KeyError("test")) == ErrorCategory.CONFIGURATION
        assert handler._categorize_exception(ValueError("test")) == ErrorCategory.CONFIGURATION

    def test_error_severity_determination(self):
        """测试错误严重程度确定"""
        handler = EnhancedErrorHandler()

        # 测试系统错误严重程度
        assert handler._determine_severity(ErrorCategory.SYSTEM, SystemError("test")) == ErrorSeverity.CRITICAL

        # 测试文件I/O错误严重程度
        assert handler._determine_severity(ErrorCategory.FILE_IO, FileNotFoundError("test")) == ErrorSeverity.HIGH

        # 测试配置错误严重程度
        assert handler._determine_severity(ErrorCategory.CONFIGURATION, ValueError("test")) == ErrorSeverity.MEDIUM


class TestErrorRecoveryMechanisms:
    """测试错误恢复机制"""

    def test_retry_strategy(self):
        """测试重试策略"""
        handler = EnhancedErrorHandler()

        # 创建一个模拟的错误信息
        error_info = Mock()
        error_info.retry_count = 0
        error_info.max_retries = 3
        error_info.error_id = "TEST_001"

        # 测试重试逻辑
        handler._handle_retry_strategy(error_info)

        assert error_info.retry_count == 1

    def test_fallback_strategy(self):
        """测试降级策略"""
        handler = EnhancedErrorHandler()

        # 创建一个模拟的错误信息
        error_info = Mock()
        error_info.error_id = "TEST_002"

        # 测试降级逻辑（应该标记为已解决）
        handler._handle_fallback_strategy(error_info)

        # 验证错误被标记为已解决
        assert error_info.resolved == True
        assert error_info.resolution_method == "降级处理"

    def test_ignore_strategy(self):
        """测试忽略策略"""
        handler = EnhancedErrorHandler()

        # 创建一个模拟的错误信息
        error_info = Mock()
        error_info.error_id = "TEST_003"

        # 测试忽略逻辑
        handler._handle_ignore_strategy(error_info)

        # 验证错误被标记为已解决
        assert error_info.resolved == True
        assert error_info.resolution_method == "忽略处理"

    def test_abort_strategy(self):
        """测试中止策略"""
        handler = EnhancedErrorHandler()

        # 创建一个模拟的错误信息
        error_info = Mock()
        error_info.error_id = "TEST_004"

        # 测试中止逻辑
        handler._handle_abort_strategy(error_info)

        # 验证错误被标记为已解决
        assert error_info.resolved == True
        assert error_info.resolution_method == "中止处理"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
