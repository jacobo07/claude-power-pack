#!/usr/bin/env python3
"""gex44_env_preflight -- may a mission launch in this GEX44 env? READY, NOT_READY(reason) or UNMEASURABLE.

Pillar B of the incremental-cognition program. The a7 loop (96+ dead relaunches) happened in an env whose
credentials were zeroed and whose PP install predated the breaker; nothing measured either. This asks the four
questions of the frozen rule, each as its own check, read-only:

    auth          credentials expiry (never the token): shared reader + predicate with pillar C
    pp_install    the install contains PP_COMMIT_FLOOR (the rules version) and its required files
    hooks         every registered hook script exists, parses and loads under the env's own node
    interpreters  env node inside the vendored engine range, python >= PYTHON_MIN, and the executables
                  probed through tools/gsd_x_runtime_preflight.js (CALLED, not forked)

Three outcomes, kept apart (exit 0 / 1 / 2). UNMEASURABLE is never READY: a check that could not judge says so.

Read-only by construction: env.sh is parsed statically and never sourced; every spawned process is an argv list
(no shell) run with a throwaway HOME and GIT_OPTIONAL_LOCKS=0; the claude binary is never executed; credentials
leave the reader as instants and booleans only.

    python3 tools/gex44_env_preflight.py --env-root ~/a7-env --json
    python3 tools/gex44_env_preflight.py --current --checks auth,pp_install
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import provider_breaker  # noqa: E402 -- one credentials reader and one expiry predicate, shared with pillar C

READY = "READY"
NOT_READY = "NOT_READY"
UNMEASURABLE = "UNMEASURABLE"
EXIT = {READY: 0, NOT_READY: 1, UNMEASURABLE: 2}

# The closed set of refusals. Anything a check cannot place here is UNMEASURABLE, never a new reason.
REASONS = ("auth_expired", "auth_missing", "pp_install_stale", "hooks_broken", "interpreter_unsupported")
# Non-refusing observations: reported beside a READY (or any) verdict, never a reason to refuse.
FINDINGS = ("access_token_lapsed_refreshable", "hooks_foreign_env", "install_modified", "hook_entries_unjudged")

# The first PP commit whose install both parks an auth refusal (plan 02-01: tools/gsd_mission.py +
# tools/provider_breaker.py) and carries the pre-launch gate (plan 02-03: tools/mission_launch_gate.py, which is
# also the one place a renewal inherits a quarantine and a NOT_READY env refuses). An install that does not contain
# it relaunches a dead-login worker forever, or launches into a NOT_READY env. Raising the floor edits this
# constant plus PP_REQUIRED_FILES when the new floor adds a required file -- plan 02-04 raised it from the 02-01
# commit 5962571c to the 02-03 commit.
PP_COMMIT_FLOOR = "60e7947dcf3cf0f9c660e412ec6276a8b2922f99"
PP_REQUIRED_FILES = ("tools/gsd_mission.py", "tools/provider_breaker.py", "tools/mission_launch_gate.py")
PYTHON_MIN = (3, 9)
PROBE_TIMEOUT_S = 15
BUDGET_S = 120
MAX_HOOK_SCRIPTS = 200

CHECK_ORDER = ("auth", "pp_install", "hooks", "interpreters")
# Variable NAMES that stand in for a credentials file. Only the name is ever looked at.
AUTH_ENV_NAMES = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN")
_KEPT_VALUES = ("HOME", "PATH", "CPP_GIT_EXE", "CPP_CLAUDE_EXE", "CPP_NODE_EXE")
_EXPORT_RE = re.compile(r"^\s*export\s+([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def _iso(ts) -> str | None:
    if ts is None:
        return None
    return _dt.datetime.fromtimestamp(float(ts), _dt.timezone.utc).isoformat(timespec="seconds")


def _result(check: str, state: str, why: str, *, reasons=(), findings=(), detail=None) -> dict:
    return {"check": check, "state": state, "reasons": list(reasons), "why": why,
            "findings": list(findings), "detail": detail or {}}


# --------------------------------------------------------------------------- env description
def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def env_from_root(env_root) -> dict:
    """Describe an env root from its env.sh, STATICALLY: `export NAME=VALUE` lines only, never sourced and
    never executed (a value containing a command substitution is recorded by name and left unresolved).
    Raises ValueError (the CLI maps it to UNMEASURABLE) when env.sh is missing or exports no HOME."""
    root = Path(env_root)
    env_sh = root / "env.sh"
    try:
        text = env_sh.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"env.sh unreadable ({exc.__class__.__name__}): {env_sh}") from None
    names: list[str] = []
    values: dict[str, str] = {}
    for line in text.splitlines():
        m = _EXPORT_RE.match(line)
        if not m:
            continue
        name, raw = m.group(1), _unquote(m.group(2))
        if name not in names:
            names.append(name)
        if name not in _KEPT_VALUES or "$(" in raw or "`" in raw:
            continue
        subs = [("${PATH}", os.environ.get("PATH", "")), ("$PATH", os.environ.get("PATH", ""))]
        if values.get("HOME"):
            subs += [("${HOME}", values["HOME"]), ("$HOME", values["HOME"])]
        for ref, repl in subs:
            raw = raw.replace(ref, repl)
        values[name] = raw
    home = values.get("HOME")
    if not home:
        raise ValueError(f"env.sh exports no HOME: {env_sh}")
    path = values.get("PATH", os.environ.get("PATH", ""))
    return {
        "source": "env.sh", "env_root": str(root), "home": home, "path": path,
        "install": str(Path(home) / ".claude" / "skills" / "claude-power-pack"),
        "git": values.get("CPP_GIT_EXE") or shutil.which("git", path=path),
        "node": values.get("CPP_NODE_EXE") or shutil.which("node", path=path),
        "python": shutil.which("python3", path=path),
        "claude": values.get("CPP_CLAUDE_EXE") or shutil.which("claude", path=path),
        "env_var_names": names,
    }


def env_current() -> dict:
    """The running process as an env: this worktree's PP install, this PATH, this interpreter."""
    path = os.environ.get("PATH", "")
    return {
        "source": "process", "env_root": None, "home": str(Path.home()), "path": path,
        "install": str(Path(__file__).resolve().parent.parent),
        "git": os.environ.get("CPP_GIT_EXE") or shutil.which("git"),
        "node": os.environ.get("CPP_NODE_EXE") or shutil.which("node"),
        "python": sys.executable,
        "claude": os.environ.get("CPP_CLAUDE_EXE") or shutil.which("claude"),
        "env_var_names": sorted(os.environ),
    }


