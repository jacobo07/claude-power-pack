#!/usr/bin/env python3
"""V-HOOK gates -- the process boundary CDIO enforcement actually crosses.

Every existing CDIO gate calls `design_gate()` in-process. That proves the gate
computes the right verdict; it proves NOTHING about the thing the product does,
which is: the harness spawns `node cdio_visual_advisory.js`, that spawns
`python design_gate.py --json`, and the FIRST process turns the SECOND process's
stdout into a `permissionDecision`. Three processes, two serialisation hops, and
until this file nothing had ever run them together.

The in-process suites cannot see any of: argv construction, the interpreter the
hook resolves, the working directory, JSON round-tripping, a BOM on either hop,
stdout/stderr separation, the exit-code convention (the hook ALWAYS exits 0 and
carries its refusal in the payload), or the `.git`-bounded upward walk that finds
the DESIGN.md in the first place. A regression in any of them leaves every
existing suite green and the enforcement silently absent.

WHAT THIS FILE DOES NOT PROVE. It drives the hook as the harness drives it, but
it is not the harness: it does not prove the harness HONOURS a returned
`permissionDecision: deny`, only that the hook emits one. That last hop is the
harness's own contract. `V-HOOK-TRIGGER-REGISTERED` covers the other end -- that
something is wired to invoke this hook at all -- and between them the chain is
attributable end to end except for that single harness-internal step, which is
named here rather than quietly claimed.

The subject is the WORKING-TREE hook, which is what actually runs. At the time of
writing that file also carries uncommitted work from another session; these gates
assert only behaviour this repo's committed contract defines.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.liveness.reachability import (  # noqa: E402
    live_root,
    registration_sites,
)

PP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(PP_ROOT, "hooks", "cdio_visual_advisory.js")
STATE_DIR = os.path.join(os.path.expanduser("~"), ".claude", "state", "cdio")

_passes = 0
_fails = 0
# Unique per run so the hook's 15-minute advisory throttle can never make a gate
# depend on whether this suite ran recently. A throttled advisory returns `{}`,
# which is indistinguishable from "the hook declined to fire" -- the exact
# ambiguity that would let a broken hook read as a passing control.
_SESSION = f"vhookbnd{int(time.time() * 1000) % 100000000}"


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  [PASS] {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  [FAIL] {gate}: {diagnostic}")


def _node() -> str:
    found = shutil.which("node")
    if found:
        return found
    fallback = r"C:\Program Files\nodejs\node.exe"
    return fallback if os.path.isfile(fallback) else "node"


def _run_hook(payload: dict, env_extra: dict | None = None):
    """Drive the hook exactly as the harness does: JSON on stdin, JSON on stdout.

    Returns (parsed_dict_or_None, exit_code, raw_stdout).
    """
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(
        [_node(), HOOK],
        input=json.dumps(payload),
        capture_output=True, text=True, timeout=60,
        cwd=PP_ROOT, env=env,
    )
    try:
        parsed = json.loads(proc.stdout) if proc.stdout.strip() else None
    except json.JSONDecodeError:
        parsed = None
    return parsed, proc.returncode, proc.stdout


def _decision(parsed) -> str:
    if not isinstance(parsed, dict):
        return ""
    return str(parsed.get("hookSpecificOutput", {}).get("permissionDecision", ""))


def _write(directory: str, name: str, body: str) -> str:
    path = os.path.join(directory, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(body)
    return path


SLOP_DESIGN = """---
name: SlopProject
colors:
  accent: "#8b5cf6"
  neutral: "#ffffff"
typography:
  h1:
    fontFamily: Roboto
---
No declared family, inherited fonts, purple on white.
"""

CLEAN_DESIGN = """---
name: CleanProject
aesthetic_family: F1
colors:
  accent: "#5e6ad2"
  neutral: "#ffffff"
typography:
  body-md:
    fontFamily: Inter
---
Editorial Minimalism; Inter is deliberate here.
"""

REVISE_DESIGN = """---
name: ContradictoryProject
aesthetic_family: F3
colors:
  accent: "#2d6cdf"
  neutral: "#ffffff"
typography:
  body-md:
    fontFamily: Charter
experience:
  trust_posture: critical
  celebration_policy: milestones_only
  waiting: optimistic
  error_posture: terse
  feedback_latency_ms: 2000
  progress_threshold_ms: 500
