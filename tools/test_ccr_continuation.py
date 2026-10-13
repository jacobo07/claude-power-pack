"""V-CCRCONT gates for tools/ccr_continuation.py. Run: python -m unittest tools.test_ccr_continuation"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ccr_continuation as cc  # noqa: E402


def _repo(d: Path) -> Path:
    subprocess.run([cc.GIT, "init", "-q", str(d)], check=True)
    (d / "a.txt").write_text("x")
    subprocess.run([cc.GIT, "-C", str(d), "add", "."], check=True)
    subprocess.run([cc.GIT, "-C", str(d), "-c", "user.name=t", "-c", "user.email=t@t",
                    "commit", "-qm", "i"], check=True)
    return d


def _transcript(p: Path, turns: int) -> Path:
    with open(p, "w", encoding="utf-8") as f:
        for i in range(turns):
            f.write(json.dumps({"type": "user", "message": {"content": "q%d " % i + "z" * 400}}) + "\n")
            f.write(json.dumps({"type": "assistant", "message": {
                "content": [{"type": "text", "text": "answer %d " % i + "w" * 300}]}}) + "\n")
        f.write(json.dumps({"type": "assistant", "message": {
            "content": [{"type": "text", "text": "final state: tests green"}]}}) + "\n")
    return p


class T(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.d = Path(self.td.name)
        self.repo = _repo(self.d / "repo")
        self.rc = self.d / "r.md"
        self.rc.write_text("# R\nStatus: DONE\nbody noise\nVerdicts: ok\n")

    def tearDown(self):
        self.td.cleanup()

    def test_V_CCRCONT_01_flat_under_history_doubling(self):
        sizes = {}
        for k, h in (("H", 50), ("2H", 100), ("4H", 200), ("8H", 400)):
            t = _transcript(self.d / f"t{k}.jsonl", h)
            sizes[k] = len(cc.build(self.repo, "next", [self.rc], t).encode())
        for k, v in sizes.items():
            self.assertLessEqual(v, sizes["H"] * 1.05, (k, sizes))

    def test_V_CCRCONT_02_over_budget_receipts_become_refs(self):
        big = self.d / "big.md"
        big.write_text("# B\n" + "".join(f"Status: fact {i} " + "x" * 200 + "\n" for i in range(200)))
        out = cc.build(self.repo, "next", [big, self.rc])
        self.assertIn("REF receipt:", out)
        self.assertIn(cc.sha256_file(big), out)
        self.assertNotIn("fact 0 ", out)           # not partially inlined
        self.assertIn("Status: DONE", out)          # small one still inline
        self.assertTrue(cc.check_budget(out))

    def test_V_CCRCONT_03_capsule_over_budget_fails_gate(self):
        self.assertFalse(cc.check_budget("x" * (cc.budget_chars() + 1)))
        f = self.d / "c.txt"
        f.write_text("x" * (cc.budget_chars() + 1))
        self.assertEqual(cc.main(["rent", "--capsule", str(f)]), 1)
        with self.assertRaises(ValueError):
            cc.build(self.repo, "o" * (cc.budget_chars() + 10))

    def test_V_CCRCONT_04_long_note_is_ref_and_labelled_claim(self):
        t = self.d / "long.jsonl"
        t.write_text(json.dumps({"type": "assistant", "message": {
            "content": [{"type": "text", "text": "y" * 5000}]}}) + "\n")
        out = cc.build(self.repo, "n", [], t)
        self.assertIn("REF predecessor note (CLAIM", out)
        self.assertNotIn("yyyy", out)
        out2 = cc.build(self.repo, "n", [], _transcript(self.d / "s.jsonl", 3))
        self.assertIn("(CLAIM, unverified): final state", out2)

    def test_V_CCRCONT_05_dirty_names_capped(self):
        for i in range(55):
            (self.repo / f"u{i}.txt").write_text("1")
        names, more = cc.dirty_paths(self.repo)
        self.assertEqual((len(names), more), (40, 15))

    def test_V_CCRCONT_06_rent_calibration(self):
        self.assertEqual(cc.est_tokens(1000), 585)

    def test_V_CCRCONT_07_one_read_invalidation(self):
        # A4 benchmark: a certified fact keyed by its source fingerprint is reused without a re-read; changing the
        # source invalidates it; a raw read (a rebuilt capsule) makes the fact valid again.
        big = self.d / "big.md"
        big.write_text("# B\n" + "".join(f"Status: fact {i} " + "x" * 200 + "\n" for i in range(200)))
        cap = cc.build(self.repo, "next", [self.rc, big])
        fp = cc.fingerprints(cap)
        self.assertEqual(fp[self.rc.as_posix()], cc.sha256_file(self.rc))   # inlined fact block is fingerprinted
        self.assertEqual(fp[big.as_posix()], cc.sha256_file(big))           # and so is a ref
        self.assertTrue(cc.reuse(cap, self.rc)["reuse"])
        self.assertTrue(cc.reuse(cap, big)["reuse"])
        self.rc.write_text("# R\nStatus: FAILED\nVerdicts: regressed\n")
        r = cc.reuse(cap, self.rc)
        self.assertFalse(r["reuse"])
        self.assertIn("raw read required", r["reason"])
        self.assertTrue(cc.reuse(cap, big)["reuse"])                        # an untouched source stays valid
        cap2 = cc.build(self.repo, "next", [self.rc, big])
        self.assertTrue(cc.reuse(cap2, self.rc)["reuse"])
        self.assertIn("Status: FAILED", cap2)
        self.assertEqual(cc.reuse(cap2, self.d / "nope.md")["reason"], "not-in-capsule")
        self.rc.unlink()
        self.assertEqual(cc.reuse(cap2, self.rc)["reason"], "source-missing")


if __name__ == "__main__":
    unittest.main()
