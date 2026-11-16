#!/usr/bin/env python3
"""V-TASTE-* -- the Taste Skill (design-taste-frontend, MIT) is absorbed 100%, and every claim of that is falsifiable.

  V-TASTE-MAP-*      every ##/### section and every Pre-Flight checkbox of the vendored SKILL.md (parsed here, never
                     listed by hand) has exactly one destination; no dead map rule; every ENFORCED id exists in
                     modules.cdio.taste.CHECKS and every check is claimed; every COVERED_BY owner exists on disk.
                     Negative poles: a map with one rule removed, and a skill with one added heading, both FAIL.
  V-TASTE-HASH       vendored SKILL.md sha256 == the map's skill_sha256 (an upstream update forces a re-map).
  V-TASTE-CHECK-*    each of the 27 checks fails its bad snippet and passes its good snippet.
  V-TASTE-SLOP       a seeded slop page blocks on all 10 critical checks; a clean page blocks on none.
  V-TASTE-WAIVER     a reasoned taste_overrides entry waives; an unreasoned one is refused and still blocks.
  V-TASTE-KIND       tower check `taste:<file>`: FAIL on slop, PASS on clean, UNREADABLE missing, REFUSED_PATH escape.
  V-TASTE-BLOCK      the web_surface family block names the skill and the NO APLICA grammar; a non-web prompt does not.
  V-TASTE-STOP-*     the Stop hook blocks a VIOLATED turn of a session that was shown the family, honours NO APLICA,
                     never blocks twice for one set, never under stop_hook_active, never in an unrelated session.
  V-TASTE-LENS       CDIO-05 carries the Taste render lens listing every RENDER_REVIEW Pre-Flight item.
  V-TASTE-WIRED      the repo dispatcher's Stop-chain registers tools/family_donegate_stop.py.
Never calls a model, never touches the network; HOME and the tower state dir are throwaway.
"""
from __future__ import annotations

import copy
import fnmatch
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_TMP = tempfile.mkdtemp(prefix="v-taste-")
os.environ["HOME"] = os.environ["USERPROFILE"] = _TMP          # offer counters / ledgers never touch the real HOME
os.environ["CPP_TOWER_STATE_DIR"] = os.path.join(_TMP, "tower")

from modules.cdio import taste  # noqa: E402

SKILL = ROOT / "vendor" / "skills" / "design-taste-frontend" / "SKILL.md"
MAP = ROOT / "vault" / "knowledge_base" / "cdio" / "taste-absorption.json"
DESTS = {"ENFORCED", "COVERED_BY", "RENDER_REVIEW", "GUIDANCE", "CONFLICT", "OUT_OF_SCOPE"}
RESULTS: list = []


def ok(name: str, cond: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(cond)))
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail if not cond else ""))


# --------------------------------------------------------------------------- map coverage
def parse_items(text: str) -> list:
    items, parent, fence = [], "", False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        m2 = re.match(r"^## (?:(\d+)\.\s|(Appendix [A-Z])\b)", line)
        if m2:
            parent = m2.group(1) or m2.group(2)
            items.append(parent)
            continue
        m3 = re.match(r"^### (?:(\d+\.[A-Z0-9]+)\s|(.+?)\s*$)", line)
        if m3:
            items.append(m3.group(1) if m3.group(1) else "%s/%s" % (parent, m3.group(2).strip()))
            continue
        mc = re.match(r"^- \[ \] \*\*(.+?)\*\*", line)
        if mc:
            items.append("preflight/" + mc.group(1))
    return items


