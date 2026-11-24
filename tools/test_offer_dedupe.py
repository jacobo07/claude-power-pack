"""V-OD-* gate: UserPromptSubmit offer dedupe (T3-CT W4(b), modules/gsd_x/cli.py::_delivered).

The Tower and family blocks are offered on a session's first MAX_OFFERS prompts. With a transcript on record, a later
offer stops once an earlier copy was DELIVERED (a hook_additional_context attachment row). Driven from both poles,
plus a source mutant (any line quoting the marker counts as delivery) that must go red.
Run from the repo root: python tools/test_offer_dedupe.py
"""
import json, os, sys, tempfile, types, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TMP = Path(tempfile.mkdtemp(prefix="v-od-"))
os.environ["CPP_TOWER_STATE_DIR"] = str(TMP / "tower")   # never the live offer counters / consumption ledger
os.environ.pop("CPP_OFFER_DEDUPE", None)

from modules.gsd_x import cli  # noqa: E402

FAILS = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  " + detail))
    if not ok:
        FAILS.append(name)


def transcript(rows):
    p = TMP / ("t-%s.jsonl" % uuid.uuid4().hex[:8])
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return str(p)


def att(text):
    return {"type": "attachment", "attachment": {"type": "hook_additional_context", "content": [text],
                                                 "hookName": "UserPromptSubmit", "hookEvent": "UserPromptSubmit"}}


def quoted(text):  # a tool result quoting the same words: NOT a delivery
    return {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "content": text}]}}


def pl(tp=None):
    d = {"session_id": "v-od-" + uuid.uuid4().hex[:10], "cwd": str(ROOT)}
    if tp is not None:
        d["transcript_path"] = tp
    return d


def run(mod):
    tower = mod.inherited_block(pl(transcript([])))
    check("V-OD-PRECONDITION tower lessons exist for this repo", bool(tower), "empty block: gate cannot judge")
    if not tower:
        return
    check("V-OD-FIRST empty transcript -> offered", bool(mod.inherited_block(pl(transcript([]))))),
    check("V-OD-DELIVERED attachment on record -> not re-offered",
          mod.inherited_block(pl(transcript([att(tower)]))) == "")
    check("V-OD-QUOTE tool_result quoting the block -> still offered",
          bool(mod.inherited_block(pl(transcript([quoted(tower)])))))
    check("V-OD-UNKNOWN no transcript_path -> MAX_OFFERS behaviour (offered)", bool(mod.inherited_block(pl())))
    check("V-OD-MISSING transcript path that does not exist -> offered",
          bool(mod.inherited_block(pl(str(TMP / "nope.jsonl")))))
    os.environ["CPP_OFFER_DEDUPE"] = "0"
    try:
        check("V-OD-KILL switch 0 -> offered even when delivered",
              bool(mod.inherited_block(pl(transcript([att(tower)])))))
    finally:
        os.environ.pop("CPP_OFFER_DEDUPE", None)
    # cap still holds without a transcript: MAX_OFFERS offers, then none
    p = pl()
    seq = [bool(mod.inherited_block(p)) for _ in range(mod.MAX_OFFERS + 1)]
    check("V-OD-CAP MAX_OFFERS unchanged when unobservable", seq == [True] * mod.MAX_OFFERS + [False], str(seq))

    prompt = "build a landing page website for my saas product with a pricing section and signup"
    fam = mod.family_block(prompt, pl(transcript([])))
    check("V-OD-FAM-PRECONDITION a family matches the web prompt", bool(fam), "no family block: gate cannot judge")
    if fam:
        check("V-OD-FAM-DELIVERED family block on record -> not re-offered",
              mod.family_block(prompt, pl(transcript([att(fam)]))) == "")
        check("V-OD-FAM-QUOTE quoted family block -> still offered",
              bool(mod.family_block(prompt, pl(transcript([quoted(fam)])))))
        check("V-OD-FAM-OTHER tower block on record does not suppress the family block",
              bool(mod.family_block(prompt, pl(transcript([att(tower)])))))


def mutant():
    """Source mutant: drop the attachment-type check -> a quoted block counts as delivered. Must go red."""
    src = (ROOT / "modules" / "gsd_x" / "cli.py").read_text(encoding="utf-8")
    needle = 'if marker in line and "hook_additional_context" in line:'
    assert needle in src, "mutant anchor missing"
    mutated = src.replace(needle, "if marker in line:\n                    return True\n                if False:", 1)
    m = types.ModuleType("cli_mutant")
    m.__file__ = str(ROOT / "modules" / "gsd_x" / "cli.py")
    exec(compile(mutated, m.__file__, "exec"), m.__dict__)
    tower = m.inherited_block(pl(transcript([])))
    return bool(tower) and m.inherited_block(pl(transcript([quoted(tower)]))) == ""


run(cli)
killed = mutant()
check("V-OD-MUTANT quote-counts-as-delivery is killed by V-OD-QUOTE", killed, "mutant survived")
print("V-OD: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
