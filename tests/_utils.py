#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test utilities."""

import sys
from PyQt5.QtWidgets import QApplication


def get_qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

