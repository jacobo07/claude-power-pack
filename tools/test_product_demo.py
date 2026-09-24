#!/usr/bin/env python3
"""V-DEMO-* gates for modules/product_demo.

    python tools/test_product_demo.py            # all gates (real browser, ~5-8 min on this host)
    python tools/test_product_demo.py --fast     # pure gates only (no browser)

Every refusal gate is paired with a control in which the same machinery admits
a clean input, so a gate that refuses everything cannot pass. The fixture app is
owned by this test (tests/fixtures/product_demo/app); no real data is touched.
"""
from __future__ import annotations

import copy
import functools
import http.server
import json
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PP))

from modules.product_demo import manifest as mf  # noqa: E402
from modules.product_demo import stage, timeline, validate  # noqa: E402
from modules.product_demo.capture import pii_findings  # noqa: E402
from modules.product_demo.cli import native_crash, revise  # noqa: E402
from modules.product_demo.runner import pid_alive, run_bounded  # noqa: E402
from modules.product_demo.spec import SpecError, parse  # noqa: E402

FIX = PP / "tests" / "fixtures" / "product_demo"
FAST = "--fast" in sys.argv
_pass = _fail = 0


def gate(name: str, ok: bool, evidence: str = "") -> None:
    global _pass, _fail
    if ok:
        _pass += 1
    else:
        _fail += 1
    print(f"  {'PASS' if ok else 'FAIL'}  {name}  {evidence}", flush=True)


def base_spec() -> dict:
    return json.loads((FIX / "fixture_spec.json").read_text(encoding="utf-8")
                      .replace("{PORT}", "8").replace("{QUERY}", ""))


# ---------------------------------------------------------------- pure gates
print("=" * 64)
print("PRODUCT DEMO -- V-DEMO gates" + (" (fast)" if FAST else ""))
print("=" * 64)

try:
    s = parse(base_spec())
    gate("V-DEMO-SPEC-VALID", len(s.steps) == 7 and s.steps[-1].do == "hover" and len(s.viewports) == 2
         and len(s.sha256) == 64,
         f"({len(s.steps)} steps, sha {s.sha256[:10]})")
except Exception as exc:
    gate("V-DEMO-SPEC-VALID", False, f"({exc})")

refusals = {
    "css without allow_css": lambda d: d["steps"][1].update(target={"css": "#tenant"}),
    "role without name": lambda d: d["steps"][4].update(target={"role": "button"}),
    "callout without target": lambda d: d["steps"][0].update(callout="hi"),
    "duplicate step id": lambda d: d["steps"][2].update(id="tenant"),
    "fill without value": lambda d: d["steps"][1].pop("value"),
    "unknown stage": lambda d: d["viewports"][0].update(stage="tv"),
}
wrong = []
for label, mutate in refusals.items():
    d = base_spec()
    mutate(d)
    try:
        parse(d)
        wrong.append(label)
    except SpecError:
        pass
gate("V-DEMO-SPEC-REFUSALS", not wrong, f"({len(refusals) - len(wrong)}/{len(refusals)} refused)"
     + (f" admitted: {wrong}" if wrong else ""))

pii_red = pii_findings("contact maria.lopez@example.org, NIF 12345678Z, IBAN ES91 2100 0418 4502 0005 1332", [])
pii_ok = pii_findings("Tenant: Ana Ruiz, 950 EUR/month, NIF 12345678Z", ["12345678Z"])
gate("V-DEMO-PII", {k for k, _ in pii_red} >= {"email", "es_nif_nie", "iban"} and not pii_ok,
     f"(red kinds {sorted({k for k, _ in pii_red})}; declared fixture admitted: {not pii_ok})")


import os  # noqa: E402

from modules.product_demo.capture import Capture, Refusal  # noqa: E402


class _TextPage:
    """Stands in for a page whose visible text is known; scan() only calls evaluate()."""

    def __init__(self, text):
        self.text = text

    def evaluate(self, _js):
        return self.text