def coverage_problems(items: list, doc: dict) -> list:
    rules = doc.get("rules") or []
    out = []
    for it in items:
        hit = [r for r in rules if fnmatch.fnmatchcase(it, r["match"])]
        if not hit:
            out.append("unmapped: %s" % it)
        elif len({r["dest"] for r in hit}) > 1:
            out.append("ambiguous: %s -> %s" % (it, [r["match"] for r in hit]))
    for r in rules:
        if not any(fnmatch.fnmatchcase(it, r["match"]) for it in items):
            out.append("dead rule: %s" % r["match"])
        if r.get("dest") not in DESTS:
            out.append("bad dest %s: %s" % (r["match"], r.get("dest")))
        if r.get("dest") == "ENFORCED" and not r.get("checks"):
            out.append("ENFORCED without checks: %s" % r["match"])
        if r.get("dest") == "CONFLICT" and not str(r.get("conflict") or "").strip():
            out.append("CONFLICT without its reason: %s" % r["match"])
        for cid in r.get("checks") or []:
            if cid not in taste.CHECKS:
                out.append("unknown check %s in %s" % (cid, r["match"]))
        for owner in r.get("owners") or []:
            path, _, sym = owner.partition("::")
            p = ROOT / path
            if not p.is_file():
                out.append("owner missing: %s" % owner)
            elif sym and not re.search(r"\bdef %s\b" % re.escape(sym), p.read_text(encoding="utf-8", errors="replace")):
                out.append("owner symbol missing: %s" % owner)
    claimed = {c for r in rules for c in r.get("checks") or []}
    out += ["check claimed by no rule: %s" % c for c in taste.CHECKS if c not in claimed]
    return out


def test_map() -> None:
    text = SKILL.read_text(encoding="utf-8")
    doc = json.loads(MAP.read_text(encoding="utf-8"))
    items = parse_items(text)
    probs = coverage_problems(items, doc)
    ok("V-TASTE-MAP-POPULATION", len(items) >= 150, "parsed %d items" % len(items))
    ok("V-TASTE-MAP-COVERAGE", not probs, "; ".join(probs[:8]))
    dropped = copy.deepcopy(doc)
    dropped["rules"] = [r for r in dropped["rules"] if r["match"] != "9.G"]
    ok("V-TASTE-MAP-NEG-DROPPED-RULE", any("unmapped: 9.G" in p for p in coverage_problems(items, dropped)))
    grown = parse_items(text + "\n### 9.H A brand-new upstream rule\n")
    ok("V-TASTE-MAP-NEG-NEW-UPSTREAM-RULE", any("9.H" in p for p in coverage_problems(grown, doc)))
    dests = {}
    for it in items:
        d = next(r["dest"] for r in doc["rules"] if fnmatch.fnmatchcase(it, r["match"]))
        dests[d] = dests.get(d, 0) + 1
    print("     destinations over %d items: %s" % (len(items), dict(sorted(dests.items()))))
    sha = hashlib.sha256(SKILL.read_bytes()).hexdigest()
    ok("V-TASTE-HASH", sha == doc.get("skill_sha256"), "vendored %s != map %s" % (sha[:12], str(doc.get("skill_sha256"))[:12]))


