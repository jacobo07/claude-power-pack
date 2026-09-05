#!/usr/bin/env python3
"""Done-gate for the motion-promo skill.  V-MOTION-*

Every check drives a branch that could actually fail. The palette and
determinism checks run against the real engine in a real browser rather
than a Python restatement of it — a reimplementation can only ever agree
with itself.

    python tools/test_motion_promo.py

Exit 0 = every gate passed.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL / "assets" / "film.template.html"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

_passes: list[str] = []
_fails: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    _passes.append(gate)
    print(f"PASS  {gate:<34} {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    _fails.append(gate)
    print(f"FAIL  {gate:<34} {diagnostic}")


# ── static ──────────────────────────────────────────────────────────────
def test_layout() -> None:
    missing = [str(p.relative_to(SKILL)) for p in (
        TEMPLATE,
        SCRIPTS / "new_film.py",
        SCRIPTS / "render_film.py",
        SCRIPTS / "contact_sheet.py",
        SKILL / "SKILL.md",
    ) if not p.is_file()]
    if missing:
        _fail("V-MOTION-LAYOUT", f"missing: {', '.join(missing)}")
    else:
        _ok("V-MOTION-LAYOUT", "template, 3 scripts and SKILL.md present")


def test_shots_derived() -> None:
    """new_film.py must read the shot list OUT of the template, so it can
    never claim a shot the engine cannot draw."""
    import new_film

    text = TEMPLATE.read_text(encoding="utf-8")
    shots = new_film.known_shots(text)
    if len(shots) < 10:
        _fail("V-MOTION-SHOTS", f"only {len(shots)} shots found: {shots}")
        return
    # Positive control: a template with no shots must yield an empty list,
    # otherwise this check could be passing on a hardcoded fallback.
    if new_film.known_shots("no shots here"):
        _fail("V-MOTION-SHOTS", "known_shots() invents shots when given none")
        return
    _ok("V-MOTION-SHOTS", f"{len(shots)} shots derived from the engine: {', '.join(shots)}")


def test_validation() -> None:
    import new_film

    shots = new_film.known_shots(TEMPLATE.read_text(encoding="utf-8"))
    good = {
        "title": "T", "aspect": "9:16", "fps": 30, "brand": {"hero": "#00D4FF"},
        "beats": [{"shot": "title", "dur": 3.0, "text": "one two three"},
                  {"shot": "type-line", "dur": 3.5, "text": "four five six"},
                  {"shot": "number-slam", "dur": 3.5, "value": "40%", "text": "seven"},
                  {"shot": "logo-lockup", "dur": 4.0, "text": "BRAND", "sub": "brand.app"}],
    }
    errs, _ = new_film.validate(good, shots)
    if errs:
        _fail("V-MOTION-VALIDATE-OK", f"a valid spec was rejected: {errs}")
    else:
        _ok("V-MOTION-VALIDATE-OK", "a well-formed 4-beat spec validates clean")

    # RED branch — each of these MUST produce an error, or the gate is decorative.
    bad_cases = {
        "unknown shot":  {**good, "beats": [{"shot": "explode", "dur": 3.0, "text": "x"}]},
        "bad aspect":    {**good, "aspect": "4:3"},
        "no beats":      {**good, "beats": []},
        "zero duration": {**good, "beats": [{"shot": "title", "dur": 0, "text": "x"}]},
        "bad hex":       {**good, "brand": {"hero": "not-a-colour"}},
        "bad fps":       {**good, "fps": 900},
    }
    unflagged = [name for name, spec in bad_cases.items() if not new_film.validate(spec, shots)[0]]
    if unflagged:
        _fail("V-MOTION-VALIDATE-REJECT", f"accepted broken specs: {', '.join(unflagged)}")
    else:
        _ok("V-MOTION-VALIDATE-REJECT", f"all {len(bad_cases)} malformed specs rejected")


def test_build(tmp: Path) -> Path | None:
    import new_film

    spec = {
        "title": "Gate", "aspect": "16:9", "fps": 30, "brand": {"hero": "#00D4FF"},
        "beats": [{"shot": "title", "dur": 0.5, "text": "Alpha beat"},
                  {"shot": "number-slam", "dur": 0.5, "value": "40%", "text": "beta"}],
    }
    spec_path = tmp / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    out = tmp / "gate.html"
    rc = new_film.main(["--spec", str(spec_path), "--out", str(out)])
    if rc != 0 or not out.is_file():
        _fail("V-MOTION-BUILD", f"new_film returned {rc}")
        return None
    text = out.read_text(encoding="utf-8")
    if '"shot": "number-slam"' not in text:
        _fail("V-MOTION-BUILD", "the built html does not carry the spec's beats")
        return None
    if "window.__renderFrame" not in text:
        _fail("V-MOTION-BUILD", "the built html lost the engine")
        return None
    _ok("V-MOTION-BUILD", f"{out.name} carries both the spec and the engine")
    return out


# ── live engine ─────────────────────────────────────────────────────────
def test_engine(film: Path) -> None:
    from playwright.sync_api import sync_playwright

    errors: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--force-color-profile=srgb", "--hide-scrollbars"])
        page = browser.new_page(viewport={"width": 640, "height": 360}, device_scale_factor=1)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.goto(film.as_uri() + "?capture=1", timeout=60_000)
        page.wait_for_function("window.__ready === true", timeout=60_000)
        meta = page.evaluate("window.__meta")

        # -- palette band, measured from the real makePalette ------------
        probes = {
            "#00D4FF": "cyan", "#00D4A0": "teal", "#6633EE": "violet",
            "#FF2FB0": "magenta", "#FF6A3D": "warm orange", "#2E6BFF": "blue",
        }
        band = page.evaluate(
            """hexes => hexes.map(h => {
                 const p = makePalette(h, null);
                 return { hex:h, hero:p.heroH, open:p.hueAt(0), close:p.hueAt(1) };
               })""",
            list(probes),
        )
        off_arc, not_warming = [], []
        for row in band:
            span = row["close"] - row["open"]
            if span <= 0:
                not_warming.append(row["hex"])
            hero = row["hero"]
            hero_alt = hero + 360
            on = (row["open"] - 0.5 <= hero <= row["close"] + 0.5) or \
                 (row["open"] - 0.5 <= hero_alt <= row["close"] + 0.5)
            if not on:
                off_arc.append(f"{row['hex']} hero={hero:.0f} arc={row['open']:.0f}..{row['close']:.0f}")
        if not_warming:
            _fail("V-MOTION-PALETTE-WARMS", f"arc does not travel cool->warm for {not_warming}")
        else:
            _ok("V-MOTION-PALETTE-WARMS", f"all {len(band)} brand hues travel cool->warm")
        if off_arc:
            _fail("V-MOTION-PALETTE-HERO", "brand colour is not on its own arc: " + "; ".join(off_arc))
        else:
            _ok("V-MOTION-PALETTE-HERO",
                "brand hue lies on the arc for " + ", ".join(probes.values()))

        # -- every shot draws without throwing ---------------------------
        # sorted(set(...)): the engine also *reads* SHOTS["title"] as its
        # fallback, so a raw findall counts that shot twice.
        shots = sorted(set(re.findall(r'SHOTS\["([a-z-]+)"\]',
                                      TEMPLATE.read_text(encoding="utf-8"))))
        drew = page.evaluate(
            """names => {
                 const bad = [];
                 for (const n of names){
                   try {
                     const c = document.createElement('canvas');
                     c.width = 400; c.height = 400;
                     const x = c.getContext('2d');
                     SHOTS[n](x, {shot:n, dur:2, text:'Five word line here now',
                                  value:'40%', sub:'sub',
                                  items:[{glyph:'clock'},{glyph:'check'}]},
                              0.5, 260, Math.random);
                   } catch (e) { bad.push(n + ': ' + e.message); }
                 }
                 return bad;
               }""",
            shots,
        )
        if drew:
            _fail("V-MOTION-SHOTS-DRAW", "; ".join(drew))
        else:
            _ok("V-MOTION-SHOTS-DRAW", f"all {len(shots)} shots drew without throwing")

        # -- determinism: the same frame twice must be the same bytes ----
        page.set_viewport_size({"width": meta["w"], "height": meta["h"]})
        clip = {"x": 0, "y": 0, "width": meta["w"], "height": meta["h"]}
        mid = meta["frames"] // 2
        page.evaluate("i => window.__renderFrame(i)", mid)
        a = page.screenshot(clip=clip)
        page.evaluate("i => window.__renderFrame(0)", 0)      # move away
        page.evaluate("i => window.__renderFrame(i)", mid)    # and back
        b = page.screenshot(clip=clip)
        if a != b:
            _fail("V-MOTION-DETERMINISM", f"frame {mid} differs between two renders "
                                          f"({len(a)} vs {len(b)} bytes)")
        else:
            _ok("V-MOTION-DETERMINISM", f"frame {mid} is byte-identical across renders")

        browser.close()

    if errors:
        _fail("V-MOTION-NO-JS-ERRORS", f"{len(errors)} page error(s): {errors[0][:120]}")
    else:
        _ok("V-MOTION-NO-JS-ERRORS", "no uncaught page errors while driving the engine")


def test_encode(film: Path, tmp: Path) -> None:
    out = tmp / "gate.mp4"
    rc = subprocess.run(
        [sys.executable, str(SCRIPTS / "render_film.py"), str(film),
         "--out", str(out), "--scale", "0.25", "--preset", "ultrafast"],
        capture_output=True, text=True,
    )
    if rc.returncode != 0 or not out.is_file():
        _fail("V-MOTION-ENCODE", f"render_film exited {rc.returncode}: {rc.stderr[-300:]}")
        return
    import imageio_ffmpeg
    probe = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-i", str(out)],
                           capture_output=True, text=True).stderr
    if "Video: h264" not in probe:
        _fail("V-MOTION-ENCODE", f"output is not H.264. ffmpeg said: {probe[-300:]}")
        return
    _ok("V-MOTION-ENCODE", f"{out.name} is H.264, {out.stat().st_size:,} bytes")


def main() -> int:
    print("motion-promo done-gate\n" + "-" * 62)
    test_layout()
    test_shots_derived()
    test_validation()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        film = test_build(tmp)
        if film:
            test_engine(film)
            test_encode(film, tmp)
        else:
            _fail("V-MOTION-ENGINE", "skipped: nothing was built to drive")
    total = len(_passes) + len(_fails)
    print("-" * 62)
    print(f"MOTION_PROMO_PASS={len(_passes)}/{total}  threshold={total}/{total}")
    return 0 if not _fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
