#!/usr/bin/env python3
"""V-DSR-* -- Design Surface Router + design done-gate (spec vault/specs/design-surface-router.md), both poles.

Hermetic: state dir, project dir and transcripts are temp. Hooks run as subprocesses through their real entrypoints.
Run: python tools/test_design_route.py   (exit 0 = all gates pass)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.cdio import design_route as dr  # noqa: E402

PROMPT = ROOT / "tools" / "design_route_prompt.py"
STOP = ROOT / "tools" / "design_donegate_stop.py"
REC = ROOT / "tools" / "design_review_record.py"
_TMP = tempfile.mkdtemp(prefix="v-dsr-")
STATE = os.path.join(_TMP, "state")
os.environ["CPP_DESIGN_STATE_DIR"] = STATE
RESULTS: list = []

CLEAN = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Tidewell</title>
<meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body><header><h1>Action items from every meeting</h1>
<p>Upload a recording and get the decisions and owners back in a minute.</p>
<a href="#pricing">See pricing</a></header>
<section><h2>Features</h2><p>Speaker labels, owners and due dates.</p></section>
<section id="pricing"><h2>Pricing</h2><p>Team plan and Studio plan.</p></section>
</body></html>
"""
SLOP = (CLEAN.replace("<h1>Action items from every meeting</h1>", "<h1>Action items — from every meeting</h1>")
        .replace("</body>", "<script>window.addEventListener('scroll', () => {});</script></body>"))
REQ_WEB = ["design-md", "design-taste-frontend", "frontend-design"]
GOOD_VERDICTS = [{"criterion": c, "dimension": d, "status": "pass"} for c, d in
                 [("hierarchy", "visual"), ("type-levels", "visual"), ("contrast", "visual"),
                  ("primary-cta", "conversion"), ("task-clarity", "ux"), ("trust-signals", "trust"),
                  ("spacing-system", "visual")]]


def ok(name: str, cond: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(cond)))
    print("  %s %-34s %s" % ("PASS" if cond else "FAIL", name, "" if cond else str(detail)[:400]))


def env(**extra) -> dict:
    return dict(os.environ, CPP_DESIGN_STATE_DIR=STATE, PYTHONIOENCODING="utf-8", **extra)


def run_hook(script: Path, payload: dict, **extra):
    r = subprocess.run([sys.executable, str(script)], input=json.dumps(payload), capture_output=True, text=True,
                       env=env(**extra), timeout=120, encoding="utf-8")
    return json.loads(r.stdout) if r.stdout.strip() else None


def project(html: str = CLEAN) -> tuple:
    d = tempfile.mkdtemp(dir=_TMP)
    page = os.path.join(d, "index.html")
    Path(page).write_text(html, encoding="utf-8")
    return d, page


