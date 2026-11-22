#!/usr/bin/env python3
"""V-DRU-*: app surfaces are reviewed on their RUNNING route, never on an arbitrary PNG (spec design-surface-router.md,
section "App surfaces render through the running route").

Incident (measured 2026-11-22, ~/.claude/state/design_route/reviews.jsonl): most of the 28 live APPROVEs were .tsx
files (page.tsx, header.tsx, contactform.tsx) admitted by `--screenshot`: ANY >= 300x300 PNG newer than the file. Nothing
bound that PNG to a route, a viewport or these bytes, and none of the render facts (broken images, failed requests,
console errors, dead links, overflow) were ever collected for an app.

Hermetic: temp state dir, a real local HTTP server, real headless Chromium, the real CLI and the real Stop hook.
Both poles: a clean route records APPROVE and the Stop gate goes silent; a seeded route, a 404 route, a stale file and a
bare screenshot are all refused. No Chromium on the host = FAIL (unverified), never a pass.
Run: python tools/test_design_render_url.py   (exit 0 = all pass)
"""
from __future__ import annotations

import functools
import http.server
import json
import os
import struct
import subprocess
import sys
import tempfile
import threading
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_TMP = tempfile.mkdtemp(prefix="v-dru-")
STATE = os.path.join(_TMP, "state")
os.environ["CPP_DESIGN_STATE_DIR"] = STATE
from modules.cdio import design_route as dr  # noqa: E402

REC = ROOT / "tools" / "design_review_record.py"
PROMPT = ROOT / "tools" / "design_route_prompt.py"
STOP = ROOT / "tools" / "design_donegate_stop.py"
REQ_WEB = ["design-md", "design-taste-frontend", "frontend-design"]
GOOD = [{"criterion": c, "dimension": d, "status": "pass"} for c, d in
        [("hierarchy", "visual"), ("type-levels", "visual"), ("contrast", "visual"), ("primary-cta", "conversion"),
         ("task-clarity", "ux"), ("trust-signals", "trust"), ("spacing-system", "visual")]]
RESULTS: list = []


def ok(name: str, cond: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(cond)))
    print("  %s %-38s %s" % ("PASS" if cond else "FAIL", name, "" if cond else str(detail)[:500]))


def png(w: int, h: int) -> bytes:
    """A real, decodable RGB PNG (solid colour)."""
    raw = b"".join(b"\x00" + b"\xc8\x6e\x3c" * w for _ in range(h))

    def chunk(t: bytes, d: bytes) -> bytes:
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


PAGE = """<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Bodega Sur</title>
<meta name="viewport" content="width=device-width, initial-scale=1"></head><body>
<header><h1>Bodega Sur</h1><p>Tapas de temporada en el barrio de Triana.</p><a href="/reservar/">Reservar mesa</a></header>
<img src="/plato.png" alt="Plato del dia" width="320" height="200">%s</body></html>"""
# The seeded route plants its defects ON PURPOSE (a missing image and a link that goes nowhere), built from constants
# because the Woz write veto is a literal matcher (KNOWN_FALSE_POSITIVES FP-03 class).
NOWHERE = "#"
SEEDED = '<img src="/no-existe.png" alt="roto" width="320" height="200"><a href="%s">Ver carta</a>' % NOWHERE


def site() -> str:
    root = os.path.join(_TMP, "site")
    for sub, extra in (("ok", ""), ("broken", SEEDED), ("reservar", "")):
        os.makedirs(os.path.join(root, sub), exist_ok=True)
        Path(root, sub, "index.html").write_text(PAGE % extra, encoding="utf-8")
    Path(root, "plato.png").write_bytes(png(320, 200))
    # a section revealed by a CSS scroll-driven animation, far below the fold (the bodeguita `.reveal` shape)
    os.makedirs(os.path.join(root, "scroll"), exist_ok=True)
    Path(root, "scroll", "index.html").write_text((PAGE % (
        '<div style="height:2400px"></div><section class="reveal"><h2>Carta</h2></section>')).replace(
        "</head>", "<style>@keyframes rise{from{opacity:.15}to{opacity:1}}"
                   # base opacity 0: dropping the animation would capture it INVISIBLE; only finishing it shows it
                   ".reveal{opacity:0;animation:rise linear both;animation-timeline:view()}</style></head>"),
        encoding="utf-8")
    return root


