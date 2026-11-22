#!/usr/bin/env python3
"""self_improve_guard.py -- the FIXED CORE policy of the autonomous self-improve loop.

Spec: vault/specs/self-improve-unattended.md. The loop (tools/self_improve_unattended.py, also core) may improve
tools/self_improve_policy.py and ordinary files in its allowlist. It may NOT change the core, its pin, its judges
(the regression suites and the transcript analyser that measures it) or the controls listed below: a loop that can
rewrite its own brakes or its own judge is unbounded, not autonomous (mission rule "No desactives controles de
seguridad"). The driver verifies the core's sha256 against vault/self_improve/guard.sha256 on every run and after
every execution of agent-written code, and stops on a mismatch. Only the Owner re-pins
(`python tools/self_improve_guard.py --pin`).

Pure policy: no model calls, no git writes.
"""
from __future__ import annotations

import ctypes
import hashlib
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PIN_PATH = REPO / "vault" / "self_improve" / "guard.sha256"

# ---------------------------------------------------------------- kill switch
SWITCH = "CPP_SELF_IMPROVE"


def killed(state_dir: Path) -> str | None:
    if str(os.environ.get(SWITCH) or "").strip().lower() in ("0", "off", "false", "no"):
        return f"kill switch {SWITCH}=off"
    if (Path(state_dir) / "OFF").exists():
        return f"kill switch file {Path(state_dir) / 'OFF'}"
    return None


# ---------------------------------------------------------------- integrity
# The core = this policy AND the driver that enforces it (an editable driver could stop calling this file).
CORE_FILES = ("tools/self_improve_guard.py", "tools/self_improve_unattended.py")


def sha256_of(path: Path) -> str:
    # Line endings normalised, so a CRLF checkout does not read as tampering.
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def integrity(pin_path: Path = PIN_PATH, repo: Path = REPO) -> str | None:
    """None when every core file matches its pin, else why the run must stop."""
    try:
        pins = {}
        for line in Path(pin_path).read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) >= 2:
                pins[parts[1]] = parts[0]
    except OSError:
        return f"core pin missing ({pin_path})"
    for rel in CORE_FILES:
        if rel not in pins:
            return f"core pin has no entry for {rel}"
        try:
            actual = sha256_of(Path(repo) / rel)
        except OSError:
            return f"core file missing: {rel}"
        if actual != pins[rel]:
            return (f"{rel} hash {actual[:12]} != pinned {pins[rel][:12]}: the fixed core changed; "
                    "the Owner must review and re-pin")
    return None


def pin(pin_path: Path = PIN_PATH, repo: Path = REPO) -> str:
    Path(pin_path).parent.mkdir(parents=True, exist_ok=True)
    text = "".join(f"{sha256_of(Path(repo) / rel)}  {rel}\n" for rel in CORE_FILES)
    Path(pin_path).write_text(text, encoding="utf-8")
    return text


# Files outside the repo whose change during a cycle means agent-written code escaped its worktree.
WATCHED_OUTSIDE = (Path.home() / ".claude" / "settings.json", Path.home() / ".claude" / "settings.local.json",
                   Path.home() / ".gitconfig")


def fingerprint(pin_path: Path, repo: Path, watched=WATCHED_OUTSIDE) -> dict:
    out = {}
    for p in [Path(pin_path)] + [Path(repo) / r for r in CORE_FILES] + [Path(w) for w in watched]:
        try:
            out[str(p)] = sha256_of(p)
        except OSError:
            out[str(p)] = None
    return out


def tamper(before: dict, after: dict) -> str | None:
    moved = [k for k in before if before.get(k) != after.get(k)]
    return f"changed during the cycle: {', '.join(moved)}" if moved else None


# ---------------------------------------------------------------- admission
MIN_FREE_RAM_PCT = 20.0          # 2026-11-21 triage: timeouts are host-wide stalls at p50 3.8% free
FOREIGN_LOCKS = ("compound-unattended.lock",)


