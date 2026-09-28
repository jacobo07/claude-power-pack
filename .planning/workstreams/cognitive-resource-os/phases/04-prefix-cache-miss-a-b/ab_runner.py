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
# Task 2: RULES, validity, manipulation/variance, verdict, fingerprint
# ---------------------------------------------------------------------------

RULES = {
    "GAP_SUPPORT": 0.3,
    "B2_FLOOR": 0.5,
    "GAP_NULL": 0.1,
    "MISS_BAND": 0.5,
    "TTL_5M_BOUND_S": 240,
    "TTL_1H_BOUND_S": 3300,
    "REPLACEMENT_BUDGET": 0,
}


def _parse_iso(ts):
    if not ts:
        return None
    try:
        return dt.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def ttl_bound(first_call):
    if not first_call:
        return RULES["TTL_5M_BOUND_S"]
    cc_5m = first_call.get("cache_creation_5m")
    cc_1h = first_call.get("cache_creation_1h")
    if cc_1h is not None and cc_5m is not None and cc_1h > 0 and cc_5m == 0:
        return RULES["TTL_1H_BOUND_S"]
    return RULES["TTL_5M_BOUND_S"]


def _vr7_ok(prev_run, run):
    if not prev_run:
        return False
    prev_transcript = prev_run.get("transcript") or {}
    cur_transcript = run.get("transcript") or {}
    last_ts = prev_transcript.get("last_call_ts")
    cur_fc = cur_transcript.get("first_call") or {}
    cur_ts = cur_fc.get("ts")
    t1 = _parse_iso(last_ts)
    t2 = _parse_iso(cur_ts)
    if t1 is None or t2 is None:
        return False
    bound = ttl_bound(prev_transcript.get("first_call"))
    gap_s = (t2 - t1).total_seconds()
    if not (0 <= gap_s <= bound):
        return False
    return t1.astimezone().date() == t2.astimezone().date()


def run_validity(run, prev_run, ref_model) -> list:
    """Returns the sorted list of failed rule ids (VR1-VR7). A clean record returns []."""
    failed = []
    transcript = run.get("transcript") or {}
    fc = transcript.get("first_call") or {}

    if run.get("rc") != 0 or run.get("timed_out"):
        failed.append("VR1")

    if transcript.get("matches") != 1:
        failed.append("VR2")

    if transcript.get("state") != "MEASURED" or not fc.get("context"):
        failed.append("VR3")

    if transcript.get("entrypoint") != "sdk-cli":
        failed.append("VR4")

    model = fc.get("model") or ""
    if "haiku" not in model or (ref_model is not None and model != ref_model):
        failed.append("VR5")

    init = run.get("init") or {}
    if init.get("present"):
        aks = init.get("apiKeySource")
        if aks not in (None, "none"):
            failed.append("VR6")

    if run.get("index") == 2 and not _vr7_ok(prev_run, run):
        failed.append("VR7")

    return failed


def mcp_checks(runs):
    """Returns (M1, M2, vA, vA_detail)."""
    by_run = {r["run"]: r for r in runs}

    def init_of(run_id):
        r = by_run.get(run_id)
        if not r:
            return None
        init = r.get("init") or {}
        return init if init.get("present") else None

    b1, b2 = init_of("B1"), init_of("B2")
    if b1 is not None and b2 is not None:
        def _b_clean(b):
            return (b.get("mcp_servers") or []) == [] and (b.get("mcp_tools_n") or 0) == 0
        m1 = "PASS" if (_b_clean(b1) and _b_clean(b2)) else "FAIL"
    else:
        m1 = "UNKNOWN"

    a1, a2 = init_of("A1"), init_of("A2")
    a1_has = bool(a1 and (a1.get("mcp_servers") or []))
    a2_has = bool(a2 and (a2.get("mcp_servers") or []))
    if a1_has or a2_has:
        m2 = "PASS"
    elif a1 is not None and a2 is not None:
        m2 = "FAIL"
    else:
        m2 = "UNKNOWN"

    if a1 is not None and a2 is not None:
        diff = (a1.get("tools_sha256") != a2.get("tools_sha256")) or (
            sorted(tuple(p) for p in (a1.get("mcp_servers") or []))
            != sorted(tuple(p) for p in (a2.get("mcp_servers") or [])))
        vA = "YES" if diff else "NO"
        vA_detail = ("tools_sha256 or mcp_servers differ between A1 and A2" if diff
                     else "A1 and A2 init tools_sha256 and mcp_servers are identical")
    else:
        vA = "UNKNOWN"
        vA_detail = "an A init is missing"

    return m1, m2, vA, vA_detail


def verdict(metrics, invalid_ids, launches, complete, m1, m2):
    """Returns (label, reason, rule_fired). Implements R1-R8, first match wins (R1 is
    handled by the caller before metrics exist -- a guard/pre-check refusal)."""
    if invalid_ids or launches != 4 or not complete:
        return ("UNJUDGED",
                f"invalid: runs {sorted(invalid_ids)} launches={launches} complete={complete}",
                "R2")
    if m1 != "PASS":
        return ("UNJUDGED", "manipulation: Arm B MCP strip not confirmed", "R3")
    if m2 != "PASS":
        return ("UNJUDGED",
                "no MCP server in Arm A's default configuration; arms not differentiated", "R4")

    gap = metrics.get("gap")
    s_A2 = metrics.get("s_A2")
    s_B2 = metrics.get("s_B2")
    vA = metrics.get("vA")
    if gap is None or s_A2 is None or s_B2 is None:
        return ("UNJUDGED", "metrics incomplete", "R2")

    GAP_SUPPORT = RULES["GAP_SUPPORT"]
    B2_FLOOR = RULES["B2_FLOOR"]
    GAP_NULL = RULES["GAP_NULL"]
    MISS_BAND = RULES["MISS_BAND"]

    if gap >= GAP_SUPPORT and s_B2 >= B2_FLOOR and vA == "YES":
        return ("SUPPORTED", "gap_run2 >= 0.3, s_B2 >= 0.5, vA YES", "R5")
    if abs(gap) < GAP_NULL and s_A2 < MISS_BAND and s_B2 < MISS_BAND:
        return ("REFUTED", "both-miss: the miss persists with MCP stripped", "R6")
    if abs(gap) < GAP_NULL and vA == "YES":
        return ("REFUTED",
                "variance-without-miss: Arm A's MCP surface changed yet its run-2 reuse "
                "matched Arm B's", "R7")

    if abs(gap) < GAP_NULL:
        return ("UNJUDGED", "similar-reuse-variance-not-observed", "R8")
    if gap >= GAP_SUPPORT and s_B2 < B2_FLOOR:
        return ("UNJUDGED", "B2-below-floor", "R8")
    if gap >= GAP_SUPPORT and s_B2 >= B2_FLOOR and vA != "YES":
        return ("UNJUDGED", "gap-without-observed-variance", "R8")
    if GAP_NULL <= gap < GAP_SUPPORT:
        return ("UNJUDGED", "intermediate-gap", "R8")
    if gap <= -GAP_NULL:
        return ("UNJUDGED", "A-above-B", "R8")
    return ("UNJUDGED", "unclassified", "R8")


