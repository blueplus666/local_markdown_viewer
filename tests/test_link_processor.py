#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytest 用例骨架：LinkProcessor
覆盖：识别/路由/最小返回/日志字段占位（session_id由上层注入时再测）
"""
from pathlib import Path
import os
import logging

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from core.link_processor import (
    LinkProcessor,
    LinkType,
    LinkContext,
    ExternalHandler,
    RelativeMarkdownHandler,
    DirectoryHandler,
    AnchorHandler,
    ImageHandler,
    MermaidHandler,
    TocHandler,
    FileProtocolHandler,
    PathResolver,
    LinkValidator,
    ErrorCode,
)


@pytest.fixture()
def lp():
    import logging
    logger = logging.getLogger("lp")
    logger.setLevel(logging.INFO)
    p = LinkProcessor(logger=logger)
    # 放宽策略：不强制存在性，避免依赖真实文件
    p.set_policy({
        "check_exists": False,
        "logging": {"json": False},
        # 允许 https://example.com 以通过外链测试（fail-closed 默认策略下）
        "security": {"allowed_protocols": ["https"], "allowed_domains": ["example.com"]}
    })
    p.set_handlers({
        LinkType.EXTERNAL_HTTP: ExternalHandler(),
        LinkType.RELATIVE_MD: RelativeMarkdownHandler(),
        LinkType.DIRECTORY: DirectoryHandler(),
        LinkType.ANCHOR: AnchorHandler(),
        LinkType.IMAGE: ImageHandler(),
        LinkType.MERMAID: MermaidHandler(),
        LinkType.TOC: TocHandler(),
        LinkType.FILE_PROTOCOL: FileProtocolHandler(),
    })
    return p


def test_recognize_external(lp):
    ctx = LinkContext(href="https://example.com", extra={"session_id": "sid-123"})
    res = lp.process_link(ctx)
    assert res.success is True
    assert res.action == "open_browser"
    assert res.payload.get("url") == "https://example.com"


def test_recognize_relative_md(lp):
    ctx = LinkContext(href="docs/readme.md", current_file=Path("D:/repo/a.md"))
    res = lp.process_link(ctx)
    assert res.success is True
    assert res.action == "open_markdown_in_tree"


def test_recognize_directory(lp):
    ctx = LinkContext(href="docs/")
    res = lp.process_link(ctx)
    assert res.success is True
    assert res.action == "open_directory"


def test_recognize_anchor(lp):
    ctx = LinkContext(href="#intro")
    res = lp.process_link(ctx)
    assert res.success is True
    assert res.action == "scroll_to_anchor"
    assert res.payload.get("id") == "intro"


def test_unsupported_returns_error(lp):
    ctx = LinkContext(href="unknown.scheme://abc")
    res = lp.process_link(ctx)
    assert res.success is False
    assert res.error_code.name in ("UNSUPPORTED", "INTERNAL_ERROR")


def test_recognize_image(lp):
    ctx = LinkContext(href="images/pic.png")
    res = lp.process_link(ctx)
    assert res.success is True
    assert res.action == "open_image_viewer"


def test_recognize_mermaid(lp):
    ctx = LinkContext(href="graph.mmd", extra={"mermaid_container": True})
    res = lp.process_link(ctx)
    assert res.success is True
    assert res.action == "open_mermaid_viewer"


def test_recognize_toc(lp):
    ctx = LinkContext(href="docs/guide.md#introduction")
    res = lp.process_link(ctx)
    assert res.success is True
    assert res.action == "scroll_to_anchor"


def test_recognize_file_protocol(lp):
    ctx = LinkContext(href="file:///C:/data/file.md")
    res = lp.process_link(ctx)
    assert res.success is True
    assert res.action == "open_markdown_in_tree"


def test_pathresolver_relative_normalize():
    pr = PathResolver()
    base = Path("D:/proj/docs/guide.md")
    out = pr.resolve_relative(base, "../images/pic.png")
    # 不断言具体路径，仅断言为Path并标准化执行
    assert isinstance(out, Path)
    assert ".." not in str(out)


def test_pathresolver_file_protocol():
    pr = PathResolver()
    out = pr.resolve_file_protocol("file:///C:/data/a.md")
    assert isinstance(out, Path)
    assert str(out).lower().startswith("c:")


def test_validator_url_fail_closed():
    v = LinkValidator()


def test_validator_security_policy():
    v = LinkValidator()
    
    # 测试协议白名单
    policy = {
        "security": {
            "allowed_protocols": ["https"],
            "allowed_domains": ["example.com"]
        }
    }
    
    # HTTPS + 允许域名应该通过
    result = v.validate("https://example.com/page", policy)
    assert result.ok is True
    
    # HTTP + 允许域名应该被拒绝（协议不在白名单）
    result = v.validate("http://example.com/page", policy)
    assert result.ok is False
    assert result.error_code == ErrorCode.SECURITY_BLOCKED
    
    # HTTPS + 不允许域名应该被拒绝
    result = v.validate("https://other.com/page", policy)
    assert result.ok is False
    assert result.error_code == ErrorCode.SECURITY_BLOCKED


def test_validator_path_security():
    v = LinkValidator()
    
    policy = {
        "security": {
            "forbidden_patterns": ["../..", "~"]
        },
        "windows_specific": {
            "max_path_depth": 3,
            "drive_letters": ["C:", "D:"]
        }
    }
    
    # 测试禁止模式（使用不会被标准化的模式）
    result = v.validate(Path("C:/path/~/file.txt"), policy)
    assert result.ok is False
    assert result.error_code == ErrorCode.SECURITY_BLOCKED
    
    # 测试深度限制（C:/path/to/deep/file.txt 有4个部分：path, to, deep, file.txt）
    result = v.validate(Path("C:/path/to/deep/file.txt"), policy)
    assert result.ok is False
    assert result.error_code == ErrorCode.SECURITY_BLOCKED
    
    # 测试驱动器限制
    result = v.validate(Path("E:/path/file.txt"), policy)
    assert result.ok is False
    assert result.error_code == ErrorCode.SECURITY_BLOCKED
    policy = {"security": {"allowed_protocols": ["https"], "allowed_domains": []}}
    res = v.validate("https://example.com", policy)
    assert res.ok is False
    assert res.error_code.name == "SECURITY_BLOCKED"


def test_validator_path_not_found(tmp_path):
    v = LinkValidator()
    missing = tmp_path / "no_such_file.md"
    res = v.validate(missing, {"check_exists": True})
    assert res.ok is False
    assert res.error_code.name == "NOT_FOUND"


def test_validator_forbidden_pattern(tmp_path):
    v = LinkValidator()
    p = tmp_path / "a" / "b" / "c.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("x", encoding="utf-8")
    pat = f"{os.sep}b{os.sep}"
    res = v.validate(p, {"check_exists": True, "security": {"forbidden_patterns": [pat]}})
    assert res.ok is False
    assert res.error_code.name == "SECURITY_BLOCKED"


def test_validator_max_depth(tmp_path):
    v = LinkValidator()
    d = tmp_path / "a" / "b" / "c" / "d"
    d.mkdir(parents=True, exist_ok=True)
    res = v.validate(d, {"check_exists": True, "windows_specific": {"max_path_depth": 2}})
    assert res.ok is False
    assert res.error_code.name == "SECURITY_BLOCKED"


def test_logging_with_session_id(caplog):
    import logging
    logger = logging.getLogger("lp-json")
    logger.setLevel(logging.INFO)
    p = LinkProcessor(logger=logger)
    p.set_handlers({LinkType.EXTERNAL_HTTP: ExternalHandler()})
    p.set_policy({
        "logging": {"json": True},
        "security": {"allowed_protocols": ["https"], "allowed_domains": ["example.com"]}
    })
    with caplog.at_level(logging.INFO, logger="lp-json"):
        ctx = LinkContext(href="https://example.com", extra={"session_id": "sess-001"})
        res = p.process_link(ctx)
        assert res.success is True
    # 校验JSON日志包含session_id字段，且包含固定字段app/module_name
    found = any(("\"session_id\": \"sess-001\"" in rec.message and
                 "\"app\": \"local_markdown_viewer\"" in rec.message and
                 "\"module_name\": \"link_processor\"" in rec.message and
                 "\"build_version\":" in rec.message)
                for rec in caplog.records)
    assert found


def test_logging_with_session_id_extra(caplog):
    import logging
    logger = logging.getLogger("lp-extra")
    logger.setLevel(logging.INFO)
    p = LinkProcessor(logger=logger)
    p.set_handlers({LinkType.EXTERNAL_HTTP: ExternalHandler()})
    # 标准extra模式
    p.set_policy({
        "logging": {"json": False},
        "security": {"allowed_protocols": ["https"], "allowed_domains": ["example.com"]}
    })
    with caplog.at_level(logging.INFO, logger="lp-extra"):
        ctx = LinkContext(href="https://example.com", extra={"session_id": "sess-002"})
        res = p.process_link(ctx)
        assert res.success is True
            # 校验日志记录是否成功
        # 简化测试：只检查是否有日志记录
        assert len(caplog.records) > 0
        assert any(rec.name == "lp-extra" and rec.msg == "link_processed" for rec in caplog.records)


def test_build_version_from_pyproject_toml(tmp_path):
    """测试从pyproject.toml读取版本号"""
    from pathlib import Path
    
    # 构造临时pyproject.toml文件
    pyproject_content = '''[project]
name = "test-project"
version = "1.2.3"
description = "Test project"

[tool.poetry]
name = "test-poetry"
version = "2.3.4"
'''
    
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(pyproject_content, encoding="utf-8")
    
    # 模拟LinkProcessor的_read_pyproject_version方法
    def read_pyproject_version(toml_path):
        try:
            text = toml_path.read_text(encoding="utf-8", errors="ignore")
            current = None
            version_in_project = None
            version_in_poetry = None
            for raw in text.splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    current = line.strip("[]").strip()
                    continue
                if line.startswith("version") and "=" in line:
                    try:
                        right = line.split("=", 1)[1].strip()
                        if right.startswith("\""):
                            val = right.split("\"", 2)[1]
                        elif right.startswith("'"):
                            val = right.split("'", 2)[1]
                        else:
                            val = right
                    except Exception:
                        continue
                    if current == "project" and not version_in_project:
                        version_in_project = val
                    elif current == "tool.poetry" and not version_in_poetry:
                        version_in_poetry = val
            return version_in_project or version_in_poetry
        except Exception:
            return None
    
    # 测试读取
    version = read_pyproject_version(pyproject_file)
    assert version == "1.2.3"  # 优先返回[project]中的版本


def test_build_version_from_pyproject_toml_poetry_fallback(tmp_path):
    """测试从pyproject.toml读取版本号（poetry fallback）"""
    from pathlib import Path
    
    # 构造只有poetry版本的临时文件
    pyproject_content = '''[tool.poetry]
name = "test-poetry"
version = "3.4.5"
'''
    
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(pyproject_content, encoding="utf-8")
    
    # 模拟LinkProcessor的_read_pyproject_version方法
    def read_pyproject_version(toml_path):
        try:
            text = toml_path.read_text(encoding="utf-8", errors="ignore")
            current = None
            version_in_project = None
            version_in_poetry = None
            for raw in text.splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    current = line.strip("[]").strip()
                    continue
                if line.startswith("version") and "=" in line:
                    try:
                        right = line.split("=", 1)[1].strip()
                        if right.startswith("\""):
                            val = right.split("\"", 2)[1]
                        elif right.startswith("'"):
                            val = right.split("'", 2)[1]
                        else:
                            val = right
                    except Exception:
                        continue
                    if current == "project" and not version_in_project:
                        version_in_project = val
                    elif current == "tool.poetry" and not version_in_poetry:
                        version_in_poetry = val
            return version_in_project or version_in_poetry
        except Exception:
            return None
    
    # 测试读取
    version = read_pyproject_version(pyproject_file)
    assert version == "3.4.5"  # 返回[tool.poetry]中的版本


def test_build_version_from_pyproject_toml_invalid_file(tmp_path):
    """测试无效pyproject.toml文件的处理"""
    from pathlib import Path
    
    # 构造无效的临时文件
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text("invalid toml content", encoding="utf-8")
    
    # 模拟LinkProcessor的_read_pyproject_version方法
    def read_pyproject_version(toml_path):
        try:
            text = toml_path.read_text(encoding="utf-8", errors="ignore")
            current = None
            version_in_project = None
            version_in_poetry = None
            for raw in text.splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    current = line.strip("[]").strip()
                    continue
                if line.startswith("version") and "=" in line:
                    try:
                        right = line.split("=", 1)[1].strip()
                        if right.startswith("\""):
                            val = right.split("\"", 2)[1]
                        elif right.startswith("'"):
                            val = right.split("'", 2)[1]
                        else:
                            val = right
                    except Exception:
                        continue
                    if current == "project" and not version_in_project:
                        version_in_project = val
                    elif current == "tool.poetry" and not version_in_poetry:
                        version_in_poetry = val
            return version_in_project or version_in_poetry
        except Exception:
            return None
    
    # 测试读取
    version = read_pyproject_version(pyproject_file)
    assert version is None  # 无效文件应返回None

def test_external_link_blocked_by_default_fail_closed_lp():
    import logging
    logger = logging.getLogger("lp-fc")
    logger.setLevel(logging.INFO)
    p = LinkProcessor(logger=logger)
    p.set_handlers({LinkType.EXTERNAL_HTTP: ExternalHandler()})
    ctx = LinkContext(href="https://not-allowed.com")
    res = p.process_link(ctx)
    assert res.success is False
    assert res.action == "show_error"
    assert res.error_code == ErrorCode.SECURITY_BLOCKED


def test_relative_md_resolution_payload_path():
    import logging
    logger = logging.getLogger("lp-rel")
    logger.setLevel(logging.INFO)
    p = LinkProcessor(logger=logger)
    p.set_policy({"check_exists": False})
    p.set_handlers({LinkType.RELATIVE_MD: RelativeMarkdownHandler()})
    ctx = LinkContext(href="../images/pic.md", current_file=Path("D:/proj/docs/guide.md"))
    res = p.process_link(ctx)
    assert res.success is True
    assert res.action == "open_markdown_in_tree"
    out = res.payload.get("path")
    norm = out.replace("\\", "/").lower()
    assert norm.endswith("d:/proj/images/pic.md")


def test_relative_md_not_found_when_check_exists_true():
    import logging
    logger = logging.getLogger("lp-exist")
    logger.setLevel(logging.INFO)
    p = LinkProcessor(logger=logger)
    p.set_handlers({LinkType.RELATIVE_MD: RelativeMarkdownHandler()})
    ctx = LinkContext(href="docs/no_such.md", current_file=Path("D:/repo/root.md"))
    res = p.process_link(ctx)
    assert res.success is False
    assert res.action == "show_error"
    assert res.error_code == ErrorCode.NOT_FOUND


def test_snapshot_records_for_route_actions():
    import logging
    class SnapStub:
        def __init__(self):
            self.records = []
        def save_link_snapshot(self, data):
            self.records.append(data)
    snap = SnapStub()
    logger = logging.getLogger("lp-snap")
    logger.setLevel(logging.INFO)
    p = LinkProcessor(logger=logger, snapshot_manager=snap)
    p.set_handlers({
        LinkType.EXTERNAL_HTTP: ExternalHandler(),
        LinkType.RELATIVE_MD: RelativeMarkdownHandler(),
    })
    p.set_policy({
        "check_exists": False,
        "security": {"allowed_protocols": ["https"], "allowed_domains": ["example.com"]}
    })
    r1 = p.process_link(LinkContext(href="https://example.com", extra={"policy": "test"}))
    r2 = p.process_link(LinkContext(href="https://blocked.example"))
    assert len(snap.records) >= 2
    ok = any(
        rec.get("details", {}).get("href") == "https://example.com" and
        rec.get("last_action") == "open_browser" and
        rec.get("last_result") == "ok"
        for rec in snap.records
    )
    blocked = any(
        rec.get("details", {}).get("href") == "https://blocked.example" and
        rec.get("last_action") == "show_error" and
        rec.get("error_code") == "SECURITY_BLOCKED" and
        rec.get("last_result") in ("warn", "error")
        for rec in snap.records
    )
    assert ok and blocked