d_env = base_spec()
d_env["fixture_env"] = ["PDEMO_TEST_EMAIL"]
spec_env = parse(d_env)
cap_env = Capture(spec_env, "desktop", Path(tempfile.mkdtemp()), probe=True)
page_env = _TextPage("Signed in as run-123@example.com")
os.environ["PDEMO_TEST_EMAIL"] = "run-123@example.com"
try:
    cap_env.scan(page_env, "s")
    admitted = True
except Refusal:
    admitted = False
del os.environ["PDEMO_TEST_EMAIL"]
try:
    cap_env.scan(page_env, "s")
    refused_without = False
except Refusal as r:
    refused_without = r.code == "PRIVACY_REFUSED"
gate("V-DEMO-FIXTURE-ENV", admitted and refused_without,
     f"(env-declared email admitted: {admitted}; same email refused once the env is unset: {refused_without})")


def tele(work_real_ms: int = 6000, callout: str = "Only the facts it needs") -> dict:
    return {"outcome": "ok", "viewport": {"name": "t", "width": 1000, "height": 800, "dsf": 1},
            "steps": [
                {"id": "open", "do": "goto", "film": True, "t_end_ms": 500,
                 "frames": [{"file": "a.png", "t_ms": 0, "kind": "arrive"}]},
                {"id": "go", "do": "click", "film": True, "callout": callout, "t_end_ms": 1300,
                 "target": {"box": {"x": 100, "y": 200, "width": 200, "height": 40}, "describe": "x",
                            "text_sha256": "h"},
                 "click_point": {"x": 200.0, "y": 220.0},
                 "frames": [{"file": "b.png", "t_ms": 600, "kind": "before"},
                            {"file": "c.png", "t_ms": 1200, "kind": "after"}]},
                {"id": "wait", "do": "wait_text", "film": True, "t_end_ms": 1300 + work_real_ms + 400,
                 "frames": [{"file": "d.png", "t_ms": 1300, "kind": "working"},
                            {"file": "e.png", "t_ms": 1300 + work_real_ms, "kind": "result"}]}]}


out_cfg = {"default_hold_ms": 1400, "typing_ms_per_char": 45, "max_seconds": 40}
tl = timeline.build(tele(6000), out_cfg)
work = [x for x in tl.segments if x.kind == "working"][0]
gate("V-DEMO-TIME-HONEST", work.dur_ms * timeline.MAX_WORK_COMPRESSION >= 6000
     and any(c["kind"] == "working" for c in tl.compressions),
     f"(6000 ms of real work presented as {work.dur_ms} ms; compression recorded)")

clicks = [k for k in tl.cursor if k["click"]]
arrive = [k for k in tl.cursor if not k["click"] and k["t_ms"] > 0]
gate("V-DEMO-CURSOR-TRUTH", len(clicks) == 1 and (clicks[0]["x"], clicks[0]["y"]) == (200.0, 220.0)
     and (arrive[-1]["x"], arrive[-1]["y"]) == (200.0, 220.0),
     f"(click at {clicks[0]['x'] if clicks else None},{clicks[0]['y'] if clicks else None}; recorded 200,220)")

co = tl.callouts[0]
before_seg = next(s for s in tl.segments if s.step == "go" and s.kind == "before")
after_seg = next(s for s in tl.segments if s.step == "go" and s.kind == "after")
gate("V-DEMO-CALLOUT-ENDS-AT-CLICK",
     co["end_ms"] == before_seg.start_ms + before_seg.dur_ms and co["end_ms"] <= after_seg.start_ms,
     f"(callout ends {co['end_ms']} ms; pre-click frame ends {before_seg.start_ms + before_seg.dur_ms}; "
     f"next page starts {after_seg.start_ms})")

