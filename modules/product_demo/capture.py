"""Capture worker: drive the REAL product through a spec, record pixels + telemetry.

Runs as a child process under runner.run_bounded (never call it in-process for a
real capture: the runner is what guarantees the Chromium tree dies).

Capture model: a screenshot at every SETTLED semantic state (after an action,
per typing chunk, and periodically while the system is working), with CSS
animations disabled. That is what makes a real app -- network, server, React --
reproducible: pixels are taken only when the DOM has stopped moving, and
presentation time is decided later by the timeline, which records every
compression it applies. Nothing on screen is synthesised here.

Every abnormal condition is a named refusal, never a skipped animation:
TARGET_DRIFT, TARGET_AMBIGUOUS, AUTH_REDIRECT, FORBIDDEN_TEXT, PRIVACY_REFUSED,
INPUT_NOT_ACCEPTED, PRODUCT_ERROR, BLOCKED_ENV.

    python -m modules.product_demo.capture --spec S.json --viewport desktop --out DIR [--probe]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from modules.product_demo.spec import DemoSpec, SpecError, Step, load  # noqa: E402

EXIT_OK, EXIT_USAGE, EXIT_REFUSED = 0, 2, 3

# Personal-data shapes that must never reach a public video unless the spec
# declares them as fixture values. Credentials are the secret firewall's job;
# these are the PII shapes it does not cover.
PII_PATTERNS = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "es_nif_nie": re.compile(r"\b[XYZ]?\d{7,8}[A-HJ-NP-TV-Z]\b"),
    "iban": re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){3,7}(?:[ ]?[A-Z0-9]{1,4})?\b"),
    "phone": re.compile(r"(?<![\w-])\+?\d{2,3}[ .-]?\d{3}[ .-]?\d{2,3}[ .-]?\d{2,3}(?![\w-])"),
    "card": re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"),
}

SETTLE_JS = """
() => new Promise(resolve => {
  let last = performance.now(), done = false;
  const obs = new MutationObserver(() => { last = performance.now(); });
  obs.observe(document.documentElement, {subtree: true, childList: true, attributes: true, characterData: true});
  const start = performance.now();
  (function tick() {
    const now = performance.now();
    if (!done && (now - last > 300 || now - start > 4000)) {
      done = true; obs.disconnect(); resolve(now - start); return;
    }
    requestAnimationFrame(tick);
  })();
})
"""

VISIBLE_TEXT_JS = """
() => {
  const vals = [];
  for (const el of document.querySelectorAll('input, textarea, select')) {
    if (el.type === 'password' || el.type === 'hidden') continue;
    if (el.value) vals.push(el.value);
  }
  return (document.body ? document.body.innerText : '') + '\\n' + vals.join('\\n');
}
"""


TEXT_BOXES_JS = """
() => {
  // Rects of the visible TEXT itself (Range over text nodes), plus form controls:
  // what a callout must not hide. Element boxes would over-report -- a <label>
  // wrapping its input spans the input too.
  const out = [], vw = innerWidth, vh = innerHeight;
  const push = r => {
    if (r.width < 2 || r.height < 2 || r.bottom < 0 || r.right < 0 || r.top > vh || r.left > vw) return;
    out.push({x: +r.x.toFixed(1), y: +r.y.toFixed(1), width: +r.width.toFixed(1), height: +r.height.toFixed(1)});
  };
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const range = document.createRange();
  for (let n = walk.nextNode(); n && out.length < 300; n = walk.nextNode()) {
    if (!n.textContent.trim()) continue;
    const s = getComputedStyle(n.parentElement);
    if (s.visibility === 'hidden' || s.opacity === '0' || s.display === 'none') continue;
    range.selectNodeContents(n);
    for (const r of range.getClientRects()) push(r);
  }
  for (const el of document.body.querySelectorAll('input, select, textarea, button, img')) push(el.getBoundingClientRect());
  return out;
}
"""


class Refusal(Exception):
    def __init__(self, code: str, detail: str, step_id: str | None = None):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.step_id = code, detail, step_id


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def pii_findings(text: str, fixture: list) -> list:
    """PII-shaped tokens in text that are NOT declared fixture values."""
    found = []
    for kind, pat in PII_PATTERNS.items():
        for m in pat.finditer(text):
            token = m.group(0)
            if not any(token in f or f in token for f in fixture if f):
                found.append((kind, token))
    return found


def _locator(page, step: Step):
    t = step.target
    if t.kind == "role":
        return page.get_by_role(t.value, name=t.name, exact=True)
    if t.kind == "label":
        # A control nested inside its <label> (a common pattern) gets the whole
        # label text as its name, options included, so an exact match misses it.
        # Fall back to contains; resolve() still demands exactly one match.
        exact = page.get_by_label(t.value, exact=True)
        return exact if exact.count() else page.get_by_label(t.value)
    if t.kind == "testid":
        return page.get_by_test_id(t.value)
    if t.kind == "text":
        return page.get_by_text(t.value, exact=True)
    return page.locator(t.value)


class Capture:
    def __init__(self, spec: DemoSpec, viewport_name: str, out: Path, probe: bool):
        self.spec, self.out, self.probe = spec, out, probe
        vps = [v for v in spec.viewports if v.name == viewport_name]
        if not vps:
            raise SpecError(f"viewport '{viewport_name}' not in spec ({[v.name for v in spec.viewports]})")
        self.vp = vps[0]
        self.frames_dir = out / "frames"
        self.t0 = 0.0
        self.frame_no = 0
        self.console_errors: list = []
        self.http_errors: list = []
        self.steps: list = []
        self.idle_timeouts = 0

    # ---- helpers ---------------------------------------------------------
    def now_ms(self) -> int:
        return int((time.monotonic() - self.t0) * 1000)

    def settle(self, page) -> int:
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            # Long-polling apps never go idle; DOM stability below still bounds
            # the wait. Counted so the telemetry says how often this happened.
            self.idle_timeouts += 1
        return int(page.evaluate(SETTLE_JS))

    def scan(self, page, step_id: str) -> None:
        text = page.evaluate(VISIBLE_TEXT_JS)
        for forbidden in self.spec.forbid_text:
            if forbidden and forbidden in text:
                raise Refusal("FORBIDDEN_TEXT", f"'{forbidden}' is on screen", step_id)
        fixture = self.spec.fixture_text + [os.environ[v] for v in self.spec.fixture_env if os.environ.get(v)]
        leaks = pii_findings(text, fixture)
        if leaks:
            kinds = sorted({k for k, _ in leaks})
            raise Refusal("PRIVACY_REFUSED",
                          f"{len(leaks)} undeclared personal-data token(s) of kind {kinds}; "
                          f"declare them in fixture_text only if they are synthetic", step_id)

    def shot(self, page, rec: dict, kind: str, caret: bool = False) -> None:
        if self.probe or not rec["film"]:
            return
        self.scan(page, rec["id"])
        name = f"f{self.frame_no:04d}_{rec['id']}_{kind}.png"
        path = self.frames_dir / name
        page.screenshot(path=str(path), animations="disabled",
                        caret="initial" if caret else "hide", scale="device")
        self.frame_no += 1
        rec["frames"].append({"file": name, "t_ms": self.now_ms(), "kind": kind,
                              "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})

    def resolve(self, page, step: Step, rec: dict):
        loc = _locator(page, step)
        deadline = time.monotonic() + step.timeout_ms / 1000
        count = 0
        while time.monotonic() < deadline:
            count = loc.count()
            if count == 1 and loc.is_visible():
                break
            time.sleep(0.2)
        if count == 0:
            raise Refusal("TARGET_DRIFT", f"{step.target.describe()} not found on {page.url}", step.id)
        if count > 1:
            raise Refusal("TARGET_AMBIGUOUS", f"{step.target.describe()} matched {count} elements", step.id)
        if not loc.is_visible():
            raise Refusal("TARGET_DRIFT", f"{step.target.describe()} exists but is not visible", step.id)
        loc.scroll_into_view_if_needed(timeout=step.timeout_ms)
        self.settle(page)
        box = loc.bounding_box()
        if not box:
            raise Refusal("TARGET_DRIFT", f"{step.target.describe()} has no layout box", step.id)
        label = (loc.inner_text(timeout=2000) if step.do != "fill" else "") or ""
        rec["target"] = {"describe": step.target.describe(),
                         "box": {k: round(box[k], 2) for k in ("x", "y", "width", "height")},
                         "text_sha256": hashlib.sha256(label.strip().encode("utf-8")).hexdigest()}
        if step.callout:
            rec["text_boxes"] = page.evaluate(TEXT_BOXES_JS)
        return loc

    def value_for(self, step: Step) -> str:
        if step.value_env:
            v = os.environ.get(step.value_env)
            if not v:
                raise Refusal("BLOCKED_ENV", f"environment variable {step.value_env} is not set", step.id)
            return v
        return step.value or ""

    # ---- one step ----------------------------------------------------------
    def run_step(self, page, step: Step) -> None:
        rec = {"id": step.id, "do": step.do, "film": step.film, "t_start_ms": self.now_ms(),
               "frames": [], "hold_ms": step.hold_ms, "callout": step.callout,
               "secret": step.secret, "typed": step.typed}
        self.steps.append(rec)
        if step.do == "goto":
            url = self.spec.base_url + step.path
            resp = page.goto(url, wait_until="domcontentloaded", timeout=step.timeout_ms)
            if resp is not None and resp.status >= 400:
                # A broken route is not selector drift: name it, or the reader fixes the wrong thing.
                raise Refusal("PRODUCT_ERROR", f"{step.path} answered HTTP {resp.status}", step.id)
            self.settle(page)
            if "sign-in" in page.url and "sign-in" not in step.path:
                raise Refusal("AUTH_REDIRECT", f"{step.path} redirected to {page.url}", step.id)
            rec["url"] = page.url
            self.shot(page, rec, "arrive")
        elif step.do == "assert_absent":
            if step.text in page.evaluate(VISIBLE_TEXT_JS):
                raise Refusal("FORBIDDEN_TEXT", f"'{step.text}' must be absent", step.id)
        elif step.do == "wait_text":
            loc = page.get_by_text(step.text).first
            deadline = time.monotonic() + step.timeout_ms / 1000
            while time.monotonic() < deadline:
                if loc.count() and loc.is_visible():
                    break
                self.shot(page, rec, "working")        # real in-progress states
                time.sleep(0.6)
            else:
                raise Refusal("PRODUCT_ERROR", f"'{step.text}' never appeared within {step.timeout_ms} ms",
                              step.id)
            self.settle(page)
            rec["result_ms"] = self.now_ms() - rec["t_start_ms"]
            self.shot(page, rec, "result")
        else:
            loc = self.resolve(page, step, rec)
            self.shot(page, rec, "before")
            if step.do == "fill":
                value = self.value_for(step)
                rec["chars"] = len(value)
                if step.secret or not step.typed or self.probe:
                    loc.fill(value)
                else:
                    loc.fill("")
                    # 2-6 real intermediate states: enough to read as typing,
                    # few enough that each chunk is a genuine settled frame.
                    k = 1 if len(value) < 2 else min(6, max(2, -(-len(value) // 3)))
                    cuts = [round(len(value) * (i + 1) / k) for i in range(k)]
                    prev = 0
                    for c in cuts:
                        loc.press_sequentially(value[prev:c])
                        prev = c
                        self.shot(page, rec, f"typing{c}", caret=True)
                # Never trust a fill. Measured on a live Next.js app: a value typed
                # before hydration was silently reset to "" by the controlled input,
                # and the submit then failed on native validation. Filming that
                # would show typing that the product threw away.
                self.settle(page)
                held = loc.input_value()
                if held != value:
                    shown = f"{len(held)} chars" if step.secret else repr(held[:40])
                    raise Refusal("INPUT_NOT_ACCEPTED",
                                  f"{step.target.describe()} holds {shown} after filling "
                                  f"{len(value)} chars", step.id)
            elif step.do == "select":
                value = self.value_for(step)
                try:
                    loc.select_option(label=value)
                except Exception:
                    loc.select_option(value=value)
            elif step.do == "check":
                loc.check()
            elif step.do == "press":
                loc.press(step.value)
            elif step.do == "hover":
                loc.hover(timeout=step.timeout_ms)   # real hover state; nothing is activated
            elif step.do == "click":
                box = rec["target"]["box"]
                rec["click_point"] = {"x": round(box["x"] + box["width"] / 2, 2),
                                      "y": round(box["y"] + box["height"] / 2, 2)}
                rec["event_ms"] = self.now_ms()
                loc.click(timeout=step.timeout_ms)
            self.settle(page)
            self.shot(page, rec, "after")
        rec["t_end_ms"] = self.now_ms()

    # ---- whole run -----------------------------------------------------------
    def run(self) -> dict:
        from playwright.sync_api import sync_playwright
        self.out.mkdir(parents=True, exist_ok=True)
        if not self.probe:
            self.frames_dir.mkdir(exist_ok=True)
        result = {"spec_id": self.spec.id, "spec_sha256": self.spec.sha256, "viewport": vars(self.vp),
                  "base_url": self.spec.base_url, "probe": self.probe, "started_utc": _utc(),
                  "outcome": "ok", "refusal": None}
        allowed = self.spec.allow_http_errors
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=["--force-color-profile=srgb", "--hide-scrollbars",
                                               "--disable-lcd-text"])
            try:
                ctx = browser.new_context(
                    viewport={"width": self.vp.width, "height": self.vp.height},
                    device_scale_factor=self.vp.dsf, is_mobile=self.vp.is_mobile,
                    has_touch=self.vp.is_mobile, locale=self.spec.locale,
                    timezone_id=self.spec.timezone, service_workers="block")
                page = ctx.new_page()
                page.on("console", lambda m: m.type == "error" and self.console_errors.append(
                    {"t_ms": self.now_ms(), "text": m.text[:300]}))
                page.on("pageerror", lambda e: self.console_errors.append(
                    {"t_ms": self.now_ms(), "text": f"pageerror: {str(e)[:300]}"}))
                page.on("response", lambda r: r.status >= 400 and not any(a in r.url for a in allowed)
                        and self.http_errors.append({"t_ms": self.now_ms(), "status": r.status,
                                                     "url": r.url[:200]}))
                self.t0 = time.monotonic()
                for step in self.spec.steps:
                    self.run_step(page, step)
                if self.http_errors:
                    raise Refusal("PRODUCT_ERROR", f"{len(self.http_errors)} HTTP error response(s), first "
                                  f"{self.http_errors[0]['status']} {self.http_errors[0]['url']}")
                if self.console_errors:
                    raise Refusal("PRODUCT_ERROR", f"{len(self.console_errors)} console error(s), first: "
                                  f"{self.console_errors[0]['text']}")
            except Refusal as r:
                result.update(outcome="refused",
                              refusal={"code": r.code, "detail": r.detail, "step": r.step_id})
            finally:
                browser.close()
        result.update(ended_utc=_utc(), steps=self.steps, console_errors=self.console_errors,
                      http_errors=self.http_errors, frame_count=self.frame_no,
                      network_idle_timeouts=self.idle_timeouts)
        (self.out / "telemetry.json").write_text(json.dumps(result, indent=2, ensure_ascii=False),
                                                 encoding="utf-8")
        return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec", required=True)
    ap.add_argument("--viewport", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--probe", action="store_true", help="resolve targets only, no screenshots")
    a = ap.parse_args(argv)
    try:
        spec = load(a.spec)
        res = Capture(spec, a.viewport, Path(a.out), a.probe).run()
    except SpecError as exc:
        print(f"SPEC_INVALID: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except ImportError as exc:
        print(f"BLOCKED_ENV: playwright not importable: {exc}", file=sys.stderr)
        return EXIT_REFUSED
    print(json.dumps({"outcome": res["outcome"], "refusal": res["refusal"], "frames": res["frame_count"]}))
    return EXIT_OK if res["outcome"] == "ok" else EXIT_REFUSED


if __name__ == "__main__":
    raise SystemExit(main())