# --------------------------------------------------------------------------- checks
def check_auth(env: dict, now: float) -> dict:
    """Auth readiness from credentials EXPIRY, never the token: the pillar-C reader and predicate."""
    cred = provider_breaker.credentials_state(env["home"])
    detail = {"expires_at": _iso(cred.get("expires_at")), "refresh_expires_at": _iso(cred.get("refresh_expires_at")),
              "mtime": _iso(cred.get("mtime")), "refresh_token_present": bool(cred.get("refresh_token"))}
    if not cred.get("readable"):
        if cred.get("why") == "missing":
            via = [n for n in AUTH_ENV_NAMES if n in env.get("env_var_names", ())]
            if via:
                return _result("auth", UNMEASURABLE, f"no credentials file; {', '.join(via)} is exported "
                               "(name only, the value is never read) so a login may exist that this cannot judge",
                               detail=detail)
            return _result("auth", NOT_READY, "no credentials file and no API-key variable exported",
                           reasons=["auth_missing"], detail=detail)
        return _result("auth", UNMEASURABLE, f"credentials file unreadable: {cred.get('why')}", detail=detail)
    expired = provider_breaker.credentials_expired(cred, now)
    if expired is None:
        return _result("auth", UNMEASURABLE, "credentials carry no judgeable expiresAt", detail=detail)
    if expired:
        return _result("auth", NOT_READY, "access token expired and not refreshable "
                       f"(expiresAt {detail['expires_at']})", reasons=["auth_expired"], detail=detail)
    exp = cred.get("expires_at")
    if exp is not None and exp <= now:
        return _result("auth", READY, f"access token lapsed {detail['expires_at']} but refreshable until "
                       f"{detail['refresh_expires_at']}", findings=["access_token_lapsed_refreshable"],
                       detail=detail)
    return _result("auth", READY, f"access token valid until {detail['expires_at']}", detail=detail)


# --------------------------------------------------------------------------- probe plumbing
_DEADLINE: list = [None]   # monotonic instant after which every probe refuses to start (set by run())


