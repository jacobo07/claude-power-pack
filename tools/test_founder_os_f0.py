#!/usr/bin/env python3
"""V-FOUNDER-F0: adversarial checks found by the Founder OS v1 audit of v0.
Run from CPP repo root: python tools/test_founder_os_f0.py.

Every refusal below is paired with a control where the fact exists and the
input is admitted, so a gate that refuses everything cannot pass.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from founder_round import initialize, start, status, record, recover, _storage  # noqa: E402


def _dead_pid() -> int:
    p = subprocess.Popen([sys.executable, "-c", "pass"])
    p.wait()
    return p.pid


class TestFounderF0(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "state"
        self.a = self.root / "Biz"
        (self.a / ".git").mkdir(parents=True)
        initialize(self.a, self.home)
        start(self.a, self.home)
        self.d = _storage(self.a, self.home)

    def _ev(self, summary, **extra):
        row = {"kind": "observation", "summary": summary, "effect": "internal_reversible",
               "source_ref": "repo:metrics.csv#sha256:1", "evidence_class": "observed"}
        row.update(extra)
        return row

    # F0-1 personal data and live payment keys must not reach the journal
    def test_personal_data_is_refused(self):
        for text in ("customer jane.doe@example.com paid", "IBAN ES9121000418450200051332",
                     "card 4111 1111 1111 1111", "call +34 600 123 456",
                     "key sk_live_" + "C" * 24):
            with self.subTest(text=text):
                with self.assertRaisesRegex(ValueError, "personal or secret data"):
                    record(self.a, self._ev(text), self.home)

    def test_clean_summary_with_numbers_is_admitted(self):
        out = record(self.a, self._ev("signups rose from 120 to 150 in week 42, 2026"), self.home)
        self.assertEqual(out["seq"], 2)

    # F0-2 an amount travels with its currency
    def test_amount_requires_currency_and_nonnegative(self):
        with self.assertRaisesRegex(ValueError, "currency"):
            record(self.a, self._ev("projected", estimated_value=1200), self.home)
        with self.assertRaisesRegex(ValueError, "negative"):
            record(self.a, self._ev("projected", estimated_cost=-5, currency="EUR"), self.home)
        out = record(self.a, self._ev("projected", estimated_value=1200, currency="EUR"), self.home)
        self.assertEqual(out["seq"], 2)

    # F0-3 a repeated action is not a second action
    def test_duplicate_action_ref_is_refused(self):
        ex = {"kind": "execution", "summary": "sent price test", "effect": "internal_reversible",
              "action_ref": "git:abc123", "outcome_ref": "repo:out.json"}
        record(self.a, ex, self.home)
        with self.assertRaisesRegex(ValueError, "duplicate action_ref"):
            record(self.a, ex, self.home)
        record(self.a, dict(ex, action_ref="git:def456"), self.home)

    # F0-4 a crash mid-append leaves a recoverable, explicitly named state
    def test_torn_tail_is_named_and_recoverable(self):
        record(self.a, self._ev("first fact"), self.home)
        events = self.d / "events.jsonl"
        before = events.read_bytes()
        with events.open("ab") as f:
            f.write(b'{"seq": 4, "kind": "obs')
        with self.assertRaisesRegex(RuntimeError, "TORN_TAIL"):
            status(self.a, self.home)
        out = recover(self.a, self.home)
        self.assertEqual(out["quarantined_bytes"], len(b'{"seq": 4, "kind": "obs'))
        self.assertEqual(events.read_bytes(), before)
        self.assertEqual(status(self.a, self.home)["journal_integrity"], "VERIFIED")
        self.assertTrue(any(self.d.glob("torn-tail-*.bin")))

    def test_mid_journal_corruption_is_not_recoverable(self):
        record(self.a, self._ev("first fact"), self.home)
        record(self.a, self._ev("second fact"), self.home)
        events = self.d / "events.jsonl"
        lines = events.read_text(encoding="utf-8").splitlines()
        row = json.loads(lines[1])
        row["payload"] = {"summary": "tampered"}
        lines[1] = json.dumps(row, sort_keys=True)
        events.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "integrity failure"):
            recover(self.a, self.home)

    # F0-5 a dead owner's lock is named stale; a live owner's lock is untouched
    def test_stale_lock_is_recoverable_but_live_lock_is_not(self):
        lock = self.d / ".write.lock"
        lock.write_text(json.dumps({"pid": _dead_pid(), "time": "2026-01-01T00:00:00+00:00"}))
        with self.assertRaisesRegex(RuntimeError, "stale"):
            record(self.a, self._ev("blocked by stale lock"), self.home)
        out = recover(self.a, self.home)
        self.assertTrue(out["stale_lock_removed"])
        record(self.a, self._ev("after recovery"), self.home)
        lock.write_text(json.dumps({"pid": os.getpid(), "time": "2026-01-01T00:00:00+00:00"}))
        with self.assertRaisesRegex(RuntimeError, "locked"):
            recover(self.a, self.home)
        self.assertTrue(lock.exists())
        lock.unlink()


if __name__ == "__main__":
    unittest.main(verbosity=2)
