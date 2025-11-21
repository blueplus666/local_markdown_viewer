#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
方案C：混合方案 - 最小验证用例
验证目标：
1) 集成桥接在默认关闭配置下不抛异常
2) 打开监控最小开关后，可创建 metrics 输出目录
"""

import asyncio
from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_bridge_noop_when_disabled():
    from integration.bridge import integrate_if_enabled
    from monitoring.bridge import start_monitoring_if_enabled

    async def run():
        await integrate_if_enabled()
        await start_monitoring_if_enabled()

    # 不应抛异常
    asyncio.run(run())


def test_enable_monitoring_creates_metrics(tmp_path):
    cfg_path = PROJECT_ROOT / "config" / "lad_integration.json"
    original = None
    if cfg_path.exists():
        original = cfg_path.read_text(encoding="utf-8")

    try:
        cfg = {
            "enabled": True,
            "monitoring": {"enabled": True, "interval_seconds": 30}
        }
        cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

        from monitoring.bridge import start_monitoring_if_enabled

        async def run():
            await start_monitoring_if_enabled()

        asyncio.run(run())

        metrics_dir = PROJECT_ROOT / "metrics" / "bridge"
        assert metrics_dir.exists()
    finally:
        # 还原配置
        if original is None:
            try:
                cfg_path.unlink()
            except Exception:
                pass
        else:
            cfg_path.write_text(original, encoding="utf-8")

