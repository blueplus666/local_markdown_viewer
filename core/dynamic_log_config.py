import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class DynamicLogConfigManager:
    def __init__(self, config_file_path: str, poll_interval: float = 2.0) -> None:
        self.config_file_path = Path(config_file_path)
        self.poll_interval = max(poll_interval, 0.5)
        self.current_config: Dict[str, Any] = {}
        self._last_mtime: Optional[float] = None
        self._reload_callbacks: List[Callable[[Dict[str, Any], Dict[str, Any]], None]] = []
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger(__name__)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        self._load_and_notify(initial=True)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3.0)

    def register_reload_callback(self, callback: Callable[[Dict[str, Any], Dict[str, Any]], None]) -> None:
        if callback not in self._reload_callbacks:
            self._reload_callbacks.append(callback)

    def _watch_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                if self.config_file_path.exists():
                    mtime = self.config_file_path.stat().st_mtime
                    if self._last_mtime is None or mtime > self._last_mtime:
                        self._load_and_notify()
                        self._last_mtime = mtime
                else:
                    if self._last_mtime is not None:
                        self._last_mtime = None
                        self._load_and_notify(missing=True)
            except Exception as exc:
                self.logger.warning("log config watch loop error: %s", exc)
            time.sleep(self.poll_interval)

    def _load_and_notify(self, initial: bool = False, missing: bool = False) -> None:
        old_config = self.current_config
        new_config: Dict[str, Any] = {}
        if missing:
            self.current_config = {}
            self._notify_callbacks(old_config, new_config)
            return
        try:
            if self.config_file_path.exists():
                with self.config_file_path.open("r", encoding="utf-8") as handle:
                    new_config = json.load(handle)
            else:
                new_config = {}
        except Exception as exc:
            self.logger.warning("failed to load log config: %s", exc)
            return
        self.current_config = new_config
        if initial or old_config != new_config:
            self._notify_callbacks(old_config, new_config)

    def _notify_callbacks(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> None:
        for callback in list(self._reload_callbacks):
            try:
                callback(old_config, new_config)
            except Exception as exc:
                self.logger.warning("log config callback error: %s", exc)

    def get_current_config(self) -> Dict[str, Any]:
        return dict(self.current_config)


class RuntimeLogLevelController:
    def __init__(self) -> None:
        self._loggers: Dict[str, logging.Logger] = {}
        self._original_levels: Dict[str, int] = {}
        self.logger = logging.getLogger(__name__)

    def register_logger(self, logger: logging.Logger) -> None:
        name = logger.name or "root"
        if name not in self._loggers:
            self._loggers[name] = logger
            self._original_levels[name] = logger.level
        else:
            self._loggers[name] = logger

    def set_level(self, logger_name: str, level: str) -> None:
        logger = self._loggers.get(logger_name)
        if not logger:
            return
        numeric = getattr(logging, level.upper(), None)
        if numeric is None:
            self.logger.warning("invalid log level: %s", level)
            return
        logger.setLevel(numeric)

    def set_global_level(self, level: str) -> None:
        numeric = getattr(logging, level.upper(), None)
        if numeric is None:
            self.logger.warning("invalid global log level: %s", level)
            return
        for logger in self._loggers.values():
            logger.setLevel(numeric)

    def restore_original_levels(self) -> None:
        for name, logger in self._loggers.items():
            original = self._original_levels.get(name)
            if original is not None:
                logger.setLevel(original)

    def get_current_levels(self) -> Dict[str, str]:
        result: Dict[str, str] = {}
        for name, logger in self._loggers.items():
            result[name] = logging.getLevelName(logger.level)
        return result


__all__ = [
    "DynamicLogConfigManager",
    "RuntimeLogLevelController",
]
