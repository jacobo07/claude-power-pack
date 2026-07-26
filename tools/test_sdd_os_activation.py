#!/usr/bin/env python3
"""SDD-OS activation done-gate -- BL-SDD-ACT-001.

Six V-gates proving the activation path is live, correct, proportional,
non-destructive, and actually reaching the Owner's repos.

    python tools/test_sdd_os_activation.py

Exit 0 only when every gate passes. Global CLAUDE.md registration is
reported as an explicit STATUS line rather than folded into a gate: it is
an Owner action under HR-001, and a gate that silently passes on work
nobody did is the exact failure this whole effort exists to close.
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

_passes: list[str] = []
_fails: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    _passes.append(gate)
    print(f"  [PASS] {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    _fails.append(gate)
    print(f"  [FAIL] {gate}: {diagnostic}")


# --- V-SDDOS-CLAUDE-MD ---------------------------------------------------

def v_claude_md() -> None:
    """The activation criteria exist as explicit, verifiable rules."""
    gate = "V-SDDOS-CLAUDE-MD"
    doc = PP_ROOT / "governance" / "SDD_OS_GOVERNANCE.md"
    if not doc.is_file():
        _fail(gate, f"missing {doc}")
        return
    text = doc.read_text(encoding="utf-8")

    # Each tier must be named with a concrete trigger, not "when needed".
    required = [
        "Tier 0", "Tier 1", "Tier 2", "Tier 3",
        "covers", "Spec First. Execution Second. Validation Always.",
        "T-SDD-OS-IMPLICIT-ACTIVATION-001",
    ]
    missing = [r for r in required if r not in text]
    if missing:
        _fail(gate, f"criteria doc lacks {missing}")
        return

    # The failure mode being closed: vague activation language. A doc that
    # NAMES the antipattern must not be flagged for naming it, so quoted
    # and italicised spans are citations and are stripped before matching
    # (the doc's own UKDL entry quotes the phrase it forbids).
    import re as _re
    normative = _re.sub(r'"[^"]*"|\*[^*\n]+\*|`[^`]*`', " ", text).lower()
    vague = [p for p in ("when it seems", "cuando lo juzgue", "if appropriate",
                         "at the agent's discretion", "as needed")
             if p in normative]
    if vague:
        _fail(gate, f"criteria still vague outside citations: {vague}")
        return
    _ok(gate, f"{len(required)} explicit criteria present, 0 vague phrases "
              f"in normative text")


# --- V-SDDOS-TIER-CLASSIFICATION -----------------------------------------

def v_tier_classification() -> None:
    gate = "V-SDDOS-TIER-CLASSIFICATION"
    from modules.sdd_os.pre_exec_gate import evaluate

    cases = [
        ("fix a typo in the readme label", 0),
        ("rename a local variable for clarity", 0),
        ("add a command option to the exporter", 1),
        ("fix bug in the date parser with a clear cause", 1),
        ("create a new billing integration module with persistence", 2),
        ("add an authentication endpoint and schema migration", 2),
        ("build a universal spec-driven development framework for every repo", 3),
        ("design a new internal OS as a global standard", 3),
    ]
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        wrong = []
        for task, expected in cases:
            got = evaluate(task, root).tier
            if got != expected:
                wrong.append(f"{task[:34]!r} -> {got} (want {expected})")
    if wrong:
        _fail(gate, f"{len(wrong)}/{len(cases)} misclassified: {wrong[:3]}")
        return
    _ok(gate, f"{len(cases)}/{len(cases)} tiers correct across all four levels")


# --- V-SDDOS-SPEC-BEFORE-CODE --------------------------------------------

def v_spec_before_code() -> None:
    """Tier 2+ with no bound spec must GENERATE one, and it must bind."""
    gate = "V-SDDOS-SPEC-BEFORE-CODE"
    from modules.sdd_os.pre_exec_gate import enforce, evaluate
    from modules.sdd_os.spec_binding import find_bound_spec, read_covers

    task = "create a new billing integration module with persistence"
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        if evaluate(task, root).action != "write_spec":
            _fail(gate, "Tier 2 on an empty repo did not demand a spec")
            return

        d = enforce(task, root, auto_generate=True)
        if not d.spec_written or not d.spec_path or not d.spec_path.is_file():
            _fail(gate, "gate did not write the spec skeleton")
            return

        covers = read_covers(d.spec_path)
        if not covers:
            _fail(gate, "generated spec declares no `covers` -- cannot bind")
            return

        # The decisive property: the generated spec closes its own gate.
        if not find_bound_spec(task, root).bound:
            _fail(gate, "generated spec does not bind to the task that made it")
            return

        # Non-destructive on re-entry.
        again = enforce(task, root, auto_generate=True)
        if again.spec_written:
            _fail(gate, "second pass overwrote an existing spec")
            return

        # And it must NOT bind an unrelated task (RC-2 regression guard).
        if find_bound_spec("rewrite the shader compiler", root).bound:
            _fail(gate, "spec binds an unrelated task -- RC-2 reintroduced")
            return

        # Tier 0 must stay cheap: no file demanded.
        if evaluate("fix a typo in a label", root).action == "write_spec":
            _fail(gate, "Tier 0 demanded a written spec -- not proportional")
            return

    _ok(gate, f"Tier2 generated+bound+idempotent, covers={list(covers)[:3]}, "
              f"Tier0 stays inline")


# --- V-SDDOS-SPEC-UPDATE -------------------------------------------------

def v_spec_update() -> None:
    gate = "V-SDDOS-SPEC-UPDATE"
    from modules.sdd_os.scaffold import check_drift

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "vault" / "specs").mkdir(parents=True)
        spec = root / "vault" / "specs" / "t2-thing.md"
        spec.write_text("---\ncovers: [thing]\ntier: 2\n---\n# spec\n",
                        encoding="utf-8")
        (root / "app.py").write_text("print(1)\n", encoding="utf-8")

        old = time.time() - 86400 * 5
        os.utime(spec, (old, old))
        stale = [r for r in check_drift(root) if r.drifted]
        if not stale:
            _fail(gate, "spec older than the code was not reported stale")
            return

        # Touching the spec must clear it -- the loop has to be closeable.
        now = time.time() + 5
        os.utime(spec, (now, now))
        still = [r for r in check_drift(root) if r.drifted]
        if still:
            _fail(gate, "refreshed spec still reported stale -- loop cannot close")
            return

        # An undeclared spec is not checkable, and must not be silently "ok".
        undecl = root / "vault" / "specs" / "legacy.md"
        undecl.write_text("# no front matter\n", encoding="utf-8")
        checked = {r.spec_path.name for r in check_drift(root)}
        if "legacy.md" in checked:
            _fail(gate, "undeclared spec was drift-checked as if it bound")
            return

    _ok(gate, "stale detected, refresh clears it, undeclared excluded")


# --- V-SDDOS-SCAFFOLD ----------------------------------------------------

def v_scaffold() -> None:
    gate = "V-SDDOS-SCAFFOLD"
    from modules.sdd_os.scaffold import SCAFFOLD_FILES, is_scaffolded, scaffold

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text("[project]\nname='x'\n",
                                             encoding="utf-8")
        r = scaffold(root)
        created = {p.name for p in r.created}
        if not set(SCAFFOLD_FILES).issubset(created):
            _fail(gate, f"scaffold created {created}, want {SCAFFOLD_FILES}")
            return
        if not is_scaffolded(root):
            _fail(gate, "is_scaffolded False right after scaffolding")
            return

    # Non-destructive is the hard contract: this runs on repos with years
    # of real documentation.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        sentinel = "# HAND WRITTEN - MUST SURVIVE\n"
        (root / "ARCHITECTURE.md").write_text(sentinel, encoding="utf-8")
        r = scaffold(root)
        if (root / "ARCHITECTURE.md").read_text(encoding="utf-8") != sentinel:
            _fail(gate, "scaffold overwrote existing documentation")
            return
        if (root / "ARCHITECTURE.md") not in r.skipped:
            _fail(gate, "existing file not reported as preserved")
            return

    _ok(gate, f"{list(SCAFFOLD_FILES)} created on a bare repo; "
              f"existing docs preserved byte-for-byte")


# --- V-SDDOS-ACTIVE-REPOS ------------------------------------------------

ACTIVE_REPOS_FILE = PP_ROOT / "vault" / "sdd_os" / "active_repos.txt"


def v_active_repos(minimum: int = 3) -> None:
    """Real repos carry a generated Architecture Spec."""
    gate = "V-SDDOS-ACTIVE-REPOS"
    if not ACTIVE_REPOS_FILE.is_file():
        _fail(gate, f"rollout manifest absent: {ACTIVE_REPOS_FILE}")
        return

    repos = [
        Path(l.strip()) for l in
        ACTIVE_REPOS_FILE.read_text(encoding="utf-8-sig").splitlines()
        if l.strip() and not l.strip().startswith("#")
    ]
    have, missing = [], []
    for repo in repos:
        arch = repo / "ARCHITECTURE.md"
        if arch.is_file():
            have.append(repo.name)
        else:
            missing.append(repo.name)

    if len(have) < minimum:
        _fail(gate, f"only {len(have)}/{len(repos)} repos carry an "
                    f"Architecture Spec (need >= {minimum}); missing {missing[:4]}")
        return
    _ok(gate, f"{len(have)}/{len(repos)} active repos carry an Architecture "
              f"Spec: {have[:5]}")


# --- V-SDDOS-ACTIVATION-LIVE --------------------------------------------

def v_activation_live() -> None:
    """The directive reaches a prompt through the real hook decorator."""
    gate = "V-SDDOS-ACTIVATION-LIVE"
    import tools.jit_skill_loader as jsl
    from modules.sdd_os.activation import build_directive

    if not hasattr(jsl, "_sdd_os_activation_inject"):
        _fail(gate, "jit_skill_loader has no _sdd_os_activation_inject")
        return

    src = (PP_ROOT / "tools" / "jit_skill_loader.py").read_text(
        encoding="utf-8")
    if "@_sdd_os_activation_inject" not in src:
        _fail(gate, "decorator defined but never applied to run()")
        return

    # Exercise the decorator itself, not just its existence.
    @jsl._sdd_os_activation_inject
    def _run(_data):
        return {"continue": True, "additionalContext": "PRIOR"}

    with tempfile.TemporaryDirectory() as td:
        out = _run({
            "prompt": "create a new billing integration module with "
                      "persistence and auth for this service",
            "cwd": td,
        })
    ac = out.get("additionalContext", "")
    if "SDD-OS" not in ac:
        _fail(gate, "decorator ran but injected no SDD-OS directive")
        return
    if not ac.startswith("==="):
        _fail(gate, "directive did not take priority position")
        return
    if "PRIOR" not in ac:
        _fail(gate, "decorator destroyed pre-existing additionalContext")
        return

    # Fail-open: a broken inner call must never block a prompt.
    @jsl._sdd_os_activation_inject
    def _boom(_data):
        return "not-a-dict"
    if _boom({"prompt": "x" * 80, "cwd": "."}) != "not-a-dict":
        _fail(gate, "decorator mutated a non-dict result")
        return

    # Silence conditions must hold.
    with tempfile.TemporaryDirectory() as td:
        if build_directive("continue", td) is not None:
            _fail(gate, "fired on a short follow-up prompt")
            return

    _ok(gate, "decorator applied to run(), injects in priority position, "
              "preserves prior context, fail-open on non-dict")


# --- V-SDDOS-HOOK-READONLY ----------------------------------------------

def v_hook_readonly() -> None:
    """The prompt-path must never write, even in a scaffolded repo.

    Regression guard for the defect that shipped and spread the same day:
    generation was tied to "is this repo scaffolded", so the hook wrote a
    spec skeleton per long prompt. `_active_spec()` picks the newest spec,
    so an EMPTY skeleton became the injected "ACTIVE PROJECT SPEC". Three
    junk files landed across three repos before it was caught.
    """
    gate = "V-SDDOS-HOOK-READONLY"
    from modules.sdd_os.activation import build_directive
    from modules.sdd_os.pre_exec_gate import enforce, evaluate
    from modules.sdd_os.scaffold import scaffold

    task = ("create a new billing integration module with persistence and "
            "auth for the payments service")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        scaffold(root)                      # the condition that enabled writes
        before = {p for p in root.rglob("*") if p.is_file()}

        directive = build_directive(task, root)
        after = {p for p in root.rglob("*") if p.is_file()}

        leaked = after - before
        if leaked:
            _fail(gate, f"prompt path wrote {[p.name for p in leaked]}")
            return
        if not directive or "SDD-OS" not in directive:
            _fail(gate, "read-only, but the directive stopped firing")
            return
        if evaluate(task, root).action == "proceed":
            _fail(gate, "evaluate() saw a spec that was never written")
            return

        # Read-only must not mean the generator is dead.
        d = enforce(task, root, auto_generate=True)
        if not d.spec_written:
            _fail(gate, "explicit generation no longer writes")
            return

    _ok(gate, "0 files written by the prompt path in a scaffolded repo; "
              "explicit generation still works")


# --- V-SDDOS-GLOBAL-REGISTERED ------------------------------------------

REQUIRED_GLOBAL_CLAUSES = (
    "SDD-OS",
    "Spec First. Execution Second. Validation Always.",
    "T2", "T3", "covers:", "prohibited",
)


def v_global_registered() -> None:
    """The activation rules are on the standing global instruction surface.

    Host-coupled by nature: this asserts a fact about ~/.claude/CLAUDE.md,
    which is Owner-owned config. It was a STATUS line until the Owner
    authorized the write on 2026-07-26 (lifting HR-001 for that operation);
    gating on it earlier would have been a gate passing on work nobody had
    done. On a fresh host, register the block from
    governance/SDD_OS_GOVERNANCE.md to clear it.
    """
    gate = "V-SDDOS-GLOBAL-REGISTERED"
    global_md = Path.home() / ".claude" / "CLAUDE.md"
    if not global_md.is_file():
        _fail(gate, f"{global_md} not found")
        return
    text = global_md.read_text(encoding="utf-8", errors="replace")

    missing = [c for c in REQUIRED_GLOBAL_CLAUSES if c not in text]
    if missing:
        _fail(gate, f"global CLAUDE.md lacks {missing} -- register the block "
                    f"from governance/SDD_OS_GOVERNANCE.md")
        return

    heads = text.count("## SDD-OS")
    if heads != 1:
        _fail(gate, f"expected exactly 1 SDD-OS section, found {heads}")
        return

    _ok(gate, f"registered in ~/.claude/CLAUDE.md, 1 section, "
              f"{len(REQUIRED_GLOBAL_CLAUSES)} clauses present "
              f"({len(text)} chars total)")


def main() -> int:
    print("SDD-OS activation done-gate (BL-SDD-ACT-001)\n")
    for fn in (v_claude_md, v_global_registered, v_tier_classification,
               v_spec_before_code, v_spec_update, v_scaffold,
               v_active_repos, v_activation_live, v_hook_readonly):
        try:
            fn()
        except Exception as exc:  # a crashing gate is a failing gate
            _fail(fn.__name__, f"raised {type(exc).__name__}: {exc}")

    total = len(_passes) + len(_fails)
    print(f"\nSDDOS_PASS={len(_passes)}/{total}  threshold={total}/{total}")

    # Owner-action status, reported honestly, never folded into a gate.
    global_md = Path.home() / ".claude" / "CLAUDE.md"
    registered = False
    if global_md.is_file():
        registered = "SDD-OS" in global_md.read_text(
            encoding="utf-8", errors="replace")
    print(f"STATUS global_claude_md_registered={registered} "
          f"({'live via hook chain regardless' if not registered else 'durable'})")
    if not registered:
        print("  -> Owner step (HR-001): paste the block from "
              "governance/SDD_OS_GOVERNANCE.md into ~/.claude/CLAUDE.md")

    if _fails:
        print(f"\nFAILING: {_fails}")
    return 1 if _fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