long_text = "A deliberately long callout that nobody could read in time"
tl_short = timeline.build(tele(6000, long_text), out_cfg)
has_timing = any(d["class"] == "TIMING" for d in tl_short.defects)
fixed, hist = revise(tele(6000, long_text), out_cfg)
gate("V-DEMO-REVISION-LOOP", has_timing and not any(d["class"] == "TIMING" for d in fixed.defects)
     and 1 <= len(hist) <= 3,
     f"(TIMING before: {has_timing}; after {len(hist)} revision(s): "
     f"{[d['class'] for d in fixed.defects] or 'clean'})")

scr = stage.screen_rect("laptop", 1000, 800)
box = {"x": 100, "y": 200, "width": 200, "height": 40}
label_above = {"x": 100, "y": 176, "width": 120, "height": 18}
c = stage.callout_rect(box, "Only the facts it needs", 1, scr, [label_above])
layout_ok = {"screen": scr, "callouts": [{**c, "text": "t"}]}
bad = copy.deepcopy(layout_ok)
bad["callouts"][0]["anchor"] = {"x": bad["callouts"][0]["target"]["x"] - 300, "y": 5}
gate("V-DEMO-CALLOUT-PLACEMENT", c["hidden_text_px"] == 0 and not validate.check_layout(layout_ok)
     and any(d["class"] == "MISPOINTED_CALLOUT" for d in validate.check_layout(bad)),
     f"(side {c['side']}, hidden {c['hidden_text_px']} px^2; mispointed control flagged)")

with tempfile.TemporaryDirectory() as td:
    empty = Path(td) / "empty.mp4"
    empty.write_bytes(b"")
    v_missing = validate.validate(Path(td) / "nope.mp4", layout=layout_ok, timeline=tl.to_dict(),
                                  telemetry=tele(), output=out_cfg, canvas=(1920, 1080))
    v_empty = validate.validate(empty, layout=layout_ok, timeline=tl.to_dict(), telemetry=tele(),
                                output=out_cfg, canvas=(1920, 1080))
    junk = Path(td) / "junk.mp4"
    junk.write_bytes(b"not a video" * 100)
    v_junk = validate.validate(junk, layout=layout_ok, timeline=tl.to_dict(), telemetry=tele(),
                               output=out_cfg, canvas=(1920, 1080))
gate("V-DEMO-VALIDATOR-UNREADABLE", v_missing.outcome == v_empty.outcome == v_junk.outcome == validate.UNREADABLE,
     f"(missing={v_missing.outcome}, empty={v_empty.outcome}, junk={v_junk.outcome})")

man = {"spec": {"sha256": "S"}, "capture": {"targets": [
    {"step": "go", "describe": "x", "text_sha256": "h", "box": {"x": 100, "y": 200, "width": 200, "height": 40}}]}}
probe_same = {"outcome": "ok", "spec_sha256": "S", "viewport": {"width": 1000, "height": 800},
              "steps": [{"id": "go", "target": {"text_sha256": "h", "box": {"x": 101, "y": 201, "width": 200, "height": 40}}}]}
probe_text = copy.deepcopy(probe_same)
probe_text["steps"][0]["target"]["text_sha256"] = "changed"
probe_moved = copy.deepcopy(probe_same)
probe_moved["steps"][0]["target"]["box"]["y"] = 600
states = (mf.staleness(man, probe_same)["state"], mf.staleness(man, probe_text)["state"],
          mf.staleness(man, probe_moved)["state"],
          mf.staleness(man, {"outcome": "refused", "refusal": {"code": "BLOCKED_ENV"}})["state"],
          mf.staleness(man, {"outcome": "refused", "refusal": {"code": "TARGET_DRIFT", "detail": "x"}})["state"])
gate("V-DEMO-STALENESS", states == ("CURRENT", "STALE", "STALE", "UNKNOWN", "STALE"),
     f"(same/text/moved/blocked/drift -> {states})")

gate("V-DEMO-NATIVE-CRASH", native_crash(-1073740022) and not native_crash(2) and not native_crash(None)
     and not native_crash(1), "(0xC000070A retried; rc 2 / 1 / None are not)")

# ---------------------------------------------------------------- browser gates
if FAST:
    print(f"\nRESULT: {_pass} PASS / {_fail} FAIL (fast)")
    sys.exit(0 if _fail == 0 else 1)