class _Sandbox:
    """One throwaway HOME per check: nothing a probe does can land in the env's own HOME, git never takes an
    optional lock, and the child environment is built from scratch (no inherited credentials variables)."""

    def __init__(self, path: str):
        self._td = tempfile.TemporaryDirectory(prefix="envpf-probe-")
        self.home = self._td.name
        self.env = {"PATH": path or "", "HOME": self.home, "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"}

    def run(self, argv, cwd=None, timeout=None):
        """(returncode | None when the program could not start, stdout, stderr). Raises TimeoutError when a
        probe exceeds its bound or the run's budget is spent -- the caller turns that into UNMEASURABLE."""
        dl = _DEADLINE[0]
        if dl is not None and time.monotonic() > dl:
            raise TimeoutError("budget exhausted")
        limit = PROBE_TIMEOUT_S if timeout is None else timeout
        try:
            p = subprocess.run([str(a) for a in argv], capture_output=True, text=True, errors="replace",
                               env=self.env, cwd=cwd or self.home, timeout=limit)
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"{os.path.basename(str(argv[0]))} timed out after {limit}s") from None
        except OSError as exc:
            return None, "", exc.__class__.__name__
        return p.returncode, p.stdout, p.stderr

    def version_of(self, exe: str):
        """The first output line of `exe --version`, None when it cannot run or exits non-zero."""
        rc, out, err = self.run([exe, "--version"])
        text = (out or err).strip().splitlines()
        return text[0].strip() if rc == 0 and text else None

    def close(self) -> None:
        self._td.cleanup()


_VER_RE = re.compile(r"\s*v?(\d+)\.(\d+)\.(\d+)\s*")
_ALT_RE = re.compile(r"(\^|>=)?\s*v?(\d+)\.(\d+)\.(\d+)")


def satisfies(version, rng):
    """True / False / None (cannot judge) for `version` against an npm-style range of `||` alternatives of
    `^X.Y.Z`, `>=X.Y.Z` or exact `X.Y.Z`. Anything else, in the version or in any alternative, is None: a range
    this cannot read must surface as UNMEASURABLE, never as a guess in either direction."""
    m = _VER_RE.fullmatch(str(version)) if version is not None else None
    if m is None or not isinstance(rng, str) or not rng.strip():
        return None
    v = tuple(int(x) for x in m.groups())
    verdicts = []
    for alt in rng.split("||"):
        a = _ALT_RE.fullmatch(alt.strip())
        if a is None:
            return None
        base = tuple(int(x) for x in a.groups()[1:])
        op = a.group(1)
        if op == ">=":
            verdicts.append(v >= base)
        elif op == "^":
            hi = (base[0] + 1, 0, 0) if base[0] > 0 else (0, base[1] + 1, 0) if base[1] > 0 else (0, 0, base[2] + 1)
            verdicts.append(base <= v < hi)
        else:
            verdicts.append(v == base)
    return any(verdicts)


def _under(path: str, roots) -> bool:
    p = os.path.normpath(path)
    return any(p == r or p.startswith(r.rstrip("/") + "/") for r in (os.path.normpath(x) for x in roots if x))


# --------------------------------------------------------------------------- rules version
def _is_ancestor(sbx: _Sandbox, git: str, install: str, floor: str):
    """True / False / None: is `floor` an ancestor of (or equal to) HEAD. `git merge-base --is-ancestor`
    exits 0 yes, 1 no, anything else is a failure to ask."""
    rc, _, _ = sbx.run([git, "merge-base", "--is-ancestor", floor, "HEAD"], cwd=install)
    return True if rc == 0 else False if rc == 1 else None


