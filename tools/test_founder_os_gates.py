#!/usr/bin/env python3
"""V-FOUNDER-GATES: security/autonomy (G9), cross-business (G11) and fresh-agent (G12) checks.

Structural evidence only: it proves the code cannot reach the outside world and that every documented
command exists and runs. It says nothing about real business outcomes.
Run from the CPP repo root: python tools/test_founder_os_gates.py
"""
from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "founder_round.py"
GIT = None
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT))
from founder_round import initialize, start, record  # noqa: E402

FORBIDDEN_IMPORTS = {"socket", "urllib", "urllib.request", "http", "http.client", "requests", "httpx",
                     "aiohttp", "smtplib", "ftplib", "subprocess", "webbrowser", "ctypes_http"}
EXTERNAL = ("outward", "spend", "legal", "sensitive_data", "irreversible")
SOURCES = [TOOL] + sorted((ROOT / "modules" / "founder_os").glob("*.py"))


def _imports(path: Path) -> set:
    found = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


class TestSecurityAndAutonomy(unittest.TestCase):
    def test_founder_code_cannot_reach_the_network_or_spawn_processes(self):
        for path in SOURCES:
            with self.subTest(file=path.name):
                bad = {m for m in _imports(path) if m in FORBIDDEN_IMPORTS or m.split(".")[0] in FORBIDDEN_IMPORTS}
                self.assertEqual(bad, set(), f"{path.name} imports {bad}")

    @staticmethod
    def _spread_overrides(source: str) -> list:
        """Dict literals where an explicit key precedes a `**` unpack: the unpack can overwrite that key."""
        hits = []
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Dict):
                explicit: list = []
                for key in node.keys:
                    if key is None and explicit:
                        hits.append((node.lineno, list(explicit)))
                    elif isinstance(key, ast.Constant):
                        explicit.append(key.value)
        return hits

    def test_no_dict_literal_lets_a_spread_overwrite_an_earlier_explicit_key(self):
        """Incident I-2: {"status": "STALE", **row} reported STALE as OBSERVED. Spread first, explicit keys last."""
        for path in SOURCES:
            with self.subTest(file=path.name):
                self.assertEqual(self._spread_overrides(path.read_text(encoding="utf-8")), [])

    def test_the_spread_detector_can_fail(self):
        bad = 'row = {}\nx = {"status": "STALE", **row}\ny = {**row, "status": "STALE"}\n'
        self.assertEqual(self._spread_overrides(bad), [(2, ["status"])])

    def test_every_external_effect_needs_an_authorization_ref(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, state = Path(tmp) / "biz", Path(tmp) / "state"
            (repo / ".git").mkdir(parents=True)
            initialize(repo, state)
            start(repo, state)
            for effect in EXTERNAL:
                with self.subTest(effect=effect):
                    row = {"kind": "decision", "summary": "do the thing", "effect": effect}
                    with self.assertRaisesRegex(ValueError, "authorization_ref"):
                        record(repo, row, state)
                    ok = record(repo, dict(row, authorization_ref="owner-grant:2026-10-27/x"), state)
                    self.assertIn("event_id", ok)

    def test_an_authorization_string_does_not_change_any_verdict(self):
        """It is audit metadata. Journalling a spend with a grant string must not make the business look better."""
        with tempfile.TemporaryDirectory() as tmp:
            repo, state = Path(tmp) / "biz", Path(tmp) / "state"
            (repo / ".git").mkdir(parents=True)
            initialize(repo, state)
            start(repo, state)
            from founder_round import assess_business
            before = assess_business(repo, state)
            record(repo, {"kind": "execution", "summary": "ad spend", "effect": "spend",
                          "authorization_ref": "OWNER-APPROVED", "action_ref": "git:abc", "outcome_ref": "repo:o"}, state)
            self.assertEqual(assess_business(repo, state), before)


class TestCrossBusinessAndFreshAgent(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / "state"
        self.env = dict(os.environ, CPP_FOUNDER_STATE_DIR=str(self.state))
        self.git = self._find_git()

    @staticmethod
    def _find_git() -> str:
        import shutil
        return shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"

    def _repo(self, name):
        p = self.root / name
        p.mkdir()
        subprocess.run([self.git, "init", "-q", str(p)], check=True)
        return p

    def _run(self, repo, *args, cwd=None):
        r = subprocess.run([sys.executable, str(TOOL), "--repo", str(repo), *args], capture_output=True,
                           text=True, env=self.env, cwd=str(cwd or self.root), timeout=90)
        return r.returncode, r.stdout, r.stderr

    def _event(self, repo, **row):
        f = self.root / "e.json"
        base = {"kind": "observation", "effect": "internal_reversible", "evidence_class": "observed",
                "source_ref": "repo:docs/x.md#sha256:1"}
        base.update(row)
        f.write_text(json.dumps(base), encoding="utf-8")
        rc, out, err = self._run(repo, "event", "--file", str(f))
        self.assertEqual(rc, 0, err)
        return json.loads(out)["event_id"]

    def test_two_different_business_models_through_every_command(self):
        saas, shop = self._repo("saas"), self._repo("shop")
        for repo in (saas, shop):
            self.assertEqual(self._run(repo, "init")[0], 0)
            self.assertEqual(self._run(repo, "start")[0], 0)
        self._event(saas, summary="model", subject="business_model", value="seat-based subscription")
        self._event(saas, summary="segments", subject="customer_segments", value="design agencies")
        self._event(shop, summary="model", subject="business_model", value="made-to-order furniture")
        self._event(shop, summary="capacity", subject="operating_capacity", value="two workshop slots per week")
        out = {}
        for name, repo in (("saas", saas), ("shop", shop)):
            out[name] = {c: self._run(repo, *c.split())[1] for c in
                         ("kernel", "assess", "backlog", "context --lens Operations", "status")}
            for cmd, text in out[name].items():
                self.assertTrue(text.strip().startswith("{"), f"{name} {cmd} did not emit JSON")
        blob = {n: json.dumps(v) for n, v in out.items()}
        self.assertIn("seat-based subscription", blob["saas"])
        self.assertNotIn("furniture", blob["saas"])
        self.assertIn("furniture", blob["shop"])
        self.assertNotIn("seat-based", blob["shop"])
        saas_ops = json.loads(out["saas"]["assess"])["operational_readiness"]["verdict"]
        shop_ops = json.loads(out["shop"]["assess"])["operational_readiness"]["verdict"]
        self.assertEqual((saas_ops, shop_ops), ("UNKNOWN", "UNKNOWN"))
        self.assertNotEqual(out["saas"]["kernel"], out["shop"]["kernel"])
        # closing: a proof from the other business is refused, the own one accepted
        foreign = self._event(saas, summary="more", subject="stage", value="early revenue")
        self.assertEqual(self._run(shop, "close", "--outcome", "UNCERTAINTY_REDUCED", "--proof", foreign)[0], 2)
        self.assertEqual(self._run(saas, "close", "--outcome", "UNCERTAINTY_REDUCED", "--proof", foreign)[0], 0)

    def test_fresh_agent_can_use_only_the_documented_commands_from_a_foreign_cwd(self):
        docs = (ROOT / "commands" / "cpp-founder-round.md").read_text(encoding="utf-8")
        documented = set(re.findall(r"founder_round\.py\"? --repo \. ([a-z]+)", docs))
        documented |= {"kernel", "assess", "backlog", "context", "init", "start", "status", "recover", "event", "close"}
        helptext = subprocess.run([sys.executable, str(TOOL), "--help"], capture_output=True, text=True,
                                  timeout=60).stdout
        for cmd in sorted(documented):
            with self.subTest(command=cmd):
                self.assertIn(cmd, helptext, f"documented command {cmd!r} is not offered by the CLI")
        repo = self._repo("fresh")
        foreign = self.root / "elsewhere"
        foreign.mkdir()
        self.assertEqual(self._run(repo, "init", cwd=foreign)[0], 0)
        self.assertEqual(self._run(repo, "start", cwd=foreign)[0], 0)
        rc, out, _ = self._run(repo, "kernel", cwd=foreign)
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out)["plan"][0]["action"], "discover")

    def test_every_path_the_resumption_file_names_exists(self):
        text = (ROOT / "RESUMPTION_FILE.founder-os.md").read_text(encoding="utf-8")
        paths = set(re.findall(r"`((?:tools|modules|vault|commands)/[A-Za-z0-9_./-]+\.(?:py|md|json))`", text))
        self.assertGreater(len(paths), 5)
        missing = sorted(p for p in paths if not (ROOT / p).exists())
        self.assertEqual(missing, [], f"RESUMPTION_FILE.founder-os.md names files that do not exist: {missing}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
