#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
方案C MVI 一次性运行验证脚本：
1) 打开配置开关
2) 运行集成与监控桥接
3) 校验 metrics 目录
4) 还原配置
"""

import json
from pathlib import Path
import asyncio
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CFG = PROJECT_ROOT / "config" / "lad_integration.json"
METRICS = PROJECT_ROOT / "metrics"


def main() -> int:
    # 备份配置
    original = None
    if CFG.exists():
        original = CFG.read_text(encoding="utf-8")

    try:
        enabled_cfg = {
            "enabled": True,
            "monitoring": {"enabled": True, "interval_seconds": 10}
        }
        CFG.write_text(json.dumps(enabled_cfg, ensure_ascii=False, indent=2), encoding="utf-8")

        # 确保项目根目录在 sys.path
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))

        # 运行桥接
        from integration.bridge import integrate_if_enabled
        from monitoring.bridge import start_monitoring_if_enabled

        async def run():
            await integrate_if_enabled()
            await start_monitoring_if_enabled()

        asyncio.get_event_loop().run_until_complete(run())

        # 校验输出
        ok = METRICS.exists()
        print(f"MVI_OK={ok}")
        if ok:
            files = list(METRICS.glob("**/*"))
            print("MVI_FILES=", ",".join(str(p.relative_to(PROJECT_ROOT)) for p in files))
        return 0 if ok else 1
    finally:
        # 还原配置
        if original is None:
            try:
                CFG.unlink()
            except Exception:
                pass
        else:
            CFG.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())

