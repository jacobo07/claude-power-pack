#!/usr/bin/env python
"""V-BR-* gates for tools/boundary_receipts.py, driven by small synthetic transcripts."""
from __future__ import annotations

import json
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


def main() -> int:
    fail_out = "FAILED tests/test_x.py::test_boom - AssertionError: boom\n1 failed"
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
    print(f"BR_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
