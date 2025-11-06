from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Dict, List
import pytest
import threading
from collections import Counter
from PyQt5.QtCore import QCoreApplication, Qt

PRIORITY_TEST_MODULES: List[str] = [
    "tests/test_architecture_alignment.py",
    "tests/test_boundary_condition_handling.py",
    "tests/test_content_preview.py",
    "tests/test_content_viewer.py",
    "tests/test_integration.py",
    "tests/test_performance_optimization.py",
]


_LOG_FH = None
_SESSION_T0 = None

def _ts():
    return time.strftime('%Y-%m-%d %H:%M:%S')

def pytest_configure(config):
    global _LOG_FH
    log_path = os.environ.get('PYTEST_PROGRESS_LOG', 'pytest_progress.log')
    _LOG_FH = open(log_path, 'a', buffering=1, encoding='utf-8')
    _LOG_FH.write(f"[SESSION_START] {_ts()} pid={os.getpid()}\n")
    _LOG_FH.flush()
    global _SESSION_T0
    _SESSION_T0 = time.perf_counter()
    try:
        if QCoreApplication.instance() is None:
            QCoreApplication.setAttribute(Qt.AA_UseSoftwareOpenGL, True)
            QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    except Exception:
        pass
    try:
        print(f"[SESSION_BEGIN] {_ts()} pid={os.getpid()}")
    except Exception:
        pass

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    _p0 = time.perf_counter()
    try:
        print(f"[PROTO_BEGIN] {_ts()} {item.nodeid}")
    except Exception:
        pass
    outcome = yield
    _p1 = time.perf_counter()
    try:
        print(f"[PROTO_END] {_ts()} {item.nodeid} elapsed={(_p1 - _p0):.3f}s")
    except Exception:
        pass
    return outcome

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_setup(item):
    _s0 = time.perf_counter()
    try:
        print(f"[STAGE_BEGIN] setup {_ts()} {item.nodeid}")
    except Exception:
        pass
    outcome = yield
    _s1 = time.perf_counter()
    try:
        print(f"[STAGE_END] setup {_ts()} {item.nodeid} elapsed={(_s1 - _s0):.3f}s")
    except Exception:
        pass
    return outcome

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    _c0 = time.perf_counter()
    try:
        print(f"[STAGE_BEGIN] call {_ts()} {item.nodeid}")
    except Exception:
        pass
    outcome = yield
    _c1 = time.perf_counter()
    try:
        print(f"[STAGE_END] call {_ts()} {item.nodeid} elapsed={(_c1 - _c0):.3f}s")
    except Exception:
        pass
    return outcome

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_teardown(item, nextitem):
    _t0 = time.perf_counter()
    try:
        ts = [t for t in threading.enumerate() if t is not threading.main_thread()]
        thr = [t.name for t in ts]
        def _sig(t):
            tgt = getattr(t, "_target", None)
            if callable(tgt):
                mod = getattr(tgt, "__module__", "")
                qn = getattr(tgt, "__qualname__", getattr(tgt, "__name__", ""))
                return f"{mod}:{qn}"
            return str(tgt)
        sigs = Counter([_sig(t) for t in ts])
        print(f"[STAGE_BEGIN] teardown {_ts()} {item.nodeid}")
        print(f"[TEARDOWN_THREADS_BEGIN] count={len(thr)} names={thr}")
        try:
            top = ", ".join([f"{k}={v}" for k, v in sigs.most_common(5)])
            print(f"[TEARDOWN_TARGETS_BEGIN] top5={top}")
        except Exception:
            pass
    except Exception:
        pass
    outcome = yield
    _t1 = time.perf_counter()
    try:
        ts2 = [t for t in threading.enumerate() if t is not threading.main_thread()]
        thr2 = [t.name for t in ts2]
        sigs2 = Counter([_sig(t) for t in ts2])
        print(f"[STAGE_END] teardown {_ts()} {item.nodeid} elapsed={(_t1 - _t0):.3f}s")
        print(f"[TEARDOWN_THREADS_END] count={len(thr2)} names={thr2}")
        try:
            top2 = ", ".join([f"{k}={v}" for k, v in sigs2.most_common(5)])
            print(f"[TEARDOWN_TARGETS_END] top5={top2}")
        except Exception:
            pass
    except Exception:
        pass
    return outcome

def pytest_runtest_logstart(nodeid, location):
    if _LOG_FH:
        _LOG_FH.write(f"[START] {_ts()} pid={os.getpid()} {nodeid}\n")
        _LOG_FH.flush()
    try:
        print(f"[TEST_START_TS] {_ts()} {nodeid}")
    except Exception:
        pass

def pytest_runtest_logreport(report):
    if _LOG_FH:
        _LOG_FH.write(f"[{report.when.upper()} {report.outcome.upper()}] {_ts()} pid={os.getpid()} {report.nodeid}\n")
        _LOG_FH.flush()

def pytest_runtest_logfinish(nodeid, location):
    if _LOG_FH:
        _LOG_FH.write(f"[FINISH] {_ts()} pid={os.getpid()} {nodeid}\n")
        _LOG_FH.flush()
    try:
        print(f"[TEST_FINISH_TS] {_ts()} {nodeid}")
    except Exception:
        pass

def pytest_sessionfinish(session, exitstatus):
    if _LOG_FH:
        _LOG_FH.write(f"[SESSION_FINISH] {_ts()} pid={os.getpid()} exitstatus={exitstatus}\n")
        _LOG_FH.flush()
        _LOG_FH.close()
    try:
        elapsed = None
        if _SESSION_T0 is not None:
            elapsed = time.perf_counter() - _SESSION_T0
        if elapsed is not None:
            print(f"[SESSION_END] {_ts()} pid={os.getpid()} exit={exitstatus} elapsed={elapsed:.3f}s")
        else:
            print(f"[SESSION_END] {_ts()} pid={os.getpid()} exit={exitstatus}")
        try:
            if os.environ.get('LAD_FAST_EXIT') == '1':
                os._exit(0)
        except Exception:
            pass
    except Exception:
        pass


def _normalize_path(path: Path, root: Path) -> str:
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path
    return str(rel).replace("\\", "/")


def pytest_collection_modifyitems(config, items):
    root = Path(config.rootpath)
    priority_map: Dict[str, int] = {module: index for index, module in enumerate(PRIORITY_TEST_MODULES)}
    original_order = {item: position for position, item in enumerate(items)}

    def sort_key(item):
        normalized = _normalize_path(Path(item.fspath), root)
        priority = priority_map.get(normalized, len(priority_map))
        return priority, original_order[item]

    items.sort(key=sort_key)
