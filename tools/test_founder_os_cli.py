#!/usr/bin/env python3
"""V-FOUNDER-CLI: drives the real command entry point as a subprocess on real git repos.

The unit suites call the functions; the command a user runs is `python tools/founder_round.py`.
This crosses that boundary with two independent businesses, a nested working directory and the
exit-code contract (0 ok, 2 refused). Run from the CPP repo root.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parent / "founder_round.py"
GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"


class TestFounderCli(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / "state"
        self.env = dict(os.environ, CPP_FOUNDER_STATE_DIR=str(self.state))
        self.saas = self._repo("SaasCo")
        self.shop = self._repo("ShopCo")

    def _repo(self, name: str) -> Path:
        p = self.root / name
        p.mkdir()
        subprocess.run([GIT, "init", "-q", str(p)], check=True)
        return p

    def _run(self, repo: Path, *args: str, cwd: Path | None = None):
        proc = subprocess.run([sys.executable, str(TOOL), "--repo", str(repo), *args],
                              capture_output=True, text=True, env=self.env,
                              cwd=str(cwd or repo), timeout=60)
        return proc.returncode, proc.stdout, proc.stderr

    def _event(self, repo: Path, row: dict):
        f = self.root / "event.json"
        f.write_text(json.dumps(row), encoding="utf-8")
        return self._run(repo, "event", "--file", str(f))

    def test_two_businesses_full_cycle_through_the_command(self):
        for repo in (self.saas, self.shop):
            self.assertEqual(self._run(repo, "init")[0], 0)
            self.assertEqual(self._run(repo, "start")[0], 0)
        rc, out, err = self._event(self.saas, {
            "kind": "observation", "summary": "trial to paid conversion read from export",
            "effect": "internal_reversible", "source_ref": "repo:exports/funnel.csv#sha256:9",
            "evidence_class": "observed"})
        self.assertEqual(rc, 0, err)
        saas_event = json.loads(out)["event_id"]
        # the other business sees none of it
        shop_status = json.loads(self._run(self.shop, "status")[1])
        self.assertEqual(shop_status["events"], 1)  # only its own round_open
        # a nested directory is the same business
        nested = self.saas / "app" / "deep"
        nested.mkdir(parents=True)
        nested_status = json.loads(self._run(self.saas, "status", cwd=nested)[1])
        self.assertEqual(nested_status["events"], 2)
        # a closing claim may cite only its own business's events
        rc, _, err = self._run(self.shop, "close", "--outcome", "UNCERTAINTY_REDUCED",
                               "--proof", saas_event)
        self.assertEqual(rc, 2)
        self.assertIn("BLOCKED", err)
        rc, out, err = self._run(self.saas, "close", "--outcome", "UNCERTAINTY_REDUCED",
                                 "--proof", saas_event)
        self.assertEqual(rc, 0, err)
        self.assertEqual(json.loads(self._run(self.saas, "status")[1])["last_outcome"],
                         "UNCERTAINTY_REDUCED")

    def test_refusals_exit_2_and_write_nothing(self):
        self._run(self.saas, "init")
        self._run(self.saas, "start")
        before = json.loads(self._run(self.saas, "status")[1])["events"]
        rc, _, err = self._event(self.saas, {
            "kind": "observation", "summary": "refund for jane.doe@example.com",
            "effect": "internal_reversible", "source_ref": "repo:x", "evidence_class": "observed"})
        self.assertEqual(rc, 2)
        self.assertIn("personal or secret data", err)
        self.assertEqual(json.loads(self._run(self.saas, "status")[1])["events"], before)

    def test_uninitialized_repo_is_refused(self):
        rc, _, err = self._run(self.shop, "status")
        self.assertEqual(rc, 2)
        self.assertIn("uninitialized", err)

    def test_recover_through_the_command(self):
        self._run(self.saas, "init")
        self._run(self.saas, "start")
        key_dir = next(self.state.iterdir())
        with (key_dir / "events.jsonl").open("ab") as f:
            f.write(b'{"seq": 2, "ki')
        self.assertEqual(self._run(self.saas, "status")[0], 2)
        rc, out, err = self._run(self.saas, "recover")
        self.assertEqual(rc, 0, err)
        self.assertGreater(json.loads(out)["quarantined_bytes"], 0)
        self.assertEqual(self._run(self.saas, "status")[0], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
