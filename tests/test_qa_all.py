#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4.3.4 QA 聚合入口：串联 4.3.3 验证用例，覆盖 功能/性能/稳定性/告警。
允许逐项失败时定位具体脚本。
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "第二阶段实现提示词" / "本地Markdown文件渲染程序-重构过程-第二阶段核心功能-06_后期完善-实现提示词" / "outputs"


def _run(cmd: list[str]):
    print("RUN:", " ".join(cmd))
    # 强制子进程启用UTF-8，避免Windows控制台GBK导致emoji报错
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    print(proc.stdout)
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
    assert proc.returncode == 0, f"命令执行失败: {' '.join(cmd)}"


def test_run_integration_suite():
    # 运行 4.3.3 集成测试
    script = OUT / "integration_test_suite.py"
    _run([sys.executable, "-X", "utf8", str(script)])


def test_run_validation_suite():
    # 运行 4.3.3 验证测试（含性能/稳定性/告警验证）
    script = OUT / "validation_test.py"
    _run([sys.executable, "-X", "utf8", str(script)])


def test_minimal_ci_asserts():
    # 使用最小门禁进行最终断言
    script = ROOT / "tests" / "test_qa_minimal.py"
    _run([sys.executable, "-m", "pytest", str(script), "-q"])

