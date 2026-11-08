"""Freeze judge tolerances from synthetic clips with known truth: `python tests/freeze_tolerances.py OUT.json`.

Builds a reference, a benign re-encode (A/A) and three negative controls, measures them with the same pipeline the
judge uses, and calls `judge.freeze`, which refuses when the A/A floor does not clear the best control. Run it BEFORE
the first candidate is judged; the written file is hashed and `load_tolerances` refuses an edited copy."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import synth_judge as sj  # noqa: E402
from test_judge import BASE, measure  # noqa: E402

from vre import judge  # noqa: E402


def main(out: str) -> dict:
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        ref = sj.variant(base / "ref.mp4")
        clips = {
            "aa": sj.encode(base / "aa.mp4", (sj.frame(f) for f in range(sj.N)), crf=30),
            "wrong_easing": sj.variant(base / "c2.mp4", easing="easeInCubic"),
            "missing_object": sj.variant(base / "c3.mp4", missing_shot=1),
            "blank": sj.variant(base / "c4.mp4", n_blank=(40, 41, 42)),
        }
        rspec, rgray = measure(ref, base / "ref")
        per = {k: measure(v, base / k) for k, v in clips.items()}

        def worst(k):
            rows = judge.d_shot_ssim(rspec, rgray, per[k][1], {"shot_ssim_min": 0})["per_shot"]
            return [r["mean"] for r in rows]

        controls = {k: float(np.min(worst(k))) for k in ("wrong_easing", "missing_object", "blank")}
        return judge.freeze(out, worst("aa"), controls, BASE)


if __name__ == "__main__":
    print(main(sys.argv[1]))