def check_pp_install(env: dict, floor=None) -> dict:
    """Rules version: the PP install is a git checkout whose HEAD descends from the floor commit and which
    carries the required files. The floor's presence also proves repo identity: a foreign repository cannot
    contain this sha. Local modifications are a finding, never a refusal."""
    floor = floor or PP_COMMIT_FLOOR
    install, git = env.get("install"), env.get("git")
    detail = {"install": install, "floor": floor}
    if not re.fullmatch(r"[0-9a-f]{40}", floor or ""):
        return _result("pp_install", UNMEASURABLE, "the floor is not a full 40-hex commit id", detail=detail)
    if not install or not os.path.isdir(install):
        return _result("pp_install", NOT_READY, f"no PP install at {install}", reasons=["pp_install_stale"],
                       detail=detail)
    if not git or not os.path.isfile(git):
        return _result("pp_install", UNMEASURABLE, "no git executable to ask", detail=detail)
    sbx = _Sandbox(env.get("path"))
    try:
        rc, out, _ = sbx.run([git, "rev-parse", "--show-toplevel"], cwd=install)
        if rc != 0 or os.path.realpath(out.strip()) != os.path.realpath(install):
            return _result("pp_install", UNMEASURABLE, "the install is not the root of a git checkout",
                           detail=detail)
        rc, head, _ = sbx.run([git, "rev-parse", "HEAD"], cwd=install)
        if rc != 0:
            return _result("pp_install", UNMEASURABLE, "git could not resolve HEAD", detail=detail)
        detail["head"] = head.strip()
        rc, br, _ = sbx.run([git, "rev-parse", "--abbrev-ref", "HEAD"], cwd=install)
        detail["branch"] = br.strip() if rc == 0 else None
        rc, _, _ = sbx.run([git, "rev-parse", "--verify", "--quiet", f"{floor}^{{commit}}"], cwd=install)
        if rc not in (0, 1):
            return _result("pp_install", UNMEASURABLE, "git could not look up the floor commit", detail=detail)
        problems = []
        if rc == 1:
            problems.append(f"floor {floor[:8]} is not in this install's history (head {detail['head'][:8]})")
        else:
            anc = _is_ancestor(sbx, git, install, floor)
            if anc is None:
                return _result("pp_install", UNMEASURABLE, "git could not compare HEAD with the floor",
                               detail=detail)
            if not anc:
                problems.append(f"head {detail['head'][:8]} does not contain the floor {floor[:8]}")
        missing = [f for f in PP_REQUIRED_FILES if not (Path(install) / f).is_file()]
        if missing:
            problems.append("required files missing: " + ", ".join(missing))
        findings = []
        rc, st, _ = sbx.run([git, "--no-optional-locks", "status", "--porcelain", "--untracked-files=no"],
                            cwd=install)
        if rc == 0 and st.strip():
            rows = st.splitlines()
            findings.append("install_modified")
            detail["modified_count"] = len(rows)
            detail["modified_first"] = [r[3:] for r in rows[:5]]
        if problems:
            return _result("pp_install", NOT_READY, "; ".join(problems), reasons=["pp_install_stale"],
                           findings=findings, detail=detail)
        return _result("pp_install", READY, f"head {detail['head'][:8]} contains the floor {floor[:8]}",
                       findings=findings, detail=detail)
    except TimeoutError as exc:
        return _result("pp_install", UNMEASURABLE, str(exc), detail=detail)
    finally:
        sbx.close()


# --------------------------------------------------------------------------- hook health
_SCRIPT_SUFFIXES = (".js", ".cjs", ".mjs", ".py", ".sh")
_JS_SUFFIXES = (".js", ".cjs", ".mjs")
_VERSIONED = ("node", "python", "python3", "bash", "sh")
_SHELL_MARKS = (";", "|", "&&", "$(", "`")
_CHAINS_ONELINER = ("const m=require(process.argv[1]);"
                    "console.log(JSON.stringify((m.CHAIN_NAMES||[]).concat(m.EVENT_NAMES||[])))")


def _script_exists(path: str) -> bool:
    return os.path.isfile(path)


def _expand(token: str, home: str) -> str:
    if token == "~" or token.startswith("~/"):
        token = home + token[1:]
    return token.replace("${HOME}", home).replace("$HOME", home)


def _hook_entries(settings: dict) -> list:
    out = []
    hooks = settings.get("hooks") if isinstance(settings, dict) else None
    if not isinstance(hooks, dict):
        return out
    for event, items in hooks.items():
        for item in items if isinstance(items, list) else []:
            for hk in (item.get("hooks") if isinstance(item, dict) and isinstance(item.get("hooks"), list) else []):
                if isinstance(hk, dict) and hk.get("type", "command") == "command":
                    out.append((event, hk))
    return out


