"""V-BCAP2-BRAND gate: the 16 falsification scenarios BR-01..BR-16 of
vault/backlog/2026-10-21_cdio-brand-identity-logo-absorption.md, driven on real bytes and (where a CLI path exists)
through the real `modules.ccf.cli`, each from BOTH poles (bad case refused, clean control accepted).
No network, no API key, no paid call: the provider is a counting fake. python3 tools/test_bcap2_brand.py (exit 0 == PASS)

Scope honesty: validators are pure-Python structural parsers (no resvg/fontTools render); font glyph coverage is checked
against a declared registry, not a real font file; the trademark scanner is a first-pass filter, recall measured on a small
frozen set below, NOT legal clearance. Real-render visual inspection and a live provider run are laptop/paid plane.
"""
from __future__ import annotations

import base64
import contextlib
import hashlib
import io
import json
import struct
import sys
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from modules.ccf import artifact_compiler as AC  # noqa: E402
from modules.ccf import asset_validator as AV  # noqa: E402
from modules.ccf import cli, kit_readiness as KR, knowledge_feed, model_adapter, release_manager  # noqa: E402
from modules.ccf import trademark_scanner as TS  # noqa: E402

FAILS = []


def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + (f" -- {d}" if d and not c else ""))
    if not c:
        FAILS.append(n)


def _chunk(t, d):
    c = struct.pack(">I", len(d)) + t + d
    return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)


def png(pixel, w=64, h=64):
    """pixel(x, y) -> (r, g, b); a real RGB PNG."""
    raw = b"".join(b"\x00" + b"".join(bytes(pixel(x, y)) for x in range(w)) for y in range(h))
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + _chunk(b"IDAT", zlib.compress(raw)) + _chunk(b"IEND", b""))


# a mark with structure at 16px (two-tone ring) vs a uniform blob
def _ring(x, y):
    d = ((x - 32) ** 2 + (y - 32) ** 2) ** 0.5
    return (20, 20, 20) if 12 <= d <= 24 else (240, 240, 240)