# --------------------------------------------------------------------------- per-check poles
PAGE = "<!doctype html><html><head><style>%s</style></head><body>%s<script>%s</script></body></html>"
DARK = "@media (prefers-color-scheme: dark){body{color:#eee}}"
HINT = taste._HINT_ATTR
CASES = {   # id: ((css, body, js) bad, (css, body, js) good)
    "TASTE-EMDASH": (("", "<h1>Fast — and calm</h1>", ""), ("", "<h1>Fast - and calm</h1>", "")),
    "TASTE-SCROLL-LISTENER": (("", "", "window.addEventListener('scroll', f)"), ("", "", "new IntersectionObserver(f)")),
    "TASTE-H-SCREEN": (("", '<div class="h-screen"></div>', ""), ("", '<div class="min-h-[100dvh]"></div>', "")),
    "TASTE-REDUCED-MOTION": (("a{transition: transform .2s}", "", ""),
                             ("a{transition: transform .2s} @media (prefers-reduced-motion: reduce){a{transition:none}}", "", "")),
    "TASTE-HINT-AS-LABEL": (("", '<input id="e" %s="Email">' % HINT, ""),
                            ("", '<label for="e">Email</label><input id="e" %s="you@x.es">' % HINT, "")),
    "TASTE-SCROLL-CUE": (("", "<p>Scroll to explore</p>", ""), ("", "<p>See the menu</p>", "")),
    "TASTE-QUIETLY": (("", "<h2>Quietly in use at</h2>", ""), ("", "<h2>Trusted by</h2>", "")),
    "TASTE-JANE-DOE": (("", "<p>Jane Doe, CEO</p>", ""), ("", "<p>Inés Caro, CEO</p>", "")),
    "TASTE-EYEBROW-COUNT": (("", '<section><p class="uppercase tracking-wide">A</p></section>'
                                 '<section><p class="uppercase tracking-wide">B</p></section>', ""),
                            ("", '<section><p class="uppercase tracking-wide">A</p></section><section></section>', "")),
    "TASTE-DUP-CTA-INTENT": (("", '<a href="#contact">Get in touch</a><a href="#contact">Contact us</a>', ""),
                             ("", '<a href="#contact">Get in touch</a><a href="#contact">Get in touch</a>', "")),
    "TASTE-GENERIC-BRANDS": (("", "<p>Nexus</p>", ""), ("", "<p>Olivar</p>", "")),
    "TASTE-FILLER-VERBS": (("", "<p>Elevate your team</p>", ""), ("", "<p>Plan your week</p>", "")),
    "TASTE-VERSION-STAMP": (("", "<footer><p>v1.4.2</p></footer>", ""), ("", "<footer><p>Madrid</p></footer>", "")),
    "TASTE-SECTION-NUMBERING": (("", "<p>001 · Capabilities</p>", ""), ("", "<p>Capabilities</p>", "")),
    "TASTE-STEP-LABELS": (("", "<h3>Step 1</h3>", ""), ("", "<h3>Install</h3>", "")),
    "TASTE-MARQUEE-MAX-ONE": (("", '<div class="marquee"></div><div class="marquee"></div>', ""),
                              ("", '<div class="marquee"></div>', "")),
    "TASTE-CUSTOM-CURSOR": (("body{cursor:none}", "", ""), ("body{cursor:pointer}", "", "")),
    "TASTE-PURE-BLACK-WHITE": (("body{color:#000000}", "", ""), ("body{color:#18181b}", "", "")),
    "TASTE-BANNED-SERIF": (("h1{font-family:Fraunces}", "", ""), ("h1{font-family:Satoshi}", "", "")),
    "TASTE-PREMIUM-PALETTE": (("body{background:#f5f1ea;color:#1a1714}", "", ""), ("body{background:#eef2f6}", "", "")),
    "TASTE-BROKEN-UNSPLASH": (("", '<img src="https://source.unsplash.com/x" alt="a">', ""),
                              ("", '<img src="/hero.jpg" alt="a">', "")),
    "TASTE-DARK-MODE": (("body{color:#111}", "", ""), (DARK, "", "")),
    "TASTE-GOOGLE-FONTS-LINK": (("", '<link href="https://fonts.googleapis.com/css2?family=X" rel="stylesheet">', ""),
                                ("", '<link href="fonts.css" rel="stylesheet">', "")),
    "TASTE-MIDDOT-RATION": (("", "<p>a · b · c</p>", ""), ("", "<p>a · b</p>", "")),
    "TASTE-ZINDEX-SPAM": (("a{z-index:1}b{z-index:2}c{z-index:3}d{z-index:4}e{z-index:5}", "", ""),
                          ("a{z-index:10}b{z-index:50}", "", "")),
    "TASTE-EMOJI": (("", "<p>Launch 🚀</p>", ""), ("", "<p>Launch</p>", "")),
    "TASTE-GRADIENT-TEXT": (("h1{background-clip:text}", "", ""), ("h1{color:#222}", "", "")),
}


