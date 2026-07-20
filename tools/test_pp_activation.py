#!/usr/bin/env python3
"""test_pp_activation.py -- V-gates for PP proactive activation.

Sealed 2026-07-20 alongside the PP Activation Audit
(vault/plans/pp-activation-2026-07-20.md).

Measures the thing that was actually broken (T-PP-SILENT-SKILL-001):
not "does PP exist" but "can anything reach it from a real repo".
Activation is counted in repos that reference PP, never in modules
that exist (PR-PP-ACTIVATION-EXPLICIT-001).

Hermetic: the JIT gates use a dedicated session id whose dedupe-state
file is removed before and after, so three consecutive runs are
identical. No wall-clock or TTL dependence.

Run: python tools/test_pp_activation.py   (exit 0 = all gates pass)
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
PP_ROOT = HOME / ".claude" / "skills" / "claude-power-pack"
SKILL_MD = PP_ROOT / "SKILL.md"
GLOBAL_CLAUDE_MD = HOME / ".claude" / "CLAUDE.md"
SETTINGS = HOME / ".claude" / "settings.json"
JIT = PP_ROOT / "tools" / "jit_skill_loader.py"
STATE_DIR = HOME / ".claude" / "state"
PROJECTS = HOME.parent / "User" / "Desktop" / "Cursor Projects"

TEST_SID = "pp-activation-selftest"
MIN_TRIGGER_TERMS = 8
MIN_CRITERIA_ROWS = 8
MIN_REPOS = 3

_passes: list[str] = []
_fails: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    _passes.append(gate)
    print(f"OK   {gate}  -- {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    _fails.append(gate)
    print(f"FAIL {gate}  -- {diagnostic}")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8-sig")


def _clean_state() -> None:
    """Remove the self-test dedupe file so runs are order-independent."""
    try:
        (STATE_DIR / f"jit-injected-{TEST_SID}.json").unlink(missing_ok=True)
    except Exception:
        pass


# --------------------------------------------------------------------
# V-PP-SKILL-DISCOVERABLE
# --------------------------------------------------------------------
def gate_discoverable() -> str | None:
    gate = "V-PP-SKILL-DISCOVERABLE"
    if not SKILL_MD.is_file():
        _fail(gate, f"{SKILL_MD} absent")
        return None
    body = _read(SKILL_MD)
    m = re.match(r"^---\n(.*?)\n---\n", body, re.S)
    if not m:
        _fail(gate, "no YAML frontmatter block")
        return None
    fm = m.group(1)
    if not re.search(r"^name:\s*claude-power-pack\s*$", fm, re.M):
        _fail(gate, "frontmatter name is not claude-power-pack")
        return None
    desc = re.search(r'^description:\s*"(.*)"\s*$', fm, re.M | re.S)
    if not desc:
        _fail(gate, "no quoted description in frontmatter")
        return None
    _ok(gate, f"frontmatter valid, description {len(desc.group(1))} chars")
    return desc.group(1)


# --------------------------------------------------------------------
# V-PP-DESC-TRIGGERS -- the description must be a trigger list, not a
# tagline. This is the gate that would have caught the original bug.
# --------------------------------------------------------------------
TRIGGER_TERMS = [
    "architect", "multi-file", "scratch", "debug", "done", "deploy",
    "dataset", "vault", "token", "governance", "review", "recovery",
    "handoff", "infra", "audit",
]


def gate_desc_triggers(desc: str | None) -> None:
    gate = "V-PP-DESC-TRIGGERS"
    if desc is None:
        _fail(gate, "description unavailable (discoverable gate failed)")
        return
    low = desc.lower()
    hits = sorted({t for t in TRIGGER_TERMS if t in low})
    if len(hits) < MIN_TRIGGER_TERMS:
        _fail(gate, f"only {len(hits)} trigger terms ({hits}); "
                    f"need >= {MIN_TRIGGER_TERMS}. A tagline is not a "
                    f"trigger list.")
        return
    if "use " not in low and "when " not in low:
        _fail(gate, "description never states WHEN to use the skill")
        return
    _ok(gate, f"{len(hits)} trigger terms: {', '.join(hits)}")


# --------------------------------------------------------------------
# V-PP-AUTOINVOKE-DEFINED
# --------------------------------------------------------------------
def gate_autoinvoke() -> None:
    gate = "V-PP-AUTOINVOKE-DEFINED"
    if not GLOBAL_CLAUDE_MD.is_file():
        _fail(gate, f"{GLOBAL_CLAUDE_MD} absent")
        return
    body = _read(GLOBAL_CLAUDE_MD)
    if "PP Activation Criteria" not in body:
        _fail(gate, "no 'PP Activation Criteria' section in global CLAUDE.md")
        return
    section = body.split("PP Activation Criteria", 1)[1]
    section = section.split("\n## ", 1)[0]
    rows = [ln for ln in section.splitlines()
            if ln.startswith("| ") and "---" not in ln]
    rows = [r for r in rows if "Invoke PP for" not in r]
    if len(rows) < MIN_CRITERIA_ROWS:
        _fail(gate, f"only {len(rows)} criteria rows; need >= "
                    f"{MIN_CRITERIA_ROWS}")
        return
    _ok(gate, f"{len(rows)} explicit IF/THEN criteria rows")


# --------------------------------------------------------------------
# V-PP-SESSION-START
# --------------------------------------------------------------------
def gate_session_start() -> None:
    gate = "V-PP-SESSION-START"
    hub = PP_ROOT / "hooks" / "session_start_hub.js"
    if not hub.is_file():
        _fail(gate, "session_start_hub.js absent")
        return
    if not SETTINGS.is_file():
        _fail(gate, "settings.json absent")
        return
    try:
        cfg = json.loads(_read(SETTINGS))
    except Exception as exc:
        _fail(gate, f"settings.json unparseable: {exc}")
        return
    wired = json.dumps(cfg.get("hooks", {}).get("SessionStart", []))
    if "session_start_hub.js" not in wired:
        _fail(gate, "hub exists but is NOT wired into SessionStart "
                    "(built != wired)")
        return
    _ok(gate, "hub present and wired in settings.json SessionStart")


# --------------------------------------------------------------------
# V-PP-JIT-PP-FAMILY -- behavioral, not structural.
# --------------------------------------------------------------------
def _load_jit():
    spec = importlib.util.spec_from_file_location("jit_pp_test", JIT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def gate_jit_family():
    gate = "V-PP-JIT-PP-FAMILY"
    if not JIT.is_file():
        _fail(gate, "jit_skill_loader.py absent")
        return None
    try:
        mod = _load_jit()
    except Exception as exc:
        _fail(gate, f"jit_skill_loader.py does not import: {exc}")
        return None
    if not hasattr(mod, "_detect_pp_capability_trigger"):
        _fail(gate, "_detect_pp_capability_trigger absent")
        return mod

    non_pp = str(PROJECTS / "TUA-X")

    def run(prompt: str, cwd: str) -> str:
        return json.dumps(mod.run({
            "hook_event_name": "UserPromptSubmit",
            "prompt": prompt, "cwd": cwd, "session_id": TEST_SID,
        }))

    task_prompt = "audit this dataset before we deploy to production"
    _clean_state()
    try:
        first = run(task_prompt, non_pp)
        if "claude-power-pack" not in first:
            _fail(gate, "card did NOT fire on a task-shaped prompt in a "
                        "non-PP repo")
            return mod
        second = run(task_prompt, non_pp)
        if "claude-power-pack" in second:
            _fail(gate, "card fired twice in one session (dedupe broken)")
            return mod
        _clean_state()
        in_pp = run(task_prompt, str(PP_ROOT))
        if "PP activation criteria" in in_pp:
            _fail(gate, "card fired inside the PP repo (should be silent)")
            return mod
        _clean_state()
        trivial = run("rename this variable", non_pp)
        if "claude-power-pack" in trivial:
            _fail(gate, "card fired on a trivial prompt (spam mode)")
            return mod
        if json.loads(trivial).get("continue") is not True:
            _fail(gate, "loader did not return continue:true (fail-open "
                        "contract broken)")
            return mod
    finally:
        _clean_state()
    _ok(gate, "fires once in non-PP repo, dedupes, silent in PP repo, "
              "silent on trivial, fail-open")
    return mod


# --------------------------------------------------------------------
# V-PP-REPOS-CONFIGURED
# --------------------------------------------------------------------
def gate_repos() -> None:
    gate = "V-PP-REPOS-CONFIGURED"
    if not PROJECTS.is_dir():
        _fail(gate, f"{PROJECTS} absent")
        return
    rx = re.compile(r"claude-power-pack|Power Pack|/cpp-", re.I)
    found = []
    for d in sorted(PROJECTS.iterdir()):
        if not d.is_dir():
            continue
        cm = d / "CLAUDE.md"
        if not cm.is_file():
            continue
        try:
            if rx.search(_read(cm)):
                found.append(d.name)
        except Exception:
            continue
    if len(found) < MIN_REPOS:
        _fail(gate, f"only {len(found)} repos reference PP ({found}); "
                    f"need >= {MIN_REPOS}")
        return
    _ok(gate, f"{len(found)} repos reference PP: {', '.join(found[:6])}")


# --------------------------------------------------------------------
# V-BASELINE -- the Apollo trigger families must survive the retrofit.
# --------------------------------------------------------------------
def gate_baseline(mod) -> None:
    gate = "V-BASELINE"
    if mod is None:
        _fail(gate, "loader unavailable")
        return
    names = {t[0] for t in getattr(mod, "TRIGGERS", [])}
    required = {"graphql_ops", "apollo_client", "apollo_server"}
    missing = required - names
    if missing:
        _fail(gate, f"Apollo trigger families lost: {sorted(missing)}")
        return
    if not getattr(mod, "TASK_PROFILES", None):
        _fail(gate, "TASK_PROFILES empty")
        return
    _ok(gate, f"{len(names)} Apollo trigger families intact, "
              f"{len(mod.TASK_PROFILES)} task profiles")


def main() -> int:
    desc = gate_discoverable()
    gate_desc_triggers(desc)
    gate_autoinvoke()
    gate_session_start()
    mod = gate_jit_family()
    gate_repos()
    gate_baseline(mod)
    total = len(_passes) + len(_fails)
    print(f"\nPP_ACTIVATION_PASS={len(_passes)}/{total}  "
          f"threshold={total}/{total}")
    if _fails:
        print("FAILED GATES: " + ", ".join(_fails))
    return 0 if not _fails else 1


if __name__ == "__main__":
    sys.exit(main())
