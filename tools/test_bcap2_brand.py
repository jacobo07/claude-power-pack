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

    # ---- BI-12: typed Visual DNA contract
    from modules.ccf import visual_dna as VD
    dna = {"schema_version": "1.0", "brand_id": "b", "approved_brief_ref": "brief#1", "territory": "t1",
           "symbol_strategy": "negative space", "geometric_constraints": ["8px grid"], "shape_language": "rounded",
           "relative_proportion": {"mark_to_wordmark": 1.2}, "palette_roles": {"primary": "#112233", "surface": "#FFFFFF"},
           "typography": {"family": "Poppins", "source": "google-fonts"}, "spacing": {"unit": 8}, "variants": ["mono"],
           "forbidden_patterns": ["swoosh"], "avatar_rules": "mark only", "small_size_rules": "min 16px",
           "applications": ["favicon"], "selection_evidence": {"selected_by": "human", "critique_ref": "c#1"}}
    check("BI-12 control: a complete DNA validates", VD.validate(dna) == [], str(VD.validate(dna)))
    bad = {k: v for k, v in dna.items() if k != "forbidden_patterns"}
    check("BI-12 pole: a missing required section is named", VD.validate(bad) == ["missing forbidden_patterns"])
    check("BI-12 pole: wrong version, bad colour and font without source are all reported",
          len(VD.validate(dict(dna, schema_version="0.9", palette_roles={"primary": "blue"}, typography={"family": "X"}))) == 3)
    check("BI-12 pole: selection without a critique reference is invalid",
          any("selection_evidence" in x for x in VD.validate(dict(dna, selection_evidence={"selected_by": "human"}))))
    check("BI-12 control: tokens derive from the DNA", VD.tokens_for(dna, {})["color.primary"] == "#112233")
    try:
        VD.tokens_for(dna, {"color.primary": "#FF0000"})
        forked = True
    except ValueError:
        forked = False
    check("BI-12 pole: DNA cannot fork a project-pinned token (SSOT wins)", not forked)
    check("BI-12 control: an identical project pin is accepted", VD.tokens_for(dna, {"color.primary": "#112233"})["color.primary"] == "#112233")

    # ---- BI-13: creative provider policy
    from modules.ccf import provider_policy as PP
    check("BI-13 pole: image model only with deterministic=False AND a stated need",
          PP.route({"deterministic_possible": False, "needs": ["photoreal texture"]})["route"] == "IMAGE_MODEL")
    check("BI-13 pole: deterministic-possible stays vector", PP.route({"deterministic_possible": True, "needs": ["x"]})["route"] == "DETERMINISTIC_VECTOR")
    um = PP.route({"deterministic_possible": None})
    check("BI-13 pole: unmeasured never buys an image call and is flagged", um["route"] == "DETERMINISTIC_VECTOR" and um.get("flag") == "UNMEASURED")
    check("BI-13 pole: False without a stated need is not enough", PP.route({"deterministic_possible": False, "needs": []})["route"] == "DETERMINISTIC_VECTOR")
    check("BI-13 pole: missing or same-model fallback is refused", not PP.plan_call("m1", None, 1)["ok"] and not PP.plan_call("m1", "m1", 1)["ok"])
    check("BI-13 pole: tool-call bound and refused imports are refused",
          not PP.plan_call("m1", "m2", 9)["ok"] and not PP.plan_call("m1", "m2", 1, ["parallel_orchestration"])["ok"])
    ok = PP.plan_call("m1", "m2", 2)
    check("BI-13 control: a bounded call with fallback is ok; cost fields start None, not 0",
          ok["ok"] and all(v is None for v in ok["tracking"].values()) and set(ok["tracking"]) == set(PP.TRACKED))

    # ---- BI-11: cohesive identity set
    from modules.ccf import identity_set as IS
    base = {"comparison_axes": ["warm vs cool", "geometric vs organic"], "rationale": "honeycomb = shared work",
            "category_default_challenge": "category default is blue; we chose amber because ...",
            "palette": {"text": "#111111", "surface": "#FFFFFF"}, "typography_test": {"observed": "16px legible"},
            "logo": "L1", "font": "Poppins"}
    check("BI-11 control: a complete NEW set validates", IS.validate_set(base) == [], str(IS.validate_set(base)))
    check("BI-11 pole: contrast is computed (black/white = 21, grey on white fails)",
          IS.contrast("#000000", "#FFFFFF") == 21.0 and any("contrast" in x for x in IS.validate_set(dict(base, palette={"text": "#AAAAAA", "surface": "#FFFFFF"}))))
    check("BI-11 pole: 1 or 5 axes refused", any("axes" in x for x in IS.validate_set(dict(base, comparison_axes=["a"]))) and any("axes" in x for x in IS.validate_set(dict(base, comparison_axes=list("abcde")))))
    check("BI-11 pole: missing rationale, challenge and typography observation all named",
          len(IS.validate_set(dict(base, rationale="", category_default_challenge="", typography_test={}))) == 3)
    orig = {"logo": "L0", "font": "Poppins", "palette": {"text": "#111111", "surface": "#FFFFFF"}}
    check("BI-11 pole: KEEP refuses a changed logo", any("logo" in x for x in IS.validate_set(base, "KEEP", orig)))
    check("BI-11 control: REFRESH may change the palette but not the logo/font",
          IS.validate_set(dict(base, logo="L0", palette={"text": "#222222", "surface": "#FAFAFA"}), "REFRESH", orig) == [])
    check("BI-11 pole: KEEP without the original is refused", any("requires" in x for x in IS.validate_set(base, "KEEP")))

    # ---- BI-10: technique taxonomy as typed hypotheses
    from modules.ccf import techniques as TQ
    good_h = {"id": "h1", "technique": "negative_space_letterform", "brand_observation": "the name Pip has two parallel stems",
              "recipe": ["align the two stems 40 units apart", "subtract a triangle between them"], "self_rating": 9}
    check("BI-10 control: a complete hypothesis has no problems", TQ.check_hypothesis(good_h) == [], str(TQ.check_hypothesis(good_h)))
    check("BI-10 pole: exactly the 12 pinned technique names", len(TQ.TECHNIQUES) == 12 and "monogram_construction" in TQ.TECHNIQUES)
    check("BI-10 pole: unknown technique refused", any("taxonomy" in x for x in TQ.check_hypothesis(dict(good_h, technique="vibes"))))
    check("BI-10 pole: generic observation refused", any("brand_observation" in x for x in TQ.check_hypothesis(dict(good_h, brand_observation="looks modern"))))
    check("BI-10 pole: missing recipe and non-geometric step refused",
          any("recipe missing" in x for x in TQ.check_hypothesis(dict(good_h, recipe=[]))) and any("step 1" in x for x in TQ.check_hypothesis(dict(good_h, recipe=["make it pop"]))))
    sm = TQ.summarize([good_h])
    check("BI-10 pole: self-rating is UNVERIFIED and measured originality stays None",
          sm["rows"][0]["self_rating_status"] == "UNVERIFIED" and sm["rows"][0]["measured_originality"] is None and sm["pin"]["sha"].startswith("d14340c3"))

    # ---- BI-20 / 15 / 22-23 / 25 / 26 / 29 / 34 (pure; epoch 8)
    from modules.ccf import brand_color as BC, brand_release as BRL
    pal = {"ink": "#111111", "paper": "#FFFFFF", "mid": "#AAAAAA"}
    ok = BC.check_palette(pal, [{"fg": "ink", "bg": "paper", "context": "body"}])
    check("BI-20 control: ink/paper body passes with computed ratio", ok["problems"] == [] and ok["rows"][0]["ratio"] > 15, str(ok))
    check("BI-20 pole: grey on white fails body, passes nothing silently",
          BC.check_palette(pal, [{"fg": "mid", "bg": "paper", "context": "body"}])["problems"] != [])
    check("BI-20 pole: undeclared context is UNASSESSED, bad hex and unknown role refused",
          BC.check_palette(pal, [{"fg": "ink", "bg": "paper", "context": "vibes"}])["rows"][0]["status"] == "UNASSESSED"
          and BC.check_palette({"x": "red"}, [])["problems"] and BC.check_palette(pal, [{"fg": "nope", "bg": "paper", "context": "body"}])["problems"])
    check("BI-20 pole: delta E is 0 for equal and 100 for black/white; bare conversion claim refused",
          BC.delta_e76("#336699", "#336699") == 0 and BC.delta_e76("#000000", "#FFFFFF") == 100.0
          and not BC.association_claim_ok({"evidence_source": "folk"}) and BC.association_claim_ok({"evidence_source": "ab-test-7", "measured": True}))
    prof = {"source_sha256": "a" * 64, "derivatives": [{"format": "svg"}, {"format": "png", "size": 512}, {"format": "ico", "sizes": [16, 32], "container": "ico"}]}
    check("BI-22 control: a complete export profile has no problems", BRL.check_export_profile(prof) == [], str(BRL.check_export_profile(prof)))
    bad = {"derivatives": [{"format": "ico", "sizes": [17], "container": "png"}, {"format": "png", "generated_independently": True, "shell_command": "x"}, {"format": "bmp"}, {"format": "pdf", "size": 1, "font_fallback": "silent"}]}
    pb = BRL.check_export_profile(bad)
    check("BI-22/23 pole: no source, PNG-as-ICO, bad ICO size, rerun, shell, unknown format, silent font, missing size all refused", len(pb) >= 8, str(pb))
    tok = {"color": {"ink": {"$value": "#111111", "$type": "color"}, "text": {"$value": "{color.ink}", "$type": "color"}}}
    check("BI-25 control: DTCG tokens valid and CSS derived from them", BRL.check_dtcg(tok) == [] and "--color-text: var(--color-ink);" in BRL.to_css(tok))
    check("BI-25 pole: missing $type and dangling alias refused",
          len(BRL.check_dtcg({"a": {"$value": "{b.c}"}})) == 2)
    files = {"logo.svg": b"<svg/>", "logo.png": b"png"}
    meta = {k: "x" for k in ("owner_approval", "generator_ref", "license_notice", "brief_ref", "visual_dna_ref")}
    m = BRL.build_manifest("1.0.0", files, meta)
    check("BI-26 control: manifest verifies against its own files", BRL.verify_manifest(m, files) == [])
    check("BI-26 pole: tamper, missing and contaminant files all named",
          len(BRL.verify_manifest(m, {"logo.svg": b"<svg x/>", "extra.bin": b"?"})) == 3)
    try:
        BRL.build_manifest("1.0.0", files, dict(meta, owner_approval=""))
        refused = False
    except ValueError:
        refused = True
    check("BI-26 pole: no owner approval -> no manifest at all", refused)
    pv = {"contexts": [{"context": c, "visual_dna": "d1", "is_mock": True} for c in BRL.CONTEXTS]}
    check("BI-15 control: all 9 contexts on one Visual DNA, marked mock, pass", BRL.check_preview(pv, "d1") == [])
    pv2 = {"contexts": [dict(c) for c in pv["contexts"][:-1]]}
    pv2["contexts"][0]["visual_dna"] = "other"; pv2["contexts"][1]["is_mock"] = False
    check("BI-15 pole: missing context, reinvented identity, unmarked mock all named", len(BRL.check_preview(pv2, "d1")) == 3)
    check("BI-29 pole: no corpus abstains; PASS never means clearance",
          BRL.similarity_report({"size": 0}, [])["verdict"] == "ABSTAIN"
          and BRL.similarity_report({"size": 50, "provenance_logged": True}, [])["clearance"] == "NOT_ASSESSED"
          and BRL.similarity_report({"size": 50, "provenance_logged": True}, [{"score": 0.9}])["verdict"] == "REVIEW"
          and BRL.similarity_report({"size": 50, "provenance_logged": False}, [])["verdict"] == "ABSTAIN")
    check("BI-34 pole: logo/brand wording routes to CCF with human approval; unrelated text does not; budget abstains",
          BRL.applicable("make a logo for my bakery")["route"] == "CCF" and BRL.applicable("fix the login bug")["route"] == "NONE"
          and BRL.applicable("new brand identity", budget_ok=False)["route"] == "ABSTAIN")

    # ---- BI-16 / BI-21: upstream probe evidence is recorded and honest about what was NOT run
    up = json.loads((ROOT / "vault/programs/bcap-2/UPSTREAM_BRAND_PROBE.json").read_text())
    m16 = up["sigilgen"].get("bi16_measured", {})
    check("BI-16 evidence: sigilgen pinned to a full sha, 5 engines inventoried, same-host cross-process measured, cross-platform NOT claimed",
          len(up["sigilgen"]["pinned_sha"]) == 40 and len(up["sigilgen"]["engines"]) == 5
          and up["sigilgen"]["bi16_status"].startswith("SAME_HOST_CROSS_PROCESS_MEASURED") and "84c031a31fbb" in m16.get("result", "")
          and any("cross-platform" in c and "NOT measured" in c for c in m16.get("caveats", [])))
    check("BI-21 evidence: archived branding-mcp is historical, licence-less logo-generator-skill admits no code",
          up["branding_mcp"]["archived"] is True and up["branding_mcp"]["verdict"] == "HISTORICAL_REFERENCE"
          and up["logo_generator_skill"]["licence_file"] is False and "no code" in up["logo_generator_skill"]["verdict"])

    # ---- BI-17 / 19 / 28 / 31 / 35 (pure; epoch 10)
    from modules.ccf import brand_review as BV
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><g data-part="icon"><circle r="4"/></g><g data-part="wordmark"><rect width="9" height="3"/></g></svg>'
    sp = BV.split_parts(svg)
    check("BI-17 control: typed icon and wordmark parts split without regex", sp["ok"] and set(sp["parts"]) == {"icon", "wordmark"}, str(sp))
    check("BI-17 pole: script svg, unknown part, duplicate part and untyped svg all refused",
          not BV.split_parts(b'<svg xmlns="http://www.w3.org/2000/svg"><script>x</script></svg>')["ok"]
          and not BV.split_parts(svg.replace(b"wordmark", b"badge"))["ok"]
          and not BV.split_parts(svg.replace(b"wordmark", b"icon"))["ok"]
          and not BV.split_parts(b'<svg xmlns="http://www.w3.org/2000/svg"><g/></svg>')["ok"])
    reg = {"F1": {"license": "OFL", "glyphs": "".join(set("".join(BV.LANGS.values()))) + "abc"},
           "F2": {"license": "OFL", "glyphs": "abc"}}
    check("BI-19 control: a font with the full diacritic set covers ES/PT/FR/DE", BV.language_coverage("F1", reg)["ok"])
    lc = BV.language_coverage("F2", reg)
    check("BI-19 pole: ascii-only font names the missing diacritics per language; unknown font refused (no Inter fallback)",
          not lc["ok"] and "ES" in lc["missing"] and "DE" in lc["missing"] and not BV.language_coverage("Inter", reg)["ok"])
    ev = {k: {"observed": True, "instrument": "probe"} for k in BV.LENS}
    check("BI-28 control: all 12 criteria observed -> approve pending human, no UI score", BV.logo_lens(ev)["verdict"] == "APPROVE_PENDING_HUMAN" and BV.logo_lens(ev)["ui_score"] is None)
    check("BI-28 pole: one fail blocks; a missing criterion or instrument-less claim is UNASSESSED not pass; no human signoff stays incomplete",
          BV.logo_lens(dict(ev, small_size={"observed": False, "instrument": "p"}))["verdict"] == "BLOCK"
          and BV.logo_lens({k: v for k, v in ev.items() if k != "silhouette"})["verdict"] == "INCOMPLETE"
          and BV.logo_lens(dict(ev, spelling={"observed": True}))["rows"]["spelling"] == "UNASSESSED"
          and BV.logo_lens(dict(ev, human_signoff={"observed": False, "instrument": "p"}))["verdict"] == "BLOCK")
    cats = list(BV.CATEGORIES)
    briefs = [{"id": f"b{i}", "categories": [cats[i % len(cats)]], "frozen_sha256": "a" * 64} for i in range(12)]
    briefs[11]["categories"] = cats[11 % len(cats):] + cats
    check("BI-31 control: 12 frozen briefs covering all categories pass", BV.check_benchmark(briefs) == [], str(BV.check_benchmark(briefs)))
    check("BI-31 pole: 11 briefs, unfrozen brief, duplicate id and a dropped category are all named",
          len(BV.check_benchmark(briefs[:11])) >= 1 and any("frozen" in x for x in BV.check_benchmark([dict(b, frozen_sha256="") for b in briefs]))
          and any("duplicate" in x for x in BV.check_benchmark(briefs[:11] + [briefs[0]])))
    rv = {"reviewer": "r", "implementer": "i", "refusal_cases_proven": True, "commit_refs": ["x"], "test_counts": {"p": 1}, "revert_path": "git revert x", "status": "NOT_DONE"}
    check("BI-35 control: a distinct, evidenced review is valid", BV.review_independent(rv) == [])
    check("BI-35 pole: self-review, no refusal proof, missing revert, bad status all named",
          len(BV.review_independent(dict(rv, reviewer="i", refusal_cases_proven=False, revert_path="", status="maybe"))) == 4)

# Residual (recorded, not hidden): the scanner is a first-pass filter; WARN rate on the clean set is high by design.
print(f"\n{'V-BCAP2-BRAND (BR-01..16, BI-08, BI-09, BI-10, BI-11, BI-12, BI-13, BI-14, BI-15, BI-20, BI-22..26, BI-17, BI-19, BI-28, BI-29, BI-31, BI-34, BI-35) PASS' if not FAILS else 'V-BCAP2-BRAND FAIL: ' + ', '.join(FAILS)}")
sys.exit(1 if FAILS else 0)
