"""V-REUSE-* gates for tools/verified_reuse.py and its consumer tools/batch_drafts.py (T8 item 30).

Every binding is driven from both poles against the real vendored module through the bridge,
in private temp roots (never the repo, never ~/.claude):
  identical inputs -> HIT, never accepted     changed source byte -> MISS
  changed contract -> MISS                    same bytes, other worktree root -> MISS
  stored draft edited in place -> MISS        kill switch -> no lookup at all
and the approval boundary is DRIVEN, not asserted: a reused draft offered to the review gate
after a ticket was issued is judged "fail", because it cannot echo that ticket's nonce.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
os.environ["CPP_BATCH_DRAFTS_DIR"] = tempfile.mkdtemp(prefix="reuse-receipts-")
import batch_drafts as bd  # noqa: E402
import evidence_bundle as eb  # noqa: E402
import verified_reuse as vr  # noqa: E402

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def make_root() -> Path:
    r = Path(tempfile.mkdtemp(prefix="reuse-root-"))
    (r / "src").mkdir()
    (r / "src" / "mod.py").write_text("def f(x):\n    return x + 1\n", encoding="utf-8")
    return r


def mk_task(acceptance=("name the return expression",)):
    return bd.task(id="review-mod", review="What does f return?", paths=["src/mod.py"],
                   selectors=[{"path": "src/mod.py", "startLine": 1, "endLine": 2}], acceptance=list(acceptance))


DRAFT = {"id": "review-mod", "verdict": "pass", "mechanism": "f returns x + 1",
         "fix": "none", "evidence": [{"path": "src/mod.py", "line": 2, "quote": "return x + 1"}]}


def main() -> int:
    root = make_root()
    t = mk_task()
    st, info = vr.admit(root, t, bd.OUTPUT_BOUNDS, DRAFT, plan_id="plan-a", worker_id="w1")
    check("V-REUSE-ADMIT", st == vr.ADMITTED, f"validated draft admitted: {st} {info}")

    st, hit = vr.lookup(root, t, bd.OUTPUT_BOUNDS, plan_id="plan-b")
    check("V-REUSE-HIT", st == vr.HIT and hit.get("draft") == DRAFT, f"identical inputs hand back the draft: {st}")
    check("V-REUSE-NEVER-ACCEPTED", st == vr.HIT and hit["accepted"] is False and hit["needsFreshReview"] is True,
          "a hit is a draft that still needs a fresh review")

    # The approval boundary, driven through the real review gate.
    eroot = make_root()
    _, nonce = eb.ticket(eroot, "plan-b", "review-mod", ["src/mod.py"])
    reused_reply = json.dumps(hit.get("draft") if st == vr.HIT else DRAFT)
    rel, _res = eb.write_review(eroot, "plan-b", "review-mod", reused_reply,
                                {"agent": "pp-code-reviewer", "model": "claude"}, ["src/mod.py"], [])
    verdict = json.loads((eroot / rel).read_text(encoding="utf-8"))["verdict"]
    check("V-REUSE-CANNOT-APPROVE", verdict == "fail",
          f"a reused draft offered to the review gate is judged {verdict!r}: it cannot echo the new ticket")
    # Positive control for that gate: the same text WITH the nonce is not refused for being unbound.
    rel2, _ = eb.write_review(eroot, "plan-b", "review-mod", reused_reply + "\n" + eb.ticket_line(nonce),
                              {"agent": "pp-code-reviewer", "model": "claude"}, ["src/mod.py"], [])
    reason = json.loads((eroot / rel2).read_text(encoding="utf-8"))["intake"]["reason"] or ""
    check("V-REUSE-GATE-CONTROL", "nonce" not in reason and "ticket" not in reason,
          f"with the nonce echoed the refusal reason is no longer the ticket: {reason[:80]!r}")

    st, miss = vr.lookup(root, mk_task(acceptance=("a different criterion",)), bd.OUTPUT_BOUNDS)
    check("V-REUSE-CONTRACT-BOUND", st == vr.MISS, f"a changed contract misses: {miss.get('reason')}")

    other = Path(tempfile.mkdtemp(prefix="reuse-other-"))
    shutil.copytree(root, other / "wt")
    st, miss = vr.lookup(other / "wt", t, bd.OUTPUT_BOUNDS)
    check("V-REUSE-ROOT-BOUND", st == vr.MISS, f"same bytes in another worktree miss: {miss.get('reason')}")

    out_dir = vr.store(root) / "output"
    stored = next(out_dir.glob("*.txt"))
    original = stored.read_bytes()
    stored.write_bytes(original.replace(b"x + 1", b"x + 2"))
    st, miss = vr.lookup(root, t, bd.OUTPUT_BOUNDS)
    # Must be the vendor's re-hash refusing, not a fingerprint miss (which a broken admit also yields).
    check("V-REUSE-TAMPER", st == vr.MISS and "no admitted draft" not in str(miss.get("reason")),
          f"a stored draft edited in place is refused on re-read: {miss.get('reason')}")
    stored.write_bytes(original)
    st, _ = vr.lookup(root, t, bd.OUTPUT_BOUNDS)
    check("V-REUSE-TAMPER-CONTROL", st == vr.HIT, "restoring the exact bytes restores the hit")

    (root / "src" / "mod.py").write_text("def f(x):\n    return x + 2\n", encoding="utf-8")
    st, miss = vr.lookup(root, t, bd.OUTPUT_BOUNDS)
    check("V-REUSE-SOURCE-BOUND", st == vr.MISS, f"a changed source byte misses: {miss.get('reason')}")
    (root / "src" / "mod.py").write_text("def f(x):\n    return x + 1\n", encoding="utf-8")

    outcome, batch, reused = bd.compile_with_reuse(str(root), [t])
    check("V-REUSE-BATCH-CONSUMER", outcome == bd.REUSED and "review-mod" in reused and not batch,
          f"batch compile hands back the verified draft and dispatches nothing: {outcome}")
    os.environ["CPP_VERIFIED_REUSE"] = "off"
    try:
        outcome, batch, reused = bd.compile_with_reuse(str(root), [t, dict(mk_task(), id="second")])
    finally:
        os.environ.pop("CPP_VERIFIED_REUSE", None)
    check("V-REUSE-KILL-SWITCH", outcome != bd.REUSED and not reused,
          f"with CPP_VERIFIED_REUSE=off nothing is reused: {outcome}")

    import hashlib
    now_sha = hashlib.sha256((root / "src" / "mod.py").read_bytes()).hexdigest()
    st, why = vr.admit(root, t, bd.OUTPUT_BOUNDS, DRAFT, plan_id="plan-c", worker_id="w1",
                       expected_sources={"src/mod.py": "0" * 64})
    check("V-REUSE-COMPILE-BYTES", st == vr.REFUSED and "changed since the batch was compiled" in why.get("reason", ""),
          "a draft written about other bytes is not admitted under today's fingerprint")
    st, _ = vr.admit(root, t, bd.OUTPUT_BOUNDS, DRAFT, plan_id="plan-c", worker_id="w1",
                     expected_sources={"src/mod.py": now_sha})
    check("V-REUSE-COMPILE-BYTES-CONTROL", st == vr.ADMITTED, "matching compile-time bytes admit")

    s = vr.stats(root)
    check("V-REUSE-MEASURED", s["hits"] >= 3 and s["reviewer_dispatches_avoided"] == s["hits"]
          and s["source_chars_avoided"] > 0 and s["tokens_saved"] is None,
          f"what a hit avoided is measured, tokens are not claimed: {s}")
    print(f"REUSE_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
