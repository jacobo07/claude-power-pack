"""V-ASC-WEB gate: web vertical slice, 12 mandatory cases, each driven from both poles
(a seeded failure the instrument must catch, and a clean case it must pass).
python3 tools/test_asc_webslice.py (exit 0 == PASS)"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from modules.backlog_autopilot import webslice as W  # noqa: E402

FAILS = []


def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + (f" -- {d}" if d and not c else ""))
    if not c:
        FAILS.append(n)


def wr(d, rel, txt):
    p = Path(d) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(txt, encoding="utf-8")


if not W.chrome_path():
    print("FAIL instrument: no Chromium (set ASC_CHROME); gate cannot observe a render")
    sys.exit(2)

PROJECT_REACT = {"runtime": "react", "npm": []}
PROJECT_STATIC = {"runtime": "static-html", "npm": []}
INTENT = "landing page hero for a newsletter signup"

with tempfile.TemporaryDirectory() as t:
    t = Path(t)

    # ---- slice: the clean build, real render, real scorer ------------------------------------
    good = W.slice_run(t / "good")
    check("slice good: CDIO gate done (APPROVE, no critical)", good["surface"]["gate"]["is_done"],
          json.dumps(good["surface"]["gate"])[:300])
    check("slice good: Production Reality REAL", good["reality"]["verdict"] == "REAL", str(good["reality"]))
    check("slice good: legal gate APPROVE (privacy + terms linked)", good["legal"]["verdict"] == "APPROVE", str(good["legal"]))
    check("slice good: screenshot is a real PNG", W.png_ok(t / "good" / "render.png"))
    check("slice good: interaction observed in the browser",
          bool(good["surface"]["interactions"]) and all(i["ok"] for i in good["surface"]["interactions"]))

    # ---- 1 / 2 / 5 / 6 / 7: selection ---------------------------------------------------------
    cands = W.catalog_candidates()
    check("case 1 inputs discovered from the real catalog (not hand-listed)", len(cands) >= 50, str(len(cands)))
    sel = [W.select(INTENT, c, PROJECT_REACT, {"expressiveness": "high"}) for c in cands]
    chosen = [s for s in sel if s["decision"] == "SELECTED"]
    check("case 1: a useful resource is SELECTED from real candidates", len(chosen) >= 1, str(len(chosen)))
    check("case 1 pole: the same pool is not all-accepting (refusals exist)",
          any(s["decision"] != "SELECTED" for s in sel))

    base = W.Candidate("seed:ok", "MIT", "react", applies_to=["landing", "hero"], deps=[])
    check("case 1 control: clean seeded candidate SELECTED",
          W.select(INTENT, base, PROJECT_REACT, {"expressiveness": "high"})["decision"] == "SELECTED")
    unsuit = W.Candidate("seed:checkout-only", "MIT", "react", applies_to=["checkout"], excluded_from=["landing", "hero"])
    r2 = W.select(INTENT, unsuit, PROJECT_REACT, {"expressiveness": "high"})
    check("case 2: unsuitable resource REJECTED at the applicability gate",
          r2["decision"] == "REJECTED" and r2["gate"] == "applicability", str(r2))

    r5 = W.select(INTENT, W.Candidate("seed:agpl", "AGPL-3.0", "react", applies_to=["landing", "hero"]),
                  PROJECT_REACT, {"expressiveness": "high"})
    check("case 5: AGPL licence REFUSED at the licence gate", r5["decision"] == "REFUSED" and r5["gate"] == "license", str(r5))
    r5u = W.select(INTENT, W.Candidate("seed:unk", "UNKNOWN", "react", applies_to=["landing", "hero"]),
                   PROJECT_REACT, {"expressiveness": "high"})
    check("case 5: UNKNOWN licence is refused, never waved through", r5u["state"] == "LICENSE_UNKNOWN", str(r5u))

    r6 = W.select(INTENT, W.Candidate("seed:react-comp", "MIT", "react", applies_to=["landing", "hero"]),
                  PROJECT_STATIC, {"expressiveness": "high"})
    check("case 6: React component into a static-html project REFUSED (TECH_INCOMPATIBLE)",
          r6["decision"] == "REFUSED" and r6["state"] == "TECH_INCOMPATIBLE", str(r6))
    r6d = W.select(INTENT, W.Candidate("seed:needs-dep", "MIT", "react", applies_to=["landing", "hero"], deps=["framer-motion"]),
                   PROJECT_REACT, {"expressiveness": "high"})
    check("case 6: undeclared npm dependency REFUSED", r6d["state"] == "TECH_INCOMPATIBLE", str(r6d))

    flashy = W.Candidate("seed:flashy", "MIT", "react", applies_to=["landing", "hero"], min_expressiveness="high")
    r7 = W.select(INTENT, flashy, PROJECT_REACT, {"expressiveness": "none"})
    check("case 7: expressiveness 'none' contract honoured (high-expressiveness candidate REFUSED)",
          r7["decision"] == "REFUSED" and r7["gate"] == "expressiveness", str(r7))
    check("case 7 control: same candidate passes under a high ceiling",
          W.select(INTENT, flashy, PROJECT_REACT, {"expressiveness": "high"})["decision"] == "SELECTED")
    still = W.slice_run(t / "still", expressiveness="none", shot=False)
    check("case 7: a 'none' site renders with no motion at all and is still DONE",
          still["surface"]["observed"]["motion_present"] is False and still["surface"]["gate"]["is_done"],
          str(still["surface"]["observed"]))
    anim = W.slice_run(t / "anim", variant="animated", expressiveness="none", shot=False)
    check("case 7 pole: motion under a 'none' contract is NOT done",
          not anim["surface"]["gate"]["is_done"], json.dumps(anim["surface"]["gate"])[:300])
    anr = W.slice_run(t / "anr", variant="animated_no_reduce", expressiveness="restrained", shot=False)
    check("case 7 pole: motion without a reduced-motion equivalent is NOT done",
          not anr["surface"]["gate"]["is_done"], json.dumps(anr["surface"]["gate"])[:300])

    # ---- 3: backlog-only is not announced available (real ledger rows) ----------------------
    led = json.loads((ROOT / W.LEDGER).read_text(encoding="utf-8"))
    rows = led["rows"]
    bl = [r for r in rows if r["state"] == "BACKLOG_ONLY"]
    act = [r for r in rows if r["state"] == "ACTIVATED"]
    check("case 3 inputs: real ledger has BACKLOG_ONLY and ACTIVATED rows", bool(bl) and bool(act), f"{len(bl)} {len(act)}")
    check("case 3: honest announce says NOT_AVAILABLE for every real BACKLOG_ONLY row",
          all(W.announce(r) == "NOT_AVAILABLE_BACKLOG" for r in bl))
    check("case 3 pole: the naive announcer lies on the same real rows",
          len(W.announcement_lies(W.naive_announce, bl)) == len(bl))
    check("case 3: honest announce never says AVAILABLE for a row without exit-0 evidence",
          W.announcement_lies(W.announce, rows) == [])
    check("case 3 pole: naive announcer also lies on ACTIVATED-without-evidence rows",
          len(W.announcement_lies(W.naive_announce, [r for r in act if not r.get("execution_evidence")])) > 0)
    ok_row = dict(act[0], execution_evidence={"exit": 0, "cmd": "x"})
    bad_row = dict(act[0], execution_evidence={"exit": 1, "cmd": "x"})
    check("case 3 control: ACTIVATED + exit-0 evidence is AVAILABLE", W.announce(ok_row) == "AVAILABLE")
    check("case 3 control: ACTIVATED + exit-1 evidence is not", W.announce(bad_row) == "ACTIVATED_UNVERIFIED")

    # ---- 4: installed but unreachable skill -----------------------------------------------
    fx = t / "skillfx"
    wr(fx, "skills/wired-skill/SKILL.md", "# wired")
    wr(fx, "skills/orphan-skill/SKILL.md", "# orphan")
    wr(fx, "commands/go.md", "run the wired-skill before shipping\n")
    sr = W.skill_reachability(fx)
    check("case 4: installed-but-unreachable skill is flagged", sr["unreachable"] == ["orphan-skill"], str(sr))
    check("case 4 pole: a cited skill is reachable", sr["reachable"] == ["wired-skill"], str(sr))
    wr(fx, "skills/orphan-skill/SKILL.md", "# orphan\nmentions orphan-skill itself\n")
    check("case 4: a skill citing only itself stays unreachable",
          W.skill_reachability(fx)["unreachable"] == ["orphan-skill"])

    # ---- 8: existing design system is not overwritten ---------------------------------------
    site = t / "ds"
    site.mkdir()
    (site / "DESIGN.md").write_text("# the owner's real identity\n", encoding="utf-8")
    before = W.sha(site / "DESIGN.md")
    res = W.ensure_design_md(site, W.DESIGN_TEMPLATE.format(expr="none", budget="none"))
    check("case 8: existing DESIGN.md preserved byte-for-byte",
          res["action"] == "PRESERVED" and W.sha(site / "DESIGN.md") == before)
    W.naive_ensure_design_md(site, "# clobbered\n")
    check("case 8 pole: the naive writer destroys it (instrument could say no)", W.sha(site / "DESIGN.md") != before)
    fresh = t / "ds2"
    fresh.mkdir()
    check("case 8 control: absent DESIGN.md is CREATED",
          W.ensure_design_md(fresh, "x")["action"] == "CREATED")
    build_over = W.build_site(t / "ds", variant="good")
    check("case 8: build_site over an existing identity preserves it",
          build_over["design_md"]["action"] == "PRESERVED")

    # ---- 9: too-close brand reference --------------------------------------------------------
    close = W.brand_verdict("seed-close", "apple with a bite taken out of it, silver, minimal")
    check("case 9: description near a known mark REFUSED", close["decision"] == "REFUSED" and close["nearest"] == "Apple", str(close))
    clean = W.brand_verdict("seed-clean", "teal hexagon cells interlocking in a honeycomb lattice with a small dot")
    check("case 9 control: a distinct description ACCEPTED", clean["decision"] == "ACCEPTED", str(clean))

    # ---- 10: tool success without artifact ---------------------------------------------------
    art = t / "out.txt"
    lie = W.run_tool([sys.executable, "-c", "pass"], art)
    check("case 10: exit 0 with no artifact is TOOL_LIED_NO_ARTIFACT", lie["verdict"] == "TOOL_LIED_NO_ARTIFACT", str(lie))
    check("case 10 pole: the naive verifier believes the lie", W.naive_verify(lie) == "OK")
    empty = W.run_tool([sys.executable, "-c", f"open({str(art)!r},'w').close()"], art)
    check("case 10: exit 0 with an EMPTY artifact is a lie", empty["verdict"] == "TOOL_LIED_NO_ARTIFACT", str(empty))
    badpng = W.run_tool([sys.executable, "-c", f"open({str(art)!r},'w').write('not a png'*400)"], art, valid=W.png_ok)
    check("case 10: exit 0 with a malformed artifact is a lie", badpng["verdict"] == "TOOL_LIED_BAD_ARTIFACT", str(badpng))
    okr = W.run_tool([sys.executable, "-c", f"open({str(art)!r},'w').write('hello')"], art)
    check("case 10 control: exit 0 plus real artifact is OK", okr["verdict"] == "OK", str(okr))
    failed = W.run_tool([sys.executable, "-c", "raise SystemExit(3)"], art)
    check("case 10: a non-zero exit is TOOL_FAILED", failed["verdict"] == "TOOL_FAILED")

    # ---- 11: green test over broken behaviour ------------------------------------------------
    W.build_site(t / "broken", variant="broken_handler")
    bv = W.behaviour_verdict(t / "broken" / "index.html")
    check("case 11: structural test is GREEN over a broken handler", bv["structural_green"] is True)
    check("case 11: the browser behaviour check catches it (GREEN_OVER_BROKEN)", bv["verdict"] == "GREEN_OVER_BROKEN", str(bv))
    gv = W.behaviour_verdict(t / "good" / "index.html")
    check("case 11 control: the good page behaves (OK)", gv["verdict"] == "OK", str(gv))
    brk = W.slice_run(t / "brk", variant="broken_handler", shot=True)
    check("case 11: Production Reality refuses the broken surface", brk["reality"]["verdict"] == "NOT_REAL", str(brk["reality"]))

    # ---- 12: undiscoverable feature ---------------------------------------------------------
    dx = t / "disc"
    wr(dx, "CLAUDE.md", "# project\nUse webslice for the web vertical slice.\n")
    wr(dx, "README.md", "readme\n")
    check("case 12: a feature absent from the entry docs is flagged undiscoverable",
          W.discoverability(dx, ["webslice", "hidden-feature-x"])["discoverable"] is False
          and W.discoverability(dx, ["webslice", "hidden-feature-x"])["missing"] == ["hidden-feature-x"])
    check("case 12 control: a documented feature is discoverable", W.discoverability(dx, ["webslice"])["discoverable"] is True)

    # ---- execution evidence is recorded honestly --------------------------------------------
    ev_root = t / "evroot"
    ev_root.mkdir()
    a = W.record_execution(ev_root, "OBL-x", [sys.executable, "-c", "pass"])
    b = W.record_execution(ev_root, "OBL-y", [sys.executable, "-c", "raise SystemExit(2)"])
    check("record_execution: exit 0 recorded as 0, failure recorded as non-zero (not papered over)",
          a["exit"] == 0 and b["exit"] == 2)

# ---- informational real-tree measurements (NOT asserted: Phase 5 flips discoverability) -----
sr = W.skill_reachability(ROOT)
print(f"INFO skill reachability (real tree): installed={sr['installed']} unreachable={len(sr['unreachable'])}")
toks = ["webslice", "test_asc_webslice", "backlog_autopilot", "reconciliation_ledger"]
dr = W.discoverability(ROOT, toks)
print(f"INFO discoverability (real tree, entry docs {dr['read']}): discoverable={dr['discoverable']} missing={dr['missing']}")

print(f"\n{'V-ASC-WEB PASS' if not FAILS else 'V-ASC-WEB FAIL: ' + ', '.join(FAILS)}")
sys.exit(1 if FAILS else 0)
