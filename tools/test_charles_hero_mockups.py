"""V-CHM-*: the charles-hero-mockups absorption (skills/charles-hero-mockups, NOTICE.md).

Run from the repo root: python tools/test_charles_hero_mockups.py   (exit 0 = all gates pass)
Drives the vendored script for real (check, render --dry-run) with OPENAI_API_KEY removed, so nothing is spent and no
network call can happen, and pins the design-router kind that loads the skill without it being named.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.cdio import design_route as dr  # noqa: E402

SKILL = ROOT / "skills" / "charles-hero-mockups"
MIRROR = Path.home() / ".claude" / "skills" / "charles-hero-mockups"
SCRIPT = SKILL / "scripts" / "heroes.py"
FILES = ["SKILL.md", "README.md", "NOTICE.md", "references/craft.md", "scripts/heroes.py", "scripts/ocr.swift"]

# One invented page, with non-ASCII copy on purpose: the encoding gate needs "Común" in it.
CONCEPTS = {"miga": {
    "brand": "Miga Común", "what": "panadería cooperativa de barrio, para vecinos",
    "layout": "word-behind", "subject": "one dark rye loaf, cut open, crumb catching the light",
    "background": "raw linen", "light": "one hard window light from high left, the loaf lit, the linen falling to shadow",
    "headline": "Pan común", "headline_note": "The loaf sits in front of the word, hiding part of the o.",
    "ui": "wordmark 'Miga Común', nav 'Pan, Horario, Socios', button 'Hacerse socio', caption 'Calle Mayor 12'",
    "palette": [["linen", "#E9E2D4"], ["ink", "#2B2420"], ["blue", "#1F5FD8"]],
    "variations": ["whole loaf", "loaf cut by two edges", "camera lower", "closer, crumb filling half",
                   "steam rising off the cut"],
}}

results = []


def ok(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  :: %s" % (detail,)))


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(args, project, utf8=True):
    env = {k: v for k, v in os.environ.items() if k not in ("OPENAI_API_KEY", "PYTHONUTF8", "PYTHONIOENCODING")}
    cmd = [sys.executable] + (["-X", "utf8"] if utf8 else []) + ["-I", str(SCRIPT)] + args + ["--project", str(project)]
    return subprocess.run(cmd, capture_output=True, env=env, timeout=120, cwd=str(project))


def main():
    # --- vendored files, notice, mirror ---
    missing = [f for f in FILES if not (SKILL / f).is_file()]
    ok("V-CHM-FILES-PRESENT", not missing, missing)
    head = (SKILL / "SKILL.md").read_text(encoding="utf-8").split("---")[1] if not missing else ""
    ok("V-CHM-SKILL-FRONTMATTER", "name: charles-hero-mockups" in head and "description:" in head, head[:120])
    notice = (SKILL / "NOTICE.md").read_text(encoding="utf-8") if (SKILL / "NOTICE.md").is_file() else ""
    ok("V-CHM-NOTICE", "MIT License" in notice and "738e27ffecda9e8ac37279cfc37446d7ef22794d" in notice
       and "Copyright (c) 2026 Charles Liu" in notice, notice[:200])
    drift = [f for f in FILES if not (MIRROR / f).is_file() or sha(MIRROR / f) != sha(SKILL / f)]
    ok("V-CHM-MIRROR-IN-SYNC", not drift, "out of sync or missing in %s: %s" % (MIRROR, drift))

    # --- the script, driven for real with no key ---
    with tempfile.TemporaryDirectory() as td:
        proj = Path(td)
        (proj / "concepts.json").write_text(json.dumps(CONCEPTS, ensure_ascii=False, indent=1), encoding="utf-8")
        r = run(["check"], proj)
        report = proj / "out" / "check.json"
        ok("V-CHM-CHECK-RUNS-WITHOUT-KEY", r.returncode == 0 and report.is_file(),
           (r.returncode, r.stderr.decode("utf-8", "replace")[-400:]))
        flags = json.loads(report.read_text(encoding="utf-8"))["set_flags"] if report.is_file() else ["no report"]
        ok("V-CHM-CHECK-FIXTURE-CLEAN", flags == [], flags)

        # check must also be able to say no: a page missing fields is flagged
        bad = {"x": {"brand": "X", "layout": "nowhere"}}
        (proj / "concepts.json").write_text(json.dumps(bad), encoding="utf-8")
        run(["check"], proj)
        bflags = json.loads(report.read_text(encoding="utf-8"))["set_flags"] if report.is_file() else []
        ok("V-CHM-CHECK-FLAGS-A-BAD-PAGE", any("missing" in f for f in bflags) and any("layout" in f for f in bflags),
           bflags)

        (proj / "concepts.json").write_text(json.dumps(CONCEPTS, ensure_ascii=False, indent=1), encoding="utf-8")
        r = run(["render", "--dry-run"], proj)
        out = r.stdout.decode("utf-8", "replace")
        ok("V-CHM-DRYRUN-NO-KEY-NO-SPEND", r.returncode == 0 and out.count("=====") == 5 and not (proj / "out" / "log.jsonl").exists(),
           (r.returncode, out[:200], r.stderr.decode("utf-8", "replace")[-300:]))
        ok("V-CHM-DRYRUN-UTF8-INTACT", "Miga Común" in out and "ComÃºn" not in out, out[:300])

        # negative control: without -X utf8 the same file reaches the prompt garbled on a cp1252 host, which is why
        # the SKILL addendum and the router advice demand the flag. Only meaningful where the locale is not UTF-8.
        if os.name == "nt":
            r2 = run(["render", "--dry-run"], proj, utf8=False)
            garbled = r2.stdout.decode("cp1252", "replace")
            ok("V-CHM-UTF8-FLAG-IS-NEEDED", "ComÃºn" in garbled, garbled[:300])

        # no network path was taken: a render without a key must refuse, not call out
        r3 = run(["render"], proj)
        err = (r3.stdout + r3.stderr).decode("utf-8", "replace")
        ok("V-CHM-RENDER-REFUSES-WITHOUT-KEY", r3.returncode != 0 and "OPENAI_API_KEY not found" in err, err[-300:])

    # --- router: loads the skill unnamed, and does not steal ordinary web work ---
    routes = dr.load_routes()
    c = lambda p: dr.classify(p, routes)  # noqa: E731
    pos = ["haz cuatro hero mockups para una cerámica", "three hero directions for my app's landing page",
           "dame direcciones de arte para la landing de la panadería", "mock up a hero for our coffee brand",
           "maquetas del hero para la web nueva", "Awwwards-style hero art for an invented brand"]
    ok("V-CHM-ROUTE-POSITIVE", all("hero_mockup" in c(p) for p in pos), {p: c(p) for p in pos})
    ok("V-CHM-ROUTE-OVERRIDES-WEB", all("web" not in c(p) for p in pos), {p: c(p) for p in pos})
    neg = ["build the hero section of the landing page", "cambia la imagen del hero de la landing",
           "add a hero image to the homepage", "rediseña la web del despacho", "make a 30 s promo video for the launch"]
    ok("V-CHM-ROUTE-NEGATIVE", all("hero_mockup" not in c(p) for p in neg), {p: c(p) for p in neg})
    ok("V-CHM-ROUTE-WEB-STAYS-WEB", c("build the hero section of the landing page") == ["web"],
       c("build the hero section of the landing page"))
    pol = dr.policy(["hero_mockup"], routes)
    ok("V-CHM-ROUTE-REQUIRES-SKILL", pol["required"] == ["charles-hero-mockups"] and not pol["review"]
       and any("-X utf8" in a and "$5" in a for a in pol["advice"]), pol)

    failed = [n for n, good in results if not good]
    print("\n%d/%d V-CHM gates pass" % (len(results) - len(failed), len(results)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
