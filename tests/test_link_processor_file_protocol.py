import os
import pytest
import logging
from pathlib import Path
from core.link_processor import LinkProcessor, LinkType, LinkContext, FileProtocolHandler, ErrorCode

pytestmark = pytest.mark.skipif(os.environ.get("LAD_RUN_013_TESTS") != "1", reason="013 tests gated")

def test_file_protocol_parse_ok():
    logger = logging.getLogger("lp-file-ok")
    logger.setLevel(logging.INFO)
    p = LinkProcessor(logger=logger)
    p.set_policy({"check_exists": False})
    p.set_handlers({LinkType.FILE_PROTOCOL: FileProtocolHandler()})
    ctx = LinkContext(href="file:///C:/data/a.md")
    res = p.process_link(ctx)
    assert res.success is True
    assert res.action == "open_markdown_in_tree"

def test_file_protocol_not_found_when_check_exists_true():
    logger = logging.getLogger("lp-file-miss")
    logger.setLevel(logging.INFO)
    p = LinkProcessor(logger=logger)
    p.set_handlers({LinkType.FILE_PROTOCOL: FileProtocolHandler()})
    ctx = LinkContext(href="file:///C:/no_such_dir/no_such_file.md")
    res = p.process_link(ctx)
    assert res.success is False
    assert res.action == "show_error"
    assert res.error_code == ErrorCode.NOT_FOUND