MARK = png(_ring)
BLOB = png(lambda x, y: (200, 90, 40))
MARK2 = png(lambda x, y: (10, 10, 10) if (x // 8 + y // 8) % 2 else (250, 250, 250))
CALLS: list = []
MODE = {"bytes": "good", "fail_on": None}


class FakeAdapter:
    def generate(self, prompt, params=None):
        CALLS.append(prompt)
        if MODE["fail_on"] and MODE["fail_on"] in prompt:
            return model_adapter.ImageArtifact(status="FAILED", provider="fake", model_id="f", error_detail="provider down")
        payload = {"good": MARK, "blob": BLOB}.get(MODE["bytes"], MARK)
        return model_adapter.ImageArtifact(status="OK", provider="fake", model_id="fake-1",
                                           bytes_=base64.b64encode(payload), format="png",
                                           resolution="64x64", latency_ms=1.0, request_id="r1")


def cfg(ids=("ring", "bars"), icons=None):
    icons = icons or {"ring": "hexagonal honeycomb of amber cells", "bars": "three offset vertical bars"}
    return {"schema_version": "1.0", "theme": "modern", "accent": "#112233", "headFont": "Poppins", "labels": [],
            "concepts": [{"id": i, "font": "Poppins", "colours": ["#112233"], "bg": "#FFFFFF", "wordmark": "Orbit",
                          "avoid": [], "icon": icons[i]} for i in ids]}


def project(tmp, name, config):
    p = tmp / name
    (p / ".ccf").mkdir(parents=True)
    (p / "config.json").write_text(json.dumps(config), encoding="utf-8")
    (p / "spec.json").write_text(json.dumps({"brand_name": "Orbit", "industry": "tools", "audience": "devs",
                                              "values": ["craft"]}), encoding="utf-8")
    return str(p)


def run(argv):
    with contextlib.redirect_stdout(io.StringIO()):
        return cli.main(argv)


def sha(b):
    return hashlib.sha256(b).hexdigest()


class _Art:
    def __init__(self, status="OK", image_bytes=None):
        self.status, self.image_bytes = status, image_bytes


def bundle_for(concept_cfg, art):
    return AC.compile_artifacts(concept_cfg["concepts"][:1], {concept_cfg["concepts"][0]["id"]: art}, "brandkit")


def rel(bundle, scans, sel="ring", acks=None):
    return release_manager.release({}, scans, bundle, {"passed": bool(bundle.get("built"))},
                                   {"concept_id": sel}, acks or {})


GOOD_SCAN = {"ring": {"verdict": "PASS", "corpus_version": TS.CORPUS_VERSION}}

with tempfile.TemporaryDirectory() as t:
    t = Path(t)
    knowledge_feed.FEED_DIR = t / "feed"
    for n in ("CREATIVE_FAILURES_PATH", "PROVIDER_BENCHMARKS_PATH", "TRADEMARK_RISK_PATH"):
        setattr(knowledge_feed, n, knowledge_feed.FEED_DIR / getattr(knowledge_feed, n).name)
    cli.model_adapter.GPTImage2Adapter = FakeAdapter
    C = cfg()

    # ---- BR-01: status OK but zero bytes / no source file -> no BRAND_KIT, no SEALED
    b = bundle_for(C, _Art("OK", None))
    check("BR-01 pole: OK status with no bytes builds nothing", b["built"] is False)
    check("BR-01 pole: release over it is BLOCKED, not SEALED", rel(b, GOOD_SCAN)["status"] == "BLOCKED")
    good = bundle_for(C, _Art("OK", MARK))
    check("BR-01 control: real bytes build and SEAL", good["built"] and rel(good, GOOD_SCAN)["status"] == "SEALED")

    # ---- BR-02: corrupt / truncated / false-format raster -> explicit validation failure
    corrupt = bytearray(MARK)
    corrupt[40] ^= 0xFF
    for label, data in (("truncated", MARK[:-20]), ("bit-flipped (CRC)", bytes(corrupt)),
                        ("jpeg magic", b"\xff\xd8\xff\xe0" + b"0" * 200), ("empty", b"")):
        ok, why = AV.validate_png(data)
        check(f"BR-02 pole: {label} PNG rejected", not ok, why)
    check("BR-02 control: intact PNG accepted", AV.validate_png(MARK)[0])

    # ---- BR-03: text-only kit PDF is a CONCEPT_REPORT, never a BRAND_KIT
    text_only = AC._build_minimal_pdf([["ring", "Wordmark: Orbit", f"Logo sha256: {sha(MARK)}"]])
    ok_t, _ = AV.validate_kit_pdf(text_only, MARK)
    check("BR-03 pole: valid text-only PDF does not depict the mark", not ok_t)
    ok_k, why_k = AV.validate_kit_pdf(good["pdf_bytes"], MARK)
    check("BR-03 control: compiled kit PDF embeds the selected mark (Image XObject == PNG pixel stream)", ok_k, why_k)
    check("BR-03 pole: a PDF embedding a DIFFERENT mark is refused", not AV.validate_kit_pdf(good["pdf_bytes"], MARK2)[0])
    assess_bad = KR.assess(MARK, text_only, C["concepts"][0], {"concept_sha": KR.concept_sha(C["concepts"][0])})
    check("BR-03 pole: readiness BLOCKED for a text-only PDF kit", assess_bad["state"] == "BLOCKED", str(assess_bad))
    check("BR-03: the text-only draft itself is still producible (CONCEPT_REPORT lane)", text_only.startswith(b"%PDF-"))

    # ---- BR-04: scanner BLOCK before generate -> zero provider calls
    CB = cfg(("ring", "wing"), {"ring": "hexagonal honeycomb of amber cells", "wing": "a checkmark-shaped swoosh curve"})
    P = project(t, "br04", CB)
    CALLS.clear()
    rc = run(["generate", P])
    check("BR-04 pole: BLOCKed concept never reaches the provider", len(CALLS) == 1 and all("swoosh" not in c for c in CALLS), str(len(CALLS)))
    check("BR-04: generate reports gate_blocked", rc == 3, str(rc))
    check("BR-04 pole: no asset written for the BLOCKed concept", not Path(P, ".ccf", "images", "wing.png").exists())
    CALLS.clear()
    run(["generate", project(t, "br04c", C)])
    check("BR-04 control: clean config calls the provider once per concept", len(CALLS) == 2, str(len(CALLS)))

    # ---- BR-05: missing / UNKNOWN / stale scan -> UNASSESSED, never an implied PASS
    for label, scans in (("missing report", {}), ("UNKNOWN verdict", {"ring": {"verdict": "UNKNOWN", "corpus_version": TS.CORPUS_VERSION}}),
                         ("stale corpus", {"ring": {"verdict": "PASS", "corpus_version": "0.9"}})):
        r = rel(good, scans)
        check(f"BR-05 pole: {label} -> BLOCKED/UNASSESSED", r["status"] == "BLOCKED" and r.get("readiness") == "UNASSESSED", str(r))
    check("BR-05 control: fresh PASS scan seals", rel(good, GOOD_SCAN)["status"] == "SEALED")

    # ---- BR-06: WARN needs accountable human acknowledgment
    warn = {"ring": {"verdict": "WARN", "corpus_version": TS.CORPUS_VERSION}}
    check("BR-06 pole: WARN without ack is BLOCKED", rel(good, warn)["status"] == "BLOCKED")
    check("BR-06 pole: a falsy ack is not an acknowledgment", rel(good, warn, acks={"ring": False})["status"] == "BLOCKED")
    check("BR-06 control: WARN with recorded ack seals", rel(good, warn, acks={"ring": True})["status"] == "SEALED")
    check("BR-06: a trademark BLOCK is not overridable by an ack", rel(good, {"ring": {"verdict": "BLOCK", "corpus_version": TS.CORPUS_VERSION}}, acks={"ring": True})["status"] == "BLOCKED")

    # ---- BR-07: untrusted SVG
    SVG_OK = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><g><path d="M0 0L10 10"/><circle cx="5" cy="5" r="2"/></g></svg>'
    bad_svgs = {
        "script": b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
        "onload": b'<svg xmlns="http://www.w3.org/2000/svg" onload="x()"><path d="M0 0"/></svg>',
        "foreignObject": b'<svg xmlns="http://www.w3.org/2000/svg"><foreignObject><div/></foreignObject></svg>',
        "external href": b'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><use xlink:href="http://evil/x.svg#a"/></svg>',
        "external url()": b'<svg xmlns="http://www.w3.org/2000/svg"><rect fill="url(http://evil/p)"/></svg>',
        "image tag": b'<svg xmlns="http://www.w3.org/2000/svg"><image href="http://evil/a.png"/></svg>',
        "entity bomb": b'<!DOCTYPE svg [<!ENTITY a "x">]><svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0"/></svg>',
        "not xml": b"<svg><path",
    }
    for label, data in bad_svgs.items():
        check(f"BR-07 pole: svg with {label} rejected", not AV.validate_svg(data)[0], AV.validate_svg(data)[1])
    check("BR-07 control: clean svg accepted", AV.validate_svg(SVG_OK)[0])
    check("BR-07 control: internal #fragment reference accepted",
          AV.validate_svg(b'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><defs><path id="a" d="M0 0"/></defs><use xlink:href="#a"/></svg>')[0])

    # ---- BR-08: hostile id / path -> no shell, no write outside the project
    for hostile in ("../../escaped", "a;touch pwned", "$(id)", "a/b", "", "x" * 80):
        bad = cfg()
        bad["concepts"][0]["id"] = hostile
        pr = project(t, "br08-" + hashlib.md5(hostile.encode()).hexdigest()[:6], bad)
        CALLS.clear()
        rc8 = run(["generate", pr])
        check(f"BR-08 pole: id {hostile[:20]!r} rejected before any provider call", rc8 == 1 and CALLS == [], f"rc={rc8} calls={len(CALLS)}")
    check("BR-08 pole: nothing escaped the tmp tree", not (t.parent / "escaped.png").exists() and not any(t.rglob("pwned")))
    check("BR-08 control: safe ids accepted", AV.safe_concept_id("ring-2_a") and not AV.safe_concept_id("a b"))

    # ---- BR-09: PNG bytes named .ico
    entry = MARK
    ico = struct.pack("<HHH", 0, 1, 1) + struct.pack("<BBBBHHII", 64, 64, 0, 0, 1, 32, len(entry), 22) + entry
    check("BR-09 pole: PNG bytes as favicon.ico fail the parser", not AV.validate_ico(MARK)[0])
    check("BR-09 pole: truncated ICO fails", not AV.validate_ico(ico[:30])[0])
    check("BR-09 pole: ICO entry pointing outside the file fails", not AV.validate_ico(ico[:-100])[0])
    check("BR-09 control: a real ICO container parses", AV.validate_ico(ico)[0], AV.validate_ico(ico)[1])
    P9 = project(t, "br09", C)
    run(["generate", P9]); run(["select", P9, "--concept", "ring", "--by", "gate"])
    Path(P9, ".ccf", "assets").mkdir()
    Path(P9, ".ccf", "assets", "favicon.ico").write_bytes(MARK)
    check("BR-09 via CLI: package BLOCKED when favicon.ico is renamed PNG", run(["package", P9]) == 3)
    Path(P9, ".ccf", "assets", "favicon.ico").write_bytes(ico)
    check("BR-09 via CLI control: package passes with a real ICO", run(["package", P9]) == 0)

    # ---- BR-10: font policy, no silent substitution
    REG = {"Poppins": {"license": "OFL-1.1", "glyphs": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"}}
    check("BR-10 pole: unregistered font rejected", not AV.check_font("Comic Sans MS", "Orbit", REG)[0])
    check("BR-10 pole: wordmark glyphs outside the font rejected", not AV.check_font("Poppins", "OrbitÑş", REG)[0])
    check("BR-10 pole: registered font without license rejected", not AV.check_font("Poppins", "Orbit", {"Poppins": {"glyphs": "Orbit"}})[0])
    check("BR-10 control: registered, licensed, covering font accepted", AV.check_font("Poppins", "Orbit", REG)[0])

    # ---- BR-11: determinism (same inputs -> same bytes and verdicts)
    d1, d2 = bundle_for(C, _Art("OK", MARK)), bundle_for(C, _Art("OK", MARK))
    check("BR-11 pole: two compiles of identical inputs yield identical PDF bytes", sha(d1["pdf_bytes"]) == sha(d2["pdf_bytes"]))
    check("BR-11 pole: scanner verdict is stable across runs",
          TS.scan("a", "three offset vertical bars", []) == TS.scan("a", "three offset vertical bars", []))
    check("BR-11 control: a different mark changes the PDF (the hash is not constant)",
          sha(bundle_for(C, _Art("OK", MARK2))["pdf_bytes"]) != sha(d1["pdf_bytes"]))

    # ---- BR-12: a blob logo must not reach BRAND_KIT_READY through the CLI
    MODE["bytes"] = "blob"
    P12 = project(t, "br12", C)
    run(["generate", P12]); run(["select", P12, "--concept", "ring", "--by", "gate"])
    rc12 = run(["package", P12])
    rel12 = sorted(Path(P12, ".ccf", "releases").glob("*.json")) if Path(P12, ".ccf", "releases").exists() else []
    state12 = json.loads(rel12[-1].read_text())["readiness"]["state"] if rel12 else "NOT_SEALED"
    check("BR-12 pole: blob logo is not BRAND_KIT_READY via CLI", state12 != "BRAND_KIT_READY", f"rc={rc12} state={state12}")
    MODE["bytes"] = "good"

    # ---- BR-13: config edited after generate -> package refuses (provenance)
    P13 = project(t, "br13", C)
    run(["generate", P13]); run(["select", P13, "--concept", "ring", "--by", "gate"])
    edited = cfg()
    edited["concepts"][0]["icon"] = "a completely different hexagonal lattice"
    Path(P13, "config.json").write_text(json.dumps(edited), encoding="utf-8")
    check("BR-13 pole: package exits 3 after the concept was edited post-generate", run(["package", P13]) == 3)
    Path(P13, "config.json").write_text(json.dumps(C), encoding="utf-8")
    check("BR-13 control: restoring the config lets package pass", run(["package", P13]) == 0)

    # ---- BR-14: license conflict poles
    MIT_L = "Permission is hereby granted, free of charge, to any person obtaining a copy"
    GPL_L = "GNU General Public License version 3"
    check("BR-14 pole: README MIT but LICENSE GPL -> blocked", AV.license_conflict("Licensed under MIT", GPL_L)[0])
    check("BR-14 pole: unrecognised LICENSE text -> blocked", AV.license_conflict("MIT", "all rights reserved")[0])
    check("BR-14 pole: README with no license claim -> blocked", AV.license_conflict("a logo tool", MIT_L)[0])
    check("BR-14 control: README and LICENSE agree -> not blocked", not AV.license_conflict("License: MIT", MIT_L)[0])

    # ---- BR-15: provider failure on the second concept leaves partial state
    MODE["fail_on"] = "three offset vertical bars"
    P15 = project(t, "br15", C)
    rc15 = run(["generate", P15])
    MODE["fail_on"] = None
    check("BR-15 pole: generate reports a provider error (exit 2)", rc15 == 2, str(rc15))
    check("BR-15 pole: first concept kept, failed concept has no asset",
          Path(P15, ".ccf", "images", "ring.png").exists() and not Path(P15, ".ccf", "images", "bars.png").exists())
    run(["select", P15, "--concept", "bars", "--by", "gate"])
    check("BR-15 pole: package on the failed concept exits 3", run(["package", P15]) == 3)
    run(["select", P15, "--concept", "ring", "--by", "gate"])
    check("BR-15 control: package on the surviving concept passes", run(["package", P15]) == 0)

    # ---- BR-16: scanner recall on a frozen paraphrase set, clean-set false blocks, BLOCK not overridable
    FROZEN_POS = ["a sweeping tick-shaped swish", "an apple with a bitten edge and a leaf",
                  "a single-line monoline loop with a heart pin", "golden double arches",
                  "concentric red circles bullseye", "three-pointed star inside a circle",
                  "three diagonal stripes forming a mountain", "a small songbird perched flying blue"]
    FROZEN_NEG = ["hexagonal honeycomb of amber cells", "three offset vertical bars", "a folded paper crane in teal",
                  "interlocking square tiles in a grid", "a compass needle over a dotted grid"]
    hits = sum(TS.scan("p", d, [])["verdict"] == "BLOCK" for d in FROZEN_POS)
    check("BR-16 pole: recall 8/8 BLOCK on the frozen known-mark paraphrases", hits == len(FROZEN_POS), f"{hits}/{len(FROZEN_POS)}")
    check("BR-16 control: no frozen clean description is falsely BLOCKed", all(TS.scan("n", d, [])["verdict"] != "BLOCK" for d in FROZEN_NEG))
    check("BR-16 control: at least two clean descriptions are plain PASS", sum(TS.scan("n", d, [])["verdict"] == "PASS" for d in FROZEN_NEG) >= 2)
    check("BR-16 pole: select --by llm cannot override a BLOCK (even with --ack)",
          run(["select", P, "--concept", "wing", "--by", "llm", "--ack"]) == 3)

    # ---- BI-09: multi-territory check, both poles
    from modules.ccf import territories as TR
    def _c(i, m, f, ic):
        return {"id": i, "mechanism": m, "brand_fact": f, "icon": ic}
    good = [_c("a", "negative space", "founded in a port city", "hex cells"),
            _c("b", "letterform mutation", "serves night-shift nurses", "bent O"),
            _c("c", "monogram", "family name since 1952", "")]
    check("BI-09 pole: three distinct mechanisms+facts PASS", TR.check_territories(good)["verdict"] == "PASS")
    recol = [_c("a", "negative space", "port city", "hex cells"), _c("b", "negative space", "nurses", "hex cells"),
             _c("c", "gestalt", "family", "x")]
    check("BI-09 pole: recoloured same mechanism is not a territory", TR.check_territories(recol)["verdict"] == "FAIL")
    check("BI-09 pole: shared brand_fact does not count twice",
          TR.check_territories([_c("a", "m1", "same", "i1"), _c("b", "m2", "same", "i2"), _c("c", "m3", "other", "i3")])["verdict"] == "FAIL")
    check("BI-09 pole: missing mechanism is unmeasured, not counted",
          TR.check_territories([{"id": "a", "brand_fact": "x"}] + good[:2])["verdict"] == "FAIL")
    check("BI-09 pole: two territories without exception FAIL", TR.check_territories(good[:2])["verdict"] == "FAIL")
    check("BI-09 control: reasoned narrow-brief exception is its own verdict, not PASS",
          TR.check_territories(good[:2], {"reason": "client mandates the existing wordmark"})["verdict"] == "NARROW_BRIEF_EXCEPTION")
    check("BI-09 pole: bare True / blank-reason exception refused",
          TR.check_territories(good[:2], True)["verdict"] == "FAIL" and TR.check_territories(good[:2], {"reason": "  "})["verdict"] == "FAIL")

    # ---- BI-14: critique separates evidence from judgment, cannot self-approve
    from modules.ccf import critique as CR
    full = lambda cid, v=True: CR.build_critique(cid, [{"criterion": c, "kind": "evidence", "value": v, "instrument": "probe"} for c in CR.CRITERIA])
    a, b, c3 = full("a"), full("b"), full("c", False)
    check("BI-14 pole: evidence without instrument is demoted to judgment",
          "spelling" in CR.build_critique("x", [{"criterion": "spelling", "kind": "evidence", "value": True}])["judgment"])
    check("BI-14 pole: unassessed criteria stay UNASSESSED and block qualification",
          CR.build_critique("x", [])["unassessed"] == list(CR.CRITERIA) and not CR.qualifies(CR.build_critique("x", [])))
    check("BI-14 pole: an LLM actor cannot approve", not CR.approve([a, b], "a", "llm")["approved"])
    check("BI-14 pole: fewer than two qualifying directions blocks approval", not CR.approve([a, c3], "a", "human")["approved"])
    check("BI-14 pole: a failing-evidence concept cannot be selected", not CR.approve([a, b, c3], "c", "human")["approved"])
    check("BI-14 control: human selects among two qualifying directions", CR.approve([a, b, c3], "b", "human")["approved"])
    check("BI-14 control: a critique itself is never pre-approved", a["approval"] == "NOT_APPROVED")

    # ---- BI-08: brand truth intake never fabricates
    from modules.ccf import brand_truth as BT
    r = BT.intake("b", [{"field": "audience", "value": "night nurses", "origin": "stated"},
                        {"field": "sector", "value": "health", "origin": "observed", "source": "https://x.example/about", "retrieved_at": "2026-11-19"}])
    check("BI-08 pole: sourced observed and stated facts are kept", set(r["facts"]) == {"audience", "sector"})
    check("BI-08 pole: unfilled fields are listed unknown, not invented", "purpose" in r["unknown"] and "audience" not in r["unknown"])
    r2 = BT.intake("b", [{"field": "sector", "value": "health", "origin": "observed"}])
    check("BI-08 pole: observed without source/retrieved_at is rejected, not kept", not r2["facts"] and len(r2["rejected"]) == 1)
    r3 = BT.intake("b", [{"field": "mood", "value": "x", "origin": "stated"}, {"field": "purpose", "value": "", "origin": "stated"},
                         {"field": "purpose", "value": "x", "origin": "llm"}])
    check("BI-08 pole: unknown field, empty value and bad origin are all rejected", not r3["facts"] and len(r3["rejected"]) == 3)
    check("BI-08 control: trademark clearance is never claimed", r["clearance"] == "NOT_ASSESSED")

# Residual (recorded, not hidden): the scanner is a first-pass filter; WARN rate on the clean set is high by design.
print(f"\n{'V-BCAP2-BRAND (BR-01..16, BI-08, BI-09, BI-14) PASS' if not FAILS else 'V-BCAP2-BRAND FAIL: ' + ', '.join(FAILS)}")
sys.exit(1 if FAILS else 0)
