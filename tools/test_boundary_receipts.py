#!/usr/bin/env python
"""V-BR-* gates for tools/boundary_receipts.py, driven by small synthetic transcripts."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import boundary_receipts as br  # noqa: E402

passes = fails = 0
PACKET = "---\nfingerprint: x\nunit: U\n---\n\n## Claims\n\n- c1: first [gates: G1]\n- c2: second [gates: G2]\n\n" \
         "## Context\n\n- src/*.ts\n\n## Acceptance\n\n- pytest tests/test_a.py\n"
USAGE = {"input_tokens": 10, "cache_read_input_tokens": 90, "cache_creation_input_tokens": 0, "output_tokens": 5}


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


class T:
    """Synthetic transcript builder: one assistant call (+ its results) per add()."""

    def __init__(self):
        self.lines, self.n = [], 0

    def add(self, tools=(), text="", dup_line=False):
        self.n += 1
        mid, ts = f"msg_{self.n}", f"2026-10-06T10:00:{self.n:02d}Z"
        blocks = [{"type": "text", "text": text}] if text else []
        results = []
        for i, (name, inp, result, *err) in enumerate(tools):
            tid = f"t{self.n}_{i}"
            blocks.append({"type": "tool_use", "id": tid, "name": name, "input": inp})
            results.append({"type": "tool_result", "tool_use_id": tid, "content": result, "is_error": bool(err and err[0])})
        row = {"type": "assistant", "timestamp": ts,
               "message": {"id": mid, "model": "m", "usage": USAGE, "content": blocks}}
        self.lines.append(json.dumps(row))
        if dup_line:
            self.lines.append(json.dumps(row))
        if results:
            self.lines.append(json.dumps({"type": "user", "timestamp": ts, "message": {"content": results}}))

    def run(self, packet=PACKET):
        d = Path(tempfile.mkdtemp(prefix="br-test-"))
        (d / "s.jsonl").write_text("\n".join(self.lines), encoding="utf-8")
        (d / "p.md").write_text(packet, encoding="utf-8")
        calls, results = br.read_transcripts(br.transcript_paths(d / "s.jsonl"))
        return br.build_receipts(calls, results, br.load_packet(d / "p.md"))


def count(receipts, kind):
    return sum(1 for r in receipts for e in r["events"] if e["kind"] == kind)


def bash(cmd, result, err=False):
    return ("Bash", {"command": cmd}, result, err)


PROJ = Path(r"C:\Users\User\.claude\projects\C--Users-User-Apps-io-ql-story")
FIX_F = PROJ / "22b08816-e7ad-43d8-829c-b4f6500d1105.jsonl"
FIX_T = next(iter(sorted(PROJ.glob("886279a8*.jsonl"))), PROJ / "886279a8.jsonl")
PACKETS = Path(r"C:\Users\User\Apps\io-ql-story\.planning\workstreams\ql-story-tour\packets")


def png_bytes(w, h):
    import struct
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I4sIIBBBBB", 13, b"IHDR", w, h, 8, 2, 0, 0, 0) + b"\0" * 20


def jpg_bytes(w, h):
    import struct
    # SOI, an APP0 segment, then SOF0 (precision 8, height, width, 1 component)
    return b"\xff\xd8" + b"\xff\xe0" + struct.pack(">H", 6) + b"JFIF" + \
        b"\xff\xc0" + struct.pack(">HBHHB", 11, 8, h, w, 1) + b"\x01\x11\x00" + b"\xff\xd9"


def img_block(data, media):
    import base64
    return {"type": "image", "source": {"type": "base64", "media_type": media,
                                        "data": base64.b64encode(data).decode()}}


def raw_image_truth(main: Path):
    """Independent pass over the raw transcript: image blocks inside tool results, by tool_use_id, no module code."""
    import base64
    import hashlib
    paths = [main] + sorted((main.with_suffix("") / "subagents").glob("*.jsonl"))
    seen, hashes = set(), []
    for p in paths:
        for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                row = json.loads(raw)
            except ValueError:
                continue
            msg = row.get("message") if isinstance(row, dict) else None
            content = msg.get("content") if isinstance(msg, dict) else None
            for b in content if isinstance(content, list) else []:
                if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id") not in seen:
                    seen.add(b.get("tool_use_id"))
                    inner = b.get("content")
                    for x in inner if isinstance(inner, list) else []:
                        if isinstance(x, dict) and x.get("type") == "image":
                            hashes.append(hashlib.sha256(base64.b64decode(x["source"]["data"])).hexdigest())
    return hashes


def real_receipts(transcript: Path, packet: Path):
    calls, results = br.read_transcripts(br.transcript_paths(transcript))
    return br.build_receipts(calls, results, br.load_packet(packet))


def image_checks() -> None:
    # synthetic: dimensions come from the bytes' header, model from the call, identity from the data
    r = T()
    r.add([("Read", {"file_path": "a.png"}, [img_block(png_bytes(640, 480), "image/png")]),
           ("Read", {"file_path": "b.jpg"}, [img_block(jpg_bytes(1800, 1300), "image/jpeg")])])
    rc = r.run()
    ev = [e for x in rc for e in x["events"] if e["kind"] == "image_new"]
    got = sorted((e["media_type"], e["width"], e["height"]) for e in ev)
    check("V-BR-IMAGE-EVENT-HEADER-DIMENSIONS", got == [("image/jpeg", 1800, 1300), ("image/png", 640, 480)], str(got))
    check("V-BR-IMAGE-EVENT-CARRIES-MODEL-AND-COUNT", all(e["model"] == "m" for e in ev) and rc[0]["images"] == 2,
          f"{[e.get('model') for e in ev]} images={rc[0].get('images')}")
    import hashlib
    check("V-BR-IMAGE-IDENTITY-IS-DATA-HASH", {e["key"] for e in ev} ==
          {hashlib.sha256(png_bytes(640, 480)).hexdigest()[:12], hashlib.sha256(jpg_bytes(1800, 1300)).hexdigest()[:12]})
    # control: text-only transcript yields no image event and a zero image count
    t = T()
    t.add([("Read", {"file_path": "a"}, "plain text")])
    rt = t.run()
    check("V-BR-TEXT-ONLY-ZERO-IMAGE-EVENTS-CONTROL", count(rt, "image_new") == 0 and rt[0]["images"] == 0)
    # the same image twice is one event and one duplicate, but two images in the call counts
    d = T()
    same = [img_block(png_bytes(10, 10), "image/png")]
    d.add([("Read", {"file_path": "a.png"}, same), ("Read", {"file_path": "a2.png"}, same)])
    d.add([("Read", {"file_path": "a.png"}, same)])
    rd = d.run()
    check("V-BR-IMAGE-DUPLICATES-COUNT-AS-DUPLICATES", count(rd, "image_new") == 1 and sum(x["image_dups"] for x in rd) == 2
          and [x["images"] for x in rd] == [2, 1], f"{count(rd, 'image_new')} {[x['image_dups'] for x in rd]}")
    # an image result with text and a non-image-only result still keeps its text evidence
    m = T()
    m.add([("Read", {"file_path": "a"}, [{"type": "text", "text": "caption words"}, img_block(png_bytes(3, 3), "image/png")])])
    rm = m.run()
    check("V-BR-MIXED-RESULT-KEEPS-TEXT-EVIDENCE", count(rm, "evidence_new") == 1 and count(rm, "image_new") == 1)
    # an unparseable image keeps its identity and reports dimensions UNKNOWN (None), never a guess
    u = T()
    u.add([("Read", {"file_path": "x"}, [img_block(b"not an image at all", "image/webp")])])
    eu = [e for x in u.run() for e in x["events"] if e["kind"] == "image_new"]
    check("V-BR-IMAGE-UNPARSEABLE-DIMENSIONS-UNKNOWN", len(eu) == 1 and eu[0]["width"] is None and eu[0]["height"] is None, str(eu))

    # real fixtures: the module's image events equal an independent pass over the raw transcript
    for name, fix, pk in (("F", FIX_F, PACKETS / "F.md"), ("T", FIX_T, PACKETS / "T.md")):
        ok = fix.exists() and pk.exists()
        check(f"V-BR-REAL-FIXTURE-{name}-EXISTS", ok, f"{fix} {pk}")
        if not ok:
            continue
        truth = raw_image_truth(fix)
        rc = real_receipts(fix, pk)
        events = [e for x in rc for e in x["events"] if e["kind"] == "image_new"]
        total = sum(x["images"] for x in rc)
        dups = sum(x["image_dups"] for x in rc)
        check(f"V-BR-REAL-{name}-IMAGE-COUNT-EQUALS-RAW-PASS", total == len(truth) and len(events) + dups == len(truth)
              and {e["key"] for e in events} == {h[:12] for h in truth},
              f"events={len(events)} dups={dups} per-call={total} raw={len(truth)} distinct={len(set(truth))}")
        if name == "F":
            check("V-BR-REAL-F-IMAGES-ARE-8-WITH-DIMENSIONS", len(truth) == 8 and all(e["width"] and e["height"] for e in events),
                  str([(e["media_type"], e["width"], e["height"]) for e in events]))
        else:
            check("V-BR-REAL-T-TEXT-ONLY-ZERO-IMAGES-CONTROL", len(truth) == 0 and not events, f"raw={len(truth)}")


IR_PATH = Path(os.environ.get("QL_CLAIMS_IR") or r"C:\Users\User\Apps\io-ql-story\17_Businesses\QuickLease"
               r"\docs\plans\ql-story-tour\claims.json")
F_E6 = "22b08816"
WANT_F = {"orient": 1, "explore": 7, "files": 1, "runs": 0, "repairs": 0, "commit": 1, "report": 1, "images": 8}


def ir_copy(mutate=None) -> Path:
    p = Path(tempfile.mkdtemp(prefix="br-closeout-")) / "claims.json"
    if mutate:
        doc = json.loads(IR_PATH.read_text(encoding="utf-8-sig"))
        mutate(doc)
        p.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    else:
        p.write_bytes(IR_PATH.read_bytes())
    return p


def drop_f_e6(doc) -> None:
    f = next(u for u in doc["units"] if u["id"] == "F")
    f["actuals"] = [a for a in f["actuals"] if a.get("session") != F_E6]


def unit_actuals(p: Path, uid: str) -> list:
    return next(u for u in json.loads(p.read_text(encoding="utf-8-sig"))["units"] if u["id"] == uid).get("actuals") or []


def raw_processed(main: Path, through_report: bool = True) -> int:
    """Independent census: last usage row per assistant message id, input + cache + output, main transcript only,
    through the first assistant message with no tool_use (the worker's report) unless through_report is False."""
    last, order, has_tool = {}, [], {}
    for raw in main.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(raw)
        except ValueError:
            continue
        m = row.get("message") if isinstance(row, dict) else None
        if row.get("type") == "assistant" and isinstance(m, dict) and m.get("id") and m.get("usage"):
            if m["id"] not in last:
                order.append(m["id"])
            last[m["id"]] = m["usage"]
            has_tool[m["id"]] = has_tool.get(m["id"], False) or any(
                isinstance(b, dict) and b.get("type") == "tool_use" for b in (m.get("content") or []))
    if through_report:
        stop = next((i for i, k in enumerate(order) if not has_tool[k]), len(order) - 1)
        order = order[:stop + 1]
    return sum(int(last[k].get("input_tokens") or 0) + int(last[k].get("cache_read_input_tokens") or 0)
               + int(last[k].get("cache_creation_input_tokens") or 0) + int(last[k].get("output_tokens") or 0) for k in order)


def closeout_checks() -> None:
    import hashlib
    import io
    from contextlib import redirect_stdout
    import cost_to_completion as ctc
    # synthetic roles from tools alone: orient, explore, files, red run, repair, green run, commit, report
    r = T()
    r.add([("Read", {"file_path": "p"}, "packet")])
    r.add([("Read", {"file_path": "a"}, "alpha")])
    r.add([("Write", {"file_path": "C:/repo/src/a.ts", "content": "const a = 1;"}, "ok")])
    r.add([bash("pytest tests/test_a.py -q", "1 failed", True)])
    r.add([("Edit", {"file_path": "C:/repo/src/a.ts", "old_string": "1", "new_string": "2"}, "ok")])
    r.add([bash("pytest tests/test_a.py -q", "1 passed")])
    r.add([bash("git commit -m x", "[main abc] x")])
    r.add(text="done")
    rc = r.run()
    sh = br.derive_shape(rc)
    check("V-BR-SHAPE-ROLES-FROM-TOOLS", all(sh[k] == v for k, v in {"orient": 1, "explore": 1, "files": 1, "runs": 2,
          "repairs": 1, "commit": 1, "report": 1, "images": 0}.items()), str(sh))
    ok = T()
    ok.add([("Read", {"file_path": "p"}, "packet")])
    ok.add([("Write", {"file_path": "C:/repo/src/a.ts", "content": "const a = 1;"}, "ok")])
    ok.add([("Edit", {"file_path": "C:/repo/src/a.ts", "old_string": "1", "new_string": "2"}, "ok")])
    sc = br.derive_shape(ok.run())
    check("V-BR-EDIT-WITHOUT-RED-RUN-IS-NOT-A-REPAIR-CONTROL", sc["repairs"] == 0 and sc["files"] == 1, str(sc))
    check("V-BR-WALL-TIME-FROM-RECEIPT-TIMESTAMPS", br._wall_seconds(rc) == 7, str(br._wall_seconds(rc)))

    # real F epoch 6: the packet's acceptance shape, 8 images, the 14,298-token write
    if not (FIX_F.exists() and (PACKETS / "F.md").exists() and IR_PATH.exists()):
        check("V-BR-CLOSEOUT-FIXTURES-EXIST", False, f"{FIX_F} {IR_PATH}")
        return
    allf = real_receipts(FIX_F, PACKETS / "F.md")
    wf, ignored = br.worker_receipts(allf)
    shf = br.derive_shape(wf)
    check("V-BR-REAL-F-SHAPE-EQUALS-ACCEPTANCE", all(shf[k] == v for k, v in WANT_F.items()) and shf.get("write_output") == 14298,
          str(shf))
    check("V-BR-REAL-F-CALLS-AFTER-REPORT-NOT-IN-SHAPE", len(wf) == 11 and ignored == len(allf) - 11 and ignored > 0,
          f"worker={len(wf)} all={len(allf)} ignored={ignored}")
    # failure words in a grep/ls dump are not a red run: the write after it is `files`, not `repairs`
    g = T()
    g.add([("Read", {"file_path": "p"}, "packet")])
    g.add([bash("git grep -n FAILED -- src", "src/x.py:3: FAILED Traceback Error")])
    g.add([("Write", {"file_path": "C:/repo/src/a.ts", "content": "x"}, "ok")])
    check("V-BR-FAILURE-WORDS-IN-GREP-DUMP-NOT-A-RED-RUN", br.derive_shape(g.run())["repairs"] == 0
          and br.derive_shape(g.run())["files"] == 1)

    # closeout on the unmodified IR: F e6 is already recorded, so nothing is appended and no byte moves
    base = ir_copy()
    before = hashlib.sha256(base.read_bytes()).hexdigest()
    res = br.closeout(FIX_F, PACKETS / "F.md", base)
    check("V-BR-CLOSEOUT-RECORDED-SESSION-IS-NOOP", res["status"] == "already_recorded"
          and hashlib.sha256(base.read_bytes()).hexdigest() == before, res["status"])

    # on a copy without the e6 entry: appended once, earlier entries untouched, second run adds nothing
    cp = ir_copy(drop_f_e6)
    old = unit_actuals(cp, "F")
    other_before = {u["id"]: u for u in json.loads(cp.read_text(encoding="utf-8"))["units"] if u["id"] != "F"}
    res = br.closeout(FIX_F, PACKETS / "F.md", cp, epoch=6)
    new = unit_actuals(cp, "F")
    check("V-BR-CLOSEOUT-APPENDS-ONE-ENTRY-APPEND-ONLY", res["status"] == "appended" and new[:-1] == old and len(new) == len(old) + 1
          and new[-1]["session"] == F_E6 and new[-1]["epoch"] == 6 and new[-1]["calls"] == 11, str(new[-1]["shape"]))
    check("V-BR-CLOSEOUT-ENTRY-SHAPE-AND-PROCESSED", all(new[-1]["shape"][k] == v for k, v in WANT_F.items())
          and new[-1]["processed"] == raw_processed(FIX_F) and res["summary"]["processed"] == new[-1]["processed"],
          f"{new[-1]['processed']:,} raw={raw_processed(FIX_F):,}")
    other_after = {u["id"]: u for u in json.loads(cp.read_text(encoding="utf-8"))["units"] if u["id"] != "F"}
    check("V-BR-CLOSEOUT-OTHER-UNITS-UNTOUCHED", other_before == other_after)
    h1 = hashlib.sha256(cp.read_bytes()).hexdigest()
    again = br.closeout(FIX_F, PACKETS / "F.md", cp, epoch=6)
    check("V-BR-CLOSEOUT-TWICE-NO-DUPLICATE-APPEND", again["status"] == "already_recorded"
          and hashlib.sha256(cp.read_bytes()).hexdigest() == h1 and len(unit_actuals(cp, "F")) == len(new))

    # forecast vs actual: the 7 pre-registered calls have a forecast, the 4 unforecast calls say so (None), not 0
    pc = res["per_call"]
    fc = [p for p in pc if p["forecast_processed"] is not None]
    check("V-BR-CLOSEOUT-FORECAST-TABLE-UNFORECAST-CALLS-ARE-NONE", len(pc) == 11 and len(fc) == res["forecast"]["calls"] == 7
          and all(p["forecast_processed"] is None and p["delta_pct"] is None for p in pc[7:])
          and abs(sum(p["forecast_processed"] for p in fc) - res["forecast"]["processed"]) <= 7,
          f"{len(pc)} {len(fc)} {res['forecast']}")
    check("V-BR-CLOSEOUT-ACTUAL-COLUMN-EQUALS-RECEIPTS", [p["actual_processed"] for p in pc] == [x["processed"] for x in res["receipts"]])

    # route recompiled with the measured actual: the unit is now `measured`
    check("V-BR-CLOSEOUT-ROUTE-RECOMPILED-UNIT-MEASURED", res["route"].get("unit_shape_basis") == "measured"
          and "F" not in res["route"].get("prior_units", ["F"]) and res["route"]["verdict"] != "REFUSED", str(res["route"]))

    # Orchestration Amplification Ratio = orchestration processed / worker processed, with and without orchestrators
    if FIX_T.exists():
        o = br.closeout(FIX_F, PACKETS / "F.md", ir_copy(), orchestrators=[FIX_T])
        want = round(raw_processed(FIX_T, through_report=False) / raw_processed(FIX_F), 4)
        check("V-BR-CLOSEOUT-OAR-IS-ORCH-OVER-WORKER", o["orchestration_amplification_ratio"] == want, f"{o['orchestration_amplification_ratio']} want {want}")
    check("V-BR-CLOSEOUT-NO-ORCHESTRATOR-OAR-NONE-CONTROL", res["orchestration_amplification_ratio"] is None)

    # append_actual_text keeps the hand-formatted IR bytes: only the inserted text differs
    text = IR_PATH.read_text(encoding="utf-8-sig")
    ent = {"session": "deadbeef", "calls": 1, "processed": 2}
    ins = json.dumps(ent)
    t_new = br.append_actual_text(text, "T", ent)
    mh_new = br.append_actual_text(text, "MH", ent)
    check("V-BR-APPEND-TEXT-EXISTING-ACTUALS-BYTES-PRESERVED", t_new.replace(",\n      " + ins, "") == text and ins in t_new)
    check("V-BR-APPEND-TEXT-NEW-ACTUALS-BYTES-PRESERVED", mh_new.replace(',\n     "actuals": [' + ins + "]", "") == text and ins in mh_new)
    try:
        br.append_actual_text(text, "NOPE", ent)
        check("V-BR-APPEND-TEXT-UNKNOWN-UNIT-REFUSED", False, "accepted")
    except ValueError:
        check("V-BR-APPEND-TEXT-UNKNOWN-UNIT-REFUSED", True)

    # CLI: --no-write leaves the file alone; --closeout without --claims and an unknown unit are refused
    cn = ir_copy(drop_f_e6)
    h0 = hashlib.sha256(cn.read_bytes()).hexdigest()
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc_ok = br.main(["--transcript", str(FIX_F), "--packet", str(PACKETS / "F.md"), "--closeout", "--claims", str(cn), "--no-write"])
    out = json.loads(buf.getvalue())
    check("V-BR-CLI-CLOSEOUT-NO-WRITE", rc_ok == 0 and out["status"] == "not_written" and hashlib.sha256(cn.read_bytes()).hexdigest() == h0
          and "receipts" not in out)
    check("V-BR-CLI-CLOSEOUT-WITHOUT-CLAIMS-REFUSED", br.main(["--transcript", str(FIX_F), "--packet", str(PACKETS / "F.md"), "--closeout"]) == 2)
    noun = Path(tempfile.mkdtemp(prefix="br-pk-")) / "p.md"
    noun.write_text(PACKET.replace("unit: U", "unit: ZZ"), encoding="utf-8")
    try:
        br.closeout(FIX_F, noun, ir_copy())
        check("V-BR-CLOSEOUT-UNKNOWN-UNIT-REFUSED", False, "accepted")
    except ctc.Refused as e:
        check("V-BR-CLOSEOUT-UNKNOWN-UNIT-REFUSED", e.reason == "BAD_CLAIM", e.reason)


def main() -> int:
    fail_out ="FAILED tests/test_x.py::test_boom - AssertionError: boom\n1 failed"
    r = T()
    for i in range(3):
        r.add([bash(f"pytest -k boom # try {i}", fail_out)])
    rc = r.run()
    check("V-BR-SAME-FAILING-TEST-COUNTS-ONCE", count(rc, "test_transition") == 1 and count(rc, "failure_signature_new") == 1,
          f"{count(rc, 'test_transition')}/{count(rc, 'failure_signature_new')}")

    r = T()
    r.add([bash("run a", "Traceback\nAssertionError at src/foo.py:12:5 token deadbeef01")])
    r.add([bash("run b", "Traceback\nAssertionError at src/foo.py:34:9 token cafebabe99")])
    rc = r.run()
    check("V-BR-SAME-SIGNATURE-DIFFERENT-LINES-ONCE", count(rc, "failure_signature_new") == 1, str(count(rc, "failure_signature_new")))
    r.add([bash("run c", "TypeError: cannot read property of undefined at src/bar.ts:3")])
    rc = r.run()
    check("V-BR-NEW-FAILURE-SIGNATURE-COUNTS", count(rc, "failure_signature_new") == 2, str(count(rc, "failure_signature_new")))

    r = T()
    w = ("Write", {"file_path": "C:/repo/src/a.ts", "content": "const a = 1;"}, "ok")
    r.add([w])
    r.add([w])
    rc = r.run()
    check("V-BR-IDENTICAL-REWRITE-NOT-COUNTED", count(rc, "artifact_delta") == 1, str(count(rc, "artifact_delta")))
    r.add([("Write", {"file_path": "C:/repo/src/a.ts", "content": "const a = 2;"}, "ok")])
    r.add([("Write", {"file_path": "C:/repo/docs/outside.md", "content": "x"}, "ok")])
    rc = r.run()
    check("V-BR-CHANGED-REWRITE-COUNTS-OUTSIDE-GLOB-DOES-NOT", count(rc, "artifact_delta") == 2, str(count(rc, "artifact_delta")))

    r = T()
    r.add([("Read", {"file_path": "a"}, "alpha contents")])
    r.add([("Read", {"file_path": "b"}, "beta contents")])
    r.add([("Read", {"file_path": "a"}, "alpha contents")])
    rc = r.run()
    check("V-BR-NEW-EVIDENCE-COUNTS-REPEAT-DOES-NOT", count(rc, "evidence_new") == 2 and rc[2]["duplicates"] == 1,
          f"{count(rc, 'evidence_new')} dup={rc[2]['duplicates']}")

    r = T()
    r.add([bash("pytest -v", "tests/test_x.py::test_a FAILED")])
    r.add([bash("pytest -v", "tests/test_x.py::test_a PASSED")])
    rc = r.run()
    check("V-BR-TEST-FAIL-TO-PASS-COUNTS", [e["key"] for x in rc for e in x["events"] if e["kind"] == "test_transition"]
          == ["tests/test_x.py::test_a:fail", "tests/test_x.py::test_a:pass"])

    r = T()
    r.add([bash("pytest tests/test_a.py -q", "1 passed in 0.1s")])
    r.add([bash("pytest tests/test_a.py -q", "1 passed in 0.2s")])
    rc = r.run()
    check("V-BR-OBLIGATION-CLOSURE-COUNTS-ONCE", count(rc, "obligation_closed") == 1, str(count(rc, "obligation_closed")))
    r = T()
    r.add([bash("pytest tests/test_a.py -q", "1 failed", True)])
    check("V-BR-FAILED-ACCEPTANCE-NOT-CLOSED-CONTROL", count(r.run(), "obligation_closed") == 0)

    r = T()
    r.add(text="Thinking.\nADVANCED: discriminator: flag set before load")
    r.add(text="ADVANCED: Discriminator -- flag set before load!")
    rc = r.run()
    check("V-BR-ADVANCED-DISCRIMINATOR-ONCE", sum(len(x["advancements"]) for x in rc) == 1 and rc[1]["duplicates"] == 1)

    r = T()
    for i in range(3):
        r.add([("Read", {"file_path": f"f{i}"}, f"content {i}")], dup_line=True)
    rc = r.run()
    check("V-BR-RECEIPT-PER-CALL-NO-LOGGING-TOOLS", len(rc) == 3 and all(x["consumer_claims"] == ["c1", "c2"]
          and x["unit"] == "U" and x["context"] == 100 and x["processed"] == 105 for x in rc), f"{len(rc)}")

    r = T()
    r.add([bash("echo hi", "same output")])
    for _ in range(6):
        r.add([bash("echo hi", "same output")])
    s = br.summarize(r.run())
    check("V-BR-SIX-CALLS-NO-NEW-IDENTITY-ONE-STALL", s["stalls"] == 1 and s["longest_run_without_new_identity"] == 6,
          str(s))
    r2 = T()
    for i in range(6):
        r2.add([("Read", {"file_path": f"f{i}"}, f"unique {i}")])
    s2 = br.summarize(r2.run())
    check("V-BR-FRESH-CALLS-NO-STALL-CONTROL", s2["stalls"] == 0 and s2["semantic_interrupt_density"] == 1.0, str(s2))

    # Canary T (2026-10-06): a real packet's Context is prose, so using it as globs dropped every write.
    prose = PACKET.replace("- src/*.ts", "- ENVIRONMENT IS PRE-STAGED: node_modules installed, do not reinstall")
    r = T()
    r.add([("Write", {"file_path": "C:/repo/src/a.ts", "content": "const a = 1;"}, "ok")])
    r.add([("Write", {"file_path": "C:/repo/docs/outside.md", "content": "x"}, "ok")])
    rc = r.run(prose.replace("## Acceptance", "## Affected\n\n- src/*.ts\n\n## Acceptance"))
    check("V-BR-AFFECTED-GLOBS-NOT-PROSE-CONTEXT", count(rc, "artifact_delta") == 1, str(count(rc, "artifact_delta")))
    check("V-BR-PROSE-CONTEXT-WITHOUT-AFFECTED-COUNTS-NOTHING-CONTROL", count(r.run(prose), "artifact_delta") == 0,
          str(count(r.run(prose), "artifact_delta")))

    image_checks()
    closeout_checks()
    print(f"BR_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