def runner_sha256() -> str:
    return hashlib.sha256(THIS_FILE.read_bytes()).hexdigest()


def rules_fingerprint() -> str:
    h = hashlib.sha256()
    h.update(json.dumps(RULES, sort_keys=True).encode("utf-8"))
    for fn in (verdict, run_validity, mcp_checks, ttl_bound, reuse_share):
        h.update(inspect.getsource(fn).encode("utf-8"))
    return h.hexdigest()


def assemble(result, projects_dir):
    """Shared readout for live() and readout(). Mutates and returns `result`."""
    _ensure_tools_importable()
    projects_dir = Path(projects_dir)
    runs = result.get("runs") or []
    by_run = {r["run"]: r for r in runs}

    for r in runs:
        sid = r.get("session_id")
        init = r.get("init") or {}
        init_sid = init.get("session_id")
        loc = locate_transcript(projects_dir, sid, init_sid)
        transcript = {k: v for k, v in loc.items() if k != "path"}
        path = loc.get("path")
        if path is not None:
            transcript.update(read_run(path))
        else:
            transcript.update({"state": None, "entrypoint": None, "calls": 0,
                                "models": {}, "subagent_files": 0, "first_call": None,
                                "last_call_ts": None, "tis_consistency": None})
        r["transcript"] = transcript
        r["reuse_share"] = reuse_share(transcript.get("first_call"))

    ref_model = None
    a1 = by_run.get("A1")
    if a1:
        ref_model = ((a1.get("transcript") or {}).get("first_call") or {}).get("model")

    for r in runs:
        prev_run = by_run.get(r["arm"] + "1") if r.get("index") == 2 else None
        failed = run_validity(r, prev_run, ref_model)
        r["validity"] = {"valid": not failed, "failed": failed}

    m1, m2, vA, vA_detail = mcp_checks(runs)

    def share_of(run_id):
        r = by_run.get(run_id)
        return r.get("reuse_share") if r else None

    s_A1, s_A2, s_B1, s_B2 = (share_of("A1"), share_of("A2"), share_of("B1"), share_of("B2"))

    def _delta(a, b):
        return round(b - a, 6) if a is not None and b is not None else None

    delta_A = _delta(s_A1, s_A2)
    delta_B = _delta(s_B1, s_B2)
    gap = _delta(s_A2, s_B2)
    delta_gap = round(delta_B - delta_A, 6) if delta_A is not None and delta_B is not None else None

    metrics = {
        "s_A1": round(s_A1, 6) if s_A1 is not None else None,
        "s_A2": round(s_A2, 6) if s_A2 is not None else None,
        "s_B1": round(s_B1, 6) if s_B1 is not None else None,
        "s_B2": round(s_B2, 6) if s_B2 is not None else None,
        "delta_A": delta_A, "delta_B": delta_B, "gap": gap, "delta_gap": delta_gap,
        "vA": vA, "vA_detail": vA_detail,
    }

    def _ttl_of(arm):
        r1 = by_run.get(arm + "1")
        r2 = by_run.get(arm + "2")
        if not r1 or not r2:
            return {"gap_s": None, "bound_s": None, "same_local_date": None}
        t1 = _parse_iso((r1.get("transcript") or {}).get("last_call_ts"))
        t2 = _parse_iso(((r2.get("transcript") or {}).get("first_call") or {}).get("ts"))
        gap_s = round((t2 - t1).total_seconds(), 3) if t1 and t2 else None
        bound_s = ttl_bound((r1.get("transcript") or {}).get("first_call"))
        same_date = (t1.astimezone().date() == t2.astimezone().date()) if t1 and t2 else None
        return {"gap_s": gap_s, "bound_s": bound_s, "same_local_date": same_date}

    ttl = {"A": _ttl_of("A"), "B": _ttl_of("B")}

    invalid_ids = [r["run"] for r in runs if not r["validity"]["valid"]]
    launches = len(runs)
    complete_data = launches == 4
    label, reason, rule = verdict(metrics, invalid_ids, launches, complete_data, m1, m2)

    result["launches"] = launches
    result["ttl"] = ttl
    result["manipulation"] = {"M1": m1, "M2": m2}
    result["metrics"] = metrics
    result["verdict"] = label
    result["verdict_reason"] = reason
    result["rule_fired"] = rule
    return result