def free_ram_pct() -> float | None:
    if sys.platform != "win32":
        try:
            info = dict(l.split(":", 1) for l in Path("/proc/meminfo").read_text().splitlines() if ":" in l)
            tot = float(info["MemTotal"].split()[0]); av = float(info["MemAvailable"].split()[0])
            return round(100.0 * av / tot, 1)
        except (OSError, KeyError, ValueError):
            return None

    class MS(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    m = MS(); m.dwLength = ctypes.sizeof(MS)
    try:
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
            return None
    except (AttributeError, OSError):
        return None
    return round(100.0 * m.ullAvailPhys / m.ullTotalPhys, 1)


def ram_refusal(ram_pct: float | None) -> str | None:
    if ram_pct is None:
        return "free RAM unmeasurable -- refusing (unknown is not an allowance)"
    if ram_pct < MIN_FREE_RAM_PCT:
        return f"free RAM {ram_pct}% < {MIN_FREE_RAM_PCT}%"
    return None


def admission(spend_refusal: str | None, ram_pct: float | None, claude_state_dir: Path) -> str | None:
    """None when a model-spending step may run. Unknown is a refusal, never an allowance."""
    if spend_refusal:
        return f"spend refused: {spend_refusal}"
    why = ram_refusal(ram_pct)
    if why:
        return why
    for name in FOREIGN_LOCKS:
        if (Path(claude_state_dir) / name).exists():
            return f"another unattended run holds {name}"
    return None


# ---------------------------------------------------------------- the agent's sandbox (claude CLI flags)
# --restricted: no code-running tools unless --tools names them, user/project/local settings ignored (so their
# blanket allows and hooks do not apply), file tools confined to the working directory. Verified against the CLI's
# own --help on 2026-11-22; V-SIU-AGENT-SANDBOX pins that these flags are what the driver passes.
AGENT_TOOLS = "Read,Write,Edit,Glob,Grep"
AGENT_FLAGS = ("--restricted", "--strict-mcp-config", "--disable-slash-commands", "--permission-mode", "acceptEdits",
               "--tools", AGENT_TOOLS, "--disallowed-tools", "Bash PowerShell WebFetch WebSearch Agent")

# ---------------------------------------------------------------- edit allowlist
ALLOWED_PREFIXES = ("tools/", "hooks/", "modules/", "commands/")
# Path tokens that mark a control: secrets, spend, governance, push, hard rules, guards and gates.
DENIED_TOKENS = ("secret", "firewall", "governance", "governor", "spend", "push", "hard_rule", "hardrule",
                 "ovo", "guard", "gate", "dispatcher", "settings", "permission", "zero-crash", "credential")
# The core, its tests, and its judges: the regression suites and the analyser that measures every change.
DENIED_EXACT = CORE_FILES + ("tools/test_self_improve_unattended.py", "tools/test_analyze_transcripts.py",
                             "tools/test_reader_robustness.py", "tools/analyze_transcripts.py",
                             "tools/transcript_events.py")
BLOCKING_HOOK_RE = re.compile(r"""permissionDecision|["']decision["']\s*:\s*["']block|process\.exit\(\s*2\s*\)|sys\.exit\(\s*2\s*\)""")
# Agent-written code is EXECUTED by the driver's tests with the Owner's privileges. A diff may not ADD any of these
# (counted against the old text, so existing uses in a file it extends do not refuse it).
DANGEROUS = [re.compile(p) for p in (
    r"\bsubprocess\b", r"\bos\.(system|popen|exec\w*|spawn\w*|startfile|remove|unlink|rmdir|rename|replace)\b",
    r"\bshutil\.(rmtree|move|copy\w*)\b", r"\bsocket\b", r"\burllib\b", r"\brequests\b", r"\bhttp\.client\b",
    r"\bctypes\b", r"\beval\s*\(", r"\bexec\s*\(", r"__import__", r"\bimportlib\b", r"\bexpanduser\b",
    r"Path\.home\b", r"[A-Za-z]:[\\/]", r"~[\\/]", r"\bUSERPROFILE\b", r"\bHOME\b", r"\.claude\b",
    r"child_process", r"\bos\.homedir\b", r"\brequire\(\s*['\"](https?|net|child_process)['\"]",
    r"\bfs\.(rm|unlink|rename|writeFile|appendFile|mkdir)\w*\b", r"\bprocess\.env\b")]
MAX_FILES = 6
MAX_CHANGED_LINES = 400


def _norm(path: str) -> str:
    p = path.replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p


def path_refusal(path: str, old_text: str | None = None, new_text: str | None = None) -> str | None:
    p = _norm(path)
    low = p.lower()
    if p in DENIED_EXACT:
        return f"{p}: the loop's fixed core or one of its judges"
    if p.startswith("/") or ".." in p.split("/") or ":" in p:
        return f"{p}: not a plain repo-relative path"
    if not p.startswith(ALLOWED_PREFIXES):
        return f"{p}: outside the allowlist {ALLOWED_PREFIXES}"
    for tok in DENIED_TOKENS:
        if tok in low:
            return f"{p}: names a control ('{tok}')"
    if p.startswith("hooks/"):
        for text in (old_text, new_text):
            if text and BLOCKING_HOOK_RE.search(text):
                return f"{p}: a blocking hook (can refuse a call)"
    return None


def dangerous_refusal(path: str, old_text: str | None, new_text: str | None) -> str | None:
    if not new_text:
        return None
    for rx in DANGEROUS:
        if len(rx.findall(new_text)) > len(rx.findall(old_text or "")):
            return f"{_norm(path)}: adds `{rx.pattern}` -- agent-written code runs with the Owner's privileges"
    return None


def diff_refusal(changes: list) -> str | None:
    """changes: [{path, status (A/M/D/R...), old_text, new_text, lines, binary}] for one proposal."""
    if not changes:
        return "empty diff"
    if len(changes) > MAX_FILES:
        return f"{len(changes)} files > {MAX_FILES}"
    total = sum(int(c.get("lines") or 0) for c in changes)
    if total > MAX_CHANGED_LINES:
        return f"{total} changed lines > {MAX_CHANGED_LINES}"
    for c in changes:
        st = str(c.get("status") or "M")[:1]
        if st not in ("A", "M"):
            return f"{c['path']}: status {st} (only add/modify allowed; no delete, rename or mode change)"
        if c.get("binary"):
            return f"{c['path']}: binary content is not allowed"
        why = path_refusal(c["path"], c.get("old_text"), c.get("new_text")) or \
            dangerous_refusal(c["path"], c.get("old_text"), c.get("new_text"))
        if why:
            return why
    return None


# ---------------------------------------------------------------- landing
# Branches the loop may land on. Another branch checked out in the shared checkout -> no landing (PENDING_MERGE).
LAND_BRANCHES = ("refs/heads/main", "refs/heads/feature/knowledge-acquisition")

# ---------------------------------------------------------------- git commands
_FORBIDDEN_GIT = ("push", "rebase", "reset", "clean", "filter-branch", "reflog", "gc", "prune", "remote", "fetch",
                  "pull", "config", "tag", "stash")


def git_refusal(args: list) -> str | None:
    """Every git invocation of the loop passes here. No publication, no history rewrite."""
    words = [str(a) for a in args]
    if not words:
        return "empty git command"
    sub = words[0]
    if sub in _FORBIDDEN_GIT:
        return f"git {sub} is forbidden to the loop"
    if any(w in ("--force", "-f", "--force-with-lease") for w in words) and sub != "worktree":
        return f"git {sub} with force is forbidden"
    if sub == "update-ref" and not (len(words) == 4 and words[1] in LAND_BRANCHES):
        return "update-ref must be a compare-and-swap on a landing branch: update-ref <ref> <new> <old>"
    if sub == "branch" and any(w in ("-D", "-d", "--delete", "-m", "-M") for w in words) \
            and not all(w.startswith("si/") for w in words[2:]):
        return "only the loop's own si/* branches may be deleted"
    return None


# ---------------------------------------------------------------- rectify floor
REVERT_RATIO_FLOOR = 1.5      # params may make reverting MORE eager (lower), never less
REVERT_RATIO_MIN = 1.2
REVERT_ABS_MIN = 5.0
MEASURE_MIN_DAYS = 3
MEASURE_MIN_SESSIONS = 10
MEASURE_MAX_DAYS = 14
VALIDATE_RATIO = 0.7
RETIRE_AFTER_REVERTS = 2

# ---------------------------------------------------------------- self-tuning bounds
BOUNDS = {
    "min_score": (5.0, 500.0),
    "kind_weight": (0.25, 4.0),
    "revert_ratio": (REVERT_RATIO_MIN, REVERT_RATIO_FLOOR),
    "baseline_days": (3, 14),
}
BENCH_DAYS = 30
MAX_APPLIES_PER_DAY = 1
AGENT_TIMEOUT_S = 20 * 60
GATE_TIMEOUT_S = 900          # test_self_improve_unattended alone took 315 s on the loaded host (2026-11-22)
SELF_SUITE = "tools/test_self_improve_unattended.py"
# Kinds whose fix is structurally a control, data entry or host action: never attempted.
NEVER_KINDS = ("host-stall", "owner-corrections", "repeated-failure", "hook-block")
# Always run before a merge and before keeping an applied change.
REGRESSION_BLOCK = (
    "tools/test_self_improve_unattended.py",
    "tools/test_analyze_transcripts.py",
    "tools/test_reader_robustness.py",
)


def clamp(name: str, value: float) -> float:
    lo, hi = BOUNDS[name]
    return max(lo, min(hi, value))


def clamp_params(p: dict) -> dict:
    """Bounded copy. Any malformed value falls back to its default rather than crashing the cycle."""
    p = p if isinstance(p, dict) else {}

    def num(key, default, kind=float):
        try:
            return kind(p.get(key, default))
        except (TypeError, ValueError):
            return default
    out = {"min_score": clamp("min_score", num("min_score", 20.0)),
           "revert_ratio": clamp("revert_ratio", num("revert_ratio", REVERT_RATIO_FLOOR)),
           "baseline_days": int(clamp("baseline_days", num("baseline_days", 7, int)))}
    weights = {}
    for k, v in (p.get("kind_weights") or {}).items() if isinstance(p.get("kind_weights"), dict) else []:
        try:
            if k not in NEVER_KINDS:
                weights[str(k)] = clamp("kind_weight", float(v))
        except (TypeError, ValueError):
            continue
    out["kind_weights"] = weights
    b = p.get("benched") if isinstance(p.get("benched"), dict) else {}
    out["benched"] = {str(k): str(v) for k, v in b.items()}
    return out


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="self-improve fixed core")
    ap.add_argument("--pin", action="store_true", help="Owner only: pin the current core hashes")
    a = ap.parse_args(argv)
    if a.pin:
        print(pin(), end="")
        return 0
    why = integrity()
    print(why or "OK: core matches its pin")
    return 1 if why else 0


if __name__ == "__main__":
    sys.exit(main())
