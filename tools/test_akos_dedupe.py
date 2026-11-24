"""V-AKD-* gate: AKOS block re-send + duplicate-unit dedupe (T3-CT W5d).

(1) select_units drops a unit whose (domain, title) is already selected and backfills the slot.
(2) _akos_on_record: True only for a delivered hook_additional_context row with no compact since.
(3) The real injector wrapper: TTL expired + block on record -> nothing appended; not on record -> appended.
Run from the repo root: python tools/test_akos_dedupe.py
"""
import json, os, sys, tempfile, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tools"))
TMP = Path(tempfile.mkdtemp(prefix="v-akd-"))
os.environ.pop("CPP_OFFER_DEDUPE", None); os.environ.pop("CLAUDEPP_AKOS_DISABLE", None)
from modules.akos_knowledge.akos import AkosUnit, select_units  # noqa: E402
from modules.cognitive_os import co_12_telemetry as co12  # noqa: E402
import jit_skill_loader as jit  # noqa: E402

jit.STATE_DIR = TMP / "state"
co12._default_state_dir = lambda: TMP / "co12"   # same isolation as test_akos_integration: no live telemetry writes
FAILS = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  " + detail))
    if not ok:
        FAILS.append(name)


def transcript(rows):
    p = TMP / ("t-%s.jsonl" % uuid.uuid4().hex[:8])
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return str(p)


BLOCK = jit._AKOS_MARK + ": saas)\nBusiness knowledge ...\n(AKOS knowledge injector; ...)"
ATT = {"type": "attachment", "attachment": {"type": "hook_additional_context", "content": [BLOCK]}}
QUOTE = {"type": "user", "message": {"content": [{"type": "tool_result", "content": BLOCK}]}}
BOUNDARY = {"type": "system", "subtype": "compact_boundary"}


def main():
    u = lambda d, i, t, s="": AkosUnit(domain=d, index=i, kind="prompt", title=t, snippet=s)  # noqa: E731
    units = [u("saas", 1, "Sell X", "quote"), u("saas", 2, "Sell X"), u("saas", 3, "Other"), u("saas", 4, "Third"),
             u("scaling", 1, "Ops"), u("scaling", 2, "Ops")]
    sel = select_units(units, ["saas", "scaling"], max_units=6, per_domain=3)
    titles = [(x.domain, x.title) for x in sel]
    check("V-AKD-NO-DUP-TITLE", len(titles) == len(set(titles)), str(titles))
    check("V-AKD-BACKFILL", titles == [("saas", "Sell X"), ("saas", "Other"), ("saas", "Third"), ("scaling", "Ops")]
          and sel[0].snippet == "quote", str(titles))
    check("V-AKD-CAPS", len(select_units(units, ["saas"], max_units=2, per_domain=3)) == 2, "max_units")

    check("V-AKD-ON-RECORD", jit._akos_on_record({"transcript_path": transcript([ATT])}) is True, "delivered")
    check("V-AKD-COMPACT-CLEARS", jit._akos_on_record({"transcript_path": transcript([ATT, BOUNDARY])}) is False, "")
    check("V-AKD-AFTER-COMPACT", jit._akos_on_record({"transcript_path": transcript([ATT, BOUNDARY, ATT])}) is True, "")
    check("V-AKD-QUOTED-NOT-DELIVERY", jit._akos_on_record({"transcript_path": transcript([QUOTE])}) is False, "")
    check("V-AKD-NO-TRANSCRIPT", jit._akos_on_record({}) is None
          and jit._akos_on_record({"transcript_path": str(TMP / "none.jsonl")}) is None, "")
    os.environ["CPP_OFFER_DEDUPE"] = "0"
    try:
        check("V-AKD-KILL-SWITCH", jit._akos_on_record({"transcript_path": transcript([ATT])}) is None, "")
    finally:
        os.environ.pop("CPP_OFFER_DEDUPE", None)

    pad = json.dumps({"type": "assistant", "message": {"content": "x" * 1000}}) + "\n"
    n = jit._AKOS_TAIL_BYTES // len(pad) + 200
    old = Path(transcript([ATT])); old.write_text(old.read_text(encoding="utf-8") + pad * n, encoding="utf-8")
    check("V-AKD-TAIL-UNSEEN", jit._akos_on_record({"transcript_path": str(old)}) is None, "outside window -> None")
    late = Path(transcript([])); late.write_text(pad * n + json.dumps(ATT) + "\n", encoding="utf-8")
    check("V-AKD-TAIL-SEEN", jit._akos_on_record({"transcript_path": str(late)}) is True, "inside window -> True")

    # the real wrapper, on this repo's real brief; a fresh sid each time so the TTL is expired
    wrapped = jit._akos_knowledge_inject(lambda d: {"additionalContext": "base"})

    def run(tp):
        d = {"session_id": "v-akd-" + uuid.uuid4().hex[:10], "cwd": str(ROOT), "prompt": "x"}
        if tp:
            d["transcript_path"] = tp
        return wrapped(d).get("additionalContext", "")

    fresh = run(transcript([]))
    check("V-AKD-WRAPPER-SENDS", jit._AKOS_MARK in fresh, "no copy on record -> block appended (brief must exist)")
    check("V-AKD-WRAPPER-SUPPRESSES", jit._AKOS_MARK not in run(transcript([ATT])), "copy on record -> nothing")
    check("V-AKD-WRAPPER-AFTER-COMPACT", jit._AKOS_MARK in run(transcript([ATT, BOUNDARY])), "compact -> TTL path")
    check("V-AKD-WRAPPER-UNKNOWN", jit._AKOS_MARK in run(None), "no transcript -> old behaviour")
    print("V-AKD: %s" % ("ALL PASS" if not FAILS else "%d FAIL" % len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