def live(exe, exe_sha256, expect_runner_sha256, expect_fp, out,
         scratch_root=SCRATCH_ROOT, projects_dir=None, environ=None, sids=None,
         run_timeout_s=RUN_TIMEOUT_S):
    _ensure_tools_importable()
    environ = dict(os.environ) if environ is None else dict(environ)
    out = Path(out)
    scratch_root = Path(scratch_root)
    projects_dir = Path(projects_dir) if projects_dir is not None else T.PROJECTS_DIR

    ec = env_check(environ)
    if ec["blocked"]:
        print("REFUSED: G1 env_check blocked (an ANTHROPIC_* or BLOCKING_ENV name is present)")
        return 3
    if out.exists():
        print("REFUSED: G2 out already exists")
        return 3
    latch = scratch_root / "LIVE-LATCH"
    if latch.exists():
        print("REFUSED: G3 LIVE-LATCH already exists")
        return 3
    arm_a_dir = scratch_root / "armA"
    arm_b_dir = scratch_root / "armB"
    if arm_a_dir.exists() or arm_b_dir.exists():
        print("REFUSED: G4 armA or armB already exists")
        return 3
    try:
        actual_sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    except OSError as exc:
        print(f"REFUSED: G5 could not read claude binary: {exc}")
        return 3
    if actual_sha != exe_sha256:
        print("REFUSED: G5 claude binary sha256 mismatch")
        return 3
    if runner_sha256() != expect_runner_sha256 or rules_fingerprint() != expect_fp:
        print("REFUSED: G6 runner_sha256 or rules_fingerprint mismatch")
        return 3
    try:
        scrubbed = scrubbed_env(environ)
    except ValueError:
        print("REFUSED: G1 env_check blocked (scrubbed_env raised)")
        return 3
    auth = auth_check(exe, scrubbed, projects_dir)
    if auth["credentials_type"] != "claudeAiOauth" or not auth["projects_dir_match"]:
        print("REFUSED: G7 auth_check is not claudeAiOauth or projects dir mismatch")
        return 3

    if sids is None:
        sids = {r: str(uuid.uuid4()) for r in RUN_ORDER}
    for r in RUN_ORDER:
        sid = sids[r]
        existing = locate_transcript(projects_dir, sid, None)
        if existing["matches"] > 0:
            print(f"REFUSED: G8 session id for {r} already has a transcript")
            return 3

    try:
        version_proc = subprocess.run([str(exe), "--version"], stdin=subprocess.DEVNULL,
                                       capture_output=True, text=True, timeout=30)
        claude_version = (version_proc.stdout or "").strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        claude_version = f"UNKNOWN ({exc})"

    scratch_root.mkdir(parents=True, exist_ok=True)
    latch.write_text(_utcnow_iso(), encoding="utf-8")
    arm_a_dir.mkdir(parents=True, exist_ok=True)
    arm_b_dir.mkdir(parents=True, exist_ok=True)
    mcp_file = scratch_root / "empty-mcp.json"
    mcp_file.write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
    json.loads(mcp_file.read_text(encoding="utf-8"))  # validate it parses

    live_started_utc = _utcnow_iso()
    result = {
        "schema": "cro-p04-ab/1",
        "runner_sha256": runner_sha256(),
        "rules_fingerprint": rules_fingerprint(),
        "rules": dict(RULES),
        "claude": {"path": str(exe), "sha256": exe_sha256, "version": claude_version},
        "prompt": PROMPT,
        "model_arg": MODEL_ARG,
        "scratch_root": str(scratch_root),
        "projects_dir": str(projects_dir),
        "env": {"anthropic_env_names": ec["anthropic_env_names"],
                "blocking_env_names": ec["blocking_env_names"],
                "scrubbed_env_names": ec["scrubbed_env_names"]},
        "auth": {"fields": auth["fields"], "credentials_type": auth["credentials_type"],
                 "projects_dir_match": auth["projects_dir_match"]},
        "live_started_utc": live_started_utc,
        "complete": False,
        "runs": [],
    }
    out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    for r in RUN_ORDER:
        arm = r[0]
        index = int(r[1])
        sid = sids[r]
        cwd = arm_a_dir if arm == "A" else arm_b_dir
        print(f"LAUNCH {r} sid={sid}", flush=True)
        argv = build_argv(exe, arm, sid, mcp_file)
        launch_result = launch(exe, argv, cwd, scrubbed, run_timeout_s)
        run_record = {"run": r, "arm": arm, "index": index, "cwd": str(cwd), "session_id": sid,
                      "argv_display": render_argv(arm)}
        run_record.update(launch_result)
        result["runs"].append(run_record)
        out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    result["live_ended_utc"] = _utcnow_iso()
    assemble(result, projects_dir)
    result["complete"] = True
    result["completed_by"] = "live"
    out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"LIVE_DONE launches={result['launches']} verdict={result['verdict']} "
          f"rule={result['rule_fired']}")
    return 0


def readout(path, projects_dir=None, write=False):
    _ensure_tools_importable()
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    pd = Path(projects_dir) if projects_dir is not None else Path(data.get("projects_dir") or T.PROJECTS_DIR)
    was_complete = data.get("complete") is True

    prior = {k: data.get(k) for k in ("ttl", "manipulation", "metrics", "verdict",
                                       "verdict_reason", "rule_fired", "launches")}
    prior_runs = [{k: r.get(k) for k in ("transcript", "reuse_share", "validity")}
                  for r in data.get("runs", [])]

    recomputed = dict(data)
    recomputed["runs"] = [dict(r) for r in data.get("runs", [])]
    for r in recomputed["runs"]:
        r.pop("transcript", None)
        r.pop("reuse_share", None)
        r.pop("validity", None)
    assemble(recomputed, pd)

    if not was_complete:
        if not write:
            print("READOUT: INCOMPLETE")
            return 1
        recomputed["complete"] = True
        recomputed["completed_by"] = "readout"
        path.write_text(json.dumps(recomputed, indent=2, default=str), encoding="utf-8")
        print("READOUT: MATCH")
        return 0

    mismatches = []
    for key in ("ttl", "manipulation", "metrics", "verdict", "verdict_reason",
                "rule_fired", "launches"):
        if recomputed.get(key) != prior.get(key):
            mismatches.append(key)
    for i, r in enumerate(recomputed["runs"]):
        old = prior_runs[i] if i < len(prior_runs) else {}
        for key in ("transcript", "reuse_share", "validity"):
            if r.get(key) != old.get(key):
                mismatches.append(f"{r.get('run')}.{key}")

    if mismatches:
        print(f"READOUT: MISMATCH {mismatches}")
        return 1
    print("READOUT: MATCH")
    return 0