def _page(d: str, css: str, body: str, js: str, name: str = "index.html") -> str:
    p = os.path.join(d, name)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(PAGE % (css, body, js))
    return p


def _verdict(path: str, cid: str):
    return next(v for v in taste.lint(path).verdicts if v.criterion == cid)


def test_checks() -> None:
    ok("V-TASTE-CHECK-TABLE", set(CASES) == set(taste.CHECKS), "cases %s vs checks %s"
       % (sorted(set(taste.CHECKS) - set(CASES)), sorted(set(CASES) - set(taste.CHECKS))))
    for cid, (bad, good) in sorted(CASES.items()):
        d = tempfile.mkdtemp(dir=_TMP)
        vb = _verdict(_page(d, *bad, name="bad.html"), cid)
        vg = _verdict(_page(d, *good, name="good.html"), cid)
        ok("V-TASTE-CHECK-%s" % cid[6:], vb.status == "fail" and vg.status == "pass",
           "bad=%s good=%s (%s)" % (vb.status, vg.status, vg.observed if vg.status == "fail" else vb.observed))


SLOP = ("body{background:#f5f1ea;color:#1a1714} .hero{height:100vh} a{transition: transform .3s}",
        '<header class="h-screen"><p class="uppercase tracking-widest">V0.6 · BETA · NOW</p>'
        "<h1>Elevate your workflow — seamlessly</h1><a href='#contact'>Get in touch</a>"
        "<a href='#contact'>Let's talk</a><p>Scroll to explore</p></header><section>"
        "<p class='uppercase tracking-wide'>001 · Capabilities</p><p>Quietly trusted by Acme Inc</p></section>"
        "<section><p class='eyebrow'>X</p><input type='email' %s='Your email'></section>" % HINT,
        "window.addEventListener('scroll', () => {});")
CLEAN = ("body{background:#f4f4f5;color:#18181b} a{transition: transform .3s} " + DARK +
         " @media (prefers-reduced-motion: reduce){a{transition:none}}",
         '<header class="min-h-[100dvh]"><h1>Plan the week in ten minutes</h1><a href="#contact">Get in touch</a>'
         '</header><section><h2>Trusted by</h2><p>Inés Caro, Olivar</p></section>'
         '<section id="contact"><label for="e">Email</label><input id="e" type="email" %s="you@olivar.es"></section>'
         % HINT, "new IntersectionObserver(() => {});")
CRITICAL = sorted(k for k, v in taste.CHECKS.items() if v[1] == "critical")


def test_slop_and_waiver() -> None:
    d = tempfile.mkdtemp(dir=_TMP)
    slop = taste.lint(_page(d, *SLOP, name="slop.html"))
    ok("V-TASTE-SLOP", sorted(slop.blocking) == CRITICAL, "blocking=%s" % slop.blocking)
    clean = taste.lint(_page(d, *CLEAN, name="clean.html"))
    ok("V-TASTE-CLEAN", clean.blocking == [], "blocking=%s" % clean.blocking)
    w = tempfile.mkdtemp(dir=_TMP)
    p = _page(w, "", "<h1>Fast — calm</h1><p>Step 1</p>", "")
    Path(w, "DESIGN.md").write_text("---\naesthetic_family: F1\ntaste_overrides:\n"
                                    "  - TASTE-EMDASH: brand style guide mandates the em-dash in its tagline\n"
                                    "  - TASTE-STEP-LABELS\n---\n# x\n", encoding="utf-8")
    rep = taste.lint(p)
    ok("V-TASTE-WAIVER", "TASTE-EMDASH" in rep.waived and "TASTE-EMDASH" not in rep.blocking
       and rep.refused_waivers == ["TASTE-STEP-LABELS"], "waived=%s refused=%s blocking=%s"
       % (rep.waived, rep.refused_waivers, rep.blocking))
    Path(w, "DESIGN.md").write_text("---\ntaste_overrides:\n  - TASTE-EMDASH\n---\n", encoding="utf-8")
    ok("V-TASTE-WAIVER-NEEDS-REASON", "TASTE-EMDASH" in taste.lint(p).blocking)


