#!/usr/bin/env python3
"""Done-gate for the CDIO-06 anti-slop design gate (V-DESIGN-*).

The gate must be OBSERVED REFUSING. A gate that has never been seen emitting FAIL is
a preference, not a gate (feedback_zero_cannot_fall). So the suite proves BOTH poles
are reachable: slop BLOCKs, and a real, characterful design system APPROVEs.

It also pins the load-bearing nuance: a default-tier font is NOT slop when the
declared family sanctions it (F1/F4/F6). If that case failed, this would be a blanket
font ban, which is a different -- and wrong -- product.

Run:  python tools/test_design_gate.py
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.cdio.scorer import (  # noqa: E402
    check_family_declared,
    check_font_stack,
    check_palette_cliche,
)
from tools.design_gate import design_gate, parse_design_md  # noqa: E402

PASSES = 0
FAILS = 0


def _ok(gate: str, evidence: str) -> None:
    global PASSES
    PASSES += 1
    print(f"  [PASS] {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global FAILS
    FAILS += 1
    print(f"  [FAIL] {gate}: {diagnostic}")


def _write(tmpdir: str, name: str, body: str) -> str:
    path = os.path.join(tmpdir, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    return path


SLOP = """---
name: SlopProject
colors:
  accent: "#8b5cf6"
  neutral: "#ffffff"
typography:
  h1:
    fontFamily: Roboto
  body-md:
    fontFamily: Inter
---
A surface with no declared family, an inherited font stack, and a purple accent
on a white ground.
"""

SANCTIONED = """---
name: SanctionedProject
aesthetic_family: F1
colors:
  accent: "#5e6ad2"
  neutral: "#ffffff"
typography:
  body-md:
    fontFamily: Inter
---
Editorial Minimalism. Inter is the deliberate choice here, not the default.
"""

REPO_TEMPLATE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "modules", "design-md", "DESIGN.md.template",
)


def main() -> int:
    print("V-DESIGN gates (CDIO-06 anti-slop)")

    with tempfile.TemporaryDirectory() as tmp:
        # --- V-DESIGN-SLOP-BLOCKS: the gate must be observed REFUSING ----------
        slop_path = _write(tmp, "SLOP.md", SLOP)
        out = design_gate(slop_path)
        crit = {f["criterion"] for f in out.get("critical", [])}
        if out["verdict"] == "BLOCK" and "aesthetic-family-declared" in crit \
                and "font-stack-intent" in crit and "palette-cliche" in crit:
            _ok("V-DESIGN-SLOP-BLOCKS",
                f"verdict=BLOCK score={out['score']} criticals={sorted(crit)}")
        else:
            _fail("V-DESIGN-SLOP-BLOCKS",
                  f"expected BLOCK with 3 criticals, got {out['verdict']} "
                  f"score={out['score']} criticals={sorted(crit)}")

        # --- V-DESIGN-SANCTIONED-FONT-PASSES: the nuance, not a blanket ban ----
        sanc_path = _write(tmp, "SANCTIONED.md", SANCTIONED)
        out = design_gate(sanc_path)
        font = next((f for f in out.get("passed", [])
                     if f["criterion"] == "font-stack-intent"), None)
        if out["verdict"] == "APPROVE" and font:
            _ok("V-DESIGN-SANCTIONED-FONT-PASSES",
                f"F1 + Inter -> APPROVE ({font['observed']})")
        else:
            _fail("V-DESIGN-SANCTIONED-FONT-PASSES",
                  f"F1 + Inter should APPROVE (family sanctions the default); "
                  f"got {out['verdict']} score={out['score']}")

        # --- V-DESIGN-FONT-STACK-SPLIT: a comma must not defeat the font check --
        # A CSS font-family is a FALLBACK LIST. The parser split only on '#', so the
        # whole stack arrived as one name; no name containing a comma is in
        # DEFAULT_TIER_FONTS, so `Inter, sans-serif` was classified "characterful"
        # and PASSED. The check could then only ever fail a document declaring one
        # bare default family -- the shape almost nobody writes. Measured 2026-09-13.
        #
        # The control is what makes this evidence rather than a stricter assertion:
        # a stack whose FIRST face is real must still pass, or the repair would just
        # be a blanket ban on writing fallbacks.
        stack_slop = _write(tmp, "STACKSLOP.md", """---
