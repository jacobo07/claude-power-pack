"""V-CCREPOCH-*: python tools/test_ccr_epoch_econ.py"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ccr_epoch_econ as E


def mk(ctxs, cw_of):
    out, prev = [], 0
    for i, c in enumerate(ctxs):
        cw = cw_of(i, c, prev)
        out.append({"inp": 1, "cw": cw, "cr": c - 1 - cw, "out": 100})
        prev = c
    return out


class T(unittest.TestCase):
    def test_linear_growth_F_beats_A(self):  # V-CCREPOCH-LINEAR
        ctxs = [20000 + 3000 * i for i in range(120)]
        calls = mk(ctxs, lambda i, c, p: 20000 - 1 if i == 0 else 3000)
        a = E.simulate(calls, "A")["cost"]
        f = E.simulate(calls, "F", m=1.0, exp_len=120)
        self.assertLess(f["cost"], a)
        self.assertGreater(f["rotations"], 0)

    def test_flat_every_rotation_loses(self):  # V-CCREPOCH-FLAT
        calls = mk([30000] * 60, lambda i, c, p: 29999 if i == 0 else 50)
        a = E.simulate(calls, "A")["cost"]
        for arm, kw in (("B", {}), ("C", {}), ("D", {}), ("E", {}), ("F", {"m": 1.0, "exp_len": 60})):
            r = E.simulate(calls, arm, **kw)
            if arm in ("B", "C", "D"):
                self.assertGreater(r["rotations"], 0)
                self.assertGreater(r["cost"], a, arm)
            else:
                self.assertGreaterEqual(r["cost"], a - 1e-6, arm)

    def test_missing_cache_creation_is_unknown(self):  # V-CCREPOCH-UNKNOWN
        with tempfile.TemporaryDirectory() as d:
            row = {"type": "assistant", "message": {"id": "m1", "usage": {"input_tokens": 5, "cache_read_input_tokens": 10, "output_tokens": 1}}}
            p = os.path.join(d, "s.jsonl")
            with open(p, "w") as fh:
                fh.write(json.dumps(row) + "\n")
            calls, unk, _ = E.load_session(p)
            self.assertTrue(unk)
            tr, he, unknown, short = E.load_dir_sessions(d, "2026-10-01")
            self.assertEqual((len(tr), len(he), unknown), (0, 0, 1))


if __name__ == "__main__":
    unittest.main()