def test_kind() -> None:
    from modules.tower import checks as ck
    d = tempfile.mkdtemp(dir=_TMP)
    _page(d, *SLOP, name="index.html")
    os.makedirs(os.path.join(d, "ok"))
    _page(os.path.join(d, "ok"), *CLEAN, name="index.html")
    out = {name: ck.evaluate({"id": "x", "check": "taste:%s" % rel}, d).outcome
           for name, rel in (("slop", "index.html"), ("clean", "ok/index.html"), ("missing", "nope.html"),
                             ("escape", "../index.html"))}
    ok("V-TASTE-KIND", out == {"slop": ck.FAIL, "clean": ck.PASS, "missing": ck.UNREADABLE, "escape": ck.REFUSED_PATH},
       str(out))
    ok("V-TASTE-KIND-STATIC", "taste" in ck.STATIC_KINDS)


def test_external_assets() -> None:
    """M3/L2 (review of bb4db9f4): assets and DESIGN.md outside the page's folder, both poles."""
    from modules.tower import checks as ck
    r = tempfile.mkdtemp(dir=_TMP)
    for sub in ("public", "assets", "css", "site", "site2"):
        os.makedirs(os.path.join(r, sub))
    rm = "@media (prefers-reduced-motion: reduce){a{transition:none}}"
    for rel in ("assets/site.css", "css/site.css", "site2/m.css"):
        Path(r, rel).write_text(rm, encoding="utf-8")
    moving = "a{transition: transform .3s}"
    root_rel = _page(os.path.join(r, "public"), moving, '<link href="/assets/site.css" rel="stylesheet">', "")
    up_rel = _page(os.path.join(r, "public"), moving, '<link href="../css/site.css" rel="stylesheet">', "",
                   name="up.html")
    sib = _page(os.path.join(r, "site"), moving, '<link href="../site2/m.css" rel="stylesheet">', "")
    st = lambda p, root=None: next(v.status for v in taste.lint(p, site_root=root).verdicts  # noqa: E731
                                   if v.criterion == "TASTE-REDUCED-MOTION")
    ok("V-TASTE-ASSET-ROOT-RELATIVE", st(root_rel, r) == "pass" and st(root_rel) == "fail",
       "with root=%s without=%s" % (st(root_rel, r), st(root_rel)))
    ok("V-TASTE-ASSET-PARENT", st(up_rel, r) == "pass")
    ok("V-TASTE-ASSET-SIBLING-PREFIX", st(sib, os.path.join(r, "site")) == "fail",
       "site2/ must not count as inside site/")
    ok("V-TASTE-KIND-ROOT-ASSET", ck.evaluate({"id": "x", "check": "taste:public/index.html"}, r).outcome == ck.PASS)
    w = tempfile.mkdtemp(dir=_TMP)
    os.makedirs(os.path.join(w, "public"))
    _page(os.path.join(w, "public"), "", "<h1>Fast — calm</h1>", "")
    before = ck.evaluate({"id": "x", "check": "taste:public/index.html"}, w).outcome
    Path(w, "DESIGN.md").write_text("---\ntaste_overrides:\n  - TASTE-EMDASH: brand tagline mandates it\n---\n",
                                    encoding="utf-8")
    after = ck.evaluate({"id": "x", "check": "taste:public/index.html"}, w)
    ok("V-TASTE-ROOT-DESIGN-WAIVER", before == ck.FAIL and after.outcome == ck.PASS and "TASTE-EMDASH" in after.detail,
       "before=%s after=%s %s" % (before, after.outcome, after.detail))


WEB_PROMPT = "Hazme una landing page para una academia de yoga con formulario de contacto"


