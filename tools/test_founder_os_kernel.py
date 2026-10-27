#!/usr/bin/env python3
"""V-FOUNDER-KERNEL: the business-state view folds only from journal events and keeps UNKNOWN unknown.
Run from CPP repo root: python tools/test_founder_os_kernel.py.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from founder_round import initialize, start, record, close, kernel_view  # noqa: E402


class TestKernel(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "state"
        self.a = self.root / "alpha"
        self.b = self.root / "beta"
        for p in (self.a, self.b):
            (p / ".git").mkdir(parents=True)
            initialize(p, self.home)
            start(p, self.home)

    def _fact(self, repo, subject, value, cls="observed", **extra):
        row = {"kind": "observation", "summary": f"{subject} noted", "effect": "internal_reversible",
               "source_ref": f"repo:docs/{subject}.md#sha256:1", "evidence_class": cls,
               "subject": subject, "value": value}
        row.update(extra)
        return record(repo, row, self.home)

    def test_empty_journal_is_all_unknown_and_discovery_is_first(self):
        view = kernel_view(self.a, self.home)
        self.assertTrue(all(f["status"] == "UNKNOWN" for f in view["fields"].values()))
        self.assertEqual(view["plan"][0]["action"], "discover")
        self.assertEqual(view["plan"][0]["field"], "business_model")
        self.assertEqual(view["executes"], "NOTHING")
        self.assertIn("missing_evidence", view["fields"]["revenue_model"])

    def test_inference_is_not_observation_and_cannot_close_a_round(self):
        ev = self._fact(self.a, "stage", "pre-revenue", cls="inferred")
        self.assertEqual(kernel_view(self.a, self.home)["fields"]["stage"]["status"], "INFERRED")
        with self.assertRaisesRegex(ValueError, "simulated evidence cannot prove"):
            close(self.a, "UNCERTAINTY_REDUCED", [ev["event_id"]], state_home=self.home)

    def test_two_different_businesses_get_different_plans_from_evidence_only(self):
        for field, val in (("business_model", "subscription software"), ("revenue_model", "monthly plans"),
                           ("customer_segments", "small agencies"), ("stage", "early revenue")):
            self._fact(self.a, field, val)
        for field, val in (("business_model", "online retail"), ("revenue_model", "per-order margin"),
                           ("customer_segments", "consumers"), ("stage", "established")):
            self._fact(self.b, field, val)
        self._fact(self.b, "funnel", "visit to order tracked", cls="verified")
        plan_a = kernel_view(self.a, self.home)["plan"]
        plan_b = kernel_view(self.b, self.home)["plan"]
        self.assertEqual([(p["action"], p["field"]) for p in plan_a],
                         [("instrument", "funnel"), ("instrument", "metrics")])
        self.assertEqual([(p["action"], p["field"]) for p in plan_b], [("instrument", "metrics")])
        self.assertNotIn("subscription", kernel_view(self.b, self.home)["fields"]["business_model"]["value"])

    def test_contradiction_is_reported_then_resolved_only_by_supersedes(self):
        first = self._fact(self.a, "revenue_model", "monthly plans")
        self._fact(self.a, "revenue_model", "one-off licences")
        field = kernel_view(self.a, self.home)["fields"]["revenue_model"]
        self.assertEqual(field["status"], "CONTRADICTED")
        self.assertEqual(len(field["claims"]), 2)
        self.assertEqual(kernel_view(self.a, self.home)["plan"][0]["action"], "reconcile")
        self._fact(self.a, "revenue_model", "one-off licences", supersedes=first["event_id"])
        self.assertEqual(kernel_view(self.a, self.home)["fields"]["revenue_model"]["status"], "OBSERVED")

    def test_supersedes_must_name_a_same_subject_event(self):
        ev = self._fact(self.a, "stage", "idea")
        with self.assertRaisesRegex(ValueError, "supersedes must name"):
            self._fact(self.a, "budget", "none", supersedes=ev["event_id"])
        with self.assertRaisesRegex(ValueError, "supersedes must name"):
            self._fact(self.a, "stage", "idea", supersedes="not-an-event")

    def test_stale_uses_observation_date_not_record_date(self):
        old = (datetime.now(timezone.utc) - timedelta(days=200)).date().isoformat()
        self._fact(self.a, "stage", "early revenue", observed_at=old)
        field = kernel_view(self.a, self.home)["fields"]["stage"]
        self.assertEqual(field["status"], "STALE")
        self.assertEqual(field["basis"], "observed_at")
        fresh = self._fact(self.a, "stage", "early revenue")
        self.assertEqual(kernel_view(self.a, self.home)["fields"]["stage"]["status"], "OBSERVED")
        self.assertTrue(fresh["seq"] > 1)

    def test_subject_misuse_is_refused(self):
        with self.assertRaisesRegex(ValueError, "subject must be one of"):
            self._fact(self.a, "favourite_colour", "blue")
        with self.assertRaisesRegex(ValueError, "value requires a subject"):
            record(self.a, {"kind": "observation", "summary": "x", "effect": "internal_reversible",
                            "source_ref": "repo:x", "evidence_class": "observed", "value": "v"}, self.home)
        with self.assertRaisesRegex(ValueError, "only valid on observation"):
            record(self.a, {"kind": "decision", "summary": "x", "effect": "internal_reversible",
                            "subject": "stage", "value": "v"}, self.home)
        with self.assertRaisesRegex(ValueError, "observed_at"):
            self._fact(self.a, "stage", "idea", observed_at="last tuesday")

    def test_businesses_do_not_see_each_others_facts(self):
        self._fact(self.a, "business_model", "subscription software")
        self.assertEqual(kernel_view(self.b, self.home)["fields"]["business_model"]["status"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main(verbosity=2)
