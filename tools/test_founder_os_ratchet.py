#!/usr/bin/env python3
"""V-FOUNDER-RATCHET: a business-round baseline is inherited by a fresh prompt through the real hook path.

Reuses the live family-baseline machinery (no parallel ratchet). Poles are the ones predeclared in
vault/audits/ucr_cif/19_BUSINESS_ROUND_FAMILY_PREDECLARATION.md before the family file existed.
Hermetic: HOME points at a temp dir so offer counters and the consumption ledger stay out of ~/.claude.
Run from the CPP repo root: python tools/test_founder_os_ratchet.py
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

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from modules.gsd_x import cli  # noqa: E402
from modules.tower import baselines as bl, families as fm  # noqa: E402

FAMILY = "business_round"
IN_ES = ("haz una ronda de negocio en este repositorio: encuentra el cuello de botella del embudo "
         "de ventas y propone un experimento")
IN_EN = "run a founder round on this repo: find the business bottleneck and propose one experiment"
IN_CMD = "mejorar el negocio de este repositorio con /cpp-founder-round"
OUT = ("arregla el crash del escritor de level.dat en la Wii",
       "añade una tabla de suscripciones con su migración al backend de InfinityOps",
       "hazme una landing para un restaurante con reservas online")
HARD_LANDING = "haz una landing que explique el modelo de negocio de nuestro SaaS"
HARD_MIXED = "haz una ronda de negocio y de paso arregla el crash del escritor de level.dat"
NONE_PROMPT = "qué hora es"
PRIVATE_NAMES = ("QuickLease", "CostaLuz", "KobiCraft", "KobiiCraft", "CommonWealth", "InfinityOps")


def _ids(prompt: str) -> set:
    return {fid for fid, _ in fm.classify_prompt(prompt)}


class TestBusinessRoundFamily(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="fo-ratchet-")
        self.addCleanup(shutil.rmtree, self.home, True)
        self.env = dict(os.environ, HOME=self.home, USERPROFILE=self.home, PYTHONIOENCODING="utf-8")
        self.env.pop(cli.FAMILY_SWITCH, None)
        self._saved = {k: os.environ.get(k) for k in ("HOME", "USERPROFILE", cli.FAMILY_SWITCH)}
        os.environ.update(HOME=self.home, USERPROFILE=self.home)
        os.environ.pop(cli.FAMILY_SWITCH, None)
        # Promoted entries cite repo-relative files, so origin checks need the repo root as cwd.
        self._cwd = os.getcwd()
        os.chdir(ROOT)
        self.addCleanup(os.chdir, self._cwd)
        self.addCleanup(self._restore)

    def _restore(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _spawn(self, argv, prompt):
        r = subprocess.run(argv, input=json.dumps({"prompt": prompt, "session_id": ""}),
                           capture_output=True, text=True, encoding="utf-8", env=self.env,
                           cwd=str(ROOT), timeout=60)
        return r.returncode, r.stdout

    def _header(self):
        return "Family baseline %s/B%d " % (FAMILY, bl.generations(FAMILY)[-1])

    # --- the classifier, both poles ---------------------------------------------------------
    def test_predeclared_poles(self):
        for p in (IN_ES, IN_EN, IN_CMD, HARD_MIXED):
            with self.subTest(inside=p):
                self.assertIn(FAMILY, _ids(p))
        for p in OUT + (HARD_LANDING, NONE_PROMPT):
            with self.subTest(outside=p):
                self.assertNotIn(FAMILY, _ids(p))

    def test_hard_case_builds_a_web_page_not_a_business_round(self):
        self.assertIn("web_surface", _ids("hazme una landing para un restaurante con reservas online"))
        self.assertEqual(fm.classify_prompt(NONE_PROMPT), [])

    # --- B0 is sealed doctrine, privacy-safe and verifiable -------------------------------
    def test_b0_is_cited_verified_and_carries_no_private_business_data(self):
        entries = bl.active_entries(FAMILY)
        self.assertGreaterEqual(len(entries), 4)
        for e in entries:
            with self.subTest(entry=e["id"]):
                self.assertEqual(bl.verify_origin(e, window=0), bl.VERIFIED)
        blob = json.dumps([bl.load_generation(FAMILY, n) for n in bl.generations(FAMILY)],
                          ensure_ascii=False)
        for name in PRIVATE_NAMES:
            self.assertNotIn(name, blob)

    # --- the first improvement born in this mission reaches a fresh prompt ----------------
    def test_mission_derived_entry_is_promoted_and_reaches_a_fresh_prompt(self):
        entry_id = "business_round-journal-refuses-customer-data"
        active = {e["id"]: e for e in bl.active_entries(FAMILY)}
        self.assertIn(entry_id, active)
        self.assertEqual(active[entry_id]["status"], "auto")
        self.assertIn(entry_id, cli.family_block(IN_EN, {}))
        self.assertNotIn(entry_id, cli.family_block(HARD_LANDING, {}))
        # The baseline's claim is true of the code it cites: the journal really refuses.
        sys.path.insert(0, str(ROOT / "tools"))
        from founder_round import initialize, record, start
        with tempfile.TemporaryDirectory() as tmp:
            repo, state = Path(tmp) / "biz", Path(tmp) / "state"
            (repo / ".git").mkdir(parents=True)
            initialize(repo, state)
            start(repo, state)
            with self.assertRaisesRegex(ValueError, "personal or secret data"):
                record(repo, {"kind": "observation", "summary": "refund to jane.doe@example.com",
                              "effect": "internal_reversible", "source_ref": "repo:x",
                              "evidence_class": "observed"}, state)

    # --- G14: the Owner can undo the automatic promotion, and ordinary build work is not burdened ---
    def test_owner_can_revert_the_auto_entry_and_the_chain_still_verifies(self):
        from modules.tower import ratchet
        entry_id = "business_round-journal-refuses-customer-data"
        before = bl.generation_sha256(FAMILY, 1)
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "baselines")
            shutil.copytree(bl.BASELINES_DIR, root)
            ratchet.revert(FAMILY, entry_id, "owner review test", "owner-test", root=root)
            ids = {e["id"] for e in bl.active_entries(FAMILY, root)}
            self.assertNotIn(entry_id, ids)
            self.assertIn("business_round-claim-needs-a-fact", ids)
            self.assertEqual(bl.generations(FAMILY, root), [0, 1, 2])
            self.assertEqual(bl.generation_sha256(FAMILY, 1, root), before)
            self.assertEqual(ratchet.verify_chain(FAMILY, root).generations, [0, 1, 2])
            with self.assertRaises(ratchet.RatchetRefusal):
                ratchet.revert(FAMILY, entry_id, "again", "owner-test", root=root)
        self.assertIn(entry_id, {e["id"] for e in bl.active_entries(FAMILY)})

    def test_ordinary_build_prompts_get_no_business_baseline(self):
        for prompt in ("implementa un parser de CSV en python con tests",
                       "add a retry with backoff to the upload client",
                       "refactoriza el módulo de logging para usar structlog",
                       "write a README section explaining the install steps"):
            with self.subTest(prompt=prompt):
                self.assertNotIn(self._header(), cli.family_block(prompt, {}))
                self.assertNotIn(FAMILY, _ids(prompt))

    def test_generation_chain_verifies(self):
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "family_baseline.py"), "verify", FAMILY],
                           capture_output=True, text=True, cwd=str(ROOT), timeout=60)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    # --- a fresh agent inherits it by execution, not by reading docs ----------------------
    def test_fresh_prompt_receives_the_baseline_and_an_outsider_does_not(self):
        got = cli.family_block(IN_ES, {})
        self.assertIn(self._header(), got)
        self.assertIn("business_round-claim-needs-a-fact", got)
        self.assertNotIn(self._header(), cli.family_block(HARD_LANDING, {}))
        self.assertEqual(cli.family_block(NONE_PROMPT, {}), "")

    def test_kill_switch_with_its_own_control(self):
        self.assertNotEqual(cli.family_block(IN_ES, {}), "")
        os.environ[cli.FAMILY_SWITCH] = "off"
        try:
            self.assertEqual(cli.family_block(IN_ES, {}), "")
        finally:
            del os.environ[cli.FAMILY_SWITCH]

    def test_real_process_and_real_hook_deliver_it(self):
        cli_path = str(ROOT / "modules" / "gsd_x" / "cli.py")
        rc, out = self._spawn([sys.executable, cli_path], IN_EN)
        self.assertEqual(rc, 0)
        self.assertIn(self._header(), out)
        rc, out = self._spawn([sys.executable, cli_path], NONE_PROMPT)
        self.assertEqual(rc, 0)
        self.assertNotIn("Family baseline", out)
        node = shutil.which("node")
        if not node:
            self.fail("node not on PATH: the hook plane was NOT exercised")
        rc, out = self._spawn([node, str(ROOT / "hooks" / "gsd_x_tier.js")], IN_EN)
        self.assertEqual(rc, 0)
        self.assertIn(self._header(), out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