def test_family_block() -> None:
    from modules.gsd_x import cli
    from modules.tower import baselines as bl
    web = cli.family_block(WEB_PROMPT, {"session_id": "S-WEB"})
    other = cli.family_block("Refactoriza el parser de logs del servidor", {})
    ok("V-TASTE-BLOCK", "design-taste-frontend" in web and "NO APLICA: <entry-id>: <reason>" in web
       and "Design Read" in web, web[-400:])
    ok("V-TASTE-BLOCK-SILENT-ELSEWHERE", "design-taste-frontend" not in other)
    # M1: the block may claim the done-gate lints the page only when an ACTIVE entry carries a taste: check.
    gated = any(str(e.get("check") or "").startswith("taste:") for e in bl.active_entries("web_surface", None))
    claims = "judged by the done-gate (`taste:` checks)" in web
    ok("V-TASTE-BLOCK-CLAIM-HONEST", claims == gated and (gated or "python -m modules.cdio.taste" in web),
       "gated=%s claims=%s" % (gated, claims))
    # L1: the writer honours CPP_TOWER_STATE_DIR, so this run's row lands in the private dir, not the live ledger.
    led = Path(os.environ["CPP_TOWER_STATE_DIR"]) / "consumption.jsonl"
    rows = [json.loads(x) for x in led.read_text(encoding="utf-8").splitlines() if x.strip()] if led.exists() else []
    ok("V-TASTE-BLOCK-PRIVATE-LEDGER", any(r.get("sid") == "S-WEB" and r.get("family") == "web_surface"
                                           and r.get("kind") == "family" for r in rows), "rows=%d" % len(rows))


def _load_stop():
    spec = importlib.util.spec_from_file_location("family_donegate_stop", ROOT / "tools" / "family_donegate_stop.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _site(member: bool = True) -> str:
    d = tempfile.mkdtemp(dir=_TMP)
    _page(d, *CLEAN, name="index.html")                     # no privacy / terms page -> B5 regex entries VIOLATED
    if member:
        Path(d, "vercel.json").write_text("{}", encoding="utf-8")   # a web_surface repo marker
    return d


def _transcript(text: str) -> str:
    tr = tempfile.mktemp(suffix=".jsonl", dir=_TMP)
    Path(tr).write_text(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}})
                        + "\n", encoding="utf-8")
    return tr


def _stop_rows(sid: str) -> list:
    led = Path(os.environ["CPP_TOWER_STATE_DIR"]) / "donegate_stop.jsonl"
    rows = [json.loads(x) for x in led.read_text(encoding="utf-8").splitlines() if x.strip()] if led.exists() else []
    return [r for r in rows if r.get("sid") == sid]