def check_hooks(env: dict) -> dict:
    """Hook health: every registered command hook resolves to an interpreter and a script that exist; JS
    scripts parse under `node --check`; hook-dispatcher.js loads and knows every `--event=` registered against
    it. Hook commands are never run: only `--version`, `--check <path>` and a fixed `-e require` one-liner are
    spawned, as argv lists. A command that is a shell construct is reported unjudged, not executed."""
    home = env["home"]
    settings_path = Path(home) / ".claude" / "settings.json"
    detail: dict = {"settings": str(settings_path)}
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return _result("hooks", NOT_READY, "no settings.json: no hooks are registered", reasons=["hooks_broken"],
                       detail=detail)
    except (OSError, ValueError) as exc:
        return _result("hooks", UNMEASURABLE, f"settings.json unreadable: {exc.__class__.__name__}", detail=detail)
    entries = _hook_entries(settings)
    detail["entries"] = len(entries)
    if not entries:
        return _result("hooks", NOT_READY, "settings.json registers no command hooks", reasons=["hooks_broken"],
                       detail=detail)
    root = env.get("env_root") or home
    allowed = [root, "/usr", "/bin", "/opt"]
    sbx = _Sandbox(env.get("path"))
    broken: list[str] = []
    unmeasured: list[str] = []
    foreign: set[str] = set()
    interpreters: dict[str, bool] = {}     # path -> runs
    js_checked: dict[tuple, bool] = {}     # (node, script) -> parses
    dispatchers: dict[tuple, set | None] = {}
    all_scripts: set[str] = set()
    judged = unjudged = 0
    cap_hit = False
    try:
        for event, hk in entries:
            cmd, args = hk.get("command"), hk.get("args")
            try:
                tokens = shlex.split(cmd) if isinstance(cmd, str) else []
            except ValueError:
                tokens = []
            if (not tokens or any(m in cmd for m in _SHELL_MARKS) or cmd.lstrip().startswith("if ")):
                unjudged += 1
                continue
            tokens = [_expand(t, home) for t in tokens + [str(a) for a in (args if isinstance(args, list) else [])]]
            first = tokens[0]
            if first.endswith(_SCRIPT_SUFFIXES):
                interp_path, rest = None, tokens
            else:
                if "$" in first:
                    unjudged += 1
                    continue
                interp_path = first if "/" in first else shutil.which(first, path=env.get("path") or "")
                rest = tokens[1:]
            scripts = [t for t in rest if t.endswith(_SCRIPT_SUFFIXES)]
            if any("$" in s or not os.path.isabs(s) for s in scripts):
                unjudged += 1
                continue
            judged += 1
            if interp_path is not None or not first.endswith(_SCRIPT_SUFFIXES):
                if not interp_path or not os.path.isfile(interp_path) or not os.access(interp_path, os.X_OK):
                    broken.append(f"{event}: interpreter {first} not found")
                    continue
                if not _under(interp_path, allowed):
                    foreign.add(os.path.dirname(interp_path))
                base = os.path.basename(interp_path)
                if base in _VERSIONED or base.startswith("python"):
                    if interp_path not in interpreters:
                        interpreters[interp_path] = sbx.version_of(interp_path) is not None
                    if not interpreters[interp_path]:
                        broken.append(f"{event}: interpreter {interp_path} does not run (--version failed)")
                        continue
            node = interp_path if interp_path and os.path.basename(interp_path) == "node" else env.get("node")
            for script in scripts:
                all_scripts.add(script)
                if not _under(script, allowed):
                    foreign.add(os.path.dirname(script))
                if not _script_exists(script):
                    broken.append(f"{event}: missing script {script}")
                    continue
                if script.endswith(_JS_SUFFIXES):
                    if not node:
                        unmeasured.append(f"{event}: no node to check {os.path.basename(script)}")
                        continue
                    key = (node, script)
                    if key not in js_checked:
                        if len(js_checked) >= MAX_HOOK_SCRIPTS:
                            cap_hit = True
                            continue
                        try:
                            rc, _, _ = sbx.run([node, "--check", script])
                        except TimeoutError as exc:
                            unmeasured.append(f"{event}: {exc}")
                            continue
                        js_checked[key] = rc == 0
                        if rc != 0:
                            broken.append(f"{event}: {os.path.basename(script)} fails node --check")
                    elif not js_checked[key]:
                        broken.append(f"{event}: {os.path.basename(script)} fails node --check")
                if os.path.basename(script) == "hook-dispatcher.js":
                    wanted = [t.split("=", 1)[1] for t in rest if t.startswith("--event=")]
                    if node and wanted:
                        dkey = (node, script)
                        if dkey not in dispatchers:
                            try:
                                rc, out, _ = sbx.run([node, "-e", _CHAINS_ONELINER, script])
                            except TimeoutError as exc:
                                unmeasured.append(f"{event}: {exc}")
                                continue
                            try:
                                dispatchers[dkey] = set(json.loads(out)) if rc == 0 else None
                            except ValueError:
                                dispatchers[dkey] = None
                        names = dispatchers[dkey]
                        if names is None:
                            broken.append(f"{event}: hook-dispatcher.js does not load under {os.path.basename(node)}")
                        else:
                            for w in wanted:
                                if w not in names:
                                    broken.append(f"{event}: dispatcher has no chain/event {w}")
    except TimeoutError as exc:
        unmeasured.append(str(exc))
    finally:
        sbx.close()
    detail.update({"judged": judged, "unjudged": unjudged, "scripts_distinct": len(all_scripts),
                   "scripts_checked": len(js_checked), "script_cap_hit": cap_hit,
                   "interpreters": sorted(interpreters), "broken": broken[:10], "broken_count": len(broken),
                   "foreign_roots": sorted(foreign)[:5], "unmeasured": unmeasured[:5]})
    findings = []
    if foreign:
        findings.append("hooks_foreign_env")
    if unjudged:
        findings.append("hook_entries_unjudged")
    if broken:
        return _result("hooks", NOT_READY, f"{len(broken)} broken hook(s), first: {broken[0]}",
                       reasons=["hooks_broken"], findings=findings, detail=detail)
    if unmeasured:
        return _result("hooks", UNMEASURABLE, f"could not finish: {unmeasured[0]}", findings=findings, detail=detail)
    if judged == 0:
        return _result("hooks", UNMEASURABLE, f"{unjudged} hook command(s) registered and none could be judged",
                       findings=findings, detail=detail)
    note = f"; {unjudged} unjudged" if unjudged else ""
    return _result("hooks", READY, f"{judged} hook(s) judged healthy{note}", findings=findings, detail=detail)


