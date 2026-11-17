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


def approve(page: str) -> dict:
    """What a real cdio-reviewer pass leaves behind: a render row, then a record row."""
    dr.append_row("renders.jsonl", {"file": dr.canon(page), "sha": dr.sha256(page), "pngs": ["fake.png"]})
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
    ok("V-DSR-CLASSIFY-MOTION", c("make a 30 s promo for the launch") == ["motion"], c("promo"))
    ok("V-DSR-CLASSIFY-NONE", c("fix the postgres migration and the retry loop") == [], c("postgres"))
    pol = dr.policy(dr.effective_kinds([], routes), routes)
    ok("V-DSR-DEFAULT-WEB", pol["kinds"] == ["web"] and pol["review"] and pol["taste"], pol)


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


def test_record() -> None:
    sys.path.insert(0, str(ROOT / "tools"))
    import design_review_record as rec
    d, page = project(CLEAN)
    thin = os.path.join(_TMP, "thin.json")
    Path(thin).write_text(json.dumps(GOOD_VERDICTS[:2]), encoding="utf-8")
    dr.append_row("renders.jsonl", {"file": dr.canon(page), "sha": dr.sha256(page), "pngs": ["fake.png"]})
    row = rec.record(thin, [page])
    ok("V-DSR-RECORD-REFUSES-THIN", not row["is_done"] and any("thin review" in r for r in row["refused"]), row)
    d2, page2 = project(CLEAN.replace("Tidewell", "Tidewell two"))
    full = os.path.join(_TMP, "full.json")
    Path(full).write_text(json.dumps(GOOD_VERDICTS), encoding="utf-8")
    row = rec.record(full, [page2])
    ok("V-DSR-RECORD-REFUSES-UNRENDERED", not row["is_done"] and any("never rendered" in r for r in row["refused"]), row)
    d3, page3 = project(SLOP)
    dr.append_row("renders.jsonl", {"file": dr.canon(page3), "sha": dr.sha256(page3), "pngs": ["fake.png"]})
    row = rec.record(full, [page3])
    ok("V-DSR-RECORD-FOLDS-TASTE", not row["is_done"] and row["verdict"] != "APPROVE" and row["critical"], row)
    css = os.path.join(d, "app.css")
    Path(css).write_text("body{margin:0}\n", encoding="utf-8")
    row = rec.record(full, [css])
    ok("V-DSR-RECORD-NONHTML-NEEDS-SHOT", not row["is_done"] and any("--screenshot" in r for r in row["refused"]), row)


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


def test_wired() -> None:
    disp = (ROOT / "hooks" / "hook-dispatcher.js").read_text(encoding="utf-8")

    def chain(name: str) -> str:
        i = disp.find("'%s': [" % name)
        return disp[i:disp.find("\n  ],", i)] if i >= 0 else ""
    ok("V-DSR-WIRED-PROMPT", "tools/design_route_prompt.py" in chain("UserPromptSubmit-chain"))
    ok("V-DSR-WIRED-STOP", "tools/design_donegate_stop.py" in chain("Stop-chain"))


def main() -> int:
    t0 = time.time()
    try:
        for t in (test_routes, test_prompt, test_stop, test_record, test_render, test_wired):
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