name: StackSlop
aesthetic_family: F2
colors:
  accent: "#c2410c"
  neutral: "#f5f0e8"
typography:
  body-md:
    fontFamily: Inter, sans-serif
---
F2 does not sanction a default stack; every face here is default-tier.
""")
        stack_ok = _write(tmp, "STACKOK.md", """---
name: StackOk
aesthetic_family: F2
colors:
  accent: "#c2410c"
  neutral: "#f5f0e8"
typography:
  body-md:
    fontFamily: Lora, Georgia, serif
---
A real typeface with defaults behind it as fallbacks.
""")
        slop_fonts = parse_design_md(stack_slop)["fonts"]
        out_slop = design_gate(stack_slop)
        out_ok = design_gate(stack_ok)
        slop_crit = [f["criterion"] for f in out_slop.get("critical", [])]
        ok_font = next((f for f in out_ok.get("passed", [])
                        if f["criterion"] == "font-stack-intent"), None)
        if (slop_fonts == ["Inter", "sans-serif"]
                and "font-stack-intent" in slop_crit and ok_font):
            _ok("V-DESIGN-FONT-STACK-SPLIT",
                f"'Inter, sans-serif' -> {slop_fonts} -> critical; "
                f"control 'Lora, Georgia, serif' -> pass ({ok_font['observed']})")
        else:
            _fail("V-DESIGN-FONT-STACK-SPLIT",
                  f"stack must split on ',' and fail as all-default; parsed="
                  f"{slop_fonts} criticals={slop_crit} control_pass={bool(ok_font)}")

        # --- V-DESIGN-FAIL-OPEN: a gate that cannot read must never block ------
        missing = os.path.join(tmp, "no-such-dir", "DESIGN.md")
        out = design_gate(missing)
        if out["verdict"] == "BLOCK" and out["score"] == 75:
            _ok("V-DESIGN-NO-DESIGN-MD-BLOCKS",
                "absent DESIGN.md is a real finding (critical), not a gate error")
        else:
            _fail("V-DESIGN-NO-DESIGN-MD-BLOCKS",
                  f"expected BLOCK on absent DESIGN.md, got {out['verdict']}")

        # A path that exists but is unreadable as text -> SKIP, exit-0, never BLOCK.
        binpath = os.path.join(tmp, "BINARY.md")
        with open(binpath, "wb") as fh:
            fh.write(b"\xff\xfe\x00\x00\x80\x81\x82")
        out = design_gate(binpath)
        # Two separate claims, and they used to be one. The ACTION must fail open --
        # SKIP, never BLOCK, so a gate that cannot read never stops real work. The
        # ASSESSMENT must stay honest -- `is_done` False and `assessment` explicitly
        # "unevaluated", because an unreadable artifact is the one thing we know
        # nothing about. Asserting `is_done is True` here (as this did until
        # 2026-09-13) made an unevaluable gate indistinguishable from a surface that
        # passed every check, which is the sealed rule at ukdl-universal.md:7035.
        if (out["verdict"] == "SKIP" and out["verdict"] != "BLOCK"
                and out.get("is_done") is False
                and out.get("assessment") == "unevaluated"):
            _ok("V-DESIGN-FAIL-OPEN",
                f"unreadable artifact -> SKIP, assessment=unevaluated, is_done=False "
                f"({out['reason'][:40]}...)")
        else:
            _fail("V-DESIGN-FAIL-OPEN",
                  f"action must fail open AND the assessment stay honest; got "
                  f"verdict={out['verdict']} is_done={out.get('is_done')} "
                  f"assessment={out.get('assessment')!r}")

        # --- V-DESIGN-HARD-FILTERS-REACHED: the automatic path runs review_gate --
        # Until 2026-09-13 `review_gate` had ZERO production callers: this entrypoint
        # called `score_review` directly, so the CDICF dependency filter and the
        # CDIO-07 conformance filter were reachable only by an agent choosing to run
        # a command written in prose -- while DESIGN_GOVERNANCE.md sec.8.2 asserted as
        # a normative rule that the dependency check runs "again at review time".
        #
        # The suite was 44/44 green throughout, because every test called review_gate
        # DIRECTLY. Coverage sat beside the capability instead of downstream of
        # production, so deleting the wiring could not turn anything red. This gate is
        # the one that can.
        proj = os.path.join(tmp, "proj")
        os.makedirs(os.path.join(proj, ".cdicf"), exist_ok=True)
        _write(proj, "package.json", '{"dependencies": {}}')
        with open(os.path.join(proj, ".cdicf", "installed.json"), "w",
                  encoding="utf-8") as fh:
            fh.write('{"components": {"card": {"dependencies": '
                     '{"npm": ["clsx"], "registry": []}}}}')
        _write(proj, "DESIGN.md", SANCTIONED)
        out = design_gate(os.path.join(proj, "DESIGN.md"))

        dep = next((f for f in out.get("hard_filters", [])
                    if f["criterion"] == "component-dependency-scope"), None)
        exp = next((f for f in out.get("hard_filters", [])
                    if f["criterion"] == "experience-contract"), None)
        # Report-only: the filter is SEEN (unresolved, not passed) and withholds
        # is_done, but must NOT decide the verdict -- widening what the gate sees and
        # widening what it may refuse are separate decisions.
        if (dep is not None and dep["state"] == "unresolved"
                and dep["passed"] is False
                and out["is_done"] is False
                and out["verdict"] != "BLOCK"
                and "clsx" in out["reason"]):
            _ok("V-DESIGN-HARD-FILTERS-REACHED",
                f"automatic path reached the dependency filter: state={dep['state']}, "
                f"verdict stays {out['verdict']} (report-only), is_done withheld, "
                f"experience={exp['state'] if exp else 'n/a'}")
        else:
            _fail("V-DESIGN-HARD-FILTERS-REACHED",
                  f"review_gate not reached from the automatic path, or it refused "
                  f"when it should only report: filters={out.get('hard_filters')} "
                  f"verdict={out.get('verdict')} is_done={out.get('is_done')}")

        # Control: the same project with the dependency declared must come back
        # resolved and DONE. Without this, a filter that flagged everything would
        # satisfy the assertion above and look like a working detector.
        _write(proj, "package.json", '{"dependencies": {"clsx": "^2.0.0"}}')
        out_ok = design_gate(os.path.join(proj, "DESIGN.md"))
        dep_ok = next((f for f in out_ok.get("hard_filters", [])
                       if f["criterion"] == "component-dependency-scope"), None)
        if dep_ok is not None and dep_ok["passed"] is True \
                and out_ok["is_done"] is True and out_ok["verdict"] == "APPROVE":
            _ok("V-DESIGN-HARD-FILTERS-NEGATIVE-CONTROL",
                f"declaring the dependency resolves the filter and restores done "
                f"(verdict={out_ok['verdict']}, state={dep_ok['state']})")
        else:
            _fail("V-DESIGN-HARD-FILTERS-NEGATIVE-CONTROL",
                  f"a resolved project must still reach APPROVE/done; got "
                  f"verdict={out_ok.get('verdict')} is_done={out_ok.get('is_done')} "
                  f"filter={dep_ok}")

        # --- V-DESIGN-FILTER-CRASH-KEEPS-REFUSAL: isolation, not collapse ---------
        # Wiring the hard filters in was a REGRESSION until this was added. The filters
        # read the filesystem; score_review does not. So a malformed artifact belonging
        # to some OTHER concern could raise inside design_gate, and main()'s bare except
        # degrades any exception to SKIP/exit 0/ALLOW -- turning a slop document that
        # scored 25 and BLOCKed into an allowed write. A refusal that already worked,
        # traded for someone else's broken JSON.
        #
        # Found by an adversarial review of this session's own diff, after 48/48 suite
        # gates and a 4/4 red-branch drill had all passed. Mutation testing proves a
        # suite notices the repairs it was written for; it says nothing about what the
        # repairs broke.
        crash = os.path.join(tmp, "crash")
        os.makedirs(os.path.join(crash, ".cdicf"), exist_ok=True)
        _write(crash, "DESIGN.md", SLOP)
        with open(os.path.join(crash, ".cdicf", "installed.json"), "w",
                  encoding="utf-8") as fh:
            # Well-formed JSON, wrong shape: "components" as a list, not a mapping.
            fh.write('{"components": ["card", "button"]}')
        out_crash = design_gate(os.path.join(crash, "DESIGN.md"))
        hf = (out_crash.get("hard_filters") or [{}])[0]
        if (out_crash["verdict"] == "BLOCK"
                and out_crash["is_done"] is False
                and hf.get("state") == "unevaluated"
                and "UNEVALUATED" in out_crash["reason"]):
            _ok("V-DESIGN-FILTER-CRASH-KEEPS-REFUSAL",
                f"a filter raising on a malformed install record leaves the verdict at "
                f"{out_crash['verdict']} (score {out_crash['score']}), reports the "
                f"filter as {hf.get('state')}, and withholds done")
        else:
            _fail("V-DESIGN-FILTER-CRASH-KEEPS-REFUSAL",
                  f"a crashing filter must not cost the refusal; got "
                  f"verdict={out_crash.get('verdict')} is_done={out_crash.get('is_done')} "
                  f"filter_state={hf.get('state')}")

    # --- V-DESIGN-TEMPLATE-CLEAN: the PP's own canonical template must PASS ----
    out = design_gate(REPO_TEMPLATE)
    if out["verdict"] == "APPROVE":
        _ok("V-DESIGN-TEMPLATE-CLEAN",
            f"DESIGN.md.template APPROVE score={out['score']} "
            f"family={out['parsed']['family']} fonts={out['parsed']['fonts']}")
    else:
        _fail("V-DESIGN-TEMPLATE-CLEAN",
              f"the PP's own canonical template must clear its own gate; got "
              f"{out['verdict']} score={out['score']} "
              f"criticals={[f['criterion'] for f in out.get('critical', [])]}")

    # --- V-DESIGN-UNIT: the checks in isolation -------------------------------
    if check_family_declared("").status == "fail" \
            and check_family_declared("F3").status == "pass" \
            and check_family_declared("F99").status == "fail":
        _ok("V-DESIGN-UNIT-FAMILY", "absent + unknown fail; F3 passes")
    else:
        _fail("V-DESIGN-UNIT-FAMILY", "family check does not discriminate")

    if check_font_stack(["Inter"], "F3").status == "fail" \
            and check_font_stack(["Inter"], "F1").status == "pass" \
            and check_font_stack(["Lora", "Inter"], "F3").status == "pass":
        _ok("V-DESIGN-UNIT-FONT",
            "default-only fails unsanctioned family; passes F1; passes when paired")
    else:
        _fail("V-DESIGN-UNIT-FONT", "font check does not discriminate")

    # Cream (#f4f3ee) has a relative luminance of ~0.90 -- it IS a near-white ground,
    # so a purple accent on cream is the same cliché as purple on white and must also
    # fail. The discriminator is the HUE, not the warmth of the ground: terracotta on
    # cream passes, purple on cream does not. A mid-tone ground (#5a5a5a) is neither
    # near-white nor near-black, so the clichéd-gradient rule does not reach it.
    if check_palette_cliche(["#8b5cf6"], background="#ffffff").status == "fail" \
            and check_palette_cliche(["#8b5cf6"], background="#f4f3ee").status == "fail" \
            and check_palette_cliche(["#8b5cf6"], background="#5a5a5a").status == "pass" \
            and check_palette_cliche(["#16d5e6"]).status == "fail" \
            and check_palette_cliche(["#c96442"], background="#f4f3ee").status == "pass":
        _ok("V-DESIGN-UNIT-PALETTE",
            "purple fails on white AND on cream (both near-white); passes on a mid-tone "
            "ground; teal fingerprint fails; terracotta on cream passes")
    else:
        _fail("V-DESIGN-UNIT-PALETTE", "palette check does not discriminate")

    total = PASSES + FAILS
    print(f"\nDESIGN_PASS={PASSES}/{total}  threshold={total}/{total}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
