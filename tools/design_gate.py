#!/usr/bin/env python3
"""design_gate.py -- the anti-slop done-gate for any PP output with a visual surface.

This is an ENTRYPOINT, not an engine. Every verdict it emits is computed by
`modules.cdio.scorer` -- the same deterministic scorer the cdio-reviewer agent uses
and the same sealed verdict contract (PR-CDIO-REVIEW-GATE-001: APPROVE requires
score >= 80 AND zero critical). There is exactly one definition of "acceptable
design" in the Power Pack, and it does not live in this file.

What it adds on top of the scorer: it reads a project's DESIGN.md, extracts the
declared family, the font stack, and the palette, and feeds them to the CDIO-06
anti-slop checks. Before this, the Anti-Slop Kit could not FAIL anything.

It also reads the CDIO-07 `experience:` contract, when one is declared, and does two
things with it that nothing else in the repo could do before:

  1. Refuses an INCOHERENT contract at declaration time -- a contract that cannot be
     conformed to without breaching a floor should never have a surface built against
     it. This needs no rendered pixel; it is a property of the declaration itself.
  2. EMITS the CDICF selector's project context from it (--emit-context). The
     DESIGN.md template states its provenance decisions "are the context object the
     CDICF selector consumes", but the selector reads a hand-authored --context file
     and no producer joined the two. A declared budget that no filter ever reads is
     the write-without-read defect; this is the missing reader's producer.

An ABSENT experience block is `unassessed` -- reported, never failed, and it appends
no verdict at all, so every project that predates the contract scores byte-identically.

FAIL-OPEN, ABSOLUTELY (design constraint): a gate that cannot read its artifact
returns SKIP and exit 0. A broken gate must never block real work -- it must only
ever be the reason a genuinely-slop surface is stopped, never the reason a good one
is. Every unreadable / missing / unparseable input is a SKIP with a stated reason,
never a BLOCK.

Usage:
    python tools/design_gate.py <path/to/DESIGN.md>
    python tools/design_gate.py <path/to/DESIGN.md> --json
    python tools/design_gate.py <path/to/DESIGN.md> --emit-context > ctx.json

Exit codes:
    0  APPROVE (score >= 80, zero critical) or SKIP (gate could not evaluate)
    1  REVISE  (majors to resolve)
    2  BLOCK   (a critical -- slop detected, or no family declared)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.cdio.scorer import (  # noqa: E402
    Verdict,
    check_design_md_exists,
    check_family_declared,
    check_font_stack,
    check_palette_cliche,
    score_review,
)

HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}")
FONT_RE = re.compile(r"^\s*fontFamily:\s*(.+?)\s*$", re.MULTILINE)
FAMILY_RE = re.compile(r"^\s*aesthetic_family:\s*([A-Za-z0-9]+)", re.MULTILINE)
# The page ground: the token a surface actually sits on. `neutral` is the DESIGN.md
# convention for it; `background` and `bg` are accepted as common aliases.
GROUND_RE = re.compile(r"^\s*(?:neutral|background|bg):\s*\"?(#[0-9a-fA-F]{3,8})\"?",
                       re.MULTILINE)

# --- CDIO-07 experience contract -------------------------------------------- #
# The block is an indented mapping under `experience:`. Parsed with the same
# deliberate tolerance as everything else here: the point is to extract declared
# values, not to validate YAML. A malformed block yields fewer fields, and a field
# that did not parse is reported as undeclared rather than assumed.
EXPERIENCE_BLOCK_RE = re.compile(
    r"^experience:[ \t]*\r?\n((?:[ \t]+\S.*\r?\n?|[ \t]*\r?\n)*)", re.MULTILINE)
EXPERIENCE_FIELD_RE = re.compile(r"^[ \t]+([a-z_]+):[ \t]*(.+?)[ \t]*$", re.MULTILINE)

# Ordered ceilings. `motion_budget` may never outrank `expressiveness`: a budget
# above the declared ceiling is a ceiling that does not cap anything.
EXPRESSIVENESS_RANK = {"none": 0, "restrained": 1, "moderate": 2, "high": 3}
MOTION_RANK = {"none": 0, "low": 1, "medium": 2, "high": 3}

EXPERIENCE_ENUMS = {
    "expressiveness": set(EXPRESSIVENESS_RANK),
    "motion_budget": set(MOTION_RANK),
    "reduced_motion": {"equivalent", "absent"},
    "waiting": {"skeleton", "spinner", "progress", "optimistic", "none"},
    "progress_language": {"numeric", "staged", "indeterminate", "none"},
    "success_posture": {"silent", "confirm", "acknowledge", "celebrate"},
    "error_posture": {"terse", "explain", "explain_and_recover"},
    "celebration_policy": {"never", "milestones_only", "first_success", "unrestricted"},
    "character_policy": {"none", "voice_only", "illustrated", "persistent_character"},
    "trust_posture": {"standard", "elevated", "critical"},
}
EXPERIENCE_INTS = ("feedback_latency_ms", "progress_threshold_ms")

# A surface at or above this expressiveness cannot honour an `absent` reduced-motion
# declaration without breaching the accessibility floor (CDIO-07 sec.5).
REDUCED_MOTION_REQUIRED_AT = EXPRESSIVENESS_RANK["moderate"]

# WCAG AA is the CDIO-00 sec.4 floor for every surface in the Power Pack, so a
# document that does not restate it has not left the field unknown. Emitted with its
# derivation named, because a defaulted value that looks declared is how an
# assumption becomes a fact nobody checked.
WCAG_FLOOR = "AA"

# Context fields the selector reads that a DESIGN.md may declare directly at the top
# level of its front-matter. Undeclared ones are OMITTED, never guessed: the selector
# treats a missing field as "unconstrained", and emitting an invented value would
# turn a filter that never runs into a filter that runs on fiction.
CONTEXT_SCALARS = {
    "required_wcag": re.compile(r"^required_wcag:[ \t]*\"?([A-Za-z]+)\"?", re.MULTILINE),
    "bundle_budget_kb": re.compile(r"^bundle_budget_kb:[ \t]*(\d+)", re.MULTILINE),
}
UX_FINDINGS_RE = re.compile(
    r"^unresolved_ux_findings:[ \t]*\r?\n((?:[ \t]+-[ \t]*.+\r?\n?)*)", re.MULTILINE)
UX_FINDING_ITEM_RE = re.compile(r"^[ \t]+-[ \t]*(.+?)[ \t]*$", re.MULTILINE)


class SkipGate(Exception):
    """Raised when the gate cannot evaluate. Always fail-open -> SKIP, exit 0."""


def _front_matter(text: str) -> str:
    """Return the YAML front-matter block, or the whole text if there is no fence.

    Deliberately tolerant: the point is to extract tokens, not to validate YAML. A
    malformed fence yields the whole document, and the regexes simply find less.
    """
    if text.lstrip().startswith("---"):
        parts = text.lstrip().split("---", 2)
        if len(parts) >= 3:
            return parts[1]
    return text


def parse_experience(fm: str):
    """Extract the CDIO-07 `experience:` contract from front-matter.

    Returns None when no block is declared -- which is the `unassessed` state, not an
    empty contract. The two are different: a project that declared nothing has made
    no promise to break, and collapsing it into an empty contract would manufacture
    violations out of silence.
    """
    block = EXPERIENCE_BLOCK_RE.search(fm)
    if not block:
        return None
    exp = {}
    for key, raw in EXPERIENCE_FIELD_RE.findall(block.group(1)):
        value = raw.split("#", 1)[0].strip().strip("\"'")
        if not value:
            continue
        if key in EXPERIENCE_INTS:
            try:
                exp[key] = int(value)
            except ValueError:
                exp[key] = value          # kept verbatim; flagged by the coherence check
        else:
            exp[key] = value
    return exp


def check_experience_coherence(exp, *, criterion: str = "experience-contract-coherent"):
    """Refuse a declared contract that contradicts itself or a CDIO-00 floor.

    Returns None when no contract is declared, so an unassessed project appends no
    verdict and its score is byte-identical to what it was before this axis existed.

    This is a DECLARATION-time check. It sees what a project committed to and nothing
    about what it rendered (CDIO-07 sec.8); the rendered surface stays the property of
    the render-verified path (VQ-8). Refusing an unconformable contract before a
    surface is built against it is the cheapest possible moment to refuse it.
    """
    if exp is None:
        return None

    unknown, problems, floor_breach = [], [], False

    for key, allowed in EXPERIENCE_ENUMS.items():
        val = exp.get(key)
        if val is not None and val not in allowed:
            unknown.append(f"{key}={val!r}")
    for key in EXPERIENCE_INTS:
        val = exp.get(key)
        if val is not None and not isinstance(val, int):
            unknown.append(f"{key}={val!r}")

    expr = exp.get("expressiveness")
    motion = exp.get("motion_budget")
    reduced = exp.get("reduced_motion")
    expr_rank = EXPRESSIVENESS_RANK.get(expr)
    motion_rank = MOTION_RANK.get(motion)

    if expr_rank is not None and expr_rank >= REDUCED_MOTION_REQUIRED_AT \
            and reduced == "absent":
        floor_breach = True
        problems.append(
            f"expressiveness={expr} with reduced_motion=absent -- the contract cannot "
            "be honoured without breaching the accessibility floor")

    if expr_rank is not None and motion_rank is not None and motion_rank > expr_rank:
        problems.append(
            f"motion_budget={motion} outranks expressiveness={expr} -- a ceiling above "
            "the declared ceiling caps nothing")

    if exp.get("trust_posture") == "critical" \
            and exp.get("celebration_policy") not in (None, "never"):
        problems.append(
            f"trust_posture=critical with celebration_policy="
            f"{exp.get('celebration_policy')} -- a celebration on a surface where "
            "mistakes are costly asserts a confidence the surface exists to withhold")

    if exp.get("success_posture") == "celebrate" \
            and exp.get("celebration_policy") == "never":
        problems.append(
            "success_posture=celebrate with celebration_policy=never -- the contract "
            "contradicts itself")

    if exp.get("waiting") == "optimistic" and exp.get("error_posture") == "terse":
        problems.append(
            "waiting=optimistic with error_posture=terse -- an optimistic update whose "
            "failure is terse leaves the user holding a belief the system has abandoned")

    fb = exp.get("feedback_latency_ms")
    pt = exp.get("progress_threshold_ms")
    if isinstance(fb, int) and isinstance(pt, int) and fb > pt:
        problems.append(
            f"feedback_latency_ms={fb} exceeds progress_threshold_ms={pt} -- an "
            "acknowledgement that arrives after the progress cue inverts the sequence")

    if unknown:
        problems.append(
            "unrecognised value(s): " + ", ".join(sorted(unknown))
            + " -- a value outside the vocabulary silently disables the check that "
              "reads it, and a check nobody can fail is not a check")

    if not problems:
        return Verdict(
            criterion=criterion, dimension="experience", status="pass",
            observed=f"{len(exp)} field(s) declared, internally coherent "
                     f"(expressiveness={expr}, motion_budget={motion}, "
                     f"reduced_motion={reduced})")

    return Verdict(
        criterion=criterion, dimension="experience", status="fail",
        severity="critical" if floor_breach else "major",
        observed="; ".join(problems),
        recommendation="re-run the CDIO-07 sec.2 picker "
                       "(modules/design-md/prompts/experience-picker.md); a contract "
                       "that cannot be conformed to is not a contract a surface "
                       "should be built against")


def parse_design_md(path: str) -> dict:
    """Extract (family, fonts, colors, ground, experience, context) from a DESIGN.md.
    Raises SkipGate if the file cannot be read -- never a hard failure."""
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:   # -sig: strip a BOM
            text = fh.read()
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        # UnicodeDecodeError is NOT an OSError. Catching only OSError here let a
        # binary / mis-encoded artifact crash the gate instead of failing open --
        # a broken gate would then have blocked good work, which is the one thing
        # this gate must never do. Caught by V-DESIGN-FAIL-OPEN.
        raise SkipGate(f"cannot decode {path}: {exc}") from exc

    fm = _front_matter(text)

    family = ""
    m = FAMILY_RE.search(fm)
    if m:
        family = m.group(1).strip()

    fonts = []
    for raw in FONT_RE.findall(fm):
        # Strip inline comments and quotes: `Lora   # body serif` -> `Lora`
        name = raw.split("#", 1)[0].strip().strip("\"'")
        if name:
            fonts.append(name)

    colors = sorted(set(HEX_RE.findall(fm)))

    ground = None
    g = GROUND_RE.search(fm)
    if g:
        ground = g.group(1)

    declared = {}
    for key, rx in CONTEXT_SCALARS.items():
        hit = rx.search(fm)
        if hit:
            declared[key] = int(hit.group(1)) if key.endswith("_kb") else hit.group(1)
    findings = UX_FINDINGS_RE.search(fm)
    if findings:
        items = [i.strip().strip("\"'")
                 for i in UX_FINDING_ITEM_RE.findall(findings.group(1))]
        declared["unresolved_ux_findings"] = [i for i in items if i]

    return {"family": family, "fonts": fonts, "colors": colors, "ground": ground,
            "experience": parse_experience(fm), "declared_context": declared}


def emit_context(design_md_path: str) -> dict:
    """Derive the CDICF selector's project context from a DESIGN.md.

    The DESIGN.md template states its provenance decisions ARE the context object the
    selector consumes; `selector.js` reads a `--context <file.json>` nobody produced.
    This closes that gap in the only honest direction: every emitted field is traced
    to where it came from in `_derivation`, and a field the document does not declare
    is OMITTED rather than invented. The selector treats a missing field as
    unconstrained, so omission costs a filter; a guess costs correctness, and a filter
    running on fiction is worse than a filter not running.
    """
    parsed = parse_design_md(design_md_path)
    exp = parsed["experience"]
    declared = parsed["declared_context"]

    ctx, derivation = {}, {}

    if exp and exp.get("motion_budget"):
        ctx["motion_budget"] = exp["motion_budget"]
        derivation["motion_budget"] = "declared: experience.motion_budget"

    if "required_wcag" in declared:
        ctx["required_wcag"] = declared["required_wcag"]
        derivation["required_wcag"] = "declared: required_wcag"
    else:
        ctx["required_wcag"] = WCAG_FLOOR
        derivation["required_wcag"] = (
            f"defaulted to the CDIO-00 sec.4 floor ({WCAG_FLOOR}); not declared in "
            "this document")

    if "bundle_budget_kb" in declared:
        ctx["bundle_budget_kb"] = declared["bundle_budget_kb"]
        derivation["bundle_budget_kb"] = "declared: bundle_budget_kb"

    if "unresolved_ux_findings" in declared:
        ctx["unresolved_ux_findings"] = declared["unresolved_ux_findings"]
        derivation["unresolved_ux_findings"] = "declared: unresolved_ux_findings"

    omitted = sorted({"motion_budget", "bundle_budget_kb", "unresolved_ux_findings"}
                     - set(ctx))
    ctx["_derivation"] = {
        "source": design_md_path,
        "fields": derivation,
        "omitted": omitted,
        "note": "omitted fields are undeclared, not unconstrained-by-choice; the "
                "selector will not filter on them",
    }
    return ctx


def design_gate(design_md_path: str) -> dict:
    """Run the CDIO-06 anti-slop checks against a DESIGN.md.

    Returns a dict with `verdict` in {APPROVE, REVISE, BLOCK, SKIP}. SKIP means the
    gate could not evaluate and is standing down -- it is never a failure verdict.
    """
    presence = check_design_md_exists(design_md_path)
    if presence.status == "fail":
        # No DESIGN.md at all is a REAL finding, not a gate malfunction: a visual
        # surface with no tokens is unreviewable by construction. It BLOCKs.
        result = score_review([presence])
        out = result.to_json()
        out["design_md"] = design_md_path
        return out

    try:
        parsed = parse_design_md(design_md_path)
    except SkipGate as exc:
        return {"verdict": "SKIP", "score": None, "reason": str(exc),
                "design_md": design_md_path, "is_done": True}

    verdicts = [
        presence,
        check_family_declared(parsed["family"]),
        check_font_stack(parsed["fonts"], parsed["family"]),
        check_palette_cliche(parsed["colors"], background=parsed["ground"]),
    ]

    # Appended ONLY when a contract is declared. An unassessed project therefore
    # scores exactly what it scored before this axis existed -- the equality that
    # makes adding the axis a gate and not a silent re-score of everyone's history.
    coherence = check_experience_coherence(parsed["experience"])
    if coherence is not None:
        verdicts.append(coherence)

    result = score_review(verdicts)
    out = result.to_json()
    out["design_md"] = design_md_path
    out["parsed"] = parsed
    out["experience_state"] = "unassessed" if parsed["experience"] is None else "declared"
    return out


def _render(out: dict) -> str:
    lines = [f"design_gate: {out['verdict']}  (score={out.get('score')})",
             f"  design.md: {out.get('design_md')}",
             f"  reason:    {out.get('reason')}"]
    state = out.get("experience_state")
    if state == "unassessed":
        # Reported, never scored. Silence here would be the absence-reads-as-health
        # defect: nobody would ever learn the contract was missing.
        lines.append("  experience: unassessed -- no CDIO-07 contract declared "
                     "(not a finding; declare one to make behaviour refusable)")
    elif state == "declared":
        lines.append("  experience: declared -- CDIO-07 contract present")
    for sev in ("critical", "major", "minor"):
        for f in out.get(sev, []) or []:
            lines.append(f"  [{sev.upper():8}] {f['criterion']}: {f['observed']}")
            if f.get("recommendation"):
                lines.append(f"             -> {f['recommendation']}")
    for f in out.get("passed", []) or []:
        lines.append(f"  [PASS    ] {f['criterion']}: {f['observed']}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="CDIO-06 anti-slop design gate")
    ap.add_argument("design_md", help="path to the project's DESIGN.md")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--emit-context", action="store_true",
                    help="emit the CDICF selector project context derived from this "
                         "DESIGN.md, instead of running the gate")
    ap.add_argument("--out", metavar="FILE",
                    help="write the emitted context to FILE as UTF-8 without a BOM. "
                         "Prefer this over a shell redirect on Windows: PowerShell's "
                         "`>` and `Out-File -Encoding utf8` both prepend a BOM, and a "
                         "BOM'd context is a file the consumer cannot parse")
    args = ap.parse_args(argv)

    if args.emit_context:
        try:
            ctx = emit_context(args.design_md)
        except (SkipGate, OSError) as exc:
            payload = {"_derivation": {"source": args.design_md,
                                       "error": f"cannot read: {exc}"}}
        else:
            payload = ctx
        text = json.dumps(payload, indent=2, ensure_ascii=False)
        if args.out:
            # newline="" + no BOM: the consumer is `selector.js --context`, and the
            # producer owning its own encoding is the only way the round trip does not
            # depend on which shell the operator happened to use.
            with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text + "\n")
            print(f"context written: {args.out}")
        else:
            print(text)
        return 0                          # fail-open: never block on an unreadable file

    try:
        out = design_gate(args.design_md)
    except Exception as exc:                      # noqa: BLE001 -- fail-open is the contract
        out = {"verdict": "SKIP", "score": None, "is_done": True,
               "reason": f"gate error, standing down (fail-open): {exc}",
               "design_md": args.design_md}

    print(json.dumps(out, indent=2, ensure_ascii=False) if args.json else _render(out))

    return {"APPROVE": 0, "SKIP": 0, "REVISE": 1, "BLOCK": 2}.get(out["verdict"], 0)


if __name__ == "__main__":
    raise SystemExit(main())
