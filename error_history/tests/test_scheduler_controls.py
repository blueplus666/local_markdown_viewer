import os
import json
import time
import unittest
from pathlib import Path
from datetime import datetime, timedelta

from error_history.core.manager import ErrorHistoryManager
from utils.config_manager import ConfigManager
from error_history.core.models import ErrorRecord, ErrorSeverity


class TestSchedulerControls(unittest.TestCase):
    def setUp(self):
        # 准备临时根目录与配置/数据库路径
        self.tmp_root = Path(".tmp_test_eh2").absolute()
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
        self.db_path = self.tmp_root / "error_history_test2.db"
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

    def _make_manager(self, cfg_payload: dict) -> ErrorHistoryManager:
        self._write_error_handling(cfg_payload)
        cfg = ConfigManager(config_dir=str(self.config_dir))
        mgr = ErrorHistoryManager(db_path=str(self.db_path), config_manager=cfg)
        return mgr

    def test_trigger_cleanup_now_deletes_old_records(self):
        payload = {
            "error_history": {
                "enabled": True,
                "database_path": str(self.db_path),
                "retention_days": 1,
                "auto_cleanup": False,
                "cleanup_schedule": "@every 10s",
                "max_connections": 5,
                "timeout_seconds": 30
            }
        }
        self.manager = self._make_manager(payload)

        rec = ErrorRecord(
            error_id="UT_NOW_DEL",
            error_type="ValueError",
            error_message="old",
            severity=ErrorSeverity.LOW,
        )
        self.manager.save_error(rec)
        ten_days_ago = (datetime.now() - timedelta(days=10)).isoformat()
        with self.manager._get_connection() as conn:  # noqa: accessing context
            conn.execute("UPDATE error_history SET created_at = ? WHERE error_id = ?", (ten_days_ago, "UT_NOW_DEL"))
            conn.commit()

        deleted = self.manager.trigger_cleanup_now()
        self.assertGreaterEqual(deleted, 1)

        info = self.manager.get_database_info()
        self.assertEqual(info.get('table_counts', {}).get('error_history', 0), 0)

    def test_restart_scheduler_toggles_running_state(self):
        payload = {
            "error_history": {
                "enabled": True,
                "database_path": str(self.db_path),
                "retention_days": 1,
                "auto_cleanup": False,
                "cleanup_schedule": "@every 1s",
                "max_connections": 5,
                "timeout_seconds": 30
            }
        }
        self.manager = self._make_manager(payload)

        # 初始未启用自动清理
        st = self.manager.get_cleanup_status()
        self.assertFalse(st.get('enabled'))
        self.assertFalse(st.get('running'))

        # 启用并重启
        self.manager.config.auto_cleanup = True
        self.manager.config.cleanup_schedule = "@every 1s"
        self.assertTrue(self.manager.restart_scheduler())

        # 等待线程启动
        ok = False
        for _ in range(10):
            st = self.manager.get_cleanup_status()
            if st.get('running'):
                ok = True
                break
            time.sleep(0.2)
        self.assertTrue(ok, "调度器未在预期时间内运行")

        # 关闭并重启
        self.manager.config.auto_cleanup = False
        self.assertTrue(self.manager.restart_scheduler())
        time.sleep(0.5)
        st = self.manager.get_cleanup_status()
        self.assertFalse(st.get('running'))

    def test_get_cleanup_status_mode_and_next_run(self):
        payload = {
            "error_history": {
                "enabled": True,
                "database_path": str(self.db_path),
                "retention_days": 1,
                "auto_cleanup": True,
                "cleanup_schedule": "@every 1s",
                "max_connections": 5,
                "timeout_seconds": 30
            }
        }
        self.manager = self._make_manager(payload)
        time.sleep(0.2)
        st = self.manager.get_cleanup_status()
        self.assertEqual(st.get('mode'), 'interval')
        self.assertIsNotNone(st.get('next_run'))


if __name__ == "__main__":
    unittest.main()