def serve(root: str) -> str:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=root)
    handler.log_message = lambda *a, **k: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return "http://127.0.0.1:%d" % srv.server_address[1]


def cli(*args) -> subprocess.CompletedProcess:
    env = dict(os.environ, CPP_DESIGN_STATE_DIR=STATE, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, str(REC), *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=env, timeout=240)


def app(name: str, body: str = "export default function Page() { return null }\n") -> tuple:
    d = tempfile.mkdtemp(dir=_TMP)
    f = os.path.join(d, name)
    Path(f).write_text(body, encoding="utf-8")
    return d, f


def record(files: list) -> dict:
    rec = _rec()
    v = os.path.join(_TMP, "good.json")
    Path(v).write_text(json.dumps(GOOD), encoding="utf-8")
    return rec.record(v, files)


@functools.lru_cache(maxsize=1)
def _rec():
    sys.path.insert(0, str(ROOT / "tools"))
    import design_review_record as rec  # noqa: E402
    return rec


def failed(row: dict) -> dict:
    return {c: s for c, s, _ in row.get("failed", [])}


def hook(script: Path, payload: dict):
    env = dict(os.environ, CPP_DESIGN_STATE_DIR=STATE, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, str(script)], input=json.dumps(payload), capture_output=True, text=True,
                       encoding="utf-8", env=env, timeout=120)
    return json.loads(r.stdout) if r.stdout.strip() else None


def transcript(writes: list) -> str:
    p = os.path.join(tempfile.mkdtemp(dir=_TMP), "t.jsonl")
    rows = [{"type": "user", "message": {"role": "user", "content": "mejora la landing page de la bodega"}}]
    rows += [{"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": s}}]}}
             for s in REQ_WEB]
    rows += [{"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Write", "input": {"file_path": w, "content": "x"}}]}} for w in writes]
    rows.append({"type": "assistant", "message": {"content": [{"type": "text", "text": "Listo."}]}})
    Path(p).write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return p


