"""V-EVB-*: tools/evidence_bundle.py -- CPP V-gates and review intake as collector receipts.

Hermetic: a temporary root holding the artifact and a synthetic gate script whose summary line
and exit code each case chooses. The green control is a gate that passed with n==m>0 and an
independent reviewer that EXPLICITLY returned no findings; every other case breaks one property.
    python tools/test_evidence_bundle.py
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import evidence_bundle as eb  # noqa: E402

passes = fails = 0
REVIEWER = {"agent": "pp-code-reviewer", "model": "claude-sonnet-5", "effort": "default"}
REQUIRED = {"model": "claude-sonnet-5", "effort": "default"}


def check(gate: str, cond: bool, ev: object = "") -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {ev}")


def gate_script(root: Path, name: str, summary: str | None, code: int) -> str:
    body = (f"print({summary!r})\n" if summary else "print('no summary here')\n") + f"raise SystemExit({code})\n"
    (root / f"{name}.py").write_text(body, encoding="utf-8")
    return f"python {name}.py"


def bundle(root: Path, task: str, cmd: str, reply: str | None, worker: str = "worker-7",
           reviewer: dict = REVIEWER, mutate_after_check: bool = False, ticket: bool = True,
           edit_after_ticket: bool = False, echo: bool = True, old_reply: bool = False) -> dict:
    arts = ["art.py"]
    if reply is not None:
        reply = "```json\n" + reply + "\n```"  # the shape REPLY_INSTRUCTION asks a real reviewer for
    if reply is not None and old_reply:
        # A reply written for an EARLIER dispatch: it echoes that ticket's nonce, not the new one.
        _, stale_nonce = eb.ticket(root, "plan-1", task, arts)
        reply = eb.ticket_line(stale_nonce) + "\n" + reply
    if reply is not None and ticket:
        _, nonce = eb.ticket(root, "plan-1", task, arts)  # the reviewer is dispatched now, on these bytes
        if echo and not old_reply:
            reply = eb.ticket_line(nonce) + "\n" + reply
    if edit_after_ticket:
        (root / "art.py").write_text("x = 3  # edited after the review\n", encoding="utf-8")
    chk = eb.run_check(root, "plan-1", task, "gate-green", cmd, arts)
    if mutate_after_check:
        (root / "art.py").write_text("x = 2\n", encoding="utf-8")
    review_path = None
    if reply is not None:
        review_path, _ = eb.write_review(root, "plan-1", task, reply, reviewer, arts, [chk])
    return eb.collect(root, "plan-1", task, worker, ["gate-green"], arts, [chk], review_path,
                      REQUIRED if reply is not None else None)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="evb_t_"))
    try:
        (tmp / "art.py").write_text("x = 1\n", encoding="utf-8")
        good = gate_script(tmp, "g_ok", "DEMO_PASS=3/3  threshold=3/3", 0)
        b = bundle(tmp, "t-green", good, '{"findings": []}')
        check("V-EVB-GREEN", b.get("ok") is True and not b.get("failures"), b.get("failures"))

        print("a gate that judged nothing is not a green gate")
        for gate, summary, code in [("V-EVB-EMPTY-GATE", "DEMO_PASS=0/0", 0), ("V-EVB-NO-SUMMARY", None, 0),
                                    ("V-EVB-PARTIAL-GATE", "DEMO_PASS=2/3", 0),
                                    ("V-EVB-EXIT-NONZERO", "DEMO_PASS=3/3", 1)]:
            cmd = gate_script(tmp, "g_" + gate[6:].lower().replace("-", "_"), summary, code)
            b = bundle(tmp, "t-" + gate.lower(), cmd, '{"findings": []}')
            check(gate, b.get("ok") is False and any("Failed, empty or stale" in f for f in b.get("failures") or []),
                  b.get("failures"))

        print("independent review")
        b = bundle(tmp, "t-self", good, '{"findings": []}', worker="pp-code-reviewer")
        check("V-EVB-REVIEWER-IS-WORKER", b.get("ok") is False
              and any("Independent review" in f for f in b.get("failures") or []), b.get("failures"))
        b = bundle(tmp, "t-noreview", good, None)
        check("V-EVB-NO-REVIEW", b.get("ok") is False
              and any("Independent review required" in f for f in b.get("failures") or []), b.get("failures"))
        b = bundle(tmp, "t-prose", good, "Looks fine to me.")
        check("V-EVB-PROSE-REVIEW-FAILS", b.get("ok") is False, b.get("failures"))
        b = bundle(tmp, "t-high", good, '{"findings": [{"id": "a", "severity": "high", "title": "t", '
                                        '"description": "d", "evidence": "art.py:1"}]}')
        check("V-EVB-HIGH-FINDING-FAILS", b.get("ok") is False, b.get("failures"))

        print("bytes bind")
        b = bundle(tmp, "t-moved", good, '{"findings": []}', mutate_after_check=True)
        check("V-EVB-ARTIFACT-MOVED", b.get("ok") is False, b.get("failures"))
        (tmp / "art.py").write_text("x = 1\n", encoding="utf-8")

        print("an approval binds what the reviewer SAW (real review, 2026-09-28: it bound disk-now)")
        b = bundle(tmp, "t-edited", good, '{"findings": []}', edit_after_ticket=True)
        check("V-EVB-REVIEWED-THEN-EDITED", b.get("ok") is False
              and any("Independent review" in f for f in b.get("failures") or []), b.get("failures"))
        (tmp / "art.py").write_text("x = 1\n", encoding="utf-8")
        b = bundle(tmp, "t-noticket", good, '{"findings": []}', ticket=False)
        check("V-EVB-NO-TICKET-NO-PASS", b.get("ok") is False, b.get("failures"))
        b = bundle(tmp, "t-green-2", good, '{"findings": []}')
        check("V-EVB-GREEN-AFTER-RESTORE", b.get("ok") is True, b.get("failures"))
        # Second real review: re-ticketing after an edit let an OLD approval through, because
        # hashes record when --ticket ran. The reply must echo the nonce of THIS ticket.
        b = bundle(tmp, "t-stale-reply", good, '{"findings": []}', old_reply=True)
        check("V-EVB-OLD-REPLY-RETICKETED-FAILS", b.get("ok") is False, b.get("failures"))
        b = bundle(tmp, "t-no-echo", good, '{"findings": []}', echo=False)
        check("V-EVB-NO-NONCE-ECHO-FAILS", b.get("ok") is False, b.get("failures"))
        (tmp / "secret_rotation.py").write_text("x = 1\n", encoding="utf-8")
        prot = eb.collect(tmp, "plan-1", "t-prot", "w", ["gate-green"], ["secret_rotation.py"], [])
        check("V-EVB-PROTECTED-PATH-NAMED", prot.get("unjudged") is True
              and "protected proof paths" in (prot.get("failures") or [""])[0], prot.get("failures"))
        # Third real review: receipt paths carry the plan/task/criterion slugs, so a plan named for
        # the secret firewall was a bare UNJUDGED from the collector's throw.
        chk = eb.run_check(tmp, "secret-firewall-v2", "t", "gate-green", good, ["art.py"])
        prot2 = eb.collect(tmp, "secret-firewall-v2", "t", "w", ["gate-green"], ["art.py"], [chk])
        check("V-EVB-PROTECTED-RECEIPT-PATH-NAMED", prot2.get("unjudged") is True
              and "secret-firewall-v2" in (prot2.get("failures") or [""])[0], prot2.get("failures"))

        print("a gate binds the bytes it ran against")
        (tmp / "g_mutates.py").write_text("import pathlib\npathlib.Path('art.py').write_text('x = 9\\n')\n"
                                          "print('DEMO_PASS=1/1')\n", encoding="utf-8")
        rel = eb.run_check(tmp, "plan-1", "t-mid", "gate-green", "python g_mutates.py", ["art.py"])
        rec = json.loads((tmp / rel).read_text(encoding="utf-8"))
        check("V-EVB-MOVED-DURING-RUN-FAILS", rec["status"] == "failed" and rec["artifactsMovedDuringRun"] is True,
              (rec["status"], rec["artifactsMovedDuringRun"]))
        (tmp / "art.py").write_text("x = 1\n", encoding="utf-8")
        if os.name == "nt":
            (tmp / "sub").mkdir(exist_ok=True)
            (tmp / "sub" / "g.py").write_text("print('DEMO_PASS=1/1')\n", encoding="utf-8")
            rel = eb.run_check(tmp, "plan-1", "t-bs", "gate-green", "python sub\\g.py", ["art.py"])
            rec = json.loads((tmp / rel).read_text(encoding="utf-8"))
            check("V-EVB-BACKSLASH-COMMAND-RUNS", rec["status"] == "passed", (rec["exitCode"], rec["checkedCount"]))

        saved = os.environ.get("CPP_NODE_EXE")
        os.environ["CPP_NODE_EXE"] = str(tmp / "no-node.exe")
        try:
            down = bundle(tmp, "t-down", good, None)
        finally:
            if saved is None:
                os.environ.pop("CPP_NODE_EXE", None)
            else:
                os.environ["CPP_NODE_EXE"] = saved
        check("V-EVB-BRIDGE-DOWN-UNJUDGED", down.get("ok") is False and down.get("unjudged") is True, down.get("failures"))
        check("V-EVB-RECEIPTS-UNDER-LOGS", (tmp / "_logs" / "evidence" / "plan-1" / "t-green" / "checks"
                                             / "gate-green.json").is_file(), "receipt path")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    total = passes + fails
    print(f"EVB_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
