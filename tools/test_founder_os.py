#!/usr/bin/env python3
"""V-FOUNDER: adversarial checks for repo-scoped business-round journal.
Run from CPP repo root: python tools/test_founder_os.py.
"""
from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path

from founder_round import initialize, start, status, record, close, _storage


class TestFounderRound(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "state"
        self.a = self.root / "QuickLease"
        self.b = self.root / "KobiCraft"
        for p in (self.a, self.b):
            (p / ".git").mkdir(parents=True)
        initialize(self.a, self.home)
        initialize(self.b, self.home)

    def _obs(self, summary="Observation", cls="observed"):
        return {"kind": "observation", "summary": summary, "effect": "internal_reversible",
                "source_ref": "repo:metrics/metrics.csv#sha256:123", "evidence_class": cls}

    def test_isolation_between_businesses(self):
        ra = start(self.a, self.home)
        self.assertIsNone(status(self.b, self.home)["active_round"])
        self.assertNotEqual(_storage(self.a, self.home), _storage(self.b, self.home))
        self.assertEqual(status(self.a, self.home)["active_round"], ra["round_id"])

    def test_subdirectory_is_same_business(self):
        child = self.a / "code" / "nested"
        child.mkdir(parents=True)
        self.assertEqual(_storage(child, self.home), _storage(self.a, self.home))
        self.assertEqual(start(child, self.home)["repository"], str(self.a))

    def test_worktree_git_marker_file(self):
        other = self.root / "CostaLuz"
        other.mkdir()
        (other / ".git").write_text("gitdir: ../common/worktrees/costaluz")
        initialize(other, self.home)
        self.assertEqual(status(other, self.home)["repository"], str(other))

    def test_no_parallel_rounds(self):
        start(self.a, self.home)
        with self.assertRaisesRegex(RuntimeError, "active"):
            start(self.a, self.home)

    def test_event_requires_source(self):
        start(self.a, self.home)
        with self.assertRaisesRegex(ValueError, "source_ref"):
            record(self.a, {"kind": "observation", "summary": "visits 100", "effect": "internal_reversible",
                            "evidence_class": "observed"}, self.home)

    def test_external_action_requires_approval_reference(self):
        start(self.a, self.home)
        with self.assertRaisesRegex(ValueError, "authorization_ref"):
            record(self.a, {"kind": "execution", "summary": "spend ad budget", "effect": "spend",
                            "action_ref": "task1", "outcome_ref": "task1-evidence"}, self.home)

    def test_projection_is_not_business_validation(self):
        start(self.a, self.home)
        e = record(self.a, self._obs(cls="simulated"), self.home)
        with self.assertRaisesRegex(ValueError, "simulated"):
            close(self.a, "UNCERTAINTY_REDUCED", [e["event_id"]], state_home=self.home)
        close(self.a, "INCONCLUSIVE", [], state_home=self.home)

    def test_impact_requires_measurement(self):
        start(self.a, self.home)
        e = record(self.a, self._obs(), self.home)
        with self.assertRaisesRegex(ValueError, "measured"):
            close(self.a, "IMPACT_VERIFIED", [e["event_id"]], state_home=self.home)
        measurement = record(self.a, {"kind": "measurement", "summary": "Validated conversion movement",
               "effect": "internal_reversible", "source_ref": "report:2026-week42", "evidence_class": "verified",
               "baseline_ref": "cohort-before", "after_ref": "cohort-after", "metric": "qualified_lead_rate",
               "window": "2026-W42", "method": "reconciled CRM funnel"}, self.home)
        c = close(self.a, "IMPACT_VERIFIED", [measurement["event_id"]], state_home=self.home)
        self.assertEqual(c["outcome"], "IMPACT_VERIFIED")
        self.assertEqual(status(self.a, self.home)["rounds_closed"], 1)

    def test_measurement_without_before_after_refused(self):
        start(self.a, self.home)
        with self.assertRaisesRegex(ValueError, "baseline_ref"):
            record(self.a, {"kind": "measurement", "summary": "missing before", "effect": "internal_reversible",
                            "source_ref": "some-report", "evidence_class": "verified"}, self.home)

    def test_capability_requires_verified_test(self):
        start(self.a, self.home)
        e = record(self.a, {"kind": "execution", "summary": "Implemented new local tool",
                 "effect": "internal_reversible", "action_ref": "commit:abc", "outcome_ref": "job:1"}, self.home)
        with self.assertRaisesRegex(ValueError, "verified test"):
            close(self.a, "CAPABILITY_VERIFIED", [e["event_id"]], state_home=self.home)

    def test_cannot_prove_with_other_round_event(self):
        start(self.a, self.home)
        e = record(self.a, self._obs(), self.home)
        close(self.a, "INCONCLUSIVE", [], state_home=self.home)
        start(self.a, self.home)
        with self.assertRaisesRegex(ValueError, "this-round"):
            close(self.a, "UNCERTAINTY_REDUCED", [e["event_id"]], state_home=self.home)

    def test_blocked_requires_reason(self):
        start(self.a, self.home)
        with self.assertRaisesRegex(ValueError, "blocker"):
            close(self.a, "BLOCKED", [], state_home=self.home)
        close(self.a, "BLOCKED", [], blocker="Waiting for Owner authorization", state_home=self.home)

    def test_tampered_journal_does_not_silently_pass(self):
        start(self.a, self.home)
        journal = _storage(self.a, self.home) / "events.jsonl"
        rows = journal.read_text().splitlines()
        row = json.loads(rows[0]);row["kind"] = "round_close"
        journal.write_text(json.dumps(row)+"\n")
        with self.assertRaisesRegex(RuntimeError, "integrity"):
            status(self.a, self.home)

    def test_lock_conflict_does_not_mutate(self):
        d = _storage(self.a, self.home)
        (d / ".write.lock").write_text("locked")
        with self.assertRaisesRegex(RuntimeError, "locked"):
            start(self.a, self.home)
        self.assertFalse((d / "events.jsonl").exists())

    def test_nested_customer_payload_is_refused(self):
        start(self.a, self.home)
        with self.assertRaisesRegex(ValueError, "metadata scalars"):
            record(self.a, {"kind": "observation", "summary": "customer table",
                "effect": "internal_reversible", "source_ref": "file:example",
                "evidence_class": "observed", "limitations": {"private_customer": "do not store"}}, self.home)

    def test_nan_is_refused(self):
        start(self.a, self.home)
        with self.assertRaisesRegex(ValueError, "non-finite"):
            record(self.a, {"kind": "observation", "summary": "bad metric",
                "effect": "internal_reversible", "source_ref": "file:example",
                "evidence_class": "observed", "estimated_value": math.nan}, self.home)

    def test_no_git_repo_refused(self):
        x = self.root / "loose";x.mkdir()
        with self.assertRaisesRegex(ValueError, "version-control"):
            initialize(x, self.home)


if __name__ == "__main__":
    unittest.main(verbosity=2)
