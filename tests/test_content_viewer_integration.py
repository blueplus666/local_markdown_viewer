#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 ContentViewer 与 LinkProcessor 的集成
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QUrl

from ui.content_viewer import ContentViewer
from core.link_processor import LinkProcessor, LinkContext, LinkType


@pytest.fixture(scope="session")
def qapp():
    """创建QApplication实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    app.quit()


@pytest.fixture
def content_viewer(qapp):
    """创建ContentViewer实例"""
    viewer = ContentViewer()
    yield viewer
    viewer.deleteLater()


def test_content_viewer_initialization(content_viewer):
    """测试ContentViewer初始化"""
    assert content_viewer.link_processor is not None
    assert isinstance(content_viewer.link_processor, LinkProcessor)
    assert content_viewer.file_resolver is not None
    assert content_viewer.current_file_path is None


def test_link_processor_integration(content_viewer):
    """测试LinkProcessor集成"""
    # 模拟文件路径
    test_file = Path("D:/test/sample.md")
    content_viewer.current_file_path = str(test_file)
    
    # 测试外部链接处理
    link_data = {
        "href": "https://example.com",
        "text": "Example Link",
        "title": "Example Title",
        "type": "link"
    }
    
    with patch('webbrowser.open') as mock_browser:
        content_viewer.handle_link_click(link_data)
        # 验证外部链接被正确处理
        assert mock_browser.called


def test_anchor_link_handling(content_viewer):
    """测试锚点链接处理"""
    # 模拟文件路径
    test_file = Path("D:/test/sample.md")
    content_viewer.current_file_path = str(test_file)
    
    # 测试锚点链接
    link_data = {
        "href": "#section1",
        "text": "Section 1",
        "type": "anchor"
    }
    
    # 模拟JavaScript执行
    with patch.object(content_viewer.web_engine_view, 'page') as mock_page:
        mock_page.return_value.runJavaScript = Mock()
        content_viewer.handle_link_click(link_data)
        # 验证锚点处理被调用


def test_markdown_file_link_handling(content_viewer):
    """测试Markdown文件链接处理"""
    # 模拟文件路径
    test_file = Path("D:/test/sample.md")
    content_viewer.current_file_path = str(test_file)
    
    # 测试相对Markdown文件链接
    link_data = {
        "href": "docs/readme.md",
        "text": "README",
        "type": "markdown"
    }
    
    # 模拟信号发射
    with patch.object(content_viewer, 'content_loaded') as mock_signal:
        content_viewer.handle_link_click(link_data)
        # 验证信号被发射


def test_image_link_handling(content_viewer):
    """测试图片链接处理"""
    # 模拟文件路径
    test_file = Path("D:/test/sample.md")
    content_viewer.current_file_path = str(test_file)
    
    # 测试图片链接
    image_data = {
        "href": "images/logo.png",
        "text": "Logo",
        "type": "image",
        "width": 200,
        "height": 100
    }
    
    content_viewer.handle_image_click(image_data)
    # 验证图片处理被调用


def test_link_script_injection(content_viewer):
    """测试链接处理脚本注入"""
    # 测试HTML内容注入
    test_html = "<html><body><h1>Test</h1></body></html>"
    
    with patch.object(content_viewer.web_engine_view, 'setHtml') as mock_set_html:
        content_viewer._display_html(test_html)
        
        # 验证脚本被注入
        call_args = mock_set_html.call_args[0][0]
        assert "link_handling" in call_args or "addEventListener" in call_args


def test_error_handling(content_viewer):
    """测试错误处理"""
    # 测试无效链接处理
    invalid_link_data = {
        "href": "",
        "text": "",
        "type": "invalid"
    }
    
    # 应该不会抛出异常
    try:
        content_viewer.handle_link_click(invalid_link_data)
    except Exception as e:
        pytest.fail(f"处理无效链接时不应该抛出异常: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 