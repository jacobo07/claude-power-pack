#!/usr/bin/env python
"""V-ENV-* / V-CWU-* gates for the mission envelope setter and the compiled work-unit launch
(spec vault/specs/mission-envelope-and-compiled-wu.md).

Hermetic, like test_gsd_mission_owner_hold.py: state goes to a temp dir BEFORE import and the launcher is
an injected runner. Every refusal has a paired control, so a setter that refuses (or accepts) everything
cannot go green.

Mutation drill: set GSD_MISSION_DRILL_DIR to a directory holding a mutated copy of gsd_mission.py; it is
imported instead of the real module, so the live file is never edited to prove the gates can go red.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

TMP = tempfile.mkdtemp(prefix="gsd-mission-envelope-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ.pop("CPP_MISSION_RENEW", None)
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402
import mission_spend as ms  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None

passes = fails = 0
NOW = 1_800_000_000.0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def refused(fn) -> bool:
    try:
        fn()
    except gm.MissionError:
        return True
    return False


def _running(mid: str) -> dict:
    gm.create(TMP, "/gsd-autonomous --ws wsx", mission_id=mid, now=NOW)
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                         state=gm.RUNNING, epoch=1, cost_mark={"fp": "abc", "tokens": 5})


def main() -> int:
    # 1. the envelope is stored, normalised, and read by its consumers; identity and clock untouched.
    before = _running("m-env")
    rec = gm.set_envelope("m-env", token_estimate="16M", model="sonnet", autocompact="300K", now=NOW + 60)
    check("V-ENV-STORED", rec.get("token_estimate") == 16_000_000 and rec.get("model") == "sonnet"
          and rec.get("autocompact") == "300k",
          f"{rec.get('token_estimate')} {rec.get('model')} {rec.get('autocompact')}")
    check("V-ENV-CLOCK-AND-IDENTITY-KEPT",
          rec["state"] == before["state"] and rec["epoch"] == before["epoch"]
          and rec["created_at"] == before["created_at"] and rec.get("cost_mark") == before.get("cost_mark")
          and rec["seq"] == before["seq"] + 1, f"{rec['state']} e{rec['epoch']} seq{rec['seq']}")
    rows = [e for e in gm.lr.ledger_events("m-env") if e.get("event") == "envelope_set"]
    check("V-ENV-LEDGER-ROW", len(rows) == 1 and "token_estimate" in (rows[0].get("reason") or ""),
          str(rows[-1] if rows else None))
    argv = gm.worker_argv(rec, "PROMPT")
    check("V-ENV-ARGV-MODEL", argv[argv.index("--model") + 1] == "sonnet" if "--model" in argv else False)
    check("V-ENV-ARGV-AUTOCOMPACT", argv[argv.index("--autocompact") + 1] == "300k")
    check("V-ENV-BREAKER-READS-ESTIMATE",
          ms.judge(rec, 20_000_000, None)["trip"] is None and bool(ms.judge(rec, 40_000_000, None)["trip"]),
          "20M under 2x16M, 40M over")
    one = gm.set_envelope("m-env", model="claude-opus-5-5", now=NOW + 61)
    check("V-ENV-PARTIAL-KEEPS-OTHERS", one.get("model") == "claude-opus-5-5"
          and one.get("token_estimate") == 16_000_000 and one.get("autocompact") == "300k")

    # 2. refusals, each with nothing written.
    seq = gm.load("m-env")["seq"]
    bad = {
        "NO-FIELD": lambda: gm.set_envelope("m-env", now=NOW),
        "ZERO": lambda: gm.set_envelope("m-env", token_estimate="0", now=NOW),
        "NEGATIVE": lambda: gm.set_envelope("m-env", token_estimate="-5", now=NOW),
        "GARBAGE": lambda: gm.set_envelope("m-env", autocompact="abc", now=NOW),
        "MODEL-FOREIGN": lambda: gm.set_envelope("m-env", model="gpt-4", now=NOW),
        "MODEL-FLAG": lambda: gm.set_envelope("m-env", model="--x", now=NOW),
        "PACKET-MISSING": lambda: gm.set_envelope("m-env", wu_packet=str(Path(TMP) / "nope.md"), now=NOW),
        "UNKNOWN-MISSION": lambda: gm.set_envelope("m-none", model="sonnet", now=NOW),
    }
    empty = Path(TMP) / "empty.md"
    empty.write_text("", encoding="utf-8")
    bad["PACKET-EMPTY"] = lambda: gm.set_envelope("m-env", wu_packet=str(empty), now=NOW)
    for name, fn in bad.items():
        check(f"V-ENV-REFUSE-{name}", refused(fn))
    check("V-ENV-REFUSAL-WRITES-NOTHING", gm.load("m-env")["seq"] == seq, f"seq {gm.load('m-env')['seq']}")
    gm.create(TMP, "/gsd-autonomous", mission_id="m-done", now=NOW)
    gm.transition("m-done", expect_epoch=0, expect_state=gm.PREPARED, event="t_done", now=NOW,
                  state=gm.HALTED, reason="test")
    check("V-ENV-REFUSE-TERMINAL", refused(lambda: gm.set_envelope("m-done", model="sonnet", now=NOW)))
    check("V-ENV-CONTROL-VALID-ACCEPTED",
          gm.set_envelope("m-env", token_estimate="1.5m", now=NOW).get("token_estimate") == 1_500_000)

    # 3. launch_prompt: legacy bytes without a packet; compiled prompt with one.
    plain = gm.load("m-env")
    check("V-CWU-LEGACY-PROMPT", gm.launch_prompt(plain) == gm.bind_workstream(plain["resume_command"],
                                                                                 plain.get("workstream")),
          gm.launch_prompt(plain))
    pkt = Path(TMP) / "WU-A.md"
    pkt.write_text("# WU-A\nDo the thing.\n", encoding="utf-8")
    withp = gm.set_envelope("m-env", wu_packet=str(pkt), now=NOW)
    p = gm.launch_prompt(withp)
    check("V-CWU-PACKET-STORED", (withp.get("wu_packet") or {}).get("path") == str(pkt.resolve())
          and len((withp.get("wu_packet") or {}).get("sha256") or "") == 64)
    check("V-CWU-PROMPT-NAMES-PACKET", str(pkt.resolve()) in p and withp["wu_packet"]["sha256"][:12] in p, p[:200])
    check("V-CWU-PROMPT-NO-GSD", "/gsd-" not in p, p[:200])
    check("V-CWU-PROMPT-CARRIES-LESSONS", "git log" in p and "question" in p.lower() and "await" in p.lower())

    # 4. launch_worker sends the compiled prompt; an unreadable packet refuses before the claim.
    calls = []

    def runner(argv, cwd):
        calls.append(argv)
        return SimpleNamespace(stdout=f"backgrounded · deadbeef · {argv[3]}", stderr="", returncode=0)

    cur = gm.load("m-env")
    res = gm.launch_worker("m-env", expect_epoch=cur["epoch"], expect_state=cur["state"], reason="t",
                           runner=runner, now=NOW)
    # Judged against the packet path, never against launch_prompt's own output: a mutant that ignores
    # the packet would otherwise agree with itself.
    check("V-CWU-LAUNCH-SENDS-PACKET", bool(res.get("ok") and calls and str(pkt.resolve()) in calls[-1][-1]
                                            and "/gsd-" not in calls[-1][-1]), str(res))
    after = gm.load("m-env")
    pkt.unlink()
    n = len(calls)
    res2 = gm.launch_worker("m-env", expect_epoch=after["epoch"], expect_state=after["state"], reason="t",
                            runner=runner, now=NOW)
    check("V-CWU-MISSING-PACKET-REFUSES", res2.get("ok") is False and len(calls) == n
          and gm.load("m-env")["epoch"] == after["epoch"], str(res2))

    # 5. the Owner-facing CLI reaches the same setter; a bare call is refused.
    _running("m-cli")
    rc = gm._cli(["envelope", "--mission", "m-cli", "--token-estimate", "16M", "--model", "sonnet",
                  "--autocompact", "300k"])
    c = gm.load("m-cli")
    check("V-ENV-CLI-SETS", rc == 0 and c.get("token_estimate") == 16_000_000 and c.get("model") == "sonnet"
          and c.get("autocompact") == "300k", str(rc))
    check("V-ENV-CLI-BARE-REFUSED", refused(lambda: gm._cli(["envelope", "--mission", "m-cli"])))

    print(f"ENVELOPE_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