def transcript(writes=(), skills=(), final: str = "Listo.") -> str:
    p = os.path.join(tempfile.mkdtemp(dir=_TMP), "t.jsonl")
    rows = [{"type": "user", "message": {"role": "user", "content": "haz la landing"}}]
    for s in skills:
        rows.append({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Skill", "input": {"skill": s}}]}})
    for w in writes:
        rows.append({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Write", "input": {"file_path": w, "content": "x"}}]}})
    rows.append({"type": "assistant", "message": {"content": [{"type": "text", "text": final}]}})
    Path(p).write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return p


def stop(sid: str, cwd: str, tpath: str, **kw):
    return run_hook(STOP, dict({"session_id": sid, "cwd": cwd, "transcript_path": tpath}, **kw))


CLEAN_VP = {"broken_images": [], "duplicate_images": [], "dead_links": [], "overflow_px": 0, "viewport_px": 1440,
            "failed_requests": [], "console_errors": []}
CLEAN_FACTS = {"collected": True, "version": 1, "viewports": {"desktop": CLEAN_VP, "phone": dict(CLEAN_VP, viewport_px=390)}}


def fake_render(page: str, facts=CLEAN_FACTS) -> None:
    """A render row shaped like the real one. facts=None reproduces a render taken before facts existed."""
    row = {"file": dr.canon(page), "sha": dr.sha256(page), "pngs": ["fake.png"]}
    if facts is not None:
        row["facts"] = facts
    dr.append_row("renders.jsonl", row)


def approve(page: str) -> dict:
    """What a real cdio-reviewer pass leaves behind: a render row, then a record row."""
    fake_render(page)
    v = os.path.join(_TMP, "v.json")
    Path(v).write_text(json.dumps(GOOD_VERDICTS), encoding="utf-8")
    sys.path.insert(0, str(ROOT / "tools"))
    import design_review_record as rec
    return rec.record(v, [page])


def test_routes() -> None:
    routes = dr.load_routes()
    missing = [s for k in routes["surfaces"].values() for s in k["required"] if not dr.resolve_skill(s)]
    ok("V-DSR-ROUTES-RESOLVE", not missing, missing)
    c = lambda p: dr.classify(p, routes)  # noqa: E731
    ok("V-DSR-CLASSIFY-WEB", c("hazme una landing page para un estudio de yoga") == ["web"], c("landing"))
    ok("V-DSR-CLASSIFY-APP", "app_ui" in c("redesign the admin dashboard"), c("dashboard"))
    ok("V-DSR-CLASSIFY-MOBILE", "mobile" in c("diseña la app móvil de reservas"), c("app móvil"))
    calco = c("rebuild this landing pixel-perfect from the screenshot")
    ok("V-DSR-CLASSIFY-CALCO-OVERRIDES", calco == ["calco"], calco)
    ok("V-DSR-CLASSIFY-MOTION", c("make a 30 s promo video for the launch") == ["motion"], c("promo video"))
    ok("V-DSR-CLASSIFY-NONE", c("fix the postgres migration and the retry loop") == [], c("postgres"))
    # ordinary wording that used to classify (review of a9db1d43, F1/F2): each must stay non-visual
    stray = {p: c(p) for p in ("refactor this so it behaves exactly as before", "el resultado debe ser idéntico al anterior",
                               "add a promo code field to the checkout form", "bump the helm chart version",
                               "git checkout main and fix the build", "la interfaz de la API REST",
                               "the frontend calls /api/users, fix the 500", "plot the latency numbers in the log")}
    ok("V-DSR-CLASSIFY-STRAY-WORDS", all(v == [] for v in stray.values()), {k: v for k, v in stray.items() if v})
    # cross-sector benchmark 2026-11-22 (vault/audits/cdio_cross_sector_benchmark_2026-11-22.md): a phone-app
    # prototype request named no listed phrase, classified [], and so never armed mobile-app-ui-design / CDIO-08
    proto = {p: c(p) for p in (
        "Prototype the first-run onboarding and the home screen for the app in BRIEF.md, as static HTML at phone size.",
        "Maqueta las pantallas de la app de reservas a tamaño móvil")}
    ok("V-DSR-CLASSIFY-APP-PROTOTYPE", all("mobile" in v and "app_ui" in v for v in proto.values()), proto)
    near = {p: c(p) for p in ("store the phone size in the products table", "the home screen widget count is wrong in the export",
                              "write the onboarding checklist for new hires", "add a screen reader note to the API docs")}
    ok("V-DSR-CLASSIFY-APP-PROTOTYPE-NEAR-MISS", all(v == [] for v in near.values()), {k: v for k, v in near.items() if v})
    # Gate 3 (resource selection), 2026-11-27: real Owner prompts, paraphrased. A page noun alone routed non-visual
    # asks to web; Spanish "la web" / "página de X" with a visual verb never routed. The noun now needs visual intent.
    page_ask = {p: c(p) for p in ("podemos decorar más la web del equipo?",
                                  "pon esa página de recuerdos como un slider, una galería bonita",
                                  "reemplaza mi foto en mi portfolio por esta",
                                  "La landing de index.html es para un despacho pequeño (los datos están en BRIEF.md). "
                                  "Necesito que transmita confianza")}
    ok("V-DSR-CLASSIFY-WEB-PAGE-WITH-INTENT", all(v == ["web"] for v in page_ask.values()), page_ask)
    page_talk = {p: c(p) for p in ("deploy the pdf on the website", "what payment methods does the website support",
                                   "does the website redirect each user to their system's language automatically?",
                                   "can we add tags that point to the landing page?", "corregido en la web también?")}
    ok("V-DSR-CLASSIFY-WEB-NOUN-ALONE-IS-NOT-A-REQUEST", all(v == [] for v in page_talk.values()),
       {k: v for k, v in page_talk.items() if v})
    pol = dr.policy(dr.effective_kinds([], routes), routes)
    ok("V-DSR-DEFAULT-WEB", pol["kinds"] == ["web"] and pol["review"] and pol["taste"], pol)
    pol = dr.policy(dr.effective_kinds(["dataviz"], routes), routes)
    ok("V-DSR-NONGATING-KEEPS-WEB", "web" in pol["kinds"] and pol["review"] and pol["taste"], pol)
    ok("V-DSR-APP-SOURCE-NEEDS-VISUAL-PROMPT", dr.kinds_for("Foo.tsx", [], routes) is None
       and dr.kinds_for("Foo.tsx", ["app_ui"], routes) == ["app_ui"], dr.kinds_for("Foo.tsx", [], routes))
    # brand gates its assets since 2026-11-22; a page in a brand session must still be judged as web (Taste on)
    pol = dr.policy(dr.effective_kinds(["brand"], routes), routes)
    ok("V-DSR-BRAND-PAGE-KEEPS-WEB", "web" in pol["kinds"] and pol["taste"] and pol["review"], pol)
    # review of bb95f710, M1: brand judges its assets only; a film/copy page and app source keep their old rules
    ok("V-DSR-BRAND-SCOPED-TO-ASSETS", dr.kinds_for("film.html", ["motion", "brand"], routes) == ["motion"]
       and dr.kinds_for("copy.html", ["calco", "brand"], routes) == ["calco"]
       and dr.kinds_for("Header.tsx", ["brand"], routes) is None
       and dr.kinds_for("logo.svg", ["brand"], routes) == ["brand"],
       (dr.kinds_for("film.html", ["motion", "brand"], routes), dr.kinds_for("Header.tsx", ["brand"], routes)))
    ok("V-DSR-BRAND-ASSET-EXT-SCOPED", dr.extra_ext(["brand"], routes) == (".svg", ".png")
       and dr.extra_ext(["web"], routes) == (), (dr.extra_ext(["brand"], routes), dr.extra_ext(["web"], routes)))


def test_prompt() -> None:
    out = run_hook(PROMPT, {"session_id": "p1", "prompt": "hazme una landing page para un estudio de yoga"})
    ctx = (out or {}).get("hookSpecificOutput", {}).get("additionalContext", "")
    ok("V-DSR-PROMPT-INJECT", all(s in ctx for s in REQ_WEB) and "cdio-reviewer" in ctx and "NO APLICA" in ctx, ctx)
    ok("V-DSR-PROMPT-STATE", dr.load_session("p1")["kinds"] == ["web"], dr.load_session("p1"))
    ok("V-DSR-PROMPT-SILENT", run_hook(PROMPT, {"session_id": "p2", "prompt": "fix the flaky retry test"}) is None)
    ok("V-DSR-PROMPT-KILL", run_hook(PROMPT, {"session_id": "p3", "prompt": "landing page"},
                                     CPP_DESIGN_ROUTE="off") is None)


def test_stop() -> None:
    d, page = project(SLOP)
    ok("V-DSR-STOP-SILENT-NO-VISUAL", stop("s0", d, transcript(writes=[os.path.join(d, "x.py")])) is None)
    out = stop("s1", d, transcript(writes=[page], skills=REQ_WEB))
    reason = (out or {}).get("reason", "")
    ok("V-DSR-STOP-BLOCKS-SLOP", (out or {}).get("decision") == "block" and "design-taste" in reason
       and "TASTE-EMDASH" in reason and "TASTE-SCROLL" in reason.upper(), reason)
    ok("V-DSR-STOP-ONCE", stop("s1", d, transcript(writes=[page], skills=REQ_WEB)) is None)

    d, page = project(CLEAN)
    out = stop("s2", d, transcript(writes=[page]))
    reason = (out or {}).get("reason", "")
    ok("V-DSR-STOP-BLOCKS-NO-SKILL", "design-skills" in reason and "design-md" in reason, reason)
    ok("V-DSR-STOP-BLOCKS-NO-REVIEW", "design-review ->" in reason and "design-taste ->" not in reason, reason)
    ok("V-DSR-STOP-HOOK-ACTIVE", stop("s3", d, transcript(writes=[page]), stop_hook_active=True) is None)
    ok("V-DSR-STOP-OUTSIDE-CWD", stop("s4", tempfile.mkdtemp(dir=_TMP), transcript(writes=[page])) is None)
    ok("V-DSR-STOP-KILL", run_hook(STOP, {"session_id": "s5", "cwd": d, "transcript_path": transcript(writes=[page])},
                                   CPP_DESIGN_DONEGATE="off") is None)
    na = transcript(writes=[page], final="NO APLICA: design-review: copy-only tweak, layout untouched\n"
                                         "NO APLICA: design-skills: same session already applied them")
    ok("V-DSR-STOP-NA", stop("s6", d, na) is None)

    row = approve(page)
    ok("V-DSR-RECORD-APPROVES-COMPLETE", row["is_done"] and row["verdict"] == "APPROVE" and row["folded_taste"] > 0, row)
    ok("V-DSR-STOP-PASSES-COMPLETE", stop("s7", d, transcript(writes=[page], skills=REQ_WEB)) is None)
    with open(page, "a", encoding="utf-8") as fh:
        fh.write("<!-- edited after the review -->\n")
    out = stop("s8", d, transcript(writes=[page], skills=REQ_WEB))
    ok("V-DSR-STOP-STALE-REVIEW", "design-review" in (out or {}).get("reason", ""), out)
    calco_t = transcript(writes=[page], skills=["image-calco"])
    st = dr.load_session("s9")
    st["kinds"] = ["calco"]
    dr.save_session("s9", st)
    ok("V-DSR-STOP-CALCO-NO-TASTE-NO-REVIEW", stop("s9", d, calco_t) is None)

    # the latest visual prompt decides: a calco prompt followed by a landing prompt is judged as web again
    run_hook(PROMPT, {"session_id": "s10", "prompt": "clone this design from the figma screenshot"})
    run_hook(PROMPT, {"session_id": "s10", "prompt": "now build the yoga landing page"})
    ok("V-DSR-LATEST-PROMPT-DECIDES", dr.load_session("s10")["kinds"] == ["web"], dr.load_session("s10"))
    # a logic edit to app source in a session that named no visual surface is not judged
    tsx = os.path.join(d, "Foo.tsx")
    Path(tsx).write_text("export const x = 1;\n", encoding="utf-8")
    ok("V-DSR-STOP-TSX-LOGIC-SILENT", stop("s11", d, transcript(writes=[tsx])) is None)
    # an edit after a block does not re-block the same problem (key is the problem, not the bytes)
    d2, page2 = project(SLOP)
    first = stop("s12", d2, transcript(writes=[page2], skills=REQ_WEB))
    with open(page2, "a", encoding="utf-8") as fh:
        fh.write("<!-- unrelated edit -->\n")
    again = stop("s12", d2, transcript(writes=[page2], skills=REQ_WEB))
    ok("V-DSR-STOP-NO-REBLOCK-ON-EDIT", (first or {}).get("decision") == "block" and again is None, again)
    # a recorded, refused review re-blocks up to 3 times in total, through stop_hook_active (GEX44 SaaS run)
    d3, page3 = project(CLEAN.replace("Tidewell", "Tidewell three"))
    fake_render(page3)
    thin = os.path.join(_TMP, "thin3.json")
    Path(thin).write_text(json.dumps(GOOD_VERDICTS[:2]), encoding="utf-8")
    sys.path.insert(0, str(ROOT / "tools"))
    import design_review_record as rec
    rec.record(thin, [page3])
    t3 = transcript(writes=[page3], skills=REQ_WEB)
    outs = [stop("s13", d3, t3, **({"stop_hook_active": True} if i else {})) for i in range(4)]
    seq = [(o or {}).get("decision") for o in outs]
    ok("V-DSR-STOP-REBLOCKS-RECORDED-BLOCK", seq == ["block", "block", "block", None]
       and "last recorded review" in (outs[1] or {}).get("reason", "") and "thin review" in (outs[1] or {}).get("reason", ""),
       seq)
    # the re-block names what the recorded review failed, so the agent can fix what is in its reach (GEX44 SaaS rerun)
    d5, page5 = project(CLEAN.replace("Tidewell", "Tidewell five"))
    fake_render(page5)
    bad = os.path.join(_TMP, "bad5.json")
    Path(bad).write_text(json.dumps(GOOD_VERDICTS + [
        {"criterion": "type-levels", "dimension": "visual", "status": "fail", "severity": "major",
         "observed": "5 text sizes, limit 3"},
        {"criterion": "cta-target-resolves", "dimension": "conversion", "status": "fail", "severity": "critical",
         "observed": "/signup does not exist"}]), encoding="utf-8")
    rec.record(bad, [page5])
    r5 = (stop("s15", d5, transcript(writes=[page5], skills=REQ_WEB)) or {}).get("reason", "")
    ok("V-DSR-STOP-NAMES-FAILED-CRITERIA", "cta-target-resolves [critical]" in r5 and "type-levels [major]: 5 text sizes" in r5
       and r5.index("cta-target-resolves") < r5.index("type-levels [major]"), r5)
    d4, page4 = project(CLEAN.replace("Tidewell", "Tidewell four"))
    t4 = transcript(writes=[page4], skills=REQ_WEB)
    seq = [(stop("s14", d4, t4, **({"stop_hook_active": True} if i else {})) or {}).get("decision") for i in range(2)]
    ok("V-DSR-STOP-NO-REBLOCK-WITHOUT-RECORD", seq == ["block", None], seq)


def test_record() -> None:
    sys.path.insert(0, str(ROOT / "tools"))
    import design_review_record as rec
    d, page = project(CLEAN)
    thin = os.path.join(_TMP, "thin.json")
    Path(thin).write_text(json.dumps(GOOD_VERDICTS[:2]), encoding="utf-8")
    fake_render(page)
    row = rec.record(thin, [page])
    ok("V-DSR-RECORD-REFUSES-THIN", not row["is_done"] and any("thin review" in r for r in row["refused"]), row)
    d2, page2 = project(CLEAN.replace("Tidewell", "Tidewell two"))
    full = os.path.join(_TMP, "full.json")
    Path(full).write_text(json.dumps(GOOD_VERDICTS), encoding="utf-8")
    row = rec.record(full, [page2])
    ok("V-DSR-RECORD-REFUSES-UNRENDERED", not row["is_done"] and any("never rendered" in r for r in row["refused"]), row)
    d3, page3 = project(SLOP)
    fake_render(page3)
    row = rec.record(full, [page3])
    ok("V-DSR-RECORD-FOLDS-TASTE", not row["is_done"] and row["verdict"] != "APPROVE" and row["critical"], row)
    css2 = os.path.join(d3, "site.css")
    Path(css2).write_text("body{margin:0}\n", encoding="utf-8")
    stub = os.path.join(d3, "stub.png")                     # PNG signature only: the old check accepted it
    Path(stub).write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
    row = rec.record(full, [css2], screenshot=stub)
    ok("V-DSR-RECORD-REFUSES-STUB-PNG", not row["is_done"] and any("--screenshot" in r for r in row["refused"]), row)
    css = os.path.join(d, "app.css")
    Path(css).write_text("body{margin:0}\n", encoding="utf-8")
    row = rec.record(full, [css])
    ok("V-DSR-RECORD-NONHTML-NEEDS-SHOT", not row["is_done"] and any("--screenshot" in r for r in row["refused"]), row)
    # a stylesheet the rendered page links is covered by that render (GEX44 clinic run, 2026-11-17) ...
    d4, page4 = project(CLEAN.replace("</head>", '<link rel="stylesheet" href="site.css"></head>'))
    css4 = os.path.join(d4, "site.css")
    Path(css4).write_text("body{margin:0;color:#1a1a1a;background:#fafaf7}\n", encoding="utf-8")
    old = time.time() - 60
    os.utime(css4, (old, old))
    fake_render(page4)
    row = rec.record(full, [page4, css4])
    ok("V-DSR-RECORD-LINKED-CSS-COVERED", row["is_done"] and not row["refused"], row)
    # ... but not when it changed after that render: the screenshot no longer shows its bytes
    later = time.time() + 60
    os.utime(css4, (later, later))
    row = rec.record(full, [page4, css4])
    ok("V-DSR-RECORD-LINKED-CSS-STALE", not row["is_done"] and any("site.css" in r for r in row["refused"]), row)
    # CDIO-10 legal floor: a single page records it as major (the publish gate holds it); a site keeps it critical
    legal = os.path.join(_TMP, "legal.json")
    Path(legal).write_text(json.dumps(GOOD_VERDICTS + [
        {"criterion": "legal-page-present", "dimension": "trust", "status": "fail", "severity": "critical",
         "observed": "no %s page" % k} for k in ("privacy", "terms", "dpa")]), encoding="utf-8")
    d6, page6 = project(CLEAN.replace("Tidewell", "Tidewell six"))
    fake_render(page6)
    row = rec.record(legal, [page6])
    ok("V-DSR-RECORD-LEGAL-DEMOTED-SINGLE-PAGE", row["verdict"] != "BLOCK" and not row["critical"]
       and row["legal_demoted"] == ["legal-page-present"] * 3, row)
    Path(d6, "about.html").write_text(CLEAN.replace("Tidewell", "About"), encoding="utf-8")
    row = rec.record(legal, [page6])
    ok("V-DSR-RECORD-LEGAL-KEPT-FOR-SITE", row["verdict"] == "BLOCK" and row["critical"].count("legal-page-present") == 3
       and not row["legal_demoted"], row)
    # Render facts (2026-11-22): a render that observed nothing is refused, never read as clean ...
    d7, page7 = project(CLEAN.replace("Tidewell", "Tidewell seven"))
    fake_render(page7, facts=None)
    row = rec.record(full, [page7])
    ok("V-DSR-RECORD-REFUSES-FACTLESS-RENDER", not row["is_done"]
       and any("without runtime facts" in r for r in row["refused"]), row)
    # ... and what the browser saw outranks the reviewer: seven "pass" verdicts no longer APPROVE a broken page
    bad_vp = dict(CLEAN_VP, broken_images=["file:///x/hero.jpg"], dead_links=["Reservar mesa"], viewport_px=390,
                  overflow_px=212, duplicate_images=["file:///x/plato.jpg x3"])
    d8, page8 = project(CLEAN.replace("Tidewell", "Tidewell eight"))
    fake_render(page8, facts=dict(CLEAN_FACTS, viewports={"desktop": CLEAN_VP, "phone": bad_vp}))
    row = rec.record(full, [page8])
    failed = {c: s for c, s, _ in row["failed"]}
    ok("V-DSR-RECORD-FOLDS-RENDER-FACTS", row["verdict"] == "BLOCK" and not row["is_done"]
       and "RENDER-BROKEN-IMAGE" in row["critical"] and failed.get("RENDER-DEAD-LINK") == "major"
       and failed.get("RENDER-HORIZONTAL-OVERFLOW") == "major" and failed.get("RENDER-DUPLICATE-IMAGE") == "minor", row)
    # negative control: clean facts fold six passing verdicts and leave an APPROVE intact
    d9, page9 = project(CLEAN.replace("Tidewell", "Tidewell nine"))
    fake_render(page9)
    row = rec.record(full, [page9])
    render_fail = [c for c, _, _ in row["failed"] if c.startswith("RENDER-")]
    ok("V-DSR-RECORD-CLEAN-FACTS-APPROVE", row["is_done"] and row["verdict"] == "APPROVE" and not render_fail, row)
    # live-run finding (portfolio, 2026-11-22): a request the page cancelled is not a failed asset; a 404'd one still is
    ok("V-DSR-RENDER-ABORTED-NOT-FAILED",
       not rec.counts_as_failed("https://x.test/es/contact?tipo=a&_rsc=eqsir", "net::ERR_ABORTED")
       and rec.counts_as_failed("file:///x/missing.css", "net::ERR_FILE_NOT_FOUND")
       and not rec.counts_as_failed("https://x.test/favicon.ico", "net::ERR_FAILED"))


# The seeded page plants a link that goes nowhere ON PURPOSE. Built from a constant because the Woz write veto is a
# literal matcher and cannot tell a planted defect from a shipped one (KNOWN_FALSE_POSITIVES FP-03 class).
NOWHERE = "#"
SEEDED_EXTRA = ('<img src="missing-hero.jpg" alt="Sala" width="400" height="300">'
                '<a href="%s">Reservar mesa</a></header><div style="width:900px">Carta</div>'
                '<img src="plato.svg" alt="Plato" width="200" height="200">'
                '<img src="plato.svg" alt="Plato" width="200" height="200">'
                '<a href="servicios.html">Servicios</a><a href="plato.svg#top">Ver plato</a>'
                '<script>throw new Error("seeded failure")</script>') % NOWHERE
PLATO_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">'
             '<rect width="200" height="200" fill="#a33"/></svg>')
SCREENS_EXTRA = ('</header><div class="app">'
                 '<section id="s1"><h2>First screen</h2><p>Welcome text long enough to count as content.</p>'
                 '<button type="button">Next</button></section>'
                 '<section id="s2" hidden><h2>Second screen</h2><p>Too wide for a phone on purpose here.</p>'
                 '<div style="width:1200px;height:10px"></div><button type="button">Go</button></section>'
                 '<section id="s3" hidden><h2>Home</h2><p>Home screen content long enough to count here.</p>'
                 '<button type="button">Act</button></section>'
                 '<section id="sheet" role="dialog" hidden><p>A dialog overlay, long enough to have text.</p>'
                 '<button type="button">Close</button></section></div>')
SEEDED_WANT = ("RENDER-BROKEN-IMAGE", "RENDER-ASSET-FAILED", "RENDER-CONSOLE-ERROR", "RENDER-DEAD-LINK",
               "RENDER-HORIZONTAL-OVERFLOW", "RENDER-DUPLICATE-IMAGE")


def test_render() -> None:
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        print("  SKIP V-DSR-RENDER-REAL: playwright not installed (reported, not counted)")
        return
    d, page = project(CLEAN)
    r = subprocess.run([sys.executable, str(REC), "render", page], capture_output=True, text=True, env=env(),
                       timeout=180, encoding="utf-8")
    rows = [x for x in dr.read_rows("renders.jsonl") if x.get("file") == dr.canon(page)]
    pngs = rows[-1]["pngs"] if rows else []
    real = bool(pngs) and all(os.path.isfile(p) and open(p, "rb").read(8) == b"\x89PNG\r\n\x1a\n" for p in pngs)
    if r.returncode != 0 and "no Chromium-family browser could start" in (r.stderr or ""):
        print("  SKIP V-DSR-RENDER-REAL: no Chromium, Chrome or Edge on this host (reported, not counted)")
        return
    ok("V-DSR-RENDER-REAL", r.returncode == 0 and real and len(pngs) == 2, (r.stdout + r.stderr)[-400:])
    # the same real render carries facts, and they are empty for the clean page (negative control) ...
    sys.path.insert(0, str(ROOT / "tools"))
    import design_review_record as rec
    facts = rows[-1].get("facts") if rows else None
    clean_fail = [v.criterion for v in rec.facts_verdicts(facts or {}) if v.status == "fail"]
    ok("V-DSR-RENDER-FACTS-CLEAN", bool(facts and facts.get("collected")) and not clean_fail, (facts, clean_fail))
    # ... and they catch every seeded defect on a page built to fail, each one a real browser observation
    d2, bad = project(CLEAN.replace("</head>", '<link rel="stylesheet" href="missing.css"></head>')
                      .replace("</header>", SEEDED_EXTRA))
    Path(d2, "plato.svg").write_text(PLATO_SVG, encoding="utf-8")
    r = subprocess.run([sys.executable, str(REC), "render", bad], capture_output=True, text=True, env=env(),
                       timeout=180, encoding="utf-8")
    rows = [x for x in dr.read_rows("renders.jsonl") if x.get("file") == dr.canon(bad)]
    got = {v.criterion: v for v in rec.facts_verdicts((rows[-1].get("facts") if rows else None) or {})
           if v.status == "fail"}
    over = got.get("RENDER-HORIZONTAL-OVERFLOW")
    ok("V-DSR-RENDER-FACTS-SEEDED", all(w in got for w in SEEDED_WANT) and over is not None
       and "phone" in over.observed and "desktop" not in over.observed,
       ([w for w in SEEDED_WANT if w not in got], {k: v.observed for k, v in got.items()}, (r.stdout + r.stderr)[-300:]))
    # benchmark 2026-11-22, B-1: a link to a local file that does not exist is dead on a file:// render; one that exists
    # (with a #fragment) is not
    dead = got.get("RENDER-DEAD-LINK")
    ok("V-DSR-RENDER-DEAD-LOCAL-LINK", dead is not None and "servicios.html" in dead.observed
       and "Ver plato" not in dead.observed, dead.observed if dead else None)
    # benchmark 2026-11-22, B-8: a one-file app swaps sibling <section hidden> screens by JS state; the render captured
    # the first screen only, so the APPROVE bound bytes whose other screens no render showed. Every hidden screen is now
    # revealed alone, captured and observed. Negative control: a hidden role=dialog section is an overlay, not a screen.
    d3, app = project(CLEAN.replace("</header>", SCREENS_EXTRA))
    r = subprocess.run([sys.executable, str(REC), "render", app], capture_output=True, text=True, env=env(),
                       timeout=240, encoding="utf-8")
    rows = [x for x in dr.read_rows("renders.jsonl") if x.get("file") == dr.canon(app)]
    vps = ((rows[-1].get("facts") or {}).get("viewports") or {}) if rows else {}
    labels = sorted(s.get("label") for s in (vps.get("phone") or {}).get("screens") or [])
    spngs = [s.get("png") for x in vps.values() for s in x.get("screens") or []]
    ok("V-DSR-RENDER-SCREENS", labels == ["s2", "s3"] and len(spngs) == 4
       and all(p and os.path.isfile(p) for p in spngs) and len(rows[-1]["pngs"]) == 6,
       (labels, spngs, (r.stdout + r.stderr)[-300:]))
    got = {v.criterion: v for v in rec.facts_verdicts(rows[-1].get("facts") if rows else {}) if v.status == "fail"}
    over = got.get("RENDER-HORIZONTAL-OVERFLOW")
    ok("V-DSR-RENDER-SCREEN-FACTS", over is not None and "phone#s2" in over.observed and "#s3" not in over.observed
       and "RENDER-UNRENDERED-SCREEN" not in got, {k: v.observed for k, v in got.items()})


def test_wired() -> None:
    disp = (ROOT / "hooks" / "hook-dispatcher.js").read_text(encoding="utf-8")

    def chain(name: str) -> str:
        i = disp.find("'%s': [" % name)
        return disp[i:disp.find("\n  ],", i)] if i >= 0 else ""
    ok("V-DSR-WIRED-PROMPT", "tools/design_route_prompt.py" in chain("UserPromptSubmit-chain"))
    ok("V-DSR-WIRED-STOP", "tools/design_donegate_stop.py" in chain("Stop-chain"))


def shell_transcript(tool: str, command: str, cwd: str, when: float) -> str:
    """A session whose only visual write is a shell command (no Write/Edit row at all)."""
    from datetime import datetime, timezone
    p = os.path.join(tempfile.mkdtemp(dir=_TMP), "t.jsonl")
    rows = [{"type": "user", "message": {"role": "user", "content": "haz la landing"}},
            {"type": "assistant", "cwd": cwd, "timestamp": datetime.fromtimestamp(when, timezone.utc).isoformat(),
             "message": {"content": [{"type": "tool_use", "name": tool, "input": {"command": command}}]}},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "Listo."}]}}]
    Path(p).write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return p


