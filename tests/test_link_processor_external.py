import os
import pytest
import logging
from core.link_processor import LinkProcessor, LinkType, LinkContext, ExternalHandler, ErrorCode

pytestmark = pytest.mark.skipif(os.environ.get("LAD_RUN_013_TESTS") != "1", reason="013 tests gated")

def test_external_allowlist_allow():
    logger = logging.getLogger("lp-ext-allow")
    logger.setLevel(logging.INFO)
    p = LinkProcessor(logger=logger)
    p.set_handlers({LinkType.EXTERNAL_HTTP: ExternalHandler()})
    ctx = LinkContext(href="https://example.com")
    res = p.process_link(ctx)
    assert res.success is True
    assert res.action == "open_browser"

def test_external_allowlist_block_not_in_list():
    logger = logging.getLogger("lp-ext-block")
    logger.setLevel(logging.INFO)
    p = LinkProcessor(logger=logger)
    p.set_handlers({LinkType.EXTERNAL_HTTP: ExternalHandler()})
    ctx = LinkContext(href="https://evil.com")
    res = p.process_link(ctx)
    assert res.success is False
    assert res.action == "show_error"
    assert res.error_code == ErrorCode.SECURITY_BLOCKED

def test_protocol_enforcement_disallow_http_when_https_only():
    logger = logging.getLogger("lp-ext-http")
    logger.setLevel(logging.INFO)
    p = LinkProcessor(logger=logger)
    p.set_handlers({LinkType.EXTERNAL_HTTP: ExternalHandler()})
    ctx = LinkContext(href="http://example.com")
    res = p.process_link(ctx)
    assert res.success is False
    assert res.error_code == ErrorCode.SECURITY_BLOCKED

def test_protocol_mailto_allowed_when_whitelisted():
    logger = logging.getLogger("lp-ext-mailto")
    logger.setLevel(logging.INFO)
    p = LinkProcessor(logger=logger)
    p.set_handlers({LinkType.EXTERNAL_HTTP: ExternalHandler()})
    ctx = LinkContext(href="mailto:user@example.com")
    res = p.process_link(ctx)
    assert res.success is True
    assert res.action == "open_browser"

def test_logging_blocked_has_errorcode_and_action(caplog):
    logger = logging.getLogger("lp-ext-log")
    logger.setLevel(logging.INFO)
    p = LinkProcessor(logger=logger)
    p.set_handlers({LinkType.EXTERNAL_HTTP: ExternalHandler()})
    p.set_policy({"logging": {"json": True}})
    with caplog.at_level(logging.INFO, logger="lp-ext-log"):
        ctx = LinkContext(href="https://evil.com")
        res = p.process_link(ctx)
        assert res.success is False
    found = any(("SECURITY_BLOCKED" in rec.message) and ("show_error" in rec.message) for rec in caplog.records)
    assert found
