"""Mission policy: what a mission worker may do, decided before it runs and re-decided when it stops.

AMR addendum (vault/plans/amr-addendum-decision-env-executor-20261013.md). Origin, measured 2026-10-12:
mission m-5cd1a041bc0f (kobicraft-web) ran in a repo whose `.planning/config.json` says
`workflow.use_worktrees: false`. The runtime pre-approved EnterWorktree for every worker and never read that
file, so the worker chose a worktree; EnterWorktree failed (git is not on PATH on this machine); the worker
made one by hand, then ended its turn asking the Owner which to use. The host recorded the question as the
job's `needs` and listed the session `blocked`; the supervisor read every bare `blocked` as "a human must
answer" and parked the mission for 21 h 43 min on a question the repo config already answered.

Everything here is deterministic. I/O is limited to reading a config file, probing an executable, and
asking git about one worktree; each is injectable for tests.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

# ----------------------------------------------------------------------------------------- precedence
# Higher index loses. A layer that does not state the key is skipped; the first layer that does wins.
PRECEDENCE = ("owner", "constitution", "repo", "mission", "runtime_default", "model")


def resolve(key: str, layers: dict) -> dict:
    """{"value", "source", "layer"} from the highest-precedence layer that states ``key``.

    ``layers`` maps a layer name to {"values": {...}, "source": "<path or label>"}. A layer absent from
    PRECEDENCE is refused, so a typo cannot silently become the lowest layer."""
    unknown = set(layers) - set(PRECEDENCE)
    if unknown:
        raise ValueError(f"unknown policy layer(s): {sorted(unknown)}")
    for layer in PRECEDENCE:
        spec = layers.get(layer) or {}
        values = spec.get("values") or {}
        if key in values and values[key] is not None:
            return {"value": values[key], "layer": layer, "source": spec.get("source") or layer}
    return {"value": None, "layer": None, "source": None}


GIT_CANDIDATES = (r"C:\Program Files\Git\cmd\git.exe", r"C:\Program Files\Git\bin\git.exe",
                  "/usr/bin/git", "/usr/local/bin/git")


def git_exe(which=shutil.which, exists=os.path.isfile) -> str | None:
    return which("git") or next((p for p in GIT_CANDIDATES if exists(p)), None)


def _toplevel(cwd: str, runner=None) -> Path:
    exe = git_exe()
    if exe:
        try:
            r = (runner or subprocess.run)([exe, "-C", cwd, "rev-parse", "--show-toplevel"],
                                           capture_output=True, text=True, timeout=20)
            if r.returncode == 0 and r.stdout.strip():
                return Path(r.stdout.strip())
        except (OSError, subprocess.SubprocessError):
            pass
    return Path(cwd)


def repo_policy(cwd: str, root: Path | None = None) -> dict:
    """The repo layer: `.planning/config.json` -> {"values", "source", "fingerprint"}.

    Missing file -> no values (the runtime default decides). Unreadable or malformed file -> values empty
    and ``error`` set: a broken policy file is reported, never read as permission."""
    root = root or _toplevel(cwd)
    p = root / ".planning" / "config.json"
    if not p.is_file():
        return {"values": {}, "source": None, "fingerprint": None}
    raw = p.read_bytes()
    fp = hashlib.sha256(raw).hexdigest()[:16]
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"values": {}, "source": str(p), "fingerprint": fp, "error": f"{type(exc).__name__}: {exc}"[:200]}
    wf = data.get("workflow") if isinstance(data, dict) else None
    values = {}
    if isinstance(wf, dict) and isinstance(wf.get("use_worktrees"), bool):
        values["use_worktrees"] = wf["use_worktrees"]
    return {"values": values, "source": str(p), "fingerprint": fp}


# ------------------------------------------------------------------------------------- capabilities
def probe_capabilities(needed, which=shutil.which, exists=os.path.isfile) -> dict:
    """Health of the capabilities a topology needs, and only those (proportional preflight).

    git: HEALTHY on PATH; PATH_MISMATCH when only a known absolute path has it (scripts using the absolute
    path work, PATH-resolving tools do not); EXECUTABLE_NOT_FOUND otherwise.
    EnterWorktree resolves git through PATH (measured 2026-10-12: "Command 'git' not found or is in an
    unsafe location"), so it is HEALTHY only when git is on PATH."""
    out = {}
    on_path = which("git")
    absolute = next((p for p in GIT_CANDIDATES if exists(p)), None)
    git = ({"health": "HEALTHY", "path": on_path} if on_path else
           {"health": "PATH_MISMATCH", "path": absolute} if absolute else
           {"health": "EXECUTABLE_NOT_FOUND", "path": None})
    for cap in needed:
        if cap == "git":
            out["git"] = git
        elif cap == "EnterWorktree":
            out[cap] = ({"health": "HEALTHY"} if git["health"] == "HEALTHY" else
                        {"health": "UNHEALTHY", "cause": f"git {git['health']}"})
        else:
            out[cap] = {"health": "UNKNOWN", "cause": "no probe for this capability"}
    return out


ENV_CLASSES = (
    ("EXECUTABLE_NOT_FOUND", re.compile(r"not found|is not recognized|no such file|cannot find", re.I)),
    ("PERMISSION", re.compile(r"permission denied|access is denied|EACCES|EPERM", re.I)),
    ("PATH_MISMATCH", re.compile(r"unsafe location|not on (the )?PATH", re.I)),
    ("VERSION_MISMATCH", re.compile(r"unsupported version|requires version|version mismatch", re.I)),
    ("RESOURCE_UNAVAILABLE", re.compile(r"no space left|out of memory|ENOSPC|ENOMEM", re.I)),
    ("TRANSIENT_FAILURE", re.compile(r"timed? ?out|ECONNRESET|temporarily unavailable|HTTP 5\d\d", re.I)),
)


def classify_env_failure(text: str) -> str:
    for cls, rx in ENV_CLASSES:
        if rx.search(text or ""):
            return cls
    return "UNKNOWN"


# ----------------------------------------------------------------------------------------- topology
def compile_topology(policy: dict, health: dict | None = None) -> dict:
    """Main tree unless policy allows worktrees AND EnterWorktree is healthy.

    ``policy`` is the resolve() result for `use_worktrees`. Runtime default when nobody states it: worktrees
    allowed (today's behaviour), but only with a healthy capability -- otherwise the precompiled fallback."""
    allowed = policy.get("value")
    allowed = True if allowed is None else bool(allowed)
    ent = (health or {}).get("EnterWorktree", {}).get("health")
    if not allowed:
        return {"kind": "main_tree", "worktrees": False, "policy_forbids": True,
                "why": f"use_worktrees=false ({policy.get('source')})",
                "allowed_tools": [], "disallowed_tools": ["EnterWorktree", "ExitWorktree"]}
    if ent not in (None, "HEALTHY"):
        return {"kind": "main_tree", "worktrees": False, "fallback": True,
                "why": f"worktrees allowed but EnterWorktree {ent}: fallback main tree",
                "allowed_tools": [], "disallowed_tools": ["EnterWorktree", "ExitWorktree"]}
    return {"kind": "worktree_allowed", "worktrees": True, "why": "use_worktrees not false and capability healthy",
            "allowed_tools": ["EnterWorktree", "ExitWorktree"], "disallowed_tools": []}


def topology_for(cwd: str, health_probe=None) -> dict:
    """Repo policy -> resolved value -> topology, with provenance. Never raises: a probe failure keeps
    the main tree (the safe topology), recorded. The probe is looked up at call time, so it stays
    injectable."""
    try:
        rp = repo_policy(cwd)
        pol = resolve("use_worktrees", {"repo": {"values": rp["values"], "source": rp["source"]}})
        probe = health_probe or probe_capabilities
        health = probe(["git", "EnterWorktree"]) if pol["value"] is not False else {}
        topo = compile_topology(pol, health)
        topo.update({"policy": pol, "fingerprint": rp.get("fingerprint"), "health": health})
        if rp.get("error"):
            topo["policy_error"] = rp["error"]
        return topo
    except Exception as exc:  # noqa: BLE001 -- recorded in the result, the safe topology is kept
        return {"kind": "main_tree", "worktrees": False, "why": f"policy unreadable: {type(exc).__name__}",
                "allowed_tools": [], "disallowed_tools": ["EnterWorktree", "ExitWorktree"], "error": str(exc)[:200]}


WORKTREE_MUTATION = re.compile(r"\bworktree\s+add\b", re.I)


def denies_command(command: str, topology: dict) -> str | None:
    """Reason to refuse a shell command under ``topology``, or None."""
    if not topology.get("worktrees", True) and WORKTREE_MUTATION.search(command or ""):
        return f"refused: `git worktree add` under {topology.get('why')}; work in the main tree"
    return None


# --------------------------------------------------------------------------- Owner Escalation Gate
# The ONLY question classes that may reach the Owner. Each needs a match in the question itself.
# Done-gate override, spend/overrun acceptance, VERIFICATION set to passed with gaps/deviations, envelope-STOP release.
# Bare "gap", "deviation" and "verification" must NOT match (an ordinary ordering question stays RESOLVE_BY_DEFAULT).
DONE_GATE_RX = re.compile(
    r"\boverrid\w*\b[^?.]{0,40}\b(?:done[- ]?gate|envelope|breach|stop)\b|"
    r"\baccept\w*\b[^?.]{0,25}\b(?:breach|overrun)\b|"
    r"\bverification\b[^?.]{0,60}\bpassed\b[^?.]{0,80}\b(?:gaps?|deviations?|breach)\b|"
    r"\b(?:record|accept)\w*\b[^?.]{0,50}\bas\s+(?:an?\s+|accepted\s+)*deviations?\b|"
    r"\b(?:release|lift|waive|bypass|authori[sz]e)\b[^?.]{0,80}\b(?:envelope|stop)\b", re.I)
# Truth contract (S11 A1, incident 2026-11-02 Game-A S10 m-e6e0340e743d: "Decide whether cert-cxx may admit an sd8
# variant" was answered RESOLVE_BY_DEFAULT). Changing what counts as certified, exact or held-out changes WHAT the
# Owner authorised, never only HOW. Strong nouns pair with any change verb; bare exact/certified only with a relaxing
# verb, so "count exact matches per batch" stays an ordinary question.
_TC_VERB = (r"(?:admit|allow|accept|relax|loosen|weaken|change|modify|redefine|waive|lower|widen|count|reuse|treat|"
            r"drop|skip|bypass)\w*")
_TC_RELAX = r"(?:accept|relax|loosen|weaken|redefine|waive|lower)\w*"
# S11 D3 (incident 2026-11-02 23:31Z, "Waive fn_00000A02 for OM-PR1" answered RESOLVE_BY_DEFAULT): the controls and
# gates that release a held-out are part of the truth contract too.
_TC_STRONG = (r"(?:certification contract|cert-[a-z0-9]+(?:@\d+)?|truth contract|match threshold|held[- ]?out|"
              r"independent evidence|evidence (?:accounting|independence)|definition of (?:exact|certified)|"
              r"(?:positive|negative) controls?|kill[- ]gates?|OM-PR\d+|release (?:conditions?|gates?|set))")
# S11 D2 (incident 2026-11-03, a checkpoint reason "in-scope routes falsified" read as PRODUCT_SCOPE): an in/out-of-scope
# adjective in front of an engineering noun describes work; it does not ask about scope. Removed before the class check.
_DESCRIPTIVE_SCOPE_RX = re.compile(
    r"\b(?:in|within|out[- ]of)[- ]scope(?=[ -]+(?:routes?|methods?|options?|approach\w*|candidates?|variants?|work|"
    r"items?|attempts?|fixes)\b)", re.I)
TRUTH_CONTRACT_RX = re.compile(
    r"\b" + _TC_VERB + r"\b[^?.]{0,80}" + _TC_STRONG + r"|"
    r"\b" + _TC_RELAX + r"\b[^?.]{0,60}\b(?:exact(?:ness)?|certified)\b|"
    # S11H P5: waiving a named function (a gate member) is a gate change even with no control noun beside it.
    r"\bwaiv\w*\b[^?.]{0,20}\bfn_[0-9a-f]{6,8}\b|"
    + _TC_STRONG + r"[^?.]{0,60}\b" + _TC_VERB + r"\b[^?.]{0,40}\b(?:variant|flags?|config\w*|lane|threshold|rules?)\b",
    re.I)
# An IMPERATIVE switch-off acting on a guard ("clear the breaker", "set the kill switch off"), or a CPP_* env switch
# set off. Review F2: status sentences ("kill gate K5 cleared at 3/3", "the breaker reset overnight"), the adjective
# ("not clear which gate") and "kick off the gate suite" are descriptions, and checkpoint REASONS are gated too.
_GD_VERB = r"(?:disable|clear|reset|bypass|skip|silence|mute|turn\s+off|switch\s+off)"
_GD_NOUN = r"(?:breakers?|guards?|gates?|hooks?|kill[- ]?switch(?:es)?|firewalls?|sentinels?)"
_GD_DET = r"(?:the|this|that|its|their|a|an|all|every|both|my|our)"
GUARD_DISABLE_RX = re.compile(
    r"\b" + _GD_VERB + r"\s+" + _GD_DET + r"\s+(?:[\w-]+\s+){0,3}" + _GD_NOUN + r"\b|"
    r"\b(?:set|turn|switch|put)\s+" + _GD_DET + r"\s+(?:[\w-]+\s+){0,3}" + _GD_NOUN + r"\s+off\b|"
    r"\bCPP_[A-Z0-9_]+\s*=\s*(?:off|0|false|disabled?)\b", re.I)
OWNER_CLASSES = (
    ("DEPLOY_OR_LIVE_WRITE", re.compile(r"\bHR-0?4\b|\bdeploy|\bpush\b|producci[oó]n|\bprod(uction)?\b|live (server|write)|"
                                        r"servidor (vivo|en vivo)", re.I)),
    ("SECURITY_OR_CREDENTIAL", re.compile(r"credential|secret|password|contraseñ|api[ _-]?key|\btoken\b|login required|"
                                          r"sign[ -]?in|oauth", re.I)),
    ("EXTERNAL_PROPERTY", re.compile(r"\bGA4\b|property|propiedad|vercel|dns|registrar|billing|factur|purchase|pago", re.I)),
    ("IRREVERSIBLE", re.compile(r"irreversib|permanently|force[- ]push|drop (table|database)|delete (the )?(remote|production)", re.I)),
    # Spec capsule-seal-on-question-end D2 (m-81b9650c6ff2, 2026-11-03 15:47Z): "set CPP_SEM_BREAKER=off (or clear the
    # breaker)" was answered RESOLVE_BY_DEFAULT, so a successor would have been told to switch a guard off.
    ("GUARD_DISABLE", GUARD_DISABLE_RX),
    ("PRODUCT_SCOPE", re.compile(r"\bscope\b|alcance|product decision|decisi[oó]n de producto|pricing|precio|monetiz", re.I)),
    ("AUTHORITY", re.compile(r"budget (is )?exhausted|authority|more tokens|raise the (cap|envelope)", re.I)),
    ("TRUTH_CONTRACT", TRUTH_CONTRACT_RX),
    ("DONE_GATE_OR_DEVIATION", DONE_GATE_RX),
)
# Questions the runtime answers itself, with the policy key that answers them.
POLICY_RESOLVABLE = (
    ("use_worktrees", re.compile(r"worktree|`?! ?cd`?|restart the session|absolute path|main (tree|checkout)", re.I)),
)


def gate_question(text: str, policy_values: dict | None = None) -> dict:
    """Classify a worker's question. {"result", "owner_class"?, "resolution"}.

    result ∈ OWNER_REQUIRED · RESOLVE_BY_POLICY · RESOLVE_BY_DEFAULT. An Owner class is checked FIRST and is
    decisive: a question that mentions a worktree AND a deploy is still the Owner's (review F1, 2026-10-13 --
    policy-first answered "push to main and deploy?" with "use_worktrees decides it"). With no class at all the
    Owner is not necessary: proof of necessity is a match, not the presence of a question mark."""
    t = text or ""
    pv = policy_values or {}
    gates_off = os.environ.get("CPP_MISSION_OWNER_GATES", "").lower() == "off"
    t_scope = _DESCRIPTIVE_SCOPE_RX.sub(" ", t)
    for cls, rx in OWNER_CLASSES:
        if cls == "DONE_GATE_OR_DEVIATION" and gates_off:
            continue
        if rx.search(t_scope if cls == "PRODUCT_SCOPE" else t):
            return {"result": "OWNER_REQUIRED", "owner_class": cls,
                    "resolution": "Record an `OWNER DECISION NEEDED:` line in the mission STATE and continue every "
                                  "obligation that does not depend on it."}
    for key, rx in POLICY_RESOLVABLE:
        if rx.search(t) and key in pv and pv[key] is not None:
            if key == "use_worktrees" and pv[key] is False:
                return {"result": "RESOLVE_BY_POLICY", "key": key,
                        "resolution": "Repo policy `.planning/config.json` workflow.use_worktrees=false: do NOT use "
                                      "a worktree. Work in the main checkout (the mission cwd), call git by its "
                                      "absolute path, commit locally, do not push."}
            return {"result": "RESOLVE_BY_POLICY", "key": key, "resolution": f"Policy {key}={pv[key]!r} decides it."}
    return {"result": "RESOLVE_BY_DEFAULT",
            "resolution": "No Owner class applies. Take the option you recommended (the evidence-backed one); if you "
                          "named none, take the most reversible option inside the approved scope, record the choice "
                          "in the mission STATE, and continue."}


# ------------------------------------------------------------------------------ blocked validity
def job_state(session_id: str, jobs_dir: Path | None = None) -> dict | None:
    """The host's own record of a background job: ~/.claude/jobs/<sid[:8]>/state.json."""
    jobs_dir = jobs_dir or Path(os.environ.get("CPP_CLAUDE_JOBS_DIR") or Path.home() / ".claude" / "jobs")
    for name in (session_id[:8], session_id):
        p = jobs_dir / name / "state.json"
        if p.is_file():
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return None
            if isinstance(d, dict) and d.get("sessionId", session_id) == session_id:
                return d
    return None


# `needs` shapes that are genuinely a human's (host-level gates, not a model's question).
HOST_GATES = re.compile(r"login required|startup approval|trust (this|the) (folder|workspace)|permission to use|"
                        r"do you want to (proceed|allow|create|make this edit)", re.I)


LIFECYCLE_WORDS = ("stopped", "done", "exited", "failed", "killed")


def classify_blocked(job: dict | None, policy_values: dict | None = None) -> dict:
    """Type a host-`blocked` session. {"class", "why", "gate"?}.

    PERMISSION_PROMPT / HOST_GATE -> a real wait for a human (today's behaviour).
    QUESTION_* -> the model ended its turn on a question: the gate decides.
    UNKNOWN -> no job record: the caller keeps today's behaviour (unknown is never recovered on)."""
    if not job:
        return {"class": "UNKNOWN", "why": "no host job record"}
    needs = str(job.get("needs") or job.get("detail") or "")
    if job.get("waitingFor"):
        return {"class": "PERMISSION_PROMPT", "why": f"host waiting for {job.get('waitingFor')}"}
    if not needs:
        return {"class": "UNKNOWN", "why": "blocked with no `needs` text"}
    # S11H P5: a lifecycle word is the job's end, never a model's question (it cost a decision recovery on GEX44).
    if str(job.get("state") or "").lower() in LIFECYCLE_WORDS or needs.strip().lower() in LIFECYCLE_WORDS:
        return {"class": "STOPPED", "why": f"job ended ({job.get('state')}: {needs.strip()[:40]})"}
    if HOST_GATES.search(needs):
        return {"class": "HOST_GATE", "why": needs[:200]}
    g = gate_question(needs, policy_values)
    if g["result"] == "OWNER_REQUIRED":
        return {"class": "QUESTION_OWNER", "why": needs[:200], "gate": g}
    return {"class": "QUESTION_RESOLVABLE", "why": needs[:200], "gate": g}


LIVENESS_VALID = ("ACTIVE", "SUCCESSOR_COMPILING", "SUCCESSOR_READY", "DURABLE_WAIT", "EXTERNAL_WAIT",
                  "OWNER_BOUNDARY", "TERMINAL")


def goal_liveness(state: str, owner_verdict: str, blocked: dict | None, recovering: bool,
                  owner_packet: bool) -> str:
    """Map a mission to a valid liveness state, or "INCIDENT" (BLOCKED_STATE_WITHOUT_VALID_WAIT)."""
    if state in ("COMPLETED", "HALTED", "STOPPED"):
        return "TERMINAL"
    if recovering:
        return "SUCCESSOR_COMPILING"
    if state == "LAUNCHING":
        return "SUCCESSOR_READY"
    if owner_verdict == "LIVE":
        return "ACTIVE"
    cls = (blocked or {}).get("class")
    if cls in ("PERMISSION_PROMPT", "HOST_GATE"):
        return "OWNER_BOUNDARY"
    if cls == "QUESTION_OWNER":
        return "OWNER_BOUNDARY" if owner_packet else "INCIDENT"
    return "INCIDENT"


# ------------------------------------------------------------------------- artifact cleanup proof
def worktree_cleanup_proof(repo: str, wt_path: str, branch: str, base: str = "main", runner=None) -> dict:
    """Prove a worktree + branch hold nothing: 0 commits outside ``base``, clean status incl. ignored files,
    no stash, worktree not locked. {"safe", "facts", "why"}. Any question git cannot answer -> not safe."""
    exe = git_exe()
    run = runner or (lambda a: subprocess.run(a, capture_output=True, text=True, timeout=60))
    facts: dict = {}
    if not exe:
        return {"safe": False, "facts": facts, "why": "git unavailable"}

    def g(*args, cwd=repo):
        r = run([exe, "-C", cwd, *args])
        return r.returncode, (r.stdout or "").strip()

    rc, out = g("rev-list", "--count", f"{base}..{branch}")
    facts["unique_commits"] = int(out) if rc == 0 and out.isdigit() else None
    rc, out = g("status", "--porcelain", "--ignored", cwd=wt_path)
    facts["dirty"] = out.splitlines() if rc == 0 else None
    rc, out = g("stash", "list")
    facts["stash"] = out.splitlines() if rc == 0 else None
    rc, out = g("worktree", "list", "--porcelain")
    block = next((b for b in out.split("\n\n") if Path(wt_path).as_posix().lower() in b.replace("\\", "/").lower()), "")
    facts["locked"] = ("locked" in block) if rc == 0 else None
    facts["listed"] = bool(block)
    problems = [k for k, bad in (("unique_commits", facts["unique_commits"] != 0),
                                 ("dirty", facts["dirty"] != []),
                                 ("stash", facts["stash"] != []),
                                 ("locked", facts["locked"] is not False),
                                 ("listed", not facts["listed"])) if bad]
    return {"safe": not problems, "facts": facts,
            "why": "empty: 0 unique commits, clean incl. ignored, no stash, unlocked" if not problems
            else f"not proven empty: {', '.join(problems)}"}