def test_shell() -> None:
    """A page written through Bash or PowerShell reaches the Stop gate (it used to bypass Taste and the review)."""
    now = time.time()
    d, page = project(CLEAN)                                   # written AFTER the command's timestamp
    t = shell_transcript("Bash", "cat > index.html <<'EOF'\n<!doctype html>...\nEOF", d, now - 5)
    out = stop("shell-bash", d, t)
    ok("V-DSR-SHELL-HEREDOC-JUDGED", bool(out) and out.get("decision") == "block" and "index.html" in out["reason"]
       and "design-review" in out["reason"], out)
    d2, _ = project(CLEAN)
    page2 = os.path.join(d2, "carta.html")
    Path(page2).write_text(CLEAN, encoding="utf-8")
    t2 = shell_transcript("PowerShell", 'Set-Content -Path "%s" -Value $html -Encoding utf8' % page2, d2, now - 5)
    out = stop("shell-ps", d2, t2)
    ok("V-DSR-SHELL-POWERSHELL-JUDGED", bool(out) and "carta.html" in out.get("reason", ""), out)
    # negative control: a command that only READ a page written an hour earlier does not make it this session's work
    d3, page3 = project(CLEAN)
    old = now - 3600
    os.utime(page3, (old, old))
    t3 = shell_transcript("Bash", "cat index.html | head -20", d3, now - 5)
    ok("V-DSR-SHELL-READ-NOT-JUDGED", stop("shell-read", d3, t3) is None)
    # review M3: the same read-only session must stay unjudged when someone else saves the page AFTER the scan
    os.utime(page3, (now + 30, now + 30))
    ok("V-DSR-SHELL-FOREIGN-EDIT-NOT-JUDGED", stop("shell-read", d3, t3) is None)
    # review M1: a heredoc carrying a 200 KB inline image must not backtrack the Stop hook past its 8 s kill
    blob = "cat > index.html <<'EOF'\n<img src=\"data:image/png;base64," + "A" * 200_000 + "\">\nEOF"
    t0 = time.time()
    found = dr.shell_paths(blob)
    took = time.time() - t0
    ok("V-DSR-SHELL-NO-QUADRATIC", found == ["index.html"] and took < 1.0, "%.2f s %s" % (took, found))
    # B-4 (benchmark 2026-11-22): unexpanded variables, globs and placeholders are not paths; a Next.js [slug] route is
    nonpaths = dr.shell_paths(r'Copy-Item $out\p1.png x; ls assets\*.svg; cp %TEMP%\a.html b; "$env:temp\c.css"; '
                              r'f"{out}/p{i}.png"; echo shot?.png; cat app/[slug]/page.tsx docs/real.html')
    ok("V-DSR-SHELL-NON-PATHS-DROPPED", nonpaths == ["app/[slug]/page.tsx", "docs/real.html"], nonpaths)
    # pre-push review of d850e5f0: a Remix/TanStack route parameter is a literal `$` in a real file name
    routes = dr.shell_paths(r"cp a.tsx 'app/routes/posts.$slug.tsx'; cp b.tsx app/routes/$.tsx; "
                            r"cp c.tsx app\routes\$id.tsx; cp d.tsx app/routes/posts.$slug/route.tsx; "
                            r"Copy-Item $out\p1.png x; cp $name/x.html y")
    want = ["app/routes/posts.$slug.tsx", "app/routes/$.tsx", r"app\routes\$id.tsx", "app/routes/posts.$slug/route.tsx"]
    ok("V-DSR-SHELL-ROUTE-PARAM-KEPT", all(w in routes for w in want)
       and not any(r.startswith("$") for r in routes), routes)
    # review M2: Git Bash names the page /c/Users/... ; that must reach the gate like C:\Users\...
    if os.name == "nt":
        d5, page5 = project(CLEAN)
        msys = "/" + page5[0].lower() + page5[2:].replace("\\", "/")
        t5 = shell_transcript("Bash", "cat > %s <<'EOF'\nx\nEOF" % msys, os.path.dirname(_TMP), now - 5)
        out = stop("shell-msys", d5, t5)
        ok("V-DSR-SHELL-MSYS-PATH-JUDGED", bool(out) and "index.html" in out.get("reason", ""), (msys, out))
    # and a non-visual file written through the shell stays out of the design gate
    d4, _ = project(CLEAN)
    os.utime(os.path.join(d4, "index.html"), (old, old))
    Path(d4, "notes.md").write_text("x", encoding="utf-8")
    t4 = shell_transcript("Bash", "echo x > notes.md", d4, now - 5)
    ok("V-DSR-SHELL-NONVISUAL-IGNORED", stop("shell-md", d4, t4) is None)