def test_stop_hook() -> None:
    from modules.gsd_x import cli
    stop = _load_stop()
    state = Path(os.environ["CPP_TOWER_STATE_DIR"])
    # L1: the rows come from the real writer (test_family_block wrote S-WEB), never hand-shaped.
    ok("V-TASTE-STOP-READS-WRITER", stop.families_shown("S-WEB") == ["web_surface"], str(stop.families_shown("S-WEB")))
    base = {"session_id": "S-WEB", "cwd": _site(), "transcript_path": _transcript("done")}
    first = stop.decide(dict(base))
    ok("V-TASTE-STOP-BLOCKS", bool(first) and first.get("decision") == "block"
       and "web_surface-privacy-page-linked" in first.get("reason", ""), str(first)[:300])
    ok("V-TASTE-STOP-NO-LOOP", stop.decide(dict(base)) is None)
    ok("V-TASTE-STOP-ACTIVE", stop.decide(dict(base, stop_hook_active=True)) is None)
    ok("V-TASTE-STOP-UNRELATED", stop.decide(dict(base, session_id="S-OTHER")) is None)
    # M2: a repo PROVEN outside the family is skipped (and ledgered); the same page in a member repo blocks.
    cli.family_block(WEB_PROMPT, {"session_id": "S-OUT"})
    out = stop.decide({"session_id": "S-OUT", "cwd": _site(member=False), "transcript_path": _transcript("done")})
    ok("V-TASTE-STOP-NON-MEMBER-SKIPPED", out is None and any(r.get("decision") == "skipped" for r in _stop_rows("S-OUT")),
       "out=%s rows=%s" % (str(out)[:120], _stop_rows("S-OUT")))
    # M4: the waiver is proven by the ledger verdict, and the same repo without the NO APLICA lines blocks.
    na_text = ("NO APLICA: web_surface-privacy-page-linked: internal staff tool, no public visitors\n"
               "NO APLICA: web_surface-terms-page-linked: internal staff tool, no public visitors")
    site2 = _site()
    for sid in ("S-NA", "S-NA-CTRL"):
        cli.family_block(WEB_PROMPT, {"session_id": sid})
    second = stop.decide({"session_id": "S-NA", "cwd": site2, "transcript_path": _transcript(na_text)})
    verdicts = next((r.get("verdicts") or {} for r in _stop_rows("S-NA") if r.get("family") == "web_surface"
                     and "verdicts" in r), {})
    reason = (second or {}).get("reason", "")
    ok("V-TASTE-STOP-NA", verdicts.get("web_surface-privacy-page-linked") == "NOT_APPLICABLE"
       and verdicts.get("web_surface-terms-page-linked") == "NOT_APPLICABLE"
       and "privacy-page-linked" not in reason and "terms-page-linked" not in reason,
       "verdicts=%s reason=%s" % ({k: v for k, v in verdicts.items() if "page-linked" in k}, reason[:200]))
    ctrl = stop.decide({"session_id": "S-NA-CTRL", "cwd": site2, "transcript_path": _transcript("done")})
    ok("V-TASTE-STOP-NA-CONTROL", bool(ctrl) and "privacy-page-linked" in ctrl.get("reason", ""), str(ctrl)[:200])
    led = state / "donegate_stop.jsonl"
    ledger = led.read_text(encoding="utf-8") if led.exists() else ""
    ok("V-TASTE-STOP-LEDGER", '"decision": "block"' in ledger and '"sid": "S-WEB"' in ledger)


def test_lens_and_wiring() -> None:
    doc = json.loads(MAP.read_text(encoding="utf-8"))
    lens = (ROOT / "vault" / "knowledge_base" / "cdio" / "CDIO-05-design-review-pipeline.md").read_text(encoding="utf-8")
    render = [r["match"][len("preflight/"):] for r in doc["rules"]
              if r["dest"] == "RENDER_REVIEW" and r["match"].startswith("preflight/")]
    missing = [t for t in render if t not in lens]
    ok("V-TASTE-LENS", "Taste pre-flight lens" in lens and not missing, "missing in CDIO-05: %s" % missing[:5])
    disp = (ROOT / "hooks" / "hook-dispatcher.js").read_text(encoding="utf-8")
    i = disp.find("'Stop-chain': [")
    ok("V-TASTE-WIRED", i >= 0 and "tools/family_donegate_stop.py" in disp[i:i + 20000])


def main() -> int:
    try:
        for t in (test_map, test_checks, test_slop_and_waiver, test_kind, test_external_assets, test_family_block,
                  test_stop_hook,
                  test_lens_and_wiring):
            try:
                t()
            except Exception as exc:  # noqa: BLE001 -- a crashed section is a FAIL, never a skip
                ok("V-TASTE-CRASH-%s" % t.__name__, False, "%s: %s" % (type(exc).__name__, exc))
    finally:
        shutil.rmtree(_TMP, ignore_errors=True)
    passed = sum(1 for _, c in RESULTS if c)
    print("V-TASTE: %d passed, %d failed" % (passed, len(RESULTS) - passed))
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
