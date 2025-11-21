import os
import pytest
from pathlib import Path
from core.link_processor import LinkValidator, ErrorCode

pytestmark = pytest.mark.skipif(os.environ.get("LAD_RUN_013_TESTS") != "1", reason="013 tests gated")

def test_max_path_depth_blocked():
    v = LinkValidator()
    p = Path("C:/a/b/c/d/e.md")
    res = v.validate(p, {"check_exists": False, "windows_specific": {"max_path_depth": 3}})
    assert res.ok is False
    assert res.error_code == ErrorCode.SECURITY_BLOCKED

def test_drive_letter_blocked():
    v = LinkValidator()
    p = Path("E:/data/file.md")
    res = v.validate(p, {"check_exists": False, "windows_specific": {"drive_letters": ["C:", "D:"]}})
    assert res.ok is False
    assert res.error_code == ErrorCode.SECURITY_BLOCKED
