"""V-CEPS-DRAFT gates: distribute() stages UKDL entries as drafts (E4).

The tracked UKDL file changes only through promote_ukdl_draft(). Every path
under test is redirected into a tmpdir; the real UKDL file is only hashed.
"""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ceps  # noqa: E402

passes = 0
fails = 0


def check(gate, cond, evidence):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {evidence}")
    else:
        fails += 1
        print(f"FAIL {gate}: {evidence}")


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def _ukdl_drafts():
    return [d for d in ceps.list_drafts() if d.get("kind") == ceps.UKDL_DRAFT_KIND]


def main():
    real_before = _sha(ceps.UKDL_PATH)
    saved = (ceps.UKDL_PATH, ceps.DRAFTS_DIR, ceps.LESSONS_PATH)
    with tempfile.TemporaryDirectory() as tmp:
        td = Path(tmp)
        try:
            # Arrange
            ukdl = td / "ukdl.md"
            ukdl.write_bytes(b"# UKDL\n\n- seed rule\n")
            before = ukdl.read_bytes()
            ceps.UKDL_PATH = ukdl
            ceps.DRAFTS_DIR = td / "drafts"
            ceps.LESSONS_PATH = td / "lessons.md"
            event = {"id": "ceps-e4test01", "category": "logic", "subsystem": "e4",
                     "ts": "2026-10-07T00:00:00Z", "root_cause": "rc",
                     "prevention_rule": "stage before promote",
                     "pattern_signature": "sig", "confidence": "high",
                     "auto_test_eligible": False}
            # Act
            res = ceps.distribute(event)
            drafts = _ukdl_drafts()
            # Assert
            check("V-CEPS-DRAFT-UKDL-BYTES-UNCHANGED", ukdl.read_bytes() == before,
                  f"len {len(before)} -> {len(ukdl.read_bytes())}")
            check("V-CEPS-DRAFT-ADDED",
                  len(drafts) == 1 and drafts[0]["event_id"] == event["id"]
                  and event["id"] in drafts[0]["ukdl_line"],
                  json.dumps(drafts)[:200])
            check("V-CEPS-DRAFT-RESULT",
                  bool(drafts) and res.get("ukdl") is True
                  and res.get("ukdl_draft") == drafts[0]["draft_id"], json.dumps(res))
            check("V-CEPS-DRAFT-CONFIRM-REFUSES",
                  bool(drafts) and ceps.confirm_draft(drafts[0]["draft_id"]) is None,
                  "confirm_draft on a UKDL draft returns None")
            # Control: promotion is the one path that writes the tracked file.
            got = ceps.promote_ukdl_draft(drafts[0]["draft_id"]) if drafts else None
            text = ukdl.read_text(encoding="utf-8")
            check("V-CEPS-DRAFT-PROMOTE-WRITES",
                  got is not None and bool(drafts) and drafts[0]["ukdl_line"] in text
                  and not _ukdl_drafts(), f"promoted={got is not None}")

            # Migration: two CEPS lines and one human line added over HEAD.
            head = "# UKDL\n\n- rule A\n"
            work = (head + "\n- [logic/foo] `ceps-abc` -- do x\n"
                    + "\n- a human note\n" + "\n- [runtime/bar] `ceps-def` -- do y\n")
            mig = td / "mig.md"
            mig.write_bytes(work.encode("utf-8"))
            ceps.DRAFTS_DIR = td / "drafts2"
            dry = ceps.migrate_pending_ukdl(mig, head_text=head)
            check("V-CEPS-MIGRATE-DRYRUN-NOOP",
                  mig.read_bytes() == work.encode("utf-8") and not ceps.list_drafts()
                  and dry["ceps_shaped"] == 2 and dry["moved"] == 0, json.dumps(dry))
            app = ceps.migrate_pending_ukdl(mig, head_text=head, apply=True)
            lines = sorted(d["ukdl_line"] for d in _ukdl_drafts())
            check("V-CEPS-MIGRATE-MOVES-ONLY-CEPS",
                  mig.read_bytes().decode("utf-8") == head + "\n- a human note\n"
                  and lines == ["- [logic/foo] `ceps-abc` -- do x",
                                "- [runtime/bar] `ceps-def` -- do y"]
                  and app["moved"] == 2, json.dumps(app))
            # A committed CEPS line in a CRLF checkout is not "added".
            head2 = "# U\n- [logic/old] `ceps-old` -- kept\n"
            mig2 = td / "mig2.md"
            mig2.write_bytes(head2.replace("\n", "\r\n").encode("utf-8"))
            b2 = mig2.read_bytes()
            r2 = ceps.migrate_pending_ukdl(mig2, head_text=head2, apply=True)
            check("V-CEPS-MIGRATE-COMMITTED-UNTOUCHED",
                  mig2.read_bytes() == b2 and r2["ceps_shaped"] == 0, json.dumps(r2))
        finally:
            ceps.UKDL_PATH, ceps.DRAFTS_DIR, ceps.LESSONS_PATH = saved
    check("V-CEPS-DRAFT-REAL-UKDL-UNTOUCHED", _sha(ceps.UKDL_PATH) == real_before,
          str(ceps.UKDL_PATH))
    print(f"CEPS_DRAFTS_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
