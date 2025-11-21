#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import unittest
import uuid
from pathlib import Path

from core.link_processor import (
    LinkProcessor,
    LinkContext,
    LinkType,
    LinkResult,
    ErrorCode,
)
from utils.config_manager import ConfigManager


class _StubHttpHandler:
    def handle(self, ctx: LinkContext, resolved):
        return LinkResult(success=True, action="open_browser", payload={"url": resolved}, message="", error_code=None)


class TestSecurityPolicyMinimal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("LAD_TEST_MODE", "1")

    def test_config_loading_features(self):
        cm = ConfigManager()
        sec = cm.get_unified_config("features.security", {})
        lp = cm.get_unified_config("features.link_processing", {})
        self.assertIsInstance(sec, dict)
        self.assertIsInstance(lp, dict)
        self.assertIn("allowed_protocols", sec)
        self.assertIn("allowed_domains", sec)
        self.assertIn("windows_specific", sec)
        self.assertIn("check_exists", lp)
        self.assertIn("security", lp)
        self.assertIn("windows_specific", lp)
        self.assertIn("logging", lp)

    def test_external_https_allowed_domain_from_features(self):
        cm = ConfigManager()
        lp = LinkProcessor(config_manager=cm)
        lp.set_handlers({LinkType.EXTERNAL_HTTP: _StubHttpHandler()})
        ctx = LinkContext(href="https://example.com", current_file=None, current_dir=None)
        res = lp.process_link(ctx)
        # 允许域名时，不应出现 SECURITY_BLOCKED
        self.assertNotEqual(res.error_code, ErrorCode.SECURITY_BLOCKED)

    def test_external_https_blocked_domain_fail_closed(self):
        cm = ConfigManager()
        lp = LinkProcessor(config_manager=cm)
        lp.set_handlers({LinkType.EXTERNAL_HTTP: _StubHttpHandler()})
        policy = {
            "check_exists": True,
            "security": {"allowed_protocols": ["https"], "allowed_domains": []},
        }
        lp.set_policy(policy)
        ctx = LinkContext(href="https://not-allowed.example", current_file=None, current_dir=None)
        res = lp.process_link(ctx)
        self.assertEqual(res.error_code, ErrorCode.SECURITY_BLOCKED)
        self.assertFalse(res.success)
        self.assertEqual(res.action, "show_error")

    def test_http_protocol_blocked_by_protocols(self):
        cm = ConfigManager()
        lp = LinkProcessor(config_manager=cm)
        lp.set_handlers({LinkType.EXTERNAL_HTTP: _StubHttpHandler()})
        policy = {
            "check_exists": True,
            "security": {"allowed_protocols": ["https"], "allowed_domains": ["example.com"]},
        }
        lp.set_policy(policy)
        ctx = LinkContext(href="http://example.com", current_file=None, current_dir=None)
        res = lp.process_link(ctx)
        self.assertEqual(res.error_code, ErrorCode.SECURITY_BLOCKED)
        self.assertFalse(res.success)

    def test_file_protocol_not_found(self):
        cm = ConfigManager()
        lp = LinkProcessor(config_manager=cm)
        # 构造当前盘符下的一个极小概率存在的文件路径
        drive = Path.cwd().drive or "C:"
        name = f"unlikely_nonexistent_{uuid.uuid4().hex}.md"
        url = f"file:///{drive}/{name}".replace("\\", "/")
        ctx = LinkContext(href=url, current_file=None, current_dir=None)
        res = lp.process_link(ctx)
        self.assertEqual(res.error_code, ErrorCode.NOT_FOUND)
        self.assertFalse(res.success)

    def test_relative_path_depth_exceeded(self):
        cm = ConfigManager()
        lp = LinkProcessor(config_manager=cm)
        policy = {
            "check_exists": False,
            "windows_specific": {"max_path_depth": 1},
            "security": {"allowed_protocols": ["https"], "allowed_domains": ["example.com"]},
        }
        lp.set_policy(policy)
        base = Path.cwd() / "base.md"
        ctx = LinkContext(href="a/b/c/d.md", current_file=base)
        res = lp.process_link(ctx)
        self.assertEqual(res.error_code, ErrorCode.SECURITY_BLOCKED)
        # 现有实现会将验证信息放入 message，而非 payload 细节
        self.assertIn("max depth", (res.message or "").lower())

    def test_drive_letters_restriction(self):
        cm = ConfigManager()
        lp = LinkProcessor(config_manager=cm)
        cur_drive = (Path.cwd().drive or "C:")
        # 设置一个不包含当前盘符的白名单
        allow_drive = "Z:"
        policy = {
            "check_exists": False,
            "windows_specific": {"drive_letters": [allow_drive]},
            "security": {"allowed_protocols": ["https"], "allowed_domains": ["example.com"]},
        }
        lp.set_policy(policy)
        # 构造当前盘符上的绝对路径
        abs_path = Path(cur_drive + "\\") / "some" / "path" / "file.md"
        url = f"file:///{abs_path.as_posix()}"
        ctx = LinkContext(href=url)
        res = lp.process_link(ctx)
        self.assertEqual(res.error_code, ErrorCode.SECURITY_BLOCKED)

    def test_forbidden_patterns_block(self):
        cm = ConfigManager()
        lp = LinkProcessor(config_manager=cm)
        policy = {
            "check_exists": False,
            "security": {"forbidden_patterns": ["__FORBID__"]},
        }
        lp.set_policy(policy)
        base = Path.cwd() / "base.md"
        ctx = LinkContext(href=str(Path("foo") / "__FORBID__" / "bar.md"), current_file=base)
        res = lp.process_link(ctx)
        self.assertEqual(res.error_code, ErrorCode.SECURITY_BLOCKED)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
