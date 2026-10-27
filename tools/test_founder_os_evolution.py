#!/usr/bin/env python3
"""V-FOUNDER-EVOLVE: opportunity lifecycle, live cap, evidence-gated success, evidence-based bottleneck.
Run from the CPP repo root: python tools/test_founder_os_evolution.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT))
from founder_round import initialize, start, record, backlog_view  # noqa: E402


class TestEvolution(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / "state"
        self.a = Path(self.temp.name) / "a"
        (self.a / ".git").mkdir(parents=True)
        initialize(self.a, self.home)
        start(self.a, self.home)

    def _opp(self, name="raise activation", **extra):
        row = {"kind": "opportunity", "summary": name, "effect": "internal_reversible",
               "success_gate": "activation up by a measured amount", "abandon_gate": "no change after 4 weeks"}
        row.update(extra)
        return record(self.a, row, self.home)["event_id"]

    def _decide(self, ref, change, **extra):
        row = {"kind": "decision", "summary": f"{change} it", "effect": "internal_reversible",
               "opportunity_ref": ref, "state_change": change}
        row.update(extra)
        return record(self.a, row, self.home)

    def _measure(self, ref, cls="verified"):
        return record(self.a, {"kind": "measurement", "summary": "activation measured",
                               "effect": "internal_reversible", "source_ref": "repo:exports/a.csv#sha256:1",
                               "evidence_class": cls, "baseline_ref": "repo:exports/b.csv", "after_ref": "repo:exports/a.csv",
                               "metric": "activation", "window": "2026-W40..W43", "method": "before-after",
                               "opportunity_ref": ref}, self.home)["event_id"]

    def _state(self, ref):
        return backlog_view(self.a, self.home)["opportunities"][ref]["state"]

    def test_full_cycle_propose_adopt_measure_succeed(self):
        ref = self._opp()
        self.assertEqual(self._state(ref), "PROPOSED")
        self._decide(ref, "adopt")
        self.assertEqual(self._state(ref), "ACTIVE")
        m = self._measure(ref)
        self._decide(ref, "succeed", proof_ref=m)
        self.assertEqual(self._state(ref), "DONE")

    def test_success_without_or_with_weak_proof_is_refused(self):
        ref = self._opp()
        self._decide(ref, "adopt")
        with self.assertRaisesRegex(ValueError, "proof_ref naming a measurement"):
            self._decide(ref, "succeed")
        sim = self._measure(ref, cls="simulated")
        with self.assertRaisesRegex(ValueError, "verified measurement"):
            self._decide(ref, "succeed", proof_ref=sim)
        other = self._opp("other idea")
        with self.assertRaisesRegex(ValueError, "proof_ref naming a measurement"):
            self._decide(ref, "succeed", proof_ref=self._measure(other))
        self.assertEqual(self._state(ref), "ACTIVE")

    def test_live_cap_forces_a_decision_before_new_ideas(self):
        refs = [self._opp(f"idea {i}") for i in range(5)]
        with self.assertRaisesRegex(ValueError, "live opportunity cap"):
            self._opp("idea 6")
        self._decide(refs[0], "abandon")
        self._opp("idea 6")
        self.assertEqual(backlog_view(self.a, self.home)["live"], 5)

    def test_terminal_cannot_move_and_order_is_enforced(self):
        ref = self._opp()
        with self.assertRaisesRegex(ValueError, "requires the opportunity to be ACTIVE"):
            self._decide(ref, "succeed", proof_ref=self._measure(ref))
        self._decide(ref, "abandon")
        with self.assertRaisesRegex(ValueError, "terminal opportunity"):
            self._decide(ref, "adopt")

    def test_merge_needs_a_different_live_target(self):
        a, b = self._opp("a"), self._opp("b")
        with self.assertRaisesRegex(ValueError, "different live opportunity"):
            self._decide(a, "merge", merged_into=a)
        self._decide(a, "merge", merged_into=b)
        self.assertEqual(self._state(a), "ABANDONED")
        self.assertEqual(self._state(b), "PROPOSED")

    def test_lifecycle_fields_are_only_valid_on_decisions(self):
        with self.assertRaisesRegex(ValueError, "only valid on a decision"):
            self._opp(state_change="adopt")
        with self.assertRaisesRegex(ValueError, "confidence must be"):
            self._opp(confidence="certain")
        self._opp(confidence="low")

    def test_bottleneck_is_null_without_evidence_and_points_at_the_best_reducer(self):
        b = backlog_view(self.a, self.home)["bottleneck"]
        self.assertIsNone(b["bottleneck"])
        self.assertEqual(b["next"]["action"], "discover")

    def test_inferred_bottleneck_is_not_a_selection_observed_one_is(self):
        def say(cls):
            record(self.a, {"kind": "observation", "summary": "bottleneck noted", "effect": "internal_reversible",
                            "source_ref": "repo:docs/b.md#sha256:1", "evidence_class": cls,
                            "subject": "bottleneck", "value": "trial to paid conversion"}, self.home)
        say("inferred")
        b = backlog_view(self.a, self.home)["bottleneck"]
        self.assertIsNone(b["bottleneck"])
        self.assertIn("inferred", b["reason"])
        say("observed")
        b = backlog_view(self.a, self.home)["bottleneck"]
        self.assertEqual(b["bottleneck"], "trial to paid conversion")
        self.assertEqual(b["provenance"], "repo:docs/b.md#sha256:1")

    def test_real_command(self):
        self._opp()
        env = dict(os.environ, CPP_FOUNDER_STATE_DIR=str(self.home))
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "founder_round.py"), "--repo", str(self.a),
                            "backlog"], capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["live"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