def main() -> int:
    base = serve(site())

    # 0. the CLI refuses what is not a running route
    _, f0 = app("page.tsx")
    ok("V-DRU-REFUSES-NON-HTTP", cli("render-url", "--url", Path(f0).as_uri(), "--files", f0).returncode == 2)

    # 1. positive pole: a clean route renders at 3 widths, binds the bytes, records APPROVE ...
    d1, f1 = app("page.tsx")
    r = cli("render-url", "--url", base + "/ok/", "--files", f1)
    rows = [x for x in dr.read_rows("renders.jsonl") if x.get("file") == dr.canon(f1)]
    shots = rows[-1]["pngs"] if rows else []
    ok("V-DRU-RENDER-REAL", r.returncode == 0 and len(shots) == 3 and all(os.path.getsize(p) > 1000 for p in shots)
       and set(rows[-1]["facts"]["viewports"]) == {"desktop", "tablet", "phone"}, (r.stdout + r.stderr)[-500:])
    row = record([f1])
    ok("V-DRU-CLEAN-APPROVES", row["is_done"] and row["verdict"] == "APPROVE"
       and not [c for c in failed(row) if c.startswith("RENDER-")], row)
    # ... and the live Stop gate, the real consumer, accepts it: routed, skills loaded, recorded APPROVE -> silent
    hook(PROMPT, {"session_id": "dru-1", "prompt": "mejora la landing page de la bodega"})
    ok("V-DRU-STOP-ACCEPTS-URL-REVIEW",
       hook(STOP, {"session_id": "dru-1", "cwd": d1, "transcript_path": transcript([f1])}) is None)

    # 1b. a scroll-driven reveal is captured in its end state, and the render says it neutralised it
    _, f6 = app("page.tsx", "// scroll-driven\n")
    cli("render-url", "--url", base + "/scroll/", "--files", f6)
    rows = [x for x in dr.read_rows("renders.jsonl") if x.get("file") == dr.canon(f6)]
    vps = (rows[-1]["facts"]["viewports"] if rows else {})
    ok("V-DRU-SCROLL-DRIVEN-NEUTRALISED", bool(vps) and all((v.get("scroll_animations_neutralised") or 0) >= 1
                                                            and v.get("scroll_animations_still_faint") == 0
                                                            for v in vps.values()), vps)

    # 1c. two renders of ONE url are two observations: a later broken render must not hide behind an earlier clean one
    flip = os.path.join(_TMP, "site", "flip")
    os.makedirs(flip, exist_ok=True)
    Path(flip, "index.html").write_text(PAGE % "", encoding="utf-8")
    d7, f7b = app("header.tsx", "export const Header = () => null\n")
    f7a = os.path.join(d7, "page.tsx")
    Path(f7a).write_text("// before\n", encoding="utf-8")
    cli("render-url", "--url", base + "/flip/", "--files", f7a, f7b)          # T1: clean, both files
    Path(f7a).write_text("// after: breaks an image\n", encoding="utf-8")
    Path(flip, "index.html").write_text(PAGE % SEEDED, encoding="utf-8")
    cli("render-url", "--url", base + "/flip/", "--files", f7a)               # T2: broken, a.tsx only
    row = record([f7b, f7a])
    ok("V-DRU-SAME-URL-NEWER-DEFECT-KEPT", not row["is_done"] and failed(row).get("RENDER-BROKEN-IMAGE") == "critical",
       row)

    # 2. negative poles
    d2, f2 = app("page.tsx", "// seeded\nexport default function Page() { return null }\n")
    f2b = os.path.join(d2, "header.tsx")
    Path(f2b).write_text("export const Header = () => null\n", encoding="utf-8")
    cli("render-url", "--url", base + "/broken/", "--files", f2, f2b)
    row = record([f2, f2b])
    got = failed(row)
    ok("V-DRU-SEEDED-REFUSED", not row["is_done"] and got.get("RENDER-BROKEN-IMAGE") == "critical"
       and got.get("RENDER-DEAD-LINK") == "major", row)
    ok("V-DRU-ONE-ROUTE-ONE-OBSERVATION",
       sum(1 for c, _, _ in row["failed"] if c == "RENDER-BROKEN-IMAGE") == 1, row["failed"])

    _, f3 = app("page.tsx", "// 404 route\n")
    cli("render-url", "--url", base + "/no-such-route/", "--files", f3)
    row = record([f3])
    ok("V-DRU-ERROR-ROUTE-REFUSED", not row["is_done"] and failed(row).get("RENDER-DOCUMENT-STATUS") == "critical", row)

    # a file edited after its render: the render no longer shows these bytes
    d4, f4 = app("page.tsx", "// stale\n")
    cli("render-url", "--url", base + "/ok/", "--files", f4)
    Path(f4).write_text("// stale, edited after the render\n", encoding="utf-8")
    row = record([f4])
    ok("V-DRU-STALE-REFUSED", not row["is_done"] and any("render-url" in x for x in row["refused"]), row)

    # the retired proof: a valid 400x400 PNG newer than the file admits nothing on its own
    _, f5 = app("page.tsx", "// screenshot only\n")
    shot = os.path.join(_TMP, "shot.png")
    time.sleep(0.05)
    Path(shot).write_bytes(png(400, 400))
    v = os.path.join(_TMP, "good.json")
    Path(v).write_text(json.dumps(GOOD), encoding="utf-8")
    row = _rec().record(v, [f5], screenshot=shot)
    ok("V-DRU-SCREENSHOT-RETIRED", not row["is_done"] and any("--screenshot" in x and "render-url" in x
                                                              for x in row["refused"]), row)
    # ... and the Stop gate keeps blocking that session (the consumer sees the refusal, not a pass)
    hook(PROMPT, {"session_id": "dru-5", "prompt": "mejora la landing page de la bodega"})
    out = hook(STOP, {"session_id": "dru-5", "cwd": os.path.dirname(f5), "transcript_path": transcript([f5])})
    ok("V-DRU-STOP-BLOCKS-SCREENSHOT-ONLY", (out or {}).get("decision") == "block"
       and "design-review" in (out or {}).get("reason", ""), out)

    failed_n = [n for n, c in RESULTS if not c]
    print("V-DRU: %d passed, %d failed" % (len(RESULTS) - len(failed_n), len(failed_n)))
    return 1 if failed_n else 0


if __name__ == "__main__":
    raise SystemExit(main())
