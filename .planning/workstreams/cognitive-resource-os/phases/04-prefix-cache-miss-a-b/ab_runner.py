#!/usr/bin/env python3
"""ab_runner.py -- read-only evidence runner for Phase 4 (prefix cache-miss A/B, GEX44).

Composes tools/tis_observed.py for every transcript read (session lookup, dedupe, project
keys) and modules/secret_firewall/redactor.py for any text that might leave this process.
It never re-implements transcript parsing, dedupe or project-key derivation, and it never
prints model reply text. Only `--live` spends subscription quota; every other mode
(--selftest, --env-check, --auth-check, --fingerprint, --readout, --evidence-lines) makes
zero model calls.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import inspect
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

# .../04-prefix-cache-miss-a-b/ab_runner.py -> parents[5] is the repo/worktree root:
# 0 phases/04-.../ (self.parent), 1 phases/, 2 cognitive-resource-os/, 3 workstreams/,
# 4 .planning/, 5 repo root. Same depth as Phase 2's by_entrypoint.py (WR-04 pattern).
THIS_FILE = Path(__file__).resolve()
ROOT = THIS_FILE.parents[5]

# Populated by _ensure_tools_importable(), never at module-import time (WR-04): a bare
# `import ab_runner` must not print or sys.exit.
T = redact_for_log = None


def _ensure_tools_importable() -> None:
    global T, redact_for_log
    if T is not None:
        return
    if not (ROOT / "tools" / "tis_observed.py").is_file():
        print(json.dumps({"state": "UNMEASURED", "reason": "repo root not found"}))
        sys.exit(2)
    sys.path.insert(0, str(ROOT / "tools"))
    sys.path.insert(0, str(ROOT))
    import tis_observed as _T
    from modules.secret_firewall.redactor import redact_for_log as _redact_for_log
    T, redact_for_log = _T, _redact_for_log


# ---------------------------------------------------------------------------
# Constants (Pre-registered design)
# ---------------------------------------------------------------------------

SCRATCH_ROOT = Path("/tmp/claude-1000/cro-p04-ab")
PROMPT = "Reply with the single word OK."
MODEL_ARG = "haiku"
RUN_ORDER = ("A1", "A2", "B1", "B2")
RUN_TIMEOUT_S = 240
BLOCKING_ENV = (
    "CLAUDE_CODE_OAUTH_TOKEN",
    "CLAUDE_CONFIG_DIR",
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
    "CLAUDE_CODE_USE_FOUNDRY",
)
AUTH_KEYS = (
    "loggedIn", "authMethod", "apiProvider", "apiKeySource",
    "subscriptionType", "forcedLoginMethod", "projectsDirectory", "configDirectory",
)

passes = fails = 0


def _ok(gate, ev):
    global passes
    passes += 1
    print(f"  [PASS] {gate}: {ev}")


def _fail(gate, ev):
    global fails
    fails += 1
    print(f"  [FAIL] {gate}: {ev}")


def check(gate, cond, ev):
    (_ok if cond else _fail)(gate, ev)


def _utcnow_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

def env_check(environ: dict) -> dict:
    """Never includes a value -- names only."""
    anthropic_names = sorted(k for k in environ if k.startswith("ANTHROPIC_") and environ.get(k))
    blocking_names = sorted(k for k in BLOCKING_ENV if environ.get(k))
    scrubbed_names = sorted(k for k in environ if k.startswith("CLAUDE") and k not in BLOCKING_ENV)
    return {
        "ANTHROPIC_API_KEY": "SET" if environ.get("ANTHROPIC_API_KEY") else "UNSET",
        "anthropic_env_names": anthropic_names,
        "blocking_env_names": blocking_names,
        "scrubbed_env_names": scrubbed_names,
        "home": environ.get("HOME"),
        "blocked": bool(anthropic_names) or bool(blocking_names),
    }


def scrubbed_env(environ: dict) -> dict:
    """Raises before stripping -- a blocked environment can never become a launch env."""
    if env_check(environ)["blocked"]:
        raise ValueError("environment is blocked: an ANTHROPIC_* or BLOCKING_ENV name is present")
    return {k: v for k, v in environ.items() if not k.startswith("CLAUDE")}


# ---------------------------------------------------------------------------
# argv
# ---------------------------------------------------------------------------

def build_argv(exe, arm: str, sid: str, mcp_file) -> list:
    argv = [str(exe), "-p", PROMPT, "--model", MODEL_ARG, "--session-id", str(sid),
            "--output-format", "stream-json", "--verbose"]
    if arm == "B":
        argv += ["--strict-mcp-config", "--mcp-config", str(mcp_file)]
    return argv


def render_argv(arm: str) -> str:
    return shlex.join(build_argv("EXE", arm, "SID", SCRATCH_ROOT / "empty-mcp.json"))


# ---------------------------------------------------------------------------
# stream-json init parsing
# ---------------------------------------------------------------------------

def parse_init(stdout_text: str) -> dict:
    for line in (stdout_text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(obj, dict) and obj.get("type") == "system" and obj.get("subtype") == "init":
            tools = obj.get("tools") or []
            tools = [t for t in tools if isinstance(t, str)]
            mcp_servers_raw = obj.get("mcp_servers") or []
            mcp_tool_names = [t for t in tools if t.startswith("mcp__")]
            tools_sha256 = hashlib.sha256("\n".join(sorted(tools)).encode("utf-8")).hexdigest()
            server_pairs = sorted(
                (s.get("name"), s.get("status")) for s in mcp_servers_raw if isinstance(s, dict)
            )
            mcp_tools_by_server: dict = {}
            for name in mcp_tool_names:
                parts = name.split("__")
                if len(parts) >= 3:
                    server = parts[1]
                    mcp_tools_by_server[server] = mcp_tools_by_server.get(server, 0) + 1
            return {
                "present": True,
                "session_id": obj.get("session_id"),
                "model": obj.get("model"),
                "apiKeySource": obj.get("apiKeySource"),
                "tools_n": len(tools),
                "mcp_tools_n": len(mcp_tool_names),
                "tools_sha256": tools_sha256,
                "mcp_servers": [list(p) for p in server_pairs],
                "mcp_tools_by_server": mcp_tools_by_server,
            }
    return {"present": False}


# ---------------------------------------------------------------------------
# launch
# ---------------------------------------------------------------------------

def launch(exe, argv: list, cwd, env: dict, timeout_s: int) -> dict:
    start_utc = _utcnow_iso()
    proc = subprocess.Popen(
        argv, cwd=str(cwd), env=env, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        start_new_session=True,
    )
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            stdout, stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            stdout, stderr = proc.communicate()
    end_utc = _utcnow_iso()
    rc = proc.returncode
    stderr = stderr or ""
    stderr_bytes = len(stderr.encode("utf-8"))
    stderr_head = None
    if rc != 0:
        first_line = next((l for l in stderr.splitlines() if l.strip()), "")
        _ensure_tools_importable()
        stderr_head = redact_for_log(first_line)[:200]
    return {
        "rc": rc,
        "timed_out": timed_out,
        "start_utc": start_utc,
        "end_utc": end_utc,
        "stderr_bytes": stderr_bytes,
        "stderr_head": stderr_head,
        "init": parse_init(stdout or ""),
    }


# ---------------------------------------------------------------------------
# transcript lookup
# ---------------------------------------------------------------------------

def locate_transcript(projects_dir, sid: str, init_sid) -> dict:
    projects_dir = Path(projects_dir)
    matches = sorted(projects_dir.glob(f"*/{sid}.jsonl"))
    sid_source = "preassigned"
    used_sid = sid
    if not matches and init_sid and init_sid != sid:
        matches = sorted(projects_dir.glob(f"*/{init_sid}.jsonl"))
        sid_source = "init"
        used_sid = init_sid
    if not matches:
        sid_source = "NONE"
        used_sid = None
    path = matches[0] if len(matches) == 1 else None
    path_rel = None
    project_key = None
    if len(matches) == 1:
        project_key = matches[0].parent.name
        path_rel = f"{project_key}/{matches[0].name}"
    return {
        "matches": len(matches),
        "sid_source": sid_source,
        "session_id": used_sid,
        "path": path,
        "path_rel": path_rel,
        "project_key": project_key,
    }


def predicted_project_key(cwd) -> str:
    _ensure_tools_importable()
    return T.project_key(Path(cwd).resolve())


# ---------------------------------------------------------------------------
# read_run (composes tis_observed only)
# ---------------------------------------------------------------------------

def read_run(path) -> dict:
    _ensure_tools_importable()
    path = Path(path)
    s = T.read_session(path)
    all_calls = list(T.iter_calls([path.parent], include_subagents=False))
    calls = [c for c in all_calls if c.get("session_id") == path.stem]
    first_call_raw = calls[0] if calls else None

    result = {
        "state": s.state,
        "entrypoint": s.entrypoint,
        "calls": s.calls,
        "models": s.models,
        "subagent_files": s.subagent_files,
        "first_call": None,
        "last_call_ts": None,
        "tis_consistency": None,
    }

    if first_call_raw is not None:
        usage = first_call_raw.get("usage") or {}
        cc_split = usage.get("cache_creation")
        cc_5m = cc_1h = None
        if isinstance(cc_split, dict):
            cc_5m = cc_split.get("ephemeral_5m_input_tokens")
            cc_1h = cc_split.get("ephemeral_1h_input_tokens")
        input_tokens = usage.get("input_tokens") or 0
        cache_creation = usage.get("cache_creation_input_tokens") or 0
        cache_read = usage.get("cache_read_input_tokens") or 0
        context = s.first_call_context
        result["first_call"] = {
            "model": first_call_raw.get("model"),
            "ts": first_call_raw.get("ts"),
            "input_tokens": input_tokens,
            "cache_creation_input_tokens": cache_creation,
            "cache_creation_5m": cc_5m,
            "cache_creation_1h": cc_1h,
            "cache_read_input_tokens": cache_read,
            "context": context,
        }
        consistency = (cache_read == (s.first_call_cache_read or 0)) and (
            (context is not None) and (input_tokens + cache_creation + cache_read == context)
        )
        result["tis_consistency"] = bool(consistency)

    all_ts = [c.get("ts") for c in calls if c.get("ts")]
    result["last_call_ts"] = max(all_ts) if all_ts else None
    return result


def reuse_share(first_call):
    if not first_call:
        return None
    context = first_call.get("context")
    if not context or context <= 0:
        return None
    cache_read = first_call.get("cache_read_input_tokens") or 0
    return round(cache_read / context, 6)


# ---------------------------------------------------------------------------
# auth
# ---------------------------------------------------------------------------

def auth_check(exe, env: dict, projects_dir) -> dict:
    proc = subprocess.run(
        [str(exe), "auth", "status", "--json"], stdin=subprocess.DEVNULL,
        capture_output=True, text=True, env=env, timeout=30,
    )
    rc = proc.returncode
    try:
        data = json.loads(proc.stdout)
    except (json.JSONDecodeError, ValueError):
        data = {}
    fields = {k: data.get(k) for k in AUTH_KEYS}
    logged_in = fields.get("loggedIn")
    auth_method = fields.get("authMethod")
    api_key_source = fields.get("apiKeySource")
    subscription_type = fields.get("subscriptionType")
    if (logged_in is True and auth_method == "claude.ai" and api_key_source is None
            and isinstance(subscription_type, str) and subscription_type):
        credentials_type = "claudeAiOauth"
    else:
        if logged_in is not True:
            reason = "loggedIn"
        elif auth_method != "claude.ai":
            reason = "authMethod"
        elif api_key_source is not None:
            reason = "apiKeySource"
        else:
            reason = "subscriptionType"
        credentials_type = f"NOT_OAUTH ({reason})"
    projects_dir_match = fields.get("projectsDirectory") == str(projects_dir)
    return {
        "rc": rc,
        "fields": fields,
        "credentials_type": credentials_type,
        "projects_dir_match": projects_dir_match,
    }


# ---------------------------------------------------------------------------
# fake claude (selftest fixture only)
# ---------------------------------------------------------------------------

_FAKE_CLAUDE_SRC = r'''#!/usr/bin/env python3
"""Fake claude for ab_runner.py's selftest. Never invoked outside a TemporaryDirectory."""
import json, os, re, sys, time