state = {"moved": False}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(FIX / "app"), **k)

    def log_message(self, *a):
        return

    def do_GET(self):
        if state["moved"] and self.path.startswith("/index.html"):
            body = (FIX / "app" / "index.html").read_text(encoding="utf-8").replace(
                ">Generate contract</button>", ">Create</button>").encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()


srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler)
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
work_dir = Path(tempfile.mkdtemp(prefix="pdemo_"))


def spec_file(query: str = "", name: str = "spec.json", path: str | None = None) -> Path:
    raw = (FIX / "fixture_spec.json").read_text(encoding="utf-8").replace("{PORT}", str(port)).replace("{QUERY}", query)
    d = json.loads(raw)
    if path:
        d["steps"][0]["path"] = path
    p = work_dir / name
    p.write_text(json.dumps(d), encoding="utf-8")
    return p


def capture(spec: Path, out: str, probe: bool, viewport: str = "phone") -> dict:
    argv = [sys.executable, "-m", "modules.product_demo.capture", "--spec", str(spec), "--viewport", viewport,
            "--out", str(work_dir / out)] + (["--probe"] if probe else [])
    r = run_bounded(argv, timeout_s=240, cwd=str(PP))
    t = work_dir / out / "telemetry.json"
    return json.loads(t.read_text(encoding="utf-8")) if t.is_file() else {"outcome": None, "run": r.outcome,
                                                                          "stderr": r.stderr[-300:]}


def refusal_of(t: dict):
    return (t.get("refusal") or {}).get("code")


cases = [("V-DEMO-REFUSE-DRIFT", "?mode=moved", True, "TARGET_DRIFT"),
         ("V-DEMO-REFUSE-AMBIGUOUS", "?mode=dupe", True, "TARGET_AMBIGUOUS"),
         ("V-DEMO-REFUSE-PII", "?mode=pii", False, "PRIVACY_REFUSED"),
         ("V-DEMO-REFUSE-HTTP-ERROR", "?mode=500", True, "PRODUCT_ERROR"),
         ("V-DEMO-REFUSE-INPUT-RESET", "?mode=reset", True, "INPUT_NOT_ACCEPTED")]
for name, q, probe, want in cases:
    t = capture(spec_file(q, f"{name}.json"), name, probe)
    gate(name, refusal_of(t) == want, f"(got {refusal_of(t) or t.get('outcome')}: {(t.get('refusal') or {}).get('detail', t.get('stderr', ''))})")

t404 = capture(spec_file("", "404.json", path="/missing.html"), "r404", True)
gate("V-DEMO-REFUSE-404", refusal_of(t404) == "PRODUCT_ERROR" and "404" in (t404.get("refusal") or {}).get("detail", ""),
     f"(got {refusal_of(t404)}: {(t404.get('refusal') or {}).get('detail')})")

t_ctrl = capture(spec_file("", "control.json"), "control", True)
gate("V-DEMO-REFUSE-CONTROL", t_ctrl.get("outcome") == "ok", f"(clean fixture probe -> {t_ctrl.get('outcome')})")

# Kill drill: a child that launches Chromium and would sleep 120 s, bounded at 15 s.
sibling = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(90)"])   # outside the job
seen: list = []
# The grandchild python is not coupled to the Playwright pipe: killing only the
# direct child leaves it running (measured). Chromium alone would not tell a tree
# kill from a direct kill, because the driver takes Chromium down when its pipe closes.
child = ("from playwright.sync_api import sync_playwright\nimport subprocess, sys, time\n"
         "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'])\n"
         "with sync_playwright() as p:\n  b = p.chromium.launch()\n  b.new_page().goto('about:blank')\n"
         "  time.sleep(120)\n")
