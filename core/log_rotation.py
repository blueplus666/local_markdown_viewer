import gzip
import logging
import os
import shutil
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class IntelligentLogRotationManager:
    def __init__(self, log_file_path: str, config: Optional[Dict[str, Any]] = None) -> None:
        self.logger = logging.getLogger(__name__)
        self._rotation_callbacks: List[Callable[[], None]] = []
        self.update_config(log_file_path, config or {})

    def update_config(self, log_file_path: str, config: Dict[str, Any]) -> None:
        self.log_file_path = Path(log_file_path)
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        rotation_config = config.get("rotation", {}) if config else {}
        self.max_size_mb = rotation_config.get("max_size_mb")
        if self.max_size_mb is None:
            max_size_bytes = config.get("max_size") if config else None
            self.max_size_mb = (max_size_bytes or 10485760) / (1024 * 1024)
        self.backup_count = rotation_config.get("backup_count")
        if self.backup_count is None:
            self.backup_count = config.get("backup_count", 5)
        self.compress_backups = rotation_config.get("compress_backups", True)
        self.retention_days = rotation_config.get("retention_days", 30)
        time_str = rotation_config.get("rotation_time", "00:00")
        try:
            self.rotation_hour, self.rotation_minute = [int(x) for x in time_str.split(":", 1)]
        except Exception:
            self.rotation_hour, self.rotation_minute = 0, 0
        self._last_rotation_date: Optional[datetime] = None

    def should_rotate(self) -> bool:
        if not self.log_file_path.exists():
            return False
        file_size_mb = self.log_file_path.stat().st_size / (1024 * 1024)
        if file_size_mb >= self.max_size_mb:
            return True
        now = datetime.now()
        if self._last_rotation_date is None:
            self._last_rotation_date = now.date()
        if now.date() > self._last_rotation_date:
            if now.hour > self.rotation_hour or (now.hour == self.rotation_hour and now.minute >= self.rotation_minute):
                return True
        return False

    def rotate(self) -> None:
        if not self.log_file_path.exists():
            return
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = self.log_file_path.with_suffix("")
            rotated_path = Path(f"{base_name}_{timestamp}.log")
            os.rename(self.log_file_path, rotated_path)
            if self.compress_backups:
                compressed = rotated_path.with_suffix(rotated_path.suffix + ".gz")
                with rotated_path.open("rb") as src, gzip.open(compressed, "wb") as dst:
                    dst.writelines(src)
                rotated_path.unlink(missing_ok=True)
            self._cleanup_old_files()
            self._last_rotation_date = datetime.now().date()
            self._notify_rotation_callbacks()
        except Exception as exc:
            self.logger.warning("log rotation failed: %s", exc)

    def _cleanup_old_files(self) -> None:
        directory = self.log_file_path.parent
        base = self.log_file_path.stem
        pattern = f"{base}_"
        files = []
        for item in directory.iterdir():
            if item.is_file() and item.name.startswith(pattern) and item.name != self.log_file_path.name:
                files.append((item, item.stat().st_mtime))
        files.sort(key=lambda x: x[1], reverse=True)
        for item, _ in files[self.backup_count:]:
            item.unlink(missing_ok=True)
        cutoff = time.time() - self.retention_days * 86400
        for item, mtime in files:
            if mtime < cutoff:
                item.unlink(missing_ok=True)

    def register_rotation_callback(self, callback: Callable[[], None]) -> None:
        if callback not in self._rotation_callbacks:
            self._rotation_callbacks.append(callback)

    def _notify_rotation_callbacks(self) -> None:
        for callback in list(self._rotation_callbacks):
            try:
                callback()
            except Exception as exc:
                self.logger.warning("log rotation callback error: %s", exc)


class LogRotationScheduler:
    def __init__(self, rotation_manager: IntelligentLogRotationManager, check_interval: float = 3600.0) -> None:
        self.rotation_manager = rotation_manager
        self.check_interval = max(check_interval, 60.0)
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.logger = logging.getLogger(__name__)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3.0)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                if self.rotation_manager.should_rotate():
                    self.rotation_manager.rotate()
            except Exception as exc:
                self.logger.warning("log rotation scheduler error: %s", exc)
            self._stop_event.wait(self.check_interval)

    def set_check_interval(self, seconds: float) -> None:
        self.check_interval = max(seconds, 60.0)

    def register_rotation_callback(self, callback: Callable[[], None]) -> None:
        self.rotation_manager.register_rotation_callback(callback)


class DiskSpaceMonitor:
    def __init__(self, path: str, min_free_gb: float = 1.0, check_interval: float = 300.0) -> None:
        self.path = Path(path)
        if self.path.is_file():
            self.path = self.path.parent
        self.path.mkdir(parents=True, exist_ok=True)
        self.min_free_gb = min_free_gb
        self.check_interval = max(check_interval, 60.0)
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.logger = logging.getLogger(__name__)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3.0)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                usage = shutil.disk_usage(self.path)
                free_gb = usage.free / (1024 ** 3)
                if free_gb < self.min_free_gb:
                    self.logger.warning("disk free space below threshold: %.2f GB", free_gb)
            except Exception as exc:
                self.logger.warning("disk space monitor error: %s", exc)
            self._stop_event.wait(self.check_interval)

    def update_settings(self, min_free_gb: float, check_interval: float) -> None:
        self.min_free_gb = min_free_gb
        self.check_interval = max(check_interval, 60.0)


__all__ = [
    "IntelligentLogRotationManager",
    "LogRotationScheduler",
    "DiskSpaceMonitor",
]
