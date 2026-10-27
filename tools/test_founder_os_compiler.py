#!/usr/bin/env python3
"""V-FOUNDER-COMPILER: lens contexts carry provenance, keep gaps as gaps, and never cross businesses.
Run from the CPP repo root: python tools/test_founder_os_compiler.py
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
from founder_round import initialize, start, record, context_for  # noqa: E402
from modules.founder_os import compiler  # noqa: E402

SECRET_A = "annual contracts for dental clinics"
SECRET_B = "pottery sold at weekend markets"


class TestCompiler(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        os.chdir(ROOT)
        self.addCleanup(os.chdir, self._cwd)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "state"
        self.a, self.b = self.root / "a", self.root / "b"
        for p in (self.a, self.b):
            (p / ".git").mkdir(parents=True)
            initialize(p, self.home)
            start(p, self.home)

    def _fact(self, repo, subject, value, cls="observed"):
        return record(repo, {"kind": "observation", "summary": f"{subject} noted",
                             "effect": "internal_reversible", "source_ref": f"repo:docs/{subject}.md#sha256:1",
                             "evidence_class": cls, "subject": subject, "value": value}, self.home)

    def test_every_item_has_provenance_or_is_a_named_gap(self):
        self._fact(self.a, "revenue_model", SECRET_A)
        out = context_for(self.a, "Finance", self.home)
        for item in out["items"]:
            if item["kind"] == "gap":
                self.assertIn("Needs", item["text"])
            else:
                self.assertTrue(item["provenance"], item)
        fact = next(i for i in out["items"] if i["field"] == "revenue_model")
        self.assertEqual(fact["kind"], "observed_fact")
        self.assertEqual(fact["provenance"][0]["source_ref"], "repo:docs/revenue_model.md#sha256:1")

    def test_unknown_stays_a_gap_not_an_invented_value(self):
        out = context_for(self.a, "Finance", self.home)
        by_field = {i["field"]: i for i in out["items"] if i["field"]}
        self.assertEqual({by_field[f]["kind"] for f in ("budget", "costs", "margins")}, {"gap"})
        self.assertNotIn("unknown_value", json.dumps(out))

    def test_lens_gets_only_its_fields(self):
        self._fact(self.a, "risks", "single supplier")
        self._fact(self.a, "margins", "thin")
        fields = {i["field"] for i in context_for(self.a, "Finance", self.home)["items"] if i["field"]}
        self.assertIn("margins", fields)
        self.assertNotIn("risks", fields)

    def test_competitive_returns_a_named_gap_not_remembered_text(self):
        items = context_for(self.a, "Competitive", self.home)["items"]
        self.assertEqual([i["kind"] for i in items], ["gap"])
        self.assertIn("source_ref", items[0]["text"])

    def test_businesses_never_leak_into_each_other(self):
        self._fact(self.a, "revenue_model", SECRET_A)
        self._fact(self.b, "revenue_model", SECRET_B)
        blob_a = json.dumps(context_for(self.a, "Sales", self.home))
        blob_b = json.dumps(context_for(self.b, "Sales", self.home))
        self.assertIn(SECRET_A, blob_a)
        self.assertNotIn(SECRET_B, blob_a)
        self.assertIn(SECRET_B, blob_b)
        self.assertNotIn(SECRET_A, blob_b)

    def test_contradiction_and_stale_are_surfaced_first(self):
        self._fact(self.a, "revenue_model", "monthly plans")
        self._fact(self.a, "revenue_model", "one-off licences")
        out = context_for(self.a, "Sales", self.home)
        self.assertEqual(out["items"][0]["kind"], "contradicted")
        self.assertEqual(len(out["items"][0]["provenance"]), 2)

    def test_principles_are_universal_cited_and_stamped(self):
        out = context_for(self.a, "Finance", self.home)
        pr = [i for i in out["items"] if i["kind"] == "principle"]
        self.assertTrue(pr)
        for i in pr:
            self.assertEqual(i["scope"], "universal")
            self.assertTrue(i["provenance"]["origin"]["file"])
            self.assertIn("business_round/B", i["provenance"]["stamp"])

    def test_cap_reports_what_it_cut(self):
        saved = compiler.MAX_ITEMS
        compiler.MAX_ITEMS = 3
        try:
            out = context_for(self.a, "Research", self.home)
        finally:
            compiler.MAX_ITEMS = saved
        self.assertEqual(len(out["items"]), 3)
        self.assertGreater(len(out["omitted"]), 0)

    def test_unknown_lens_is_refused_and_every_lens_compiles(self):
        with self.assertRaisesRegex(ValueError, "unknown lens"):
            context_for(self.a, "Astrology", self.home)
        for lens in compiler.lenses():
            with self.subTest(lens=lens):
                self.assertEqual(context_for(self.a, lens, self.home)["lens"], lens)

    def test_real_command_emits_the_context(self):
        env = dict(os.environ, CPP_FOUNDER_STATE_DIR=str(self.home))
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "founder_round.py"), "--repo", str(self.a),
                            "context", "--lens", "Growth"], capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["lens"], "Growth")
        bad = subprocess.run([sys.executable, str(ROOT / "tools" / "founder_round.py"), "--repo", str(self.a),
                              "context", "--lens", "Nope"], capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(bad.returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
