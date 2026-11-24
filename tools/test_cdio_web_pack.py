#!/usr/bin/env python3
"""test_cdio_web_pack.py -- done-gate for CDIO-13, the Creative Web Pack (V-CDIO-WEBPACK-*).

Spec: vault/specs/cdio-13-creative-web-pack.md. Hermetic, read-only: it reads the
dataset, the vendored tree, the CDIO wiring points and the agents' live mirrors,
and drives the real scorer. It writes nothing and touches no network.

  V-CDIO-WEBPACK-DATASET    CDIO-13 sealed, governed by CDIO-00, source + evidence recorded
  V-CDIO-WEBPACK-FIDELITY   3 websites, 10 repos, 6 flow steps, 3 recipes, 4 checks and the
                            verbatim prompt present, in order (red drill: a removed recipe)
  V-CDIO-WEBPACK-CRITERIA   every sec.8 criterion names a scorable dimension and a severity
                            (population floor + red drill)
  V-CDIO-WEBPACK-SCORABLE   each criterion, as a failing verdict, lowers the real score
  V-CDIO-WEBPACK-VENDOR     every manifest file exists with its upstream sha256, nothing
                            unlisted on disk, every repo carries its licence, 317 SKILL.md
                            (red drills: one flipped byte, one stray file)
  V-CDIO-WEBPACK-RECIPES    every vendored path a recipe names exists
  V-CDIO-WEBPACK-LIVE       the 3 live skills are licensed and hash-pinned; the real installer,
                            driven in temp dirs, installs them, never overwrites, skips a
                            plugin-provided one, copies nothing from a tampered copy; both
                            install.ps1 and install.sh call it (only temp dirs are written)
  V-CDIO-WEBPACK-HONEST     collisions, unviewed images, PLANNED run, no-live-install recorded
  V-CDIO-WEBPACK-WIRED      kernel governs CDIO-13; the three agents name it
  V-CDIO-WEBPACK-MIRRORS    repo agents == live agents (red drill on drift)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

# One parser for one grammar, shared with CDIO-08 and CDIO-12.
from test_cdio_mobile import (  # noqa: E402
    AGENTS, CDIO, HOME_CLAUDE, _read, _section, mirror_drift, parse_criteria)

DATASET = os.path.join(CDIO, "CDIO-13-creative-web-pack.md")
WEBPACK = os.path.join(CDIO, "web-pack")
VENDOR = os.path.join(WEBPACK, "vendor")
MANIFEST = os.path.join(WEBPACK, "manifest.json")

EXPECTED_CRITERIA = {
    "layout-before-motion", "smooth-scroll-yields", "mobile-motion-checked",
    "one-signature-interaction", "stable-layout-while-loading", "webgl-has-fallback",
    "3d-assets-budgeted", "animations-cleaned-up", "split-text-stays-readable",
}
EXPECTED_CRITICAL = {"smooth-scroll-yields"}
EXPECTED_SKILLS = 317
EXPECTED_REPOS = {
    "greensock/gsap-skills", "nateherkai/scroll-craft", "MengTo/Skills",
    "iart-ai/web-animation-skills", "iart-ai/webgl-animation-skills",
    "JustineBijuPaul/frontend-ai-skills", "anthropics/skills",
}
# The ten repos of the PDF, in its order (pages 6-7).
PDF_REPOS = [
    "greensock/gsap-skills", "nateherkai/scroll-craft", "MengTo/Skills",
    "iart-ai/web-animation-skills", "iart-ai/webgl-animation-skills",
    "JustineBijuPaul/frontend-ai-skills", "anthropics/skills", "darkroomengineering/lenis",
    "pmndrs/drei", "pmndrs/react-three-fiber",
]
# Anchors in document order: the pack's pages 3-9.
ANCHORS = (
    [rf"^### Website 0{n} — " for n in (1, 2, 3)]
    + [rf"^### Flow 0{n} — " for n in range(1, 7)]
    + [rf"^### Recipe 0{n} — " for n in (1, 2, 3)]
    + [rf"^### Check {n} — " for n in (1, 2, 3, 4)]
)
# Load-bearing sentences of the page-10 prompt; dropping one changes the brief.
PROMPT_LINES = [
    "Build an original website for [brand and audience].",
    "Create an\n> original composition with my content and brand.",
    "Build the responsive layout and working controls before adding motion.",
    "For 3D, optimize models and textures and add a fallback.",
    "Support keyboard navigation, readable contrast and reduced motion.",
]
LICENCE_RE = re.compile(r"(^|/)LICEN[CS]E(\.txt|\.md)?$")

_passes = 0
_fails = 0


def _ok(name, detail):
    global _passes
    _passes += 1
    print(f"[PASS] {name}: {detail}")


def _fail(name, detail):
    global _fails
    _fails += 1
    print(f"[FAIL] {name}: {detail}")


def anchor_gaps(text):
    """Return the anchors absent or out of order."""
    positions, gaps = [], []
    for a in ANCHORS:
        m = re.search(a, text, flags=re.M)
        if m:
            positions.append(m.start())
        else:
            gaps.append(a)
    if positions != sorted(positions):
        gaps.append("order")
    return gaps


def vendor_gaps(manifest, read_bytes, on_disk):
    """Return integrity problems: hash mismatch, missing, unlisted, unlicensed repos."""
    problems, listed = [], set()
    for repo in manifest["repos"]:
        folder = repo["repo"].replace("/", "__")
        paths = [f["path"] for f in repo["files"]]
        if not any(LICENCE_RE.search(p) for p in paths):
            problems.append(f"no licence: {repo['repo']}")
        for f in repo["files"]:
            rel = f"{folder}/{f['path']}"
            listed.add(rel)
            data = read_bytes(rel)
            if data is None:
                problems.append(f"missing: {rel}")
            elif hashlib.sha256(data).hexdigest() != f["sha256"]:
                problems.append(f"sha256: {rel}")
    problems += [f"unlisted: {p}" for p in sorted(set(on_disk) - listed)]
    return problems


def _disk_reader(rel):
    p = os.path.join(VENDOR, *rel.split("/"))
    if not os.path.isfile(p):
        return None
    with open(p, "rb") as fh:
        return fh.read()


def _disk_files():
    out = []
    for dp, _, fns in os.walk(VENDOR):
        for fn in fns:
            out.append(os.path.relpath(os.path.join(dp, fn), VENDOR).replace("\\", "/"))
    return out


def v_dataset():
    if not os.path.isfile(DATASET):
        _fail("V-CDIO-WEBPACK-DATASET", "CDIO-13 missing")
        return
    fm = re.match(r"^---(.*?)---", _read(DATASET), flags=re.S)
    fm = fm.group(1) if fm else ""
    need = ("id: CDIO-13", "status: sealed", "governed_by: CDIO-00",
            "source: PDF \"The WEB Pack\" (Sanjai Builds", "evidence:")
    missing = [n for n in need if n not in fm]
    if missing:
        _fail("V-CDIO-WEBPACK-DATASET", f"front matter lacks {missing}")
    else:
        _ok("V-CDIO-WEBPACK-DATASET", "sealed, governed by CDIO-00, source + evidence recorded")


def v_fidelity():
    text = _read(DATASET)
    gaps = anchor_gaps(text)
    repos = _section(text, 3)
    absent_repos = [r for r in PDF_REPOS if f"`{r}`" not in repos]
    prompt = _section(text, 7)
    absent_lines = [ln for ln in PROMPT_LINES if ln not in prompt]
    drilled = re.sub(r"^### Recipe 02 —.*$", "### Recipe two removed", text, flags=re.M)
    drill_ok = anchor_gaps(drilled) == [r"^### Recipe 02 — "]
    if gaps or absent_repos or absent_lines or not drill_ok:
        _fail("V-CDIO-WEBPACK-FIDELITY",
              f"anchors={gaps} repos={absent_repos} prompt={absent_lines} drill_ok={drill_ok}")
    else:
        _ok("V-CDIO-WEBPACK-FIDELITY",
            f"{len(ANCHORS)} anchors in order, {len(PDF_REPOS)} repos, "
            f"{len(PROMPT_LINES)} prompt lines verbatim; drill caught a removed recipe")


def v_criteria():
    found, malformed = parse_criteria(_section(_read(DATASET), 8))
    missing = sorted(EXPECTED_CRITERIA - set(found))
    critical = {n for n, (_, sev) in found.items() if sev == "critical"}
    _, drill_bad = parse_criteria(
        "**`synthetic-no-dimension`** (severity major). text\n"
        "**`synthetic-ok`** (dimension `ux`, severity minor). text\n")
    drill_ok = drill_bad == ["synthetic-no-dimension"]
    if malformed or missing or critical != EXPECTED_CRITICAL or not drill_ok:
        _fail("V-CDIO-WEBPACK-CRITERIA",
              f"malformed={malformed} missing={missing} critical={sorted(critical)} "
              f"drill_ok={drill_ok}")
    else:
        _ok("V-CDIO-WEBPACK-CRITERIA",
            f"{len(found)} criteria well-formed, {len(critical)} critical; "
            "red drill caught the synthetic one")
    return found


def v_scorable(found):
    from modules.cdio.scorer import Verdict, score_review
    baseline = score_review([Verdict("value-3s", "trust", "pass",
                                     observed="value stated")]).score
    bad = []
    for name, (dim, sev) in sorted(found.items()):
        r = score_review([Verdict(name, dim, "fail", sev,
                                  observed=f"synthetic observation for {name}")])
        if r.dropped or r.score is None or r.score >= baseline:
            bad.append((name, r.score, len(r.dropped)))
    if not found or bad:
        _fail("V-CDIO-WEBPACK-SCORABLE", f"found={len(found)} bad={bad}")
    else:
        _ok("V-CDIO-WEBPACK-SCORABLE",
            f"{len(found)} criteria accepted by the real scorer, each lowers it")


def v_vendor():
    if not os.path.isfile(MANIFEST):
        _fail("V-CDIO-WEBPACK-VENDOR", "manifest.json missing")
        return
    with open(MANIFEST, encoding="utf-8") as fh:
        manifest = json.load(fh)
    repos = {r["repo"] for r in manifest["repos"]}
    skills = sum(1 for r in manifest["repos"] for f in r["files"]
                 if f["path"].endswith("SKILL.md"))
    disk = _disk_files()
    problems = vendor_gaps(manifest, _disk_reader, disk)

    # Red drills on the same function, in memory: one flipped byte, one stray file.
    first = manifest["repos"][0]
    victim = f"{first['repo'].replace('/', '__')}/{first['files'][0]['path']}"

    def flipped(rel):
        data = _disk_reader(rel)
        if rel == victim and data:
            return bytes([data[0] ^ 1]) + data[1:]
        return data

    drill_hash = vendor_gaps(manifest, flipped, disk) == [f"sha256: {victim}"]
    drill_stray = vendor_gaps(manifest, _disk_reader, disk + ["stray/file.md"]) == \
        ["unlisted: stray/file.md"]
    if problems or repos != EXPECTED_REPOS or skills != EXPECTED_SKILLS \
            or not (drill_hash and drill_stray):
        _fail("V-CDIO-WEBPACK-VENDOR",
              f"problems={problems[:8]} (+{max(0, len(problems) - 8)}) repos={sorted(repos ^ EXPECTED_REPOS)} "
              f"skills={skills} drills=({drill_hash},{drill_stray})")
    else:
        nfiles = sum(len(r["files"]) for r in manifest["repos"])
        _ok("V-CDIO-WEBPACK-VENDOR",
            f"{nfiles} files hash-match upstream, {len(repos)} repos licensed, {skills} skills; "
            "drills caught a flipped byte and a stray file")


def v_recipes():
    sec = _section(_read(DATASET), 5)
    paths = re.findall(r"`([A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+/[^`]+?SKILL\.md)`", sec)
    absent = [p for p in paths if not os.path.isfile(os.path.join(VENDOR, *p.split("/")))]
    if len(paths) < 3 or absent:
        _fail("V-CDIO-WEBPACK-RECIPES", f"named={len(paths)} absent={absent}")
    else:
        _ok("V-CDIO-WEBPACK-RECIPES", f"{len(paths)} vendored skills named by recipes, all present")


LIVE_SKILLS = {"impeccable", "ui-ux-pro-max", "anydesign"}


def v_live():
    import shutil
    import tempfile
    from pathlib import Path
    from install_cdio_live_skills import LIVE, install, integrity_gaps

    manifest = json.loads((LIVE / "live-manifest.json").read_text(encoding="utf-8"))
    names = {s["name"] for s in manifest["skills"]}
    static = []
    for s in manifest["skills"]:
        paths = [f["path"] for f in s["files"]]
        if "SKILL.md" not in paths:
            static.append(f"{s['name']}: no SKILL.md")
        if not any(LICENCE_RE.search(p) for p in paths):
            static.append(f"{s['name']}: no licence")
        static += [f"{s['name']}: {g}" for g in integrity_gaps(s)]
    installers = {n: _read(os.path.join(ROOT, n)) for n in ("install.ps1", "install.sh")}
    unwired = [n for n, t in installers.items() if "install_cdio_live_skills.py" not in t]

    runtime = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        target, plugins = tmp / "skills", tmp / "plugins"
        code, res = install(target, plugins)
        if code != 0 or {n for n, o, _ in res if o == "INSTALLED"} != names:
            runtime.append(f"first install: {res}")
        for s in manifest["skills"]:
            copied = integrity_gaps(s, target)
            if copied:
                runtime.append(f"installed copy of {s['name']} differs: {copied[:2]}")
        marker = target / "anydesign" / "SKILL.md"
        marker.write_text("owner edit", encoding="utf-8")
        code, res = install(target, plugins)
        if code != 0 or any(o != "SKIP" for _, o, _ in res) or \
                marker.read_text(encoding="utf-8") != "owner edit":
            runtime.append(f"re-run overwrote or did not skip: {res}")
        # A marketplace clone on disk is not an installed plugin: the skill still installs.
        mkt = plugins / "marketplaces" / "m" / "plugins" / "ui" / "skills" / "ui-ux-pro-max"
        mkt.mkdir(parents=True)
        (mkt / "SKILL.md").write_text("marketplace source", encoding="utf-8")
        settings = tmp / "settings.json"
        target_m = tmp / "skills_m"
        _, res = install(target_m, plugins, settings)
        if {n: o for n, o, _ in res}.get("ui-ux-pro-max") != "INSTALLED":
            runtime.append(f"marketplace-only copy suppressed the install: {res}")
        # Installed + enabled plugin provides ui-ux-pro-max: no duplicate.
        ipath = plugins / "cache" / "x" / "ui" / "1.0"
        (ipath / ".claude" / "skills" / "ui-ux-pro-max").mkdir(parents=True)
        (ipath / ".claude" / "skills" / "ui-ux-pro-max" / "SKILL.md").write_text("p", encoding="utf-8")
        (plugins / "installed_plugins.json").write_text(json.dumps(
            {"version": 2, "plugins": {"ui@x": [{"installPath": str(ipath)}]}}), encoding="utf-8")
        settings.write_text(json.dumps({"enabledPlugins": {"ui@x": True}}), encoding="utf-8")
        target2 = tmp / "skills2"
        _, res = install(target2, plugins, settings)
        if {n: o for n, o, _ in res}.get("ui-ux-pro-max") != "SKIP" or \
                (target2 / "ui-ux-pro-max").exists():
            runtime.append(f"enabled plugin skill duplicated: {res}")
        # The same plugin disabled: it provides nothing, so the skill installs.
        settings.write_text(json.dumps({"enabledPlugins": {"ui@x": False}}), encoding="utf-8")
        target_d = tmp / "skills_d"
        _, res = install(target_d, plugins, settings)
        if {n: o for n, o, _ in res}.get("ui-ux-pro-max") != "INSTALLED":
            runtime.append(f"disabled plugin suppressed the install: {res}")
        # Red drill: a stray unlisted file in a live folder is refused, not shipped.
        live_s = tmp / "live_stray"
        shutil.copytree(LIVE, live_s)
        (live_s / "anydesign" / "stray.pyc").write_bytes(b"x")
        target_s = tmp / "skills_s"
        code, res = install(target_s, tmp / "none", live=live_s)
        if code != 1 or {n: o for n, o, _ in res}.get("anydesign") != "FAIL" or \
                (target_s / "anydesign").exists():
            runtime.append(f"stray-file drill not caught: {res}")
        # Red drill: a tampered live copy installs nothing for that skill.
        live2 = tmp / "live"
        shutil.copytree(LIVE, live2)
        victim = live2 / "impeccable" / "SKILL.md"
        data = victim.read_bytes()
        victim.write_bytes(bytes([data[0] ^ 1]) + data[1:])
        target3 = tmp / "skills3"
        code, res = install(target3, tmp / "none", live=live2)
        outcome = {n: o for n, o, _ in res}
        if code != 1 or outcome.get("impeccable") != "FAIL" or (target3 / "impeccable").exists():
            runtime.append(f"tamper drill not caught: {res}")

    if names != LIVE_SKILLS or static or unwired or runtime:
        _fail("V-CDIO-WEBPACK-LIVE",
              f"names={sorted(names)} static={static[:4]} unwired={unwired} runtime={runtime}")
    else:
        nfiles = sum(len(s["files"]) for s in manifest["skills"])
        _ok("V-CDIO-WEBPACK-LIVE",
            f"3 live skills ({nfiles} files) licensed + hash-pinned; installer installed, "
            "skipped without overwriting, skipped an enabled-plugin duplicate, installed past "
            "a marketplace-only and a disabled plugin, refused a tampered copy and a stray "
            "file; wired in install.ps1 + install.sh")


def v_honest():
    text = _read(DATASET)
    collisions, vendored, evidence = _section(text, 10), _section(text, 9), _section(text, 11)
    markers = {
        "collision 10.1 smooth scroll": "### 10.1" in collisions,
        "collision 10.2 references": "### 10.2" in collisions,
        "collision 10.3 webgl": "### 10.3" in collisions,
        "collision 10.4 vendored guidance": "### 10.4" in collisions,
        "never installed live": "never installed as live skills" in vendored,
        "outward effects need Owner": "human-facing-external-effects" in vendored,
        "images not viewed": re.search(r"\|\s*PDF images\s*\|\s*not viewed", evidence) is not None,
        "end-to-end run PLANNED": "**PLANNED**" in evidence,
        "backlog for the rest": "D44" in evidence,
    }
    absent = [k for k, ok in markers.items() if not ok]
    if absent:
        _fail("V-CDIO-WEBPACK-HONEST", f"no longer recorded: {absent}")
    else:
        _ok("V-CDIO-WEBPACK-HONEST", f"{len(markers)} limits and collisions recorded")


def wiring_gaps(texts):
    checks = {
        "kernel-governs": re.search(r"^governs:.*CDIO-13", texts["kernel"], flags=re.M) is not None,
        "agents": all("CDIO-13" in t for t in texts["agents"].values()),
    }
    return [c for c, ok in checks.items() if not ok]


def v_wired():
    texts = {
        "kernel": _read(os.path.join(CDIO, "CDIO-00-design-intelligence-kernel.md")),
        "agents": {n: _read(os.path.join(ROOT, "vault", "agents", n)) for n in AGENTS},
    }
    gaps = wiring_gaps(texts)
    drilled = dict(texts, kernel=texts["kernel"].replace("CDIO-13", "CDIO-1X"))
    drill_ok = wiring_gaps(drilled) == ["kernel-governs"]
    if gaps or not drill_ok:
        _fail("V-CDIO-WEBPACK-WIRED", f"not wired: {gaps} drill_ok={drill_ok}")
    else:
        _ok("V-CDIO-WEBPACK-WIRED", "kernel + 3 agents wired; drill caught a removed pointer")


def v_mirrors():
    pairs = [(os.path.join(ROOT, "vault", "agents", n), os.path.join(HOME_CLAUDE, "agents", n))
             for n in AGENTS]
    drift = mirror_drift(pairs)
    drill = mirror_drift([(DATASET, pairs[0][0])]) == [os.path.basename(DATASET)]
    if drift or not drill:
        _fail("V-CDIO-WEBPACK-MIRRORS", f"drift={drift} drill_ok={drill}")
    else:
        _ok("V-CDIO-WEBPACK-MIRRORS", f"{len(pairs)} live copies identical; drill caught drift")


def main():
    v_dataset()
    if not os.path.isfile(DATASET):
        print(f"CDIO_WEBPACK_PASS={_passes}/{_passes + _fails}")
        return 1
    v_fidelity()
    found = v_criteria()
    v_scorable(found)
    v_vendor()
    v_recipes()
    v_live()
    v_honest()
    v_wired()
    v_mirrors()
    total = _passes + _fails
    print(f"CDIO_WEBPACK_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
