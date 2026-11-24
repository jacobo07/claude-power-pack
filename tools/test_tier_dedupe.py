"""V-TD-* gate: tier-note dedupe (T3-CT W5c, modules/gsd_x/cli.py::advisory + _last_tier_on_record).

A non-floor tier note (~300 chars) was re-sent in full on every prompt. With a transcript on record, a prompt whose
verdict equals the LATEST delivered tier note (after the last compact boundary) gets a one-line form instead.
Both poles, the compact boundary, the UNKNOWN cases, the kill switch, the tail window and a real-text round trip.
Run from the repo root: python tools/test_tier_dedupe.py
"""
import json, os, sys, tempfile, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TMP = Path(tempfile.mkdtemp(prefix="v-td-"))
os.environ.pop("CPP_OFFER_DEDUPE", None)

from modules.gsd_x import cli, tier  # noqa: E402

FAILS = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  " + detail))
    if not ok:
        FAILS.append(name)


def transcript(rows, pad=0):
    p = TMP / ("t-%s.jsonl" % uuid.uuid4().hex[:8])
    with p.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
        if pad:
            filler = json.dumps({"type": "assistant", "message": {"content": "x" * 1000}}) + "\n"
            for _ in range(pad // len(filler) + 1):
                fh.write(filler)
    return str(p)


def att(text):
    return {"type": "attachment", "attachment": {"type": "hook_additional_context", "content": [text]}}


def quoted(text):
    return {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "content": text}]}}


BOUNDARY = {"type": "system", "subtype": "compact_boundary"}
DEEP = tier.TierVerdict(tier="DEEP", drivers=[("cap.a", "VIOLATED")])
FOREN = tier.TierVerdict(tier="FORENSIC", drivers=[("cap.b", "VIOLATED")])
ABST = tier.TierVerdict(tier=tier.ABSTAIN, missing=["needs the diff"])
FLOOR = tier.TierVerdict(tier="LIGHT", by_floor=True)
FULL_DEEP = cli.advisory(DEEP)
FULL_ABST = cli.advisory(ABST)


def pl(tp):
    return {"session_id": "v-td", "transcript_path": tp}


def short(s):
    return "same tier as stated earlier" in s and len(s) < 200


def main():
    check("V-TD-KEY-ROUNDTRIP", cli._tier_key(FULL_DEEP) == "DEEP" and cli._tier_key(FULL_ABST) == "NOT MEASURED",
          "%r %r" % (cli._tier_key(FULL_DEEP), cli._tier_key(FULL_ABST)))
    ladder = ("- ExecutionOS Lite tier: LIGHT (lookup/fix) | STANDARD (1-5 files) | DEEP (5+ files) | "
              "FORENSIC (prod risk). Default LIGHT.")  # power-pack-reminder.js, same prefix, not a verdict
    check("V-TD-LADDER-NOT-VERDICT", cli._tier_key(ladder) == "" and cli._tier_key(FULL_DEEP + "\n" + ladder) == "DEEP",
          "the reminder's ladder line must not parse as a verdict")
    check("V-TD-LADDER-ROW-SKIPPED", short(cli.advisory(DEEP, pl(transcript([att(FULL_DEEP), att(ladder)])))),
          "a later reminder row must not hide the delivered note")
    same = cli.advisory(DEEP, pl(transcript([att(FULL_DEEP)])))
    check("V-TD-SAME-SHORT", short(same) and cli._tier_key(same) == "DEEP", same)
    check("V-TD-CHAIN", short(cli.advisory(DEEP, pl(transcript([att(FULL_DEEP), att(same)])))), "short after short")
    check("V-TD-CHANGED-FULL", cli.advisory(FOREN, pl(transcript([att(FULL_DEEP)]))) == cli.advisory(FOREN),
          "a changed verdict must get the full note")
    check("V-TD-LATEST-WINS", cli.advisory(DEEP, pl(transcript([att(FULL_DEEP), att(cli.advisory(FOREN))])))
          == FULL_DEEP, "DEEP after FORENSIC is a change")
    check("V-TD-ABSTAIN-SHORT", short(cli.advisory(ABST, pl(transcript([att(FULL_ABST)])))), "abstain repeat")
    check("V-TD-COMPACT-FULL", cli.advisory(DEEP, pl(transcript([att(FULL_DEEP), BOUNDARY]))) == FULL_DEEP,
          "a compact boundary since the note must re-send it")
    check("V-TD-QUOTED-NOT-DELIVERY", cli.advisory(DEEP, pl(transcript([quoted(FULL_DEEP)]))) == FULL_DEEP,
          "a tool result quoting the note is not delivery")
    check("V-TD-NO-TRANSCRIPT-FULL", cli.advisory(DEEP, {"session_id": "x"}) == FULL_DEEP
          and cli.advisory(DEEP, pl(str(TMP / "missing.jsonl"))) == FULL_DEEP, "UNKNOWN keeps the full note")
    check("V-TD-FLOOR-SILENT", cli.advisory(FLOOR, pl(transcript([att(FULL_DEEP)]))) == "", "floor says nothing")
    # tail window: the note sits before the last TIER_TAIL_BYTES -> unseen -> UNKNOWN -> full
    big = transcript([att(FULL_DEEP)], pad=cli.TIER_TAIL_BYTES + 200_000)
    check("V-TD-TAIL-UNSEEN-FULL", cli._last_tier_on_record(pl(big)) is None and cli.advisory(DEEP, pl(big)) == FULL_DEEP,
          "a note outside the tail window cannot be claimed")
    big2 = transcript([quoted("x")], pad=cli.TIER_TAIL_BYTES + 200_000)
    with open(big2, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(att(FULL_DEEP)) + "\n")
    check("V-TD-TAIL-SEEN-SHORT", short(cli.advisory(DEEP, pl(big2))), "a note inside the tail window counts")
    os.environ["CPP_OFFER_DEDUPE"] = "0"
    try:
        check("V-TD-KILL-SWITCH", cli.advisory(DEEP, pl(transcript([att(FULL_DEEP)]))) == FULL_DEEP, "switch off")
    finally:
        os.environ.pop("CPP_OFFER_DEDUPE", None)
    print("V-TD: %s" % ("ALL PASS" if not FAILS else "%d FAIL" % len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
