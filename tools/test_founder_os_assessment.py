#!/usr/bin/env python3
"""V-FOUNDER-ASSESS: five separate verdicts; a projection or a simulation never validates a business.
Run from the CPP repo root: python tools/test_founder_os_assessment.py
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
from founder_round import initialize, start, record, assess_business  # noqa: E402


class TestAssessment(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / "state"
        self.a = Path(self.temp.name) / "a"
        (self.a / ".git").mkdir(parents=True)
        initialize(self.a, self.home)
        start(self.a, self.home)

    def _f(self, subject, cls="observed", value="x"):
        return record(self.a, {"kind": "observation", "summary": f"{subject} noted",
                               "effect": "internal_reversible", "source_ref": f"repo:docs/{subject}.md#sha256:1",
                               "evidence_class": cls, "subject": subject, "value": value}, self.home)

    def _v(self, name):
        return assess_business(self.a, self.home)[name]["verdict"]

    def test_empty_business_is_unknown_everywhere_and_names_what_is_missing(self):
        out = assess_business(self.a, self.home)
        for name in ("economic_viability", "demand_validation", "operational_readiness", "growth_readiness"):
            self.assertEqual(out[name]["verdict"], "UNKNOWN", name)
        self.assertIn("costs", out["economic_viability"]["why"])

    def test_simulated_demand_is_unproven_never_supported(self):
        self._f("customer_segments", "simulated")
        self._f("funnel", "simulated")
        self.assertEqual(self._v("demand_validation"), "UNPROVEN")

    def test_a_projected_profit_does_not_validate_the_economics(self):
        for s in ("revenue_model", "costs", "margins"):
            self._f(s, "hypothesis")
        self.assertEqual(self._v("economic_viability"), "UNPROVEN")

    def test_dimensions_are_independent_sales_without_margins(self):
        self._f("customer_segments")
        self._f("funnel", "verified")
        self.assertEqual(self._v("demand_validation"), "SUPPORTED")
        self.assertEqual(self._v("economic_viability"), "UNKNOWN")
        self.assertEqual(self._v("operational_readiness"), "UNKNOWN")

    def test_profitable_but_unready_cannot_be_growth_ready(self):
        for s in ("revenue_model", "costs", "margins", "customer_segments", "funnel", "metrics", "objectives"):
            self._f(s, "verified")
        out = assess_business(self.a, self.home)
        self.assertEqual(out["economic_viability"]["verdict"], "SUPPORTED")
        self.assertEqual(out["demand_validation"]["verdict"], "SUPPORTED")
        self.assertEqual(out["growth_readiness"]["verdict"], "UNKNOWN")
        self.assertEqual(out["growth_readiness"]["limited_by"], "operational_readiness")

    def test_all_prerequisites_supported_lets_growth_be_supported(self):
        for s in ("revenue_model", "costs", "margins", "customer_segments", "funnel", "operating_capacity",
                  "constraints", "metrics", "objectives"):
            self._f(s, "verified")
        out = assess_business(self.a, self.home)
        self.assertEqual(out["growth_readiness"]["verdict"], "SUPPORTED")
        self.assertIsNone(out["growth_readiness"]["limited_by"])

    def test_contradiction_dominates_and_is_not_averaged_away(self):
        self._f("margins", value="thin")
        self._f("margins", value="fat")
        self._f("revenue_model")
        self._f("costs")
        self.assertEqual(self._v("economic_viability"), "CONTRADICTED")

    def test_confidence_is_a_named_breakdown_not_a_number(self):
        self._f("funnel", "verified")
        self._f("stage", "inferred")
        conf = assess_business(self.a, self.home)["evidence_confidence"]
        self.assertIn("funnel", conf["breakdown"]["verified"])
        self.assertIn("stage", conf["breakdown"]["weaker"])
        self.assertNotIn("score", json.dumps(conf).replace("deliberately not a ratio or a score", ""))

    def test_real_command(self):
        env = dict(os.environ, CPP_FOUNDER_STATE_DIR=str(self.home))
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "founder_round.py"), "--repo", str(self.a),
                            "assess"], capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["economic_viability"]["verdict"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main(verbosity=2)
