"""V-ABA-*: the A->B->A hole in tools/evidence_bundle.py (R05).

A review ticket binds the artifact bytes at ISSUE time. A concurrent writer who changes A to B and back to
A between the ticket and the reviewer's read leaves identical bytes, so the review of B passed as a review
of A. The ticket now also carries a stat journal (a live read is refused when mtime/size/inode moved) and a
read-only snapshot of the ticketed bytes (a reviewer who echoes the snapshot line read the frozen copy and
is immune). Hermetic: a temp root, no network.
    python tools/test_evidence_bundle_aba.py
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import evidence_bundle as eb  # noqa: E402

passes = fails = 0
REVIEWER = {"agent": "pp-code-reviewer", "model": "claude-sonnet-5", "effort": "default"}
OK_REPLY = "```json\n{\"findings\": []}\n```"
A = "x = 1\n"
B = "x = 2  # B\n"


def check(gate: str, cond: bool, ev: object = "") -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {ev}")


def put(root: Path, text: str, mtime: int) -> None:
    """Write with an explicit mtime: Windows timestamp granularity must not decide a case."""
    p = root / "art.py"
    p.write_text(text, encoding="utf-8")
    mtime = 1_000_000_000_000_000_000 + (mtime - 1_000_000_000_000_000_000) * 1_000_000   # steps of 1 ms
    os.utime(p, ns=(mtime, mtime))


def review(root: Path, nonce: str, snapshot: bool) -> dict:
    reply = eb.ticket_line(nonce) + "\n" + (eb.snapshot_line(nonce) + "\n" if snapshot else "") + OK_REPLY
    rel, _ = eb.write_review(root, "p", "t", reply, REVIEWER, ["art.py"], [])
    return json.loads((root / rel).read_text(encoding="utf-8"))


def fresh() -> Path:
    root = Path(tempfile.mkdtemp(prefix="aba_t_"))
    put(root, A, 1_000_000_000_000_000_000)
    (root / "other.py").write_text("y = 0\n", encoding="utf-8")
    return root


def rm(root: Path) -> None:
    for f in root.rglob("*"):
        if f.is_file():
            try:
                os.chmod(f, stat.S_IWRITE)
            except OSError:
                pass
    shutil.rmtree(root, ignore_errors=True)


def main() -> int:
    tmp = fresh()
    try:
        roots = [tmp]
        # --- control: a live read with nothing moved is a pass
        _, n = eb.ticket(tmp, "p", "t", ["art.py"])
        r = review(tmp, n, snapshot=False)
        check("V-ABA-CONTROL-LIVE-READ", r["verdict"] == "pass", r["intake"])

        # --- A -> B -> A rewritten in place: bytes equal, mtime moved
        _, n = eb.ticket(tmp, "p", "t", ["art.py"])
        put(tmp, B, 1_000_000_000_000_000_001)
        put(tmp, A, 1_000_000_000_000_000_002)
        r = review(tmp, n, snapshot=False)
        check("V-ABA-LIVE-REWRITE-STALE", r["verdict"] == "fail" and "art.py" in r["intake"]["reason"],
              r["intake"])

        # --- A -> B -> A through a replace: a new inode (the mtime is put back to the ticketed one)
        put(tmp, A, 1_000_000_000_000_000_000)
        _, n = eb.ticket(tmp, "p", "t", ["art.py"])
        (tmp / "art.new").write_text(A, encoding="utf-8")      # both files exist, so the inodes differ
        os.utime(tmp / "art.new", ns=(1_000_000_000_000_000_000,) * 2)
        os.replace(tmp / "art.new", tmp / "art.py")
        ino_now = (tmp / "art.py").stat().st_ino
        moved_ino = ino_now != json.loads(eb._ticket_path(tmp, "p", "t").read_text(encoding="utf-8"))["journal"][0]["ino"]
        r = review(tmp, n, snapshot=False)
        check("V-ABA-REPLACE-NEW-INODE", moved_ino and r["verdict"] == "fail",
              {"inode_moved": moved_ino, "verdict": r["verdict"]})

        # --- snapshot read: survives the same A -> B -> A, and the receipt names A
        put(tmp, A, 1_000_000_000_000_000_000)
        _, n = eb.ticket(tmp, "p", "t", ["art.py"])
        put(tmp, B, 1_000_000_000_000_000_001)
        put(tmp, A, 1_000_000_000_000_000_002)
        r = review(tmp, n, snapshot=True)
        check("V-ABA-SNAPSHOT-READ-SURVIVES", r["verdict"] == "pass", r["intake"])

        # --- the snapshot is the ticketed bytes even while the live file is B
        _, n = eb.ticket(tmp, "p", "t", ["art.py"])
        snap_file = tmp / eb.snapshot_root(tmp, "p", "t") / "art.py"
        put(tmp, B, 1_000_000_000_000_000_003)
        check("V-ABA-SNAPSHOT-STAYS-A", snap_file.read_text(encoding="utf-8") == A
              and not os.access(snap_file, os.W_OK), {"snapshot": snap_file.read_text(encoding="utf-8")})

        # --- a tampered snapshot is refused
        os.chmod(snap_file, stat.S_IWRITE)
        snap_file.write_text(B, encoding="utf-8")
        r = review(tmp, n, snapshot=True)
        check("V-ABA-SNAPSHOT-TAMPERED", r["verdict"] == "fail" and "snapshot" in r["intake"]["reason"], r["intake"])

        # --- final bytes B: the snapshot review of A is stale for the collector (hash of B != hash of A)
        put(tmp, A, 1_000_000_000_000_000_000)
        _, n = eb.ticket(tmp, "p", "t", ["art.py"])
        put(tmp, B, 1_000_000_000_000_000_004)
        r = review(tmp, n, snapshot=True)
        seen = r["artifacts"][0]["sha256"]
        now = eb._proofs(tmp, ["art.py"])[0]["sha256"]
        check("V-ABA-FINAL-B-STALE", r["verdict"] == "pass" and seen != now,
              "the receipt keeps A's hash, so the collector compares it to B and fails the review as stale")

        # --- a file nobody ticketed does not matter
        put(tmp, A, 1_000_000_000_000_000_000)
        _, n = eb.ticket(tmp, "p", "t", ["art.py"])
        (tmp / "other.py").write_text("y = 99\n", encoding="utf-8")
        r = review(tmp, n, snapshot=False)
        check("V-ABA-UNREVIEWED-FILE-IRRELEVANT", r["verdict"] == "pass", r["intake"])

        # --- an old ticket (no journal) fails closed on a live read
        tp = eb._ticket_path(tmp, "p", "t")
        t = json.loads(tp.read_text(encoding="utf-8"))
        t.pop("journal")
        tp.write_text(json.dumps(t), encoding="utf-8")
        r = review(tmp, t["nonce"], snapshot=False)
        check("V-ABA-OLD-TICKET-FAILS-CLOSED", r["verdict"] == "fail" and "journal" in r["intake"]["reason"],
              r["intake"])

        # --- the public ticket API is unchanged
        out = eb.ticket(tmp, "p", "t", ["art.py"])
        check("V-ABA-TICKET-API-STABLE", isinstance(out, tuple) and len(out) == 2
              and isinstance(out[0], str) and isinstance(out[1], str) and len(out[1]) == 24, out[0])
    finally:
        rm(tmp)
    print(f"EVB_ABA_PASS={passes}/{passes + fails}  threshold=10/10")
    return 0 if fails == 0 and passes == 10 else 1


if __name__ == "__main__":
    sys.exit(main())
