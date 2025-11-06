#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
方案C：混合方案 - 集成桥接（最小可行接入 MVI）
说明：不移动 outputs 产物，通过相对路径导入协调器，受配置开关控制。
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "lad_integration.json"


def _load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {"enabled": False}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"enabled": False}


async def integrate_if_enabled() -> None:
    """在配置开启时执行系统集成协调器。"""
    cfg = _load_config()
    if not cfg.get("enabled", False):
        return

    try:
        # 直接引用已迁入主项目目录的稳定模块
        from .system_integration_coordinator import SystemIntegrationCoordinator  # type: ignore
    except Exception:
        return

    coordinator = SystemIntegrationCoordinator()
    try:
        await coordinator.integrate_all_modules()
    except Exception:
        # 最小接入：静默失败，避免影响主程序启动
        return