---
Three independent contract contradictions, no floor breach.
"""


def _surface_payload(surface: str) -> dict:
    return {"tool_name": "Write",
            "tool_input": {"file_path": surface, "content": "export const X = 1;"},
            "session_id": _SESSION}


def gate_block_denies(tmp: str) -> None:
    """THE claim the previous session left open: a BLOCK becomes a real deny."""
    project = os.path.join(tmp, "blockproj")
    os.makedirs(os.path.join(project, ".git"), exist_ok=True)
    _write(project, "DESIGN.md", SLOP_DESIGN)
    surface = _write(project, "hero.tsx", "export const Hero = () => null;\n")

    parsed, code, raw = _run_hook(_surface_payload(surface))
    decision = _decision(parsed)
    reason = str(parsed.get("hookSpecificOutput", {}).get("permissionDecisionReason", "")
                 if isinstance(parsed, dict) else "")

    if decision == "deny" and code == 0 and "BLOCK" in reason:
        _ok("V-HOOK-BLOCK-DENIES",
            f"node->python->deny across the real boundary; exit {code} (the refusal "
            f"rides in the payload, never the exit code); reason names the verdict")
    else:
        _fail("V-HOOK-BLOCK-DENIES",
              f"a BLOCKing DESIGN.md must deny at the hook boundary; got "
              f"decision={decision!r} exit={code} raw={raw[:200]!r}")


def gate_approve_allows(tmp: str) -> None:
    """Negative control. Without it, a hook that denied EVERYTHING would pass the
    gate above and read as working enforcement."""
    project = os.path.join(tmp, "cleanproj")
    os.makedirs(os.path.join(project, ".git"), exist_ok=True)
    _write(project, "DESIGN.md", CLEAN_DESIGN)
    surface = _write(project, "hero.tsx", "export const Hero = () => null;\n")

    parsed, code, raw = _run_hook(_surface_payload(surface))
    decision = _decision(parsed)
    if decision != "deny" and code == 0:
        _ok("V-HOOK-APPROVE-ALLOWS",
            "a conforming design system is not denied at the boundary "
            f"(decision={decision or 'none'})")
    else:
        _fail("V-HOOK-APPROVE-ALLOWS",
              f"a clean DESIGN.md must not be denied; got decision={decision!r} "
              f"exit={code} raw={raw[:200]!r}")


def gate_revise_does_not_deny(tmp: str) -> None:
    """REVISE became reachable today. Only BLOCK may refuse a write.

    Making a verdict reachable is exactly the moment to check it did not become a
    new way to refuse: the hook branches on the verdict STRING, so a newly
    producible value lands in whichever branch happens to catch it.
    """
    project = os.path.join(tmp, "reviseproj")
    os.makedirs(os.path.join(project, ".git"), exist_ok=True)
    _write(project, "DESIGN.md", REVISE_DESIGN)
    surface = _write(project, "dashboard.tsx", "export const D = () => null;\n")

    parsed, code, raw = _run_hook(_surface_payload(surface))
    decision = _decision(parsed)
    if decision != "deny" and code == 0:
        _ok("V-HOOK-REVISE-DOES-NOT-DENY",
            "a REVISE verdict is surfaced, not refused -- reachability of the "
            "verdict did not widen what the gate may block")
    else:
        _fail("V-HOOK-REVISE-DOES-NOT-DENY",
              f"REVISE must not deny; got decision={decision!r} exit={code} "
              f"raw={raw[:200]!r}")


def gate_non_surface_inert(tmp: str) -> None:
    """A non-visual write must not even reach the gate."""
    project = os.path.join(tmp, "inertproj")
    os.makedirs(os.path.join(project, ".git"), exist_ok=True)
    _write(project, "DESIGN.md", SLOP_DESIGN)
    surface = _write(project, "util.py", "x = 1\n")

    parsed, code, raw = _run_hook(_surface_payload(surface))
    if parsed == {} and code == 0:
        _ok("V-HOOK-NON-SURFACE-INERT",
            "a .py write beside a BLOCKing DESIGN.md returns exactly {} -- the hook "
            "is scoped, not universal")
    else:
        _fail("V-HOOK-NON-SURFACE-INERT",
              f"non-surface write must be inert; got {raw[:200]!r} exit={code}")


def gate_unavailable_fails_open(tmp: str) -> None:
    """Infrastructure failure must not become a refusal -- nor a crash.

    Driven by pointing PP_PYTHON at a REAL executable that is not python, which
    is the honest shape of the failure: `spawnSync` succeeds, the child writes
    something that is not the gate's JSON, and the hook has to decide what an
    unreadable answer means. Pointing it at a nonexistent path would NOT drive
    this branch at all -- the hook's resolver tests the override with existsSync
    and silently falls back to a working interpreter, so that fixture would have
    measured the healthy path while appearing to measure the broken one.
    """
    project = os.path.join(tmp, "brokenproj")
    os.makedirs(os.path.join(project, ".git"), exist_ok=True)
    _write(project, "DESIGN.md", SLOP_DESIGN)
    surface = _write(project, "hero.tsx", "export const Hero = () => null;\n")

    parsed, code, raw = _run_hook(_surface_payload(surface),
                                  env_extra={"PP_PYTHON": _node()})
    decision = _decision(parsed)
    if decision != "deny" and code == 0 and parsed is not None:
        _ok("V-HOOK-GATE-UNAVAILABLE-FAILS-OPEN",
            "an unusable interpreter yields valid JSON, exit 0 and no refusal -- a "
            "broken gate stands down instead of blocking real work")
    else:
        _fail("V-HOOK-GATE-UNAVAILABLE-FAILS-OPEN",
              f"a broken gate must fail open, not deny or crash; got "
              f"decision={decision!r} exit={code} raw={raw[:200]!r}")


# --- The trust root -------------------------------------------------------- #
# Everything above proves the hook behaves once something runs it. This asks the
# other half -- whether anything DOES -- and it is where the recursion stops.
# A registration is an ordinary line in an ordinary file that can be read
# directly, so there is no checker-of-the-checker regress here: the chain
# terminates at an artifact, not at another gate.

_DISPATCH_EVENT_RE = re.compile(r"--event=([A-Za-z0-9\-]+)")
_JS_REF_RE = re.compile(r"([A-Za-z0-9_\-./\\]+\.js)")


def _chain_members(text: str, chain: str) -> set[str]:
    """Basenames named inside one CHAIN_MAP entry, by bracket matching."""
    match = re.search(r"['\"]" + re.escape(chain) + r"['\"]\s*:\s*\[", text)
    if not match:
        return set()
    depth, index = 0, match.end() - 1
    while index < len(text):
        if text[index] == "[":
            depth += 1
        elif text[index] == "]":
            depth -= 1
            if depth == 0:
                break
        index += 1
    body = text[match.end():index]
    return {r.replace("\\", "/").rsplit("/", 1)[-1] for r in _JS_REF_RE.findall(body)}


def double_invocations(settings: dict, dispatcher_text: str) -> list[str]:
    """Scripts reachable TWICE for one tool: directly from settings AND via a chain.

    Accumulates PER TOOL, not per settings entry.

    Grouping by entry reported a clean bill against a duplicate measured by hand
    minutes earlier: the two registrations of the CDIO hook live in TWO SEPARATE
    entries that happen to share one matcher, so the intersection inside either
    entry alone is necessarily empty. An instrument whose grouping key is finer
    than the effect it measures can only ever return "clean".

    Splitting the matcher into individual tool names rather than comparing matcher
    STRINGS is that correction one step further: "Write" and "Write|Edit" are
    different strings that both fire on a Write, so string equality would still
    under-report. Per tool, the question is exactly the question -- when the harness
    runs tool T, is this script reached twice.
    """
    per_tool: dict[str, dict[str, set]] = {}
    for entry in settings.get("hooks", {}).get("PreToolUse", []):
        tools = [t.strip() for t in str(entry.get("matcher", "*")).split("|")
                 if t.strip()] or ["*"]
        for hook in entry.get("hooks", []):
            command = str(hook.get("command", ""))
            refs = {r.replace("\\", "/").rsplit("/", 1)[-1]
                    for r in _JS_REF_RE.findall(command)}
            event = _DISPATCH_EVENT_RE.search(command)
            for tool in tools:
                slot = per_tool.setdefault(tool, {"direct": set(),
                                                  "reachable": set()})
                if event:
                    slot["reachable"] |= _chain_members(dispatcher_text,
                                                        event.group(1))
                else:
                    slot["direct"] |= refs
    found = []
    for tool, slot in sorted(per_tool.items()):
        for name in sorted(slot["direct"] & slot["reachable"]):
            found.append(f"{name} on tool {tool}")
    return found


_SYNTH_DISPATCH = """
const CHAIN_MAP = {
  'PreToolUse-Edit-chain': [
    { exe: NODE, script: './alpha.js' },
    { exe: NODE, script: '../pack/hooks/beta.js', block: true },
  ],
  'PreToolUse-Read-chain': [
    { exe: NODE, script: './gamma.js' },
  ],
};
"""


def _synth_settings(direct_script: str) -> dict:
    return {"hooks": {"PreToolUse": [
        {"matcher": "Write|Edit",
         "hooks": [{"command": '"node" "/x/hooks/hook-dispatcher.js" '
                               '--event=PreToolUse-Edit-chain'}]},
        {"matcher": "Write|Edit",
         "hooks": [{"command": f'"node" "/x/hooks/{direct_script}"'}]},
    ]}}


def gate_registry_detector_works() -> None:
    """Positive control for the duplicate branch, on a SYNTHETIC registry.

    The duplicate check returned a false clean bill once during its own
    development, and an empty result is exactly what a broken parser produces --
    so a green from it means nothing without a case that MUST come back non-empty.

    Synthetic on purpose. Pinning this to the real duplicate in settings.json would
    give the drill an interest in that duplicate surviving: the moment the Owner
    removes it, the control would pass vacuously at precisely the moment it stopped
    proving anything. A planted registry keeps working after the estate is clean and
    still exercises the real predicates.
    """
    planted = double_invocations(_synth_settings("beta.js"), _SYNTH_DISPATCH)
    clean = double_invocations(_synth_settings("delta.js"), _SYNTH_DISPATCH)
    # A script belonging to a DIFFERENT chain must not count: gamma is in the Read
    # chain, so a Write-matcher direct registration of it is one invocation, not two.
    cross = double_invocations(_synth_settings("gamma.js"), _SYNTH_DISPATCH)

    want = {"beta.js on tool Edit", "beta.js on tool Write"}
    if set(planted) == want and clean == [] and cross == []:
        _ok("V-HOOK-REGISTRY-DETECTOR-WORKS",
            "planted duplicate found on both tools; an unrelated direct script and a "
            "script from a DIFFERENT chain both report clean -- the detector "
            "discriminates rather than always answering")
    else:
        _fail("V-HOOK-REGISTRY-DETECTOR-WORKS",
              f"planted={sorted(planted)} (want {sorted(want)}) "
              f"clean={clean} cross-chain={cross}")


def gate_trigger_registered() -> None:
    """Is CDIO enforcement wired to anything, and wired exactly once per matcher?

    Absence is the severe case and it is the one this asserts hard: a gate with no
    registration is not weak enforcement, it is no enforcement, while every
    in-process suite stays green. Duplication is REPORTED, not failed -- the fix
    lives in ~/.claude/settings.json, which is Owner-owned (HR-001), and a gate
    that is red on arrival for a file it may not edit is the shape that gets
    switched off within a week.
    """
    hook_name = os.path.basename(HOOK)
    sites = registration_sites(Path(PP_ROOT))
    where = sites.get(hook_name, [])

    if not where:
        _fail("V-HOOK-TRIGGER-REGISTERED",
              f"{hook_name} is named by NO registration surface -- the CDIO design "
              f"gate cannot be reached automatically, and no in-process suite can "
              f"see that")
        return

    settings_path = live_root() / "settings.json"
    dispatcher_path = live_root() / "hooks" / "hook-dispatcher.js"
    doubles = []
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8-sig"))
        dispatcher_text = dispatcher_path.read_text(encoding="utf-8-sig")
        doubles = double_invocations(settings, dispatcher_text)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        # An unreadable registration surface is NOT a clean bill. Say which of the
        # two questions went unanswered rather than reporting the silence as "no
        # duplicates found".
        _ok("V-HOOK-TRIGGER-REGISTERED",
            f"registered on {len(where)} surface(s): {', '.join(sorted(set(where)))}; "
            f"duplicate-invocation check UNEVALUATED ({exc})")
        return

    mine = [d for d in doubles if d.startswith(hook_name)]
    if mine:
        _ok("V-HOOK-TRIGGER-REGISTERED",
            f"registered on {len(where)} surface(s): {', '.join(sorted(set(where)))}. "
            f"REPORTED, not failed -- DOUBLE INVOCATION: {'; '.join(mine)}. The hook "
            f"runs twice per matching write, spawning design_gate.py twice. The fix "
            f"is Owner-side in ~/.claude/settings.json (HR-001): remove the standalone "
            f"entry, keep the dispatcher chain, which carries block:true and the "
            f"larger timeout budget")
    else:
        _ok("V-HOOK-TRIGGER-REGISTERED",
            f"registered on {len(where)} surface(s): {', '.join(sorted(set(where)))}; "
            f"no matcher reaches it twice"
            + (f"; other hooks double-registered: {len(doubles)}" if doubles else ""))


def _cleanup_markers() -> None:
    """Remove this run's throttle markers. The hook writes them into a GLOBAL state
    directory, so a suite that left them behind would slowly fill it and, worse,
    would be writing outside its own fixture -- the non-hermetic shape this estate
    has already been bitten by."""
    try:
        for name in os.listdir(STATE_DIR):
            if _SESSION in name:
                os.remove(os.path.join(STATE_DIR, name))
    except OSError:
        pass


def main() -> int:
    print("V-HOOK gates (CDIO enforcement across the real process boundary)")
    if not os.path.isfile(HOOK):
        print(f"  [FAIL] V-HOOK-PRESENT: {HOOK} absent")
        print("HOOK_PASS=0/1  threshold=6/6")
        return 1

    try:
        with tempfile.TemporaryDirectory() as tmp:
            gate_block_denies(tmp)
            gate_approve_allows(tmp)
            gate_revise_does_not_deny(tmp)
            gate_non_surface_inert(tmp)
            gate_unavailable_fails_open(tmp)
        gate_registry_detector_works()
        gate_trigger_registered()
    finally:
        _cleanup_markers()

    total = _passes + _fails
    print(f"HOOK_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
