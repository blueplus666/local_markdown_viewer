import os
import pytest
import logging
from pathlib import Path
from core.link_processor import LinkProcessor, LinkType, LinkContext, RelativeMarkdownHandler, ErrorCode, LinkValidator

pytestmark = pytest.mark.skipif(os.environ.get("LAD_RUN_013_TESTS") != "1", reason="013 tests gated")

def test_relative_path_resolves_and_open_action():
    logger = logging.getLogger("lp-rel-open")
    logger.setLevel(logging.INFO)
    p = LinkProcessor(logger=logger)
    p.set_policy({"check_exists": False})
    p.set_handlers({LinkType.RELATIVE_MD: RelativeMarkdownHandler()})
    ctx = LinkContext(href="../images/pic.md", current_file=Path("D:/proj/docs/guide.md"))
    res = p.process_link(ctx)
    assert res.success is True
    assert res.action == "open_markdown_in_tree"

def test_relative_path_not_found_when_check_exists_true():
    logger = logging.getLogger("lp-rel-miss")
    logger.setLevel(logging.INFO)
    p = LinkProcessor(logger=logger)
    p.set_handlers({LinkType.RELATIVE_MD: RelativeMarkdownHandler()})
    ctx = LinkContext(href="docs/no_such.md", current_file=Path("D:/repo/root.md"))
    res = p.process_link(ctx)
    assert res.success is False
    assert res.action == "show_error"
    assert res.error_code == ErrorCode.NOT_FOUND

def test_forbidden_patterns_block():
    v = LinkValidator()
    res = v.validate(Path("C:/tmp/~/.hidden"), {"check_exists": False, "security": {"forbidden_patterns": ["~"]}})
    assert res.ok is False
    assert res.error_code == ErrorCode.SECURITY_BLOCKED
