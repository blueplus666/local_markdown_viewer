import os
import json
import time
import unittest
from pathlib import Path
from datetime import datetime, timedelta

from error_history.core.manager import ErrorHistoryManager
from utils.config_manager import ConfigManager
from error_history.core.models import ErrorRecord, ErrorSeverity


class TestErrorHistoryHotReloadAndCleanup(unittest.TestCase):
    def setUp(self):
        # 临时测试目录
        self.tmp_root = Path(".tmp_test_eh").absolute()
        if self.tmp_root.exists():
            # 清理历史
            for p in self.tmp_root.rglob("*"):
                try:
                    if p.is_file():
                        p.unlink()
                except Exception:
                    pass
        self.tmp_root.mkdir(parents=True, exist_ok=True)

        # 配置目录（必须指向包含配置文件的目录）
        self.config_dir = self.tmp_root / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # 数据库文件
        self.db_path = self.tmp_root / "error_history_test.db"

    def tearDown(self):
        try:
            if hasattr(self, 'manager') and self.manager:
                self.manager.shutdown()
        except Exception:
            pass

    def _write_error_handling(self, payload: dict):
        cfg_path = self.config_dir / "error_handling.json"
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        # 确保 mtime 发生变化
        os.utime(cfg_path, None)
        return cfg_path

    def test_hot_reload_updates_config(self):
        # 初始配置：retention_days=30, max_connections=5
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

        # 修改配置：retention_days=7, max_connections=2
        updated = initial.copy()
        updated["error_history"] = dict(initial["error_history"], retention_days=7, max_connections=2)
        self._write_error_handling(updated)

        # 等待文件监听生效（轮询2s间隔，最多等待6s）
        ok = False
        for _ in range(12):
            if self.manager.config.retention_days == 7 and self.manager.config.max_connections == 2:
                ok = True
                break
            time.sleep(0.5)
        self.assertTrue(ok, "配置热重载未在预期时间内生效")

    def test_auto_cleanup_scheduler_deletes_old_records(self):
        # 配置为每1秒清理，保留1天
        initial = {
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
        self._write_error_handling(initial)

        cfg = ConfigManager(config_dir=str(self.config_dir))
        self.manager = ErrorHistoryManager(db_path=str(self.db_path), config_manager=cfg)

        # 写入一条10天前的错误记录
        rec = ErrorRecord(
            error_id="UT_ERR_OLD",
            error_type="ValueError",
            error_message="old record",
            severity=ErrorSeverity.LOW
        )
        self.manager.save_error(rec)

        ten_days_ago = (datetime.now() - timedelta(days=10)).isoformat()
        with self.manager._get_connection() as conn:
            conn.execute("UPDATE error_history SET created_at = ? WHERE error_id = ?", (ten_days_ago, "UT_ERR_OLD"))
            conn.commit()

        # 等待清理任务执行（@every 1s），最多等待8s
        removed = False
        for _ in range(16):
            info = self.manager.get_database_info()
            count = info.get('table_counts', {}).get('error_history', 0)
            if count == 0:
                removed = True
                break
            time.sleep(0.5)
        self.assertTrue(removed, "自动清理未在预期时间内删除过期记录")


if __name__ == "__main__":
    unittest.main()
