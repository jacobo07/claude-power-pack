"""tests/test_forensic_probes.py — MC-OVO-102

Real-fixture tests for the 3 forensic probes (RLP, AFHL, CGAR).
No mocks: every test writes a real probe artifact to a tmpdir, runs the
probe, and asserts on the actual ProbeResult.

Run:
    python -m unittest tests.test_forensic_probes -v
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

# Make tools/ importable.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import forensic_probes as fp  # noqa: E402


def _project(tmpdir: Path) -> Path:
    """Bare project root with empty audit cache + vault dirs."""
    (tmpdir / "_audit_cache").mkdir(parents=True, exist_ok=True)
    (tmpdir / "vault" / "anti_fragility").mkdir(parents=True, exist_ok=True)
    (tmpdir / "vault" / "audits").mkdir(parents=True, exist_ok=True)
    return tmpdir


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# RLP
# ---------------------------------------------------------------------------

class TestRLP(unittest.TestCase):
    def test_not_configured_when_file_missing(self):
        with tempfile.TemporaryDirectory() as td:
            project = _project(Path(td))
            r = fp.rlp_check(project)
            self.assertEqual(r.state, fp.STATE_NOT_CONFIGURED)
            self.assertEqual(r.verdict_cap, "none")
            self.assertIn("runtime_probe.jsonl", r.advisory)

    def test_not_configured_when_file_empty(self):
        with tempfile.TemporaryDirectory() as td:
            project = _project(Path(td))
            (project / "_audit_cache" / "runtime_probe.jsonl").write_text(
                "", encoding="utf-8"
            )
            r = fp.rlp_check(project)
            self.assertEqual(r.state, fp.STATE_NOT_CONFIGURED)

    def test_configured_clean_under_higher_is_better(self):
        with tempfile.TemporaryDirectory() as td:
            project = _project(Path(td))
            samples = [
                {"iso_ts": "t", "probe_id": "srv", "metric": "tps",
                 "value": 19.8, "baseline": 20.0, "unit": "tps",
                 "sample_window_s": 10}
                for _ in range(5)
            ]
            _write_jsonl(project / "_audit_cache" / "runtime_probe.jsonl", samples)
            r = fp.rlp_check(project)
            self.assertEqual(r.state, fp.STATE_CONFIGURED)
            self.assertEqual(r.verdict_cap, "none")
            self.assertEqual(r.findings, [])

    def test_configured_b_at_50pct_degradation(self):
        with tempfile.TemporaryDirectory() as td:
            project = _project(Path(td))
            samples = [
                {"iso_ts": "t", "probe_id": "srv", "metric": "tps",
                 "value": 8.0, "baseline": 20.0, "unit": "tps",
                 "sample_window_s": 10}
            ]
            _write_jsonl(project / "_audit_cache" / "runtime_probe.jsonl", samples)
            r = fp.rlp_check(project)
            self.assertEqual(r.state, fp.STATE_CONFIGURED)
            self.assertEqual(r.verdict_cap, "B")
            self.assertTrue(any("srv:tps B" in f for f in r.findings))

    def test_configured_reject_at_90pct_degradation(self):
        with tempfile.TemporaryDirectory() as td:
            project = _project(Path(td))
            samples = [
                {"iso_ts": "t", "probe_id": "srv", "metric": "tps",
                 "value": 1.0, "baseline": 20.0, "unit": "tps",
                 "sample_window_s": 10}
            ]
            _write_jsonl(project / "_audit_cache" / "runtime_probe.jsonl", samples)
            r = fp.rlp_check(project)
            self.assertEqual(r.verdict_cap, "REJECT")

    def test_lower_is_better_metric_inverts_correctly(self):
        # p99_ms baseline=50 → value=200 means 4x worse → REJECT (ratio 0.25 < 0.5 inverted)
        with tempfile.TemporaryDirectory() as td:
            project = _project(Path(td))
            samples = [
                {"iso_ts": "t", "probe_id": "srv", "metric": "p99_ms",
                 "value": 600.0, "baseline": 50.0, "unit": "ms",
                 "sample_window_s": 10}
            ]
            _write_jsonl(project / "_audit_cache" / "runtime_probe.jsonl", samples)
            r = fp.rlp_check(project)
            self.assertEqual(r.verdict_cap, "REJECT")  # 50/600 = 0.083 < 0.10

    def test_sustained_degradation_caps_b(self):
        # 10 consecutive samples in WARN band (none individually B) → sustained B
        with tempfile.TemporaryDirectory() as td:
            project = _project(Path(td))
            samples = [
                {"iso_ts": f"t{i}", "probe_id": "srv", "metric": "tps",
                 "value": 14.0, "baseline": 20.0, "unit": "tps",
                 "sample_window_s": 10}
                for i in range(10)
            ]  # ratio 0.7 → warn band, not individually B
            _write_jsonl(project / "_audit_cache" / "runtime_probe.jsonl", samples)
            r = fp.rlp_check(project)
            self.assertEqual(r.verdict_cap, "B")
            self.assertTrue(any("sustained degradation" in f for f in r.findings))

    def test_malformed_sample_is_finding(self):
        with tempfile.TemporaryDirectory() as td:
            project = _project(Path(td))
            (project / "_audit_cache" / "runtime_probe.jsonl").write_text(
                'this is not json\n{"valid": false}\n', encoding="utf-8"
            )
            r = fp.rlp_check(project)
            # Either finding is fine (malformed line OR missing required fields).
            self.assertEqual(r.verdict_cap, "B")


# ---------------------------------------------------------------------------
# AFHL
# ---------------------------------------------------------------------------

class TestAFHL(unittest.TestCase):
    def test_not_configured_when_file_missing(self):
        with tempfile.TemporaryDirectory() as td:
            project = _project(Path(td))
            (project / "vault" / "anti_fragility").mkdir(parents=True, exist_ok=True)
            # No file written.
            r = fp.afhl_check(project, [])
            self.assertEqual(r.state, fp.STATE_NOT_CONFIGURED)

    def test_configured_clean_when_delta_does_not_touch_hacks(self):
        with tempfile.TemporaryDirectory() as td:
            project = _project(Path(td))
            entries = [
                {"_schema": "afhl-v1"},
                {
                    "hack_id": "x",
                    "added": "2026-04-01",
                    "file": "src/hack.js",
                    "upstream": "x",
                    "upstream_version_range": "[1.0,2.0)",
                    "upstream_bug_url": "http://example.com",
                    "reason": "x",
                    "validates_via": "tests/x.test.js",
                },
            ]
            _write_jsonl(project / "vault" / "anti_fragility" / "hacks.jsonl",
                         entries)
            r = fp.afhl_check(project, ["lib/other.js"])
            self.assertEqual(r.state, fp.STATE_CONFIGURED)
            self.assertEqual(r.verdict_cap, "none")
            self.assertEqual(r.findings, [])

    def test_configured_b_when_delta_touches_a_hack(self):
        with tempfile.TemporaryDirectory() as td:
            project = _project(Path(td))
            entries = [{
                "hack_id": "nms-pose",
                "added": "2026-03-15",
                "file": "src/main/java/com/kobii/util/NMSPose.java",
                "upstream": "papermc/Paper",
                "upstream_version_range": "[1.21.0, 1.21.4)",
                "upstream_bug_url": "https://github.com/PaperMC/Paper/issues/12345",
                "reason": "Reflection accessor",
                "validates_via": "tests/integration/PoseRegressionTest.java",
            }]
            _write_jsonl(project / "vault" / "anti_fragility" / "hacks.jsonl",
                         entries)
            r = fp.afhl_check(project, [
                "src/main/java/com/kobii/util/NMSPose.java",
                "src/other.java",
            ])
            self.assertEqual(r.state, fp.STATE_CONFIGURED)
            self.assertEqual(r.verdict_cap, "B")
            self.assertTrue(any("nms-pose" in f for f in r.findings))
            self.assertTrue(any("NEVER" in f for f in r.findings))  # never revalidated

    def test_missing_required_fields_is_finding(self):
        with tempfile.TemporaryDirectory() as td:
            project = _project(Path(td))
            entries = [{"hack_id": "incomplete"}]  # missing many fields
            _write_jsonl(project / "vault" / "anti_fragility" / "hacks.jsonl",
                         entries)
            r = fp.afhl_check(project, [])
            self.assertEqual(r.verdict_cap, "B")
            self.assertTrue(any("missing fields" in f for f in r.findings))

    def test_path_separator_normalization(self):
        # Hack file uses forward slashes; delta uses Windows backslashes.
        with tempfile.TemporaryDirectory() as td:
            project = _project(Path(td))
            entries = [{
                "hack_id": "x", "added": "t", "file": "lib/hack.js",
                "upstream": "x", "upstream_version_range": "[1.0,2.0)",
                "upstream_bug_url": "u", "reason": "r", "validates_via": "t",
            }]
            _write_jsonl(project / "vault" / "anti_fragility" / "hacks.jsonl",
                         entries)
            r = fp.afhl_check(project, ["lib\\hack.js"])
            self.assertEqual(r.verdict_cap, "B")


# ---------------------------------------------------------------------------
# CGAR
# ---------------------------------------------------------------------------

class TestCGAR(unittest.TestCase):
    def test_not_configured_when_file_missing(self):
        with tempfile.TemporaryDirectory() as td:
            project = _project(Path(td))
            r = fp.cgar_check(project, [])
            self.assertEqual(r.state, fp.STATE_NOT_CONFIGURED)

    def test_not_configured_with_v1_empty_placeholder(self):
        with tempfile.TemporaryDirectory() as td:
            project = _project(Path(td))
            (project / "vault" / "audits" / "cascade_graph.json").write_text(
                json.dumps({
                    "schema": "ovo-cascade-graph-v1",
                    "classes": [], "event_to_listeners": {},
                    "event_to_publishers": {},
                }), encoding="utf-8")
            r = fp.cgar_check(project, ["any/file.py"])
            self.assertEqual(r.state, fp.STATE_NOT_CONFIGURED)
            self.assertEqual(r.verdict_cap, "none")

    def test_configured_clean_when_delta_misses_all_nodes(self):
        with tempfile.TemporaryDirectory() as td:
            project = _project(Path(td))
            graph = {
                "schema": "ovo-cascade-graph-v2",
                "nodes": [{
                    "id": "src/hot.py", "kind": "module",
                    "criticality": "core",
                    "blast_radius": {"transitive_callers": 100,
                                     "downstream_systems": ["X"]},
                }],
            }
            (project / "vault" / "audits" / "cascade_graph.json").write_text(
                json.dumps(graph), encoding="utf-8")
            r = fp.cgar_check(project, ["docs/readme.md"])
            self.assertEqual(r.state, fp.STATE_CONFIGURED)
            self.assertEqual(r.verdict_cap, "none")

    def test_configured_b_when_delta_touches_core_node(self):
        with tempfile.TemporaryDirectory() as td:
            project = _project(Path(td))
            graph = {
                "schema": "ovo-cascade-graph-v2",
                "nodes": [{
                    "id": "src/auth.py", "kind": "module",
                    "criticality": "core",
                    "blast_radius": {"transitive_callers": 8,
                                     "downstream_systems": ["api", "worker"]},
                }],
            }
            (project / "vault" / "audits" / "cascade_graph.json").write_text(
                json.dumps(graph), encoding="utf-8")
            r = fp.cgar_check(project, ["src/auth.py"])
            self.assertEqual(r.verdict_cap, "B")
            self.assertTrue(any("criticality=core" in f for f in r.findings))

    def test_configured_b_when_delta_touches_high_blast_radius(self):
        with tempfile.TemporaryDirectory() as td:
            project = _project(Path(td))
            graph = {
                "schema": "ovo-cascade-graph-v2",
                "nodes": [{
                    "id": "lib/util.js", "kind": "module",
                    "blast_radius": {"transitive_callers": 200,
                                     "downstream_systems": []},
                }],
            }
            (project / "vault" / "audits" / "cascade_graph.json").write_text(
                json.dumps(graph), encoding="utf-8")
            r = fp.cgar_check(project, ["lib/util.js"])
            self.assertEqual(r.verdict_cap, "B")
            self.assertTrue(any("transitive_callers=200" in f for f in r.findings))

    def test_configured_reject_when_delta_touches_migration(self):
        with tempfile.TemporaryDirectory() as td:
            project = _project(Path(td))
            graph = {
                "schema": "ovo-cascade-graph-v2",
                "nodes": [{
                    "id": "migrations/2026_drop_users.sql",
                    "kind": "migration",
                    "blast_radius": {"transitive_callers": 0,
                                     "downstream_systems": []},
                }],
            }
            (project / "vault" / "audits" / "cascade_graph.json").write_text(
                json.dumps(graph), encoding="utf-8")
            r = fp.cgar_check(project, ["migrations/2026_drop_users.sql"])
            self.assertEqual(r.verdict_cap, "REJECT")

    def test_malformed_graph_is_b(self):
        with tempfile.TemporaryDirectory() as td:
            project = _project(Path(td))
            (project / "vault" / "audits" / "cascade_graph.json").write_text(
                "{not valid json", encoding="utf-8")
            r = fp.cgar_check(project, [])
            self.assertEqual(r.verdict_cap, "B")
            self.assertTrue(any("malformed" in f for f in r.findings))


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

class TestAggregate(unittest.TestCase):
    def test_overall_cap_is_max_of_probes(self):
        results = [
            fp.ProbeResult(probe="rlp", state=fp.STATE_CONFIGURED, verdict_cap="none"),
            fp.ProbeResult(probe="afhl", state=fp.STATE_CONFIGURED, verdict_cap="B",
                          findings=["x"]),
            fp.ProbeResult(probe="cgar", state=fp.STATE_NOT_CONFIGURED, verdict_cap="none"),
        ]
        bundle = fp.aggregate(results)
        self.assertEqual(bundle["overall_verdict_cap"], "B")
        self.assertEqual(len(bundle["probes"]), 3)

    def test_reject_beats_b(self):
        results = [
            fp.ProbeResult(probe="rlp", state=fp.STATE_CONFIGURED, verdict_cap="REJECT"),
            fp.ProbeResult(probe="afhl", state=fp.STATE_CONFIGURED, verdict_cap="B"),
        ]
        self.assertEqual(fp.aggregate(results)["overall_verdict_cap"], "REJECT")


if __name__ == "__main__":
    unittest.main()