def evidence_lines(result) -> list:
    lines = []
    lines.append(f"launches: {result.get('launches')}")
    lines.append(f"runner_sha256_at_run: {result.get('runner_sha256')}")
    lines.append(f"rules_fingerprint_at_run: {result.get('rules_fingerprint')}")
    claude = result.get("claude") or {}
    lines.append(f"claude_at_run: {claude.get('path')} {claude.get('sha256')}")

    by_run = {r["run"]: r for r in result.get("runs", [])}
    for run_id in RUN_ORDER:
        r = by_run.get(run_id)
        if not r:
            continue
        transcript = r.get("transcript") or {}
        fc = transcript.get("first_call") or {}
        init = r.get("init") or {}
        validity = r.get("validity") or {}

        lines.append(f"{run_id}_session_id: {r.get('session_id')}")
        lines.append(f"{run_id}_sid_source: {transcript.get('sid_source', 'NONE')}")
        if transcript.get("path_rel"):
            predicted = predicted_project_key(r.get("cwd"))
            pk_match = "YES" if transcript.get("project_key") == predicted else "NO"
            lines.append(f"{run_id}_transcript: {transcript.get('path_rel')} "
                         f"(matches {transcript.get('matches')}, project_key_match {pk_match})")
        else:
            lines.append(f"{run_id}_transcript: NONE (matches {transcript.get('matches', 0)})")
        lines.append(f"{run_id}_rc: {r.get('rc')}")
        lines.append(f"{run_id}_timed_out: {'true' if r.get('timed_out') else 'false'}")
        lines.append(f"{run_id}_start_utc: {r.get('start_utc')}")
        lines.append(f"{run_id}_end_utc: {r.get('end_utc')}")
        lines.append(f"{run_id}_state: {transcript.get('state') or 'n/a'}")
        lines.append(f"{run_id}_entrypoint: {transcript.get('entrypoint') or 'n/a'}")
        lines.append(f"{run_id}_calls: {transcript.get('calls', 0)} (GEX44)")
        lines.append(f"{run_id}_model: {fc.get('model') or 'n/a'}")
        for key in ("input_tokens", "cache_read_input_tokens", "context"):
            val = fc.get(key, "n/a") if fc else "n/a"
            lines.append(f"{run_id}_first_call_{key}: {val} (GEX44)")
        cc = fc.get("cache_creation_input_tokens", "n/a") if fc else "n/a"
        cc5 = fc.get("cache_creation_5m") if fc else None
        cc1 = fc.get("cache_creation_1h") if fc else None
        if fc:
            lines.append(f"{run_id}_first_call_cache_creation_input_tokens: {cc} "
                         f"(5m {cc5 if cc5 is not None else 'n/a'} / "
                         f"1h {cc1 if cc1 is not None else 'n/a'}) (GEX44)")
        else:
            lines.append(f"{run_id}_first_call_cache_creation_input_tokens: n/a (GEX44)")
        rs = r.get("reuse_share")
        lines.append(f"{run_id}_reuse_share: {rs if rs is not None else 'n/a'} (GEX44)")
        if init.get("present"):
            servers = ", ".join(f"{n}:{s}" for n, s in (init.get("mcp_servers") or []))
            lines.append(f"{run_id}_init: tools {init.get('tools_n')}, "
                         f"mcp_tools {init.get('mcp_tools_n')}, mcp_servers [{servers}], "
                         f"apiKeySource {init.get('apiKeySource')}")
        else:
            lines.append(f"{run_id}_init: ABSENT")
        if validity.get("valid"):
            lines.append(f"{run_id}_valid: VALID")
        else:
            lines.append(f"{run_id}_valid: INVALID ({', '.join(validity.get('failed') or [])})")

    metrics = result.get("metrics") or {}
    for key, label in (("s_A1", "s_A1"), ("s_A2", "s_A2"), ("s_B1", "s_B1"), ("s_B2", "s_B2"),
                        ("delta_A", "delta_A"), ("delta_B", "delta_B"),
                        ("gap", "gap_run2"), ("delta_gap", "delta_gap")):
        v = metrics.get(key)
        lines.append(f"{label}: {v if v is not None else 'n/a'} (GEX44)")

    ttl = result.get("ttl") or {}
    for arm in ("A", "B"):
        t = ttl.get(arm) or {}
        lines.append(f"ttl_{arm}: gap_s {t.get('gap_s')} bound_s {t.get('bound_s')} "
                     f"same_local_date {t.get('same_local_date')}")

    vA = metrics.get("vA", "UNKNOWN")
    vA_detail = metrics.get("vA_detail", "")
    lines.append(f"vA: {vA} ({vA_detail})")

    manipulation = result.get("manipulation") or {}
    lines.append(f"M1: {manipulation.get('M1')}")
    lines.append(f"M2: {manipulation.get('M2')}")
    lines.append(f"comparison: run-2 against run-1 reuse in Arm A moved by {metrics.get('delta_A')}, "
                 f"in Arm B by {metrics.get('delta_B')}; the arms differ by "
                 f"gap_run2={metrics.get('gap')} in run-2 reuse, with vA={vA}.")

    lines.append(f"verdict: {result.get('verdict')} ({result.get('verdict_reason')})")
    lines.append(f"rule_fired: {result.get('rule_fired')}")
    return lines


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

    # ---- S7: run_validity (VR1-VR7) ----
    try:
        def _mk_run(index=1, run_id=None, rc=0, timed_out=False, matches=1, state="MEASURED",
                    entrypoint="sdk-cli", model="claude-haiku-fake", context=1000,
                    ts="2026-01-01T12:00:00Z", api_key_source="none", init_present=True):
            run_id = run_id or ("A1" if index == 1 else "A2")
            return {
                "run": run_id, "arm": run_id[0], "index": index,
                "rc": rc, "timed_out": timed_out,
                "init": {"present": init_present, "apiKeySource": api_key_source},
                "transcript": {
                    "matches": matches, "state": state, "entrypoint": entrypoint,
                    "first_call": {"model": model, "ts": ts, "context": context,
                                   "cache_read_input_tokens": 0,
                                   "cache_creation_5m": 1000, "cache_creation_1h": 0},
                    "last_call_ts": ts,
                },
            }

        ref = "claude-haiku-fake"
        clean1 = _mk_run(index=1, ts="2026-01-01T12:00:00Z")
        clean2 = _mk_run(index=2, run_id="A2", ts="2026-01-01T12:00:30Z")
        s7_clean1 = run_validity(clean1, None, ref) == []
        s7_clean2 = run_validity(clean2, clean1, ref) == []

        vr1a = _mk_run(index=1, rc=1)
        vr1b = _mk_run(index=1, timed_out=True)
        s7_vr1 = run_validity(vr1a, None, ref) == ["VR1"] and run_validity(vr1b, None, ref) == ["VR1"]

        vr2a = _mk_run(index=1, matches=0)
        vr2b = _mk_run(index=1, matches=2)
        s7_vr2 = run_validity(vr2a, None, ref) == ["VR2"] and run_validity(vr2b, None, ref) == ["VR2"]

        vr3 = _mk_run(index=1, state="MEASURED_ZERO", context=0)
        s7_vr3 = run_validity(vr3, None, ref) == ["VR3"]

        vr4 = _mk_run(index=1, entrypoint="cli")
        s7_vr4 = run_validity(vr4, None, ref) == ["VR4"]

        vr5a = _mk_run(index=1, model="claude-sonnet-fake")
        vr5b = _mk_run(index=1, model="claude-haiku-fake-OTHER")
        s7_vr5 = run_validity(vr5a, None, ref) == ["VR5"] and run_validity(vr5b, None, ref) == ["VR5"]

        vr6 = _mk_run(index=1, api_key_source="ANTHROPIC_API_KEY")
        s7_vr6 = run_validity(vr6, None, ref) == ["VR6"]

        vr7_over = _mk_run(index=2, run_id="A2", ts="2026-01-01T13:00:00Z")
        s7_vr7_over = run_validity(vr7_over, clean1, ref) == ["VR7"]

        vr7_neg = _mk_run(index=2, run_id="A2", ts="2026-01-01T11:59:00Z")
        s7_vr7_neg = run_validity(vr7_neg, clean1, ref) == ["VR7"]

        local_tz = dt.datetime.now().astimezone().tzinfo
        local_midnight = dt.datetime.now(local_tz).replace(hour=0, minute=0, second=0, microsecond=0)
        before = local_midnight - dt.timedelta(seconds=10)
        after = local_midnight + dt.timedelta(seconds=10)
        ts_before = before.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        ts_after = after.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        prev_midnight = _mk_run(index=1, ts=ts_before)
        vr7_date = _mk_run(index=2, run_id="A2", ts=ts_after)
        s7_vr7_date = run_validity(vr7_date, prev_midnight, ref) == ["VR7"]

        vr7_unknown = _mk_run(index=2, run_id="A2", ts=None)
        s7_vr7_unknown = run_validity(vr7_unknown, clean1, ref) == ["VR7"]

        s7 = all([s7_clean1, s7_clean2, s7_vr1, s7_vr2, s7_vr3, s7_vr4, s7_vr5, s7_vr6,
                  s7_vr7_over, s7_vr7_neg, s7_vr7_date, s7_vr7_unknown])
        check("S7", s7, f"clean1={s7_clean1} clean2={s7_clean2} vr1={s7_vr1} vr2={s7_vr2} "
                         f"vr3={s7_vr3} vr4={s7_vr4} vr5={s7_vr5} vr6={s7_vr6} "
                         f"vr7_over={s7_vr7_over} vr7_neg={s7_vr7_neg} vr7_date={s7_vr7_date} "
                         f"vr7_unknown={s7_vr7_unknown}")
    except Exception as exc:
        check("S7", False, f"exception: {type(exc).__name__}: {exc}")

    # ---- S8: ttl_bound ----
    try:
        fc_1h_only = {"cache_creation_5m": 0, "cache_creation_1h": 500}
        fc_5m = {"cache_creation_5m": 500, "cache_creation_1h": 0}
        fc_zero = {"cache_creation_5m": 0, "cache_creation_1h": 0}
        fc_unknown = {"cache_creation_5m": None, "cache_creation_1h": None}
        fc_mixed = {"cache_creation_5m": 100, "cache_creation_1h": 200}
        s8 = (ttl_bound(fc_1h_only) == 3300 and ttl_bound(fc_5m) == 240
              and ttl_bound(fc_zero) == 240 and ttl_bound(fc_unknown) == 240
              and ttl_bound(fc_mixed) == 240 and ttl_bound(None) == 240 and ttl_bound({}) == 240)
        check("S8", s8, f"1h_only={ttl_bound(fc_1h_only)} 5m={ttl_bound(fc_5m)} "
                         f"zero={ttl_bound(fc_zero)} unknown={ttl_bound(fc_unknown)}")
    except Exception as exc:
        check("S8", False, f"exception: {type(exc).__name__}: {exc}")

    # ---- S9: mcp_checks (M1/M2/vA) ----
    try:
        def _init(present=True, mcp_servers=None, mcp_tools_n=0, tools_sha256="x"):
            if not present:
                return {"present": False}
            return {"present": True, "mcp_servers": mcp_servers or [], "mcp_tools_n": mcp_tools_n,
                    "tools_sha256": tools_sha256}

        def _runs_for(a1=None, a2=None, b1=None, b2=None):
            out = []
            for run_id, init in (("A1", a1), ("A2", a2), ("B1", b1), ("B2", b2)):
                if init is not None:
                    out.append({"run": run_id, "init": init})
            return out

        r_m1_pass = _runs_for(
            a1=_init(True, mcp_servers=[["context7", "connected"]], tools_sha256="a1"),
            a2=_init(True, mcp_servers=[["context7", "connected"]], tools_sha256="a1"),
            b1=_init(True, mcp_servers=[], tools_sha256="b"),
            b2=_init(True, mcp_servers=[], tools_sha256="b"),
        )
        m1a, m2a, vAa, _ = mcp_checks(r_m1_pass)
        s9_1 = (m1a == "PASS" and m2a == "PASS" and vAa == "NO")

        r_m1_fail = _runs_for(
            a1=_init(True, mcp_servers=[["context7", "connected"]]),
            a2=_init(True, mcp_servers=[["context7", "connected"]]),
            b1=_init(True, mcp_servers=[]),
            b2=_init(True, mcp_servers=[["context7", "connected"]], mcp_tools_n=1),
        )
        m1b, _, _, _ = mcp_checks(r_m1_fail)
        s9_2 = (m1b == "FAIL")

        r_m1_unknown = _runs_for(
            a1=_init(True, mcp_servers=[["context7", "connected"]]),
            a2=_init(True, mcp_servers=[["context7", "connected"]]),
            b1=_init(True, mcp_servers=[]),
        )
        m1c, _, _, _ = mcp_checks(r_m1_unknown)
        s9_3 = (m1c == "UNKNOWN")

        r_m2_fail = _runs_for(
            a1=_init(True, mcp_servers=[]), a2=_init(True, mcp_servers=[]),
            b1=_init(True, mcp_servers=[]), b2=_init(True, mcp_servers=[]),
        )
        _, m2d, _, _ = mcp_checks(r_m2_fail)
        s9_4 = (m2d == "FAIL")

        r_m2_unknown = _runs_for(
            b1=_init(True, mcp_servers=[]), b2=_init(True, mcp_servers=[]),
        )
        _, m2e, vAe, _ = mcp_checks(r_m2_unknown)
        s9_5 = (m2e == "UNKNOWN" and vAe == "UNKNOWN")

        r_vA_status = _runs_for(
            a1=_init(True, mcp_servers=[["context7", "connected"]], tools_sha256="same"),
            a2=_init(True, mcp_servers=[["context7", "failed"]], tools_sha256="same"),
            b1=_init(True, mcp_servers=[]), b2=_init(True, mcp_servers=[]),
        )
        _, _, vAf, _ = mcp_checks(r_vA_status)
        s9_6 = (vAf == "YES")

        r_vA_sha = _runs_for(
            a1=_init(True, mcp_servers=[["context7", "connected"]], tools_sha256="one"),
            a2=_init(True, mcp_servers=[["context7", "connected"]], tools_sha256="two"),
            b1=_init(True, mcp_servers=[]), b2=_init(True, mcp_servers=[]),
        )
        _, _, vAg, _ = mcp_checks(r_vA_sha)
        s9_7 = (vAg == "YES")

        s9 = all([s9_1, s9_2, s9_3, s9_4, s9_5, s9_6, s9_7])
        check("S9", s9, f"m1_pass={s9_1} m1_fail={s9_2} m1_unknown={s9_3} m2_fail={s9_4} "
                         f"m2_unknown={s9_5} vA_status={s9_6} vA_sha={s9_7}")
    except Exception as exc:
        check("S9", False, f"exception: {type(exc).__name__}: {exc}")

    # ---- S10: verdict boundaries (R1-R8) ----
    try:
        def _metrics(s_a2, s_b2, vA):
            return {"gap": round(s_b2 - s_a2, 6), "s_A2": s_a2, "s_B2": s_b2, "vA": vA}

        cases = [
            (_metrics(0.5, 0.8, "YES"), [], 4, True, "PASS", "PASS", "SUPPORTED", "R5"),
            (_metrics(0.8, 0.9, "YES"), [], 4, True, "PASS", "PASS", "UNJUDGED", "R8"),
            (_metrics(0.3, 0.35, "NO"), [], 4, True, "PASS", "PASS", "REFUTED", "R6"),
            (_metrics(0.9, 0.92, "YES"), [], 4, True, "PASS", "PASS", "REFUTED", "R7"),
            (_metrics(0.9, 0.92, "NO"), [], 4, True, "PASS", "PASS", "UNJUDGED", "R8"),
            (_metrics(0.3, 0.8, "NO"), [], 4, True, "PASS", "PASS", "UNJUDGED", "R8"),
            (_metrics(0.05, 0.45, "UNKNOWN"), [], 4, True, "PASS", "PASS", "UNJUDGED", "R8"),
            (_metrics(0.8, 0.6, "NO"), [], 4, True, "PASS", "PASS", "UNJUDGED", "R8"),
            (_metrics(0.5, 0.8, "YES"), ["A1"], 4, True, "PASS", "PASS", "UNJUDGED", "R2"),
            (_metrics(0.5, 0.8, "YES"), [], 4, True, "FAIL", "PASS", "UNJUDGED", "R3"),
            (_metrics(0.5, 0.8, "YES"), [], 4, True, "PASS", "FAIL", "UNJUDGED", "R4"),
        ]
        s10_results = []
        for (metrics, invalid_ids, launches, complete, m1, m2, exp_label, exp_rule) in cases:
            label, reason, rule = verdict(metrics, invalid_ids, launches, complete, m1, m2)
            s10_results.append((label == exp_label and rule == exp_rule, label, rule, exp_label, exp_rule))
        s10 = all(r[0] for r in s10_results)
        check("S10", s10, f"{s10_results}")
    except Exception as exc:
        check("S10", False, f"exception: {type(exc).__name__}: {exc}")

    # ---- S11: full fake live run (SUPPORTED/R5) ----
    try:
        with tempfile.TemporaryDirectory() as td2_s:
            td2 = Path(td2_s)
            fake2 = _write_fake_claude(td2)
            fake2_sha = hashlib.sha256(fake2.read_bytes()).hexdigest()
            projects_dir2 = td2 / "projects"
            projects_dir2.mkdir()
            scratch2 = td2 / "scratch"
            out2 = td2 / "ab-live.json"
            sids11 = {
                "A1": "aaaaaaaa-0000-0000-0000-000000000001",
                "A2": "aaaaaaaa-0000-0000-0000-000000000002",
                "B1": "bbbbbbbb-0000-0000-0000-000000000001",
                "B2": "bbbbbbbb-0000-0000-0000-000000000002",
            }
            fixture11 = {
                sids11["A1"]: {
                    "usage": {"input_tokens": 200, "cache_creation_input_tokens": 800,
                              "cache_creation": {"ephemeral_5m_input_tokens": 800,
                                                  "ephemeral_1h_input_tokens": 0},
                              "cache_read_input_tokens": 0, "output_tokens": 5},
                    "model": "claude-haiku-fake", "entrypoint": "sdk-cli", "rc": 0,
                    "tools": ["Bash", "Read", "mcp__context7__search"],
                    "mcp_servers": [{"name": "context7", "status": "connected"}],
                },
                sids11["A2"]: {
                    "usage": {"input_tokens": 1000, "cache_creation_input_tokens": 0,
                              "cache_creation": {"ephemeral_5m_input_tokens": 0,
                                                  "ephemeral_1h_input_tokens": 0},
                              "cache_read_input_tokens": 0, "output_tokens": 5},
                    "model": "claude-haiku-fake", "entrypoint": "sdk-cli", "rc": 0,
                    "tools": ["Bash", "Read"],
                    "mcp_servers": [{"name": "context7", "status": "failed"}],
                },
                sids11["B1"]: {
                    "usage": {"input_tokens": 1000, "cache_creation_input_tokens": 0,
                              "cache_creation": {"ephemeral_5m_input_tokens": 0,
                                                  "ephemeral_1h_input_tokens": 0},
                              "cache_read_input_tokens": 0, "output_tokens": 5},
                    "model": "claude-haiku-fake", "entrypoint": "sdk-cli", "rc": 0,
                    "tools": ["Bash", "Read"], "mcp_servers": [],
                },
                sids11["B2"]: {
                    "usage": {"input_tokens": 0, "cache_creation_input_tokens": 3,
                              "cache_creation": {"ephemeral_5m_input_tokens": 3,
                                                  "ephemeral_1h_input_tokens": 0},
                              "cache_read_input_tokens": 997, "output_tokens": 5},
                    "model": "claude-haiku-fake", "entrypoint": "sdk-cli", "rc": 0,
                    "tools": ["Bash", "Read"], "mcp_servers": [],
                },
            }
            fixture_path2 = td2 / "fixture11.json"
            fixture_path2.write_text(json.dumps(fixture11), encoding="utf-8")
            log_path2 = td2 / "log11.jsonl"

            environ2 = dict(bare)
            environ2.update({
                "FAKE_LOG": str(log_path2), "FAKE_FIXTURE": str(fixture_path2),
                "FAKE_PROJECTS_DIR": str(projects_dir2), "HOME": bare.get("HOME", ""),
            })

            expect_fp = rules_fingerprint()
            expect_sha = runner_sha256()
            rc11 = live(fake2, fake2_sha, expect_sha, expect_fp, out2,
                        scratch_root=scratch2, projects_dir=projects_dir2, environ=environ2,
                        sids=sids11, run_timeout_s=30)
            launches_logged = 0
            if log_path2.is_file():
                launches_logged = sum(1 for _ in log_path2.read_text(encoding="utf-8").splitlines())
            result11 = json.loads(out2.read_text(encoding="utf-8")) if out2.is_file() else {}
            only_b_strict = all(
                ("--strict-mcp-config" in r.get("argv_display", "")) == (r["arm"] == "B")
                for r in result11.get("runs", [])
            )
            run_order_ok = [r["run"] for r in result11.get("runs", [])] == list(RUN_ORDER)
            dumped11 = json.dumps(result11)

            forbidden_keys = set()

            def _walk(o):
                if isinstance(o, dict):
                    for k, v in o.items():
                        forbidden_keys.add(k)
                        _walk(v)
                elif isinstance(o, list):
                    for v in o:
                        _walk(v)

            _walk(result11)
            bad_keys = forbidden_keys & {"result", "text", "content", "message", "stdout",
                                          "email", "orgId", "orgName"}

            readout_proc = subprocess.run(
                [sys.executable, str(THIS_FILE), "--readout", str(out2)],
                capture_output=True, text=True, timeout=60, env=dict(os.environ))
            readout_last = (readout_proc.stdout.strip().splitlines() or [""])[-1]

            lines11 = evidence_lines(result11)
            gex44_ok = all(
                l.endswith("(GEX44)") for l in lines11
                if re.match(r"^[AB][12]_(?:first_call_[a-z_]+|reuse_share|calls): ", l)
            )

            s11 = (rc11 == 0 and launches_logged == 4 and run_order_ok and only_b_strict
                   and result11.get("verdict") == "SUPPORTED" and result11.get("rule_fired") == "R5"
                   and "FAKE-REPLY-SENTINEL" not in dumped11 and not bad_keys
                   and readout_proc.returncode == 0 and readout_last == "READOUT: MATCH"
                   and gex44_ok)
            check("S11", s11, f"rc11={rc11} launches_logged={launches_logged} run_order_ok={run_order_ok} "
                               f"only_b_strict={only_b_strict} verdict={result11.get('verdict')} "
                               f"rule={result11.get('rule_fired')} readout={readout_last!r} "
                               f"bad_keys={bad_keys} readout_stderr={readout_proc.stderr[:300]!r}")
    except Exception as exc:
        check("S11", False, f"exception: {type(exc).__name__}: {exc}")

    # ---- S12: guards G1-G8 ----
    try:
        with tempfile.TemporaryDirectory() as td3_s:
            td3 = Path(td3_s)
            fake3 = _write_fake_claude(td3)
            fake3_sha = hashlib.sha256(fake3.read_bytes()).hexdigest()
            good_fp = rules_fingerprint()
            good_sha = runner_sha256()
            g_results = []

            def _fresh(tag):
                d = td3 / tag
                pd = d / "projects"
                pd.mkdir(parents=True)
                sc = d / "scratch"
                out = d / "out.json"
                log = d / "log.jsonl"
                fixture_path = d / "fixture.json"
                sids = {r: f"{tag}-{r.lower()}-0000-0000-000000000000" for r in RUN_ORDER}
                fixture = {sid: {"usage": {"input_tokens": 10, "cache_read_input_tokens": 0,
                                            "cache_creation_input_tokens": 0},
                                  "model": "claude-haiku-fake", "entrypoint": "sdk-cli", "rc": 0,
                                  "tools": [], "mcp_servers": []}
                           for sid in sids.values()}
                fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
                env = dict(bare)
                env.update({"FAKE_LOG": str(log), "FAKE_FIXTURE": str(fixture_path),
                            "FAKE_PROJECTS_DIR": str(pd), "HOME": bare.get("HOME", "")})
                return pd, sc, out, log, sids, env

            def _launch_count(log_path):
                return sum(1 for _ in log_path.read_text(encoding="utf-8").splitlines()) \
                    if log_path.is_file() else 0

            # G1 case 1: ANTHROPIC_API_KEY alone
            pd, sc, out, log, sids, env = _fresh("g1a")
            env["ANTHROPIC_API_KEY"] = "FAKE-KEY-G1A"
            rc = live(fake3, fake3_sha, good_sha, good_fp, out, scratch_root=sc,
                      projects_dir=pd, environ=env, sids=sids, run_timeout_s=10)
            g_results.append(("G1a", rc == 3 and _launch_count(log) == 0 and not out.exists()
                               and not (sc / "LIVE-LATCH").exists()))

            # G1 case 2: only a BLOCKING_ENV name (CLAUDE_CONFIG_DIR)
            pd, sc, out, log, sids, env = _fresh("g1b")
            env["CLAUDE_CONFIG_DIR"] = "/tmp/FAKE-G1B"
            rc = live(fake3, fake3_sha, good_sha, good_fp, out, scratch_root=sc,
                      projects_dir=pd, environ=env, sids=sids, run_timeout_s=10)
            g_results.append(("G1b", rc == 3 and _launch_count(log) == 0 and not out.exists()
                               and not (sc / "LIVE-LATCH").exists()))

            # G2: out already exists
            pd, sc, out, log, sids, env = _fresh("g2")
            out.write_text("{}", encoding="utf-8")
            rc = live(fake3, fake3_sha, good_sha, good_fp, out, scratch_root=sc,
                      projects_dir=pd, environ=env, sids=sids, run_timeout_s=10)
            g_results.append(("G2", rc == 3 and _launch_count(log) == 0
                               and not (sc / "LIVE-LATCH").exists()))

            # G3: LIVE-LATCH pre-exists
            pd, sc, out, log, sids, env = _fresh("g3")
            sc.mkdir(parents=True)
            (sc / "LIVE-LATCH").write_text("pre-existing", encoding="utf-8")
            rc = live(fake3, fake3_sha, good_sha, good_fp, out, scratch_root=sc,
                      projects_dir=pd, environ=env, sids=sids, run_timeout_s=10)
            g_results.append(("G3", rc == 3 and _launch_count(log) == 0 and not out.exists()))

            # G4: armA pre-exists
            pd, sc, out, log, sids, env = _fresh("g4")
            (sc / "armA").mkdir(parents=True)
            rc = live(fake3, fake3_sha, good_sha, good_fp, out, scratch_root=sc,
                      projects_dir=pd, environ=env, sids=sids, run_timeout_s=10)
            g_results.append(("G4", rc == 3 and _launch_count(log) == 0 and not out.exists()
                               and not (sc / "LIVE-LATCH").exists()))

            # G5: wrong exe sha256
            pd, sc, out, log, sids, env = _fresh("g5")
            rc = live(fake3, "0" * 64, good_sha, good_fp, out, scratch_root=sc,
                      projects_dir=pd, environ=env, sids=sids, run_timeout_s=10)
            g_results.append(("G5", rc == 3 and _launch_count(log) == 0 and not out.exists()
                               and not (sc / "LIVE-LATCH").exists()))

            # G6: wrong expected fingerprint
            pd, sc, out, log, sids, env = _fresh("g6")
            rc = live(fake3, fake3_sha, good_sha, "0" * 64, out, scratch_root=sc,
                      projects_dir=pd, environ=env, sids=sids, run_timeout_s=10)
            g_results.append(("G6", rc == 3 and _launch_count(log) == 0 and not out.exists()
                               and not (sc / "LIVE-LATCH").exists()))

            # G7: auth not oauth (FAKE_AUTH_METHOD=api_key)
            pd, sc, out, log, sids, env = _fresh("g7")
            env["FAKE_AUTH_METHOD"] = "api_key"
            rc = live(fake3, fake3_sha, good_sha, good_fp, out, scratch_root=sc,
                      projects_dir=pd, environ=env, sids=sids, run_timeout_s=10)
            g_results.append(("G7", rc == 3 and _launch_count(log) == 0 and not out.exists()
                               and not (sc / "LIVE-LATCH").exists()))

            # G8: a pre-assigned id already has a transcript
            pd, sc, out, log, sids, env = _fresh("g8")
            precreated_key = "precreated-key"
            (pd / precreated_key).mkdir(parents=True)
            (pd / precreated_key / f"{sids['A1']}.jsonl").write_text("{}\n", encoding="utf-8")
            rc = live(fake3, fake3_sha, good_sha, good_fp, out, scratch_root=sc,
                      projects_dir=pd, environ=env, sids=sids, run_timeout_s=10)
            g_results.append(("G8", rc == 3 and _launch_count(log) == 0 and not out.exists()
                               and not (sc / "LIVE-LATCH").exists()))

            # Pass-through: only non-blocking CLAUDE* names set -> passes G1 and launches
            pd, sc, out, log, sids, env = _fresh("g1pass")
            env.update({"CLAUDECODE": "FAKE-1", "CLAUDE_CODE_SESSION_ID": "FAKE-SESS"})
            rc = live(fake3, fake3_sha, good_sha, good_fp, out, scratch_root=sc,
                      projects_dir=pd, environ=env, sids=sids, run_timeout_s=10)
            saw_no_claude_names = True
            if log.is_file():
                for line in log.read_text(encoding="utf-8").splitlines():
                    rec = json.loads(line)
                    if any(n.startswith("CLAUDE") for n in rec.get("env_names", [])):
                        saw_no_claude_names = False
            g_results.append(("G1pass", rc == 0 and _launch_count(log) == 4 and saw_no_claude_names))

            s12 = all(ok for _, ok in g_results)
            check("S12", s12, f"{g_results}")
    except Exception as exc:
        check("S12", False, f"exception: {type(exc).__name__}: {exc}")

    # ---- S13: no early stop, no retry (INVALID runs still give 4 launches) ----
    try:
        with tempfile.TemporaryDirectory() as td4_s:
            td4 = Path(td4_s)
            fake4 = _write_fake_claude(td4)
            fake4_sha = hashlib.sha256(fake4.read_bytes()).hexdigest()
            good_fp = rules_fingerprint()
            good_sha = runner_sha256()
            pd = td4 / "projects"
            pd.mkdir()
            sc = td4 / "scratch"
            out = td4 / "out.json"
            log = td4 / "log.jsonl"
            sids13 = {
                "A1": "13111111-0000-0000-0000-000000000001",
                "A2": "13111111-0000-0000-0000-000000000002",
                "B1": "13222222-0000-0000-0000-000000000001",
                "B2": "13222222-0000-0000-0000-000000000002",
            }
            fixture13 = {
                sids13["A1"]: {"usage": {"input_tokens": 10, "cache_read_input_tokens": 0,
                                          "cache_creation_input_tokens": 0},
                               "model": "claude-haiku-fake", "entrypoint": "sdk-cli", "rc": 1,
                               "tools": [], "mcp_servers": []},
                sids13["A2"]: {"usage": {"input_tokens": 10, "cache_read_input_tokens": 0,
                                          "cache_creation_input_tokens": 0},
                               "model": "claude-haiku-fake", "entrypoint": "sdk-cli", "rc": 0,
                               "tools": [], "mcp_servers": []},
                sids13["B1"]: {"usage": {"input_tokens": 10, "cache_read_input_tokens": 0,
                                          "cache_creation_input_tokens": 0},
                               "model": "claude-haiku-fake", "entrypoint": "sdk-cli", "rc": 0,
                               "tools": [], "mcp_servers": []},
                sids13["B2"]: {"usage": {"input_tokens": 10, "cache_read_input_tokens": 0,
                                          "cache_creation_input_tokens": 0},
                               "model": "claude-haiku-fake", "entrypoint": "sdk-cli", "rc": 0,
                               "tools": [], "mcp_servers": [], "sleep_s": 4},
            }
            fixture_path = td4 / "fixture13.json"
            fixture_path.write_text(json.dumps(fixture13), encoding="utf-8")
            environ13 = dict(bare)
            environ13.update({"FAKE_LOG": str(log), "FAKE_FIXTURE": str(fixture_path),
                               "FAKE_PROJECTS_DIR": str(pd), "HOME": bare.get("HOME", "")})

            rc13 = live(fake4, fake4_sha, good_sha, good_fp, out, scratch_root=sc,
                        projects_dir=pd, environ=environ13, sids=sids13, run_timeout_s=2)
            launches13 = sum(1 for _ in log.read_text(encoding="utf-8").splitlines()) if log.is_file() else 0
            result13 = json.loads(out.read_text(encoding="utf-8")) if out.is_file() else {}
            by_run13 = {r["run"]: r for r in result13.get("runs", [])}
            a1_invalid = "VR1" in (by_run13.get("A1", {}).get("validity", {}).get("failed") or [])
            b2_timed_out = by_run13.get("B2", {}).get("timed_out") is True
            b2_invalid = "VR1" in (by_run13.get("B2", {}).get("validity", {}).get("failed") or [])

            # a second live() call on the same out/scratch must refuse (G2/G3) -- no fifth launch
            out2exists_before = out.exists()
            rc_second = live(fake4, fake4_sha, good_sha, good_fp, out, scratch_root=sc,
                              projects_dir=pd, environ=environ13, sids=sids13, run_timeout_s=2)
            launches_after_second = sum(1 for _ in log.read_text(encoding="utf-8").splitlines()) \
                if log.is_file() else 0

            s13 = (rc13 == 0 and launches13 == 4 and a1_invalid and b2_timed_out and b2_invalid
                   and result13.get("rule_fired") == "R2" and result13.get("verdict") == "UNJUDGED"
                   and rc_second == 3 and launches_after_second == 4 and out2exists_before)
            check("S13", s13, f"rc13={rc13} launches13={launches13} a1_invalid={a1_invalid} "
                               f"b2_timed_out={b2_timed_out} b2_invalid={b2_invalid} "
                               f"rule_fired={result13.get('rule_fired')} rc_second={rc_second} "
                               f"launches_after_second={launches_after_second}")
    except Exception as exc:
        check("S13", False, f"exception: {type(exc).__name__}: {exc}")

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
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--claude-sha256")
    ap.add_argument("--expect-runner-sha256")
    ap.add_argument("--expect-rules-fingerprint")
    ap.add_argument("--out")
    ap.add_argument("--readout")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--evidence-lines")
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

    if args.fingerprint:
        _ensure_tools_importable()
        print(f"runner_sha256: {runner_sha256()}")
        print(f"rules_fingerprint: {rules_fingerprint()}")
        thresholds = " ".join(f"{k}={v}" for k, v in RULES.items())
        print(f"thresholds: {thresholds}")
        print(f"prompt: {PROMPT}")
        print(f"model: {MODEL_ARG}")
        print(f"argv_A: {render_argv('A')}")
        print(f"argv_B: {render_argv('B')}")
        print(f"scratch_root: {SCRATCH_ROOT}")
        print(f"cwd_A: {SCRATCH_ROOT / 'armA'}")
        print(f"cwd_B: {SCRATCH_ROOT / 'armB'}")
        print(f"project_key_A: {predicted_project_key(SCRATCH_ROOT / 'armA')}")
        print(f"project_key_B: {predicted_project_key(SCRATCH_ROOT / 'armB')}")
        print(f"run_order: {' '.join(RUN_ORDER)}")
        print(f"run_timeout_s: {RUN_TIMEOUT_S}")
        return 0

    if args.live:
        _ensure_tools_importable()
        if not (args.claude and args.claude_sha256 and args.expect_runner_sha256
                and args.expect_rules_fingerprint and args.out):
            print("ERROR: --live requires --claude --claude-sha256 --expect-runner-sha256 "
                  "--expect-rules-fingerprint --out", file=sys.stderr)
            return 2
        return live(args.claude, args.claude_sha256, args.expect_runner_sha256,
                    args.expect_rules_fingerprint, args.out)

    if args.readout:
        _ensure_tools_importable()
        return readout(args.readout, write=args.write)

    if args.evidence_lines:
        _ensure_tools_importable()
        data = json.loads(Path(args.evidence_lines).read_text(encoding="utf-8"))
        for line in evidence_lines(data):
            print(line)
        return 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
