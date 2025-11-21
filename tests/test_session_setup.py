#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyQt测试环境初始化：确保QApplication只创建一次。
"""

import sys
from PyQt5.QtWidgets import QApplication


def ensure_qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


ensure_qapp()