# --------------------------------------------------------------------------- interpreters
def js_manifest(env: dict) -> dict:
    """The requirement manifest handed to the existing JS engine (called, not forked). Executables are
    spawned by the engine with a trivial probe; the claude binary is only checked for existence -- the
    preflight never executes it."""
    def exe(rid, name, args):
        return {"id": rid, "kind": "executable", "name": name, "probeArgs": args}
    return {"runtimeRequirements": {"requirements": [
        exe("posix-shell", "sh", ["-c", "exit 0"]),
        exe("env-node", env.get("node") or "node", ["--version"]),
        exe("python3", env.get("python") or "python3", ["--version"]),
        exe("git", env.get("git") or "git", ["--version"]),
        {"id": "claude-cli", "kind": "file", "path": env.get("claude") or "<unresolved:claude>"},
    ]}}


def run_js_engine(manifest: dict, env: dict):
    """Run tools/gsd_x_runtime_preflight.js on `manifest` -> (returncode, parsed stdout | None). Raises
    TimeoutError past the probe bound and RuntimeError when no node exists to run it."""
    node = env.get("node") or shutil.which("node")
    if not node:
        raise RuntimeError("no node to run the JS preflight engine")
    lib = Path(env["home"]) / ".claude" / "gsd-core" / "bin" / "lib"
    sbx = _Sandbox(env.get("path"))
    try:
        mpath = Path(sbx.home) / "manifest.json"
        mpath.write_text(json.dumps(manifest), encoding="utf-8")
        rc, out, _ = sbx.run([node, str(Path(__file__).resolve().parent / "gsd_x_runtime_preflight.js"),
                              "--manifest", str(mpath), "--gsd-lib", str(lib), "--json"], timeout=PROBE_TIMEOUT_S * 2)
        try:
            parsed = json.loads(out)
        except ValueError:
            parsed = None
        return rc, parsed
    finally:
        sbx.close()


def _judge_js(rc, parsed):
    """("ok" | "refuse" | "unmeasured", text). Only a self-consistent engine answer counts: exit 0 with
    SATISFIED, or exit 1 with UNMET (naming the UNMET ids). Anything else is the instrument failing."""
    verdict = parsed.get("verdict") if isinstance(parsed, dict) else None
    if rc == 0 and verdict == "SATISFIED":
        return "ok", "executables probed"
    if rc == 1 and verdict == "UNMET":
        ids = [r.get("id") for r in parsed.get("results", []) if isinstance(r, dict) and r.get("state") == "UNMET"]
        return "refuse", "executables not runnable here: " + (", ".join(str(i) for i in ids) or "unnamed")
    return "unmeasured", f"JS engine gave exit {rc} verdict {verdict}"


