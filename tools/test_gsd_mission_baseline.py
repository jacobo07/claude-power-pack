#!/usr/bin/env python
"""V-BASE-* gates for the launch-time baseline resolver (ce-presence U6a).

Pure: state goes to a temp dir BEFORE import and the launcher is an injected runner; no worker starts.
Mutation drill: GSD_MISSION_DRILL_DIR names a directory holding a mutated copy of gsd_mission.py.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

TMP = tempfile.mkdtemp(prefix="mission-baseline-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ.pop("CPP_MISSION_RENEW", None)
os.environ.pop("CPP_CE_BASELINE", None)
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
NOW = 1_800_000_000.0
passes = fails = 0
REAL_POLICY = gm._BUDGET_DEFAULTS


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
    else:
        fails += 1
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def arg(argv, flag):
    return argv[argv.index(flag) + 1] if flag in argv else None


def mission(mid, cmd="/gsd-autonomous --ws wsx", **fields):
    gm.create(TMP, cmd, mission_id=mid, now=NOW)
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, **fields)


def launch(mid, mode=None):
    calls = []

    def runner(argv, cwd):
        calls.append(argv)
        return SimpleNamespace(stdout=f"backgrounded · deadbeef · {argv[3]}", stderr="", returncode=0)

    if mode is None:
        os.environ.pop("CPP_CE_BASELINE", None)
    else:
        os.environ["CPP_CE_BASELINE"] = mode
    cur = gm.load(mid)
    res = gm.launch_worker(mid, expect_epoch=cur["epoch"], expect_state=cur["state"], reason="t",
                           runner=runner, now=NOW)
    return res, (calls[-1] if calls else None)


def main() -> int:
    # V-BASE-ABSENT: nothing set -> sonnet + policy ceilings, provenance recorded.
    mission("m-abs")
    res, argv = launch("m-abs")
    rec = gm.load("m-abs")
    check("V-BASE-ABSENT-MODEL", bool(argv) and arg(argv, "--model") == "sonnet", str(argv))
    check("V-BASE-ABSENT-CEILINGS", arg(argv, "--autocompact") == "250k" and rec.get("continue_max_tokens") == 250_000,
          f"{arg(argv, '--autocompact')} {rec.get('continue_max_tokens')}")
    b = rec.get("baseline") or {}
    check("V-BASE-RECORD", b.get("version") == "1" and b.get("tier") == "BASIC" and b.get("work_class") == "GSD_RESUME"
          and set((b.get("src") or {}).values()) == {"policy@1"}, str(b))
    check("V-BASE-LEDGER-ROW", any(e.get("event") == "baseline_resolved" for e in gm.lr.ledger_events("m-abs")))
    check("V-BASE-GSD-RESUME-NEVER-SLIM", not gm.slim_profile(rec) and argv[1] == "--bg", str(argv[:3]))

    # V-BASE-EXPLICIT: an explicit value is kept, source explicit.
    mission("m-exp", model="claude-opus-5-5", autocompact="300k")
    _, argv = launch("m-exp")
    b = gm.load("m-exp")["baseline"]
    check("V-BASE-EXPLICIT-KEPT", arg(argv, "--model") == "claude-opus-5-5" and arg(argv, "--autocompact") == "300k"
          and b["src"]["model"] == "explicit" and b["src"]["autocompact"] == "explicit"
          and b["src"]["continue_max_tokens"] == "policy@1", str(b))

    # V-BASE-BUILTIN: unreadable policy -> built-in values, never opus / 600k.
    gm._BUDGET_DEFAULTS = Path(TMP) / "nope.json"
    mission("m-bi")
    _, argv = launch("m-bi")
    b = gm.load("m-bi")["baseline"]
    check("V-BASE-BUILTIN", arg(argv, "--model") == "sonnet" and arg(argv, "--autocompact") not in (None, "600k")
          and "opus" not in " ".join(argv).lower() and set(b["src"].values()) == {"builtin"}, str(b))
    bad = Path(TMP) / "bad.json"
    bad.write_text('{"baseline_version": "9"}', encoding="utf-8")
    gm._BUDGET_DEFAULTS = bad
    check("V-BASE-MALFORMED-POLICY-BUILTIN", gm._baseline_policy()[1] == "builtin")
    gm._BUDGET_DEFAULTS = REAL_POLICY
    check("V-BASE-OLD-KEYS-UNCHANGED", gm._budget_defaults()[0] == {"headroom_tokens": 15_000_000,
                                                                     "min_headroom_tokens": 1_000_000})

    # V-BASE-CLASS: Work Class from the record only.
    check("V-BASE-CLASS", gm.work_class({"wu_packet": {"path": "x"}}) == "COMPILED_UNIT"
          and gm.work_class({"resume_command": "/gsd-autonomous"}) == "GSD_RESUME"
          and gm.work_class({"resume_command": "do x"}) == "OTHER")

    # V-BASE-PACKET-SLIM: a packet record keeps its slim route untouched.
    slim = gm.resolve_baseline({"mission_id": "m", "epoch": 1, "resume_command": "x", "wu_packet": {"path": "p"},
                                "worker_profile": "slim-t2"})
    check("V-BASE-PACKET-SLIM-UNTOUCHED", gm.slim_profile(slim) == "slim-t2" and slim["baseline"]["tier"] == "COMPILED"
          and slim["baseline"]["work_class"] == "COMPILED_UNIT")

    # V-BASE-OFF: no change at all.
    mission("m-off")
    _, argv = launch("m-off", "off")
    rec = gm.load("m-off")
    check("V-BASE-OFF-ARGV-IDENTICAL", "--model" not in argv and arg(argv, "--autocompact") == "600k"
          and "baseline" not in rec and "continue_max_tokens" not in rec, str(argv))
    check("V-BASE-OFF-NO-LEDGER", not any(e.get("event") == "baseline_resolved" for e in gm.lr.ledger_events("m-off")))

    # V-BASE-ENFORCE: unexplained legacy combo refused; reason allows and records.
    mission("m-enf", model="opus", autocompact="600k")
    res, argv = launch("m-enf", "enforce")
    check("V-BASE-ENFORCE-REFUSED", not res["ok"] and argv is None and "legacy_reason" in res["why"]
          and gm.load("m-enf")["epoch"] == 0, str(res))
    mission("m-enf2", model="opus", autocompact="600k", legacy_reason="quality_requirement")
    res, argv = launch("m-enf2", "enforce")
    check("V-BASE-ENFORCE-WITH-REASON", bool(res["ok"]) and gm.load("m-enf2")["baseline"]["legacy_reason"]
          == "quality_requirement", str(res))
    mission("m-enf3", model="opus", autocompact="600k", legacy_reason="made_up")
    res, _ = launch("m-enf3", "enforce")
    check("V-BASE-ENFORCE-UNKNOWN-REASON-REFUSED", not res["ok"])
    mission("m-enf4")
    res, _ = launch("m-enf4", "enforce")
    check("V-BASE-ENFORCE-DEFAULTS-PASS", bool(res["ok"]), str(res))

    # V-BASE-SHADOW: the legacy combo launches and only logs.
    mission("m-sh", model="opus", autocompact="600k")
    res, argv = launch("m-sh", "shadow")
    check("V-BASE-SHADOW-LOGS", bool(res["ok"]) and any(e.get("event") == "would_refuse_legacy"
                                                         for e in gm.lr.ledger_events("m-sh")))
    check("V-BASE-MODE-PARSER", all((os.environ.__setitem__("CPP_CE_BASELINE", v), gm.baseline_mode())[1] == w
                                    for v, w in (("enforce", "enforce"), ("OFF", "off"), ("zzz", "shadow"))))
    os.environ.pop("CPP_CE_BASELINE", None)
    print(f"{passes} passed, {fails} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