LOGO_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120">'
            '<circle cx="60" cy="60" r="50" fill="#9c3d24"/></svg>')


def test_brand() -> None:
    """Brand kits: CCF produces, CDIO judges (Owner 'rec', 2026-11-22). Assets are judged only in a brand session."""
    sys.path.insert(0, str(ROOT / "tools"))
    import design_review_record as rec
    d = tempfile.mkdtemp(dir=_TMP)
    logo = os.path.join(d, "logo.svg")
    Path(logo).write_text(LOGO_SVG, encoding="utf-8")
    run_hook(PROMPT, {"session_id": "b1", "prompt": "diseña el logo y la paleta de colores de la marca"})
    out = stop("b1", d, transcript(writes=[logo]))
    ok("V-DSR-BRAND-SVG-JUDGED", bool(out) and out.get("decision") == "block" and "logo.svg" in out["reason"]
       and "design-review" in out["reason"], out)
    d2 = tempfile.mkdtemp(dir=_TMP)
    icon = os.path.join(d2, "icon.svg")
    Path(icon).write_text(LOGO_SVG, encoding="utf-8")
    run_hook(PROMPT, {"session_id": "b2", "prompt": "hazme una landing page para un estudio de yoga"})
    ok("V-DSR-WEB-SVG-NOT-JUDGED", stop("b2", d2, transcript(writes=[icon])) is None)
    # review of bb95f710, M2: `ccf.cli generate` writes .ccf/images/<id>.png from inside its process; the command names
    # no .png, so CCF's own outputs never reached the gate. Negative control: an image from before the command stays out.
    now = time.time()
    d3 = tempfile.mkdtemp(dir=_TMP)
    imgs = os.path.join(d3, "kit", ".ccf", "images")
    os.makedirs(imgs)
    Path(imgs, "c1.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\0" * 32)
    Path(imgs, "old.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\0" * 32)
    os.utime(os.path.join(imgs, "old.png"), (now - 3600, now - 3600))
    run_hook(PROMPT, {"session_id": "b3", "prompt": "diseña el logo de la marca"})
    t3 = shell_transcript("PowerShell", "python -m modules.ccf.cli generate kit", d3, now - 5)
    out = stop("b3", d3, t3)
    # review of bb95f710, L1: an asset is judged by the kinds it was WRITTEN under, not by the latest prompt's.
    routes = dr.load_routes()
    d4 = tempfile.mkdtemp(dir=_TMP)
    mark = os.path.join(d4, "mark.svg")
    Path(mark).write_text(LOGO_SVG, encoding="utf-8")
    run_hook(PROMPT, {"session_id": "b4", "prompt": "diseña el logo de la marca"})
    stop("b4", d4, transcript(writes=[mark]))
    run_hook(PROMPT, {"session_id": "b4", "prompt": "ahora la landing page"})
    kept = dr.judge(dr.load_session("b4"), d4, routes)["files"]
    d5 = tempfile.mkdtemp(dir=_TMP)
    shot = os.path.join(d5, "shot.png")
    Path(shot).write_bytes(b"\x89PNG\r\n\x1a\n" + b"\0" * 32)
    run_hook(PROMPT, {"session_id": "b5", "prompt": "hazme una landing page para un estudio de yoga"})
    stop("b5", d5, transcript(writes=[shot]))
    run_hook(PROMPT, {"session_id": "b5", "prompt": "ajusta el color del logo de la marca"})
    late = dr.judge(dr.load_session("b5"), d5, routes)["files"]
    ok("V-DSR-ASSET-KINDS-AT-WRITE", dr.canon(mark) in kept and dr.canon(shot) not in late, (kept, late))
    ok("V-DSR-CCF-GENERATE-JUDGED", bool(out) and "c1.png" in out.get("reason", "")
       and "old.png" not in out.get("reason", ""), out)
    # benchmark 2026-11-22, B-3: `python build.py` wrote the kit's logo SVGs from inside its process; the command named
    # none, so only the favicon (named elsewhere) got its framed review. Negative controls: an SVG from before the
    # command, an SVG under node_modules, and the same script run in a web session.
    d6 = tempfile.mkdtemp(dir=_TMP)
    os.makedirs(os.path.join(d6, "assets"))
    os.makedirs(os.path.join(d6, "node_modules", "pkg"))
    for rel in ("assets/mark.svg", "assets/wordmark.svg", "assets/old.svg", "node_modules/pkg/icon.svg"):
        Path(d6, rel).write_text(LOGO_SVG, encoding="utf-8")
    os.utime(os.path.join(d6, "assets", "old.svg"), (now - 3600, now - 3600))
    run_hook(PROMPT, {"session_id": "b6", "prompt": "diseña el logo de la marca"})
    out6 = stop("b6", d6, shell_transcript("PowerShell", "python build.py", d6, now - 5))
    r6 = (out6 or {}).get("reason", "")
    ok("V-DSR-SCRIPT-OUTPUT-JUDGED", "mark.svg" in r6 and "wordmark.svg" in r6 and "old.svg" not in r6
       and "icon.svg" not in r6, out6)
    run_hook(PROMPT, {"session_id": "b7", "prompt": "hazme una landing page para un estudio de yoga"})
    d7 = tempfile.mkdtemp(dir=_TMP)
    Path(d7, "logo.svg").write_text(LOGO_SVG, encoding="utf-8")
    ok("V-DSR-SCRIPT-OUTPUT-WEB-SESSION-NOT-JUDGED",
       stop("b7", d7, shell_transcript("PowerShell", "python build.py", d7, now - 5)) is None)
    ok("V-DSR-SCRIPT-RUN-SHAPES", all(dr._SCRIPT_RUN_RX.search(c) for c in (
        "python build.py", "py -3 tools\\gen.py --out assets", "node scripts/icons.mjs", "python -m kit.build",
        "cd kit; python3 build.py")) and not any(dr._SCRIPT_RUN_RX.search(c) for c in (
        "cat build.py", "Get-Content build.py", "git add build.py", "python --version")))
    full = os.path.join(_TMP, "brand_full.json")
    Path(full).write_text(json.dumps(GOOD_VERDICTS), encoding="utf-8")
    unrendered = rec.record(full, [logo])
    fake_render(logo)                                     # a page-style render: no frame, so not a brand render
    unframed = rec.record(full, [logo])
    fake_render(logo, facts=dict(CLEAN_FACTS, frame=True))
    framed = rec.record(full, [logo])
    ok("V-DSR-RECORD-ASSET-NEEDS-FRAME", not unrendered["is_done"] and not unframed["is_done"]
       and any("brand asset never rendered" in r for r in unframed["refused"]) and framed["is_done"],
       (unrendered["refused"], unframed["refused"], framed["verdict"], framed["refused"]))
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        print("  SKIP V-DSR-RENDER-ASSET-*: playwright not installed (reported, not counted)")
        return
    bad = os.path.join(d, "broken.svg")
    Path(bad).write_text("this is not an svg", encoding="utf-8")
    r = subprocess.run([sys.executable, str(REC), "render", logo, bad], capture_output=True, text=True, env=env(),
                       timeout=240, encoding="utf-8")
    last = {}
    for x in dr.read_rows("renders.jsonl"):
        last[x.get("file")] = x
    good_row, bad_row = last.get(dr.canon(logo), {}), last.get(dr.canon(bad), {})
    good_fail = [v.criterion for v in rec.facts_verdicts(good_row.get("facts") or {}) if v.status == "fail"]
    bad_fail = [v.criterion for v in rec.facts_verdicts(bad_row.get("facts") or {}) if v.status == "fail"]
    ok("V-DSR-RENDER-ASSET-FRAMED", (good_row.get("facts") or {}).get("frame") is True
       and len(good_row.get("pngs") or []) == 2 and not good_fail, (good_fail, (r.stdout + r.stderr)[-300:]))
    ok("V-DSR-RENDER-ASSET-BROKEN-CAUGHT", "RENDER-BROKEN-IMAGE" in bad_fail, (bad_fail, (r.stdout + r.stderr)[-300:]))


def main() -> int:
    t0 = time.time()
    try:
        for t in (test_routes, test_prompt, test_stop, test_record, test_render, test_shell, test_brand, test_wired):
            try:
                t()
            except Exception as exc:  # noqa: BLE001 -- a crashed section is a FAIL, never a skip
                ok("V-DSR-CRASH-%s" % t.__name__, False, "%s: %s" % (type(exc).__name__, exc))
    finally:
        shutil.rmtree(_TMP, ignore_errors=True)
    passed = sum(1 for _, c in RESULTS if c)
    print("V-DSR: %d passed, %d failed (%.1f s)" % (passed, len(RESULTS) - passed, time.time() - t0))
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
