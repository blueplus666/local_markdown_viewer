#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""StatusEventEmitter架构对齐测试（LAD-IMPL-007 V4.2）。"""

import unittest

from ui.status_events import StatusEventEmitter, StatusChangeEvent


class TestStatusEvents(unittest.TestCase):
    """事件系统测试。"""

    def test_event_emitter_add_and_emit(self) -> None:
        emitter = StatusEventEmitter()
        received = []

        def listener(event):
            received.append(event)

        emitter.add_listener(listener)
        emitter.emit(StatusChangeEvent("module_status", "ui", "old", "new"))
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].new_status, "new")

    def test_event_history(self) -> None:
        emitter = StatusEventEmitter(max_history=2)
        emitter.emit(StatusChangeEvent("type1", "ui", "old", "new1"))
        emitter.emit(StatusChangeEvent("type2", "ui", "old", "new2"))
        emitter.emit(StatusChangeEvent("type3", "ui", "old", "new3"))
        history = emitter.get_history(5)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].new_status, "new2")
        self.assertEqual(history[1].new_status, "new3")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
 