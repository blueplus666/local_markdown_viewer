import os
import json
import time
import unittest
from pathlib import Path

try:
    import watchdog.events  # noqa: F401
    HAS_WATCHDOG = True
except Exception:
    HAS_WATCHDOG = False

from error_history.core.manager import ErrorHistoryManager
from utils.config_manager import ConfigManager


@unittest.skipUnless(HAS_WATCHDOG, "watchdog not installed; skipping event-driven hot reload test")
class TestWatchdogHotReload(unittest.TestCase):
    def setUp(self):
        self.tmp_root = Path(".tmp_test_eh_wd").absolute()
        if self.tmp_root.exists():
            for p in sorted(self.tmp_root.rglob("*"), reverse=True):
                try:
                    if p.is_file():
                        p.unlink()
                    elif p.is_dir():
                        try:
                            p.rmdir()
                        except Exception:
                            pass
                except Exception:
                    pass
        self.tmp_root.mkdir(parents=True, exist_ok=True)
        self.config_dir = self.tmp_root / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.tmp_root / "error_history_wd.db"
        self.manager = None

    def tearDown(self):
        try:
            if self.manager:
                self.manager.shutdown()
        except Exception:
            pass

    def _write_error_handling(self, payload: dict):
        path = self.config_dir / "error_handling.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.utime(path, None)
        return path

    def test_watchdog_hot_reload_applies_config_quickly(self):
        initial = {
            "error_history": {
                "enabled": True,
                "database_path": str(self.db_path),
                "retention_days": 30,
                "auto_cleanup": False,
                "cleanup_schedule": "@every 10s",
                "max_connections": 5,
                "timeout_seconds": 30
            }
        }
        self._write_error_handling(initial)
        cfg = ConfigManager(config_dir=str(self.config_dir))
        self.manager = ErrorHistoryManager(db_path=str(self.db_path), config_manager=cfg)

        updated = initial.copy()
        updated["error_history"] = dict(initial["error_history"], retention_days=7)
        self._write_error_handling(updated)

        # watchdog 事件监听应在 < 2s 内生效，这里最多等待 5s
        ok = False
        for _ in range(25):
            if self.manager.config.retention_days == 7:
                ok = True
                break
            time.sleep(0.2)
        self.assertTrue(ok, "watchdog 热重载未在预期时间内应用配置变更")


if __name__ == "__main__":
    unittest.main()
