#!/usr/bin/env python
"""V-MQR-* gates: a quota hold is released when a DIFFERENT account is logged in than the one the
refused worker ran as.

Origin (2026-10-04, GEX44 m-a828e0f4feb9): the Owner logged in with a new account, but
quota_hold_from_transcript re-derived "weekly limit, resets Oct 7" from the old worker's last line
on every pass, so the renewal would have held for three days. A credentials-file timestamp is not
the fix: token refreshes by other missions rewrite that file every few hours, and each rewrite
would launch a worker into the same limit. Identity is: record the account at launch, compare at
hold time. Every release gate has a hold control, or a module that releases everything passes.

Hermetic: state and the account file live in a temp dir; the launcher and the breaker are fakes.
Run: python tools/test_gsd_mission_quota_relogin.py   (MQR_TOOLS_DIR=<dir> runs a scratch copy)
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-mqr-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
ACCOUNT_FILE = Path(TMP) / "claude.json"
os.environ["CPP_CLAUDE_ACCOUNT_FILE"] = str(ACCOUNT_FILE)

TOOLS = Path(os.environ.get("MQR_TOOLS_DIR") or Path(__file__).resolve().parent)
sys.path.insert(0, str(TOOLS))
sys.path.insert(1, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402
import envelope_fixture  # noqa: E402  (compiled-grammar-default law 2: lifecycle gates need a bounded mission)
envelope_fixture.bound_missions(gm)
import gsd_long_run as lr  # noqa: E402
import provider_breaker as pb  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
NOW = 1_800_000_000.0
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def login(uuid):
    if uuid is None:
        if ACCOUNT_FILE.exists():
            ACCOUNT_FILE.unlink()
        return
    ACCOUNT_FILE.write_text(json.dumps({"oauthAccount": {"accountUuid": uuid, "emailAddress": "x@example.invalid"}}),
                            encoding="utf-8")


class R:
    def __init__(self, out):
        self.stdout, self.stderr, self.returncode = out, "", 0


def launched(mid, bg):
    """Arm + launch one worker whose host id is `bg`; returns the mission record."""
    for p in Path(TMP).glob("gsd-mission-*.json"):
        p.unlink()
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    out = gm.launch_worker(mid, expect_epoch=0, expect_state=gm.PREPARED, reason="armed", now=NOW,
                           runner=lambda argv, cwd: R(f"backgrounded · {bg} · {mid}-e1\n"))
    return out, gm.load(mid)


QUOTA = {"class": "quota", "until": NOW + 3 * 86400, "reason": "You've hit your weekly limit"}


def hold_with(rec, owner_session):
    real = pb.hold_for
    pb.hold_for = lambda r, now: dict(QUOTA)
    try:
        return gm.provider_hold({**rec, "owner": {"session_id": owner_session}}, NOW + 60)
    finally:
        pb.hold_for = real


def main() -> int:
    login("acct-A")
    out, rec = launched("m-mqr-1", "a1b2c3d4")
    seen = json.loads((Path(TMP) / "launch-accounts.json").read_text(encoding="utf-8")) \
        if (Path(TMP) / "launch-accounts.json").exists() else {}
    check("V-MQR-RECORDS-ACCOUNT-AT-LAUNCH", out.get("ok") and seen.get("a1b2c3d4") == "acct-A", str(seen))

    check("V-MQR-SAME-ACCOUNT-HOLDS", hold_with(rec, "a1b2c3d4-0000") is not None,
          "same account still logged in: the successor would meet the same limit")

    login("acct-B")
    released = hold_with(rec, "a1b2c3d4-0000")
    events = [e["event"] for e in lr.ledger_events("m-mqr-1")]
    check("V-MQR-ACCOUNT-CHANGED-RELEASES", released is None and "quota_hold_released" in events,
          f"hold={released} ledger has release={'quota_hold_released' in events}")

    check("V-MQR-UNRECORDED-HOLDS", hold_with(rec, "ffffffff-0000") is not None,
          "a worker launched before recording existed: no evidence, keep the hold")

    login(None)
    check("V-MQR-UNREADABLE-HOLDS", hold_with(rec, "a1b2c3d4-0000") is not None,
          "account unreadable: unknown is not changed")

    # Renewal: the owner was launched by the PREVIOUS mission; the record is keyed by worker id.
    login("acct-A")
    launched("m-mqr-old", "e5f6a7b8")
    gm.create(TMP, "/gsd-autonomous", mission_id="m-mqr-renewal", now=NOW)
    renewal = gm.load("m-mqr-renewal")
    login("acct-B")
    check("V-MQR-RENEWAL-RELEASES", hold_with(renewal, "e5f6a7b8-1111") is None,
          "a renewal inherits the old worker; its account record still applies")

    other = {**QUOTA, "class": "auth"}
    real = pb.hold_for
    pb.hold_for = lambda r, now: dict(other)
    try:
        h = gm.provider_hold({**rec, "owner": {"session_id": "a1b2c3d4-0000"}}, NOW + 60)
    finally:
        pb.hold_for = real
    check("V-MQR-ONLY-QUOTA-RELEASED", h is not None and h.get("class") == "auth",
          "an auth hold is not lifted by an account change (it needs its own evidence)")

    print(f"MQR_PASS={passes}/{passes + fails}  threshold=7/7")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