def check_interpreters(env: dict, version_of=None, js_runner=None) -> dict:
    """Interpreters: the env's node inside the vendored engine range, python >= PYTHON_MIN, and the
    executables the launch needs, probed through the JS engine. A measured refusal outranks an unmeasured
    sub-probe (the unmeasured ones are listed in detail)."""
    sbx = _Sandbox(env.get("path"))
    vo = version_of or sbx.version_of
    refusals: list[str] = []
    unmeasured: list[str] = []
    notes: list[str] = []
    versions: dict[str, str] = {}   # what was measured, kept even when the range cannot be judged
    try:
        pkg = Path(env["install"]) / "vendor" / "genesis-suite" / "package.json"
        try:
            rng = json.loads(pkg.read_text(encoding="utf-8"))["engines"]["node"]
        except (OSError, ValueError, KeyError, TypeError):
            rng = None
        node = env.get("node")
        if not node:
            refusals.append("no node on the env PATH")
        else:
            try:
                nv = vo(node)
            except TimeoutError as exc:
                nv = False
                unmeasured.append(f"node: {exc}")
            if nv is None:
                refusals.append(f"node at {node} does not run")
            elif nv is not False:
                versions["node"] = nv
                if rng is None:
                    unmeasured.append(f"engine range unreadable ({pkg})")
                else:
                    sat = satisfies(nv, rng)
                    if sat is None:
                        unmeasured.append(f"node {nv} against range {rng!r}: range not understood")
                    elif not sat:
                        refusals.append(f"node {nv} is outside {rng}")
                    else:
                        notes.append(f"node {nv} in {rng}")
        py = env.get("python")
        if not py:
            refusals.append("no python3 on the env PATH")
        else:
            try:
                pv = vo(py)
            except TimeoutError as exc:
                pv = False
                unmeasured.append(f"python: {exc}")
            m = re.search(r"(\d+)\.(\d+)", pv) if isinstance(pv, str) else None
            if pv is None:
                refusals.append(f"python at {py} does not run")
            elif pv is not False and m is None:
                unmeasured.append(f"python version not understood: {pv!r}")
            elif m is not None:
                versions["python"] = pv
                got = (int(m.group(1)), int(m.group(2)))
                if got < PYTHON_MIN:
                    refusals.append(f"python {got[0]}.{got[1]} is below {PYTHON_MIN[0]}.{PYTHON_MIN[1]}")
                else:
                    notes.append(f"python {got[0]}.{got[1]}")
        runner = js_runner or run_js_engine
        try:
            rc, parsed = runner(js_manifest(env), env)
            kind, text = _judge_js(rc, parsed)
        except (TimeoutError, RuntimeError, OSError) as exc:
            kind, text = "unmeasured", f"JS engine: {exc}"
        if kind == "refuse":
            refusals.append(text)
        elif kind == "unmeasured":
            unmeasured.append(text)
        else:
            notes.append(text)
    finally:
        sbx.close()
    detail = {"node_range": rng, "versions": versions, "refusals": refusals, "unmeasured": unmeasured}
    if refusals:
        return _result("interpreters", NOT_READY, "; ".join(refusals), reasons=["interpreter_unsupported"],
                       detail=detail)
    if unmeasured:
        return _result("interpreters", UNMEASURABLE, "; ".join(unmeasured), detail=detail)
    return _result("interpreters", READY, "; ".join(notes), detail=detail)


