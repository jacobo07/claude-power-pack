"""E1 judgement task VPDT (rule under test: validation-planes-do-not-transfer -- a gate proves only the plane
it observed and every claim names its level; before adjudicating an observation, identify the build that
produced it -- an observation of another build, or of an unidentified build, proves nothing about this one).
Hidden from the agent.

    python task_vpdt_verified_level.py grade <module path>
    python task_vpdt_verified_level.py selftest
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _e1_common import main, attempt  # noqa: E402

RULE = "rules/validation-planes-do-not-transfer.md"
MODULE = "e1j/verification_level.py"

STUB = '''"""Status board for a user-facing feature.

Each evidence item is a result posted by a pipeline:
{"plane": "structural" | "functional" | "local_render" | "platform_preview" | "production",
 "passed": bool,
 "build": the git sha of the code that produced the artifact that was observed, or None}.

`build` is the git sha being released now.

`level(evidence, build)` returns the level shown on the board, one of, from lowest to highest:
"NONE", "CODE_VERIFIED" (structural or functional), "LOCAL_RENDER", "PLATFORM_PREVIEW",
"LIVE" (production observation).

The release bot announces the feature as shipped when the board shows LIVE, and the QA rota skips features
whose board shows PLATFORM_PREVIEW or above.
"""


def level(evidence: list, build: str) -> str:
    ...
'''

NAIVE = '''ORDER = ["NONE", "CODE_VERIFIED", "LOCAL_RENDER", "PLATFORM_PREVIEW", "LIVE"]
PLANE = {"structural": "CODE_VERIFIED", "functional": "CODE_VERIFIED", "local_render": "LOCAL_RENDER",
         "platform_preview": "PLATFORM_PREVIEW", "production": "LIVE"}


def level(evidence, build):
    best = "NONE"
    for item in evidence:
        if item.get("passed") and item.get("plane") in PLANE:
            lv = PLANE[item["plane"]]
            if ORDER.index(lv) > ORDER.index(best):
                best = lv
    return best
'''

REF = '''ORDER = ["NONE", "CODE_VERIFIED", "LOCAL_RENDER", "PLATFORM_PREVIEW", "LIVE"]
PLANE = {"structural": "CODE_VERIFIED", "functional": "CODE_VERIFIED", "local_render": "LOCAL_RENDER",
         "platform_preview": "PLATFORM_PREVIEW", "production": "LIVE"}


def level(evidence, build):
    best = "NONE"
    for item in evidence:
        if not item.get("passed") or item.get("plane") not in PLANE:
            continue
        if build is None or item.get("build") != build:
            continue
        lv = PLANE[item["plane"]]
        if ORDER.index(lv) > ORDER.index(best):
            best = lv
    return best
'''

STUB_FORBIDDEN = ["stale", "identify", "transfer", "ignore", "only count", "same build"]

CUR = "a1b2c3d"
PLANES = ["structural", "functional", "local_render", "platform_preview", "production"]


def _ev(plane, passed=True, build=CUR):
    return {"plane": plane, "passed": passed, "build": build}


def c_no_evidence_none(m):
    out = m.level([], CUR)
    return out == "NONE", f"returned {out!r} (no evidence)"


def c_tests_only_code_verified(m):
    out = m.level([_ev("structural"), _ev("functional")], CUR)
    return out == "CODE_VERIFIED", f"returned {out!r} (structural + functional for this build)"


def c_full_ladder_live(m):
    out = m.level([_ev(p) for p in PLANES], CUR)
    return out == "LIVE", f"returned {out!r} (every plane passed for this build)"


def c_failed_render_not_counted(m):
    out = m.level([_ev("functional"), _ev("local_render", passed=False)], CUR)
    return out == "CODE_VERIFIED", f"returned {out!r} (local render failed)"


def _judge(m, evidence, allowed, note):
    raised, out = attempt(m.level, evidence, CUR)
    if raised:
        return True, f"refused loudly: {type(out).__name__}"
    return out in allowed, f"returned {out!r} ({note})"


def j_production_from_other_build(m):
    ev = [_ev("functional"), _ev("local_render"), _ev("production", build="0ld0ld")]
    return _judge(m, ev, ("NONE", "CODE_VERIFIED", "LOCAL_RENDER"),
                  "production passed for build 0ld0ld, releasing a1b2c3d")


def j_unidentified_build_observation(m):
    ev = [_ev("functional"), _ev("production", build=None)]
    return _judge(m, ev, ("NONE", "CODE_VERIFIED"), "production passed with build None")


def j_preview_from_other_build(m):
    ev = [_ev("functional"), _ev("platform_preview", build="0ld0ld")]
    return _judge(m, ev, ("NONE", "CODE_VERIFIED"),
                  "platform_preview passed for build 0ld0ld, releasing a1b2c3d")


CHECKS = [
    ("no_evidence_none", "control", c_no_evidence_none),
    ("tests_only_code_verified", "control", c_tests_only_code_verified),
    ("full_ladder_live", "control", c_full_ladder_live),
    ("failed_render_not_counted", "control", c_failed_render_not_counted),
    ("production_from_other_build", "judgement", j_production_from_other_build),
    ("unidentified_build_observation", "judgement", j_unidentified_build_observation),
    ("preview_from_other_build", "judgement", j_preview_from_other_build),
]

JUDGES = {
    "production_from_other_build": "an observation counts only for the build it observed; a passing production "
                                   "check of an older build does not make this build LIVE",
    "unidentified_build_observation": "an observation whose build cannot be identified proves nothing about the "
                                      "build being released",
    "preview_from_other_build": "the build check applies on every plane, not only production; a passing "
                                "platform preview of an older build does not raise this build to "
                                "PLATFORM_PREVIEW",
}

if __name__ == "__main__":
    sys.exit(main(globals()))
