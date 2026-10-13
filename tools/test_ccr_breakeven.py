"""V-CCRBE: weighted rotation break-even (tools/ccr_breakeven.py)."""
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ccr_breakeven as be  # noqa: E402

M = {"cls": "t", "n": 10, "capsule": 1000.0, "r": 3, "floor": 20000.0, "R": 5000.0, "rehyd_cost": 10000.0,
     "first_overhead": 500.0, "g": 2000.0, "lengths": [60] * 10}


def linear(n, floor=20000, g=2000, out=300):
    calls, prev = [], 0
    for i in range(n):
        ctx = floor + g * i
        calls.append({"inp": 5, "cr": prev, "cw": ctx - prev - 5, "out": out})
        prev = ctx
    return calls


class T(unittest.TestCase):
    def test_V_CCRBE_01_rotate_once_and_k_star(self):
        once = 1.25 * (20000 + 1000) + 10000 + 3 * 0.1 * 1000 + 500
        self.assertAlmostEqual(be.rotate_once(M), once)
        self.assertAlmostEqual(be.k_star(126000, M), once / (0.1 * 100000))
        self.assertTrue(math.isinf(be.k_star(25000, M)))      # no carry above the rotated prefix: never pays

    def test_V_CCRBE_02_renewal_threshold(self):
        self.assertAlmostEqual(be.x_star(M), math.sqrt(2 * be.rotate_once(M) * 2000 / 0.1))
        self.assertTrue(math.isinf(be.x_star({**M, "g": 0})))

    def test_V_CCRBE_03_decision_rule(self):
        xs = be.x_star(M)
        below = 20000 + 1000 + 5000 + xs - 1
        self.assertFalse(be.decide(below, 10, M)["rotate"])           # carry under X*
        self.assertTrue(be.decide(below + 2, 10, M)["rotate"])        # over X*, 50 calls still expected
        self.assertFalse(be.decide(below + 2, 59, M)["rotate"])       # over X*, but 1 call left < k*

    def test_V_CCRBE_04_no_greedy_over_rotation(self):
        # A4 regression: the greedy rule rotated every ~15 calls on Lobby and lost 22 %. On a linear session the
        # renewal rule rotates about every T* = X*/g calls and never costs more than not rotating.
        calls = linear(60)
        a, b = be.simulate(calls, M, "A"), be.simulate(calls, M, "BE")
        self.assertLess(b["cost"], a["cost"])
        t_star = be.x_star(M) / M["g"]
        self.assertLessEqual(b["rotations"], math.ceil(60 / t_star))
        self.assertGreaterEqual(b["rotations"], 1)

    def test_V_CCRBE_05_arm_A_is_the_recorded_cost(self):
        calls = linear(12)
        self.assertAlmostEqual(be.simulate(calls, M, "A")["cost"], sum(be.cost_of(c) for c in calls))

    def test_V_CCRBE_06_projection_dedups_streamed_mid(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.jsonl"
            rows = [{"t": "assistant", "mid": "m1", "usage": {"input_tokens": 3, "cache_read_input_tokens": 100,
                                                              "cache_creation_input_tokens": 10, "output_tokens": 5}},
                    {"t": "assistant", "mid": "m1", "usage": {"input_tokens": 3, "cache_read_input_tokens": 100,
                                                              "cache_creation_input_tokens": 10, "output_tokens": 50}},
                    {"t": "assistant", "mid": "m2", "usage": {"input_tokens": 1, "cache_read_input_tokens": 200,
                                                              "cache_creation_input_tokens": 0, "output_tokens": 7}}]
            p.write_text("".join(json.dumps(r) + "\n" for r in rows))
            calls, _ = be.calls_of(p)
            self.assertEqual([c["out"] for c in calls], [50, 7])

    def test_V_CCRBE_07_expected_remaining_survivors(self):
        self.assertEqual(be.expected_remaining(10, [5, 20, 30]), 15)
        self.assertEqual(be.expected_remaining(40, [5, 20, 30]), 0)


if __name__ == "__main__":
    unittest.main()
