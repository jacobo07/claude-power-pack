"""V-SPD-* gate: no active-spec re-send while the same copy is in context (T3-CT W5e).

Drives the real JIT run() (decorators unwrapped) on a temp project with a vault/specs spec, a fresh
session id per case so the 2 h state TTL is always expired, and a transcript built from the block the
hook itself emitted. Both poles: suppressed only for the exact same block, delivered, no compact since.
Run from the repo root: python tools/test_spec_dedupe.py
"""
import inspect, json, os, sys, tempfile, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tools"))
TMP = Path(tempfile.mkdtemp(prefix="v-spd-"))
os.environ.pop("CPP_OFFER_DEDUPE", None)
import jit_skill_loader as jit  # noqa: E402

jit.STATE_DIR = TMP / "state"
RUN = inspect.unwrap(jit.run)
PROJ = TMP / "proj"
SPEC = PROJ / "vault" / "specs" / "w5e-probe.md"
HEAD = "=== ACTIVE PROJECT SPEC: "
FAILS = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  " + detail))
    if not ok:
        FAILS.append(name)


def transcript(rows):
    p = TMP / ("t-%s.jsonl" % uuid.uuid4().hex[:8])
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return str(p)


def att(ctx):
    return {"type": "attachment", "attachment": {"type": "hook_additional_context", "content": [ctx]}}


def run(tp):
    d = {"session_id": "v-spd-" + uuid.uuid4().hex[:10], "cwd": str(PROJ), "prompt": "x"}
    if tp:
        d["transcript_path"] = tp
    return RUN(d).get("additionalContext", "") or ""


def main():
    SPEC.parent.mkdir(parents=True)
    SPEC.write_text("# W5e probe spec\n\nAC-1: the spec is sent once per context.\n", encoding="utf-8")
    first = run(None)
    check("V-SPD-SENDS-UNKNOWN", HEAD in first, "no transcript -> old behaviour (spec sent)")
    if HEAD not in first:
        print("V-SPD: %d FAIL" % len(FAILS)); return 1
    delivered = att("other hook text\n\n" + first)
    boundary = {"type": "system", "subtype": "compact_boundary"}
    quote = {"type": "user", "message": {"content": [{"type": "tool_result", "content": first}]}}

    again = run(transcript([delivered]))
    check("V-SPD-SUPPRESSED", HEAD not in again, "same block on record -> not re-sent")
    check("V-SPD-POINTER", "unchanged since it was injected" in again, repr(again[:200]))
    check("V-SPD-COMPACT-SENDS", HEAD in run(transcript([delivered, boundary])), "compact since -> sent")
    check("V-SPD-AFTER-COMPACT", HEAD not in run(transcript([delivered, boundary, delivered])), "")
    check("V-SPD-QUOTED-SENDS", HEAD in run(transcript([quote])), "a tool_result quote is not a delivery")
    os.environ["CPP_OFFER_DEDUPE"] = "0"
    try:
        check("V-SPD-KILL-SWITCH", HEAD in run(transcript([delivered])), "")
    finally:
        os.environ.pop("CPP_OFFER_DEDUPE", None)

    # an edited spec is a new block: the old copy on record must not suppress it
    SPEC.write_text("# W5e probe spec\n\nAC-1: edited.\n", encoding="utf-8")
    os.utime(SPEC, None)
    for f in jit.STATE_DIR.glob("jit-spec-*.json"):
        f.unlink()                                    # the 5 min spec cache is keyed on mtime; drop it outright
    edited = run(transcript([delivered]))
    check("V-SPD-EDITED-SENDS", HEAD in edited and "AC-1: edited." in edited, repr(edited[:200]))
    print("V-SPD: %s" % ("ALL PASS" if not FAILS else "%d FAIL" % len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