r = run_bounded([sys.executable, "-c", child], timeout_s=15, observe_pids=lambda p: seen.extend(p))
time.sleep(1.0)
survivors = [p for p in seen if pid_alive(p)]
sibling_alive = sibling.poll() is None
sibling.kill()
# The PIDs must be a plausible real tree (python + node driver + chrome processes).
# A reading of zeros, or a count equal to the query buffer, is an instrument
# failure: pid_alive(0) is False, so "no survivors" would pass while measuring nothing.
plausible = 3 <= len(seen) <= 200 and all(p > 0 for p in seen)
# The discriminating clause is the BOUND. Measured with a direct-child-only kill (the
# old behaviour): the grandchild kept the stdout pipe open, communicate() blocked on
# it, and a 15 s timeout returned after 127 s. The job object is what makes the
# ceiling true.
bounded = r.elapsed_s < 15 + 10
gate("V-DEMO-KILL-TREE", r.outcome == "timeout" and plausible and bounded and not survivors and sibling_alive,
     f"(outcome {r.outcome} after {r.elapsed_s:.1f}s of a 15 s bound, {len(seen)} tree pids, "
     f"survivors {survivors}, unrelated sibling alive: {sibling_alive})")

# End to end, then live staleness against the manifest it wrote.
e2e_spec = spec_file("", "e2e.json")
out = work_dir / "e2e"
r = subprocess.run([sys.executable, "-m", "modules.product_demo.cli", "run", "--spec", str(e2e_spec), "--out", str(out),
                    "--viewport", "phone", "--app-repo", str(PP)], cwd=str(PP), capture_output=True, text=True,
                   encoding="utf-8", errors="replace", timeout=1500)
res = json.loads(r.stdout[r.stdout.index("["):]) if "[" in r.stdout else [{}]
mpath = out / "phone" / "manifest.json"
m = json.loads(mpath.read_text(encoding="utf-8")) if mpath.is_file() else {}
probe_info = validate.probe(Path(res[0]["mp4"])) if res[0].get("mp4") else {}
tl_path = out / "phone" / "timeline.json"
clicks = sum(1 for k in json.loads(tl_path.read_text(encoding="utf-8"))["cursor"] if k["click"]) if tl_path.is_file() else -1
# 2 fills + 1 select + 1 click activate; the closing hover must NOT show a click.
gate("V-DEMO-HOVER-NO-CLICK", clicks == 4, f"({clicks} click emphases; expected 4 -- the hover adds none)")
gate("V-DEMO-E2E", r.returncode == 0 and res[0].get("outcome") == "VALID"
     and (probe_info.get("w"), probe_info.get("h")) == (1080, 1920)
     and len(m.get("capture", {}).get("frameset_sha256", "")) == 64 and "mp4" in m.get("outputs", {}),
     f"(exit {r.returncode}, {res[0].get('outcome')}, {probe_info.get('w')}x{probe_info.get('h')}, "
     f"{probe_info.get('duration_s')}s, defects {res[0].get('defects')}) {r.stderr[-300:]}")


def probe_state() -> str:
    pr = subprocess.run([sys.executable, "-m", "modules.product_demo.cli", "probe", "--spec", str(e2e_spec),
                         "--manifest", str(mpath), "--out", str(work_dir / f"probe{time.time_ns()}")],
                        cwd=str(PP), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    try:
        return json.loads(pr.stdout)["state"]
    except (ValueError, KeyError):
        return f"unparsed rc={pr.returncode} {pr.stderr[-200:]}"


if mpath.is_file():
    current = probe_state()
    state["moved"] = True
    stale = probe_state()
    state["moved"] = False
    gate("V-DEMO-STALENESS-LIVE", current == "CURRENT" and stale == "STALE",
         f"(unchanged app -> {current}; button renamed -> {stale})")
else:
    gate("V-DEMO-STALENESS-LIVE", False, "(no manifest from V-DEMO-E2E)")

srv.shutdown()
print()
print("=" * 64)
print(f"RESULT: {_pass} PASS / {_fail} FAIL ({_pass + _fail} total)   work dir: {work_dir}")
print("=" * 64)
sys.exit(0 if _fail == 0 else 1)