# --------------------------------------------------------------------------- aggregate / run
def aggregate(checks: list[dict]) -> dict:
    """Verdict over the checks: any measured NOT_READY -> NOT_READY; else any UNMEASURABLE -> UNMEASURABLE;
    else READY. This differs on purpose from the JS activation aggregate (gsd_x_runtime_preflight.js), where
    UNMEASURABLE outranks UNMET because its question is "is the host satisfied" and an unjudged requirement
    leaves that open. Here the question is "is there a measured reason not to launch", and a measured refusal
    stands whatever was left unjudged; the unjudged checks are listed beside it, never dropped."""
    reasons = [r for r in REASONS if any(r in c.get("reasons", ()) for c in checks)]
    unmeasured = [{"check": c["check"], "why": c["why"]} for c in checks if c["state"] == UNMEASURABLE]
    verdict_unmeasured = bool(unmeasured)
    # A refusing check may itself have left sub-probes unjudged: list them beside the refusal.
    for c in checks:
        if c["state"] == NOT_READY:
            unmeasured += [{"check": c["check"], "why": w} for w in c.get("detail", {}).get("unmeasured", ())]
    findings: list[str] = []
    for c in checks:
        for f in c.get("findings", ()):
            if f not in findings:
                findings.append(f)
    if any(c["state"] == NOT_READY for c in checks):
        verdict = NOT_READY
    elif verdict_unmeasured or not checks:
        verdict = UNMEASURABLE
    else:
        verdict = READY
    return {"verdict": verdict, "reasons": reasons, "unmeasured": unmeasured, "findings": findings}


def _check_funcs() -> dict:
    return {"auth": lambda env, now: check_auth(env, now),
            "pp_install": lambda env, now: check_pp_install(env),
            "hooks": lambda env, now: check_hooks(env),
            "interpreters": lambda env, now: check_interpreters(env)}


def _paths_only(env: dict) -> dict:
    return {k: env.get(k) for k in ("source", "env_root", "home", "install", "node", "python", "git", "claude")}


def run(env: dict, now=None, checks=None) -> dict:
    """Run the named checks in canonical order (unknown names are UNMEASURABLE, never skipped). A check
    started after BUDGET_S has elapsed becomes UNMEASURABLE "budget exhausted"."""
    now = time.time() if now is None else float(now)
    wanted = list(checks) if checks else list(CHECK_ORDER)
    ordered = [c for c in CHECK_ORDER if c in wanted] + [c for c in wanted if c not in CHECK_ORDER]
    funcs = _check_funcs()
    started = time.monotonic()
    _DEADLINE[0] = started + BUDGET_S
    out: list[dict] = []
    try:
        for name in ordered:
            if time.monotonic() - started > BUDGET_S:
                out.append(_result(name, UNMEASURABLE, "budget exhausted"))
                continue
            fn = funcs.get(name)
            if fn is None:
                out.append(_result(name, UNMEASURABLE, f"unknown check: {name}"))
                continue
            try:
                out.append(fn(env, now))
            except Exception as exc:  # noqa: BLE001 -- an instrument crash is UNMEASURABLE, never READY
                out.append(_result(name, UNMEASURABLE, f"check raised {exc.__class__.__name__}"))
    finally:
        _DEADLINE[0] = None
    host = socket.gethostname()
    res = aggregate(out)
    res.update({"checks": out, "host": host, "plane": "gex44" if "gex44" in host.lower() else host,
                "checked_at": _iso(time.time()), "env": _paths_only(env)})
    return res


# --------------------------------------------------------------------------- CLI
def _render(res: dict) -> str:
    lines = [f"{c['state']:<12} {c['check']:<13} {c['why']}" for c in res["checks"]]
    lines.append(f"PREFLIGHT={res['verdict']} reasons={','.join(res['reasons']) or '-'}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--env-root", help="an env root holding env.sh (e.g. ~/a7-env)")
    grp.add_argument("--current", action="store_true", help="judge the running process")
    ap.add_argument("--checks", help="comma list of: " + ",".join(CHECK_ORDER))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--now", type=float, help="epoch seconds to judge expiry against (test seam)")
    args = ap.parse_args(argv)
    checks = [c.strip() for c in args.checks.split(",") if c.strip()] if args.checks else None
    try:
        env = env_current() if args.current else env_from_root(Path(args.env_root).expanduser())
    except ValueError as exc:
        res = {"verdict": UNMEASURABLE, "reasons": [], "unmeasured": [{"check": "env", "why": str(exc)}],
               "findings": [], "checks": [], "host": socket.gethostname(), "plane": None,
               "checked_at": _iso(time.time()), "env": {}}
        print(json.dumps(res, indent=2) if args.json else f"{UNMEASURABLE:<12} env           {exc}\n"
              f"PREFLIGHT={UNMEASURABLE} reasons=-")
        return EXIT[UNMEASURABLE]
    res = run(env, args.now, checks)
    print(json.dumps(res, indent=2) if args.json else _render(res))
    return EXIT[res["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