def main():
    argv = sys.argv[1:]
    if "--version" in argv:
        print("9.9.9 (Fake)")
        return 0
    if argv[:2] == ["auth", "status"]:
        out = {
            "loggedIn": True,
            "authMethod": os.environ.get("FAKE_AUTH_METHOD", "claude.ai"),
            "apiProvider": "firstParty",
            "subscriptionType": "max",
            "projectsDirectory": os.environ.get("FAKE_PROJECTS_DIR", ""),
            "configDirectory": "x",
            "email": "FIXTURE-EMAIL-SENTINEL",
            "orgId": "FIXTURE-ORG-SENTINEL",
            "orgName": "FIXTURE-ORG-SENTINEL",
        }
        print(json.dumps(out))
        return 0

    sid = None
    if "--session-id" in argv:
        i = argv.index("--session-id")
        sid = argv[i + 1] if i + 1 < len(argv) else None

    log_path = os.environ.get("FAKE_LOG")
    if log_path:
        rec = {"argv": argv, "env_names": sorted(os.environ.keys()), "cwd": os.getcwd()}
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")

    fixture = {}
    fixture_path = os.environ.get("FAKE_FIXTURE")
    if fixture_path and os.path.isfile(fixture_path):
        with open(fixture_path, encoding="utf-8") as fh:
            all_fx = json.load(fh)
        fixture = all_fx.get(sid, {}) if sid else {}

    sleep_s = fixture.get("sleep_s") or 0
    if sleep_s:
        time.sleep(sleep_s)

    projects_dir = os.environ.get("FAKE_PROJECTS_DIR")
    if projects_dir:
        key = re.sub(r"[^A-Za-z0-9]", "-", os.getcwd())
        d = os.path.join(projects_dir, key)
        os.makedirs(d, exist_ok=True)
        entrypoint = fixture.get("entrypoint", "sdk-cli")
        usage = fixture.get("usage", {})
        model = fixture.get("model", "claude-haiku-fake")
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        lines = [json.dumps({"type": "user", "entrypoint": entrypoint, "message": {"content": "x"}})]
        msg = {"id": "fake-msg-1", "model": model, "usage": usage}
        line_obj = {"type": "assistant", "message": msg, "requestId": "fake-req-1", "timestamp": ts}
        lines.append(json.dumps(line_obj))
        lines.append(json.dumps(line_obj))
        tpath = os.path.join(d, (sid or "unknown") + ".jsonl")
        with open(tpath, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")

    init = fixture.get("init", True)
    if init:
        tools = fixture.get("tools", [])
        mcp_servers = fixture.get("mcp_servers", [])
        init_event = {
            "type": "system", "subtype": "init", "cwd": os.getcwd(), "session_id": sid,
            "tools": tools, "mcp_servers": mcp_servers,
            "model": fixture.get("model", "claude-haiku-fake"),
            "apiKeySource": "none",
        }
        print(json.dumps(init_event))
    print(json.dumps({"type": "assistant",
                       "message": {"content": [{"type": "text", "text": "FAKE-REPLY-SENTINEL"}]}}))
    print(json.dumps({"type": "result", "result": "FAKE-REPLY-SENTINEL"}))
    return fixture.get("rc", 0)


if __name__ == "__main__":
    sys.exit(main())
'''


def _write_fake_claude(dirpath: Path) -> Path:
    p = Path(dirpath) / "fake_claude.py"
    p.write_text(_FAKE_CLAUDE_SRC, encoding="utf-8")
    p.chmod(0o755)
    return p


def _clean_base_env() -> dict:
    return {k: v for k, v in os.environ.items()
            if not k.startswith("ANTHROPIC_") and k not in BLOCKING_ENV}


def _bare_env() -> dict:
    """Base environ with every ANTHROPIC_* and every CLAUDE* name stripped, so a test can
    add back exactly the names it means to test -- the executor's own session already
    carries several non-blocking CLAUDE* coupling variables (CLAUDECODE,
    CLAUDE_CODE_ENTRYPOINT, ...) that would otherwise leak into an "only these names"
    assertion."""
    return {k: v for k, v in os.environ.items()
            if not k.startswith("ANTHROPIC_") and not k.startswith("CLAUDE")}


def _run_self_subprocess(args: list, env: dict, timeout: int = 30):
    return subprocess.run([sys.executable, str(THIS_FILE)] + args, env=env,
                           capture_output=True, text=True, timeout=timeout)


# ---------------------------------------------------------------------------
# selftest
# ---------------------------------------------------------------------------

def selftest() -> int:
    global passes, fails
    passes = fails = 0
    _ensure_tools_importable()

    # S0 (WR-04): a bare `import ab_runner` in a fresh subprocess must not print or
    # sys.exit. Checked in a subprocess since this process already imported the module.
    proc = subprocess.run(
        [sys.executable, "-c",
         f"import sys; sys.path.insert(0, {str(THIS_FILE.parent)!r}); import ab_runner"],
        capture_output=True, text=True, timeout=30,
    )
    s0 = proc.returncode == 0 and proc.stdout == "" and proc.stderr == ""
    check("S0", s0, f"rc={proc.returncode} stdout={proc.stdout!r} stderr={proc.stderr!r}")

    # S1: build_argv / render_argv shape.
    argv_a = build_argv("EXE", "A", "SID-A", "/tmp/does-not-matter/empty-mcp.json")
    expect_a = ["EXE", "-p", PROMPT, "--model", "haiku", "--session-id", "SID-A",
                "--output-format", "stream-json", "--verbose"]
    argv_b = build_argv("EXE", "B", "SID-B", "/tmp/mcp/empty-mcp.json")
    expect_b = expect_a[:6] + ["SID-B"] + expect_a[7:]
    # rebuild expect_b cleanly instead of slicing expect_a (session id differs)
    expect_b = ["EXE", "-p", PROMPT, "--model", "haiku", "--session-id", "SID-B",
                "--output-format", "stream-json", "--verbose",
                "--strict-mcp-config", "--mcp-config", "/tmp/mcp/empty-mcp.json"]
    render_a = render_argv("A")
    render_b = render_argv("B")
    s1 = (argv_a == expect_a and argv_b == expect_b
          and "EXE" in render_a and "SID" in render_a
          and "EXE" in render_b and "SID" in render_b)
    check("S1", s1, f"argv_a={argv_a} argv_b={argv_b} render_a={render_a!r} render_b={render_b!r}")

    # S2: env_check / scrubbed_env cases.
    base = _clean_base_env()
    bare = _bare_env()
    s2_parts = []

    nonblocking_env = dict(bare)
    nonblocking_env.update({"CLAUDECODE": "FAKE-1", "CLAUDE_CODE_SESSION_ID": "FAKE-SESS",
                             "CLAUDE_EFFORT": "FAKE-LOW"})
    ec_nb = env_check(nonblocking_env)
    s2_parts.append(("nonblocking-env-check", ec_nb["blocked"] is False
                      and ec_nb["scrubbed_env_names"] == sorted(
                          ["CLAUDECODE", "CLAUDE_CODE_SESSION_ID", "CLAUDE_EFFORT"])))
    rc_nb = _run_self_subprocess(["--env-check"], nonblocking_env)
    try:
        nb_json = json.loads(rc_nb.stdout)
    except (json.JSONDecodeError, ValueError):
        nb_json = {}
    s2_parts.append(("nonblocking-subprocess", rc_nb.returncode == 0
                      and nb_json.get("blocked") is False
                      and nb_json.get("scrubbed_env_names") == sorted(
                          ["CLAUDECODE", "CLAUDE_CODE_SESSION_ID", "CLAUDE_EFFORT"])))

    scrub_nb = scrubbed_env(nonblocking_env)
    s2_parts.append(("scrubbed-strips-claude", not any(k.startswith("CLAUDE") for k in scrub_nb)
                      and "HOME" in scrub_nb and scrub_nb.get("PATH") == base.get("PATH")))

    confdir_env = dict(bare)
    confdir_env["CLAUDE_CONFIG_DIR"] = "/tmp/FAKE-CONFIG-DIR"
    rc_cd = _run_self_subprocess(["--env-check"], confdir_env)
    try:
        cd_json = json.loads(rc_cd.stdout)
    except (json.JSONDecodeError, ValueError):
        cd_json = {}
    s2_parts.append(("confdir-blocked", rc_cd.returncode == 3
                      and cd_json.get("blocked") is True
                      and cd_json.get("blocking_env_names") == ["CLAUDE_CONFIG_DIR"]
                      and cd_json.get("anthropic_env_names") == []
                      and "CLAUDE_CONFIG_DIR" not in (cd_json.get("scrubbed_env_names") or [])))

    oauth_env = dict(bare)
    oauth_env["CLAUDE_CODE_OAUTH_TOKEN"] = "FAKE-OAUTH-TOKEN-VALUE"
    rc_oauth = _run_self_subprocess(["--env-check"], oauth_env)
    s2_parts.append(("oauth-token-blocked", rc_oauth.returncode == 3))

    apikey_env = dict(bare)
    apikey_env["ANTHROPIC_API_KEY"] = "FAKE-ANTHROPIC-API-KEY-VALUE"
    rc_apikey = _run_self_subprocess(["--env-check"], apikey_env)
    s2_parts.append(("api-key-blocked", rc_apikey.returncode == 3))

    raised = False
    try:
        scrubbed_env(confdir_env)
    except ValueError:
        raised = True
    s2_parts.append(("scrubbed-env-raises", raised))

    s2 = all(ok for _, ok in s2_parts)
    check("S2", s2, "; ".join(f"{name}={ok}" for name, ok in s2_parts))

    with tempfile.TemporaryDirectory() as td_s:
        td = Path(td_s)
        fake = _write_fake_claude(td)
        projects_dir = td / "projects"
        projects_dir.mkdir()
        cwd_dir = td / "cwd"
        cwd_dir.mkdir()

        def run_fake(sid, fixture_by_sid, timeout_s=30, extra_env=None):
            fixture_path = td / f"fixture-{sid}.json"
            fixture_path.write_text(json.dumps(fixture_by_sid), encoding="utf-8")
            log_path = td / f"log-{sid}.jsonl"
            env = dict(base)
            env.update({
                "FAKE_LOG": str(log_path),
                "FAKE_FIXTURE": str(fixture_path),
                "FAKE_PROJECTS_DIR": str(projects_dir),
                "HOME": base.get("HOME", ""),
            })
            if extra_env:
                env.update(extra_env)
            argv = [sys.executable, str(fake), "-p", PROMPT, "--model", "haiku",
                    "--session-id", sid, "--output-format", "stream-json", "--verbose"]
            res = launch(sys.executable, argv, cwd_dir, env, timeout_s)
            return res, log_path

        # ---- S3: locate_transcript ----
        sid3 = "3333333-cafe-aaaa-bbbb-000000000001"
        fixture3 = {sid3: {"usage": {"input_tokens": 5, "cache_creation_input_tokens": 100,
                                      "cache_creation": {"ephemeral_5m_input_tokens": 100,
                                                          "ephemeral_1h_input_tokens": 0},
                                      "cache_read_input_tokens": 20, "output_tokens": 3},
                            "model": "claude-haiku-fake", "tools": ["Bash", "Read"],
                            "mcp_servers": [], "rc": 0, "entrypoint": "sdk-cli"}}
        res3, _log3 = run_fake(sid3, fixture3)
        own_key = re.sub(r"[^A-Za-z0-9]", "-", str(cwd_dir))
        predicted = predicted_project_key(cwd_dir)
        # decoy: a different session id under the same project dir
        decoy_path = projects_dir / own_key / "decoy-9999.jsonl"
        decoy_path.write_text("{}\n", encoding="utf-8")
        loc3 = locate_transcript(projects_dir, sid3, res3["init"].get("session_id"))
        two_dirs_projects = td / "projects-two"
        two_dirs_projects.mkdir()
        (two_dirs_projects / "keyA").mkdir()
        (two_dirs_projects / "keyB").mkdir()
        (two_dirs_projects / "keyA" / f"{sid3}.jsonl").write_text("{}\n", encoding="utf-8")
        (two_dirs_projects / "keyB" / f"{sid3}.jsonl").write_text("{}\n", encoding="utf-8")
        loc3_dup = locate_transcript(two_dirs_projects, sid3, None)
        loc3_fallback = locate_transcript(projects_dir, "sid-not-preassigned",
                                           res3["init"].get("session_id"))
        s3 = (loc3["matches"] == 1 and loc3["sid_source"] == "preassigned"
              and loc3["project_key"] == own_key == predicted
              and loc3_dup["matches"] == 2 and loc3_dup["path"] is None
              and loc3_fallback["sid_source"] == "init"
              and loc3_fallback["session_id"] == sid3)
        check("S3", s3, f"loc3={loc3} dup_matches={loc3_dup['matches']} "
                         f"fallback_source={loc3_fallback['sid_source']}")

        # ---- S4: read_run via tis_observed ----
        path4 = loc3["path"]
        run4 = read_run(path4)
        s = T.read_session(path4)
        s4 = (run4["state"] == "MEASURED" and run4["entrypoint"] == "sdk-cli"
              and run4["calls"] == 1
              and run4["first_call"]["input_tokens"] == 5
              and run4["first_call"]["cache_creation_input_tokens"] == 100
              and run4["first_call"]["cache_creation_5m"] == 100
              and run4["first_call"]["cache_creation_1h"] == 0
              and run4["first_call"]["cache_read_input_tokens"] == 20
              and run4["first_call"]["context"] == s.first_call_context
              and run4["tis_consistency"] is True
              and reuse_share(run4["first_call"]) == round(20 / s.first_call_context, 6))
        check("S4", s4, f"run4={run4} first_call_context(tis)={s.first_call_context}")

        # ---- S5: launch record carries init + no reply sentinel ----
        init3 = res3["init"]
        s5 = (init3["present"] is True and init3["tools_n"] == 2 and init3["mcp_tools_n"] == 0
              and init3["mcp_servers"] == []
              and init3["tools_sha256"] == hashlib.sha256(
                  "\n".join(sorted(["Bash", "Read"])).encode()).hexdigest()
              and "FAKE-REPLY-SENTINEL" not in json.dumps(res3)
              and "FAKE-REPLY-SENTINEL" not in json.dumps(run4))
        check("S5", s5, f"init3={init3}")

        # ---- S6: auth_check ----
        fake_projects_dir_str = str(projects_dir)
        auth_env = dict(base)
        auth_env["FAKE_PROJECTS_DIR"] = fake_projects_dir_str
        auth_env.pop("FAKE_AUTH_METHOD", None)
        res6 = auth_check(fake, auth_env, projects_dir)
        dumped6 = json.dumps(res6)
        auth_env_bad = dict(auth_env)
        auth_env_bad["FAKE_AUTH_METHOD"] = "api_key"
        res6_bad = auth_check(fake, auth_env_bad, projects_dir)
        s6 = (res6["credentials_type"] == "claudeAiOauth" and res6["projects_dir_match"] is True
              and set(res6["fields"].keys()) == set(AUTH_KEYS)
              and "FIXTURE-EMAIL-SENTINEL" not in dumped6
              and "FIXTURE-ORG-SENTINEL" not in dumped6
              and res6_bad["credentials_type"].startswith("NOT_OAUTH"))
        check("S6", s6, f"res6={res6} res6_bad_type={res6_bad['credentials_type']}")

    print(f"ABRUN_SELFTEST_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--env-check", action="store_true")
    ap.add_argument("--auth-check", action="store_true")
    ap.add_argument("--claude")
    ap.add_argument("--fingerprint", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    if args.env_check:
        ec = env_check(os.environ)
        print(json.dumps(ec))
        return 3 if ec["blocked"] else 0

    if args.auth_check:
        if not args.claude:
            print("ERROR: --auth-check requires --claude PATH", file=sys.stderr)
            return 2
        _ensure_tools_importable()
        try:
            env = scrubbed_env(os.environ)
        except ValueError as exc:
            print(json.dumps({"error": str(exc)}))
            return 3
        result = auth_check(args.claude, env, T.PROJECTS_DIR)
        print(json.dumps(result))
        ok = result["credentials_type"] == "claudeAiOauth" and result["projects_dir_match"]
        return 0 if ok else 3

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
