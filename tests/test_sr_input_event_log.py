# -*- coding: utf-8
"""Tests for the opt-in SR-local input event log."""
from __future__ import annotations

import copy
import unittest

from core.VitaLoom.simulation.sr_input_event_log import (
    SrInputEventLog,
    validate_sr_input_event_log_state,
)


class SrInputEventLogTests(unittest.TestCase):
    def test_append_assigns_contiguous_sequences_and_preserves_payload_copy(self) -> None:
        log = SrInputEventLog()
        payload = {"x": [1.0, 2.0]}
        event = log.append(3, "mouse_move", payload=payload)
        payload["x"].append(9.0)

        self.assertEqual(event.sequence, 0)
        self.assertEqual(log.cursor, 1)
        self.assertEqual(log.events_since(), [{"sequence": 0, "tick": 3, "action": "mouse_move", "payload": {"x": [1.0, 2.0]}}])
        returned = log.events_since()
        returned[0]["payload"]["x"].append(8.0)
        self.assertEqual(log.events_since()[0]["payload"]["x"], [1.0, 2.0])

    def test_rejects_bad_action_tick_and_payload_without_mutation(self) -> None:
        log = SrInputEventLog()
        log.append(2, "thrust", value=1.0)
        before = log.capture_state()
        invalid = (
            (1, "turn", None, None),
            (2, "unknown", None, None),
            (3, "turn", float("nan"), None),
            (3, "turn", 1.0, 2.0),
        )
        for tick, action, value, payload in invalid:
            with self.subTest(tick=tick, action=action), self.assertRaises(ValueError):
                log.append(tick, action, value, payload=payload)
            self.assertEqual(log.capture_state(), before)

    def test_snapshot_restore_and_digest_tamper_are_atomic(self) -> None:
        source = SrInputEventLog()
        source.append(0, "key_down", value="W")
        source.append(1, "key_up", value="W")
        snapshot = source.capture_state()

        target = SrInputEventLog()
        target.append(9, "thrust", value=0.5)
        before = target.capture_state()
        tampered = copy.deepcopy(snapshot)
        tampered["events"][1]["sequence"] = 4
        with self.assertRaises(ValueError):
            target.restore_state(tampered)
        self.assertEqual(target.capture_state(), before)

        target.restore_state(snapshot)
        self.assertEqual(target.capture_state(), snapshot)
        self.assertEqual(validate_sr_input_event_log_state(snapshot), {"valid": True, "errors": []})

    def test_cursor_slicing_and_restore_rejects_gaps(self) -> None:
        log = SrInputEventLog()
        log.append(4, "turn", value=0.25)
        log.append(4, "thrust", value=0.75)
        self.assertEqual(log.events_since(1)[0]["sequence"], 1)
        with self.assertRaises(ValueError):
            log.events_since(3)
        broken = log.capture_state()
        broken["events"][1]["sequence"] = 3
        broken["digest"] = ""
        with self.assertRaises(ValueError):
            log.restore_state(broken)


if __name__ == "__main__":
    unittest.main()
